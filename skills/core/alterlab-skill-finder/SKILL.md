---
name: alterlab-skill-finder
description: "The AlterLab front door and multi-agent launcher — routes a task to the right AlterLab skill(s) when the user invokes the suite without naming one, and for a multi-stage goal (or on the keyword 'alterflow', aliases 'alterresearch' / 'ultralab') it clarifies the goal with a few questions before anything runs, selects the skills the task needs, and runs a multi-agent workflow composing them (a packaged alterlab-workflows workflow, alterlab-research-pipeline, alterlab-ssci-orchestrator, or a bespoke plan via alterlab-workflow-orchestration). Triggers on 'use AlterLab skills', 'which AlterLab skill for X', 'is there an AlterLab skill for…', a multi-stage research goal, 'alterflow …', or any generic AlterLab request where the user does not know skill names. Use when someone references AlterLab generically, describes a multi-stage goal, or fires the alterflow keyword; when the user already names a specific skill, defer to that skill directly. Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read Grep Agent
compatibility: "No API key or network required. A routing + orchestration front-end: it reads the bundled skill index and hands off to the matching AlterLab skill(s). Multi-agent execution uses the host's subagent/Workflow tools where available (Claude Code, Cowork); on surfaces without them it decomposes the work into sequential phases."
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    last_updated: "2026-09-23"
    depends_on: "dispatches to any AlterLab skill; composes multi-step runs via alterlab-research-pipeline, alterlab-workflow-orchestration, and alterlab-ssci-orchestrator"
---

# AlterLab Skill Finder — Name the Task, Get the Right Skill (or the Whole Workflow)

**Skill type: ROUTER / LAUNCHER.** Users say *"use AlterLab skills"* or fire **`alterflow`** without
knowing the 230+ skill names. This is the front door: it reads the task, picks the AlterLab skill(s)
that fit, and either **uses one skill** or **launches a clarified, multi-agent workflow**.

## Core Mission

```
WHEN THE USER NAMES ALTERLAB BUT NOT A SKILL, YOU PICK THE SKILL(S).
SIMPLE TASK → ROUTE TO ONE SKILL.   BIG / KEYWORD TASK → CLARIFY, THEN ORCHESTRATE MANY.
ALWAYS ASK YOUR QUESTIONS BEFORE YOU START A MULTI-STEP RUN.
```

## Two modes

| Mode | Fires on | What happens |
|------|----------|--------------|
| **Route** (default) | "use AlterLab skills to…", "which AlterLab skill for…", any generic AlterLab ask | classify the task → map to a domain → name and **apply** the best-fitting skill(s) — Anthropic's **routing** pattern |
| **Orchestrate** | a task that **spans several dependent stages** (research → write → review, etc.); the keyword **`alterflow`** — aliases `alterresearch` / `ultralab` — is an explicit shortcut into this mode | **clarify → select skills → plan a multi-agent workflow → confirm → execute** — Anthropic's **orchestrator-workers** pattern |

## When to Use This Skill

- "Use AlterLab skills to [do X]." / "Which AlterLab skill should I use for [task]?"
- "Is there an AlterLab skill / workflow for [task]?"
- "**alterflow** — investigate [topic] and draft a paper." (→ Orchestrate mode)
- Any request that references AlterLab by name without specifying a skill.

### Does NOT Trigger

| The request is really about… | Route to | Why not this skill |
|---|---|---|
| A **specific named** skill ("run alterlab-deep-research", "use survey-analysis") | that skill directly | The user already knows it; no routing needed. |
| Composing a bespoke multi-agent workflow the user is hand-designing | `alterlab-workflow-orchestration` | This skill *calls* that engine; it doesn't replace its mechanics. |
| A task with no AlterLab framing at all | (answer normally) | Nothing to route. |

## Route mode — the method

1. **Classify the task** — what is the user doing (find literature? clean data? fit a model? write a
   section? query a database? design a study?).
2. **Map to a domain** (table below).
3. **Select the skill(s)** — name the best fit. For an exact niche name, consult
   `references/skill_index.md` (every AlterLab skill, grouped by domain, one-liner each) or match the
   installed AlterLab skill descriptions.
4. **Check it is installed.** The index lists all AlterLab skills, but the host can only run the ones
   installed there. In Claude Code a skill is available when it appears in the host's skill list as
   `alterlab-<domain>:<skill>`; a Skill call that returns *Unknown skill* means its plugin is not
   installed. Then stop and use the **not-installed reply** below — do not retry, and do not search
   for other tools.
