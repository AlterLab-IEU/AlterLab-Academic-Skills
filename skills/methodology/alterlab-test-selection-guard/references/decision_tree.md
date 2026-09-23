# Decision Tree — Full Branch Logic

This expands the digraph in `SKILL.md`. Every fork is decided by the research question
and the data's structure, **before** any p-value is visible. It mirrors and stays
consistent with the Test Selection Guide in `alterlab-statistical-analysis`
(`references/test_selection_guide.md`); this file adds the timing discipline.

## 1. Outcome type — the first fork

| Outcome | Goes to |
|---|---|
| Continuous or ordinal, compared across groups | Group-comparison branch (§2/§3) |
| Categorical counts (frequencies in cells) | Categorical branch (§4) |
| Relationship between two variables | Association branch (§5) |

## 2. Two groups, continuous/ordinal outcome

- **Independent + normal** → independent-samples t-test. If the variances are unequal
  (Levene significant), use **Welch's** t-test rather than the pooled-variance form.
- **Independent + non-normal** → Mann-Whitney U.
- **Paired + normal differences** → paired-samples t-test (normality applies to the
  *difference* scores, not the raw groups).
- **Paired + non-normal differences** → Wilcoxon signed-rank.

The parametric branch is the default pre-specification; the non-parametric branch is taken
**only when the assumption-check gate (`references/assumption_gate.md`) sends you there** —
never because the t-test returned a non-significant p-value.

**Simplest defensible pre-specification for two independent groups: Welch's t-test
unconditionally.** Welch controls the Type I error rate when variances are unequal and
loses very little when they are equal, so many methodologists recommend it as the default
rather than choosing between Student and Welch with a Levene test (Delacre, Lakens & Leys,
2017, *International Review of Social Psychology* 30(1):92–101,
https://doi.org/10.5334/irsp.82). A Levene pre-test followed by Student-or-Welch fails to
protect the significance level in simulations, especially with unequal group sizes
(Zimmerman, 2004, *Br J Math Stat Psychol* 57(1):173–181,
https://doi.org/10.1348/000711004849222). A Shapiro-Wilk pre-test distorts the
*conditional* error rates of the t-test or Mann-Whitney chosen after it, although the
overall two-stage procedure stayed near the nominal level in Rochon, Gondan & Kieser's
simulations (2012, *BMC Med Res Methodol* 12:81, https://doi.org/10.1186/1471-2288-12-81).
Either route is compatible with this guard as long as it is fixed in the plan before any
outcome is seen.

## 3. Three or more groups, continuous/ordinal outcome

- **Independent + normal** → one-way ANOVA. Plan post-hoc comparisons (e.g. Tukey HSD) in
  advance; do not pick the post-hoc by which pair is significant.
- **Independent + non-normal** → Kruskal-Wallis.
- **Repeated/within-subject + normal** → repeated-measures ANOVA (check sphericity;
  Greenhouse-Geisser correction if violated).
- **Repeated + non-normal** → Friedman.

A non-significant omnibus test does **not** license fishing through pairwise tests; that is
the multiplicity trap (`references/multiplicity.md`).

## 4. Categorical outcome (counts)

- **Expected cell count >= 5 in (nearly) all cells** → chi-square test of independence.
- **Small expected counts / 2x2 with sparse cells** → Fisher's exact test.

The choice here is driven by the *expected* cell counts, computed before testing — not by
which test yields significance.

## 5. Association between two variables

- **Both continuous, linear + bivariate-normal** → Pearson r.
- **Both continuous, monotonic but non-normal / non-linear** → Spearman rho.
- **Continuous outcome + one or more predictors** → linear regression (check
  linearity, residual normality, homoscedasticity).
- **Binary outcome + predictors** → logistic regression.

## Bayesian alternatives

Bayesian counterparts exist for all of the above and can support the null directly (Bayes
factors). They are chosen the same way — by structure, in advance. See
`alterlab-statistical-analysis` (`references/bayesian_statistics.md`).

## What does NOT change the branch

- The p-value of a previously run test.
- A desire to "get under .05."
- Eyeballing descriptives split by the outcome.

What legitimately moves you between branches: the **pre-specified** assumption-check
verdict, a corrected design fact (e.g. realizing the data are actually paired), or a
correction to the research question made and documented *before* the result is seen.
