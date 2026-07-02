---
name: alterlab-hypogenic
description: Runs automated LLM-driven hypothesis generation and testing on tabular datasets with HypoGeniC, combining literature insights with data-driven testing. Use when systematically exploring hypotheses about patterns in empirical data (for example deception detection or content analysis). For manual hypothesis formulation use alterlab-hypothesis-gen; for open-ended creative ideation use alterlab-scientific-brainstorm. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(uv:*) Bash(python:*) Bash(hypogenic_generation:*) Bash(hypogenic_inference:*) Bash(git clone:*)
compatibility: Requires the hypogenic Python package plus an LLM provider API key (e.g. OPENAI_API_KEY) for hypothesis generation. Runs via `uv run python`.
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# Hypogenic

## Overview

Hypogenic provides automated hypothesis generation and testing using large language models to accelerate scientific discovery. The framework supports three approaches: HypoGeniC (data-driven hypothesis generation), HypoRefine (synergistic literature and data integration), and Union methods (mechanistic combination of literature and data-driven hypotheses).

## Quick Start

Get started with Hypogenic in minutes:

```bash
# Install the package
uv pip install hypogenic

# Clone example datasets
git clone https://github.com/ChicagoHAI/HypoGeniC-datasets.git ./data

# Run basic hypothesis generation
hypogenic_generation --config ./data/your_task/config.yaml --method hypogenic --num_hypotheses 20

# Run inference on generated hypotheses
hypogenic_inference --config ./data/your_task/config.yaml --hypotheses output/hypotheses.json
```

> Flag names below are illustrative. The upstream docs expose exact arguments only via
> `hypogenic_generation --help` / `hypogenic_inference --help` — confirm there before scripting.

**Or use the example scripts** (the library ships runnable scripts under `examples/`; there is no one-line fluent `task.generate_hypotheses(...)` API — see "Python API Usage" below for the real classes):

```bash
python ./examples/generation.py   --help   # HypoGeniC data-driven generation
python ./examples/inference.py     --help   # single-hypothesis inference
```

## When to Use This Skill

Use this skill when working on:
- Generating scientific hypotheses from observational datasets
- Testing multiple competing hypotheses systematically
- Combining literature insights with empirical patterns
- Accelerating research discovery through automated hypothesis ideation
- Domains requiring hypothesis-driven analysis: deception detection, AI-generated content identification, mental health indicators, predictive modeling, or other empirical research

## Key Features

**Automated Hypothesis Generation**
- Generate 10-20+ testable hypotheses from data in minutes
- Iterative refinement based on validation performance
- Support for both API-based (OpenAI, Anthropic) and local LLMs

**Literature Integration**
- Extract insights from research papers via PDF processing
- Combine theoretical foundations with empirical patterns
- Systematic literature-to-hypothesis pipeline with GROBID

**Performance Optimization**
- Redis caching reduces API costs for repeated experiments
- Parallel processing for large-scale hypothesis testing
- Adaptive refinement focuses on challenging examples

**Flexible Configuration**
- Template-based prompt engineering with variable injection
- Custom label extraction for domain-specific tasks
- Modular architecture for easy extension

**Reported Results** (from arXiv:2410.17309, *Literature Meets Data*)
- +8.97% over few-shot, +15.75% over literature-only, +3.37% over data-driven-only baselines
- Human accuracy improved +7.44% (deception detection) and +14.19% (AI-generated content detection)
- A redundancy checker prunes near-duplicate hypotheses to keep the final bank diverse

## Core Capabilities

### 1. HypoGeniC: Data-Driven Hypothesis Generation

Generate hypotheses solely from observational data through iterative refinement.

**Process:**
1. Initialize with a small data subset to generate candidate hypotheses
2. Iteratively refine hypotheses based on performance
3. Replace poorly-performing hypotheses with new ones from challenging examples

**Best for:** Exploratory research without existing literature, pattern discovery in novel datasets

### 2. HypoRefine: Literature and Data Integration

Synergistically combine existing literature with empirical data through an agentic framework.

**Process:**
1. Extract insights from relevant research papers (typically 10 papers)
2. Generate theory-grounded hypotheses from literature
3. Generate data-driven hypotheses from observational patterns
4. Refine both hypothesis banks through iterative improvement

**Best for:** Research with established theoretical foundations, validating or extending existing theories

### 3. Union Methods

Mechanistically combine literature-only hypotheses with framework outputs.

