#!/usr/bin/env python3
"""Check a DNA FASTA against the Ginkgo Cloud Lab cell-free expression constraints — offline.

Ginkgo Cloud Lab orders go through the web interface (there is no public ordering API), so
there is nothing to submit from code. What *can* be done with no account is make the inputs
correct first: the Cell Free Protein Expression Validation protocol takes linear DNA up to
1800 bp (per the protocol page, confirm current limits there before relying on them). This
reads a FASTA and reports, per record, length, whether it is within the 1800 bp limit, any
non-ACGT/IUPAC characters, and an estimated sample count and cost so the order is ready.

  python3 check_cfps_input.py constructs.fasta [--price-per-sample 39] [--replicates 1]

Exit 0 when every record passes, 1 when any record has a problem, 2 on a bad path.
Prices/limits as listed on cloud.ginkgo.bio 2026-09-23; confirm on the protocol page.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

MAX_BP = 1800
IUPAC = set("ACGTRYSWKMBDHVN")


def read_fasta(path: Path) -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    name, seq = None, []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(">"):
            if name is not None:
                records.append((name, "".join(seq)))
            name, seq = line[1:].strip().split()[0] if line[1:].strip() else "(unnamed)", []
        elif line.strip():
            seq.append(line.strip())
    if name is not None:
        records.append((name, "".join(seq)))
    return records


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("fasta", type=Path)
    ap.add_argument("--price-per-sample", type=float, default=39.0,
                    help="USD per sample as listed on the protocol page (default 39)")
    ap.add_argument("--replicates", type=int, default=1)
    args = ap.parse_args()
    if not args.fasta.is_file():
        print(f"error: {args.fasta} not found", file=sys.stderr)
        return 2
    records = read_fasta(args.fasta)
    if not records:
        print("error: no FASTA records found", file=sys.stderr)
        return 2
    problems = 0
    for name, seq in records:
        bases = seq.upper()
        issues = []
        if len(bases) > MAX_BP:
            issues.append(f"{len(bases)} bp exceeds the {MAX_BP} bp limit")
        bad = sorted(set(bases) - IUPAC)
        if bad:
            issues.append(f"non-DNA characters {bad}")
        if not bases:
            issues.append("empty sequence")
        status = "OK" if not issues else "PROBLEM: " + "; ".join(issues)
        problems += bool(issues)
        print(f"{name}: {len(bases)} bp — {status}")
    n_samples = len(records) * args.replicates
    print(f"\n{len(records)} construct(s) x {args.replicates} replicate(s) = {n_samples} sample(s); "
          f"estimated ${n_samples * args.price_per_sample:.0f} at ${args.price_per_sample:.0f}/sample "
          "(confirm on the protocol page). Ordering is through cloud.ginkgo.bio.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
