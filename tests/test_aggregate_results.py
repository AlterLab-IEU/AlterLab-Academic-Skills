"""scripts/aggregate_results.py: schema checks, selection rules, denominators, reproducibility.

Inputs are the SYNTHETIC example records in docs/examples/eval-records/ (every one carries
``synthetic_example: true``) and variants of them built per test, plus — in the last test —
records that ``run_evals.py`` itself writes against the fake ``claude`` CLI of
test_behavioral_runner.py. No model, network or real result is involved.
"""

from __future__ import annotations

import copy
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import aggregate_results as agg
from tests.test_behavioral_runner import _case, _run, fake_cli  # noqa: F401  (fixture)

REPO = Path(__file__).resolve().parents[1]
EXAMPLES = REPO / "docs" / "examples" / "eval-records"
EXAMPLES_ARG = "docs/examples/eval-records"
V1 = "round-1/behavioral-20261001T100000Z.json"
V1_DIRTY = "round-1/behavioral-20261001T120000Z.json"
COLLECT = "round-2/behavioral-20261002T090000Z.json"
REGRADE = "round-2/regrade-20261002T093000Z.json"
TWIN_A = "round-2/behavioral-20261002T100500Z.json"
TWIN_B = "round-2/behavioral-20261002T100500Z-1.json"
V2 = "round-3/behavioral-20261003T090000Z.json"


def _example(rel: str) -> dict:
    return copy.deepcopy(json.loads((EXAMPLES / rel).read_text(encoding="utf-8")))


