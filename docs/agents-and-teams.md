# Subagents & Teams

> **Generated** — do not edit by hand. Regenerate with `python3 scripts/gen_agents_catalog.py`; CI fails if this file is stale.

The core research-to-publication pipeline is a multi-agent system: **35 first-class subagents** across **4 skills**, composed into named **teams**. Each subagent is a real artifact under `skills/core/<skill>/agents/*.md` with its own `name`/`description` frontmatter, loaded by its host skill; the plugin manifest wires them in via the `agents` field.

## Teams (named compositions)

### Research Team — `alterlab-deep-research`

Turn a raw topic into a verified, cited synthesis with devil's-advocate and risk-of-bias checkpoints.

**Orchestration:** 6-phase pipeline: question framing → architecture → verified search → synthesis with adversarial checkpoints → ethics/editorial review → compile

**Members:** `research_question_agent`, `research_architect_agent`, `source_verification_agent`, `synthesis_agent`, `devils_advocate_agent`, `risk_of_bias_agent`, `meta_analysis_agent`, `ethics_review_agent`, `editor_in_chief_agent`, `report_compiler_agent`, `bibliography_agent`

### Writing Team — `alterlab-paper-writer`

Turn research materials into a publishable IMRaD draft with bilingual abstract and multi-format output.

**Orchestration:** sequential draft pipeline: intake → literature strategy → structure → argument → draft → figures + citation compliance → peer read → revision → bilingual abstract → format

**Members:** `intake_agent`, `literature_strategist_agent`, `structure_architect_agent`, `argument_builder_agent`, `draft_writer_agent`, `visualization_agent`, `citation_compliance_agent`, `peer_reviewer_agent`, `revision_coach_agent`, `abstract_bilingual_agent`, `formatter_agent`

### Reviewer Panel — `alterlab-paper-reviewer`

Multi-perspective peer review of a finished manuscript, auto-configured to the detected field, ending in an accept/revise/reject decision letter.

**Orchestration:** field analyst configures the panel → domain / methodology / perspective / devil's-advocate reviewers run in parallel → editorial synthesizer merges → editor-in-chief issues the decision

**Members:** `field_analyst_agent`, `domain_reviewer_agent`, `methodology_reviewer_agent`, `perspective_reviewer_agent`, `devils_advocate_reviewer_agent`, `editorial_synthesizer_agent`, `eic_agent`

### Pipeline Orchestration — `alterlab-research-pipeline`

Drive the end-to-end research → write → review → revise → finalize workflow and keep the handoff artifacts consistent.

**Orchestration:** meta-orchestration across the three teams above, tracking state and verifying integrity at each handoff

**Members:** `pipeline_orchestrator_agent`, `state_tracker_agent`, `integrity_verification_agent`

## Full subagent roster

### `alterlab-deep-research` (13 agents)

