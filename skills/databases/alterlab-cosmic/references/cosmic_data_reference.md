# COSMIC Database Reference

## Overview

COSMIC (Catalogue of Somatic Mutations in Cancer) is the world's largest and most comprehensive resource for exploring the impact of somatic mutations in human cancer. Maintained by the Wellcome Sanger Institute, it catalogs millions of mutations across thousands of cancer types.

**Website**: https://cancer.sanger.ac.uk/cosmic
**Releases**: Two per year (May and November). Current: **v104**, released 2026-05-19 (v103: 2025-11-18). Check the [release notes](https://cancer.sanger.ac.uk/cosmic/release_notes) for newer versions.

## Data Access

### Authentication
- **Academic users**: Free access (registration required)
- **Commercial users**: Commercial licence required (commercial R&D, products/services,
  patient services/clinical reporting) — https://www.cosmickb.org/licensing
- **Registration**: https://cancer.sanger.ac.uk/cosmic/register

### Download Methods
From https://cancer.sanger.ac.uk/cosmic/download/cosmic, pick a release and product and
click the file name; three options appear:
1. **Download in browser** — the whole `.tar` (gzipped TSV/VCF + README of all columns)
2. **Scripted download** — two-step API: `GET https://cancer.sanger.ac.uk/api/mono/products/v1/downloads/scripted?path=<archive path>&bucket=downloads`
   with HTTP Basic auth (email:password) → JSON `{"url": <signed URL>}` → fetch that URL
   without auth. `path` and `bucket` are both required (HTTP 400 otherwise); bad
   credentials give 401. `scripts/download_cosmic.py` implements this.
3. **Filtered download** — a subset by gene symbol, primary site, or sample name

## Available Data Types

### 1. Core Mutation Data
**Main archives** (`grch38/cosmic/v104/…`; legacy names in brackets):
- `Cosmic_GenomeScreensMutant_Tsv_v104_GRCh38.tar` - Coding mutations from genome-wide screens (WGS/WES)
- `Cosmic_CompleteTargetedScreensMutant_Tsv_v104_GRCh38.tar` - Coding mutations from targeted screens
  (together these replace `CosmicMutantExport.tsv.gz`)
- `VCF/Cosmic_GenomeScreensMutant_Vcf_v104_GRCh38.tar` (also `…_VcfNormal_…` normalized) - VCF [`CosmicCodingMuts.vcf.gz`]
- `VCF/Cosmic_NonCodingVariants_Vcf_v104_GRCh38.tar` - Non-coding variants [`CosmicNonCodingVariants.vcf.gz`]
- `Cosmic_MutantCensus_Tsv_v104_GRCh38.tar` - Coding mutations in Cancer Gene Census genes [`CosmicMutantExportCensus.tsv.gz`]

**Content**:
- Point mutations (SNVs)
- Small insertions and deletions (indels)
- Genomic coordinates
- Variant annotations
- Sample information
- Tumor type associations

### 2. Cancer Gene Census
**File**: `Cosmic_CancerGeneCensus_Tsv_v104_GRCh38.tar` [legacy `cancer_gene_census.csv`];
hallmarks in `Cosmic_CancerGeneCensusHallmarksOfCancer_Tsv_v104_GRCh38.tar`

**Content**:
- Expert-curated list of cancer genes
- ~700+ genes with substantial evidence of involvement in cancer
- Gene roles (oncogene, tumor suppressor, fusion)
- Mutation types
- Tissue associations
- Molecular genetics information

### 3. Mutational Signatures
**Where**: https://cancer.sanger.ac.uk/signatures/downloads/ (a separate site; not part of
the product archives above)
- Single Base Substitution (SBS), Doublet Base Substitution (DBS), Insertion/Deletion (ID),
  Copy Number (CN), and Structural Variant (SV) reference signatures
- Matrices per reference genome (GRCh37, GRCh38, mouse builds)

**Current Version**: v3.6 (May 2026)

**Content**:
- Signature profiles (96-channel, 78-channel, 83-channel)
- Etiology annotations
- Reference signatures for signature analysis

### 4. Structural Variants
**Files**: `Cosmic_StructuralVariants_Tsv_v104_GRCh38.tar`, `Cosmic_Breakpoints_Tsv_v104_GRCh38.tar`,
fusions in `Cosmic_Fusion_Tsv_v104_GRCh38.tar` [legacy `CosmicStructExport.tsv.gz`, `CosmicFusionExport.tsv.gz`]

**Content**:
- Gene fusions
- Structural breakpoints
- Translocation events
- Large deletions/insertions
- Complex rearrangements

### 5. Copy Number Variations
**File**: `Cosmic_CompleteCNA_Tsv_v104_GRCh38.tar` [legacy `CosmicCompleteCNA.tsv.gz`]

**Content**:
- Copy number gains and losses
- Amplifications and deletions
- Segment-level data
- Gene-level annotations

### 6. Gene Expression
**File**: `Cosmic_CompleteGeneExpression_Tsv_v104_GRCh38.tar` [legacy `CosmicCompleteGeneExpression.tsv.gz`]

**Content**:
- Over/under-expression data
- Gene expression Z-scores
- Tissue-specific expression patterns

