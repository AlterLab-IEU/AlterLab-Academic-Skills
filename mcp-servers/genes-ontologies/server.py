#!/usr/bin/env python3
"""AlterLab `genes-ontologies` MCP connector.

Aggregates gene/protein annotation and ontology sources behind one typed tool surface:
MyGene.info (gene lookup), UniProt (protein entries), EBI QuickGO (GO annotations), and
Reactome (pathways). Each tool returns typed JSON and degrades gracefully. Authoring
references: the `alterlab-uniprot`, `alterlab-reactome`, and `alterlab-gene-db` skills document
the same endpoints.

Run:  uv run --with fastmcp python mcp-servers/genes-ontologies/server.py
Stdlib HTTP only (urllib); sole third-party dependency is `fastmcp`.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from fastmcp import FastMCP

mcp = FastMCP("genes-ontologies")

_TIMEOUT = 30
_UA = "AlterLab-genes-ontologies-connector/1.0 (mailto:alterlab.ieu@gmail.com)"


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


@mcp.tool()
def gene_info(query: str, species: str = "human") -> dict[str, Any]:
    """Look up a gene across identifiers via MyGene.info.

    Args:
        query: gene symbol, name, or identifier (e.g. "TP53" or "entrezgene:7157").
        species: species filter (default "human").
    Returns:
        MyGene.info query JSON (symbol, name, entrez/ensembl ids), or an error object.
    """
    params = urllib.parse.urlencode({
        "q": query.strip(),
        "species": species,
        "fields": "symbol,name,entrezgene,ensembl.gene,uniprot.Swiss-Prot",
    })
    return _get_json(f"https://mygene.info/v3/query?{params}")


@mcp.tool()
def uniprot_entry(accession: str) -> dict[str, Any]:
    """Fetch a UniProtKB entry (function, features, cross-references).

    Args:
        accession: UniProt accession (e.g. "P04637").
    Returns:
        The UniProtKB entry JSON, or an error object.
    """
    acc = accession.strip().upper()
    return _get_json(f"https://rest.uniprot.org/uniprotkb/{acc}.json")


@mcp.tool()
def go_annotations(gene_product_id: str, limit: int = 25) -> dict[str, Any]:
    """GO annotations for a gene product from EBI QuickGO.

    Args:
        gene_product_id: a UniProt accession (e.g. "P04637").
        limit: max annotations to return (1-100).
    Returns:
        QuickGO annotation-search JSON (GO id, aspect, evidence), or an error object.
    """
    limit = max(1, min(int(limit), 100))
    params = urllib.parse.urlencode({
        "geneProductId": gene_product_id.strip().upper(),
        "limit": str(limit),
    })
    return _get_json(
        f"https://www.ebi.ac.uk/QuickGO/services/annotation/search?{params}"
    )


@mcp.tool()
def pathways(uniprot_accession: str, species: str = "Homo sapiens") -> dict[str, Any]:
    """Reactome pathways a protein participates in, by UniProt accession.

    Args:
        uniprot_accession: UniProt accession (e.g. "P04637").
        species: species name filter (default "Homo sapiens").
    Returns:
        Reactome ContentService JSON list of mapped pathways, or an error object.
        TODO(verify) the mapping endpoint/params against the current ContentService.
    """
    acc = urllib.parse.quote(uniprot_accession.strip().upper())
    sp = urllib.parse.quote(species)
    return _get_json(
        f"https://reactome.org/ContentService/data/mapping/UniProt/{acc}/pathways?species={sp}"
    )


if __name__ == "__main__":
    mcp.run()
