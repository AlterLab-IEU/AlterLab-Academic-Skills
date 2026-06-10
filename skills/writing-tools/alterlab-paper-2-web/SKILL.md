---
name: alterlab-paper-2-web
description: Converts academic papers into promotional and presentation formats — interactive websites (Paper2Web), presentation videos (Paper2Video), and conference posters (Paper2Poster) from LaTeX or PDF sources. Use when disseminating a paper, preparing for a conference, building an explorable academic homepage, generating a video abstract, or producing a print-ready poster from a paper. Part of the AlterLab Academic Skills suite.
allowed-tools: Read Write Edit Bash
license: MIT
compatibility: Requires an OPENAI_API_KEY (set in a .env file) for the generation pipelines; optional talking-head video needs an NVIDIA GPU (A6000 48GB)
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# Paper2All: Academic Paper Transformation Pipeline

## Overview

This skill enables the transformation of academic papers into multiple promotional and presentation formats using the Paper2All autonomous pipeline. The system converts research papers (LaTeX or PDF) into three primary outputs:

1. **Paper2Web**: Interactive, explorable academic homepages with layout-aware design
2. **Paper2Video**: Professional presentation videos with narration, slides, and optional talking-head
3. **Paper2Poster**: Print-ready conference posters with professional layouts

The pipeline uses LLM-powered content extraction, design generation, and iterative refinement to create high-quality outputs suitable for conferences, journals, preprint repositories, and academic promotion.

## When to Use This Skill

Use this skill when:

- **Creating conference materials**: Posters, presentation videos, and companion websites for academic conferences
- **Promoting research**: Converting published papers or preprints into accessible, engaging web formats
- **Preparing presentations**: Generating video abstracts or full presentation videos from paper content
- **Disseminating findings**: Creating promotional materials for social media, lab websites, or institutional showcases
- **Enhancing preprints**: Adding interactive homepages to bioRxiv, arXiv, or other preprint submissions
- **Batch processing**: Generating promotional materials for multiple papers simultaneously

**Trigger phrases**:
- "Convert this paper to a website"
- "Generate a conference poster from my LaTeX paper"
- "Create a video presentation from this research"
- "Make an interactive homepage for my paper"
- "Transform my paper into promotional materials"
- "Generate a poster and video for my conference talk"

## Visual Enhancement with Scientific Schematics

If a diagram or figure would aid comprehension, invoke the **alterlab-scientific-schematics** skill (diagrams/schematics) or the **alterlab-generate-image** skill (images). Figures are optional — add them only where they improve clarity.

---

## Core Capabilities

### 1. Paper2Web: Interactive Website Generation

Converts papers into layout-aware, interactive academic homepages that go beyond simple HTML conversion.

**Key Features**:
- Responsive, multi-section layouts adapted to paper content
- Interactive figures, tables, and citations
- Mobile-friendly design with navigation
- Automatic logo discovery (with Google Search API)
- Aesthetic refinement and quality assessment

**Best For**: Post-publication promotion, preprint enhancement, lab websites, permanent research showcases

→ **See `references/paper2web.md` for detailed documentation**

---

### 2. Paper2Video: Presentation Video Generation

Generates professional presentation videos with slides, narration, cursor movements, and optional talking-head video.

**Key Features**:
- Automated slide generation from paper structure
- Natural-sounding speech synthesis
- Synchronized cursor movements and highlights
- Optional talking-head video using Hallo2 (requires GPU)
- Multi-language support

**Best For**: Video abstracts, conference presentations, online talks, course materials, YouTube promotion

→ **See `references/paper2video.md` for detailed documentation**

---

### 3. Paper2Poster: Conference Poster Generation

Creates print-ready academic posters with professional layouts and visual design.

**Key Features**:
- Custom poster dimensions (any size)
- Professional design layouts
- High-resolution, print-ready output
- QR codes / institution logos may need to be added manually (not documented pipeline flags)

