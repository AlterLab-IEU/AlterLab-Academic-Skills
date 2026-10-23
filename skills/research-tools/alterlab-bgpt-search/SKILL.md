---
name: alterlab-bgpt-search
description: Search scientific papers and retrieve structured experimental evidence from their full text — methods, results, sample sizes, effect sizes, risk-of-bias / quality assessment, limitations and conclusions, 25+ fields per paper, each value traced to the section it came from. Keyless by default — finds open-access studies in Europe PMC / PubMed Central, pulls their full text with the bundled script, and Claude extracts the fields; the BGPT MCP server (search_papers, lookup_paper by DOI) is an optional backend for its pre-extracted records (first 50 results free, then BGPT_API_KEY). Use when running a literature review or evidence synthesis, or when needing experimental details (sample sizes, effect sizes, methods, quality scores) that abstracts alone do not provide. Part of the AlterLab Academic Skills suite.
allowed-tools: Read Write WebFetch WebSearch Bash
license: MIT
compatibility: No API key required. The default path fetches open-access full text from Europe PMC / PubMed Central with a stdlib script (keyless REST) and Claude does the field extraction. Optional BGPT backend - the remote BGPT MCP server or its HTTP endpoint; the first 50 results per network are free, then BGPT_API_KEY ($0.02 per result). Network access to ebi.ac.uk (and bgpt.pro for BGPT).
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    skill-source: https://github.com/connerlambden/bgpt-mcp
    last_updated: "2026-10-22"
    credentials: "optional: BGPT_API_KEY (BGPT's pre-extracted 25+ field records beyond its 50-result free tier; $0.02 per result returned). Never needed: the keyless Europe PMC full-text path produces the same evidence fields"
---

# Full-Text Evidence Search (BGPT-style)

## Overview

This skill returns what abstracts leave out: structured data from the actual paper content — methods, quantitative results, sample sizes, quality assessments and 25+ fields per paper — organized as **evidence units** that link each claim to the experiment, reported statistics, scope and provenance behind it.

