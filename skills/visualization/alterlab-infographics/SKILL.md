---
name: alterlab-infographics
description: "Creates professional infographics with Nano Banana Pro AI and smart iterative refinement, using Gemini 3.1 Pro for automated quality review and an optional Perplexity Sonar research phase for sourced data — supports 10 infographic types, 8 industry styles, and colorblind-safe palettes. Use when the request is for an infographic, data-story graphic, statistical poster, comparison chart, timeline, process/how-to visual, or list/social graphic that pairs a designed layout with figures. Use alterlab-scientific-schematics instead for technical flowcharts, CONSORT/PRISMA, pathways, or architecture diagrams; alterlab-generate-image for non-infographic illustrations; alterlab-matplotlib for exact plots of a dataset. Part of the AlterLab Academic Skills suite."
license: MIT
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
allowed-tools: Read Write Edit Bash
compatibility: Requires an OpenRouter API key (OPENROUTER_API_KEY) and the requests library for Nano Banana Pro generation (google/gemini-3-pro-image), Gemini 3.1 Pro quality review, and optional Perplexity sonar-pro research; models can be overridden with ALTERLAB_IMAGE_MODEL / ALTERLAB_REVIEW_MODEL
---

# Infographics

## Overview

Infographics are visual representations of information, data, or knowledge designed to present complex content quickly and clearly. **This skill uses Nano Banana Pro AI for infographic generation with Gemini 3.1 Pro quality review and Perplexity Sonar for research.**

**How it works:**
- (Optional) **Research phase**: Gather accurate facts and statistics using Perplexity Sonar
- Describe your infographic in natural language
- Nano Banana Pro generates publication-quality infographics automatically
- **Gemini 3.1 Pro reviews quality** against document-type thresholds
- **Smart iteration**: Only regenerates if quality is below threshold
- Professional-ready output in minutes; no design skills required

**Quality Thresholds by Document Type:**
| Document Type | Threshold | Description |
|---------------|-----------|-------------|
| marketing | 8.5/10 | Marketing materials - must be compelling |
| report | 8.0/10 | Business reports - professional quality |
| presentation | 7.5/10 | Slides, talks - clear and engaging |
| social | 7.0/10 | Social media content |
| internal | 7.0/10 | Internal use |
| draft | 6.5/10 | Working drafts |
| default | 7.5/10 | General purpose |

## When to Use This Skill

Use the **infographics** skill when:
- Presenting data or statistics in a visual format
- Creating timeline visualizations for project milestones or history
- Explaining processes, workflows, or step-by-step guides
- Comparing options, products, or concepts side-by-side
- Summarizing key points in an engaging visual format
- Creating geographic or map-based data visualizations
- Building hierarchical or organizational charts
- Designing social media content or marketing materials

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Technical flowchart, CONSORT/PRISMA diagram, biological pathway, circuit, or neural-network architecture | `alterlab-scientific-schematics` |
| Photo, illustration, concept art, or hero image with no data layout | `alterlab-generate-image` |
| Exact chart of a dataset (every value must match the data) for a paper or report | `alterlab-matplotlib` / `alterlab-scientific-viz` |
| Full research poster for a conference session | `alterlab-latex-posters` |

## Quick Start

Generate any infographic by describing it; the script handles generation, review, and iteration.

```bash
# Generate a list infographic (default threshold 7.5/10)
python scripts/generate_infographic.py \
  "5 benefits of regular exercise" \
  -o figures/exercise_benefits.png --type list

# Marketing (highest threshold: 8.5/10)
python scripts/generate_infographic.py \
  "Product features comparison" \
  -o figures/product_comparison.png --type comparison --doc-type marketing

# Corporate style + colorblind-safe palette
python scripts/generate_infographic.py \
  "Company milestones 2010-2025" \
  -o figures/timeline.png --type timeline --style corporate

# WITH RESEARCH for accurate, up-to-date data
python scripts/generate_infographic.py \
  "Global AI market size and growth projections" \
  -o figures/ai_market.png --type statistical --research
```

**What happens behind the scenes:**
1. **(Optional) Research**: Perplexity Sonar gathers accurate facts, statistics, and data
2. **Generation 1**: Nano Banana Pro creates the initial infographic
3. **Review 1**: **Gemini 3.1 Pro** evaluates quality against the document-type threshold
4. **Decision**: quality >= threshold → **DONE** (early stop); below threshold → improve prompt and regenerate
5. **Repeat** until quality meets threshold OR max iterations reached

**Output**: Versioned images plus a detailed JSON review log with quality scores, critiques, and early-stop info. With `--research`, a `_research.json` file also records the gathered facts and the source URLs returned by the search model.

**Check the numbers before you publish.** The image model draws every figure and label itself, so it can misspell words or alter digits even when the prompt was correct, and the review model scores design quality, not factual accuracy. Compare each statistic in the finished graphic against your data or the `_research.json` sources, and cite those sources wherever the infographic is used. If the review call fails, the script keeps the image and records `"review_skipped": true` with a null score in the log instead of inventing one.

## Core Workflow

1. **Pick the type** (`--type`) — one of 10 presets (statistical, timeline, process, comparison, list, geographic, hierarchical, anatomical, resume, social). Full catalog with examples in `references/type_catalog.md`.
2. **Pick a style and (optionally) palette** — 8 industry `--style` presets, 3 colorblind-safe `--palette` presets. Tables in `references/type_catalog.md`.
3. **Set `--doc-type`** to choose the quality threshold (see table above).
4. **Add `--research`** when accurate sourced data matters.
5. **Configure the API key** (`OPENROUTER_API_KEY`) and run; review the JSON log and regenerate with a more specific prompt if needed.

## Configuration

Set the OpenRouter API key in the environment, or in a `.env` file if `python-dotenv` is installed:

```bash
export OPENROUTER_API_KEY='your_api_key_here'   # https://openrouter.ai/keys
```

Default models (verified on OpenRouter 2026-09-23): `google/gemini-3-pro-image` (Nano Banana Pro) for generation, `google/gemini-3.1-pro-preview` for review, and `perplexity/sonar-pro` for research. Override the first two with `ALTERLAB_IMAGE_MODEL` / `ALTERLAB_REVIEW_MODEL`.

**Data & privacy:** prompts and research/infographic content are sent to a third-party API (OpenRouter) for generation and quality review. Avoid sending confidential, clinical, or unpublished material.

## Reference Index

| File | Contents |
| ---- | -------- |
| [`references/type_catalog.md`](references/type_catalog.md) | All 10 `--type` presets with runnable examples; `--style` and `--palette` tables |
| [`references/cli_and_workflow.md`](references/cli_and_workflow.md) | Full CLI options, smart-refinement loop + Gemini review criteria + review-log schema, `--research` integration, prompt-engineering tips, troubleshooting, cross-skill integration, checklist |
| [`references/design_principles.md`](references/design_principles.md) | Visual hierarchy, layout, typography |
| [`references/color_palettes.md`](references/color_palettes.md) | Full palette specifications |
| [`references/infographic_types.md`](references/infographic_types.md) | Extended layout templates for all types |

Use this skill to create professional, accessible, and visually compelling infographics using Nano Banana Pro AI with intelligent Gemini 3.1 Pro quality review.
