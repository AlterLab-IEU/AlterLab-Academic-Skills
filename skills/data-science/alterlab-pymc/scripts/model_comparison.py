"""
PyMC Model Comparison Script

Utilities for comparing multiple Bayesian models with PSIS-LOO cross-validation.

Targets PyMC >= 6 / ArviZ >= 1.1. ArviZ 1.x removed WAIC and the `ic=` / `scale=`
arguments of az.compare(): comparison is always PSIS-LOO on the log (elpd) scale,
higher elpd is better, and weights default to stacking.

Usage:
    from scripts.model_comparison import compare_models, plot_model_comparison

    # Each model needs a log_likelihood group: pm.compute_log_likelihood(idata)
    comparison = compare_models({'model1': idata1, 'model2': idata2, 'model3': idata3})

    # Visualize comparison
    plot_model_comparison(comparison, output_path='model_comparison.png')
"""

from typing import Dict

import arviz as az
import matplotlib.pyplot as plt
import numpy as np
from xarray import DataTree


def compare_models(models_dict: Dict[str, DataTree],
                   method='stacking',
                   verbose=True):
    """
    Compare multiple models using PSIS-LOO (expected log predictive density).

    Parameters
    ----------
    models_dict : dict
        Dictionary mapping model names to DataTree results from pm.sample().
        Every model must have a log_likelihood group.
    method : str
        Weighting method passed to az.compare: 'stacking' (default), 'bb-pseudo-bma'
        or 'pseudo-bma'.
    verbose : bool
        Print detailed comparison results (default: True)

    Returns
    -------
    pd.DataFrame
        Comparison table ranked best-first, with columns rank, elpd, p, elpd_diff,
        dse, p_worse, weight, se, diag_elpd, diag_diff.

    Notes
    -----
    Compute the pointwise log-likelihood after sampling with
    pm.compute_log_likelihood(idata); PyMC 6 deprecates
    pm.sample(idata_kwargs={'log_likelihood': True}).
    """
    comparison = az.compare(models_dict, method=method)

    if verbose:
        print("="*70)
        print(" " * 22 + "MODEL COMPARISON (PSIS-LOO)")
        print("="*70)
        print("\nModel Rankings:")
        print("-"*70)
        print(comparison.to_string())

        print("\n" + "="*70)
        print("INTERPRETATION GUIDE")
        print("="*70)
        print("• rank:       Model ranking (0 = best)")
        print("• elpd:       Expected log predictive density (higher is better)")
        print("• p:          Effective number of parameters")
        print("• elpd_diff:  Difference in elpd from the best model")
        print("• dse:        Standard error of that difference")
        print("• p_worse:    Approx. probability the model predicts worse than the best")
        print(f"• weight:     Model weight ({method})")
        print("• diag_*:     Non-empty when the elpd or difference estimate is unreliable")

        print("\n" + "="*70)
        print("MODEL SELECTION GUIDELINES")
        print("="*70)

        best_model = comparison.index[0]
        print(f"\n✓ Best model: {best_model}")

        # Rule of thumb from the LOO cross-validation FAQ (Vehtari): an elpd
        # difference below ~4 is small; above that, judge it against its SE.
        if len(comparison) > 1:
            runner_up = comparison.index[1]
            delta = abs(comparison.iloc[1]['elpd_diff'])
            delta_se = comparison.iloc[1]['dse']

            if delta < 4:
                print(f"  → {best_model} and {runner_up} are SIMILAR (|elpd_diff| < 4)")
                print("    Consider model averaging or choose based on simplicity")
            elif delta > 2 * delta_se:
                print(f"  → {best_model} predicts better than {runner_up} "
                      f"(|elpd_diff| = {delta:.1f} > 2 × dse = {2 * delta_se:.1f})")
            else:
                print(f"  → Difference is < 2 × dse ({delta:.1f} vs {2 * delta_se:.1f}); "
                      "the ranking is uncertain")

        # Reliability diagnostics (string columns; empty when fine)
        flags = comparison[['diag_elpd', 'diag_diff']].fillna('').astype(str)
        flagged = flags[(flags['diag_elpd'] != '') | (flags['diag_diff'] != '')]
        if len(flagged) > 0:
            print("\n⚠️  WARNING: Some estimates have reliability issues")
            for name, row in flagged.iterrows():
                print(f"   {name}: {row['diag_elpd'] or row['diag_diff']}")
            print("   → Check Pareto-k diagnostics with check_loo_reliability()")

    return comparison


