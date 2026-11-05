"""Tests for ``scripts/check_workflow_run.py``, the checker for live dynamic-workflow runs.

Every payload here comes from the MOCKED runtime (``scripts/workflow_dryrun.mjs``), driven by each
fixture's ``args.json`` and ``mock-scenario.json`` plus injected faults; the output files are
written by the tests. Nothing here is a live run: these tests show that the checker accepts a
consistent run, reports a partial or blocked run as incomplete, and fails a run whose payload,
files, or report disagree — and that a mock payload can never be recorded as live.

Skipped when Node.js is not installed.
"""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_workflow_run as cwr  # noqa: E402

DRYRUN = REPO_ROOT / "scripts" / "workflow_dryrun.mjs"
CHECKER = REPO_ROOT / "scripts" / "check_workflow_run.py"
SCRIPTS = REPO_ROOT / "skills" / "workflows" / "workflows"
FX = cwr.FIXTURES
NODE = shutil.which("node")
WORKFLOWS = list(cwr.WORKFLOWS)

needs_node = pytest.mark.skipif(NODE is None, reason="Node.js not installed")

# One agent per workflow whose failure (null on the call and on its retry) leaves work unfinished.
NULL_FAULT = {
    "citation-audit": "^claims batch 1",
    "review-panel": "^Devil's-advocate reviewer",
    "claim-stress-test": "^C2 · inference",
    "rebuttal": "^R2\\.2",
    "grant-mock-panel": "^check secondary",
    "literature-map": "^gap: Feedback",
    "systematic-review-screening": "^adjudication 1",
}


# ---------------------------------------------------------------- helpers
def expect(workflow: str) -> dict:
    return json.loads((FX / workflow / "expect.json").read_text(encoding="utf-8"))


def scenario_rules(workflow: str, out_dir: Path) -> list[dict]:
    raw = json.loads((FX / workflow / "mock-scenario.json").read_text(encoding="utf-8"))
    return cwr.substitute(raw, str(out_dir))["rules"]


def dryrun(workflow: str, out_dir: Path, extra: list[dict] | None = None, *, scenario: bool = True, mode: str = "a") -> dict:
    """Mock-run a workflow on its fixture args; ``extra`` rules go first (the first "return" wins)."""
    args = cwr.fixture_args(workflow, str(out_dir))
    rules = list(extra or []) + (scenario_rules(workflow, out_dir) if scenario else [])
    cmd = [NODE, str(DRYRUN), str(SCRIPTS / f"{workflow}.js"), json.dumps(args), mode]
    if rules:
        cmd.append(json.dumps({"rules": rules}))
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=REPO_ROOT)
    return json.loads((proc.stdout.strip().splitlines() or ["{}"])[-1])


def null_rule(match: str) -> dict:
    return {"match": match, "action": "null"}


def confirm_says(status: str, **values: object) -> dict:
    return {"match": "^confirm report on disk", "action": "set", "values": {"states_status": status, **values}}


def write_outputs(workflow: str, out_dir: Path, payload: dict, *, status: str | None = None, skip: tuple[str, ...] = ()) -> None:
    """Write the deliverables a consistent run would leave: each file the fixture declares."""
    out_dir.mkdir(parents=True, exist_ok=True)
    stated = (status or payload["status"]).upper()
    for spec in expect(workflow)["outputs"]:
        name = spec.get("path") or spec["glob"].replace("*", "core")
        if name in skip:
            continue
        if spec["type"] == "md":
            text = f"# Synthetic test output for {workflow}\n\nStatus: {stated}\n\n| stage | requested |\n|---|---|\n"
        else:
            rule = spec.get("count_equals")
            n = 1 if rule is None else cwr._expected_count(rule, payload)
            text = "".join(json.dumps({"sid": i + 1, "title": f"record {i + 1}"}) + "\n" for i in range(n))
        (out_dir / name).write_text(text, encoding="utf-8")


def verdict(workflow: str, raw: dict, out_dir: Path, **kw: object) -> dict:
    return cwr.check_payload(workflow, raw, out_dir, **kw)


