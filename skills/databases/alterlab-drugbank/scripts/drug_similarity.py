#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["rdkit"]
# ///
"""Keyless drug-similarity scan: one query drug against every approved small-molecule drug.

The approved set (ChEMBL max_phase 4, small molecules, ~3,500 parents) is fetched once from
the keyless ChEMBL API and cached as JSON; fingerprints, Tanimoto similarity and the
Lipinski / Veber checks are computed locally with RDKit. No DrugBank account needed.

    uv run --python ">=3.11" scripts/drug_similarity.py celecoxib --top 15
    uv run --python ">=3.11" scripts/drug_similarity.py "CC1=CC=C(C=C1)C1=CC(=NN1C1=CC=C(C=C1)S(N)(=O)=O)C(F)(F)F" --fp maccs
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from drug_open import CHEMBL, _get, chembl_molecule  # noqa: E402

from rdkit import Chem, DataStructs, RDLogger  # noqa: E402
from rdkit.Chem import Descriptors, Lipinski, MACCSkeys, rdFingerprintGenerator  # noqa: E402

RDLogger.DisableLog("rdApp.*")


def approved_set(cache: Path) -> list[dict]:
    if cache.exists() and time.time() - cache.stat().st_mtime < 30 * 24 * 3600:
        return json.loads(cache.read_text())
    rows, offset = [], 0
    while True:
        page = _get(f"{CHEMBL}/molecule.json", {
            "max_phase": 4, "molecule_type": "Small molecule", "limit": 1000, "offset": offset,
            "only": "molecule_chembl_id,pref_name,molecule_structures,molecule_hierarchy"}) or {}
        for m in page.get("molecules", []):
            smi = (m.get("molecule_structures") or {}).get("canonical_smiles")
            parent = (m.get("molecule_hierarchy") or {}).get("parent_chembl_id")
            if smi and (not parent or parent == m["molecule_chembl_id"]):  # parents only, no salts
                rows.append({"chembl_id": m["molecule_chembl_id"], "name": m.get("pref_name"), "smiles": smi})
        if not (page.get("page_meta") or {}).get("next"):
            break
        offset += 1000
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(rows))
    return rows


def fingerprint(mol, kind: str):
    if kind == "maccs":
        return MACCSkeys.GenMACCSKeys(mol)
    return rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048).GetFingerprint(mol)


def rules(mol) -> dict:
    mw, logp = Descriptors.MolWt(mol), Descriptors.MolLogP(mol)
    hbd, hba = Lipinski.NumHDonors(mol), Lipinski.NumHAcceptors(mol)
    tpsa, rotb = Descriptors.TPSA(mol), Lipinski.NumRotatableBonds(mol)
    violations = sum([mw > 500, logp > 5, hbd > 5, hba > 10])
    return {"mw": round(mw, 1), "logp": round(logp, 2), "hbd": hbd, "hba": hba,
            "tpsa": round(tpsa, 1), "rot_bonds": rotb, "lipinski_violations": violations,
            "passes_lipinski": violations <= 1, "passes_veber": rotb <= 10 and tpsa <= 140}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("query", help="drug name, ChEMBL id, or SMILES")
    ap.add_argument("--fp", choices=["morgan", "maccs"], default="morgan",
                    help="Morgan radius 2 / 2048 bits (default) or MACCS keys")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--min", type=float, default=0.0, help="minimum Tanimoto (0-1)")
    ap.add_argument("--cache", default=os.path.join("drug_open_cache", "chembl_approved_small_molecules.json"))
    a = ap.parse_args()

    qmol = Chem.MolFromSmiles(a.query) if any(c in a.query for c in "=()[]#") else None
    qinfo = {"query": a.query}
    if qmol is None:
        rec = chembl_molecule(a.query)
        smi = ((rec or {}).get("molecule_structures") or {}).get("canonical_smiles")
        if not smi:
            raise SystemExit(f"No structure found for {a.query!r} in ChEMBL")
        qmol = Chem.MolFromSmiles(smi)
        qinfo.update(chembl_id=rec.get("molecule_chembl_id"), name=rec.get("pref_name"), smiles=smi)
    qfp = fingerprint(qmol, a.fp)
    hits = []
    for d in approved_set(Path(a.cache)):
        if d.get("chembl_id") == qinfo.get("chembl_id"):
            continue
        mol = Chem.MolFromSmiles(d["smiles"])
        if mol is None:
            continue
        sim = DataStructs.TanimotoSimilarity(qfp, fingerprint(mol, a.fp))
        if sim >= a.min:
            hits.append((sim, d, mol))
    hits.sort(key=lambda x: -x[0])
    out = {"query": {**qinfo, **rules(qmol)}, "fingerprint": a.fp, "approved_drugs_screened": None,
           "results": [{"name": d["name"], "chembl_id": d["chembl_id"], "tanimoto": round(s, 3),
                        **rules(m), "smiles": d["smiles"]} for s, d, m in hits[:a.top]],
           "source": "ChEMBL approved small molecules (max_phase 4); RDKit fingerprints and rules"}
    out["approved_drugs_screened"] = len(json.loads(Path(a.cache).read_text()))
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