5. **Apply it** — invoke the skill and do the work. Tell the user which skill you picked and why (one line).
6. **If the routing genuinely forks, ask ONE clarifying question** before committing.

### Not-installed reply

Name the skill and why it fits, then how to get it. Its plugin is `alterlab-` plus the domain id shown
in backticks in the index heading (for example `turkish-academia` → `alterlab-turkish-academia`):

- **Claude Code:** `/plugin install alterlab-<domain>@alterlab-academic-skills`, then `/reload-plugins`
  (or `alterlab-complete@alterlab-academic-skills` for every domain).
- **Claude app (claude.ai):** upload `skill-<skill-name>-<version>.zip` from the latest GitHub release
  (Customize ▸ Skills → Upload a skill).

If an installed skill covers part of the task, offer it as a stopgap and say what it will not cover;
otherwise wait for the user to install the plugin.

## Orchestrate mode — `alterflow` (clarify FIRST, then multi-agent)

Fires when the task **spans several dependent stages** (e.g. "investigate X *and* write it up",
"research → analyze → publish") — the `alterflow` keyword is just an explicit shortcut into this
mode, not the only way in; detect the multi-stage intent even when the user never types it. This is
Anthropic's **orchestrator-workers** pattern (a lead agent dynamically decomposes the task, delegates
to workers, and synthesizes) with a human-in-the-loop clarify/confirm gate in front. Do **not** start
executing — run this sequence:

1. **CLARIFY (mandatory, before any execution).** Ask 2–4 sharp scoping questions — e.g. the research
   question / deliverable, quantitative vs qualitative, the dataset or corpus, the target output
   (report, paper, model, figures), depth/time budget, and language. Do not guess when the answer
   changes the plan.
2. **SELECT.** From the answers, choose the AlterLab skills the job needs (use the domain map + the
   index). List them. **First ask whether it should be multi-agent at all:** if the work is tightly
   coupled, needs one shared context, or has little that runs in parallel (Anthropic's caution — most
   coding-like, dependency-heavy tasks), prefer a **sequential pipeline (prompt-chaining)** or a single
   Route-mode skill over a fan-out.
3. **PLAN.** Lay out the **dynamic multi-agent workflow** — the phases, which skill runs in each, where
   subagents fan out in parallel, and the **evaluator-optimizer** verification/critique step. **Scale
   the subagent count to complexity and default low** (Anthropic's rule of thumb: simple fact-finding
   ≈ 1 agent; a focused comparison ≈ 2–4; only genuinely broad work ≈ 10+). Reuse the existing
   orchestrators rather than reinventing them:
   - a packaged job — whole-manuscript citation audit, independent review panel, claim stress-test,
     PRISMA dual screening, response to reviewers, grant mock panel, literature map →
     **`alterlab-research-workflows`** (in Claude Code: `/alterlab-workflows:<name>`)
   - end-to-end research→publish → **`alterlab-research-pipeline`** (deep-research → paper-writer → paper-reviewer, revision loops)
   - a whole social-science study → **`alterlab-ssci-orchestrator`** (design → measurement/reflexivity → sampling → analysis module → inference)
   - a bespoke fan-out / judge-panel / adversarial-verify workflow → **`alterlab-workflow-orchestration`**
4. **CONFIRM — plan *and its rough cost*.** Show the selected skills + the phases in a few lines,
   **plus an effort estimate** (≈ how many phases / subagents). Multi-agent runs spend far more tokens
   than a single pass, so let the user opt in knowingly; get a go-ahead (or incorporate a correction).
5. **EXECUTE.** The user's go-ahead in step 4 is their opt-in to a multi-agent run. In Claude Code
   with dynamic workflows, launch a matching packaged workflow (`/alterlab-workflows:<name>`), or write
   a workflow script for a bespoke plan that fans out beyond a handful of workers; for a few workers,
   spawn subagents (the Agent tool). On surfaces without these tools, execute the phases sequentially and keep
   the same hand-offs. **Give every spawned subagent a complete task spec** — an objective, an
   output format, which skills/tools/sources to use, and clear boundaries — or workers duplicate work
   and leave gaps (`alterlab-workflow-orchestration` models these specs). Carry each stage's artifact
   to the next (the pipelines define the hand-off contracts).