**Best For**: Conference poster sessions, symposiums, academic exhibitions, virtual conferences

→ **See `references/paper2poster.md` for detailed documentation**

---

## Quick Start

### Prerequisites

1. **Install Paper2All**:
   ```bash
   git clone https://github.com/YuhangChen1/Paper2All.git
   cd Paper2All
   conda create -n p2w python=3.11
   conda activate p2w
   pip install -r requirements.txt
   ```
   Paper2Video runs in its own environment (`conda create -n p2v python=3.10`), and the optional talking-head module in a third (`conda create -n hallo python=3.10`).

2. **Configure API Keys** (create `.env` file):
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_API_BASE=https://api.openai.com/v1   # or https://openrouter.ai/api/v1 for OpenRouter
   # Optional: GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID for logo search
   ```

3. **Install System Dependencies**:
   - LibreOffice (document conversion)
   - Poppler utilities (PDF processing)
   - NVIDIA GPU with 48GB (optional, for talking-head videos)

→ **See `references/installation.md` for complete installation guide**

---

### Basic Usage

`pipeline_all.py` drives the website, poster, and PR-material modules. The `--model-choice` flag selects **which component** to run — it is NOT a model selector. Omit it to run all modules (with automatic PDF detection).

| `--model-choice` | Component |
|------------------|-----------|
| (omitted)        | All modules |
| `1`              | Website (Paper2Web) only |
| `2`              | Poster (Paper2Poster) only |
| `3`              | PR materials (AutoPR) only |

**Generate Everything** (website + poster + PR materials):
```bash
python pipeline_all.py \
  --input-dir "path/to/paper" \
  --output-dir "path/to/output"
```

**Generate Website Only**:
```bash
python pipeline_all.py \
  --input-dir "path/to/paper" \
  --output-dir "path/to/output" \
  --model-choice 1
```

**Generate Poster with Custom Size**:
```bash
python pipeline_all.py \
  --input-dir "path/to/paper" \
  --output-dir "path/to/output" \
  --model-choice 2 \
  --poster-width-inches 60 \
  --poster-height-inches 40
```

**Generate Video** (separate `p2v` environment, lightweight pipeline — no talking-head):
```bash
python pipeline_light.py \
  --model_name_t gpt-4.1 \
  --model_name_v gpt-4.1 \
  --result_dir "path/to/output" \
  --paper_latex_root "path/to/paper"
```

For the full video pipeline with a Hallo2 talking-head, use `pipeline.py` with `--ref_img`, `--ref_audio`, and `--gpu_list` (requires the `hallo` env and an NVIDIA A6000 48GB GPU).

→ **See `references/usage_examples.md` for comprehensive workflow examples**

---

## Workflow Decision Tree

Use this decision tree to determine which components to generate:

```
User needs promotional materials for paper?
│
├─ Need permanent online presence?
│  └─→ Generate Paper2Web (interactive website)
│
├─ Need physical conference materials?
│  ├─→ Poster session? → Generate Paper2Poster
│  └─→ Oral presentation? → Generate Paper2Video
│
├─ Need video content?
│  ├─→ Journal video abstract? → Generate Paper2Video (5-10 min)
│  ├─→ Conference talk? → Generate Paper2Video (15-20 min)
│  └─→ Social media? → Generate Paper2Video (1-3 min)
│
└─ Need complete package?
   └─→ Generate all three components
```

## Input Requirements

### Supported Input Formats

**1. LaTeX Source** (Recommended):
```
paper_directory/
├── main.tex              # Main paper file
├── sections/             # Optional: split sections
├── figures/              # All figure files
├── tables/               # Table files
└── bibliography.bib      # References
```

**2. PDF**:
- High-quality PDF with embedded fonts
- Selectable text (not scanned images)
- High-resolution figures (300+ DPI preferred)

### Input Organization

**Single Paper**:
```bash
input/
└── paper_name/
    ├── main.tex (or paper.pdf)
    ├── figures/
    └── bibliography.bib
