# Seaborn Best Practices and Troubleshooting

For longer, scenario-based worked examples (EDA, publication figures, time series, categorical comparisons), see `examples.md`.

## Best Practices

### 1. Data Preparation
Use well-structured DataFrames with meaningful column names:
```python
# Good: Named columns in DataFrame
df = pd.DataFrame({'bill': bills, 'tip': tips, 'day': days})
sns.scatterplot(data=df, x='bill', y='tip', hue='day')

# Avoid: Unnamed arrays (loses axis labels)
sns.scatterplot(x=x_array, y=y_array)
```

### 2. Choose the Right Plot Type
- Continuous x, continuous y: `scatterplot`, `lineplot`, `kdeplot`, `regplot`
- Continuous x, categorical y: `violinplot`, `boxplot`, `stripplot`, `swarmplot`
- One continuous variable: `histplot`, `kdeplot`, `ecdfplot`
- Correlations/matrices: `heatmap`, `clustermap`
- Pairwise relationships: `pairplot`, `jointplot`

### 3. Use Figure-Level Functions for Faceting
```python
sns.relplot(data=df, x='x', y='y', col='category', col_wrap=3)
```

### 4. Leverage Semantic Mappings
```python
sns.scatterplot(data=df, x='x', y='y',
                hue='category',     # Color by category
                size='importance',  # Size by continuous variable
                style='type')       # Marker style by type
```

### 5. Control Statistical Estimation
```python
# Lineplot computes mean and 95% CI by default
sns.lineplot(data=df, x='time', y='value', errorbar='sd')

# Barplot computes mean by default
sns.barplot(data=df, x='category', y='value',
            estimator='median', errorbar=('ci', 95))
```

### 6. Combine with Matplotlib
```python
ax = sns.scatterplot(data=df, x='x', y='y')
ax.set(xlabel='Custom X Label', ylabel='Custom Y Label', title='Custom Title')
ax.axhline(y=0, color='r', linestyle='--')
plt.tight_layout()
```

### 7. Save High-Quality Figures
```python
fig = sns.relplot(data=df, x='x', y='y', col='group')
fig.savefig('figure.png', dpi=300, bbox_inches='tight')
fig.savefig('figure.pdf')  # Vector format for publications
```

## Common Patterns

### Exploratory Data Analysis
```python
sns.pairplot(data=df, hue='target', corner=True)
sns.displot(data=df, x='variable', hue='group',
            kind='kde', fill=True, col='category')
corr = df.corr()
sns.heatmap(corr, annot=True, cmap='coolwarm', center=0)
```

### Publication-Quality Figures
```python
sns.set_theme(style='ticks', context='paper', font_scale=1.1)

g = sns.catplot(data=df, x='treatment', y='response',
                col='cell_line', kind='box', height=3, aspect=1.2)
g.set_axis_labels('Treatment Condition', 'Response (μM)')
g.set_titles('{col_name}')
sns.despine(trim=True)

g.savefig('figure.pdf', dpi=300, bbox_inches='tight')
```

### Complex Multi-Panel Figures
```python
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

sns.scatterplot(data=df, x='x1', y='y', hue='group', ax=axes[0, 0])
sns.histplot(data=df, x='x1', hue='group', ax=axes[0, 1])
sns.violinplot(data=df, x='group', y='y', ax=axes[1, 0])
sns.heatmap(df.pivot_table(values='y', index='x1', columns='x2'),
            ax=axes[1, 1], cmap='viridis')

plt.tight_layout()
```

### Time Series with Confidence Bands
```python
sns.lineplot(data=timeseries, x='date', y='measurement',
             hue='sensor', style='location', errorbar='sd')

g = sns.relplot(data=timeseries, x='date', y='measurement',
                col='location', hue='sensor', kind='line',
                height=4, aspect=1.5, errorbar=('ci', 95))
g.set_axis_labels('Date', 'Measurement (units)')
```

## Troubleshooting

### Legend Outside Plot Area
Figure-level functions place legends outside by default. To move inside:
```python
g = sns.relplot(data=df, x='x', y='y', hue='category')
g._legend.set_bbox_to_anchor((0.9, 0.5))
```

### Overlapping Labels
```python
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
```

### Figure Too Small
```python
# Figure-level
sns.relplot(data=df, x='x', y='y', height=6, aspect=1.5)

# Axes-level
fig, ax = plt.subplots(figsize=(10, 6))
sns.scatterplot(data=df, x='x', y='y', ax=ax)
```

### Colors Not Distinct Enough
```python
sns.set_palette("bright")

palette = sns.color_palette("husl", n_colors=len(df['category'].unique()))
sns.scatterplot(data=df, x='x', y='y', hue='category', palette=palette)
```

### KDE Too Smooth or Jagged
```python
sns.kdeplot(data=df, x='x', bw_adjust=0.5)  # Less smooth
sns.kdeplot(data=df, x='x', bw_adjust=2)    # More smooth
```
