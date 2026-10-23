#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Keyless somatic-cancer data for the COSMIC skill (no COSMIC account needed).

COSMIC's own products (Cancer Gene Census, mutation exports, resistance file) sit behind a
login, and its gene pages show data only after login. These keyless sources answer the
same questions; every result names its source so it is never passed off as COSMIC:

  signatures  COSMIC Mutational Signatures (cancer.sanger.ac.uk/signatures) — the
              reference matrices download without login (v3.6: SBS/DBS/ID/CN/SV/RNA).
  genes       OncoKB Cancer Gene List (oncokb.org) — ONCOGENE / TSG type per gene and a
              "COSMIC CGC (v99)" membership column; a public proxy for the CGC, not v104.
  hotspots    Cancer Hotspots (cancerhotspots.org, MSK; Chang et al. 2016/2018) —
              statistically recurrent residues with tumour counts and tumour-type mix.
  mutations   cBioPortal public API — somatic mutations of a gene across public cohorts
              (default: the 32 TCGA PanCancer Atlas studies; or msk_impact_2017; or ids).
  resistance  CIViC (civicdb.org GraphQL) — curated predictive evidence whose significance
              is RESISTANCE, by gene or molecular profile, with drug, disease, level.

    python cosmic_open.py signatures --type SBS --genome GRCh38 -o COSMIC_v3.6_SBS_GRCh38.txt
    python cosmic_open.py genes --gene TP53 --gene KRAS
    python cosmic_open.py genes --cgc-only --csv > cgc_proxy.csv
    python cosmic_open.py hotspots BRAF
    python cosmic_open.py mutations TP53 --top 15
    python cosmic_open.py resistance --gene EGFR
    python cosmic_open.py resistance --profile "EGFR T790M"
