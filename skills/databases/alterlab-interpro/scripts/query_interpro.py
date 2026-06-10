#!/usr/bin/env python3
"""
InterPro query tool.

Query the EMBL-EBI InterPro REST API for protein family/domain annotations:
look up InterPro entries for a UniProt protein, fetch an entry's details, or
list proteins annotated with an entry. Standard library only.

API base: https://www.ebi.ac.uk/interpro/api
Docs:     https://github.com/ProteinsWebTeam/interpro7-api
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://www.ebi.ac.uk/interpro/api"
USER_AGENT = "AlterLab-Academic-Skills/1.0 (InterPro query tool)"


def _get(path, params=None):
    """GET an InterPro endpoint and return parsed JSON."""
    url = f"{BASE_URL}/{path.strip('/')}/"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def protein(uniprot_id):
    """InterPro entries that match a UniProt protein.

    The first path segment is the resource you want returned, so to list
    *entries* for a protein the protein filter goes last:
    entry/InterPro/protein/UniProt/{id}/. (The inverse, protein/UniProt/{id}/
    entry/InterPro/, returns an empty wrapper with no results.)
    """
    return _get(f"entry/InterPro/protein/UniProt/{uniprot_id}")


def entry(interpro_id):
    """Details for an InterPro entry (e.g. IPR000719)."""
    return _get(f"entry/InterPro/{interpro_id}")


def entry_proteins(interpro_id, page_size=25):
    """UniProt proteins annotated with an InterPro entry.

    Mirror of protein(): to list *proteins* the protein resource goes first,
    protein/UniProt/entry/InterPro/{id}/. This returns count/next/results;
    entry/InterPro/{id}/protein/UniProt/ only returns a proteins_url wrapper.
    """
    return _get(
        f"protein/UniProt/entry/InterPro/{interpro_id}",
        {"page_size": page_size},
    )


def main():
    parser = argparse.ArgumentParser(description="Query the EMBL-EBI InterPro REST API")
    sub = parser.add_subparsers(dest="command", required=True)

    p_p = sub.add_parser("protein", help="InterPro entries for a UniProt accession")
    p_p.add_argument("uniprot_id", help="UniProt accession, e.g. P04637")

    p_e = sub.add_parser("entry", help="Details for an InterPro entry")
    p_e.add_argument("interpro_id", help="InterPro accession, e.g. IPR000719")

    p_m = sub.add_parser("entry-proteins", help="Proteins annotated with an entry")
    p_m.add_argument("interpro_id", help="InterPro accession, e.g. IPR000719")
    p_m.add_argument("--page-size", type=int, default=25, help="Results per page")

    args = parser.parse_args()
    try:
        if args.command == "protein":
            result = protein(args.uniprot_id)
        elif args.command == "entry":
            result = entry(args.interpro_id)
        elif args.command == "entry-proteins":
            result = entry_proteins(args.interpro_id, args.page_size)
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
