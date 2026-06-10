---
name: alterlab-adaptyv
description: Submits and tracks protein-testing experiments on the Adaptyv Bio Foundry cloud lab (wet-lab validation), and optimizes protein sequences before submission with computational tools (NetSolP, SoluProt, SolubleMPNN, ESM). Use when designing proteins that need wet-lab validation - binding/affinity screening, expression testing, thermostability, or fluorescence assays - or when submitting experiments to the Foundry API, browsing the target catalog, tracking experiment status, retrieving results, or pre-screening sequences for solubility/expression. Triggers on "Adaptyv", "Foundry API", "cloud lab", "biolayer interferometry / BLI", "wet-lab validation". Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*)
compatibility: Requires an Adaptyv Bio Foundry account and an ADAPTYV_API_KEY token for experiment submission; local protein-optimization steps (ESM, etc.) run via `uv run python` without a key.
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# Adaptyv

Adaptyv Bio runs the **Foundry** cloud lab: submit protein sequences and a target, the lab runs the assay, and you retrieve experimental data (binding/affinity, thermostability, expression, fluorescence). The public **Foundry API** drives the full lifecycle programmatically. Turnaround is on the order of weeks; confirm the current estimate from the per-experiment quote rather than assuming a fixed number.

> The exact request/response shapes evolve. This skill captures the verified API contract and conventions; for the authoritative spec see the OpenAPI doc at `https://foundry-api-public.adaptyvbio.com/api/v1/openapi.json` and `https://docs.adaptyvbio.com`.

## Prefer the official tooling first

Adaptyv ships its own integrations - reach for them before hand-rolling `requests`:
- **Official Python SDK** — `github.com/adaptyvbio/adaptyv-sdk` (MIT). Decorator-based: wrap a design function with `@lab.experiment(target=...)`; reads `ADAPTYV_API_KEY` / `ADAPTYV_API_URL` (and optional `ADAPTYV_ORGANIZATION_ID`) from the environment. Install from source (`pip install -e .` after cloning — no PyPI release confirmed; verify before pinning).
- **Adaptyv's own Claude Code skills** — `github.com/adaptyvbio/protein-design-skills`. Useful prior art for protein-design + Foundry workflows.

Use this skill's raw-`requests` recipes when the SDK is unavailable or you need fine control over the lifecycle.

## Quick Start

### Authentication Setup

1. Create a token in the Foundry portal: `https://foundry.adaptyvbio.com/` → **Organization → Settings → Tokens** (pick a role: Member = read/write, Viewer = read-only; set an expiry). The token value is shown only once — copy it immediately.
2. Set it in your environment (never commit it):

```bash
export ADAPTYV_API_KEY="your_token_here"
```

Or put it in a gitignored `.env`:

```
ADAPTYV_API_KEY=your_token_here
```

### Installation

If using the raw API directly:

```bash
uv pip install requests python-dotenv
```

### Basic Usage

The API uses a **draft → submit** flow: create an experiment (it starts as a `draft`), then submit it. `sequences` is a `{label: amino_acid_string}` map (multi-chain constructs join chains with a colon, e.g. `"heavy:light"`).

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ADAPTYV_API_KEY")
base_url = "https://foundry-api-public.adaptyvbio.com/api/v1"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

# 1. Create a draft experiment
resp = requests.post(
    f"{base_url}/experiments",
    headers=headers,
    json={
        "name": "mini-binder round 1",
        "experiment_spec": {
            "experiment_type": "affinity",   # screening|affinity|thermostability|fluorescence|expression
            "method": "bli",                 # bli|spr (for binding-type assays)
            "target_id": "<target uuid from GET /targets>",
            "sequences": {
                "design_a": "MKVLWALLGLLGAA...",
                "design_b": "MATGVLWALLG...",
            },
        },
    },
)
resp.raise_for_status()
experiment_id = resp.json()["experiment_id"]

# 2. Submit it to the lab (after reviewing the quote — see reference/api_reference.md)
requests.post(f"{base_url}/experiments/{experiment_id}/submit", headers=headers).raise_for_status()
```

## Available Experiment Types
Foundry supports these `experiment_type` values:
- **screening** - Binding detection via biolayer interferometry (BLI) or SPR. Requires a target.
- **affinity** - Kinetic constants (KD, kon, koff) by BLI/SPR. Requires a target.
- **thermostability** - Melting temperature (Tm) via DSF. No target required.
- **fluorescence** - Fluorescence intensity. No target required.
- **expression** - Protein yield quantification. No target required.

See `reference/experiments.md` for detailed information on each assay and its outputs.

## Protein Sequence Optimization
Before submitting sequences, optimize them for better expression and stability:

**Common issues to address:**
- Unpaired cysteines that create unwanted disulfides
- Excessive hydrophobic regions causing aggregation
- Poor solubility predictions

**Recommended tools:**
- NetSolP / SoluProt - Initial solubility filtering (both are web services, not pip packages)
- SolubleMPNN - Solubility-biased sequence redesign (a weight set within the ProteinMPNN / LigandMPNN family)
- ESM (`fair-esm`) - Sequence likelihood / naturalness scoring
- ipTM (AlphaFold-Multimer / ColabFold) - Interface stability for binder designs
- pSAE - Solvent-accessible hydrophobic exposure, from a predicted/known structure

See `reference/protein_optimization.md` for detailed optimization workflows and tool usage.

## API Reference
For complete API documentation including all endpoints, request/response formats, and authentication details, see `reference/api_reference.md`.

## Examples
For concrete code examples covering common use cases (experiment submission, status tracking, result retrieval, batch processing), see `reference/examples.md`.

## Important Notes
- The Foundry API is public but still evolving — treat the OpenAPI doc (`/api/v1/openapi.json`) as the source of truth and verify field names before relying on them.
- Submission is two-step: create a `draft`, review the cost quote, then `POST .../submit`. Nothing is charged until you confirm the quote.
- `affinity`/`screening` require a `target_id` from the catalog (`GET /targets`); `thermostability`, `fluorescence`, and `expression` do not.
- Turnaround is multiple weeks — read the estimate from the experiment/quote rather than assuming a fixed number.
- Support and docs: support@adaptyvbio.com / `https://docs.adaptyvbio.com`.
- Suitable for high-throughput AI-driven protein design workflows (closed-loop design → test → learn).

