---
name: alterlab-perplexity
description: "Run Perplexity-style grounded searches (answers where every claim cites a current source) for current information and recent literature. Keyless by default: Claude's WebSearch and WebFetch plus keyless scholarly APIs (Europe PMC, Crossref, arXiv) find and open the sources; Perplexity Sonar models (sonar, sonar-pro, sonar-pro-search agentic search, sonar-reasoning-pro) via LiteLLM and OpenRouter are an optional backend when the user asks for Perplexity and sets OPENROUTER_API_KEY. Use when searching for current information or recent scientific literature, getting answers grounded in cited sources, verifying a claim against current evidence, or reaching information beyond the model's training cutoff. This is the direct single-backend search: for automatic routing with results saved to sources/ use alterlab-research-lookup, and for structured per-paper experimental-data extraction (sample sizes, effect sizes, quality scores) use alterlab-bgpt-search. Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read Write WebFetch WebSearch Bash(curl:*) Bash(python:*) Bash(python3:*) Bash(uv run:*)
compatibility: No API key required. Grounded search runs on Claude's WebSearch and WebFetch plus keyless scholarly APIs (Europe PMC, Crossref, arXiv). Optional Perplexity backend - OPENROUTER_API_KEY and the litellm package, resolved per call by uv - sends queries to OpenRouter/Perplexity.
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    last_updated: "2026-10-22"
    credentials: "optional: OPENROUTER_API_KEY (Perplexity Sonar answers via OpenRouter, only when the user asks for Perplexity or a Sonar model; paid per token)"
---

# Perplexity-Style Grounded Search

Answer questions about current information, recent literature, and facts beyond the training cutoff with **web-grounded, citation-backed answers** — the Perplexity workflow: a sharp query, current sources, and an answer in which every claim points to a source the reader can open. It needs **no API key**: you search with WebSearch, read with WebFetch, and query keyless scholarly APIs for papers. Perplexity's own Sonar models (one OpenRouter key covers all of them) are an optional backend when the user asks for Perplexity.

## When to Use This Skill

Use for: current developments, latest publications, citation-grounded answers, verifying a claim against current sources, or anything past the training cutoff.

Skip for: arithmetic/logic, code execution, or facts well within training data (answer directly).

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Unsure which search backend fits; want automatic routing and results saved to `sources/` | `alterlab-research-lookup` |
| General web, market, or technical research via Parallel, or extracting a known URL | `alterlab-parallel-web` |
| Per-paper structured experimental data (sample sizes, effect sizes, quality scores) | `alterlab-bgpt-search` |
| Reproducible biomedical database search by MeSH terms or PMIDs | `alterlab-pubmed` |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-research-lookup`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

## Default Path: Grounded Search Without a Key

1. **Write the query like a good Sonar prompt** — domain + time frame + desired output + source preference ("RCTs on intermittent fasting and HbA1c in adults with type 2 diabetes, 2019–2025, peer-reviewed"). Split a compound question into 2–4 searches.
2. **Search.**
   - Current web (news, guidelines, agency figures, announcements): WebSearch.
   - Papers: keyless scholarly APIs, by curl or WebFetch —
     `https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=TITLE_ABS:(<terms>)&format=json&resultType=core&pageSize=10` (biomedicine, abstracts, `sort=CITED%20desc` for influential work; `DOI:"<doi>"` to fetch one record),
     `https://api.crossref.org/works?query.bibliographic=<terms>&rows=10` (every discipline, `is-referenced-by-count`; `/works/<DOI>` for one record),
     `https://export.arxiv.org/api/query?search_query=all:<word>+AND+all:<word>&max_results=10` (preprints).
     OpenAlex and Semantic Scholar also answer keyless but share small per-IP budgets (HTTP 429 when spent) — use them as extras, not the only source.
3. **Open what you cite.** WebFetch the primary page — the journal article or its Europe PMC record, the agency report, the trial registry — not a news summary of it. A claim seen only in a search snippet is labelled "snippet only, not verified".
4. **Answer grounded, the way Perplexity does:** a direct answer first, then the evidence with an inline citation `[n]` on every factual sentence, exact figures as the source states them (effect sizes with CIs, dates, counts), conflicts between sources flagged with which is stronger (evidence hierarchy: meta-analyses > RCTs > cohort > case reports > expert opinion), and a numbered source list: title, publisher/journal, year, DOI or URL, and the retrieval date. Cite the underlying sources, never "Perplexity" or "a search engine".
5. **Keep a record when asked** (or for anything the user will cite): Write `sources/search_YYYYMMDD_HHMMSS_<topic>.md` with the queries, retrieval date, the answer and the source list — the keyless equivalent of `--output results.json`.

If the user asked specifically for Perplexity and there is no key, say so in the first line ("Perplexity needs OPENROUTER_API_KEY, which is not set"), then — unless they only wanted Perplexity — give the keyless answer above, labelled as WebSearch-based, never presented as Perplexity output.

## Optional Backend: Perplexity Sonar via OpenRouter

