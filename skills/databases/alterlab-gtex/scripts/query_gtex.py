#!/usr/bin/env python3
"""Query the GTEx Portal API v2 (no authentication required).

Base: https://gtexportal.org/api/v2/  (GET, JSON)
  /expression/medianGeneExpression   gencodeId, datasetId -> median TPM per tissue
  /association/singleTissueEqtl       gencodeId|variantId, tissueSiteDetailId
  /association/singleTissueSqtl       gencodeId, tissueSiteDetailId (splicing QTLs)
  /dataset/tissueSiteDetail           list available tissues
  /reference/gene                     geneId (symbol), gencodeVersion -> versioned gencodeId

Gene IDs are versioned GENCODE IDs whose .version suffix must match the dataset:
gtex_v10 uses GENCODE v39 (e.g. APOE = ENSG00000130203.10, PCSK9 = ENSG00000169174.11),
gtex_v8 uses GENCODE v26. The wrong suffix silently returns zero rows.

eqtl/sqtl accept a symbol (resolved to the dataset's GENCODE ID) or a versioned ID, and page
through every result: a single page holds at most itemsPerPage rows (ERAP2 has 655 muscle
sQTLs in gtex_v10; one default page returns 250). Standard library only.

Smoke test:
    python query_gtex.py gene APOE            # -> ENSG00000130203.10 (gtex_v10)
    python query_gtex.py expression ENSG00000130203.10
    python query_gtex.py eqtl PCSK9 --tissue Liver
    python query_gtex.py sqtl ERAP2 --tissue Muscle_Skeletal --summary
    python query_gtex.py tissues
"""
import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://gtexportal.org/api/v2"
GENCODE_FOR_DATASET = {"gtex_v10": "v39", "gtex_v8": "v26"}
USER_AGENT = "alterlab-gtex/1.1 (AlterLab Academic Skills)"


def _get(path: str, params: dict, retries: int = 4) -> dict:
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    req = urllib.request.Request(f"{BASE}{path}?{query}",
                                 headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or attempt == retries:
                raise
        except urllib.error.URLError:
            if attempt == retries:
                raise
        time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def _get_all(path: str, params: dict) -> dict:
    """Every page of a paged endpoint, as {"data": [...], "totalNumberOfItems": n}."""
    params = dict(params, itemsPerPage=1000)
    rows, page = [], 0
    while True:
        data = _get(path, dict(params, page=page))
        rows.extend(data.get("data", []))
        info = data.get("paging_info", {})
        page += 1
        if page >= info.get("numberOfPages", 1):
            return {"data": rows, "totalNumberOfItems": info.get("totalNumberOfItems", len(rows))}


def _gencode(gene_or_id: str, dataset: str) -> str:
    """Pass a versioned ENSG through; resolve a symbol for this dataset's GENCODE release."""
    if gene_or_id.startswith("ENSG") and "." in gene_or_id:
        return gene_or_id
    hits = gene(gene_or_id, dataset).get("data", [])
    if not hits:
        raise SystemExit(f"{gene_or_id}: not found in GENCODE {GENCODE_FOR_DATASET.get(dataset)}")
    return hits[0]["gencodeId"]


def median_expression(gencode_id: str, dataset: str = "gtex_v10") -> dict:
    """Median TPM expression for a gene across tissues."""
    return _get("/expression/medianGeneExpression",
                {"gencodeId": gencode_id, "datasetId": dataset, "itemsPerPage": 250})


def eqtl(gencode_id: str, tissue: str | None = None, dataset: str = "gtex_v10") -> dict:
    """All significant single-tissue cis-eQTLs for a gene (every page)."""
    return _get_all("/association/singleTissueEqtl",
                    {"gencodeId": _gencode(gencode_id, dataset), "tissueSiteDetailId": tissue,
                     "datasetId": dataset})


def sqtl(gencode_id: str, tissue: str | None = None, dataset: str = "gtex_v10") -> dict:
    """All significant single-tissue sQTLs for a gene (every page; datasetId always sent,
    because this endpoint falls back to gtex_v8 without it)."""
    return _get_all("/association/singleTissueSqtl",
                    {"gencodeId": _gencode(gencode_id, dataset), "tissueSiteDetailId": tissue,
                     "datasetId": dataset})


def qtl_summary(result: dict) -> dict:
    """Counts, distinct phenotypes (introns for sQTLs) and the five strongest associations."""
    rows = sorted(result["data"], key=lambda r: r.get("pValue", 1.0))
    by_pheno = {}
    for r in rows:
        by_pheno.setdefault(r.get("phenotypeId") or r.get("gencodeId"), r)
    keep = ("snpId", "variantId", "phenotypeId", "tissueSiteDetailId", "nes", "pValue")
    return {
        "associations": result["totalNumberOfItems"],
        "variants": len({r.get("variantId") for r in rows}),
        "phenotypes": {k: {f: v.get(f) for f in ("snpId", "nes", "pValue")} for k, v in by_pheno.items()},
        "top": [{f: r.get(f) for f in keep} for r in rows[:5]],
    }


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

    for name in ("eqtl", "sqtl"):
        pq = sub.add_parser(name)
        pq.add_argument("gencode_id", help="symbol (e.g. ERAP2) or versioned GENCODE ID")
        pq.add_argument("--tissue", default=None, help="e.g. Liver, Muscle_Skeletal")
        pq.add_argument("--dataset", default="gtex_v10")
        pq.add_argument("--summary", action="store_true",
                        help="counts, distinct phenotypes and top hits instead of all rows")

    pt = sub.add_parser("tissues")
    pt.add_argument("--dataset", default="gtex_v10")

    pg = sub.add_parser("gene")
    pg.add_argument("symbol", help="gene symbol, e.g. APOE")
    pg.add_argument("--dataset", default="gtex_v10")

    args = p.parse_args()
    if args.cmd == "expression":
        out = median_expression(args.gencode_id, args.dataset)
    elif args.cmd in ("eqtl", "sqtl"):
        out = (eqtl if args.cmd == "eqtl" else sqtl)(args.gencode_id, args.tissue, args.dataset)
        if args.summary:
            out = qtl_summary(out)
    elif args.cmd == "gene":
        out = gene(args.symbol, args.dataset)
    else:
        out = tissues(args.dataset)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
