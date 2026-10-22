# Scientific Schematics - Quick Reference

**How it works (no API key):** Claude draws the diagram as SVG / TikZ / schemdraw code ->
`generate_schematic.py` renders and lints it -> Claude Reads the PNG and scores it ->
`figure_tools.py score` applies the document-type threshold -> revise once if needed.

## Commands

```bash
# Design brief for the venue (guidelines, threshold, criteria)
python scripts/generate_schematic.py --brief --doc-type journal

# Render + lint a source (SVG needs cairosvg; TikZ needs a LaTeX engine)
uv run --python ">=3.11" --with cairosvg --with pillow python scripts/generate_schematic.py \
    figures/consort.svg -o figures/consort_v1.png --doc-type journal --width-in 7.2 --gray

# Vector export for submission
uv run --python ">=3.11" --with cairosvg python scripts/figure_tools.py render \
    figures/consort.svg -o figures/consort.pdf

# Record the review (answers REVISE / DONE / STOP)
python scripts/figure_tools.py score figures/consort_review_log.json --kind schematic \
    --doc-type journal --image figures/consort_v1.png --source figures/consort.svg \
    --score 8.0 --critique "..."

# Thresholds and criteria
python scripts/figure_tools.py thresholds --kind schematic
```

## Thresholds (score out of 10; max 2 iterations)

| journal | conference | thesis | grant | preprint | report | poster | presentation | default |
|---------|-----------|--------|-------|----------|--------|--------|--------------|---------|
| 8.5 | 8.0 | 8.0 | 8.0 | 7.5 | 7.5 | 7.0 | 6.5 | 7.5 |

Criteria, 0-2 each: scientific accuracy; clarity and readability; label quality; layout and
composition; professional appearance.

## Sizes

| Target | Width | Notes |
|--------|-------|-------|
| One journal column | 3.5 in (89 mm) | `--width-in 3.5` |
| Two columns / full width | 7.2 in (183 mm) | `--width-in 7.2` |
| Slide (16:9) | 13.33 x 7.5 in | labels >= 18 pt at that size |
| Print | 300 dpi PNG, or PDF/SVG vector | smallest label >= 7 pt at print size |

## Starting points

- CONSORT: `assets/consort_template.svg` (replace every `N_*` token with the trial's counts)
- SVG building blocks, PRISMA / transformer / pathway / block-diagram recipes, TikZ and
  schemdraw skeletons: `README.md` in this folder
- Diagram catalogue: `diagram_types.md`; standards: `best_practices.md`

## Before you deliver

- [ ] Every count and label matches the user's source (re-read it, do not trust memory)
- [ ] No overflow warnings; smallest label >= 7 pt at print width
- [ ] Grayscale preview still distinguishes every category
- [ ] Review log shows the final score >= threshold, or lists what is still short
- [ ] PNG (300 dpi) + PDF/SVG + source file + review log saved together

## Optional AI raster backend

With `OPENROUTER_API_KEY` set, `python scripts/generate_schematic.py "description" -o out.png
--doc-type journal --backend ai` generates the image with Nano Banana 2 and reviews it with
Gemini 3.1 Pro Preview (see `ai_generation_guide.md`). Without the key it exits 2 and names the
keyless route. AI images redraw every label themselves, so check counts and spelling.
