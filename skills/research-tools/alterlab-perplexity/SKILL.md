---
name: alterlab-perplexity
description: "Run AI web searches with real-time, citation-grounded answers using Perplexity Sonar models (sonar, sonar-pro, sonar-pro-search agentic search, sonar-reasoning, sonar-reasoning-pro) via LiteLLM and a single OpenRouter API key. Use when searching for current information or recent scientific literature, getting answers grounded in cited web sources, verifying a claim against current evidence, or reaching information beyond the model's training cutoff. Requires an OpenRouter API key. This is the direct single-backend Perplexity tool: for automatic routing between Perplexity and other backends use alterlab-research-lookup, and for structured per-paper experimental-data extraction (sample sizes, effect sizes, quality scores) use alterlab-bgpt-search. Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read WebFetch WebSearch Bash(python:*)
compatibility: An OpenRouter API key is required to use Perplexity search
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# Perplexity Search

Run AI web searches using Perplexity Sonar models through LiteLLM and OpenRouter. Perplexity returns real-time, web-grounded answers with source citations — ideal for current information, recent literature, and facts beyond the model's training cutoff. One OpenRouter key covers all models; no separate Perplexity account needed.

## When to use

Use for: current developments, latest publications, citation-grounded answers, verifying a claim against current sources, or anything past the training cutoff.

Skip for: arithmetic/logic, code execution, or facts well within training data (answer directly). For automatic backend routing prefer `alterlab-research-lookup`; for per-paper structured experimental-data extraction prefer `alterlab-bgpt-search`.

## Setup (one-time)

```bash
# 1. Get a key at https://openrouter.ai/keys and add credits ($5+ recommended)
# 2. Configure (either form works)
export OPENROUTER_API_KEY='sk-or-v1-your-key-here'
python scripts/setup_env.py --api-key sk-or-v1-your-key-here   # writes .env

# 3. Install LiteLLM
uv pip install litellm

# 4. Verify
python scripts/perplexity_search.py --check-setup
```

`--check-setup` reads the live environment, not `.env`. After `setup_env.py`, `export OPENROUTER_API_KEY=...` (or use python-dotenv) so the variable is actually in scope. See `references/openrouter_setup.md` for full setup, security, and troubleshooting.

## Basic usage

```bash
python scripts/perplexity_search.py "What are the latest developments in CRISPR gene editing?"
python scripts/perplexity_search.py "Recent CAR-T therapy clinical trials" --output results.json
python scripts/perplexity_search.py "Compare mRNA and viral vector vaccines" --model sonar-pro-search
python scripts/perplexity_search.py "Quantum computing for drug discovery" --verbose
```

The CLI takes the bare model name (e.g. `sonar-pro`); the script prepends `openrouter/perplexity/` automatically.

## Models

Select with `--model` (or set `DEFAULT_MODEL`):

| Model | Use it for |
|-------|------------|
| `sonar-pro` (default) | General research, balanced cost/quality |
| `sonar-pro-search` | Most advanced agentic, multi-step search; comprehensive comparisons. Highest cost; OpenRouter-exclusive |
| `sonar` | Simple fact lookups, cost-sensitive bulk queries |
| `sonar-reasoning-pro` | Tasks needing explicit step-by-step reasoning |
| `sonar-reasoning` | Lighter reasoning at lower cost |

See `references/model_comparison.md` for detailed trade-offs, pricing, and performance.

## Writing good queries

Be specific (domain + time frame + desired output). Examples that work well:

- "Latest clinical trial results for CAR-T therapy in B-cell lymphoma published in 2024"
- "Compare PyTorch vs TensorFlow for transformer training: ease of use, performance, ecosystem — with recent benchmarks"
- "Evidence for intermittent fasting on HbA1c in adults with type 2 diabetes; focus on RCTs"

Add source preferences ("peer-reviewed", "clinicaltrials.gov", "FDA-approved") for higher-quality grounding. Full query-design patterns, domain templates, and pitfalls live in `references/search_strategies.md`.

## Programmatic access

```python
from scripts.perplexity_search import search_with_perplexity

result = search_with_perplexity(
    query="What are the latest CRISPR developments?",
    model="openrouter/perplexity/sonar-pro",  # full path required when calling directly
    max_tokens=4000,
    temperature=0.2,
)
if result["success"]:
    print(result["answer"])
    print(f"Tokens: {result['usage']['total_tokens']}")
else:
    print(f"Error: {result['error']}")
```

Saved JSON (`--output`) carries `answer`, `model`, `usage`, and `citations` (when the model returns them); process with `jq '.answer'`.

## Cost

Pricing is per token (plus a per-request fee on `sonar-pro-search`); rough per-query order: `sonar` < `sonar-pro` < `sonar-reasoning-pro` < `sonar-pro-search`. Control spend by matching the model to the query, capping `--max-tokens`, and setting a spending limit in the OpenRouter dashboard. Monitor usage at https://openrouter.ai/activity. Exact rates: `references/model_comparison.md` and https://openrouter.ai/perplexity.

## Environment variables

- `OPENROUTER_API_KEY` (required)
- `DEFAULT_MODEL` (default `sonar-pro`), `DEFAULT_MAX_TOKENS` (default `4000`), `DEFAULT_TEMPERATURE` (default `0.2`) — honored as CLI defaults; override per call with the matching flag.

## Resources

- `scripts/perplexity_search.py` — search CLI / importable function
- `scripts/setup_env.py` — key setup and validation
- `references/openrouter_setup.md` — setup, security, troubleshooting
- `references/model_comparison.md` — model selection and pricing
- `references/search_strategies.md` — query design
- `assets/.env.example` — environment template

