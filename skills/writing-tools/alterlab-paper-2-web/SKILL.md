---
name: alterlab-paper-2-web
description: Converts a finished academic paper (PDF or LaTeX source) into promotional and presentation formats with no API key — Claude reads the paper and builds an interactive project website (static HTML/CSS for GitHub Pages; Paper2Web), a print-ready conference poster (LaTeX with QR code; Paper2Poster), a narrated video abstract (slides, script, local text-to-speech or the author's voice, captions, assembled with ffmpeg; Paper2Video), and social/PR summaries, using the paper's real figures and numbers. The third-party Paper2All pipeline (LLM calls via OpenRouter/OpenAI) is an optional route. Use when disseminating a paper, preparing for a conference, building an explorable academic homepage, generating a video abstract, or producing a poster from a finished paper. For a hand-built LaTeX poster use alterlab-latex-posters; for a talk deck use alterlab-scientific-slides. Part of the AlterLab Academic Skills suite.
allowed-tools: Read Write Edit Bash WebFetch
license: MIT
compatibility: "No API key required. Helpers run via `uv run --python \">=3.11\"` with pymupdf (figure extraction), piper-tts (local narration) and weasyprint (optional site preview); posters compile with pdflatex (tikzposter, qrcode); video needs ffmpeg. Optional Paper2All pipeline: OPENROUTER_API_KEY / OPENAI_API_KEY, LibreOffice, Poppler; its talking-head video needs an NVIDIA GPU."
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    last_updated: "2026-10-22"
    credentials: "optional: OPENROUTER_API_KEY (the Paper2All pipeline_all.py: website, poster and PR modules), OPENAI_API_KEY (Paper2All sub-modules and Paper2Video), GOOGLE_SEARCH_API_KEY (Paper2All automatic logo search)"
---

# Paper to Website, Poster, Video and Promotion Kit

## Overview

This skill turns a finished research paper (LaTeX or PDF) into three primary outputs plus a
promotion kit, **with no API key**: Claude reads the paper itself, and small local scripts do
the mechanical work.

1. **Paper2Web**: an interactive, explorable project homepage (static HTML/CSS, responsive,
   accessible, GitHub Pages ready)
2. **Paper2Poster**: a print-ready conference poster at any size (LaTeX tikzposter, QR code,
   logo)
3. **Paper2Video**: a narrated video abstract — slides, a spoken script, local text-to-speech or
   the author's recordings, captions, assembled into an MP4
4. **Promotion kit**: post, thread, LinkedIn paragraph, lay summary

Everything uses the paper's own figures and numbers. The third-party **Paper2All** pipeline,
which automates the same outputs with paid LLM calls, is an optional route when the user has a
key and asks for it (see the last section).

## When to Use This Skill

Use this skill when:

- **Creating conference materials**: Posters, presentation videos, and companion websites for academic conferences
- **Promoting research**: Converting published papers or preprints into accessible, engaging web formats
- **Preparing presentations**: Generating video abstracts or full presentation videos from paper content
- **Disseminating findings**: Creating promotional materials for social media, lab websites, or institutional showcases
- **Enhancing preprints**: Adding interactive homepages to bioRxiv, arXiv, or other preprint submissions
- **Batch processing**: Producing promotional materials for several papers

**Trigger phrases**:
- "Convert this paper to a website"
- "Generate a conference poster from my LaTeX paper"
- "Create a video presentation from this research"
- "Make an interactive homepage for my paper"
- "Transform my paper into promotional materials"
- "Generate a poster and video for my conference talk"

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Hand-building a LaTeX research poster (beamerposter, tikzposter, baposter) | `alterlab-latex-posters` |
| A PowerPoint/PPTX or HTML poster the user will edit themselves | `alterlab-pptx-posters` |
| Designing and delivering a slide deck for a live talk | `alterlab-scientific-slides` |
| Posting the paper to arXiv, bioRxiv, medRxiv, or SSRN | `alterlab-preprint-deposition` |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-latex-posters`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

## Step 0 — Read the paper and write the fact sheet

Every output starts from the same verified facts:

1. **Read** the PDF or the LaTeX project (`main.tex`, sections, `.bib`, `figures/`).
2. **Extract figures** from a PDF (raster images, page renders, and crops of vector figures by
   page fractions):
   ```bash
   uv run --python ">=3.11" --with pymupdf python scripts/extract_assets.py paper.pdf --out paper_assets/ --pages
   uv run --python ">=3.11" --with pymupdf python scripts/extract_assets.py paper.pdf --out paper_assets/ \
       --clip 3:0.25,0.07,0.75,0.52:fig1 --dpi 300
   ```
   `paper_assets/manifest.json` lists metadata, captions (with page and position), images and renders.
   From LaTeX, copy the figure files directly.
3. **Write `facts.md`**: exact title; authors in order with affiliations; venue/year; DOI or
   arXiv id; code/data links; the abstract verbatim; 3-5 key numbers with the table or figure
   they come from; the take-home sentence; the paper's own limitations. Ask for anything the
   paper does not contain (e.g. the project URL); never invent authors, links or results.

## Paper2Web — project website

1. Copy `assets/website_template/` (`index.html`, `style.css`) to `site/`; put compressed
   figures in `site/assets/`; replace every `{{PLACEHOLDER}}` from the fact sheet; delete
   sections or buttons the paper has no content for.
2. Write real alt text; keep numbers exactly as in the paper.
3. Check and preview:
   ```bash
   python scripts/check_site.py site/
   uv run --python ">=3.11" --with weasyprint --with pymupdf python scripts/check_site.py site/ --preview site_preview.png
   ```
   Zero errors (missing files, missing alt text, leftover placeholders, no viewport tag); Read
   the preview to judge the layout; check the listed external links with WebFetch.
4. Deployment targets: GitHub Pages (`docs/` folder or `gh-pages` branch), university server,
   Netlify/Vercel.

Output: `site/index.html`, `site/style.css`, `site/assets/`.

## Paper2Poster — conference poster

1. Copy `assets/poster_template.tex`; set `\geometry{paperwidth=..., paperheight=...}` (default
   48 x 36 in landscape; e.g. 60 x 40 in, A0 portrait 841 x 1189 mm).
2. Fill motivation, method, key results, take-home, limitations and references from the fact
   sheet; place figures in `figures/`; put the DOI or project URL in the `\qrcode{...}` and the
   lab logo in `figures/logo.png`.
3. `pdflatex poster.tex`, then preview with `pdftoppm -png -r 20 -singlefile poster.pdf preview`
   and Read it: text readable at 1.5-2 m, no overflow, figures sharp at print size.

Output: `poster.pdf` (vector, print-ready) and its `.tex` source.

## Paper2Video — narrated video abstract

1. **Slides** via `alterlab-scientific-slides` (editable deck) or Beamer, exported to PDF and
   then to PNGs (`pdftoppm -png -r 150 slides.pdf slides/slide`).
2. **Script**: `narration.json`, one `{"slide": ..., "text": ...}` per slide, ~150 words per
   minute (a 3-minute abstract is ~450 words), numbers exactly as in the paper.
3. **Voice**: local Piper text-to-speech (no account; voice downloaded once with
   `uv run --with piper-tts python -m piper.download_voices en_US-lessac-medium`), the author's
   own recordings (`--audio-dir`), or captions only (`--silent`).
4. **Assemble** (ffmpeg):
   ```bash
   uv run --python ">=3.11" --with piper-tts python scripts/assemble_video.py narration.json \
       -o video/abstract.mp4 --voice voices/en_US-lessac-medium.onnx
   ```
   Output: 1920-px H.264/AAC MP4 with a caption track, a sidecar `.srt`, and per-slide timings.
   Check a few frames and the timing before sharing.

Synchronized cursor highlights and a talking-head avatar need the optional Paper2Video pipeline.

## Promotion kit

From the fact sheet: a 280-character post (claim + key number + link), a 4-6 post thread, a
LinkedIn paragraph, a ~150-word lay summary, and other languages on request. Every claim must be
traceable to the paper.

Detailed procedures, layouts and the full quality checklist: `references/keyless_workflow.md`.

## Workflow Decision Tree

```
User needs promotional materials for a paper?
│
├─ Permanent online presence?            → Paper2Web (website)
├─ Physical conference materials?
│  ├─ Poster session?                    → Paper2Poster
│  └─ Oral presentation?                 → alterlab-scientific-slides (+ Paper2Video for a recording)
├─ Video content?
│  ├─ Journal video abstract (3-5 min)   → Paper2Video
│  ├─ Conference talk recording (15-20)  → Paper2Video
│  └─ Social media (1-3 min)             → Paper2Video
└─ Complete package?                     → all three + promotion kit, from one fact sheet
```

For a tight deadline: website first (most versatile), then poster (print deadline), then video.

## Input Requirements

**LaTeX source** (best: figures and text are exact):
```
paper_directory/
├── main.tex
├── sections/
├── figures/
└── bibliography.bib
```

**PDF**: selectable text (not scanned — `extract_assets.py` warns when the text layer is thin),
embedded fonts, high-resolution figures. Keep each paper's outputs in its own folder.

## Quality Assurance

Before sharing:
1. **Website**: `check_site.py` with zero errors; test on a phone-width window; verify links
2. **Poster**: print a test page or view at 100%; text readable from 1.5-2 m; colours in grayscale
3. **Video**: watch it through; audio matches slides; captions present

Review dimensions (also used by the Paper2Web benchmark, arXiv:2510.15842): content
completeness, accuracy, clarity, informativeness; design aesthetics, layout, readability,
consistency; technical performance, compatibility, accessibility (WCAG), valid HTML/CSS,
print-ready PDF.

## Optional: the Paper2All pipeline

[Paper2All](https://github.com/YuhangChen1/Paper2All) (Chen et al., 2025, "Paper2Web: Let's Make
Your Paper Alive!", arXiv:2510.15842) automates website, poster, PR and video generation with
LLM calls. Use it when the user asks for it by name, or wants synchronized cursor highlights or
a talking-head avatar. It needs model API keys and sends paper content to the providers —
confirm that is acceptable for unpublished work.

- **Install**: `git clone https://github.com/YuhangChen1/Paper2All.git`, a `p2w` conda env
  (Python 3.11) with `pip install -r requirements.txt`; Paper2Video in its own `p2v` env
  (Python 3.10); the talking head in a `hallo` env. System: LibreOffice, Poppler.
- **Keys**: `pipeline_all.py` reads only `OPENROUTER_API_KEY` from the shell (not `.env`) and
  exits without it; the sub-modules and Paper2Video read `OPENAI_API_KEY` / `OPENAI_API_BASE`
  from a `.env` in the repo root; optional `GOOGLE_SEARCH_API_KEY` + `GOOGLE_SEARCH_ENGINE_ID`
  enable logo search; AutoPR has its own `AutoPR/.env`.
- **Run**: `python pipeline_all.py --input-dir path/to/paper --output_dir path/to/output`
  (`--model-choice 1` website, `2` poster, `3` PR; it selects components, not models; the
  underscore `--output_dir` is required although the upstream README shows a hyphen; only the
  first PDF under `--input-dir` is processed unless `--pdf-path` is given; poster size via
  `--poster-width-inches` / `--poster-height-inches`, default 48 x 36). Video:
  `python pipeline_light.py --model_name_t gpt-4.1 --model_name_v gpt-4.1 --result_dir out
  --paper_latex_root path/to/paper`; the talking-head `pipeline.py` adds `--ref_img`,
  `--ref_audio`, `--gpu_list` and needs an NVIDIA A6000-class 48 GB GPU.
- **Outputs**: `output/website/`, `output/poster/`, `output/PR/`; Paper2Video writes to its
  `--result_dir`. Model routing is hard-coded upstream for `pipeline_all.py`; upstream
  publishes no cost figures, so run one paper first and check provider usage.

Details: `references/installation.md`, `references/paper2web.md`, `references/paper2poster.md`,
`references/paper2video.md`, `references/usage_examples.md`.

## Integration and Deployment

- **Website**: GitHub Pages, institutional hosting, Netlify/Vercel
- **Poster**: professional or university print shops, large-format printers; keep the vector PDF
- **Video**: YouTube (public/unlisted), institutional repositories, conference platforms; upload
  the `.srt` as captions
- **Figures and diagrams**: `alterlab-scientific-schematics` (diagrams) and
  `alterlab-generate-image` (illustrations) when the paper lacks a suitable teaser figure

## References

- **`references/keyless_workflow.md`**: the keyless procedures for all outputs, promotion kit, checklist
- **`references/installation.md`**: Paper2All installation and configuration (optional route)
- **`references/paper2web.md`**, **`references/paper2poster.md`**, **`references/paper2video.md`**: Paper2All component documentation
- **`references/usage_examples.md`**: Paper2All workflow examples

Part of the AlterLab Academic Skills suite.
