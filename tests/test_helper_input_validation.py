"""Input-domain validation + independent numerical checks for the scientific helper scripts.

Helpers covered (each loaded with importlib and exercised as a CLI via subprocess):

  * sample_size.py   skills/social-science-workflow/alterlab-ssci-sampling-gate/scripts/
  * omega.py         skills/social-science-workflow/alterlab-sem-psychometrics/scripts/
  * icr.py           skills/social-science-workflow/alterlab-qualitative-analysis/scripts/
  * tesvik_score.py  skills/turkish-academia/alterlab-akademik-tesvik/scripts/
  * score_docentlik.py  skills/turkish-academia/alterlab-docentlik-eligibility/scripts/

Contract under test: invalid input raises ValueError from the library functions, and the CLI
exits 2 with the reason on stderr (no traceback, nothing on stdout). Valid input keeps working.

Independent references: scipy / statsmodels / pingouin are NOT in the uv environment and are not
added as dependencies, so the statistical helpers are checked against (a) the stdlib
statistics.NormalDist quantile/CDF (Wichura's AS241 algorithm, independent of the Acklam
approximation the script uses), (b) first-principles definitions re-derived here (the power
function, the reliability of a weighted composite, Krippendorff's D_o/D_e by pair enumeration),
and (c) published worked examples, cited in each test's docstring.

The two Turkish regulatory scorers are checked for ARITHMETIC CONSISTENCY ONLY (against the worked
examples in their own skill references). That is NOT independent verification of the regulatory
rules: if a reference transcribed a regulation table wrongly, these tests would not notice.
"""

from __future__ import annotations

import importlib.util
import json
import math
import random
import subprocess
import sys
from pathlib import Path
from statistics import NormalDist

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "skills"
SS_PATH = SKILLS / "social-science-workflow/alterlab-ssci-sampling-gate/scripts/sample_size.py"
OMEGA_PATH = SKILLS / "social-science-workflow/alterlab-sem-psychometrics/scripts/omega.py"
ICR_PATH = SKILLS / "social-science-workflow/alterlab-qualitative-analysis/scripts/icr.py"
TESVIK_PATH = SKILLS / "turkish-academia/alterlab-akademik-tesvik/scripts/tesvik_score.py"
DOCENT_PATH = SKILLS / "turkish-academia/alterlab-docentlik-eligibility/scripts/score_docentlik.py"

N01 = NormalDist()


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # dataclasses need the module registered before exec
    spec.loader.exec_module(module)
    return module


ss = _load("helper_validation_sample_size", SS_PATH)
omega = _load("helper_validation_omega", OMEGA_PATH)
icr = _load("helper_validation_icr", ICR_PATH)
tesvik = _load("helper_validation_tesvik", TESVIK_PATH)
docent = _load("helper_validation_docentlik", DOCENT_PATH)


def _cli(path: Path, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(path), *args], input=stdin, capture_output=True,
                          text=True, timeout=120, cwd=REPO_ROOT)


def _assert_rejected(proc: subprocess.CompletedProcess, *fragments: str) -> None:
    detail = f"exit={proc.returncode}\nstdout={proc.stdout!r}\nstderr={proc.stderr!r}"
    assert proc.returncode == 2, detail
    assert "Traceback" not in proc.stderr, detail
    assert proc.stdout.strip() == "", detail
    for fragment in fragments:
        assert fragment in proc.stderr, f"missing {fragment!r}\n{detail}"


NAN, INF = float("nan"), float("inf")


# =========================================================================== #
# sample_size.py                                                               #
# =========================================================================== #

QUANTILE_PROBES = [1e-12, 1e-9, 1e-6, 1e-4, 0.001, 0.01, 0.02425, 0.025, 0.05, 0.2, 0.5, 0.8,
                   0.95, 0.975, 0.97575, 0.99, 0.999, 1 - 1e-6, 1 - 1e-9]


@pytest.mark.parametrize("p", QUANTILE_PROBES)
def test_norm_ppf_matches_independent_stdlib_quantile(p):
    """Acklam's approximation vs stdlib NormalDist.inv_cdf (Wichura 1988, AS241).

    Acklam documents a relative error below 1.15e-9; allow 2e-9 relative (to max(1, |z|)).
    """
    ref = N01.inv_cdf(p)
    assert abs(ss._norm_ppf(p) - ref) <= 2e-9 * max(1.0, abs(ref))


MEAN_GRID = [(d, a, b) for d in (0.1, 0.2, 0.35, 0.5, 0.8, 1.2, 2.0)
             for a in (0.001, 0.01, 0.05, 0.1) for b in (0.5, 0.8, 0.9, 0.95, 0.99)]