def by_name(v: dict) -> dict[str, dict]:
    return {c["name"]: c for c in v["checks"]}


def failed(v: dict) -> list[str]:
    return [f"{c['name']}: {c['detail']}" for c in v["checks"] if c["verdict"] == "FAIL"]


def scrub_mock_text(payload: dict) -> dict:
    """A payload with the mock runtime's tell-tale text replaced, as a live run would read."""
    p = copy.deepcopy(payload)
    for key in ("summary", "decision"):
        if p.get(key) == "mock agent text":
            p[key] = "Two-sentence summary written by the report agent."
    return p


# ---------------------------------------------------------------- the fixtures themselves
@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_fixture_is_complete_and_inputs_exist(workflow: str) -> None:
    d = FX / workflow
    for name in ("args.json", "expect.json", "mock-scenario.json"):
        assert (d / name).is_file(), f"{workflow}: missing {name}"
    exp = expect(workflow)
    assert exp["workflow"] == workflow
    assert any(o.get("role") == "report" and o.get("path") == exp["report"] for o in exp["outputs"])
    raw_args = (d / "args.json").read_text(encoding="utf-8")
    assert cwr.PLACEHOLDER in raw_args, "outputs must go to the caller-supplied ${OUT_DIR}"
    args = cwr.fixture_args(workflow, "/tmp/out")
    assert cwr.PLACEHOLDER not in json.dumps(args)
    for key in ("path", "manuscript", "reviews", "records"):
        if isinstance(args.get(key), str):
            assert (REPO_ROOT / args[key]).is_file(), f"{workflow}: {key} {args[key]} does not exist"
    assert "MOCK RUNTIME SCENARIO" in json.loads((d / "mock-scenario.json").read_text(encoding="utf-8"))["_comment"]


def test_synthetic_inputs_are_labelled_synthetic() -> None:
    inputs = [p for p in FX.rglob("*") if p.is_file() and p.suffix in {".md", ".csv"}]
    assert len(inputs) >= 3
    for p in inputs:
        head = p.read_text(encoding="utf-8")[:400].upper()
        assert "SYNTHETIC" in head, f"{p.relative_to(REPO_ROOT)} is not labelled synthetic in its header"
    grant = cwr.fixture_args("grant-mock-panel", "/tmp/out")["path"]
    assert "Fictional application" in (REPO_ROOT / grant).read_text(encoding="utf-8")


@needs_node
@pytest.mark.parametrize("mode", ["a", "b", "mixed"])
@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_fixture_args_run_through_the_dry_run(workflow: str, mode: str, tmp_path: Path) -> None:
    out = dryrun(workflow, tmp_path, scenario=False, mode=mode)
    assert out.get("ok"), f"{workflow} [{mode}]: {out.get('error')}"
    assert out["result"]["status"] in cwr.STATUSES


@needs_node
@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_mock_scenario_is_complete_and_matches_the_documented_agent_count(workflow: str, tmp_path: Path) -> None:
    out = dryrun(workflow, tmp_path)
    assert out.get("ok"), out.get("error")
    assert out["result"]["status"] == "complete", out["result"]["status_reasons"]
    assert out["agents"] == expect(workflow)["mock_agent_count"]
    doc = (REPO_ROOT / "docs" / "workflow-validation.md").read_text(encoding="utf-8")
    assert f"| `{workflow}` | {out['agents']} |" in doc, "docs/workflow-validation.md must list the mock-derived agent count"


# ---------------------------------------------------------------- consistent mock runs
@needs_node
@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_consistent_mock_run_passes_and_is_labelled_mock(workflow: str, tmp_path: Path) -> None:
    raw = dryrun(workflow, tmp_path)
    write_outputs(workflow, tmp_path, raw["result"])
    v = verdict(workflow, raw, tmp_path)
    assert not failed(v), failed(v)
    assert v["overall"] == "pass"
    assert v["live"] is False and v["provenance"] == "mock" and v["mock_markers"]
    assert {f["path"] for f in v["files"]} >= {expect(workflow)["report"]}
    assert all(len(f["sha256"]) == 64 and f["bytes"] > 0 for f in v["files"] if f["path"] != "unresolved.jsonl")


