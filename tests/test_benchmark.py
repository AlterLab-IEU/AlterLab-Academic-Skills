"""Structural checks for benchmarks/*/task.json and unit tests for the deterministic scorer.

These tests use hand-written answers, not model output: they show the scorer counts false
approvals, false accusations, abstentions and missing items correctly. Live benchmark numbers
come only from ``scripts/run_benchmark.py`` runs, never from this file.
"""

from __future__ import annotations

import json

import pytest

import run_benchmark as rb

TASKS = rb.task_files()


def test_benchmark_has_tasks() -> None:
    assert TASKS, "benchmarks/*/task.json not found"


@pytest.mark.parametrize("path", TASKS, ids=lambda p: p.parent.name)
def test_task_file_is_valid(path) -> None:
    assert rb.validate_task(path) == []


@pytest.mark.parametrize("path", TASKS, ids=lambda p: p.parent.name)
def test_task_measures_both_error_types(path) -> None:
    """Every task needs items that should be approved and items that are problems, so both
    false approvals and false accusations are measurable; and an incomplete-input case whose
    correct answers include abstention."""
    task = json.loads(path.read_text(encoding="utf-8"))
    approve = set(task["label_semantics"]["approve"])
    abstain = set(task["label_semantics"]["abstain"])
    expected = [i.get("expected") for c in task["cases"] for i in c["items"]
                if i.get("kind") != "number"]
    assert any(e in approve for e in expected)
    assert any(e not in approve and e not in abstain for e in expected)
    incomplete = [c for c in task["cases"] if c.get("kind") == "incomplete-input"]
    assert incomplete and any(i.get("expected") in abstain
                              for c in incomplete for i in c["items"])


CASE = {
    "labels": ["OK", "BAD", "UNKNOWN"],
    "items": [
        {"id": "a", "expected": "OK"},
        {"id": "b", "expected": "BAD"},
        {"id": "c", "expected": "UNKNOWN"},
        {"id": "d", "expected": "BAD"},
        {"id": "n", "kind": "number", "expected": 2.5, "tolerance": 0.1},
    ],
}
SEM = {"approve": ["OK"], "abstain": ["UNKNOWN"]}


def _answer(**labels) -> dict:
    return {k: ({"label": None, "value": v} if k == "n" else {"label": v, "value": None})
            for k, v in labels.items()}


def test_all_correct() -> None:
    t = rb.score_case(CASE, SEM, _answer(a="OK", b="bad", c="UNKNOWN", d="BAD", n=2.55))["tally"]
    assert t["correct"] == 5 and t["complete"] and t["correct_abstention"] == 1
    assert t["false_approval"] == t["false_accusation"] == 0


def test_false_approval_and_accusation_are_distinguished() -> None:
    t = rb.score_case(CASE, SEM, _answer(a="BAD", b="OK", c="UNKNOWN", d="BAD", n=9))["tally"]
    assert t["false_accusation"] == 1  # a: fine item flagged
    assert t["false_approval"] == 1    # b: problem passed as fine
    assert t["wrong_other"] == 1       # n: wrong number
    assert t["correct"] == 2


def test_overconfidence_on_incomplete_input_counts_as_false_approval_when_approving() -> None:
    t = rb.score_case(CASE, SEM, _answer(a="OK", b="BAD", c="OK", d="BAD", n=2.5))["tally"]
    assert t["overconfident_on_incomplete"] == 1 and t["false_approval"] == 1


def test_unnecessary_abstention_missing_and_invalid_labels() -> None:
    t = rb.score_case(CASE, SEM, _answer(a="UNKNOWN", b="MAYBE", n=2.5))["tally"]
    assert t["unnecessary_abstention"] == 1 and t["invalid_label"] == 1
    assert t["missing"] == 2 and not t["complete"]


def test_unparseable_answer_scores_nothing_as_correct() -> None:
    t = rb.score_case(CASE, SEM, None)["tally"]
    assert t["missing"] == 5 and t["correct"] == 0 and not t["complete"]


def test_parse_answer_takes_the_last_json_block() -> None:
    """Drafts then a final answer: the last parseable block wins (a separate rule from
    duplicate handling, which the next tests cover)."""
    text = ("draft ```json\n{\"items\": [{\"id\": \"a\", \"label\": \"BAD\"}]}\n```\nfinal:\n"
            "```json\n{\"items\": [{\"id\": \"a\", \"label\": \"OK\", "
            "\"evidence\": \"looks fine\"}]}\n```")
    assert rb.parse_answer(text) == {"a": {"label": "OK", "value": None, "evidence": "looks fine"}}
    assert rb.parse_answer("no json here") is None