"""
from __future__ import annotations

import argparse
import base64
import csv
import io
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict

UA = "AlterLab-Academic-Skills/1.0 (alterlab-cosmic keyless)"
SIG_PAGE = "https://cancer.sanger.ac.uk/signatures/downloads/"
ONCOKB_LIST = "https://www.oncokb.org/api/v1/utils/cancerGeneList.txt"
HOTSPOTS = "https://www.cancerhotspots.org/api/hotspots/single/byGene"
CBIO = "https://www.cbioportal.org/api"
CIVIC = "https://civicdb.org/api/graphql"


def _req(url, body=None, accept="application/json", tries=3, raw=False):
    data, hdrs = None, {"User-Agent": UA, "Accept": accept}
    if body is not None:
        data = json.dumps(body).encode()
        hdrs["Content-Type"] = "application/json"
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=hdrs),
                                        timeout=180) as r:
                payload = r.read()
                return payload if raw else json.loads(payload)
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            raise SystemExit(f"HTTP {exc.code} from {url.split('?')[0]}: {exc.read()[:200]!r}")
        except urllib.error.URLError as exc:
            if attempt < tries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            raise SystemExit(f"Cannot reach {url.split('?')[0]}: {exc.reason}")
    return None


# ------------------------------------------------------------------ signatures
def signature_files() -> list[dict]:
    """[{name, genome, url}] for every reference matrix on the downloads page."""
    page = _req(SIG_PAGE, accept="text/html", raw=True).decode("utf-8", "replace")
    page = page.encode().decode("unicode_escape", "ignore") if "\\u0022" in page else page
    out = []
    for m in re.finditer(r'"name":\s*"(COSMIC_v[^"]+)",\s*"_id":\s*"([A-Za-z0-9+/=]+)"'
                         r'(?:,\s*"genome":\s*"([^"]*)")?', page):
        name, oid, genome = m.group(1), m.group(2), m.group(3)
        try:
            doc = base64.b64decode(oid + "=" * (-len(oid) % 4)).decode()
        except ValueError:
            continue
        num = re.search(r"Document-(\d+)@", doc)
        if num:
            out.append({"name": name, "genome": genome,
                        "url": f"https://cancer.sanger.ac.uk/signatures/documents/{num.group(1)}/{name}.txt"})
    return out


def _version_key(name: str):
    m = re.match(r"COSMIC_v(\d+)(?:\.(\d+))?", name)
    return (int(m.group(1)), int(m.group(2) or 0)) if m else (0, 0)


# ------------------------------------------------------------------- gene list
def oncokb_genes() -> list[dict]:
    text = _req(ONCOKB_LIST, accept="text/plain", raw=True).decode("utf-8", "replace")
    rows = list(csv.DictReader(io.StringIO(text), delimiter="\t"))
    cgc_col = next((c for c in rows[0] if c.upper().startswith("COSMIC CGC")), None) if rows else None
    out = []
    for r in rows:
        out.append({"gene": r.get("Hugo Symbol"), "entrez": r.get("Entrez Gene ID"),
                    "gene_type": r.get("Gene Type"), "oncokb_annotated": r.get("OncoKB Annotated"),
                    "in_cosmic_cgc": r.get(cgc_col) if cgc_col else None,
                    "cgc_snapshot": cgc_col, "aliases": r.get("Gene Aliases")})
    return out


# -------------------------------------------------------------------- hotspots
def hotspots(gene: str) -> list[dict]:
    rows = _req(HOTSPOTS, body=[gene.upper()])
    out = []
    for h in rows or []:
        tt = h.get("tumorTypeComposition") or {}
        out.append({"gene": h.get("hugoSymbol"), "residue": h.get("residue"), "type": h.get("type"),
                    "tumor_count": h.get("tumorCount"), "q_value": h.get("qValue"),
                    "variant_amino_acids": h.get("variantAminoAcid"),
                    "top_tumor_types": dict(sorted(tt.items(), key=lambda kv: -kv[1])[:6])})
    return sorted(out, key=lambda x: -(x["tumor_count"] or 0))


# ------------------------------------------------------------------- cBioPortal
def _pancan_studies() -> list[dict]:
    studies = _req(f"{CBIO}/studies?projection=DETAILED&pageSize=10000")
    return [s for s in studies if s["studyId"].endswith("_tcga_pan_can_atlas_2018")]


def gene_mutations(gene: str, studies: str = "pancan", top: int = 20) -> dict:
    g = _req(f"{CBIO}/genes/{urllib.parse.quote(gene.upper())}")
    if studies == "pancan":
        meta = _pancan_studies()
    else:
        ids = ["msk_impact_2017"] if studies == "msk" else [s.strip() for s in studies.split(",")]
        meta = [_req(f"{CBIO}/studies/{s}") for s in ids]
    profiles = [f"{s['studyId']}_mutations" for s in meta]
    muts = _req(f"{CBIO}/mutations/fetch?projection=SUMMARY&pageSize=10000000",
                body={"entrezGeneIds": [g["entrezGeneId"]], "molecularProfileIds": profiles})
    denom = sum(s.get("sequencedSampleCount") or 0 for s in meta)
    by_change: dict[str, set] = defaultdict(set)
    types, per_study = Counter(), defaultdict(set)
    mutated = set()
    for m in muts:
        key = m["uniqueSampleKey"]
        mutated.add(key)
        by_change[m.get("proteinChange") or "?"].add(key)
        types[m.get("mutationType") or "?"] += 1
        per_study[m["studyId"]].add(key)
    top_changes = sorted(by_change.items(), key=lambda kv: -len(kv[1]))[:top]
    return {
        "gene": g["hugoGeneSymbol"], "entrez": g["entrezGeneId"],
        "studies": len(meta), "sequenced_samples": denom,
        "mutated_samples": len(mutated),
        "mutated_fraction": round(len(mutated) / denom, 4) if denom else None,
        "mutations": len(muts),
        "top_protein_changes": [{"protein_change": k, "samples": len(v)} for k, v in top_changes],
        "mutation_types": dict(types.most_common()),
        "by_study": {s: len(v) for s, v in sorted(per_study.items(), key=lambda kv: -len(kv[1]))},
        "source": "cBioPortal public API (somatic calls of the listed studies; not COSMIC counts)",
    }


# ------------------------------------------------------------------------ CIViC
def resistance(gene: str | None = None, profile: str | None = None, first: int = 100) -> list[dict]:
    """Accepted CIViC predictive evidence with significance RESISTANCE.

    CIViC's molecularProfileName filter is a substring match, so a gene symbol returns
    every profile that contains it; gene mode keeps profiles that start with the gene.
    """
    q = ("query($name: String, $first: Int) { evidenceItems(evidenceType: PREDICTIVE, "
         "significance: RESISTANCE, status: ACCEPTED, molecularProfileName: $name, first: $first) "
         "{ totalCount nodes { id name evidenceLevel evidenceDirection evidenceRating "
         "molecularProfile { name } therapies { name } disease { name } "
         "source { citation sourceType citationId } } } }")
    d = _req(CIVIC, body={"query": q, "variables": {"name": profile or gene, "first": first}})
    if d.get("errors"):
        raise SystemExit(f"CIViC query error: {d['errors'][0].get('message')}")
    items = d["data"]["evidenceItems"]["nodes"]
    out = []
    for it in items:
        mp = (it.get("molecularProfile") or {}).get("name", "")
        if gene and not mp.upper().startswith(gene.upper()):
            continue
        src = it.get("source") or {}
        out.append({"evidence": it["name"], "molecular_profile": mp,
                    "therapies": [t["name"] for t in it.get("therapies") or []],
                    "disease": (it.get("disease") or {}).get("name"),
                    "level": it.get("evidenceLevel"), "direction": it.get("evidenceDirection"),
                    "rating": it.get("evidenceRating"),
                    "source": f"{src.get('sourceType', '')} {src.get('citationId', '')}".strip(),
                    "url": f"https://civicdb.org/evidence/{it['id']}"})
    return out


def _emit(rows, as_csv=False):
    if as_csv and isinstance(rows, list):
        cols = list(dict.fromkeys(k for r in rows for k in r))
        w = csv.DictWriter(sys.stdout, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in r.items()})
    else:
        print(json.dumps(rows, indent=2, ensure_ascii=False))


def main() -> int:
    ap = argparse.ArgumentParser(description="Keyless somatic-cancer data (no COSMIC login).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ps = sub.add_parser("signatures", help="COSMIC reference signature matrices (no login)")
    ps.add_argument("--type", default="SBS", help="SBS, DBS, ID, CN, SV or RNA")
    ps.add_argument("--genome", default="GRCh38", help="GRCh37, GRCh38, mm9, mm10, mm39, rn6, rn7")
    ps.add_argument("--version", help="e.g. v3.4 (default: newest listed)")
    ps.add_argument("--list", action="store_true", help="list every matrix with its URL")
    ps.add_argument("-o", "--output", help="save the matrix here (default: print the URL)")
    pg = sub.add_parser("genes", help="OncoKB cancer gene list with COSMIC CGC membership")
    pg.add_argument("--gene", action="append", default=[])
    pg.add_argument("--cgc-only", action="store_true", help="only genes flagged as in the COSMIC CGC")
    pg.add_argument("--csv", action="store_true")
    ph = sub.add_parser("hotspots", help="Cancer Hotspots recurrent residues for a gene")
    ph.add_argument("gene")
    pm = sub.add_parser("mutations", help="cBioPortal somatic mutations of a gene across cohorts")
    pm.add_argument("gene")
    pm.add_argument("--studies", default="pancan", help="pancan (32 TCGA PanCancer Atlas), msk, or ids")
    pm.add_argument("--top", type=int, default=20)
    pr = sub.add_parser("resistance", help="CIViC resistance evidence")
    g = pr.add_mutually_exclusive_group(required=True)
    g.add_argument("--gene")
    g.add_argument("--profile", help='molecular profile, e.g. "EGFR T790M"')
    pr.add_argument("--first", type=int, default=100)
    pr.add_argument("--csv", action="store_true")
    a = ap.parse_args()

    if a.cmd == "signatures":
        files = signature_files()
        if a.list:
            _emit(files)
            return 0
        want = [f for f in files if f"_{a.type.upper()}" in f["name"] and
                (a.type.upper() == "RNA" or f["name"].endswith(a.genome))]
        if a.version:
            want = [f for f in want if f["name"].startswith(f"COSMIC_{a.version}_")]
        if not want:
            raise SystemExit(f"No {a.type} matrix for {a.genome} {a.version or ''}; try --list")
        best = max(want, key=lambda f: _version_key(f["name"]))
        if a.output:
            data = _req(best["url"], accept="text/plain", raw=True)
            with open(a.output, "wb") as fh:
                fh.write(data)
            print(f"saved {best['name']} ({len(data)} bytes) -> {a.output}", file=sys.stderr)
        _emit(best)
    elif a.cmd == "genes":
        rows = oncokb_genes()
        if a.gene:
            want = {x.upper() for x in a.gene}
            rows = [r for r in rows if (r["gene"] or "").upper() in want]
        if a.cgc_only:
            rows = [r for r in rows if (r["in_cosmic_cgc"] or "").strip().lower() == "yes"]
        print(f"OncoKB Cancer Gene List: {len(rows)} gene(s); CGC column = "
              f"{rows[0]['cgc_snapshot'] if rows else 'n/a'} (a snapshot, not the current CGC)",
              file=sys.stderr)
        _emit(rows, a.csv)
    elif a.cmd == "hotspots":
        _emit(hotspots(a.gene))
    elif a.cmd == "mutations":
        _emit(gene_mutations(a.gene, a.studies, a.top))
    else:
        _emit(resistance(a.gene, a.profile, a.first), a.csv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
