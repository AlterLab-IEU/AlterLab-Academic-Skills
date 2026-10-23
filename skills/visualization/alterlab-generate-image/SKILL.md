---
name: alterlab-generate-image
description: Creates and edits images for research communication with no API key — Claude draws illustrations, concept art, icons, backgrounds and slide/poster visuals as code (SVG, TikZ, matplotlib) rendered locally with exact, editable text, and edits existing images with Pillow (crop, annotate, scale bars, redaction, overlays). Photorealistic generation and AI edits (FLUX.2, Gemini 3.1 Flash Image via OpenRouter) are an optional extra with OPENROUTER_API_KEY. Use when the request is to generate or edit a photo, illustration, artwork, concept art, poster hero image, or presentation/slide visual asset — anything that is not a technical diagram, an infographic, or a data chart. For flowcharts, circuits, pathways, neural-net architectures, and technical/methodology diagrams use alterlab-scientific-schematics; for infographics that lay out statistics or timelines use alterlab-infographics; for plotting numeric data (scatter, bar, line) use alterlab-matplotlib instead. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*) WebSearch WebFetch
compatibility: "No API key required. Code-drawn images render via `uv run --python \">=3.11\" --with cairosvg --with pillow` (needs the Cairo library); edits use Pillow. Optional AI backend: OPENROUTER_API_KEY and requests; default model overridable with ALTERLAB_IMAGE_MODEL."
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    last_updated: "2026-10-22"
    credentials: "optional: OPENROUTER_API_KEY (the AI image-model backend, generate_image.py: photorealistic generation and AI edits with Gemini 3.1 Flash Image or FLUX.2 through OpenRouter)"
---

# Generate Image

Create and edit images for papers, slides, posters and websites. **The default needs no API
key**: Claude draws the image as code and renders it locally, or edits an existing file with
Pillow. Text in a code-drawn image is exactly what was typed, the source stays editable, and
nothing leaves the machine. Photorealistic generation is the one thing code cannot do; it is
available through an optional image model when the user has an OpenRouter key.

## When to Use This Skill

**Use this skill (`alterlab-generate-image`) for:**
- Photos and photorealistic images
- Artistic illustrations and artwork
- Concept art and visual concepts
- Visual assets for presentations or documents
- Image editing and modifications
- Any general-purpose image generation needs

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Flowchart, CONSORT/PRISMA or methodology diagram, circuit, biological pathway, system or neural-network architecture | `alterlab-scientific-schematics` |
| Infographic that lays out statistics, a timeline, a comparison, or process steps as a designed graphic | `alterlab-infographics` |
| Plot of numeric data from a file or array (scatter, bar, line, distribution) | `alterlab-matplotlib` / `alterlab-seaborn` / `alterlab-plotly` |
| Diagram that should stay editable, version-controlled text in a README or Markdown doc | `alterlab-mermaid` |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-scientific-schematics`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

## Choose the route

| Request | Keyless route (default) | With `OPENROUTER_API_KEY` (optional) |
|---------|-------------------------|---------------------------------------|
| Concept illustration, graphical-abstract art, icons, cover art | Draw as SVG (layered shapes, gradients) → `figure_tools.py render` | `generate_image.py` for a painterly or photographic look |
| Background, pattern, texture for a slide or poster | Procedural SVG or matplotlib (Python places the shapes) → render | — |
| Edit an existing image: crop, resize, labels, arrows, scale bar, blur/redact, add a drawn element | `edit_image.py --input …` (overlay an SVG-drawn element rendered with `--transparent`) | `generate_image.py --input …` for photo-real changes (relight, remove an object, change the sky) |
| Photorealistic scene or photo | An openly licensed real photo (Wikimedia Commons / Unsplash licence) with the licence and attribution recorded, or a stylised code-drawn version — say which; never present a drawing as a photograph | `generate_image.py` (Gemini 3.1 Flash Image or FLUX.2 Pro) |

Ask before choosing when the user's wording does not settle it ("photorealistic" vs "clean
illustration"), and say plainly when a request needs the optional key.

## Keyless workflow: code-drawn images

1. **Plan the canvas**: 1920x1080 for a 16:9 slide, 3.5 in / 7.2 in wide for a journal figure,
   the poster's hero box size; palette (Okabe-Ito or the user's brand colours); elements.
2. **Draw** the image as SVG (or TikZ for a LaTeX document, matplotlib for procedural
   patterns), saved next to the output, e.g. `figures/immunotherapy_concept.svg`. Techniques —
   layered shapes, linear/radial gradients for soft lighting, opacity, `clipPath`, procedural
   placement with Python — and worked recipes are in `references/code_drawn_images.md`.
3. **Render** locally:
   ```bash
   uv run --python ">=3.11" --with cairosvg --with pillow python scripts/figure_tools.py render \
       figures/immunotherapy_concept.svg -o figures/immunotherapy_concept.png --width-px 2400
   ```
   It reports the renderer, size, DPI and blank-image check, and lints text (overflowing a box,
   too small at `--width-in`). Add `--transparent` for an element meant to be overlaid.
4. **Look and refine**: Read the PNG, compare it with the request, fix what is off, re-render
   (`_v2`). Optional bookkeeping: `python scripts/figure_tools.py score log.json --kind image …`.
5. **Deliver** the PNG (and PDF/SVG for print), the source file, and one line on what it is
   (e.g. "vector illustration, not a micrograph").

## Keyless workflow: editing an existing image

Read the image first to find the coordinates, then apply operations in order:

```bash
uv run --python ">=3.11" --with pillow python scripts/edit_image.py --input field.png --info
uv run --python ">=3.11" --with pillow python scripts/edit_image.py --input field.png \
    --output field_annotated.png --scale-bar 20,0.25,um,br \
    --arrow 590,60,515,125,#FFFFFF,4 --text "596,56,22,#FFFFFF,rb:mitotic?"
