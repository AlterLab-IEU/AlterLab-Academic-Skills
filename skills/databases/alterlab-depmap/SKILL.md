---
name: alterlab-depmap
description: Query the Cancer Dependency Map (DepMap) for cancer cell line gene dependency scores (CRISPR Chronos), drug sensitivity data, and gene effect profiles. Use when identifying cancer-specific genetic vulnerabilities, finding synthetic lethal interactions, checking whether a gene is essential in given cell lines, or validating oncology drug targets. Part of the AlterLab Academic Skills suite.
license: CC-BY-4.0
allowed-tools: Read WebFetch Bash(curl:*) Bash(python:*)
compatibility: Keyless DepMap public data downloads/API (no authentication required)
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# DepMap — Cancer Dependency Map

## Overview

The Cancer Dependency Map (DepMap) project, run by the Broad Institute, systematically characterizes genetic dependencies across hundreds of cancer cell lines using genome-wide CRISPR knockout screens (DepMap CRISPR), RNA interference (RNAi), and compound sensitivity assays (PRISM). DepMap data is essential for:
- Identifying which genes are essential for specific cancer types
- Finding cancer-selective dependencies (therapeutic targets)
- Validating oncology drug targets
- Discovering synthetic lethal interactions

**Key resources:**
- DepMap Portal: https://depmap.org/portal/
- DepMap data downloads: https://depmap.org/portal/data_page/
- Figshare deposits (programmatic, keyless): https://api.figshare.com/v2/articles/{article_id}

**Access model — read this first.** DepMap has *no* documented, stable public REST API for gene-level queries (the internal `depmap.org/portal/api/...` paths are undocumented and return 404 for ad-hoc requests — do not script against them). The supported workflow is: download the release matrix CSVs, then analyse them locally with pandas. The keyless programmatic path to those files is the **Figshare API** (`/articles/{id}/files` lists `name` + `download_url`); `scripts/query_depmap.py` wraps this.

## When to Use This Skill

Use DepMap when:

- **Target validation**: Is a gene essential for survival in cancer cell lines with a specific mutation (e.g., KRAS-mutant)?
- **Biomarker discovery**: What genomic features predict sensitivity to knockout of a gene?
- **Synthetic lethality**: Find genes that are selectively essential when another gene is mutated/deleted
- **Drug sensitivity**: What cell line features predict response to a compound?
- **Pan-cancer essentiality**: Is a gene broadly essential across all cancer types (bad target) or selectively essential?
- **Correlation analysis**: Which pairs of genes have correlated dependency profiles (co-essentiality)?

## Core Concepts

### Dependency Scores

| Score | Range | Meaning |
|-------|-------|---------|
| **Chronos** (CRISPR) | ~ -3 to 0+ | More negative = more essential. Common essential threshold: −1. Pan-essential genes ~−1 to −2 |
| **RNAi DEMETER2** | ~ -3 to 0+ | Similar scale to Chronos |
| **Gene Effect** | normalized | Normalized Chronos; −1 = median effect of common essential genes |

**Key thresholds:**
- Chronos ≤ −0.5: likely dependent
- Chronos ≤ −1: strongly dependent (common essential range)

### Cell Line Annotations

Each cell line has:
- `DepMap_ID`: unique identifier (e.g., `ACH-000001`)
- `cell_line_name`: human-readable name
- `primary_disease`: cancer type
- `lineage`: broad tissue lineage
- `lineage_subtype`: specific subtype

## Core Capabilities

### 1. Resolve & Download Release Files (Figshare API, keyless)

Get the file inventory for a release, resolve a file's download URL by name, then stream it to disk. Article IDs: 24Q4 = `27993248`, 24Q2 = `25880521`, 23Q4 = `24667905`. Figshare hosting stopped after 24Q4 — for newer releases (25Q2+) download manually from https://depmap.org/portal/data_page/.

