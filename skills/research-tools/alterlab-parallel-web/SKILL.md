---
name: alterlab-parallel-web
description: Search the web, run deep research, and extract content from known URLs via Parallel Web Systems — the Chat API (Beta, OpenAI-compatible `base`/`core` research models) for synthesized answers with inline citations and the Extract API v1 for URL content — with notes on the raw Search, Task, and Responses APIs. Use when running general web searches, current-events/market/technical lookups, broad information gathering, comprehensive research reports, or verifying a specific URL's content (requires PARALLEL_API_KEY). For scholarly paper retrieval or dual-backend academic lookup that auto-routes to Perplexity prefer alterlab-research-lookup instead. Part of the AlterLab Academic Skills suite.
allowed-tools: Read Write Edit Bash
license: MIT
compatibility: PARALLEL_API_KEY required. Python packages openai (Chat API) and parallel-web >= 1.0 (Extract API v1); sends queries and URLs to api.parallel.ai.
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# Parallel Web Systems API

## Overview

This skill gives access to **Parallel Web Systems** APIs for web search, deep research, and content extraction. In the scientific-writing workflow it is the default tool for general web information — news, market and technical data, documentation — while scholarly paper retrieval goes to `alterlab-research-lookup`.

**Primary interface:** Chat API (Beta, OpenAI-compatible, `POST /v1beta/chat/completions`) for search and research.
**Secondary interface:** Extract API v1 (`POST /v1/extract`) for URL verification and special cases.

**API Documentation:** https://docs.parallel.ai
**API Key:** https://platform.parallel.ai
**Environment Variable:** `PARALLEL_API_KEY`

## When to Use This Skill

Use this skill for:

- **Web Search**: queries that need current information from the internet
- **Deep Research**: comprehensive, multi-source research reports on a topic
- **Market Research**: industry analysis, competitive intelligence, market data
- **Current Events**: news, recent developments, announcements
- **Technical Information**: documentation, specifications, product details
- **Statistical Data**: market sizes, growth rates, industry figures

Use the Extract API only for citation verification (confirming what a specific URL says) and for cases where you need raw content from a known URL.

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Finding peer-reviewed papers to cite; academic queries auto-routed to Perplexity | `alterlab-research-lookup` |
| You specifically want Perplexity Sonar models (e.g. `sonar-pro-search`) | `alterlab-perplexity` |
| Google Scholar / PubMed lookups and DOI → BibTeX conversion | `alterlab-citation-mgmt` |
| A consulting-style market research report (frameworks, LaTeX, 50+ pages) | `alterlab-market-research` |
| A systematic literature review with PRISMA screening | `alterlab-literature-review` |

---

## Three Capabilities

### 1. Web Search (`search` command)

Search the web via the Chat API (`base` model) and get a **synthesized summary** with cited sources.

**Best for:** General web searches, current events, fact-finding, technical lookups, news, market data.

```bash
# Basic search
python scripts/parallel_web.py search "latest advances in quantum computing 2025"

# Use core model for more complex queries
python scripts/parallel_web.py search "compare EV battery chemistries NMC vs LFP" --model core

# Save results to file
python scripts/parallel_web.py search "renewable energy policy updates" -o results.txt

# JSON output for programmatic use
python scripts/parallel_web.py search "AI regulation landscape" --json -o results.json
```

**Key Parameters:**
- `objective`: Natural language description of what you want to find
- `--model`: Chat model to use (`base` default, or `core` for deeper research)
- `-o`: Output file path
- `--json`: Output as JSON

**Response includes:** Synthesized summary organized by themes, with inline citations and a sources list.

### 2. Deep Research (`research` command)

Run comprehensive multi-source research via the Chat API (`core` model) that produces detailed reports with citations.

**Best for:** Market research, comprehensive analysis, competitive intelligence, technology surveys, industry reports, any question requiring synthesis of many sources.

```bash
# Default deep research (core model)
python scripts/parallel_web.py research "comprehensive analysis of the global EV battery market"

# Save research report to file
python scripts/parallel_web.py research "AI adoption in healthcare 2025" -o report.md

# Use base model for faster, lighter research
python scripts/parallel_web.py research "latest funding rounds in AI startups" --model base

# JSON output
python scripts/parallel_web.py research "renewable energy storage market in Europe" --json -o data.json
```

**Key Parameters:**
- `query`: Research question or topic
- `--model`: Chat model to use (`core` default for deep research, or `base` for faster results)
- `-o`: Output file path
- `--json`: Output as JSON

### 3. URL Extraction (`extract` command) — Verification Only

Extract content from specific URLs (up to 20 per call). Use it for citation verification and special cases; for general research, use `search` or `research`.

```bash
# Verify a citation's content
python scripts/parallel_web.py extract "https://example.com/article" --objective "key findings"

# Also return the full page as markdown (excerpts are always returned)
python scripts/parallel_web.py extract "https://docs.example.com/api" --full-content

# Save extraction to file
python scripts/parallel_web.py extract "https://paper-url.com" --objective "methodology" -o extracted.md
```

---

## Model Selection Guide

The script uses the Chat API research models: `base` for most searches and `core` for deep research.

| Model  | Latency    | Strengths                        | Use When                    |
|--------|------------|----------------------------------|-----------------------------|
| `base` | 15s-100s   | Standard research, factual queries | Web searches, quick lookups |
| `core` | 60s-5min   | Complex research, multi-source synthesis | Deep research, comprehensive reports |

- `search` defaults to `base` — fast, good for most queries
- `research` defaults to `core` — thorough, good for comprehensive reports
- Override with `--model` when you need a different depth/speed trade-off