```

Operations: `--crop`, `--resize`/`--scale`, `--rotate`, `--flip`, `--grayscale`,
`--brightness`/`--contrast`/`--saturation`/`--sharpness`, `--blur`, `--redact X0,Y0,X1,Y1[,blur|pixelate|fill]`
(faces, names, record numbers), `--rect`/`--ellipse`/`--line`/`--arrow`, `--text "X,Y[,SIZE[,COLOR[,ANCHOR]]]:TEXT"`,
`--scale-bar LENGTH,UNITS_PER_PX,UNIT[,CORNER]` (computes the bar length in pixels), `--overlay FILE@X,Y[,OPACITY]`,
`--pad`. To **add an object** (glasses, a label badge, an icon), draw it as SVG sized to the
spot, render it with `--transparent`, overlay it at the coordinates you read off the image, then
Read the result to check placement. Output keeps the input's pixels except where edited; scale
bars on microscopy must use the true pixel size, and no resampling should follow them.

## Optional: AI image model (OpenRouter)

Use only when the user asks for photorealism or an AI edit and has a key. `generate_image.py`
reads it from `--api-key`, `OPENROUTER_API_KEY`, or an `OPENROUTER_API_KEY=` line in a `.env`
file (current or parent directory); without one it exits 2 and names the keyless alternatives.
Keys are issued at https://openrouter.ai/keys.

```bash
python scripts/generate_image.py "Modern, well-lit laboratory with current equipment, photorealistic" \
    --output poster/hero.png
python scripts/generate_image.py "Add sunglasses to the person" --input portrait.png --output cleaned.png
python scripts/generate_image.py "A cat in space" --model "black-forest-labs/flux.2-pro" --output cat.png
```

Parameters: `prompt` (required); `--input/-i` (edit mode); `--model/-m` (default
`$ALTERLAB_IMAGE_MODEL`, else `google/gemini-3.1-flash-image`, "Nano Banana 2", GA — it replaced
the `-preview` ID Google shut down on 2026-06-25); `--output/-o` (default `generated_image.png`,
folders are created); `--api-key`. Other models: `black-forest-labs/flux.2-pro` (frontier
quality, up to 4 MP) and `black-forest-labs/flux.2-flex` (cheaper, good typography). Model IDs
were verified against the OpenRouter list on 2026-09-23; the script uses chat completions with
the `modalities` parameter, so a model added only to OpenRouter's newer Image API
(`/api/v1/images`) may fail here. Output is one PNG per run; image-only models that reject a
text modality are retried once with image output only. Supported edit inputs: PNG, JPEG, GIF,
WebP.

**Data & privacy:** the AI backend sends prompts and any input image to OpenRouter; keep
confidential, clinical, or unpublished material out of it. The keyless routes stay local.

## Notes & Tips

- A code-drawn "illustration" of cells, molecules or equipment is a schematic depiction: say so
  in captions, and never let it stand in for experimental imagery.
- Real photos from Wikimedia Commons carry their licence on the file page; record title, author,
  licence and URL with the image and credit it where it is shown.
- AI-generated images draw their own text, often garbled: add labels afterwards with
  `edit_image.py --text` or in the slide/figure software.
- Editing works best with specific, element-referenced instructions ("arrow to the cell at top
  right", "blur the name field in the header").

Part of the AlterLab Academic Skills suite.
