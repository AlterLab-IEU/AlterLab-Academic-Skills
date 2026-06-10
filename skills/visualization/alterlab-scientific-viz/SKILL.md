---
name: alterlab-scientific-viz
description: Orchestrates matplotlib, seaborn, and plotly with publication styles to produce journal-ready figures. Use when creating journal-submission figures that need multi-panel layouts, statistical significance annotations, error bars, colorblind-safe palettes, or specific journal formatting (Nature, Science, Cell). For quick statistical exploration use seaborn or plotly directly, for raw low-level plotting use matplotlib. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*)
compatibility: Requires the matplotlib, seaborn, and plotly Python libraries (pip install matplotlib seaborn plotly); no API key or external service needed
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# Scientific Visualization

## Overview

Scientific visualization transforms data into clear, accurate figures for publication. Create journal-ready plots with multi-panel layouts, error bars, significance markers, and colorblind-safe palettes. Export as PDF/EPS/TIFF using matplotlib, seaborn, and plotly for manuscripts.

## When to Use This Skill

This skill should be used when:
- Creating plots or visualizations for scientific manuscripts
- Preparing figures for journal submission (Nature, Science, Cell, PLOS, etc.)
- Ensuring figures are colorblind-friendly and accessible
- Making multi-panel figures with consistent styling
- Exporting figures at correct resolution and format
- Following specific publication guidelines
- Improving existing figures to meet publication standards
- Creating figures that need to work in both color and grayscale

## Quick Start Guide

### Basic Publication-Quality Figure

```python
import matplotlib.pyplot as plt
import numpy as np

# Apply publication style (from scripts/style_presets.py)
from style_presets import apply_publication_style
apply_publication_style('default')

# Create figure with appropriate size (single column = 3.5 inches)
fig, ax = plt.subplots(figsize=(3.5, 2.5))

# Plot data
x = np.linspace(0, 10, 100)
ax.plot(x, np.sin(x), label='sin(x)')
ax.plot(x, np.cos(x), label='cos(x)')

# Proper labeling with units
ax.set_xlabel('Time (seconds)')
ax.set_ylabel('Amplitude (mV)')
ax.legend(frameon=False)

# Remove unnecessary spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Save in publication formats (from scripts/figure_export.py)
from figure_export import save_publication_figure
save_publication_figure(fig, 'figure1', formats=['pdf', 'png'], dpi=300)
```

### Using Pre-configured Styles

Apply journal-specific styles using the matplotlib style files in `assets/`:

```python
import matplotlib.pyplot as plt

# Option 1: Use style file directly
plt.style.use('assets/nature.mplstyle')

# Option 2: Use style_presets.py helper
from style_presets import configure_for_journal
configure_for_journal('nature', figure_width='single')

# Now create figures - they'll automatically match Nature specifications
fig, ax = plt.subplots()
# ... your plotting code ...
```

### Quick Start with Seaborn

For statistical plots, use seaborn with publication styling:

```python
import seaborn as sns
import matplotlib.pyplot as plt
from style_presets import apply_publication_style

# Apply publication style
apply_publication_style('default')
sns.set_theme(style='ticks', context='paper', font_scale=1.1)
sns.set_palette('colorblind')

# Create statistical comparison figure
fig, ax = plt.subplots(figsize=(3.5, 3))
# seaborn >=0.13: pass hue + legend=False to color by category
# (a bare palette= without hue= is deprecated and removed in v0.14)
sns.boxplot(data=df, x='treatment', y='response',
            order=['Control', 'Low', 'High'],
            hue='treatment', palette='Set2', legend=False, ax=ax)
sns.stripplot(data=df, x='treatment', y='response',
              order=['Control', 'Low', 'High'], 
              color='black', alpha=0.3, size=3, ax=ax)
ax.set_ylabel('Response (μM)')
sns.despine()

# Save figure
from figure_export import save_publication_figure
save_publication_figure(fig, 'treatment_comparison', formats=['pdf', 'png'], dpi=300)
```

## Core Principles and Best Practices

### 1. Resolution and File Format

**Critical requirements** (detailed in `references/publication_guidelines.md`):
- **Raster images** (photos, microscopy): 300-600 DPI
- **Line art** (graphs, plots): 600-1200 DPI or vector format
- **Vector formats** (preferred): PDF, EPS, SVG
- **Raster formats**: TIFF, PNG (never JPEG for scientific data)

