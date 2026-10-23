#!/usr/bin/env bash
# eval_sweep.sh — run `run_evals.py --behavioral` over many skills, N at a time.
#
#   scripts/eval_sweep.sh LIST PARALLEL OUTDIR [extra run_evals.py args ...]
#
# LIST is a file with one skill directory per line (e.g. skills/data-science/alterlab-eda),
# optionally followed by arguments for that skill only (e.g. `--case some-id --case other-id`).
# Each skill gets one results JSON in OUTDIR and a log in OUTDIR/logs/<skill>.log;
# OUTDIR/logs/_done.txt gets "<skill> exit=<code>" per skill and ALL_DONE at the end.
# Extra arguments go to every run (default: --runs 1 --timeout 400 --wait-on-limit).
#
# Several sweeps may share one OUTDIR: each skill is claimed with an atomic lock directory, so
# a second sweep started later (e.g. with more workers) skips skills already run or running.
# EVAL_ROOT overrides which checkout's skills and harness are used (default: this one).
#
# Run it from a disposable checkout, not your working copy: answer arms are confined (see
# docs/evals.md, "A temporary directory is not a sandbox"), but only on Linux.
set -u
LIST="$1"; PAR="$2"; OUT="$3"; shift 3
EXTRA=("$@"); [ ${#EXTRA[@]} -eq 0 ] && EXTRA=(--runs 1 --timeout 400 --wait-on-limit)
ROOT="${EVAL_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
OUT="$(mkdir -p "$OUT" && cd "$OUT" && pwd)"; LOGS="$OUT/logs"; mkdir -p "$LOGS"
cd "$ROOT"
run_one() {
  read -r -a words <<< "$1"; d="${words[0]}"; name=$(basename "$d")
  key=$(printf '%s' "$d" | tr -c 'A-Za-z0-9._-' '_')
  mkdir "$LOGS/.claim-$key" 2>/dev/null || return 0   # another sweep has it
  uv run --no-sync python scripts/run_evals.py --behavioral --skill-dir "$d" \
     --results-dir "$OUT" "${EXTRA[@]}" "${words[@]:1}" > "$LOGS/$name.log" 2>&1
  echo "$name exit=$?" >> "$LOGS/_done.txt"
}
export -f run_one; export OUT LOGS; export EXTRA_STR="${EXTRA[*]}"
grep -v '^\s*\(#\|$\)' "$LIST" | xargs -P "$PAR" -I{} bash -c 'EXTRA=($EXTRA_STR); run_one "$@"' _ {}
echo ALL_DONE >> "$LOGS/_done.txt"
