#!/usr/bin/env python3
"""Keyless HMDB answers when hmdb.ca blocks scripted clients. Standard library only.

hmdb.ca (records, search, downloads) answers scripted requests with a Cloudflare challenge
(HTTP 403, `cf-mitigated: challenge`; checked 2026-10-23). This tool assembles the same
HMDB content from open mirrors, each value tagged with its source:

  record HMDB0000001
      PubChem (HMDB accessions are PubChem RegistryIDs): name, formula, average and
      monoisotopic mass, SMILES, InChI/InChIKey; the HMDB-sourced annotations PubChem
      mirrors: tissue and cellular locations, metabolite pathways, disease associations
      with PubMed IDs. MarkerDB (Wishart lab, built on HMDB): measured concentrations by
      biofluid, normal and per condition, with PMIDs.
  disease "type 2 diabetes"
      MarkerDB condition card: every chemical biomarker with biofluid, disease and normal
      concentration, p-value / AUC where given, clinical status, PMIDs, and the HMDB ID
      where MarkerDB shows one.
  structure "<SMILES>"
      exact structure -> PubChem CID -> HMDB accession(s); plus same-formula isomers that
      carry an HMDB accession (a mass match alone cannot tell isomers apart).

Usage:
    python hmdb_open.py record HMDB0000001
    python hmdb_open.py disease "diabetes mellitus type 2" [--biofluid Blood]
    python hmdb_open.py structure "CN1C=NC2=C1C(=O)NC(=O)N2C" [--isomers 200]
"""
import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

PUG = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
PUGVIEW = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound"
MARKERDB = "https://markerdb.ca"
USER_AGENT = "alterlab-hmdb/1.1 (AlterLab Academic Skills)"
HMDB_SOURCE = "Human Metabolome Database (HMDB)"
RETRY = {429, 500, 502, 503, 504}


def _get(url: str, data: bytes = None, retries: int = 5, timeout: int = 60) -> bytes:
    """GET/POST with a User-Agent, a timeout and backoff on 429/5xx (PubChem's ServerBusy is 503)."""
    req = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code not in RETRY or attempt == retries:
                raise
            wait = e.headers.get("Retry-After")
            time.sleep(float(wait) if wait and wait.isdigit() else 1.5 * 2 ** attempt)
        except urllib.error.URLError:
            if attempt == retries:
                raise
            time.sleep(1.5 * 2 ** attempt)
    raise RuntimeError("unreachable")


def _json(url: str, data: bytes = None):
    return json.loads(_get(url, data))


def normalize_hmdb(acc: str) -> str:
    """'1', 'HMDB00001' or 'HMDB0000001' -> 'HMDB0000001' (HMDB 4+ uses 7 digits)."""
    digits = re.sub(r"\D", "", acc)
    return f"HMDB{int(digits):07d}"


# ---------------------------------------------------------------- PubChem
PROPS = ("Title,IUPACName,MolecularFormula,MolecularWeight,ExactMass,MonoisotopicMass,"
         "SMILES,ConnectivitySMILES,InChI,InChIKey")


def pubchem_cids_for_hmdb(acc: str) -> list:
    try:
        return _json(f"{PUG}/compound/xref/RegistryID/{acc}/cids/JSON")["IdentifierList"]["CID"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return []
        raise


def pubchem_properties(cids: list) -> list:
    ids = ",".join(str(c) for c in cids)
    return _json(f"{PUG}/compound/cid/{ids}/property/{PROPS}/JSON")["PropertyTable"]["Properties"]


def pubchem_hmdb_ids(cids: list) -> dict:
    """CID -> HMDB accessions listed among its RegistryIDs."""
    out = {}
    for i in range(0, len(cids), 100):
        chunk = ",".join(str(c) for c in cids[i:i + 100])
        info = _json(f"{PUG}/compound/cid/{chunk}/xrefs/RegistryID/JSON")["InformationList"]["Information"]
        for rec in info:
            hm = sorted({r for r in rec.get("RegistryID", []) if re.fullmatch(r"HMDB\d{7}", r)})
            if hm:
                out[rec["CID"]] = hm
    return out


def _strings(info: dict) -> list:
    return [s.get("String", "") for s in info.get("Value", {}).get("StringWithMarkup", [])]


def pubchem_hmdb_annotations(cid: int) -> dict:
    """HMDB-sourced sections PubChem mirrors: locations, pathways, disease associations."""
    out = {}
    for heading, key in (("Human Metabolite Information", "metabolite"),
                         ("Associated Disorders and Diseases", "diseases")):
        try:
            rec = _json(f"{PUGVIEW}/{cid}/JSON?heading={urllib.parse.quote_plus(heading)}")["Record"]
        except urllib.error.HTTPError:
            continue
        refs = {r["ReferenceNumber"]: r.get("SourceName") for r in rec.get("Reference", [])}

        def walk(section):
            for sub in section.get("Section", []):
                yield sub
                yield from walk(sub)

        for sec in walk(rec):
            for info in sec.get("Information", []):
                if refs.get(info.get("ReferenceNumber")) != HMDB_SOURCE:
                    continue
                if key == "metabolite":
                    out.setdefault(sec["TOCHeading"], []).extend(_strings(info))
                else:
                    pmids = sorted({p for s in _strings(info) for p in re.findall(r"\b\d{6,9}\b", s)
                                    if s.startswith("PubMed")})
                    out.setdefault("Associated diseases (HMDB)", []).append(
                        {"disease": info.get("Name"), "pmids": pmids[:12], "n_pmids": len(pmids)})
    return out


# ---------------------------------------------------------------- MarkerDB
def _text(fragment: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fragment))).strip()


