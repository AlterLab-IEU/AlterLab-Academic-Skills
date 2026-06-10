# Nano Banana Pro Script Reference and Prompt Writing

## generate_slide_image.py

Generate presentation slides or visuals using Nano Banana Pro AI.

```bash
# Full slide (default) - generates complete slide as image
python scripts/generate_slide_image.py "slide description" -o output.png

# Visual only - generates just the image/figure for embedding in PPT
python scripts/generate_slide_image.py "visual description" -o output.png --visual-only

# With reference images attached (Nano Banana Pro will see these)
python scripts/generate_slide_image.py "Create a slide explaining this chart" -o slide.png --attach chart.png
python scripts/generate_slide_image.py "Combine these into a comparison slide" -o compare.png --attach before.png --attach after.png
```

**Options:**
- `-o, --output`: Output file path (required)
- `--attach IMAGE`: Attach image file(s) as context for generation (can use multiple times)
- `--visual-only`: Generate just the visual/figure, not a complete slide
- `--iterations`: Max refinement iterations (default: 2)
- `--api-key`: OpenRouter API key (or set OPENROUTER_API_KEY env var)
- `-v, --verbose`: Verbose output

**Attaching Reference Images:**

Use `--attach` when you want Nano Banana Pro to see existing images as context:
- "Create a slide about this data" + attach the data chart
- "Make a title slide with this logo" + attach the logo
- "Combine these figures into one slide" + attach multiple images
- "Explain this diagram in a slide" + attach the diagram

**Environment Setup:**
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

## Prompt Writing for Slide Generation

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
