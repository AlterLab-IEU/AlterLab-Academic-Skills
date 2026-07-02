# Research Lookup — Setup & Troubleshooting

Backend-key setup and common failure modes for `scripts/research_lookup.py`. Loaded on demand from the SKILL.md Error Handling section.

## Setup

Set at least one backend key (both recommended):

```bash
export PARALLEL_API_KEY="your_parallel_api_key"      # primary backend
export OPENROUTER_API_KEY="your_openrouter_api_key"  # academic search + fallback
```

Python deps: `openai` (Parallel Chat API client) and `requests` (Perplexity HTTP calls).

`lookup.py` is a thin single-query wrapper used by the Claude Code integration; the CLI
in `scripts/research_lookup.py` is the full interface (batch, force-backend, JSON, file output).

## Troubleshooting

- **"no backend API key set"** — set `PARALLEL_API_KEY` and/or `OPENROUTER_API_KEY`.
- **Parallel query times out** — `core`-model queries can take up to several minutes; the
  script uses long timeouts. Rephrase or narrow if it stalls.
- **Perplexity rate limit / 4xx** — check OpenRouter credits and that your key has
  Perplexity access.
- **No relevant results** — make the query more specific, add a time frame (e.g.
  "2024-2025"), or use academic keywords to force the Perplexity path.