@pytest.mark.parametrize("d,alpha,power", MEAN_GRID)
def test_n_mean_is_smallest_n_reaching_power(d, alpha, power):
    """Defining property, not the closed form: under the normal approximation the two-sample
    z-test power at n per group is Phi(|d| sqrt(n/2) - z_{1-alpha/2}) (far tail ignored). The
    returned n must reach the target power and n - 1 must not. The exact two-tailed power at n
    (both rejection regions) is also >= target."""
    n = ss.n_mean(d, alpha, power)
    za = N01.inv_cdf(1 - alpha / 2)

    def approx_power(m):
        return N01.cdf(abs(d) * math.sqrt(m / 2) - za)

    assert approx_power(n) >= power
    assert approx_power(n - 1) < power
    lam = abs(d) * math.sqrt(n / 2)
    assert N01.cdf(lam - za) + N01.cdf(-lam - za) >= power
    assert ss.n_mean(-d, alpha, power) == n  # two-sided: the sign of d is irrelevant


PROP_GRID = [(p1, p2, a, b) for p1, p2 in ((0.1, 0.2), (0.3, 0.45), (0.5, 0.4), (0.05, 0.01),
                                           (0.9, 0.95), (0.6, 0.3))
             for a in (0.01, 0.05) for b in (0.8, 0.9)]


@pytest.mark.parametrize("p1,p2,alpha,power", PROP_GRID)
def test_n_prop_is_smallest_n_reaching_power(p1, p2, alpha, power):
    """Unpooled two-proportion z-test (Fleiss, Levin & Paik 2003, ch. 4, without continuity
    correction): power(n) ~ Phi(|p1 - p2| sqrt(n) / sqrt(p1 q1 + p2 q2) - z_{1-alpha/2})."""
    n = ss.n_prop(p1, p2, alpha, power)
    za = N01.inv_cdf(1 - alpha / 2)
    sd = math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))

    def approx_power(m):
        return N01.cdf(abs(p1 - p2) * math.sqrt(m) / sd - za)

    assert approx_power(n) >= power
    assert approx_power(n - 1) < power
    assert ss.n_prop(p2, p1, alpha, power) == n


PRECISION_GRID = [(m, p, a) for m in (0.01, 0.03, 0.05, 0.1) for p in (0.1, 0.3, 0.5, 0.9)
                  for a in (0.01, 0.05, 0.1)]


@pytest.mark.parametrize("margin,p,alpha", PRECISION_GRID)
def test_n_precision_is_smallest_n_reaching_margin(margin, p, alpha):
    """Wald half-width z_{1-alpha/2} sqrt(p(1-p)/n) must be <= margin at n and > margin at n-1."""
    n = ss.n_precision(margin, p, alpha)
    za = N01.inv_cdf(1 - alpha / 2)

    def half_width(m):
        return za * math.sqrt(p * (1 - p) / m)

    assert half_width(n) <= margin
    assert n == 1 or half_width(n - 1) > margin


def test_n_mean_published_example_cohen_d05():
    """d = 0.5, two-sided alpha = .05, power = .80.

    z approximation: 2 (1.95996 + 0.84162)^2 / 0.5^2 = 62.79 -> 63 per group. Cohen (1988),
    Statistical Power Analysis for the Behavioral Sciences, 2nd ed., Table 2.4.1, tabulates
    n = 64 for the t-test (as does Lehr's 16/d^2 rule, Stat Med 1992;11:1099-1102); the normal
    approximation documented by the script is known to come out slightly below the t-test value.
    """
    n = ss.n_mean(0.5, 0.05, 0.80)
    assert n == 63
    assert 62.79 < 2 * (N01.inv_cdf(0.975) + N01.inv_cdf(0.80)) ** 2 / 0.25 < 62.80
    assert 64 - n == 1


def test_n_precision_published_formula_three_points():
    """Cochran (1977), Sampling Techniques, 3rd ed., eq. 4.2: n0 = z^2 p q / d^2. For d = 0.03,
    p = 0.5 at 95%: 1.96^2 * 0.25 / 0.0009 = 1067.1 -> 1068 respondents."""
    assert ss.n_precision(0.03, 0.5, 0.05) == 1068
    assert math.ceil(1.96 ** 2 * 0.25 / 0.03 ** 2) == 1068