@needs_node
@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_null_agent_is_reported_partial_and_checker_says_incomplete(workflow: str, tmp_path: Path) -> None:
    extra = [null_rule(NULL_FAULT[workflow]), confirm_says("PARTIAL")]
    if workflow == "systematic-review-screening":  # sid 6 is unresolved, so 2 included and 1 unresolved line
        extra[1]["values"]["others"] = [
            {"path": f"{tmp_path}/included.jsonl", "exists": True, "lines": 2},
            {"path": f"{tmp_path}/unresolved.jsonl", "exists": True, "lines": 1},
        ]
    raw = dryrun(workflow, tmp_path, extra)
    assert raw.get("ok"), raw.get("error")
    p = raw["result"]
    assert p["status"] == "partial" and p["status_reasons"], p
    write_outputs(workflow, tmp_path, p)
    v = verdict(workflow, raw, tmp_path)
    assert not failed(v), failed(v)
    assert v["overall"] == "incomplete"
    checks = by_name(v)
    assert checks["incomplete_work_visible"]["verdict"] == "PASS"
    assert "unfinished work" in checks["incomplete_work_visible"]["detail"]


@needs_node
@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_partial_payload_relabelled_complete_fails(workflow: str, tmp_path: Path) -> None:
    """Unfinished work reported as complete is the failure the checker exists to catch."""
    extra = [null_rule(NULL_FAULT[workflow])]
    raw = dryrun(workflow, tmp_path, extra)
    p = copy.deepcopy(raw["result"])
    p["status"], p["status_reasons"] = "complete", []
    if p.get("coverage", {}).get("report", {}).get("read_back"):
        p["coverage"]["report"]["read_back"]["states_status"] = "COMPLETE"
    write_outputs(workflow, tmp_path, p)
    v = verdict(workflow, p, tmp_path)
    assert v["overall"] == "fail"
    assert by_name(v)["incomplete_work_visible"]["verdict"] == "FAIL"


@needs_node
@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_report_that_cannot_be_read_back_is_blocked(workflow: str, tmp_path: Path) -> None:
    raw = dryrun(workflow, tmp_path, [null_rule("^confirm report on disk")])
    p = raw["result"]
    assert p["status"] == "blocked" and p["report"] is None and p["status_reasons"]
    v = verdict(workflow, raw, tmp_path)  # nothing written to the out dir
    assert not failed(v), failed(v)
    assert v["overall"] == "incomplete"
    checks = by_name(v)
    assert checks["status_consistent"]["verdict"] == "PASS"
    assert checks["report_path"]["verdict"] == "NA"
    assert checks[f"file:{expect(workflow)['report']}"]["verdict"] == "NA"


@needs_node
def test_blocked_run_whose_unconfirmed_file_claims_complete_fails(tmp_path: Path) -> None:
    raw = dryrun("citation-audit", tmp_path, [null_rule("^confirm report on disk")])
    write_outputs("citation-audit", tmp_path, raw["result"], status="complete")
    v = verdict("citation-audit", raw, tmp_path)
    assert by_name(v)["report_states_payload_status"]["verdict"] == "FAIL"


# ---------------------------------------------------------------- output files
@pytest.fixture
def screening_run(tmp_path: Path) -> tuple[dict, Path]:
    if NODE is None:
        pytest.skip("Node.js not installed")
    raw = dryrun("systematic-review-screening", tmp_path)
    write_outputs("systematic-review-screening", tmp_path, raw["result"])
    return raw, tmp_path


def test_good_out_dir_passes(screening_run) -> None:
    raw, out = screening_run
    v = verdict("systematic-review-screening", raw, out)
    assert v["overall"] == "pass", failed(v)
    assert by_name(v)["file:unresolved.jsonl"]["verdict"] == "PASS"  # empty is allowed: no unresolved records
    assert (out / "unresolved.jsonl").read_text() == ""