**Implementation:**
```python
# Use the figure_export.py script for correct settings
from figure_export import save_publication_figure

# Saves in multiple formats with proper DPI
save_publication_figure(fig, 'myfigure', formats=['pdf', 'png'], dpi=300)

# Or save for specific journal requirements
from figure_export import save_for_journal
save_for_journal(fig, 'figure1', journal='nature', figure_type='combination')
```

### 2. Color Selection - Colorblind Accessibility

**Always use colorblind-friendly palettes** (detailed in `references/color_palettes.md`):

**Recommended: Okabe-Ito palette** (distinguishable by all types of color blindness):
```python
# Option 1: Use assets/color_palettes.py
from color_palettes import OKABE_ITO_LIST, apply_palette
apply_palette('okabe_ito')

# Option 2: Manual specification
okabe_ito = ['#E69F00', '#56B4E9', '#009E73', '#F0E442',
             '#0072B2', '#D55E00', '#CC79A7', '#000000']
plt.rcParams['axes.prop_cycle'] = plt.cycler(color=okabe_ito)
```

**For heatmaps/continuous data:**
- Use perceptually uniform colormaps: `viridis`, `plasma`, `cividis`
- Avoid red-green diverging maps (use `PuOr`, `RdBu`, `BrBG` instead)
- Never use `jet` or `rainbow` colormaps

**Always test figures in grayscale** to ensure interpretability.

### 3. Typography and Text

**Font guidelines** (detailed in `references/publication_guidelines.md`):
- Sans-serif fonts: Arial, Helvetica, Calibri
- Minimum sizes at **final print size**:
  - Axis labels: 7-9 pt
  - Tick labels: 6-8 pt
  - Panel labels: 8-12 pt (bold)
- Sentence case for labels: "Time (hours)" not "TIME (HOURS)"
- Always include units in parentheses

**Implementation:**
```python
# Set fonts globally
import matplotlib as mpl
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = ['Arial', 'Helvetica']
mpl.rcParams['font.size'] = 8
mpl.rcParams['axes.labelsize'] = 9
mpl.rcParams['xtick.labelsize'] = 7
mpl.rcParams['ytick.labelsize'] = 7
```

### 4. Figure Dimensions

**Journal-specific widths** (detailed in `references/journal_requirements.md`):
- **Nature**: Single 89 mm, Double 183 mm
- **Science**: Single 55 mm, Double 175 mm
- **Cell**: Single 85 mm, Double 178 mm

**Check figure size compliance:**
```python
from figure_export import check_figure_size

fig = plt.figure(figsize=(3.5, 3))  # 89 mm for Nature
check_figure_size(fig, journal='nature')
```

### 5. Multi-Panel Figures

**Best practices:**
- Label panels with bold letters: **A**, **B**, **C** (uppercase for most journals, lowercase for Nature)
- Maintain consistent styling across all panels
- Align panels along edges where possible
- Use adequate white space between panels

**Example implementation** (see `references/matplotlib_examples.md` for complete code):
```python
from string import ascii_uppercase

fig = plt.figure(figsize=(7, 4))
gs = fig.add_gridspec(2, 2, hspace=0.4, wspace=0.4)

ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])
# ... create other panels ...

# Add panel labels
for i, ax in enumerate([ax1, ax2, ...]):
    ax.text(-0.15, 1.05, ascii_uppercase[i], transform=ax.transAxes,
            fontsize=10, fontweight='bold', va='top')
```

## Common Tasks

Step-by-step recipes — full code for each lives in `references/common_tasks.md` and `references/matplotlib_examples.md`:

1. **Publication-ready line plot** — style, journal size, colorblind colors, error bars, units, despine, vector export.
2. **Multi-panel figure** — `GridSpec` layout, consistent styling, bold panel labels.
3. **Heatmap with proper colormap** — perceptually uniform (`viridis`) or colorblind-safe diverging (`RdBu_r`), labeled colorbar, grayscale test.
4. **Prepare for a specific journal** — `configure_for_journal(...)` then `save_for_journal(...)`.
5. **Fix an existing figure** — run the publication checklist (resolution, format, colors, fonts, labels, size, grayscale, chart junk).
6. **Colorblind-friendly figures** — approved palettes + redundant encoding (line styles, markers) + simulator test.

**Statistical rigor (always):** error bars (SD/SEM/CI — state which in caption), sample size n, significance markers, individual data points where possible.

## Plotting Libraries — when to use which

