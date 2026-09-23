"""
PyMC Model Diagnostics Script

Comprehensive diagnostic checks for PyMC models.
Run this after sampling to validate results before interpretation.

Targets PyMC >= 6 / ArviZ >= 1.1: `idata` is the xarray.DataTree returned by
pm.sample() (ArviZ 1.x replaced InferenceData), and ArviZ plots return a
PlotCollection that is saved with pc.savefig(). Works with PyMC's own NUTS
and with nutpie (PyMC 6's default NUTS sampler when installed), whose
sample-stat names differ.

Usage:
    from scripts.model_diagnostics import check_diagnostics, create_diagnostic_report

    # Quick check
    check_diagnostics(idata)

    # Full report with plots
    create_diagnostic_report(idata, var_names=['alpha', 'beta', 'sigma'], output_dir='diagnostics/')
"""

import arviz as az
import matplotlib.pyplot as plt
from pathlib import Path

# Sample-stat names differ between PyMC's NUTS and nutpie.
_MAX_DEPTH_FLAGS = ('reached_max_treedepth', 'maxdepth_reached')
_DEPTH_VARS = ('tree_depth', 'depth')


def _first_present(stats, names):
    return next((name for name in names if name in stats), None)


def check_diagnostics(idata, var_names=None, ess_threshold=400, rhat_threshold=1.01):
    """
    Perform comprehensive diagnostic checks on MCMC samples.

    Parameters
    ----------
    idata : xarray.DataTree
        Result of pm.sample() (arviz.InferenceData in ArviZ < 1)
    var_names : list, optional
        Variables to check. If None, checks all model parameters
    ess_threshold : int
        Minimum acceptable effective sample size (default: 400)
    rhat_threshold : float
        Maximum acceptable R-hat value (default: 1.01)

    Returns
    -------
    dict
        Dictionary with diagnostic results and flags
    """
    print("="*70)
    print(" " * 20 + "MCMC DIAGNOSTICS REPORT")
    print("="*70)

    # Get summary statistics
    summary = az.summary(idata, var_names=var_names)

    results = {
        'summary': summary,
        'has_issues': False,
        'issues': []
    }

    # 1. Check R-hat (convergence)
    print("\n1. CONVERGENCE CHECK (R-hat)")
    print("-" * 70)
    bad_rhat = summary[summary['r_hat'] > rhat_threshold]

    if len(bad_rhat) > 0:
        print(f"⚠️  WARNING: {len(bad_rhat)} parameters have R-hat > {rhat_threshold}")
        print("\nTop 10 worst R-hat values:")
        print(bad_rhat[['r_hat']].sort_values('r_hat', ascending=False).head(10))
        print("\n⚠️  Chains may not have converged!")
        print("   → Run longer chains or check for multimodality")
        results['has_issues'] = True
        results['issues'].append('convergence')
    else:
        print(f"✓ All R-hat values ≤ {rhat_threshold}")
        print("  Chains have converged successfully")

    # 2. Check Effective Sample Size
    print("\n2. EFFECTIVE SAMPLE SIZE (ESS)")
    print("-" * 70)
    low_ess_bulk = summary[summary['ess_bulk'] < ess_threshold]
    low_ess_tail = summary[summary['ess_tail'] < ess_threshold]

    if len(low_ess_bulk) > 0 or len(low_ess_tail) > 0:
        print(f"⚠️  WARNING: Some parameters have ESS < {ess_threshold}")

        if len(low_ess_bulk) > 0:
            print(f"\n   Bulk ESS issues ({len(low_ess_bulk)} parameters):")
            print(low_ess_bulk[['ess_bulk']].sort_values('ess_bulk').head(10))

        if len(low_ess_tail) > 0:
            print(f"\n   Tail ESS issues ({len(low_ess_tail)} parameters):")
            print(low_ess_tail[['ess_tail']].sort_values('ess_tail').head(10))

        print("\n⚠️  High autocorrelation detected!")
        print("   → Sample more draws or reparameterize to reduce correlation")
        results['has_issues'] = True
        results['issues'].append('low_ess')
    else:
        print(f"✓ All ESS values ≥ {ess_threshold}")
        print("  Sufficient effective samples")

    # 3. Check Divergences
    print("\n3. DIVERGENT TRANSITIONS")
    print("-" * 70)
    stats = idata.sample_stats
    divergences = int(stats['diverging'].sum()) if 'diverging' in stats else 0
    total_samples = idata.posterior.sizes['draw'] * idata.posterior.sizes['chain']

    if divergences > 0:
        divergence_rate = divergences / total_samples * 100

        print(f"⚠️  WARNING: {divergences} divergent transitions ({divergence_rate:.2f}% of samples)")
        print("\n   Divergences indicate biased sampling in difficult posterior regions")
        print("   Solutions:")
        print("   → Increase target_accept (e.g., target_accept=0.95 or 0.99)")
        print("   → Use non-centered parameterization for hierarchical models")
        print("   → Add stronger/more informative priors")
        print("   → Check for model misspecification")
        results['has_issues'] = True
        results['issues'].append('divergences')
        results['n_divergences'] = divergences
    else:
        print("✓ No divergences detected")
        print("  NUTS explored the posterior successfully")

    # 4. Check Tree Depth
    print("\n4. TREE DEPTH")
    print("-" * 70)
    flag_var = _first_present(stats, _MAX_DEPTH_FLAGS)
    depth_var = _first_present(stats, _DEPTH_VARS)
    max_tree_depth = int(stats[depth_var].max()) if depth_var else None

    if flag_var:
        hits_max = int(stats[flag_var].sum())
    elif depth_var:
        # Default maximum tree depth is 10 for both PyMC NUTS and nutpie
        hits_max = int((stats[depth_var] >= 10).sum())
    else:
        hits_max = 0  # not a NUTS run (e.g. SMC or Metropolis)

    if hits_max > 0:
        hit_rate = hits_max / total_samples * 100

        print(f"⚠️  WARNING: Hit maximum tree depth {hits_max} times ({hit_rate:.2f}% of samples)")
        print("\n   Model may be difficult to explore efficiently")
        print("   Solutions:")
        print("   → Reparameterize model to improve geometry")
        print("   → Increase max_treedepth (if necessary)")
        results['issues'].append('max_treedepth')
    else:
        print("✓ No maximum tree depth issues")
        if max_tree_depth is not None:
            print(f"  Maximum tree depth reached: {max_tree_depth}")

    # 5. Check Energy (if available)
    if 'energy' in idata.sample_stats:
        print("\n5. ENERGY DIAGNOSTICS")
        print("-" * 70)
        print("✓ Energy statistics available")
        print("  Use az.plot_energy(idata) to visualize energy transitions")
        print("  Good separation indicates healthy HMC sampling")

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    if not results['has_issues']:
        print("✓ All diagnostics passed!")
        print("  Your model has sampled successfully.")
        print("  Proceed with inference and interpretation.")
    else:
        print("⚠️  Some diagnostics failed!")
        print(f"  Issues found: {', '.join(results['issues'])}")
        print("  Review warnings above and consider re-running with adjustments.")

    print("="*70)

    return results


