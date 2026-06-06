#!/usr/bin/env python3
"""
PubMed query tool.

Query PubMed via the NCBI E-utilities REST API: search (ESearch) returns PMIDs,
fetch (EFetch) returns abstracts, summary (ESummary) returns metadata. Supports
an optional API key for higher rate limits. Standard library only.

API base: https://eutils.ncbi.nlm.nih.gov/entrez/eutils
Docs:     https://www.ncbi.nlm.nih.gov/books/NBK25501/
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
USER_AGENT = "AlterLab-Academic-Skills/1.0 (PubMed query tool)"


def _get(endpoint, params):
    """GET an E-utilities endpoint and return raw text."""
    url = f"{BASE_URL}/{endpoint}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def search(term, retmax=20, api_key=None):
    """ESearch: return PMIDs for a query term."""
    params = {"db": "pubmed", "term": term, "retmax": retmax, "retmode": "json"}
    if api_key:
        params["api_key"] = api_key
    return json.loads(_get("esearch.fcgi", params))


def summary(pmids, api_key=None):
    """ESummary: document summaries (JSON) for a list of PMIDs."""
    params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "json"}
    if api_key:
        params["api_key"] = api_key
    return json.loads(_get("esummary.fcgi", params))


def fetch(pmids, api_key=None):
    """EFetch: plain-text abstracts for a list of PMIDs."""
    params = {"db": "pubmed", "id": ",".join(pmids),
              "rettype": "abstract", "retmode": "text"}
    if api_key:
        params["api_key"] = api_key
    return {"abstracts": _get("efetch.fcgi", params)}


def main():
    parser = argparse.ArgumentParser(description="Query PubMed via NCBI E-utilities")
    parser.add_argument("--api-key", help="NCBI API key (raises rate limit to 10 req/s)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_s = sub.add_parser("search", help="ESearch: PMIDs for a query")
    p_s.add_argument("term", help='Query, e.g. "diabetes[tiab] AND 2024[dp]"')
    p_s.add_argument("--retmax", type=int, default=20, help="Max PMIDs")

    p_m = sub.add_parser("summary", help="ESummary: metadata for PMIDs")
    p_m.add_argument("pmids", nargs="+", help="One or more PMIDs")

    p_f = sub.add_parser("fetch", help="EFetch: abstracts for PMIDs")
    p_f.add_argument("pmids", nargs="+", help="One or more PMIDs")

    args = parser.parse_args()
    try:
        if args.command == "search":
            result = search(args.term, args.retmax, args.api_key)
        elif args.command == "summary":
            result = summary(args.pmids, args.api_key)
        elif args.command == "fetch":
            result = fetch(args.pmids, args.api_key)
    except urllib.error.HTTPError as exc:
        print(f"HTTP error {exc.code}: {exc.reason}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Connection error: {exc.reason}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
