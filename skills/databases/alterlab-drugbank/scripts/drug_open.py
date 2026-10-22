#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Keyless drug records for the DrugBank skill (no DrugBank account or licence needed).

DrugBank's XML, its open-data vocabulary and its drug pages are not reachable without an
account (downloads paused; go.drugbank.com answers 403). These open sources cover the same
fields, and every result names its source:

  ChEMBL (EBI)  identity, SMILES/InChI/InChIKey/formula, Ro5 properties, max phase,
                indications (MeSH/EFO), mechanisms of action with action type and target
                (UniProt accessions), server-side Tanimoto similarity search
  openFDA       US label sections: indications, mechanism of action, pharmacokinetics,
                drug interactions, boxed warning, contraindications (CYP mentions parsed)
  PubChem       CID and computed identifiers (retried; it answers 503 when busy)
  KEGG DRUG     structured drug-drug interaction flags: CI (contraindication) or
                P (precaution), with the mechanism class when KEGG has one
                (KEGG API terms: academic use)

    python drug_open.py info metformin
    python drug_open.py targets imatinib
    python drug_open.py interactions warfarin amiodarone simvastatin
    python drug_open.py similar celecoxib --threshold 70     # ChEMBL-wide neighbours
    uv run --python ">=3.11" drug_similarity.py celecoxib    # vs every approved drug (RDKit)
"""
from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "AlterLab-Academic-Skills/1.0 (alterlab-drugbank keyless)"
CHEMBL = "https://www.ebi.ac.uk/chembl/api/data"
FDA = "https://api.fda.gov/drug/label.json"
PUBCHEM = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
KEGG = "https://rest.kegg.jp"
LABEL_SECTIONS = ("boxed_warning", "contraindications", "drug_interactions", "warnings_and_cautions",
                  "warnings", "precautions", "clinical_pharmacology", "pharmacokinetics")


def _get(url, params=None, accept="application/json", tries=4, raw=False):
    if params:
        url = f"{url}?{urllib.parse.urlencode(params, doseq=True)}"
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
            with urllib.request.urlopen(req, timeout=120) as r:
                body = r.read()
                return body.decode("utf-8", "replace") if raw else json.loads(body)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            if exc.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            print(f"warning: HTTP {exc.code} from {url.split('?')[0]}", file=sys.stderr)
            return None
        except urllib.error.URLError as exc:
            if attempt < tries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            print(f"warning: cannot reach {url.split('?')[0]}: {exc.reason}", file=sys.stderr)
            return None
    return None


# ----------------------------------------------------------------------- ChEMBL
def chembl_molecule(name: str) -> dict | None:
    """Parent molecule record for a drug name or ChEMBL id."""
    if re.fullmatch(r"CHEMBL\d+", name.upper()):
        mol = _get(f"{CHEMBL}/molecule/{name.upper()}.json")
    else:
        hits = (_get(f"{CHEMBL}/molecule.json", {"pref_name__iexact": name, "limit": 5}) or {}).get("molecules")
        if not hits:
            hits = (_get(f"{CHEMBL}/molecule/search.json", {"q": name, "limit": 5}) or {}).get("molecules")
        if not hits:
            return None
        mol = max(hits, key=lambda m: float(m.get("max_phase") or 0))
    parent = ((mol or {}).get("molecule_hierarchy") or {}).get("parent_chembl_id")
    if parent and parent != mol.get("molecule_chembl_id"):
        mol = _get(f"{CHEMBL}/molecule/{parent}.json") or mol
    return mol


def _identity(mol: dict) -> dict:
    s = mol.get("molecule_structures") or {}
    p = mol.get("molecule_properties") or {}
    return {"chembl_id": mol.get("molecule_chembl_id"), "name": mol.get("pref_name"),
            "max_phase": mol.get("max_phase"), "molecule_type": mol.get("molecule_type"),
            "first_approval": mol.get("first_approval"),
            "formula": p.get("full_molformula"), "mw": p.get("full_mwt"),
            "smiles": s.get("canonical_smiles"), "inchi": s.get("standard_inchi"),
            "inchikey": s.get("standard_inchi_key"),
            "ro5": {"alogp": p.get("alogp"), "hba": p.get("hba"), "hbd": p.get("hbd"),
                    "psa": p.get("psa"), "rtb": p.get("rtb"),
                    "violations": p.get("num_ro5_violations")}}


def chembl_mechanisms(chembl_id: str) -> list[dict]:
    rows = (_get(f"{CHEMBL}/mechanism.json", {"parent_molecule_chembl_id": chembl_id, "limit": 100})
            or {}).get("mechanisms", [])
    out = []
    for m in rows:
        tid = m.get("target_chembl_id")
        t = _get(f"{CHEMBL}/target/{tid}.json") if tid else None
        comps = (t or {}).get("target_components") or []
        out.append({"mechanism": m.get("mechanism_of_action"), "action_type": m.get("action_type"),
                    "target_chembl_id": tid, "target": (t or {}).get("pref_name"),
                    "target_type": (t or {}).get("target_type"),
                    "uniprot": [c.get("accession") for c in comps if c.get("accession")][:10],
                    "n_components": len(comps),
                    "refs": [r.get("ref_url") for r in m.get("mechanism_refs") or []][:3]})
    return out


def chembl_indications(chembl_id: str, limit: int = 30) -> list[dict]:
    rows = (_get(f"{CHEMBL}/drug_indication.json",
                 {"parent_molecule_chembl_id": chembl_id, "limit": limit}) or {}).get("drug_indications", [])
    rows.sort(key=lambda r: -float(r.get("max_phase_for_ind") or 0))
    out, seen = [], set()
    for r in rows:
        key = (r.get("mesh_heading"), r.get("efo_term"))
        if key not in seen:
            seen.add(key)
            out.append({"mesh": r.get("mesh_heading"), "efo": r.get("efo_term"),
                        "max_phase": r.get("max_phase_for_ind")})
    return out


# ---------------------------------------------------------------------- openFDA
def fda_label(name: str) -> dict | None:
    """Best openFDA label for a drug: single-ingredient first, then the most complete one."""
    def score(r: dict) -> tuple:
        generics = [g.lower() for g in (r.get("openfda") or {}).get("generic_name", [])]
        single = len(generics) == 1 and " and " not in generics[0] and "/" not in generics[0]
        return (single, sum(bool(r.get(k)) for k in ("indications_and_usage", "mechanism_of_action",
                                                       "drug_interactions", "pharmacokinetics")))
    for field in ("openfda.generic_name", "openfda.brand_name", "openfda.substance_name"):
        d = _get(FDA, {"search": f'{field}:"{name}"', "limit": 25})
        if d and d.get("results"):
            return max(d["results"], key=score)
    return None


def _text(label: dict, key: str) -> str:
    return " ".join(label.get(key) or [])


def cyp_mentions(label: dict) -> dict:
    """CYP isoenzymes named in the label's pharmacokinetic / interaction text, with a quote."""
    found: dict[str, str] = {}
    for key in ("pharmacokinetics", "clinical_pharmacology", "drug_interactions", "metabolism"):
        for sentence in re.split(r"(?<=\.)\s+", _text(label, key)):
            for code in re.findall(r"\bCYP\s?(\d[A-Z]\d{1,2})\b", sentence):
                found.setdefault(f"CYP{code}", f"[{key}] " + " ".join(sentence.split())[:400])
    return found