@pytest.mark.parametrize("case", ["missing", "empty", "no_heading", "bad_jsonl", "line_count", "status_mismatch", "no_status_line"])
def test_bad_out_dir_fails(screening_run, case: str) -> None:
    raw, out = screening_run
    target = {
        "missing": "file:codebook.md", "empty": "file:prisma-screening.md", "no_heading": "file:codebook.md",
        "bad_jsonl": "file:records.jsonl", "line_count": "file:included.jsonl",
        "status_mismatch": "report_states_payload_status", "no_status_line": "report_states_payload_status",
    }[case]
    if case == "missing":
        (out / "codebook.md").unlink()
    elif case == "empty":
        (out / "prisma-screening.md").write_text("")
    elif case == "no_heading":
        (out / "codebook.md").write_text("I1 include: undergraduates\nE1 exclude: K-12\n")
    elif case == "bad_jsonl":
        (out / "records.jsonl").write_text('{"sid": 1}\n{"sid": 2,\n')
    elif case == "line_count":
        (out / "included.jsonl").write_text('{"sid": 1}\n')  # the payload includes three records
    elif case == "status_mismatch":
        (out / "prisma-screening.md").write_text("# PRISMA screening\n\nStatus: PARTIAL\n")
    else:
        (out / "prisma-screening.md").write_text("# PRISMA screening\n\nAll records were screened.\n")
    v = verdict("systematic-review-screening", raw, out)
    assert v["overall"] == "fail"
    assert by_name(v)[target]["verdict"] == "FAIL", by_name(v)[target]


def test_read_back_that_disagrees_with_the_file_fails(screening_run) -> None:
    raw, out = screening_run
    raw = copy.deepcopy(raw)
    raw["result"]["coverage"]["report"]["read_back"]["states_status"] = "PARTIAL"
    v = verdict("systematic-review-screening", raw, out)
    assert by_name(v)["read_back_matches_file"]["verdict"] == "FAIL"


@needs_node
def test_status_downgraded_after_the_report_was_written_is_caught(tmp_path: Path) -> None:
    """The workflow writes "Status: COMPLETE", then the companion-file read-back turns the run
    partial; the report on disk still says COMPLETE. The script cannot see that, the checker can."""
    wrong_lines = confirm_says("COMPLETE", others=[
        {"path": f"{tmp_path}/included.jsonl", "exists": True, "lines": 1},
        {"path": f"{tmp_path}/unresolved.jsonl", "exists": True, "lines": 0},
    ])
    raw = dryrun("systematic-review-screening", tmp_path, [wrong_lines])
    p = raw["result"]
    assert p["status"] == "partial" and any("included.jsonl" in r for r in p["status_reasons"])
    write_outputs("systematic-review-screening", tmp_path, p, status="complete")  # what the writer was told
    v = verdict("systematic-review-screening", raw, tmp_path)
    assert by_name(v)["report_states_payload_status"]["verdict"] == "FAIL"
    assert v["overall"] == "fail"


def test_complete_payload_with_a_null_companion_file_fails(screening_run) -> None:
    raw, out = screening_run
    raw = copy.deepcopy(raw)
    raw["result"]["files"]["included"] = None
    v = verdict("systematic-review-screening", raw, out)
    assert by_name(v)["payload_file:files.included"]["verdict"] == "FAIL"


def test_csv_outputs_are_parsed_with_their_columns(tmp_path: Path) -> None:
    exp = {"workflow": "citation-audit", "report": "r.md", "outputs": [{"path": "t.csv", "type": "csv", "columns": ["sid", "decision"]}]}
    exp_path = tmp_path / "expect.json"
    exp_path.write_text(json.dumps(exp))
    payload = {"status": "blocked", "status_reasons": ["test"], "report": None, "coverage": {}}

    def run(text: str) -> str:
        (tmp_path / "t.csv").write_text(text)
        return by_name(verdict("citation-audit", payload, tmp_path, expect_path=exp_path))["file:t.csv"]["verdict"]

    assert run("sid,decision,reason\n1,include,RCT\n2,exclude,K-12\n") == "PASS"
    assert run("sid,reason\n1,RCT\n") == "FAIL"  # a declared column is missing
    assert run("sid,decision\n1,include,extra,fields\n") == "FAIL"  # ragged row
    assert run("") == "FAIL"  # empty