def create_diagnostic_report(idata, var_names=None, output_dir='diagnostics/', show=False):
    """
    Create comprehensive diagnostic report with plots.

    Parameters
    ----------
    idata : xarray.DataTree
        Result of pm.sample() (arviz.InferenceData in ArviZ < 1)
    var_names : list, optional
        Variables to plot. If None, uses all model parameters
    output_dir : str
        Directory to save diagnostic plots
    show : bool
        Whether to display plots (default: False, just save)

    Returns
    -------
    dict
        Diagnostic results from check_diagnostics
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Run diagnostic checks
    results = check_diagnostics(idata, var_names=var_names)

    print(f"\nGenerating diagnostic plots in '{output_dir}'...")

    # ArviZ 1.x plotting functions return a PlotCollection; no ax=/axes= args.
    plots = {
        'trace_plots.png': lambda: az.plot_trace_dist(idata, var_names=var_names),
        'rank_plots.png': lambda: az.plot_rank(idata, var_names=var_names),
        'autocorr_plots.png': lambda: az.plot_autocorr(idata, var_names=var_names),
        'ess_evolution.png': lambda: az.plot_ess_evolution(idata, var_names=var_names),
    }
    if 'energy' in idata.sample_stats:
        plots['energy_plot.png'] = lambda: az.plot_energy(idata)

    for filename, make_plot in plots.items():
        pc = make_plot()
        pc.savefig(output_path / filename)
        print(f"  ✓ Saved {filename}")
        if show:
            pc.show()
        plt.close('all')

    # Save summary to CSV
    results['summary'].to_csv(output_path / 'summary_statistics.csv')
    print(f"  ✓ Saved summary statistics")

    print(f"\nDiagnostic report complete! Files saved in '{output_dir}'")

    return results


def compare_prior_posterior(idata, prior_idata, var_names=None, output_path=None):
    """
    Compare prior and posterior distributions.

    Parameters
    ----------
    idata : xarray.DataTree
        Result of pm.sample() with a posterior group
    prior_idata : xarray.DataTree
        Result of pm.sample_prior_predictive() with a prior group
    var_names : list, optional
        Variables to compare
    output_path : str, optional
        If provided, save plot to this path; otherwise show it

    Returns
    -------
    PlotCollection
    """
    # az.plot_prior_posterior needs both groups in one DataTree; merge a
    # shallow copy so the caller's idata is left unchanged.
    combined = idata.copy()
    combined.update({'prior': prior_idata['prior']})
    pc = az.plot_prior_posterior(combined, var_names=var_names)

    if output_path:
        pc.savefig(output_path)
        print(f"Prior-posterior comparison saved to {output_path}")
    else:
        pc.show()
    return pc


# Example usage
if __name__ == '__main__':
    print("This script provides diagnostic functions for PyMC models.")
    print("\nExample usage:")
    print("""
    import pymc as pm
    from scripts.model_diagnostics import check_diagnostics, create_diagnostic_report

    # After sampling (idata is an xarray.DataTree in PyMC 6 / ArviZ 1.x)
    with pm.Model() as model:
        # ... define model ...
        idata = pm.sample()

    # Quick diagnostic check
    results = check_diagnostics(idata)

    # Full diagnostic report with plots
    create_diagnostic_report(
        idata,
        var_names=['alpha', 'beta', 'sigma'],
        output_dir='my_diagnostics/'
    )
    """)
