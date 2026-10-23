#!/usr/bin/env python3
"""Query the AlphaFold DB public REST API (no API key required). Standard library only.

Endpoints (https://alphafold.ebi.ac.uk/api/):
  - prediction/{uniprot}   -> prediction metadata (modelEntityId, file URLs, sequence)

The prediction metadata carries the exact, version-stamped file URLs
(cifUrl / pdbUrl / bcifUrl / plddtDocUrl / paeDocUrl). This script reads those
URLs from the response rather than hand-building a `_v{N}` suffix, so it keeps
working as the DB version advances (currently v6; old `_v4` file URLs now 404).

The endpoint returns a list that also includes isoform records (e.g. P00520-2)
and possibly third-party models, so the script picks the record whose
uniprotAccession matches the query instead of blindly taking the first one.

The /files/ host answers HTTP 403 to curl's default User-Agent (checked 2026-10-23;
Python, wget and named clients get 200), so every request here sends its own
User-Agent; with curl, pass one too: curl -A "alterlab-alphafold-db/1.2" <url>.

Smoke test:
    python query_alphafold.py prediction P00520
    python query_alphafold.py confidence P04637 --summary     # pLDDT bands + segments
    python query_alphafold.py pae P04637 --summary            # PAE between confident segments
    python query_alphafold.py pae P04637 --domains 94-292,325-356
    python query_alphafold.py download P00520 --fmt cif -o ./structures
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://alphafold.ebi.ac.uk/api"
USER_AGENT = "alterlab-alphafold-db/1.2 (AlterLab Academic Skills)"
RETRY_STATUS = {429, 500, 502, 503, 504}

# Map a coordinate format to the metadata key that holds its URL.
_MODEL_URL_KEY = {"cif": "cifUrl", "pdb": "pdbUrl", "bcif": "bcifUrl"}

# pLDDT bands used by AlphaFold DB (confidenceCategory letters in the JSON).
BANDS = [("very_high", 90.0, "VH"), ("confident", 70.0, "H"), ("low", 50.0, "L"),
         ("very_low", float("-inf"), "D")]


def _get(url: str, timeout: int = 60, retries: int = 4) -> bytes:
    """GET with a User-Agent, a timeout and exponential backoff on 429/5xx."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code not in RETRY_STATUS or attempt == retries:
                raise
            wait = e.headers.get("Retry-After")
            time.sleep(float(wait) if wait and wait.isdigit() else 2 ** attempt)
        except urllib.error.URLError:
            if attempt == retries:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def get_prediction(uniprot: str) -> list:
    """Return AlphaFold prediction metadata records for a UniProt accession."""
    return json.loads(_get(f"{API}/prediction/{uniprot}", timeout=30))


def _first_record(uniprot: str) -> dict:
    """Return the record for exactly this accession (canonical, not an isoform)."""
    preds = get_prediction(uniprot)
    if not preds:
        sys.exit(f"No AlphaFold prediction for {uniprot}")
    for rec in preds:
        if rec.get("uniprotAccession") == uniprot or rec.get("modelEntityId") == uniprot:
            return rec
    return preds[0]


def get_confidence(uniprot: str) -> dict:
    """Fetch the per-residue confidence (pLDDT) JSON for a UniProt accession."""
    return json.loads(_get(_first_record(uniprot)["plddtDocUrl"]))


def get_pae(uniprot: str) -> list:
    """Fetch the PAE matrix (list of rows, Angstrom) for a UniProt accession."""
    doc = json.loads(_get(_first_record(uniprot)["paeDocUrl"], timeout=120))
    doc = doc[0] if isinstance(doc, list) else doc  # single-element array
    return doc["predicted_aligned_error"]


def _band(score: float) -> str:
    return next(name for name, low, _ in BANDS if score > low or low == float("-inf"))


def confidence_summary(conf: dict, min_len: int = 5) -> dict:
    """Mean pLDDT, fraction per band, and contiguous residue segments per band."""
    scores = conf.get("confidenceScore", [])
    resnums = conf.get("residueNumber", list(range(1, len(scores) + 1)))
    if not scores:
        return {"length": 0}
    fractions = {name: 0 for name, _, _ in BANDS}
    segments, start = [], 0
    for i, s in enumerate(scores):
        fractions[_band(s)] += 1
        if i + 1 == len(scores) or _band(scores[i + 1]) != _band(s):
            if i - start + 1 >= min_len:
                seg = scores[start:i + 1]
                segments.append({"start": resnums[start], "end": resnums[i], "band": _band(s),
                                 "mean_plddt": round(sum(seg) / len(seg), 1)})
            start = i + 1
    return {
        "length": len(scores),
        "mean_plddt": round(sum(scores) / len(scores), 2),
        "fraction": {k: round(v / len(scores), 3) for k, v in fractions.items()},
        "bands": "pLDDT >90 very high, 70-90 confident, 50-70 low, <50 very low",
        f"segments_min_{min_len}_residues": segments,
    }