@pytest.mark.parametrize("call,fragment", [
    (lambda: ss.n_mean(0, 0.05, 0.8), "must be non-zero"),
    (lambda: ss.n_mean(0.0, 0.05, 0.8), "no finite sample size"),
    (lambda: ss.n_mean(NAN, 0.05, 0.8), "d must be finite"),
    (lambda: ss.n_mean(INF, 0.05, 0.8), "d must be finite"),
    (lambda: ss.n_mean("0.5", 0.05, 0.8), "d must be a real number"),
    (lambda: ss.n_mean(True, 0.05, 0.8), "d must be a real number"),
    (lambda: ss.n_mean(1e-200, 0.05, 0.8), "too large to represent"),
    (lambda: ss.n_mean(0.5, 0, 0.8), "alpha must be strictly between 0 and 1"),
    (lambda: ss.n_mean(0.5, 1, 0.8), "alpha must be strictly between 0 and 1"),
    (lambda: ss.n_mean(0.5, -0.05, 0.8), "alpha must be strictly between 0 and 1"),
    (lambda: ss.n_mean(0.5, NAN, 0.8), "alpha must be finite"),
    (lambda: ss.n_mean(0.5, 0.05, 1.0), "power must be strictly between 0 and 1"),
    (lambda: ss.n_mean(0.5, 0.05, 1.5), "power must be strictly between 0 and 1"),
    (lambda: ss.n_mean(0.5, 0.05, INF), "power must be finite"),
    (lambda: ss.n_mean(0.5, 0.05, 0.05), "must be greater than alpha"),
    (lambda: ss.n_mean(0.5, 0.05, 0.01), "must be greater than alpha"),
    (lambda: ss.n_prop(0.3, 0.3, 0.05, 0.8), "p1 and p2 must differ"),
    (lambda: ss.n_prop(0.0, 0.3, 0.05, 0.8), "p1 must be strictly between 0 and 1"),
    (lambda: ss.n_prop(0.3, 1.0, 0.05, 0.8), "p2 must be strictly between 0 and 1"),
    (lambda: ss.n_prop(-0.2, 0.4, 0.05, 0.8), "p1 must be strictly between 0 and 1"),
    (lambda: ss.n_prop(0.3, NAN, 0.05, 0.8), "p2 must be finite"),
    (lambda: ss.n_precision(0.03, 1.2, 0.05), "p must be strictly between 0 and 1"),
    (lambda: ss.n_precision(0.03, 0.0, 0.05), "p must be strictly between 0 and 1"),
    (lambda: ss.n_precision(0, 0.5, 0.05), "margin must be > 0 and < 1"),
    (lambda: ss.n_precision(-0.03, 0.5, 0.05), "margin must be > 0 and < 1"),
    (lambda: ss.n_precision(1.0, 0.5, 0.05), "margin must be > 0 and < 1"),
    (lambda: ss.n_precision(3, 0.5, 0.05), "margin must be > 0 and < 1"),
    (lambda: ss.n_precision(NAN, 0.5, 0.05), "margin must be finite"),
    (lambda: ss.n_precision(0.03, 0.5, 1.5), "alpha must be strictly between 0 and 1"),
])
def test_sample_size_library_rejects_invalid_domains(call, fragment):
    with pytest.raises(ValueError, match=fragment):
        call()


@pytest.mark.parametrize("argv,fragment", [
    (["precision", "--margin", "0.03", "--p", "1.2"], "p must be strictly between 0 and 1"),
    (["mean", "--d", "0"], "effect size d must be non-zero"),
    (["prop", "--p1", "0.3", "--p2", "0.3"], "p1 and p2 must differ"),
    (["precision", "--margin", "0"], "margin must be > 0"),
    (["mean", "--d", "nan"], "d must be finite"),
    (["mean", "--d", "inf"], "d must be finite"),
    (["mean", "--d", "0.5", "--alpha", "nan"], "alpha must be finite"),
    (["mean", "--d", "0.5", "--power", "1.5"], "power must be strictly between 0 and 1"),
    (["mean", "--d", "0.5", "--power", "0.01"], "must be greater than alpha"),
    (["precision", "--margin", "inf"], "margin must be finite"),
    (["precision", "--margin", "3"], "margin must be > 0 and < 1"),
    (["prop", "--p1", "-0.2", "--p2", "0.4"], "p1 must be strictly between 0 and 1"),
    (["mean", "--d", "abc"], "invalid float value"),
])
def test_sample_size_cli_rejects_invalid_input(argv, fragment):
    _assert_rejected(_cli(SS_PATH, *argv), fragment)


def test_sample_size_cli_reported_defect_no_negative_n():
    """Reported defect: `precision --margin 0.03 --p 1.2` printed n = -1024 and exited 0."""
    proc = _cli(SS_PATH, "precision", "--margin", "0.03", "--p", "1.2")
    _assert_rejected(proc, "p must be strictly between 0 and 1, got 1.2")
    assert "-1024" not in proc.stdout + proc.stderr


def test_sample_size_cli_valid_inputs_unchanged():
    proc = _cli(SS_PATH, "mean", "--d", "0.5")
    assert proc.returncode == 0, proc.stderr
    assert "per group n = 63   (total = 126)" in proc.stdout
    proc = _cli(SS_PATH, "prop", "--p1", "0.30", "--p2", "0.45", "--power", "0.90")
    assert proc.returncode == 0 and "per group n = 214" in proc.stdout
    proc = _cli(SS_PATH, "precision", "--margin", "0.03", "--p", "0.5")
    assert proc.returncode == 0 and "total n = 1068" in proc.stdout


