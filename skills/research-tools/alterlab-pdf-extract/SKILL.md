---
name: alterlab-pdf-extract
description: Free Elicit-columns analog — ingest N PDFs (or any MarkItDown-supported document) and build a per-paper evidence table with user-defined columns, one row per paper and one column per attribute/question you want pulled from every source. Use when extracting structured data across many papers into a comparison table or data-extraction sheet (sample size, methods, main finding, effect, population/intervention/outcome, limitations), screening a corpus into a spreadsheet, or pulling the same fields from a stack of PDFs into CSV/Markdown. Routes conversion through MarkItDown; offline heuristic backend by default, optional LLM backend for precise answers. Part of the AlterLab Academic Skills suite.
allowed-tools: Read Write Edit Bash
license: MIT
compatibility: markitdown (uv pip install 'markitdown[all]') required for conversion; optional llm backend needs the openai client + OPENROUTER_API_KEY (or OPENAI_API_KEY/OPENAI_BASE_URL)
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# PDF Extract — User-Defined Evidence Tables

## Overview

The free analog of Elicit's "columns" feature. Point it at a stack of PDFs, declare the
columns you care about, and get back a tidy evidence table — **one row per paper, one
column per question** — as CSV or a Markdown table. Built for data extraction across a
corpus: literature screening, methods comparison, PICO/sample-size pulls, and review
evidence sheets.

Every input is normalized to clean Markdown via Microsoft **MarkItDown** (see the
`alterlab-markitdown` skill) before any column is extracted, so PDF, DOCX, PPTX, HTML, and
the other MarkItDown formats all work.

## When to Use

- Extracting the **same fields from many papers** into a comparison table or spreadsheet.
- Building a data-extraction sheet for a review (sample size, design, intervention,
  outcome, effect size, limitations).
- Screening a folder of PDFs into a CSV you can sort/filter.
- Any "make me a table where each row is a paper and each column is X" request.

**Not for:** searching databases to *find* papers, or synthesizing a narrative review.
Discovering literature and writing the prose synthesis is `alterlab-literature-review`'s
job — this skill operates on PDFs you already have and produces a structured table, not
prose. Use it *after* you have the papers.

## Quick Start

```bash
SCRIPT=skills/research-tools/alterlab-pdf-extract/scripts/extract_to_table.py

# Heuristic backend: use 'label:question' so the question carries the words the
# papers actually use — overlap is lexical, so a bare label like "Sample size"
# rarely matches "we enrolled 240 participants" (see Backends below).
uv run python "$SCRIPT" papers/*.pdf \
    --column "Sample size:how many participants were enrolled" \
    --column "Main finding:primary result reported" \
    --column "Limitations:study limitations weaknesses" --format md

# Columns with explicit extraction questions, CSV to a file:
uv run python "$SCRIPT" a.pdf b.pdf \
    --column "n:how many participants were enrolled" \
    --column "effect:what was the main reported effect size" \
    --format csv -o evidence.csv

# Precise LLM-backed extraction (needs OPENROUTER_API_KEY) — label-only columns
# are fine here, since the model reads the paper rather than matching keywords:
uv run python "$SCRIPT" lit/*.pdf \
    --columns "Population" "Intervention" "Outcome" --backend llm
```

## Defining Columns

A column is a **label** plus the **question** that drives extraction. Two ways to declare:

| Spec form | Meaning |
|-----------|---------|
| `"Sample size"` | label == question; keywords come from the label |
| `"n:how many participants"` | label `n`, question `how many participants` |

Use `--columns` for a space-separated list of simple labels, and repeat `--column` for
specs that need an explicit question. Both combine; duplicate labels are rejected.

## Backends

- **heuristic** (default, offline, free): for each column, scores Markdown sentences by
  **literal keyword overlap** with the column spec and emits the best evidence snippet.
  Deterministic — good for a first pass, screening, and reproducible runs. Returns an empty
  cell when no sentence shares a keyword.
  **Gotcha:** matching is lexical, not semantic. A generic label like `"Sample size"`
  tokenizes to `sample`, `size` — which never appears in "we enrolled 240 participants", so
  the cell comes back empty. For the heuristic backend, phrase columns as `Label:question`
  where the question uses the **words the papers actually use** (`participants`, `enrolled`,
  `cohort`, `n=`). Quantitative questions also get a small ranking bonus for sentences
  containing digits when the question itself contains a digit or `%`. When you only have
  generic labels, use the `llm` backend instead.
- **llm** (optional, precise): sends the converted Markdown plus all column questions to an
  OpenAI-compatible endpoint (OpenRouter by default) for a concise per-column answer
  (`N/A` when the paper is silent). The model ID follows the **ALTERLAB_MODEL** convention
  (`skills/core/shared/model_env.md`): `$ALTERLAB_MODEL`, else the dated default. Override
  per-run with `--model`.

## Output

- `--format md` → GitHub-flavored Markdown table (pipes in cell text are escaped).
- `--format csv` → CSV via `csv.DictWriter`.
- `-o FILE` writes to disk (UTF-8); otherwise the table goes to stdout.

The first column is always `Source` (the input filename); a file that fails conversion
yields an `ERROR` row so the table stays aligned.

## Pipeline Fit

`alterlab-pdf-extract` sits downstream of paper discovery and upstream of synthesis:

1. Find papers — database/search skills (`alterlab-literature-review`, search backends).
2. **Extract the evidence table — this skill.**
3. Synthesize / write up — `alterlab-literature-review`, `alterlab-paper-writer`.

## Files

- `scripts/extract_to_table.py` — the CLI. `--help` lists every flag; `--columns` /
  `--column` define the table; `--backend`, `--format`, `--model`, `-o` control extraction
  and output.