def _block(*entries: dict) -> str:
    return "```json\n" + json.dumps({"items": list(entries)}) + "\n```"


def test_conflicting_duplicate_ids_are_unresolved_never_correct() -> None:
    """Replaces the old first-duplicate-wins test: [a=OK, a=BAD] used to score as one correct,
    complete answer. A conflicting duplicate is now an unresolved conflict."""
    ans = rb.parse_answer(_block({"id": "a", "label": "OK", "evidence": "first"},
                                 {"id": "a", "label": "BAD", "evidence": "second"},
                                 {"id": "b", "label": "BAD"}, {"id": "c", "label": "UNKNOWN"},
                                 {"id": "d", "label": "BAD"}, {"id": "n", "value": 2.5}))
    scored = rb.score_case(CASE, SEM, ans)
    t = scored["tally"]
    assert t["unresolved_conflict"] == 1 and t["correct"] == 4
    assert not t["complete"]
    rec = next(r for r in scored["items"] if r["id"] == "a")
    assert rec["result"] == "unresolved_conflict"
    assert [(a["label"], a["evidence"]) for a in rec["answers"]] == [("OK", "first"),
                                                                     ("BAD", "second")]
    # Order does not matter: [a=BAD, a=OK] is the same conflict, not a false accusation.
    ans = rb.parse_answer(_block({"id": "a", "label": "BAD"}, {"id": "a", "label": "OK"}))
    t = rb.score_case(CASE, SEM, ans)["tally"]
    assert t["unresolved_conflict"] == 1 and t["correct"] == 0 and t["false_accusation"] == 0


def test_conflicting_duplicate_numbers_are_unresolved() -> None:
    ans = rb.parse_answer(_block({"id": "n", "label": None, "value": 2.5},
                                 {"id": "n", "label": None, "value": 9}))
    rec = next(r for r in rb.score_case(CASE, SEM, ans)["items"] if r["id"] == "n")
    assert rec["result"] == "unresolved_conflict"
    assert [a["value"] for a in rec["answers"]] == [2.5, 9]


def test_identical_duplicates_collapse_with_a_count() -> None:
    ans = rb.parse_answer(_block({"id": "a", "label": "OK", "evidence": "x"},
                                 {"id": "a", "label": " ok ", "evidence": "y"},
                                 {"id": "b", "label": "BAD"}, {"id": "c", "label": "UNKNOWN"},
                                 {"id": "d", "label": "BAD"}, {"id": "n", "value": 2.5},
                                 {"id": "n", "value": 2.50}))
    scored = rb.score_case(CASE, SEM, ans)
    t = scored["tally"]
    assert t["correct"] == 5 and t["complete"] and t["unresolved_conflict"] == 0
    assert t["duplicate_ids_collapsed"] == 2
    rec = next(r for r in scored["items"] if r["id"] == "a")
    assert rec["duplicates"] == 1 and rec["evidence"] == "x"
    assert rec["alternate_evidence"] == ["y"]


def test_unknown_and_missing_ids_are_reported_as_diagnostics() -> None:
    ans = rb.parse_answer(_block({"id": "a", "label": "OK"}, {"id": "zz", "label": "BAD"},
                                 {"id": "B", "label": "BAD"}))
    scored = rb.score_case(CASE, SEM, ans)
    assert scored["unknown_ids"] == ["zz", "B"]
    assert scored["missing_ids"] == ["b", "c", "d", "n"]
    t = scored["tally"]
    assert t["unknown_ids"] == 2 and t["missing"] == 4 and t["correct"] == 1
    assert not t["complete"]


def test_evidence_text_is_preserved_per_item() -> None:
    ans = rb.parse_answer(_block({"id": "a", "label": "OK", "evidence": "L3: 'fine'"},
                                 {"id": "n", "value": 2.5, "evidence": 7}))
    recs = {r["id"]: r for r in rb.score_case(CASE, SEM, ans)["items"]}
    assert recs["a"]["evidence"] == "L3: 'fine'"
    assert recs["n"]["evidence"] is None and recs["n"]["evidence_status"] == "missing"
    assert recs["b"]["evidence"] is None and recs["b"]["result"] == "missing"


# --- Deterministic evidence checks on the real benchmark fixtures -----------------------
def _task(task_id: str) -> tuple[dict, object]:
    path = rb.BENCH / task_id / "task.json"
    return json.loads(path.read_text(encoding="utf-8")), path.parent


