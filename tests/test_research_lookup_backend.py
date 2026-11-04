"""alterlab-research-lookup's keyless scholarly backend: Semantic Scholar search is best effort.

Semantic Scholar's keyless search pool is often spent (HTTP 429 for minutes from busy
networks), so it can never be a precondition: Crossref, Europe PMC and arXiv carry the query,
the output names Semantic Scholar as not checked, and a refused source is never reported as
"no results". A forced keyed backend whose key is missing still exits without answering from
another backend. No test touches the network: every request goes to an in-memory router.
"""

from __future__ import annotations

import email.message
import importlib
import json
import sys
import urllib.error
import urllib.parse
from pathlib import Path

import pytest

SCRIPTS = (Path(__file__).resolve().parent.parent / "skills" / "research-tools"
           / "alterlab-research-lookup" / "scripts")
sys.path.insert(0, str(SCRIPTS))
sb = importlib.import_module("scholarly_backend")
rl = importlib.import_module("research_lookup")

_CROSSREF = {"message": {"items": [{
    "DOI": "10.1111/j.1467-9280.2006.01693.x", "title": ["Test-enhanced learning"],
    "author": [{"family": "Roediger", "given": "Henry"}], "issued": {"date-parts": [[2006]]},
    "container-title": ["Psychological Science"], "is-referenced-by-count": 2000, "URL": "u"}]}}
_EPMC = {"resultList": {"result": [{
    "title": "The critical importance of retrieval for learning.", "pubYear": "2008",
    "doi": "10.1126/science.1152408", "authorList": {"author": [{"fullName": "Karpicke JD"}]},
    "citedByCount": 700, "source": "MED", "id": "18276894", "abstractText": "Learning..."}]}}
_ARXIV = (b'<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom" '
          b'xmlns:arxiv="http://arxiv.org/schemas/atom"><entry><id>http://arxiv.org/abs/2101.00001v1</id>'
          b'<title>Retrieval practice at scale</title><published>2021-01-01T00:00:00Z</published>'
          b'<summary>We study retrieval.</summary><author><name>A. Author</name></author></entry></feed>')


