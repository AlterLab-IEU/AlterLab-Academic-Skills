#!/usr/bin/env python3
"""AlterLab `chemistry` MCP connector.

Aggregates compound and bioactivity sources behind one typed tool surface: PubChem (compound
lookup and 2D similarity, via PUG REST) and BindingDB (measured protein–ligand affinities).
Each tool returns typed JSON and degrades gracefully. Authoring references: the
`alterlab-pubchem` and `alterlab-bindingdb` skills document the same endpoints.

Run:  uv run --with fastmcp python mcp-servers/chemistry/server.py
Stdlib HTTP only (urllib); sole third-party dependency is `fastmcp`.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from fastmcp import FastMCP

mcp = FastMCP("chemistry")

_TIMEOUT = 30
_UA = "AlterLab-chemistry-connector/1.0 (mailto:alterlab.ieu@gmail.com)"
_PUBCHEM = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
_BINDINGDB = "https://bindingdb.org/rest"


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
def compound_by_name(name: str) -> dict[str, Any]:
    """Resolve a compound name to its PubChem identity + key properties.

    Args:
        name: a chemical name or synonym (e.g. "aspirin").
    Returns:
        PubChem property JSON (CID, MolecularFormula, MolecularWeight, CanonicalSMILES,
        InChIKey), or an error object.
    """
    props = "MolecularFormula,MolecularWeight,CanonicalSMILES,InChIKey,IUPACName"
    n = urllib.parse.quote(name.strip())
    return _get_json(f"{_PUBCHEM}/compound/name/{n}/property/{props}/JSON")


@mcp.tool()
def similarity_search(smiles: str, threshold: int = 90, max_records: int = 25) -> dict[str, Any]:
    """2D Tanimoto similarity search in PubChem for compounds like a query SMILES.

    Args:
        smiles: query structure as SMILES.
        threshold: minimum 2D Tanimoto similarity percent (0-100).
        max_records: max CIDs to return (1-100).
    Returns:
        PubChem JSON with the matching CID list, or an error object.
    """
    threshold = max(0, min(int(threshold), 100))
    max_records = max(1, min(int(max_records), 100))
    s = urllib.parse.quote(smiles.strip())
    return _get_json(
        f"{_PUBCHEM}/compound/fastsimilarity_2d/smiles/{s}/cids/JSON"
        f"?Threshold={threshold}&MaxRecords={max_records}"
    )


@mcp.tool()
def binding_affinity(uniprot_accession: str, cutoff_nm: int = 10000) -> dict[str, Any]:
    """Measured protein–ligand binding affinities for a target from BindingDB.

    Args:
        uniprot_accession: the target protein's UniProt accession (e.g. "P00533").
        cutoff_nm: affinity cutoff in nM (return ligands with measured affinity below this).
    Returns:
        BindingDB JSON of ligands + measured affinities (Ki/Kd/IC50) for the target, or an
        error object. TODO(verify) the exact BindingDB REST path/params for your use.
    """
    acc = uniprot_accession.strip().upper()
    cutoff_nm = max(1, int(cutoff_nm))
    return _get_json(
        f"{_BINDINGDB}/getLigandsByUniprots?uniprot={acc}"
        f"&cutoff={cutoff_nm}&response=application/json"
    )


if __name__ == "__main__":
    mcp.run()