# ------------------------------------------------------------------------ KEGG
def kegg_ids(name: str) -> list[str]:
    txt = _get(f"{KEGG}/find/drug/{urllib.parse.quote(name)}", accept="text/plain", raw=True) or ""
    return [line.split("\t")[0] for line in txt.splitlines() if line.startswith("dr:") or line[:1] == "D"]


def kegg_pair(a_ids: list[str], b_ids: list[str]) -> list[dict]:
    # With several entries, /ddi/A+B+... returns the interactions AMONG the given entries.
    if not a_ids or not b_ids:
        return []
    a = {x.replace("dr:", "") for x in a_ids[:5]}
    b = {x.replace("dr:", "") for x in b_ids[:5]}
    txt = _get(f"{KEGG}/ddi/{'+'.join(sorted(a | b))}", accept="text/plain", raw=True) or ""
    out = []
    for line in txt.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        x, y = parts[0].replace("dr:", ""), parts[1].replace("dr:", "")
        if (x in a and y in b) or (x in b and y in a):
            out.append({"kegg": f"{parts[0]} -> {parts[1]}",
                        "flag": {"CI": "contraindication", "P": "precaution"}.get(parts[2], parts[2]),
                        "mechanism": parts[3] if len(parts) > 3 else ""})
    return out


# -------------------------------------------------------------------- commands
def info(name: str) -> dict:
    mol = chembl_molecule(name)
    label = fda_label(name)
    pc = _get(f"{PUBCHEM}/compound/name/{urllib.parse.quote(name)}/property/"
              "MolecularFormula,ConnectivitySMILES,InChIKey,IUPACName/JSON")
    out = {"query": name,
           "chembl": _identity(mol) if mol else None,
           "indications_chembl": chembl_indications(mol["molecule_chembl_id"]) if mol else [],
           "mechanisms_chembl": chembl_mechanisms(mol["molecule_chembl_id"]) if mol else [],
           "pubchem": ((pc or {}).get("PropertyTable") or {}).get("Properties", [None])[0],
           "fda_label": None,
           "sources": ["ChEMBL", "openFDA drug label", "PubChem"]}
    if label:
        out["fda_label"] = {"brand": (label.get("openfda") or {}).get("brand_name"),
                            "set_id": label.get("set_id"),
                            "dailymed": f"https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid={label.get('set_id')}",
                            "indications_and_usage": _text(label, "indications_and_usage")[:1500],
                            "mechanism_of_action": _text(label, "mechanism_of_action")[:1500],
                            "pharmacokinetics": _text(label, "pharmacokinetics")[:1500]}
    return out


