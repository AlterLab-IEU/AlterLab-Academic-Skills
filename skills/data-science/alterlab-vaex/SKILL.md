---
name: alterlab-vaex
description: Out-of-core tabular analytics with Vaex — memory-mapped HDF5/Arrow/Parquet via vaex.open, lazy virtual columns, delayed single-pass aggregations on billion-row tables, binned histograms/heatmaps, and vaex.ml transformers on one machine. Vaex is in minimal-maintenance mode (vaex-core 4.19 from Sep 2025 supports only Python 3.9–3.12 and pandas < 3), so use it to run, fix, or migrate existing Vaex code; for new larger-than-RAM work prefer Polars lazy/streaming queries (alterlab-polars) or Dask (alterlab-dask). Use when a project already depends on Vaex, when opening memory-mapped HDF5/Arrow files, batching aggregations with delay=True, or porting a Vaex pipeline to Polars. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*)
compatibility: No API key required. Runs locally via `uv run python` in a dedicated Python 3.12 (or older) environment; requires vaex 4.19.x, which pins pandas < 3 and has no wheels for Python 3.13+. 2-D plots (`df.viz.heatmap`) also need matplotlib < 3.9.
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# Vaex

## Overview

Vaex is a Python library for lazy, out-of-core DataFrames: it memory-maps HDF5/Arrow files, evaluates expressions lazily, and computes statistics on N-dimensional grids fast enough for interactive work on billions of rows on a single machine.

## Maintenance Status (read first)

Vaex is effectively in minimal-maintenance mode. In the project's "Is Vaex active?" discussion (vaexio/vaex #2363, June 2024), one core developer stated he is no longer involved and the other committed only to "do my best to at least get vaex releases out". Releases have slowed to roughly one per year (vaex-core 4.18 in Oct 2024, 4.19 in Sep 2025), and 4.19 still supports only Python 3.9–3.12 with `pandas<3`; the 2-D matplotlib plots break on matplotlib ≥ 3.9. Practical consequences:

- **Existing Vaex code**: keep it running in a pinned Python 3.12 environment (below), and plan a migration.
- **New projects**: default to Polars (`alterlab-polars`) — `pl.scan_parquet(...)` plus `collect(engine="streaming")` covers most larger-than-RAM aggregation work — or Dask (`alterlab-dask`) for clusters. Recommend Vaex for new work only when its specific strengths (memory-mapped HDF5, fast binned statistics/visualization of huge tables) matter and the user accepts the environment constraints.

## When to Use This Skill

Use this skill when the user wants to:
- Run, debug, or extend an existing Vaex pipeline (`vaex.open`, virtual columns, selections, `vaex.ml`).
- Open memory-mapped HDF5/Arrow files that exceed RAM and compute fast aggregations or binned statistics.
- Batch several aggregations into one pass with `delay=True` / `df.execute()`.
- Convert large CSV to HDF5/Arrow/Parquet, or port a Vaex workflow to Polars.

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| New larger-than-RAM analytics project with no existing Vaex code, or Python 3.13+ / pandas 3 environments | `alterlab-polars` |
| Data fits in memory and the goal is the fastest in-memory groupby/joins | `alterlab-polars` |
| Multi-node cluster execution, task graphs, or a distributed scheduler dashboard | `alterlab-dask` |
| Chunked N-D scientific arrays (not tables) on disk or cloud object stores | `alterlab-zarr` |

## Installation

```bash
# Dedicated environment — vaex 4.19 has no wheels for Python 3.13+ and requires pandas < 3
uv venv --python 3.12 .venv-vaex
uv pip install --python .venv-vaex "vaex==4.19.*"
uv pip install --python .venv-vaex "matplotlib<3.9"   # only if you need df.viz.heatmap
```

## Core Capabilities

Vaex provides six capability areas, each documented in `references/`:

### 1. DataFrames and Data Loading
Open HDF5/Arrow/Parquet/CSV files, convert from pandas/NumPy/Arrow, and inspect structure — `references/core_dataframes.md`.

### 2. Data Processing and Manipulation
Filtering, named selections, virtual columns and expressions, groupby/aggregations, strings, datetimes, and missing data — `references/data_processing.md`.

### 3. Performance and Optimization
Lazy evaluation, `delay=True` batching, materialization, caching, and async execution — `references/performance.md`.

### 4. Data Visualization
Binned histograms and heatmaps of huge tables via the `df.viz` accessor, selections, and widgets — `references/visualization.md`.

