---
name: alterlab-infographics
description: "Creates professional infographics with no API key: Claude lays the graphic out as code (SVG, with charts computed from the numbers), renders it locally to PNG/PDF with every word and figure exact, sources statistics with web search when asked, each tied to a citation, then reviews the render itself against a document-type quality threshold and iterates — 10 infographic types, 8 industry styles, colorblind-safe palettes. Optional AI raster generation (Nano Banana Pro, Gemini review, Perplexity research via OpenRouter) with OPENROUTER_API_KEY. Use when the request is for an infographic, data-story graphic, statistical poster, comparison chart, timeline, process/how-to visual, or list/social graphic that pairs a designed layout with figures. Use alterlab-scientific-schematics instead for technical flowcharts, CONSORT/PRISMA, pathways, or architecture diagrams; alterlab-generate-image for non-infographic illustrations; alterlab-matplotlib for exact plots of a dataset. Part of the AlterLab Academic Skills suite."
license: MIT
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    last_updated: "2026-10-22"
    credentials: "optional: OPENROUTER_API_KEY (the AI raster backend, --backend ai: Nano Banana Pro generation, Gemini 3.1 Pro review and Perplexity Sonar research through OpenRouter)"
allowed-tools: Read Write Edit Bash WebSearch WebFetch
compatibility: "No API key required. Renders locally via `uv run --python \">=3.11\" --with cairosvg --with pillow` (needs the Cairo library); research uses Claude's own web search. Optional AI backend (--backend ai): OPENROUTER_API_KEY and requests; models via ALTERLAB_IMAGE_MODEL / ALTERLAB_REVIEW_MODEL."
---

# Infographics

## Overview

Infographics present information, data, or knowledge so it can be grasped quickly. **This skill
builds them as code**: Claude lays the infographic out in SVG — charts drawn from the actual
numbers, every label typed exactly — renders it locally, looks at the render, and iterates until
it meets the quality threshold for its document type. No image model and no API key are needed.

**How it works:**
- (Optional) **Research phase** (`--research`): gather accurate, recent facts with web search
  and record each with its source in `<name>_research.json`
- Get the **design brief** for the type, style, palette and document type
- **Draw** the infographic as SVG from the user's data and the research file
- **Render and lint** it locally (font sizes, text overflow, grayscale preview)
- **Claude reviews the render** against the document-type threshold
- **Smart iteration**: revise only if the score is below threshold (max 3 iterations)

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

Review criteria, 0-2 points each (the same rubric the optional AI reviewer uses): visual hierarchy
and layout; typography and readability; data visualization; color and accessibility; overall
impact. Before scoring, every number, date and name is checked against the data or research
file; a mismatch is fixed first, never traded against design points.

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

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-scientific-schematics`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

## Quick Start

```bash
# 1. Design brief (type guidelines, style colours, palette, threshold, criteria)
python scripts/generate_infographic.py "5 benefits of regular exercise" \
  -o figures/exercise_benefits.png --type list --doc-type social

# Brief WITH the research step, for numbers that must be sourced and current
python scripts/generate_infographic.py "Global AI market size and growth projections" \
  -o figures/ai_market.png --type statistical --style technology --palette wong \
  --doc-type report --research

# 2. Claude writes figures/ai_market.svg; render + lint it (versioned)
uv run --python ">=3.11" --with cairosvg --with pillow python scripts/generate_infographic.py \
  figures/ai_market.svg -o figures/ai_market_v1.png --doc-type report --gray

# 3. Claude Reads the PNG, scores it, and records the review (REVISE / DONE / STOP)
python scripts/figure_tools.py score figures/ai_market_review_log.json --kind infographic \
  --doc-type report --image figures/ai_market_v1.png --source figures/ai_market.svg \
  --score 7.6 --critique "source line too small; 2030 projection label overlaps bar"
