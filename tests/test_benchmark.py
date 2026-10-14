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


def test_parse_answer_takes_the_last_json_block_and_first_duplicate() -> None:
    text = ("draft ```json\n{\"items\": [{\"id\": \"a\", \"label\": \"BAD\"}]}\n```\nfinal:\n"
            "```json\n{\"items\": [{\"id\": \"a\", \"label\": \"OK\"}, "
            "{\"id\": \"a\", \"label\": \"BAD\"}]}\n```")
    assert rb.parse_answer(text) == {"a": {"label": "OK", "value": None}}
    assert rb.parse_answer("no json here") is None


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
