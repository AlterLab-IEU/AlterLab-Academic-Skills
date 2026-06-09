# Research Lookup Skill

Real-time research lookup with automatic dual-backend routing:

- **Parallel Chat API** (`core` model) — default for all general research, market/technical/statistical queries.
- **Perplexity `sonar-pro-search`** (via OpenRouter) — academic-specific paper searches (DOIs, peer-reviewed sources, citations).

The router inspects each query for academic keywords (see `ACADEMIC_KEYWORDS` in
`scripts/research_lookup.py`) and sends those to Perplexity; everything else goes
to Parallel. See `SKILL.md` for the full routing rules, save-to-`sources/`
workflow, and paper-quality ranking.

## Setup

Set at least one backend key (both recommended):

```bash
export PARALLEL_API_KEY="your_parallel_api_key"      # primary backend
export OPENROUTER_API_KEY="your_openrouter_api_key"  # academic search + fallback
```

Python deps: `openai` (Parallel Chat API client) and `requests` (Perplexity HTTP calls).

## Usage

```bash
# Auto-routed query (recommended) — save to the project's sources/ folder
python scripts/research_lookup.py "latest advances in quantum computing 2025" \
  -o sources/research_quantum.md

# Academic paper search (auto-routes to Perplexity)
python scripts/research_lookup.py "find papers on CRISPR off-target effects" \
  -o sources/papers_crispr.md

# Force a backend
python scripts/research_lookup.py "topic" --force-backend parallel
python scripts/research_lookup.py "topic" --force-backend perplexity

# Batch queries / JSON output
python scripts/research_lookup.py --batch "query 1" "query 2" -o sources/batch.md
python scripts/research_lookup.py "topic" --json -o sources/research.json
```

`lookup.py` is a thin single-query wrapper used by the Claude Code integration;
the CLI in `scripts/research_lookup.py` is the full interface (batch, force-backend,
JSON, file output).

## Troubleshooting

- **"no backend API key set"** — set `PARALLEL_API_KEY` and/or `OPENROUTER_API_KEY`.
- **Parallel query times out** — `core`-model queries can take up to several minutes; the script uses long timeouts. Rephrase or narrow if it stalls.
- **Perplexity rate limit / 4xx** — check OpenRouter credits and that your key has Perplexity access.
- **No relevant results** — make the query more specific, add a time frame (e.g. "2024-2025"), or use academic keywords to force the Perplexity path.

This skill is part of the AlterLab Academic Skills suite. For direct
single-backend Perplexity search use the `alterlab-perplexity` skill; for
Zotero/BibTeX reference management use `alterlab-pyzotero`.
