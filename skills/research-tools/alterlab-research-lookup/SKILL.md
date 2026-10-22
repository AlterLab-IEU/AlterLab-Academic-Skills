---
name: alterlab-research-lookup
description: Look up current research and scholarly papers by auto-routing each query to the best backend and saving every result with citations to sources/. Keyless by default — paper searches go to the built-in scholarly backend (Crossref, Europe PMC, arXiv, Semantic Scholar, OpenAlex index records with real DOIs, venues and citation counts) and general questions to Claude's WebSearch and WebFetch; the Parallel Chat API and Perplexity sonar-pro-search via OpenRouter are optional backends used when their keys are set. Use when finding papers, gathering research data, verifying scientific claims, or assembling citation lists and unsure which search backend fits. For plain general web search or extracting content from a known URL prefer alterlab-parallel-web; to call Perplexity directly with a chosen Sonar model prefer alterlab-perplexity. Part of the AlterLab Academic Skills suite.
allowed-tools: Read Write Edit Bash WebSearch WebFetch
license: MIT
compatibility: No API key required. The scholarly backend is stdlib Python that queries Crossref, Europe PMC, arXiv, Semantic Scholar and OpenAlex keyless; general web questions use Claude's WebSearch/WebFetch. Optional backends, used only when their keys are set or forced - PARALLEL_API_KEY (Parallel Chat API, openai package) and OPENROUTER_API_KEY (Perplexity, requests package) - send queries to those services.
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    last_updated: "2026-10-22"
    credentials: "optional: PARALLEL_API_KEY (Parallel Chat API synthesized web research reports; paid), OPENROUTER_API_KEY (Perplexity sonar-pro-search synthesized academic answers via OpenRouter; paid). Neither is needed: the keyless scholarly backend and WebSearch/WebFetch do the lookup without them"
---

# Research Information Lookup

## Overview

This skill provides real-time research information lookup with **intelligent backend routing**, and it works with no API key:

- **Scholarly backend** (keyless, default for paper searches): `scripts/research_lookup.py` queries Crossref, Europe PMC, arXiv, Semantic Scholar and OpenAlex, merges the hits by DOI, and returns index records — title, authors, year, venue, DOI, each index's citation count, an abstract snippet — ordered by influence (or relevance for "recent/latest" requests). You read the records, open the papers you cite, and write the synthesis.
- **Keyless web lookup** (default for general questions — statistics, market data, news, documentation): you run the search with WebSearch, open the sources with WebFetch, and save the result to `sources/` (procedure below).
- **Parallel Chat API** (`core` model, optional, `PARALLEL_API_KEY`): synthesized multi-source web research reports with inline citations (`https://api.parallel.ai/v1beta/chat/completions`).
- **Perplexity sonar-pro-search** (optional, `OPENROUTER_API_KEY`): synthesized academic answers with citations.

The skill detects the query type and routes it; keys only add the two paid backends.

## When to Use This Skill

Use this skill when you need:

- **Current Research Information**: Latest studies, papers, and findings
- **Literature Verification**: Check facts, statistics, or claims against current research
- **Background Research**: Gather context and supporting evidence for scientific writing
- **Citation Sources**: Find relevant papers and studies to cite
- **Technical Documentation**: Look up specifications, protocols, or methodologies
- **Market/Industry Data**: Current statistics, trends, competitive intelligence
- **Recent Developments**: Emerging trends, breakthroughs, announcements

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| You specifically want Perplexity (choosing a Sonar model yourself), no routing | `alterlab-perplexity` |
| Extracting or verifying the content of a known URL, or calling Parallel's Search/Task APIs directly | `alterlab-parallel-web` |
| Structured per-paper experimental data (sample sizes, effect sizes, quality scores) | `alterlab-bgpt-search` |
| Mapping the citation network around a seed paper | `alterlab-citation-graph` |
| A systematic review with PRISMA screening and risk-of-bias assessment | `alterlab-literature-review` |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-perplexity`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

## Automatic Backend Selection

The skill automatically routes queries to the best backend based on content:

### Routing Logic

```
Query arrives
    |
    +-- Contains academic keywords? (papers, DOI, journal, peer-reviewed, etc.)
    |       OPENROUTER_API_KEY set --> Perplexity sonar-pro-search (academic mode)
    |       otherwise              --> scholarly backend (keyless index records)
    |
    +-- Everything else (general research, market data, technical info, statistics)
            PARALLEL_API_KEY set   --> Parallel Chat API (core model)
            OPENROUTER_API_KEY set --> Perplexity
            no key                 --> keyless web lookup with WebSearch/WebFetch (you);
                                       the script, if run, returns papers only and says so
