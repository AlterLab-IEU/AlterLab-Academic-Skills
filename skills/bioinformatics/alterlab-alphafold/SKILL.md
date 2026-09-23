---
name: alterlab-alphafold
description: Predict protein 3D structures with AlphaFold2 via ColabFold — MMseqs2-accelerated MSAs, monomer and AlphaFold2-Multimer complex folding, and confidence-based validation (pLDDT, pTM/ipTM, PAE). Use when folding a protein sequence or complex from FASTA, generating a predicted structure with confidence metrics, ranking models, or checking self-consistency of a design. For co-folding a protein WITH a small-molecule ligand or predicting binding affinity prefer alterlab-boltz; for antibody–antigen or one-FASTA multi-entity complexes prefer alterlab-chai; to LOOK UP an already-computed structure prefer alterlab-alphafold-db; for ESM embeddings or inverse folding prefer alterlab-esm. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*)
compatibility: "Runs via ColabFold (`colabfold_batch`) — install `colabfold[alphafold,openmm]` plus a CUDA-matched JAX (current release 1.6.3 as of 2026-09). Requires a CUDA GPU for folding (JAX/CUDA); the MSA step uses the hosted MMseqs2 API by default or a local database. AF2 network weights download once and cache (~several GB). Dispatch heavy runs via alterlab-remote-compute."
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# AlphaFold (via ColabFold)

## Overview

Predict a protein's 3D structure from its amino-acid sequence with **AlphaFold2**, run through
**ColabFold** (Mirdita et al., *Nature Methods* 2022) — which replaces AlphaFold's slow
genetic-database MSA search with the fast **MMseqs2** API, making folding practical on a
single GPU. Handles single chains (monomer) and complexes via **AlphaFold2-Multimer** (Evans
et al. 2021), and reports per-residue and per-interface **confidence metrics** so you know
which parts of a prediction to trust.

This skill **runs** folding and returns structures + confidence. To retrieve an
*already-computed* AlphaFold prediction for a known UniProt entry without running anything,
use `alterlab-alphafold-db` instead.

## When to Use This Skill

Use this skill when the user wants to:
- Fold a protein sequence (FASTA) into a predicted 3D structure (PDB/mmCIF).
- Predict a protein **complex** (AF2-Multimer) and score the interface (ipTM).
- Rank multiple models and read confidence (pLDDT, pTM, PAE) to judge reliability.
- Validate a designed sequence by refolding it and checking self-consistency vs. a target.

### Does NOT Trigger

| Scenario | Use instead |
|----------|-------------|
| Co-fold a protein **with a ligand** (SMILES/CCD) or predict binding affinity | `alterlab-boltz` |
| Antibody–antigen / arbitrary multi-entity complex from one FASTA | `alterlab-chai` |
| Look up a **precomputed** AlphaFold model by UniProt id | `alterlab-alphafold-db` |
| ESM embeddings, inverse folding, generative design | `alterlab-esm` |
| Dock a ligand into an existing structure | `alterlab-diffdock` |
| De-novo backbone generation | `alterlab-rfdiffusion` |

## Core Capabilities

### 1. Monomer folding

```bash
# One sequence per FASTA record; MSAs via the hosted MMseqs2 API (--msa-mode)
colabfold_batch input.fasta out/ --num-models 5 --num-recycle 3
```

Outputs per record: ranked `*_rank_00N_*.pdb`/`.cif`, a JSON with `plddt`/`pae`, and
coverage/pLDDT plots. Relaxation is off by default — add `--amber --num-relax 1
--use-gpu-relax` to Amber-relax the top model (needs the `openmm` extra).

### 2. Complex folding (AF2-Multimer)

Join chains with a colon in one FASTA record to fold a complex:

```text
>my_complex
MKT...AAA:MSE...GGG
```

```bash
colabfold_batch complex.fasta out/ --model-type alphafold2_multimer_v3
```

Read **ipTM** (interface confidence) and the inter-chain **PAE** block to judge whether the
predicted interface is meaningful, not just the intra-chain pLDDT.

### 3. Confidence and validation

| Metric | Reads |
|--------|-------|
| **pLDDT** (0–100, per residue) | local confidence; <50 = likely disordered/unreliable |
| **pTM** | global fold confidence; >0.5 means the overall fold is plausibly right |
| **ipTM** | interface confidence (complexes) — the number that matters for binding. DeepMind's published bands: **>0.8 confident**, **0.6–0.8 gray zone**, **<0.6 likely failed** |
| **PAE** | expected positional error between residue pairs; low off-diagonal = confident relative orientation |

**Self-consistency check** (validating a design): fold the candidate, then compare to the
intended backbone (e.g. TM-score / RMSD). A design that folds back to its target with high
pLDDT and low PAE is self-consistent — the standard acceptance gate in a
design→fold→score loop (see `alterlab-proteinmpnn`, `alterlab-rfdiffusion`).

### 4. Running on a GPU

Folding needs a CUDA GPU. For anything beyond a quick monomer, dispatch through
`alterlab-remote-compute` (SLURM or a managed GPU provider): submit `colabfold_batch`, poll
to completion, and harvest `out/`.

### 5. When AlphaFold 3 is the better tool

This skill runs **AlphaFold 2** through ColabFold, which folds proteins and protein
complexes only. **AlphaFold 3** (Abramson et al., *Nature* 2024,
doi:10.1038/s41586-024-07487-w) additionally handles ligands, nucleic acids, ions, and
covalent modifications in one prediction. Access routes, as of 2026-09:

- **AlphaFold Server** (`alphafoldserver.com`) — free for non-commercial use, with a
  restricted ligand/modification set and no install.
- **Local inference** — `google-deepmind/alphafold3` ships the inference pipeline under
  Apache-2.0; the model parameters are distributed separately by Google under their own
  terms of use (not Apache-2.0), so check those terms before using them in a project.
- **Commercial use** — available through Google Cloud rather than the open weights.

If the biology is a protein–ligand or protein–nucleic-acid complex and you want an openly
licensed local model instead, `alterlab-boltz` (MIT) and `alterlab-chai` (Apache-2.0) are
the AF3-class options this suite wraps.

## Resources

- `references/colabfold_usage.md` — install/pinning, MSA modes (API vs. local DB), templates,
  relaxation, batch/array runs, and full metric interpretation. Loaded on demand.

Part of the AlterLab Academic Skills suite.
