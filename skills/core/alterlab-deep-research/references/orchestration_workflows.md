# Orchestration Workflow Diagrams

Detailed phase-by-phase agent-flow diagrams for the standard 6-phase pipeline, the Socratic 5-layer guided dialogue, and the PRISMA systematic-review pipeline. The SKILL.md body keeps the section intros, checkpoint rules, and mode tables; this file holds the full flow diagrams.

## Standard Orchestration Workflow (6 Phases)

```
User: "Research [topic]"
     |
=== Phase 1: SCOPING (Interactive) ===
     |
     |-> [research_question_agent] -> RQ Brief
     |   - FINER criteria scoring (Feasible, Interesting, Novel, Ethical, Relevant)
     |   - Scope boundaries (in-scope / out-of-scope)
     |   - 2-3 sub-questions
     |
     |-> [research_architect_agent] -> Methodology Blueprint
     |   - Research paradigm (positivist / interpretivist / pragmatist)
     |   - Method selection (qualitative / quantitative / mixed)
     |   - Data strategy (primary / secondary / both)
     |   - Analytical framework
     |   - Validity & reliability criteria
     |
     +-> [devils_advocate_agent] -- CHECKPOINT 1
         - RQ clarity and answerable?
         - Method appropriate for question?
         - Scope too broad or too narrow?
         - Verdict: PASS / REVISE (with specific feedback)
     |
     ** User confirmation before Phase 2 **
     |
=== Phase 2: INVESTIGATION ===
     |
     |-> [bibliography_agent] -> Source Corpus + Annotated Bibliography
     |   - Systematic search strategy (databases, keywords, Boolean)
     |   - Inclusion/exclusion criteria
     |   - PRISMA-style flow (if applicable)
     |   - Annotated bibliography (APA 7.0)
     |
     +-> [source_verification_agent] -> Verified & Graded Sources
         - Evidence hierarchy grading (Level I-VII)
         - Predatory journal screening
         - Conflict-of-interest flagging
         - Currency assessment (publication date relevance)
         - Source quality matrix
     |
=== Phase 3: ANALYSIS ===
     |
     |-> [synthesis_agent] -> Synthesis Narrative + Gap Analysis
     |   - Thematic synthesis across sources
     |   - Contradiction identification & resolution
     |   - Evidence convergence/divergence mapping
     |   - Knowledge gap analysis
     |   - Theoretical framework integration
     |
     +-> [devils_advocate_agent] -- CHECKPOINT 2
         - Cherry-picking check
         - Confirmation bias detection
         - Logic chain validation
         - Alternative explanations explored?
         - Verdict: PASS / REVISE
     |
=== Phase 4: COMPOSITION ===
     |
     +-> [report_compiler_agent] -> Full APA 7.0 Draft
         - Title Page
         - Abstract (150-250 words)
         - Introduction (context, problem, purpose, RQ)
         - Literature Review / Theoretical Framework
         - Methodology
         - Findings / Results
         - Discussion (interpretation, implications, limitations)
         - Conclusion & Recommendations
         - References (APA 7.0)
         - Appendices (if applicable)
     |
=== Phase 5: REVIEW (Parallel) ===
     |
     |-> [editor_in_chief_agent] -> Editorial Verdict + Line Feedback
     |   - Originality assessment
     |   - Methodological rigor
     |   - Evidence sufficiency
     |   - Argument coherence
     |   - Writing quality (clarity, conciseness, flow)
     |   - Verdict: ACCEPT / MINOR REVISION / MAJOR REVISION / REJECT
     |
     |-> [ethics_review_agent] -> Ethics Clearance
     |   - AI disclosure compliance
     |   - Attribution integrity
     |   - Dual-use screening
     |   - Fair representation check
     |   - Verdict: CLEARED / CONDITIONAL / BLOCKED
     |
     +-> [devils_advocate_agent] -- CHECKPOINT 3
         - Final vulnerability scan
         - Strongest counter-argument test
         - "So what?" significance check
         - Verdict: PASS / REVISE
     |
=== Phase 6: REVISION ===
     |
     +-> [report_compiler_agent] -> Final Report
         - Address editorial feedback
         - Resolve ethics conditions
         - Incorporate devil's advocate insights
         - Max 2 revision loops
         - Remaining issues -> "Acknowledged Limitations" section
```

## Socratic Mode Layer Flow (Guided Research Dialogue)

