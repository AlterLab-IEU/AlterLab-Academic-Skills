---
name: alterlab-denario
description: Runs a Denario-style end-to-end research pipeline from a described dataset with no API key — Claude itself plays every agent (idea maker and idea critic, methodologist, analyst who writes and runs the analysis code locally, paper writer) and produces idea.md, methods.md, results with figures and a journal-formatted LaTeX paper (APS revtex or plain LaTeX; AAS/JHEP/ICML/NeurIPS/PASJ with the venue's style file). The optional denario package (AstroPilot-AI; AG2 + LangGraph + cmbagent) runs the same stages with its own LLM keys. Use when automating research from a dataset description to a paper, generating hypotheses from a dataset, developing methodology, executing analysis, turning methods and results into a journal manuscript, or driving Denario (get_idea/get_method/get_results/get_paper). Part of the AlterLab Academic Skills suite.
license: GPL-3.0
allowed-tools: Read Write Edit WebFetch WebSearch Bash(uv:*) Bash(python:*) Bash(pdflatex:*) Bash(xelatex:*) Bash(bibtex:*)
compatibility: No API key required. Claude carries out every stage and runs the analysis with local Python (`uv run --python ">=3.12" --with pandas ...`); pdflatex compiles the paper (scripts/research_project.py scaffolds and compiles it). The optional denario package (1.0.x, Python 3.12-3.13) runs the stages with its own LLM keys.
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    credentials: "optional: OPENAI_API_KEY (lets the denario package run its own agents; its analysis/results module requires it), GOOGLE_API_KEY (Gemini models in the package, the default for its fast mode, check_idea and get_paper), ANTHROPIC_API_KEY (Claude models inside the package), PERPLEXITY_API_KEY (the package's citation search), SEMANTIC_SCHOLAR_KEY (faster check_idea lookups)"
    last_updated: "2026-09-23"
---

# Denario

## Overview

This skill runs the Denario research pipeline (data description, idea, methods, analysis,
paper) with Claude doing every agent role, so it needs no API key and no extra LLM service. The
denario package by AstroPilot-AI automates the same stages with its own multiagent system (AG2
and LangGraph, with [cmbagent](https://github.com/CMBAgents/cmbagent) as the analysis backend);
use it when the user asks for the package and has its LLM keys ("Optional: the denario
package" below).

Source: https://github.com/AstroPilot-AI/Denario  |  Docs: https://denario.readthedocs.io  |  Paper: arXiv:2510.26887 (v1.0, Nov 2025).

## When to Use This Skill

Use this skill when:
- Analyzing datasets to generate novel research hypotheses
- Developing structured research methodologies
- Executing computational experiments and generating visualizations
- Conducting literature searches for research context
- Writing journal-formatted LaTeX papers from research results
- Automating the complete research pipeline from data to publication

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| A cited literature review or fact-check with no dataset to analyze | `alterlab-deep-research` |
| Coordinating research → writing → review → revision for your own manuscript | `alterlab-research-pipeline` |
| Drafting or revising a paper you are writing yourself (IMRaD, bilingual abstract) | `alterlab-paper-writer` |
| LLM-driven hypothesis generation and testing on a tabular dataset (HypoGeniC) | `alterlab-hypogenic` |
| Consulting-style market or industry report | `alterlab-market-research` |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-deep-research`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

Denario output is AI-generated end to end: treat its ideas, code, results, and citations as drafts that a researcher must verify, and disclose the AI assistance in any resulting manuscript.

## Keyless pipeline (default): Claude runs the agents

Work in the package's project layout, so the project can later be handed to `Denario(project_dir=...)`
unchanged. `scripts/research_project.py` creates it and compiles the paper:

```bash
python scripts/research_project.py init ./my_research --journal aps --data-description notes.md
python scripts/research_project.py status ./my_research     # which stage files are still TODO
python scripts/research_project.py compile ./my_research    # pdflatex -> paper/paper.pdf
```

| Denario stage | What you do instead | Output |
|---------------|---------------------|--------|
| `set_data_description()` | Record the data, units, sample sizes, file paths, tools, and hypotheses already considered | `input_files/data_description.md` |
| `get_idea()` (idea maker + idea hater) | Propose 3-5 hypotheses that the described variables can test; critique each as the "idea hater" (novelty, feasibility with this data, confounds, what result would refute it); revise once; pick one and keep the rejected ones with reasons | `input_files/idea.md` |
| `set_idea()` | Use the user's own hypothesis verbatim and skip generation | `input_files/idea.md` |
| `check_idea()` | Novelty check with WebSearch and keyless OpenAlex/arXiv queries; list the closest prior work with DOIs | `idea.md`, Literature section |
| `get_method()` / `set_method()` | Data preparation, model, tests, robustness checks, and the result that would falsify the idea | `input_files/methods.md` |
| `get_results()` / `set_results()` | Write the analysis in `analysis/`, run it (`uv run --python ">=3.12" --with pandas --with statsmodels --with matplotlib python analysis/run.py`), save figures to `input_files/plots/`, and write the results from the actual output | `input_files/results.md`, `plots/` |
| `get_paper(journal=...)` | Fill `paper/paper.tex` from the four files, cite only sources you retrieved, keep the AI-assistance section, and compile | `paper/paper.pdf` |

Rules: each stage reads the previous file. Numbers in results.md and the paper come only from
code you ran. When only a description exists and no data, stop after methods and say the
results need the data. APS (`revtex4-2`) and plain LaTeX compile with a standard TeX Live; for AAS,
JHEP, ICML, NeurIPS or PASJ, place the venue's class or style file next to `paper.tex` (the scaffold
starts those as plain `article` and says so).

## Optional: the denario package (needs LLM keys)

### Installation

No install step with uv (pin Python 3.12-3.13), or add it to a project. Quote the extra so zsh
does not glob `[app]`:

```bash
uv run --python ">=3.12,<3.14" --with "denario>=1.0" python run_denario.py
uv init && uv add "denario[app]"   # project install, with the Streamlit GUI
```

The `[app]` extra pulls in the Streamlit GUI (DenarioApp); omit it for headless/library use. For Docker deployment or building from source, see `references/installation.md`.

### LLM API Configuration

On init, `Denario` reads provider keys from the environment via its `KeyManager` (no config object). The relevant variables:

- `OPENAI_API_KEY` — **required** (the analysis/results module needs it; OpenAI models are the cmbagent-mode defaults).
- `GOOGLE_API_KEY` — optional, a **Gemini API key**, needed whenever a Gemini model is selected (the `mode="fast"`, `check_idea`, and `get_paper` defaults are Gemini). Note this is a plain Gemini key, not a Vertex AI service-account JSON.
- `ANTHROPIC_API_KEY` — optional (Claude).
- `PERPLEXITY_API_KEY` — optional, only for citation search.

Set them in the shell or a `.env` in the working directory (`KeyManager` calls `load_dotenv()` itself). Google Vertex AI is also supported as a backend; see `references/llm_configuration.md` for that and `.env`/Docker details.

#### Model IDs: pass current ones explicitly

denario 1.0.1 (the current release; the GitHub master is unchanged as of 2026-09) hard-codes defaults that providers have since retired, so choose models per call instead of relying on them:

- `mode="fast"` (`get_idea`/`get_method`) defaults to `gemini-2.0-flash`, which Google shut down on 2026-06-01 — the default path now fails. Pass `llm=` explicitly.
- The cmbagent defaults (`mode="cmbagent"` and `get_results`) use `o3-mini` (OpenAI shutdown scheduled for 2026-10-23) alongside `gpt-4o` and `gpt-4.1`; override every `o3-mini` role: `idea_hater_model`, `plan_reviewer_model`, `formatter_model`, and (in `get_results`) `researcher_model`.
- The registry entry `"gpt-4.5"` (gpt-4.5-preview) was retired on 2025-07-14; do not select it.

String model names must be keys of `denario.models` (e.g. `"gpt-4.1"`, `"gpt-5"`, `"gpt-5-mini"`, `"gemini-2.5-flash"`, `"gemini-2.5-pro"`); for any other provider model ID, pass an `LLM` object — routing is by substring (`gemini` → Google, `gpt`/`o3` → OpenAI, `claude` → Anthropic):

```python
from denario import Denario, LLM

den = Denario(project_dir="./my_research")
den.get_idea(mode="fast", llm="gpt-4.1")  # a registry key the provider still serves
den.get_method(mode="fast", llm=LLM(name="gemini-3.6-flash", max_output_tokens=8192, temperature=0.7))
```

`gemini-3.6-flash` is Google's listed replacement for `gemini-2.0-flash`; Google now limits the Gemini 2.5 models to existing users, so new Google accounts should use the `LLM` object route. Check the provider model lists before a long run — IDs keep rotating. See `references/llm_configuration.md` for per-stage parameters.

### Core Research Workflow (package API)

The package runs the same stages as API calls:

#### 1. Data Description

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

#### 2. Idea Generation

Generate research hypotheses from the data description:

```python
den.get_idea(llm="gpt-4.1")  # pass a live model; the built-in fast-mode default is retired
```

This produces a research question or hypothesis based on the described data. `get_idea()` and `get_method()` take a `mode` argument: `mode="fast"` (default; LangGraph backend, faster but less reliable) or `mode="cmbagent"` (cmbagent backend, slower but more reliable). Alternatively, provide a custom idea:

```python
den.set_idea("Custom research hypothesis")
```

#### 3. Methodology Development

Develop the research methodology:

```python
den.get_method(llm="gpt-4.1")
```

This creates a structured approach for investigating the hypothesis. Can also accept markdown files with custom methodologies:

```python
den.set_method("path/to/methodology.md")
```

#### 4. Results Generation

Execute computational experiments and generate analysis:

```python
den.get_results(researcher_model="gpt-4.1", plan_reviewer_model="gpt-4.1", formatter_model="gpt-4.1")
```

This runs the methodology, performs computations, creates visualizations, and produces findings. Can also provide pre-computed results:

```python
den.set_results("path/to/results.md")
```

#### 5. Paper Generation

Create a publication-ready LaTeX paper:

```python
from denario import Journal

den.get_paper(journal=Journal.APS)
```

The generated paper includes proper formatting for the specified journal, integrated figures, and complete LaTeX source.

## Available Journals

In the keyless pipeline `research_project.py init --journal aps` (revtex4-2) and `--journal none` compile with a standard TeX Live; the other venues need their own class or style file.

`get_paper(journal=...)` defaults to `Journal.NONE` (plain LaTeX, unsrt bibliography). The `Journal` enum (`from denario import Journal`) supports:

- `Journal.NONE` — generic LaTeX, no journal preset
- `Journal.AAS` — American Astronomical Society (e.g. ApJ)
- `Journal.APS` — American Physical Society (Physical Review, PRL, PRA, ...)
- `Journal.ICML` — International Conference on Machine Learning
- `Journal.JHEP` — Journal of High Energy Physics (incl. JCAP)
- `Journal.NeurIPS` — Conference on Neural Information Processing Systems
- `Journal.PASJ` — Publications of the Astronomical Society of Japan

### Launching the GUI (package)

Run the graphical user interface:

```bash
denario run
```

This launches a web-based interface for interactive research workflow management.

### Common Workflows (package)

#### End-to-End Research Pipeline

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

# Generate research idea and methodology (explicit models; see "Model IDs" above)
den.get_idea(llm="gpt-4.1")
den.get_method(llm="gpt-4.1")

# Execute analysis (cmbagent agents); replace the o3-mini defaults before OpenAI retires them
den.get_results(researcher_model="gpt-4.1", plan_reviewer_model="gpt-4.1", formatter_model="gpt-4.1")

# Create publication (default writer LLM is gemini-2.5-flash; pass llm= to change it)
den.get_paper(journal=Journal.APS)
```

#### Hybrid Workflow (Custom + Automated)

```python
# Provide custom research idea
den.set_idea("Investigate the correlation between X and Y using time-series analysis")

# Auto-generate methodology
den.get_method(llm="gpt-4.1")

# Auto-generate results
den.get_results(researcher_model="gpt-4.1", plan_reviewer_model="gpt-4.1", formatter_model="gpt-4.1")

# Generate paper
den.get_paper(journal=Journal.APS)
```

#### Literature / Novelty Check

Use `den.check_idea(mode="semantic_scholar")` (or `mode="futurehouse"`) to test whether an idea is original against existing literature before committing to method/results. See `references/examples.md`.

## Detailed References

For comprehensive documentation:
- **Installation options**: `references/installation.md`
- **LLM configuration**: `references/llm_configuration.md`
- **Complete API reference**: `references/research_pipeline.md`
- **Example workflows**: `references/examples.md`

## Troubleshooting

Common issues and solutions:
- **API key errors** (package only): Ensure environment variables are set correctly (see `references/llm_configuration.md`)
- **LaTeX compilation**: Install TeX distribution or use Docker image with pre-installed LaTeX
- **Package conflicts**: Use virtual environments or Docker for isolation
- **Python version**: denario 1.0.x requires Python 3.12 or 3.13 (`>=3.12,<3.14`)
- **`KeyError: LLM '...' not available`**: the string is not a `denario.models` key; pass an `LLM(...)` object instead
- **Model not found / deprecated errors from the provider**: a retired default is in use; pass a current model (see "Model IDs" above)

Part of the AlterLab Academic Skills suite.
