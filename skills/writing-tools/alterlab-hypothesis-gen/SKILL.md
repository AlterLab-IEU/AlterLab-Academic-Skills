---
name: alterlab-hypothesis-gen
description: Formulates structured, testable hypotheses from experimental observations using a scientific-method framework — derives predictions, proposes mechanisms, and designs experiments to test them, then renders a LaTeX report. Use when turning observations or data into falsifiable, mechanistic hypotheses, competing-explanation sets, testable predictions, or experimental designs. For a standalone systematic literature review or evidence synthesis (not a means to hypotheses) use alterlab-literature-review; for open-ended brainstorming before any specific observation use alterlab-scientific-brainstorm; to evaluate an existing manuscript use alterlab-peer-review. Part of the AlterLab Academic Skills suite.
allowed-tools: Read Write Edit Bash WebSearch WebFetch
license: MIT
compatibility: Hypothesis reasoning runs with the Read/Write/Edit/Bash tools alone; the literature-grounding step uses WebSearch/WebFetch (skip it if offline). Rendering the LaTeX report requires a local XeLaTeX/LuaLaTeX install (e.g. TeX Live) — optional, the analysis stands without it.
metadata:
    skill-author: AlterLab
    version: "1.0.1"
    last_updated: "2026-09-23"
---

# Scientific Hypothesis Generation

## Overview

Hypothesis generation is a systematic process for developing testable explanations. Formulate evidence-based hypotheses from observations, design experiments, explore competing explanations, and develop predictions. Apply this skill for scientific inquiry across domains.

## When to Use This Skill

This skill should be used when:
- Developing hypotheses from observations or preliminary data
- Designing experiments to test scientific questions
- Exploring competing explanations for phenomena
- Formulating testable predictions for research
- Conducting literature-based hypothesis generation
- Planning mechanistic studies across scientific domains

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Open-ended, blue-sky ideation with no specific observation to explain yet | `alterlab-scientific-brainstorm` |
| Automated LLM-driven hypothesis generation and testing over a tabular dataset (HypoGeniC) | `alterlab-hypogenic` |
| A standalone systematic review or PRISMA evidence synthesis as the deliverable | `alterlab-literature-review` |
| Grading the evidence quality or design flaws of existing claims | `alterlab-scientific-thinking` |
| Freezing hypotheses and the analysis plan in a pre-registration before data collection | `alterlab-preregistration-discipline` |

## Workflow

Follow this systematic process to generate robust scientific hypotheses:

### 1. Understand the Phenomenon

Start by clarifying the observation, question, or phenomenon that requires explanation:

- Identify the core observation or pattern that needs explanation
- Define the scope and boundaries of the phenomenon
- Note any constraints or specific contexts
- Clarify what is already known vs. what is uncertain
- Identify the relevant scientific domain(s)

### 2. Conduct Comprehensive Literature Search

Search existing scientific literature to ground hypotheses in current evidence. Use both PubMed (for biomedical topics) and general web search (for broader scientific domains):

**For biomedical topics:**
- Use WebFetch with PubMed URLs to access relevant literature
- Search for recent reviews, meta-analyses, and primary research
- Look for similar phenomena, related mechanisms, or analogous systems

**For all scientific domains:**
- Use WebSearch to find recent papers, preprints, and reviews
- Search for established theories, mechanisms, or frameworks
- Identify gaps in current understanding

**Search strategy:**
- Begin with broad searches to understand the landscape
- Narrow to specific mechanisms, pathways, or theories
- Look for contradictory findings or unresolved debates
- Consult `references/literature_search_strategies.md` for detailed search techniques

### 3. Synthesize Existing Evidence

Analyze and integrate findings from literature search:

- Summarize current understanding of the phenomenon
- Identify established mechanisms or theories that may apply
- Note conflicting evidence or alternative viewpoints
- Recognize gaps, limitations, or unanswered questions
- Identify analogies from related systems or domains

### 4. Generate Competing Hypotheses

Develop 3-5 distinct hypotheses that could explain the phenomenon. Each hypothesis should:

- Provide a mechanistic explanation (not just description)
- Be distinguishable from other hypotheses
- Draw on evidence from the literature synthesis
- Consider different levels of explanation (molecular, cellular, systemic, population, etc.)

**Strategies for generating hypotheses:**
- Apply known mechanisms from analogous systems
- Consider multiple causative pathways
- Explore different scales of explanation
- Question assumptions in existing explanations
- Combine mechanisms in novel ways

### 5. Evaluate Hypothesis Quality

Assess each hypothesis against established quality criteria from `references/hypothesis_quality_criteria.md`:

**Testability:** Can the hypothesis be empirically tested?
**Falsifiability:** What observations would disprove it?
**Parsimony:** Is it the simplest explanation that fits the evidence?
**Explanatory Power:** How much of the phenomenon does it explain?
**Scope:** What range of observations does it cover?
**Consistency:** Does it align with established principles?
**Novelty:** Does it offer new insights beyond existing explanations?

Explicitly note the strengths and weaknesses of each hypothesis.

### 6. Design Experimental Tests

For each viable hypothesis, propose specific experiments or studies to test it. Consult `references/experimental_design_patterns.md` for common approaches:

**Experimental design elements:**
- What would be measured or observed?
- What comparisons or controls are needed?
- What methods or techniques would be used?
- What sample sizes or statistical approaches are appropriate?
- What are potential confounds and how to address them?

