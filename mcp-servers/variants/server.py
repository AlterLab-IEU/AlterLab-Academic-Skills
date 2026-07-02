#!/usr/bin/env python3
"""AlterLab `variants` MCP connector.

Aggregates human-variant sources behind one typed tool surface: gnomAD (population
frequencies, via its GraphQL API) and ClinVar/dbSNP (clinical significance and rsIDs, via NCBI
E-utilities). Each tool returns typed JSON and degrades gracefully. Authoring references: the
`alterlab-gnomad` and `alterlab-clinvar` skills document the same endpoints.

Credentials/etiquette: NCBI requests read a contact email from NCBI_EMAIL (E-utilities policy);
no key is hardcoded. Set NCBI_API_KEY to raise the NCBI rate limit if you have one.

Run:  uv run --with fastmcp python mcp-servers/variants/server.py
Stdlib HTTP only (urllib); sole third-party dependency is `fastmcp`.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from fastmcp import FastMCP

mcp = FastMCP("variants")

_TIMEOUT = 30
_UA = "AlterLab-variants-connector/1.0"
_GNOMAD_API = "https://gnomad.broadinstitute.org/api"
_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def _get_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {"error": f"HTTP {exc.code}", "url": url}
    except (urllib.error.URLError, TimeoutError) as exc:
        return {"error": f"request failed: {exc}", "url": url}
    except json.JSONDecodeError:
        return {"error": "non-JSON response", "url": url}


def _gnomad_query(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    """POST a GraphQL query to the gnomAD API. Schema fields may drift — TODO(verify)."""
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(
        _GNOMAD_API, data=body,
        headers={"User-Agent": _UA, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {"error": f"HTTP {exc.code}", "api": _GNOMAD_API}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"error": f"gnomAD request failed: {exc}"}


def _ncbi_params(extra: dict[str, str]) -> str:
    params = {"tool": "alterlab-variants", **extra}
    if os.environ.get("NCBI_EMAIL"):
        params["email"] = os.environ["NCBI_EMAIL"]
    if os.environ.get("NCBI_API_KEY"):
        params["api_key"] = os.environ["NCBI_API_KEY"]
    return urllib.parse.urlencode(params)


@mcp.tool()
def gene_variants(gene_symbol: str, dataset: str = "gnomad_r4") -> dict[str, Any]:
    """List variants in a gene from gnomAD (via its GraphQL API).

    Args:
        gene_symbol: HGNC gene symbol (e.g. "BRCA1").
        dataset: gnomAD dataset id (e.g. "gnomad_r4"). TODO(verify) current dataset ids.
    Returns:
        gnomAD GraphQL response with the gene's variants (id, consequence, allele frequency),
        or an error object.
    """
    query = (
        "query GeneVariants($symbol: String!, $dataset: DatasetId!) {"
        "  gene(gene_symbol: $symbol, reference_genome: GRCh38) {"
        "    variants(dataset: $dataset) { variant_id consequence "
        "      genome { af ac an } } } }"
    )
    return _gnomad_query(query, {"symbol": gene_symbol.strip().upper(), "dataset": dataset})


@mcp.tool()
def variant_frequency(variant_id: str, dataset: str = "gnomad_r4") -> dict[str, Any]:
    """Population allele frequency for a single variant from gnomAD.

    Args:
        variant_id: gnomAD variant id "chrom-pos-ref-alt" (e.g. "1-55051215-G-GA").
        dataset: gnomAD dataset id. TODO(verify) current dataset ids.
    Returns:
        gnomAD GraphQL response with genome/exome allele frequency and popmax, or an error.
    """
    query = (
        "query VariantFreq($id: String!, $dataset: DatasetId!) {"
        "  variant(variantId: $id, dataset: $dataset) {"
        "    variant_id genome { af ac an } exome { af ac an } } }"
    )
    return _gnomad_query(query, {"id": variant_id.strip(), "dataset": dataset})


@mcp.tool()
def clinvar_record(term: str, retmax: int = 5) -> dict[str, Any]:
    """Look up ClinVar records (clinical significance) for a variant/gene term via NCBI.

    Args:
        term: a ClinVar search term (gene, rsID, HGVS, or condition).
        retmax: max records to summarize (1-20).
    Returns:
        {"ids": [...], "summary": {...}} from ClinVar esearch + esummary, or an error object.
    """
    retmax = max(1, min(int(retmax), 20))
    search = _get_json(
        f"{_EUTILS}/esearch.fcgi?"
        + _ncbi_params({"db": "clinvar", "term": term, "retmax": str(retmax), "retmode": "json"})
    )
    ids = (search.get("esearchresult", {}) or {}).get("idlist", []) if isinstance(search, dict) else []
    if not ids:
        return {"ids": [], "summary": {}, "note": "no ClinVar records", "raw": search}
    summary = _get_json(
        f"{_EUTILS}/esummary.fcgi?"
        + _ncbi_params({"db": "clinvar", "id": ",".join(ids), "retmode": "json"})
    )
    return {"ids": ids, "summary": summary}


if __name__ == "__main__":
    mcp.run()