def _http_error(url: str, code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(url, code, "Too Many Requests", email.message.Message(), None)


@pytest.fixture(autouse=True)
def _isolated(monkeypatch):
    monkeypatch.setattr(sb, "_S2_PAUSED_UNTIL", 0.0)
    monkeypatch.setattr(sb.time, "sleep", lambda s: None)

    def no_network(*a, **k):
        pytest.fail("test attempted network access")

    monkeypatch.setattr(sb.urllib.request, "urlopen", no_network)


def _router(s2=429, calls=None, sleeps=None):
    """A fake ``get``: Crossref, Europe PMC and arXiv answer; Semantic Scholar answers ``s2``
    (an HTTP status to raise, or a JSON body)."""
    calls = [] if calls is None else calls

    def get(url: str) -> bytes:
        calls.append(url)
        host = urllib.parse.urlsplit(url).hostname
        if host == "api.crossref.org":
            return json.dumps(_CROSSREF).encode()
        if host == "www.ebi.ac.uk":
            return json.dumps(_EPMC).encode()
        if host == "export.arxiv.org":
            return _ARXIV
        if host == "api.semanticscholar.org":
            if isinstance(s2, int):
                raise _http_error(url, s2)
            return json.dumps(s2).encode()
        pytest.fail(f"unexpected host contacted: {url}")

    return get, calls


def test_refused_semantic_scholar_leaves_the_other_indexes_answering(monkeypatch):
    sleeps = []
    monkeypatch.setattr(sb.time, "sleep", sleeps.append)
    get, calls = _router(s2=429)
    res = sb.search("retrieval practice", limit=5, rank="relevance", get=get)
    found = {s for r in res["records"] for s in r["found_in"]}
    assert found == {"crossref", "europepmc", "arxiv"} and len(res["records"]) == 3
    assert set(res["errors"]) == {"semanticscholar"}
    assert "HTTP 429" in res["errors"]["semanticscholar"]
    assert "not checked" in res["errors"]["semanticscholar"]
    assert sleeps == list(sb.BACKOFF["semanticscholar"])  # one retry after the backoff
    assert len([u for u in calls if "semanticscholar" in u]) == len(sb.BACKOFF["semanticscholar"]) + 1
    md = sb.to_markdown(res)
    assert "in crossref, europepmc, arxiv; not checked: semanticscholar" in md
    assert "Sources that did not answer: semanticscholar: HTTP 429" in md


def test_semantic_scholar_is_skipped_for_the_rest_of_the_run_after_a_429():
    get, calls = _router(s2=429)
    sb.search("first query", limit=3, get=get)
    before = len([u for u in calls if "semanticscholar" in u])
    res = sb.search("second query", limit=3, get=get)
    assert len([u for u in calls if "semanticscholar" in u]) == before  # no new S2 request
    assert res["records"] and "earlier in this run" in res["errors"]["semanticscholar"]
    assert "not checked" in res["errors"]["semanticscholar"]


def test_semantic_scholar_still_merges_when_it_answers():
    s2 = {"data": [{"title": "Test-enhanced learning", "year": 2006, "venue": "Psych Sci",
                    "externalIds": {"DOI": "10.1111/j.1467-9280.2006.01693.x"}, "citationCount": 2500,
                    "authors": [{"name": "H. Roediger"}], "url": "s2url"}]}
    get, _ = _router(s2=s2)
    res = sb.search("retrieval practice", limit=5, rank="cited", get=get)
    assert not res["errors"]
    top = res["records"][0]
    assert set(top["found_in"]) == {"crossref", "semanticscholar"}
    assert top["cited_by"] == {"crossref": 2000, "semanticscholar": 2500}


def test_research_lookup_answers_from_the_keyless_indexes_when_s2_is_refused(monkeypatch):
    get, _ = _router(s2=429)
    monkeypatch.setattr(sb, "_http_get", get)
    monkeypatch.delenv("PARALLEL_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    out = rl.ResearchLookup(limit=5).lookup("find papers on retrieval practice")
    assert out["success"] is True and out["backend"] == "scholarly"
    assert out["model"] == "keyless/crossref+europepmc+arxiv"
    assert "semanticscholar" in out["source_errors"] and out["citations"]
    assert "not checked: semanticscholar" in out["response"]


def test_s2_key_header_goes_to_semantic_scholar_only(monkeypatch):
    seen = {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return b"{}"

    def fake_urlopen(req, timeout=None):
        seen[urllib.parse.urlsplit(req.full_url).hostname] = req.get_header("X-api-key")
        return _Resp()

    monkeypatch.setattr(sb, "S2_API_KEY", "k-123")
    monkeypatch.setattr(sb.urllib.request, "urlopen", fake_urlopen)
    sb._http_get("https://api.semanticscholar.org/graph/v1/paper/search?query=x")
    sb._http_get("https://api.crossref.org/works?query=x")
    assert seen == {"api.semanticscholar.org": "k-123", "api.crossref.org": None}


def test_unknown_source_exits_2_without_answering_from_the_others(capsys):
    assert sb.main(["retrieval practice", "--sources", "openalex"]) == 2
    err = capsys.readouterr().err
    assert "unknown source(s) openalex" in err and "OpenAlex was removed" in err


@pytest.mark.parametrize("backend, key", [("parallel", "PARALLEL_API_KEY"),
                                          ("perplexity", "OPENROUTER_API_KEY")])
def test_forced_keyed_backend_without_its_key_refuses(monkeypatch, backend, key):
    monkeypatch.delenv(key, raising=False)
    with pytest.raises(ValueError, match="not falling back to another backend"):
        rl.ResearchLookup(force_backend=backend).lookup("find papers on retrieval practice")
