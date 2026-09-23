---
name: alterlab-cosmic
description: Access the COSMIC catalogue of somatic mutations in cancer to query somatic mutations, the Cancer Gene Census, mutational signatures, and gene fusions (authentication required). Use when curating known cancer driver genes, looking up recurrent somatic mutations in a gene, or interpreting mutational signatures for cancer research and precision oncology. Not for germline pathogenicity calls (use alterlab-clinvar) or interactive cohort visualization like OncoPrints and survival from study data (use alterlab-cbioportal). Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read WebFetch Bash(curl:*) Bash(python:*)
compatibility: Requires a free academic COSMIC account (registration) for data downloads; commercial or clinical use needs a COSMIC licence
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# COSMIC Database

## Overview

COSMIC (Catalogue of Somatic Mutations in Cancer) is the world's largest and most comprehensive database for exploring somatic mutations in human cancer. Access COSMIC's extensive collection of cancer genomics data, including millions of mutations across thousands of cancer types, curated gene lists, mutational signatures, and clinical annotations programmatically.

## When to Use This Skill

This skill should be used when:
- Downloading cancer mutation data from COSMIC
- Accessing the Cancer Gene Census for curated cancer gene lists
- Retrieving mutational signature profiles
- Querying structural variants, copy number alterations, or gene fusions
- Analyzing drug resistance mutations
- Working with cancer cell line genomics data
- Integrating cancer mutation data into bioinformatics pipelines
- Researching specific genes or mutations in cancer contexts

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Germline variant pathogenicity (ACMG/AMP, ClinVar stars) | `alterlab-clinvar` |
| Mutation frequency / OncoPrint / survival in TCGA or MSK cohorts via a keyless API | `alterlab-cbioportal` |
| CRISPR/RNAi gene dependency in cancer cell lines | `alterlab-depmap` |
| Population allele frequencies in non-cancer cohorts | `alterlab-gnomad` |

## Prerequisites

### Account Registration
COSMIC requires authentication for data downloads:
- **Academic users**: Free access with registration at https://cancer.sanger.ac.uk/cosmic/register
- **Commercial users**: A COSMIC commercial licence is required for commercial R&D, products/services, and patient services or clinical reporting — see https://www.cosmickb.org/licensing

### Python Requirements
```bash
uv pip install requests pandas
# pysam is only needed if you read the VCF-format downloads
uv pip install pysam
```

## Quick Start

COSMIC's current download service delivers each product as a `.tar` archive (the
gzipped TSV or VCF plus a README describing every column) at an explicit release path,
e.g. `grch38/cosmic/v104/Cosmic_GenomeScreensMutant_Tsv_v104_GRCh38.tar`. Scripted
downloads are a two-step call: `GET https://cancer.sanger.ac.uk/api/mono/products/v1/downloads/scripted?path=<archive path>&bucket=downloads`
with HTTP Basic auth (email:password) returns JSON with a signed `url`, which you then
fetch without auth. The legacy `/cosmic/file_download/...` endpoint and legacy names such
as `CosmicMutantExport.tsv.gz` or `cancer_gene_census.csv` no longer work for scripts —
the old endpoint now redirects to the login page.

### 1. Basic File Download

Use the `scripts/download_cosmic.py` script to download COSMIC data files:

```python
from scripts.download_cosmic import download_cosmic_file, get_common_file_path

# Cancer Gene Census, current release (v104), GRCh38
download_cosmic_file(
    email="your_email@institution.edu",
    password="your_password",
    filepath=get_common_file_path("gene_census"),
    # = "grch38/cosmic/v104/Cosmic_CancerGeneCensus_Tsv_v104_GRCh38.tar"
)
```

### 2. Command-Line Usage

```bash
# Download using shorthand data type (prompts for the password)
python scripts/download_cosmic.py user@email.com --data-type mutations

# Download a specific archive path
python scripts/download_cosmic.py user@email.com \
    --filepath grch38/cosmic/v104/Cosmic_CancerGeneCensus_Tsv_v104_GRCh38.tar

# GRCh37 and/or a pinned release
python scripts/download_cosmic.py user@email.com \
    --data-type gene_census --assembly GRCh37 --version v103
```

If the scripted endpoint changes, copy the command shown under **Scripted download**
for any file on https://cancer.sanger.ac.uk/cosmic/download/cosmic and set
`COSMIC_SCRIPTED_URL`.

### 3. Working with Downloaded Data

```bash
tar -xf Cosmic_CancerGeneCensus_Tsv_v104_GRCh38.tar   # -> gzipped TSV + README
```

```python
import glob
import pandas as pd

# Column names differ from the legacy exports — check the README in each archive.
gene_census = pd.read_csv(glob.glob("Cosmic_CancerGeneCensus*GRCh38*.tsv.gz")[0], sep="\t")
print(gene_census.columns.tolist())

# VCF products (e.g. VCF/Cosmic_GenomeScreensMutant_Vcf_...) extract to .vcf.gz files
import pysam
vcf = pysam.VariantFile(glob.glob("Cosmic_GenomeScreensMutant*_GRCh38.vcf.gz")[0])
```

