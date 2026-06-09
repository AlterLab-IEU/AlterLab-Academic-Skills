---
name: alterlab-seaborn
description: Builds statistical plots with the seaborn Python library and pandas DataFrame integration, on attractive matplotlib-based defaults. Use for quick exploration of distributions, relationships, and categorical comparisons — box plots, violin plots, swarm/strip plots, KDE/histograms, pair plots, joint plots, regression plots, correlation heatmaps, and faceted small multiples (relplot/displot/catplot/lmplot). For interactive/hover/zoom charts defer to alterlab-plotly; for exact journal/manuscript styling (column widths, point fonts, CMYK, vector export) defer to alterlab-scientific-viz; for low-level custom matplotlib figures defer to alterlab-matplotlib (seaborn integrates with it for fine-tuning). Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*)
compatibility: Requires the seaborn and pandas Python libraries (pip install seaborn pandas); no API key or external service needed
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# Seaborn Statistical Visualization

## Overview

Seaborn is a Python visualization library for creating publication-quality statistical graphics. Use this skill for dataset-oriented plotting, multivariate analysis, automatic statistical estimation, and complex multi-panel figures with minimal code.

## When to Use This Skill

Use seaborn for quick, attractive statistical graphics straight from a pandas DataFrame: distributions, relationships, categorical comparisons, correlation heatmaps, and faceted small multiples. Route elsewhere when the need differs:

- **Interactive charts** (hover, zoom, HTML dashboards) → `alterlab-plotly`
- **Exact journal/manuscript styling** (column widths, point fonts, CMYK, vector export) → `alterlab-scientific-viz`
- **Low-level custom plotting** → `alterlab-matplotlib` (seaborn integrates with it for fine-tuning)

## Design Philosophy

1. **Dataset-oriented** — work directly with DataFrames and named variables, not abstract coordinates.
2. **Semantic mapping** — automatically translate data values into visual properties (color, size, style).
3. **Statistical awareness** — built-in aggregation, error estimation, and confidence intervals.
4. **Aesthetic defaults** — publication-ready themes and palettes out of the box.
5. **Matplotlib integration** — full compatibility with matplotlib customization when needed.

## Quick Start

Examples target **seaborn ≥ 0.13** (verified on 0.13.2). Two API points that bite on this version: pass `palette=` only together with `hue=` (palette-without-hue is deprecated, removed in 0.14), and style error bars via `err_kws={...}` rather than the removed-in-0.15 `errcolor`/`errwidth`/`scale`/`join` keywords.

```python
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

df = sns.load_dataset('tips')
sns.scatterplot(data=df, x='total_bill', y='tip', hue='day')
plt.show()
```

## Core Workflow

1. **Shape the data** as long-form ("tidy") — one column per variable, one row per observation. This works with every seaborn function. Reshape wide data with `df.melt(...)`. See `references/data_palettes_theming.md`.
2. **Pick the plot category** for your variable types (see routing below).
3. **Encode extra dimensions** with `hue`, `size`, `style` semantic mappings.
4. **Choose axes-level vs figure-level**: axes-level (`scatterplot`, `boxplot`, `heatmap`, …) plug into custom matplotlib layouts via `ax=`; figure-level (`relplot`, `displot`, `catplot`, `lmplot`, …) own the whole figure and facet via `col`/`row`.
5. **Theme and save** with `set_theme`/`set_context` and `savefig(dpi=300, bbox_inches='tight')` (PDF for vector).

## Plot Category Routing

Choose the category, then see `references/plotting_functions.md` for parameters and code for each.

| Goal | Category | Key functions |
|------|----------|---------------|
| How variables relate | Relational | `scatterplot`, `lineplot`, `relplot` |
| Spread / shape / density | Distribution | `histplot`, `kdeplot`, `ecdfplot`, `displot`, `jointplot`, `pairplot` |
| Compare across categories | Categorical | `stripplot`, `swarmplot`, `boxplot`, `violinplot`, `barplot`, `pointplot`, `countplot`, `catplot` |
| Linear relationships / residuals | Regression | `regplot`, `lmplot`, `residplot` |
| Matrices / correlations | Matrix | `heatmap`, `clustermap` |
| Custom multi-panel grids | Grids | `FacetGrid`, `PairGrid`, `JointGrid` |

The modern declarative `seaborn.objects` interface (ggplot2-like, composable) is best for complex layered or programmatic plots — see `references/objects_interface.md`.

## Color and Theming (essentials)

- **Qualitative** palettes for categories (`"colorblind"`, `"deep"`, `"muted"`); **sequential** for ordered data (`"rocket"`, `"viridis"`); **diverging** for centered data (`"vlag"`, `"coolwarm"`, with `center=0`).
- `set_theme(style=..., context=..., palette=...)`; styles `whitegrid`/`ticks`/…; contexts `paper`→`talk`→`poster` scale element sizes.

Full palette and theming reference: `references/data_palettes_theming.md`.

## Best Practices (essentials)

- Plot from named DataFrame columns (preserves axis labels); use figure-level functions for faceting; encode extra dimensions with `hue`/`size`/`style`.
- Know what each function estimates: `lineplot`/`barplot` auto-compute mean + CI — override with `errorbar=` and `estimator=`.
- Combine with matplotlib (`ax.set(...)`, `axhline`, `tight_layout`) for fine-tuning; save at `dpi=300`, and PDF for publications.

Full best-practices, common patterns, and troubleshooting (legend placement, overlapping labels, figure sizing, palette distinctness, KDE bandwidth): `references/best_practices_and_troubleshooting.md`.

## Reference Index

- **`references/plotting_functions.md`** — every plot category with parameters and code (relational, distribution, categorical, regression, matrix, multi-plot grids, figure-vs-axes-level).
- **`references/data_palettes_theming.md`** — long/wide data structure, color palettes (qualitative/sequential/diverging/custom), and theming (`set_theme`, styles, contexts).
- **`references/best_practices_and_troubleshooting.md`** — best practices, common patterns (EDA, publication figures, multi-panel, time series), and troubleshooting.
- **`references/function_reference.md`** — comprehensive function signatures, parameters, and examples.
- **`references/objects_interface.md`** — detailed guide to the modern `seaborn.objects` API.
- **`references/examples.md`** — scenario-based worked examples and code patterns.
