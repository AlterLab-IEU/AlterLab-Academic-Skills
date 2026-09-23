---
name: alterlab-esm
description: Run ESM protein language models — ESMC for embeddings and representations, ESMFold2 for structure prediction, and ESM3 for generative multimodal protein design across sequence, structure, and function — locally or through the hosted Biohub Platform API (formerly Forge). Use when working with protein sequences, structures, or function prediction, designing novel proteins, generating protein embeddings, performing inverse folding, or doing protein-engineering tasks. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*)
compatibility: "Runs under `uv run python` with the `esm` package (3.4.1.post1 as of 2026-09; requires Python >= 3.12 and torch >= 2.11). Local weights come from Hugging Face (`huggingface_hub` login) and run best on a CUDA GPU; CPU works for small ESMC embeddings but is slow. The hosted path is the Biohub Platform (`https://biohub.ai`, formerly forge.evolutionaryscale.ai) and needs an API token, read from the `ESM_API_KEY` environment variable by default."
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# ESM: Evolutionary Scale Modeling

## Overview

ESM provides state-of-the-art protein language models for understanding, generating, and designing proteins. Three families ship in the same `esm` package:

- **ESMC** — the current representation model (300M / 600M open weights, 6B via the hosted
  platform), used for embeddings, logits, and downstream ML features.
- **ESMFold2** — structure prediction built on ESMC-6B, hosted via `esmfold2_client`.
- **ESM3** — the generative multimodal model over sequence / structure / function tracks.

### Naming and hosting changed — read this before copying old code

EvolutionaryScale now operates as **Biohub**. The practical consequences:

- The hosted API moved from `forge.evolutionaryscale.ai` to **`https://biohub.ai`**; every
  client in `esm.sdk` defaults to that URL and reads the token from `ESM_API_KEY`. The
  classes are still named `*ForgeInferenceClient` for backwards compatibility.
- Model weights live under the **`biohub`** Hugging Face organisation (`biohub/ESMC-6B`,
  `biohub/esm3-sm-open-v1`, `biohub/ESMFold2`).
- ESMC and ESMFold2 are also available through Hugging Face Transformers v5.16+, which is
  a different dependency stack from the `esm` package's optimized inference path.

## When to Use This Skill

Use this skill when the user wants protein embeddings or logits, a protein structure from
an ESM model, inverse folding, or generative sequence design.

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Fold a protein or complex with AlphaFold2/ColabFold | `alterlab-alphafold` |
| Co-fold with a ligand, or predict binding affinity | `alterlab-boltz` |
| Antibody–antigen or mixed multi-entity complexes | `alterlab-chai` |
| Design a sequence for a fixed backbone (ProteinMPNN family) | `alterlab-proteinmpnn`, `alterlab-ligandmpnn` |
| Generate a de-novo backbone to design onto | `alterlab-rfdiffusion` |

## Core Capabilities

### 1. Protein Sequence Generation with ESM3

Generate novel protein sequences with desired properties using multimodal generative modeling.

**When to use:**
- Designing proteins with specific functional properties
- Completing partial protein sequences
- Generating variants of existing proteins
- Creating proteins with desired structural characteristics

**Basic usage:**

```python
from esm.models.esm3 import ESM3
from esm.sdk.api import ESM3InferenceClient, ESMProtein, GenerationConfig

# Load model locally
model: ESM3InferenceClient = ESM3.from_pretrained("esm3-sm-open-v1").to("cuda")

# Create protein prompt
protein = ESMProtein(sequence="MPRT___KEND")  # '_' represents masked positions

# Generate completion
protein = model.generate(protein, GenerationConfig(track="sequence", num_steps=8))
print(protein.sequence)
```

**For remote/cloud usage via the Biohub Platform:**

```python
import esm
from esm.sdk.api import ESMProtein, GenerationConfig

# url defaults to https://biohub.ai and token to os.environ["ESM_API_KEY"]
model = esm.sdk.client("esm3-medium-2024-08")

protein = model.generate(protein, GenerationConfig(track="sequence", num_steps=8))
```

See `references/esm3-api.md` for detailed ESM3 model specifications, advanced generation configurations, and multimodal prompting examples.

### 2. Structure Prediction and Inverse Folding

Use ESM3's structure track for structure prediction from sequence or inverse folding (sequence design from structure).

**Structure prediction:**

```python
from esm.sdk.api import ESM3InferenceClient, ESMProtein, GenerationConfig

# Predict structure from a complete sequence
protein = ESMProtein(sequence="MPRTKEINDAGLIVHSP")
protein_with_structure = model.generate(
    protein,
    # num_steps controls how many structure tokens are decoded per step;
    # use the sequence length (not a "_" count — the sequence is complete here)
    GenerationConfig(track="structure", num_steps=len(protein.sequence))
)

# Access predicted structure
coordinates = protein_with_structure.coordinates  # 3D coordinates
pdb_string = protein_with_structure.to_pdb()
```

**Inverse folding (sequence from structure):**

