---
name: alterlab-tiledbvcf
description: Store and query genomic variant data at scale with TileDB-VCF — ingest VCF/BCF into compressed TileDB arrays, add samples incrementally, run fast parallel region/sample queries, and export back to VCF. Use when managing population-genomics variant datasets that are too large for flat VCF, building joint variant stores, or querying thousands of samples by region. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*)
compatibility: "tiledbvcf-py is distributed via the `tiledb` conda channel (not PyPI/conda-forge/bioconda); native osx-arm64 builds exist for Apple Silicon. Local VCF stores work offline. TileDB Cloud features require a TileDB Cloud account and TILEDB_REST_TOKEN."
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# TileDB-VCF

## Overview

TileDB-VCF is a high-performance C++ library with Python and CLI interfaces for efficient storage and retrieval of genomic variant-call data. Built on TileDB's sparse array technology, it enables scalable ingestion of VCF/BCF files, incremental sample addition without expensive merging operations, and efficient parallel queries of variant data stored locally or in the cloud.

## When to Use This Skill

This skill should be used when:
- Building a queryable, compressed variant store from many single-sample VCF/BCF files (cohort/population datasets too large for flat VCF)
- Incrementally adding new samples to an existing store without re-merging
- Querying specific genomic regions across many samples (region/sample-partitioned reads)
- Exporting region/sample subsets back to VCF/BCF for downstream tools
- Working with variant data on cloud storage (S3, Azure, GCS) or TileDB Cloud
- Prototyping or teaching scalable genomics-variant workflows

## Quick Start

### Installation

**Preferred method: conda/mamba from the `tiledb` channel.** `tiledbvcf-py` is NOT on PyPI, conda-forge, or bioconda — it ships from the `tiledb` Anaconda channel, with native `osx-arm64` builds (no Rosetta/`CONDA_SUBDIR` workaround needed on Apple Silicon). Supports Python 3.9–3.12.
```bash
# Native Apple Silicon (osx-arm64) — also works on osx-64 / linux-64
conda create -n tiledb-vcf -c conda-forge -c tiledb \
  python=3.12 tiledbvcf-py=0.40 pandas pyarrow numpy
conda activate tiledb-vcf
```

**Alternative: Docker images** (pulls the CLI/Python interface; latest tag tracks current release)
```bash
docker pull tiledb/tiledbvcf-py     # Python interface
docker pull tiledb/tiledbvcf-cli    # Command-line interface
```

### Basic Examples

**Create and populate a dataset:**
```python
import tiledbvcf

# Create a new dataset
ds = tiledbvcf.Dataset(uri="my_dataset", mode="w",
                      cfg=tiledbvcf.ReadConfig(memory_budget_mb=1024))

# Ingest VCF files (must be single-sample with indexes)
# Requirements:
# - VCFs must be single-sample (not multi-sample)
# - Must have indexes: .csi (bcftools) or .tbi (tabix)
ds.ingest_samples(["sample1.vcf.gz", "sample2.vcf.gz"])
```

**Query variant data:**
```python
# Open existing dataset for reading
ds = tiledbvcf.Dataset(uri="my_dataset", mode="r")

# Query specific regions and samples
df = ds.read(
    attrs=["sample_name", "pos_start", "pos_end", "alleles", "fmt_GT"],
    regions=["chr1:1000000-2000000", "chr2:500000-1500000"],
    samples=["sample1", "sample2", "sample3"]
)
print(df.head())
```

**Export to VCF:**
```python
import os

# Export two VCF samples
ds.export(
    regions=["chr21:8220186-8405573"],
    samples=["HG00101", "HG00097"],
    output_format="v",
    output_dir=os.path.expanduser("~"),
)
```

## Core Capabilities

### 1. Dataset Creation and Ingestion

Create TileDB-VCF datasets and incrementally ingest variant data from multiple VCF/BCF files. This is appropriate for building population genomics databases and cohort studies.

**Requirements:**
- **Single-sample VCFs only**: Multi-sample VCFs are not supported
- **Index files required**: VCF/BCF files must have indexes (.csi or .tbi)

**Common operations:**
- Create new datasets with optimized array schemas
- Ingest single or multiple VCF/BCF files in parallel
- Add new samples incrementally without re-processing existing data
- Configure memory usage and compression settings
- Handle various VCF formats and INFO/FORMAT fields
- Resume interrupted ingestion processes
- Validate data integrity during ingestion


### 2. Efficient Querying and Filtering

