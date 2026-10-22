---
name: alterlab-adaptyv
description: Prepares and validates Adaptyv Bio Foundry protein-testing submissions with no account — optimizes and pre-screens sequences locally (NetSolP/SoluProt heuristics, SolubleMPNN, ESM), assembles the experiment payload, and validates it offline against the Foundry's own type/method/sequence rules so it is ready and correct before it costs anything. Submitting to the Foundry, browsing the target catalog, tracking status and retrieving results run through the Foundry API with the user's own ADAPTYV_API_KEY (experiments cost money and take weeks). Use when designing proteins for wet-lab validation (binding/affinity, expression, thermostability, fluorescence), preparing or validating a Foundry submission, pre-screening sequences, or tracking an Adaptyv experiment. Triggers on "Adaptyv", "Foundry API", "cloud lab", "biolayer interferometry / BLI", "wet-lab validation". Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*) Bash(uv run:*)
compatibility: "No API key required to optimize/pre-screen sequences locally and to assemble and validate a Foundry submission offline (scripts/validate_submission.py, stdlib-only, from the published OpenAPI contract). Optional: the user's own ADAPTYV_API_KEY to submit experiments, browse the target catalog, track status and pull results; experiments cost money and take weeks."
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    last_updated: "2026-10-22"
    credentials: "optional: ADAPTYV_API_KEY (an Adaptyv Foundry Biscuit token — adds submitting experiments, the target catalog GET /targets, status tracking and result retrieval; runs incur real cost). ADAPTYV_API_URL and ADAPTYV_ORGANIZATION_ID are optional non-secret config the SDK reads"
---

# Adaptyv

Adaptyv Bio runs the **Foundry** cloud lab: submit protein sequences and a target, the lab runs the assay, and you retrieve experimental data (binding/affinity, thermostability, expression, fluorescence). The design, sequence optimization, and a validated, ready-to-submit experiment package are produced with no account; only the submission itself and reading results use the Foundry API.

> The exact request/response shapes evolve. This skill captures the API contract as published in the OpenAPI doc (v0.0.2, checked 2026-10-22) at `https://foundry-api-public.adaptyvbio.com/api/v1/openapi.json`; that spec lists `https://devs.adaptyvbio.com` as the production base URL, and both hosts serve the same `/api/v1` routes. See also `https://docs.adaptyvbio.com`.

## Keyless Path (default — no Foundry account)

1. **Optimize and pre-screen sequences locally** (already keyless): flag unpaired cysteines and aggregation-prone hydrophobic stretches, filter with NetSolP/SoluProt-style solubility scoring, redesign with SolubleMPNN, and score naturalness with ESM — `uv run python` with no token. See `reference/protein_optimization.md`.
2. **Assemble the experiment payload** (`experiment_spec`: `experiment_type`, `method`, `target_id`, the `{label: aa_string}` `sequences` map, `n_replicates`) from the OpenAPI contract in `reference/api_reference.md`.
3. **Validate the submission offline** with `python3 scripts/validate_submission.py spec.json` before it ever reaches the API — it enforces the Foundry's own per-type matrix with no key: `method` (bli|spr) required for affinity/screening and rejected otherwise; `target_id` required for affinity/screening/epitope_binning and rejected otherwise; `sequences` non-empty (epitope_binning a multiple of 4, 4..28); `n_replicates` rejected for epitope_binning; and every sequence a valid amino-acid string (the 20 AAs plus ':' for multichain). This catches the exact problems the API's 400 would list, without a round trip.
4. **Hand over submission.** Give the authenticated `POST /experiments` -> review quote -> `POST .../quote/confirm` flow; it needs the user's `ADAPTYV_API_KEY`, and the catalog `GET /targets` (to resolve a real `target_id`) is also token-gated. If the key is unset, deliver the validated package and stop — never claim an experiment was submitted or invent results.

Experiments cost money and run for weeks; nothing is billed until the user confirms the quote.

## When to Use This Skill