Use it when the user asks for Perplexity or a specific Sonar model and `OPENROUTER_API_KEY` is set. Without the key the script exits 1 before sending anything and prints the keyless alternative.

### Setup (one-time)

```bash
# 1. Get a key at https://openrouter.ai/keys and add credits ($5+ recommended)
# 2. Configure (either form works; setup_env.py writes .env with owner-only permissions)
export OPENROUTER_API_KEY='sk-or-v1-your-key-here'
python scripts/setup_env.py --api-key sk-or-v1-your-key-here   # writes .env

# 3. Verify. LiteLLM needs no install step: uv resolves it per call, without a virtualenv
uv run --python ">=3.11" --with litellm python scripts/perplexity_search.py --check-setup
```

`--check-setup` reads the live environment, not `.env`. After `setup_env.py`, load the file with `set -a; source .env; set +a` (plain `source` does not export) or use python-dotenv, so the variable is actually in scope. Ask the user to set the key themselves rather than pasting it into the conversation. See `references/openrouter_setup.md` for full setup, security, and troubleshooting.

### Basic usage

```bash
uv run --python ">=3.11" --with litellm python scripts/perplexity_search.py "What are the latest developments in CRISPR gene editing?"
uv run --python ">=3.11" --with litellm python scripts/perplexity_search.py "Recent CAR-T therapy clinical trials" --output results.json
uv run --python ">=3.11" --with litellm python scripts/perplexity_search.py "Compare mRNA and viral vector vaccines" --model sonar-pro-search
uv run --python ">=3.11" --with litellm python scripts/perplexity_search.py "Quantum computing for drug discovery" --verbose
```

Where LiteLLM is already installed, plain `python scripts/perplexity_search.py …` works the same. The CLI takes the bare model name (e.g. `sonar-pro`); the script prepends `openrouter/perplexity/` automatically.

### Models

Select with `--model` (or set `DEFAULT_MODEL`):

| Model | Use it for |
|-------|------------|
| `sonar-pro` (default) | General research, balanced cost/quality |
| `sonar-pro-search` | Most advanced agentic, multi-step search; comprehensive comparisons. Highest cost; OpenRouter-exclusive |
| `sonar` | Simple fact lookups, cost-sensitive bulk queries |
| `sonar-reasoning-pro` | Tasks needing explicit step-by-step reasoning |

`sonar-reasoning` was retired on OpenRouter (not listed as of 2026-09-23) and the CLI no longer accepts it; a stale `DEFAULT_MODEL=sonar-reasoning` now fails fast with a clear error. See `references/model_comparison.md` for detailed trade-offs, pricing, context windows, and `sonar-deep-research` for programmatic use. On the keyless path, the equivalent of `sonar-pro-search` is simply more searches: plan sub-questions, search each, and open more sources before comparing.

### Programmatic access

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

Saved JSON (`--output`) carries `answer`, `model`, `usage`, and `citations` — a deduplicated list of `{url, title}` gathered from OpenRouter's `url_citation` annotations and Perplexity's `citations`/`search_results` fields, present when the model returns sources. Process with `jq '.answer'` or `jq '.citations[].url'`. Cite the underlying sources, not Perplexity, and open any source you quote: answers are generated summaries and can misattribute a claim.

### Cost

Pricing is per token (plus a per-request fee on `sonar-pro-search`); rough per-query order: `sonar` < `sonar-pro` < `sonar-reasoning-pro` < `sonar-pro-search`. Control spend by matching the model to the query, capping `--max-tokens`, and setting a spending limit in the OpenRouter dashboard. Monitor usage at https://openrouter.ai/activity. Exact rates: `references/model_comparison.md` and https://openrouter.ai/perplexity.

### Environment variables (optional backend only)

- `OPENROUTER_API_KEY` — needed by `scripts/perplexity_search.py`, not by the skill
- `DEFAULT_MODEL` (default `sonar-pro`), `DEFAULT_MAX_TOKENS` (default `4000`), `DEFAULT_TEMPERATURE` (default `0.2`) — honored as CLI defaults; override per call with the matching flag.

## Writing good queries

Be specific (domain + time frame + desired output). Examples that work well on both paths:

- "Latest clinical trial results for CAR-T therapy in B-cell lymphoma published in 2024"
- "Compare PyTorch vs TensorFlow for transformer training: ease of use, performance, ecosystem — with recent benchmarks"
- "Evidence for intermittent fasting on HbA1c in adults with type 2 diabetes; focus on RCTs"

Add source preferences ("peer-reviewed", "clinicaltrials.gov", "FDA-approved") for higher-quality grounding. Full query-design patterns, domain templates, and pitfalls live in `references/search_strategies.md`.

## Resources

- `scripts/perplexity_search.py` — optional Perplexity search CLI / importable function
- `scripts/setup_env.py` — key setup and validation for the optional backend
- `references/openrouter_setup.md` — setup, security, troubleshooting
- `references/model_comparison.md` — model selection and pricing
- `references/search_strategies.md` — query design (applies to both paths)
- `assets/.env.example` — environment template

Part of the AlterLab Academic Skills suite.
