---
name: alterlab-zarr
description: Chunked, compressed N-dimensional arrays for cloud storage with Zarr — parallel I/O, S3/GCS integration, and NumPy/Dask/Xarray compatibility. Use when storing or reading large N-D scientific arrays, streaming chunked data to/from cloud object stores, or building large-scale scientific computing pipelines. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*)
compatibility: No API key required. Runs locally via `uv run python`; requires zarr >= 3 (current 3.4 as of 2026-09; zarr >= 3.2 needs Python >= 3.12 and NumPy >= 2). Cloud credentials only needed for S3/GCS object stores.
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# Zarr Python

## Overview

Zarr is a Python library for storing large N-dimensional arrays with chunking and compression. Apply this skill for efficient parallel I/O, cloud-native workflows, and seamless integration with NumPy, Dask, and Xarray. The guidance targets zarr-python 3.x (current 3.4.0), which writes the Zarr v3 format by default.

## When to Use This Skill

Use this skill when the user wants to:
- Create, open, or write chunked and compressed N-D arrays (`zarr.create_array`, groups, attributes).
- Choose chunk shapes, sharding, and codecs (Zstandard, Blosc, Gzip) for an access pattern.
- Put arrays on S3/GCS or other object stores and read slices remotely (consolidated metadata, sharding).
- Convert HDF5/NumPy/NetCDF data to Zarr, or migrate Zarr v2-era code (`compressor=`, `synchronizer=`, `create_dataset`) to v3.

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Parallel or distributed computation over arrays already stored in Zarr (scheduling, out-of-core math) | `alterlab-dask` |
| Exploring an unknown data file and writing a structure/quality report | `alterlab-eda` |
| Single-cell AnnData objects stored as `.h5ad` or AnnData-on-zarr | `alterlab-anndata` |
| Tabular analytics on large CSV/Parquet files | `alterlab-polars` |

## Quick Start

### Installation

```bash
uv pip install zarr
```

Zarr v3 (`zarr>=3`); zarr 3.2+ requires Python 3.12+ and NumPy 2 (the 3.1.x line still supports
Python 3.11). For cloud storage support, install the matching fsspec backend:
```bash
uv pip install s3fs   # For S3
uv pip install gcsfs  # For Google Cloud Storage
```

### Basic Array Creation

```python
import zarr
import numpy as np

# Create a 2D array with chunking and compression
z = zarr.create_array(
    store="data/my_array.zarr",
    shape=(10000, 10000),
    chunks=(1000, 1000),
    dtype="f4"
)

# Write data using NumPy-style indexing
z[:, :] = np.random.random((10000, 10000))

# Read data
data = z[0:100, 0:100]  # Returns NumPy array
```

## Core Workflow

1. **Create or open** an array/group, picking a store appropriate to the environment (local, in-memory, ZIP, S3/GCS).
2. **Choose chunking** aligned to your access pattern (aim for 1-10 MB chunks; rows-first → chunks span columns, and vice versa). This is the single biggest performance lever.
3. **Pick compression** via `compressors=` based on workload — Zstandard (the default), Blosc+LZ4 (fast), Gzip (max ratio); `compressors=None` to disable. Pass Blosc options as strings (`shuffle="shuffle"`, `cname="zstd"`); the `BloscShuffle`/`BloscCname` enums are deprecated since 3.1.
4. **Read/write** with NumPy-style indexing; resize/append as data grows.
5. **Scale out** with Dask (lazy, out-of-core, parallel) or label with Xarray for climate/geospatial data.
6. **For cloud and many-array stores**, consolidate metadata and consider sharding to cut object/file count. Consolidated metadata is a zarr-python convention, not yet part of the v3 spec (zarr warns), so other readers may ignore it.

```python
# Minimal end-to-end
import zarr, numpy as np
z = zarr.create_array(store="data/my_array.zarr", shape=(10000, 10000),
                      chunks=(1000, 1000), dtype="f4")
z[:, :] = np.random.random((10000, 10000))
sub = z[0:100, 0:100]            # returns a NumPy array
```

## Routing — where to look

| You need… | Go to |
|-----------|-------|
| Array create/open, read/write, resize/append, attributes, groups & hierarchies, consolidated metadata | `references/array_operations.md` |
| Chunk-size guidelines, aligning chunks to access patterns, sharding, compression codecs & tips | `references/chunking_compression.md` |
| Local / in-memory / ZIP / S3 / GCS stores and cloud best practices | `references/storage_backends.md` |
| NumPy / Dask / Xarray integration, thread- and process-safe parallel writes | `references/integration.md` |
| Performance checklist, profiling, common patterns (time series, large matrices, cloud-native, format conversion), troubleshooting | `references/patterns_performance.md` |
| Full API surface | `references/api_reference.md` |

## Additional Resources

- **Official Documentation**: https://zarr.readthedocs.io/
- **Zarr Specifications**: https://zarr-specs.readthedocs.io/
- **GitHub Repository**: https://github.com/zarr-developers/zarr-python
- **Related**: Xarray (labeled arrays), Dask (parallel computing), NumCodecs (compression codecs)

Part of the AlterLab Academic Skills suite.