def _cards(page: str, chemical: str = None, chemical_url: str = None) -> list:
    """Parse MarkerDB biomarker cards (one info-table per chemical x condition x biofluid).
    On a condition page the chemical comes from the card's <h3> link; on a chemical page
    pass it in."""
    out = []
    starts = [m.start() for m in re.finditer(r'<table class="info-table table">', page)]
    heads = [(m.start(), m) for m in re.finditer(r'<h3>\s*<a href="/chemicals/(\d+)">([^<]+)</a>', page)]
    for i, s in enumerate(starts):
        block = page[s:starts[i + 1] if i + 1 < len(starts) else len(page)]
        head = [m for pos, m in heads if pos < s]
        if head:
            name = html.unescape(head[-1].group(2)).strip()
            url = f"{MARKERDB}/chemicals/{head[-1].group(1)}"
        else:
            name, url = chemical or "", chemical_url
        rec = {"chemical": re.sub(r"\s*\(MDB\d+\)$", "", name),
               "markerdb_id": (re.search(r"MDB\d+", name) or [None])[0],
               "markerdb_url": url}
        hm = re.search(r"(HMDB\d{7})_", block)
        if hm:
            rec["hmdb_id"] = hm.group(1)
        side = "disease"
        for label, value in re.findall(r"<strong>([^<]+?):?\s*</strong></td><td[^>]*>(.*?)</td>", block, re.S):
            label = label.strip().rstrip(":")
            if label == "Normal concentration":
                side = "normal"
            val = _text(value)
            if label == "References":
                rec.setdefault(f"{side}_pmids", []).extend(re.findall(r"PMID:\s*(\d+)", val))
            elif label in ("Age", "Sex"):
                rec[f"{side}_{label.lower()}"] = val
            elif label not in ("Condition Categories",):
                rec[label.lower().replace(" ", "_").replace("/", "_")] = val
        out.append(rec)
    return out


def markerdb_search(query: str, searcher: str) -> list:
    page = _get(f"{MARKERDB}/unearth/q?" + urllib.parse.urlencode({"query": query, "searcher": searcher})).decode("utf-8", "replace")
    return [(int(i), _text(n)) for i, n in re.findall(rf'href="/{searcher}/(\d+)">([^<]+)</a>', page)]


def markerdb_chemical(hmdb_id: str) -> list:
    hits = markerdb_search(hmdb_id, "chemicals")
    if not hits:
        return []
    url = f"{MARKERDB}/chemicals/{hits[0][0]}"
    page = _get(url).decode("utf-8", "replace")
    if hmdb_id not in page:  # the search matched something else
        return []
    title = re.search(r"Showing biomarkercard for ([^<]+)", page)
    cards = _cards(page, title.group(1).strip() if title else "", url)
    for c in cards:
        c.setdefault("hmdb_id", hmdb_id)
    return cards


# ---------------------------------------------------------------- commands
def cmd_record(acc: str) -> dict:
    acc = normalize_hmdb(acc)
    out = {"hmdb_id": acc, "hmdb_url": f"https://hmdb.ca/metabolites/{acc}",
           "note": "hmdb.ca blocks scripted clients (Cloudflare challenge); values below come "
                   "from the sources named in each field.", "sources": {}}
    cids = pubchem_cids_for_hmdb(acc)
    if not cids:
        out["error"] = f"No PubChem compound lists {acc} as a RegistryID."
        return out
    props = pubchem_properties(cids[:1])[0]
    out["pubchem_cid"] = cids[0]
    out["other_cids"] = cids[1:5]
    out["identity"] = props
    out["sources"]["identity"] = f"PubChem CID {cids[0]} (PUG-REST)"
    ann = pubchem_hmdb_annotations(cids[0])
    if ann:
        out["hmdb_annotations"] = ann
        out["sources"]["hmdb_annotations"] = f"PubChem PUG-View, entries sourced from {HMDB_SOURCE} {acc}"
    cards = markerdb_chemical(acc)
    if cards:
        out["concentrations"] = cards
        out["biofluids_with_measurements"] = sorted({c.get("biofluid") for c in cards if c.get("biofluid")})
        out["sources"]["concentrations"] = f"MarkerDB {cards[0]['markerdb_url']}"
    else:
        out["concentrations"] = "MarkerDB lists no concentration records for this metabolite"
    return out


