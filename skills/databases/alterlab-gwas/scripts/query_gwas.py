#!/usr/bin/env python3
"""
GWAS Catalog query tool (REST API v2).

Query the NHGRI-EBI GWAS Catalog REST API v2 for curated SNP-trait associations
by rsID, trait (efo_id), mapped gene, or study accession. Standard library only.

API base: https://www.ebi.ac.uk/gwas/rest/api/v2   (no key; 15 requests/s throttle)
Docs:     https://www.ebi.ac.uk/gwas/rest/api/v2/docs

The legacy v1 API (/singleNucleotidePolymorphisms, /efoTraits, camelCase fields)
is deprecated, and the Summary Statistics API is retired (HTTP 410) — full
summary statistics come from the FTP link in a study's `full_summary_stats` field.
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://www.ebi.ac.uk/gwas/rest/api/v2"
USER_AGENT = "AlterLab-Academic-Skills/1.1 (GWAS Catalog query tool)"
MAX_PAGE_SIZE = 200  # larger pages routinely time out on v2


def _get(path, params=None):
    """GET a GWAS Catalog v2 endpoint and return parsed JSON."""
    url = f"{BASE_URL}/{path.lstrip('/')}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def associations(page=0, size=20, **filters):
    """Associations filtered by rs_id / efo_id / mapped_gene / accession_id, strongest first."""
    params = {k: v for k, v in filters.items() if v is not None}
    params.update(
        {"sort": "p_value", "direction": "asc", "page": page,
         "size": min(size, MAX_PAGE_SIZE)}
    )
    return _get("associations", params)


def find_trait(text, size=20):
    """Resolve free-text trait names to current efo_id short-forms."""
    return _get("efo-traits", {"efo_trait": text, "size": size})


def study(accession):
    """Study metadata for a GCST accession (includes full_summary_stats FTP link)."""
    return _get(f"studies/{accession}")


def main():
    parser = argparse.ArgumentParser(description="Query the NHGRI-EBI GWAS Catalog REST API v2")
    sub = parser.add_subparsers(dest="command", required=True)

    p_v = sub.add_parser("variant", help="Associations for an rsID")
    p_v.add_argument("rs_id", help="Variant rsID, e.g. rs7903146")

    p_t = sub.add_parser("trait", help="Associations for a trait short-form")
    p_t.add_argument("efo_id", help="Trait short-form, e.g. MONDO_0005148")

    p_g = sub.add_parser("gene", help="Associations whose variant maps to a gene")
    p_g.add_argument("gene", help="HGNC symbol, e.g. TCF7L2")

    for p in (p_v, p_t, p_g):
        p.add_argument("--page", type=int, default=0, help="Page index (0-based)")
        p.add_argument("--size", type=int, default=20,
                       help=f"Results per page (max {MAX_PAGE_SIZE})")

    p_f = sub.add_parser("find-trait", help="Free-text trait search -> efo_id")
    p_f.add_argument("text", help='Trait name, e.g. "type 2 diabetes"')

    p_s = sub.add_parser("study", help="Study metadata by accession")
    p_s.add_argument("accession", help="Study accession, e.g. GCST001795")

    args = parser.parse_args()
    try:
        if args.command == "variant":
            result = associations(args.page, args.size, rs_id=args.rs_id)
        elif args.command == "trait":
            result = associations(args.page, args.size, efo_id=args.efo_id)
        elif args.command == "gene":
            result = associations(args.page, args.size, mapped_gene=args.gene)
        elif args.command == "find-trait":
            result = find_trait(args.text)
        else:
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
