---
name: alterlab-research-grants
description: Writes competitive research grant proposals for NSF, NIH, DOE, DARPA, and Taiwan NSTC — applies agency-specific formatting and current review criteria (NIH Simplified Review Framework, NSF Intellectual Merit and Broader Impacts under PAPPG 24-1), prepares budgets and justifications, drafts Specific Aims, broader-impacts, significance, and innovation narratives, and checks compliance, including funder rules on AI-assisted applications. Use when drafting or revising a grant proposal or resubmission, aligning it to an agency's review criteria, or preparing budgets, biosketches, and compliance sections. For Turkey's TÜBİTAK 1001/1002-A national proposals use alterlab-tubitak-proposal; for post-award progress or final reports (RPPR, NSF annual reports) use alterlab-grant-reporting; to critique someone else's proposal use alterlab-peer-review; for a journal manuscript use alterlab-scientific-writing. Part of the AlterLab Academic Skills suite.
allowed-tools: Read Write Edit Bash
license: MIT
compatibility: No external tools, API keys, or services required — ships no helper scripts and works from the Read/Write/Edit/Bash tools alone
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# Research Grant Writing

## Overview

Research grant writing is the process of developing competitive funding proposals for federal agencies and foundations. Master agency-specific requirements, review criteria, narrative structure, budget preparation, and compliance for NSF (National Science Foundation), NIH (National Institutes of Health), DOE (Department of Energy), DARPA (Defense Advanced Research Projects Agency), and Taiwan's NSTC (National Science and Technology Council) submissions.

**Core principle:** a grant is a persuasive document that has to demonstrate scientific rigor, innovation, feasibility, and broader impact at the same time. Each agency has distinct priorities, review criteria, formatting requirements, and strategic goals, and reviewers score against those — so write to the agency's criteria, not to a generic template.

## When to Use This Skill

This skill should be used when:
- Writing research proposals for NSF, NIH, DOE, DARPA, or NSTC programs
- Preparing project descriptions, specific aims, or technical narratives
- Developing broader impacts or significance statements
- Creating research timelines and milestone plans
- Preparing budget justifications and personnel allocation plans
- Responding to program solicitations or funding announcements
- Addressing reviewer comments in resubmissions
- Planning multi-institutional collaborative proposals
- Writing preliminary data or feasibility sections
- Preparing biosketches, CVs, or facilities descriptions

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| A TÜBİTAK 1001 or 1002-A proposal (özgün değer, yaygın etki, PBS submission) | `alterlab-tubitak-proposal` |
| Post-award deliverables: NIH RPPR, NSF annual/final or Project Outcomes Report, no-cost extension | `alterlab-grant-reporting` |
| Reviewing or critiquing someone else's proposal as a panelist | `alterlab-peer-review` |
| The FAIR data-sharing and repository content of a data management plan | `alterlab-open-science` |
| A recommendation or support letter for another applicant | `alterlab-recommendation-letters` |

## Current Funder Policies (verified 2026-09; re-check before each submission)

