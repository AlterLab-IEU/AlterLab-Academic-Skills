#!/usr/bin/env python3
"""Query the cBioPortal public REST API (no API key required for public data).

Base: https://www.cbioportal.org/api  (RESTful JSON)
  GET  studies
  GET  studies/{studyId}/molecular-profiles
  POST molecular-profiles/{profileId}/mutations/fetch

Smoke test:
    uv run python query_cbioportal.py studies --filter tcga
    uv run python query_cbioportal.py profiles brca_tcga
    uv run python query_cbioportal.py mutations brca_tcga_mutations --genes 7157,672
"""
import argparse
import json

import requests

BASE = "https://www.cbioportal.org/api"
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}


def get_studies(name_filter: str | None = None) -> list:
    """List public cancer studies (optionally filter by substring in studyId)."""
    r = requests.get(f"{BASE}/studies", params={"pageSize": 1000},
                     headers=HEADERS, timeout=60)
    r.raise_for_status()
    studies = r.json()
    if name_filter:
        studies = [s for s in studies if name_filter.lower() in s["studyId"].lower()]
    return studies


def get_profiles(study_id: str) -> list:
    """List molecular profiles for a study."""
    r = requests.get(f"{BASE}/studies/{study_id}/molecular-profiles",
                     headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.json()


def get_mutations(profile_id: str, entrez_ids: list[int],
                  sample_list_id: str | None = None) -> list:
    """Fetch mutations for given Entrez gene IDs in a molecular profile."""
    body = {
        "entrezGeneIds": entrez_ids,
        "sampleListId": sample_list_id or profile_id.replace("_mutations", "_all"),
    }
    r = requests.post(f"{BASE}/molecular-profiles/{profile_id}/mutations/fetch",
                      json=body, headers=HEADERS, timeout=120)
    r.raise_for_status()
    return r.json()


def main() -> None:
    p = argparse.ArgumentParser(description="Query cBioPortal (public, no key).")
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("studies")
    ps.add_argument("--filter", dest="name_filter", default=None)

    pp = sub.add_parser("profiles")
    pp.add_argument("study_id")

    pm = sub.add_parser("mutations")
    pm.add_argument("profile_id")
    pm.add_argument("--genes", required=True, help="comma-separated Entrez IDs, e.g. 7157,672")
    pm.add_argument("--sample-list", default=None)

    args = p.parse_args()
    if args.cmd == "studies":
        out = get_studies(args.name_filter)
    elif args.cmd == "profiles":
        out = get_profiles(args.study_id)
    else:
        ids = [int(x) for x in args.genes.split(",") if x.strip()]
        out = get_mutations(args.profile_id, ids, args.sample_list)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
