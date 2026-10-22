#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Query Google Data Commons with no API key (keyless by default).

Backends
  website (default, keyless) - the JSON API behind datacommons.org itself
      GET https://datacommons.org/api/observations/point         latest or one date
      GET https://datacommons.org/api/observations/series        every date
      GET https://datacommons.org/api/observations/{point,series}/within   all children
      GET https://datacommons.org/api/place/{name,parent,descendent}
      GET https://datacommons.org/api/stats/stat-var-search      find variables
      POST https://datacommons.org/api/observation/existence     which variables exist
    It is undocumented (it serves the site's own charts, source in
    github.com/datacommonsorg/website) and can change without notice; every record
    keeps its provenance so results can be cited and re-checked.
  api (optional) - the documented REST v2 API, https://api.datacommons.org/v2,
    which needs DC_API_KEY (free, https://apikeys.datacommons.org/) for
    observation and node calls. Only `observe` and `within` use it.
  Name and Wikidata resolution use https://api.datacommons.org/v2/resolve, which
  answers without a key. Coordinates fall back to the keyless US Census geocoder
  (US points) and OpenStreetMap Nominatim -> Wikidata (anywhere).

Standard library only. Examples:
    python query_datacommons.py resolve California Texas --type State
    python query_datacommons.py resolve --wikidata Q30 Q99
    python query_datacommons.py resolve --coords 37.7749,-122.4194
    python query_datacommons.py observe Count_Person geoId/06 geoId/48 --date all --csv
    python query_datacommons.py within Median_Income_Household geoId/06 County --date 2020 --names
    python query_datacommons.py vars-search "unemployment rate" --place country/USA
    python query_datacommons.py has UnemploymentRate_Person Count_Person --entity country/USA
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

WEB = "https://datacommons.org/api"
V2 = "https://api.datacommons.org/v2"
UA = "AlterLab-Academic-Skills/1.0 (alterlab-datacommons)"
FACET_FIELDS = ("provenanceId", "provenanceUrl", "importName", "measurementMethod",
                "observationPeriod", "unit", "scalingFactor")


def _request(url: str, params=None, body=None, headers=None, tries: int = 3):
    if params:
        url = f"{url}?{urllib.parse.urlencode(params, doseq=True)}"
    data = None
    hdrs = {"User-Agent": UA, "Accept": "application/json", **(headers or {})}
    if body is not None:
        data = json.dumps(body).encode()
        hdrs["Content-Type"] = "application/json"
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=hdrs),
                                        timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            detail = exc.read()[:300].decode("utf-8", "replace")
            raise SystemExit(f"HTTP {exc.code} from {url.split('?')[0]}: {detail}")
        except urllib.error.URLError as exc:
            if attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            raise SystemExit(f"Connection error for {url.split('?')[0]}: {exc.reason}")
    return None


def _key_headers() -> dict:
    key = os.environ.get("DC_API_KEY")
    return {"X-API-Key": key} if key else {}


def pick_backend(requested: str) -> str:
    """auto = api when DC_API_KEY is set, else the keyless website API."""
    key = os.environ.get("DC_API_KEY")
    if requested == "api":
        if not key:
            raise SystemExit("--backend api needs DC_API_KEY (free at https://apikeys.datacommons.org/). "
                             "Without a key, omit --backend (or pass --backend website) to use the "
                             "keyless datacommons.org website API, which serves the same statistics.")
        return "api"
    if requested == "website":
        return "website"
    if key:
        return "api"
    print("DC_API_KEY not set: using the keyless datacommons.org website API "
          "(undocumented; provenance kept per record).", file=sys.stderr)
    return "website"


# ----------------------------------------------------------------- resolve
def resolve_names(names, entity_type=None) -> dict:
    prop = "<-description{typeOf:%s}->dcid" % entity_type if entity_type else "<-description->dcid"
    out = _request(f"{V2}/resolve", body={"nodes": list(names), "property": prop},
                   headers=_key_headers())
    return {e["node"]: [c["dcid"] for c in e.get("candidates", [])] for e in out.get("entities", [])}


def resolve_wikidata(qids) -> dict:
    out = _request(f"{V2}/resolve", body={"nodes": list(qids), "property": "<-wikidataId->dcid"},
                   headers=_key_headers())
    return {e["node"]: [c["dcid"] for c in e.get("candidates", [])] for e in out.get("entities", [])}