- **AI-assisted writing.** NIH will not consider applications "substantially developed by AI" (or containing sections that are) to be the applicants' original ideas; AI use detected after award can be referred to the Office of Research Integrity (NOT-OD-25-132, effective 25 Sept 2025). NSF encourages proposers to state in the project description whether and how generative AI was used and holds them responsible for accuracy, and PAPPG 24-1 Supplement 1 (NSF 26-200, effective 8 Dec 2025) extends research misconduct to acts committed with AI-based tools. So work with the PI's own aims, data, and ideas: structure, critique, tighten, and check compliance — do not generate a proposal wholesale for submission.
- **NIH application cap.** NIH accepts at most six new, renewal, resubmission, or revision applications per PI (including MPIs) per calendar year, excluding T activity codes and R13 (NOT-OD-25-132).
- **NIH peer review.** For most research project grants (R01, R21, R03, R15, R34, U01, and others) due on or after 25 Jan 2025, the Simplified Review Framework scores Factor 1 *Importance of the Research* (Significance + Innovation) and Factor 2 *Rigor and Feasibility* (Approach) on 1-9, and rates Factor 3 *Expertise and Resources* (Investigators + Environment) only as sufficient or not, alongside the Overall Impact score.
- **NIH forms and funding.** Biosketches and Current and Pending (Other) Support use the Common Forms generated and certified in SciENcv, with an ORCID iD linked to eRA Commons, for due dates on or after 25 Jan 2026 (NOT-OD-26-018). From the January 2026 council round NIH's Unified Funding Strategy stopped relying on paylines, so a percentile no longer maps to a published cutoff. The 2026 salary cap (Executive Level II) is $228,000.
- **NSF.** PAPPG NSF 24-1 remains in force (NSF deferred NSF 26-1), amended by Supplement 1 (8 Dec 2025) and Supplement 2 (22 Jan 2026). Biosketches and Current and Pending (Other) Support are prepared and certified in SciENcv; Synergistic Activities is a separate one-page document; a one-page Mentoring Plan is required when requesting support for postdoctoral scholars or graduate students; the Data Management and Sharing Plan (two pages) is created with the Research.gov DMSP tool. NSF's April 2025 priorities statement (updated July 2026) requires broadening-participation activities to be open to all Americans and not to preference some groups over others.

Details and sources are in `references/nih_guidelines.md` and `references/nsf_guidelines.md`.

## Visual Communication in Proposals

Well-chosen figures strengthen a proposal: a Gantt chart clarifies the timeline, a conceptual framework orients reviewers, and a workflow diagram makes methodology legible at a glance. Figures are optional — add them only where they genuinely improve clarity, and never pad a proposal with decorative graphics.

If a diagram or figure would aid comprehension, invoke the **alterlab-scientific-schematics** skill (diagrams/schematics) or the **alterlab-generate-image** skill (images). Figures are optional — add them only where they improve clarity.

**Where figures typically earn their space in a proposal:**
- Research methodology and workflow diagrams
- Project timeline Gantt charts
- Conceptual framework illustrations
- System architecture diagrams (for technical proposals)
- Experimental design flowcharts
- Preliminary data visualizations

---

## Agency Profiles (at a glance)

| Agency | Core structure | Primary review focus |
|--------|----------------|----------------------|
| **NSF** | 15-page project description; 1-page project summary | Intellectual Merit + Broader Impacts (both given full consideration) |
| **NIH** | 1-page Specific Aims + 12-page Research Strategy (R01) | Simplified framework: Importance of the Research, Rigor and Feasibility (scored); Expertise and Resources (sufficient/insufficient) |
| **DOE** | Project narrative; often cost-sharing | Technical merit, mission relevance, often national-lab collaboration |
| **DARPA** | Technical volume by phase; BAA-driven | DARPA-hard impact (Heilmeier Catechism), transition paths |
| **NSTC (Taiwan)** | CM03 form; bilingual abstract; architecture diagram | Innovation, Feasibility, PI Capability, Value |

Full agency profiles, complete review criteria, and award-mechanism catalogs (NSF CAREER/RAPID/EAGER;
NIH R01/R21/R35/F-series/K-series; DOE Office of Science/ARPA-E/EERE; DARPA YFA/offices) are in
`references/agency_profiles.md`. For binding requirements and formatting, use the per-agency guides:
`references/nsf_guidelines.md`, `references/nih_guidelines.md`, `references/doe_guidelines.md`,
`references/darpa_guidelines.md`, `references/nstc_guidelines.md`.

## Core Components of a Proposal

A competitive proposal assembles these ten components. Detailed purpose, length, essential elements,
and writing strategy for each — plus discipline-specific method guidance — are in
`references/proposal_components.md`.

