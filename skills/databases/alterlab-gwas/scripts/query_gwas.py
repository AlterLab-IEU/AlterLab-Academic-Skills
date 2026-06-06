#!/usr/bin/env python3
"""
GWAS Catalog query tool.

Query the NHGRI-EBI GWAS Catalog REST API for SNP-trait associations by
rsID, EFO trait, or study accession. Uses only the Python standard library.

API base: https://www.ebi.ac.uk/gwas/rest/api
Docs:     https://www.ebi.ac.uk/gwas/rest/docs/api
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://www.ebi.ac.uk/gwas/rest/api"
USER_AGENT = "AlterLab-Academic-Skills/1.0 (GWAS Catalog query tool)"


def _get(path, params=None):
    """GET a GWAS Catalog endpoint and return parsed JSON."""
    url = f"{BASE_URL}/{path.lstrip('/')}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def variant(rs_id):
    """All associations for a SNP (rsID)."""
    return _get(
        f"singleNucleotidePolymorphisms/{rs_id}/associations",
        {"projection": "associationBySnp"},
    )


def trait(efo_id, page=0, size=100):
    """Associations for an EFO trait term (e.g. EFO_0001360)."""
    return _get(
        f"efoTraits/{efo_id}/associations", {"page": page, "size": size}
    )


def study(accession):
    """Study metadata for a GCST accession."""
    return _get(f"studies/{accession}")


def main():
    parser = argparse.ArgumentParser(description="Query the NHGRI-EBI GWAS Catalog REST API")
    sub = parser.add_subparsers(dest="command", required=True)

    p_v = sub.add_parser("variant", help="Associations for an rsID")
    p_v.add_argument("rs_id", help="Variant rsID, e.g. rs7903146")

    p_t = sub.add_parser("trait", help="Associations for an EFO trait")
    p_t.add_argument("efo_id", help="EFO trait ID, e.g. EFO_0001360")
    p_t.add_argument("--page", type=int, default=0, help="Page index (0-based)")
    p_t.add_argument("--size", type=int, default=100, help="Results per page")

    p_s = sub.add_parser("study", help="Study metadata by accession")
    p_s.add_argument("accession", help="Study accession, e.g. GCST001795")

    args = parser.parse_args()
    try:
        if args.command == "variant":
            result = variant(args.rs_id)
        elif args.command == "trait":
            result = trait(args.efo_id, args.page, args.size)
        elif args.command == "study":
            result = study(args.accession)
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
