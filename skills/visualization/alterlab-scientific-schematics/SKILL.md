---
name: alterlab-scientific-schematics
description: Creates publication-quality scientific diagrams with no API key - Claude draws the diagram as code (SVG, TikZ/PGF, schemdraw for circuits), renders it locally to PNG/PDF with exact, editable labels, then reviews the render itself against a document-type quality threshold (journal 8.5/10, poster 7.0, ...) and revises until it passes (max 2 iterations). Use when the request is for a rendered technical or scientific diagram — CONSORT/PRISMA flowcharts, neural-network architectures, system/block diagrams, biological pathways, circuits, or other complex scientific visuals. Optional AI raster generation (Nano Banana 2 with Gemini review, via OpenRouter) when OPENROUTER_API_KEY is set. For general photos, illustrations, or artwork use alterlab-generate-image; for infographics use alterlab-infographics; for editable text-based Mermaid diagrams use alterlab-mermaid. Part of the AlterLab Academic Skills suite.
allowed-tools: Read Write Edit Bash
license: MIT
compatibility: "No API key required. Renders locally: SVG via `uv run --python \">=3.11\" --with cairosvg --with pillow` (needs the Cairo library), TikZ via pdflatex/lualatex/xelatex/tectonic, circuits via schemdraw. Optional AI backend (--backend ai): OPENROUTER_API_KEY and requests; models via ALTERLAB_IMAGE_MODEL / ALTERLAB_REVIEW_MODEL."
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    last_updated: "2026-10-22"
    credentials: "optional: OPENROUTER_API_KEY (the AI raster backend, --backend ai: Nano Banana 2 generation and Gemini 3.1 Pro Preview review through OpenRouter)"
---

# Scientific Schematics and Diagrams

## Overview

Scientific schematics turn complex concepts into clear visuals for publication. **This skill draws
them as code** — SVG by default, TikZ for LaTeX manuscripts, schemdraw for circuits — renders the
code locally, then **reviews the rendered image itself** against a document-type threshold and
revises until it passes. No image model and no API key are involved.

Why code: every label and count is exactly the text you typed (an image model redraws text and
can change an `n=`), the figure stays editable, it exports as vector PDF/SVG for the journal,
and unpublished content never leaves the machine.