# ---------------------------------------------------------------- accounting invariants
@pytest.fixture
def ca_run(tmp_path: Path) -> tuple[dict, Path]:
    if NODE is None:
        pytest.skip("Node.js not installed")
    raw = dryrun("citation-audit", tmp_path)
    write_outputs("citation-audit", tmp_path, raw["result"])
    return copy.deepcopy(raw["result"]), tmp_path


def test_count_above_its_denominator_fails(ca_run) -> None:
    p, out = ca_run
    p["counts"]["claims_checked"] = p["counts"]["claims_checkable"] + 1
    v = verdict("citation-audit", p, out)
    assert by_name(v)["ca_claim_denominators"]["verdict"] == "FAIL"


def test_unchecked_reference_also_counted_as_checked_fails(ca_run) -> None:
    p, out = ca_run
    p["unchecked"]["references_without_verdict"] = ["R3"]  # but references_with_verdict still counts all 3
    p["status"], p["status_reasons"] = "partial", ["1 of 3 references have no verification verdict"]
    v = verdict("citation-audit", p, out)
    assert by_name(v)["ca_references_checked_plus_unchecked"]["verdict"] == "FAIL"


def test_stage_arithmetic_that_does_not_add_up_fails(ca_run) -> None:
    p, out = ca_run
    p["coverage"]["references"]["unresolved"] = 1  # requested 3, completed 3
    v = verdict("citation-audit", p, out)
    assert by_name(v)["coverage_accounting"]["verdict"] == "FAIL"


def test_retired_fabrication_count_is_rejected(ca_run) -> None:
    p, out = ca_run
    p["counts"]["TF"] = 1
    v = verdict("citation-audit", p, out)
    assert by_name(v)["payload_schema"]["verdict"] == "FAIL"
    assert "counts.TF" in by_name(v)["payload_schema"]["detail"]


@needs_node
def test_included_record_that_is_also_unresolved_fails(tmp_path: Path) -> None:
    raw = dryrun("systematic-review-screening", tmp_path)
    p = copy.deepcopy(raw["result"])
    p["unresolved"] = [{"sid": p["included_sids"][0], "reason": "adjudication did not complete"}]
    v = verdict("systematic-review-screening", p, tmp_path)
    assert by_name(v)["srs_unresolved_not_included"]["verdict"] == "FAIL"


@needs_node
def test_claim_rated_survives_with_a_missing_lens_fails(tmp_path: Path) -> None:
    raw = dryrun("claim-stress-test", tmp_path)
    p = copy.deepcopy(raw["result"])
    p["claims"][0].update(rating="survives", lenses_completed=2, lenses_missing=["inference"])
    v = verdict("claim-stress-test", p, tmp_path)
    assert by_name(v)["cst_survives_needs_all_lenses"]["verdict"] == "FAIL"


@needs_node
def test_consistency_pass_that_did_not_run_must_not_report_zero_issues(tmp_path: Path) -> None:
    raw = dryrun("rebuttal", tmp_path)
    p = copy.deepcopy(raw["result"])
    p["consistency_checked"], p["consistency_issues"] = False, 0
    v = verdict("rebuttal", p, tmp_path)
    assert by_name(v)["rb_consistency_not_run_is_not_zero"]["verdict"] == "FAIL"


@needs_node
def test_grant_mean_is_recomputed(tmp_path: Path) -> None:
    raw = dryrun("grant-mock-panel", tmp_path)
    p = copy.deepcopy(raw["result"])
    assert p["overall_mean"] == 3.8  # (3 + 4 + 3 + 5) / 4, computed in the workflow
    p["overall_mean"] = 2.0
    v = verdict("grant-mock-panel", p, tmp_path)
    assert by_name(v)["gmp_overall_mean_recomputed"]["verdict"] == "FAIL"


