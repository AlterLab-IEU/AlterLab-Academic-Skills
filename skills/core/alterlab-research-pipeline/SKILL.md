---
name: alterlab-research-pipeline
description: "Orchestrates the full academic research pipeline (research, write, integrity check, review, revise, re-review, re-revise, final integrity check, finalize), coordinating alterlab-deep-research, alterlab-paper-writer, and alterlab-paper-reviewer into a seamless 10-stage workflow with mandatory integrity verification, two-stage peer review, and reproducible quality gates. Use when the request mentions academic pipeline, research to paper, full paper workflow, paper pipeline, end-to-end paper, research-to-publication, or complete paper workflow. Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read Write Edit Bash WebFetch WebSearch
compatibility: Orchestrates alterlab-deep-research, alterlab-paper-writer, and alterlab-paper-reviewer; uses built-in Claude tools only; no external API key or account required
metadata:
  skill-author: AlterLab
  version: "2.6"
  last_updated: "2026-03-08"
  depends_on: "alterlab-deep-research, alterlab-paper-writer, alterlab-paper-reviewer"
---

# Academic Pipeline v2.6 — Full Academic Research Workflow Orchestrator

A lightweight orchestrator that manages the complete academic pipeline from research exploration to final manuscript. It does not perform substantive work — it only detects stages, recommends modes, dispatches skills, manages transitions, and tracks state.

**v2.0 Core Improvements**:
1. **Mandatory user confirmation checkpoints** — Each stage completion requires user confirmation before proceeding to the next step
2. **Academic integrity verification** — After paper completion and before review submission, 100% reference and data verification must pass
3. **Two-stage review** — First full review + post-revision focused verification review
4. **Final integrity check** — After revision completion, re-verify all citations and data are 100% correct
5. **Reproducible** — Standardized workflow producing consistent quality assurance each time
6. **Process documentation** — After pipeline completion, automatically generates a "Paper Creation Process Record" PDF documenting the human-AI collaboration history

## Quick Start

**Full workflow (from scratch):**
```
I want to write a research paper on the impact of AI on higher education quality assurance
```
--> alterlab-research-pipeline launches, starting from Stage 1 (RESEARCH)

**Mid-entry (existing paper):**
```
I already have a paper, help me review it
```
--> alterlab-research-pipeline detects mid-entry, starting from Stage 2.5 (INTEGRITY)

**Revision mode (received reviewer feedback):**
```
I received reviewer comments, help me revise
```
--> alterlab-research-pipeline detects, starting from Stage 4 (REVISE)

**Execution flow:**
1. Detect the user's current stage and available materials
2. Recommend the optimal mode for each stage
3. Dispatch the corresponding skill for each stage
4. **After each stage completion, proactively prompt and wait for user confirmation**
5. Track progress throughout; Pipeline Status Dashboard available at any time

---

## Trigger Conditions

### Trigger Keywords

**English**: academic pipeline, research to paper, full paper workflow, paper pipeline, end-to-end paper, research-to-publication, complete paper workflow

### Non-Trigger Scenarios

| Scenario | Skill to Use |
|----------|-------------|
| Only need to search materials or do a literature review | `alterlab-deep-research` |
| Only need to write a paper (no research phase needed) | `alterlab-paper-writer` |
| Only need to review a paper | `alterlab-paper-reviewer` |
| Only need to check citation format | `alterlab-paper-writer` (citation-check mode) |
| Only need to convert paper format | `alterlab-paper-writer` (format-convert mode) |

### Trigger Exclusions

- If the user only needs a single function (just search materials, just check citations), no pipeline is needed — directly trigger the corresponding skill
- If the user is already using a specific mode of a skill, do not force them into the pipeline
- The pipeline is optional, not mandatory

---

## Pipeline Stages (10 Stages)