# =========================================================================== #
# omega.py                                                                     #
# =========================================================================== #

def _implied_cov(lams):
    """Model-implied correlation matrix of a one-factor model: lambda lambda' + diag(1 - lambda^2)."""
    k = len(lams)
    return [[lams[i] * lams[j] + ((1.0 - lams[i] ** 2) if i == j else 0.0) for j in range(k)]
            for i in range(k)]


def _quad(w, s):
    return sum(w[i] * s[i][j] * w[j] for i in range(len(w)) for j in range(len(w)))


def _composite_reliability(w, lams):
    """Reliability of the composite sum(w_i X_i): common-factor variance / total variance."""
    return sum(wi * li for wi, li in zip(w, lams)) ** 2 / _quad(w, _implied_cov(lams))


def _alpha_from_cov(s):
    """Cronbach's alpha computed from a covariance matrix: k/(k-1) * (1 - tr(S) / 1'S1)."""
    k = len(s)
    total = sum(sum(row) for row in s)
    return k / (k - 1) * (1 - sum(s[i][i] for i in range(k)) / total)


CONGENERIC = [[0.72, 0.68, 0.81, 0.55], [0.9, 0.4], [0.3, 0.5, 0.7, 0.9, 0.6],
              [0.95, 0.2, 0.6], [0.45] * 3 + [0.85] * 3]


@pytest.mark.parametrize("lams", CONGENERIC)
def test_omega_equals_reliability_of_unit_weighted_sum(lams):
    """McDonald (1999), Test Theory, ch. 6: omega_total is the share of the unit-weighted sum's
    variance due to the common factor, computed here from the model-implied covariance matrix."""
    assert omega.omega_total(lams) == pytest.approx(_composite_reliability([1.0] * len(lams), lams),
                                                    rel=1e-12)


@pytest.mark.parametrize("lam,k", [(0.3, 2), (0.5, 4), (0.7, 6), (0.9, 10), (0.6, 25)])
def test_omega_parallel_items_spearman_brown_and_alpha(lam, k):
    """Parallel items (equal standardized loadings): omega equals the Spearman-Brown prophecy
    k rho / (1 + (k - 1) rho) with item reliability rho = lambda^2 (Spearman 1910; Brown 1910),
    and equals Cronbach's alpha, which is exact under tau-equivalence (Novick & Lewis 1967,
    Psychometrika 32:1-13)."""
    lams = [lam] * k
    rho = lam * lam
    assert omega.omega_total(lams) == pytest.approx(k * rho / (1 + (k - 1) * rho), rel=1e-12)
    assert omega.omega_total(lams) == pytest.approx(_alpha_from_cov(_implied_cov(lams)), rel=1e-12)


@pytest.mark.parametrize("lams", CONGENERIC[:4])
def test_alpha_is_a_lower_bound_for_congeneric_items(lams):
    """Unequal loadings: Cronbach's alpha < omega (Novick & Lewis 1967; Sijtsma 2009)."""
    assert _alpha_from_cov(_implied_cov(lams)) < omega.omega_total(lams)


@pytest.mark.parametrize("lams", CONGENERIC)
def test_coefficient_h_is_maximal_reliability(lams):
    """Hancock & Mueller (2001): H is the reliability of the optimally weighted composite,
    weights w_i = lambda_i / (1 - lambda_i^2). Checked by computing that composite's reliability
    from the implied covariance matrix, and by showing 500 random weightings never exceed it."""
    h = omega.coefficient_h(lams)
    w_opt = [lam / (1 - lam * lam) for lam in lams]
    assert h == pytest.approx(_composite_reliability(w_opt, lams), rel=1e-12)
    assert h >= omega.omega_total(lams) - 1e-12
    rng = random.Random(20261014)
    for _ in range(500):
        w = [rng.uniform(-1, 2) for _ in lams]
        if abs(sum(wi * li for wi, li in zip(w, lams))) < 1e-9:
            continue
        assert _composite_reliability(w, lams) <= h + 1e-12


def test_omega_documented_boundary_behaviour():
    assert omega.omega_total([1.0, 1.0]) == 1.0 and omega.coefficient_h([1.0, 1.0]) == 1.0
    assert omega.coefficient_h([1.0, 0.5]) == 1.0
    assert omega.omega_total([0.0, 0.0, 0.0]) == 0.0 and omega.coefficient_h([0, 0, 0]) == 0.0


