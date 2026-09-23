---
name: alterlab-venue-templates
description: Provides LaTeX templates, formatting requirements, and submission guidelines for major scientific venues (Nature, Science, PLOS, IEEE, ACM, Cell Press), conferences (NeurIPS, ICML, ICLR, CVPR, CHI), research posters, and grant proposals (NSF, NIH, DOE, DARPA). Also covers venue-specific writing style (tone, abstract format, what reviewers prioritize). Use when preparing a manuscript, conference paper, poster, or grant proposal and you need the right template, page/word limits, citation style, figure specs, or venue conventions. For substantive prose/content development defer to alterlab-scientific-writing; for grant argumentation defer to alterlab-research-grants. Part of the AlterLab Academic Skills suite.
allowed-tools: Read Write Edit Bash
license: MIT
compatibility: Requires a LaTeX distribution (pdflatex/latexmk) to compile the bundled templates; helper scripts (query/customize/validate) are stdlib Python. validate_format.py needs pdfinfo (poppler) for PDF checks.
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# Venue Templates

## Overview

LaTeX templates, formatting requirements, and writing-style guidance for academic journals, conferences, posters, and grants. Provides ready-to-use templates plus references that cover many more venues than are bundled.

## When to Use This Skill

Use this skill when you need venue-specific **formatting** (templates, page/word limits, citation style, figure specs, anonymization rules, mandatory checklists and statements) or **style** (tone, abstract format, reviewer priorities) for a journal, conference, poster session, or funder.

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Drafting or tightening the manuscript's prose itself | `alterlab-scientific-writing` |
| Grant argumentation — Specific Aims, significance, broader impacts strategy | `alterlab-research-grants` |
| Designing and laying out the poster itself in LaTeX | `alterlab-latex-posters` |
| Turkish journal / TR Dizin formatting and Turkish APA 7 | `alterlab-tr-academic-style` |
| Building or cleaning the bibliography (.bib) | `alterlab-citation-mgmt` |

## What's Bundled

**6 ready-to-use LaTeX templates** in `assets/`:

| Type | File | Notes |
|------|------|-------|
| Journal | `assets/journals/nature_article.tex` | Nature, single column |
| Journal | `assets/journals/plos_one.tex` | PLOS ONE |
| Conference | `assets/journals/neurips_article.tex` | NeurIPS, `\documentclass{article}` (single column) |
| Poster | `assets/posters/beamerposter_academic.tex` | beamerposter, A0 customizable |
| Grant | `assets/grants/nsf_proposal_template.tex` | NSF project description |
| Grant | `assets/grants/nih_specific_aims.tex` | NIH Specific Aims page |

**Formatting references** in `references/`: `journals_formatting.md`, `conferences_formatting.md`, `posters_guidelines.md`, `grants_requirements.md`. These cover many venues beyond the bundled templates (Science, Cell Press, IEEE, ACM, ICML, ICLR, CVPR, CHI, ISMB, DOE, DARPA, foundations).

**Writing-style guides** in `references/`: `venue_writing_styles.md` (master overview), `nature_science_style.md`, `cell_press_style.md`, `medical_journal_styles.md`, `ml_conference_style.md`, `cs_conference_style.md`, `reviewer_expectations.md`.

**Writing examples** in `assets/examples/`: `nature_abstract_examples.md`, `neurips_introduction_example.md`, `cell_summary_example.md`, `medical_structured_abstract.md`.

## Workflow

1. **Identify the venue.** Journal, conference, poster, or grant agency.
2. **Query template + requirements.** Run `query_template.py` (below) or read the relevant `references/*.md`. Verify currency against the official author guidelines — venue style files change yearly.
3. **Customize the template.** Use `customize_template.py` or edit placeholders by hand.
4. **For writing register**, load the matching style guide and check `reviewer_expectations.md`.
5. **Validate + compile.** Run `validate_format.py` on the PDF, then compile.

```bash
# Compile (run pdflatex 2-3x, or use latexmk for automatic rerun handling)
latexmk -pdf my_paper.tex
```

## Helper Scripts

All scripts are stdlib Python; run from the skill root.

### query_template.py — find templates and requirements
```bash
python scripts/query_template.py --list-all
python scripts/query_template.py --venue "Nature" --type journals
python scripts/query_template.py --venue "NeurIPS" --requirements
python scripts/query_template.py --keyword "machine learning"
```

### customize_template.py — fill in title/authors/affiliations
`--template` takes the **bare filename** (not a path); the script searches `assets/{journals,posters,grants}/` for it.
```bash
python scripts/customize_template.py \
  --template nature_article.tex \
  --title "Novel Approach to Protein Folding" \
  --authors "Jane Doe, John Smith" \
  --affiliations "MIT, Stanford" \
  --email "doe@mit.edu" \
  --output my_paper.tex

# Interactive picker
python scripts/customize_template.py --interactive
```

