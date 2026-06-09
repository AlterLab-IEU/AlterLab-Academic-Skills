---
name: alterlab-generate-image
description: Generates or edits raster images via AI models (FLUX.2, Gemini 3.1 Flash Image / "Nano Banana 2") through an OpenRouter API key. Use when the request is to generate or edit a photo, illustration, artwork, concept art, poster hero image, or presentation/slide visual asset — anything that is not a technical diagram or a data chart. For flowcharts, circuits, pathways, neural-net architectures, and technical/methodology diagrams use alterlab-scientific-schematics; for plotting numeric data (scatter, bar, line) use alterlab-matplotlib instead. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*)
compatibility: Requires an OpenRouter API key
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# Generate Image

Generate and edit high-quality images using OpenRouter's image generation models including FLUX.2 Pro and Gemini 3.1 Flash Image Preview (a.k.a. "Nano Banana 2").

## When to Use This Skill

**Use this skill (`alterlab-generate-image`) for:**
- Photos and photorealistic images
- Artistic illustrations and artwork
- Concept art and visual concepts
- Visual assets for presentations or documents
- Image editing and modifications
- Any general-purpose image generation needs

**Use a different skill instead for:**
- Flowcharts, process diagrams, circuits, biological pathways, system architecture, CONSORT/methodology diagrams, or any technical schematic → `alterlab-scientific-schematics`
- Plotting numeric data from a file or array (scatter, bar, line, distribution) → `alterlab-matplotlib` / `alterlab-plotly` / `alterlab-seaborn`

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

**CRITICAL**: The script requires an OpenRouter API key. Before running, check if the user has configured their API key:

1. Look for a `.env` file in the project directory or parent directories
2. Check for `OPENROUTER_API_KEY=<key>` in the `.env` file
3. If not found, inform the user they need to:
   - Create a `.env` file with `OPENROUTER_API_KEY=your-api-key-here`
   - Or set the environment variable: `export OPENROUTER_API_KEY=your-api-key-here`
   - Get an API key from: https://openrouter.ai/keys

The script will automatically detect the `.env` file and provide clear error messages if the API key is missing.

## Data & Privacy

This skill sends your prompts and any input image to a third-party API (OpenRouter) for processing. Avoid sending confidential, clinical, or unpublished material. The OpenRouter API key is read from the environment (`OPENROUTER_API_KEY`).

## Model Selection

**Default**: `google/gemini-3.1-flash-image-preview` ("Nano Banana 2") — high quality, generation + editing. Use this unless there's a reason not to.

Other models (all support both generation and editing on OpenRouter):
- `black-forest-labs/flux.2-pro` — frontier visual quality, strong prompt adherence, up to 4 MP.
- `black-forest-labs/flux.2-flex` — cheaper; especially good at rendering text/typography and fine detail.

Model IDs are version-sensitive — confirm against https://openrouter.ai/models if a call returns a "model not found" error.

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
- `--model` or `-m`: OpenRouter model ID (default: google/gemini-3.1-flash-image-preview)
- `--output` or `-o`: Output file path (default: generated_image.png)
- `--api-key`: OpenRouter API key (overrides .env file)

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
- The script exits non-zero with a clear message on a missing API key, missing `requests`, an API error (with status code), or an unexpected response shape — read it and fix before retrying.