| Stage | Name | Skill / Agent Called | Available Modes | Deliverables |
|-------|------|---------------------|----------------|-------------|
| 1 | RESEARCH | `alterlab-deep-research` | socratic, full, quick | RQ Brief, Methodology, Bibliography, Synthesis |
| 2 | WRITE | `alterlab-paper-writer` | plan, full | Paper Draft |
| **2.5** | **INTEGRITY** | **`integrity_verification_agent`** | **pre-review** | **Integrity verification report + corrected paper** |
| 3 | REVIEW | `alterlab-paper-reviewer` | full (incl. Devil's Advocate) | 5 review reports + Editorial Decision + Revision Roadmap |
| 4 | REVISE | `alterlab-paper-writer` | revision | Revised Draft, Response to Reviewers |
| **3'** | **RE-REVIEW** | **`alterlab-paper-reviewer`** | **re-review** | **Verification review report: revision response checklist + residual issues** |
| **4'** | **RE-REVISE** | **`alterlab-paper-writer`** | **revision** | **Second revised draft (if needed)** |
| **4.5** | **FINAL INTEGRITY** | **`integrity_verification_agent`** | **final-check** | **Final verification report (must achieve 100% pass to proceed)** |
| 5 | FINALIZE | `alterlab-paper-writer` | format-convert | Final Paper (default MD + DOCX; ask about LaTeX; confirm correctness; PDF) |
| **6** | **PROCESS SUMMARY** | **orchestrator** | **auto** | **Paper creation process record MD + LaTeX to PDF (bilingual)** |

---

## Pipeline State Machine

1. **Stage 1 RESEARCH** -> user confirmation -> Stage 2
2. **Stage 2 WRITE** -> user confirmation -> Stage 2.5
3. **Stage 2.5 INTEGRITY** -> PASS -> Stage 3 (FAIL -> fix and re-verify, max 3 rounds)
4. **Stage 3 REVIEW** -> Accept -> Stage 4.5 / Minor|Major -> Stage 4 / Reject -> Stage 2 or end
5. **Stage 4 REVISE** -> user confirmation -> Stage 3'
6. **Stage 3' RE-REVIEW** -> Accept|Minor -> Stage 4.5 / Major -> Stage 4'
7. **Stage 4' RE-REVISE** -> user confirmation -> Stage 4.5 (no return to review)
8. **Stage 4.5 FINAL INTEGRITY** -> PASS (zero issues) -> Stage 5 (FAIL -> fix and re-verify)
9. **Stage 5 FINALIZE** -> MD + DOCX -> ask about LaTeX -> confirm -> PDF -> Stage 6
10. **Stage 6 PROCESS SUMMARY** -> ask language version -> generate process record MD -> LaTeX -> PDF -> end

See `references/pipeline_state_machine.md` for complete state transition definitions.

---

## Adaptive Checkpoint System

**Core rule: After each stage completion, the system must proactively prompt the user and wait for confirmation. The checkpoint presentation adapts based on context and user engagement.**

### Checkpoint Types

| Type | When Used | Content |
|------|-----------|---------|
| FULL | First checkpoint; after integrity boundaries; before finalization | Full deliverables list + decision dashboard + all options |
| SLIM | After 2+ consecutive "continue" responses on non-critical stages | One-line status + auto-continue in 5 seconds |
| MANDATORY | Integrity FAIL; Review decision; Stage 5 | Cannot be skipped; requires explicit user input |

### Decision Dashboard (shown at FULL checkpoints)

```
━━━ Stage [X] [Name] Complete ━━━

Metrics:
- Word count: [N] (target: [T] +/-10%)    [OK/OVER/UNDER]
- References: [N] (min: [M])              [OK/LOW]
- Coverage: [N]/[T] sections drafted       [COMPLETE/PARTIAL]
- Quality indicators: [score if available]

Deliverables:
- [Material 1]
- [Material 2]

Flagged: [any issues detected, or "None"]

Ready to proceed to Stage [Y]? You can also:
1. View progress (say "status")
2. Adjust settings
3. Pause pipeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Adaptive Rules

1. **First checkpoint**: always FULL
2. **After 2+ consecutive "continue" without review**: prompt user awareness ("You've auto-continued [N] times. Want to review progress?")
3. **Integrity boundaries (Stage 2.5, 4.5)**: always MANDATORY
4. **Review decisions (Stage 3, 3')**: always MANDATORY
5. **Before finalization (Stage 5)**: always MANDATORY
6. **All other stages**: start FULL, downgrade to SLIM if user says "just continue"

### Checkpoint Rules

1. **Cannot auto-skip MANDATORY checkpoints**: Even if the previous stage result is perfect, explicit user input is required at MANDATORY checkpoints
2. **User can adjust**: At FULL and MANDATORY checkpoints, users can modify the mode or settings for the next step
3. **Pause-friendly**: Users can pause at any checkpoint and resume later
4. **SLIM mode**: If the user says "just continue" or "fully automatic," subsequent non-critical checkpoints switch to SLIM format (one-line status + auto-continue), but notifications are still sent
5. **Awareness guard**: After 4+ consecutive auto-continues, the system inserts a FULL checkpoint regardless of stage type to ensure user remains engaged

---

## Agent Team (3 Agents)

| # | Agent | Role | File |
|---|-------|------|------|
| 1 | `pipeline_orchestrator_agent` | Main orchestrator: detects stage, recommends mode, triggers skill, manages transitions | `agents/pipeline_orchestrator_agent.md` |
| 2 | `state_tracker_agent` | State tracker: records completed stages, produced materials, revision loop count | `agents/state_tracker_agent.md` |
| 3 | `integrity_verification_agent` | Integrity verifier: 100% reference/citation/data verification | `agents/integrity_verification_agent.md` |

---

## Orchestrator Workflow

The orchestrator runs a four-step loop for every stage:

1. **INTAKE & DETECTION** — Analyze the user's materials to pick the entry stage (no materials -> Stage 1; paper draft -> Stage 2.5; review comments -> Stage 4; final draft -> Stage 5) and confirm entry point + goal.
2. **MODE RECOMMENDATION** — Recommend per-stage modes by user type (novice -> socratic/plan/guided; experienced -> full; time-limited -> quick), explaining the trade-offs so the user chooses.
3. **STAGE EXECUTION** — Dispatch the stage's skill (never doing the work itself), monitor completion, compile deliverables, update state via `state_tracker_agent`, then raise a MANDATORY checkpoint.
4. **TRANSITION** — After confirmation, pass deliverables forward via the per-stage handoff protocol, then begin the next stage.

Full detection decision tree, mode-selection matrix, and the complete per-stage handoff mapping: see `references/orchestrator_workflow.md`.

---

## Integrity & Two-Stage Review Protocols (v2.0)

**Stage 2.5 — First Integrity Check (pre-review):** After WRITE, before REVIEW. `integrity_verification_agent` Mode 1 runs Phases A-E (100% reference existence, >=30% citation-context spot-check, 100% statistical data, >=30% originality + self-plagiarism, 30% claim spot-check / min 10 claims). PASS -> Stage 3; FAIL -> correction list, fix item-by-item, re-verify (max 3 rounds).

**Stage 4.5 — Final Integrity Check (post-revision):** After RE-REVISE / RE-REVIEW-Accept, before FINALIZE. Mode 2 runs Phases A-E at full coverage (100% citation-context, 100% claim verification, zero MAJOR_DISTORTION + zero UNVERIFIABLE required) and cross-checks that every Stage 2.5 issue is resolved. Must PASS with zero issues to reach Stage 5.

**Stage 3 — First Review:** EIC + R1 (methodology) + R2 (domain) + R3 (interdisciplinary) + Devil's Advocate. Output: 5 reports + Editorial Decision + Revision Roadmap + Socratic Revision Coaching. Accept -> Stage 4.5 / Minor|Major -> Stage 4 / Reject -> Stage 2 or end.

**Stage 3' — Verification Review:** `re-review` mode over revised draft + Response to Reviewers. Output: revision-response comparison table + new-issues list + new Editorial Decision. Accept|Minor -> Stage 4.5 / Major -> Stage 4'.

Revision Coaching (Stage 3->4, max 8 rounds) and Residual Coaching (Stage 3'->4', max 5 rounds) use EIC Socratic dialogue; the user can say "just fix it" to skip. Full phase-by-phase execution steps, result handling, and coaching detail: see `references/integrity_and_review_protocols.md`.

---

## Mid-Entry Protocol

Users can enter from any stage. The orchestrator will:

1. **Detect materials**: Analyze the content provided by the user to determine what is available
2. **Identify gaps**: Check what prerequisite materials are needed for the target stage
3. **Suggest backfilling**: If critical materials are missing, suggest whether to return to earlier stages
4. **Direct entry**: If materials are sufficient, directly start the specified stage

**Important: mid-entry cannot skip Stage 2.5**
- If the user brings a paper and enters directly, go through Stage 2.5 (INTEGRITY) first before Stage 3 (REVIEW)
- Only exception: User can provide a previous integrity verification report and content has not been modified

---

## External Review Protocol (Added in v2.5)

**Scenario**: The user submitted to a journal and received feedback from real human reviewers, bringing those comments into the pipeline.

**Trigger**: User says "I received reviewer comments," "reviewer comments," "revise and resubmit," etc.

Unlike internal simulated review, external review handles unstructured, variable-quality human comments that must be judged (accept / partially accept / reject) rather than accepted wholesale. The four-step workflow is: (1) intake and structuring into an External Review Summary with user confirmation; (2) strategic revision coaching (judgment + strategy + risk assessment per Major comment, no default "accept all", max 8 rounds); (3) revision + point-by-point Response to Reviewers letter; (4) self-verification for completeness/consistency/truthfulness. Honest capability boundaries apply: AI verification does not equal human-reviewer satisfaction, and final scholarly judgment rests with the researcher.

Full comparison table, per-step templates (External Review Summary, Response to Reviewers), coaching questions, and the four capability-boundary caveats: see `references/external_review_protocol.md`.

---

## Progress Dashboard

Users can say "status" or "pipeline status" at any time to view:

```
+=============================================+
|   Academic Pipeline v2.0 Status             |
+=============================================+
| Topic: Impact of AI on Higher Education     |
|        Quality Assurance                    |
+---------------------------------------------+

  Stage 1   RESEARCH          [v] Completed
  Stage 2   WRITE             [v] Completed
  Stage 2.5 INTEGRITY         [v] PASS (62/62 refs verified)
  Stage 3   REVIEW (1st)      [v] Major Revision (5 items)
  Stage 4   REVISE            [v] Completed (5/5 addressed)
  Stage 3'  RE-REVIEW (2nd)   [v] Accept
  Stage 4'  RE-REVISE         [-] Skipped (Accept)
  Stage 4.5 FINAL INTEGRITY   [..] In Progress
  Stage 5   FINALIZE          [ ] Pending
  Stage 6   PROCESS SUMMARY   [ ] Pending

+---------------------------------------------+
| Integrity Verification:                     |
|   Pre-review:  PASS (0 issues)              |
|   Final:       In progress...               |
+---------------------------------------------+
| Review History:                             |
|   Round 1: Major Revision (5 required)      |
|   Round 2: Accept                           |
+=============================================+
```

See `templates/pipeline_status_template.md` for the output template.

---

## Revision Loop Management

- Stage 3 (first review) -> Stage 4 (revision) -> Stage 3' (verification review) -> Stage 4' (re-revision, if needed) -> Stage 4.5 (final verification)
- **Maximum 1 round of RE-REVISE** (Stage 4'): If Stage 3' gives Major, enter Stage 4' for revision then proceed directly to Stage 4.5 (no return to review)
- **Pipeline overrides alterlab-paper-writer's max 2 revision rule**: In the pipeline, revisions are limited to Stage 4 + Stage 4' (one round each), replacing alterlab-paper-writer's max 2 rounds rule
- Mark unresolved issues as Acknowledged Limitations
- Provide cumulative revision history (each round's decision, items addressed, unresolved items)

---

## Reproducibility

v2.0 design ensures consistent quality assurance with each execution: mandatory Stage 2.5 + 4.5 integrity checks that cannot be skipped, five fixed review perspectives (EIC + R1/R2/R3 + Devil's Advocate), standardized verification search templates, explicit PASS/FAIL thresholds (zero SERIOUS + zero MEDIUM + zero MAJOR_DISTORTION + zero UNVERIFIABLE), and per-stage recorded deliverables for retrospective audit. When the pipeline ends, `state_tracker_agent` produces a complete audit trail.

Standardized-workflow guarantee table and the full end-of-pipeline audit-trail template: see `references/reproducibility_and_audit.md`.

---

## Stage 6: Process Summary Protocol (Added in v2.4)

**Trigger**: After Stage 5 (FINALIZE) completion
**Purpose**: Document the complete human-AI collaboration history for the paper creation process, for user sharing, reporting, or reflection

Workflow: ask language preference (zh / en / both) -> review session history and compile user quotes, per-stage decisions, iteration details, and pipeline statistics -> generate Markdown (`paper_creation_process.md` / `_en.md`) -> convert to LaTeX and compile PDF via tectonic (Chinese uses xeCJK + Source Han Serif TC VF). The record ends with a **mandatory Collaboration Quality Evaluation** — a `/insight`-style final chapter scoring the user 1-100 across six dimensions (Direction Setting, Intellectual Contribution, Quality Gatekeeping, Iteration Discipline, Delegation Efficiency, Meta-Learning) with honest, evidence-based, constructive analysis (What Worked Well / Missed Opportunities / Recommendations / Human vs AI Value-Add / Claude self-reflection).

Full workflow steps, required-content table, six-dimension score card, scoring-criteria bands, required subsections, evaluation principles, and output specifications: see `references/process_summary_protocol.md`.

---

## Quality Standards

| Dimension | Requirement |
|-----------|------------|
| Stage detection | Correctly identify user's current stage and available materials |
| Mode recommendation | Recommend appropriate mode based on user preferences and material status |
| Material handoff | Stage-to-stage handoff materials are complete and correctly formatted |
| State tracking | Pipeline state updated in real time; Progress Dashboard accurate |
| **Mandatory checkpoint** | **User confirmation required after each stage completion** |
| **Mandatory integrity check** | **Stage 2.5 and 4.5 cannot be skipped, must PASS** |
| No overstepping | Orchestrator does not perform substantive research/writing/reviewing, only dispatching |
| No forcing | User can pause or exit pipeline at any time (but cannot skip integrity checks) |
| Reproducible | Same input follows the same workflow across different sessions |

---

## Error Recovery

| Stage | Error | Handling |
|-------|-------|---------|
| Intake | Cannot determine entry point | Ask user what materials they have and their goal |
| Stage 1 | alterlab-deep-research not converging | Suggest mode switch (socratic -> full) or narrow scope |
| Stage 2 | Missing research foundation | Suggest returning to Stage 1 to supplement research |
| Stage 2.5 | Still FAIL after 3 correction rounds | List unverifiable items; user decides whether to continue |
| Stage 3 | Review result is Reject | Provide options: major restructuring (Stage 2) or abandon |
| Stage 4 | Revision incomplete on all items | List unaddressed items; ask whether to continue |
| Stage 3' | Verification still has major issues | Enter Stage 4' for final revision |
| Stage 4' | Issues remain after revision | Mark as Acknowledged Limitations; proceed to Stage 4.5 |
| Stage 4.5 | Final verification FAIL | Fix and re-verify (max 3 rounds) |
| Any | User leaves midway | Save pipeline state; can resume from breakpoint next time |
| Any | Skill execution failure | Report error; suggest retry or skip |

---

## Agent File References

| Agent | Definition File |
|-------|----------------|
| pipeline_orchestrator_agent | `agents/pipeline_orchestrator_agent.md` |
| state_tracker_agent | `agents/state_tracker_agent.md` |
| integrity_verification_agent | `agents/integrity_verification_agent.md` |

---

## Reference Files

| Reference | Purpose |
|-----------|---------|
| `references/pipeline_state_machine.md` | Complete state machine definition: all legal transitions, preconditions, actions |
| `references/orchestrator_workflow.md` | Full four-step orchestration loop: detection decision tree, mode-selection matrix, per-stage handoff mapping |
| `references/integrity_and_review_protocols.md` | Stage 2.5/4.5 integrity gates + Stage 3/3' two-stage review: phase-by-phase execution steps and coaching detail |
| `references/external_review_protocol.md` | Full external (real journal) review workflow: intake templates, strategic coaching, Response to Reviewers, capability boundaries |
| `references/reproducibility_and_audit.md` | Standardized-workflow guarantee table + full end-of-pipeline audit-trail template |
| `references/process_summary_protocol.md` | Stage 6 process record: workflow, required content, Collaboration Quality Evaluation score card, output specs |
| `references/plagiarism_detection_protocol.md` | Phase D originality verification protocol + self-plagiarism + AI text characteristics |
| `references/mode_advisor.md` | Unified cross-skill decision tree: maps user intent to optimal skill + mode |
| `references/claim_verification_protocol.md` | Phase E claim verification protocol: claim extraction, source tracing, cross-referencing, verdict taxonomy |
| `references/team_collaboration_protocol.md` | Multi-person team coordination: role definitions, handoff protocol, version control, conflict resolution |
| `shared/handoff_schemas.md` | Cross-skill data contracts: 9 schemas for all inter-stage handoff artifacts |

---

## Templates

| Template | Purpose |
|----------|---------|
| `templates/pipeline_status_template.md` | Progress Dashboard output template |

---

## Examples

| Example | Demonstrates |
|---------|-------------|
| `examples/full_pipeline_example.md` | Complete pipeline conversation log (Stage 1-5, with integrity + 2-stage review) |
| `examples/mid_entry_example.md` | Mid-entry example starting from Stage 2.5 (existing paper -> integrity check -> review -> revision -> finalization) |

---

## Output Language

Follows user language. Academic terminology retained in English.

---

## Integration with Other Skills

```
alterlab-research-pipeline dispatches the following skills (does not do work itself):

Stage 1: alterlab-deep-research
  - socratic mode: Guided research exploration
  - full mode: Complete research report
  - quick mode: Quick research summary

Stage 2: alterlab-paper-writer
  - plan mode: Socratic chapter-by-chapter guidance
  - full mode: Complete paper writing

Stage 2.5: integrity_verification_agent (Mode 1: pre-review)
Stage 4.5: integrity_verification_agent (Mode 2: final-check)

Stage 3: alterlab-paper-reviewer
  - full mode: Complete 5-person review (EIC + R1/R2/R3 + Devil's Advocate)

Stage 3': alterlab-paper-reviewer
  - re-review mode: Verification review (focused on revision responses)

Stage 4/4': alterlab-paper-writer (revision mode)
Stage 5: alterlab-paper-writer (format-convert mode)
  - Step 1: Ask user which academic formatting style (APA 7.0 / Chicago / IEEE, etc.)
  - Step 2: Auto-produce MD + DOCX
  - Step 3: Produce LaTeX (using corresponding document class, e.g., apa7 class for APA 7.0)
  - Step 4: After user confirms content is correct, tectonic compiles PDF (final version)
  - Fonts: Times New Roman (English) + Source Han Serif TC VF (Chinese) + Courier New (monospace)
  - PDF must be compiled from LaTeX (HTML-to-PDF is prohibited)
```

---

## Related Skills

| Skill | Relationship |
|-------|-------------|
| `alterlab-deep-research` | Dispatched (Stage 1 research phase) |
| `alterlab-paper-writer` | Dispatched (Stage 2 writing, Stage 4/4' revision, Stage 5 formatting) |
| `alterlab-paper-reviewer` | Dispatched (Stage 3 first review, Stage 3' verification review) |

---

## Version Info

| Item | Content |
|------|---------|
| Skill Version | 2.6 |
| Last Updated | 2026-03-08 |
| Maintainer | AlterLab |
| Dependent Skills | alterlab-deep-research v2.0+, alterlab-paper-writer v2.0+, alterlab-paper-reviewer v1.1+ |
| Role | Full academic research workflow orchestrator |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 2.6 | 2026-03-08 | **Handoff Data Schema**: Enhanced `shared/handoff_schemas.md` with 9 comprehensive schemas (RQ Brief, Bibliography, Synthesis, Paper Draft, Integrity Report, Review Report, Revision Roadmap, Response to Reviewers, Material Passport) with full field definitions, type constraints, and validation rules; orchestrator validates output against schemas before each transition. **Adaptive Checkpoint System**: Replaced static checkpoint template with 3-tier system (FULL/SLIM/MANDATORY) based on stage criticality and user engagement; FULL checkpoints include decision dashboard with metrics; SLIM auto-continues for experienced users; MANDATORY cannot be bypassed at integrity/review/finalization boundaries; awareness guard after 4+ auto-continues. **Mode Advisor**: New `references/mode_advisor.md` with unified cross-skill decision tree, common misconceptions table, user archetype recommendations, decision flowchart, and anti-patterns guide. **Team Collaboration Protocol**: New `references/team_collaboration_protocol.md` with 5 role definitions, per-transition handoff procedures, git branching/tagging strategy, conflict resolution matrix, and communication templates; state tracker extended with `assigned_to`, `approval_gate`, `team_notes` per stage and `schema_validation_log`. **Phase E Claim Verification**: New `references/claim_verification_protocol.md` with E1 claim extraction, E2 source tracing, E3 cross-referencing; verdict taxonomy (VERIFIED / MINOR_DISTORTION / MAJOR_DISTORTION / UNVERIFIABLE / UNVERIFIABLE_ACCESS); severity mapping (MAJOR_DISTORTION -> SERIOUS, UNVERIFIABLE -> SERIOUS, MINOR_DISTORTION -> MINOR, UNVERIFIABLE_ACCESS -> MEDIUM); integrated into integrity_verification_agent Mode 1 (30% spot-check) and Mode 2 (100%); pass/fail criteria updated to include Phase E verdicts. **Mid-Entry Material Passport Check**: Pipeline orchestrator now validates Material Passport on mid-entry; decision tree checks verification_status, freshness (< 24 hours), and content modification (version_label comparison); offers skip/spot-check/full re-verify options for Stage 2.5 when passport is valid; passport freshness validation rules added to `shared/handoff_schemas.md` |
| 2.5 | 2026-03-08 | External Review Protocol: structured intake of real journal reviewer feedback (text/PDF/DOCX); 4-step workflow (parse -> strategic coaching -> revise + Response to Reviewers -> completeness check); differentiated behavior from internal simulated review (no default "accept all", risk assessment per comment, user confirmation of parsed items); explicit capability boundaries (AI verification ≠ reviewer satisfaction) |
| 2.4 | 2026-03-08 | Stage 6 PROCESS SUMMARY: post-pipeline paper creation process record; asks user preferred language (zh/en/both); generates structured MD summarizing full human-AI collaboration history with user quotes, key decisions, iteration details, and lessons learned; mandatory final chapter: **Collaboration Quality Evaluation** (6 dimensions scored 1-100, bar chart visualization, What Worked Well / Missed Opportunities / Recommendations / Human vs AI Value-Add / Claude's Self-Reflection); compiles to PDF via LaTeX + tectonic; outputs `paper_creation_process_zh.pdf` + `paper_creation_process_en.pdf` |
| 2.3 | 2026-03-08 | Stage 5 FINALIZE: mandatory formatting style prompt (APA 7.0 / Chicago / IEEE); PDF must compile from LaTeX via tectonic (no HTML-to-PDF); APA 7.0 uses `apa7` document class (`man` mode) with XeCJK for bilingual support; font stack: Times New Roman + Source Han Serif TC VF + Courier New |
| 2.2 | 2025-03-05 | Checkpoint confirmation semantics (6 user commands with precise actions); mode switching rules (safe/dangerous/prohibited matrix); skill failure fallback matrix (per-stage degradation strategies); state ownership protocol (single source of truth with write access control); material version control (versioned artifacts with audit trail); cross-skill reference to `shared/handoff_schemas.md` |
| 2.1 | 2026-03 | Added plagiarism detection protocol (Phase D); enhanced integrity_verification_agent with originality verification (D1 WebSearch, D2 self-plagiarism); updated both verification modes |
| 2.0 | 2026-02 | Added Stage 2.5/4.5 integrity checks, two-stage review, mandatory checkpoints, Devil's Advocate, reproducibility guarantees, integrity_verification_agent |
| 1.0 | 2026-02 | Initial version: 5+1 stage pipeline |