def _write(path: Path, data: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
    return path


def _copy_examples(tmp_path: Path, rels: list[str]) -> Path:
    root = tmp_path / "records"
    for rel in rels:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(EXAMPLES / rel, root / rel)
    return root


def _summary(paths: list[str | Path], mode: str = "latest-clean", **kw) -> dict:
    files = [agg.load_file(label, p) for label, p in agg.discover([str(p) for p in paths])]
    return agg.build_summary(files, mode, **kw)


def _counted(s: dict) -> dict[str, dict]:
    return {c["case_id"]: c for c in s["counted_cases"]}


def _group(s: dict, prefix: str) -> dict:
    (g,) = [g for g in s["methodologies"] if g["methodology"].startswith(prefix)]
    return g


def _not_counted(s: dict, case_id: str) -> list[tuple[str, str]]:
    return [(x["category"], x["file"]) for x in s["runs_not_counted"] if x["case_id"] == case_id]


# --------------------------------------------------------------------------- examples
def test_every_example_record_is_marked_synthetic() -> None:
    files = sorted(EXAMPLES.rglob("*.json"))
    assert len(files) >= 8
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        assert data.get("synthetic_example") is True, f"{f.name} must be marked synthetic"
        assert all(c.get("skill", "").startswith("alterlab-example-")
                   for c in data.get("cases", [])), "examples must not name real skills"


def test_committed_expected_summary_matches_the_examples() -> None:
    """docs/examples/eval-records/expected-summary.md is what the aggregator prints for the
    examples; it is regenerated, never hand-edited."""
    proc = subprocess.run([sys.executable, "scripts/aggregate_results.py", EXAMPLES_ARG],
                          cwd=REPO, capture_output=True, text=True)
    assert proc.returncode == 3, proc.stderr  # the two malformed examples are rejected
    assert proc.stdout == (EXAMPLES / "expected-summary.md").read_text(encoding="utf-8")


# --------------------------------------------------------------------------- schema checks
@pytest.mark.parametrize("rel", [V1, V1_DIRTY, COLLECT, REGRADE, TWIN_A, TWIN_B, V2])
def test_valid_v1_v2_and_regrade_records_pass_the_schema_check(rel) -> None:
    assert agg.validate_record(_example(rel)) == []


@pytest.mark.parametrize("version", [None, 0, 3, 9, "1", True, 1.0])
def test_unknown_or_mistyped_schema_version_is_rejected(version) -> None:
    rec = _example(V1)
    rec["schema_version"] = version
    errors = agg.validate_record(rec)
    assert errors and "unsupported schema_version" in errors[0]
    del rec["schema_version"]
    assert agg.validate_record(rec) == ["top level: missing required key 'schema_version'"]


def test_v2_requires_judge_runner_and_consistent_dimensions() -> None:
    rec = _example(V2)
    del rec["judge"]
    assert any("judge" in e for e in agg.validate_record(rec))
    rec = _example(V2)
    rec["runner"]["script_sha256"] = "not-a-hash"
    assert any("script_sha256" in e for e in agg.validate_record(rec))
    rec = _example(V2)  # outcome PASS while the substantive dimension FAILed
    rec["cases"][0]["skilled"]["dimensions"]["substantive"] = "FAIL"
    assert any("contradicts" in e for e in agg.validate_record(rec))
    rec = _example(V2)  # outcome FAIL with no failing gating dimension
    rec["cases"][1]["skilled"]["dimensions"]["routing"] = "PASS"
    assert any("no gating dimension" in e for e in agg.validate_record(rec))
    rec = _example(V2)  # the bare arm never has a routing verdict
    rec["cases"][0]["bare"]["dimensions"]["routing"] = "FAIL"
    assert any("bare arm has no routing" in e for e in agg.validate_record(rec))
    rec = _example(V2)  # a graded v2 arm must carry its dimensions
    del rec["cases"][0]["skilled"]["dimensions"]
    assert any("has no 'dimensions'" in e for e in agg.validate_record(rec))


def test_v1_regrade_must_name_its_source_and_judge() -> None:
    rec = _example(REGRADE)
    del rec["regraded_from"], rec["judge"]
    errors = agg.validate_record(rec)
    assert any("regraded_from" in e for e in errors) and any("'judge'" in e for e in errors)


def test_malformed_files_are_reported_not_crashed_on(tmp_path, capsys) -> None:
    root = _copy_examples(tmp_path, [V1])
    _write(root / "bad" / "truncated.json", '{"schema_version": 1, "kind": "behav')
    _write(root / "bad" / "list.json", [1, 2, 3])
    (root / "bad" / "binary.json").write_bytes(b"\xff\xfe\x00garbage")
    _write(root / "bad" / "cases-not-list.json", {**_example(V1), "cases": {"a": 1}})
    rc = agg.main([str(root), "--format", "json"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 3
    status = {Path(i["file"]).name: (i["status"], i["errors"]) for i in out["inputs"]}
    assert status["truncated.json"][0] == "rejected" and "JSON" in status["truncated.json"][1][0]
    assert status["binary.json"][0] == "rejected"
    assert status["list.json"][0] == "rejected"
    assert status["cases-not-list.json"][0] == "rejected"
    assert out["totals"]["cases_counted"] == 7, "the valid file is still summarised"


# --------------------------------------------------------------------------- selection
def test_latest_clean_skips_dirty_unconfined_runs_and_latest_does_not() -> None:
    clean = _summary([EXAMPLES / V1, EXAMPLES / V1_DIRTY])
    case = "alterlab-example-alpha:trigger-1"
    assert _counted(clean)[case]["skilled"] == "PASS"
    assert _counted(clean)[case]["file"].endswith(V1)
    assert ("unclean", str(EXAMPLES / V1_DIRTY)) in _not_counted(clean, case)
    anyrun = _summary([EXAMPLES / V1, EXAMPLES / V1_DIRTY], mode="latest")
    assert _counted(anyrun)[case]["skilled"] == "FAIL", "latest ignores the clean-tree rule"
    assert _counted(anyrun)[case]["file"].endswith(V1_DIRTY)


def test_a_run_that_did_not_record_confinement_is_not_eligible_for_latest_clean(tmp_path):
    rec = _example(V1)
    del rec["isolation"]
    s = _summary([_write(tmp_path / "old.json", rec)])
    assert s["totals"]["cases_counted"] == 0
    assert len(s["cases_without_eligible_run"]) == 7
    assert {x["reason"] for x in s["runs_not_counted"]} == {
        "not namespace-confined (confinement not recorded)"}


def test_latest_picks_the_newest_run_and_earliest_the_first() -> None:
    paths = [EXAMPLES / V1, EXAMPLES / V2]
    case = "alterlab-example-alpha:trigger-2"
    latest = _counted(_summary(paths))[case]
    earliest = _counted(_summary(paths, mode="earliest"))[case]
    assert (latest["skilled"], latest["methodology"]) == (
        "PASS", "v2-dimensions-literal-judge/literal-v1")
    assert (earliest["skilled"], earliest["methodology"]) == (
        "FAIL", "v1-combined-literal-judge")


def test_regrade_supersedes_its_source_and_collect_only_is_ungraded() -> None:
    case = "alterlab-example-gamma:trigger-1"
    s = _summary([EXAMPLES / COLLECT, EXAMPLES / REGRADE])
    assert _counted(s)[case]["file"].endswith(REGRADE)
    assert _counted(s)[case]["methodology"] == "v1-combined-substance-judge"
    assert [c for c, _ in _not_counted(s, case)] == ["superseded"]
    alone = _summary([EXAMPLES / COLLECT])
    assert case in alone["cases_without_eligible_run"]
    assert [c for c, _ in _not_counted(alone, case)] == ["ungraded"]


def test_conflicting_duplicate_runs_are_reported_and_not_counted() -> None:
    s = _summary([EXAMPLES / TWIN_A, EXAMPLES / TWIN_B])
    (conflict,) = s["conflicts"]
    assert conflict["case_id"] == "alterlab-example-gamma:trigger-2"
    assert sorted(r["skilled"] for r in conflict["runs"]) == ["FAIL", "PASS"]
    assert "alterlab-example-gamma:trigger-2" not in _counted(s)
    # the identical twin is counted once, from the lexicographically first file
    twin = _counted(s)["alterlab-example-gamma:trigger-3"]
    assert twin["file"].endswith(TWIN_B)
    assert [c for c, _ in _not_counted(s, "alterlab-example-gamma:trigger-3")] == ["duplicate"]


def test_require_ancestor_keeps_only_runs_on_descendant_commits(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*a):
        return subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c",
                               "user.email=t@example.com", *a], capture_output=True,
                              text=True, check=True).stdout.strip()

    git("init", "-q")
    git("commit", "-q", "--allow-empty", "-m", "before the fix")
    before = git("rev-parse", "HEAD")
    git("commit", "-q", "--allow-empty", "-m", "the fix")
    fix = git("rev-parse", "HEAD")
    git("commit", "-q", "--allow-empty", "-m", "after the fix")
    after = git("rev-parse", "HEAD")
    old, new, unknown = _example(V1), _example(V1), _example(V1)
    old["repo_commit"], new["repo_commit"] = before, after
    unknown["repo_commit"] = "f" * 40
    new["finished_at"] = "2026-09-01T00:00:00+00:00"  # older than `old`, yet the only eligible
    unknown["finished_at"] = "2026-12-01T00:00:00+00:00"
    paths = [_write(tmp_path / n / "r.json", r) for n, r in
             (("old", old), ("new", new), ("unknown", unknown))]
    s = _summary(paths, require_ancestor=fix, git_repo=str(repo))
    assert {c["file"] for c in s["counted_cases"]} == {str(paths[1])}
    reasons = {x["file"]: x["reason"] for x in s["runs_not_counted"]
               if x["case_id"] == "alterlab-example-alpha:trigger-1"}
    assert "does not contain" in reasons[str(paths[0])]
    assert "unverifiable" in reasons[str(paths[2])]


def test_skills_root_leaves_out_skills_no_longer_in_the_suite(tmp_path) -> None:
    root = tmp_path / "skills"
    _write(root / "examples" / "alterlab-example-alpha" / "SKILL.md", "---\nname: x\n---\n")
    s = _summary([EXAMPLES / V1], skills_root=str(root))
    assert {c["skill"] for c in s["counted_cases"]} == {"alterlab-example-alpha"}
    assert {x["category"] for x in s["runs_not_counted"]} == {"not-in-suite"}


# --------------------------------------------------------------------------- denominators
def test_denominators_and_non_verdict_outcomes_are_reported() -> None:
    g = _group(_summary([EXAMPLES / V1]), "v1-combined-literal")
    assert g["denominators"] == {"selected": 7, "attempted": 6, "answered": 4,
                                 "usable_verdicts": 3}
    assert g["skilled"] == {"PASS": 1, "FAIL": 2, "INCONCLUSIVE": 1, "REFUSED": 1,
                            "INFRA_ERROR": 1, "NOT_RUN": 1}
    assert g["not_run"] == {"not_runnable_here": 1, "aborted_or_other": 0}
    assert g["graded_cases"] == {"skilled_pass": 1, "bare_pass_same_cases": 1, "helped": 1,
                                 "hurt": 1, "denominator": 3}


def test_every_printed_percentage_carries_its_numerator_and_denominator() -> None:
    md = agg.render_markdown(_summary([EXAMPLES]))
    percentages = re.findall(r"[^\n]{0,25}\d+(?:\.\d+)?%", md)
    assert percentages
    for p in percentages:
        assert re.search(r"\d+ / \d+ \(\d+\.\d%$", p), f"bare percentage: {p!r}"
    assert agg.frac(0, 0) == "0 / 0 (no denominator)"


def test_excluded_and_non_passing_cases_are_listed_with_reasons() -> None:
    md = agg.render_markdown(_summary([EXAMPLES]))
    for needle in ("not namespace-confined", "superseded by regrade", "tied with a run that "
                   "disagrees", "not runnable here: env: EXAMPLE_API_KEY",
                   "synthetic usage-policy refusal", "timed out after 600s",
                   "judges returned no majority verdict", "unsupported schema_version 9",
                   "'MOSTLY_PASS' is not one of"):
        assert needle in md, needle


# --------------------------------------------------------------------------- v1 / v2
def test_v1_and_v2_outcomes_are_never_summed_into_one_figure(tmp_path) -> None:
    s = _summary([EXAMPLES / V1, EXAMPLES / V2])
    labels = [g["methodology"] for g in s["methodologies"]]
    assert labels == ["v1-combined-literal-judge", "v2-dimensions-literal-judge/literal-v1"]
    v1, v2 = s["methodologies"]
    assert v1["denominators"]["selected"] == 6 and v2["denominators"]["selected"] == 4
    assert v1["dimensions"] is None, "v1 has no routing/substantive split"
    assert not ({"PASS", "skilled", "graded_cases"} & set(s["totals"])), "no cross-version sum"
    # another endpoint is another model: its own methodology, never mixed into Claude numbers
    other = _example(V1)
    other["endpoint"] = "base-url:http://127.0.0.1:8080"
    for c in other["cases"]:
        c["case_id"] += "-local"
    s2 = _summary([EXAMPLES / V1, _write(tmp_path / "local.json", other)])
    assert [g["methodology"] for g in s2["methodologies"]] == [
        "v1-combined-literal-judge", "v1-combined-literal-judge @ base-url:http://127.0.0.1:8080"]


def test_routing_and_substantive_outcomes_are_separated_for_v2() -> None:
    g = _group(_summary([EXAMPLES / V2]), "v2-")
    dm = g["dimensions"]
    assert g["skilled"]["PASS"] == 1 and g["skilled"]["FAIL"] == 2
    # the near-miss case failed on routing only, the artifact case on its artifact only
    assert dm["substantive"] == {"denominator_both_arms_verdict": 3, "skilled_pass": 3,
                                 "bare_pass": 1, "helped": 2, "hurt": 0}
    assert dm["routing"] == {"denominator_skilled_verdict": 3, "skilled_pass": 2}
    assert dm["counts"]["bare"]["routing"] == {"null": 4}
    assert dm["counts"]["skilled"]["artifacts"] == {"FAIL": 1, "absent": 1, "null": 2}


def test_provenance_records_hashes_versions_and_commits() -> None:
    s = _summary([EXAMPLES / V1, EXAMPLES / V2])
    row = _counted(s)["alterlab-example-delta:artifact-1"]
    assert re.fullmatch(r"[0-9a-f]{64}", row["skill_md_sha256"])
    assert re.fullmatch(r"[0-9a-f]{64}", row["rubric_sha256"])
    assert list(row["fixtures_sha256"]) == ["data.csv"]
    v1 = _counted(s)["alterlab-example-alpha:trigger-1"]
    assert (v1["skill_version"], v1["claude_cli_version"]) == (
        "1.0.0", "0.0.0-synthetic (Claude Code)")
    assert v1["repo_commit"] and v1["skill_md_sha256"] is None
    prov = _group(s, "v2-")["provenance"]
    assert prov["cases_without_hashes"] == 0 and prov["runner_script_sha256"][0][1] == 4


# --------------------------------------------------------------------------- reproducibility
def test_output_is_byte_identical_and_order_independent(tmp_path, capsys) -> None:
    subdirs = sorted(str(p) for p in EXAMPLES.iterdir() if p.is_dir())
    outs = []
    for i, order in enumerate((subdirs, list(reversed(subdirs)), subdirs)):
        md, js = tmp_path / f"s{i}.md", tmp_path / f"s{i}.json"
        assert agg.main([*order, "--md-out", str(md), "--json-out", str(js)]) == 3
        capsys.readouterr()
        outs.append((md.read_bytes(), js.read_bytes()))
    assert outs[0] == outs[1] == outs[2]
    # no timestamp of its own: every timestamp printed was read from an input
    inputs = {json.loads(p.read_text()).get(k) for p in EXAMPLES.rglob("*.json")
              for k in ("started_at", "finished_at")}
    printed = set(re.findall(r"\d{4}-\d\d-\d\dT[\d:]+\+00:00", outs[0][0].decode()))
    assert printed and printed <= inputs


# --------------------------------------------------------------------------- exit codes
def test_exit_codes(tmp_path, capsys) -> None:
    assert agg.main([str(EXAMPLES / V1)]) == 0
    assert agg.main([str(EXAMPLES / V1), str(EXAMPLES / "malformed")]) == 3
    assert agg.main([str(EXAMPLES / "malformed")]) == 2
    assert agg.main([str(tmp_path / "does-not-exist.json")]) == 2
    assert agg.main([]) == 2
    activation = _write(tmp_path / "activation.json", {"schema_version": 1,
                                                       "kind": "activation", "picks": []})
    assert agg.main([str(activation)]) == 2, "an ignored kind is not a valid input"
    assert agg.main([str(activation), str(EXAMPLES / V1)]) == 0, "ignored is not rejected"
    capsys.readouterr()
    assert agg.main(["--list-rules"]) == 0
    assert "latest-clean:" in capsys.readouterr().out


# --------------------------------------------------------------------------- run_evals.py
@pytest.mark.usefixtures("fake_cli")
def test_records_written_by_run_evals_are_accepted_and_regrade_supersedes(
        tmp_path, monkeypatch) -> None:
    """End to end: run_evals.py writes a behavioral record and a regrade of it (fake CLI, no
    model); the aggregator accepts both and counts the case from the regrade."""
    import run_evals

    rc, res = _run(tmp_path, [_case("a")], "skilled_bad", monkeypatch)
    src = next((tmp_path / "results").glob("behavioral-*.json"))
    monkeypatch.setenv("FAKE_CLAUDE_MODE", "substance_lenient")
    run_evals.regrade_results(src, "substance", 30, tmp_path / "results")
    files = [agg.load_file(label, p) for label, p in agg.discover([str(tmp_path / "results")])]
    assert [f.status for f in files] == ["valid", "valid"], [f.errors for f in files]
    s = agg.build_summary(files, "latest")
    (row,) = s["counted_cases"]
    assert row["case_id"] == "alterlab-controlled-fixture:a"
    assert Path(row["file"]).name.startswith("regrade-")
    assert [x["category"] for x in s["runs_not_counted"]] == ["superseded"]
