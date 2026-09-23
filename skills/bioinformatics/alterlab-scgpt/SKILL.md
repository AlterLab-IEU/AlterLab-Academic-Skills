---
name: alterlab-scgpt
description: Apply the scGPT single-cell foundation model (Cui 2024) to annotate and embed cells — zero-shot and fine-tuned cell-type annotation, gene/cell embeddings, batch integration, and gene-regulatory / perturbation inference from AnnData. Use when annotating cell types with a pretrained foundation model, generating scGPT embeddings, integrating batches with a transformer, or running zero-shot single-cell inference on an h5ad. For probabilistic latent models (scVI/scANVI) prefer alterlab-scvi-tools; for the standard QC→cluster→UMAP→DE pipeline prefer alterlab-scanpy; for the AnnData data structure itself prefer alterlab-anndata; for protein language models prefer alterlab-esm. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*)
compatibility: "Runs scGPT (`bowang-lab/scGPT`; PyPI `scgpt` 0.2.4, unchanged since 2025-03) under `uv run python`. Its old pins (`scvi-tools<1.0`, `scanpy<2.0`, `torchtext`) conflict with a current scverse stack, so use a dedicated environment, not one shared with alterlab-scanpy/alterlab-scvi-tools. Checkpoints (GB-scale) download manually from the repo's Drive links; a CUDA GPU is strongly recommended. I/O is AnnData (`.h5ad`); dispatch heavy fine-tuning via alterlab-remote-compute."
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# scGPT (single-cell foundation model)

## Overview

**scGPT** (Cui et al., *Nature Methods* 2024; `bowang-lab/scGPT`) is a transformer **foundation
model** pretrained on tens of millions of cells. It provides **zero-shot** and fine-tuned
**cell-type annotation**, **gene and cell embeddings**, **batch integration**, and
gene-regulatory / perturbation inference — all operating on **AnnData** (`.h5ad`) objects.

Its niche vs. the existing single-cell skills: scGPT is the *pretrained-transformer* route.
For probabilistic latent-variable models use `alterlab-scvi-tools`; for the conventional
Scanpy analysis pipeline use `alterlab-scanpy`; scGPT complements both.

## When to Use This Skill

Use this skill when the user wants to:
- **Annotate cell types** with a pretrained foundation model (zero-shot or fine-tuned).
- Generate **scGPT embeddings** for cells or genes.
- **Integrate batches** using the transformer's representation.
- Run **zero-shot** inference / transfer to a new dataset without training from scratch.

### Does NOT Trigger

| Scenario | Use instead |
|----------|-------------|
| Probabilistic integration / latent model (scVI, scANVI) | `alterlab-scvi-tools` |
| Standard QC → cluster → UMAP → differential expression | `alterlab-scanpy` |
| Read/write/wrangle the `.h5ad` data structure itself | `alterlab-anndata` |
| RNA velocity | `alterlab-scvelo` |
| Protein (not single-cell) language models | `alterlab-esm` |

## Core Capabilities

### 1. Zero-shot cell embedding & annotation

```python
import scanpy as sc
from scgpt.tasks import embed_data

adata = sc.read_h5ad("cells.h5ad")
adata = embed_data(
    adata,
    model_dir="checkpoints/scGPT_human",   # downloaded checkpoint folder
    gene_col="feature_name",               # column in adata.var holding gene symbols
    batch_size=64,
    device="cuda",
)
# cell embeddings land in adata.obsm["X_scGPT"]
```

`gene_col` must name an `adata.var` column of gene symbols matching the checkpoint's vocabulary
(pass `"index"` to use `var_names`); symbols that miss the vocab are dropped, so check how many
genes survive before trusting the embedding. Set `use_fast_transformer=False` when flash-attn
is not installed. Zero-shot mode maps a new dataset onto scGPT's learned space without training
— fast triage of cell identities. Fine-tuning on labeled reference data improves accuracy on a
specific tissue.

### 2. Embeddings for downstream analysis

Produce cell embeddings (for clustering/visualization) or gene embeddings (for
gene-network/similarity analysis). Feed embeddings back into a Scanpy neighbors/UMAP workflow.

### 3. Batch integration

Use the model representation to integrate across batches/donors, comparable in role to
scVI-based integration but from the pretrained-transformer paradigm.

### 4. Environment, GPU, and dispatch

scGPT's last release is 0.2.4 (March 2025) and its pins have not moved since: it requires
`scvi-tools<1.0` and `scanpy<2.0`, and imports `torchtext`, whose own last release was 0.18.0
in April 2024. That stack will not co-install with a current scverse environment, so give scGPT
its own venv and move data between environments as `.h5ad` files rather than trying to satisfy
both sets of pins at once. Say so plainly when a user expects it to drop into their existing
environment.

Checkpoints (whole-human, continual-pretrained, organ-specific) are downloaded by hand from the
Drive links in the upstream README — there is no `from_pretrained` downloader. The
whole-human model is the default choice; the continual-pretrained one is aimed at zero-shot
cell-embedding tasks.

scGPT needs a GPU for realistic dataset sizes; fine-tuning is heavy. Dispatch fine-tuning /
large inference via `alterlab-remote-compute` (submit → poll → harvest). Keep the AnnData I/O
consistent with `alterlab-anndata`.

Because the model has been static for over a year while the foundation-model field has not,
treat its published benchmarks as a 2024 snapshot: report the checkpoint name and date with any
result, and where annotation accuracy matters, sanity-check the labels against marker-gene
evidence (`alterlab-scanpy`) rather than accepting them unverified.

## Resources

- `references/scgpt_usage.md` — install/pinning, checkpoints, embed/annotate/fine-tune calls,
  scverse integration, and paradigm comparison. Loaded on demand.

Part of the AlterLab Academic Skills suite.