```python
import requests

FIGSHARE = "https://api.figshare.com/v2"

def list_release_files(article_id=27993248):
    """List {name, download_url} for every file in a DepMap release."""
    r = requests.get(f"{FIGSHARE}/articles/{article_id}/files", timeout=60)
    r.raise_for_status()
    return {f["name"]: f["download_url"] for f in r.json()}

def download_depmap_file(name, article_id=27993248, out_path=None):
    """Resolve `name` to its Figshare URL and stream it to disk."""
    url = list_release_files(article_id)[name]   # KeyError if name not in release
    out_path = out_path or name
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 16):
                f.write(chunk)
    return out_path

# download_depmap_file("CRISPRGeneEffect.csv")   # ~430 MB
# CLI equivalent: scripts/query_depmap.py (see end of file)
```

Cell line metadata lives in `Model.csv` (current releases) — older releases used `sample_info.csv`. Column names also drifted across releases (e.g. `primary_disease` -> `OncotreePrimaryDisease`, `lineage` -> `OncotreeLineage`); inspect the header of the version you downloaded rather than assuming.

### 2. Load the Gene Effect Matrix

```python
import pandas as pd

def load_depmap_gene_effect(filepath="CRISPRGeneEffect.csv"):
    """
    Load DepMap CRISPR gene effect matrix.
    Rows = cell lines (DepMap_ID), Columns = genes (Symbol (EntrezID))
    """
    df = pd.read_csv(filepath, index_col=0)
    # Rename columns to gene symbols only
    df.columns = [col.split(" ")[0] for col in df.columns]
    return df

def load_cell_line_info(filepath="Model.csv"):
    """Load cell line metadata (older releases: sample_info.csv)."""
    return pd.read_csv(filepath)
```

### 3. Identifying Selective Dependencies

```python
import numpy as np
import pandas as pd

def find_selective_dependencies(gene_effect_df, cell_line_info, target_gene,
                                 cancer_type=None, threshold=-0.5):
    """Find cell lines selectively dependent on a gene."""

    # Get scores for target gene
    if target_gene not in gene_effect_df.columns:
        return None

    scores = gene_effect_df[target_gene].dropna()
    dependent = scores[scores <= threshold]

    # Add cell line info
    result = pd.DataFrame({
        "DepMap_ID": dependent.index,
        "gene_effect": dependent.values
    }).merge(cell_line_info[["DepMap_ID", "cell_line_name", "primary_disease", "lineage"]])

    if cancer_type:
        result = result[result["primary_disease"].str.contains(cancer_type, case=False, na=False)]

    return result.sort_values("gene_effect")

# Example usage (after loading data; adjust column names to your release header)
# df_effect = load_depmap_gene_effect("CRISPRGeneEffect.csv")
# cell_info = load_cell_line_info("Model.csv")
# deps = find_selective_dependencies(df_effect, cell_info, "KRAS", cancer_type="Lung")
```

### 4. Biomarker Analysis (Gene Effect vs. Mutation)

```python
import pandas as pd
from scipy import stats

def biomarker_analysis(gene_effect_df, mutation_df, target_gene, biomarker_gene):
    """
    Test if mutation in biomarker_gene predicts dependency on target_gene.

    Args:
        gene_effect_df: CRISPR gene effect DataFrame
        mutation_df: Binary mutation DataFrame (1 = mutated)
        target_gene: Gene to assess dependency of
        biomarker_gene: Gene whose mutation may predict dependency
    """
    if target_gene not in gene_effect_df.columns or biomarker_gene not in mutation_df.columns:
        return None

    # Align cell lines
    common_lines = gene_effect_df.index.intersection(mutation_df.index)
    scores = gene_effect_df.loc[common_lines, target_gene].dropna()
    mutations = mutation_df.loc[scores.index, biomarker_gene]

    mutated = scores[mutations == 1]
    wt = scores[mutations == 0]

    stat, pval = stats.mannwhitneyu(mutated, wt, alternative='less')

    return {
        "target_gene": target_gene,
        "biomarker_gene": biomarker_gene,
        "n_mutated": len(mutated),
        "n_wt": len(wt),
        "mean_effect_mutated": mutated.mean(),
        "mean_effect_wt": wt.mean(),
        "pval": pval,
        "significant": pval < 0.05
    }
```

### 5. Co-Essentiality Analysis