**Consider multiple approaches:**
- Laboratory experiments (in vitro, in vivo, computational)
- Observational studies (cross-sectional, longitudinal, case-control)
- Clinical trials (if applicable)
- Natural experiments or quasi-experimental designs

### 7. Formulate Testable Predictions

For each hypothesis, generate specific, quantitative predictions:

- State what should be observed if the hypothesis is correct
- Specify expected direction and magnitude of effects when possible
- Identify conditions under which predictions should hold
- Distinguish predictions between competing hypotheses
- Note predictions that would falsify the hypothesis

### 8. Present Structured Output

Generate a professional LaTeX document using the template in `assets/hypothesis_report_template.tex`. The report should be well-formatted with colored boxes for visual organization and divided into a concise main text with comprehensive appendices.

**Document Structure:**

**Main Text (about 4 pages):**
1. **Executive Summary** — brief overview in `summarybox` (0.5-1 page)
2. **Competing Hypotheses** — each hypothesis in its own colored box with a brief mechanistic explanation and key evidence (2-2.5 pages for 3-5 hypotheses)
3. **Testable Predictions** — key predictions in `predictionbox` (0.5-1 page)
4. **Critical Comparisons** — priority comparisons in `comparisonbox` (0.5-1 page)

Keep the main text to the essentials; everything else goes to the appendices:
- **Appendix A:** Comprehensive literature review with extensive citations
- **Appendix B:** Detailed experimental designs with full protocols
- **Appendix C:** Quality assessment tables and detailed evaluations
- **Appendix D:** Supplementary evidence and analogous systems

**Colored Box Usage** (environments from `hypothesis_generation.sty`):
- `hypothesisbox1` through `hypothesisbox5` — one per competing hypothesis (blue, green, purple, teal, orange)
- `predictionbox` — testable predictions (amber)
- `comparisonbox` — critical comparisons (steel gray)
- `evidencebox` — supporting-evidence highlights (light blue)
- `summarybox` — executive summary (blue)

**Each hypothesis box contains:**
- **Mechanistic Explanation:** 1-2 brief paragraphs (6-10 sentences) explaining how and why
- **Key Supporting Evidence:** 2-3 bullet points with citations (most important evidence only)
- **Core Assumptions:** 1-2 critical assumptions

**Page overflow.** The boxes in `hypothesis_generation.sty` are not `breakable` tcolorboxes, so a box taller than the space left on the page runs off the bottom and the PDF becomes unreadable. Keep each hypothesis box to about 0.6 page (15-20 lines); move longer mechanism detail and extra evidence to Appendix A. Before each box, start a fresh page with `\newpage` if less than ~0.6 page remains, and put `\newpage` between major appendix sections.

```latex
\newpage
\begin{hypothesisbox1}[Hypothesis 1: Title]
% mechanistic explanation, 2-3 evidence bullets, 1-2 assumptions
\end{hypothesisbox1}
```

**Citation Requirements:**
- **Main text:** 10-15 key citations for the most important evidence only
- **Appendix A:** comprehensive coverage of the relevant literature (typically 40-70 citations for a well-studied phenomenon)

Cite only sources you actually retrieved and checked during the literature search — never invent or pad references to reach a target, because a fabricated citation undermines the whole report. For a sparse literature, fewer verified citations are the right answer. Use `\citep{author2023}` for parenthetical citations.

**LaTeX Compilation:**

The template requires XeLaTeX or LuaLaTeX (it loads `fontspec`):

```bash
xelatex hypothesis_report.tex
bibtex hypothesis_report
xelatex hypothesis_report.tex
xelatex hypothesis_report.tex
```

**Required packages:** `hypothesis_generation.sty` must be in the same directory or on the LaTeX path. It requires tcolorbox, xcolor, fontspec, fancyhdr, titlesec, enumitem, booktabs, and natbib.

**Quick Reference:** See `assets/FORMATTING_GUIDE.md` for detailed examples of all box types, color schemes, and common formatting patterns.

## Quality Standards

Ensure all generated hypotheses meet these standards:

- **Evidence-based:** Grounded in existing literature with citations
- **Testable:** Include specific, measurable predictions
- **Mechanistic:** Explain how/why, not just what
- **Comprehensive:** Consider alternative explanations
- **Rigorous:** Include experimental designs to test predictions

## Resources

### references/

- `hypothesis_quality_criteria.md` - Framework for evaluating hypothesis quality (testability, falsifiability, parsimony, explanatory power, scope, consistency)
- `experimental_design_patterns.md` - Common experimental approaches across domains (RCTs, observational studies, lab experiments, computational models)
- `literature_search_strategies.md` - Effective search techniques for PubMed and general scientific sources

### assets/

- `hypothesis_generation.sty` - LaTeX style package providing colored boxes, professional formatting, and custom environments for hypothesis reports
- `hypothesis_report_template.tex` - Complete LaTeX template with main text structure and comprehensive appendix sections
- `FORMATTING_GUIDE.md` - Quick reference guide with examples of all box types, color schemes, citation practices, and troubleshooting tips

### Related Skills

- **alterlab-literature-review** — for a standalone systematic review / PRISMA synthesis when the deliverable is the review itself rather than a focused search to ground hypotheses.
- **alterlab-venue-templates** — for venue-specific LaTeX templates and submission formatting when turning a hypothesis report into a manuscript.
- **alterlab-scientific-writing** — for drafting the resulting manuscript in flowing IMRAD prose.

Part of the AlterLab Academic Skills suite.
