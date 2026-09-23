# Model Comparison and Diagnostics

Code for comparing models (PSIS-LOO), diagnostic scripts, and troubleshooting common sampling issues.

## Comparing Models

ArviZ 1.x compares models with PSIS-LOO only: WAIC and the `ic=`/`scale=` arguments of
`az.compare` were removed. Results are on the elpd (log) scale, where higher is better.

```python
from scripts.model_comparison import compare_models, check_loo_reliability

# Each result needs a log_likelihood group: pm.compute_log_likelihood(idata)
models = {
    'Model1': idata1,
    'Model2': idata2,
    'Model3': idata3
}

# Compare using PSIS-LOO (stacking weights by default)
comparison = compare_models(models)

# Check reliability
check_loo_reliability(models)
```

**Interpretation** (columns `elpd`, `p`, `elpd_diff`, `dse`, `p_worse`, `weight`, `diag_*`;
rule of thumb from Vehtari's LOO cross-validation FAQ):
- **|elpd_diff| < 4**: difference is small; prefer the simpler model or average
- **|elpd_diff| ≥ 4**: compare it with `dse`; a difference several times its SE is credible
- A non-empty `diag_elpd` / `diag_diff` flags an unreliable estimate (e.g. few observations)

**Check Pareto-k values** (threshold `good_k` = min(1 − 1/log10(S), 0.7) for S draws):
- k ≤ `good_k`: PSIS-LOO reliable for that observation
- k above it: investigate influential points, try a more robust likelihood, refit without them
  (`az.reloo`), or use K-fold CV (`az.loo_kfold`). WAIC is not a fallback — it fails in the same
  situations and is no longer in ArviZ

## Model Averaging

When models are similar, average predictions:

```python
from scripts.model_comparison import model_averaging

# Resamples posterior predictive draws in proportion to the stacking weights
averaged_pred, weights = model_averaging(models, var_name='y_obs')
```

## Diagnostic Scripts

### Comprehensive Diagnostics

```python
from scripts.model_diagnostics import create_diagnostic_report

create_diagnostic_report(
    idata,
    var_names=['alpha', 'beta', 'sigma'],
    output_dir='diagnostics/'
)
```

Creates: trace plots, rank plots (mixing check), autocorrelation plots, energy plots, ESS evolution, summary statistics CSV.

### Quick Diagnostic Check

```python
from scripts.model_diagnostics import check_diagnostics

results = check_diagnostics(idata)
```

Checks R-hat, ESS, divergences, and tree depth (works with both PyMC's NUTS and nutpie output).

## Common Issues and Solutions

### Divergences

**Symptom:** `idata.sample_stats.diverging.sum() > 0`

**Solutions:**
1. Increase `target_accept=0.95` or `0.99`
2. Use non-centered parameterization (hierarchical models)
3. Add stronger priors to constrain parameters
4. Check for model misspecification

### Low Effective Sample Size

**Symptom:** total bulk- or tail-`ESS < 400`

**Solutions:**
1. Sample more draws: `draws=5000`
2. Reparameterize to reduce posterior correlation
3. Use QR decomposition for regression with correlated predictors

### High R-hat

**Symptom:** `R-hat > 1.01`

**Solutions:**
1. Run longer chains: `tune=2000, draws=5000`
2. Check for multimodality
3. Improve initialization with ADVI

### Slow Sampling

**Solutions:**
1. Install nutpie (`uv pip install "pymc[nutpie]"`); PyMC 6 then uses it as the default NUTS sampler
2. Use ADVI initialization (`init='advi+adapt_diag', nuts_sampler='pymc'` — `init` applies to PyMC's own NUTS)
3. Reduce model complexity
4. Increase parallelization: `cores=8, chains=8`
5. Use variational inference if appropriate

## Sampling and Inference

### MCMC with NUTS

Default and recommended for most models:

```python
idata = pm.sample(
    draws=2000,
    tune=1000,
    chains=4,
    target_accept=0.9,
    random_seed=42
)
```

**Adjust when needed:**
- Divergences → `target_accept=0.95` or higher
- Slow sampling → Use ADVI for initialization
- Discrete parameters → Use `pm.Metropolis()` for discrete vars

### Variational Inference

Fast approximation for exploration or initialization:

```python
with model:
    approx = pm.fit(n=20000, method='advi')

    # Use one ADVI draw as starting values (`start=` no longer works; use initvals=)
    start = approx.sample(1, return_inferencedata=False)[0]
    idata = pm.sample(initvals=start)
```

**Trade-offs:** much faster than MCMC, but approximate (may underestimate uncertainty). Good for large models or quick exploration.

See `references/sampling_inference.md` for the detailed sampling guide.
