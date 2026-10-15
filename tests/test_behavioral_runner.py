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
import stat
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
                          "skilled": skilled, "files": sorted(
                              os.path.relpath(os.path.join(r, f), cwd)
                              for r, _, fs in os.walk(cwd) for f in fs)}) + "\n")
def out(text, is_error=False):
    print(json.dumps({"type": "result", "subtype": "success", "is_error": is_error,
                      "result": text, "duration_ms": 10, "total_cost_usd": 0.001,
                      "usage": {"input_tokens": 1, "output_tokens": 1}}))
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
    exe.write_text(FAKE_CLAUDE.replace("/usr/bin/env python3", sys.executable), encoding="utf-8")
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    log = tmp_path / "calls.jsonl"
    monkeypatch.setenv("PATH", f"{bin_dir}:{__import__('os').environ['PATH']}")
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