1. **Executive Summary / Abstract** — standalone hook + significance + approach + impact.
2. **Project Description / Research Strategy** — the core technical narrative (structure varies by agency).
3. **Specific Aims / Objectives** — 2-4 testable, complementary goals (see `references/specific_aims_guide.md`).
4. **Broader Impacts / Significance** — societal/educational value; NSF gives it full consideration alongside Intellectual Merit (see `references/broader_impacts.md`).
5. **Innovation** — conceptual, methodological, integrative, translational, or scale novelty.
6. **Approach and Methods** — design, power, analysis, alternatives, rigor (see `references/research_methods.md`).
7. **Preliminary Data and Feasibility** — proof-of-concept that de-risks the proposal.
8. **Timeline, Milestones, Management** — phased plan with go/no-go points (see `references/timeline_planning.md`).
9. **Team Qualifications and Collaboration** — expertise, roles, biosketches, letters (see `references/team_building.md`).
10. **Budget and Justification** — categories, agency rules, line-item justification (see `references/budget_preparation.md`).

## Writing Craft, Mistakes, Resubmission, and Workflow

These cross-cutting topics are consolidated in `references/writing_and_workflow.md`:

- **Writing principles** — write for multiple audiences; the hook→problem→solution→evidence→impact→team
  persuasion arc; active voice and precise language; figure design; balancing innovation against risk;
  internal coherence (budget/timeline/team/aims must align).
- **Common mistakes** — conceptual, writing, technical, formatting, and strategic pitfalls to avoid.
- **Resubmission strategies** — NIH A1 introduction and NSF revision (see `references/resubmission_strategies.md`).
- **5-phase development workflow** — planning (2-6 mo out) → drafting → internal review → finalization →
  submission (submit 24-48 h early; never wait for the deadline).

## Reference Files

Load these as needed; the body above already cites each one at its point of use.

- `references/agency_profiles.md` — agency profiles, review criteria, award-mechanism catalogs (NSF/NIH/DOE/DARPA/NSTC)
- `references/proposal_components.md` — the ten core proposal components, with discipline-specific method guidance
- `references/writing_and_workflow.md` — writing principles, common mistakes, and the 5-phase development workflow
- Per-agency guides — `references/nsf_guidelines.md`, `nih_guidelines.md`, `doe_guidelines.md`, `darpa_guidelines.md`, `nstc_guidelines.md`
- Component deep-dives — `references/broader_impacts.md`, `specific_aims_guide.md`, `research_methods.md`, `budget_preparation.md`, `timeline_planning.md`, `team_building.md`, `resubmission_strategies.md`

## Templates and Assets

- `assets/nsf_project_summary_template.md`: NSF project summary structure
- `assets/nih_specific_aims_template.md`: NIH specific aims page template
- `assets/budget_justification_template.md`: Budget justification structure
- Agency-specific biosketch formats: see the per-agency guides in `references/` (`nsf_guidelines.md`, `nih_guidelines.md`, `doe_guidelines.md`, `darpa_guidelines.md`, `nstc_guidelines.md`) and `references/team_building.md`.

## Tasks and Tools

This skill ships no helper scripts; handle these tasks directly:

- **Compliance checking**: Verify formatting requirements (page limits, margins, fonts, required sections) against the relevant agency guide in `references/` (e.g. `references/nsf_guidelines.md`, `references/nih_guidelines.md`).
- **Budget calculation**: Build budgets with inflation escalation and fringe rates following `references/budget_preparation.md` and the `assets/budget_justification_template.md` structure.
- **Deadline tracking**: Track submission deadlines and milestones using the timeline/Gantt guidance in `references/timeline_planning.md`.

---

**Final Note**: Grant writing is both an art and a science. Success requires not only excellent research ideas but also clear communication, strategic positioning, and meticulous attention to detail. Start early, seek feedback, and remember that even the best researchers face rejection—persistence and revision are key to funding success.

Part of the AlterLab Academic Skills suite.