```

**Multiple Papers** (batch processing):
```bash
input/
├── paper1/
│   └── main.tex
├── paper2/
│   └── main.tex
└── paper3/
    └── main.tex
```

## Common Parameters

### Component Selection (`pipeline_all.py`)
- `--model-choice 1`: Website (Paper2Web) only
- `--model-choice 2`: Poster (Paper2Poster) only
- `--model-choice 3`: PR materials (AutoPR) only
- (omit `--model-choice`): Run all modules

### Model Selection (video pipeline)
- `--model_name_t`: Model for text/script generation (e.g. `gpt-4.1`)
- `--model_name_v`: Model for visual/slide generation (e.g. `gpt-4.1`)

### Poster Customization (`pipeline_all.py`)
- `--poster-width-inches [width]`: Custom poster width
- `--poster-height-inches [height]`: Custom poster height

## Output Structure

Generated outputs are organized by paper and component:

```
output/
└── paper_name/
    ├── website/
    │   ├── index.html
    │   ├── styles.css
    │   └── assets/
    ├── poster/
    │   ├── poster_final.pdf
    │   ├── poster_final.png
    │   └── poster_source/
    └── video/
        ├── final_video.mp4
        ├── slides/
        ├── audio/
        └── subtitles/
```

## Best Practices

### Input Preparation
1. **Use LaTeX when possible**: Provides best content extraction and structure
2. **Organize files properly**: Keep all assets (figures, tables, bibliography) in paper directory
3. **High-quality figures**: Use vector formats (PDF, SVG) or high-resolution rasters (300+ DPI)
4. **Clean LaTeX**: Remove compilation artifacts, ensure source compiles successfully

### Model Selection Strategy
The LLM is configured via `OPENAI_API_KEY` / `OPENAI_API_BASE` in `.env` (point the base at OpenRouter to use Claude or other models). The video pipeline takes explicit `--model_name_t` / `--model_name_v` overrides:
- **Stronger models (e.g. gpt-4.1)**: Best for production-quality outputs, conferences, publications
- **Cheaper/faster models**: Fine for quick drafts, testing, or simple papers

### Component Priority
For tight deadlines, generate in this order:
1. **Website** (fastest, most versatile, ~15-30 min)
2. **Poster** (moderate speed, for print deadlines, ~10-20 min)
3. **Video** (slowest, can be generated later, ~20-60 min)

### Quality Assurance
Before finalizing outputs:
1. **Website**: Test on multiple devices, verify all links work, check figure quality
2. **Poster**: Print test page, verify text readability from 3-6 feet, check colors
3. **Video**: Watch entire video, verify audio synchronization, test on different devices

## Resource Requirements

### Processing Time
- **Website**: 15-30 minutes per paper
- **Poster**: 10-20 minutes per paper
- **Video (no talking-head)**: 20-60 minutes per paper
- **Video (with talking-head)**: 60-120 minutes per paper

### Computational Requirements
- **CPU**: Multi-core processor for parallel processing
- **RAM**: 16GB minimum, 32GB recommended for large papers
- **GPU**: Optional for standard outputs, required for talking-head (NVIDIA A6000 48GB)
- **Storage**: 1-5GB per paper depending on components and quality settings

### API Costs (Approximate)
- **Website**: $0.50-2.00 per paper (GPT-4)
- **Poster**: $0.30-1.00 per paper (GPT-4)
- **Video**: $1.00-3.00 per paper (GPT-4)
- **Complete package**: $2.00-6.00 per paper (GPT-4)

## Troubleshooting

### Common Issues

**LaTeX parsing errors**:
- Ensure LaTeX source compiles successfully: `pdflatex main.tex`
- Check all referenced files are present
- Verify no custom packages prevent parsing

**Poor figure quality**:
- Use vector formats (PDF, SVG, EPS) instead of rasters
- Ensure raster images are 300+ DPI
- Check figures render correctly in compiled PDF

**Video generation failures**:
- Verify sufficient disk space (5GB+ recommended)
- Check all dependencies installed (LibreOffice, Poppler)
- Review error logs in output directory

**Poster layout issues**:
- Verify poster dimensions are reasonable (24"-72" range)
- Check content length (very long papers may need manual curation)
- Ensure figures have appropriate resolution for poster size

**API errors**:
- Verify API keys in `.env` file
- Check API credit balance
- Ensure no rate limiting (wait and retry)

## Platform-Specific Features

### Social Media Optimization

The system auto-detects target platforms:

**Twitter/X** (English, numeric folder names):
```bash
mkdir -p input/001_twitter/
# Generates English promotional content
```

**Xiaohongshu/小红书** (Chinese, alphanumeric folder names):
```bash
mkdir -p input/xhs_paper/
# Generates Chinese promotional content
```

### Conference-Specific Formatting

Specify conference requirements:
- Standard poster sizes (4'×3', 5'×4', A0, A1)
- Video abstract length limits (typically 3-5 minutes)
- Institution branding requirements
- Color scheme preferences

## Integration and Deployment

### Website Deployment
Deploy generated websites to:
- **GitHub Pages**: Free hosting with custom domain
- **Academic hosting**: University web servers
- **Personal servers**: AWS, DigitalOcean, etc.
- **Netlify/Vercel**: Modern hosting with CI/CD

### Poster Printing
Print-ready files work with:
- Professional poster printing services
- University print shops
- Online services (e.g., Spoonflower, VistaPrint)
- Large format printers (if available)

### Video Distribution
Share videos on:
- **YouTube**: Public or unlisted for maximum reach
- **Institutional repositories**: University video platforms
- **Conference platforms**: Virtual conference systems
- **Social media**: Twitter, LinkedIn, ResearchGate

## Advanced Usage

### Batch Processing
Process multiple papers efficiently:
```bash
# Organize papers in batch directory
for paper in paper1 paper2 paper3; do
    python pipeline_all.py \
      --input-dir input/$paper \
      --output-dir output/$paper &