@pytest.mark.parametrize("loadings,fragment", [
    ([], "at least 2"),
    ([0.7], "at least 2"),
    ([0.7, NAN], "loading 2 must be finite"),
    ([INF, 0.5], "loading 1 must be finite"),
    ([0.7, 1.2], "outside \\[-1, 1\\]"),
    ([0.7, -1.01], "outside \\[-1, 1\\]"),
    ([0.7, 10 ** 400], "outside \\[-1, 1\\]"),
    ([0.7, "0.5"], "must be a real number"),
    ([True, 0.5], "must be a real number"),
    ("0.7,0.5", "not a string"),
    (0.7, "sequence of numbers"),
])
@pytest.mark.parametrize("fn", ["omega_total", "coefficient_h"])
def test_omega_library_rejects_invalid_loadings(fn, loadings, fragment):
    with pytest.raises(ValueError, match=fragment):
        getattr(omega, fn)(loadings)


@pytest.mark.parametrize("argv,fragment", [
    (["0.7", "nan", "0.6"], "loading 2 must be finite"),
    (["0.7", "inf"], "loading 2 must be finite"),
    (["0.7", "abc"], "not a number: 'abc'"),
    (["0.7", "1.2"], "outside [-1, 1]"),
    (["0.7"], "at least 2"),
    ([], "at least 2"),
])
def test_omega_cli_rejects_invalid_input(argv, fragment):
    _assert_rejected(_cli(OMEGA_PATH, *argv), fragment)


def test_omega_cli_negative_loading_is_noted_not_rejected():
    proc = _cli(OMEGA_PATH, "0.7", "-0.6", "0.5")
    assert proc.returncode == 0, proc.stderr
    assert "omega_total:  0.159" in proc.stdout
    assert "negative loading" in proc.stderr


def test_omega_cli_valid_example_unchanged():
    proc = _cli(OMEGA_PATH, "--loadings", "0.72,0.68,0.81,0.55")
    assert proc.returncode == 0 and proc.stderr == ""
    assert "omega_total:  0.787" in proc.stdout and "coefficient H:0.811" in proc.stdout


# =========================================================================== #
# icr.py                                                                       #
# =========================================================================== #

# Krippendorff (2011), "Computing Krippendorff's Alpha-Reliability", Annenberg School for
# Communication, University of Pennsylvania (Departmental Papers): reliability data for 4
# observers x 12 units, '' = missing. Published nominal alpha = 0.743.
KRIPP_2011 = [["1", "1", "", "1"], ["2", "2", "3", "2"], ["3", "3", "3", "3"],
              ["3", "3", "3", "3"], ["2", "2", "2", "2"], ["1", "2", "3", "4"],
              ["4", "4", "4", "4"], ["1", "1", "2", "1"], ["2", "2", "2", "2"],
              ["", "5", "5", "5"], ["", "", "1", "1"], ["", "3", "", ""]]


def _alpha_by_pair_enumeration(by_unit):
    """alpha = 1 - D_o / D_e from the definitions (Krippendorff 2004, Content Analysis, ch. 11),
    by enumerating ordered value pairs — not via the coincidence-matrix marginals the script uses.
    D_o: within-unit pairs weighted 1/(m_u - 1); D_e: all pairs of pairable values."""
    units = [[c for c in u if c not in ("", None)] for u in by_unit]
    units = [u for u in units if len(u) >= 2]
    values = [c for u in units for c in u]
    n = len(values)
    d_o = sum(sum(1 for i in range(len(u)) for j in range(len(u)) if i != j and u[i] != u[j])
              / (len(u) - 1) for u in units) / n
    d_e = sum(1 for i in range(n) for j in range(n)
              if i != j and values[i] != values[j]) / (n * (n - 1))
    return 1 - d_o / d_e


def test_krippendorff_alpha_published_example():
    """Krippendorff (2011) worked example: nominal alpha = 0.743."""
    a = icr.krippendorff_alpha_nominal(KRIPP_2011)
    assert round(a, 3) == 0.743
    assert a == pytest.approx(_alpha_by_pair_enumeration(KRIPP_2011), rel=1e-12)


@pytest.mark.parametrize("seed", range(12))
def test_krippendorff_alpha_matches_pair_enumeration_on_random_data(seed):
    rng = random.Random(seed)
    coders, cats = rng.randint(2, 5), rng.randint(2, 4)
    data = [[(str(rng.randrange(cats)) if rng.random() > 0.2 else "") for _ in range(coders)]
            for _ in range(rng.randint(8, 30))]
    got = icr.krippendorff_alpha_nominal(data)
    units = [[c for c in u if c] for u in data]
    pairable = [c for u in units if len(u) >= 2 for c in u]
    if len(set(pairable)) < 2:
        assert got is None
    else:
        assert got == pytest.approx(_alpha_by_pair_enumeration(data), rel=1e-12, abs=1e-12)


