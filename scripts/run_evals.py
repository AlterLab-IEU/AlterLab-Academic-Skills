#!/usr/bin/env python3
"""Discover and validate per-skill eval files (evals/evals.json).

Anthropic recommends building evaluations for each skill (>=3 trigger cases). Full
*behavioral* execution requires the `claude` CLI to actually run each query against the
skill — that is environment-specific and slow, so it is not run in CI. This script does
the CI-safe part: discover every skills/**/evals/evals.json, validate its shape, and
confirm the coverage bar (>=3 should_trigger and >=1 should_not_trigger case per skill).

    python3 scripts/run_evals.py            # validate all eval files, list coverage
    python3 scripts/run_evals.py --strict   # exit non-zero if any eval file is malformed
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"


def validate(path: Path) -> list[str]:
    errs: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"invalid JSON: {e}"]
    evals = data.get("evals")
    if not isinstance(evals, list) or not evals:
        return ["missing or empty 'evals' array"]
    pos = sum(1 for e in evals if e.get("should_trigger") is True)
    neg = sum(1 for e in evals if e.get("should_trigger") is False)
    for i, e in enumerate(evals):
        for key in ("id", "query", "expected_behavior", "should_trigger"):
            if key not in e:
                errs.append(f"eval[{i}] missing '{key}'")
    if pos < 3:
        errs.append(f"only {pos} should_trigger cases (>=3 recommended)")
    if neg < 1:
        errs.append("no should_not_trigger (near-miss) case")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="exit non-zero on any malformed eval file")
    args = ap.parse_args()

    files = sorted(SKILLS.glob("*/*/evals/evals.json"))
    if not files:
        print("No eval files found (skills/**/evals/evals.json).")
        return 0

    bad = 0
    for f in files:
        skill = f.parent.parent.name
        errs = validate(f)
        if errs:
            bad += 1
            print(f"✗ {skill}: {'; '.join(errs)}")
        else:
            print(f"✓ {skill}")
    print(f"\n{len(files)} eval file(s), {bad} with issues.")
    print("Note: behavioral execution (running each query through the skill) requires the "
          "`claude` CLI and is not performed here.")
    return 1 if (bad and args.strict) else 0


if __name__ == "__main__":
    raise SystemExit(main())
