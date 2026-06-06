---
name: alterlab-geo
description: Access NCBI GEO (Gene Expression Omnibus) for gene expression and functional genomics data — search and download microarray and RNA-seq datasets by GSE, GSM, or GPL accession and retrieve SOFT and series matrix files. Use when locating public expression datasets, fetching processed expression matrices, or sourcing transcriptomics data for differential-expression analysis. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read WebFetch Bash(curl:*) Bash(python:*)
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# GEO Database

## Overview

The Gene Expression Omnibus (GEO) is NCBI's public repository for high-throughput gene expression and functional genomics data. GEO contains over 264,000 studies with more than 8 million samples from both array-based and sequence-based experiments.

## When to Use This Skill

Use this skill when searching for gene expression datasets, retrieving experimental data, downloading raw and processed files, querying expression profiles, or integrating GEO data into computational analysis workflows.

## Core Workflow

1. **Search** for relevant studies (E-utilities / `Bio.Entrez`) → see `references/searching.md`.
2. **Retrieve** a series with GEOparse: `GEOparse.get_GEO(geo="GSE...", destdir="./data")` → see `references/geoparse_usage.md`.
3. **Extract** the expression matrix via `gse.pivot_samples('VALUE')` (genes × samples).
4. **Analyze** — QC, differential expression, clustering, meta-analysis → see `references/expression_analysis.md`.

For bulk downloads, skip GEOparse and pull files directly over FTP → see `references/data_access.md`.

## GEO Data Organization

GEO organizes data hierarchically using different accession types:

- **Series (GSE)** — a complete experiment with related samples (e.g. `GSE123456`).
  Largest organizational unit. Holds experimental design, samples, study info.
  Current count: 264,928+ series.
- **Sample (GSM)** — a single experimental sample / biological replicate
  (e.g. `GSM987654`). Linked to platforms and series. 8,068,632+ samples.
- **Platform (GPL)** — the microarray or sequencing platform (e.g. `GPL570`,
  Affymetrix Human Genome U133 Plus 2.0 Array). Shared across experiments.
  27,739+ platforms.
- **DataSet (GDS)** — curated, consistently-formatted collections (e.g. `GDS5678`)
  processed for differential analysis. 4,348 curated datasets. Ideal for quick
  comparative analyses.
- **Profiles** — gene-specific expression data linked to sequence features,
  queryable by gene name, cross-referenced to Entrez Gene.

## Access Methods (routing)

- **GEOparse (recommended)** — easiest series-level access; download, parse
  metadata, extract expression matrices, supplementary files, filter samples.
  → `references/geoparse_usage.md`
- **E-utilities (`Bio.Entrez`)** — metadata searching and batch queries across
  `gds`, `geoprofiles`. Always set `Entrez.email`. → `references/searching.md`
- **Direct FTP / wget / curl** — bulk downloads of series matrix, SOFT, MINiML,
  and supplementary files; no rate limits. → `references/data_access.md`
- **GEO2R web tool** — no-code differential expression analysis in the browser at
  `https://www.ncbi.nlm.nih.gov/geo/geo2r/?acc=GSExxxxx`; generates reproducible
  R scripts. Useful for exploratory analysis before downloading.

## Installation and Setup

```bash
uv pip install GEOparse        # primary GEO access (recommended)
uv pip install biopython       # E-utilities / programmatic NCBI access
uv pip install pandas numpy scipy statsmodels scikit-learn  # analysis
uv pip install matplotlib seaborn                           # visualization
```

Configure NCBI E-utilities access (email is required by NCBI; an API key raises
the rate limit from 3 to 10 requests/second):

```python
from Bio import Entrez

Entrez.email = "your.email@example.com"   # required
# Optional API key — https://www.ncbi.nlm.nih.gov/account/
Entrez.api_key = "your_api_key_here"
```

## Key Concepts

- **SOFT (Simple Omnibus Format in Text):** GEO's primary text format with
  metadata and data tables. Easily parsed by GEOparse.
- **MINiML (MIAME Notation in Markup Language):** XML format for programmatic
  access and data exchange.
