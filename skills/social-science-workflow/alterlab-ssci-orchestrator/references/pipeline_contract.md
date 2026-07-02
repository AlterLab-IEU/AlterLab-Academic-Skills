# Pipeline Contract — Stages, Verdicts, and Analysis-Module Routing

Loaded on demand from the orchestrator SKILL.md. Defines the stage contract the orchestrator
enforces, the PASS/WARN/BLOCK semantics, and how the analysis module is chosen.

## Stage sequence and prerequisites

| Stage | Gate skill | Prerequisite (must be PASS/WARN in `gate_log`) | Fail-closed? |
|-------|-----------|------------------------------------------------|:---:|
| design | `alterlab-ssci-design-gate` | (entry) | **yes (BLOCK-capable)** |
| measurement | `alterlab-ssci-measurement-gate` | design | no (WARN default) |
| sampling | `alterlab-ssci-sampling-gate` | design | no (WARN default) |
| analysis | (dispatched module) | design; measurement if latent constructs; sampling | inherits module |
| inference | `alterlab-ssci-inference-gate` | analysis | **yes (BLOCK-capable)** |
| reporting | (hand to `alterlab-paper-writer`) | inference PASS | — |

Measurement and sampling both depend only on design, so they may run in either order (or in
parallel); the orchestrator dispatches whichever the study needs first. Analysis requires design,
plus measurement when the study uses latent constructs.

## Verdict semantics (borrowed from the ARS MANDATORY vs FULL/SLIM taxonomy)

- **PASS** — discipline satisfied; advance and record `{gate, verdict: PASS}`.
- **WARN** — a non-fatal issue (e.g. only alpha reported, saturation argued informally). Advance,
  but record the caveat in `gate_log` and surface it in the final report. WARN never silently
  disappears.
- **BLOCK** — fail-closed. The pipeline cannot advance. Two mandatory blockers:
  - **design-gate BLOCK** when no design family / identifying assumption can be named for a causal
    question → the claim must be downgraded to descriptive/associational or the design rethought.
  - **inference-gate BLOCK** when a drafted claim exceeds the design, sample, or uncertainty →
    the claim must be rewritten down before the study can be reported.

A WARN-defaulting gate escalates to BLOCK on a *fatal* threat: measurement-gate BLOCKs if there is
**no reliability/validity evidence at all** for a construct that carries a hypothesis; sampling-gate
BLOCKs if a hypothesis test is planned with **no sizing logic** (neither power nor a pre-specified
N) — i.e. collect-until-significant.

## Analysis-module decision logic

Choose from `design_type` + the data description, not the user's tool preference:

```
design_type == observational|quasi-experimental AND causal claim
    └─ effect estimation (DiD/IV/RDD/panel FE)         → alterlab-causal-inference
constructs present AND (CFA | SEM | IRT | invariance)  → alterlab-sem-psychometrics
small N AND configurational/set-theoretic question     → alterlab-qca
relational/network data (nodes + ties)                 → alterlab-sna
mechanism via interacting heterogeneous agents          → alterlab-abm-mesa
corpus / open-ended text is the data                    → alterlab-text-as-data
interpretive / theory-building aim                       → alterlab-qualitative-methods (existing)
combined qual + quant strands                            → alterlab-mixed-methods (existing)
plain descriptive/inferential stats                      → alterlab-statistical-analysis (existing)
```

A study can dispatch to **more than one** module (e.g. a survey experiment → sem-psychometrics for
the scale + causal-inference for the treatment effect). The orchestrator records each in
`analysis_module` as a list and runs the inference-gate once over all resulting claims.

## Worked run

Passport at entry:

```yaml
research_question: "Does a minimum-wage increase reduce teen employment?"
stage: design
```

1. **design-gate** → sees a policy turned on in some states/times → routes DiD, pins
   `identifying_assumption: parallel trends`, `claim_type: causal`. Verdict PASS. `stage → measurement`.
2. **measurement-gate** → outcome is administrative employment counts, no latent construct → not
   needed; WARN "no measurement model required" (advisory). `stage → sampling`.
3. **sampling-gate** → observational panel; sizing logic = precision of the DiD estimate; frame =
   states × months. Verdict PASS. `stage → analysis`.
4. orchestrator picks `alterlab-causal-inference` (DiD). Module estimates with a defended
   pre-trend check.
5. **inference-gate** → audits "minimum wage *reduced* teen employment (β, 95% CI)" against
   `design_type: DiD` + defended parallel trends → causal language licensed **iff** pre-trends
   held; otherwise BLOCK and downgrade. Verdict PASS/BLOCK accordingly. `stage → done`.

## The FC / comm-repo boundary

This spine is discipline-agnostic and lives in AlterLab Academic Skills. Communication-specific
applications (media-effects survey design, campaign audience SNA, media-text discourse analysis)
belong in the AlterLab FC repo and must **call** these gates rather than fork them. A skill a
sociologist, economist, and psychologist would all recognize belongs here; a comm-domain
application belongs in FC and imports the spine.