def test_cohens_kappa_published_example():
    """Wikipedia 'Cohen's kappa' worked example (50 grant proposals, 2 readers): both yes 20,
    A yes/B no 5, A no/B yes 10, both no 15 -> p_o = 0.70, p_e = 0.5*0.6 + 0.5*0.4 = 0.50,
    kappa = (0.70 - 0.50) / (1 - 0.50) = 0.40."""
    a = ["Y"] * 25 + ["N"] * 25
    b = ["Y"] * 20 + ["N"] * 5 + ["Y"] * 10 + ["N"] * 15
    assert icr.cohens_kappa_2(a, b) == pytest.approx(0.40, abs=1e-12)


def test_icr_degenerate_cases_are_not_estimable():
    same = [["x", "x"]] * 5
    assert icr.krippendorff_alpha_nominal(same) is None
    assert icr.cohens_kappa_2(["x"] * 5, ["x"] * 5) is None  # was 1.0: 0/0 is undefined
    assert icr.krippendorff_alpha_nominal([["1", ""], ["", "2"]]) is None
    assert icr.cohens_kappa_2(["1", ""], ["", "2"]) is None
    with pytest.raises(ValueError, match="one code per unit"):
        icr.cohens_kappa_2(["1", "2", "1"], ["1", "2"])


@pytest.mark.parametrize("body,fragment", [
    ("", "the CSV is empty"),
    ("A,B\n", "no data rows"),
    ("A\n1\n2\n", "at least 2 coder columns"),
    ("A,B\n1,1\n2\n1,1\n", "line 3 has 1 cells but the header names 2 coders"),
    ("A,B\n1,1,3\n2,2\n", "line 2 has 3 cells but the header names 2 coders"),
])
def test_icr_cli_rejects_malformed_csv(tmp_path, body, fragment):
    path = tmp_path / "codings.csv"
    path.write_text(body, encoding="utf-8")
    _assert_rejected(_cli(ICR_PATH, str(path)), fragment)


def test_icr_cli_missing_file(tmp_path):
    _assert_rejected(_cli(ICR_PATH, str(tmp_path / "missing.csv")), "No such file")


def test_icr_cli_explains_degenerate_results(tmp_path):
    path = tmp_path / "constant.csv"
    path.write_text("A,B\nx,x\nx,x\n\n,\nx,x\n", encoding="utf-8")  # blank rows are skipped
    proc = _cli(ICR_PATH, str(path))
    assert proc.returncode == 0, proc.stderr
    assert "units: 3" in proc.stdout
    assert "not estimable — every pairable code is the same category" in proc.stdout
    path.write_text("A,B\n1,\n,2\n", encoding="utf-8")
    proc = _cli(ICR_PATH, str(path))
    assert proc.returncode == 0 and "no unit has codes from at least 2 coders" in proc.stdout


def test_icr_cli_published_example(tmp_path):
    path = tmp_path / "kripp2011.csv"
    path.write_text("A,B,C,D\n" + "\n".join(",".join(u) for u in KRIPP_2011) + "\n",
                    encoding="utf-8")
    proc = _cli(ICR_PATH, str(path))
    assert proc.returncode == 0, proc.stderr
    assert "Krippendorff alpha (nominal): 0.743" in proc.stdout


# =========================================================================== #
# tesvik_score.py — ARITHMETIC CONSISTENCY ONLY                                #
# =========================================================================== #

def _tesvik_total(activities):
    return tesvik.score(activities).final_score


def test_tesvik_reference_worked_example_arithmetic():
    """Arithmetic consistency with the worked example in the skill's own
    references/hesaplama.md (A1 field: 67.80; A2 field: 79.80). This checks that the script
    does the documented arithmetic; it is NOT independent verification of the Akademik Teşvik
    Ödeneği Yönetmeliği or of the transcribed Tablo 4 values."""
    a1 = [{"type": "Yayın", "oran": 0.48}, {"type": "Proje", "oran": 0.80},
          {"type": "Atıf", "oran": 0.04, "count": 12}, {"type": "Tebliğ", "oran": 0.15},
          {"type": "Ödül", "oran": 1.00}]
    assert _tesvik_total(a1) == pytest.approx(67.80, abs=1e-9)
    a2 = [dict(a1[0], oran=0.64), a1[1], dict(a1[2], oran=0.06), a1[3], a1[4]]
    assert _tesvik_total(a2) == pytest.approx(79.80, abs=1e-9)
    assert tesvik.score(a1).payable is True
    assert tesvik.score(a1[:1]).payable is False  # 14.40 < 30


def test_tesvik_ceiling_cap_and_gate_arithmetic():
    """Arithmetic only (not a regulatory check): per-type ceiling = headline, total cap 100,
    payable iff final >= 30, as the script documents them."""
    rep = tesvik.score([{"type": "yayin", "oran": 0.64}, {"type": "YAYIN", "oran": 0.64}])
    (yayin,) = rep.per_type
    assert yayin.raw == pytest.approx(38.4) and yayin.final == 30 and yayin.capped_at_ceiling
    every = [{"type": t, "oran": 1.0} for t in tesvik.TYPE_HEADLINE]
    rep = tesvik.score(every)
    assert rep.gross == sum(tesvik.TYPE_HEADLINE.values()) and rep.final_score == 100
    assert rep.capped_at_100
    assert tesvik.score([{"type": "Yayın", "oran": 1.0}]).payable is True  # exactly 30
    assert tesvik.score([{"type": "Yayın", "oran": 0.999}]).payable is False


