---
name: alterlab-parallel-web
description: Search the web, run multi-source deep research, and extract what a known URL actually says, saving every result with its sources to sources/. Keyless by default — Claude's WebSearch and WebFetch run the same search / research / extract workflow; Parallel Web Systems (Chat API `base`/`core` research models with inline citations, Extract API v1, plus notes on the Search, Task and Responses APIs) is an optional backend when the user asks for Parallel and sets PARALLEL_API_KEY. Use when running general web searches, current-events/market/technical lookups, broad information gathering, comprehensive research reports, or verifying a specific URL's content. For scholarly paper retrieval or dual-backend academic lookup prefer alterlab-research-lookup instead. Part of the AlterLab Academic Skills suite.
allowed-tools: Read Write Edit Bash WebSearch WebFetch
license: MIT
compatibility: No API key required. search, research and extract run on Claude's WebSearch and WebFetch and save to sources/. Optional Parallel backend - PARALLEL_API_KEY plus the openai and parallel-web >= 1.0 packages (resolved per call by uv) - sends queries and URLs to api.parallel.ai.
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    last_updated: "2026-10-22"
    credentials: "optional: PARALLEL_API_KEY (Parallel Chat API synthesized search/research reports and Extract API v1; paid, used only when the user asks for Parallel)"
---

# Web Search, Research and Extraction (Parallel-style)

## Overview

This skill handles general web information in the scientific-writing workflow — news, market and technical data, documentation, policy — with three jobs: **search**, **deep research**, and **extract** (verify what a known URL says). Scholarly paper retrieval goes to `alterlab-research-lookup`.

