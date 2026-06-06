# Retrieving GEO Data with GEOparse

**GEOparse** is the primary Python library for accessing GEO data.

## Installation

```bash
uv pip install GEOparse
```

## Basic Usage

```python
import GEOparse

# Download and parse a GEO Series
gse = GEOparse.get_GEO(geo="GSE123456", destdir="./data")

# Access series metadata
print(gse.metadata['title'])
print(gse.metadata['summary'])
print(gse.metadata['overall_design'])

# Access sample information
for gsm_name, gsm in gse.gsms.items():
    print(f"Sample: {gsm_name}")
    print(f"  Title: {gsm.metadata['title'][0]}")
    print(f"  Source: {gsm.metadata['source_name_ch1'][0]}")
    print(f"  Characteristics: {gsm.metadata.get('characteristics_ch1', [])}")

# Access platform information
for gpl_name, gpl in gse.gpls.items():
    print(f"Platform: {gpl_name}")
    print(f"  Title: {gpl.metadata['title'][0]}")
    print(f"  Organism: {gpl.metadata['organism'][0]}")
```

## Working with Expression Data

```python
import GEOparse
import pandas as pd

# Get expression data from series
gse = GEOparse.get_GEO(geo="GSE123456", destdir="./data")

# Extract expression matrix
# Method 1: From series matrix file (fastest)
if hasattr(gse, 'pivot_samples'):
    expression_df = gse.pivot_samples('VALUE')
    print(expression_df.shape)  # genes x samples

# Method 2: From individual samples
expression_data = {}
for gsm_name, gsm in gse.gsms.items():
    if hasattr(gsm, 'table'):
        expression_data[gsm_name] = gsm.table['VALUE']

expression_df = pd.DataFrame(expression_data)
print(f"Expression matrix: {expression_df.shape}")
```

## Accessing Supplementary Files

```python
import GEOparse

gse = GEOparse.get_GEO(geo="GSE123456", destdir="./data")

# Download supplementary files
gse.download_supplementary_files(
    directory="./data/GSE123456_suppl",
    download_sra=False  # Set to True to download SRA files
)

# List available supplementary files
for gsm_name, gsm in gse.gsms.items():
    if hasattr(gsm, 'supplementary_files'):
        print(f"Sample {gsm_name}:")
        for file_url in gsm.metadata.get('supplementary_file', []):
            print(f"  {file_url}")
```

## Filtering and Subsetting Data

```python
import GEOparse

gse = GEOparse.get_GEO(geo="GSE123456", destdir="./data")

# Filter samples by metadata
control_samples = [
    gsm_name for gsm_name, gsm in gse.gsms.items()
    if 'control' in gsm.metadata.get('title', [''])[0].lower()
]

treatment_samples = [
    gsm_name for gsm_name, gsm in gse.gsms.items()
    if 'treatment' in gsm.metadata.get('title', [''])[0].lower()
]

print(f"Control samples: {len(control_samples)}")
print(f"Treatment samples: {len(treatment_samples)}")

# Extract subset expression matrix
expression_df = gse.pivot_samples('VALUE')
control_expr = expression_df[control_samples]
treatment_expr = expression_df[treatment_samples]
```

## GEOparse Caching Notes

- GEOparse automatically caches downloaded files in `destdir`.
- Subsequent calls use cached data.
- Clean the cache periodically to save disk space.
