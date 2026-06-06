#!/usr/bin/env python3
"""Query the DepMap portal API (no API key required).

Base: https://depmap.org/portal/api
  GET /gene                  gene_id, dataset  -> gene-level dependency info
  GET /data/gene_dependency  gene_name, dataset_name -> dependency slice

Note: the portal API is best for single-gene lookups; for matrix-scale work
download the release files from https://depmap.org/portal/download/all/.

Smoke test:
    uv run python query_depmap.py gene KRAS --dataset Chronos_Combined
    uv run python query_depmap.py slice KRAS --dataset-name CRISPRGeneEffect
"""
import argparse
import json

import requests

BASE = "https://depmap.org/portal/api"


def gene(gene_symbol: str, dataset: str = "Chronos_Combined") -> dict:
    """Gene-level dependency record across cell lines."""
    params = {"gene_id": gene_symbol, "dataset": dataset}
    r = requests.get(f"{BASE}/gene", params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def dependency_slice(gene_symbol: str, dataset_name: str = "CRISPRGeneEffect") -> dict:
    """Fetch a gene's dependency slice from a named dataset."""
    params = {"gene_name": gene_symbol, "dataset_name": dataset_name}
    r = requests.get(f"{BASE}/data/gene_dependency", params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def main() -> None:
    p = argparse.ArgumentParser(description="Query DepMap portal API (no key required).")
    sub = p.add_subparsers(dest="cmd", required=True)

    pg = sub.add_parser("gene")
    pg.add_argument("gene_symbol")
    pg.add_argument("--dataset", default="Chronos_Combined")

    ps = sub.add_parser("slice")
    ps.add_argument("gene_symbol")
    ps.add_argument("--dataset-name", default="CRISPRGeneEffect")

    args = p.parse_args()
    if args.cmd == "gene":
        out = gene(args.gene_symbol, args.dataset)
    else:
        out = dependency_slice(args.gene_symbol, args.dataset_name)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