```python
import pandas as pd

def co_essentiality(gene_effect_df, target_gene, top_n=20):
    """Find genes with most correlated dependency profiles (co-essential partners)."""
    if target_gene not in gene_effect_df.columns:
        return None

    target_scores = gene_effect_df[target_gene].dropna()

    correlations = {}
    for gene in gene_effect_df.columns:
        if gene == target_gene:
            continue
        other_scores = gene_effect_df[gene].dropna()
        common = target_scores.index.intersection(other_scores.index)
        if len(common) < 50:
            continue
        r = target_scores[common].corr(other_scores[common])
        if not pd.isna(r):
            correlations[gene] = r

    corr_series = pd.Series(correlations).sort_values(ascending=False)
    return corr_series.head(top_n)

# Co-essential genes often share biological complexes or pathways
```

## Query Workflows

### Workflow 1: Target Validation for a Cancer Type

1. Download `CRISPRGeneEffect.csv` and the cell-line metadata file (`Model.csv`, or `sample_info.csv` on older releases)
2. Filter cell lines by cancer type
3. Compute mean gene effect for target gene in cancer vs. all others
4. Calculate selectivity: how specific is the dependency to your cancer type?
5. Cross-reference with mutation, expression, or CNA data as biomarkers

### Workflow 2: Synthetic Lethality Screen

1. Identify cell lines with mutation/deletion in gene of interest (e.g., BRCA1-mutant)
2. Compute gene effect scores for all genes in mutant vs. WT lines
3. Identify genes significantly more essential in mutant lines (synthetic lethal partners)
4. Filter by selectivity and effect size

### Workflow 3: Compound Sensitivity Analysis

1. Download PRISM compound sensitivity data (`primary-screen-replicate-treatment-info.csv`)
2. Correlate compound AUC/log2(fold-change) with genomic features
3. Identify predictive biomarkers for compound sensitivity

## DepMap Data Files Reference

| File | Description |
|------|-------------|
| `CRISPRGeneEffect.csv` | CRISPR Chronos gene effect (primary dependency data) |
| `CRISPRGeneEffectUnscaled.csv` | Unscaled CRISPR scores |
| `RNAi_merged.csv` | DEMETER2 RNAi dependency |
| `Model.csv` | Cell line metadata (lineage, disease, etc.); older releases: `sample_info.csv` |
| `OmicsExpressionProteinCodingGenesTPMLogp1.csv` | mRNA expression |
| `OmicsSomaticMutationsMatrixDamaging.csv` | Damaging somatic mutations (binary) |
| `OmicsCNGene.csv` | Copy number per gene |
| `PRISM_Repurposing_Primary_Screens_Data.csv` | Drug sensitivity (repurposing library) |

File names vary slightly between releases — confirm against the inventory (`query_depmap.py list` or the portal data page) before scripting. Download from https://depmap.org/portal/data_page/ or via the Figshare API (Capability 1).

## Best Practices

- **Use Chronos scores** (not DEMETER2) for current CRISPR analyses — better controlled for cutting efficiency
- **Distinguish pan-essential from cancer-selective**: Target genes with low variance (essential in all lines) are poor drug targets
- **Validate with expression data**: A gene not expressed in a cell line will score as non-essential regardless of actual function
- **Use DepMap ID** for cell line identification — cell_line_name can be ambiguous
- **Account for copy number**: Amplified genes may appear essential due to copy number effect (junk DNA hypothesis)
- **Multiple testing correction**: When computing biomarker associations genome-wide, apply FDR correction

## Additional Resources

- **DepMap Portal**: https://depmap.org/portal/
- **Data downloads**: https://depmap.org/portal/data_page/
- **DepMap paper**: Behan FM et al. (2019) Nature. PMID: 30971826
- **Chronos paper**: Dempster JM et al. (2021) Genome Biology 22(1):343. PMID: 34930405. DOI: 10.1186/s13059-021-02540-7
- **GitHub**: https://github.com/broadinstitute/depmap-portal
- **Figshare**: https://plus.figshare.com/articles/dataset/DepMap_24Q4_Public/27993248

## Scripts

`scripts/query_depmap.py` — keyless helper that lists a DepMap release's files and resolves a file's download URL via the Figshare API (`--article` goes before the subcommand):

```bash
uv run --with requests python scripts/query_depmap.py --article 27993248 list
uv run --with requests python scripts/query_depmap.py --article 27993248 url CRISPRGeneEffect.csv
```
