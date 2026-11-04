#!/usr/bin/env python3
"""score_hypotheses.py — deterministic scorer for the keyless HypoGeniC loop.

The keyless HypoGeniC loop (no package, no LLM API key) works like this:

  1. Claude reads a *labelled* training split and proposes candidate hypotheses, each
     expressed as a checkable keyword rule: "texts containing any of {furthermore, moreover,
     ...} are AI-generated".
  2. THIS script applies those rules to a *held-out* split and reports each hypothesis's
     accuracy, plus the accuracy of the whole bank applied as a first-match classifier.
     Nothing here calls an LLM — the scoring is pure stdlib and fully reproducible.
  3. Claude reads the scores, drops/edits weak hypotheses, adds new ones aimed at the
     misclassified examples, and re-scores. Repeat until the held-out accuracy plateaus.
  4. Report the final hypothesis bank and its held-out accuracy.

Data file: JSON lines or CSV with a text field, a label field, and a split field
(default column names: text, label, split). Hypotheses file: JSON of the shape

  {
    "default_label": "human",
    "hypotheses": [
      {"id": "h1", "description": "...", "keywords": ["furthermore", "moreover"],
       "label": "AI", "match": "substring"}
    ]
  }

match is "substring" (default, case-insensitive) or "word" (whole-word, case-insensitive).

Usage:
  python score_hypotheses.py --data data.jsonl --hypotheses hyps.json --split test
  python score_hypotheses.py --emit-template            # print a hypotheses skeleton
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path


def load_rows(path: str, text_field: str, label_field: str, split_field: str) -> list[dict]:
    p = Path(path)
    raw = p.read_text(encoding="utf-8")
    rows: list[dict] = []
    if p.suffix.lower() in (".jsonl", ".ndjson"):
        for line in raw.splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    elif p.suffix.lower() == ".json":
        data = json.loads(raw)
        rows = data if isinstance(data, list) else data.get("data", [])
    else:  # csv / tsv
        delim = "\t" if p.suffix.lower() == ".tsv" else ","
        rows = list(csv.DictReader(raw.splitlines(), delimiter=delim))
    out = []
    for r in rows:
        if text_field not in r or label_field not in r:
            raise SystemExit(f"error: row missing '{text_field}'/'{label_field}': {r}")
        out.append({"text": str(r[text_field]), "label": str(r[label_field]).strip(),
                    "split": str(r.get(split_field, "")).strip()})
    return out


def _matches(text: str, keywords: list[str], mode: str) -> bool:
    low = text.lower()
    for kw in keywords:
        k = kw.lower().strip()
        if not k:
            continue
        if mode == "word":
            if re.search(r"\b" + re.escape(k) + r"\b", low):
                return True
        elif k in low:
            return True
    return False


def predict_single(rows: list[dict], hyp: dict, default_label: str) -> list[str]:
    mode = hyp.get("match", "substring")
    return [hyp["label"] if _matches(r["text"], hyp.get("keywords", []), mode)
            else default_label for r in rows]


def predict_bank(rows: list[dict], hyps: list[dict], default_label: str) -> list[str]:
    preds = []
    for r in rows:
        chosen = default_label
        for hyp in hyps:  # first-match wins (ordered bank)
            if _matches(r["text"], hyp.get("keywords", []), hyp.get("match", "substring")):
                chosen = hyp["label"]
                break
        preds.append(chosen)
    return preds


def accuracy(preds: list[str], gold: list[str]) -> float:
    if not gold:
        return 0.0
    return sum(p == g for p, g in zip(preds, gold)) / len(gold)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", help="labelled dataset (.jsonl/.json/.csv/.tsv)")
    ap.add_argument("--hypotheses", help="hypotheses JSON (see --emit-template)")
    ap.add_argument("--split", default="test", help="which split to score (default: test)")
    ap.add_argument("--text-field", default="text")
    ap.add_argument("--label-field", default="label")
    ap.add_argument("--split-field", default="split")
    ap.add_argument("--emit-template", action="store_true",
                    help="print a hypotheses JSON skeleton and exit")
    args = ap.parse_args()

    if args.emit_template:
        print(json.dumps({
            "default_label": "human",
            "hypotheses": [
                {"id": "h1", "description": "Formal discourse connectors signal AI text.",
                 "keywords": ["furthermore", "moreover", "additionally", "consequently"],
                 "label": "AI", "match": "word"},
            ],
        }, indent=2))
        return 0

    if not args.data or not args.hypotheses:
        ap.error("--data and --hypotheses are required (or use --emit-template)")

    rows = load_rows(args.data, args.text_field, args.label_field, args.split_field)
    if any(r["split"] for r in rows):
        rows = [r for r in rows if r["split"] == args.split]
    if not rows:
        raise SystemExit(f"error: no rows in split '{args.split}'")
    gold = [r["label"] for r in rows]

    spec = json.loads(Path(args.hypotheses).read_text(encoding="utf-8"))
    default_label = spec.get("default_label", "")
    hyps = spec.get("hypotheses", [])
    if not hyps:
        raise SystemExit("error: no hypotheses in the spec")

    print(f"Scoring {len(hyps)} hypothesis/es on split '{args.split}' ({len(rows)} examples)\n")
    print(f"{'id':<8} {'acc':>6}  description")
    print("-" * 64)
    best = None
    for hyp in hyps:
        acc = accuracy(predict_single(rows, hyp, default_label), gold)
        print(f"{hyp.get('id','?'):<8} {acc:>6.3f}  {hyp.get('description','')[:46]}")
        if best is None or acc > best[1]:
            best = (hyp.get("id", "?"), acc)

    bank_preds = predict_bank(rows, hyps, default_label)
    bank_acc = accuracy(bank_preds, gold)
    print("-" * 64)
    print(f"best single hypothesis: {best[0]} (accuracy {best[1]:.3f})")
    print(f"bank (first-match) accuracy: {bank_acc:.3f}")

    mis = [r["text"] for r, p in zip(rows, bank_preds) if p != r["label"]]
    if mis:
        print(f"\n{len(mis)} misclassified by the bank — refine hypotheses to target these:")
        for t in mis[:10]:
            print(f"  - {t[:70]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