# ---------------------------------------------------------------- mock is never live
@needs_node
def test_dry_run_output_is_refused_as_live(tmp_path: Path) -> None:
    raw = dryrun("review-panel", tmp_path)
    write_outputs("review-panel", tmp_path, raw["result"])
    with pytest.raises(cwr.CannotCheck, match="refusing to mark this result live"):
        verdict("review-panel", raw, tmp_path, live=True)
    with pytest.raises(cwr.CannotCheck, match="mock agent text"):
        verdict("review-panel", raw["result"], tmp_path, live=True)  # unwrapped payload, same text


@needs_node
def test_fake_placeholder_values_are_refused_as_live(tmp_path: Path) -> None:
    raw = dryrun("literature-map", tmp_path, scenario=False)  # plain mock: s0/s1/s2 strings
    p = scrub_mock_text(raw["result"])
    with pytest.raises(cwr.CannotCheck, match="placeholder strings"):
        verdict("literature-map", p, tmp_path, live=True)


@needs_node
def test_live_comes_only_from_the_flag(tmp_path: Path) -> None:
    raw = dryrun("rebuttal", tmp_path)
    p = scrub_mock_text(raw["result"])
    write_outputs("rebuttal", tmp_path, p)
    assert cwr.mock_markers(p, False) == []
    assert verdict("rebuttal", p, tmp_path)["live"] is False
    v = verdict("rebuttal", p, tmp_path, live=True, runtime_s=12.5, cost_usd=0.9, agents=8)
    assert v["live"] is True and v["provenance"] == "live"
    assert (v["runtime_s"], v["cost_usd"], v["agents"], v["agents_reported"]) == (12.5, 0.9, 8, 8)


# ---------------------------------------------------------------- CLI
def cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(CHECKER), *args], capture_output=True, text=True, timeout=60, cwd=REPO_ROOT)


def test_print_args_substitutes_the_out_dir(tmp_path: Path) -> None:
    proc = cli("--workflow", "rebuttal", "--out-dir", str(tmp_path), "--print-args")
    assert proc.returncode == 0
    assert json.loads(proc.stdout)["out_dir"] == str(tmp_path)


@needs_node
def test_cli_exit_codes(tmp_path: Path) -> None:
    good = tmp_path / "good"
    raw = dryrun("claim-stress-test", good)
    write_outputs("claim-stress-test", good, raw["result"])
    (tmp_path / "good.json").write_text(json.dumps(raw))
    assert cli("--workflow", "claim-stress-test", "--result", str(tmp_path / "good.json"), "--out-dir", str(good)).returncode == 0
    refused = cli("--workflow", "claim-stress-test", "--result", str(tmp_path / "good.json"), "--out-dir", str(good), "--live")
    assert refused.returncode == 2 and json.loads(refused.stdout)["overall"] == "not_checked"

    (good / "claim-stress-test.md").write_text("no heading, no status\n")
    out_file = tmp_path / "verdict.json"
    bad = cli("--workflow", "claim-stress-test", "--result", str(tmp_path / "good.json"), "--out-dir", str(good), "--output", str(out_file))
    assert bad.returncode == 1 and json.loads(out_file.read_text())["overall"] == "fail"

    part_dir = tmp_path / "partial"
    part = dryrun("claim-stress-test", part_dir, [null_rule(NULL_FAULT["claim-stress-test"]), confirm_says("PARTIAL")])
    write_outputs("claim-stress-test", part_dir, part["result"])
    (tmp_path / "partial.json").write_text(json.dumps(part))
    assert cli("--workflow", "claim-stress-test", "--result", str(tmp_path / "partial.json"), "--out-dir", str(part_dir)).returncode == 3

    assert cli("--workflow", "claim-stress-test", "--result", str(tmp_path / "nope.json"), "--out-dir", str(good)).returncode == 2
    assert cli("--workflow", "not-a-workflow", "--result", str(tmp_path / "good.json"), "--out-dir", str(good)).returncode == 2
