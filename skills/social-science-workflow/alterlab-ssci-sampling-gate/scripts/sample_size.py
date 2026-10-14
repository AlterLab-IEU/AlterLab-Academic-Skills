#!/usr/bin/env python3
"""A-priori sample-size calculator (stdlib only, normal approximation).

Enforces the discipline the sampling gate cares about: you must state an effect size (or a
precision target) BEFORE collecting, and the number falls out of it. It does NOT run your
analysis and it does NOT compute post-hoc power (which carries no information).

    # two-group mean comparison, Cohen's d = 0.5, 80% power, alpha 0.05
    python sample_size.py mean --d 0.5

    # two-proportion comparison, 0.30 vs 0.45
    python sample_size.py prop --p1 0.30 --p2 0.45 --power 0.90

    # estimate a proportion to +/- 3 points at 95%
    python sample_size.py precision --margin 0.03 --p 0.5

Clustered/stratified designs: multiply the printed n by your design effect (see
references/sampling_and_power.md). SRS is assumed here.

Accepted input domains (anything else is rejected: the library functions raise ValueError,
the CLI prints the reason on stderr and exits 2):
  every value     a finite real number (nan / inf are rejected)
  alpha           0 < alpha < 1
  power           0 < power < 1 and power > alpha (a two-sided level-alpha test already
                  rejects with probability alpha when there is no effect, so power <= alpha is
                  not a planning target; below alpha/2 the formula has no solution at all)
  d               non-zero (sign ignored: the test is two-sided). d = 0 is a zero effect, and
                  no finite sample size achieves the requested power.
  p1, p2          0 < p < 1, and p1 != p2 (equal proportions are a zero effect)
  p (precision)   0 < p < 1
  margin          0 < margin < 1, on the proportion scale (0.03 = +/-3 percentage points)
"""
from __future__ import annotations

import argparse
import math
import numbers


def _real(name: str, x: object) -> float:
    """Return x as a finite float, or raise ValueError naming the parameter."""
    if isinstance(x, bool) or not isinstance(x, numbers.Real):
        raise ValueError(f"{name} must be a real number, got {x!r}")
    try:
        value = float(x)
    except OverflowError:
        raise ValueError(f"{name} is too large to represent as a float: {x!r}") from None
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite, got {x!r}")
    return value


def _open_unit(name: str, x: object) -> float:
    value = _real(name, x)
    if not 0.0 < value < 1.0:
        raise ValueError(f"{name} must be strictly between 0 and 1, got {x!r}")
    return value


def _check_alpha_power(alpha: object, power: object) -> None:
    a = _open_unit("alpha", alpha)
    b = _open_unit("power", power)
    if b <= a:
        raise ValueError(
            f"power ({power!r}) must be greater than alpha ({alpha!r}): a two-sided level-alpha "
            "test already rejects with probability alpha when there is no effect, so a target "
            "power <= alpha is not a meaningful planning target")


def _finite_n(compute, what: str) -> int:
    """Run the n formula; turn float overflow/underflow into a clear ValueError."""
    try:
        n = compute()
    except (OverflowError, ZeroDivisionError):
        n = math.inf
    if not math.isfinite(n):
        raise ValueError(f"{what}: the required sample size is too large to represent as a "
                         "float (the effect is vanishingly small relative to its variance)")
    return math.ceil(n)


def _norm_ppf(p: float) -> float:
    """Inverse standard-normal CDF via the Acklam rational approximation (stdlib only).

    Accurate to ~1e-9 in the central region, ample for sample-size planning.
    """
    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0, 1)")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


def _z_pair(alpha: float, power: float) -> tuple[float, float]:
    return _norm_ppf(1 - alpha / 2), _norm_ppf(power)


def n_mean(d: float, alpha: float, power: float) -> int:
    """Per-group n for a two-sided two-sample mean comparison (Cohen's d).

    Raises ValueError for d == 0 (no finite n achieves the power), non-finite input, or
    alpha/power outside their domains (see the module docstring).
    """
    _check_alpha_power(alpha, power)
    if _real("d", d) == 0:
        raise ValueError("effect size d must be non-zero: with a zero effect no finite sample "
                         "size achieves the requested power")
    za, zb = _z_pair(alpha, power)
    return _finite_n(lambda: 2 * (za + zb) ** 2 / d ** 2, f"d={d!r}")