### validate_format.py — check a compiled PDF against venue specs
Requires `pdfinfo` (poppler). Checks page count, margins, fonts heuristically.
```bash
python scripts/validate_format.py --file my_paper.pdf --venue "Nature" --check-all
python scripts/validate_format.py --file my_paper.pdf --venue "NeurIPS" --check page-count,fonts
python scripts/validate_format.py --file proposal.pdf --venue "NSF" --report validation.txt
```

## Quick Reference

### Page limits (typical — always re-verify yearly)

| Venue | Limit | Notes |
|-------|-------|-------|
| Nature Article | ~5 pp | ~3000 words excluding refs |
| Science Report | ~5 pp | figures count toward limit |
| PLOS ONE | none | unlimited length |
| NeurIPS 2026 | 9 pp | + unlimited refs/appendix; paper checklist mandatory (desk reject without it) |
| ICML 2026 | 8 pp | 9 pp camera-ready; impact statement mandatory (not counted) |
| ICLR 2027 | 9 pp | 10 pp in rebuttal and camera-ready; AI-use statement required |
| CVPR 2026 | 8 pp | excluding references; official author kit required |
| CHI 2027 | 5,000-8,000 words | word-based; single-column `acmart` manuscript format for review |
| NSF | 15 pp | project description only |
| NIH R01 | 12 pp | research strategy |

### Citation style

| Venue | Style |
|-------|-------|
| Nature / Science | numbered superscript |
| PLOS / IEEE | numbered brackets (Vancouver / IEEE) |
| Cell Press | author-year |
| ACM | numbered |
| NeurIPS / ICML | numbered brackets |

### Figure specs

| Venue | Resolution | Format | Color |
|-------|-----------|--------|-------|
| Nature | 300+ dpi | TIFF, EPS, PDF | RGB or CMYK |
| Science | 300+ dpi | TIFF, PDF | RGB |
| PLOS | 300–600 dpi | TIFF, EPS | RGB |
| IEEE | 300+ dpi | EPS, PDF | RGB or grayscale |

### NeurIPS at a glance
Single-column (text block 5.5 × 9 in), Times 10pt, 9-page main text for 2026 (+ unlimited refs/appendix), numbered bracket citations, **anonymization required** for the double-blind initial submission, and the **NeurIPS Paper Checklist** appended after the appendices (missing checklist = desk rejection). Official style file (`neurips_2026.sty` for 2026) changes annually; colorblind-safe figures recommended.

## Why Style Matters

The same results read very differently across venues. Load the matching guide before drafting:
- **Nature/Science** (`nature_science_style.md`): accessible to non-specialists, story-driven, broad significance, flowing-paragraph abstract.
- **Cell Press** (`cell_press_style.md`): mechanistic depth, graphical abstract, Highlights, eTOC.
- **Medical** (`medical_journal_styles.md`): patient-centered, evidence-graded, structured abstracts (NEJM/Lancet/JAMA/BMJ).
- **ML conferences** (`ml_conference_style.md`): contribution bullets, ablations, reproducibility.
- **CS conferences** (`cs_conference_style.md`): field-specific conventions (ACL, EMNLP, CHI, SIGKDD).
- `reviewer_expectations.md`: what reviewers prioritize per venue and rebuttal tips.

## Best Practices

- **Verify currency**: compare bundled templates against the latest official author guidelines (links in the references).
- **Use the official style file** where one exists; don't tweak margins/fonts (grounds for desk rejection at many venues).
- **Preserve required structure**: don't remove required sections or packages when customizing.
- **Check page limits and anonymization** before submission; remove identifying info for double-blind venues.
- **Check required statements**: many venues now require a checklist, impact statement, limitations section, or AI-use disclosure (e.g. NeurIPS checklist, ICML impact statement, ACL Limitations section, ICLR AI-use statement).

### External author guidelines
- Nature: https://www.nature.com/nature/for-authors
- Science: https://www.science.org/content/page/instructions-authors
- PLOS: https://plos.org/resources/
- Cell Press: https://www.cell.com/author-guidelines
- NeurIPS: https://neurips.cc/ · ICML: https://icml.cc/ · ICLR: https://iclr.cc/ · CVPR: https://cvpr.thecvf.com/ · ACL Rolling Review: https://aclrollingreview.org/
- NSF PAPPG: https://www.nsf.gov/policies/pappg
- NIH: https://grants.nih.gov/grants-process/write-application/how-to-apply-application-guide
- DOE: https://science.osti.gov/grants

Part of the AlterLab Academic Skills suite.
