#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///
"""Query NCBI GEO DataSets via E-utilities (no API key required; key lifts limits).

Base: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/  (db=gds)
  esearch.fcgi   term -> GEO UIDs
  esummary.fcgi  id   -> dataset/series summaries (Accession, title, n_samples)

Run with uv (auto-installs the inline `requests` dependency):
    uv run scripts/query_geo.py search "breast cancer AND Homo sapiens[ORGN]" --retmax 5
    uv run scripts/query_geo.py summary 200000001,200000002
"""
import argparse
import json
import os

import requests

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
API_KEY = os.environ.get("NCBI_API_KEY")


def _params(extra: dict) -> dict:
    p = {"db": "gds", "retmode": "json", **extra}
    if API_KEY:
        p["api_key"] = API_KEY
    return p


def search(term: str, retmax: int = 20) -> dict:
    """Search GEO DataSets; return esearch result (Count + IdList)."""
    r = requests.get(f"{BASE}/esearch.fcgi",
                     params=_params({"term": term, "retmax": retmax}), timeout=30)
    r.raise_for_status()
    return r.json().get("esearchresult", {})


def summary(uids: str) -> dict:
    """Fetch document summaries for comma-separated GEO UIDs."""
    r = requests.get(f"{BASE}/esummary.fcgi",
                     params=_params({"id": uids, "version": "2.0"}), timeout=30)
    r.raise_for_status()
    return r.json().get("result", {})


def main() -> None:
    p = argparse.ArgumentParser(description="Query NCBI GEO (db=gds) via E-utilities.")
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("search")
    ps.add_argument("term")
    ps.add_argument("--retmax", type=int, default=20)

    pm = sub.add_parser("summary")
    pm.add_argument("uids", help="comma-separated GEO UIDs")

    args = p.parse_args()
    out = search(args.term, args.retmax) if args.cmd == "search" else summary(args.uids)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
