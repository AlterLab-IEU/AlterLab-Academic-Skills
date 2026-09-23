---
name: alterlab-research-lookup
description: Look up current research and scholarly papers by auto-routing each query to the best backend — the Parallel Web Systems Chat API (general research) or Perplexity sonar-pro-search via OpenRouter (academic paper searches) — and save every result with citations to sources/. Use when finding papers, gathering research data, verifying scientific claims, or assembling citation lists and unsure which search backend fits. For plain general web search or extracting content from a known URL prefer alterlab-parallel-web; to call Perplexity directly with a chosen Sonar model prefer alterlab-perplexity. Part of the AlterLab Academic Skills suite.
allowed-tools: Read Write Edit Bash
license: MIT
compatibility: At least one of PARALLEL_API_KEY (Parallel Chat API) or OPENROUTER_API_KEY (Perplexity via OpenRouter); both recommended. Python packages openai and requests; queries are sent to those services.
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# Research Information Lookup

## Overview

This skill provides real-time research information lookup with **intelligent backend routing**:

- **Parallel Chat API** (`core` model): Default backend for all general research queries. Provides comprehensive, multi-source research reports with inline citations via the OpenAI-compatible Chat API (Beta, `https://api.parallel.ai/v1beta/chat/completions`).
- **Perplexity sonar-pro-search** (via OpenRouter): Used only for academic-specific paper searches where scholarly database access is critical.

The skill automatically detects query type and routes to the optimal backend.

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

## Automatic Backend Selection

The skill automatically routes queries to the best backend based on content:

### Routing Logic

```
Query arrives
    |
    +-- Contains academic keywords? (papers, DOI, journal, peer-reviewed, etc.)
    |       YES --> Perplexity sonar-pro-search (academic search mode)
    |
    +-- Everything else (general research, market data, technical info, analysis)
            --> Parallel Chat API (core model)
```

### Academic Keywords (Routes to Perplexity)

Queries containing these terms are routed to Perplexity for academic-focused search:

- Paper finding: `find papers`, `find articles`, `research papers on`, `published studies`
- Citations: `cite`, `citation`, `doi`, `pubmed`, `pmid`
- Academic sources: `peer-reviewed`, `journal article`, `scholarly`, `arxiv`, `preprint`
- Review types: `systematic review`, `meta-analysis`, `literature search`
- Paper quality: `foundational papers`, `seminal papers`, `landmark papers`, `highly cited`

### Everything Else (Routes to Parallel)

All other queries go to the Parallel Chat API (core model), including:

- General research questions
- Market and industry analysis
- Technical information and documentation
- Current events and recent developments
- Comparative analysis
- Statistical data retrieval
- Complex analytical queries

### Manual Override

You can force a specific backend:

```bash
# Force Parallel Deep Research
python scripts/research_lookup.py "your query" --force-backend parallel

# Force Perplexity academic search
python scripts/research_lookup.py "your query" --force-backend perplexity
```

---

## Core Capabilities

### 1. General Research Queries (Parallel Chat API)

**Default backend.** Provides comprehensive, multi-source research with citations via the Chat API (`core` model).

```
Query Examples:
- "Recent advances in CRISPR gene editing 2025"
- "Compare mRNA vaccines vs traditional vaccines for cancer treatment"
- "AI adoption in healthcare industry statistics"
- "Global renewable energy market trends and projections"
- "Explain the mechanism underlying gut microbiome and depression"
```

**Response includes:**
- Comprehensive research report in markdown
- Inline citations from authoritative web sources
- Structured sections with key findings
- Multiple perspectives and data points
- Source URLs for verification

### 2. Academic Paper Search (Perplexity sonar-pro-search)

**Used for academic-specific queries.** Prioritizes scholarly databases and peer-reviewed sources.

```
Query Examples:
- "Find papers on transformer attention mechanisms in NeurIPS 2024"
- "Foundational papers on quantum error correction"
- "Systematic review of immunotherapy in non-small cell lung cancer"
- "Cite the original BERT paper and its most influential follow-ups"
- "Published studies on CRISPR off-target effects in clinical trials"
```

**Response includes:**
- Summary of key findings from academic literature
- 5-8 high-quality citations with authors, titles, journals, years, DOIs
- Citation counts and venue tier indicators
- Key statistics and methodology highlights
- Research gaps and future directions

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

