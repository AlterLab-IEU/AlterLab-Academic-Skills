---
name: alterlab-boltz
description: Co-fold biomolecular complexes with Boltz-2, an open AlphaFold3-style model — predict protein + ligand (SMILES/CCD), protein + nucleic-acid, and multi-chain structures in one pass, with binding-affinity prediction. Use when folding a protein together with a small-molecule ligand, predicting a holo (ligand-bound) complex or its binding affinity, or co-folding protein–DNA/RNA assemblies. For protein-only or protein–protein folding without ligands prefer alterlab-alphafold; for antibody–antigen complexes prefer alterlab-chai; to dock a ligand into a FIXED receptor structure prefer alterlab-diffdock; to look up an existing structure prefer alterlab-pdb. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*)
compatibility: "Runs the Boltz-2 model (`jwohlwend/boltz`; `uv pip install 'boltz[cuda]'`, 2.2.1 as of 2026-09, Python 3.10–3.12) under `uv run python`. A CUDA GPU is strongly recommended — CPU works but is far slower; model weights download once and cache under `~/.boltz` (override with `BOLTZ_CACHE`). Inputs are a YAML spec listing chains + ligands (SMILES/CCD); FASTA input is deprecated. Code and weights are MIT-licensed. Dispatch heavy runs via alterlab-remote-compute."
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# Boltz-2 (open AlphaFold3-style co-folding)

## Overview

**Boltz-2** (Passaro, Wohlwend et al. 2025; `jwohlwend/boltz`) is an open, commercially usable
biomolecular structure model in the AlphaFold3 family: it **co-folds** proteins together with
small-molecule **ligands**, nucleic acids, and multiple chains in a single prediction, and can
predict **binding affinity** — capabilities AlphaFold2/ColabFold does not have. Use it when the
biology is a *complex with a ligand or other molecule types*, not a bare protein.

## When to Use This Skill

Use this skill when the user wants to:
- Co-fold a protein **with a small-molecule ligand** (SMILES or CCD code) into a holo complex.
- Predict a **binding affinity** alongside a co-folded pose.
- Fold **protein–nucleic-acid** or multi-entity assemblies in one pass.
- Get an open AlphaFold3-style prediction without proprietary access.

### Does NOT Trigger

| Scenario | Use instead |
|----------|-------------|
| Protein-only or protein–protein folding, no ligand | `alterlab-alphafold` |
| Antibody–antigen / general one-FASTA multi-entity complex | `alterlab-chai` |
| Dock a ligand into an **existing, fixed** receptor structure | `alterlab-diffdock` |
| Retrieve an experimentally determined structure | `alterlab-pdb` |
| Design a binding-pocket sequence around a ligand | `alterlab-ligandmpnn` |

## Core Capabilities

### 1. Protein + ligand co-folding

Describe the complex in a YAML spec (chains + ligand by SMILES or CCD), then predict:

```yaml
# complex.yaml
version: 1
sequences:
  - protein: { id: A, sequence: "MKT...GGG" }        # msa: path.a3m, or omit with --use_msa_server
  - ligand:  { id: L, smiles: "CC(=O)Oc1ccccc1C(=O)O" }   # or: ccd: SAH
```

```bash
boltz predict complex.yaml --out_dir out/ --use_msa_server --use_potentials
```

Outputs the co-folded structure (mmCIF by default, `--output_format pdb` for PDB) plus a
`confidence_*.json` per sample. `--use_msa_server` fetches the protein MSA from the hosted
MMseqs2 server (it sends your sequence out — disclose that for unpublished work); supply
`msa: my.a3m` per chain to stay offline, or `msa: empty` to force single-sequence mode.
`--use_potentials` applies inference-time potentials that improve the physical plausibility
of poses. Useful knobs: `--diffusion_samples N`, `--recycling_steps N`, `--override`.

### 2. Binding-affinity prediction

Ask for affinity in the YAML, naming the ligand chain to score:

```yaml
properties:
  - affinity:
      binder: L
```

`affinity_[input].json` then carries two distinct numbers, trained on different data and
meant for different jobs:

- **`affinity_probability_binary`** (0–1) — probability the ligand is a binder at all. Use
  it for hit discovery / binder-vs-decoy triage.
- **`affinity_pred_value`** — predicted `log10(IC50)` with IC50 in µM, so -3 ≈ 1 nM (strong),
  0 ≈ 1 µM, 2 ≈ 100 µM. It is calibrated for comparing *active* molecules during hit-to-lead
  optimisation, not for separating actives from inactives. Convert to pIC50-style kcal/mol
  with `(6 - y) * 1.364`.

Limits worth knowing before you queue a screen: one small-molecule binder per prediction,
at most 128 heavy+kept hydrogens (the training limit was ~56 atoms), and protein targets
only — an RNA/DNA "target" runs without error but the number is unreliable. Treat every
predicted affinity as a ranking signal and confirm against measured data
(`alterlab-bindingdb`) or experiment.

### 3. Confidence and validation

Each sample gets a `confidence_*.json` with `confidence_score` (the ranking score,
0.8·complex_plddt + 0.2·iptm), `ptm`, `iptm`, **`ligand_iptm`** (interface confidence at
protein–ligand interfaces specifically), `protein_iptm`, `complex_plddt`, `complex_iplddt`,
`chains_ptm` and `pair_chains_iptm`. For a ligand pose, `ligand_iptm` plus the pLDDT around
the pocket is the pair to read — a high overall score with a weak ligand interface means the
protein folded well and the ligand did not dock convincingly. Cross-check with
`alterlab-diffdock` when the receptor structure is already known and fixed.

### 4. Running on a GPU

Boltz-2 wants a CUDA GPU and downloads weights once into `~/.boltz`. Point `boltz predict` at
a *directory* of YAML files to batch a ligand series against one target in a single run, and
dispatch it via `alterlab-remote-compute`: submit → poll → harvest `out/predictions/`.

## Resources

- `references/boltz_usage.md` — install/pinning, YAML/FASTA input schema, MSA options,
  affinity output, and multi-entity examples. Loaded on demand.

Part of the AlterLab Academic Skills suite.
