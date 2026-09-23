#!/usr/bin/env python3
"""Query the GTEx Portal API v2 (no authentication required).

Base: https://gtexportal.org/api/v2/  (GET, JSON)
  /expression/medianGeneExpression   gencodeId, datasetId -> median TPM per tissue
  /association/singleTissueEqtl       gencodeId|variantId, tissueSiteDetailId
  /dataset/tissueSiteDetail           list available tissues
  /reference/gene                     geneId (symbol), gencodeVersion -> versioned gencodeId

Gene IDs are versioned GENCODE IDs whose .version suffix must match the dataset:
gtex_v10 uses GENCODE v39 (e.g. APOE = ENSG00000130203.10, PCSK9 = ENSG00000169174.11),
gtex_v8 uses GENCODE v26. The wrong suffix silently returns zero rows.

Smoke test:
    uv run python query_gtex.py gene APOE            # -> ENSG00000130203.10 (gtex_v10)
    uv run python query_gtex.py expression ENSG00000130203.10
    uv run python query_gtex.py eqtl ENSG00000169174.11 --tissue Liver
    uv run python query_gtex.py tissues
"""
import argparse
import json

import requests

BASE = "https://gtexportal.org/api/v2"
GENCODE_FOR_DATASET = {"gtex_v10": "v39", "gtex_v8": "v26"}


def _get(path: str, params: dict) -> dict:
    r = requests.get(f"{BASE}{path}", params={k: v for k, v in params.items() if v is not None},
                     timeout=60)
    r.raise_for_status()
    return r.json()


def median_expression(gencode_id: str, dataset: str = "gtex_v10") -> dict:
    """Median TPM expression for a gene across tissues."""
    return _get("/expression/medianGeneExpression",
                {"gencodeId": gencode_id, "datasetId": dataset, "itemsPerPage": 250})


def eqtl(gencode_id: str, tissue: str | None = None, dataset: str = "gtex_v10") -> dict:
    """Significant single-tissue cis-eQTLs for a gene."""
    return _get("/association/singleTissueEqtl",
                {"gencodeId": gencode_id, "tissueSiteDetailId": tissue, "datasetId": dataset})


def gene(symbol: str, dataset: str = "gtex_v10") -> dict:
    """Resolve a gene symbol to the versioned GENCODE ID used by `dataset`."""
    return _get("/reference/gene",
                {"geneId": symbol, "gencodeVersion": GENCODE_FOR_DATASET.get(dataset, "v39")})


def tissues(dataset: str = "gtex_v10") -> dict:
    """List available tissue site identifiers."""
    return _get("/dataset/tissueSiteDetail", {"datasetId": dataset, "itemsPerPage": 100})


def main() -> None:
    p = argparse.ArgumentParser(description="Query GTEx Portal API v2 (no key required).")
    sub = p.add_subparsers(dest="cmd", required=True)

    pe = sub.add_parser("expression")
    pe.add_argument("gencode_id", help="versioned GENCODE ID, e.g. ENSG00000130203.10")
    pe.add_argument("--dataset", default="gtex_v10")

    pq = sub.add_parser("eqtl")
    pq.add_argument("gencode_id")
    pq.add_argument("--tissue", default=None, help="e.g. Liver, Whole_Blood")
    pq.add_argument("--dataset", default="gtex_v10")

    pt = sub.add_parser("tissues")
    pt.add_argument("--dataset", default="gtex_v10")

    pg = sub.add_parser("gene")
    pg.add_argument("symbol", help="gene symbol, e.g. APOE")
    pg.add_argument("--dataset", default="gtex_v10")

    args = p.parse_args()
    if args.cmd == "expression":
        out = median_expression(args.gencode_id, args.dataset)
    elif args.cmd == "eqtl":
        out = eqtl(args.gencode_id, args.tissue, args.dataset)
    elif args.cmd == "gene":
        out = gene(args.symbol, args.dataset)
    else:
        out = tissues(args.dataset)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