**Variants:**
- **Literature ∪ HypoGeniC**: Combines literature hypotheses with data-driven generation
- **Literature ∪ HypoRefine**: Combines literature hypotheses with integrated approach

**Best for:** Comprehensive hypothesis coverage, eliminating redundancy while maintaining diverse perspectives

## Installation

Install via pip:
```bash
uv pip install hypogenic
```

**Optional dependencies:**
- **Redis server** (port 6832): Enables caching of LLM responses to significantly reduce API costs during iterative hypothesis generation
- **s2orc-doc2json**: Required for processing literature PDFs in HypoRefine workflows
- **GROBID**: Required for PDF preprocessing (see Literature Processing section)

**Clone example datasets:**
```bash
# For HypoGeniC examples
git clone https://github.com/ChicagoHAI/HypoGeniC-datasets.git ./data

# For HypoRefine/Union examples
git clone https://github.com/ChicagoHAI/Hypothesis-agent-datasets.git ./data
```

## Dataset Format

Datasets must follow HuggingFace datasets format with specific naming conventions:

**Required files:**
- `<TASK>_train.json`: Training data
- `<TASK>_val.json`: Validation data  
- `<TASK>_test.json`: Test data

**Required keys in JSON:**
- `text_features_1` through `text_features_n`: Lists of strings containing feature values
- `label`: List of strings containing ground truth labels

**Example (headline click prediction):**
```json
{
  "headline_1": [
    "What Up, Comet? You Just Got *PROBED*",
    "Scientists Made a Breakthrough in Quantum Computing"
  ],
  "headline_2": [
    "Scientists Everywhere Were Holding Their Breath Today. Here's Why.",
    "New Quantum Computer Achieves Milestone"
  ],
  "label": [
    "Headline 2 has more clicks than Headline 1",
    "Headline 1 has more clicks than Headline 2"
  ]
}
```

**Important notes:**
- All lists must have the same length
- Label format must match your `extract_label()` function output format
- Feature keys can be customized to match your domain (e.g., `review_text`, `post_content`, etc.)

## Configuration

Each task requires a `config.yaml` file specifying:

**Required elements:**
- Dataset paths (train/val/test)
- Prompt templates for:
  - Observations generation
  - Batched hypothesis generation
  - Hypothesis inference
  - Relevance checking
  - Adaptive methods (for HypoRefine)

**Template capabilities:**
- Dataset placeholders for dynamic variable injection (e.g., `${text_features_1}`, `${num_hypotheses}`)
- Custom label extraction functions for domain-specific parsing
- Role-based prompt structure (system, user, assistant roles)

**Configuration structure:**
```yaml
task_name: your_task_name

train_data_path: ./your_task_train.json
val_data_path: ./your_task_val.json
test_data_path: ./your_task_test.json

prompt_templates:
  # Extra keys for reusable prompt components
  observations: |
    Feature 1: ${text_features_1}
    Feature 2: ${text_features_2}
    Observation: ${label}
  
  # Required templates
  batched_generation:
    system: "Your system prompt here"
    user: "Your user prompt with ${num_hypotheses} placeholder"
  
  inference:
    system: "Your inference system prompt"
    user: "Your inference user prompt"
  
  # Optional templates for advanced features
  few_shot_baseline: {...}
  is_relevant: {...}
  adaptive_inference: {...}
  adaptive_selection: {...}
```

Refer to `references/config_template.yaml` for a complete example configuration.

## Literature Processing (HypoRefine/Union Methods)

To use literature-based hypothesis generation, you must preprocess PDF papers:

**Step 1: Setup GROBID** (first time only)
```bash
bash ./modules/setup_grobid.sh
```

**Step 2: Add PDF files**
Place research papers in `literature/YOUR_TASK_NAME/raw/`

**Step 3: Process PDFs**
```bash
# Start GROBID service
bash ./modules/run_grobid.sh

# Process PDFs for your task
cd examples
python pdf_preprocess.py --task_name YOUR_TASK_NAME
```

This converts PDFs to structured format for hypothesis extraction. Automated literature search will be supported in future releases.

## CLI Usage

### Hypothesis Generation

```bash
hypogenic_generation --help
```

**Key parameters:**
- Task configuration file path
- Model selection (API-based or local)
- Generation method (HypoGeniC, HypoRefine, or Union)
- Number of hypotheses to generate
- Output directory for hypothesis banks

### Hypothesis Inference

```bash
hypogenic_inference --help
```

**Key parameters:**
- Task configuration file path
- Hypothesis bank file path
- Test dataset path
- Inference method (default or multi-hypothesis)
- Output file for results