Parallel also offers APIs the script does not wrap (see `references/api_reference.md`): the **Search API v1** (ranked URLs with excerpts, modes `turbo`/`fast`/`basic`/`advanced`, domain source policies), the **Task API** (async deep research with processors from `lite` to `ultra8x`), and the **Responses API** (OpenAI Responses-compatible, model `parallel` with `reasoning.effort` low/medium/high; launched July 2026, and the Chat API quickstart in Parallel's docs now redirects to it). Call those through the `parallel-web` SDK or HTTP when you need domain pinning, structured output, or async runs.

---

## Python API Usage

### Search

```python
from parallel_web import ParallelSearch

searcher = ParallelSearch()
result = searcher.search(
    objective="Find latest information about transformer architectures in NLP",
    model="base",
)

if result["success"]:
    print(result["response"])  # Synthesized summary
    for src in result["sources"]:
        print(f"  {src['title']}: {src['url']}")
```

### Deep Research

```python
from parallel_web import ParallelDeepResearch

researcher = ParallelDeepResearch()
result = researcher.research(
    query="Comprehensive analysis of AI regulation in the EU and US",
    model="core",
)

if result["success"]:
    print(result["response"])  # Full research report
    print(f"Citations: {result['citation_count']}")
```

### Extract (Verification Only)

```python
from parallel_web import ParallelExtract

extractor = ParallelExtract()
result = extractor.extract(
    urls=["https://docs.example.com/api-reference"],
    objective="API authentication methods and rate limits",
)

if result["success"]:
    for r in result["results"]:
        print(r["excerpts"])
```

---

## Save Results to the Sources Folder

Save every web search, deep research, and extraction result to the project's `sources/` folder. Saved results make each claim traceable to its raw source material (reproducibility, audit, peer review), let you recover context if the conversation is compacted, and avoid paying twice for the same query.

### Saving Rules

| Operation | `-o` Flag Target | Filename Pattern |
|-----------|-----------------|------------------|
| Web Search | `sources/search_<topic>.md` | `search_YYYYMMDD_HHMMSS_<brief_topic>.md` |
| Deep Research | `sources/research_<topic>.md` | `research_YYYYMMDD_HHMMSS_<brief_topic>.md` |
| URL Extract | `sources/extract_<source>.md` | `extract_YYYYMMDD_HHMMSS_<brief_source>.md` |

Pass `-o` pointing into `sources/` on every call:

```bash
# Web search
python scripts/parallel_web.py search "latest advances in quantum computing 2025" \
  -o sources/search_20250217_143000_quantum_computing.md

# Deep research
python scripts/parallel_web.py research "comprehensive analysis of the global EV battery market" \
  -o sources/research_20250217_144000_ev_battery_market.md

# URL extraction (verification only)
python scripts/parallel_web.py extract "https://example.com/article" --objective "key findings" \
  -o sources/extract_20250217_143500_example_article.md
```

Before a new query, check whether a relevant result already exists (`ls sources/`) and re-read it instead of calling the API again. After saving, log the file:

```
[HH:MM:SS] SAVED: Search results to sources/search_20250217_143000_quantum_computing.md
[HH:MM:SS] SAVED: Deep research report to sources/research_20250217_144000_ev_battery_market.md
```

---

## Routing

| Task | Tool |
|------|------|
| Web search, current events, market/technical lookup | `parallel_web.py search` (this skill) |
| Comprehensive research report | `parallel_web.py research --model core` (this skill) |
| Citation verification / DOI metadata from a known URL | `parallel_web.py extract` (this skill) |
| Scholarly paper retrieval (peer-reviewed journals to cite) | `alterlab-research-lookup` (routes to Perplexity) |
| Google Scholar / PubMed / CrossRef database search | `alterlab-citation-mgmt` |

When writing scientific documents: gather background with `search`/`research` before drafting a section, verify any specific URL with `extract`, and route purely academic paper searches to `alterlab-research-lookup`. Check `sources/` first and save every result back.

---

## Environment Setup

```bash
# Required: set your Parallel API key
export PARALLEL_API_KEY="your_api_key_here"

# Python packages
uv pip install openai          # Chat API (search/research)
uv pip install parallel-web    # Extract API v1 (>= 1.0; imports as `parallel`)
# Or run ad hoc without a venv:
#   uv run --with openai --with parallel-web scripts/parallel_web.py search "query"
```

Get your API key at https://platform.parallel.ai. The script sends your queries and URLs to Parallel's servers.

---

## Error Handling

The script returns structured error responses rather than raising:

```json
{
  "success": false,
  "error": "Error description",
  "timestamp": "2025-02-14 12:00:00"
}
```

**Common issues:**
- `PARALLEL_API_KEY not set`: set the environment variable
- `openai not installed`: run `uv pip install openai`
- `parallel-web not installed`: run `uv pip install parallel-web` (only needed for extract)
- `'BetaResource' object has no attribute 'extract'`: an old copy of the script is calling the Beta method removed in `parallel-web` 1.0 — use this skill's current script (`client.extract()`)
- Rate limit exceeded: wait and retry (defaults: Chat 300 requests/min, Extract 600 requests/min)

---

## Complementary Skills

See the Routing table above for `alterlab-research-lookup` (scholarly papers) and `alterlab-citation-mgmt` (Scholar/PubMed/CrossRef). Also:

| Skill | Use For |
|-------|---------|
| `alterlab-literature-review` | Systematic literature reviews across academic databases |
| `alterlab-scientific-schematics` | Generate diagrams from research findings |

Part of the AlterLab Academic Skills suite.
