---
name: alterlab-bgpt-search
description: Search scientific papers and retrieve structured experimental evidence extracted from full-text studies via the BGPT MCP server (`search_papers`, plus `lookup_paper` by DOI), returning 25+ fields per paper (methods, results, sample sizes, quality scores, limitations, conclusions). Use when running a literature review or evidence synthesis, or when needing experimental details (sample sizes, effect sizes, methods, quality scores) that abstracts alone do not provide. Part of the AlterLab Academic Skills suite.
allowed-tools: Bash
license: MIT
compatibility: Connects to the remote BGPT MCP server (SSE or Streamable HTTP). The first 50 results are free with no API key; after that a paid BGPT key from bgpt.pro/mcp ($0.02 per result returned). Requires network access.
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    skill-source: https://github.com/connerlambden/bgpt-mcp
    last_updated: "2026-09-23"
---

# BGPT Paper Search

## Overview

BGPT is a remote MCP server that searches a curated database of scientific papers built from raw experimental data extracted from full-text studies. Unlike traditional literature databases that return titles and abstracts, BGPT returns structured data from the actual paper content — methods, quantitative results, sample sizes, quality assessments, and 25+ metadata fields per paper — organized as "evidence units" that link each claim to the experiment, reported statistics, scope, and provenance behind it.

## When to Use This Skill

Use BGPT when the value is in structured full-text experimental data, not titles/abstracts:
- Building evidence tables for a meta-analysis, scoping review, or clinical guideline
- Extracting sample sizes, effect sizes, methods, protocols, or conclusions across studies
- Comparing methodologies, or filtering papers by quality score / evidence grading
- Pulling the structured record for one known paper by DOI (`lookup_paper`)

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Real-time, web-grounded summary of recent news or developments | `alterlab-perplexity` |
| Broad biomedical title/abstract search by MeSH terms or PMIDs | `alterlab-pubmed` |
| Building an evidence table from PDFs you already have on disk | `alterlab-pdf-extract` |
| Full systematic review with PRISMA screening and risk-of-bias assessment | `alterlab-literature-review` |
| Organizing references or exporting BibTeX from a Zotero library | `alterlab-pyzotero` |

## Setup

BGPT is a hosted remote MCP server — no local installation required. It offers two transports:

| Transport | Endpoint |
|-----------|----------|
| SSE | `https://bgpt.pro/mcp/sse` |
| Streamable HTTP | `https://bgpt.pro/mcp/stream` |

### Claude Code

```bash
claude mcp add --transport sse bgpt https://bgpt.pro/mcp/sse
# or Streamable HTTP:
claude mcp add --transport http bgpt https://bgpt.pro/mcp/stream
```

### Other MCP clients

Clients that accept a remote server URL (Cursor, Cline, Windsurf, and similar):

```json
{
  "mcpServers": {
    "bgpt": { "url": "https://bgpt.pro/mcp/sse" }
  }
}
```

Clients that can only launch a local command can use the `bgpt-mcp` npm bridge instead: `"command": "npx", "args": ["-y", "bgpt-mcp"]`.

## Usage

The server exposes two tools:

| Tool | Parameters |
|------|------------|
| `search_papers` | `query` (required); `num_results` (1–100, default 16); `days_back` (only papers from the last N days); `output_format` (`evidence`, `full`, or `legacy`) |
| `lookup_paper` | `doi` (required); `output_format` |

```
Search BGPT for: "CRISPR gene editing efficiency in human cells", 10 results
```

Each result carries:
- **Title, authors, journal, year, DOI**
- **Methods**: experimental techniques, models, protocols
- **Results**: key findings with quantitative data and reported statistics
- **Sample sizes**: number of subjects/samples
- **Quality scores**: study quality assessments
- **Limitations and conclusions**, with provenance back to the source sections

Without an MCP client, the same search is available over plain HTTP: `POST https://bgpt.pro/api/mcp-search` with a JSON body `{"query": ..., "num_results": ..., "output_format": "evidence"}` (add `"api_key"` after the free tier).

**Verify before pooling.** BGPT fields are machine-extracted, so check the sample sizes, effect sizes, and quality judgements you rely on against the source paper before they enter a meta-analysis or guideline table — an extraction error propagates silently into the pooled estimate. Cite the papers themselves (by DOI), not BGPT.

## Pricing

- **Free tier**: the first 50 results, no API key required
- **Pay-as-you-go**: $0.02 per result actually returned (not per search), with an API key from [bgpt.pro/mcp](https://bgpt.pro/mcp) — set `num_results` deliberately, since every returned record is billed

## Complementary Skills

Pairs well with:
- `alterlab-literature-review` — gather structured data with BGPT, then synthesize
- `alterlab-pubmed` — PubMed for broad discovery, BGPT for deep experimental data
- `alterlab-biorxiv` — combine preprint discovery with full-text data extraction
- `alterlab-pyzotero` — manage citations from BGPT search results

Part of the AlterLab Academic Skills suite.
