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
4. The abstract comes from Crossref, falling back to Semantic Scholar, then Europe PMC (all
   keyless); a rate-limited source is reported as not checked, never as "no abstract". No test
   here touches the network: the fetch tests replace ``urlopen`` with an in-memory router.
"""

from __future__ import annotations

import email.message
import importlib.util
import io
import json
import sys
import urllib.error
import urllib.parse
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


# --------------------------------------------------------------------------- #
# Abstract fallback chain: Crossref -> Semantic Scholar -> Europe PMC           #
# --------------------------------------------------------------------------- #

_DOI = "10.18653/v1/N19-1423"
_S2_ABSTRACT = "We introduce a new language representation model called BERT."
_EPMC_ABSTRACT = "Deep learning allows computational models to learn representations of data."


class _Resp(io.BytesIO):
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _http_error(url: str, code: int):
    return urllib.error.HTTPError(url, code, "error", email.message.Message(), None)


def _route(monkeypatch, answers: dict) -> list:
    """Serve canned answers by host: a dict (JSON body), an int (HTTP error), or a list of
    those consumed one per call. Returns the list of URLs requested; sleeps are recorded
    as ("sleep", seconds) entries so backoff is observable without waiting."""
    calls: list = []

    def fake_urlopen(req, timeout=None):
        url = req.full_url
        calls.append(url)
        host = urllib.parse.urlsplit(url).hostname
        assert host in answers, f"unexpected host contacted: {url}"
        ans = answers[host]
        if isinstance(ans, list):
            ans = ans.pop(0) if len(ans) > 1 else ans[0]
        if isinstance(ans, int):
            raise _http_error(url, ans)
        return _Resp(json.dumps(ans).encode())

    monkeypatch.setattr(cf.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(cf.time, "sleep", lambda s: calls.append(("sleep", s)))
    return calls


_CR_EMPTY = {"message": {"DOI": _DOI, "title": ["BERT"]}}  # Crossref record, no abstract
_CR_ABSTRACT = {"message": {"abstract": "<jats:p>Crossref <jats:italic>abstract</jats:italic> text.</jats:p>"}}
_EPMC_HIT = {"resultList": {"result": [{"doi": "10.1038/NATURE14539", "abstractText": _EPMC_ABSTRACT}]}}


def test_crossref_abstract_is_used_first(monkeypatch) -> None:
    calls = _route(monkeypatch, {"api.crossref.org": _CR_ABSTRACT})
    text, source, status = cf.fetch_abstract_detailed("https://doi.org/" + _DOI)
    assert (text, source) == ("Crossref abstract text.", "crossref")
    assert status == {"crossref": "abstract"} and len(calls) == 1


def test_semantic_scholar_supplies_the_abstract_when_crossref_has_none(monkeypatch) -> None:
    calls = _route(monkeypatch, {"api.crossref.org": _CR_EMPTY,
                                 "api.semanticscholar.org": {"abstract": _S2_ABSTRACT}})
    text, source, status = cf.fetch_abstract_detailed(_DOI)
    assert (text, source) == (_S2_ABSTRACT, "semanticscholar")
    assert status == {"crossref": "no_abstract", "semanticscholar": "abstract"}
    s2 = [u for u in calls if "semanticscholar" in str(u)]
    assert s2 == [f"https://api.semanticscholar.org/graph/v1/paper/DOI:{_DOI}?fields=abstract"]


def test_europe_pmc_supplies_the_abstract_when_the_others_have_none(monkeypatch) -> None:
    calls = _route(monkeypatch, {"api.crossref.org": {"message": {}},
                                 "api.semanticscholar.org": 404,
                                 "www.ebi.ac.uk": _EPMC_HIT})
    r = cf.score_pair("Deep learning learns representations of data.", "10.1038/nature14539")
    assert r.source == "europepmc" and r.abstract_found is True and r.evidence_scope == "abstract"
    assert r.signals["abstract_sources"] == {"crossref": "no_abstract", "semanticscholar": "not_found",
                                             "europepmc": "abstract"}
    (epmc,) = [u for u in calls if "ebi.ac.uk" in str(u)]
    q = urllib.parse.parse_qs(urllib.parse.urlsplit(epmc).query)
    assert q["query"] == ['DOI:"10.1038/nature14539"'] and q["resultType"] == ["core"]
    assert r.counts_as_verified is False


def test_europe_pmc_ignores_records_with_another_doi(monkeypatch) -> None:
    other = {"resultList": {"result": [{"doi": "10.1000/other", "abstractText": "Unrelated."}]}}
    _route(monkeypatch, {"api.crossref.org": 404, "api.semanticscholar.org": 404, "www.ebi.ac.uk": other})
    text, source, status = cf.fetch_abstract_detailed("10.1038/nature14539")
    assert text is None and source == ""
    assert status == {"crossref": "not_found", "semanticscholar": "not_found", "europepmc": "not_found"}


def test_semantic_scholar_429_backs_off_then_is_not_checked(monkeypatch) -> None:
    calls = _route(monkeypatch, {"api.crossref.org": _CR_EMPTY, "api.semanticscholar.org": 429,
                                 "www.ebi.ac.uk": {"resultList": {"result": []}}})
    r = cf.score_pair("A claim about BERT.", _DOI)
    assert [c for c in calls if isinstance(c, tuple)] == [("sleep", s) for s in cf.S2_BACKOFF]
    assert len([u for u in calls if "semanticscholar" in str(u)]) == len(cf.S2_BACKOFF) + 1
    assert r.signals["abstract_sources"]["semanticscholar"] == "rate_limited"  # not "not_found"
    assert r.abstract_found is False and r.verdict == "unsupported" and r.evidence_scope == "none"
    assert "Not checked: semanticscholar" in r.rationale and "retry later" in r.rationale


def test_semantic_scholar_recovers_after_one_429(monkeypatch) -> None:
    calls = _route(monkeypatch, {"api.crossref.org": _CR_EMPTY,
                                 "api.semanticscholar.org": [429, {"abstract": _S2_ABSTRACT}]})
    text, source, _ = cf.fetch_abstract_detailed(_DOI)
    assert (text, source) == (_S2_ABSTRACT, "semanticscholar")
    assert [c for c in calls if isinstance(c, tuple)] == [("sleep", cf.S2_BACKOFF[0])]


def test_crossref_rate_limit_is_not_reported_as_not_found(monkeypatch) -> None:
    _route(monkeypatch, {"api.crossref.org": 429, "api.semanticscholar.org": 503, "www.ebi.ac.uk": 500})
    r = cf.score_pair("A claim.", _DOI)
    assert r.signals["abstract_sources"] == {"crossref": "rate_limited", "semanticscholar": "error",
                                             "europepmc": "error"}
    assert "Not checked: crossref, semanticscholar, europepmc" in r.rationale


def test_no_abstract_anywhere_has_no_caveat(monkeypatch) -> None:
    _route(monkeypatch, {"api.crossref.org": _CR_EMPTY, "api.semanticscholar.org": {"abstract": None},
                         "www.ebi.ac.uk": {"resultList": {"result": []}}})
    r = cf.score_pair("A claim.", _DOI)
    assert r.abstract_found is False and "Not checked" not in r.rationale
    assert "Crossref, Semantic Scholar or Europe PMC" in r.rationale


def test_openalex_is_gone() -> None:
    assert not hasattr(cf, "_reconstruct_openalex_abstract")
    assert [name for name, _ in cf.ABSTRACT_SOURCES] == ["crossref", "semanticscholar", "europepmc"]
    assert "api.openalex.org" not in SCRIPT.read_text(encoding="utf-8")