### 7. Resistance Mutations
**File**: `Cosmic_ResistanceMutations_Tsv_v104_GRCh38.tar` [legacy `CosmicResistanceMutations.tsv.gz`]

**Content**:
- Drug resistance mutations
- Treatment associations
- Clinical relevance

### 8. Cell Lines Project
**Files**: Various cell line-specific files

**Content**:
- Mutations in cancer cell lines
- Copy number data for cell lines
- Fusion genes in cell lines
- Microsatellite instability status

### 9. Sample Information
**Files**: `Cosmic_Sample_Tsv_v104_GRCh38.tar`, tumour classification in
`Cosmic_Classification_Tsv_v104_GRCh38.tar` [legacy `CosmicSample.tsv.gz`]

**Content**:
- Sample metadata
- Tumor site/histology
- Sample sources
- Study references

## Genome Assemblies

All genomic data is available for two reference genomes:
- **GRCh37** (hg19) - Legacy assembly
- **GRCh38** (hg38) - Current assembly (recommended)

Archive paths use the pattern: `{assembly lower-case}/cosmic/{version}/[VCF/]Cosmic_{Product}_{Tsv|Vcf|VcfNormal}_{version}_{Assembly}.tar`

## File Formats

### TSV Format
- Delivered inside a `.tar` together with a README that documents every column
- Tab-separated, gzip compressed (.gz), column headers included
- Can be read with pandas, awk, or standard tools

### VCF Format
- Standard Variant Call Format
- Version 4.x specification
- Includes INFO fields with COSMIC annotations
- Gzip compressed and indexed (.vcf.gz, .vcf.gz.tbi)

## Common File Paths

Release v104 (the download service lists only explicit-version paths):

```
# Coding mutations (TSV): genome-wide and targeted screens
grch38/cosmic/v104/Cosmic_GenomeScreensMutant_Tsv_v104_GRCh38.tar
grch38/cosmic/v104/Cosmic_CompleteTargetedScreensMutant_Tsv_v104_GRCh38.tar

# Coding mutations (VCF)
grch38/cosmic/v104/VCF/Cosmic_GenomeScreensMutant_Vcf_v104_GRCh38.tar

# Cancer Gene Census
grch38/cosmic/v104/Cosmic_CancerGeneCensus_Tsv_v104_GRCh38.tar

# Structural variants / fusions / copy number / expression
grch38/cosmic/v104/Cosmic_StructuralVariants_Tsv_v104_GRCh38.tar
grch38/cosmic/v104/Cosmic_Fusion_Tsv_v104_GRCh38.tar
grch38/cosmic/v104/Cosmic_CompleteCNA_Tsv_v104_GRCh38.tar
grch38/cosmic/v104/Cosmic_CompleteGeneExpression_Tsv_v104_GRCh38.tar

# Resistance mutations
grch38/cosmic/v104/Cosmic_ResistanceMutations_Tsv_v104_GRCh38.tar

# Samples and tumour classification
grch38/cosmic/v104/Cosmic_Sample_Tsv_v104_GRCh38.tar
grch38/cosmic/v104/Cosmic_Classification_Tsv_v104_GRCh38.tar
```

## Key Data Fields

> The fields below are described by their meaning. The current TSVs use upper-case
> column names (e.g. `GENE_SYMBOL`, `SAMPLE_NAME`) that differ from the legacy exports
> (e.g. `Gene name`, `Primary site`); read the README bundled with each archive for the
> exact names before writing filters.

### Mutation Data Fields
- **Gene name** - HGNC gene symbol
- **Accession Number** - Transcript identifier
- **COSMIC ID** - Unique mutation identifier
- **CDS mutation** - Coding sequence change
- **AA mutation** - Amino acid change
- **Primary site** - Anatomical tumor location
- **Primary histology** - Tumor type classification
- **Genomic coordinates** - Chromosome, position, strand
- **Mutation type** - Substitution, insertion, deletion, etc.
- **Zygosity** - Heterozygous/homozygous status
- **Pubmed ID** - Literature references

### Cancer Gene Census Fields
- **Gene Symbol** - Official gene name
- **Entrez GeneId** - NCBI gene identifier
- **Role in Cancer** - Oncogene, TSG, fusion
- **Mutation Types** - Types of alterations observed
- **Translocation Partner** - For fusion genes
- **Tier** - Evidence classification (1 or 2)
- **Hallmark** - Cancer hallmark associations
- **Somatic** - Whether somatic mutations are documented
- **Germline** - Whether germline mutations are documented

## Data Updates

COSMIC publishes two releases a year (May and November). Each release includes:
- New mutation data from literature and databases
- Updated Cancer Gene Census annotations
- Revised mutational signatures if applicable
- Enhanced sample annotations

## Citation

When using COSMIC data, cite the current database paper:
Sondka Z, Dhir NB, Carvalho-Silva D, et al. COSMIC: a curated database of somatic variants and clinical data for cancer. Nucleic Acids Research. 2024;52(D1):D1210-D1217. doi:10.1093/nar/gkad986

## Additional Resources

- **Documentation**: https://cancer.sanger.ac.uk/cosmic/help
- **Release Notes**: https://cancer.sanger.ac.uk/cosmic/release_notes
- **Contact**: cosmic@sanger.ac.uk
- **Licensing**: https://www.cosmickb.org/licensing
