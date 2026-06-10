---
name: alterlab-latex-posters
description: "Creates professional research posters in LaTeX using beamerposter, tikzposter, or baposter — handles layout design, color schemes, multi-column formats, figure integration, and poster-specific visual-communication best practices. Use when building a conference or academic poster in LaTeX. For PowerPoint/PPTX poster output prefer pptx-posters instead. Part of the AlterLab Academic Skills suite."
license: MIT
metadata:
    skill-author: AlterLab
    version: "1.0.0"
allowed-tools: Read Write Edit Bash
compatibility: Requires a LaTeX distribution (pdflatex/xelatex/lualatex) with beamerposter or tikzposter installed (or baposter.cls placed alongside the .tex) to compile posters
---

# LaTeX Research Posters

## Overview

Research posters are a critical medium for scientific communication at conferences, symposia, and academic events. This skill provides guidance for creating professional, visually appealing research posters using LaTeX. It is organized as a concise router: the sections below cover the workflow and the key decisions, and link to detailed reference files for templates, figures, and quality control.

## When to Use This Skill

Use this skill when:

- Creating research posters for conferences, symposia, or poster sessions
- Designing academic posters for university events or thesis defenses
- Preparing visual summaries of research for public engagement
- Converting a scientific paper into poster format
- Building template posters for a research group or department
- Designing posters to specific size requirements (A0, A1, 36×48", etc.)
- Building complex multi-column layouts that integrate figures, tables, equations, and citations

## Reference Files

Detailed guidance lives in `references/`. Load the file relevant to your current step:

| File | Use it for |
|------|------------|
| `references/templates_beamerposter.md` | beamerposter setup, themes, fonts, full-page config |
| `references/templates_tikzposter.md` | tikzposter setup, columns/blocks, themes |
| `references/templates_baposter.md` | baposter setup, header boxes, page-boundary debugging |
| `references/figures_and_visuals.md` | planning, generating, sizing, and integrating figures and QR codes |
| `references/compilation_and_qc.md` | compiling, overflow prevention, the pre-print quality checklist |
| `references/latex_poster_packages.md` | detailed comparison of the three packages with examples |
| `references/poster_layout_design.md` | layout principles, grid systems, visual flow |
| `references/poster_design_principles.md` | typography, color theory, visual hierarchy, accessibility |
| `references/poster_content_guide.md` | content organization, writing style, section-specific guidance |

Ready-to-use starter templates live in `assets/` (`beamerposter_template.tex`,
`tikzposter_template.tex`, `baposter_template.tex`, plus a quality checklist).

## Choosing a LaTeX Package

| Package | Strengths | Best for |
|---------|-----------|----------|
| **beamerposter** | Beamer syntax, strong theme/branding support | Traditional academic posters, institutional branding |
| **tikzposter** | Modern, flexible, built-in color themes, TikZ graphics | Colorful, modern designs with custom graphics |
| **baposter** | Box-based layout, automatic spacing | Structured, professional multi-column layouts |

See `references/latex_poster_packages.md` for a full comparison, and the matching
`templates_*.md` reference for setup snippets.

## Poster Sizes

**International**: A0 (841 × 1189 mm / 33.1 × 46.8 in, most common), A1 (594 × 841 mm), A2 (420 × 594 mm).
**North American**: 36 × 48 in (common US size), 42 × 56 in, 48 × 72 in.
**Orientation**: portrait (most common) or landscape (better for wide content and timelines).

Always confirm the conference's required size and orientation before starting.

## Poster Structure and Layout

**Common sections**: Header/Title (title, authors, affiliations, logos), Introduction/Background, Methods/Approach, Results, Conclusions, References (abbreviated), Acknowledgments.

**Layout strategies**:

- Column-based grids (2, 3, or 4 columns) or flexible block-based arrangements.
- Z-pattern flow to guide the reader logically through the content.
- Visual hierarchy via size, color, and spacing to emphasize key points.

See `references/poster_layout_design.md` for grid systems and visual flow.

## Design Principles

**Typography** — Title 72-120pt, section headers 48-72pt, body text 24-36pt minimum (readable from 4-6 feet). Prefer sans-serif (Arial, Helvetica, Calibri); limit to 2-3 font families.

**Color and contrast** — High-contrast schemes; color-blind-friendly palettes (avoid red-green); use institutional colors for branding. White space is active space — don't overcrowd.

**Content** — Less is more: 300-800 words total. Bullet points over paragraphs; clear, concise messaging; self-explanatory figures. Aim for a roughly even balance of visual and text area.

See `references/poster_design_principles.md` and `references/poster_content_guide.md`
for depth. Color palettes worth knowing: Viridis, ColorBrewer, and IBM Color Blind Safe.

## Figures and Visuals

Figures carry most of a poster's communicative weight, so plan them deliberately.
If a diagram or figure would aid comprehension, invoke the **alterlab-scientific-schematics**
skill (diagrams/schematics) or the **alterlab-generate-image** skill (images). Figures are
optional — add them only where they improve clarity.

Keep each graphic to one message with a few large, high-contrast elements; split anything
complex into several simple images so the text stays readable from a distance. Full guidance —
planning, generating, reviewing, sizing, integrating with `\includegraphics`, and QR codes —
is in `references/figures_and_visuals.md`.

## Workflow

### 1. Plan and develop content

- Confirm conference size, orientation, and format requirements.
- Identify 1-3 core messages and select the key figures (typically 3-6 main visuals).
- Draft concise, bullet-style text per section; aim for 300-800 words total.
- Choose a package (see the table above).

### 2. Prepare visual elements

- Plan the figures each section needs (see `references/figures_and_visuals.md`).
- Generate them via the **alterlab-scientific-schematics** or **alterlab-generate-image**
  skills where they add clarity, keeping each one simple and legible at a distance.
- Review each figure at ~25% zoom; simplify and regenerate any that read as cluttered.

### 3. Design and lay out

- Start from a template in `assets/`; customize the color scheme to match branding.
- Plan the column structure and content flow (typically left-to-right, top-to-bottom).
- Allocate space: title ~10-15%, content ~70-80%, footer ~5-10%.
- Set the typography hierarchy and verify readability from 4-6 feet.

### 4. Integrate content

- Build the header (concise title, authors, affiliations, high-res logos).
- Place figures in their sections with sensible sizing (`width=0.85\linewidth`, not full width).
- Add minimal, scannable supporting text in active voice; complement figures, don't duplicate them.
- Add QR codes, key references (5-10 typical), contact info, and acknowledgments.

### 5. Compile, review, and deliver

- Compile (`pdflatex` / `lualatex` / `xelatex`) — see `references/compilation_and_qc.md`.
- Run the overflow check on the log and inspect all four edges at 100% zoom.
- Do a 25%-scale print test, verify fonts are embedded and images are 300 DPI, and proofread.
- Prepare print output (PDF/X-1a, CMYK if required, bleed if required) and a PNG/handout version.

## Compilation and Quality Control

Compile, prevent overflow, and run the pre-print checklist using
`references/compilation_and_qc.md`. The single most important check: after every compile,
run `grep -i "overfull" poster.log` and visually inspect all four page edges — overflow
(text or graphics cut off at a boundary) is the most common poster defect. A helper script
is available at `scripts/review_poster.sh`.

## Common Pitfalls to Avoid

**Design** — Too much text (>1000 words); body text under 24pt; low-contrast colors; cluttered layout with no white space; inconsistent styling; pixelated images.

**Figures** — Cramming too many elements into one graphic (forces tiny text); too much detail; complex flowcharts with many steps; comparison charts with too many series. Split into simple, focused graphics instead.

**Content** — No clear narrative; too many research questions; unexplained jargon; results without interpretation; missing contact information.

**Technical** — Wrong dimensions for the conference; RGB sent to a CMYK printer (color shift); fonts not embedded; file too large for the submission portal; QR codes too small or untested.

## Integration with Other Skills

- **alterlab-scientific-schematics** — generate poster diagrams and flowcharts.
- **alterlab-generate-image** — stylized graphics, conceptual illustrations, summary visuals.
- **alterlab-scientific-writing** — develop poster content from a paper.
- **alterlab-literature-review** — contextualize the research.

## Package Installation

```bash
# TeX Live (Linux/Mac) — beamerposter and tikzposter are on CTAN
tlmgr install beamerposter tikzposter

# Additional recommended packages
tlmgr install qrcode graphicx xcolor tcolorbox subcaption

# MiKTeX (Windows) typically auto-installs packages on first use.
```

**baposter is not on CTAN/TeX Live.** Obtain `baposter.cls` from its repository
(github.com/mloesch/baposter) or the Overleaf template and place it next to your
`.tex` file. (CTAN's `xebaposter` is a separate Persian/Latin fork, not the same class.)

## Scripts

Helper scripts in `scripts/`:

- `review_poster.sh` — automated PDF quality check (page size, fonts, file size, page count).
