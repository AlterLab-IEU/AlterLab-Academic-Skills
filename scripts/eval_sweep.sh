#!/usr/bin/env bash
# eval_sweep.sh — run `run_evals.py --behavioral` over many skills, N at a time.
#
#   scripts/eval_sweep.sh LIST PARALLEL OUTDIR [extra run_evals.py args ...]
#
# LIST is a file with one skill directory per line (e.g. skills/data-science/alterlab-eda).
# Each skill gets one results JSON in OUTDIR and a log in OUTDIR/logs/<skill>.log;
# OUTDIR/logs/_done.txt gets "<skill> exit=<code>" per skill and ALL_DONE at the end.
# Extra arguments go to every run (default: --runs 1 --timeout 400 --wait-on-limit).
#
# Run it from a disposable checkout, not your working copy: answer arms are confined (see
# docs/evals.md, "A temporary directory is not a sandbox"), but only on Linux.
set -u
LIST="$1"; PAR="$2"; OUT="$3"; shift 3
EXTRA=("$@"); [ ${#EXTRA[@]} -eq 0 ] && EXTRA=(--runs 1 --timeout 400 --wait-on-limit)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$(mkdir -p "$OUT" && cd "$OUT" && pwd)"; LOGS="$OUT/logs"; mkdir -p "$LOGS"
cd "$ROOT"
run_one() {
  d="$1"; name=$(basename "$d")
  uv run --no-sync python scripts/run_evals.py --behavioral --skill-dir "$d" \
     --results-dir "$OUT" "${EXTRA[@]}" > "$LOGS/$name.log" 2>&1
  echo "$name exit=$?" >> "$LOGS/_done.txt"
}
export -f run_one; export OUT LOGS; export EXTRA_STR="${EXTRA[*]}"
grep -v '^\s*\(#\|$\)' "$LIST" | xargs -P "$PAR" -I{} bash -c 'EXTRA=($EXTRA_STR); run_one "$@"' _ {}
echo ALL_DONE >> "$LOGS/_done.txt"