Query variant data with high performance across genomic regions, samples, and variant attributes. This is appropriate for association studies, variant discovery, and population analysis.

**Common operations:**
- Query specific genomic regions (single or multiple)
- Filter by sample names or sample groups
- Extract specific variant attributes (position, alleles, genotypes, quality)
- Access INFO and FORMAT fields efficiently
- Combine spatial and attribute-based filtering
- Stream large query results
- Perform aggregations across samples or regions


### 3. Data Export and Interoperability

Export data in various formats for downstream analysis or integration with other genomics tools. This is appropriate for sharing datasets, creating analysis subsets, or feeding other pipelines.

**Common operations:**
- Export to standard VCF/BCF formats
- Generate TSV files with selected fields
- Create sample/region-specific subsets
- Maintain data provenance and metadata
- Lossless data export preserving all annotations
- Compressed output formats
- Streaming exports for large datasets


### 4. Population Genomics Workflows

TileDB-VCF excels at large-scale population genomics analyses requiring efficient access to variant data across many samples and genomic regions.

**Common workflows:**
- Genome-wide association studies (GWAS) data preparation
- Rare variant burden testing
- Population stratification analysis
- Allele frequency calculations across populations
- Quality control across large cohorts
- Variant annotation and filtering
- Cross-population comparative analysis


## Key Concepts

### Array Schema and Data Model

**TileDB-VCF Data Model:**
- Variants stored as sparse arrays with genomic coordinates as dimensions
- Samples stored as attributes allowing efficient sample-specific queries
- INFO and FORMAT fields preserved with original data types
- Automatic compression and chunking for optimal storage

**Schema Configuration:**
```python
# Partition a large read across region/sample space
config = tiledbvcf.ReadConfig(
    memory_budget_mb=2048,        # memory budget in MB
    region_partition=(0, 10),     # (partition_index, num_partitions) over regions
    sample_partition=(0, 4),      # (partition_index, num_partitions) over samples
)
```

### Coordinate Systems and Regions

**Critical:** TileDB-VCF uses **1-based genomic coordinates** following VCF standard:
- Positions are 1-based (first base is position 1)
- Ranges are inclusive on both ends
- Region "chr1:1000-2000" includes positions 1000-2000 (1001 bases total)

**Region specification formats:**
```python
# Single region
regions = ["chr1:1000000-2000000"]

# Multiple regions
regions = ["chr1:1000000-2000000", "chr2:500000-1500000"]

# Whole chromosome
regions = ["chr1"]
```

**Note:** `regions=` strings are always 1-based inclusive — a start <= 0 raises "Regions must be 1-based". There is no implicit BED-style conversion. To use 0-based half-open BED intervals, pass a BED file via `read(bed_file="regions.bed", ...)` instead of the `regions=` list.

### Memory Management

**Performance considerations:**
1. **Set appropriate memory budget** based on available system memory
2. **Use streaming queries** for very large result sets
3. **Partition large ingestions** to avoid memory exhaustion
4. **Configure tile cache** for repeated region access
5. **Use parallel ingestion** for multiple files
6. **Optimize region queries** by combining nearby regions

### Cloud Storage Integration

TileDB-VCF seamlessly works with cloud storage:
```python
# S3 dataset
ds = tiledbvcf.Dataset(uri="s3://bucket/dataset", mode="r")

# Azure Blob Storage
ds = tiledbvcf.Dataset(uri="azure://container/dataset", mode="r")

# Google Cloud Storage
ds = tiledbvcf.Dataset(uri="gcs://bucket/dataset", mode="r")
```

## Common Pitfalls

1. **Memory exhaustion during ingestion:** Use appropriate memory budget and batch processing for large VCF files
2. **Inefficient region queries:** Combine nearby regions instead of many separate queries
3. **Missing sample names:** Ensure sample names in VCF headers match query sample specifications
4. **Coordinate system confusion:** Remember TileDB-VCF uses 1-based coordinates like VCF standard
5. **Large result sets:** Use streaming or pagination for queries returning millions of variants
6. **Cloud permissions:** Ensure proper authentication for cloud storage access
7. **Concurrent access:** Multiple writers to the same dataset can cause corruption—use appropriate locking

## CLI Usage

TileDB-VCF provides a command-line interface with the following subcommands:

