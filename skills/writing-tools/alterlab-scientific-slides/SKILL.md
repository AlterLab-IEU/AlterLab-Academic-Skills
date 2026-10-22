---
name: alterlab-scientific-slides
description: Builds slide decks for research talks with no API key — editable PowerPoint generated from a deck plan (python-pptx) or LaTeX Beamer, slide visuals drawn as code and rendered locally, plus slide structure, design templates, timing guidance, and visual validation of every page. Optional AI-generated full-slide images (Nano Banana Pro via OpenRouter) when OPENROUTER_API_KEY is set. Use when making conference presentations, seminar talks, research presentations, thesis-defense slides, or any scientific talk deck. For a research poster use alterlab-latex-posters or alterlab-pptx-posters; to auto-generate a narrated video from a paper use alterlab-paper-2-web. Part of the AlterLab Academic Skills suite.
allowed-tools: Read Write Edit Bash
license: MIT
compatibility: "No API key required. PowerPoint output via `uv run --python \">=3.11\" --with python-pptx --with pillow`; LaTeX Beamer needs pdflatex; LibreOffice (soffice) exports PPTX to PDF for review; validation helpers use pymupdf, pypdf and Pillow; code-drawn visuals render with cairosvg. Optional AI slide images: OPENROUTER_API_KEY (prompts and attached figures go to Google Gemini models via OpenRouter)."
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-10-22"
    credentials: "optional: OPENROUTER_API_KEY (the AI slide-image backend, --backend ai: Nano Banana Pro full-slide images and Gemini review through OpenRouter)"
---

# Scientific Slides

## Overview

Scientific presentations are a critical medium for communicating research, sharing findings, and engaging with academic and professional audiences. This skill provides comprehensive guidance for creating effective scientific presentations, from structure and content development to visual design and delivery preparation.

**Key Focus**: Oral presentations for conferences, seminars, defenses, and professional talks.

**Design philosophy**: scientific presentations should be visually engaging and research-backed — audiences remember what they see far better than dense text, so avoid text-heavy slides. Great scientific presentations combine:
- **Compelling visuals**: High-quality figures, images, diagrams (not just bullet points)
- **Research context**: Proper citations (found with `alterlab-research-lookup`) establishing credibility
- **Minimal text**: Bullet points as prompts, YOU provide the explanation verbally
- **Professional design**: Modern color schemes, strong visual hierarchy, generous white space
- **Story-driven**: Clear narrative arc, not just data dumps

## When to Use This Skill

This skill should be used when:
- Preparing conference presentations (5-20 minutes)
- Developing academic seminars (45-60 minutes)
- Creating thesis or dissertation defense presentations
- Designing grant pitch presentations
- Preparing journal club presentations
- Giving research talks at institutions or companies
- Teaching or tutorial presentations on scientific topics

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| A research poster with no format named, or any LaTeX poster | `alterlab-latex-posters` |
| A poster explicitly in PowerPoint/PPTX or HTML | `alterlab-pptx-posters` |
| Auto-generating a narrated presentation video, website, or poster from a finished paper | `alterlab-paper-2-web` |
| A single standalone technical diagram or schematic for a slide | `alterlab-scientific-schematics` |
| Reviewing or critiquing someone else's talk deck | `alterlab-peer-review` |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-latex-posters`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

## Building the Deck (no API key)

Two keyless implementations; pick by content:

- **PowerPoint (default for most talks)** — write a deck plan (JSON: title, section, bullets,
  image, two_column and takeaway layouts, citations, speaker notes) and build an editable 16:9
  deck in one consistent theme with `scripts/build_deck.py`. It warns on more than 4 bullets,
  bullets over 12 words, long titles, and fails on a missing figure.
- **LaTeX Beamer (math- and algorithm-heavy talks)** — start from
  `assets/beamer_template_{conference,seminar,defense}.tex`, write native LaTeX for equations
  and pseudocode, compile with pdflatex. Guide: `references/beamer_guide.md`.

**Slide visuals** come from three keyless sources: the user's own figures (placed as they are —
never redraw data), data plots made with matplotlib at slide size, and concept graphics drawn as
SVG and rendered with `scripts/generate_slide_image.py visual.svg -o slides/visual.png`. Run it
with a description instead of a file to get the slide design brief.

**Key conventions (apply to every deck):**
- **Use the presenter's real name and affiliation** as the user gives them; if unknown, ask or leave a placeholder — never invent a speaker name.
- Define one **theme** (colours, fonts, layout) and keep it on every slide; `build_deck.py` enforces it.
- Put **citations** on the slides that use them (the `citation` field); before results slides, list `figures/`/`results/` and use the actual data figures.

### Minimal example