def _score_one(task_id: str, case_id: str, item_id: str, label: str, evidence: str) -> dict:
    task, task_dir = _task(task_id)
    case = next(c for c in task["cases"] if c["id"] == case_id)
    fixtures = rb.load_fixtures(task_dir, case)
    ans = {item_id: {"label": label, "value": None, "evidence": evidence}}
    scored = rb.score_case(case, task["label_semantics"], ans, fixtures,
                           rb.evidence_config(task))
    return next(r for r in scored["items"] if r["id"] == item_id)


def test_quote_from_the_items_cited_lines_passes_both_checks() -> None:
    # records_batch_A.txt L19-L20; the quote spans the line break and the "L20:" label and
    # uses curly quotes, which normalisation must tolerate.
    rec = _score_one("screening", "batch-a-standard", "R02", "EXCLUDE",
                     "C1 excludes physicians: \u201cSixty-four internal medicine resident "
                     "physicians were randomised to an 8-week MBSR-based course\u201d")
    assert rec["result"] == "correct"
    assert rec["evidence_status"] == "quote_in_item_region"
    checks = rec["evidence_checks"]
    assert checks["quote_in_fixture"]["result"] == "pass"
    assert checks["quote_in_item_region"]["result"] == "pass"
    # A quote that copies the fixture's line labels still matches.
    labelled = _score_one("screening", "batch-a-standard", "R02", "EXCLUDE",
                          '"L19: Abstract: Sixty-four internal medicine resident physicians"')
    assert labelled["evidence_status"] == "quote_in_item_region"


def test_quote_from_elsewhere_in_the_fixture_is_only_quote_in_fixture() -> None:
    # R03's text ("there was no control group", L28-L29), offered as evidence for R02.
    rec = _score_one("screening", "batch-a-standard", "R02", "EXCLUDE",
                     "'measured before and after the course; there was no control group'")
    assert rec["evidence_status"] == "quote_in_fixture"
    assert rec["evidence_checks"]["quote_in_item_region"]["result"] == "no_match"


def test_misquote_and_paraphrase_need_review_not_wrong() -> None:
    misquote = _score_one("screening", "batch-a-standard", "R02", "EXCLUDE",
                          '"the participants were all internal medicine physicians"')
    assert misquote["evidence_status"] == "needs_review"
    assert misquote["evidence_checks"]["quote_in_fixture"]["result"] == "no_match"
    assert misquote["result"] == "correct"  # label scoring is independent of evidence
    para = _score_one("screening", "batch-a-standard", "R02", "EXCLUDE",
                      "The sample is resident physicians, who are not eligible under C1.")
    assert para["evidence_status"] == "needs_review"
    assert para["evidence_checks"]["quote_in_fixture"]["result"] == "no_quote"


def test_short_quotes_do_not_count() -> None:
    rec = _score_one("screening", "batch-a-standard", "R06", "EXCLUDE", "'Year: 2008'")
    assert rec["evidence_checks"]["quote_in_fixture"]["result"] == "no_quote"
    assert rec["evidence_status"] == "needs_review"


def test_citation_entries_are_located_by_entry_prefix() -> None:
    task, _ = _task("citation-integrity")
    assert rb.evidence_config(task)["item_region"] == "entry_prefix"
    hit = _score_one("citation-integrity", "mixed-bibliography", "R3", "PAC",
                     "Entry says 'Why most published research findings are false. PLoS "
                     "Biology' but DOI 10.1371/journal.pmed.0020124 is PLoS Medicine 2005.")
    assert hit["evidence_status"] == "quote_in_item_region"
    assert hit["evidence_checks"]["quote_in_item_region"]["region"] == [
        {"file": "references_mixed.md", "lines": [11, 11]}]
    other = _score_one("citation-integrity", "mixed-bibliography", "R3", "PAC",
                       "'The pen is mightier than the keyboard' is a different entry")
    assert other["evidence_status"] == "quote_in_fixture"


def test_anchor_line_refs_follow_the_named_fixture_and_skip_skill_files() -> None:
    task, task_dir = _task("analysis-check")
    case = task["cases"][0]
    a1 = next(i for i in case["items"] if i["id"] == "A1")
    refs = rb.anchor_line_refs(a1["anchor"], set(rb.load_fixtures(task_dir, case)))
    assert ("analysis_log_A.md", 8, 9) in refs
    assert ("A1_writing_retreat_anxiety.csv", 3, 14) in refs
    # "SKILL.md L101-L113" names a skill file, not a fixture: it must not be attributed.
    assert not any(a == 101 for _, a, _ in refs)