def resolve_coords(lat: float, lon: float) -> dict:
    """Data Commons coordinate resolve, then keyless geocoder fallbacks."""
    node = f"{lat}#{lon}"
    out = _request(f"{V2}/resolve", body={"nodes": [node], "property": "<-geoCoordinate->dcid"},
                   headers=_key_headers())
    cands = [c["dcid"] for e in out.get("entities", []) for c in e.get("candidates", [])]
    if cands:
        return {"node": node, "dcids": cands, "via": "datacommons v2 resolve (geoCoordinate)"}
    result = {"node": node, "dcids": [], "via": []}
    census = _request("https://geocoding.geo.census.gov/geocoder/geographies/coordinates",
                      params={"x": lon, "y": lat, "benchmark": "Public_AR_Current",
                              "vintage": "Current_Current", "format": "json",
                              "layers": "States,Counties,Incorporated Places"})
    geos = (census or {}).get("result", {}).get("geographies", {})
    for layer in ("States", "Counties", "Incorporated Places"):
        for g in geos.get(layer, []):
            result["dcids"].append({"dcid": f"geoId/{g['GEOID']}", "name": g.get("NAME"),
                                    "layer": layer})
    if result["dcids"]:
        result["via"].append("US Census geocoder (GEOID -> geoId/<GEOID>)")
        return result
    # Nominatim: one reverse lookup per admin level (country, province, county, city),
    # at most 1 request/s per its usage policy; each level's Wikidata QID -> DCID.
    found = {}
    for zoom in (3, 5, 8, 10):
        osm = _request("https://nominatim.openstreetmap.org/reverse",
                       params={"lat": lat, "lon": lon, "format": "jsonv2", "zoom": zoom,
                               "extratags": 1})
        qid = ((osm or {}).get("extratags") or {}).get("wikidata")
        if qid and qid not in found:
            found[qid] = (osm.get("addresstype"), osm.get("name"))
        time.sleep(1.1)
    if found:
        dcids = resolve_wikidata(found)
        for qid, (level, name) in found.items():
            for d in dcids.get(qid, []):
                result["dcids"].append({"dcid": d, "name": name, "level": level, "wikidata": qid})
        result["via"].append("OpenStreetMap Nominatim reverse -> Wikidata -> v2 resolve")
    return result


# ------------------------------------------------------------ observations
def _facet_meta(facets: dict, facet_id) -> dict:
    meta = facets.get(str(facet_id), {}) if facet_id is not None else {}
    return {k: meta[k] for k in FACET_FIELDS if k in meta}


def _web_records(resp: dict) -> list:
    rows = []
    facets = resp.get("facets", {})
    for var, by_ent in resp.get("data", {}).items():
        for ent, obs in by_ent.items():
            if not obs:
                rows.append({"variable": var, "entity": ent, "date": None, "value": None})
                continue
            meta = _facet_meta(facets, obs.get("facet"))
            if "series" in obs:
                for point in obs["series"]:
                    rows.append({"variable": var, "entity": ent, "date": point.get("date"),
                                 "value": point.get("value"), **meta})
            else:
                rows.append({"variable": var, "entity": ent, "date": obs.get("date"),
                             "value": obs.get("value"), **meta})
    return rows


def _api_records(resp: dict, date: str) -> list:
    rows = []
    facets = resp.get("facets", {})
    for var, v in resp.get("byVariable", {}).items():
        for ent, e in v.get("byEntity", {}).items():
            ordered = e.get("orderedFacets") or []
            if not ordered:
                rows.append({"variable": var, "entity": ent, "date": None, "value": None})
                continue
            best = ordered[0]  # preferred facet, as the website charts use
            meta = _facet_meta(facets, best.get("facetId"))
            for point in best.get("observations", []):
                rows.append({"variable": var, "entity": ent, "date": point.get("date"),
                             "value": point.get("value"), **meta})
    return rows


def observe(backend: str, variables, entities, date: str = "latest") -> list:
    if backend == "api":
        params = {"variable.dcids": variables, "entity.dcids": entities,
                  "select": ["date", "entity", "variable", "value", "facet"]}
        params["date"] = "LATEST" if date == "latest" else ("" if date == "all" else date)
        return _api_records(_request(f"{V2}/observation", params=params,
                                     headers=_key_headers()), date)
    params = {"entities": entities, "variables": variables}
    if date == "all":
        return _web_records(_request(f"{WEB}/observations/series", params=params))
    if date != "latest":
        params["date"] = date
    return _web_records(_request(f"{WEB}/observations/point", params=params))


def within(backend: str, variables, parent: str, child_type: str, date: str = "latest") -> list:
    if backend == "api":
        params = {"variable.dcids": variables,
                  "entity.expression": f"{parent}<-containedInPlace+{{typeOf:{child_type}}}",
                  "select": ["date", "entity", "variable", "value", "facet"]}
        params["date"] = "LATEST" if date == "latest" else ("" if date == "all" else date)
        return _api_records(_request(f"{V2}/observation", params=params,
                                     headers=_key_headers()), date)
    params = {"parentEntity": parent, "childType": child_type, "variables": variables}
    if date == "all":
        return _web_records(_request(f"{WEB}/observations/series/within", params=params))
    if date != "latest":
        params["date"] = date
    return _web_records(_request(f"{WEB}/observations/point/within", params=params))


def place_names(dcids) -> dict:
    names = {}
    dcids = list(dcids)
    for i in range(0, len(dcids), 100):
        names.update(_request(f"{WEB}/place/name", params={"dcids": dcids[i:i + 100]}) or {})
    return names


def _print(rows, as_csv: bool) -> None:
    if not as_csv:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return
    if not rows:
        return
    cols = list(dict.fromkeys(k for r in rows for k in r))
    w = csv.DictWriter(sys.stdout, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)


