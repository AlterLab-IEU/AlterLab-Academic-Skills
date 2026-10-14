"""Pin the claim checker's honesty contract.

1. The tool never emits VERIFIED: a heuristic ``support`` is LEXICAL_MATCH_REQUIRES_REVIEW and a
   model-judged ``support`` is MODEL_JUDGED_SUPPORT_REQUIRES_REVIEW; ``counts_as_verified`` is
   always False.
2. Deterministic guards stop a lexical match from reaching ``support`` on the failure modes an
   external review found (each previously returned support -> VERIFIED at confidence 0.6): role
   reversal, a wrong figure, humans vs animal/in-vitro evidence, and a definite claim against
   tentative evidence — plus the related age-group, causal-vs-association, and missing-comparison
   cases. The same guards veto a model's ``support``.
3. Controls still reach a lexical match, so the guards cannot pass these tests by abstaining on
   everything.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent / "skills" / "core" / "alterlab-citation-verifier"
SCRIPT = SKILL / "scripts" / "claim_faithfulness.py"
FIXTURE = SKILL / "evals" / "fixtures" / "claim_faithfulness_adversarial.json"
_spec = importlib.util.spec_from_file_location("claim_faithfulness", SCRIPT)
cf = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("claim_faithfulness", cf)  # dataclasses resolve their module here
_spec.loader.exec_module(cf)

_CASES = json.loads(FIXTURE.read_text(encoding="utf-8"))
_ADVERSARIAL = _CASES["must_not_support"]
_CONTROLS = _CASES["controls"]


@pytest.mark.parametrize("case", _ADVERSARIAL, ids=lambda c: c["id"])
def test_adversarial_pairs_never_reach_support(case: dict) -> None:
    r = cf.heuristic_score(case["claim"], case["abstract"])
    assert r.verdict != "support", r.rationale
    assert r.taxonomy != "VERIFIED"
    assert r.counts_as_verified is False


@pytest.mark.parametrize("case", _CONTROLS, ids=lambda c: c["id"])
def test_controls_still_reach_a_lexical_match(case: dict) -> None:
    r = cf.heuristic_score(case["claim"], case["abstract"])
    assert r.verdict == "support", r.rationale
    assert r.taxonomy == cf.HEURISTIC_SUPPORT_TAXONOMY == "LEXICAL_MATCH_REQUIRES_REVIEW"
    assert r.requires_review is True and r.counts_as_verified is False
    assert r.method == "lexical-heuristic" and r.evidence_scope == "abstract"
    assert r.confidence <= 0.60


@pytest.mark.parametrize("case_id, needle", [
    ("role-reversal", "role reversal"),
    ("role-reversal-than", "role reversal"),
    ("number-mismatch", "50"),
    ("humans-vs-mice", "animal"),
    ("humans-vs-in-vitro", "in-vitro"),
    ("children-vs-adults", "population mismatch"),
    ("definite-vs-tentative", "tentative"),
    ("causal-vs-association", "association"),
    ("comparison-not-in-abstract", "not stated"),
])
def test_each_guard_names_its_reason(case_id: str, needle: str) -> None:
    case = next(c for c in _ADVERSARIAL if c["id"] == case_id)
    r = cf.heuristic_score(case["claim"], case["abstract"])
    assert any(needle in g for g in r.signals["guards"]), r.signals["guards"]


def test_no_label_in_the_tool_is_verified() -> None:
    assert "VERIFIED" not in cf.TAXONOMY_MAP.values()
    assert cf.TAXONOMY_MAP["support"] == "MODEL_JUDGED_SUPPORT_REQUIRES_REVIEW"


def _fake_llm(monkeypatch, verdict: str) -> None:
    class Proc:
        stdout = json.dumps({"verdict": verdict, "confidence": 0.9, "rationale": "looks fine"})
    monkeypatch.setattr(cf, "_claude_cli_available", lambda: True)
    monkeypatch.setattr(cf.subprocess, "run", lambda *a, **k: Proc())


def test_model_support_is_not_verification(monkeypatch) -> None:
    _fake_llm(monkeypatch, "support")
    c = next(c for c in _CONTROLS if c["id"] == "consistent-direction")
    r = cf.llm_score(c["claim"], c["abstract"])
    assert r.verdict == "support" and r.tier == "llm" and r.method == "model-judgment"
    assert r.taxonomy == "MODEL_JUDGED_SUPPORT_REQUIRES_REVIEW"
    assert r.counts_as_verified is False and r.requires_review is True


@pytest.mark.parametrize("case_id", ["role-reversal", "number-mismatch", "humans-vs-mice",
                                     "definite-vs-tentative"])
def test_guards_veto_a_model_support(monkeypatch, case_id: str) -> None:
    _fake_llm(monkeypatch, "support")
    c = next(c for c in _ADVERSARIAL if c["id"] == case_id)
    r = cf.llm_score(c["claim"], c["abstract"])
    assert r.verdict == "unsupported" and "Model judged support, but" in r.rationale


def test_fallback_reason_stays_visible(monkeypatch) -> None:
    monkeypatch.setattr(cf, "_claude_cli_available", lambda: False)
    c = _CONTROLS[0]
    r = cf.llm_score(c["claim"], c["abstract"])
    assert r.tier == "llm->heuristic-fallback" and "unavailable" in r.fallback_reason
    assert r.method == "lexical-heuristic" and r.taxonomy == "LEXICAL_MATCH_REQUIRES_REVIEW"


def test_missing_abstract_has_no_evidence_scope() -> None:
    r = cf.score_pair("A claim.", "10.0000/x", abstract_override="")
    assert r.verdict == "unsupported" and r.evidence_scope == "none" and r.method == "none"
    assert r.abstract_found is False and r.counts_as_verified is False


def test_explicit_negation_abstains() -> None:
    r = cf.heuristic_score("Drug X reduces mortality in adults.",
                           "Drug X did not reduce mortality in adults.")
    assert r.verdict != "support"


def test_self_test_passes() -> None:
    assert cf.run_self_test() == 0