@pytest.mark.parametrize("path", TASKS, ids=lambda p: p.parent.name)
def test_item_regions_point_inside_their_fixtures(path) -> None:
    """A stale anchor (lines renumbered) or a renamed entry would make quote_in_item_region
    silently wrong; entry_prefix tasks must locate every item's entry."""
    task = json.loads(path.read_text(encoding="utf-8"))
    mode = rb.evidence_config(task)["item_region"]
    for case in task["cases"]:
        fixtures = rb.load_fixtures(path.parent, case)
        for item in case["items"]:
            region = rb.item_region(item, fixtures, mode)
            if mode == "entry_prefix":
                assert len(region) == 1, (case["id"], item["id"], region)
            for name, a, b in region:
                n_lines = len(fixtures[name].splitlines())
                assert 1 <= a <= b <= n_lines, (case["id"], item["id"], name, a, b)


# --- Payload, Markdown, export, dry run -------------------------------------------------
class _FakeCall:
    def __init__(self, text: str) -> None:
        self.text, self.outcome, self.error = text, "answer", ""
        self.duration_ms, self.cost_usd, self.num_turns, self.permission_denials = 1000, 0.01, 2, 0


def _live_run(monkeypatch, tmp_path, extra: list[str]) -> tuple[int, dict]:
    answer = _block({"id": "R02", "label": "EXCLUDE",
                     "evidence": "'Sixty-four internal medicine resident physicians'"},
                    {"id": "R02", "label": "INCLUDE"}, {"id": "R99", "label": "INCLUDE"},
                    {"id": "R01", "label": "INCLUDE", "evidence": "meets every criterion"})
    monkeypatch.setattr(rb.shutil, "which", lambda name: "/usr/bin/claude")
    monkeypatch.setattr(rb.rv, "_claude_call", lambda *a, **k: _FakeCall(answer))
    monkeypatch.setattr(rb.rv, "_run_metadata", lambda *a, **k: {
        "kind": "benchmark", "model": "m", "claude_cli_version": "x", "repo_commit": "abc",
        "repo_dirty": False, "runs_per_arm": 1})
    code = rb.main(["--task", "screening", "--case", "batch-a-standard",
                    "--results-dir", str(tmp_path / "res"), *extra])
    payload = json.loads(next((tmp_path / "res").glob("benchmark-*.json")).read_text())
    return code, payload


def test_payload_carries_scoring_schema_version_and_evidence(monkeypatch, tmp_path) -> None:
    md_path = tmp_path / "table.md"
    code, payload = _live_run(monkeypatch, tmp_path, ["--markdown", str(md_path)])
    assert code == 0  # every arm answered; conflicts are item-level, not unparseable
    assert payload["scoring_schema_version"] == 2
    task = payload["tasks"][0]
    assert task["scoring_schema_version"] == 2
    arm = task["cases"][0]["arms"][0]
    assert arm["unknown_ids"] == ["R99"]
    recs = {r["id"]: r for r in arm["items"]}
    assert recs["R02"]["result"] == "unresolved_conflict"
    assert recs["R01"]["evidence"] == "meets every criterion"
    assert recs["R01"]["evidence_status"] == "needs_review"
    s = task["summary"]["skilled"]
    assert s["unresolved_conflict"] == 1 and s["correct"] == 1 and s["complete_cases"] == 0
    assert s["label_accuracy"] == round(1 / 6, 4)
    md = md_path.read_text()
    assert "scoring schema 2" in md and "Label accuracy" in md and "Evidence:" in md


def test_markdown_has_separate_label_and_evidence_columns() -> None:
    tally = {"items": 4, "correct": 3, "false_approval": 1, "false_accusation": 0,
             "correct_abstention": 1, "unnecessary_abstention": 0,
             "overconfident_on_incomplete": 0, "missing": 0, "unresolved_conflict": 0,
             "evidence_quote_in_item_region": 1, "evidence_quote_in_fixture": 1,
             "evidence_needs_review": 2, "evidence_missing": 0, "complete_cases": 1,
             "cases": 1, "duration_ms": 2000, "cost_usd": 0.5, "label_accuracy": 0.75}
    payload = {"started_at": "t", "model": "m", "claude_cli_version": "v", "repo_commit": "c",
               "repo_dirty": False, "runs_per_arm": 1, "status": "measured",
               "scoring_schema_version": 2,
               "tasks": [{"id": "x", "summary": {"skilled": tally, "bare": tally}}]}
    md = rb._markdown(payload)
    header = next(line for line in md.splitlines() if line.startswith("| Task"))
    cols = [c.strip() for c in header.strip("|").split("|")]
    assert "Label accuracy" in cols and "Evidence: needs review" in cols
    row = next(line for line in md.splitlines() if line.startswith("| x | skilled"))
    cells = [c.strip() for c in row.strip("|").split("|")]
    assert cells[cols.index("Label accuracy")] == "75.0%"
    assert cells[cols.index("Evidence: quote in item region")] == "1"
    assert cells[cols.index("Evidence: needs review")] == "2"