done
wait
```

### Custom Branding
Apply institution or lab branding:
- Provide logo files in paper directory
- Specify color schemes in configuration
- Use custom templates (advanced)
- Match conference theme requirements

### Multi-Language Support
Generate content in different languages:
- Specify target language in configuration
- System translates content appropriately
- Selects appropriate voice for video narration
- Adapts design conventions to culture

## References and Resources

This skill includes comprehensive reference documentation:

- **`references/installation.md`**: Complete installation and configuration guide
- **`references/paper2web.md`**: Detailed Paper2Web documentation with all features
- **`references/paper2video.md`**: Comprehensive Paper2Video guide including talking-head setup
- **`references/paper2poster.md`**: Complete Paper2Poster documentation with design templates
- **`references/usage_examples.md`**: Real-world examples and workflow patterns

**External Resources**:
- GitHub Repository: https://github.com/YuhangChen1/Paper2All
- Curated Dataset: Available on Hugging Face (13 research categories)
- Benchmark Suite: Reference websites and evaluation metrics

## Evaluation and Quality Metrics

The Paper2All system includes built-in quality assessment:

### Content Quality
- **Completeness**: Coverage of paper content
- **Accuracy**: Faithful representation of findings
- **Clarity**: Accessibility and understandability
- **Informativeness**: Key information prominence

### Design Quality
- **Aesthetics**: Visual appeal and professionalism
- **Layout**: Balance, hierarchy, and organization
- **Readability**: Text legibility and figure clarity
- **Consistency**: Uniform styling and branding

### Technical Quality
- **Performance**: Load times, responsiveness
- **Compatibility**: Cross-browser, cross-device support
- **Accessibility**: WCAG compliance, screen reader support
- **Standards**: Valid HTML/CSS, print-ready PDFs

All outputs undergo automated quality checks before generation completes.