def check_loo_reliability(models_dict: Dict[str, DataTree],
                          threshold=None,
                          verbose=True):
    """
    Check PSIS-LOO reliability using Pareto-k diagnostics.

    Parameters
    ----------
    models_dict : dict
        Dictionary mapping model names to DataTree results with a log_likelihood group
    threshold : float, optional
        Pareto-k threshold for flagging observations. Defaults to the
        sample-size-dependent threshold ArviZ reports as ``good_k``
        (min(1 - 1/log10(S), 0.7) for S posterior draws).
    verbose : bool
        Print detailed diagnostics (default: True)

    Returns
    -------
    dict
        Dictionary with Pareto-k diagnostics for each model
    """
    if verbose:
        print("="*70)
        print(" " * 20 + "LOO RELIABILITY CHECK")
        print("="*70)

    results = {}

    for name, idata in models_dict.items():
        if verbose:
            print(f"\n{name}:")
            print("-"*70)

        # Compute LOO with pointwise results
        loo_result = az.loo(idata, pointwise=True)
        pareto_k = np.asarray(loo_result.pareto_k).ravel()
        k_threshold = loo_result.good_k if threshold is None else threshold

        # Count problematic observations
        n_high = int((pareto_k > k_threshold).sum())
        n_very_high = int((pareto_k > 1.0).sum())

        results[name] = {
            'pareto_k': pareto_k,
            'threshold': k_threshold,
            'n_high': n_high,
            'n_very_high': n_very_high,
            'max_k': float(pareto_k.max()),
            'loo': loo_result
        }

        if verbose:
            print(f"Pareto-k diagnostics (threshold k = {k_threshold:.2f}):")
            print(f"  • Good (k ≤ {k_threshold:.2f}):  {int((pareto_k <= k_threshold).sum())} observations")
            print(f"  • Bad ({k_threshold:.2f} < k ≤ 1):  {n_high - n_very_high} observations")
            print(f"  • Very bad (k > 1):      {n_very_high} observations")
            print(f"  • Maximum k: {pareto_k.max():.3f}")

            if n_high > 0:
                print(f"\n⚠️  {n_high} observations with k > {k_threshold:.2f}")
                print("  PSIS-LOO may be unreliable for these points")
                print("  Solutions:")
                print("  → Investigate the influential observations (az.plot_khat(loo_result))")
                print("  → Try a more robust likelihood (e.g. StudentT instead of Normal)")
                print("  → Refit without those points (az.reloo) or use K-fold CV (az.loo_kfold)")
                print("    (WAIC is not a fix: it fails in the same cases and ArviZ 1.x removed it)")
            else:
                print(f"✓ All Pareto-k values ≤ {k_threshold:.2f}")
                print("  LOO estimates are reliable")

    return results


def plot_model_comparison(comparison, output_path=None, show=True):
    """
    Visualize model comparison results.

    Parameters
    ----------
    comparison : pd.DataFrame
        Comparison DataFrame from az.compare() / compare_models()
    output_path : str, optional
        If provided, save plot to this path
    show : bool
        Whether to display plot (default: True)

    Returns
    -------
    PlotCollection
        The ArviZ 1.x plot collection
    """
    pc = az.plot_compare(comparison)
    pc.add_title('Model Comparison (PSIS-LOO)')

    if output_path:
        pc.savefig(output_path)
        print(f"Comparison plot saved to {output_path}")

    if show:
        pc.show()
    else:
        plt.close('all')

    return pc


def model_averaging(models_dict: Dict[str, DataTree],
                    weights=None,
                    var_name='y_obs',
                    random_seed=None):
    """
    Combine posterior predictive draws across models using model weights.

    Draws are resampled from each model in proportion to its weight
    (az.weight_predictions), which yields the mixture predictive
    distribution. Averaging the draw arrays elementwise would shrink the
    predictive spread and understate uncertainty.

    Parameters
    ----------
    models_dict : dict
        Dictionary mapping model names to DataTree results that contain
        posterior_predictive and observed_data groups
    weights : array-like, optional
        Model weights in the order of models_dict. If None, stacking weights
        from az.compare are used.
    var_name : str
        Name of the predicted variable (default: 'y_obs')
    random_seed : int, optional
        Seed for the weighted resampling

    Returns
    -------
    xarray.DataArray
        Weighted posterior predictive draws for var_name
    np.ndarray
        Model weights used (in the order of models_dict)
    """
    model_names = list(models_dict.keys())

    if weights is None:
        comparison = az.compare(models_dict)
        weights = comparison.loc[model_names, 'weight'].to_numpy()
    else:
        weights = np.asarray(weights, dtype=float)
        weights = weights / weights.sum()  # Normalize

    print("="*70)
    print(" " * 22 + "BAYESIAN MODEL AVERAGING")
    print("="*70)
    print("\nModel weights:")
    for name, weight in zip(model_names, weights):
        print(f"  {name}: {weight:.4f} ({weight*100:.2f}%)")

    missing = [n for n in model_names if 'posterior_predictive' not in models_dict[n]]
    if missing:
        raise ValueError(
            f"Run pm.sample_posterior_predictive(idata, extend_inferencedata=True) first for: {missing}"
        )

    weighted = az.weight_predictions(
        [models_dict[n] for n in model_names], weights=weights, random_seed=random_seed
    )
    averaged = weighted['posterior_predictive'][var_name]

    print("\n✓ Model averaging complete")
    print(f"  Combined predictive draws from {len(model_names)} models")

    return averaged, weights