def n_prop(p1: float, p2: float, alpha: float, power: float) -> int:
    """Per-group n for a two-sided two-proportion comparison.

    Raises ValueError for p1 == p2 (zero effect), proportions outside (0, 1), non-finite
    input, or alpha/power outside their domains (see the module docstring).
    """
    _check_alpha_power(alpha, power)
    if _open_unit("p1", p1) == _open_unit("p2", p2):
        raise ValueError(f"p1 and p2 must differ (both {p1!r}): equal proportions are a zero "
                         "effect, and no finite sample size achieves the requested power")
    za, zb = _z_pair(alpha, power)
    num = (za + zb) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2))
    return _finite_n(lambda: num / (p1 - p2) ** 2, f"p1={p1!r}, p2={p2!r}")


def n_precision(margin: float, p: float, alpha: float) -> int:
    """Total n to estimate a proportion within +/- margin at confidence 1 - alpha.

    margin is a half-width on the proportion scale, 0 < margin < 1 (0.03 = +/-3 points);
    p must lie in (0, 1). Raises ValueError otherwise, or for non-finite input.
    """
    _open_unit("alpha", alpha)
    _open_unit("p", p)
    m = _real("margin", margin)
    if not 0.0 < m < 1.0:
        raise ValueError(f"margin must be > 0 and < 1 on the proportion scale (e.g. 0.03 for "
                         f"+/-3 percentage points), got {margin!r}")
    za = _norm_ppf(1 - alpha / 2)
    return _finite_n(lambda: za ** 2 * p * (1 - p) / margin ** 2, f"margin={margin!r}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="mode", required=True)

    m = sub.add_parser("mean", help="two-group mean comparison (Cohen's d)")
    m.add_argument("--d", type=float, required=True, help="smallest effect size of interest (Cohen's d)")
    m.add_argument("--alpha", type=float, default=0.05)
    m.add_argument("--power", type=float, default=0.80)

    pr = sub.add_parser("prop", help="two-proportion comparison")
    pr.add_argument("--p1", type=float, required=True)
    pr.add_argument("--p2", type=float, required=True)
    pr.add_argument("--alpha", type=float, default=0.05)
    pr.add_argument("--power", type=float, default=0.80)

    pc = sub.add_parser("precision", help="estimate a proportion to a target margin")
    pc.add_argument("--margin", type=float, required=True, help="desired half-width (e.g. 0.03)")
    pc.add_argument("--p", type=float, default=0.5, help="expected proportion (0.5 = conservative)")
    pc.add_argument("--alpha", type=float, default=0.05)

    args = ap.parse_args()
    sub_parser = {"mean": m, "prop": pr, "precision": pc}[args.mode]
    try:
        if args.mode == "mean":
            n = n_mean(args.d, args.alpha, args.power)
        elif args.mode == "prop":
            n = n_prop(args.p1, args.p2, args.alpha, args.power)
        else:
            n = n_precision(args.margin, args.p, args.alpha)
    except ValueError as exc:
        sub_parser.error(str(exc))  # prints usage + message on stderr, exits 2
    if args.mode == "mean":
        print(f"Two-group mean comparison | d={args.d}, alpha={args.alpha}, power={args.power}")
        print(f"  per group n = {n}   (total = {2 * n})")
        print("  Power on the SMALLEST meaningful effect, not a pilot's inflated one.")
    elif args.mode == "prop":
        print(f"Two-proportion comparison | p1={args.p1}, p2={args.p2}, alpha={args.alpha}, power={args.power}")
        print(f"  per group n = {n}   (total = {2 * n})")
    else:
        print(f"Estimate a proportion | margin=+/-{args.margin}, p={args.p}, conf={1 - args.alpha:.0%}")
        print(f"  total n = {n}")
    print("SRS assumed. For clustered/stratified designs multiply by the design effect (DEFF).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
