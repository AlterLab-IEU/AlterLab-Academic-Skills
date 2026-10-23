---
name: alterlab-hypogenic
description: Runs LLM-driven hypothesis generation and testing on labelled datasets with the HypoGeniC method — Claude generates, scores, and refines hypotheses in the conversation (keyless), or drives the HypoGeniC package with an LLM key. Combines literature insights with data-driven testing. Use when systematically exploring hypotheses about patterns in empirical data (for example deception detection or content analysis). For manual hypothesis formulation use alterlab-hypothesis-gen; for open-ended creative ideation use alterlab-scientific-brainstorm. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(uv:*) Bash(python:*) Bash(hypogenic_generation:*) Bash(hypogenic_inference:*) Bash(git clone:*)
compatibility: "No API key required: Claude runs the HypoGeniC loop itself in the conversation — propose keyword-rule hypotheses from a labelled training split, score them on a held-out split with the deterministic `scripts/score_hypotheses.py` (stdlib only), refine, and report accuracy. The `hypogenic` package driven by an LLM provider key (e.g. OPENAI_API_KEY) is an optional scaled-up alternative, installed in its own env via `uv pip install hypogenic`."
metadata:
    skill-author: AlterLab
    credentials: "optional: OPENAI_API_KEY (or another LLM provider / ANTHROPIC_API_KEY) — drives the hypogenic package's automated generation at scale; Claude runs the loop keyless in-conversation without it"
    version: "1.2.0"
    last_updated: "2026-09-23"
---

# Hypogenic

## Overview

Hypogenic provides automated hypothesis generation and testing using large language models to accelerate scientific discovery. The framework supports three approaches: HypoGeniC (data-driven hypothesis generation), HypoRefine (synergistic literature and data integration), and Union methods (mechanistic combination of literature and data-driven hypotheses).

## Keyless by default: Claude runs the HypoGeniC loop

**The large language model that HypoGeniC needs is Claude — so the whole loop runs in this
conversation with no package and no API key.** The deterministic scoring is a bundled
stdlib script; Claude does the generate/refine reasoning. This is the default path; the
`hypogenic` package (below) is an optional scaled-up alternative.

The loop (the HypoGeniC method, data-driven):

1. **Generate.** Claude reads the *labelled training split* and proposes candidate
   hypotheses, each written as a **checkable keyword rule** — e.g. "texts containing any of
   {furthermore, moreover, additionally, consequently} are AI-generated". Record them in a
   small JSON bank (`scripts/score_hypotheses.py --emit-template` prints the shape).
2. **Score.** Run the bundled, LLM-free scorer on a **held-out split**:
   ```bash
   python scripts/score_hypotheses.py \
     --data your_labelled_data.jsonl --hypotheses bank.json --split test
   ```
   It reports each hypothesis's held-out accuracy, the best single hypothesis, the
   first-match *bank* accuracy, and the examples the bank misclassifies. Pure stdlib, fully
   reproducible — no model call.
3. **Refine.** Claude reads the scores and the misclassified examples, drops or edits weak
   hypotheses, and adds new ones aimed at the errors; re-score. Repeat until held-out
   accuracy plateaus (HypoGeniC's iterative refinement, done keyless).
4. **Report.** Hand back the final hypothesis bank and its held-out accuracy, with the
   evidence (per-hypothesis and bank numbers from the scorer).

A worked example ships as a fixture: `evals/fixtures/ai_vs_human_texts.jsonl` (24 labelled
human-vs-AI texts, train/test split). On its test split the connector hypothesis scores
0.875 and a two-hypothesis bank reaches 1.000 — verified with the scorer, so the loop is
checkable end to end without any credential.

**For your own data**, give the scorer a `.jsonl`/`.csv` with `text`, `label`, and `split`
columns (or pass `--text-field`/`--label-field`/`--split-field`). When features are not
keyword-expressible, Claude can still apply each natural-language hypothesis to each
held-out example to emit a predicted label, then compute accuracy the same deterministic
way.

## Scaled-up option: the hypogenic package

The upstream `hypogenic` package automates the same loop against an LLM provider and adds
HypoRefine (literature) and Union methods. It needs its own environment and an LLM provider
API key, and is worth it mainly for large banks, HypoRefine's PDF/literature integration, or
heavy batch inference. Everything below documents that optional package.

## Quick Start (optional package)

Get started with the hypogenic package in minutes:

```bash
# Install into its own environment: hypogenic 0.3.5 pins numpy~=1.26, pandas~=2.1,
# torch~=2.4, transformers~=4.45, openai~=1.40 and anthropic~=0.32 (Python 3.10–3.12)
uv venv .venv-hypogenic --python 3.10 && source .venv-hypogenic/bin/activate
uv pip install hypogenic

# Clone example datasets
git clone https://github.com/ChicagoHAI/HypoGeniC-datasets.git ./data

# Run data-driven hypothesis generation (model_type: gpt | claude | vllm | huggingface)
hypogenic_generation --task_config_path ./data/your_task/config.yaml \
    --model_type gpt --model_name <provider-model-id> \
    --max_num_hypotheses 20 --output_folder ./outputs/your_task

# Run inference with a saved hypothesis bank
hypogenic_inference --task_config_path ./data/your_task/config.yaml \
    --hypothesis_file ./outputs/your_task/<hypotheses_*.json> \
    --model_type gpt --model_name <provider-model-id>
```

> Flags verified against the `hypogenic` 0.3.5 console scripts (`hypogenic_cmd`). The CLI
> covers data-driven HypoGeniC generation and inference; HypoRefine and Union runs are
> driven by the example scripts (below). Run `--help` for the full option list.

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

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Hand-formulating falsifiable hypotheses and predictions from observations (no LLM pipeline) | `alterlab-hypothesis-gen` |
| Open-ended ideation or research-gap brainstorming with no dataset yet | `alterlab-scientific-brainstorm` |
| Topic models, dictionaries, or supervised classifiers over text as social-science measurement | `alterlab-text-as-data` |
| Testing one pre-specified hypothesis with a conventional statistical test | `alterlab-statistical-analysis` |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-hypothesis-gen`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

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

Because of the pinned dependency versions above, keep hypogenic out of your main analysis
environment.

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

### scripts/

- `score_hypotheses.py` — the deterministic, LLM-free scorer for the keyless loop. Applies
  keyword-rule hypotheses to a labelled split and reports per-hypothesis and first-match
  bank accuracy plus the misclassified examples. `--emit-template` prints a hypotheses-JSON
  skeleton. Stdlib only.

### evals/fixtures/

- `ai_vs_human_texts.jsonl` — 24 labelled human-vs-AI texts (train/test split) for the
  worked keyless example; the connector hypothesis scores 0.875 and a two-hypothesis bank
  1.000 on its test split.

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