- **Series Matrix:** tab-delimited expression matrix (samples as columns,
  genes/probes as rows). Fastest format for getting expression data.
- **MIAME Compliance:** minimum standardized annotation GEO enforces on
  submissions.
- **Expression Value Types:** raw signal, normalized, or log-transformed — always
  check platform and processing methods.
- **Platform Annotation:** maps probe/feature IDs to genes; essential for
  biological interpretation.

## Common Use Cases

- **Transcriptomics research** — download expression data, compare profiles
  across studies, identify DEGs, run meta-analyses.
- **Drug response studies** — analyze post-treatment expression changes, identify
  response biomarkers, build sensitivity models.
- **Disease biology** — disease vs. normal expression, disease signatures,
  patient subgroup/stage comparisons, expression–outcome correlation.
- **Biomarker discovery** — screen diagnostic/prognostic markers, validate across
  cohorts, integrate with clinical data.

## Rate Limiting and Best Practices

- **E-utilities limits:** 3 req/s without an API key, 10 req/s with one. Insert
  delays: `time.sleep(0.34)` (no key) or `time.sleep(0.1)` (with key).
- **FTP:** no rate limits — preferred for bulk downloads (`wget -r` for whole
  directories).
- **GEOparse caching:** files cached in `destdir`; subsequent calls reuse them.
- **Method selection:** GEOparse for series-level access, E-utilities for search /
  batch metadata, FTP for direct/bulk file pulls. Cache locally; always set
  `Entrez.email` with Biopython.

## Important Notes

- **Data quality:** GEO accepts user-submitted data of varying quality. Check
  platform annotation and processing methods, verify metadata and design, watch
  for batch effects, and consider reprocessing raw data.
- **File sizes:** series matrix files can exceed 1 GB; supplementary files (e.g.
  CEL) can be very large. Plan disk space; download incrementally.
- **Citation:** GEO data is free for research. Cite original studies plus the GEO
  database (Barrett et al. 2013, *Nucleic Acids Research*). Check per-dataset
  usage restrictions and follow NCBI guidelines.
- **Common pitfalls:** platforms use different probe IDs (need annotation
  mapping); values may be raw/normalized/log-transformed (check metadata); sample
  metadata is inconsistently formatted; older submissions may lack series matrix
  files; platform annotations may be outdated.

## Reference Index

- `references/searching.md` — E-utilities search (datasets, profiles, advanced
  queries, search→summary→fetch workflow, batch metadata).
- `references/geoparse_usage.md` — GEOparse install/usage, expression matrices,
  supplementary files, sample filtering, caching.
- `references/data_access.md` — direct FTP access (ftplib, wget, curl) and the
  accession-to-path rule.
- `references/expression_analysis.md` — QC/preprocessing, differential expression,
  correlation/clustering, batch processing, cross-study meta-analysis.
- `references/geo_reference.md` — in-depth technical reference: E-utilities API
  endpoints, SOFT/MINiML format docs, FTP directory structure, normalization
  pipelines, platform quirks, and error-handling troubleshooting.

## Additional Resources

- **GEO Website:** https://www.ncbi.nlm.nih.gov/geo/
- **GEO Submission Guidelines:** https://www.ncbi.nlm.nih.gov/geo/info/submission.html
- **GEOparse Documentation:** https://geoparse.readthedocs.io/
- **E-utilities Documentation:** https://www.ncbi.nlm.nih.gov/books/NBK25501/
- **GEO FTP Site:** ftp://ftp.ncbi.nlm.nih.gov/geo/
- **GEO2R Tool:** https://www.ncbi.nlm.nih.gov/geo/geo2r/
- **NCBI API Keys:** https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/
- **Biopython Tutorial:** https://biopython.org/DIST/docs/tutorial/Tutorial.html

## Scripts

`scripts/query_geo.py` — runnable helper for GEO DataSets via NCBI E-utilities (no key; `NCBI_API_KEY` lifts the rate limit):

```bash
python scripts/query_geo.py search "breast cancer AND Homo sapiens[ORGN]" --retmax 5
python scripts/query_geo.py summary 200000001,200000002
```
