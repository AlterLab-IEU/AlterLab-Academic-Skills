# Seaborn Data Structure, Color Palettes, and Theming

## Data Structure Requirements

### Long-Form Data (preferred)
Each variable is a column, each observation is a row ("tidy" format) — works with all seaborn functions, easy to remap variables to visual properties, supports arbitrary complexity.

```python
# Long-form structure
   subject  condition  measurement
0        1    control         10.5
1        1  treatment         12.3
2        2    control          9.8
3        2  treatment         13.1
```

### Wide-Form Data
Variables spread across columns — useful for simple time series, correlation matrices, heatmaps, and quick array plots.

```python
# Wide-form structure
   control  treatment
0     10.5       12.3
1      9.8       13.1
```

**Converting wide to long:**
```python
df_long = df.melt(var_name='condition', value_name='measurement')
```

## Color Palettes

### Qualitative (categorical data)
`"deep"` (default), `"muted"`, `"pastel"`, `"bright"`, `"dark"`, `"colorblind"` (safe for color-vision deficiency).

```python
sns.set_palette("colorblind")
sns.color_palette("Set2")
```

### Sequential (ordered data)
`"rocket"`, `"mako"` (wide luminance — good for heatmaps); `"flare"`, `"crest"` (restricted luminance — good for points/lines); `"viridis"`, `"magma"`, `"plasma"` (perceptually uniform).

```python
sns.heatmap(data, cmap='rocket')
sns.kdeplot(data=df, x='x', y='y', cmap='mako', fill=True)
```

### Diverging (centered data)
`"vlag"` (blue↔red), `"icefire"` (blue↔orange), `"coolwarm"`, `"Spectral"`.

```python
sns.heatmap(correlation_matrix, cmap='vlag', center=0)
```

### Custom palettes
```python
custom = sns.color_palette("husl", 8)
palette = sns.light_palette("seagreen", as_cmap=True)
palette = sns.diverging_palette(250, 10, as_cmap=True)
```

## Theming and Aesthetics

### set_theme
```python
sns.set_theme(style='whitegrid', palette='pastel', font='sans-serif')
sns.set_theme()  # reset to defaults
```

### Styles
`"darkgrid"` (default), `"whitegrid"`, `"dark"`, `"white"`, `"ticks"`.

```python
sns.set_style("whitegrid")
sns.despine(left=False, bottom=False, offset=10, trim=True)

with sns.axes_style("white"):
    sns.scatterplot(data=df, x='x', y='y')
```

### Contexts
Scale elements for different uses: `"paper"` (default, smallest), `"notebook"`, `"talk"` (slides), `"poster"` (large).

```python
sns.set_context("talk", font_scale=1.2)

with sns.plotting_context("poster"):
    sns.barplot(data=df, x='category', y='value')
```