## Available Data Types

Every data type downloads through the same `download_cosmic_file(...)` call shown
in Quick Start — only the `filepath` changes. Use the `--data-type` shortcut (CLI)
or `get_common_file_path(...)` (Python) to build the path, or pass the filepath
directly. See `references/cosmic_data_reference.md` for full field descriptions.

| Data type                     | Shortcut               | Archive (`grch38/cosmic/v104/…`, verified 2026-09) |
|-------------------------------|------------------------|---------------------------------------------------|
| Coding mutations, genome-wide screens (WGS/WES) | `mutations` | `Cosmic_GenomeScreensMutant_Tsv_v104_GRCh38.tar` |
| Coding mutations, targeted screens | `targeted_mutations` | `Cosmic_CompleteTargetedScreensMutant_Tsv_v104_GRCh38.tar` |
| Coding mutations (VCF)        | `mutations_vcf`        | `VCF/Cosmic_GenomeScreensMutant_Vcf_v104_GRCh38.tar` |
| Non-coding variants (VCF)     | `non_coding_vcf`       | `VCF/Cosmic_NonCodingVariants_Vcf_v104_GRCh38.tar` |
| Mutations in CGC genes        | `mutation_census`      | `Cosmic_MutantCensus_Tsv_v104_GRCh38.tar`        |
| Cancer Gene Census            | `gene_census`          | `Cosmic_CancerGeneCensus_Tsv_v104_GRCh38.tar`    |
| Resistance mutations          | `resistance_mutations` | `Cosmic_ResistanceMutations_Tsv_v104_GRCh38.tar` |
| Structural variants / breakpoints | `structural_variants` / `breakpoints` | `Cosmic_StructuralVariants_Tsv_…` / `Cosmic_Breakpoints_Tsv_…` |
| Gene fusions                  | `fusion_genes`         | `Cosmic_Fusion_Tsv_v104_GRCh38.tar`              |
| Copy number                   | `copy_number`          | `Cosmic_CompleteCNA_Tsv_v104_GRCh38.tar`         |
| Gene expression               | `gene_expression`      | `Cosmic_CompleteGeneExpression_Tsv_v104_GRCh38.tar` |
| Samples / tumour classification | `sample_info` / `classification` | `Cosmic_Sample_Tsv_…` / `Cosmic_Classification_Tsv_…` |
| Mutational signatures         | `signatures`           | separate site — https://cancer.sanger.ac.uk/signatures/downloads/ |

Notes:
- **Cancer Gene Census** is the expert-curated list of cancer genes; its role-in-cancer
  field splits oncogenes from tumor suppressors (TSG), and Tier 1/2 grades the evidence.
- The old single "all coding mutations" export is now split into genome-wide and
  targeted-screen files; combine both for full coverage.
- **Mutational signatures** (SBS, DBS, ID, CN, SV; current reference set v3.6, May 2026)
  are downloaded from the signatures site, not through the product archives.
- Each product page lists sha256/md5 checksums — verify large downloads.

## Working with COSMIC Data

### Genome Assemblies
COSMIC provides data for two reference genomes:
- **GRCh38** (recommended, current standard)
- **GRCh37** (legacy, for older pipelines)

Specify the assembly in file paths (lower-case directory, upper-case suffix):
```python
# GRCh38 (recommended)
filepath = "grch38/cosmic/v104/Cosmic_GenomeScreensMutant_Tsv_v104_GRCh38.tar"

# GRCh37 (legacy)
filepath = "grch37/cosmic/v104/Cosmic_GenomeScreensMutant_Tsv_v104_GRCh37.tar"
```

### Versioning
- Archive paths carry an explicit release (`v104` = May 2026); the download service
  lists only versioned paths, so pin one — `get_common_file_path()` defaults to the
  current release
- COSMIC ships two releases a year (May and November: v101 2024-11, v102 2025-05,
  v103 2025-11, v104 2026-05); check the
  [release notes](https://cancer.sanger.ac.uk/cosmic/release_notes) before assuming
- For reproducible research, pin the release and record it alongside your results

### File Formats
- **TSV/CSV**: Tab/comma-separated, gzip compressed, read with pandas
- **VCF**: Standard variant format, use with pysam, bcftools, or GATK
- All files include headers describing column contents

### Common Analysis Patterns

Current files use upper-case column names (e.g. `GENE_SYMBOL`, `SAMPLE_NAME`), while
tumour site/histology live in the sample/classification tables linked by COSMIC IDs.
Confirm exact names in each archive's README before filtering. For a one-off slice (one
gene, primary site, or sample) the web **Filtered download** option avoids pulling the
multi-GB files at all.