**Available Subcommands:**
- `create` - Creates an empty TileDB-VCF dataset
- `store` - Ingests samples into a TileDB-VCF dataset
- `export` - Exports data from a TileDB-VCF dataset
- `list` - Lists all sample names present in a TileDB-VCF dataset
- `stat` - Prints high-level statistics about a TileDB-VCF dataset
- `utils` - Utils for working with a TileDB-VCF dataset
- `version` - Print the version information and exit

```bash
# Create empty dataset
tiledbvcf create --uri my_dataset

# Ingest samples (requires single-sample VCFs with indexes)
tiledbvcf store --uri my_dataset --samples sample1.vcf.gz,sample2.vcf.gz

# Export data
tiledbvcf export --uri my_dataset \
  --regions "chr1:1000000-2000000" \
  --sample-names "sample1,sample2"

# List all samples
tiledbvcf list --uri my_dataset

# Show dataset statistics
tiledbvcf stat --uri my_dataset
```

## Advanced Features

These are methods on the `Dataset` object (open in mode="r"), not top-level `tiledbvcf` functions. There is no `read_allele_frequency` or `sample_qc` function — use the methods below.

### Allele counts / frequencies
```python
ds = tiledbvcf.Dataset(uri="my_dataset", mode="r")

# Internal allele-count (AC) array, returned as a pandas DataFrame
ac_df = ds.read_allele_count(region="chr1:1000000-2000000")

# Apply an allele-frequency filter at read time on a normal read()
df = ds.read(
    attrs=["sample_name", "pos_start", "alleles", "fmt_GT"],
    regions=["chr1:1000000-2000000"],
    set_af_filter="<0.01",  # keep variants with AF below threshold
)
```

### Variant statistics (QC)
```python
# Internal variant-stats array (per-variant aggregate stats) as a DataFrame
stats_df = ds.read_variant_stats(region="chr1:1000000-2000000")
```
Note: `read_allele_count` and `read_variant_stats` require the dataset to have been
ingested with the corresponding internal arrays enabled (the default in recent versions).

### TileDB config passthrough
```python
# Pass raw TileDB Embedded config keys (e.g. cloud creds, cache sizing)
config = tiledbvcf.ReadConfig(
    memory_budget_mb=4096,
    tiledb_config={
        "sm.tile_cache_size": "1000000000",
        "vfs.s3.region": "us-east-1",
    },
)
```


## Resources

- TileDB-VCF GitHub (source, issues, releases): https://github.com/TileDB-Inc/TileDB-VCF
- Population Genomics Guide (Academy): https://cloud.tiledb.com/academy/structure/life-sciences/population-genomics/
- Python API reference: https://tiledb-inc.github.io/TileDB-VCF/documentation/reference/Dataset.html
- TileDB Cloud (managed, distributed): https://cloud.tiledb.com

## Scaling to TileDB-Cloud

When workloads outgrow single-node processing (roughly: > 1000 samples, > 100 GB of VCF, or a need for distributed compute / shared access), the same datasets can be ingested and queried on TileDB Cloud via `tiledb-cloud-py`. The local `tiledbvcf` API stays the same; the cloud package adds distributed orchestration.

**Setup**
```bash
pip install "tiledb-cloud[life-sciences]"   # cloud client with genomics extras
export TILEDB_REST_TOKEN="your_api_token"   # auth is automatic from this env var
```

**Distributed ingest and read.** The cloud VCF entry points live in `tiledb.cloud.vcf`:
- `tiledb.cloud.vcf.ingest(...)` — distributed ingestion into a `tiledb://namespace/dataset` URI
- `tiledb.cloud.vcf.build_read_dag(...)` — builds a distributed read DAG over regions/samples

Exact signatures and resource arguments change between releases, so consult the current Cloud API reference rather than hard-coding them: https://cloud.tiledb.com/academy/structure/life-sciences/population-genomics/api-reference/cloud/

Cloud-hosted datasets are still opened with the normal `tiledbvcf.Dataset` API by passing a `tiledb://` URI plus a `tiledb_config` carrying credentials:
```python
import tiledbvcf

cfg = {"rest.token": "your_api_token"}  # or rely on TILEDB_REST_TOKEN
ds = tiledbvcf.Dataset("tiledb://TileDB-Inc/gvcf-1kg-dragen-v376",
                       mode="r", tiledb_config=cfg)
df = ds.read(
    attrs=["sample_name", "fmt_GT", "fmt_AD", "fmt_DP"],
    regions=["chr13:32396898-32397044", "chr13:32398162-32400268"],
    samples=ds.samples(),
)
```
