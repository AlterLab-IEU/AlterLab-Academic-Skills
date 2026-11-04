"""alterlab-biorxiv: --author goes through Europe PMC's server-side author filter, and falls
back to the bioRxiv date-range scan only when Europe PMC cannot answer or a category is set."""
import importlib.util
import sys
from pathlib import Path

import types

import pytest

try:
    import requests
except ImportError:  # the test env has no requests; the script needs only these names
    requests = types.ModuleType("requests")
    requests.exceptions = types.SimpleNamespace(
        RequestException=type("RequestException", (Exception,), {}))
    requests.exceptions.HTTPError = type("HTTPError", (requests.exceptions.RequestException,), {})

    class _Session:
        def __init__(self):
            self.headers = {}

        def get(self, *a, **k):
            raise AssertionError("tests patch session.get")

    requests.Session = _Session
    sys.modules["requests"] = requests
SCRIPT = Path(__file__).resolve().parents[1] / "skills/databases/alterlab-biorxiv/scripts/biorxiv_search.py"
spec = importlib.util.spec_from_file_location("biorxiv_search", SCRIPT)
mod = importlib.util.module_from_spec(spec)
sys.modules["biorxiv_search"] = mod
spec.loader.exec_module(mod)


class _Resp:
    def __init__(self, data, status=200):
        self._data, self.status_code = data, status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._data


def test_query_restricts_to_author_biorxiv_and_window():
    q = mod.BioRxivSearcher.europepmc_author_query('Doudna "JA"', "2025-11-02", "2026-11-02")
    assert q == 'AUTH:"Doudna JA" AND PUBLISHER:"bioRxiv" AND FIRST_PDATE:[2025-11-02 TO 2026-11-02]'


def test_author_search_uses_europepmc_and_maps_fields(monkeypatch):
    s = mod.BioRxivSearcher()
    calls = []
    page = {"resultList": {"result": [{"doi": "10.64898/2026.10.15.759431", "title": "T",
                                       "authorString": "Doudna JA, X Y.",
                                       "firstPublicationDate": "2026-10-16",
                                       "abstractText": "A"}]},
            "nextCursorMark": "AoE"}
    last = {"resultList": {"result": []}, "nextCursorMark": "AoE"}

    def get(url, params=None, timeout=None):
        calls.append((url, dict(params or {})))
        return _Resp(page if len(calls) == 1 else last)

    monkeypatch.setattr(s.session, "get", get)
    monkeypatch.setattr(s, "search_by_date_range",
                        lambda *a, **k: pytest.fail("the date-range scan must not run"))
    out = s.search_by_author("Doudna", "2025-11-02", "2026-11-02")
    assert calls[0][0] == mod.BioRxivSearcher.EUROPEPMC_URL
    assert 'PUBLISHER:"bioRxiv"' in calls[0][1]["query"]
    assert out == [{"doi": "10.64898/2026.10.15.759431", "title": "T", "authors": "Doudna JA, X Y.",
                    "date": "2026-10-16", "abstract": "A", "server": "biorxiv",
                    "source": "europepmc"}]
    assert s.format_result(out[0])["pdf_url"].endswith("v1.full.pdf")


def test_falls_back_to_scan_when_europepmc_fails(monkeypatch, capsys):
    s = mod.BioRxivSearcher()

    def get(url, params=None, timeout=None):
        return _Resp({}, status=503)

    monkeypatch.setattr(s.session, "get", get)
    monkeypatch.setattr(s, "search_by_date_range",
                        lambda *a, **k: [{"authors": "Doudna, J.", "doi": "d1"},
                                         {"authors": "Other, A.", "doi": "d2"}])
    out = s.search_by_author("doudna", "2025-11-02", "2026-11-02")
    assert [p["doi"] for p in out] == ["d1"]
    assert "Europe PMC could not be reached" in capsys.readouterr().err


def test_category_forces_scan(monkeypatch):
    s = mod.BioRxivSearcher()
    monkeypatch.setattr(s.session, "get", lambda *a, **k: pytest.fail("no Europe PMC call with a category"))
    monkeypatch.setattr(s, "search_by_date_range", lambda *a, **k: [{"authors": "Doudna, J.", "doi": "d1"}])
    assert [p["doi"] for p in s.search_by_author("Doudna", "2025-11-02", "2026-11-02", "genomics")] == ["d1"]
