# Common Scientific Visualization Tasks

Step-by-step recipes for the most frequent publication-figure tasks. Complete code for each lives in `references/matplotlib_examples.md` (referenced by example number).

## Task 1: Create a Publication-Ready Line Plot

See `references/matplotlib_examples.md` Example 1 for complete code.

**Key steps:**
1. Apply publication style
2. Set appropriate figure size for target journal
3. Use colorblind-friendly colors
4. Add error bars with correct representation (SEM, SD, or CI)
5. Label axes with units
6. Remove unnecessary spines
7. Save in vector format

**Using seaborn for automatic confidence intervals:**
```python
import seaborn as sns
fig, ax = plt.subplots(figsize=(5, 3))
sns.lineplot(data=timeseries, x='time', y='measurement',
             hue='treatment', errorbar=('ci', 95),
             markers=True, ax=ax)
ax.set_xlabel('Time (hours)')
ax.set_ylabel('Measurement (AU)')
sns.despine()
```

## Task 2: Create a Multi-Panel Figure

See `references/matplotlib_examples.md` Example 2 for complete code.

**Key steps:**
1. Use `GridSpec` for flexible layout
2. Ensure consistent styling across panels
3. Add bold panel labels (A, B, C, etc.)
4. Align related panels
5. Verify all text is readable at final size

## Task 3: Create a Heatmap with Proper Colormap

See `references/matplotlib_examples.md` Example 4 for complete code.

**Key steps:**
1. Use perceptually uniform colormap (`viridis`, `plasma`, `cividis`)
2. Include labeled colorbar
3. For diverging data, use colorblind-safe diverging map (`RdBu_r`, `PuOr`)
4. Set appropriate center value for diverging maps
5. Test appearance in grayscale

**Using seaborn for correlation matrices:**
```python
import seaborn as sns
fig, ax = plt.subplots(figsize=(5, 4))
corr = df.corr()
mask = np.triu(np.ones_like(corr, dtype=bool))
sns.heatmap(corr, mask=mask, annot=True, fmt='.2f',
            cmap='RdBu_r', center=0, square=True,
            linewidths=1, cbar_kws={'shrink': 0.8}, ax=ax)
```

## Task 4: Prepare Figure for Specific Journal

**Workflow:**
1. Check journal requirements: `references/journal_requirements.md`
2. Configure matplotlib for journal:
   ```python
   from style_presets import configure_for_journal
   configure_for_journal('nature', figure_width='single')
   ```
3. Create figure (will auto-size correctly)
4. Export with journal specifications:
   ```python
   from figure_export import save_for_journal
   save_for_journal(fig, 'figure1', journal='nature', figure_type='line_art')
   ```

## Task 5: Fix an Existing Figure to Meet Publication Standards

**Checklist approach** (full checklist in `references/publication_guidelines.md`):

1. **Check resolution**: Verify DPI meets journal requirements
2. **Check file format**: Use vector for plots, TIFF/PNG for images
3. **Check colors**: Ensure colorblind-friendly
4. **Check fonts**: Minimum 6-7 pt at final size, sans-serif
5. **Check labels**: All axes labeled with units
6. **Check size**: Matches journal column width
7. **Test grayscale**: Figure interpretable without color
8. **Remove chart junk**: No unnecessary grids, 3D effects, shadows

## Task 6: Create Colorblind-Friendly Visualizations

**Strategy:**
1. Use approved palettes from `assets/color_palettes.py`
2. Add redundant encoding (line styles, markers, patterns)
3. Test with colorblind simulator
4. Ensure grayscale compatibility

**Example:**
```python
from color_palettes import apply_palette
import matplotlib.pyplot as plt

apply_palette('okabe_ito')

# Add redundant encoding beyond color
line_styles = ['-', '--', '-.', ':']
markers = ['o', 's', '^', 'v']

for i, (data, label) in enumerate(datasets):
    plt.plot(x, data, linestyle=line_styles[i % 4],
             marker=markers[i % 4], label=label)
```

## Statistical Rigor

**Always include:**
- Error bars (SD, SEM, or CI — specify which in caption)
- Sample size (n) in figure or caption
- Statistical significance markers (*, **, ***)
- Individual data points when possible (not just summary statistics)

**Example with statistics:**
```python
# Show individual points with summary statistics
ax.scatter(x_jittered, individual_points, alpha=0.4, s=8)
ax.errorbar(x, means, yerr=sems, fmt='o', capsize=3)

# Mark significance
ax.text(1.5, max_y * 1.1, '***', ha='center', fontsize=8)
```

## Library Selection

### Matplotlib
- Most control over publication details
- Best for complex multi-panel figures
- Use provided style files for consistent formatting
- See `references/matplotlib_examples.md` for extensive examples

### Seaborn
- High-level statistical graphics with automatic CIs and faceting
- See `references/seaborn_in_publications.md` for the full guide

### Plotly
- Interactive figures for exploration
- Export static images for publication
- Configure for publication quality:
```python
fig.update_layout(
    font=dict(family='Arial, sans-serif', size=10),
    plot_bgcolor='white',
    # ... see matplotlib_examples.md Example 8
)
fig.write_image('figure.png', scale=3)  # scale=3 gives ~300 DPI
```
