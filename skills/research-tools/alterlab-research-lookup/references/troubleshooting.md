# Research Lookup — Setup & Troubleshooting

Backend setup and common failure modes for `scripts/research_lookup.py`. Loaded on demand from the SKILL.md Error Handling section.

## Setup

Nothing is required: with no key the script uses the keyless scholarly backend
(`scripts/scholarly_backend.py`, Python standard library only), and general web questions are
answered with WebSearch/WebFetch. Two paid backends are optional:

```bash
export PARALLEL_API_KEY="your_parallel_api_key"      # optional: Parallel Chat API reports
export OPENROUTER_API_KEY="your_openrouter_api_key"  # optional: Perplexity academic answers
```

Python deps for those routes only: `openai` (Parallel Chat API client) and `requests`
(Perplexity HTTP calls).

`lookup.py` is a thin single-query wrapper used by the Claude Code integration; the CLI
in `scripts/research_lookup.py` is the full interface (batch, force-backend, JSON, file output).

## Troubleshooting

- **"--force-backend parallel needs PARALLEL_API_KEY" / "... perplexity needs
  OPENROUTER_API_KEY"** — the user asked for a paid backend whose key is not set. Nothing was
  written. Ask them to set the key, or use `--force-backend scholarly` / the keyless web lookup
  and say which route answered.
- **"Sources that did not answer: openalex: HTTP 429 (keyless daily budget spent)"** — OpenAlex
  meters keyless search per IP; the other indexes still answered. Nothing to fix.
- **"semanticscholar: HTTP 429"** — Semantic Scholar's shared keyless pool is busy; rerun later
  or ignore (Crossref, Europe PMC and arXiv still answered).
- **"every source failed"** — no network to the indexes; check connectivity
  (`curl -sS "https://api.crossref.org/works?rows=1"`).
- **"no records matched"** — the routing-word filter left too little or too much; pass
  `--terms` with the field's own vocabulary (quoted phrases and `OR` work in Europe PMC).
- **Classic paper missing from the list** — keyword ranking is not citation-network search; use
  `--rank cited`, add its title to `--terms`, or confirm it by DOI
  (`https://api.crossref.org/works/<DOI>`). For the network around a known paper use
  `alterlab-citation-graph`.
- **Parallel query times out** — `core`-model queries can take up to several minutes; the
  script uses long timeouts. Rephrase or narrow if it stalls.
- **Perplexity rate limit / 4xx** — check OpenRouter credits and that your key has
  Perplexity access.