```

With no key at all — the usual case — paper searches run the script and everything else is a WebSearch/WebFetch lookup that you do yourself. The script prints the route it took on stderr.

### Academic Keywords (paper-search route)

Queries containing these terms take the paper-search route (Perplexity with its key, the scholarly backend without):

- Paper finding: `find papers`, `find articles`, `research papers on`, `published studies`
- Citations: `cite`, `citation`, `doi`, `pubmed`, `pmid`
- Academic sources: `peer-reviewed`, `journal article`, `scholarly`, `arxiv`, `preprint`
- Review types: `systematic review`, `meta-analysis`, `literature search`
- Paper quality: `foundational papers`, `seminal papers`, `landmark papers`, `highly cited`

### Everything Else (general route)

General research questions, market and industry analysis, technical documentation, current events, comparative analysis and statistics go to Parallel when its key is set, and otherwise to the keyless web lookup.

### Manual Override

You can force a specific backend:

```bash
# Keyless scholarly backend, whatever the query or keys
python scripts/research_lookup.py "your query" --force-backend scholarly

# Paid backends: only when the user asks for them (or their key is set and you want them)
python scripts/research_lookup.py "your query" --force-backend parallel
python scripts/research_lookup.py "your query" --force-backend perplexity
```

A forced paid backend whose key is missing exits 1 with a message naming the variable and the keyless alternatives; it never answers from another backend and writes nothing to `-o`. Tell the user which key is missing, then offer (or, if they only wanted results, run) the keyless route and label it as such.

## Keyless Web Lookup (general questions, no key)

For statistics, market data, news, policy and documentation, do the lookup with Claude's own tools, keeping the same standards the paid backends promise:

1. **Plan.** Turn the question into 2–4 specific searches (entity + measure + year + likely publisher, e.g. `CDC National Diabetes Statistics Report prevalence`). Prefer primary publishers: agencies, statistical offices, registries, the journal itself.
2. **Search** with WebSearch; note the result URLs and their dates.
3. **Open what you will cite** with WebFetch — the primary page, not a news summary of it. A number you could not see on the page itself is marked "from a search snippet, not verified".
4. **Answer** with every figure attributed inline (publisher, document, year, URL) and the retrieval date; say which figure is the most recent official one and flag disagreements between sources.
5. **Save** a `sources/research_YYYYMMDD_HHMMSS_<topic>.md` file with Write: the question, the searches run, the retrieval date, the answer, and a numbered source list (title, publisher, date, URL, the exact sentence or table cell each figure came from).

For academic claims inside a general question, run the scholarly backend as well and cite the papers by DOI.

---

## Core Capabilities

### 1. Academic Paper Search (scholarly backend, keyless; Perplexity with its key)

```
Query Examples:
- "Find papers on transformer attention mechanisms in NeurIPS 2024"
- "Foundational papers on quantum error correction"
- "Systematic review of immunotherapy in non-small cell lung cancer"
- "Cite the original BERT paper and its most influential follow-ups"
- "Published studies on CRISPR off-target effects in clinical trials"
```

**Keyless procedure:**
1. Run `python scripts/research_lookup.py "<request>" -o sources/papers_YYYYMMDD_HHMMSS_<topic>.md`. It drops routing words ("find peer-reviewed papers on … with DOIs") before searching; pass `--terms '"exact phrase" OR "synonym"'` when you know the field's vocabulary, `--rank cited` to surface influential work (the default unless the request says recent/latest or names a year), `--limit N` for more records.
2. Read the records: they are real index entries (DOI, venue, year, the citation count each index reports, an abstract snippet), not generated citations. Keyword ranking can miss a field's classic — if you know it (e.g. the original BERT paper), confirm it with a DOI or title lookup (`--terms` with its title, or `https://api.crossref.org/works/<DOI>`) rather than citing from memory.
3. Open each paper you summarise (WebFetch the DOI or the Europe PMC record) before stating its findings; the abstract snippet is enough only for a one-line description.
4. Write 5–8 high-quality citations with authors, titles, venues, years, DOIs and citation counts (say which index each count is from), key findings and methods, and research gaps — the same response Perplexity's academic mode gives.

**With `OPENROUTER_API_KEY`:** the same query goes to Perplexity sonar-pro-search, which returns a synthesized answer with sources; still open what you cite.

### 2. General Research Queries (keyless web lookup; Parallel with its key)

```
Query Examples:
- "Recent advances in CRISPR gene editing 2025"
- "Compare mRNA vaccines vs traditional vaccines for cancer treatment"
- "AI adoption in healthcare industry statistics"
- "Global renewable energy market trends and projections"
```