### 5. Machine Learning Integration
`vaex.ml` scalers, encoders, PCA, k-means, and scikit-learn/XGBoost/LightGBM/CatBoost wrappers — `references/machine_learning.md`. The booster and scikit-learn wrappers materialize the training features in memory; only the transformers and prediction columns stay lazy.

### 6. I/O Operations
Format recommendations, export strategies, Arrow interop, chunked CSV conversion, and remote data — `references/io_operations.md`.

## Quick Start Pattern

```python
import vaex

# 1. Open or create a DataFrame
df = vaex.open('large_file.hdf5')  # or .arrow, .parquet; CSV is read (and optionally converted)
# OR
df = vaex.from_pandas(pandas_df)

# 2. Explore
print(df)          # first/last rows and column info
df.describe()      # statistical summary

# 3. Virtual columns (no memory overhead)
df['new_column'] = df.x ** 2 + df.y

# 4. Filter
df_filtered = df[df.age > 25]

# 5. Statistics (lazy, computed in passes over the data)
mean_val = df.x.mean()
stats = df.groupby('category').agg({'value': 'sum'})

# 6. Visualize (df.plot1d / df.plot are deprecated aliases of these)
df.viz.histogram(df.x, limits=[0, 100])
df.viz.heatmap(df.x, df.y, limits='99.7%')   # needs matplotlib < 3.9

# 7. Export
df.export_hdf5('output.hdf5')
```

## Best Practices

1. **Use HDF5 or Apache Arrow** for memory-mapped access to large datasets; Parquet is the most portable choice if a Polars migration is likely.
2. **Prefer virtual columns** to materializing data.
3. **Batch operations** with `delay=True` when computing several statistics.
4. **Convert CSV once** to HDF5/Arrow/Parquet rather than re-reading it.
5. **Check memory with `df.byte_size()`** and inspect data with `df.describe()` before optimizing.
6. **Pin the environment** (Python 3.12, `vaex==4.19.*`) and record it with results so analyses stay reproducible.

## Common Patterns

### Pattern: Converting Large CSV to HDF5
```python
import vaex

# convert=True streams the CSV in chunks to an HDF5 file next to it
df = vaex.from_csv('large_file.csv', convert=True, chunk_size=5_000_000)

# Future loads are memory-mapped and near-instant
df = vaex.open('large_file.csv.hdf5')
```

### Pattern: Efficient Aggregations
```python
# delay=True batches several aggregations into ONE pass over the data.
# Each delayed call returns a promise; df.execute() runs them together.
mean_x = df.mean(df.x, delay=True)
std_y = df.std(df.y, delay=True)
sum_z = df.sum(df.z, delay=True)

df.execute()
print(mean_x.get(), std_y.get(), sum_z.get())
```

### Pattern: Virtual Columns for Feature Engineering
```python
# No memory overhead — computed on the fly
df['age_squared'] = df.age ** 2
df['full_name'] = df.first_name + ' ' + df.last_name
df['is_adult'] = df.age >= 18
```

### Pattern: Migrating a Vaex Query to Polars
```python
# Vaex: df = vaex.open('big.parquet'); df['z'] = df.x ** 2 + df.y
#       df[df.x > 0.5].groupby('category').agg({'z': 'mean'})
import polars as pl

result = (
    pl.scan_parquet('big.parquet')                      # lazy, like vaex.open
    .with_columns((pl.col('x') ** 2 + pl.col('y')).alias('z'))   # virtual column
    .filter(pl.col('x') > 0.5)                          # filter
    .group_by('category').agg(pl.col('z').mean())       # groupby/agg
    .collect(engine='streaming')                        # out-of-core execution
)
```
Polars cannot read Vaex's HDF5 layout directly — export once with `df.export_parquet(...)` or `df.export_arrow(...)`. Several `delay=True` statistics become one `select(...)` in a single lazy query. See `alterlab-polars` for the rest of the Polars API.

## Resources

- `references/core_dataframes.md` — DataFrame creation, loading, and basic structure
- `references/data_processing.md` — filtering, expressions, aggregations, and transformations
- `references/performance.md` — optimization strategies and lazy evaluation
- `references/visualization.md` — plotting and interactive visualizations
- `references/machine_learning.md` — ML pipelines and model integration
- `references/io_operations.md` — file formats and data import/export

Part of the AlterLab Academic Skills suite.
