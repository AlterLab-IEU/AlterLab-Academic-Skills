---
name: alterlab-pymc
description: Bayesian modeling and probabilistic programming with PyMC 6 and ArviZ 1.x — hierarchical models, MCMC (NUTS via PyMC, nutpie, NumPyro, or BlackJAX), variational inference, PSIS-LOO model comparison, and prior/posterior predictive checks. Use when fitting Bayesian or hierarchical models, estimating posteriors and credible intervals, diagnosing divergences, R-hat, or ESS, running probabilistic inference, or comparing models with LOO (WAIC was removed from ArviZ 1.x). Part of the AlterLab Academic Skills suite.
license: Apache-2.0
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*)
compatibility: No API key required. Runs locally via `uv run python`; requires pymc >= 6 (current 6.3 as of 2026-09) with ArviZ >= 1.1 and PyTensor 3; nutpie optional but used by default when installed.
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# PyMC Bayesian Modeling

## Overview

PyMC is a Python library for Bayesian modeling and probabilistic programming. Build, fit, validate, and compare Bayesian models using the current API (PyMC ≥ 6 with ArviZ ≥ 1.1), including hierarchical models, MCMC sampling (NUTS), variational inference, and PSIS-LOO model comparison.

```bash
uv pip install "pymc[nutpie]" "arviz[matplotlib,h5netcdf]"   # nutpie sampler, plotting backend, NetCDF I/O
```

PyMC 6 changed several defaults and names that most tutorials still use — read **Version notes** at the end before reusing PyMC 5 / ArviZ 0.x code.

## When to Use This Skill

This skill should be used when:
- Building Bayesian models (linear/logistic regression, hierarchical models, time series, etc.)
- Performing MCMC sampling or variational inference
- Conducting prior/posterior predictive checks
- Diagnosing sampling issues (divergences, convergence, ESS)
- Comparing multiple models with PSIS-LOO cross-validation
- Implementing uncertainty quantification through Bayesian methods
- Working with hierarchical/multilevel data structures
- Handling missing data or measurement error in a principled way

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Frequentist regression with p-values, standard errors, and residual diagnostics | `alterlab-statsmodels` |
| Reporting-focused mixed-effects model for nested data (lme4/glmmTMB/brms, statsmodels MixedLM, or bambi formulas) with ICC and variance-component reporting | `alterlab-multilevel-models` |
| Pooling effect sizes across studies (fixed/random effects, heterogeneity, funnel plots) | `alterlab-meta-analysis` |
| Point-prediction machine learning (random forests, gradient boosting, CV tuning) | `alterlab-scikit-learn` |

## Standard Bayesian Workflow

Follow this 8-step workflow for building and validating Bayesian models:

1. **Data preparation** — standardize predictors, handle missing data, set up `coords`
2. **Model building** — weakly informative priors, named `dims`, `pm.Data()` for predictables
3. **Prior predictive check** — `pm.sample_prior_predictive`; validate priors *before* fitting
4. **Fit** — `pm.sample(draws=2000, tune=1000, chains=4, target_accept=0.9)`, then `pm.compute_log_likelihood(idata)` if you will compare models
5. **Diagnostics** — R-hat < 1.01, ESS > 400, no divergences, good trace mixing
6. **Posterior predictive check** — `pm.sample_posterior_predictive`; check fit vs. observed data
7. **Analyze** — `az.summary`, `az.plot_dist` (was `plot_posterior`), `az.plot_forest`
8. **Predict** — `pm.set_data` then `pm.sample_posterior_predictive`; extract HDI intervals

Full step-by-step code: `references/workflow_examples.md`.

## Common Model Patterns

PyMC supports linear/logistic/Poisson regression, hierarchical (multilevel) models, and
time-series (AR). Ready-to-adapt code for each lives in `references/model_patterns.md`.

Use the non-centered parameterization for hierarchical models when groups have few observations: the centered form creates funnel geometry that NUTS explores poorly, which shows up as divergences.
Templates: `assets/linear_regression_template.py`, `assets/hierarchical_model_template.py`.

## Distribution Selection

