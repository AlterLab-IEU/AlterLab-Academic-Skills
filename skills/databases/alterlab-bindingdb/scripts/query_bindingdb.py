#!/usr/bin/env python3
"""Query the BindingDB public REST API (no API key required).

REST base: https://bindingdb.org/rest
  - getLigandsByUniprot   uniprot='<acc>;<cutoff_nM>'
  - getLigandsByPDBs      pdb='<id1,id2>'  cutoff, identity
  - getTargetByCompound   smiles='<SMILES>'  cutoff (Tanimoto)

Smoke test:
    uv run python query_bindingdb.py uniprot P00519 --cutoff 10000
    uv run python query_bindingdb.py pdb 1Q0L,3ANM --cutoff 100 --identity 92
"""
import argparse
import json

import requests

BASE = "https://bindingdb.org/rest"


def by_uniprot(uniprot: str, cutoff: int = 10000) -> dict:
    """Ligands binding a target by UniProt accession (cutoff in nM)."""
    params = {"uniprot": f"{uniprot};{cutoff}", "response": "application/json"}
    r = requests.get(f"{BASE}/getLigandsByUniprot", params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def by_pdb(pdb_ids: str, cutoff: int = 100, identity: int = 92) -> dict:
    """Ligands by one or more comma-separated PDB IDs."""
    params = {"pdb": pdb_ids, "cutoff": cutoff, "identity": identity,
              "response": "application/json"}
    r = requests.get(f"{BASE}/getLigandsByPDBs", params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def by_compound(smiles: str, cutoff: float = 0.85) -> dict:
    """Targets for a compound via SMILES structural-similarity search."""
    params = {"smiles": smiles, "cutoff": cutoff, "response": "application/json"}
    r = requests.get(f"{BASE}/getTargetByCompound", params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def main() -> None:
    p = argparse.ArgumentParser(description="Query BindingDB REST (no key required).")
    sub = p.add_subparsers(dest="cmd", required=True)

    pu = sub.add_parser("uniprot", help="Query ligands by UniProt accession")
    pu.add_argument("accession")
    pu.add_argument("--cutoff", type=int, default=10000, help="affinity cutoff (nM)")

    pp = sub.add_parser("pdb", help="Query ligands by PDB ID(s)")
    pp.add_argument("pdb_ids", help="comma-separated PDB IDs, e.g. 1Q0L,3ANM")
    pp.add_argument("--cutoff", type=int, default=100)
    pp.add_argument("--identity", type=int, default=92)

    pc = sub.add_parser("compound", help="Query targets by SMILES")
    pc.add_argument("smiles")
    pc.add_argument("--cutoff", type=float, default=0.85, help="Tanimoto threshold")

    args = p.parse_args()
    if args.cmd == "uniprot":
        out = by_uniprot(args.accession, args.cutoff)
    elif args.cmd == "pdb":
        out = by_pdb(args.pdb_ids, args.cutoff, args.identity)
    else:
        out = by_compound(args.smiles, args.cutoff)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
