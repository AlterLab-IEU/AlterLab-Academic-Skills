# DepMap Dependency Analysis Guide

## Understanding Chronos Scores

Chronos is the current (v5+) algorithm for computing gene dependency scores from CRISPR screen data. It addresses systematic biases including:
- Copy number effects (high-copy genes appear essential due to DNA cutting)
- Guide RNA efficiency variation
- Cell line growth rates

### Score Interpretation

| Score Range | Interpretation |
|------------|----------------|
| > 0 | Likely growth-promoting when knocked out (some noise) |
| 0 to −0.3 | Non-essential: minimal fitness effect |
| −0.3 to −0.5 | Mild dependency |
| −0.5 to −1.0 | Significant dependency |
| < −1.0 | Strong dependency (common essential range) |
| ≈ −1.0 | Median of pan-essential genes (e.g., proteasome subunits) |

### Common Essential Genes (Controls)

Genes that are essential in nearly all cell lines (score ~−1 to −2):
- Ribosomal proteins: RPL..., RPS...
- Proteasome: PSMA..., PSMB...
- Spliceosome: SNRPD1, SNRNP70
- DNA replication: MCM2, PCNA
- Transcription: POLR2A, TAF...

These can be used as positive controls for screen quality.

### Non-Essential Controls

Genes with negligible fitness effect (score ~ 0):
- Non-expressed genes (tissue-specific)
- Safe harbor loci

## Selectivity Assessment

To determine if a dependency is cancer-selective:

```python
import pandas as pd
import numpy as np

def compute_selectivity(gene_effect_df, cell_info, target_gene, cancer_lineage,
                        id_col="ModelID", lineage_col="OncotreeLineage"):
    """Compute selectivity score for a cancer lineage.

    cell_info: metadata DataFrame (Model.csv). On older releases use
    id_col="DepMap_ID", lineage_col="lineage".
    """
    scores = gene_effect_df[target_gene].dropna()

    scores_df = scores.reset_index()
    scores_df.columns = [id_col, "score"]
    scores_df = scores_df.merge(cell_info[[id_col, lineage_col]])

    cancer_scores = scores_df[scores_df[lineage_col] == cancer_lineage]["score"]
    other_scores = scores_df[scores_df[lineage_col] != cancer_lineage]["score"]

    # Selectivity: lower mean in cancer lineage vs others
    selectivity = other_scores.mean() - cancer_scores.mean()
    return {
        "target_gene": target_gene,
        "cancer_lineage": cancer_lineage,
        "cancer_mean": cancer_scores.mean(),
        "other_mean": other_scores.mean(),
        "selectivity_score": selectivity,
        "n_cancer": len(cancer_scores),
        "fraction_dependent": (cancer_scores < -0.5).mean()
    }
```

## CRISPR Dataset Versions

| Dataset | Description | Recommended |
|---------|-------------|-------------|
| `CRISPRGeneEffect` | Chronos-corrected gene effect | Yes (current) |
| `Achilles_gene_effect` | Older CERES algorithm | Legacy only |
| `RNAi_merged` | DEMETER2 RNAi | For cross-validation |

## Quality Metrics

DepMap reports quality control metrics per screen:
- **Skewness**: Pan-essential genes should show negative skew
- **AUC**: Area under ROC for pan-essential vs non-essential controls

Good screens: skewness < −1, AUC > 0.85

## Cancer Lineage Codes

Current releases annotate lineage in `Model.csv` via `OncotreeLineage` (title-case
Oncotree terms, e.g. `Lung`, `Breast`, `Bowel`, `Skin`, `Myeloid`, `Lymphoid`).
Older releases used a lowercase `lineage` column in `sample_info.csv` (e.g. `lung`,
`breast`, `colorectal`, `leukemia`). The vocabulary and exact spellings differ
between releases — always pull the unique values from the file you downloaded
(`cell_info[lineage_col].unique()`) rather than hard-coding labels.

## Synthetic Lethality Analysis

```python
import pandas as pd
import numpy as np
from scipy import stats

def find_synthetic_lethal(gene_effect_df, mutation_df, biomarker_gene,
                           fdr_threshold=0.1):
    """
    Find synthetic lethal partners for a loss-of-function mutation.

    For each gene, tests if cell lines mutant in biomarker_gene
    are more dependent on that gene vs. WT lines.
    """
    if biomarker_gene not in mutation_df.columns:
        return pd.DataFrame()

    # Get mutant vs WT cell lines
    common = gene_effect_df.index.intersection(mutation_df.index)
    is_mutant = mutation_df.loc[common, biomarker_gene] == 1

    mutant_lines = common[is_mutant]
    wt_lines = common[~is_mutant]

    results = []
    for gene in gene_effect_df.columns:
        mut_scores = gene_effect_df.loc[mutant_lines, gene].dropna()
        wt_scores = gene_effect_df.loc[wt_lines, gene].dropna()

        if len(mut_scores) < 5 or len(wt_scores) < 10:
            continue

        stat, pval = stats.mannwhitneyu(mut_scores, wt_scores, alternative='less')
        results.append({
            "gene": gene,
            "mean_mutant": mut_scores.mean(),
            "mean_wt": wt_scores.mean(),
            "effect_size": wt_scores.mean() - mut_scores.mean(),
            "pval": pval,
            "n_mutant": len(mut_scores),
            "n_wt": len(wt_scores)
        })

    df = pd.DataFrame(results)
    # FDR correction
    from scipy.stats import false_discovery_control
    df["qval"] = false_discovery_control(df["pval"], method="bh")
    df = df[df["qval"] < fdr_threshold].sort_values("effect_size", ascending=False)
    return df
```

## Drug Sensitivity (PRISM)

DepMap also contains compound sensitivity data from the PRISM assay:

```python
import pandas as pd

def load_prism_data(filepath="primary-screen-replicate-collapsed-logfold-change.csv"):
    """
    Load PRISM drug sensitivity data.
    Rows = cell lines, Columns = compounds (broad_id::name::dose)
    Values = log2 fold change (more negative = more sensitive)
    """
    return pd.read_csv(filepath, index_col=0)

# Available datasets:
# primary-screen: 4,518 compounds at single dose
# secondary-screen: ~8,000 compounds at multiple doses (AUC available)
```
