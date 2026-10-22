# Script Reference and Prompt Writing

## build_deck.py (keyless, default)

Builds an editable 16:9 PowerPoint from a JSON deck plan with python-pptx — no image model, no key.

```bash
uv run --python ">=3.11" --with python-pptx --with pillow python scripts/build_deck.py deck.json -o talk.pptx
soffice --headless --convert-to pdf talk.pptx     # LibreOffice export for the visual review
```

**Plan fields:** `theme` (`primary`, `accent`, `text`, `background`, `muted`, `font`, `title_pt` 36,
`body_pt` 24, `small_pt` 14), `footer`, and `slides`, each with a `layout`:

| Layout | Fields |
|--------|--------|
| `title` | `title`, `subtitle` (presenter, affiliation, venue) |
| `section` | `title` |
| `bullets` | `title`, `bullets` (3-4), optional `image` placed on the right |
| `image` | `title`, `image`, optional `caption` |
| `two_column` | `title`, `left`, `right`, optional `left_heading`, `right_heading` |
| `takeaway` | `title`, `message` |

Every slide also takes `notes` (speaker notes) and `citation` (small italic line above the
footer). Image paths are relative to the plan file; a missing image fails the build unless
`--allow-missing-images`. Warnings (printed, never auto-fixed): more than 4 bullets, a bullet over
12 words, a title over 60 characters, body text under 18 pt.

## generate_slide_image.py

Keyless by default: renders a code-drawn slide visual, or prints the slide design brief.
With `--backend ai` (needs `OPENROUTER_API_KEY`) it generates slides or visuals with Nano Banana Pro.

```bash
# Keyless: design brief for a full slide or a visual (no file written)
python scripts/generate_slide_image.py "Data pipeline: collect, clean, model" -o slides/pipeline.png --visual-only
# Keyless: render the SVG Claude drew to a 1920-px PNG
uv run --python ">=3.11" --with cairosvg --with pillow python scripts/generate_slide_image.py slides/pipeline.svg -o slides/pipeline.png

# Optional AI backend
python scripts/generate_slide_image.py "slide description" -o output.png --backend ai
python scripts/generate_slide_image.py "visual description" -o output.png --visual-only --backend ai
python scripts/generate_slide_image.py "Create a slide explaining this chart" -o slide.png --attach chart.png --backend ai
```

**Options:**
- `-o, --output`: Output file path (required)
- `--backend {code,ai}`: `code` (default, keyless) or `ai` (OpenRouter; exits 2 without a key)
- `--attach IMAGE`: Reference image(s): sent to the model with `--backend ai`; listed in the keyless brief as figures to place unchanged
- `--visual-only`: A visual for a slide rather than a complete slide
- `--width-px`: PNG width for a rendered source (default 1920)
- `--iterations`: Max refinement iterations for `--backend ai` (default: 2)
- `--api-key`: OpenRouter API key (or set OPENROUTER_API_KEY env var)
- `-v, --verbose`: Verbose output

**Attaching Reference Images (`--backend ai`):**

Use `--attach` when you want Nano Banana Pro to see existing images as context:
- "Create a slide about this data" + attach the data chart
- "Make a title slide with this logo" + attach the logo
- "Combine these figures into one slide" + attach multiple images
- "Explain this diagram in a slide" + attach the diagram

**Environment Setup (`--backend ai` only):**
```bash
export OPENROUTER_API_KEY='your_api_key_here'
# Get key at: https://openrouter.ai/keys

# Optional: override the default Gemini image/review models (routed via OpenRouter)
# export ALTERLAB_IMAGE_MODEL='google/...'
# export ALTERLAB_REVIEW_MODEL='google/...'
```

The key can also be supplied via `--api-key` or a `.env` file in the working directory (or a parent). Refinement is hard-capped at 2 iterations regardless of `--iterations`.

## slides_to_pdf.py

Combine multiple slide images into a single PDF.

```bash
# Combine PNG files
python scripts/slides_to_pdf.py slides/*.png -o presentation.pdf

# Combine specific files in order
python scripts/slides_to_pdf.py title.png intro.png methods.png -o talk.pdf

# From directory (sorted by filename)
python scripts/slides_to_pdf.py slides/ -o presentation.pdf
```

**Options:**
- `-o, --output`: Output PDF path (required)
- `--dpi`: PDF resolution (default: 150)
- `-v, --verbose`: Verbose output

**Tip:** Name slides with numbers for correct ordering: `01_title.png`, `02_intro.png`, etc.

## validate_presentation.py

```bash
python scripts/validate_presentation.py presentation.pdf --duration 15

# Checks:
# - Slide count vs. recommended range
# - File size warnings
# - Slide dimensions
# - Font sizes (PowerPoint)
# - Compilation (Beamer)
```

## pdf_to_images.py

```bash
python scripts/pdf_to_images.py presentation.pdf output/slide --dpi 150

# Converts PDF to images for visual inspection
# Supports: JPG, PNG
# Adjustable DPI
# Page range selection
```

## Prompt Writing for Slide Generation (optional AI backend)

The same content checklist applies to a keyless deck plan: slide type, title, 3-4 key points,
the visual, and the theme.

### Full Slide Prompts (PDF Workflow)

For complete slides, include:
1. **Slide type**: Title slide, content slide, diagram slide, etc.
2. **Title**: The slide title text
3. **Content**: Key points, bullet items, or descriptions
4. **Visual elements**: What imagery, icons, or graphics to include
5. **Design style**: Color scheme, mood, aesthetic

**Example prompts:**

```
Title slide:
"Title slide for a medical research presentation. Title: 'Advances in Cancer Immunotherapy'. Subtitle: 'Clinical Trial Results 2024'. Professional medical theme with subtle DNA helix in background. Navy blue and white color scheme."

Content slide:
"Presentation slide titled 'Key Findings'. Three bullet points: 1) 40% improvement in response rate, 2) Reduced side effects, 3) Extended survival outcomes. Include relevant medical icons. Clean, professional design with green and white colors."

Diagram slide:
"Presentation slide showing the research methodology. Title: 'Study Design'. Flowchart showing: Patient Screening → Randomization → Treatment Groups (A, B, Control) → Follow-up → Analysis. CONSORT-style flow diagram. Professional academic style."
```

### Visual-Only Prompts (PPT Workflow)

For images to embed in PowerPoint, focus on the visual element only:

```
"Flowchart showing machine learning pipeline: Data Collection → Preprocessing → Model Training → Validation → Deployment. Clean technical style, blue and gray colors."

"Conceptual illustration of cloud computing with servers, data flow, and connected devices. Modern flat design, suitable for business presentation."

"Scientific diagram of cell division process showing mitosis phases. Educational style with labels, colorblind-friendly colors."
```

## External Tools

**Recommended:**
- PDF viewer: For reviewing presentations
- Color contrast checker: WebAIM Contrast Checker
- Color blindness simulator: Coblis
- Timer app: For practice sessions
- Screen recorder: For self-review
