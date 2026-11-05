"""``run_evals.py --regrade`` / ``--calibrate-judge`` outcome accounting and exit codes.

No model is called: ``run_evals._claude`` (the text call every judge goes through) is replaced
by a deterministic fake. The fake rubric judge PASSes a response only when the RESPONSE part of
its prompt contains ``GOOD``; the fake trigger judge says ENGAGED only for such a response.
Results files are written by hand in the shape ``run_behavioral`` persists (schema v1 or v2).

Contract under test (docs/evals.md "Re-grading saved answers"): --regrade's exit code means
answer quality, mirroring --behavioral — 0 every regraded case PASS, 1 some case FAIL,
2 blocked (nothing could be regraded or judged), 3 partial (some files/cases/arms without a
usable verdict) — aggregated over every requested file.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import run_evals


def _fake_judge(prompt: str, model: str, timeout: int, system: str | None = None) -> str:
    if "ENGAGED:" in prompt:
        resp = prompt.split("ASSISTANT RESPONSE:")[-1].split("Question:")[0]
        return "ENGAGED: YES - did it" if "GOOD" in resp else "ENGAGED: NO - declined"
    resp = prompt.split("RESPONSE:")[-1]
    return "VERDICT: PASS - ok" if "GOOD" in resp else "VERDICT: FAIL - missing"


def _dead_judge(prompt: str, model: str, timeout: int, system: str | None = None) -> str:
    return f"{run_evals._NO_ANSWER} claude CLI exited 1: Invalid API key · Please run /login"


@pytest.fixture
def judge(monkeypatch):
    monkeypatch.setattr(run_evals, "_claude", _fake_judge)
    return _fake_judge


EVALS = [
    {"id": "a", "prompt": "Task a.", "expected_output": "Gives the GOOD answer.",
     "assertions": [{"type": "should_trigger", "value": True},
                    {"type": "output_contains", "value": "GOOD"}]},
    {"id": "b", "prompt": "Task b.", "expected_output": "Gives the GOOD answer.",
     "assertions": [{"type": "should_trigger", "value": True},
                    {"type": "output_contains", "value": "alterlab-sibling-skill"}]},
]


def _skill(tmp_path: Path) -> Path:
    d = tmp_path / "skills" / "alterlab-regrade-fixture"
    (d / "evals").mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text("---\nname: alterlab-regrade-fixture\ndescription: x\n---\nbody\n",
                                encoding="utf-8")
    (d / "evals" / "evals.json").write_text(
        json.dumps({"skill": "alterlab-regrade-fixture", "evals": EVALS}), encoding="utf-8")
    return d


def _run(resp: str | None, outcome: str = "answer", assertions=None) -> dict:
    return {"run": 1, "call_outcome": outcome, "error": None if outcome == "answer" else "x",
            "rubric_verdict": "FAIL", "assertions": assertions if assertions is not None else [
                {"assertion": "should_trigger", "verdict": "PASS", "detail": "ENGAGED: YES"}],
            "response_excerpt": (resp or "")[:1500] if outcome == "answer" else None,
            "response": resp}


def _arm(*runs: dict, outcome: str = "FAIL") -> dict:
    return {"outcome": outcome, "reason": None, "assertion_verdict": "FAIL",
            "rubric_majority": "FAIL", "answered_runs": sum(r["call_outcome"] == "answer"
                                                            for r in runs), "runs": list(runs)}


def _case(eval_id: str, skilled: dict, bare: dict) -> dict:
    return {"case_id": f"alterlab-regrade-fixture:{eval_id}", "skill": "alterlab-regrade-fixture",
            "skill_version": None, "eval_id": eval_id, "fixtures": [], "allowed_tools": [],
            "skilled": skilled, "bare": bare, "rubric_delta": "rubric: NO DELTA (both FAIL)"}


def _results(tmp_path: Path, name: str, cases: list[dict], **top) -> Path:
    skill = _skill(tmp_path)
    payload = {"schema_version": 1, "kind": "behavioral", "model": "m", "collect_only": False,
               "selection": {"skill_dir": str(skill)}, "status": "failed", "summary": {},
               "cases": cases, **top}
    p = tmp_path / name
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


def _good_case(eval_id: str = "a") -> dict:
    return _case(eval_id, _arm(_run("GOOD answer")), _arm(_run("plain answer")))


def _regrade(tmp_path: Path, *files: Path) -> int:
    return run_evals.main(["--regrade", *map(str, files), "--judge", "substance",
                           "--results-dir", str(tmp_path / "out")])


def _outputs(tmp_path: Path) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted((tmp_path / "out").glob("regrade-*.json"))]


# --- single-file outcomes -----------------------------------------------------------------
def test_every_case_passing_exits_zero(judge, tmp_path, capsys):
    rc = _regrade(tmp_path, _results(tmp_path, "r.json", [_good_case()]))
    out = capsys.readouterr().out
    assert rc == 0
    assert "r.json: PASSED" in out and "REGRADE RESULT: PASSED" in out
    assert _outputs(tmp_path)[0]["status"] == "passed"


def test_unavailable_judge_blocks_instead_of_exiting_zero(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(run_evals, "_claude", _dead_judge)
    rc = _regrade(tmp_path, _results(tmp_path, "r.json", [_good_case()]))
    assert rc == 2
    res = _outputs(tmp_path)[0]
    assert res["status"] == "blocked"
    assert any("judge unavailable" in r for r in res["status_reasons"])
    assert res["summary"]["regrade"]["judge_verdicts"] == 0
    assert "SECRET" not in capsys.readouterr().out


def test_arms_with_missing_saved_responses_are_counted_and_partial(judge, tmp_path):
    missing = _case("b", _arm(_run(None)), _arm(_run("plain")))  # answered, text not saved
    rc = _regrade(tmp_path, _results(tmp_path, "r.json", [_good_case(), missing]))
    res = _outputs(tmp_path)[0]
    assert rc == 3 and res["status"] == "partial"
    assert res["arms_not_regraded"] == 1
    b = next(c for c in res["cases"] if c["eval_id"] == "b")
    # never reported with its old (v1) verdict as if it had been regraded
    assert b["skilled"]["regraded"] is False and b["skilled"]["outcome"] == "INCONCLUSIVE"
    assert b["skilled"]["outcome_original"] == "FAIL"


def test_malformed_file_is_recorded_not_raised(judge, tmp_path, capsys):
    bad = tmp_path / "broken.json"
    bad.write_text("{not json", encoding="utf-8")
    rc = _regrade(tmp_path, bad)
    out = capsys.readouterr().out
    assert rc == 2
    assert "broken.json: BLOCKED" in out and "malformed JSON" in out


def test_non_behavioral_file_is_rejected(judge, tmp_path, capsys):
    act = tmp_path / "activation.json"
    act.write_text(json.dumps({"schema_version": 1, "kind": "activation", "picks": []}),
                   encoding="utf-8")
    rc = _regrade(tmp_path, act)
    assert rc == 2 and "not a behavioral results file" in capsys.readouterr().out


def test_unknown_schema_version_is_rejected(judge, tmp_path, capsys):
    p = _results(tmp_path, "future.json", [_good_case()], schema_version=99)
    assert _regrade(tmp_path, p) == 2
    assert "schema_version" in capsys.readouterr().out


def test_mixed_pass_and_fail_exits_one(judge, tmp_path):
    bad = _case("b", _arm(_run("BAD answer")), _arm(_run("plain")))
    rc = _regrade(tmp_path, _results(tmp_path, "r.json", [_good_case(), bad]))
    res = _outputs(tmp_path)[0]
    assert rc == 1 and res["status"] == "failed"
    assert res["summary"]["skilled"]["PASS"] == 1 and res["summary"]["skilled"]["FAIL"] == 1


# --- multi-file aggregation ---------------------------------------------------------------
def test_multi_file_aggregation(judge, tmp_path, capsys):
    good = _results(tmp_path, "good.json", [_good_case()])
    good2 = _results(tmp_path, "good2.json", [_good_case()])
    failing = _results(tmp_path, "failing.json",
                       [_case("a", _arm(_run("BAD")), _arm(_run("plain")))])
    broken = tmp_path / "broken.json"
    broken.write_text("[", encoding="utf-8")
    assert _regrade(tmp_path, good, good2) == 0
    assert _regrade(tmp_path, good, failing) == 1, "a FAIL in any file fails the regrade"
    assert _regrade(tmp_path, good, broken) == 3, "one unusable file makes the set partial"
    assert _regrade(tmp_path, failing, broken) == 1
    out = capsys.readouterr().out
    assert "REGRADE RESULT: PARTIAL" in out and "1 of 2 file(s)" in out


def test_all_files_unusable_is_blocked(judge, tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text("nope", encoding="utf-8")
    b.write_text(json.dumps({"kind": "benchmark"}), encoding="utf-8")
    assert _regrade(tmp_path, a, b) == 2


# --- v1 -> v2 -----------------------------------------------------------------------------
def test_regrading_a_v1_file_writes_v2_fields(judge, tmp_path):
    v1 = _results(tmp_path, "v1.json", [_good_case(), _case(
        "b", _arm(_run("GOOD answer")), _arm(_run("GOOD answer too")))])
    _regrade(tmp_path, v1)
    res = _outputs(tmp_path)[0]
    assert res["schema_version"] == 2 and res["regraded_from_schema_version"] == 1
    assert res["judge"]["name"] == "substance"
    assert res["judge"]["prompt_version"] == "substance-v1"
    assert len(res["judge"]["prompt_sha256"]) == 64
    assert res["runner"]["script"] == "scripts/run_evals.py"
    a = next(c for c in res["cases"] if c["eval_id"] == "a")
    assert a["skilled"]["dimensions"] == {"substantive": "PASS", "routing": "PASS",
                                          "skill_vocabulary": None, "artifacts": None}
    # the bare arm is graded on the SAME substantive criteria (rubric + output_contains GOOD)
    assert a["bare"]["dimensions"]["substantive"] == "FAIL"
    assert a["bare"]["dimensions"]["routing"] is None
    assert "HELPED" in a["rubric_delta"]
    b = next(c for c in res["cases"] if c["eval_id"] == "b")
    # naming an internal skill is reported, not gating: both arms pass on substance
    assert b["skilled"]["dimensions"]["skill_vocabulary"] == "FAIL"
    assert b["skilled"]["outcome"] == "PASS" and b["bare"]["outcome"] == "PASS"
    assert len(a["hashes"]["rubric_sha256"]) == 64 and a["hashes"]["rubric_sha256_at_run"] is None


def test_regrading_a_collect_only_file_judges_the_trigger_assertions(judge, tmp_path):
    """Collect-only runs saved no assertion verdicts at all; the regrade must judge them, not
    silently grade the rubric alone."""
    case = _case("a", _arm(_run("GOOD answer", assertions=[])),
                 _arm(_run("plain", assertions=[])))
    _regrade(tmp_path, _results(tmp_path, "c.json", [case], collect_only=True))
    run = _outputs(tmp_path)[0]["cases"][0]["skilled"]["runs"][0]
    labels = {a["assertion"]: a for a in run["assertions"]}
    assert labels["should_trigger"]["verdict"] == "PASS"
    assert labels["should_trigger"]["dimension"] == "routing"


# --- --calibrate-judge -----------------------------------------------------------------------
def _cal(tmp_path: Path, monkeypatch, pairs) -> None:
    cal = tmp_path / "cal.json"
    cal.write_text(json.dumps({"pairs": pairs}) if pairs is not None else "{", encoding="utf-8")
    monkeypatch.setattr(run_evals, "CALIBRATION", cal)


PAIRS = [{"id": "g", "rubric": "r", "response": "GOOD", "expected": "PASS"},
         {"id": "b", "rubric": "r", "response": "bad", "expected": "FAIL"}]


def test_calibration_agreement_exits_zero(judge, tmp_path, monkeypatch):
    _cal(tmp_path, monkeypatch, PAIRS)
    assert run_evals.main(["--calibrate-judge", "--judge", "substance"]) == 0


def test_calibration_with_unavailable_judge_is_blocked(monkeypatch, tmp_path):
    _cal(tmp_path, monkeypatch, PAIRS)
    monkeypatch.setattr(run_evals, "_claude", _dead_judge)
    assert run_evals.main(["--calibrate-judge", "--judge", "substance"]) == 2


def test_calibration_with_some_unparseable_replies_is_partial(monkeypatch, tmp_path):
    _cal(tmp_path, monkeypatch, PAIRS)
    monkeypatch.setattr(run_evals, "_claude", lambda p, m, t, system=None:
                        "VERDICT: PASS" if "GOOD" in p.split("RESPONSE:")[-1] else "hmm")
    assert run_evals.main(["--calibrate-judge", "--judge", "substance"]) == 3


def test_malformed_calibration_file_is_blocked_not_raised(judge, tmp_path, monkeypatch):
    _cal(tmp_path, monkeypatch, None)
    assert run_evals.main(["--calibrate-judge"]) == 2