def targets(name: str) -> dict:
    mol = chembl_molecule(name)
    label = fda_label(name)
    return {"query": name, "chembl_id": (mol or {}).get("molecule_chembl_id"),
            "targets": chembl_mechanisms(mol["molecule_chembl_id"]) if mol else [],
            "metabolising_enzymes_from_label": cyp_mentions(label) if label else {},
            "sources": ["ChEMBL mechanisms", "openFDA label (CYP mentions)"]}


def interactions(names: list[str]) -> dict:
    labels = {n: fda_label(n) for n in names}
    kegg = {n: kegg_ids(n) for n in names}
    pairs = []
    for a, b in itertools.combinations(names, 2):
        evidence = []
        for src, other in ((a, b), (b, a)):
            lab = labels.get(src)
            if not lab:
                continue
            for key in LABEL_SECTIONS:
                for m in re.finditer(r"[^.]{0,220}\b%s\b[^.]{0,260}\.?" % re.escape(other), _text(lab, key), re.I):
                    evidence.append({"label_of": src, "section": key, "text": " ".join(m.group(0).split())})
        pairs.append({"pair": [a, b],
                      "kegg_ddi": kegg_pair(kegg[a], kegg[b]),
                      "fda_label_mentions": evidence[:12],
                      "n_label_mentions": len(evidence)})
    return {"drugs": names, "pairs": pairs,
            "labels_found": {n: bool(v) for n, v in labels.items()},
            "note": "Severity is not graded by these sources: read the label text (contraindicated / "
                    "avoid / dose limit / monitor) and the KEGG CI/P flag, and say so.",
            "sources": ["openFDA drug labels (SPL)", "KEGG DRUG DDI (academic use)"]}


def similar(query: str, threshold: int = 70, approved_only: bool = False, limit: int = 25) -> dict:
    mol = chembl_molecule(query)
    if not mol:
        raise SystemExit(f"No ChEMBL molecule for {query!r}")
    params = {"limit": 200, "only": "molecule_chembl_id,pref_name,similarity,max_phase,molecule_properties"}
    rows = (_get(f"{CHEMBL}/similarity/{mol['molecule_chembl_id']}/{int(threshold)}.json", params)
            or {}).get("molecules", [])
    out = []
    for r in rows:
        if r["molecule_chembl_id"] == mol["molecule_chembl_id"]:
            continue
        if approved_only and float(r.get("max_phase") or 0) < 4:
            continue
        p = r.get("molecule_properties") or {}
        viol = p.get("num_ro5_violations")
        out.append({"chembl_id": r["molecule_chembl_id"], "name": r.get("pref_name"),
                    "tanimoto_pct": round(float(r.get("similarity") or 0), 1),
                    "max_phase": r.get("max_phase"), "mw": p.get("full_mwt"), "alogp": p.get("alogp"),
                    "hba": p.get("hba"), "hbd": p.get("hbd"), "ro5_violations": viol,
                    "passes_lipinski": (viol is not None and int(viol) <= 1)})
    out.sort(key=lambda x: -x["tanimoto_pct"])
    return {"query": _identity(mol), "threshold_pct": threshold, "approved_only": approved_only,
            "similar": out[:limit],
            "note": "ChEMBL-wide neighbours (ChEMBL's own fingerprints, threshold >= 40%); approved "
                    "drugs are often below 40% (valdecoxib vs celecoxib ~32% Morgan), so for a "
                    "repurposing scan over approved drugs use drug_similarity.py. Lipinski pass = at "
                    "most one Rule-of-Five violation (ChEMBL num_ro5_violations).",
            "sources": ["ChEMBL similarity + molecule properties"]}


def main() -> int:
    ap = argparse.ArgumentParser(description="Keyless drug records (ChEMBL, openFDA, PubChem, KEGG).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    pi = sub.add_parser("info", help="identity, structure identifiers, indications, mechanism, label")
    pi.add_argument("name")
    pt = sub.add_parser("targets", help="targets with action type + CYP enzymes named on the label")
    pt.add_argument("name")
    px = sub.add_parser("interactions", help="pairwise DDI evidence for 2+ drugs")
    px.add_argument("names", nargs="+")
    ps = sub.add_parser("similar", help="ChEMBL-wide structural neighbours with Ro5 flags "
                        "(approved-drug scan: drug_similarity.py)")
    ps.add_argument("name")
    ps.add_argument("--threshold", type=int, default=70, help="Tanimoto %% cut-off (ChEMBL: 40-100)")
    ps.add_argument("--approved", action="store_true", help="keep only approved (max_phase 4) hits")
    ps.add_argument("--limit", type=int, default=25)
    a = ap.parse_args()
    if a.cmd == "info":
        out = info(a.name)
    elif a.cmd == "targets":
        out = targets(a.name)
    elif a.cmd == "interactions":
        if len(a.names) < 2:
            ap.error("give at least two drugs")
        out = interactions(a.names)
    else:
        out = similar(a.name, a.threshold, a.approved, a.limit)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
