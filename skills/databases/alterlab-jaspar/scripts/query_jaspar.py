#!/usr/bin/env python3
"""
JASPAR query tool.

Query the JASPAR REST API for transcription factor binding profiles: search
matrices by TF name/species/collection, or fetch a specific matrix (PFM) by
ID. Standard library only.

API base: https://jaspar.elixir.no/api/v1
Docs:     https://jaspar.elixir.no/api/v1/docs/
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://jaspar.elixir.no/api/v1"
USER_AGENT = "AlterLab-Academic-Skills/1.0 (JASPAR query tool)"


def _get(path, params=None):
    """GET a JASPAR endpoint and return parsed JSON."""
    url = f"{BASE_URL}/{path.strip('/')}/"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def search(name=None, species=None, collection="CORE", tf_class=None,
           tf_family=None, latest=True, page=1, page_size=25):
    """Search JASPAR matrices. latest=True returns only the current version
    of each profile (otherwise every historical version is listed)."""
    params = {"collection": collection, "page": page,
              "page_size": page_size, "format": "json"}
    if latest:
        params["version"] = "latest"
    if name:
        params["name"] = name
    if species:
        params["tax_id"] = species
    if tf_class:
        params["tf_class"] = tf_class
    if tf_family:
        params["tf_family"] = tf_family
    return _get("matrix", params)


def matrix(matrix_id):
    """Fetch a specific matrix (PFM) by ID, e.g. MA0139.1."""
    return _get(f"matrix/{matrix_id}")


def main():
    parser = argparse.ArgumentParser(description="Query the JASPAR REST API")
    sub = parser.add_subparsers(dest="command", required=True)

    p_s = sub.add_parser("search", help="Search TF binding profiles")
    p_s.add_argument("--name", help="TF name, e.g. CTCF")
    p_s.add_argument("--species", help="NCBI taxonomy ID, e.g. 9606 for human")
    p_s.add_argument("--collection", default="CORE", help="JASPAR collection (default CORE)")
    p_s.add_argument("--tf-class", help="TF structural class")
    p_s.add_argument("--tf-family", help="TF family")
    p_s.add_argument("--all-versions", action="store_true",
                     help="Include historical profile versions (default: latest only)")
    p_s.add_argument("--page", type=int, default=1, help="Page number")
    p_s.add_argument("--page-size", type=int, default=25, help="Results per page")

    p_m = sub.add_parser("matrix", help="Fetch a matrix (PFM) by ID")
    p_m.add_argument("matrix_id", help="Matrix ID, e.g. MA0139.1")

    args = parser.parse_args()
    try:
        if args.command == "search":
            result = search(args.name, args.species, args.collection,
                            args.tf_class, args.tf_family,
                            latest=not args.all_versions,
                            page=args.page, page_size=args.page_size)
        elif args.command == "matrix":
            result = matrix(args.matrix_id)
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