def test_export_evidence_review_after_a_run_and_from_saved_results(monkeypatch,
                                                                   tmp_path) -> None:
    out = tmp_path / "review.jsonl"
    code, payload = _live_run(monkeypatch, tmp_path, ["--export-evidence-review", str(out)])
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    assert code == 0 and rows
    need = {"task", "case", "arm", "run", "item", "expected", "got", "evidence", "anchor",
            "deterministic_checks", "evidence_status"}
    assert all(need <= set(r) for r in rows)
    r01 = next(r for r in rows if r["item"] == "R01" and r["arm"] == "skilled")
    assert r01["evidence"] == "meets every criterion"
    assert r01["anchor"].startswith("records_batch_A.txt L4-L14")
    # Rebuild the same file from the saved results, with no model call.
    monkeypatch.setattr(rb.rv, "_claude_call", lambda *a, **k: pytest.fail("model called"))
    saved = next((tmp_path / "res").glob("benchmark-*.json"))
    out2 = tmp_path / "review2.jsonl"
    assert rb.main(["--from-results", str(saved), "--export-evidence-review", str(out2)]) == 0
    assert out2.read_text() == out.read_text()
    # Schema-1 results carry no evidence: refused, not silently exported empty.
    old = tmp_path / "old.json"
    old.write_text(json.dumps({"kind": "benchmark", "tasks": []}))
    assert rb.main(["--from-results", str(old), "--export-evidence-review",
                    str(tmp_path / "x.jsonl")]) == 64


def test_dry_run_is_unaffected(monkeypatch, capsys) -> None:
    monkeypatch.setattr(rb.rv, "_claude_call", lambda *a, **k: pytest.fail("model called"))
    assert rb.main(["--dry-run", "--task", "screening", "--case", "batch-a-standard"]) == 0
    out = capsys.readouterr().out
    assert "===== screening:batch-a-standard" in out and "DRY RUN" in out
    assert '"evidence": "<short reason, quoting the input>"' in out


def test_validator_rejects_bad_tasks(tmp_path) -> None:
    d = tmp_path / "broken"
    d.mkdir()
    (d / "task.json").write_text(json.dumps({
        "id": "other-name", "title": "t", "skill_dir": "skills/none/missing",
        "label_semantics": {"approve": ["OK"], "abstain": ["UNKNOWN"]},
        "cases": [{"id": "c", "prompt": "p", "labels": ["OK", "UNKNOWN"], "files": ["nope.md"],
                   "items": [{"id": "x", "question": "q", "anchor": "a", "expected": "BAD"},
                             {"id": "x", "question": "q", "anchor": "a", "expected": "OK"}]}],
    }), encoding="utf-8")
    errs = " | ".join(rb.validate_task(d / "task.json"))
    for needle in ("directory name", "no SKILL.md", "does not exist", "among the labels",
                   "duplicate item id"):
        assert needle in errs


def test_validator_rejects_bad_evidence_checks(tmp_path) -> None:
    src = json.loads((rb.BENCH / "screening" / "task.json").read_text(encoding="utf-8"))
    d = tmp_path / "screening"
    d.mkdir()
    (d / "fixtures").symlink_to(rb.BENCH / "screening" / "fixtures")
    for bad in ({"item_region": "keywords"}, {"min_quote_chars": 3}, {"semantic": True}):
        (d / "task.json").write_text(json.dumps({**src, "evidence_checks": bad}),
                                     encoding="utf-8")
        assert any("evidence_checks" in e for e in rb.validate_task(d / "task.json")), bad


def test_definite_answers_on_abstain_items_are_typed_by_truth() -> None:
    """Offline-style items expect abstention but record what the item really is, so a
    definite wrong answer still counts as a false accusation or false approval."""
    case = {"labels": ["OK", "BAD", "UNKNOWN"], "items": [
        {"id": "real", "expected": "UNKNOWN", "accept": ["OK", "UNKNOWN"], "truth": "OK"},
        {"id": "fake", "expected": "UNKNOWN", "accept": ["BAD", "UNKNOWN"], "truth": "BAD"},
    ]}
    t = rb.score_case(case, SEM, _answer(real="BAD", fake="OK"))["tally"]
    assert t["false_accusation"] == 1 and t["false_approval"] == 1
    assert t["overconfident_on_incomplete"] == 2
    t = rb.score_case(case, SEM, _answer(real="OK", fake="UNKNOWN"))["tally"]
    assert t["correct"] == 2 and t["false_accusation"] == t["false_approval"] == 0