The one rule: **questions before execution.** A short clarify step beats a wrong 20-agent run.

## Domain routing map (18 domains)

| If the task is about… | Domain | Representative skills |
|---|---|---|
| Find literature, fact-check, discover, manage references | **research-tools** / **core** | `alterlab-deep-research`, `alterlab-research-lookup`, `alterlab-pyzotero`, `alterlab-citation-verifier` |
| Write / draft / revise a paper, abstract, grant, poster; disclose AI use | **core** / **writing-tools** | `alterlab-paper-writer`, `alterlab-scientific-writing`, `alterlab-research-grants`, `alterlab-ai-use-disclosure` |
| Review / critique a manuscript | **core** | `alterlab-paper-reviewer` |
| Query a scientific database (PubMed, ChEMBL, UniProt, GEO, …) | **databases** | `alterlab-pubmed`, `alterlab-chembl`, `alterlab-uniprot`, … (39) |
| Genomics, proteomics, single-cell, structure prediction | **bioinformatics** | `alterlab-scanpy`, `alterlab-alphafold`, `alterlab-biopython`, … |
| Chemistry, drug discovery, docking, ADMET | **cheminformatics** | `alterlab-rdkit`, `alterlab-deepchem`, … |
| Clinical decision support, trials, medical imaging | **clinical-research** | `alterlab-clinicaltrials`, `alterlab-clinical-decision`, … |
| ML, statistics, data analysis, dataframes | **data-science** | `alterlab-scikit-learn`, `alterlab-statistical-analysis`, `alterlab-statsmodels`, `alterlab-pymc` |
| Plots, charts, figures, schematics | **visualization** | `alterlab-matplotlib`, `alterlab-scientific-viz`, `alterlab-infographics` |
| Lab platforms (Benchling, DNAnexus, Opentrons) | **lab-integrations** | `alterlab-benchling`, … |
| Quantum, geospatial, materials, astronomy, digital humanities | **domain-specific** | `alterlab-qiskit`, `alterlab-geopandas`, `alterlab-pymatgen`, … |
| Convert / handle documents, Markdown, notebooks, PDFs | **document-tools** | `alterlab-markitdown`, `alterlab-pdf-explore` |
| Finance, economics, market/financial data | **finance-economics** | `alterlab-fred`, `alterlab-edgartools`, … |
| Turkish academic system (YÖK, ÜAK, DergiPark, TÜBİTAK, BİDEB, doçentlik, KVKK) | **turkish-academia** | `alterlab-dergipark`, `alterlab-tubitak-proposal`, `alterlab-tubitak-bideb`, `alterlab-docentlik-eligibility`, `alterlab-kvkk-dmp`, … |
| Research ethics, IRB / ethics-committee applications, consent forms | **research-tools** (Türkiye: **turkish-academia**) | `alterlab-research-ethics`, `alterlab-tr-research-ethics` |
| Teaching, grant reporting, accreditation, recommendation letters, preprints | **faculty-life** | `alterlab-syllabus-ai-policy`, `alterlab-grant-reporting`, `alterlab-accreditation-aol`, … |
| Research-rigor gates (pre-registration, test choice, transparency) | **methodology** | `alterlab-test-selection-guard`, `alterlab-preregistration-discipline` |
| Design/run a whole **social-science study** (survey, qualitative, causal, multilevel, meta, missing data) | **social-science-workflow** | `alterlab-ssci-orchestrator` (+ 16 gates & modules) |
| Run a packaged **multi-agent job** — citation audit, review panel, PRISMA screening, rebuttal, grant mock panel, literature map, claim stress-test | **workflows** | `alterlab-research-workflows` (`/alterlab-workflows:<name>`) |

Full per-domain listing of every skill with a one-liner: `references/skill_index.md`.

## Output pattern

```
Task: <one-line restatement>
Mode: route | orchestrate
AlterLab skill(s): <name(s)> — <why this fits>
[orchestrate] Questions first: <2–4 scoping questions>   ← ask, then wait
[orchestrate] Plan: <phase 1 skill → phase 2 skills (fan-out) → verify → deliver>
→ on confirmation, execute.
```

## References

- `references/skill_index.md` — every AlterLab skill, grouped by domain, one-liner each (generated, kept in sync with the catalog).

Part of the AlterLab Academic Skills suite.
