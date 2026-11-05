"""Regression tests: what verify_citations.py may and may not conclude.

These cover defects found by an external review of v4.0.0 (each reproduced on that code
before the repair):

* A1 — a DOI that resolves to the right work cleared an author list containing an invented
  co-author (``verified`` / PASS with author_overlap 0.667). Existence and metadata agreement
  are now reported separately, and an explicitly cited author the record does not support is
  flagged.
* A2 — surname comparison used unrestricted substring matching, so ``Li`` matched
  ``Williams``. Surnames are now compared token-wise after careful normalisation.
* A3 — absence from the indexes that answered was reported as Total Fabrication. Absence is
  now ``NOT_FOUND`` (not found in the checked sources); an unregistered identifier is
  ``ID_INVALID`` (the identifier is wrong; whether the work exists is undetermined).
* A4 — one host's connection failure (``NetworkUnavailable``) stopped the source loop, so the
  remaining sources were never asked.
* A5 — ``retracted: false`` was reported even when Crossref (the only retraction source) never
  answered; retraction status is now flagged / not flagged in checked sources / unknown.

No test touches the network: the HTTP layer is replaced by an in-memory router per host.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "skills" / "core" / "alterlab-citation-verifier" / "scripts" / "verify_citations.py"
MODULE_NAME = "alterlab_verify_citations_reliability"


def _load():
    spec = importlib.util.spec_from_file_location(MODULE_NAME, SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


vc = _load()
REAL_HTTP_GET = vc._http_get


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def guard(*args, **kwargs):
        pytest.fail(f"test attempted network access: {args[:1]}")

    monkeypatch.setattr(vc, "_http_get", guard)
    monkeypatch.setattr(vc.urllib.request, "urlopen", guard)
    monkeypatch.setattr(vc, "_HAS_REQUESTS", False)
    monkeypatch.setattr(vc, "_requests", None)
    monkeypatch.setattr(vc.time, "sleep", lambda _s: None)
    monkeypatch.setattr(vc, "_COOLDOWN_UNTIL", {})


EMPTY = {
    "api.crossref.org": None,
    "api.semanticscholar.org": None,
    "www.ebi.ac.uk": {"hitCount": 0, "resultList": {"result": []}},
    "export.arxiv.org": '<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>',
    "openlibrary.org": {"numFound": 0, "docs": []},
    "doi.org": {"responseCode": 1},
    "arxiv.org": "<html>abs page</html>",
}


def route(monkeypatch, calls=None, **overrides):
    """Answer by host. Keyword names use '_' for '.', e.g. api_crossref_org=...; a value may be
    an exception instance (raised), a callable(url) (called), or the JSON/text answer."""
    answers = dict(EMPTY)
    for k, v in overrides.items():
        answers[k.replace("_", ".")] = v
    calls = [] if calls is None else calls

    def fake(url, mailto, accept="application/json", extra_headers=None):
        host = vc.urllib.parse.urlsplit(url).hostname
        calls.append(host)
        if host not in answers:
            pytest.fail(f"unexpected host {host}")
        ans = answers[host]
        if isinstance(ans, Exception):
            raise ans
        if callable(ans):
            return ans(url)
        return ans

    monkeypatch.setattr(vc, "_http_get", fake)
    return calls


def entry(text):
    (e,) = vc.parse_input(text).entries
    return e


DEEP_LEARNING_CR = {"message": {
    "title": ["Deep learning"], "DOI": "10.1038/nature14539",
    "author": [{"family": "LeCun", "given": "Yann"}, {"family": "Bengio", "given": "Yoshua"},
               {"family": "Hinton", "given": "Geoffrey"}],
    "issued": {"date-parts": [[2015]]}}}


def bib_deep(authors: str, year: str = "2015") -> str:
    return ("@article{lecun2015, title={Deep learning}, author={" + authors + "}, year={" + year
            + "}, doi={10.1038/nature14539}}")


# --------------------------------------------------------------------------- #
# A1 — existence vs metadata                                                   #
# --------------------------------------------------------------------------- #

def test_correct_full_reference_passes(monkeypatch):
    route(monkeypatch, api_crossref_org=DEEP_LEARNING_CR)
    r = vc.verify_entry(entry(bib_deep("LeCun, Yann and Bengio, Yoshua and Hinton, Geoffrey")),
                        "", 0.7, False)
    assert r["verdict"] == "verified", r["detail"]
    assert r["existence"]["status"] == "found" and r["existence"]["method"] == "id"
    assert r["metadata"]["authors"]["status"] == "agrees"
    assert r["metadata"]["authors"]["unsupported"] == []
    assert r["metadata"]["year"]["status"] == "agrees"
    assert vc.build_report([r], "", 0.7, False)["summary"]["verdict"] == "PASS"


def test_invented_coauthor_is_flagged_even_though_the_doi_resolves(monkeypatch):
    route(monkeypatch, api_crossref_org=DEEP_LEARNING_CR)
    r = vc.verify_entry(entry(bib_deep("LeCun, Yann and Bengio, Yoshua and Inventedauthor, Alice")),
                        "", 0.7, False)
    assert r["existence"]["status"] == "found"          # the work exists ...
    assert r["metadata"]["authors"]["status"] == "disagrees"  # ... but not with these authors
    assert r["metadata"]["authors"]["unsupported"] == ["Inventedauthor, Alice"]
    assert r["verdict"] == "PAC" and r["severity"] != "NONE"
    assert "UNSUPPORTED_AUTHOR" in r["flags"]
    assert "Inventedauthor" in r["detail"]
    assert vc.build_report([r], "", 0.7, False)["summary"]["verdict"] != "PASS"


def test_one_correct_and_one_invented_author_is_flagged(monkeypatch):
    route(monkeypatch, api_crossref_org=DEEP_LEARNING_CR)
    r = vc.verify_entry(entry(bib_deep("LeCun, Yann and Inventedauthor, Alice")), "", 0.7, False)
    assert r["verdict"] == "PAC"
    assert r["metadata"]["authors"]["supported"] == ["LeCun, Yann"]
    assert r["metadata"]["authors"]["unsupported"] == ["Inventedauthor, Alice"]


@pytest.mark.parametrize("text", [
    bib_deep("LeCun, Yann and others"),
    "LeCun, Y., et al. (2015). Deep learning. Nature, 521, 436-444. https://doi.org/10.1038/nature14539",
])
def test_legitimate_et_al_is_not_an_accusation(monkeypatch, text):
    route(monkeypatch, api_crossref_org=DEEP_LEARNING_CR)
    r = vc.verify_entry(entry(text), "", 0.7, False)
    assert r["verdict"] == "verified", r["detail"]
    a = r["metadata"]["authors"]
    assert a["status"] == "agrees" and a["et_al"] is True and a["unsupported"] == []


def test_abbreviated_author_list_without_et_al_is_noted_not_accused(monkeypatch):
    route(monkeypatch, api_crossref_org=DEEP_LEARNING_CR)
    r = vc.verify_entry(entry(bib_deep("LeCun, Yann and Bengio, Yoshua")), "", 0.7, False)
    assert r["verdict"] == "verified"
    assert r["metadata"]["authors"]["omitted_record_authors"] == 1


def test_missing_author_metadata_is_not_confirmed_agreement(monkeypatch):
    no_authors = {"message": {**DEEP_LEARNING_CR["message"], "author": []}}
    route(monkeypatch, api_crossref_org=no_authors)
    r = vc.verify_entry(entry(bib_deep("LeCun, Yann and Inventedauthor, Alice")), "", 0.7, False)
    assert r["metadata"]["authors"]["status"] == "unknown"   # nothing to compare against
    assert r["metadata"]["authors"]["supported"] == []       # never "agreed"
    assert r["author_overlap"] is None
    # A DOI-only citation has no authors to check at all.
    route(monkeypatch, api_crossref_org=DEEP_LEARNING_CR)
    r = vc.verify_entry(entry("10.1038/nature14539"), "", 0.7, False)
    assert r["metadata"]["authors"]["status"] == "not_checked"
    assert r["metadata"]["year"]["status"] == "not_checked"
    assert r["verdict"] == "verified"


def test_doi_existence_is_reported_independently_of_metadata(monkeypatch):
    route(monkeypatch, api_crossref_org=DEEP_LEARNING_CR)
    r = vc.verify_entry(entry(bib_deep("LeCun, Yann and Bengio, Yoshua and Hinton, Geoffrey", "2019")),
                        "", 0.7, False)
    assert r["existence"] == {**r["existence"], "status": "found", "method": "id"}
    assert r["identifier"]["doi"]["status"] == "resolves_to_cited_work"
    assert r["metadata"]["year"]["status"] == "disagrees" and r["verdict"] == "PAC"


# --------------------------------------------------------------------------- #
# A2 — surname matching                                                        #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("cited, found", [
    (["Li"], ["Williams"]),
    (["Ng"], ["Wang"]),
    (["Wang"], ["Wangari"]),
    (["Lee"], ["Ashlee"]),
    (["Smith, J."], ["Smithson"]),
    (["Organization"], ["World Health Organization"]),
])
def test_unrelated_names_sharing_a_substring_do_not_match(cited, found):
    assert vc.author_overlap(cited, found) == 0.0


@pytest.mark.parametrize("cited, found", [
    (["Li, Wei"], ["Li"]),                              # short surname, exact
    (["Ng AY"], ["Ng"]),                                # Vancouver-style trailing initials
    (["Roediger HL", "Karpicke JD"], ["Roediger", "Karpicke"]),
    (["van der Waals, J. D."], ["Waals"]),              # particle surname vs bare last token
    (["Ludwig van Beethoven"], ["van Beethoven"]),
    (["García Márquez, Gabriel"], ["Márquez"]),         # compound vs last token
    (["Garcia-Marquez, G."], ["García Márquez"]),       # hyphen, accents
    (["M{\\\"u}ller, A."], ["Müller"]),                # LaTeX accent
    (["Mueller, A."], ["Müller"]),                      # explicit German umlaut transliteration
    (["Öztürk, Ş."], ["Ozturk"]),                       # Turkish letters
    (["Işık, A."], ["Isik"]),                           # dotless i
    (["O'Brien, P."], ["OBrien"]),
    (["World Health Organization"], ["World Health Organization"]),
    (["WHO"], ["World Health Organization"]),           # acronym of an organisation
    (["OECD"], ["OECD"]),
])
def test_legitimate_name_variants_match(cited, found):
    assert vc.author_overlap(cited, found) == 1.0


def test_author_overlap_is_none_without_lists():
    assert vc.author_overlap([], ["Smith"]) is None
    assert vc.author_overlap(["Smith"], []) is None


# --------------------------------------------------------------------------- #
# A3 — absence is not fabrication                                              #
# --------------------------------------------------------------------------- #

GREY = ("Ministry of National Education. (2009). Regional teacher survey technical report. "
        "Ankara: MEB Press.")


def test_obscure_grey_literature_absent_from_every_index_is_not_found_not_fabricated(monkeypatch):
    route(monkeypatch)
    r = vc.verify_entry(entry(GREY), "", 0.7, False)
    assert r["verdict"] == "NOT_FOUND" and r["verdict"] != "TF"
    assert r["existence"]["status"] == "not_found"
    assert "fabricat" not in r["detail"].lower() or "not evidence" in r["detail"].lower()
    assert set(r["existence"]["sources_answered"]) >= {"crossref", "europepmc"}
    report = vc.build_report([r], "", 0.7, False)
    assert report["summary"]["verdict"] == "REVIEW_REQUIRED"
    assert report["summary"]["verdict_counts"]["TF"] == 0


def test_obscure_real_book_found_only_in_open_library_is_verified(monkeypatch):
    ol = {"numFound": 1, "docs": [{"title": "Köy enstitüleri", "author_name": ["Fay Kirby"],
                                   "first_publish_year": 1962, "publish_year": [1962, 2000]}]}
    route(monkeypatch, openlibrary_org=ol)
    r = vc.verify_entry(entry("Kirby, F. (2000). Köy enstitüleri. Ankara: İmece."), "", 0.7, False)
    assert r["verdict"] == "verified", r["detail"]
    # Crossref has no record of this book, so no retraction check could be made for it.
    assert r["retraction"]["status"] == "unknown"


def test_unregistered_doi_is_an_identifier_problem_not_proof_of_fabrication(monkeypatch):
    route(monkeypatch, doi_org=None)  # Handle API answers 404: not registered
    r = vc.verify_entry(entry("@article{k, title={A real work cited with a typo DOI}, author={Doe, J.}, "
                              "year={2020}, doi={10.1234/typo123}}"), "", 0.7, False)
    assert r["verdict"] == "ID_INVALID" and r["verdict"] != "TF"
    assert r["existence"]["status"] == "identifier_invalid"
    assert r["identifier"]["doi"]["status"] == "unregistered"
    assert "undetermined" in r["detail"] or "not established" in r["detail"]
    assert vc.build_report([r], "", 0.7, False)["summary"]["verdict"] == "FAIL"


def test_unregistered_doi_but_the_work_is_found_by_title_is_metadata_corruption(monkeypatch):
    rec = {"message": {"items": [{"title": ["A real work cited with a typo DOI"],
                                  "author": [{"family": "Doe"}], "issued": {"date-parts": [[2020]]},
                                  "DOI": "10.1234/correct"}]}}

    def crossref(url):
        return None if "/works/10.1234" in url else rec

    route(monkeypatch, api_crossref_org=crossref, doi_org=None)
    r = vc.verify_entry(entry("@article{k, title={A real work cited with a typo DOI}, author={Doe, J.}, "
                              "year={2020}, doi={10.1234/typo123}}"), "", 0.7, False)
    assert r["verdict"] == "PAC" and r["existence"]["status"] == "found"
    assert r["identifier"]["doi"]["status"] in ("does_not_resolve_to_cited_work", "unregistered")


def test_nonexistent_arxiv_id_is_id_invalid(monkeypatch):
    route(monkeypatch, arxiv_org=None)  # arxiv.org/abs answers 404
    r = vc.verify_entry(entry("@misc{a, title={Some preprint}, author={Doe, J.}, year={2023}, "
                              "eprint={2399.99999}}"), "", 0.7, False)
    assert r["verdict"] == "ID_INVALID" and r["identifier"]["arxiv"]["status"] == "not_found"


def test_malformed_doi_field_is_reported(monkeypatch):
    route(monkeypatch)
    e = entry("@article{m, title={Some title of a paper}, author={Doe, J.}, year={2020}, doi={10.12/x}}")
    assert e.doi == ""
    assert any("DOI" in w for w in e.warnings)
    r = vc.verify_entry(e, "", 0.7, False)
    assert r["identifier"]["doi"]["status"] == "malformed"


def test_source_outage_never_yields_not_found(monkeypatch):
    route(monkeypatch, api_crossref_org=vc.SourceError("no answer after retries (HTTP 503)"))
    r = vc.verify_entry(entry(GREY), "", 0.7, False)
    assert r["verdict"] == "unverified" and r["existence"]["status"] == "unavailable"


# --------------------------------------------------------------------------- #
# A4 — a single source's connection failure                                    #
# --------------------------------------------------------------------------- #

EPMC_HIT = {"resultList": {"result": [{"title": "A study with no identifier.", "authorString": "Doe J.",
                                       "pubYear": "2020", "doi": ""}]}}
NOID = "@article{noid, title={A study with no identifier}, author={Doe, J.}, year={2020}}"


def test_first_source_unreachable_second_verifies(monkeypatch):
    calls = route(monkeypatch, calls=[], api_crossref_org=vc.NetworkUnavailable("DNS failure"),
                  www_ebi_ac_uk=EPMC_HIT)
    r = vc.verify_entry(entry(NOID), "", 0.7, False)
    assert r["verdict"] == "verified", r["detail"]
    assert r["source_status"]["crossref"] == "offline"
    assert r["source_status"]["europepmc"] == "record"
    assert {"api.semanticscholar.org", "www.ebi.ac.uk", "export.arxiv.org"} <= set(calls)


def test_all_sources_unreachable_is_unverified(monkeypatch):
    down = vc.NetworkUnavailable("no route")
    route(monkeypatch, api_crossref_org=down, api_semanticscholar_org=down, www_ebi_ac_uk=down,
          export_arxiv_org=down, openlibrary_org=down)
    r = vc.verify_entry(entry(NOID), "", 0.7, False)
    assert r["verdict"] == "unverified" and "network" in r["detail"]
    assert set(r["source_status"].values()) == {"offline"}


def test_rate_limit_then_alternate_source_verifies(monkeypatch):
    route(monkeypatch, api_crossref_org=vc.SourceError("HTTP 429 — rate limited; retry later"),
          api_semanticscholar_org=vc.SourceError("HTTP 429 — rate limited"), www_ebi_ac_uk=EPMC_HIT)
    r = vc.verify_entry(entry(NOID), "", 0.7, False)
    assert r["verdict"] == "verified"
    assert r["source_status"]["crossref"].startswith("error: HTTP 429")


def test_sources_answer_but_find_nothing_is_not_found(monkeypatch):
    route(monkeypatch)
    r = vc.verify_entry(entry(NOID), "", 0.7, False)
    assert r["verdict"] == "NOT_FOUND"
    assert all(st == "no_record" for st in r["source_status"].values())


def test_an_unreachable_host_is_paused_not_retried_for_every_entry(monkeypatch):
    attempts = []

    def urlopen(request, timeout=None):
        attempts.append(request.full_url)
        raise vc.urllib.error.URLError(ConnectionRefusedError("refused"))

    monkeypatch.setattr(vc.urllib.request, "urlopen", urlopen)
    url = "https://api.crossref.org/works/10.1000/x"
    with pytest.raises(vc.NetworkUnavailable):
        REAL_HTTP_GET(url, "")
    first = len(attempts)
    with pytest.raises(vc.NetworkUnavailable):
        REAL_HTTP_GET(url, "")
    assert len(attempts) == first  # fails fast during the pause
    with pytest.raises(vc.NetworkUnavailable):
        REAL_HTTP_GET("https://www.ebi.ac.uk/europepmc/webservices/rest/search?q=x", "")
    assert len(attempts) > first   # other hosts are still tried


# --------------------------------------------------------------------------- #
# A5 — retraction status is tri-state                                          #
# --------------------------------------------------------------------------- #

def _cr_noid(**extra):
    return {"message": {"items": [{"title": ["A study with no identifier"], "author": [{"family": "Doe"}],
                                   "issued": {"date-parts": [[2020]]}, "DOI": "10.1000/real", **extra}]}}


def test_retraction_flagged_records_source_and_time(monkeypatch):
    route(monkeypatch, api_crossref_org=_cr_noid(**{"updated-by": [{"type": "retraction",
                                                                    "source": "retraction-watch"}]}))
    r = vc.verify_entry(entry(NOID), "", 0.7, False)
    assert r["retraction"]["status"] == "flagged" and r["retracted"] is True
    assert r["retraction"]["sources_answered"] == ["crossref"] and r["retraction"]["checked_at"]


def test_retraction_not_flagged_in_checked_sources(monkeypatch):
    route(monkeypatch, api_crossref_org=_cr_noid())
    r = vc.verify_entry(entry(NOID), "", 0.7, False)
    assert r["retraction"]["status"] == "not_flagged_in_checked_sources"
    assert r["retracted"] is False


def test_retraction_unknown_when_crossref_did_not_answer(monkeypatch):
    route(monkeypatch, api_crossref_org=vc.SourceError("HTTP 429 — rate limited"), www_ebi_ac_uk=EPMC_HIT)
    r = vc.verify_entry(entry(NOID), "", 0.7, False)
    assert r["verdict"] == "verified"                     # existence is independent ...
    assert r["retraction"]["status"] == "unknown"         # ... of the retraction check
    assert r["retracted"] is None                         # never a false "cleared"
    report = vc.build_report([r], "", 0.7, False)
    assert report["summary"]["retraction"] == {"flagged": 0, "not_flagged_in_checked_sources": 0,
                                               "unknown": 1}
    assert any("retraction" in n.lower() for n in report["summary"]["notes"])


def test_report_schema_version_and_json_round_trip(monkeypatch):
    route(monkeypatch, api_crossref_org=DEEP_LEARNING_CR)
    r = vc.verify_entry(entry(bib_deep("LeCun, Yann and Bengio, Yoshua and Hinton, Geoffrey")),
                        "", 0.7, False)
    report = json.loads(json.dumps(vc.build_report([r], "", 0.7, False)))
    assert report["schema_version"] == 2
    for key in ("verdict", "severity", "retracted", "author_overlap", "title_ratio"):  # v1 keys kept
        assert key in report["entries"][0]