Choosing priors and likelihoods is the highest-leverage modeling decision. A quick chooser
(scale params, unbounded, positive, probabilities, correlation matrices; continuous/count/binary/
categorical likelihoods) is in `references/distribution_selection.md`. The comprehensive catalog
is in `references/distributions.md`.

## Model Comparison and Sampling

- **Compare models** with PSIS-LOO (`scripts/model_comparison.py`); interpret `elpd_diff` against `dse` and check Pareto-k. ArviZ 1.x has no WAIC.
- **Sample** with NUTS by default (nutpie when installed); raise `target_accept` for divergences; ADVI for fast approximation.
- **Diagnose** with `scripts/model_diagnostics.py` (`check_diagnostics`, `create_diagnostic_report`).
- **Troubleshoot** divergences, low ESS, high R-hat, slow sampling.

Code and decision rules: `references/model_comparison.md`. Detailed sampling-algorithm guide:
`references/sampling_inference.md`.

## Best Practices

### Model Building

1. **Always standardize predictors** for better sampling
2. **Use weakly informative priors** (not flat)
3. **Use named dimensions** (`dims`) for clarity
4. **Non-centered parameterization** for hierarchical models
5. **Check prior predictive** before fitting

### Sampling

1. **Run multiple chains** (at least 4) for convergence
2. **Use `target_accept=0.9`** as baseline (higher if needed)
3. **Call `pm.compute_log_likelihood(idata)`** before model comparison
4. **Set random seed** for reproducibility

### Validation

1. **Check diagnostics** before interpretation (R-hat, ESS, divergences)
2. **Posterior predictive check** for model validation
3. **Compare multiple models** when appropriate
4. **Report uncertainty** (HDI intervals, not just point estimates)

Start simple and add complexity gradually, iterating on the model based on each
predictive check (see the 8-step workflow above).

## Resources

This skill includes:

### References (`references/`)

- **`workflow_examples.md`**: Full step-by-step code for the 8-step Bayesian workflow (data prep → predictions).
- **`model_patterns.md`**: Ready-to-adapt code for linear/logistic/Poisson regression, hierarchical, and AR time-series models.
- **`distribution_selection.md`**: Quick chooser for priors and likelihoods by parameter/outcome type.
- **`model_comparison.md`**: PSIS-LOO comparison, diagnostic scripts, and troubleshooting (divergences, ESS, R-hat, slow sampling).
- **`distributions.md`**: Comprehensive catalog of PyMC distributions organized by category (continuous, discrete, multivariate, mixture, time series). Use when selecting priors or likelihoods.
- **`sampling_inference.md`**: Detailed guide to sampling algorithms (NUTS, Metropolis, SMC), variational inference (ADVI, SVGD), and handling sampling issues. Use when encountering convergence problems or choosing inference methods.
- **`workflows.md`**: A single end-to-end runnable script (data prep → save) plus extra cookbook recipes not in `workflow_examples.md` — missing-data imputation, QR reparameterization, mixture models, and a model-averaging helper.

### Scripts (`scripts/`)

- **`model_diagnostics.py`**: Automated diagnostic checking and report generation (handles both PyMC-NUTS and nutpie sample stats). Functions: `check_diagnostics()` for quick checks, `create_diagnostic_report()` for comprehensive analysis with plots.

- **`model_comparison.py`**: PSIS-LOO model comparison utilities. Functions: `compare_models()`, `check_loo_reliability()`, `model_averaging()`.

### Templates (`assets/`)

- **`linear_regression_template.py`**: Complete template for Bayesian linear regression with full workflow (data prep, prior checks, fitting, diagnostics, predictions).

- **`hierarchical_model_template.py`**: Complete template for hierarchical/multilevel models with non-centered parameterization and group-level analysis.

## Quick Reference

### Model Building
```python
with pm.Model(coords={'var': names}) as model:
    # Priors
    param = pm.Normal('param', mu=0, sigma=1, dims='var')
    # Likelihood
    y = pm.Normal('y', mu=..., sigma=..., observed=data)
```

