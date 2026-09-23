#!/usr/bin/env python3
"""AlterLab `structures` MCP connector.

Aggregates the highest-traffic structural-biology sources behind one typed tool surface:
experimental structures (RCSB PDB), predicted structures (AlphaFold DB), and macromolecular
complexes (EBI Complex Portal). Each tool returns typed JSON and degrades gracefully when a
source API is unreachable. Authoring references: the `alterlab-pdb` and `alterlab-alphafold-db`
skills document the same endpoints.

Run:  uv run --with fastmcp python mcp-servers/structures/server.py
Stdlib HTTP only (urllib), so the sole third-party dependency is `fastmcp`.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from fastmcp import FastMCP

mcp = FastMCP("structures")

_TIMEOUT = 30
_UA = "AlterLab-structures-connector/1.0 (mailto:alterlab.ieu@gmail.com)"


def _get_json(url: str) -> dict[str, Any]:
    """GET a URL and parse JSON, returning a typed error object instead of raising."""
    req = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:  # noqa: S310 (trusted hosts)
            data = json.loads(resp.read().decode("utf-8"))
        # Tools return dict[str, Any]; MCP structured output rejects a bare top-level array,
        # so wrap one (AlphaFold DB and Reactome, for example, answer with a list).
        return data if isinstance(data, dict) else {"results": data}
    except urllib.error.HTTPError as exc:
        return {"error": f"HTTP {exc.code}", "url": url}
    except (urllib.error.URLError, TimeoutError) as exc:
        return {"error": f"request failed: {exc}", "url": url}
    except json.JSONDecodeError:
        return {"error": "non-JSON response", "url": url}


@mcp.tool()
def get_structure(pdb_id: str) -> dict[str, Any]:
    """Fetch experimental-structure metadata for a PDB entry from RCSB.

    Args:
        pdb_id: 4-character PDB identifier (e.g. "1CRN").
    Returns:
        The RCSB core-entry JSON (title, method, resolution, deposition), or an error object.
    """
    pid = pdb_id.strip().upper()
    if len(pid) != 4:
        return {"error": "pdb_id must be a 4-character PDB id", "given": pdb_id}
    return _get_json(f"https://data.rcsb.org/rest/v1/core/entry/{pid}")


@mcp.tool()
def get_alphafold_prediction(uniprot_accession: str) -> dict[str, Any]:
    """Fetch the AlphaFold DB predicted-structure metadata for a UniProt accession.

    Args:
        uniprot_accession: UniProt accession (e.g. "P00520").
    Returns:
        {"accession", "models": [...]} with one compact record per model (canonical isoform
        first): entry id, model version and date, mean pLDDT (globalMetricValue), and the
        PDB/mmCIF/PAE file URLs — or an error object.
    """
    acc = uniprot_accession.strip().upper()
    data = _get_json(f"https://alphafold.ebi.ac.uk/api/prediction/{acc}")
    if "error" in data:
        return data
    keep = (
        "entryId", "uniprotAccession", "gene", "organismScientificName", "latestVersion",
        "modelCreatedDate", "globalMetricValue", "sequenceStart", "sequenceEnd",
        "pdbUrl", "cifUrl", "bcifUrl", "paeImageUrl", "paeDocUrl",
    )
    models = [{k: e[k] for k in keep if k in e} for e in data.get("results", []) if isinstance(e, dict)]
    models.sort(key=lambda m: m.get("uniprotAccession") != acc)  # canonical isoform first
    return {"accession": acc, "models": models}


@mcp.tool()
def search_complexes(query: str, size: int = 10) -> dict[str, Any]:
    """Search the EBI Complex Portal for curated macromolecular complexes.

    Args:
        query: free-text query (protein name, complex name, or accession).
        size: max results to return (1-50).
    Returns:
        The Complex Portal search JSON (matching complexes), or an error object.
    """
    size = max(1, min(int(size), 50))
    q = urllib.parse.quote(query.strip())
    return _get_json(
        f"https://www.ebi.ac.uk/intact/complex-ws/search/{q}?number={size}"
    )


if __name__ == "__main__":
    mcp.run()
