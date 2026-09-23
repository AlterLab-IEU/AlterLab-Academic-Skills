# scGPT — Usage Reference

Deeper detail for `alterlab-scgpt`. API and packaging below were checked against the upstream
`bowang-lab/scGPT` repo (2026-09); PyPI `scgpt` is still 0.2.4 (March 2025).

## Install

```bash
# dedicated environment — scgpt's pins conflict with a current scverse stack
uv venv .venv-scgpt && source .venv-scgpt/bin/activate
uv pip install scgpt "flash-attn<1.0.5"   # flash-attn optional; needs CUDA to build
```

Upstream also documents `"orbax<0.1.8"` as a workaround for resolver failures. Poetry
installation is documented as out of sync — use pip/uv.

Then download a checkpoint folder (whole-human, continual-pretrained, or organ-specific) from
the Drive links in the upstream README; each folder ships the paired gene-name→id vocabulary.
A GPU is strongly recommended.

## Zero-shot embedding API

```python
from scgpt.tasks import embed_data

adata = embed_data(
    adata_or_file,            # AnnData or path to .h5ad
    model_dir="checkpoints/scGPT_human",
    gene_col="feature_name",  # or "index" to use var_names
    max_length=1200,          # genes per cell fed to the transformer
    batch_size=64,
    obs_to_save=["celltype"], # obs columns to carry through
    device="cuda",
    use_fast_transformer=True,  # False when flash-attn is absent
    return_new_adata=False,     # False: writes adata.obsm["X_scGPT"] in place
)
```

`scgpt.tasks` also exposes `get_batch_cell_embeddings` (the lower-level batched call) and
`GeneEmbedding` (gene-embedding / GRN work).

## Typical tasks

- **Zero-shot annotation** — embed a query dataset with a pretrained checkpoint and transfer
  labels from a reference. Fast, no training.
- **Fine-tuned annotation** — fine-tune on a labeled reference for a specific tissue for higher
  accuracy (GPU-heavy — dispatch via `alterlab-remote-compute`).
- **Embeddings** — export cell/gene embeddings for clustering, UMAP, or gene-network analysis.
- **Integration** — use the model representation to integrate batches/donors.

Annotation and perturbation fine-tuning are driven by the scripts and notebooks in the repo's
`examples/` and `tutorials/` directories (e.g. `examples/finetune_integration.py`), not by a
stable importable API — read the notebook matching your task rather than assuming a function
name.

## scverse integration

Inputs and outputs are AnnData (`.h5ad`). Keep the object well-formed with `alterlab-anndata`,
and feed scGPT embeddings into a Scanpy neighbors/UMAP/Leiden workflow (`alterlab-scanpy`) for
downstream steps.

## Choosing the single-cell skill

| Goal | Skill |
|------|-------|
| Pretrained foundation-model annotation/embeddings | `alterlab-scgpt` |
| Probabilistic latent model (scVI/scANVI), integration, DE | `alterlab-scvi-tools` |
| Standard pipeline: QC, clustering, UMAP, marker DE | `alterlab-scanpy` |
| `.h5ad` data structure I/O and wrangling | `alterlab-anndata` |
| RNA velocity | `alterlab-scvelo` |