Without a key, follow **Keyless Web Lookup** above. With `PARALLEL_API_KEY`, the script's Parallel route returns a multi-source markdown report with inline citations, sections, and source URLs.

### 3. Technical and Methodological Information

```
Query Examples:
- "Western blot protocol for protein detection"
- "Statistical power analysis for clinical trials"
- "Machine learning model evaluation metrics comparison"
```

### 4. Statistical and Market Data

```
Query Examples:
- "Prevalence of diabetes in US population 2025"
- "Global AI market size and growth projections"
- "COVID-19 vaccination rates by country"
```

---

## Paper Quality and Popularity Prioritization

When searching for papers, favor high-quality, influential work, but treat citation counts and venue as rough proxies rather than measures of quality: they lag for recent papers, vary widely by field, and under-represent null results, regional journals, and non-English work. Judge each paper on its design and evidence (see `alterlab-scientific-thinking`), and include a lower-profile paper when it is the most direct evidence for the claim. The thresholds below are working heuristics, not established cut-offs.

### Citation-Based Ranking

| Paper Age | Citation Threshold | Classification |
|-----------|-------------------|----------------|
| 0-3 years | 20+ citations | Noteworthy |
| 0-3 years | 100+ citations | Highly Influential |
| 3-7 years | 100+ citations | Significant |
| 3-7 years | 500+ citations | Landmark Paper |
| 7+ years | 500+ citations | Seminal Work |
| 7+ years | 1000+ citations | Foundational |

### Venue Quality Tiers

**Tier 1 - Premier Venues** (prefer when relevant):
- **General Science**: Nature, Science, Cell, PNAS
- **Medicine**: NEJM, Lancet, JAMA, BMJ
- **Field-Specific**: Nature Medicine, Nature Biotechnology, Nature Methods
- **Top CS/AI**: NeurIPS, ICML, ICLR, ACL, CVPR

**Tier 2 - High-Impact Specialized** (Strong preference):
- Journals with Impact Factor > 10
- Top conferences in subfields (EMNLP, NAACL, ECCV, MICCAI)

**Tier 3 - Respected Specialized** (Include when relevant):
- Journals with Impact Factor 5-10

---

## Technical Integration

### Environment Variables (all optional)

```bash
# Optional paid backend for general research (Parallel Chat API)
export PARALLEL_API_KEY="your_parallel_api_key"

# Optional paid backend for academic answers (Perplexity via OpenRouter)
export OPENROUTER_API_KEY="your_openrouter_api_key"
```

No key is needed. Ask the user to set a key themselves (never paste it into chat) only when they want that paid backend.

### API Specifications

**Scholarly backend (keyless, `scripts/scholarly_backend.py`, stdlib only):**
- Crossref `api.crossref.org/works` (`query.bibliographic`, `is-referenced-by-count`), Europe PMC REST (`TITLE_ABS:` query, `sort=CITED desc` in cited mode), arXiv `export.arxiv.org/api/query`, Semantic Scholar `graph/v1/paper/search` (keyless pool, one retry on 429), OpenAlex `works?search=` (metered per IP; skipped with a note on 429)
- A source that fails is listed under "Sources that did not answer"; the rest still return. Every record is merged by DOI and keeps each index's citation count separately
- Checked live 2026-10-22: "microplastics in human placenta" returned Ragusa et al. 2021, *Environment International*, DOI 10.1016/j.envint.2020.106274, first; `--terms '"testing effect" OR "retrieval practice"'` returned Roediger & Karpicke 2006, DOI 10.1111/j.1467-9280.2006.01693.x, first

**Parallel Chat API (Beta):**
- Endpoint: `POST https://api.parallel.ai/v1beta/chat/completions` (OpenAI SDK with `base_url="https://api.parallel.ai/v1beta"`)
- Model: `core` (60s-5min latency, complex multi-source synthesis)
- Output: Markdown text with inline citations
- Citations: Research basis with source URLs and excerpts
- Rate limit: 300 requests/min by default
- Python package: `openai`

**Perplexity sonar-pro-search:**
- Model: `perplexity/sonar-pro-search` (via OpenRouter; $3/$15 per million tokens plus $18 per 1,000 requests at 2026-09 list prices)
- Sends `web_search_options.search_context_size: high` and Perplexity's `search_mode: academic`; OpenRouter may not forward the latter, so academic-only sourcing is best-effort
- Sources come back as `url_citation` annotations and/or `citations`/`search_results` fields; the script merges and deduplicates them
- The script waits up to 90 s per request
- Python package: `requests`

### Command-Line Usage