## Python API Usage

The library is **not** a one-call fluent API — generation runs as an explicit init/update
loop over the algorithm classes (`DefaultGeneration`, `DefaultInference`, `DefaultUpdate`,
`DefaultReplace`), and inference runs through the `inference_register`. Copy and adapt the
scripts under `examples/`; for HypoRefine/Union adapt `examples/union_generation.py`.

Full import list, the generation/inference loop, `inference_type` strategy options, and the
critical `extract_label()` parsing contract: see `references/python_api.md`.

## Workflow Examples

Three end-to-end scenarios — data-driven (HypoGeniC, AI-content detection), literature-informed
(HypoRefine, deception in hotel reviews), and comprehensive coverage (Union, mental-stress
detection) — with dataset prep, generation, and inference commands for each: see
`references/workflow_examples.md`.

## Performance Optimization

**Caching:** Enable Redis caching to reduce API costs and computation time for repeated LLM calls

**Parallel Processing:** Leverage multiple workers for large-scale hypothesis generation and testing

**Adaptive Refinement:** Use challenging examples to iteratively improve hypothesis quality

## Troubleshooting

**Issue:** Generated hypotheses are too generic
**Solution:** Refine prompt templates in `config.yaml` to request more specific, testable hypotheses

**Issue:** Poor inference performance
**Solution:** Ensure dataset has sufficient training examples, adjust hypothesis generation parameters, or increase number of hypotheses

**Issue:** Label extraction failures
**Solution:** Implement custom `extract_label()` function for domain-specific output parsing

**Issue:** GROBID PDF processing fails
**Solution:** Ensure GROBID service is running (`bash ./modules/run_grobid.sh`) and PDFs are valid research papers

## Creating Custom Tasks

Adding a new task follows five steps: (1) prepare `train/val/test` JSON with
`text_features_*` + `label` keys, (2) author `config.yaml`, (3) implement a custom
`extract_label()`, (4) optionally process literature PDFs for HypoRefine/Union, and
(5) run generation + inference.

Full step-by-step guide with the custom `extract_label` implementation and BaseTask wiring:
see `references/custom_tasks.md`.

## Repository Structure

Core code lives in `hypogenic/`, CLI entry points in `hypogenic_cmd/`, the HypoRefine agent in
`hypothesis_agent/`, PDF/literature tools in `literature/` + `modules/`, and runnable scripts in
`examples/`. Full annotated directory tree: see `references/repository_structure.md`.

## Related Publications

The framework rests on three papers from ChicagoHAI: **HypoBench** (2025, arXiv:2504.11524),
**Literature Meets Data** (2024, arXiv:2410.17309, introduces HypoRefine), and the original
**Hypothesis Generation with Large Language Models** (2024, EMNLP NLP4Science). Full citations,
descriptions, and BibTeX entries: see `references/publications.md`.

## Additional Resources

### Official Links

- **GitHub Repository:** https://github.com/ChicagoHAI/hypothesis-generation
- **PyPI Package:** https://pypi.org/project/hypogenic/
- **License:** MIT License
- **Issues & Support:** https://github.com/ChicagoHAI/hypothesis-generation/issues

### Example Datasets

Clone these repositories for ready-to-use examples:

```bash
# HypoGeniC examples (data-driven only)
git clone https://github.com/ChicagoHAI/HypoGeniC-datasets.git ./data

# HypoRefine/Union examples (literature + data)
git clone https://github.com/ChicagoHAI/Hypothesis-agent-datasets.git ./data
```

For contributions or questions, visit the GitHub repository and check the issues page.

## Local Resources

### references/

- `config_template.yaml` — a runnable-shape `config.yaml` matching the real `hypogenic`
  schema (`task_name`, `train/val/test_data_path`, `prompt_templates` with role-based
  system/user sub-keys and `${...}` placeholders). Read it before authoring a config:
  it documents the `${...}` substitution, the reusable "extra key" mechanism, and which
  settings belong in CLI flags rather than the YAML.
- `python_api.md` — the init/update generation loop, inference registry, `inference_type`
  strategy options, and the `extract_label()` parsing contract.
- `workflow_examples.md` — three end-to-end scenarios (HypoGeniC, HypoRefine, Union).
- `custom_tasks.md` — five-step guide for adding a new task or dataset.
- `repository_structure.md` — annotated layout of the upstream repository.
- `publications.md` — full citations and BibTeX for the HypoGeniC/HypoRefine/HypoBench papers.

Part of the AlterLab Academic Skills suite.

