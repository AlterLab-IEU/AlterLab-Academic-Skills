---
name: alterlab-generate-image
description: Generates or edits raster images via AI models (FLUX.2, Gemini 3.1 Flash Image / "Nano Banana 2") through an OpenRouter API key. Use when the request is to generate or edit a photo, illustration, artwork, concept art, poster hero image, or presentation/slide visual asset — anything that is not a technical diagram, an infographic, or a data chart. For flowcharts, circuits, pathways, neural-net architectures, and technical/methodology diagrams use alterlab-scientific-schematics; for infographics that lay out statistics or timelines use alterlab-infographics; for plotting numeric data (scatter, bar, line) use alterlab-matplotlib instead. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*)
compatibility: Requires an OpenRouter API key (OPENROUTER_API_KEY) and the requests library; the default model can be overridden with ALTERLAB_IMAGE_MODEL
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# Generate Image

Generate and edit high-quality images using OpenRouter's image generation models including FLUX.2 Pro and Gemini 3.1 Flash Image (a.k.a. "Nano Banana 2").

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

## Quick Start

Use the `scripts/generate_image.py` script to generate or edit images:

```bash
# Generate a new image
python scripts/generate_image.py "A beautiful sunset over mountains"

# Edit an existing image
python scripts/generate_image.py "Make the sky purple" --input photo.jpg
```

This generates/edits an image and saves it as `generated_image.png` in the current directory.

## API Key Setup

The script needs an OpenRouter API key and stops with an error if it can't find one. It checks, in order: the `--api-key` flag, the `OPENROUTER_API_KEY` environment variable, then an `OPENROUTER_API_KEY=<key>` line in a `.env` file in the current or a parent directory. If none is set, ask the user to either:
- `export OPENROUTER_API_KEY=your-api-key-here`, or
- add `OPENROUTER_API_KEY=your-api-key-here` to a `.env` file.

Keys are issued at https://openrouter.ai/keys.

## Data & Privacy

This skill sends your prompts and any input image to a third-party API (OpenRouter) for processing. Avoid sending confidential, clinical, or unpublished material. The OpenRouter API key is read from the environment (`OPENROUTER_API_KEY`).

## Model Selection

**Default**: `google/gemini-3.1-flash-image` ("Nano Banana 2", GA) — high quality, generation + editing. Use this unless there's a reason not to. It replaced `google/gemini-3.1-flash-image-preview`, which Google shut down on 2026-06-25. Set `ALTERLAB_IMAGE_MODEL` to change the default for every run, or pass `--model` for one run.

Other models (all support both generation and editing on OpenRouter):
- `black-forest-labs/flux.2-pro` — frontier visual quality, strong prompt adherence, up to 4 MP.
- `black-forest-labs/flux.2-flex` — cheaper; especially good at rendering text/typography and fine detail.

Model IDs are version-sensitive (verified against the OpenRouter model list on 2026-09-23) — re-check https://openrouter.ai/models if a call returns a "model not found" error. The script uses OpenRouter's chat-completions endpoint with the `modalities` parameter. OpenRouter launched a dedicated Image API (`/api/v1/images`) in June 2026: image models that existed then stay available on chat completions (all models listed here do), but models added since may be served only by the Image API — if a newer model fails with this script, that is the likely reason.

## Common Usage Patterns

```bash
# Generate (default model) to a chosen path
python scripts/generate_image.py "Abstract art" --output artwork.png

# Generate with a specific model
python scripts/generate_image.py "A cat in space" --model "black-forest-labs/flux.2-pro"

# Edit an existing image (edit mode is triggered by --input)
python scripts/generate_image.py "Add sunglasses to the person" --input portrait.png --output cleaned.png
```

For multiple images, run the script once per prompt with distinct `--output` paths (it always writes one file and overwrites the default `generated_image.png`).

## Script Parameters

- `prompt` (required): Text description of the image to generate, or editing instructions
- `--input` or `-i`: Input image path for editing (enables edit mode)
- `--model` or `-m`: OpenRouter model ID (default: `$ALTERLAB_IMAGE_MODEL`, else google/gemini-3.1-flash-image)
- `--output` or `-o`: Output file path (default: generated_image.png)
- `--api-key`: OpenRouter API key (overrides `OPENROUTER_API_KEY` and `.env`)

## Example Use Cases

```bash
# Conceptual figure for a paper (illustration, not a data plot)
python scripts/generate_image.py "Microscopic view of cancer cells being attacked by immunotherapy agents, clean scientific illustration style" --output figures/immunotherapy_concept.png

# Slide background / poster hero image
python scripts/generate_image.py "Abstract blue and white background with subtle molecular patterns, professional presentation style" --output slides/background.png
python scripts/generate_image.py "Modern, well-lit laboratory with current equipment, photorealistic" --output poster/hero.png
```

## Notes & Tips

- Output is always one PNG. Images come back base64-encoded (as a data URL or content part) and are decoded and written to `--output`; the script handles both the `images` and `content` response shapes used by different OpenRouter models.
- Supported input formats for editing: PNG, JPEG, GIF, WebP. The input is base64-encoded and sent with the edit prompt.
- Editing works best with specific, element-referenced instructions — "change the sky to sunset colors" beats "edit the sky".
- Generation typically takes ~5-30 s depending on model. Pricing: https://openrouter.ai/models
- The script exits non-zero with a clear message on a missing API key, missing `requests`, a network error, an API error (with status code), or a response without an image — read it and fix before retrying.
- If an image-only model (e.g. FLUX.2) rejects the request with a 400/422, the script retries once asking for image output only.

