---
name: alterlab-denario
description: Runs Denario (AstroPilot-AI), a multiagent AI system for scientific research assistance that automates end-to-end research workflows from a described dataset through idea, methodology, computational results, and a publication-ready LaTeX paper. Built on AG2 + LangGraph with a cmbagent analysis backend. Use when driving the Denario pipeline (Denario.get_idea/get_method/get_results/get_paper), generating research ideas from a dataset description, auto-developing methodology, executing analysis agents, or emitting a journal-formatted (APS/AAS/JHEP/ICML/NeurIPS/PASJ) LaTeX manuscript. Part of the AlterLab Academic Skills suite.
license: GPL-3.0
allowed-tools: Read WebFetch Bash(uv:*) Bash(python:*)
compatibility: Requires the denario Python package (Python 3.12+) and at least an OPENAI_API_KEY (required for the analysis/results module). GOOGLE_API_KEY (Gemini), ANTHROPIC_API_KEY (Claude), and PERPLEXITY_API_KEY (citation search) are optional. LaTeX is needed to compile the paper. Needs network access.
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# Denario

## Overview

Denario (by AstroPilot-AI) is a multiagent AI system designed to automate scientific research workflows from a described dataset through publication-ready manuscripts. It implements agents with AG2 and LangGraph, using [cmbagent](https://github.com/CMBAgents/cmbagent) as the research-analysis backend, to handle hypothesis generation, methodology development, computational analysis, and paper writing.

Source: https://github.com/AstroPilot-AI/Denario  |  Docs: https://denario.readthedocs.io  |  Paper: arXiv:2510.26887 (v1.0, Nov 2025).

## When to Use This Skill

Use this skill when:
- Analyzing datasets to generate novel research hypotheses
- Developing structured research methodologies
- Executing computational experiments and generating visualizations
- Conducting literature searches for research context
- Writing journal-formatted LaTeX papers from research results
- Automating the complete research pipeline from data to publication

## Installation

Install with uv (recommended). Quote the extra so zsh does not glob `[app]`:

```bash
uv init
uv add "denario[app]"
```

The `[app]` extra pulls in the Streamlit GUI (DenarioApp); omit it for headless/library use. For Docker deployment or building from source, see `references/installation.md`.

## LLM API Configuration

On init, `Denario` reads provider keys from the environment via its `KeyManager` (no config object). The relevant variables:

- `OPENAI_API_KEY` — **required** (the analysis/results module needs it; OpenAI models are the cmbagent-mode defaults).
- `GOOGLE_API_KEY` — optional, a **Gemini API key** (the default LLM for the faster `mode="fast"` path). Note this is a plain Gemini key, not a Vertex AI service-account JSON.
- `ANTHROPIC_API_KEY` — optional (Claude).
- `PERPLEXITY_API_KEY` — optional, only for citation search.

Set them in the shell or a `.env` (loaded with `python-dotenv` before importing `denario`). Google Vertex AI is also supported as a backend; see `references/llm_configuration.md` for that and `.env`/Docker details.

## Core Research Workflow

Denario follows a structured four-stage research pipeline:

### 1. Data Description

Define the research context by specifying available data and tools:

```python
from denario import Denario

den = Denario(project_dir="./my_research")
den.set_data_description("""
Available datasets: time-series data on X and Y
Tools: pandas, sklearn, matplotlib
Research domain: [specify domain]
""")
```

### 2. Idea Generation

Generate research hypotheses from the data description:

```python
den.get_idea()
```

This produces a research question or hypothesis based on the described data. `get_idea()` and `get_method()` take a `mode` argument: `mode="fast"` (default; LangGraph backend, faster but less reliable) or `mode="cmbagent"` (cmbagent backend, slower but more reliable). Alternatively, provide a custom idea:

```python
den.set_idea("Custom research hypothesis")
```

### 3. Methodology Development

Develop the research methodology:

```python
den.get_method()
```

This creates a structured approach for investigating the hypothesis. Can also accept markdown files with custom methodologies:

```python
den.set_method("path/to/methodology.md")
```

### 4. Results Generation

Execute computational experiments and generate analysis:

```python
den.get_results()
```

This runs the methodology, performs computations, creates visualizations, and produces findings. Can also provide pre-computed results:

```python
den.set_results("path/to/results.md")
```

### 5. Paper Generation

Create a publication-ready LaTeX paper:

```python
from denario import Journal

den.get_paper(journal=Journal.APS)
```

The generated paper includes proper formatting for the specified journal, integrated figures, and complete LaTeX source.

## Available Journals

`get_paper(journal=...)` defaults to `Journal.NONE` (plain LaTeX, unsrt bibliography). The `Journal` enum (`from denario import Journal`) supports:

- `Journal.NONE` — generic LaTeX, no journal preset
- `Journal.AAS` — American Astronomical Society (e.g. ApJ)
- `Journal.APS` — American Physical Society (Physical Review, PRL, PRA, ...)
- `Journal.ICML` — International Conference on Machine Learning
- `Journal.JHEP` — Journal of High Energy Physics (incl. JCAP)
- `Journal.NeurIPS` — Conference on Neural Information Processing Systems
- `Journal.PASJ` — Publications of the Astronomical Society of Japan

## Launching the GUI

Run the graphical user interface:

```bash
denario run
```

This launches a web-based interface for interactive research workflow management.

## Common Workflows

### End-to-End Research Pipeline

```python
from denario import Denario, Journal

# Initialize project
den = Denario(project_dir="./research_project")

# Define research context
den.set_data_description("""
Dataset: Time-series measurements of [phenomenon]
Available tools: pandas, sklearn, scipy
Research goal: Investigate [research question]
""")

# Generate research idea
den.get_idea()

# Develop methodology
den.get_method()

# Execute analysis
den.get_results()

# Create publication
den.get_paper(journal=Journal.APS)
```

### Hybrid Workflow (Custom + Automated)

```python
# Provide custom research idea
den.set_idea("Investigate the correlation between X and Y using time-series analysis")

# Auto-generate methodology
den.get_method()

# Auto-generate results
den.get_results()

# Generate paper
den.get_paper(journal=Journal.APS)
```

### Literature / Novelty Check

Use `den.check_idea(mode="semantic_scholar")` (or `mode="futurehouse"`) to test whether an idea is original against existing literature before committing to method/results. See `references/examples.md`.

## Detailed References

For comprehensive documentation:
- **Installation options**: `references/installation.md`
- **LLM configuration**: `references/llm_configuration.md`
- **Complete API reference**: `references/research_pipeline.md`
- **Example workflows**: `references/examples.md`

## Troubleshooting

Common issues and solutions:
- **API key errors**: Ensure environment variables are set correctly (see `references/llm_configuration.md`)
- **LaTeX compilation**: Install TeX distribution or use Docker image with pre-installed LaTeX
- **Package conflicts**: Use virtual environments or Docker for isolation
- **Python version**: Requires Python 3.12 or higher

