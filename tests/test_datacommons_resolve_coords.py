"""alterlab-datacommons: coordinate resolve asks Data Commons v2 and v1, merges both, and
falls back to the Census geocoder only when neither answers (offline, _request stubbed)."""
import importlib.util
import sys
from pathlib import Path

SCRIPT = (Path(__file__).resolve().parents[1]
          / "skills/databases/alterlab-datacommons/scripts/query_datacommons.py")
spec = importlib.util.spec_from_file_location("query_datacommons", SCRIPT)
qd = importlib.util.module_from_spec(spec)
sys.modules["query_datacommons"] = qd
spec.loader.exec_module(qd)


def _stub(monkeypatch, v2=None, v1=None, census=None):
    calls = []

    def fake(url, params=None, body=None, headers=None, tries=3, fatal=True, **kw):
        calls.append(url)
        if url.endswith("/resolve"):
            return v2
        if "recon/resolve/coordinate" in url:
            return v1
        if "geocoding.geo.census.gov" in url:
            return census
        raise AssertionError(f"unexpected request {url}")

    monkeypatch.setattr(qd, "_request", fake)
    monkeypatch.setattr(qd, "_with_names", lambda places: places)
    monkeypatch.setattr(qd.time, "sleep", lambda s: None)
    return calls


def test_v1_answers_when_v2_is_empty(monkeypatch):
    calls = _stub(monkeypatch, v2={"entities": [{"node": "37.7749#-122.4194"}]},
                  v1={"placeCoordinates": [{"places": [
                      {"dcid": "geoId/0667000", "dominantType": "City"},
                      {"dcid": "geoId/06075", "dominantType": "County"}]}]})
    out = qd.resolve_coords(37.7749, -122.4194)
    assert [p["dcid"] for p in out["dcids"]] == ["geoId/0667000", "geoId/06075"]
    assert any("v1 coordinate resolver" in v for v in out["via"])
    assert any("v2 resolve" in v for v in out["no_answer"])
    assert not any("census" in c for c in calls), "no geocoder fallback when Data Commons answers"


def test_v2_and_v1_results_are_merged_without_duplicates(monkeypatch):
    _stub(monkeypatch,
          v2={"entities": [{"candidates": [{"dcid": "geoId/06075", "dominantType": "County"}]}]},
          v1={"placeCoordinates": [{"places": [{"dcid": "geoId/06075", "dominantType": "County"},
                                               {"dcid": "geoId/06", "dominantType": "State"}]}]})
    out = qd.resolve_coords(37.77, -122.4194)
    assert [p["dcid"] for p in out["dcids"]] == ["geoId/06075", "geoId/06"]
    assert len(out["via"]) == 2 and out["no_answer"] == []


def test_census_fallback_only_when_both_are_empty(monkeypatch):
    calls = _stub(monkeypatch, v2={}, v1=None, census={"result": {"geographies": {
        "States": [{"GEOID": "06", "NAME": "California"}],
        "Counties": [{"GEOID": "06075", "NAME": "San Francisco County"}]}}})
    out = qd.resolve_coords(37.7749, -122.4194)
    assert [p["dcid"] for p in out["dcids"]] == ["geoId/06", "geoId/06075"]
    assert out["via"] == ["US Census geocoder (GEOID -> geoId/<GEOID>)"]
    assert len(out["no_answer"]) == 2
    assert any("census" in c for c in calls)
