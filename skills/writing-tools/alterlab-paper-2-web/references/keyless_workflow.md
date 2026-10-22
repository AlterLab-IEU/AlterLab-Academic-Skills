# Keyless Workflow: Website, Poster, Video and Promotion Kit from One Paper

Claude reads the paper and writes every output itself; small scripts do the mechanical parts.
No API key, no second model, and the paper never leaves the machine (except Claude's own web
lookups for links such as the arXiv page or a code repository).

## 0. Read the paper and collect the facts (all outputs share this)

1. **Read** the PDF (the Read tool handles PDFs) or the LaTeX project (`main.tex`, sections,
   `.bib`, `figures/`).
2. **Extract assets** from a PDF:
   ```bash
   uv run --python ">=3.11" --with pymupdf python scripts/extract_assets.py paper.pdf --out assets/ --pages
   ```
   `assets/manifest.json` lists metadata, figure/table captions with their page and position,
   embedded raster images, and page renders. Vector figures are not images: Read the page
   render, then crop each figure by page fractions —
   `--clip 3:0.25,0.07,0.75,0.52:fig1 --dpi 300` → `assets/figures/fig1.png`. From LaTeX, copy
   the figure files directly (convert PDF figures with `pdftoppm -png -r 300`).
3. **Write a fact sheet** (`facts.md`) before any output: exact title, authors in order with
   affiliations, venue/year, DOI/arXiv id, code/data links, the abstract verbatim, 3-5 key
   numbers with the table/figure they come from, the take-home sentence, and the paper's own
   stated limitations. Every output below draws only from this sheet; never round or improve a
   number, never add an author or a link the paper does not give.

## 1. Paper2Web — project website (static HTML/CSS)

Start from `assets/website_template/` (`index.html` + `style.css`; responsive, dark-mode aware,
accessible, no JavaScript):

1. Copy the folder to `site/`, put figures in `site/assets/` (compress to < 1 MB each,
   1600-2000 px wide), and replace every `{{PLACEHOLDER}}` from the fact sheet. Delete sections
   and buttons the paper has no content for (no code repository → no Code button).
2. Write alt text that says what each figure shows, not "figure".
3. Check it:
   ```bash
   python scripts/check_site.py site/
   uv run --python ">=3.11" --with weasyprint --with pymupdf python scripts/check_site.py site/ --preview site_preview.png
   ```
   Errors (missing files, missing alt text, leftover placeholders, no viewport tag) must be
   zero. Read `site_preview.png` (an approximate render) to judge the layout, and check the
   listed external links with WebFetch or lychee.
4. Deploy: GitHub Pages (push `site/` to a `gh-pages` branch or `docs/` folder), a university
   web server, Netlify or Vercel. Add an interactive element only when the paper has one
   (an embedded video, a demo link, a sortable results table as HTML).

## 2. Paper2Poster — print-ready poster (LaTeX)

Start from `assets/poster_template.tex` (tikzposter, three columns, QR code with the `qrcode`
package, optional logo):

1. Set the size in `\geometry{paperwidth=..., paperheight=...}` (default 48 x 36 in; e.g. 60 x
   40 in, or A0 841 x 1189 mm portrait). The template recomputes tikzposter's content area for
   any size.
2. Fill the blocks from the fact sheet: motivation, method (figure + one paragraph), key
   results (figure + 2-3 numbers), take-home, limitations, references; put the DOI or project
   URL in the QR code and `figures/logo.png` for the lab logo.
3. Compile and look: `pdflatex poster.tex`, then `pdftoppm -png -r 20 -singlefile poster.pdf
   preview` and Read the preview; check that body text is readable at 1.5-2 m (scale up with
   `\large`/`\Large` on big formats), nothing overflows a block, and figures are sharp
   (300 dpi at printed size). Missing figure files show a framed placeholder instead of
   failing.

For a poster the user wants to lay out by hand, hand off to `alterlab-latex-posters` (LaTeX) or
`alterlab-pptx-posters` (PowerPoint/HTML).

## 3. Paper2Video — narrated video abstract

1. **Slides**: build them with `alterlab-scientific-slides` (its `build_deck.py` makes an
   editable deck) or Beamer; export to PDF and then to images
   (`pdftoppm -png -r 150 slides.pdf slides/slide`).
2. **Script**: write `narration.json`, one entry per slide —
   `[{"slide": "slides/slide-01.png", "text": "..."}]` — at about 140-160 words per minute
   (a 3-minute abstract is ~450 words). Spoken style, numbers exactly as in the paper.
3. **Voice**, keyless:
   - local text-to-speech with Piper (download a voice once:
     `uv run --with piper-tts python -m piper.download_voices en_US-lessac-medium`), or
   - the author's own recordings (`audio/01.wav`, `audio/02.wav`, ... in slide order) — usually
     best for a journal video abstract, or
   - captions only (`--silent`), timed at `--wpm`.
4. **Assemble** (needs ffmpeg):
   ```bash
   uv run --python ">=3.11" --with piper-tts python scripts/assemble_video.py narration.json \
       -o video/abstract.mp4 --voice voices/en_US-lessac-medium.onnx
   ```
   Output: 1920-px H.264/AAC MP4 with a selectable caption track, a sidecar `.srt`, and per-slide
   timings in `abstract.json`. Watch the result (or grab frames with ffmpeg and Read them) and
   check that audio and slides line up.

Cursor-movement highlights and a talking-head avatar are features of the optional Paper2Video
pipeline (below), not of the keyless route.

## 4. Promotion kit (what AutoPR produces in Paper2All)

From the fact sheet, write: a 280-character post (claim + key number + link), a 4-6 post
thread, a LinkedIn paragraph, a lay summary (~150 words, no jargon), and, if asked, a Chinese
or other-language version. Keep every claim traceable to the paper; no hype words the results do
not support ("revolutionary", "solves").

## 5. Quality checklist (all outputs)

- [ ] Title, authors, affiliations, venue and links match the paper exactly
- [ ] Every number appears in the paper (table/figure noted in the fact sheet)
- [ ] Figures are the paper's own, sharp at their display size, with alt text / captions
- [ ] Limitations stated somewhere a reader will see them
- [ ] Website: `check_site.py` 0 errors; external links checked
- [ ] Poster: compiles, readable at 1.5-2 m, nothing overflows
- [ ] Video: narration matches the slides, captions present, length as requested

## Optional: the Paper2All pipeline (needs a model API key)

The third-party Paper2All repository automates the same outputs with LLM calls routed through
OpenRouter/OpenAI (`OPENROUTER_API_KEY` for `pipeline_all.py`; `OPENAI_API_KEY` /
`OPENAI_API_BASE` in `.env` for the sub-modules and Paper2Video; optional
`GOOGLE_SEARCH_API_KEY` + `GOOGLE_SEARCH_ENGINE_ID` for logo search). Use it when the user asks
for it or wants cursor highlights / a talking head (NVIDIA GPU, ~48 GB). Installation, flags and
examples: `installation.md`, `paper2web.md`, `paper2poster.md`, `paper2video.md`,
`usage_examples.md`.
