---
name: alterlab-scientific-slides
description: Builds slide decks for research talks in PowerPoint and LaTeX Beamer, providing slide structure, design templates, timing guidance, and visual validation. Use when making conference presentations, seminar talks, research presentations, thesis-defense slides, or any scientific talk deck. Part of the AlterLab Academic Skills suite.
allowed-tools: Read Write Edit Bash
license: MIT
compatibility: PowerPoint output uses python-pptx; LaTeX Beamer output needs a LaTeX distribution (pdflatex); slide-to-image validation helpers convert decks to PDF/PNG
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# Scientific Slides

## Overview

Scientific presentations are a critical medium for communicating research, sharing findings, and engaging with academic and professional audiences. This skill provides comprehensive guidance for creating effective scientific presentations, from structure and content development to visual design and delivery preparation.

**Key Focus**: Oral presentations for conferences, seminars, defenses, and professional talks.

**CRITICAL DESIGN PHILOSOPHY**: Scientific presentations should be VISUALLY ENGAGING and RESEARCH-BACKED. Avoid dry, text-heavy slides at all costs. Great scientific presentations combine:
- **Compelling visuals**: High-quality figures, images, diagrams (not just bullet points)
- **Research context**: Proper citations from research-lookup establishing credibility
- **Minimal text**: Bullet points as prompts, YOU provide the explanation verbally
- **Professional design**: Modern color schemes, strong visual hierarchy, generous white space
- **Story-driven**: Clear narrative arc, not just data dumps

**Remember**: Boring presentations = forgotten science. Make your slides visually memorable while maintaining scientific rigor through proper citations.

## When to Use This Skill

This skill should be used when:
- Preparing conference presentations (5-20 minutes)
- Developing academic seminars (45-60 minutes)
- Creating thesis or dissertation defense presentations
- Designing grant pitch presentations
- Preparing journal club presentations
- Giving research talks at institutions or companies
- Teaching or tutorial presentations on scientific topics

## Slide Generation with Nano Banana Pro

**This skill uses Nano Banana Pro AI to generate stunning presentation slides automatically.** There are two workflows depending on output format:

- **PDF workflow (default, recommended)** — generate each slide as a complete image, then combine into a PDF. Most visually stunning; best for conference/business/general talks.
- **PPT workflow** — generate visuals only (`--visual-only`), then build editable slides with the PPTX skill. Best for company templates and editable decks.

Full step-by-step protocol (planning, formatting-consistency rules, citation/figure-attachment handling, example commands) is in `references/nano_banana_workflows.md`.

**Key conventions (apply to every prompt):**
- **Default author is "AlterLab"** unless another name is specified.
- Define a **FORMATTING GOAL** (colors, typography, layout) and repeat it in every prompt; **always `--attach` the previous slide** for visual continuity.
- Include **citations** directly in the prompt text so they render on the slide; before results slides, list `figures/`/`results/` and `--attach` the actual data figures.

### Environment Setup (required)

```bash
export OPENROUTER_API_KEY='your_api_key_here'
# Get key at: https://openrouter.ai/keys
```

The `generate_slide_image.py` script reads `OPENROUTER_API_KEY` (or accepts `--api-key`); a `.env` in the working dir or a parent also works. The image and quality-review models default to Google Gemini image/vision models routed through OpenRouter and can be overridden with `ALTERLAB_IMAGE_MODEL` / `ALTERLAB_REVIEW_MODEL`. Refinement is capped at 2 iterations. Full script options and prompt-writing templates are in `references/scripts_and_prompts.md`.

### Minimal example

```bash
# Title slide (establishes style — default author: AlterLab)
python scripts/generate_slide_image.py "Title slide: 'Your Research Title'. Conference name, AlterLab. FORMATTING GOAL: [color scheme], minimal professional design, no decorative elements." -o slides/01_title.png

# Content slide (attach previous for consistency, include citations)
python scripts/generate_slide_image.py "Slide titled 'Why This Matters'. Three key points with simple icons. CITATIONS: (Smith et al., 2023; Jones et al., 2024). FORMATTING GOAL: Match attached slide style exactly." -o slides/02_intro.png --attach slides/01_title.png

# Combine to PDF
python scripts/slides_to_pdf.py slides/*.png -o presentation.pdf
```

If a diagram or figure would aid comprehension, invoke the **alterlab-scientific-schematics** skill (diagrams) or **alterlab-generate-image** skill (images). Figures are optional — add them only where they improve clarity.

## Core Workflow

1. **Plan** — define talk type, duration, audience, venue. Use the **research-lookup** skill to gather 8-15 papers for citations and outline the narrative arc (Hook → Context → Gap → Approach → Results [40-50% of time] → Implications → Closure).
2. **Choose implementation** — Nano Banana Pro PDF (default), PowerPoint via PPTX skill, or LaTeX Beamer (math-heavy).
3. **Build visual-first** — every slide needs a strong visual; text is supporting (3-4 bullets, 4-6 words, 24-28pt body / 36-44pt titles). Modern palette, high contrast (7:1 preferred), 40-50% white space.
4. **Validate visually** — convert to images with `pdf_to_images.py`, inspect for overflow/overlap/small fonts/contrast, iterate until clean. Run `validate_presentation.py --duration N` for slide-count-vs-duration, file-size, and (PPTX-only) font-size/bullet-count checks. Contrast is judged visually from the images, not by the script.
5. **Practice** — 3-5 times with a timer (~1 slide/min), set checkpoints, never skip conclusions.

## Routing — where to look

| You need… | Go to |
|-----------|-------|
| Full Nano Banana Pro PDF/PPT workflow, formatting-consistency protocol, citation & figure-attachment rules, worked command examples | `references/nano_banana_workflows.md` |
| Script options (`generate_slide_image.py`, `slides_to_pdf.py`, `validate_presentation.py`, `pdf_to_images.py`), env setup, prompt-writing templates, external tools | `references/scripts_and_prompts.md` |
| Capability detail: structure, design principles, data-viz for slides, talk-type guidance, implementation options, visual-review steps, timing, validation checklist | `references/core_capabilities.md` |
| End-to-end 6-stage development process, integration with other skills, common pitfalls (content/design/timing) | `references/development_workflow.md` |
| Deep dives on structure | `references/presentation_structure.md` |
| Deep dives on slide design | `references/slide_design_principles.md` |
| Adapting figures for slides | `references/data_visualization_slides.md` |
| Talk-type specifics (conference/seminar/defense/grant/journal-club) | `references/talk_types_guide.md` |
| LaTeX Beamer reference | `references/beamer_guide.md` |
| Visual review/iteration workflow | `references/visual_review_workflow.md` |

**Assets:** Beamer templates (`assets/beamer_template_{conference,seminar,defense}.tex`), `assets/powerpoint_design_guide.md`, `assets/timing_guidelines.md`.

## Key Principles

1. **Visual-First Design** — every slide needs a strong visual element; avoid text-only slides.
2. **Research-Backed** — use research-lookup to find 8-15 papers, cite 3-5 in intro and 3-5 in discussion.
3. **Modern Aesthetics** — contemporary palette matching topic, not default themes.
4. **Minimal Text** — 3-4 bullets, 4-6 words each (24-28pt), let visuals tell the story.
5. **Structure** — follow the story arc, spend 40-50% on results.
6. **High Contrast** — 7:1 preferred for professional appearance.
7. **Timing** — practice 3-5 times, ~1 slide/minute, never skip conclusions.

**Remember:** Boring = Forgotten. Combine compelling visuals with research-backed context — slides are visual support, not a replacement for your talk.

