# tidal-stress-rnaseq

Analysis code and methods for the (fictional) Tidal Stress RNA-seq project: gill tissue from
*Mytilus* mussels exposed to simulated heat waves at three tidal heights.

| Folder | Contents |
|--------|----------|
| `methods/` | Wet-lab and sequencing methods, including sample decision rules |
| `pipeline/` | Snakemake workflow (alignment, counting, QC reports) |
| `analysis/` | DESeq2 models and figures |

See [`methods/README.md`](methods/README.md) for how samples move from collection to analysis.