```python
# Design sequence for a target structure
protein_with_structure = ESMProtein.from_pdb("target_structure.pdb")
protein_with_structure.sequence = None  # Remove sequence

# Generate sequence that folds to this structure
designed_protein = model.generate(
    protein_with_structure,
    GenerationConfig(track="sequence", num_steps=50, temperature=0.7)
)
```

### 3. Protein Embeddings with ESM C

Generate high-quality embeddings for downstream tasks like function prediction, classification, or similarity analysis.

**When to use:**
- Extracting protein representations for machine learning
- Computing sequence similarities
- Feature extraction for protein classification
- Transfer learning for protein-related tasks

**Basic usage:**

```python
from esm.models.esmc import ESMC
from esm.sdk.api import ESMProtein, LogitsConfig

# Load ESMC locally (local from_pretrained names use UNDERSCORES; default is esmc_600m)
model = ESMC.from_pretrained("esmc_300m").to("cuda")

# Encode, then request embeddings via the logits() API
protein = ESMProtein(sequence="MPRTKEINDAGLIVHSP")
protein_tensor = model.encode(protein)
out = model.logits(protein_tensor, LogitsConfig(sequence=True, return_embeddings=True))

embeddings = out.embeddings   # (1, L+2, hidden_dim), incl. BOS/EOS tokens
logits = out.logits.sequence  # per-position amino-acid logits
```

Do NOT call `model.forward(...)` to get embeddings — `forward` returns a raw model output, not a usable representation tensor. Use `model.logits(..., LogitsConfig(return_embeddings=True)).embeddings`.

**Batch processing:**

```python
# Encode multiple proteins and pull mean-pooled embeddings
proteins = [
    ESMProtein(sequence="MPRTKEIND"),
    ESMProtein(sequence="AGLIVHSPQ"),
    ESMProtein(sequence="KTEFLNDGR"),
]
cfg = LogitsConfig(sequence=True, return_embeddings=True)
embeddings_list = [
    model.logits(model.encode(p), cfg).embeddings.mean(dim=1) for p in proteins
]
```

See `references/esm-c-api.md` for ESM C model details, efficiency comparisons, and advanced embedding strategies.

### 4. Function Conditioning and Annotation

Use ESM3's function track to generate proteins with specific functional annotations or predict function from sequence.

**Function-conditioned generation:**

```python
from esm.sdk.api import ESMProtein, FunctionAnnotation, GenerationConfig

# Create protein with desired function
protein = ESMProtein(
    sequence="_" * 200,  # Generate 200 residue protein
    function_annotations=[
        FunctionAnnotation(label="fluorescent_protein", start=50, end=150)
    ]
)

# Generate sequence with specified function
functional_protein = model.generate(
    protein,
    GenerationConfig(track="sequence", num_steps=200)
)
```

### 5. Chain-of-Thought Generation

Iteratively refine protein designs using ESM3's chain-of-thought generation approach.

```python
from esm.sdk.api import GenerationConfig

# Multi-step refinement
protein = ESMProtein(sequence="MPRT" + "_" * 100 + "KEND")

# Step 1: Generate initial structure
config = GenerationConfig(track="structure", num_steps=50)
protein = model.generate(protein, config)

# Step 2: Refine sequence based on structure
config = GenerationConfig(track="sequence", num_steps=50, temperature=0.5)
protein = model.generate(protein, config)

# Step 3: Predict function
config = GenerationConfig(track="function", num_steps=20)
protein = model.generate(protein, config)
```

### 6. Batch processing against the hosted platform

The client exposes both an async API and a parallel executor that handles retries and a
progress bar:

```python
import asyncio
import esm
from esm.sdk import parallel_executor
from esm.sdk.api import ESMProtein, GenerationConfig

client = esm.sdk.client("esm3-medium-2024-08")   # token from ESM_API_KEY
proteins = [ESMProtein(sequence=f"MPRT{'_' * 50}KEND") for _ in range(10)]
cfg = GenerationConfig(track="sequence", num_steps=8)

# Option A: async fan-out
async def run():
    return await asyncio.gather(*(client.async_generate(p, cfg) for p in proteins))

results = asyncio.run(run())

# Option B: managed executor (retries + progress)
with parallel_executor() as executor:
    results = executor.execute_batch(client.generate, protein=proteins, config=cfg)
```

Also available: `client.batch_generate(...)` / `async_batch_generate(...)`, and
`async_fold` / `async_inverse_fold` / `async_logits` for the other tracks.

See `references/forge-api.md` for platform documentation, authentication, rate limits, and
batch processing patterns.

## Model Selection Guide

**ESM3 Models (Generative):**
- `esm3-sm-open-v1` (1.4B, aliases `esm3_sm_open_v1` / `esm3-open`) — open weights, local
- `esm3-medium-2024-08` (7B) — balance of quality and speed (hosted only)
- `esm3-large-2024-03` (98B) — highest quality, slower (hosted only)

