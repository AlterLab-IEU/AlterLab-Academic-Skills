#!/usr/bin/env python3
"""McDonald's omega (and coefficient H) from standardized factor loadings — stdlib only.

Neither semopy nor pingouin returns omega, so this computes it directly from the standardized
loadings a CFA/EFA gives you. For a unidimensional (congeneric) factor with standardized loadings
lambda_i and standardized error variances (1 - lambda_i**2):

    omega_total = (sum lambda_i)**2 / [ (sum lambda_i)**2 + sum (1 - lambda_i**2) ]

Also reports coefficient H (construct reliability / maximal reliability):

    H = 1 / ( 1 + 1 / sum( lambda_i**2 / (1 - lambda_i**2) ) )

    python omega.py 0.72 0.68 0.81 0.55
    python omega.py --loadings 0.72,0.68,0.81,0.55

Input domain (both functions raise ValueError otherwise; the CLI exits 2 with the reason):
  * at least 2 loadings (a single item has no composite to estimate reliability for);
  * every loading a finite real number with |lambda| <= 1. |lambda| > 1 implies a negative
    error variance (a Heywood case) — fix the CFA before computing reliability.
Defined boundary behaviour: |lambda| = 1 (zero error variance) gives H = 1; all-zero loadings
(no common-factor variance) give omega = H = 0. Negative loadings are accepted — omega is then
the reliability of the unit-weighted sum of the items AS SCORED, so reverse-code items first if
they measure the construct in the opposite direction (the CLI prints a note on stderr).
"""
from __future__ import annotations

import argparse
import math
import numbers
import sys


def _validate(loadings: object) -> list:
    """Check the input domain (see module docstring); return the loadings as a list."""
    if isinstance(loadings, (str, bytes)):
        raise ValueError("loadings must be a sequence of numbers, not a string")
    try:
        lams = list(loadings)
    except TypeError:
        raise ValueError(f"loadings must be a sequence of numbers, got {loadings!r}") from None
    if len(lams) < 2:
        raise ValueError(f"at least 2 standardized loadings are required, got {len(lams)}")
    for i, lam in enumerate(lams, 1):
        if isinstance(lam, bool) or not isinstance(lam, numbers.Real):
            raise ValueError(f"loading {i} must be a real number, got {lam!r}")
        try:
            finite = math.isfinite(lam)
        except OverflowError:  # an int too big for a float is finite; the range check rejects it
            finite = True
        if not finite:
            raise ValueError(f"loading {i} must be finite, got {lam!r}")
        if abs(lam) > 1.0:
            raise ValueError(
                f"loading {i} = {lam!r} is outside [-1, 1]: a standardized loading above 1 in "
                "absolute value implies a negative error variance (Heywood case); fix the CFA "
                "before computing reliability")
    return lams


def omega_total(loadings: list[float]) -> float:
    loadings = _validate(loadings)
    s = sum(loadings)
    err = sum(1.0 - lam * lam for lam in loadings)
    denom = s * s + err
    if denom == 0:
        raise ValueError("degenerate loadings (zero denominator)")
    return (s * s) / denom


def coefficient_h(loadings: list[float]) -> float:
    loadings = _validate(loadings)
    total = 0.0
    for lam in loadings:
        e = 1.0 - lam * lam
        if e <= 0:
            # a loading of |1| means error-free; H -> 1
            return 1.0
        total += (lam * lam) / e
    return 1.0 / (1.0 + 1.0 / total) if total > 0 else 0.0


def _parse(values: list[str]) -> list[float]:
    out = []
    for v in values:
        for part in v.split(","):
            part = part.strip()
            if part:
                try:
                    out.append(float(part))
                except ValueError:
                    raise ValueError(f"not a number: {part!r}") from None
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("loadings", nargs="*", help="standardized loadings, space- or comma-separated")
    ap.add_argument("--loadings", dest="loadings_flag", default=None,
                    help="comma-separated standardized loadings")
    args = ap.parse_args()

    raw = list(args.loadings)
    if args.loadings_flag:
        raw.append(args.loadings_flag)
    try:
        lams = _parse(raw)
        if len(lams) < 2:
            ap.error("provide at least 2 standardized loadings")
        ot = omega_total(lams)
        h = coefficient_h(lams)
    except ValueError as exc:
        ap.error(str(exc))  # usage + message on stderr, exit 2
    negative = sum(1 for x in lams if x < 0)
    if negative:
        print(f"note: {negative} negative loading(s). omega_total is the reliability of the "
              "unit-weighted sum of the items AS SCORED; reverse-code items that measure the "
              "construct in the opposite direction, then re-run.", file=sys.stderr)
    print(f"items:        {len(lams)}")
    print(f"loadings:     {', '.join(f'{x:.3f}' for x in lams)}")
    print(f"omega_total:  {ot:.3f}")
    print(f"coefficient H:{h:.3f}")
    print("Report omega alongside alpha. omega assumes a correct unidimensional CFA — check fit first.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
