# Python vs R for Complex-Survey Analysis

Loaded on demand from the survey-analysis SKILL.md. Verified 2026-09 against PyPI/CRAN and the
installed packages. **The R `survey` + `srvyr` stack is the field standard and the most complete**;
the Python path is viable but younger. Since this repo already shells to R (QCA), the R path is
fully legitimate here.

## Python

### svy (the Python default — samplics' maintained successor)
- PyPI `svy>=0.29` (beta; by the samplics author; docs at svylab.com/docs/svy). The docs describe
  core design, weighting, and variance estimation as stable while the wider API keeps maturing —
  pin the version and re-check signatures after upgrades.
- `svy.Sample(data=...)` requires a **polars** DataFrame (a pandas frame fails with
  `AttributeError: ... no attribute 'clone'`) — convert with `pl.from_pandas(df)`.
- Design: `svy.Design(stratum=, psu=, ssu=, wgt=, pop_size=svy.PopSize(psu="N_psu"), rep_wgts=)`.
  Replicate weights are objects, not a column pattern: `rep_wgts=svy.JackknifeWgts(prefix="wtrep",
  n_reps=80)` (also `BrrWgts(fay_coef=...)`, `BootstrapWgts`, `SdrWgts`).
- Estimation: `sample.estimation.mean(y, by=, where=, method="taylor"|"replication", deff="wor")`,
  plus `.total()`, `.prop()`, `.ratio(y, x)`, `.median()`, `.quantile()`. Use `by=` for domains.
- Models: `sample.glm.fit(y, x=["age", svy.Cat("educ")], family="binomial")`.
- Weighting: `sample.weighting.rake(controls={"agecat": {...}, "sex": {...}})`, `.poststratify()`,
  `.calibrate()` (GREG), `.adjust()` (non-response), `.trim()`.

### samplics (archived — legacy code only)
- `samplics` 0.6.x still installs and its `TaylorEstimator(PopParam.mean).estimate(y=,
  samp_weight=, stratum=, psu=, fpc=, domain=, deff=True)` still runs, but importing it emits
  `FutureWarning: samplics is archived and no longer maintained. Migrate to 'svy'`. Port existing
  samplics code to svy rather than starting new work on it.

## R (field standard — fully verified)

### survey (Lumley) — `survey>=4.5`, `library(survey)`
```r
des <- svydesign(ids = ~psu, strata = ~strata, weights = ~wt, fpc = ~fpc, data = dat, nest = TRUE)
svymean(~y, des, deff = TRUE); svytotal(~y, des); svyquantile(~y, des, quantiles = 0.5)
svyciprop(~I(y == 1), des, method = "logit")           # proportion CI on the right scale
svyby(~y, ~group, des, svymean)                          # domain estimation
svyglm(y ~ x1 + x2, design = des, family = quasibinomial())   # design-adjusted logistic
```
Replicate designs: `svrepdesign(weights=, repweights=, type="BRR"|"JKn"|"bootstrap", data=)` or
`as.svrepdesign(des, type=...)`.
Calibration: `postStratify(des, ~cell, pop.cell)`, `rake(des, sample.margins, population.margins)`,
`calibrate(des, formula, population)`.

### srvyr — `srvyr>=1.3`, `library(srvyr)` (dplyr-style wrapper over survey)
```r
dat %>% as_survey_design(ids = psu, strata = strata, weights = wt, fpc = fpc, nest = TRUE) %>%
  group_by(group) %>%
  summarise(p = survey_mean(y, vartype = c("se", "ci"), deff = TRUE))
```

### Bayesian: csSampling + brms
`cs_sampling()` (GitHub `RyanHornby/csSampling`) wraps a `brms` model with a `survey` design and a
sandwich covariance correction. Install via `remotes::install_github` (not on CRAN).

## Choosing a path

| Situation | Use |
|-----------|-----|
| Provider ships replicate weights; complex calibration; the authoritative answer | R `survey`/`srvyr` |
| Pure-Python pipeline (Taylor or replicate SEs, raking, design-based GLMs) | `svy` (pinned) |
| Bayesian design-based model | R `csSampling` + `brms` |
| Maintaining old samplics code | `samplics` (archived) — plan a port to `svy` |
