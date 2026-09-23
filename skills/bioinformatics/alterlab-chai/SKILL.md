---
name: alterlab-chai
description: Predict biomolecular complexes with Chai-1, an open AlphaFold3-style model that folds multi-entity assemblies (proteins, ligands, nucleic acids) from a single typed FASTA — strong on antibody–antigen and protein–ligand complexes, with optional MSA and restraint inputs. Use when predicting an antibody–antigen complex, folding a mixed protein/ligand/nucleic-acid assembly described in one FASTA, or generating a complex with experimental restraints. For binding-affinity prediction or a ligand-focused co-fold prefer alterlab-boltz; for protein-only or protein–protein folding prefer alterlab-alphafold; to dock into a fixed receptor prefer alterlab-diffdock. Part of the AlterLab Academic Skills suite.
license: Apache-2.0
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*)
compatibility: "Chai-1 (`chaidiscovery/chai-lab`; `uv pip install chai_lab==0.6.1`, current as of 2026-09) under `uv run python`. Needs Linux, Python >= 3.10 and a CUDA GPU with bfloat16 (A100/H100/L40S recommended; A10/A30/RTX 4090 for smaller complexes). Weights download on first run (relocate with CHAI_DOWNLOADS_DIR). Input: one typed FASTA; MSAs, templates, restraints optional. Apache-2.0 code and weights. Dispatch heavy runs via alterlab-remote-compute."
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# Chai-1 (open complex prediction)

## Overview

**Chai-1** (Chai Discovery 2024; `chaidiscovery/chai-lab`) is an open AlphaFold3-style model
that predicts **multi-entity biomolecular complexes** — proteins, small-molecule ligands, and
nucleic acids together — from a **single typed FASTA**. It is particularly used for
**antibody–antigen** and protein–ligand complexes, can run with or without MSAs, and accepts
**restraints** to guide the prediction.

Its niche relative to the other folders: one FASTA describing a *mixed assembly*, and
antibody–antigen in particular. For a ligand co-fold where you specifically want a **binding
affinity**, use `alterlab-boltz`; for a bare protein, use `alterlab-alphafold`.

## When to Use This Skill

Use this skill when the user wants to:
- Predict an **antibody–antigen** complex structure.
- Fold a **mixed assembly** (protein + ligand + nucleic acid) described in one FASTA.
- Run complex prediction **with or without MSAs**, optionally guided by restraints.
- Get an open AlphaFold3-style complex prediction with per-entity confidence.

### Does NOT Trigger

| Scenario | Use instead |
|----------|-------------|
| Predict a protein–ligand **binding affinity** | `alterlab-boltz` |
| Protein-only or protein–protein folding | `alterlab-alphafold` |
| Dock a ligand into a **fixed** receptor structure | `alterlab-diffdock` |
| Look up an experimental complex structure | `alterlab-pdb` |
| Design antibody/interface sequences | `alterlab-proteinmpnn` / `alterlab-ligandmpnn` |

## Core Capabilities

### 1. Single-FASTA multi-entity input

Chai-1 reads one FASTA whose records are typed by entity. A protein + ligand example:

```text
>protein|name=antibody-Fv
EVQ...SS
>protein|name=antigen
MKT...GG
>ligand|name=cofactor
CC(=O)Oc1ccccc1C(=O)O
```

```bash
chai-lab fold input.fasta out/                          # single-sequence, fastest
chai-lab fold --use-msa-server --use-templates-server input.fasta out/   # recommended
```

Each header is `<entity_type>|name=<unique label>` (the bare `type|label` form also parses).
Valid entity types: `protein`, `ligand` (SMILES), `rna`, `dna`, `glycan`. Names must be
unique — a repeated name raises. The output directory must be empty.

### 2. Antibody–antigen complexes

The common use case: fold an antibody Fv/Fab against its antigen and read the **interface
confidence** (per-model / interface score) to judge whether the predicted epitope/paratope
contact is trustworthy. Use restraints when you have partial epitope knowledge.

### 3. MSA, templates and restraints

- **MSA optional** — Chai-1 runs single-sequence by default; `--use-msa-server` fetches MSAs
  from the shared ColabFold MMseqs2 server (discloseable for sensitive sequences) and
  generally improves accuracy at a time cost. Local MSAs are supplied as `aligned.pqt`
  files (convert a3m with `chai a3m-to-pqt`).
- **Templates** — `--use-templates-server`, or your own `m8` hit table plus CIFs in
  `CHAI_TEMPLATE_CIF_FOLDER`.
- **Restraints** — a CSV passed as `constraint_path`, one row per restraint with columns
  `restraint_id, chainA, res_idxA, chainB, res_idxB, connection_type, confidence,
  min_distance_angstrom, max_distance_angstrom, comment`. `connection_type` is `contact`
  (residue↔residue) or `pocket` (chain↔residue, so `res_idxA` is left blank). Residue
  indices are the residue letter plus its 1-based position (`D4`), and chains are lettered
  A–Z in input order. Published example: two ground-truth contacts lifted antibody–antigen
  interface DockQ from ~0.02 to ~0.4 on PDB 7SYZ.

### 4. Confidence and GPU dispatch

A run writes `pred.model_idx_{0..4}.cif` plus `scores.model_idx_N.npz` holding
`aggregate_score` (the ranking number), `ptm`, `iptm`, `per_chain_ptm`,
`per_chain_pair_iptm`, `has_inter_chain_clashes` and `chain_chain_clashes`. For an
antibody–antigen job the pair-wise `per_chain_pair_iptm` entry for the two chains — not the
global score — is what tells you whether the predicted epitope is trustworthy; check the
clash flags before believing a high score.

The Python entry point is `chai_lab.chai1.run_inference(fasta_file=..., output_dir=...,
num_diffn_samples=5, num_trunk_recycles=3, seed=..., device="cuda:0")`, returning a
`StructureCandidates` with `cif_paths` and `ranking_data`. Batch an antibody panel against one
antigen via `alterlab-remote-compute` (submit → poll → harvest `out/`).

## Resources

- `references/chai_usage.md` — install/pinning, FASTA type-tag syntax, MSA/restraint options,
  outputs, and folder-choice guidance. Loaded on demand.

Part of the AlterLab Academic Skills suite.