```
User: "Guide my research on [topic]"
     |
=== Layer 1: PROBLEM FRAMING (corresponds to first half of Phase 1) ===
     |
     +-> [socratic_mentor_agent] -> Follow-up on research motivation and problem definition
         [research_question_agent] -> Provide FINER guidance framework
         - "What is the question you truly want to answer?"
         - "Why does this question matter? To whom?"
         - "If your research succeeds, how would the world be different?"
         Extract [INSIGHT: ...] each round
         At least 2 rounds of dialogue before entering Layer 2
     |
=== Layer 2: METHODOLOGY REFLECTION (corresponds to second half of Phase 1) ===
     |
     +-> [socratic_mentor_agent] -> Follow-up on rationale for methodology choices
         [devils_advocate_agent] -> Challenge methodology assumptions at end of Layer 2
         - "How do you plan to answer this question? Why this approach?"
         - "Is there a completely different method that could also answer your question?"
         - "What is the biggest weakness of your method?"
         At least 2 rounds of dialogue before entering Layer 3
     |
=== Layer 3: EVIDENCE DESIGN (corresponds to Phase 2-3) ===
     |
     +-> [socratic_mentor_agent] -> Follow-up on evidence strategy
         - "What kind of evidence would convince you of your conclusion?"
         - "What evidence would make you change your conclusion?"
         - "What are you most worried about not finding?"
         At least 2 rounds of dialogue before entering Layer 4
     |
=== Layer 4: CRITICAL SELF-EXAMINATION (corresponds to Phase 5) ===
     |
     +-> [socratic_mentor_agent] -> Follow-up on limitations and risks
         [devils_advocate_agent] -> Challenge conclusion assumptions
         - "What does your research assume? What if those assumptions don't hold?"
         - "How would someone with the opposite view refute you?"
         - "What negative impact could your research have?"
         At least 2 rounds of dialogue before entering Layer 5
     |
=== Layer 5: SIGNIFICANCE & CONTRIBUTION (conclusion) ===
     |
     +-> [socratic_mentor_agent] -> Follow-up on "so what?"
         - "Why should readers care about your findings?"
         - "What aspects of our understanding of this issue does your research change?"
         At least 1 round of dialogue
     |
     +-> Compile all [INSIGHT]s into Research Plan Summary
         Can directly hand off to alterlab-paper-writer (plan mode)
```

## Systematic Review Mode Pipeline

```
User: "Systematic review of [topic]" / "Meta-analysis of [topic]"
     |
=== Phase 1: SCOPING (Generates Protocol, not just RQ) ===
     |
     |-> [research_question_agent] -> PICOS-formatted RQ
     |   - Population, Intervention, Comparator, Outcome, Study design
     |   - Explicit eligibility criteria (inclusion/exclusion)
     |
     |-> [research_architect_agent] -> Systematic Review Protocol
     |   - Protocol follows PRISMA-P 2015 (templates/prisma_protocol_template.md)
     |   - Pre-specified subgroup analyses and sensitivity analyses
     |   - Risk of bias tool selection (RoB 2 / ROBINS-I)
     |   - Meta-analysis feasibility pre-assessment
     |
     +-> [devils_advocate_agent] -- CHECKPOINT 1
         - PICOS specificity check
         - Search strategy comprehensiveness
         - Protocol completeness
         - Verdict: PASS / REVISE
     |
     ** User confirmation of protocol before Phase 2 **
     |
=== Phase 2: INVESTIGATION (PRISMA-Compliant Search + RoB) ===
     |
     |-> [bibliography_agent] -> PRISMA Flow Diagram + Source Corpus
     |   - Search ≥ 2 databases with documented strategy
     |   - Dual-pass screening (title/abstract → full text)
     |   - PRISMA 2020 flow diagram with counts at each stage
     |   - Excluded studies with reasons documented
     |
     |-> [source_verification_agent] -> Verified Sources
     |   - Standard verification + predatory journal screening
     |
     +-> [risk_of_bias_agent] -> RoB Assessment
         - Per-study domain assessment with signaling questions
         - Traffic-light summary table across all studies
         - Distribution summary (% Low / Some Concerns / High)
     |
=== Phase 3: ANALYSIS (Meta-Analysis or Narrative Synthesis) ===
     |
     |-> [meta_analysis_agent] -> Quantitative or Narrative Synthesis
     |   - Feasibility assessment (pool or not?)
     |   - If feasible: effect size calculation, forest plot data,
     |     heterogeneity (I², Q, tau²), subgroup/sensitivity analyses
     |   - If not feasible: structured narrative synthesis (SWiM)
     |   - GRADE certainty of evidence for each outcome
     |
     |-> [synthesis_agent] -> Qualitative Themes + Gap Analysis
     |   - Thematic synthesis across studies
     |   - Integration with quantitative findings
     |
     +-> [devils_advocate_agent] -- CHECKPOINT 2
         - Cherry-picking check
         - Heterogeneity explanation adequacy
         - GRADE assessment validity
         - Verdict: PASS / REVISE
     |
=== Phase 4: COMPOSITION ===
     |
     +-> [report_compiler_agent] -> PRISMA 2020 Report
         - Uses templates/prisma_report_template.md
         - All 27 PRISMA items mapped to sections
         - Study characteristics table
         - Risk of bias summary table
         - Forest plot data (if meta-analysis)
         - GRADE Summary of Findings table
     |
=== Phase 5: REVIEW (Parallel) ===
     |
     |-> [editor_in_chief_agent] -> Editorial Verdict
     |-> [ethics_review_agent] -> Ethics Clearance
     +-> [devils_advocate_agent] -- CHECKPOINT 3
     |
=== Phase 6: REVISION ===
     |
     +-> [report_compiler_agent] -> Final PRISMA Report
```
