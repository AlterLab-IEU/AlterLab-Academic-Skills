#!/usr/bin/env python3
"""Query the gnomAD GraphQL API (no API key required).

Endpoint: POST https://gnomad.broadinstitute.org/api
  body: {"query": "<graphql>", "variables": {...}}

Datasets: gnomad_r4 (GRCh38), gnomad_r3 (GRCh38), gnomad_r2_1 (GRCh37).
Variant ID format: {chrom}-{pos}-{ref}-{alt}, e.g. 17-43094692-G-A.

Smoke test:
    uv run python query_gnomad.py variant 17-43094692-G-A --dataset gnomad_r4
    uv run python query_gnomad.py constraint BRCA1 --genome GRCh38
"""
import argparse
import json
import sys

import requests

ENDPOINT = "https://gnomad.broadinstitute.org/api"

VARIANT_Q = """
query Variant($variantId: String!, $dataset: DatasetId!) {
  variant(variantId: $variantId, dataset: $dataset) {
    variant_id chrom pos ref alt consequence rsids
    genome { af ac an populations { id ac an } }
    exome  { af ac an populations { id ac an } }
  }
}"""

CONSTRAINT_Q = """
query Constraint($gene: String!, $ref: ReferenceGenomeId!) {
  gene(gene_symbol: $gene, reference_genome: $ref) {
    gene_id gene_symbol
    gnomad_constraint { oe_lof oe_mis oe_syn lof_z mis_z syn_z pLI flags }
  }
}"""


def _post(query: str, variables: dict) -> dict:
    r = requests.post(ENDPOINT, json={"query": query, "variables": variables}, timeout=60)
    r.raise_for_status()
    data = r.json()
    if data.get("errors"):
        sys.exit(json.dumps(data["errors"], indent=2))
    return data["data"]


def variant(variant_id: str, dataset: str = "gnomad_r4") -> dict:
    """Look up allele frequencies for a single variant."""
    return _post(VARIANT_Q, {"variantId": variant_id, "dataset": dataset})


def constraint(gene: str, reference_genome: str = "GRCh38") -> dict:
    """Fetch gnomAD constraint metrics (pLI, oe_lof, ...) for a gene."""
    return _post(CONSTRAINT_Q, {"gene": gene, "ref": reference_genome})


def main() -> None:
    p = argparse.ArgumentParser(description="Query gnomAD GraphQL API (no key required).")
    sub = p.add_subparsers(dest="cmd", required=True)

    pv = sub.add_parser("variant")
    pv.add_argument("variant_id", help="e.g. 17-43094692-G-A")
    pv.add_argument("--dataset", default="gnomad_r4")

    pc = sub.add_parser("constraint")
    pc.add_argument("gene", help="gene symbol, e.g. BRCA1")
    pc.add_argument("--genome", default="GRCh38", choices=["GRCh37", "GRCh38"])

    args = p.parse_args()
    if args.cmd == "variant":
        out = variant(args.variant_id, args.dataset)
    else:
        out = constraint(args.gene, args.genome)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
