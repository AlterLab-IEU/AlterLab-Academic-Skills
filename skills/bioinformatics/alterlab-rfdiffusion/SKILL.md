---
name: alterlab-rfdiffusion
description: Generate de-novo protein backbones with RFdiffusion (Watson 2023) — a diffusion model for unconditional monomer generation, motif scaffolding, binder design against a target, and symmetric oligomers. Use when generating a new protein backbone from scratch, scaffolding a functional motif into a fold, designing a binder backbone to a target surface, or building symmetric assemblies; RFdiffusion produces the STRUCTURE, then alterlab-proteinmpnn designs its sequence and alterlab-alphafold validates it. For sequence design of an existing backbone prefer alterlab-proteinmpnn (or alterlab-ligandmpnn with a ligand); to fold a known sequence prefer alterlab-alphafold; for generative multimodal design prefer alterlab-esm. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*)
compatibility: "Runs RFdiffusion (`RosettaCommons/RFdiffusion`, PyTorch + SE(3)-transformer) under `uv run python` via `run_inference.py`. Requires a CUDA GPU for practical generation; model weights download once and cache (several GB; no account). Outputs backbone PDBs (no sequence) — pair with alterlab-proteinmpnn then alterlab-alphafold. Dispatch runs via alterlab-remote-compute."
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# RFdiffusion (de-novo backbone generation)

## Overview

**RFdiffusion** (Watson et al., *Nature* 2023; `RosettaCommons/RFdiffusion`) is a diffusion
model that **generates protein backbones** — new 3D structures, not sequences. It supports
unconditional generation, **motif scaffolding** (build a fold around a fixed functional
motif), **binder design** (generate a backbone that binds a target surface), and **symmetric**
assemblies. It is the structure-generation step that *starts* the de-novo design pipeline;
`alterlab-proteinmpnn` then designs sequences for the backbone and `alterlab-alphafold`
validates them.

## When to Use This Skill

Use this skill when the user wants to:
- **Generate** a novel protein backbone from scratch (unconditional).
- **Scaffold** a functional motif (e.g. a binding loop / catalytic geometry) into a new fold.
- Design a **binder** backbone against a given target protein surface / hotspots.
- Build **symmetric** oligomers (cyclic/dihedral) as backbones.

### Does NOT Trigger

| Scenario | Use instead |
|----------|-------------|
| Design the **sequence** for an existing backbone | `alterlab-proteinmpnn` |
| Design a pocket sequence **with a ligand/metal** present | `alterlab-ligandmpnn` |
| **Fold** a known sequence into a structure | `alterlab-alphafold` |
| Generative multimodal (sequence+structure) design | `alterlab-esm` |

## Core Capabilities

### 1. Unconditional generation

```bash
# RosettaCommons/RFdiffusion — run from the repo root. RFD points at the repo's
# scripts directory, where run_inference.py lives; it is driven by a Hydra config.
RFD=./scripts
python "$RFD"/run_inference.py \
  'contigmap.contigs=[100-100]' \
  inference.output_prefix=out/uncond \
  inference.num_designs=10
```

`contigmap.contigs` specifies what to build (here, a 100-residue monomer). Quote the contig
string — the brackets and `/` are shell metacharacters. Outputs backbone PDBs with no sequence,
plus a `.trb` metadata file recording which output residues came from the motif.

### 2. Motif scaffolding

Fix a functional motif (residues from an input PDB) and let RFdiffusion build a supporting
fold around it — the way to transplant a binding/catalytic geometry into a new, stable
scaffold. The contig string mixes generated lengths with fixed ranges named by chain+index:

```bash
python "$RFD"/run_inference.py inference.input_pdb=motif.pdb \
  'contigmap.contigs=[5-15/A10-25/30-40]' contigmap.length=55-55 \
  inference.output_prefix=out/scaffold inference.num_designs=10
```

Here `5-15` and `30-40` are generated segments resampled per design, `A10-25` is the fixed
motif, and `/0 ` (with the trailing space) would start a new chain. Only the residues named in
the contig are shown to the model — other chains and residues in the input PDB are ignored, so
you do not need to pre-trim the file.

### 3. Binder design

Provide a target structure and hotspot residues; RFdiffusion generates binder backbones docked
against that surface. Hotspots are the target residues the binder must contact:

```bash
python "$RFD"/run_inference.py inference.input_pdb=target.pdb \
  'contigmap.contigs=[B1-100/0 100-100]' 'ppi.hotspot_res=[A30,A33,A34]' \
  inference.output_prefix=out/binder inference.num_designs=10
```

Follow with sequence design (`alterlab-proteinmpnn`) and an interface validation refold
(`alterlab-alphafold`, read ipTM).

### 4. Which RFdiffusion (2026-09)

Three generations coexist; they are separate codebases, not upgrades of one CLI.

| Model | Where | Run via | Pick it for |
|-------|-------|---------|-------------|
| RFdiffusion (1) | `RosettaCommons/RFdiffusion` | `run_inference.py` + Hydra | the documented workhorse — monomers, motif scaffolding, binders, symmetry; everything in this skill |
| RFdiffusion2 | `RosettaCommons/RFdiffusion2` | its own inference CLI | atom-level enzyme active-site scaffolding (Ahern et al. 2025); inference only, still marked under construction upstream |
| RFdiffusion3 (RFD3) | `RosettaCommons/foundry` | `pip install rc-foundry[rfd3]`; `foundry install rfd3`; `rfd3 design out_dir=… inputs=spec.json` | all-atom design against DNA/ligands, atom-level hotspots, JSON/YAML input instead of contig strings |

RFD3 replaces the Hydra/contig interface with a JSON or YAML input specification, so RFdiffusion-1
command lines do not carry over. Reach for it when the design target involves non-protein atoms or
per-atom constraints; stay on RFdiffusion 1 for ordinary backbone generation, where its recipes and
published benchmarks are what the field has replicated.

### 5. The full design → fold → score loop

1. **Generate** backbones here (RFdiffusion).
2. **Design** sequences with `alterlab-proteinmpnn` (or `alterlab-ligandmpnn` if a ligand is
   present).
3. **Score** by refolding with `alterlab-alphafold` and keeping only self-consistent designs.

GPU-heavy — dispatch generation and the fold sweep via `alterlab-remote-compute`.

## Resources

- `references/rfdiffusion_usage.md` — install/pinning, contig grammar, motif/binder/symmetry
  configs, and loop integration. Loaded on demand.

Part of the AlterLab Academic Skills suite.
