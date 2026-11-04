#!/usr/bin/env python3
"""Validate an Adaptyv Foundry experiment submission offline — no API key, no network.

The Foundry rejects a malformed POST /experiments with a 400 that lists every problem,
and every rejection costs a round trip (and a quote only forms once the spec is valid).
This checks the same contract locally from the OpenAPI spec (v0.0.2, read 2026-10-22),
so a submission is clean before it ever reaches the API — and before the user spends on
an experiment that runs for weeks.

Input: a JSON file holding either an ``experiment_spec`` object or a full create request
(``{"name": ..., "experiment_spec": {...}}``). Rules enforced (per-type matrix):

  * experiment_type in affinity|screening|thermostability|fluorescence|expression|
    epitope_binning|enzyme_activity
  * method (bli|spr) required for affinity & screening, rejected for the rest
  * target_id required for affinity, screening & epitope_binning, rejected for the rest
  * sequences: >=1; for epitope_binning a multiple of 4 in the range 4..28
  * n_replicates rejected for epitope_binning
  * each sequence is a valid amino-acid string: only A C D E F G H I K L M N P Q R S T V
    W Y (case-insensitive) and ':' for multichain constructs; non-empty

  python3 validate_submission.py spec.json      # exit 0 clean, 1 problems, 2 bad input
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TYPES = {"affinity", "screening", "thermostability", "fluorescence",
         "expression", "epitope_binning", "enzyme_activity"}
NEEDS_METHOD = {"affinity", "screening"}
NEEDS_TARGET = {"affinity", "screening", "epitope_binning"}
AA_RE = re.compile(r"^[ACDEFGHIKLMNPQRSTVWY:]+$", re.IGNORECASE)


def _aa_string(value) -> str | None:
    """Return the amino-acid string from a SequenceValue (str or {aa_string: ...})."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("aa_string")
    return None


def validate(spec: dict) -> list[str]:
    problems: list[str] = []
    et = spec.get("experiment_type")
    if et not in TYPES:
        problems.append(f"experiment_type {et!r} is not one of {sorted(TYPES)}")
    method = spec.get("method")
    if et in NEEDS_METHOD and method not in ("bli", "spr"):
        problems.append(f"method is required for {et} and must be 'bli' or 'spr' (got {method!r})")
    if et not in NEEDS_METHOD and method is not None:
        problems.append(f"method must not be set for {et} (got {method!r})")
    if et in NEEDS_TARGET and not spec.get("target_id"):
        problems.append(f"target_id (a catalog UUID) is required for {et}")
    if et not in NEEDS_TARGET and spec.get("target_id"):
        problems.append(f"target_id must not be set for {et}")
    seqs = spec.get("sequences")
    if not isinstance(seqs, dict) or not seqs:
        problems.append("sequences must be a non-empty {label: aa_string} map")
        seqs = {}
    if et == "epitope_binning":
        n = len(seqs)
        if not (4 <= n <= 28 and n % 4 == 0):
            problems.append(f"epitope_binning needs 4..28 sequences in multiples of 4 (got {n})")
        if spec.get("n_replicates") is not None:
            problems.append("n_replicates must not be set for epitope_binning")
    for label, value in seqs.items():
        aa = _aa_string(value)
        if not aa:
            problems.append(f"sequence {label!r}: missing amino-acid string")
        elif not AA_RE.match(aa):
            bad = sorted(set(c for c in aa.upper() if c not in "ACDEFGHIKLMNPQRSTVWY:"))
            problems.append(f"sequence {label!r}: invalid characters {bad} "
                            "(only the 20 amino acids and ':' for multichain are allowed)")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("spec_json", type=Path, help="JSON with experiment_spec or a full create request")
    args = ap.parse_args()
    try:
        data = json.loads(args.spec_json.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"error: {args.spec_json} not found", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON ({exc})", file=sys.stderr)
        return 2
    spec = data.get("experiment_spec", data) if isinstance(data, dict) else {}
    problems = validate(spec)
    for p in problems:
        print(f"PROBLEM: {p}")
    print(f"{len(problems)} problem(s); experiment_type={spec.get('experiment_type')!r}, "
          f"{len(spec.get('sequences') or {})} sequence(s) "
          "(offline check; the Foundry re-validates on submit)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
