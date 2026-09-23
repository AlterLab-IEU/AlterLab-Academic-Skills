# Standard Bayesian Workflow — Worked Examples

Step-by-step code for the full PyMC workflow. See also `references/workflows.md` for additional model-type cookbooks.

## 1. Data Preparation

```python
import pymc as pm
import arviz as az
import numpy as np

# Load and prepare data
X = ...  # Predictors
y = ...  # Outcomes

# Standardize predictors for better sampling
X_mean = X.mean(axis=0)
X_std = X.std(axis=0)
X_scaled = (X - X_mean) / X_std
```

**Key practices:**
- Standardize continuous predictors (improves sampling efficiency)
- Center outcomes when possible
- Handle missing data explicitly (treat as parameters)
- Use named dimensions with `coords` for clarity

## 2. Model Building

```python
coords = {
    'predictors': ['var1', 'var2', 'var3'],
    'obs_id': np.arange(len(y))
}

with pm.Model(coords=coords) as model:
    # Wrap predictors in pm.Data so they can be swapped for predictions later
    X_data = pm.Data('X_data', X_scaled, dims=('obs_id', 'predictors'))

    # Priors
    alpha = pm.Normal('alpha', mu=0, sigma=1)
    beta = pm.Normal('beta', mu=0, sigma=1, dims='predictors')
    sigma = pm.HalfNormal('sigma', sigma=1)

    # Linear predictor
    mu = alpha + pm.math.dot(X_data, beta)

    # Likelihood
    y_obs = pm.Normal('y_obs', mu=mu, sigma=sigma, observed=y, dims='obs_id')
```

**Key practices:**
- Use weakly informative priors (not flat priors)
- Use `HalfNormal` or `Exponential` for scale parameters
- Use named dimensions (`dims`) instead of `shape` when possible
- Wrap any value you will later swap for predictions in `pm.Data()`

## 3. Prior Predictive Check

**Always validate priors before fitting:**

```python
with model:
    prior_pred = pm.sample_prior_predictive(draws=1000, random_seed=42)

# Visualize (ArviZ 1.x: plot_ppc -> plot_ppc_dist; plots return a PlotCollection)
az.plot_ppc_dist(prior_pred, group='prior_predictive').show()
```

**Check:**
- Do prior predictions span reasonable values?
- Are extreme values plausible given domain knowledge?
- If priors generate implausible data, adjust and re-check

## 4. Fit Model

```python
with model:
    # Optional: Quick exploration with ADVI
    # approx = pm.fit(n=20000)

    # Full MCMC inference
    idata = pm.sample(
        draws=2000,
        tune=1000,
        chains=4,
        target_accept=0.9,
        random_seed=42,
    )
    # Pointwise log-likelihood for LOO comparison (PyMC 6 deprecates
    # idata_kwargs={'log_likelihood': True})
    pm.compute_log_likelihood(idata)
```

**Key parameters:**
- `draws=2000`: Number of samples per chain
- `tune=1000`: Warmup samples (discarded). If omitted, the default depends on the sampler (1000 for PyMC's NUTS, 400 for nutpie, which PyMC 6 uses by default when installed)
- `chains=4`: Run 4 chains for convergence checking
- `target_accept=0.9`: Higher for difficult posteriors (0.95-0.99)
- Call `pm.compute_log_likelihood(idata)` before LOO model comparison

## 5. Check Diagnostics

```python
from scripts.model_diagnostics import check_diagnostics

results = check_diagnostics(idata, var_names=['alpha', 'beta', 'sigma'])
```

**Check:**
- **R-hat < 1.01**: Chains have converged
- **ESS > 400**: Sufficient effective samples
- **No divergences**: NUTS sampled successfully
- **Trace plots**: Chains should mix well (fuzzy caterpillar)

**If issues arise:**
- Divergences → Increase `target_accept=0.95`, use non-centered parameterization
- Low ESS → Sample more draws, reparameterize to reduce correlation
- High R-hat → Run longer, check for multimodality

## 6. Posterior Predictive Check

```python
with model:
    pm.sample_posterior_predictive(idata, extend_inferencedata=True, random_seed=42)

# Visualize
az.plot_ppc_dist(idata).show()
```

**Check:**
- Do posterior predictions capture observed data patterns?
- Are systematic deviations evident (model misspecification)?
- Consider alternative models if fit is poor

## 7. Analyze Results

```python
# Summary statistics (ArviZ 1.x default: 89% equal-tailed interval columns
# eti89_lb/eti89_ub; pass ci_kind='hdi', ci_prob=0.94 for the old HDI columns)
print(az.summary(idata, var_names=['alpha', 'beta', 'sigma']))

# Posterior distributions (ArviZ 1.x: plot_posterior -> plot_dist)
az.plot_dist(idata, var_names=['alpha', 'beta', 'sigma']).show()

# Coefficient estimates
az.plot_forest(idata, var_names=['beta'], combined=True).show()
```

## 8. Make Predictions

```python
X_new = ...  # New predictor values
X_new_scaled = (X_new - X_mean) / X_std

with model:
    pm.set_data({'X_data': X_new_scaled}, coords={'obs_id': np.arange(len(X_new_scaled))})
    pm.sample_posterior_predictive(
        idata,
        var_names=['y_obs'],
        predictions=True,
        extend_inferencedata=True,
        random_seed=42,
    )

# Extract prediction intervals (predictions=True -> idata.predictions)
y_pred_mean = idata.predictions['y_obs'].mean(dim=['chain', 'draw'])
y_pred_hdi = az.hdi(idata, group='predictions', var_names=['y_obs'], prob=0.95)
```
