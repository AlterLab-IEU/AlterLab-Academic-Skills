---
name: alterlab-ssci-orchestrator
description: "Coordinates a social-science study through the stage-gated methods pipeline — question then design-gate then measurement-gate then sampling-gate then the right analysis module then inference-gate then reporting — holding a single YAML Design Passport that each gate reads and appends, and enforcing gate order with PASS / WARN / BLOCK semantics (design-gate and inference-gate are fail-closed). It is thin: it routes and holds the artifact, it does not run analysis itself. Use when a researcher describes a whole social-science study end to end, asks to run the methods pipeline or a full methodology review, or wants the design-to-inference workflow coordinated rather than a single step. For a single stage trigger that gate directly (alterlab-ssci-design-gate, -measurement-gate, -sampling-gate, -inference-gate); for multi-agent execution mechanics see alterlab-workflow-orchestration. Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read Bash(python:*)
compatibility: No API key required. A thin discipline-enforcing pipeline coordinator; it dispatches to sibling gate/analysis skills that run locally. Extends the composition patterns of alterlab-workflow-orchestration.
metadata:
    skill-author: AlterLab
    version: "1.0.0"
    depends_on: "alterlab-ssci-design-gate, alterlab-ssci-measurement-gate, alterlab-ssci-sampling-gate, alterlab-ssci-inference-gate; dispatches to alterlab-causal-inference, alterlab-sem-psychometrics, alterlab-qca, alterlab-sna, alterlab-abm-mesa, alterlab-text-as-data; extends alterlab-workflow-orchestration"
---

# SSci Orchestrator — Route the Study, Hold the Passport, Enforce the Gates

**Skill type: DISCIPLINE-ENFORCING (thin coordinator).** This is the conductor of the
social-science methods spine. It does **no analysis**. It walks a study through the gates in
order, carries a single **Design Passport** between them, and refuses to let a stage run before
its prerequisite gate has passed. For the actual routing/refusal logic, each gate owns its own
skill; this skill owns *sequence* and *hand-off*.

## The Core Rule

```
NO STAGE RUNS BEFORE ITS GATE PASSES. THE PASSPORT IS THE SINGLE SOURCE OF TRUTH.
```

A methods pipeline fails when stages run out of order — sampling sized before the design is
fixed, a causal estimator run before the identifying assumption is pinned, a discussion written
before the claim is audited. The orchestrator makes the order non-optional and makes every gate's
verdict visible in one artifact.

## When to Use This Skill

- "Walk me through designing and analyzing this whole study."
- "Run the methods pipeline / a full methodology review on my project."
- "I have a research question, some data, and a survey — take it from design to inference."
- The user's ask spans **more than one** gate/module and needs coordination.

### Does NOT Trigger

| The request is really about… | Route to | Why not this skill |
|---|---|---|
| A single stage (design, measurement, sampling, or claim audit) | the matching `alterlab-ssci-*-gate` | Trigger the gate directly; no orchestration needed. |
| Running one analysis method (DiD, CFA, QCA, SNA, ABM, text) | the matching analysis module | The module does it; the orchestrator only dispatches. |
| Multi-agent execution mechanics (fan-out, judge panels) | `alterlab-workflow-orchestration` | General composition engine; this skill is the social-science-specific spine on top of it. |
| A non-methods task (writing prose, literature search) | `alterlab-paper-writer` / `alterlab-deep-research` | Outside the methods pipeline. |

## The Pipeline

```
research question
  └─> [design-gate]  ── pins design_type + identifying_assumption ──▶ (MANDATORY: BLOCK-capable)
        └─> [measurement-gate]  ── reliability + validity + invariance ──▶ (WARN default)
              └─> [sampling-gate]  ── frame + method + size logic ──▶ (WARN default)
                    └─> [ANALYSIS MODULE]  ── dispatched by design_type (see routing table) ──▶
                          └─> [inference-gate]  ── audits claims vs design/sample ──▶ (MANDATORY: BLOCK-capable)
                                └─> reporting
```

**Analysis-module routing** (by `design_type` + data in the Passport):

| If the design / data is… | Dispatch to |
|---|---|
| Quasi-experimental / observational causal (DiD, IV, RDD, panel FE) | `alterlab-causal-inference` |
| Latent constructs, CFA / SEM / IRT / invariance | `alterlab-sem-psychometrics` |
| Small-N configurational, set-theoretic (fsQCA/csQCA) | `alterlab-qca` |
| Relational / network data | `alterlab-sna` |
| Simulation of interacting agents | `alterlab-abm-mesa` |
| Corpora / open-ended text | `alterlab-text-as-data` |
| Interpretive / theory-building | `alterlab-qualitative-methods` (existing) |
| Combined strands | `alterlab-mixed-methods` (existing) |

Full stage contract, PASS/WARN/BLOCK rules, and the analysis-module decision logic:
`references/pipeline_contract.md`. A stdlib validator that reads a Design Passport and reports
the next gate and whether it is fail-closed: `scripts/passport.py`.

## The Design Passport

One YAML artifact, created at entry and appended by each gate. The orchestrator never overwrites a
prior gate's fields; it only advances the `stage` and dispatches the next gate.

```yaml
research_question: <text>
stage: <design | measurement | sampling | analysis | inference | done>
design_type: <set by design-gate>
identifying_assumption: <set by design-gate>
claim_type: <causal | associational | descriptive>
constructs: [<appended by measurement-gate>]
sampling: {<appended by sampling-gate>}
analysis_module: <chosen by the orchestrator from design_type>
claims: [<audited by inference-gate>]
gate_log: [{gate: design, verdict: PASS|WARN|BLOCK, note: ...}, ...]
```

## Gate verdict semantics

- **PASS** — the gate's discipline is satisfied; advance.
- **WARN** — an advisory issue; advance **with the caveat recorded** in `gate_log` and surfaced in
  the final report (default for measurement/sampling when non-fatal).
- **BLOCK** — fail-closed; the pipeline **cannot advance** until resolved. Design-gate BLOCKs when no
  design/assumption can be named; inference-gate BLOCKs when a claim exceeds the design/sample.

## Self-Check Before Advancing a Stage

- Has the current stage's gate emitted a verdict recorded in `gate_log`?
- If the verdict is BLOCK, has it been resolved (not bypassed) before advancing?
- Is the analysis module chosen from `design_type`, not from the user's tool preference?
- Does the Passport still carry every upstream field (nothing overwritten)?

## References

- `references/pipeline_contract.md` — stage-by-stage contract, verdict rules, analysis-module routing logic, worked run.
- `scripts/passport.py` — stdlib Design Passport validator / next-gate reporter.

Part of the AlterLab Academic Skills suite.
