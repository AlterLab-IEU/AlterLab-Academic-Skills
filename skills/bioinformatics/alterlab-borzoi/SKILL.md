---
name: alterlab-borzoi
description: Predict genome-wide functional genomics tracks from DNA sequence with Borzoi (Linder 2025) — a sequence-to-function model outputting RNA-seq, CAGE, ATAC, and ChIP coverage across long context, used to score non-coding and regulatory variant effects. Use when predicting functional tracks from a DNA sequence, scoring a non-coding/regulatory variant's effect on expression or chromatin, or doing in-silico mutagenesis of a locus. To LOOK UP a variant's population frequency prefer alterlab-gnomad; for its clinical significance prefer alterlab-clinvar; for protein-structure effects prefer alterlab-alphafold; for single-cell foundation models prefer alterlab-scgpt. Part of the AlterLab Academic Skills suite.
license: Apache-2.0
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*)
compatibility: "Reference TensorFlow code (`calico/borzoi` + `calico/baskerville` from git, TF 2.15.x) or the PyTorch port `borzoi-pytorch` (0.5.1 as of 2026-09, Hugging Face weights), under `uv run python`. Weights cache after first download; a CUDA GPU is strongly recommended (~500 kb DNA context). Input: DNA (FASTA or coordinates + reference); output: multi-track coverage arrays. Dispatch large scans via alterlab-remote-compute."
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# Borzoi (sequence → function)

## Overview

**Borzoi** (Linder et al. 2025; `calico/borzoi`) is a **sequence-to-function** deep-learning
model: given a DNA sequence over a long genomic context, it predicts **genome-wide functional
tracks** — RNA-seq, CAGE, ATAC-seq, and ChIP coverage across many assays/tissues. Its headline
use is **non-coding variant effect scoring**: run the reference and alternate alleles through
the model and compare predicted tracks to estimate a regulatory variant's impact on expression
or chromatin.

It **predicts** function from sequence; it does not *look up* known variants. For a variant's
population frequency use `alterlab-gnomad`; for clinical significance use `alterlab-clinvar`.

## When to Use This Skill

Use this skill when the user wants to:
- Predict **functional tracks** (RNA-seq/CAGE/ATAC/ChIP) from a DNA sequence or locus.
- Score a **non-coding / regulatory variant's** predicted effect (ref vs. alt).
- Run **in-silico mutagenesis** to find driver bases in a regulatory element.
- Prioritize candidate regulatory variants by predicted functional impact.

### Does NOT Trigger

| Scenario | Use instead |
|----------|-------------|
| Look up a variant's **population frequency** | `alterlab-gnomad` |
| Look up a variant's **clinical significance** | `alterlab-clinvar` |
| Predict a **protein-structure** / coding effect | `alterlab-alphafold` |
| Single-cell foundation-model tasks | `alterlab-scgpt` |
| Standard variant calling from reads | `alterlab-nf-core-sarek` (or the relevant pipeline skill) |

## Core Capabilities

### 1. Track prediction from sequence

The quickest path is the PyTorch port, which loads ported weights straight from the Hub:

```python
from borzoi_pytorch import Borzoi

# replicates 0-3, human by default; 'johahi/borzoi-replicate-0-mouse' for mouse heads
model = Borzoi.from_pretrained("johahi/borzoi-replicate-0").eval().cuda()
# one-hot encode the reference window around your locus, then:
# predictions = model(one_hot_batch)   # (batch, tracks, bins)
```

The reference TensorFlow implementation (`calico/borzoi` on top of `calico/baskerville`)
is the source of truth for the published results and ships the variant-scoring and
interpretation tutorials. Either way: provide a genome window (coordinates + reference, or a
FASTA), one-hot encode it, and read predicted coverage across the output tracks.

### 2. Non-coding variant effect scoring

The core workflow: build the **reference** and **alternate** sequences for a variant, predict
tracks for each, and quantify the difference (e.g. SAD/SED-style scores) to estimate the
variant's regulatory effect. Prioritize candidates by the magnitude of predicted change.

### 3. In-silico mutagenesis

Systematically mutate bases across a regulatory element and read the predicted-track deltas to
localize functionally important positions (motif/driver discovery).

### 4. GPU and dispatch

Borzoi takes long context and is GPU-heavy; genome-wide or many-variant scans should be
dispatched via `alterlab-remote-compute` (submit → poll → harvest). **Flashzoi**
(`johahi/flashzoi-replicate-0..3`, needs FlashAttention-2) is a drop-in ~3x faster variant at
comparable accuracy — worth it for large scans.

## Resources

- `references/borzoi_usage.md` — install/pinning, sequence extraction, predict calls,
  ref/alt variant scoring, in-silico mutagenesis, and Enformer lineage. Loaded on demand.

Part of the AlterLab Academic Skills suite.