The keyless route needs only the Python standard library. The optional Parallel route imports `openai` and the Perplexity route uses `requests`; where they are not installed, prefix those commands with `uv run --python ">=3.11" --with openai --with requests` instead of installing anything.

```bash
# Auto-routed research (recommended)
python scripts/research_lookup.py "your query" -o sources/research_YYYYMMDD_HHMMSS_<topic>.md

# Paper search with exact terms, influence order, 15 records (keyless)
python scripts/research_lookup.py "find papers" --terms '"testing effect" OR "retrieval practice"' \
  --rank cited --limit 15 -o sources/papers_<topic>.md

# Force specific backend
python scripts/research_lookup.py "your query" --force-backend scholarly -o sources/papers_<topic>.md
python scripts/research_lookup.py "your query" --force-backend parallel -o sources/research_<topic>.md
python scripts/research_lookup.py "your query" --force-backend perplexity -o sources/papers_<topic>.md

# JSON output
python scripts/research_lookup.py "your query" --json -o sources/research_<topic>.json

# Batch queries
python scripts/research_lookup.py --batch "query 1" "query 2" "query 3" -o sources/batch_research_<topic>.md
```

---

## Save All Results to the Sources Folder

Save every research-lookup result to the project's `sources/` folder. The saved file is what lets you (and reviewers) trace each citation back to the raw search output, and paid backends cost money per call.

### Saving Rules

| Backend | Target | Filename Pattern |
|---------|--------|------------------|
| Scholarly backend (keyless) | `-o sources/papers_<topic>.md` | `papers_YYYYMMDD_HHMMSS_<brief_topic>.md` |
| Keyless web lookup (WebSearch/WebFetch) | Write `sources/research_<topic>.md` | `research_YYYYMMDD_HHMMSS_<brief_topic>.md` |
| Parallel Deep Research | `-o sources/research_<topic>.md` | `research_YYYYMMDD_HHMMSS_<brief_topic>.md` |
| Perplexity (academic) | `-o sources/papers_<topic>.md` | `papers_YYYYMMDD_HHMMSS_<brief_topic>.md` |
| Batch queries | `-o sources/batch_<topic>.md` | `batch_research_YYYYMMDD_HHMMSS_<brief_topic>.md` |

### How to Save

Pass `-o` pointing into `sources/` on every script call (create the folder first), and keep the citations, source URLs, and DOIs in the saved file — they are the audit trail. A failed or refused call writes nothing, so a file in `sources/` always holds real results. The default text output already includes a `Sources` section (title, date, URL for each source) and an `Additional References` section (DOIs); use `--json` for the full citation metadata. For a keyless web lookup, write the file yourself in the shape described under Keyless Web Lookup.

```bash
# General research — save to sources/ (includes Sources + Additional References sections)
python scripts/research_lookup.py "Recent advances in CRISPR gene editing 2025" \
  -o sources/research_20250217_143000_crispr_advances.md

# Academic paper search — save to sources/ (includes paper citations with DOIs)
python scripts/research_lookup.py "Find papers on transformer attention mechanisms in NeurIPS 2024" \
  -o sources/papers_20250217_143500_transformer_attention.md

# JSON format for maximum citation metadata (full citation objects with URLs, DOIs, snippets)
python scripts/research_lookup.py "CRISPR clinical trials" --json \
  -o sources/research_20250217_143000_crispr_trials.json

# Forced backend — save to sources/
python scripts/research_lookup.py "AI regulation landscape" --force-backend parallel \
  -o sources/research_20250217_144000_ai_regulation.md

# Batch queries — save to sources/
python scripts/research_lookup.py --batch "mRNA vaccines efficacy" "mRNA vaccines safety" \
  -o sources/batch_research_20250217_144500_mrna_vaccines.md
```

### Citation Preservation in Saved Files

Each output format preserves citations differently:

| Format | Citations Included | When to Use |
|--------|-------------------|-------------|
| Text (default) | `Sources (N):` section with `[title] (date) + URL` + `Additional References (N):` with DOIs and academic URLs | Standard use — human-readable with all citations |
| JSON (`--json`) | Full citation objects: `url`, `title`, `date`, `snippet`, `doi`, `type` | When you need maximum citation metadata |

**For the scholarly backend**, saved files include: the numbered index records (title, authors, year, venue, DOI, per-index citation counts, impact label, abstract snippet) + Sources list + DOIs, and which indexes did not answer.
**For Parallel backend**, saved files include: research report + Sources list (title, URL) + Additional References (DOIs, academic URLs).
**For Perplexity backend**, saved files include: academic summary + Sources list (title, date, URL, snippet) + Additional References (DOIs, academic URLs).

