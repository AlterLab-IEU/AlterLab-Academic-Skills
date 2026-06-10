# Analyzing GEO Data

Downstream analysis recipes once expression data is loaded via GEOparse.

## Quality Control and Preprocessing

```python
import GEOparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load dataset
gse = GEOparse.get_GEO(geo="GSE123456", destdir="./data")
expression_df = gse.pivot_samples('VALUE')

# Check for missing values
print(f"Missing values: {expression_df.isnull().sum().sum()}")

# Log transformation (if needed)
if expression_df.min().min() > 0:  # Check if already log-transformed
    if expression_df.max().max() > 100:
        expression_df = np.log2(expression_df + 1)
        print("Applied log2 transformation")

# Distribution plots
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
expression_df.plot.box(ax=plt.gca())
plt.title("Expression Distribution per Sample")
plt.xticks(rotation=90)

plt.subplot(1, 2, 2)
expression_df.mean(axis=1).hist(bins=50)
plt.title("Gene Expression Distribution")
plt.xlabel("Average Expression")

plt.tight_layout()
plt.savefig("geo_qc.png", dpi=300, bbox_inches='tight')
```

## Differential Expression Analysis

```python
import GEOparse
import pandas as pd
import numpy as np
from scipy import stats

gse = GEOparse.get_GEO(geo="GSE123456", destdir="./data")
expression_df = gse.pivot_samples('VALUE')

# IMPORTANT: difference-of-means equals log2 fold change ONLY on log2-scale data.
# Many series matrices are already log2; some (especially RNA-seq counts/linear
# intensities) are not. Check and transform before computing fold changes.
if expression_df.min().min() >= 0 and expression_df.max().max() > 100:
    expression_df = np.log2(expression_df + 1)  # now on log2 scale

# Define sample groups (replace with the real GSM ids for each group)
control_samples = ["GSM1", "GSM2", "GSM3"]
treatment_samples = ["GSM4", "GSM5", "GSM6"]

# Calculate fold changes and p-values
results = []
for gene in expression_df.index:
    control_expr = expression_df.loc[gene, control_samples]
    treatment_expr = expression_df.loc[gene, treatment_samples]

    # log2 fold change = difference of group means on the log2 scale
    fold_change = treatment_expr.mean() - control_expr.mean()
    t_stat, p_value = stats.ttest_ind(treatment_expr, control_expr)

    results.append({
        'gene': gene,
        'log2_fold_change': fold_change,
        'p_value': p_value,
        'control_mean': control_expr.mean(),
        'treatment_mean': treatment_expr.mean()
    })

# Create results DataFrame
de_results = pd.DataFrame(results)

# Multiple testing correction (Benjamini-Hochberg)
from statsmodels.stats.multitest import multipletests
_, de_results['q_value'], _, _ = multipletests(
    de_results['p_value'],
    method='fdr_bh'
)

# Filter significant genes
significant_genes = de_results[
    (de_results['q_value'] < 0.05) &
    (abs(de_results['log2_fold_change']) > 1)
]

print(f"Significant genes: {len(significant_genes)}")
significant_genes.to_csv("de_results.csv", index=False)
```

## Correlation and Clustering Analysis

```python
import GEOparse
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.cluster import hierarchy
from scipy.spatial.distance import pdist

gse = GEOparse.get_GEO(geo="GSE123456", destdir="./data")
expression_df = gse.pivot_samples('VALUE')

# Sample correlation heatmap
sample_corr = expression_df.corr()

plt.figure(figsize=(10, 8))
sns.heatmap(sample_corr, cmap='coolwarm', center=0,
            square=True, linewidths=0.5)
plt.title("Sample Correlation Matrix")
plt.tight_layout()
plt.savefig("sample_correlation.png", dpi=300, bbox_inches='tight')

# Hierarchical clustering
distances = pdist(expression_df.T, metric='correlation')
linkage = hierarchy.linkage(distances, method='average')

plt.figure(figsize=(12, 6))
hierarchy.dendrogram(linkage, labels=expression_df.columns)
plt.title("Hierarchical Clustering of Samples")
plt.xlabel("Samples")
plt.ylabel("Distance")
plt.xticks(rotation=90)
plt.tight_layout()
plt.savefig("sample_clustering.png", dpi=300, bbox_inches='tight')
```

## Batch Processing Multiple Datasets

```python
import GEOparse
import pandas as pd
import os

def batch_download_geo(gse_list, destdir="./geo_data"):
    """Download multiple GEO series"""
    results = {}

    for gse_id in gse_list:
        try:
            print(f"Processing {gse_id}...")
            gse = GEOparse.get_GEO(geo=gse_id, destdir=destdir)

            # Extract key information
            results[gse_id] = {
                'title': gse.metadata.get('title', ['N/A'])[0],
                'organism': gse.metadata.get('organism', ['N/A'])[0],
                'platform': list(gse.gpls.keys())[0] if gse.gpls else 'N/A',
                'num_samples': len(gse.gsms),
                'submission_date': gse.metadata.get('submission_date', ['N/A'])[0]
            }

            # Save expression data
            if hasattr(gse, 'pivot_samples'):
                expr_df = gse.pivot_samples('VALUE')
                expr_df.to_csv(f"{destdir}/{gse_id}_expression.csv")
                results[gse_id]['num_genes'] = len(expr_df)

        except Exception as e:
            print(f"Error processing {gse_id}: {e}")
            results[gse_id] = {'error': str(e)}

    # Save summary
    summary_df = pd.DataFrame(results).T
    summary_df.to_csv(f"{destdir}/batch_summary.csv")

    return results

# Process multiple datasets
gse_list = ["GSE100001", "GSE100002", "GSE100003"]
results = batch_download_geo(gse_list)
```

## Meta-Analysis Across Studies

```python
import GEOparse
import pandas as pd
import numpy as np

def meta_analysis_geo(gse_list, gene_of_interest):
    """Perform meta-analysis of gene expression across studies"""
    results = []

    for gse_id in gse_list:
        try:
            gse = GEOparse.get_GEO(geo=gse_id, destdir="./data")

            # Get platform annotation
            gpl = list(gse.gpls.values())[0]

            # Find gene in platform
            if hasattr(gpl, 'table'):
                gene_probes = gpl.table[
                    gpl.table['Gene Symbol'].str.contains(
                        gene_of_interest,
                        case=False,
                        na=False
                    )
                ]

                if not gene_probes.empty:
                    expr_df = gse.pivot_samples('VALUE')

                    for probe_id in gene_probes['ID']:
                        if probe_id in expr_df.index:
                            expr_values = expr_df.loc[probe_id]

                            results.append({
                                'study': gse_id,
                                'probe': probe_id,
                                'mean_expression': expr_values.mean(),
                                'std_expression': expr_values.std(),
                                'num_samples': len(expr_values)
                            })

        except Exception as e:
            print(f"Error in {gse_id}: {e}")

    return pd.DataFrame(results)

# Meta-analysis for TP53
gse_studies = ["GSE100001", "GSE100002", "GSE100003"]
meta_results = meta_analysis_geo(gse_studies, "TP53")
print(meta_results)
```
