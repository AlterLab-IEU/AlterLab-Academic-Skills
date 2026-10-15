"""Acceptance tests for ``run_evals.py --behavioral`` outcome accounting.

The real subprocess path runs against a fake ``claude`` executable placed first on PATH, so
CLI-flag isolation, JSON parsing, workspace preparation, the judges, the exit code, and the
persisted results file are all exercised without a model. The fake answers deterministically:
the skilled arm (``--append-system-prompt`` present) answers ``GOOD-ANSWER`` unless the mode
says otherwise, the bare arm answers ``plain answer``, and the judges PASS a response only when
it contains ``GOOD-ANSWER``. These are controlled passing/failing cases, not live results.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

import run_evals

FAKE_CLAUDE = r'''#!/usr/bin/env python3
import json, os, sys
argv = sys.argv[1:]
if "--version" in argv:
    print("9.9.9 (Fake Claude Code)")
    sys.exit(0)
mode = os.environ.get("FAKE_CLAUDE_MODE", "ok")
prompt = argv[argv.index("-p") + 1] if "-p" in argv else ""
skilled = "--append-system-prompt" in argv
cwd = os.getcwd()
with open(os.environ["FAKE_CLAUDE_LOG"], "a", encoding="utf-8") as log:
    tools = []
    if "--allowedTools" in argv:
        for a in argv[argv.index("--allowedTools") + 1:]:
            if a.startswith("-"):
                break
            tools.append(a)
    log.write(json.dumps({"cwd": cwd, "flags": [a for a in argv if a.startswith("--")],
                          "tools": tools,
                          "peek": {p: os.path.isdir(p) and bool(os.listdir(p)) for p in
                                   __import__("base64").b64decode(
                                       os.environ.get("FAKE_PEEK_B64", "")).decode().split("|")
                                   if p},
                          "skilled": skilled, "files": sorted(
                              os.path.relpath(os.path.join(r, f), cwd)
                              for r, _, fs in os.walk(cwd) for f in fs)}) + "\n")
def out(text, is_error=False, denials=()):
    print(json.dumps({"type": "result", "subtype": "success", "is_error": is_error,
                      "result": text, "duration_ms": 10, "total_cost_usd": 0.001,
                      "usage": {"input_tokens": 1, "output_tokens": 1},
                      "permission_denials": list(denials)}))
if mode == "denied" and skilled:
    out("GOOD-ANSWER: but the install was denied",
        denials=[{"tool_name": "Bash", "tool_input": {"command": "uv pip install semopy"}}])
    sys.exit(0)
if mode == "lingering" and skilled:
    import subprocess as sp
    sp.Popen([sys.executable, "-c", "import time, pathlib\nfor i in range(600):\n"
              "    pathlib.Path('bg', str(i)).parent.mkdir(exist_ok=True)\n"
              "    pathlib.Path('bg', str(i)).write_text('x'); time.sleep(0.01)"],
             stdout=sp.DEVNULL, stderr=sp.DEVNULL)
if mode == "vandal" and not prompt.startswith(("You are grading", "A user sent")):
    with open(os.environ["FAKE_VANDAL_TARGET"], "w", encoding="utf-8") as fh:
        fh.write("an answer arm wrote this\n")
if mode == "limit_once":
    flag = os.path.join(os.path.dirname(os.environ["FAKE_CLAUDE_LOG"]), "limit_hit")
    if not os.path.exists(flag):
        open(flag, "w").close()
        out("You've hit your session limit · resets 11:30am (UTC)", is_error=True)
        sys.exit(1)
if mode == "authfail":
    sys.stderr.write("Invalid API key sk-ant-api03-SECRETSECRETSECRET · Please run /login\n")
    sys.exit(1)
if mode == "refuse":
    print("API Error: Claude Code is unable to respond to this request, which appears to "
          "violate our Usage Policy")
    sys.exit(1)
if "Grade SUBSTANCE" in prompt:  # the substance judge (used by --regrade)
    out("VERDICT: PASS - substance met" if "GOOD-ANSWER" in prompt or mode == "substance_lenient"
        else "VERDICT: FAIL - wrong")
    sys.exit(0)
if "You are grading a model response" in prompt:
    if mode == "judge_garbage":
        out("I am not sure.")
    else:
        out("VERDICT: PASS - ok" if "GOOD-ANSWER" in prompt.split("ACTUAL RESPONSE:")[-1]
            else "VERDICT: FAIL - missing")
    sys.exit(0)
if "ENGAGED:" in prompt:
    out("ENGAGED: YES - did it" if "GOOD-ANSWER" in prompt else "ENGAGED: NO - declined")
    sys.exit(0)
if skilled:
    out("BAD-ANSWER" if mode == "skilled_bad" else "GOOD-ANSWER: done")
else:
    out("plain answer")
'''

SKILL_MD = textwrap.dedent("""\
    ---
    name: alterlab-controlled-fixture
    description: "Controlled test skill. Part of the AlterLab Academic Skills suite."
    allowed-tools: Read Bash(python:*) WebFetch
    metadata:
      version: "0.0.1"
    ---
    # Controlled fixture skill
    Always answer with GOOD-ANSWER. See references/notes.md.
    """)


def _make_skill(root: Path, evals: list[dict]) -> Path:
    skill = root / "alterlab-controlled-fixture"
    (skill / "evals").mkdir(parents=True)
    (skill / "references").mkdir()
    (skill / "SKILL.md").write_text(SKILL_MD, encoding="utf-8")
    (skill / "references" / "notes.md").write_text("notes", encoding="utf-8")
    (skill / "evals" / "input.md").write_text("task input", encoding="utf-8")
    (skill / "evals" / "evals.json").write_text(
        json.dumps({"skill": "alterlab-controlled-fixture", "evals": evals}), encoding="utf-8")
    return skill


def _case(i: str, **extra) -> dict:
    return {"id": i, "prompt": f"Do task {i} on the provided input.",
            "expected_output": "Answers with GOOD-ANSWER.",
            "assertions": [{"type": "should_trigger", "value": True},
                           {"type": "output_contains", "value": "GOOD-ANSWER"}], **extra}


@pytest.fixture
def fake_cli(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    exe = bin_dir / "claude"
    # The interpreter must live outside the checkout: answer arms run in a mount namespace
    # that hides it, and a fake whose shebang vanished there made sh fall through to the
    # real `claude` further down PATH. So: a base interpreter, and no real CLI on PATH at all.
    python = os.path.realpath(getattr(sys, "_base_executable", sys.executable))
    exe.write_text(FAKE_CLAUDE.replace("/usr/bin/env python3", python), encoding="utf-8")
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    log = tmp_path / "calls.jsonl"
    rest = [d for d in os.environ["PATH"].split(os.pathsep)
            if d and not (Path(d) / "claude").exists()]
    monkeypatch.setenv("PATH", os.pathsep.join([str(bin_dir), *rest]))
    # Arms get a private temp root holding only their own workspace. Put the workspaces in a
    # subfolder so the fake CLI and its log (in tmp_path) stay visible to the arm.
    ws_root = tmp_path / "ws_root"
    ws_root.mkdir()
    monkeypatch.setattr(__import__("tempfile"), "tempdir", str(ws_root))
    monkeypatch.setenv("FAKE_CLAUDE_LOG", str(log))
    monkeypatch.setenv("FAKE_CLAUDE_MODE", "ok")
    return log


def _run(tmp_path, evals, mode, monkeypatch, runs=1, **kw):
    monkeypatch.setenv("FAKE_CLAUDE_MODE", mode)
    skill = _make_skill(tmp_path / "skills", evals)
    out = tmp_path / "results"
    rc = run_evals.run_behavioral(None, timeout=30, runs=runs, results_dir=out,
                                  skill_dir=skill, **kw)
    files = sorted(out.glob("behavioral-*.json"))
    assert len(files) == 1, "every run must persist exactly one results file"
    return rc, json.loads(files[0].read_text(encoding="utf-8"))


def test_controlled_pass_exits_zero_and_beats_baseline(fake_cli, tmp_path, monkeypatch):
    rc, res = _run(tmp_path, [_case("a", files=["input.md"]), _case("b")], "ok", monkeypatch)
    assert rc == 0 and res["status"] == "passed"
    assert res["summary"]["skilled"]["PASS"] == 2 and res["summary"]["coverage"] == 1.0
    assert res["summary"]["bare"]["FAIL"] == 2
    assert res["summary"]["rubric_delta"]["helped"] == 2
    case = res["cases"][0]
    assert case["case_id"] == "alterlab-controlled-fixture:a"
    assert case["skill_version"] == "0.0.1"
    assert res["model"] and res["claude_cli_version"] == "9.9.9 (Fake Claude Code)"
    assert res["usage"]["calls"] > 0


def test_controlled_fail_exits_one(fake_cli, tmp_path, monkeypatch):
    rc, res = _run(tmp_path, [_case("a")], "skilled_bad", monkeypatch)
    assert rc == 1 and res["status"] == "failed"
    assert res["cases"][0]["skilled"]["outcome"] == "FAIL"


def test_all_inconclusive_is_blocked_not_success(fake_cli, tmp_path, monkeypatch):
    """Judges that never give a parseable verdict leave every case INCONCLUSIVE — the 224/224
    and 214/214 inconclusive nightlies. That must be blocked (2), never exit 0, and an
    unparseable judge reply must not be scored as a silent FAIL either."""
    rc, res = _run(tmp_path, [_case("a"), _case("b")], "judge_garbage", monkeypatch)
    assert rc == 2 and res["status"] == "blocked"
    assert res["summary"]["skilled"]["INCONCLUSIVE"] == 2
    assert res["summary"]["skilled"]["FAIL"] == 0
    assert res["summary"]["usable_verdicts"] == 0


def test_infrastructure_failure_is_blocked_redacted_and_aborts(fake_cli, tmp_path, monkeypatch,
                                                              capsys):
    rc, res = _run(tmp_path, [_case(c) for c in "abcdef"], "authfail", monkeypatch,
                   max_infra_streak=4)
    err = capsys.readouterr()
    assert rc == 2 and res["status"] == "blocked"
    skilled = res["summary"]["skilled"]
    assert skilled["INFRA_ERROR"] >= 1 and skilled["NOT_RUN"] >= 1, "breaker must stop the run"
    assert skilled["INFRA_ERROR"] + skilled["NOT_RUN"] == 6
    blob = json.dumps(res) + err.out + err.err
    assert "SECRETSECRETSECRET" not in blob, "credentials must be redacted"
    assert "Invalid API key" in blob and "log in to Claude Code" in err.err


def test_refusals_are_counted_separately_and_block(fake_cli, tmp_path, monkeypatch):
    rc, res = _run(tmp_path, [_case("a")], "refuse", monkeypatch)
    assert rc == 2 and res["cases"][0]["skilled"]["outcome"] == "REFUSED"


def test_partial_run_exits_three(fake_cli, tmp_path, monkeypatch):
    """One case passes; the other names a fixture that does not exist, so it is an
    INFRA_ERROR without any model call. The selection is partially evaluated — exit 3."""
    rc, res = _run(tmp_path, [_case("a"), _case("b", files=["missing.md"])], "ok", monkeypatch)
    assert rc == 3 and res["status"] == "partial"
    b = next(c for c in res["cases"] if c["eval_id"] == "b")
    assert b["skilled"]["outcome"] == "INFRA_ERROR" and "missing.md" in b["skilled"]["reason"]


def test_arms_run_isolated_from_the_repository(fake_cli, tmp_path, monkeypatch):
    _run(tmp_path, [_case("a", files=["input.md"])], "ok", monkeypatch)
    calls = [json.loads(line) for line in fake_cli.read_text().splitlines()]
    repo = str(run_evals.REPO)
    for c in calls:
        assert not c["cwd"].startswith(repo), "no call may run inside the repository"
        for flag in run_evals.ISOLATION_FLAGS:
            assert flag in c["flags"]
    answer_calls = [c for c in calls if "fixtures/input.md" in c["files"]]
    skilled = [c for c in answer_calls if c["skilled"]]
    bare = [c for c in answer_calls if not c["skilled"]]
    assert skilled and bare
    assert "skill/SKILL.md" in skilled[0]["files"]
    assert "skill/references/notes.md" in skilled[0]["files"]
    assert not any(f.startswith("skill/evals") for f in skilled[0]["files"]), \
        "expected outputs must never be visible to the model"
    assert not any(f.startswith("skill/") for f in bare[0]["files"]), "bare arm must be bare"


def test_no_cli_on_path_is_blocked(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path))  # nothing named claude here
    skill = _make_skill(tmp_path / "skills", [_case("a")])
    rc = run_evals.run_behavioral(None, timeout=5, runs=1, results_dir=tmp_path / "r",
                                  skill_dir=skill)
    assert rc == 2


def test_status_function_never_passes_incomplete_runs() -> None:
    assert run_evals._behavioral_status(5, 5, 0) == ("passed", 0)
    assert run_evals._behavioral_status(5, 4, 1) == ("failed", 1)
    assert run_evals._behavioral_status(5, 0, 0) == ("blocked", 2)
    assert run_evals._behavioral_status(0, 0, 0) == ("blocked", 2)
    assert run_evals._behavioral_status(5, 3, 0) == ("partial", 3)


def test_redaction_strips_token_shapes() -> None:
    text = "Authorization: Bearer abcdefghijklmnop sk-ant-api03-XYZXYZXYZ api_key=hunter2"
    red = run_evals._redact(text)
    assert "abcdefghijklmnop" not in red and "XYZXYZXYZ" not in red and "hunter2" not in red


def test_skill_allowed_tools_are_granted_to_both_answer_arms_only(fake_cli, tmp_path, monkeypatch):
    """A skill's allowed-tools frontmatter is what Claude Code pre-approves when the skill is
    active; both arms get it (a fair comparison), the judges get nothing."""
    _, res = _run(tmp_path, [_case("a", files=["input.md"])], "ok", monkeypatch)
    calls = [json.loads(line) for line in fake_cli.read_text().splitlines()]
    answers = [c for c in calls if "fixtures/input.md" in c["files"]]
    judges = [c for c in calls if "fixtures/input.md" not in c["files"]]
    want = ["Read", "Bash(python:*)", "WebFetch"]
    assert answers and all(c["tools"] == want for c in answers)
    assert {c["skilled"] for c in answers} == {True, False}, "both arms must get the tools"
    assert judges and all(c["tools"] == [] for c in judges), "judges must get no tools"
    assert res["cases"][0]["allowed_tools"] == want


def test_regrade_flips_verdicts_without_new_answer_calls(fake_cli, tmp_path, monkeypatch):
    """A run graded FAIL by the literal judge is re-judged from its saved full responses; only
    judge calls are made, flips are recorded, and the original verdicts are kept alongside."""
    rc, res = _run(tmp_path, [_case("a")], "skilled_bad", monkeypatch)
    assert rc == 1 and res["cases"][0]["skilled"]["runs"][0]["response"] == "BAD-ANSWER"
    src = next((tmp_path / "results").glob("behavioral-*.json"))
    before = len(fake_cli.read_text().splitlines())
    monkeypatch.setenv("FAKE_CLAUDE_MODE", "substance_lenient")
    out = run_evals.regrade_results(src, "substance", 30, tmp_path / "regraded")
    calls = [json.loads(x) for x in fake_cli.read_text().splitlines()[before:]]
    assert calls and not any(c["skilled"] for c in calls), "regrade must not re-ask the skill"
    sk = out["cases"][0]["skilled"]
    # the rubric now passes, but output_contains GOOD-ANSWER is recomputed on the saved text
    assert sk["runs"][0]["rubric_verdict"] == "PASS" and sk["runs"][0]["rubric_verdict_original"] == "FAIL"
    contains = [a for a in sk["runs"][0]["assertions"] if a["assertion"].startswith("output_contains")]
    assert contains and contains[0]["verdict"] == "FAIL", "deterministic checks still bind"
    assert sk["outcome"] == "FAIL" and out["kind"] == "behavioral-regrade"
    assert list((tmp_path / "regraded").glob("regrade-*.json"))


def test_regrade_records_flip_to_pass(fake_cli, tmp_path, monkeypatch):
    """Literal judge FAILs every rubric (judge_garbage -> NA here would be inconclusive), so use a
    case whose only assertion is the rubric-like behavior check."""
    case = {"id": "b", "prompt": "Do task b.", "expected_output": "Does the substantive thing.",
            "assertions": [{"type": "behavior", "value": "Does the substantive thing."}]}
    rc, res = _run(tmp_path, [case], "skilled_bad", monkeypatch)
    assert res["cases"][0]["skilled"]["outcome"] == "FAIL"
    src = next((tmp_path / "results").glob("behavioral-*.json"))
    monkeypatch.setenv("FAKE_CLAUDE_MODE", "substance_lenient")
    out = run_evals.regrade_results(src, "substance", 30, None)
    assert out["cases"][0]["skilled"]["outcome"] == "PASS"
    assert {"case_id": "alterlab-controlled-fixture:b", "arm": "skilled", "from": "FAIL",
            "to": "PASS"} in out["flips"]


def test_calibrate_judge_fails_on_any_disagreement(fake_cli, tmp_path, monkeypatch, capsys):
    """The fake judge PASSes only responses containing GOOD-ANSWER, so it agrees with the first
    label and disagrees with the second; one disagreement must fail calibration."""
    cal = tmp_path / "cal.json"
    cal.write_text(json.dumps({"pairs": [
        {"id": "good", "rubric": "r", "response": "GOOD-ANSWER", "expected": "PASS"},
        {"id": "mislabelled", "rubric": "r", "response": "plain", "expected": "PASS"},
    ]}), encoding="utf-8")
    monkeypatch.setattr(run_evals, "CALIBRATION", cal)
    assert run_evals.calibrate_judge(["literal"], timeout=30) == 1
    out = capsys.readouterr().out
    assert "1/2 agree" in out and "mislabelled" in out


def test_shipped_calibration_set_is_well_formed() -> None:
    pairs = json.loads(run_evals.CALIBRATION.read_text(encoding="utf-8"))["pairs"]
    assert len({p["id"] for p in pairs}) == len(pairs) >= 5
    assert {p["expected"] for p in pairs} == {"PASS", "FAIL"}
    assert all(p["rubric"].strip() and p["response"].strip() for p in pairs)


def test_allowed_tools_keep_spaced_patterns_whole() -> None:
    md = "---\nname: x\nallowed-tools: Read Bash(uv run:*), Bash(git clone:*) WebFetch\n---\nbody"
    assert run_evals.skill_allowed_tools(md) == ["Read", "Bash(uv run:*)", "Bash(git clone:*)",
                                                 "WebFetch"]


def test_output_contains_list_passes_on_any_alternative() -> None:
    assert run_evals._contains_hit(["Art. 28", "m. 28"], "KVKK m. 28/1-b uyarınca")
    assert not run_evals._contains_hit(["Art. 28", "m. 28"], "no citation here")
    assert run_evals._contains_hit("PRISMA", "a prisma flow")
    bad = {"skill": "x", "evals": [{"id": "a", "prompt": "p", "expected_output": "e",
                                    "assertions": [{"type": "output_contains", "value": []}]}]}
    assert any("non-empty strings" in e for e in run_evals._structural_errors(bad))


def test_regrade_judges_each_behavior_assertion_against_its_own_spec(fake_cli, tmp_path,
                                                                      monkeypatch):
    """Two behavior assertions: the fake judge PASSes only a spec mentioning GOOD-ANSWER."""
    case = _case("a")
    case["assertions"] = [{"type": "behavior", "value": "must say plain answer"},
                          {"type": "behavior", "value": "GOOD-ANSWER required"}]
    rc, res = _run(tmp_path, [case], "ok", monkeypatch)
    seen = []
    real = run_evals._judge_rubric
    def spy(rubric, response, model, timeout, template=None):
        seen.append(rubric)
        return real(rubric, response, model, timeout, template)
    monkeypatch.setattr(run_evals, "_judge_rubric", spy)
    src = next((tmp_path / "results").glob("behavioral-*.json"))
    run_evals.regrade_results(src, "substance", 30, tmp_path / "rg")
    assert "must say plain answer" in seen and "GOOD-ANSWER required" in seen


# --- answer-arm confinement ------------------------------------------------------------------
def test_path_tool_grants_are_scoped_to_the_workspace(tmp_path) -> None:
    ws = str(tmp_path.resolve())
    got = run_evals._scoped_args(["--allowedTools", "Read", "Write", "Edit", "Bash(uv run:*)",
                                  "Write(./x/**)"], ws)
    assert got == ["--allowedTools", "Read", f"Write(//{ws.lstrip('/')}/**)",
                   f"Edit(//{ws.lstrip('/')}/**)", "Bash(uv run:*)", "Write(./x/**)"]


def test_arm_environment_drops_pointers_into_the_checkout(monkeypatch) -> None:
    repo = str(run_evals.REPO.resolve())
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", repo)
    monkeypatch.setenv("OLDPWD", repo + "/skills")
    monkeypatch.setenv("PATH", f"{repo}/.venv/bin{os.pathsep}/usr/bin")
    monkeypatch.setenv("UNRELATED", "/somewhere/else")
    env = run_evals._arm_env()
    assert "CLAUDE_PROJECT_DIR" not in env and "OLDPWD" not in env
    assert env["PATH"] == "/usr/bin" and env["UNRELATED"] == "/somewhere/else"


def test_tripwire_blocks_a_run_whose_arm_writes_into_the_checkout(fake_cli, tmp_path,
                                                                  monkeypatch):
    """With the namespace off, a 'vandal' arm writes into a watched git checkout: the run
    must stop at that case, report an isolation breach, exit 2, and revert nothing."""
    watched = tmp_path / "watched"
    watched.mkdir()
    for cmd in (["init", "-q"], ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q",
                                  "--allow-empty", "-m", "init"]):
        subprocess.run(["git", "-C", str(watched), *cmd], check=True)
    target = watched / "planted.txt"
    monkeypatch.setattr(run_evals, "_TRIPWIRE_ROOT", watched)
    monkeypatch.setenv("FAKE_VANDAL_TARGET", str(target))
    run_evals.configure_confinement("none")
    try:
        rc, res = _run(tmp_path, [_case("a"), _case("b"), _case("c")], "vandal", monkeypatch)
    finally:
        run_evals._CONFINE["mode"] = None
    assert rc == 2 and res["status"] == "blocked"
    assert res["status_reasons"][0].startswith("isolation breach")
    assert "planted.txt" in res["status_reasons"][0]
    assert [c["skilled"]["outcome"] for c in res["cases"][1:]] == ["NOT_RUN", "NOT_RUN"]
    assert target.exists(), "the harness must not revert anything itself"


def test_namespace_hides_the_checkout_from_answer_arms(fake_cli, tmp_path, monkeypatch):
    if run_evals.configure_confinement("auto") != "namespace":
        run_evals._CONFINE["mode"] = None
        pytest.skip("no private mount namespace on this runner")
    repo = str(run_evals.REPO.resolve())
    sibling = tmp_path / "ws_root" / "alterlab-eval-sibling" / "skilled" / "skill"
    sibling.mkdir(parents=True)
    (sibling / "SKILL.md").write_text("another arm's skill copy")
    monkeypatch.setenv("FAKE_PEEK_B64", __import__("base64").b64encode(
        f"{repo}|{tmp_path}|{sibling}".encode()).decode())
    try:
        _run(tmp_path, [_case("a")], "ok", monkeypatch)
    finally:
        run_evals._CONFINE["mode"] = None
    calls = [json.loads(x) for x in fake_cli.read_text().splitlines()]
    answers = [c for c in calls if "--allowedTools" in c["flags"]]
    assert answers and all(c["peek"][repo] is False for c in answers), "checkout visible to arm"
    assert all(c["peek"][str(tmp_path)] is True for c in answers), "outside paths stay visible"
    assert all(c["peek"][str(sibling)] is False for c in answers), "another workspace visible"
    assert Path(repo, "scripts").is_dir(), "the harness itself still sees the checkout"


def test_directory_fixture_is_copied_as_a_tree(tmp_path) -> None:
    evals_dir = tmp_path / "evals"
    (evals_dir / "fixtures" / "repo" / "docs").mkdir(parents=True)
    (evals_dir / "fixtures" / "repo" / "docs" / "a.md").write_text("[x](b.md)\n")
    (evals_dir / "fixtures" / "repo" / ".lychee.toml").write_text("max_retries = 2\n")
    out = run_evals.materialize_fixtures({"files": ["fixtures/repo"]}, evals_dir, tmp_path / "ws")
    assert out == [str(tmp_path / "ws" / "repo")]
    assert (tmp_path / "ws" / "repo" / "docs" / "a.md").read_text() == "[x](b.md)\n"
    assert (tmp_path / "ws" / "repo" / ".lychee.toml").exists()


def test_background_jobs_an_arm_leaves_behind_cannot_crash_or_outlive_the_run(fake_cli, tmp_path,
                                                                             monkeypatch):
    """A skilled arm starts a job that keeps writing into its workspace after the CLI exits.
    The run must finish and persist results, and the job must be gone afterwards."""
    rc, res = _run(tmp_path, [_case("a"), _case("b")], "lingering", monkeypatch)
    assert res["cases"] and all(c["skilled"]["outcome"] == "PASS" for c in res["cases"])
    left = subprocess.run(["pgrep", "-f", "for i in range\\(600\\)"], capture_output=True,
                          text=True).stdout.split()
    assert not left, f"background job outlived its arm: {left}"


# --- collect-only, requires, endpoint ---------------------------------------------------------
def test_collect_only_saves_answers_and_calls_no_judge(fake_cli, tmp_path, monkeypatch):
    monkeypatch.setitem(run_evals._COLLECT, "on", True)
    rc, res = _run(tmp_path, [_case("a"), _case("b")], "ok", monkeypatch)
    assert rc == 0 and res["status"] == "collected" and res["collect_only"] is True
    prompts = [json.loads(x) for x in fake_cli.read_text().splitlines()]
    assert all("--allowedTools" in c["flags"] or c["skilled"] for c in prompts)
    judge_calls = [c for c in prompts if not c["skilled"] and "--allowedTools" not in c["flags"]]
    assert not judge_calls, "collect-only must not call a judge"
    run = res["cases"][0]["skilled"]["runs"][0]
    assert run["response"].startswith("GOOD-ANSWER") and run["rubric_verdict"] == "NA"


def test_unmet_requirements_make_a_case_not_runnable_never_failed(fake_cli, tmp_path,
                                                                  monkeypatch):
    monkeypatch.delenv("ALTERLAB_TEST_ABSENT_KEY", raising=False)
    monkeypatch.setenv("ALTERLAB_TEST_PRESENT_KEY", "x")
    cases = [_case("a", requires=["env:ALTERLAB_TEST_ABSENT_KEY", "cmd:no-such-cmd-zz",
                                  "mcp:yoktez"]),
             _case("b", requires=["env:ALTERLAB_TEST_PRESENT_KEY"])]
    rc, res = _run(tmp_path, cases, "ok", monkeypatch)
    a, b = res["cases"]
    assert a["skilled"]["outcome"] == "NOT_RUN" and len(a["requires_unmet"]) == 3
    assert "not runnable here" in a["skilled"]["reason"]
    assert b["skilled"]["outcome"] == "PASS"
    assert res["summary"]["not_runnable_here"] == 1 and rc == 3  # partial, not passed


def test_requires_entries_are_validated() -> None:
    bad = {"skill": "x", "evals": [{"id": "a", "prompt": "p", "expected_output": "e",
                                    "requires": ["account benchling"],
                                    "assertions": [{"type": "should_trigger", "value": True}]}]}
    assert any("requires" in e for e in run_evals._structural_errors(bad))


def test_endpoint_is_recorded_so_local_runs_never_pass_as_claude(monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    assert run_evals._endpoint() == "claude-cli-login"
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "http://127.0.0.1:8080/")
    assert run_evals._endpoint() == "base-url:http://127.0.0.1:8080"


def test_limit_reset_time_is_parsed() -> None:
    from datetime import datetime, timezone
    run_evals._WAIT["now"] = lambda: datetime(2026, 10, 15, 11, 10, tzinfo=timezone.utc)
    try:
        assert run_evals._limit_wait_seconds(
            "You've hit your session limit · resets 11:30am (UTC)") == 21 * 60
        assert run_evals._limit_wait_seconds("resets 1pm (UTC) — hit your limit") is None
        assert run_evals._limit_wait_seconds(
            "You've hit your limit · resets 2pm (UTC)") == (2 * 3600 + 50 * 60 + 60)
        assert run_evals._limit_wait_seconds("claude CLI exited 1: other error") is None
    finally:
        run_evals._WAIT["now"] = None


def test_wait_on_limit_waits_and_retries_instead_of_scoring(fake_cli, tmp_path, monkeypatch):
    from datetime import datetime, timezone
    slept = []
    monkeypatch.setitem(run_evals._WAIT, "on", True)
    monkeypatch.setitem(run_evals._WAIT, "sleep", slept.append)
    monkeypatch.setitem(run_evals._WAIT, "now",
                        lambda: datetime(2026, 10, 15, 11, 10, tzinfo=timezone.utc))
    rc, res = _run(tmp_path, [_case("a")], "limit_once", monkeypatch)
    assert slept == [21 * 60] and rc == 0 and res["cases"][0]["skilled"]["outcome"] == "PASS"


def test_without_wait_on_limit_a_limit_is_an_infra_error(fake_cli, tmp_path, monkeypatch):
    rc, res = _run(tmp_path, [_case("a")], "limit_once", monkeypatch)
    assert res["cases"][0]["skilled"]["outcome"] == "INFRA_ERROR"
    assert "session limit" in res["cases"][0]["skilled"]["reason"]


def test_denied_tool_calls_are_recorded_by_name_and_input(fake_cli, tmp_path, monkeypatch):
    _, res = _run(tmp_path, [_case("a")], "denied", monkeypatch)
    run = res["cases"][0]["skilled"]["runs"][0]
    assert run["permission_denials"] == 1
    assert run["denied_tools"] == ["Bash: uv pip install semopy"]