**Use `--json` when you need to:**
- Parse citation metadata programmatically
- Preserve full DOI and URL data for BibTeX generation
- Maintain the structured citation objects for cross-referencing

### Why Save Everything

1. **Reproducibility**: Every citation and claim can be traced back to its raw research source
2. **Context Window Recovery**: If context is compacted, saved results can be re-read without re-querying
3. **Audit Trail**: The `sources/` folder documents exactly how all research information was gathered
4. **Reuse Across Sections**: Multiple sections can reference the same saved research without duplicate queries
5. **Cost Efficiency**: Check `sources/` for existing results before making new API calls
6. **Peer Review Support**: Reviewers can verify the research backing every citation

### Before Making a New Query, Check Sources First

Before calling `research_lookup.py`, check if a relevant result already exists:

```bash
ls sources/  # Check existing saved results
```

If a prior lookup covers the same topic, re-read the saved file instead of making a new API call.

### Logging

When saving research results, always log:

```
[HH:MM:SS] SAVED: Research lookup to sources/research_20250217_143000_crispr_advances.md (3,800 words, 8 citations)
[HH:MM:SS] SAVED: Paper search to sources/papers_20250217_143500_transformer_attention.md (6 papers found)
```

---

## Integration with Scientific Writing

This skill supports scientific writing by providing (each result saved to `sources/`):

1. **Literature Review Support**: Gather current research for introduction and discussion
2. **Methods Validation**: Verify protocols against current standards
3. **Results Contextualization**: Compare findings with recent similar studies
4. **Discussion Enhancement**: Support arguments with latest evidence
5. **Citation Management**: Provide properly formatted citations

Treat returned citations as leads: open and check any paper before citing it, because search-model answers can misattribute findings or garble bibliographic details (`alterlab-citation-verifier` checks that references exist).

## Complementary Tools

| Task | Skill |
|------|------|
| Scholarly index search (OpenAlex) | `alterlab-openalex` |
| PubMed search | `alterlab-pubmed` |
| Zotero library / DOI-to-BibTeX management | `alterlab-pyzotero` |
| Verify that the references you collected exist | `alterlab-citation-verifier` |

---

## Error Handling and Limitations

**Known Limitations:**
- Scholarly backend: keyword search, so a field's classic can rank below newer work — use `--terms` and `--rank cited`, and confirm known classics by DOI; Europe PMC citation counts cover only its own corpus; OpenAlex search is skipped when the shared per-IP budget is spent and Semantic Scholar's keyless pool can 429 (both reported, never silent)
- Parallel Chat API (core model): Complex queries may take up to 5 minutes
- Perplexity: Information cutoff, may not access full text behind paywalls
- All: Cannot access proprietary or restricted databases

**Fallback Behavior:**
- Auto-routing without a key uses the keyless scholarly backend (and, for general questions, tells you on stderr to use WebSearch/WebFetch)
- A `--force-backend parallel|perplexity` whose key is missing exits 1 naming the variable; it never answers from another backend
- A call that fails is not retried on another backend; the result carries `success: false`, the error goes to stderr, and the script exits 1 — rerun with `--force-backend` to try another
- Rephrase queries (or pass `--terms`) for better results if the initial response is insufficient

Backend-key setup and specific error messages: see `references/troubleshooting.md`.

---

## Usage Examples

| Query | No key (default) | With keys |
|-------|------------------|-----------|
| "Find papers on CRISPR off-target effects in clinical trials" | Scholarly backend → `sources/papers_…md`; you open and summarise 5–8 papers with DOIs and citation counts | Perplexity sonar-pro-search (academic mode) |
| "Global AI adoption in healthcare statistics 2025" | Keyless web lookup: WebSearch → WebFetch the primary reports → Write `sources/research_…md` | Parallel Chat API (core model) |
| "Compare mRNA vaccines vs traditional vaccines for cancer treatment" | Web lookup for the overview plus the scholarly backend for the trials and reviews you cite | Parallel Chat API (core model) |

---

## Summary

This skill is the primary research interface with intelligent routing, keyless by default:

- **Scholarly backend** (keyless): real index records from five open scholarly indexes for paper searches
- **Keyless web lookup**: WebSearch + WebFetch with saved, cited sources for everything else
- **Parallel Chat API / Perplexity sonar-pro-search** (optional keys): synthesized reports and academic answers
- **Manual override**: force any backend; a forced paid backend never silently falls back
- **Complementary**: Works alongside `alterlab-parallel-web` for web search and URL extraction

Part of the AlterLab Academic Skills suite.