### Environment Variables

```bash
# Primary backend (Parallel Chat API)
export PARALLEL_API_KEY="your_parallel_api_key"

# Academic search backend (Perplexity via OpenRouter)
export OPENROUTER_API_KEY="your_openrouter_api_key"
```

At least one key is required; with only one, every query goes to that backend.

### API Specifications

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

```bash
# Auto-routed research (recommended)
python scripts/research_lookup.py "your query" -o sources/research_YYYYMMDD_HHMMSS_<topic>.md

# Force specific backend
python scripts/research_lookup.py "your query" --force-backend parallel -o sources/research_<topic>.md
python scripts/research_lookup.py "your query" --force-backend perplexity -o sources/papers_<topic>.md

# JSON output
python scripts/research_lookup.py "your query" --json -o sources/research_<topic>.json

# Batch queries
python scripts/research_lookup.py --batch "query 1" "query 2" "query 3" -o sources/batch_research_<topic>.md
```

---

## Save All Results to the Sources Folder

Save every research-lookup result to the project's `sources/` folder. Results cost money to obtain, and the saved file is what lets you (and reviewers) trace each citation back to the raw search output.

### Saving Rules

| Backend | `-o` Flag Target | Filename Pattern |
|---------|-----------------|------------------|
| Parallel Deep Research | `sources/research_<topic>.md` | `research_YYYYMMDD_HHMMSS_<brief_topic>.md` |
| Perplexity (academic) | `sources/papers_<topic>.md` | `papers_YYYYMMDD_HHMMSS_<brief_topic>.md` |
| Batch queries | `sources/batch_<topic>.md` | `batch_research_YYYYMMDD_HHMMSS_<brief_topic>.md` |

### How to Save

Pass `-o` pointing into `sources/` on every call, and keep the citations, source URLs, and DOIs in the saved file — they are the audit trail. The default text output already includes a `Sources` section (title, date, URL for each source) and an `Additional References` section (DOIs and academic URLs extracted from the response text); use `--json` for the full citation metadata.

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
- Parallel Chat API (core model): Complex queries may take up to 5 minutes
- Perplexity: Information cutoff, may not access full text behind paywalls
- Both: Cannot access proprietary or restricted databases

**Fallback Behavior:**
- If the preferred backend's API key is missing (including a `--force-backend` choice), the query goes to the other backend
- A call that fails is not retried on the other backend; the result carries `success: false` and the error — rerun with `--force-backend` to try the other one
- Rephrase queries for better results if the initial response is insufficient

Backend-key setup and specific error messages: see `references/troubleshooting.md`.

---

## Usage Examples

### Example 1: General Research (Routes to Parallel)

**Query**: "Recent advances in transformer attention mechanisms 2025"

**Backend**: Parallel Chat API (core model)

**Response**: Comprehensive markdown report with citations from authoritative sources, covering recent papers, key innovations, and performance benchmarks.

### Example 2: Academic Paper Search (Routes to Perplexity)

**Query**: "Find papers on CRISPR off-target effects in clinical trials"

**Backend**: Perplexity sonar-pro-search (academic mode)

**Response**: Curated list of 5-8 high-impact papers with full citations, DOIs, citation counts, and venue tier indicators.

### Example 3: Comparative Analysis (Routes to Parallel)

**Query**: "Compare and contrast mRNA vaccines vs traditional vaccines for cancer treatment"

**Backend**: Parallel Chat API (core model)

**Response**: Detailed comparative report with data from multiple sources, structured analysis, and cited evidence.

### Example 4: Market Data (Routes to Parallel)

**Query**: "Global AI adoption in healthcare statistics 2025"

**Backend**: Parallel Chat API (core model)

**Response**: Current market data, adoption rates, growth projections, and regional analysis with source citations.

---

## Summary

This skill serves as the primary research interface with intelligent dual-backend routing:

- **Parallel Chat API** (default, `core` model): Comprehensive, multi-source research for any topic
- **Perplexity sonar-pro-search**: Academic-specific paper searches only
- **Automatic routing**: Detects academic queries and routes appropriately
- **Manual override**: Force any backend when needed
- **Complementary**: Works alongside `alterlab-parallel-web` for web search and URL extraction

Part of the AlterLab Academic Skills suite.
