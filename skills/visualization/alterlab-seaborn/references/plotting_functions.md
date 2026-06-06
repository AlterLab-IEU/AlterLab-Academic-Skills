# Seaborn Plotting Functions by Category

Parameters and code for each plot category. For the full function signature catalogue see `function_reference.md`; for the modern declarative API see `objects_interface.md`.

## Plotting Interfaces

### Function Interface (traditional)
Specialized functions organized by visualization type. Each category has **axes-level** functions (plot to a single axes) and **figure-level** functions (manage the entire figure with faceting). Use for quick exploratory analysis, single-purpose visualizations, or when you need a specific plot type.

### Objects Interface (modern)
`seaborn.objects` is a declarative, composable API similar to ggplot2 — chain methods to specify data mappings, marks, transformations, and scales. Use for complex layered visualizations, fine-grained control over transformations, custom plot types, or programmatic generation.

```python
from seaborn import objects as so

(
    so.Plot(data=df, x='total_bill', y='tip')
    .add(so.Dot(), color='day')
    .add(so.Line(), so.PolyFit())
)
```

## Relational Plots (relationships between variables)

`scatterplot()` (individual observations), `lineplot()` (trends; auto-aggregates and computes CI), `relplot()` (figure-level with faceting).

**Key parameters:** `x`, `y`; `hue` (color), `size`, `style` (encodings); `col`, `row` (facets, figure-level only).

```python
# Scatter with multiple semantic mappings
sns.scatterplot(data=df, x='total_bill', y='tip',
                hue='time', size='size', style='sex')

# Line plot with confidence intervals
sns.lineplot(data=timeseries, x='date', y='value', hue='category')

# Faceted relational plot
sns.relplot(data=df, x='total_bill', y='tip',
            col='time', row='sex', hue='smoker', kind='scatter')
```

## Distribution Plots (single and bivariate)

`histplot()`, `kdeplot()`, `ecdfplot()`, `rugplot()`, `displot()` (figure-level), `jointplot()` (bivariate + marginals), `pairplot()` (matrix of pairwise relationships).

**Key parameters:** `x`, `y` (y optional for univariate); `hue`; `stat` ("count", "frequency", "probability", "density"); `bins`/`binwidth`; `bw_adjust` (KDE bandwidth multiplier, higher = smoother); `fill`; `multiple` ("layer", "stack", "dodge", "fill").

```python
# Histogram with density normalization
sns.histplot(data=df, x='total_bill', hue='time',
             stat='density', multiple='stack')

# Bivariate KDE with contours
sns.kdeplot(data=df, x='total_bill', y='tip',
            fill=True, levels=5, thresh=0.1)

# Joint plot with marginals
sns.jointplot(data=df, x='total_bill', y='tip',
              kind='scatter', hue='time')

# Pairwise relationships
sns.pairplot(data=df, hue='species', corner=True)
```

## Categorical Plots (comparisons across categories)

- **Categorical scatterplots:** `stripplot()` (jittered points), `swarmplot()` (non-overlapping beeswarm).
- **Distribution comparisons:** `boxplot()`, `violinplot()` (KDE + quartiles), `boxenplot()` (enhanced for large data).
- **Statistical estimates:** `barplot()` (mean + CI), `pointplot()` (point estimates with lines), `countplot()` (counts).
- **Figure-level:** `catplot()` (set `kind`).

**Key parameters:** `x`, `y` (one typically categorical); `hue`; `order`, `hue_order`; `dodge`; `orient` ("v"/"h"); `kind` for catplot ("strip", "swarm", "box", "violin", "bar", "point").

```python
# Swarm plot showing all points
sns.swarmplot(data=df, x='day', y='total_bill', hue='sex')

# Violin plot with split for comparison
sns.violinplot(data=df, x='day', y='total_bill',
               hue='sex', split=True)

# Bar plot with error bars
sns.barplot(data=df, x='day', y='total_bill',
            hue='sex', estimator='mean', errorbar='ci')

# Faceted categorical plot
sns.catplot(data=df, x='day', y='total_bill',
            col='time', kind='box')
```

## Regression Plots (linear relationships)

`regplot()` (axes-level scatter + fit), `lmplot()` (figure-level with faceting), `residplot()` (residuals for model fit).

**Key parameters:** `x`, `y`; `order` (polynomial); `logistic`; `robust`; `ci` (default 95); `scatter_kws`, `line_kws`.

```python
# Simple linear regression
sns.regplot(data=df, x='total_bill', y='tip')

# Polynomial regression with faceting
sns.lmplot(data=df, x='total_bill', y='tip',
           col='time', order=2, ci=95)

# Check residuals
sns.residplot(data=df, x='total_bill', y='tip')
```

## Matrix Plots (rectangular data)

`heatmap()` (color-encoded matrix with annotations), `clustermap()` (hierarchically clustered heatmap).

**Key parameters:** `data` (2D); `annot`; `fmt` (e.g. ".2f"); `cmap`; `center` (for diverging); `vmin`, `vmax`; `square`; `linewidths`.

```python
# Correlation heatmap
corr = df.corr()
sns.heatmap(corr, annot=True, fmt='.2f',
            cmap='coolwarm', center=0, square=True)

# Clustered heatmap
sns.clustermap(data, cmap='viridis',
               standard_scale=1, figsize=(10, 10))
```

## Multi-Plot Grids

### FacetGrid
Subplots based on categorical variables — usually via figure-level functions, but usable directly for custom plots.

```python
g = sns.FacetGrid(df, col='time', row='sex', hue='smoker')
g.map(sns.scatterplot, 'total_bill', 'tip')
g.add_legend()
```

### PairGrid
Pairwise relationships between all variables.

```python
g = sns.PairGrid(df, hue='species')
g.map_upper(sns.scatterplot)
g.map_lower(sns.kdeplot)
g.map_diag(sns.histplot)
g.add_legend()
```

### JointGrid
Bivariate plot with marginal distributions.

```python
g = sns.JointGrid(data=df, x='total_bill', y='tip')
g.plot_joint(sns.scatterplot)
g.plot_marginals(sns.histplot)
```

## Figure-Level vs Axes-Level Functions

### Axes-level
Plot to a single matplotlib `Axes`; integrate into complex figures; accept `ax=`; return `Axes`. Examples: `scatterplot`, `histplot`, `boxplot`, `regplot`, `heatmap`. Use for custom multi-plot layouts, combining plot types, or matplotlib-level control.

```python
fig, axes = plt.subplots(2, 2, figsize=(10, 10))
sns.scatterplot(data=df, x='x', y='y', ax=axes[0, 0])
sns.histplot(data=df, x='x', ax=axes[0, 1])
sns.boxplot(data=df, x='cat', y='y', ax=axes[1, 0])
sns.kdeplot(data=df, x='x', y='y', ax=axes[1, 1])
```

### Figure-level
Manage the entire figure (all subplots); built-in faceting via `col`/`row`; return `FacetGrid`/`JointGrid`/`PairGrid`; size with `height` and `aspect` (per subplot); cannot be placed in an existing figure. Examples: `relplot`, `displot`, `catplot`, `lmplot`, `jointplot`, `pairplot`. Use for faceted small multiples and consistent multi-panel layouts.

```python
sns.relplot(data=df, x='x', y='y', col='category', row='group',
            hue='type', height=3, aspect=1.2)
```
