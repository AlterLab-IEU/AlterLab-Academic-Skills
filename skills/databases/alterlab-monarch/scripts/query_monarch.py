#!/usr/bin/env python3
"""
Monarch Initiative query tool.

Query the Monarch Initiative API v3 knowledge graph for disease-gene-phenotype
associations: look up an entity (gene/disease/HPO term), search by text, or
pull associations for an entity. Standard library only.

API base: https://api-v3.monarchinitiative.org/v3
Docs:     https://api-v3.monarchinitiative.org/v3/docs
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://api-v3.monarchinitiative.org/v3"
USER_AGENT = "AlterLab-Academic-Skills/1.0 (Monarch query tool)"


def _get(path, params=None):
    """GET a Monarch API endpoint and return parsed JSON."""
    url = f"{BASE_URL}/{path.lstrip('/')}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params, doseq=True)}"
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def entity(entity_id):
    """Look up an entity by CURIE, e.g. HP:0001250, MONDO:0007739, HGNC:1100."""
    return _get(f"api/entity/{entity_id}")


def search(query, category=None, limit=20):
    """Search the knowledge graph by text."""
    params = {"q": query, "limit": limit}
    if category:
        params["category"] = category
    return _get("api/search", params)


def associations(entity_id, category=None, limit=50):
    """Associations for an entity (gene/disease/phenotype)."""
    params = {"entity": entity_id, "limit": limit}
    if category:
        params["category"] = category
    return _get("api/association", params)


def main():
    parser = argparse.ArgumentParser(description="Query the Monarch Initiative API v3")
    sub = parser.add_subparsers(dest="command", required=True)

    p_e = sub.add_parser("entity", help="Look up an entity by CURIE")
    p_e.add_argument("entity_id", help="CURIE, e.g. HP:0001250 or HGNC:1100")

    p_s = sub.add_parser("search", help="Search the knowledge graph by text")
    p_s.add_argument("query", help="Free-text query, e.g. epilepsy")
    p_s.add_argument("--category", help="Biolink category filter")
    p_s.add_argument("--limit", type=int, default=20, help="Max results")

    p_a = sub.add_parser("associations", help="Associations for an entity")
    p_a.add_argument("entity_id", help="CURIE, e.g. HGNC:1100")
    p_a.add_argument("--category", help="Biolink association category filter")
    p_a.add_argument("--limit", type=int, default=50, help="Max results")

    args = parser.parse_args()
    try:
        if args.command == "entity":
            result = entity(args.entity_id)
        elif args.command == "search":
            result = search(args.query, args.category, args.limit)
        elif args.command == "associations":
            result = associations(args.entity_id, args.category, args.limit)
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