**Default (no API key):** you do all three with WebSearch and WebFetch, following the procedures below, and save every result to `sources/`.
**Optional backend:** [Parallel Web Systems](https://docs.parallel.ai) — Chat API (Beta, OpenAI-compatible, `POST /v1beta/chat/completions`) for synthesized search and research, Extract API v1 (`POST /v1/extract`) for URL content — through `scripts/parallel_web.py`, when the user asks for Parallel. Its key (`PARALLEL_API_KEY`, from https://platform.parallel.ai) only adds that service.

## When to Use This Skill

Use this skill for:

- **Web Search**: queries that need current information from the internet
- **Deep Research**: comprehensive, multi-source research reports on a topic
- **Market Research**: industry analysis, competitive intelligence, market data
- **Current Events**: news, recent developments, announcements
- **Technical Information**: documentation, specifications, product details
- **Statistical Data**: market sizes, growth rates, industry figures

Use extract only for citation verification (confirming what a specific URL says) and for cases where you need raw content from a known URL.

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Finding peer-reviewed papers to cite; academic queries auto-routed to Perplexity | `alterlab-research-lookup` |
| You specifically want Perplexity Sonar models (e.g. `sonar-pro-search`) | `alterlab-perplexity` |
| Google Scholar / PubMed lookups and DOI → BibTeX conversion | `alterlab-citation-mgmt` |
| A consulting-style market research report (frameworks, LaTeX, 50+ pages) | `alterlab-market-research` |
| A systematic literature review with PRISMA screening | `alterlab-literature-review` |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-research-lookup`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

---

## Default Path: the Three Jobs with WebSearch and WebFetch (no key)

Check `sources/` first (`ls sources/`); if a saved result covers the question, re-read it instead of searching again.

### 1. Web Search

1. Write 2–4 specific queries (entity + measure + date + likely publisher) and run them with WebSearch.
2. Open the 3–6 most authoritative results with WebFetch — official, primary and dated pages over aggregators and SEO pages. A fact seen only in a search snippet is labelled "snippet, not opened".
3. Answer as a **synthesized summary organized by themes**, every fact with an inline citation `[n]`, then a numbered sources list (title, publisher, date, URL, retrieval date). Flag disagreements between sources instead of picking one silently.
4. Write the result to `sources/search_YYYYMMDD_HHMMSS_<brief_topic>.md` (format below).

### 2. Deep Research

Same as search, scaled up for a report: plan the sub-questions first (e.g. market size, players and shares, growth projections, policy, risks); run several searches per sub-question; open 8–15 sources across publisher types (official statistics, company filings, regulators, reputable trade and news outlets, peer-reviewed reviews via `alterlab-research-lookup` when the topic has them); then write an executive summary, themed sections with specific figures (each with its source and year), implications or outlook, and a limitations note (paywalled sources you could not open, figures that conflict). Save as `sources/research_YYYYMMDD_HHMMSS_<brief_topic>.md`.

### 3. URL Extraction (verification only)

WebFetch the exact URL with a prompt naming what to verify (e.g. "quote the methods section verbatim", "list each corollary as written"). Follow a DOI or redirect to the publisher page. Report the passages **verbatim in quotation marks** with the section they come from, say plainly when the page does not contain the thing asked about, and save as `sources/extract_YYYYMMDD_HHMMSS_<brief_source>.md`. When a page will not load (paywall, 403, script-only), say so and try an open copy (Europe PMC, PubMed Central, the author's repository) rather than paraphrasing from memory.

### Saved-file format (keyless)

```markdown
# <search|research|extract>: <question or URL>
- Date: 2026-10-22 14:30 (UTC) · Tool: WebSearch + WebFetch (keyless)
- Queries: "<q1>", "<q2>"

## Result
<summary / report / verbatim extract with [n] citations>

## Sources
1. <Title> — <Publisher>, <date>. <URL> (opened: yes/snippet only) — "<quoted sentence or figure>"
```

## Optional Parallel Backend: Three Commands

Use these when the user asks for Parallel (or wants its synthesized reports) and `PARALLEL_API_KEY` is set. Without the key the script exits 1 before contacting anything, names the variable and the keyless alternative, and writes no `-o` file: say that the key is missing and offer the keyless path above, labelled as such. The commands below are written as `python scripts/parallel_web.py …`. Where `openai` / `parallel-web` are not installed, run each one with the uv prefix from Environment Setup below instead of installing anything.

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

| Operation | Target (Write keyless, `-o` with Parallel) | Filename Pattern |
|-----------|-----------------|------------------|
| Web Search | `sources/search_<topic>.md` | `search_YYYYMMDD_HHMMSS_<brief_topic>.md` |
| Deep Research | `sources/research_<topic>.md` | `research_YYYYMMDD_HHMMSS_<brief_topic>.md` |
| URL Extract | `sources/extract_<source>.md` | `extract_YYYYMMDD_HHMMSS_<brief_source>.md` |

On the keyless path, write the file with Write in the saved-file format above. With the Parallel backend, pass `-o` pointing into `sources/` on every call (a failed call writes nothing):

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

| Task | Tool (keyless default · optional Parallel) |
|------|------|
| Web search, current events, market/technical lookup | WebSearch + WebFetch · `parallel_web.py search` (this skill) |
| Comprehensive research report | planned WebSearch/WebFetch research · `parallel_web.py research --model core` (this skill) |
| Citation verification / DOI metadata from a known URL | WebFetch the URL · `parallel_web.py extract` (this skill) |
| Scholarly paper retrieval (peer-reviewed journals to cite) | `alterlab-research-lookup` (keyless scholarly backend) |
| Google Scholar / PubMed / CrossRef database search | `alterlab-citation-mgmt` |

When writing scientific documents: gather background with `search`/`research` before drafting a section, verify any specific URL with `extract`, and route purely academic paper searches to `alterlab-research-lookup`. Check `sources/` first and save every result back.

---

## Environment Setup (optional Parallel backend only)

The keyless path needs no setup. For the Parallel backend:

```bash
# Set your Parallel API key (ask the user to set it; never paste it into chat)
export PARALLEL_API_KEY="your_api_key_here"

# Python packages: openai (Chat API: search/research) and parallel-web >= 1.0
# (Extract API v1; imports as `parallel`). uv resolves both per call, so nothing is
# installed and no virtualenv is needed:
uv run --python ">=3.11" --with openai --with parallel-web python scripts/parallel_web.py search "query"
```

Get your API key at https://platform.parallel.ai. The script sends your queries and URLs to Parallel's servers.

---

## Error Handling

The script's classes return structured error responses rather than raising (`{"success": false, "error": ..., "timestamp": ...}`); the CLI prints the error to stderr, exits 1, and writes no `-o` file.

**Common issues:**
- `PARALLEL_API_KEY is not set`: the user asked for Parallel without a key — say so, and offer the keyless path (WebSearch / WebFetch) labelled as such
- A page WebFetch cannot open (paywall, 403): say so, look for an open copy, never paraphrase it from memory
- `openai not installed` / `parallel-web not installed`: rerun the command with the `uv run --python ">=3.11" --with openai --with parallel-web python …` prefix from Environment Setup
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