```json
{"theme": {"primary": "#1B2A4A", "accent": "#0072B2"},
 "footer": "A. Researcher - EDM 2027",
 "slides": [
  {"layout": "title", "title": "Predicting Student Dropout", "subtitle": "A. Researcher, University", "notes": "Hook..."},
  {"layout": "image", "title": "Calibrated model beats the baseline", "image": "figures/auc.png",
   "caption": "AUC 0.87 vs 0.79", "citation": "Nested 5-fold CV"},
  {"layout": "takeaway", "title": "Take-home", "message": "One sentence the audience keeps"}]}
```

```bash
uv run --python ">=3.11" --with python-pptx --with pillow python scripts/build_deck.py deck.json -o talk.pptx
soffice --headless --convert-to pdf talk.pptx            # LibreOffice, for the visual review
uv run --python ">=3.11" --with pymupdf python scripts/pdf_to_images.py talk.pdf review/slide
```

Full plan format and options: `references/scripts_and_prompts.md`.

### Optional: AI-generated slide images

With `OPENROUTER_API_KEY` set, `generate_slide_image.py "slide description" -o slides/01.png
--backend ai` asks Nano Banana Pro (`google/gemini-3-pro-image`) for a complete slide image
(`--visual-only` for a visual; `--attach` the previous slide or a data figure as reference),
reviewed by Gemini 3.1 Pro (`google/gemini-3.1-pro-preview`) against the 6.5/10 slide threshold,
at most 2 iterations; `slides_to_pdf.py` combines the images. Use it when the user wants
image-designed slides; the slides are pictures, so text is not editable and the model may
garble words or numbers. Prompts and attached figures are sent to Google via OpenRouter, so keep
unpublished data out unless that is acceptable. Without the key `--backend ai` exits 2 and names
the keyless route. Models can be overridden with `ALTERLAB_IMAGE_MODEL` / `ALTERLAB_REVIEW_MODEL`.
Protocol: `references/nano_banana_workflows.md`.

If a diagram or figure would aid comprehension, invoke the **alterlab-scientific-schematics** skill (diagrams) or **alterlab-generate-image** skill (images). Figures are optional — add them only where they improve clarity.

## Core Workflow

1. **Plan** — define talk type, duration, audience, venue. Use `alterlab-research-lookup` to gather 8-15 papers for citations and outline the narrative arc (Hook → Context → Gap → Approach → Results [40-50% of time] → Implications → Closure).
2. **Choose implementation** — PowerPoint via `build_deck.py` (default), LaTeX Beamer (math-heavy), or, with a key and on request, AI slide images.
3. **Build visual-first** — every slide needs a strong visual; text is supporting (3-4 bullets, 4-6 words, 24-28pt body / 36-44pt titles). Modern palette, high contrast (7:1 preferred), 40-50% white space.
4. **Validate visually** — export to PDF (`soffice --headless --convert-to pdf talk.pptx`, or the Beamer PDF), convert to images with `uv run --python ">=3.11" --with pymupdf python scripts/pdf_to_images.py talk.pdf review/slide`, Read each image, inspect for overflow/overlap/small fonts/contrast, iterate until clean. Run `validate_presentation.py --duration N` for slide-count-vs-duration, file-size, and (PPTX-only) font-size/bullet-count checks (body text under 18 pt, footer and citation text under 12 pt). Contrast is judged visually from the images, not by the script.
5. **Practice** — 3-5 times with a timer (~1 slide/min), set checkpoints, never skip conclusions.

## Routing — where to look

| You need… | Go to |
|-----------|-------|
| Script options (`build_deck.py`, `generate_slide_image.py`, `slides_to_pdf.py`, `validate_presentation.py`, `pdf_to_images.py`), deck-plan format, prompt-writing templates | `references/scripts_and_prompts.md` |
| Optional AI slide-image workflow: formatting-consistency protocol, citation & figure-attachment rules, worked command examples | `references/nano_banana_workflows.md` |
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
2. **Research-Backed** — use `alterlab-research-lookup` to find 8-15 papers, cite 3-5 in intro and 3-5 in discussion; cite only papers you actually retrieved.
3. **Modern Aesthetics** — contemporary palette matching topic, not default themes.
4. **Minimal Text** — 3-4 bullets, 4-6 words each (24-28pt), let visuals tell the story.
5. **Structure** — follow the story arc, spend 40-50% on results.
6. **High Contrast** — 7:1 preferred for professional appearance.
7. **Timing** — practice 3-5 times, ~1 slide/minute, never skip conclusions.

Combine compelling visuals with research-backed context — slides are visual support, not a replacement for your talk.

Part of the AlterLab Academic Skills suite.