def main() -> int:
    p = argparse.ArgumentParser(description="Query Data Commons keylessly (website API by default).")
    p.add_argument("--backend", choices=["auto", "website", "api"], default="auto",
                   help="auto (default): api if DC_API_KEY is set, else the keyless website API")
    p.add_argument("--csv", action="store_true", help="print observation records as CSV")
    # The same two options are accepted after the subcommand too.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--backend", choices=["auto", "website", "api"], default=argparse.SUPPRESS)
    common.add_argument("--csv", action="store_true", default=argparse.SUPPRESS)
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("resolve", help="names / Wikidata IDs / coordinates -> DCIDs (keyless)")
    pr.add_argument("names", nargs="*")
    pr.add_argument("--type", dest="entity_type", help="e.g. State, County, Country, City")
    pr.add_argument("--wikidata", nargs="+", metavar="QID")
    pr.add_argument("--coords", metavar="LAT,LON")

    for name, helptext in (("observe", "variable(s) for entity DCIDs"),
                           ("within", "variable(s) for every child of a parent place")):
        sp = sub.add_parser(name, help=helptext, parents=[common])
        sp.add_argument("variables", help="comma-separated statistical variable DCIDs")
        if name == "observe":
            sp.add_argument("entities", nargs="+", help="entity DCIDs, e.g. geoId/06 country/TUR")
        else:
            sp.add_argument("parent", help="parent DCID, e.g. geoId/06")
            sp.add_argument("child_type", help="child place type, e.g. County, State, Country")
        sp.add_argument("--date", default="latest",
                        help="latest (default), all (full series), or a date such as 2020 / 2024-05")
        sp.add_argument("--names", action="store_true", help="add an entity_name column")

    pn = sub.add_parser("names", help="DCID -> place name", parents=[common])
    pn.add_argument("dcids", nargs="+")
    pp = sub.add_parser("parents", help="containing places of a DCID", parents=[common])
    pp.add_argument("dcid")
    pc = sub.add_parser("children", help="all descendants of a type, e.g. geoId/06 County",
                        parents=[common])
    pc.add_argument("parent")
    pc.add_argument("child_type")
    pv = sub.add_parser("vars-search", help="find statistical variables by text", parents=[common])
    pv.add_argument("query")
    pv.add_argument("--place", action="append", default=[], help="restrict to variables with data here")
    pv.add_argument("--limit", type=int, default=25)
    ph = sub.add_parser("has", help="which variables have data for which entities",
                        parents=[common])
    ph.add_argument("variables", nargs="+")
    ph.add_argument("--entity", action="append", required=True)

    a = p.parse_args()
    if a.cmd == "resolve":
        if a.coords:
            lat, lon = (float(x) for x in a.coords.split(","))
            print(json.dumps(resolve_coords(lat, lon), indent=2, ensure_ascii=False))
        elif a.wikidata:
            print(json.dumps(resolve_wikidata(a.wikidata), indent=2))
        elif a.names:
            print(json.dumps(resolve_names(a.names, a.entity_type), indent=2))
        else:
            p.error("resolve needs names, --wikidata, or --coords")
        return 0
    if a.cmd in ("observe", "within"):
        backend = pick_backend(a.backend)
        variables = [v for v in a.variables.split(",") if v]
        if a.cmd == "observe":
            rows = observe(backend, variables, a.entities, a.date)
        else:
            rows = within(backend, variables, a.parent, a.child_type, a.date)
            print(f"One hierarchy query for every {a.child_type} in {a.parent} (the relation "
                  f"expression {a.parent}<-containedInPlace+{{typeOf:{a.child_type}}}): "
                  f"{len({r['entity'] for r in rows})} entities.", file=sys.stderr)
        if a.names:
            names = place_names({r["entity"] for r in rows})
            for r in rows:
                r["entity_name"] = names.get(r["entity"])
        for r in rows:
            r["backend"] = backend
        _print(rows, a.csv)
        empty = sum(1 for r in rows if r["value"] is None)
        if empty:
            print(f"{empty} variable/entity pair(s) had no data for date={a.date} "
                  "(monthly series need YYYY-MM dates; try --date latest).", file=sys.stderr)
        return 0
    if a.backend == "api":
        raise SystemExit(f"`{a.cmd}` is served by the keyless website API only; drop --backend api "
                         "(or use datacommons-client's node methods with DC_API_KEY).")
    if a.cmd == "names":
        out = place_names(a.dcids)
    elif a.cmd == "parents":
        out = _request(f"{WEB}/place/parent", params={"dcid": a.dcid})
    elif a.cmd == "children":
        out = _request(f"{WEB}/place/descendent",
                       params={"dcids": [a.parent], "descendentType": a.child_type})
    elif a.cmd == "vars-search":
        params = {"query": a.query, "limit": a.limit}
        if a.place:
            params["places"] = a.place
        out = _request(f"{WEB}/stats/stat-var-search", params=params)
    else:
        out = _request(f"{WEB}/observation/existence",
                       body={"entities": a.entity, "variables": a.variables})
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