It works with **no API key**. The default path searches Europe PMC for open-access studies whose full text is available, downloads that full text (`scripts/fulltext_evidence.py`, Python standard library only), and you extract the fields from the paper itself, quoting the sentence or table each value came from. [BGPT](https://bgpt.pro/mcp), a remote MCP server with a curated database of pre-extracted records, is an optional backend when the user asks for it.

## When to Use This Skill

Use it when the value is in structured full-text experimental data, not titles/abstracts:
- Building evidence tables for a meta-analysis, scoping review, or clinical guideline
- Extracting sample sizes, effect sizes, methods, protocols, or conclusions across studies
- Comparing methodologies, or grading papers by study quality / risk of bias
- Pulling the structured record for one known paper by DOI, PMID or PMCID

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Real-time, web-grounded summary of recent news or developments | `alterlab-perplexity` |
| Broad biomedical title/abstract search by MeSH terms or PMIDs | `alterlab-pubmed` |
| Building an evidence table from PDFs you already have on disk | `alterlab-pdf-extract` |
| Full systematic review with PRISMA screening and risk-of-bias assessment | `alterlab-literature-review` |
| Organizing references or exporting BibTeX from a Zotero library | `alterlab-pyzotero` |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-perplexity`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

## Default Path: Open-Access Full Text + Your Extraction (no key)

```bash
S=scripts/fulltext_evidence.py   # relative to this skill's directory; stdlib only

# 1. Find studies whose full text Europe PMC serves (title/abstract match, open access)
python $S search "mindfulness anxiety" --design rct --since 2015 --sort cited --n 10

# 2. Download full text as Markdown (PMCID, DOI or PMID; DOIs/PMIDs are resolved)
python $S fetch PMC4648965 10.1002/hsr2.73154 --out evidence/

# Or both at once, plus an empty evidence_table.csv with the field columns below
python $S evidence "statin primary prevention" --design rct --sort cited --n 5 --out evidence/
```

`--design rct|meta|any` filters by publication type, `--sort relevance|cited|date`. Each `evidence/<PMCID>.md` holds the metadata (DOI, PMCID, PMID, licence), abstract, every body section, tables as pipe tables, figure captions, and the funding / conflict-of-interest sections; the reference list is dropped. A study with no open full text is reported as `SKIPPED` — say so, use its abstract only with an explicit "abstract only" label, or ask for the PDF (`alterlab-pdf-extract`).

**3. Extract the evidence record.** Read each Markdown file (Read) and fill one record per study. Take every number from the Methods, Results or a table — never from the abstract when the body gives more detail — and keep a provenance quote for each:

| Group | Fields |
|-------|--------|
| Identity | PMCID, DOI, first author + year, title, journal |
| Design | study design, setting / country, registration ID, randomisation and allocation concealment, blinding |
| Population | eligibility, **N randomised / enrolled**, **N analysed** (per arm), attrition and reasons |
| Intervention | intervention (dose, frequency, duration), comparator, adherence |
| Outcomes | primary outcome + instrument, time points, **effect estimate with its metric** (MD, SMD/d/g, OR/RR/HR, partial η²) and 95% CI, p value, secondary outcomes, adverse events |
| Appraisal | risk-of-bias tool (RoB 2 for RCTs, ROBINS-I for non-randomised, JBI / NOS otherwise) and per-domain judgement with reason, analysis population (ITT vs per-protocol), funding, conflicts of interest |
| Interpretation | limitations the authors state, authors' conclusion, your caveats |
| Provenance | `section › quote` for every value above |

Mark a field the paper does not report as **not reported** — never infer it. Write the table to `evidence/evidence_table.csv` (or Markdown) with Write and give the user the per-study records, the cross-study table, and the gaps.

**Quality judgements are yours, so show the reasoning.** A risk-of-bias call cites the specific features (e.g. "per-protocol analysis of 53/57 randomised; participants and providers unblinded; self-report outcomes → RoB 2 'some concerns' for D2 and D4"). Do not present a single numeric "quality score" as if a tool produced it.

**Coverage.** Europe PMC's open-access subset is large but not complete: many paywalled journals (NEJM, most JAMA, Lancet) have no open full text. When a key study is missing, say so and offer the abstract-level record, the user's PDF, or the optional BGPT backend.

## Optional: BGPT Backend (pre-extracted records)

Use BGPT when the user asks for it or wants its curated database. It is a hosted remote MCP server; no local installation:

| Transport | Endpoint |
|-----------|----------|
| SSE | `https://bgpt.pro/mcp/sse` |
| Streamable HTTP | `https://bgpt.pro/mcp/stream` |

```bash
claude mcp add --transport sse bgpt https://bgpt.pro/mcp/sse
# or Streamable HTTP:
claude mcp add --transport http bgpt https://bgpt.pro/mcp/stream
```

Clients that accept a remote server URL (Cursor, Cline, Windsurf, and similar) use `{"mcpServers": {"bgpt": {"url": "https://bgpt.pro/mcp/sse"}}}`; clients that can only launch a local command can use the `bgpt-mcp` npm bridge: `"command": "npx", "args": ["-y", "bgpt-mcp"]`.

| Tool | Parameters |
|------|------------|
| `search_papers` | `query` (required); `num_results` (1–100, default 16); `days_back` (only papers from the last N days); `output_format` (`evidence`, `full`, or `legacy`) |
| `lookup_paper` | `doi` (required); `output_format` |

Each BGPT result carries title, authors, journal, year, DOI, methods, results with reported statistics, sample sizes, quality scores, limitations and conclusions, with provenance to source sections.

Without an MCP client, the same search is available over plain HTTP: `POST https://bgpt.pro/api/mcp-search` with a JSON body `{"query": ..., "num_results": ..., "output_format": "evidence"}`. After the free tier, add `"api_key"` (also a `search_papers` argument) with the value of the `BGPT_API_KEY` environment variable; ask the user to set that variable rather than paste the key into the chat. **HTTP 402** means the free results are used up (checked 2026-10-22 from a shared network: `{"error": "Free tier limit reached (50 results)..."}`); 401 means the key is wrong. On 402 without a key, tell the user and continue on the default path, labelled as Europe PMC full-text extraction — never present it as BGPT output.

Pricing: the first 50 results are free with no key; then $0.02 per result actually returned (not per search), with a key from [bgpt.pro/mcp](https://bgpt.pro/mcp) — set `num_results` deliberately.

## Verify Before Pooling

Both paths are machine-assisted: BGPT fields are machine-extracted, and your own extraction can misread a table. Check every sample size, effect size and quality judgement you rely on against the source section before it enters a meta-analysis or guideline table — an extraction error propagates silently into the pooled estimate. Cite the papers themselves (by DOI), not BGPT or Europe PMC.

## Complementary Skills

Pairs well with:
- `alterlab-literature-review` — gather structured data here, then synthesize
- `alterlab-pubmed` — PubMed for broad discovery, this skill for deep experimental data
- `alterlab-biorxiv` — combine preprint discovery with full-text data extraction
- `alterlab-pyzotero` — manage citations from the search results

Part of the AlterLab Academic Skills suite.