def test_tesvik_accepts_documented_input_forms():
    assert _tesvik_total([{"type": "Atıf", "oran": "0.04", "count": "12"}]) == pytest.approx(14.4)
    assert _tesvik_total([{"type": "Atıf", "oran": 0.04, "count": 12.0}]) == pytest.approx(14.4)
    assert _tesvik_total([{"type": "Atıf", "oran": 0.06, "count": 0}]) == 0
    rep = tesvik.score([{"type": "Kitap", "oran": 0.5}, {"type": "Yayın"}])
    assert rep.final_score == 0 and len(rep.warnings) == 3  # unknown type, no oran, gate
    assert tesvik.score([]).final_score == 0


@pytest.mark.parametrize("activity,fragment", [
    ({"type": "Yayın", "oran": -0.5}, "'oran' must be >= 0"),
    ({"type": "Atıf", "oran": 0.04, "count": -12}, "'count' must be >= 0"),
    ({"type": "Atıf", "oran": 0.04, "count": 1.5}, "'count' must be a whole number"),
    ({"type": "Yayın", "oran": NAN}, "'oran' must be finite"),
    ({"type": "Yayın", "oran": INF}, "'oran' must be finite"),
    ({"type": "Yayın", "oran": "nan"}, "'oran' must be finite"),
    ({"type": "Yayın", "oran": "-inf"}, "'oran' must be finite"),
    ({"type": "Yayın", "oran": 10 ** 400}, "'oran' is too large"),
    ({"type": "Yayın", "oran": "abc"}, "'oran' must be a number"),
    ({"type": "Yayın", "oran": None}, "'oran' must be a number"),
    ({"type": "Yayın", "oran": True}, "'oran' must be a number"),
    ({"type": "Yayın", "oran": [0.5]}, "'oran' must be a number"),
    ({"type": "Atıf", "oran": 0.04, "count": NAN}, "'count' must be finite"),
    ({"type": "Kitap", "oran": -1}, "'oran' must be >= 0"),  # validated even if type unknown
])
def test_tesvik_library_rejects_invalid_activity(activity, fragment):
    with pytest.raises(ValueError, match=fragment):
        tesvik.score([{"type": "Proje", "oran": 0.8}, activity])


def test_tesvik_library_rejects_wrong_shapes():
    with pytest.raises(ValueError, match="must be a JSON object"):
        tesvik.score(["not-an-object"])
    with pytest.raises(ValueError, match="must be a list"):
        tesvik.score({"type": "Yayın", "oran": 0.5})


@pytest.mark.parametrize("payload,fragment", [
    ('[{"type": "Yayın", "oran": -0.5}, {"type": "Proje", "oran": 0.8}]', "'oran' must be >= 0"),
    ('[{"type": "Atıf", "oran": 0.04, "count": -12}]', "'count' must be >= 0"),
    ('[{"type": "Yayın", "oran": NaN}]', "non-finite number literal 'NaN'"),
    ('[{"type": "Yayın", "oran": Infinity}]', "non-finite number literal 'Infinity'"),
    ('[{"type": "Yayın", "oran": 1e400}]', "'oran' must be finite"),
    ('[{"type": "Yayın", "oran": "abc"}]', "'oran' must be a number"),
    ('["x"]', "must be a JSON object"),
    ('{"type": "Yayın"}', "must be a list"),
    ("not json", "not valid JSON"),
])
def test_tesvik_cli_rejects_invalid_input(payload, fragment):
    _assert_rejected(_cli(TESVIK_PATH, "-", "--json", stdin=payload), fragment)


def test_tesvik_cli_missing_file(tmp_path):
    _assert_rejected(_cli(TESVIK_PATH, str(tmp_path / "missing.json")), "cannot read input")


def test_tesvik_cli_valid_example_unchanged():
    payload = json.dumps([{"type": "Yayın", "oran": 0.48}, {"type": "Proje", "oran": 0.80},
                          {"type": "Atıf", "oran": 0.04, "count": 12}], ensure_ascii=False)
    proc = _cli(TESVIK_PATH, "-", "--json", stdin=payload)
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["final_score"] == pytest.approx(44.8) and out["payable"] is True


# =========================================================================== #
# score_docentlik.py — ARITHMETIC CONSISTENCY ONLY                             #
# =========================================================================== #

