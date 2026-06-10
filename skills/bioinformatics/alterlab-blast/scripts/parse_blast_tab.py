#!/usr/bin/env python3
"""Parse and QC BLAST+/DIAMOND tabular (`-outfmt 6` / `--outfmt 6`) output.

Self-contained: Python standard library only (no requests/pandas needed), so it
runs in a bare `uv run python` environment. Reads a BLAST+ or DIAMOND tabular
file (or `-` for stdin), applies identity / coverage / e-value filters, and can
extract the true best hit *per query* by sorting on bitscore.

Why this exists: `-max_target_seqs` is a heuristic keep-count, NOT a top-N
best-hits filter (ties are broken by database order, not score). So the only
reliable way to get the best hit is to sort the tabular output by bitscore here,
after the search. This script does that and warns when the column layout looks
inconsistent with the declared schema.

Default schema is the BLAST+/DIAMOND `std` 12 columns:
    qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore
Override with --columns if you searched with a custom -outfmt spec.

Usage:
    parse_blast_tab.py hits.tsv --best-hit
    parse_blast_tab.py hits.tsv --min-identity 90 --min-qcov 80 --max-evalue 1e-10
    parse_blast_tab.py hits.tsv --columns 'qseqid sseqid pident length evalue bitscore qcovs' --best-hit
    blastp ... -outfmt 6 | parse_blast_tab.py - --best-hit --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field

STD_COLUMNS = (
    "qseqid sseqid pident length mismatch gapopen "
    "qstart qend sstart send evalue bitscore"
).split()

# Columns we know how to coerce to numbers for filtering / sorting.
NUMERIC = {
    "pident", "length", "mismatch", "gapopen", "qstart", "qend",
    "sstart", "send", "evalue", "bitscore", "qcovs", "qcovhsp",
    "qlen", "slen", "score", "nident", "positive", "gaps",
}


@dataclass
class Result:
    columns: list[str]
    rows: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    n_input: int = 0
    n_kept: int = 0


def _coerce(col: str, value: str):
    if col not in NUMERIC:
        return value
    try:
        return float(value)
    except ValueError:
        return None


def parse(handle, columns: list[str]) -> Result:
    res = Result(columns=columns)
    ncol = len(columns)
    for raw in handle:
        line = raw.rstrip("\n")
        if not line or line.startswith("#"):  # outfmt 7 comment lines
            continue
        fields = line.split("\t")
        res.n_input += 1
        if len(fields) != ncol:
            res.warnings.append(
                f"row {res.n_input}: expected {ncol} columns, got {len(fields)} "
                f"-- check your --columns matches the search -outfmt spec"
            )
            # Still record what we can, padding/truncating defensively.
            fields = (fields + [""] * ncol)[:ncol]
        row = {col: _coerce(col, val) for col, val in zip(columns, fields)}
        res.rows.append(row)
    return res


def _pass_filters(row, args) -> bool:
    if args.min_identity is not None:
        v = row.get("pident")
        if not isinstance(v, float) or v < args.min_identity:
            return False
    if args.min_qcov is not None:
        # accept either qcovs or qcovhsp, whichever was requested
        v = row.get("qcovs", row.get("qcovhsp"))
        if not isinstance(v, float) or v < args.min_qcov:
            return False
    if args.max_evalue is not None:
        v = row.get("evalue")
        if not isinstance(v, float) or v > args.max_evalue:
            return False
    return True


def best_hit_per_query(rows: list[dict]) -> list[dict]:
    """One row per qseqid, the highest bitscore (e-value tiebreak). This is the
    correct way to get 'the best hit' -- do NOT rely on -max_target_seqs 1."""
    best: dict[str, dict] = {}
    for row in rows:
        q = row.get("qseqid")
        if q is None:
            continue
        bs = row.get("bitscore")
        ev = row.get("evalue")
        cur = best.get(q)
        if cur is None:
            best[q] = row
            continue
        cur_bs = cur.get("bitscore")
        better = isinstance(bs, float) and (
            not isinstance(cur_bs, float)
            or bs > cur_bs
            or (bs == cur_bs and isinstance(ev, float)
                and isinstance(cur.get("evalue"), float) and ev < cur["evalue"])
        )
        if better:
            best[q] = row
    return list(best.values())


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("path", help="tabular BLAST+/DIAMOND file, or '-' for stdin")
    p.add_argument("--columns", default=" ".join(STD_COLUMNS),
                   help="space-separated -outfmt column names (default: std 12)")
    p.add_argument("--best-hit", action="store_true",
                   help="keep only the top-bitscore hit per query (correct best-hit selection)")
    p.add_argument("--min-identity", type=float, metavar="PCT",
                   help="drop hits below this percent identity (pident)")
    p.add_argument("--min-qcov", type=float, metavar="PCT",
                   help="drop hits below this query coverage (needs qcovs/qcovhsp column)")
    p.add_argument("--max-evalue", type=float, metavar="E",
                   help="drop hits with e-value above this threshold")
    p.add_argument("--json", action="store_true", help="emit JSON instead of TSV")
    args = p.parse_args(argv)

    columns = args.columns.split()

    handle = sys.stdin if args.path == "-" else open(args.path, "r", encoding="utf-8")
    try:
        res = parse(handle, columns)
    finally:
        if handle is not sys.stdin:
            handle.close()

    rows = [r for r in res.rows if _pass_filters(r, args)]
    if args.best_hit:
        rows = best_hit_per_query(rows)
        rows.sort(key=lambda r: (-(r.get("bitscore") or 0.0), str(r.get("qseqid"))))
    res.n_kept = len(rows)

    for w in res.warnings:
        print(f"WARNING: {w}", file=sys.stderr)
    print(
        f"# parsed {res.n_input} hit(s); kept {res.n_kept} after filters"
        + (" (best-hit-per-query)" if args.best_hit else ""),
        file=sys.stderr,
    )

    if args.json:
        json.dump(
            {"columns": columns, "n_input": res.n_input, "n_kept": res.n_kept,
             "warnings": res.warnings, "rows": rows},
            sys.stdout, indent=2, default=str,
        )
        sys.stdout.write("\n")
    else:
        sys.stdout.write("\t".join(columns) + "\n")
        for r in rows:
            sys.stdout.write("\t".join(str(r.get(c, "")) for c in columns) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
