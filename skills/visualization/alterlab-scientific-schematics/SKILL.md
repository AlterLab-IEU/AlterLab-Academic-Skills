---
name: alterlab-scientific-schematics
description: Creates publication-quality scientific diagrams with Nano Banana 2 AI and smart iterative refinement, using Gemini 3.1 Pro Preview for quality review and regenerating only when quality falls below the document-type threshold. Use when the request is for a technical or scientific diagram — neural-network architectures, system/block diagrams, flowcharts, biological pathways, circuits, or other complex scientific visuals. For general photos, illustrations, or artwork use generate-image, for text-based Mermaid diagrams use mermaid. Part of the AlterLab Academic Skills suite.
allowed-tools: Read Write Edit Bash
license: MIT
compatibility: Requires an OpenRouter API key (OPENROUTER_API_KEY) for Nano Banana 2 generation and Gemini 3.1 Pro Preview quality review
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# Scientific Schematics and Diagrams

## Overview

Scientific schematics and diagrams transform complex concepts into clear visual representations for publication. **This skill uses Nano Banana 2 AI for diagram generation with Gemini 3.1 Pro Preview quality review.**

**How it works:**
- Describe your diagram in natural language
- Nano Banana 2 generates publication-quality images automatically
- **Gemini 3.1 Pro Preview reviews quality** against document-type thresholds
- **Smart iteration**: Only regenerates if quality is below threshold
- Publication-ready output in minutes
- No coding, templates, or manual drawing required

**Quality Thresholds by Document Type:**
| Document Type | Threshold | Description |
|---------------|-----------|-------------|
| journal | 8.5/10 | Nature, Science, peer-reviewed journals |
| conference | 8.0/10 | Conference papers |
| thesis | 8.0/10 | Dissertations, theses |
| grant | 8.0/10 | Grant proposals |
| preprint | 7.5/10 | arXiv, bioRxiv, etc. |
| report | 7.5/10 | Technical reports |
| poster | 7.0/10 | Academic posters |
| presentation | 6.5/10 | Slides, talks |
| default | 7.5/10 | General purpose |

**Simply describe what you want, and Nano Banana 2 creates it.** All diagrams are stored in the figures/ subfolder and referenced in papers/posters.

## Quick Start: Generate Any Diagram

Create any scientific diagram by simply describing it. Nano Banana 2 handles everything automatically with **smart iteration**:

```bash
# Generate for journal paper (highest quality threshold: 8.5/10)
python scripts/generate_schematic.py "CONSORT participant flow diagram with 500 screened, 150 excluded, 350 randomized" -o figures/consort.png --doc-type journal

# Generate for presentation (lower threshold: 6.5/10 - faster)
python scripts/generate_schematic.py "Transformer encoder-decoder architecture showing multi-head attention" -o figures/transformer.png --doc-type presentation

# Generate for poster (moderate threshold: 7.0/10)
python scripts/generate_schematic.py "MAPK signaling pathway from EGFR to gene transcription" -o figures/mapk_pathway.png --doc-type poster

# Custom max iterations (max 2)
python scripts/generate_schematic.py "Complex circuit diagram with op-amp, resistors, and capacitors" -o figures/circuit.png --iterations 2 --doc-type journal
```

**What happens behind the scenes:**
1. **Generation 1**: Nano Banana 2 creates initial image following scientific diagram best practices
2. **Review 1**: **Gemini 3.1 Pro Preview** evaluates quality against document-type threshold
3. **Decision**: If quality >= threshold → **DONE** (no more iterations needed!)
4. **If below threshold**: Improved prompt based on critique, regenerate
5. **Repeat**: Until quality meets threshold OR max iterations reached

**Smart Iteration Benefits:**
- ✅ Saves API calls if first generation is good enough
- ✅ Higher quality standards for journal papers
- ✅ Faster turnaround for presentations/posters
- ✅ Appropriate quality for each use case

**Output**: Versioned images plus a detailed review log with quality scores, critiques, and early-stop information.

### Configuration

Set your OpenRouter API key:
```bash
export OPENROUTER_API_KEY='your_api_key_here'
```

Get an API key at: https://openrouter.ai/keys

### Data & privacy

This skill's generation scripts (`scripts/generate_schematic_ai.py`) send your diagram description / prompt to a **third-party API (OpenRouter)** over the network for image generation and quality review. Your text prompts — and any details you include in them — leave your machine and are processed by an external provider. **Do not include confidential, clinical, patient-identifying, or unpublished proprietary content** in figure descriptions. Describe figures generically and add sensitive labels locally afterward if needed.

### AI Generation Best Practices

Good prompts are specific: name the diagram **type**, **components**, **flow/direction**,
**labels**, and **style**. Vague prompts ("make a flowchart", "neural network") underperform.
Scientific quality guidelines (clean background, ≥10pt labels, sans-serif, Okabe-Ito palette,
proper spacing) are applied automatically. Good/bad prompt examples and the full guideline
list are in `references/ai_generation_guide.md`.

## When to Use This Skill

This skill should be used when:
- Creating neural network architecture diagrams (Transformers, CNNs, RNNs, etc.)
- Illustrating system architectures and data flow diagrams
- Drawing methodology flowcharts for study design (CONSORT, PRISMA)
- Visualizing algorithm workflows and processing pipelines
- Creating circuit diagrams and electrical schematics
- Depicting biological pathways and molecular interactions
- Generating network topologies and hierarchical structures
- Illustrating conceptual frameworks and theoretical models
- Designing block diagrams for technical papers

