#!/usr/bin/env python3
"""Query the Google Data Commons REST v2 API.

Base: https://api.datacommons.org/v2  (JSON; needs a free key in DC_API_KEY,
request one at https://apikeys.datacommons.org/). The key is sent as the
X-API-Key header.

  GET /v2/resolve       resolve a place name -> DCID
  GET /v2/observation   statistical observations for variable + entity

Smoke test (after `export DC_API_KEY=...`):
    uv run python query_datacommons.py resolve "California" --type State
    uv run python query_datacommons.py observe Count_Person geoId/06 --date latest
"""
import argparse
import json
import os
import sys

import requests

BASE = "https://api.datacommons.org/v2"


def _headers() -> dict:
    key = os.environ.get("DC_API_KEY")
    if not key:
        sys.exit("Set DC_API_KEY (request a free key at https://apikeys.datacommons.org/).")
    return {"X-API-Key": key}


def resolve(name: str, entity_type: str | None = None) -> dict:
    """Resolve a place name to candidate DCIDs via a name relation expression."""
    prop = "<-description{typeOf:%s}->dcid" % entity_type if entity_type else "<-description->dcid"
    params = {"nodes": name, "property": prop}
    r = requests.get(f"{BASE}/resolve", params=params, headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


def observe(variable: str, entity: str, date: str = "latest") -> dict:
    """Fetch observations for a statistical variable on an entity DCID."""
    params = {
        "variable.dcids": variable,
        "entity.dcids": entity,
        "date": date,
        "select": ["date", "entity", "variable", "value"],
    }
    r = requests.get(f"{BASE}/observation", params=params, headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


def main() -> None:
    p = argparse.ArgumentParser(description="Query Data Commons REST v2 (needs DC_API_KEY).")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("resolve")
    pr.add_argument("name")
    pr.add_argument("--type", dest="entity_type", default=None)

    po = sub.add_parser("observe")
    po.add_argument("variable", help="statistical variable DCID, e.g. Count_Person")
    po.add_argument("entity", help="entity DCID, e.g. geoId/06")
    po.add_argument("--date", default="latest")

    args = p.parse_args()
    if args.cmd == "resolve":
        out = resolve(args.name, args.entity_type)
    else:
        out = observe(args.variable, args.entity, args.date)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