### Sampling
```python
idata = pm.sample(draws=2000, tune=1000, chains=4, target_accept=0.9)  # returns xarray.DataTree
pm.compute_log_likelihood(idata)  # needed for LOO / az.compare
```

### Diagnostics
```python
from scripts.model_diagnostics import check_diagnostics
check_diagnostics(idata)
```

### Model Comparison
```python
from scripts.model_comparison import compare_models
compare_models({'m1': idata1, 'm2': idata2})  # PSIS-LOO; higher elpd is better
```

### Predictions
```python
# X must have been wrapped at build time: pm.Data('X', X, dims=('obs', 'predictors'))
with model:
    pm.set_data({'X': X_new}, coords={'obs': range(len(X_new))})
    pm.sample_posterior_predictive(idata, predictions=True, extend_inferencedata=True)
# predictions land in idata.predictions
```

## Additional Notes

- PyMC integrates with ArviZ for visualization and diagnostics
- Use `pm.model_to_graphviz(model)` to visualize model structure (needs the `graphviz` package)
- Save results with `idata.to_netcdf('results.nc')` (requires `h5netcdf` or `netCDF4`, e.g. `arviz[h5netcdf]`); load with `az.from_netcdf('results.nc')`
- For very large models, consider minibatch ADVI or data subsampling

## Version notes (PyMC 6 / ArviZ 1.x)

PyMC 6.0 (May 2026) moved to ArviZ 1.x and PyTensor 3. Code written for PyMC 5 / ArviZ 0.x fails in the ways below.

- **Results are an `xarray.DataTree`**, not `az.InferenceData`. Group access (`idata.posterior`, `idata["posterior"]`) still works; `idata.extend(other)` became `idata.update(other)`; list groups with `list(idata.children)`.
- **Log-likelihood**: call `pm.compute_log_likelihood(idata)` after sampling. `pm.sample(idata_kwargs={"log_likelihood": True})` is deprecated.
- **Sampler**: nutpie is the default NUTS sampler when installed (400 tuning steps by default; PyMC's own NUTS keeps 1000). Select explicitly with `nuts_sampler="pymc" | "nutpie" | "numpyro" | "blackjax"`. Sample-stat names differ (`tree_depth` vs `depth`), so diagnostics code should check which exists. Starting values go in `initvals=` (`start=` fails).
- **Backend**: PyTensor 3 compiles with Numba by default, so the first call includes JIT-compilation time.
- **Summaries**: `az.summary` reports 89% equal-tailed intervals (`eti89_lb`, `eti89_ub`) instead of 94% HDI (`hdi_3%`, `hdi_97%`). Use `az.summary(idata, ci_kind="hdi", ci_prob=0.94)` or set `az.rcParams["stats.ci_kind"]` / `["stats.ci_prob"]`. `az.hdi(..., prob=0.95)` replaces `hdi_prob=`.
- **Plots** return a `PlotCollection` (save with `pc.savefig("file.png")`, show with `pc.show()`); `ax=` / `axes=` arguments are gone. Renames: `plot_posterior` → `plot_dist`, `plot_ppc` → `plot_ppc_dist` (prior checks: `group="prior_predictive"`, `num_samples=` instead of `num_pp_samples=`), `plot_trace` → `plot_trace_dist` (trace plus density), `plot_dist_comparison` → `plot_prior_posterior`. Install a backend with `arviz[matplotlib]`.
- **Model comparison**: `az.waic` is gone and `az.compare(dict)` takes no `ic=`/`scale=`; it ranks by PSIS-LOO `elpd` (higher is better) with stacking weights and reports `elpd_diff`, `dse`, `p_worse`, and `diag_*` columns.
- To predict on new data, the predictors must be wrapped in `pm.Data('X', X, dims=...)` at build time — only then can `pm.set_data({'X': X_new}, coords={...})` swap them. A plain NumPy array baked into the graph cannot be replaced.
- `pm.sample_prior_predictive` takes `draws=` (the old `samples=` keyword was removed).
- For out-of-sample predictions call `pm.sample_posterior_predictive(idata, predictions=True, extend_inferencedata=True, ...)`; results then live in `idata.predictions`, not `idata.posterior_predictive`.