def _confident_domains(conf: dict, min_len: int = 20) -> list:
    """Runs of pLDDT > 70 at least min_len long, as (start, end) residue numbers."""
    scores = conf["confidenceScore"]
    out, start = [], None
    for i, s in enumerate(scores + [0.0]):
        if s > 70 and start is None:
            start = i
        elif s <= 70 and start is not None:
            if i - start >= min_len:
                out.append((start + 1, i))
            start = None
    return out


def pae_summary(pae: list, domains: list) -> dict:
    """Mean PAE within each domain and between every pair (residue numbers 1-based)."""
    def block(a, b):
        vals = [pae[i - 1][j - 1] for i in range(a[0], a[1] + 1) for j in range(b[0], b[1] + 1)]
        return round(sum(vals) / len(vals), 2)

    n = len(pae)
    flat = [v for row in pae for v in row]
    out = {
        "matrix_size": [n, len(pae[0]) if pae else 0],
        "max_pae": max(flat) if flat else None,
        "fraction_pairs_below_5A": round(sum(v < 5 for v in flat) / len(flat), 3) if flat else None,
        "thresholds": "PAE < 5 A: relative placement confident; > 15 A: arrangement uncertain",
        "domains": [f"{a}-{b}" for a, b in domains],
        "within": {f"{a}-{b}": block((a, b), (a, b)) for a, b in domains},
        "between": {},
    }
    for i, d1 in enumerate(domains):
        for d2 in domains[i + 1:]:
            m = round((block(d1, d2) + block(d2, d1)) / 2, 2)
            verdict = "confident" if m < 5 else ("uncertain" if m > 15 else "intermediate")
            out["between"][f"{d1[0]}-{d1[1]} vs {d2[0]}-{d2[1]}"] = {"mean_pae": m,
                                                                      "placement": verdict}
    return out


def download(uniprot: str, fmt: str, outdir: str) -> str:
    """Download a structure file (cif/pdb/bcif) and return the saved path."""
    url = _first_record(uniprot)[_MODEL_URL_KEY[fmt]]
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, url.rsplit("/", 1)[-1])
    with open(path, "wb") as fh:
        fh.write(_get(url, timeout=120))
    return path


def _parse_domains(text: str) -> list:
    out = []
    for part in text.split(","):
        a, b = part.split("-")
        out.append((int(a), int(b)))
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Query AlphaFold DB (no key required).")
    p.add_argument("action", choices=["prediction", "confidence", "pae", "download"])
    p.add_argument("uniprot", help="UniProt accession, e.g. P00520")
    p.add_argument("--fmt", default="cif", choices=["cif", "pdb", "bcif"])
    p.add_argument("-o", "--outdir", default="./structures")
    p.add_argument("--summary", action="store_true",
                   help="confidence: bands + segments; pae: domain-pair means (not raw JSON)")
    p.add_argument("--domains", default=None,
                   help="pae: residue ranges, e.g. 94-292,325-356 (default: runs of pLDDT>70, "
                        ">=20 residues)")
    args = p.parse_args()

    try:
        if args.action == "prediction":
            print(json.dumps(get_prediction(args.uniprot), indent=2))
        elif args.action == "confidence":
            conf = get_confidence(args.uniprot)
            print(json.dumps(confidence_summary(conf) if args.summary else conf, indent=2))
        elif args.action == "pae":
            pae = get_pae(args.uniprot)
            if args.summary or args.domains:
                doms = (_parse_domains(args.domains) if args.domains
                        else _confident_domains(get_confidence(args.uniprot)))
                print(json.dumps(pae_summary(pae, doms), indent=2))
            else:
                print(json.dumps(pae))
        else:
            print(download(args.uniprot, args.fmt, args.outdir))
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} from {e.url}")
    except urllib.error.URLError as e:
        sys.exit(f"network error: {e.reason}")


if __name__ == "__main__":
    main()