```

`python scripts/generate_infographic.py --list-options` lists every type, style and palette.

## Core Workflow

1. **Collect the content.** Use the user's data and attached files verbatim (names, dates,
   numbers, brand colours). If the content is missing, ask for it; never invent milestones,
   statistics or quotes.
2. **Research when numbers must be sourced** (`--research`): with web search, find 5-8 recent
   facts from primary sources (agency or statistics-office releases, peer-reviewed papers, the
   original report), and write `<name>_research.json` (claim, value, unit, year, source title,
   URL, retrieval date). Where estimates disagree (market sizes often do), show the range or name
   the source on the graphic.
3. **Pick the type** (`--type`, 10 presets: statistical, timeline, process, comparison, list,
   geographic, hierarchical, anatomical, resume, social), a **style** (`--style`, 8 presets), and a
   colorblind-safe **palette** (`--palette wong|ibm|tol`); set `--doc-type` for the threshold.
   Print the brief. Catalog with examples: `references/type_catalog.md`.
4. **Draw it as SVG**: a viewBox for the target (1080x1080 social, 1200x1800 report page,
   1920x1080 slide), fonts on the root, one `<text>` per line, chart marks computed from the
   values with the value printed beside each, a source line at the bottom. Layout templates:
   `references/infographic_types.md`; design rules: `references/design_principles.md`.
5. **Render, review, iterate**: render `_v1`, fix every lint warning, Read the PNG and its
   grayscale preview, check each number against the data or research file, score the five
   criteria, and record the score; revise until `DONE` or `STOP` (3 iterations).
6. **Deliver**: final PNG (and PDF/SVG via `python scripts/figure_tools.py render x.svg -o x.pdf`),
   the SVG source, the research file with its sources, and the review log.

**Output**: versioned images, the review log (scores, critiques, early-stop reason), and, with
`--research`, the `_research.json` source list. Cite those sources wherever the infographic is used.

## Optional: AI raster generation

With `OPENROUTER_API_KEY` set (environment, `.env` with `python-dotenv`, or `--api-key`), add
`--backend ai` to a description to have Nano Banana Pro (`google/gemini-3-pro-image`) generate
the infographic, Gemini 3.1 Pro (`google/gemini-3.1-pro-preview`) score it against the same
thresholds, and, with `--research`, Perplexity `sonar-pro` gather the facts first:

```bash
python scripts/generate_infographic.py "Global AI market size and growth projections" \
  -o figures/ai_market.png --type statistical --research --backend ai
```

Without the key `--backend ai` exits 2 and names the keyless route; it never falls back
silently. Use it when the user asks for AI-generated artwork. The image model draws every figure
and label itself, so it can misspell words or alter digits even when the prompt was right, and
the review model scores design, not factual accuracy: compare each statistic with the data or the
`_research.json` sources. Prompts and content are sent to OpenRouter, so keep confidential,
clinical, or unpublished material out. If the review call fails the log records
`"review_skipped": true` with a null score. Override models with `ALTERLAB_IMAGE_MODEL` /
`ALTERLAB_REVIEW_MODEL`. Details: `references/cli_and_workflow.md`.

## Reference Index

| File | Contents |
| ---- | -------- |
| [`references/type_catalog.md`](references/type_catalog.md) | All 10 `--type` presets with examples; `--style` and `--palette` tables |
| [`references/cli_and_workflow.md`](references/cli_and_workflow.md) | Full CLI options, keyless refinement loop and review-log schema, research protocol, the optional AI backend, prompt tips, troubleshooting, checklist |
| [`references/design_principles.md`](references/design_principles.md) | Visual hierarchy, layout, typography |
| [`references/color_palettes.md`](references/color_palettes.md) | Full palette specifications |
| [`references/infographic_types.md`](references/infographic_types.md) | Extended layout templates for all types |

Use this skill to create professional, accessible, and visually compelling infographics whose every number is exact and sourced: drawn as code, rendered locally, and reviewed against the venue's threshold.

Part of the AlterLab Academic Skills suite.