def cmd_disease(query: str, biofluid: str = None) -> dict:
    hits = markerdb_search(query, "conditions")
    if not hits:
        return {"query": query, "error": "MarkerDB has no matching condition"}
    q = query.lower()
    words = [w for w in re.findall(r"[a-z0-9]+", q) if w not in ("of", "the", "and", "disease")]
    exact = [h for h in hits if h[1].lower() == q]
    covering = [h for h in hits if all(re.search(rf"\b{re.escape(w)}\b", h[1].lower()) for w in words)]
    if not (exact or covering):  # MarkerDB's search is fuzzy; never pick an unrelated condition
        return {"query": query, "error": "no MarkerDB condition name contains every query word",
                "candidates": [h[1] for h in hits[:10]]}
    cid, name = (exact or covering)[0]
    page = _get(f"{MARKERDB}/conditions/{cid}").decode("utf-8", "replace")
    chem = page.split('id="Chemical_Biomarkers"', 1)
    section = ""
    if len(chem) > 1:  # up to the next biomarker list (genetic, protein, ...)
        end = chem[1].find('class="list box"', 40)
        section = chem[1][:end] if end > 0 else chem[1]
    cards = _cards(section)
    if biofluid:
        cards = [c for c in cards if (c.get("biofluid") or "").lower() == biofluid.lower()]
    return {"condition": name, "markerdb_url": f"{MARKERDB}/conditions/{cid}",
            "other_matches": [h[1] for h in hits[1:8]], "n_chemical_biomarker_records": len(cards),
            "chemicals": sorted({c["chemical"] for c in cards}), "records": cards,
            "source": "MarkerDB 2.0 (Wishart lab; concentrations curated from HMDB and the literature)"}


def cmd_structure(smiles: str, isomers: int = 200) -> dict:
    data = urllib.parse.urlencode({"smiles": smiles}).encode()
    try:
        cids = _json(f"{PUG}/compound/smiles/cids/JSON", data)["IdentifierList"]["CID"]
    except urllib.error.HTTPError as e:
        return {"smiles": smiles, "error": f"PubChem could not parse or match the SMILES (HTTP {e.code})"}
    cids = [c for c in cids if c]
    out = {"query_smiles": smiles}
    if not cids:
        out["exact_match"] = None
        return out
    props = pubchem_properties(cids[:1])[0]
    hm = pubchem_hmdb_ids(cids[:1])
    out["exact_match"] = {"pubchem_cid": cids[0], "hmdb_ids": hm.get(cids[0], []),
                          "name": props.get("Title"), "formula": props.get("MolecularFormula"),
                          "monoisotopic_mass": props.get("MonoisotopicMass"),
                          "inchikey": props.get("InChIKey")}
    if isomers and props.get("MolecularFormula"):
        f = props["MolecularFormula"]
        try:
            iso = _json(f"{PUG}/compound/fastformula/{f}/cids/JSON?MaxRecords={isomers}")["IdentifierList"]["CID"]
        except urllib.error.HTTPError:
            iso = []
        with_hmdb = pubchem_hmdb_ids([c for c in iso if c != cids[0]])
        names = {p["CID"]: p.get("Title") for p in pubchem_properties(list(with_hmdb)[:100])} if with_hmdb else {}
        out["same_formula_with_hmdb"] = [{"pubchem_cid": c, "name": names.get(c), "hmdb_ids": h}
                                         for c, h in with_hmdb.items()]
        out["isomer_note"] = (f"{len(with_hmdb)} other PubChem compounds with formula {f} (first "
                              f"{isomers} checked) carry an HMDB accession; a mass-only match cannot "
                              "tell them apart.")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Keyless HMDB content via PubChem and MarkerDB.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record", help="metabolite by HMDB accession")
    r.add_argument("hmdb_id")
    d = sub.add_parser("disease", help="chemical biomarkers of a condition (MarkerDB)")
    d.add_argument("query")
    d.add_argument("--biofluid", default=None, help="e.g. Blood, Urine")
    s = sub.add_parser("structure", help="HMDB accession(s) for a structure (SMILES)")
    s.add_argument("smiles")
    s.add_argument("--isomers", type=int, default=200, help="same-formula CIDs to check (0 = skip)")
    a = ap.parse_args()
    try:
        if a.cmd == "record":
            out = cmd_record(a.hmdb_id)
        elif a.cmd == "disease":
            out = cmd_disease(a.query, a.biofluid)
        else:
            out = cmd_structure(a.smiles, a.isomers)
    except urllib.error.URLError as e:
        print(f"network error: {e}", file=sys.stderr)
        return 1
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