**Filter mutations by gene**:
```python
import glob
import pandas as pd

# Extracted from Cosmic_GenomeScreensMutant_Tsv_v104_GRCh38.tar (multi-GB)
tsv = glob.glob('Cosmic_GenomeScreensMutant*GRCh38*.tsv.gz')[0]
mutations = pd.read_csv(tsv, sep='\t', low_memory=False)
tp53_mutations = mutations[mutations['GENE_SYMBOL'] == 'TP53']
```

**Identify cancer genes by role** (normalize headers, then look up the role column):
```python
cgc = pd.read_csv(glob.glob('Cosmic_CancerGeneCensus*GRCh38*.tsv.gz')[0], sep='\t')
cgc.columns = cgc.columns.str.upper().str.replace(' ', '_')
role = cgc['ROLE_IN_CANCER'].fillna('')
oncogenes = cgc[role.str.contains('oncogene')]
tumor_suppressors = cgc[role.str.contains('TSG')]
```

**Work with VCF files** (GRCh38 coordinates, bgzip + tabix index required for `fetch`):
```python
import pysam

vcf = pysam.VariantFile(glob.glob('Cosmic_GenomeScreensMutant*GRCh38*.vcf.gz')[0])
for record in vcf.fetch('17', 7668400, 7687500):  # TP53 locus, GRCh38
    print(record.id, record.ref, record.alts, record.info)
```

## Data Reference

For comprehensive information about COSMIC data structure, available files, and field descriptions, see `references/cosmic_data_reference.md`. This reference includes:

- Complete list of available data types and files
- Detailed field descriptions for each file type
- File format specifications
- Common file paths and naming conventions
- Data update schedule and versioning
- Citation information

Use this reference when:
- Exploring what data is available in COSMIC
- Understanding specific field meanings
- Determining the correct file path for a data type
- Planning analysis workflows with COSMIC data

## Helper Functions

The download script includes helper functions for common operations:

### Get Common File Paths
```python
from scripts.download_cosmic import get_common_file_path

# Get path for mutations file
path = get_common_file_path('mutations', genome_assembly='GRCh38')
# Returns: 'grch38/cosmic/v104/Cosmic_GenomeScreensMutant_Tsv_v104_GRCh38.tar'

# Get path for gene census, pinned to an older release
path = get_common_file_path('gene_census', version='v103')
# Returns: 'grch38/cosmic/v103/Cosmic_CancerGeneCensus_Tsv_v103_GRCh38.tar'
```

The accepted `data_type` shortcuts are the ones in the Available Data Types table above
(`signatures` returns `None` — use the signatures download site).

## Troubleshooting

### Authentication Errors
- Verify email and password are correct
- Ensure account is registered at cancer.sanger.ac.uk/cosmic
- Check if commercial license is required for your use case

### File Not Found / HTTP 400
- Verify the archive path against the download page (release, product name, assembly)
- Check that the requested release exists (v101–v104 are listed as of 2026-09)
- Legacy names (`CosmicMutantExport.tsv.gz`, `cancer_gene_census.csv`) and
  `GRCh38/cosmic/latest/...` paths from older tutorials are not in the current service
- Confirm genome assembly (GRCh37 vs GRCh38) is correct

### Large File Downloads
- COSMIC files can be several GB in size
- Ensure sufficient disk space
- Download may take several minutes depending on connection
- The script shows download progress for large files

### Commercial Use
- Commercial R&D, commercial products/services, and patient services or clinical
  reporting require a COSMIC commercial licence: https://www.cosmickb.org/licensing
- Academic (not-for-profit) access is free but requires registration

## Integration with Other Tools

COSMIC data integrates well with:
- **Variant annotation**: VEP, ANNOVAR, SnpEff
- **Signature analysis**: SigProfiler, deconstructSigs, MuSiCa
- **Cancer genomics**: cBioPortal, OncoKB, CIViC
- **Bioinformatics**: Bioconductor, TCGA analysis tools
- **Data science**: pandas, scikit-learn, PyTorch

## Additional Resources

- **COSMIC Website**: https://cancer.sanger.ac.uk/cosmic
- **Documentation**: https://cancer.sanger.ac.uk/cosmic/help
- **Release Notes**: https://cancer.sanger.ac.uk/cosmic/release_notes
- **Download page (products, checksums, scripted-download help)**: https://cancer.sanger.ac.uk/cosmic/download/cosmic
- **Mutational signatures**: https://cancer.sanger.ac.uk/signatures/downloads/
- **Contact**: cosmic@sanger.ac.uk

## Citation

When using COSMIC data, cite the current database paper:
Sondka Z, Dhir NB, Carvalho-Silva D, et al. COSMIC: a curated database of somatic variants and clinical data for cancer. Nucleic Acids Research. 2024;52(D1):D1210-D1217. doi:10.1093/nar/gkad986