- **Matplotlib** — most control, best for complex multi-panel figures. Examples: `references/matplotlib_examples.md`.
- **Seaborn** — high-level statistical graphics with automatic CIs and faceting. Full guide: `references/seaborn_in_publications.md`.
- **Plotly** — interactive exploration; export static via `fig.write_image('figure.png', scale=3)` (~300 DPI). See `matplotlib_examples.md` Example 8.

## Resources

### References Directory

**Load these as needed for detailed information:**

- **`publication_guidelines.md`**: Comprehensive best practices
  - Resolution and file format requirements
  - Typography guidelines
  - Layout and composition rules
  - Statistical rigor requirements
  - Complete publication checklist

- **`color_palettes.md`**: Color usage guide
  - Colorblind-friendly palette specifications with RGB values
  - Sequential and diverging colormap recommendations
  - Testing procedures for accessibility
  - Domain-specific palettes (genomics, microscopy)

- **`journal_requirements.md`**: Journal-specific specifications
  - Technical requirements by publisher
  - File format and DPI specifications
  - Figure dimension requirements
  - Quick reference table

- **`matplotlib_examples.md`**: Practical code examples
  - 10 complete working examples
  - Line plots, bar plots, heatmaps, multi-panel figures
  - Journal-specific figure examples
  - Tips for each library (matplotlib, seaborn, plotly)

### Scripts Directory

**Use these helper scripts for automation:**

- **`figure_export.py`**: Export utilities
  - `save_publication_figure()`: Save in multiple formats with correct DPI
  - `save_for_journal()`: Use journal-specific requirements automatically
  - `check_figure_size()`: Verify dimensions meet journal specs
  - Run directly: `python scripts/figure_export.py` for examples

- **`style_presets.py`**: Pre-configured styles
  - `apply_publication_style()`: Apply preset styles (default, nature, science, cell)
  - `set_color_palette()`: Quick palette switching
  - `configure_for_journal()`: One-command journal configuration
  - Run directly: `python scripts/style_presets.py` to see examples

### Assets Directory

**Use these files in figures:**

- **`color_palettes.py`**: Importable color definitions
  - All recommended palettes as Python constants
  - `apply_palette()` helper function
  - Can be imported directly into notebooks/scripts

- **Matplotlib style files**: Use with `plt.style.use()`
  - `publication.mplstyle`: General publication quality
  - `nature.mplstyle`: Nature journal specifications
  - `presentation.mplstyle`: Larger fonts for posters/slides

## Workflow Summary

**Recommended workflow for creating publication figures:**

1. **Plan**: Determine target journal, figure type, and content
2. **Configure**: Apply appropriate style for journal
   ```python
   from style_presets import configure_for_journal
   configure_for_journal('nature', 'single')
   ```
3. **Create**: Build figure with proper labels, colors, statistics
4. **Verify**: Check size, fonts, colors, accessibility
   ```python
   from figure_export import check_figure_size
   check_figure_size(fig, journal='nature')
   ```
5. **Export**: Save in required formats
   ```python
   from figure_export import save_for_journal
   save_for_journal(fig, 'figure1', 'nature', 'combination')
   ```
6. **Review**: View at final size in manuscript context

## Common Pitfalls to Avoid

1. **Font too small**: Text unreadable when printed at final size
2. **JPEG format**: Never use JPEG for graphs/plots (creates artifacts)
3. **Red-green colors**: ~8% of males cannot distinguish
4. **Low resolution**: Pixelated figures in publication
5. **Missing units**: Always label axes with units
6. **3D effects**: Distorts perception, avoid completely
7. **Chart junk**: Remove unnecessary gridlines, decorations
8. **Truncated axes**: Start bar charts at zero unless scientifically justified
9. **Inconsistent styling**: Different fonts/colors across figures in same manuscript
10. **No error bars**: Always show uncertainty

## Final Checklist

Before submitting figures, verify:

- [ ] Resolution meets journal requirements (300+ DPI)
- [ ] File format is correct (vector for plots, TIFF for images)
- [ ] Figure size matches journal specifications
- [ ] All text readable at final size (≥6 pt)
- [ ] Colors are colorblind-friendly
- [ ] Figure works in grayscale
- [ ] All axes labeled with units
- [ ] Error bars present with definition in caption
- [ ] Panel labels present and consistent
- [ ] No chart junk or 3D effects
- [ ] Fonts consistent across all figures
- [ ] Statistical significance clearly marked
- [ ] Legend is clear and complete

Use this skill to ensure scientific figures meet the highest publication standards while remaining accessible to all readers.