| Agent | Purpose |
|-------|---------|
| `bibliography-agent` | Systematic literature search and annotated-bibliography curation agent for alterlab-deep-research. Conducts reproducible, documented searches; applies inclusion… |
| `devils-advocate-agent` | Challenges assumptions, tests logical chains, detects biases and fallacies, and stress-tests argument robustness at three mandatory checkpoints in the deep-rese… |
| `editor-in-chief-agent` | Reviews research reports with the rigor of a Q1 journal editor, assessing originality, methodological soundness, evidence sufficiency, argument coherence, and w… |
| `ethics-review-agent` | Acts as the final gate before research delivery, ensuring AI-assisted research meets ethical standards for attribution, disclosure, fair representation, and res… |
| `meta-analysis-agent` | Designs and executes meta-analyses when quantitative synthesis is feasible, computing effect sizes, assessing heterogeneity, generating forest-plot data, planni… |
| `monitoring-agent` | Provides optional post-research literature monitoring, generating actionable monitoring digests and alert configurations anchored to a completed research biblio… |
| `report-compiler-agent` | Transforms research findings, synthesis narratives, and methodological blueprints into polished academic reports following APA 7.0 format, activated for the ini… |
| `research-architect-agent` | Designs the methodological blueprint for research projects, selecting the paradigm, method, data strategy, analytical framework, and validity criteria, and ensu… |
| `research-question-agent` | Transforms vague topics and broad areas of interest into precise, researchable questions, applying the FINER framework (Feasible, Interesting, Novel, Ethical, R… |
| `risk-of-bias-agent` | Assesses risk of bias in included studies using validated instruments (RoB 2 for randomized trials, ROBINS-I for non-randomized studies), producing domain-level… |
| `deep-research-socratic-mentor-agent` | Guides researchers through the non-linear process of clarifying their research thinking as a Q1 journal editor-in-chief, never giving direct answers but asking … |
| `source-verification-agent` | Acts as the quality gatekeeper for all evidence entering the research pipeline, grading sources by the evidence hierarchy, detecting predatory publications, fla… |
| `synthesis-agent` | Performs the core intellectual work of research by integrating findings across multiple sources, identifying patterns and contradictions, resolving conflicts in… |

### `alterlab-paper-reviewer` (7 agents)

| Agent | Purpose |
|-------|---------|
| `devils-advocate-reviewer-agent` | Serves as the devil's advocate for paper review, stress-testing a manuscript before submission by finding its most vulnerable points, biggest logical gaps, and … |
| `domain-reviewer-agent` | Serves as Peer Reviewer 2, a senior researcher in the paper's field, focusing on depth and accuracy of domain knowledge: literature coverage, theoretical framew… |
| `editorial-synthesizer-agent` | Acts as the journal's managing/associate editor, consolidating all review comments, identifying consensus and disagreements, making the final editorial decision… |
| `eic-agent` | Serves as the Editor-in-Chief of a top-tier journal, taking a bird's-eye view of a paper's fit, reader interest, and contribution to the field as a whole rather… |
| `field-analyst-agent` | Acts as a senior academic publishing consultant who reads the complete paper, identifies its disciplinary positioning and methodological orientation, and dynami… |
| `methodology-reviewer-agent` | Serves as Peer Reviewer 1, a research methodology expert focusing on the rigor of research design: whether the methods answer the questions posed, the data coll… |
| `perspective-reviewer-agent` | Serves as Peer Reviewer 3, a cross-disciplinary and practical-perspective reviewer who brings an outsider's view, challenging fundamental assumptions, surfacing… |

### `alterlab-paper-writer` (12 agents)

| Agent | Purpose |
|-------|---------|
| `abstract-bilingual-agent` | Writes high-quality bilingual abstracts (English and Traditional Chinese) with keywords for academic papers, composing each language version independently rathe… |
| `argument-builder-agent` | Constructs the paper's argumentative backbone (central thesis, sub-arguments, claim-evidence-reasoning chains, counter-arguments, and logical flow) and produces… |
| `citation-compliance-agent` | Verifies all citations in the paper draft for format correctness, cross-references in-text citations against the reference list, checks DOIs and URLs, and auto-… |
| `draft-writer-agent` | Writes the complete paper draft section-by-section, following the Structure Architect's outline and the Argument Builder's blueprint, weaving citations naturall… |
| `formatter-agent` | Converts the final reviewed paper into the requested output format(s), applies journal-specific formatting, generates a submission cover letter, and performs a … |
| `intake-agent` | Conducts a structured configuration interview to establish all parameters for the paper-writing pipeline, producing a Paper Configuration Record that downstream… |
| `literature-strategist-agent` | Designs systematic, reproducible literature search strategies, screens sources, creates annotated bibliographies, and builds literature matrices, providing the … |
| `peer-reviewer-agent` | Simulates a rigorous double-blind peer review of the paper draft, scoring across five dimensions, providing line-level feedback, and determining an Accept/Minor… |
| `revision-coach-agent` | Parses unstructured reviewer comments from any format into a structured Revision Roadmap, classifying, mapping, and prioritizing every comment; it works standal… |
| `paper-writer-socratic-mentor-agent` | Acts as a senior doctoral advisor and disciplinary methodology expert, guiding users through chapter-by-chapter paper planning via Socratic dialogue focused on … |
| `structure-architect-agent` | Selects the optimal paper structure, designs a detailed section-by-section outline, allocates word counts, and maps evidence to sections, producing the blueprin… |
| `visualization-agent` | Parses paper data and statistical results to generate publication-quality figure code in Python (matplotlib/seaborn) or R (ggplot2) formatted to APA 7.0 standar… |

### `alterlab-research-pipeline` (3 agents)

| Agent | Purpose |
|-------|---------|
| `integrity-verification-agent` | Zero-tolerance academic integrity gatekeeper for alterlab-research-pipeline (Stage 2.5 pre-review + Stage 4.5 post-revision). Performs 100% verification of refe… |
| `pipeline-orchestrator-agent` | Acts as an academic research project manager, coordinating handoffs between the deep-research, paper-writer, and paper-reviewer skills and the integrity verific… |
| `state-tracker-agent` | Acts as the pipeline state recorder and single source of truth, maintaining each stage's completion status, produced-materials list, revision loop count, and in… |