def test_docentlik_self_test_passes():
    """The scorer's own hand-computed worked cases (one or more per bundled ÜAK table). These
    are ARITHMETIC CONSISTENCY checks against the skill's transcription of the tables; they are
    NOT independent verification of the ÜAK doçentlik criteria."""
    proc = _cli(DOCENT_PATH, "--self-test")
    assert proc.returncode == 0, proc.stdout[-2000:] + proc.stderr
    assert "SELF-TEST PASSED" in proc.stdout


def test_docentlik_reference_share_examples_arithmetic():
    """references/scoring_rules.md worked examples (arithmetic only, not a regulatory check):
    Sosyal Q2 article, 4 authors -> 20/4 = 5.0; Hukuk TR Dizin article, 2 authors -> 10/2 = 5.0."""
    rep = docent.build_report({"publications": [{"index": "Q2", "authors": 4, "post_doc": True}]},
                              "sosyal", None)
    assert rep["publications"][0]["scaled"] == 5.0
    rep = docent.build_report({"publications": [{"index": "TRDizin", "authors": 2}]}, "hukuk",
                              None)
    assert rep["publications"][0]["scaled"] == 5.0


@pytest.mark.parametrize("value", [NAN, INF, -INF, -1, -0.5, True, "10", None, 10 ** 400])
def test_docentlik_other_item_points_must_be_finite_non_negative(value):
    with pytest.raises(ValueError, match="other_items: points"):
        docent._num(value, "points")
    data = {"publications": [], "other_items": [{"item": 5, "points": value,
                                                 "post_doc_points": 0}]}
    with pytest.raises(ValueError, match="other_items: points"):
        docent.build_report(data, "sosyal", None)


def test_docentlik_other_item_points_valid_values():
    assert docent._num(0, "points") == 0.0 and docent._num(2.5, "points") == 2.5


@pytest.mark.parametrize("args,fragment", [
    (("equal", "article", 0, False), "author count must be an integer >= 1"),
    (("lead", "article", -2, True), "author count must be an integer >= 1"),
    (("lead", "article", 2.5, True), "author count must be an integer >= 1"),
    (("lead", "article", True, True), "author count must be an integer >= 1"),
    (("weighted", "article", 2, True), "share rule must be"),
    (("lead", "chapter", 2, True), "publication kind must be"),
])
def test_docentlik_share_factor_rejects_invalid_arguments(args, fragment):
    with pytest.raises(ValueError, match=fragment):
        docent.share_factor(*args)


def test_docentlik_invalid_author_count_stays_unscored():
    """Documented behaviour (references/scoring_rules.md): a non-integer or < 1 author count
    marks the publication unscored instead of rejecting the whole input."""
    pubs = [{"title": t, "index": "Q2", "authors": a, "post_doc": True}
            for t, a in (("zero", 0), ("neg", -2), ("frac", 2.5), ("inf", INF), ("nan", NAN))]
    rep = docent.build_report({"publications": pubs}, "sosyal", None)
    assert rep["unscored"] == ["zero", "neg", "frac", "inf", "nan"]
    assert rep["summary"]["total_points"] == 0.0


def test_docentlik_build_report_rejects_wrong_shapes():
    with pytest.raises(ValueError, match="JSON object"):
        docent.build_report([], "sosyal", None)
    with pytest.raises(ValueError, match="unknown alan code"):
        docent.build_report({"publications": []}, "astrology", None)


BASE = '{"alan": "sosyal", "publications": [{"index": "Q2", "authors": 1, "post_doc": true}], '


@pytest.mark.parametrize("payload,fragment", [
    (BASE + '"other_items": [{"item": 5, "points": NaN, "post_doc_points": 5}]}',
     "non-finite number literal 'NaN'"),
    (BASE + '"other_items": [{"item": 5, "points": Infinity, "post_doc_points": 5}]}',
     "non-finite number literal 'Infinity'"),
    (BASE + '"other_items": [{"item": 7, "points": 1e400, "post_doc_points": 1}]}',
     "points must be a finite non-negative number"),
    (BASE + '"other_items": [{"item": 5, "points": 5, "post_doc_points": -1}]}',
     "post_doc_points must be a finite non-negative number"),
    ('{"publications": [{"index": "Q2", "authors": NaN}]}', "non-finite number literal 'NaN'"),
])
def test_docentlik_cli_rejects_non_finite_and_negative_points(payload, fragment):
    _assert_rejected(_cli(DOCENT_PATH, "-", stdin=payload), fragment)


def test_docentlik_cli_io_errors(tmp_path):
    _assert_rejected(_cli(DOCENT_PATH, str(tmp_path / "missing.json")), "no readable file")
    proc = _cli(DOCENT_PATH, '{"publications": []}', "--out", str(tmp_path / "no" / "x.json"))
    assert proc.returncode == 2 and "cannot write --out" in proc.stderr
    assert "Traceback" not in proc.stderr