Use this skill to design → test → learn with Adaptyv's cloud lab: pick a catalog target,
pre-screen and submit designed sequences, track experiments through quote and production,
and pull binding, stability, expression, fluorescence, epitope-binning, or enzyme-activity data.

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Designing sequences for a fixed backbone (inverse folding) before any wet-lab step | `alterlab-proteinmpnn` |
| Protein language-model embeddings or generative design with ESM3 / ESM C | `alterlab-esm` |
| Cell-free expression or other protocols on Ginkgo's cloud lab (RACs) | `alterlab-ginkgo-cloud` |
| Recording constructs, plasmids, and results in an ELN/LIMS | `alterlab-benchling` |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-proteinmpnn`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

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

The API uses a **draft → submit → confirm quote** flow: create an experiment (it starts as `draft`), submit it (Adaptyv then generates a quote asynchronously; status `waiting_for_confirmation`), and confirm the quote to create the invoice. `sequences` is a `{label: amino_acid_string}` map (values may also be objects such as `{"aa_string": "...", "control": true}`; multi-chain constructs join chains with a colon, e.g. `"heavy:light"`).

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
            "experiment_type": "affinity",   # screening|affinity|thermostability|fluorescence|expression|epitope_binning|enzyme_activity
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

# 2. Submit the reviewed draft; the quote is generated asynchronously afterwards
requests.post(f"{base_url}/experiments/{experiment_id}/submit", headers=headers).raise_for_status()

# 3. Poll GET /experiments/{id}/quote until it exists, review totals/expiry, then accept it
#    (creates the invoice; the JSON body is required even when empty)
quote = requests.get(f"{base_url}/experiments/{experiment_id}/quote", headers=headers)
requests.post(f"{base_url}/experiments/{experiment_id}/quote/confirm",
              headers=headers, json={}).raise_for_status()
```

## Available Experiment Types
Foundry supports these `experiment_type` values:
- **screening** - Binding detection via biolayer interferometry (BLI) or SPR. Requires a target.
- **affinity** - Kinetic constants (KD, kon, koff) by BLI/SPR. Requires a target.
- **thermostability** - Melting temperature (Tm) via DSF. No target required.
- **fluorescence** - Fluorescence intensity. No target required.
- **expression** - Protein yield quantification. No target required.
- **epitope_binning** - Epitope grouping of binders; requires a target and 4–28 sequences in multiples of 4.
- **enzyme_activity** - Enzyme activity assay. No target required.

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

## Scripts and API Reference
- `scripts/validate_submission.py` — **keyless** offline validator for an experiment submission (the per-type/method/sequence contract); no token.
For complete API documentation including all endpoints, request/response formats, and authentication details, see `reference/api_reference.md`.

## Examples
For concrete code examples covering common use cases (experiment submission, status tracking, result retrieval, batch processing), see `reference/examples.md`.

## Important Notes
- The Foundry API is public but still evolving — treat the OpenAPI doc (`/api/v1/openapi.json`) as the source of truth and verify field names before relying on them.
- Submission is staged: create a `draft` (optionally price it first with `POST /experiments/cost-estimate`), `POST .../submit`, then review and `POST .../quote/confirm`. Nothing is invoiced until the quote is confirmed. `skip_draft` / `auto_accept_quote` on create exist for pre-validated automated pipelines — use them only when the user has approved the spend.
- `affinity`/`screening`/`epitope_binning` require a `target_id` from the catalog (`GET /targets`) and `affinity`/`screening` also a `method` (`bli`|`spr`); `thermostability`, `fluorescence`, `expression`, and `enzyme_activity` take neither.
- Authentication is `Authorization: Bearer <token>`; `GET /whoami` confirms which organization a token acts for.
- Turnaround is multiple weeks — read the estimate from the experiment/quote rather than assuming a fixed number.
- Support and docs: support@adaptyvbio.com / `https://docs.adaptyvbio.com`.
- Suitable for high-throughput AI-driven protein design workflows (closed-loop design → test → learn).

Part of the AlterLab Academic Skills suite.
