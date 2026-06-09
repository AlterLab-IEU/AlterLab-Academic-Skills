---
name: research-pipeline
description: Orchestrate the end-to-end academic research-to-publication workflow (research, write, integrity check, review, revise, re-review, finalize) with mandatory integrity gates and two-stage peer review. Invokes the alterlab-research-pipeline orchestrator.
argument-hint: [topic, or path to existing draft to resume from]
disable-model-invocation: true
allowed-tools: Read Write Edit Bash WebFetch WebSearch
---

Start (or resume) the **academic research pipeline** for: $ARGUMENTS

Use the `alterlab-research-pipeline` skill as the orchestrator. It does not do the
substantive work itself — it detects the current stage, recommends a mode, dispatches
the specialist skills, enforces the quality gates, and tracks state.

Behavior:
1. **Detect entry point** — If $ARGUMENTS is a topic, start at stage 1 (research). If
   it is an existing draft, detect the furthest completed stage and resume from there.
2. **Run the 10 stages** — research → write → integrity check → review → revise →
   re-review → re-revise → final integrity check → finalize → process summary,
   dispatching `alterlab-deep-research`, `alterlab-paper-writer`, and
   `alterlab-paper-reviewer` as needed.
3. **Confirm at each checkpoint** — Pause for user confirmation before advancing
   between stages; do not auto-run the whole pipeline end to end.
4. **Enforce integrity gates** — Citation existence and claim faithfulness must pass
   before review submission (Stage 2.5) and again before finalize (Stage 4.5). Both
   gates run the `integrity_verification_agent`, which shells out to the
   `alterlab-citation-verifier` scripts for deterministic resolution.

Report the current stage, what was produced, and the next gate at every transition.
If no topic or draft was provided in $ARGUMENTS, ask which to start from.