## How to Use This Skill

**Simply describe your diagram in natural language.** Nano Banana 2 generates it automatically:

```bash
python scripts/generate_schematic.py "your diagram description" -o output.png
```

**That's it!** The AI handles:
- ✓ Layout and composition
- ✓ Labels and annotations
- ✓ Colors and styling
- ✓ Quality review and refinement
- ✓ Publication-ready output

**Works for all diagram types:**
- Flowcharts (CONSORT, PRISMA, etc.)
- Neural network architectures
- Biological pathways
- Circuit diagrams
- System architectures
- Block diagrams
- Any scientific visualization

**No coding, no templates, no manual drawing required.**

---

# AI Generation Mode (Nano Banana 2 + Gemini 3.1 Pro Preview Review)

The AI generation system uses **smart iteration**: Nano Banana 2 generates an image, Gemini 3.1
Pro Preview scores it (0-10 across scientific accuracy, clarity, label quality, layout, and
professional appearance), and the system **stops early** once the score meets the document-type
threshold — otherwise it improves the prompt from the critique and regenerates (max 2 iterations).
Every run writes a JSON review log with per-iteration scores, critiques, and early-stop info.

The deep dive — iteration flowchart, review rubric, example review output, decision table, JSON
log schema, the `ScientificSchematicGenerator` Python API, all command-line options, and prompt
engineering tips — is in `references/ai_generation_guide.md`.

Copy-and-adapt worked invocations for CONSORT flowcharts, transformer architectures, biological
pathways, and system block diagrams are in `references/generation_examples.md`.

---

## Command-Line Usage

The main entry point for generating scientific schematics:

```bash
# Basic usage
python scripts/generate_schematic.py "diagram description" -o output.png

# Custom iterations (max 2)
python scripts/generate_schematic.py "complex diagram" -o diagram.png --iterations 2

# Verbose mode
python scripts/generate_schematic.py "diagram" -o out.png -v
```

**Note:** The Nano Banana 2 AI generation system includes automatic quality review in its iterative refinement process. Each iteration is evaluated for scientific accuracy, clarity, and accessibility.

## Best Practices Summary

Design for **clarity over complexity**, consistent styling, colorblind accessibility (Okabe-Ito,
redundant encoding), ≥7-8 pt sans-serif type, and vector output (PDF/SVG; 300+ DPI for raster).
Integrate with LaTeX via `\includegraphics{}`, caption thoroughly, reference in text, and keep
prompts + outputs under version control. The full design/technical/integration checklist and the
pre-submission verification checklist are in `references/submission_checklist.md`.

## Troubleshooting Common Issues

For fixes to AI generation problems (overlaps, poor connections), image-quality issues,
quality-check failures, and accessibility problems (grayscale contrast, small text), see
`references/troubleshooting.md`. Most issues resolve by making the prompt more specific or
raising `--iterations 2`.

## Resources and References

### Detailed References

Load these files for comprehensive information on specific topics:

- **`references/ai_generation_guide.md`** - Smart-iteration workflow, review rubric, Python API, CLI options, prompt engineering
- **`references/generation_examples.md`** - Worked CLI invocations (CONSORT, transformer, pathway, system diagrams)
- **`references/troubleshooting.md`** - Fixes for generation, quality-check, and accessibility issues
- **`references/submission_checklist.md`** - Best-practices summary and pre-submission verification checklist
- **`references/diagram_types.md`** - Catalog of scientific diagram types with examples
- **`references/best_practices.md`** - Publication standards and accessibility guidelines

### External Resources

**Python Libraries**
- Schemdraw Documentation: https://schemdraw.readthedocs.io/
- NetworkX Documentation: https://networkx.org/documentation/
- Matplotlib Documentation: https://matplotlib.org/

**Publication Standards**
- Nature Figure Guidelines: https://www.nature.com/nature/for-authors/final-submission
- Science Figure Guidelines: https://www.science.org/content/page/instructions-preparing-initial-manuscript
- CONSORT Diagram: https://www.consort-spirit.org/

## Integration with Other Skills

This skill works synergistically with:

- **Scientific Writing** - Diagrams follow figure best practices
- **Scientific Visualization** - Shares color palettes and styling
- **LaTeX Posters** - Generate diagrams for poster presentations
- **Research Grants** - Methodology diagrams for proposals
- **Peer Review** - Evaluate diagram clarity and accessibility

## Quick Reference Checklist

Before submitting diagrams, run through the full checklist (visual quality, accessibility,
typography, publication standards, required quality verification, documentation/version control,
and final integration) in `references/submission_checklist.md`.

## Environment Setup

```bash
# Required
export OPENROUTER_API_KEY='your_api_key_here'

# Get key at: https://openrouter.ai/keys
```

## Getting Started

**Simplest possible usage:**
```bash
python scripts/generate_schematic.py "your diagram description" -o output.png
```

---

Use this skill to create clear, accessible, publication-quality diagrams that effectively communicate complex scientific concepts. The AI-powered workflow with iterative refinement ensures diagrams meet professional standards.