**Quality thresholds by document type** (Claude's review score, out of 10):

| Document Type | Threshold | Description |
|---------------|-----------|-------------|
| journal | 8.5/10 | Nature, Science, peer-reviewed journals |
| conference | 8.0/10 | Conference papers |
| thesis | 8.0/10 | Dissertations, theses |
| grant | 8.0/10 | Grant proposals |
| preprint | 7.5/10 | arXiv, bioRxiv, etc. |
| report | 7.5/10 | Technical reports |
| poster | 7.0/10 | Academic posters |
| presentation | 6.5/10 | Slides, talks |
| default | 7.5/10 | General purpose |

Review criteria, 0-2 points each: **scientific accuracy**, **clarity and readability**, **label
quality**, **layout and composition**, **professional appearance**. At most 2 iterations.

## When to Use This Skill

This skill should be used when:
- Creating neural network architecture diagrams (Transformers, CNNs, RNNs, etc.)
- Illustrating system architectures and data flow diagrams
- Drawing methodology flowcharts for study design (CONSORT, PRISMA)
- Visualizing algorithm workflows and processing pipelines
- Creating circuit diagrams and electrical schematics
- Depicting biological pathways and molecular interactions
- Generating network topologies and hierarchical structures
- Illustrating conceptual frameworks and theoretical models
- Designing block diagrams for technical papers

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Diagram that should stay editable text in a README or Markdown doc (renders on GitHub, diffs in git) | `alterlab-mermaid` |
| Photo, illustration, artwork, or slide/poster hero image | `alterlab-generate-image` |
| Infographic that presents statistics, a timeline, or a comparison for a general audience | `alterlab-infographics` |
| Plot of measured data (scatter, bar, line, heatmap) | `alterlab-matplotlib` / `alterlab-scientific-viz` |
| Network graph whose layout is computed from real node/edge data | `alterlab-networkx` |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-mermaid`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

## Workflow (keyless)

1. **Collect the content.** List every node, arrow, label and count from the user's message and
   attached files. Copy numbers verbatim; check that they reconcile (CONSORT arms sum to the
   randomised total, each stage carries forward). If a required count is missing, ask for it —
   never invent one.
2. **Get the brief** for the venue (guidelines, threshold, criteria):
   `python scripts/generate_schematic.py --brief --doc-type journal`
3. **Draw it as code**, saved next to the figure (`figures/consort.svg`):
   - **SVG** for flowcharts, block diagrams, architectures and pathways. For CONSORT start from
     `assets/consort_template.svg` (replace every `N_*` token); building blocks and recipes for
     PRISMA, transformers, pathways and block diagrams are in `references/README.md`.
   - **TikZ** (standalone `.tex`) when the paper is LaTeX or labels need maths.
   - **schemdraw** for circuits (writes SVG); matplotlib when geometry comes from data.
   - Okabe-Ito colours plus a second cue (shape, dash, label); one `<text>` per line; font size on
     the root; no "Figure 1" or caption inside the image.
4. **Render and lint**, versioned:
   ```bash
   uv run --python ">=3.11" --with cairosvg --with pillow python scripts/generate_schematic.py \
       figures/consort.svg -o figures/consort_v1.png --doc-type journal --width-in 7.2 --gray
   ```
   The output names the renderer and flags labels below 7 pt at print width, text that probably
   overflows its box, external references and blank renders. Fix every warning before reviewing.
5. **Review the render yourself.** Read `consort_v1.png` (and `consort_v1_gray.png`), check each
   number and label against the source, score the five criteria, and record it:
   ```bash
   python scripts/figure_tools.py score figures/consort_review_log.json --kind schematic \
       --doc-type journal --image figures/consort_v1.png --source figures/consort.svg \
       --score 7.5 --critique "exclusion reasons overflow; arm boxes unequal heights"
   ```
   `REVISE` → fix the source and render `consort_v2.png`; `DONE` → deliver; `STOP` (2 iterations
   used, still below threshold) → deliver the best version and list what is still short. Never
   inflate a score to pass; the log is the audit trail.
6. **Deliver**: the final PNG (300 dpi), a vector PDF/SVG
   (`python scripts/figure_tools.py render figures/consort.svg -o figures/consort.pdf`), the
   source file, and the review log, plus a suggested caption kept outside the image.

### Output template

```markdown
**Figure:** figures/consort_v2.png (300 dpi, 7.2 in) · vector: figures/consort.pdf · source: figures/consort.svg
**Review:** journal threshold 8.5 — v1 7.5 (overflowing exclusion reasons) → v2 9.0, DONE (figures/consort_review_log.json)
**Checked against:** trial_flow_counts.md — 500 assessed, 150 excluded (98/41/11), 350 randomised, 175/175 …
**Caption (for the manuscript):** CONSORT 2010 flow diagram of participant progress through the trial …
```

## Optional: AI raster generation

When `OPENROUTER_API_KEY` is set (environment, `.env`, or `--api-key`), a description can be
turned into a raster image by Nano Banana 2 (`google/gemini-3.1-flash-image`) and reviewed by
Gemini 3.1 Pro Preview against the same thresholds:

```bash
python scripts/generate_schematic.py "CONSORT participant flow ..." -o figures/consort.png \
    --doc-type journal --backend ai
```

Without the key, `--backend ai` exits with status 2 and names the keyless route; it never falls
back silently. Use it only when the user asks for an AI-generated image. The prompt leaves the
machine (do not include confidential, clinical or unpublished details), and the image model
draws every label itself, so compare each count and term with the source before use. If the
review call fails the log records `"review_skipped": true` with a null score. Models can be
overridden with `ALTERLAB_IMAGE_MODEL` / `ALTERLAB_REVIEW_MODEL`. Details:
`references/ai_generation_guide.md`; worked prompts: `references/generation_examples.md`.

## Best Practices Summary

Design for **clarity over complexity**, consistent styling, colorblind accessibility (Okabe-Ito,
redundant encoding), ≥7-8 pt sans-serif type at print size, and vector output (PDF/SVG; 300+ DPI
for raster). Integrate with LaTeX via `\includegraphics{}`, caption thoroughly, reference in
text, and keep the figure source + outputs + review log under version control. The full
design/technical/integration checklist is in `references/submission_checklist.md`.

## Troubleshooting Common Issues

Renderer missing, overflowing text, small labels, detached arrowheads, LaTeX errors, and the
optional AI backend's setup and generation problems are covered in
`references/troubleshooting.md` and at the end of `references/README.md`.

## Resources and References

### Detailed References

- **`references/README.md`** - Code-drawn workflow: choosing SVG/TikZ/schemdraw, SVG building blocks, CONSORT/PRISMA/transformer/pathway/block-diagram recipes, review loop
- **`references/QUICK_REFERENCE.md`** - Commands, thresholds, print sizes, delivery checklist
- **`references/diagram_types.md`** - Catalog of scientific diagram types with examples
- **`references/best_practices.md`** - Publication standards and accessibility guidelines
- **`references/submission_checklist.md`** - Pre-submission verification checklist
- **`references/troubleshooting.md`** - Fixes for rendering, quality, accessibility, and AI-backend issues
- **`references/ai_generation_guide.md`** - Optional AI backend: smart iteration, review rubric, Python API, CLI options
- **`references/generation_examples.md`** - Optional AI backend: worked prompts

### External Resources

**Python Libraries**
- Schemdraw Documentation: https://schemdraw.readthedocs.io/
- CairoSVG: https://cairosvg.org/
- NetworkX Documentation: https://networkx.org/documentation/
- Matplotlib Documentation: https://matplotlib.org/

**Publication Standards**
- Nature Figure Guidelines: https://www.nature.com/nature/for-authors/final-submission
- Science Figure Guidelines: https://www.science.org/content/page/instructions-preparing-initial-manuscript
- CONSORT Diagram: https://www.consort-spirit.org/

## Integration with Other Skills

This skill works synergistically with:

- **`alterlab-scientific-writing`** - Diagrams follow figure best practices
- **`alterlab-scientific-viz`** - Shares color palettes and styling
- **`alterlab-latex-posters`** - Generate diagrams for poster presentations
- **`alterlab-research-grants`** - Methodology diagrams for proposals
- **`alterlab-peer-review`** - Evaluate diagram clarity and accessibility

## Quick Reference Checklist

Before submitting diagrams, run through the full checklist (visual quality, accessibility,
typography, publication standards, required quality verification, documentation/version control,
and final integration) in `references/submission_checklist.md`.

---

Use this skill to create clear, accessible, publication-quality diagrams that effectively communicate complex scientific concepts: drawn as code, rendered locally, and reviewed against the venue's threshold before delivery.

Part of the AlterLab Academic Skills suite.