def cross_validation_comparison(models_dict: Dict[str, DataTree],
                                k=10,
                                verbose=True):
    """
    Perform k-fold cross-validation comparison (conceptual guide).

    Note: This function provides guidance. Full k-fold CV requires
    re-fitting models k times, which should be done in the main script.

    Parameters
    ----------
    models_dict : dict
        Dictionary of model names to DataTree results
    k : int
        Number of folds (default: 10)
    verbose : bool
        Print guidance

    Returns
    -------
    None
    """
    if verbose:
        print("="*70)
        print(" " * 20 + "K-FOLD CROSS-VALIDATION GUIDE")
        print("="*70)
        print(f"\nTo perform {k}-fold CV:")
        print("""
1. Split data into k folds
2. For each fold:
   - Fit each model on the k-1 training folds
   - Compute the pointwise log predictive density on the held-out fold
3. Sum the held-out elpd across folds for each model
4. Compare models on total elpd (higher is better)

Example code (models built with pm.Data('X', ...) and
pm.Normal('y_obs', ..., observed=pm.Data('y', ...), dims='obs_id')):
-------------
import numpy as np
from scipy.special import logsumexp
from sklearn.model_selection import KFold

kf = KFold(n_splits=k, shuffle=True, random_state=42)
cv_elpd = {name: 0.0 for name in models_dict}

for train_idx, test_idx in kf.split(X):
    for name in models_dict:
        with create_model(name, X[train_idx], y[train_idx]) as model:
            idata = pm.sample()
            # Swap in the held-out fold, then score it under the posterior
            pm.set_data({'X': X[test_idx], 'y': y[test_idx]},
                        coords={'obs_id': np.arange(len(test_idx))})
            # extend_inferencedata=False returns an xarray.Dataset of pointwise log-lik
            ll = pm.compute_log_likelihood(idata, extend_inferencedata=False)

        # log mean_s p(y_i | theta_s): logsumexp over draws minus log(S)
        ll_i = ll['y_obs'].stack(sample=('chain', 'draw'))
        n_draws = ll_i.sizes['sample']
        cv_elpd[name] += float((logsumexp(ll_i, axis=ll_i.get_axis_num('sample'))
                                - np.log(n_draws)).sum())

for name, elpd in cv_elpd.items():
    print(f"{name}: elpd_kfold = {elpd:.2f}")
        """)

    print("\nNote: K-fold CV is expensive but robust when PSIS-LOO has high Pareto-k values")
    print("      (ArviZ also offers az.loo_kfold with a SamplingWrapper).")


# Example usage
if __name__ == '__main__':
    print("This script provides model comparison utilities for PyMC.")
    print("\nExample usage:")
    print("""
    import pymc as pm
    from scripts.model_comparison import compare_models, check_loo_reliability

    # Fit multiple models and add the pointwise log-likelihood
    with pm.Model() as model1:
        # ... define model 1 ...
        idata1 = pm.sample()
        pm.compute_log_likelihood(idata1)

    with pm.Model() as model2:
        # ... define model 2 ...
        idata2 = pm.sample()
        pm.compute_log_likelihood(idata2)

    # Compare models (PSIS-LOO; WAIC is not available in ArviZ 1.x)
    models = {'Simple': idata1, 'Complex': idata2}
    comparison = compare_models(models)

    # Check reliability
    reliability = check_loo_reliability(models)

    # Visualize
    plot_model_comparison(comparison, output_path='comparison.png')

    # Model averaging (needs posterior_predictive in each result)
    averaged_pred, weights = model_averaging(models, var_name='y_obs')
    """)