**ESMC Models (Representations):**
- `esmc_300m` — lightweight, fast; open weights, runs locally
- `esmc_600m` — balanced; open weights, runs locally, and the `from_pretrained` default
- `esmc_6b` / hosted `esmc-6b-2024-12` — maximum representation quality

**ESMFold2 (Structure):** `esmfold2-fast-2026-05` (the `esmfold2_client` default),
`esmfold2-2026-05`, `esmfold2-2026-05-cutoff-2025`.

Naming gotcha: local `from_pretrained(...)` names use **underscores** (`esmc_300m`,
`esmc_600m`, `esmc_6b`). Hosted client strings use **hyphens with a date**
(`esmc-600m-2024-12`, `esm3-medium-2024-08`, `esmfold2-fast-2026-05`).

**Selection criteria:**
- **Local development/testing:** `esmc_300m` for embeddings, `esm3-sm-open-v1` for generation
- **Production quality:** `esm3-medium-2024-08` or `esmc-6b-2024-12` via the Biohub Platform
- **Structure prediction:** `esmfold2_client()` rather than the ESM3 structure track
- **High throughput:** hosted clients plus `esm.sdk.parallel_executor` / batch client
- **Cost optimization:** smaller models, cache embeddings

## Installation

**Basic installation** (pin the minor — the SDK still changes across releases):

```bash
uv pip install "esm>=3.4,<3.5"     # 3.4.1.post1 as of 2026-09; needs Python >= 3.12
```

**With Flash Attention (optional, faster GPU inference):**

```bash
uv pip install flash-attn --no-build-isolation
```

The hosted clients (`esm.sdk.client`, `esmc_client`, `esmfold2_client`) ship inside the
`esm` package — no extra install. Create an API token in the Biohub developer console
(`https://biohub.ai/developer-console/api-keys`) and export it as `ESM_API_KEY`. Local
weights are pulled from Hugging Face, so run `huggingface_hub.login()` once with a
read-scoped token.

**ESMC through the Biohub Platform:**

```python
from esm.sdk import esmc_client
from esm.sdk.api import ESMProtein, LogitsConfig

model = esmc_client(model="esmc-600m-2024-12")       # url/token default as above
out = model.logits(model.encode(ESMProtein(sequence="MPRTKEINDAGLIVHSP")),
                   LogitsConfig(sequence=True, return_embeddings=True))
print(out.logits, out.embeddings)
```

## Common Workflows

For detailed examples and complete workflows, see `references/workflows.md` which includes:
- Novel GFP design with chain-of-thought
- Protein variant generation and screening
- Structure-based sequence optimization
- Function prediction pipelines
- Embedding-based clustering and analysis

## References

This skill includes comprehensive reference documentation:

- `references/esm3-api.md` - ESM3 model architecture, API reference, generation parameters, and multimodal prompting
- `references/esm-c-api.md` - ESM C model details, embedding strategies, and performance optimization
- `references/forge-api.md` - Forge platform documentation, authentication, batch processing, and deployment
- `references/workflows.md` - Complete examples and common workflow patterns

These references contain detailed API specifications, parameter descriptions, and advanced usage patterns. Load them as needed for specific tasks.

## Best Practices

**For generation tasks:**
- Start with smaller models for prototyping (`esm3-sm-open-v1`)
- Use temperature parameter to control diversity (0.0 = deterministic, 1.0 = diverse)
- Implement iterative refinement with chain-of-thought for complex designs
- Validate generated sequences with structure prediction or wet-lab experiments

**For embedding tasks:**
- Batch process sequences when possible for efficiency
- Cache embeddings for repeated analyses
- Normalize embeddings when computing similarities
- Use appropriate model size based on downstream task requirements

**For production deployment:**
- Use the hosted Biohub Platform for scalability and the largest models
- Implement error handling and retry logic for API calls
- Monitor token usage and implement rate limiting
- Consider AWS SageMaker deployment for dedicated infrastructure

## Resources and Documentation

- **GitHub Repository:** https://github.com/Biohub/esm (ESM3 docs live in `_assets/ESM3_README.md`)
- **Biohub Platform:** https://biohub.ai — API keys at https://biohub.ai/developer-console/api-keys
- **ESM Atlas:** https://biohub.ai/esm/protein/atlas
- **ESM3 paper:** Hayes et al., *Science* — https://www.science.org/doi/10.1126/science.ads0018
- **Tutorials:** https://github.com/Biohub/esm/tree/main/cookbook/tutorials
- **Model Weights:** Hugging Face `biohub` organization

## Responsible Use

ESM is designed for beneficial applications in protein engineering, drug discovery, and scientific research. Biohub publishes an Acceptable Use Policy and ran a biosafety/biosecurity risk assessment before release — follow that policy, and the Responsible Biodesign Framework (https://responsiblebiodesign.ai/), when designing novel proteins. Think through biosafety and dual-use implications before experimental validation, because a designed sequence leaves the computational realm the moment it is ordered.

Part of the AlterLab Academic Skills suite.
