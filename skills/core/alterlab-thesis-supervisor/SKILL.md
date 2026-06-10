---
name: alterlab-thesis-supervisor
description: "Supervises theses and dissertations end to end — structure guidance from proposal through defense, chapter-by-chapter writing support (introduction, literature review, methodology, results, discussion), supervision strategies, committee management, defense and viva voce preparation, timeline planning, feedback integration, examiner-expectation guidance, and formatting (APA 7, Chicago, university styles). Use when the request mentions thesis, dissertation, supervision, defense preparation, viva, proposal defense, thesis structure, thesis chapter, literature review chapter, methodology chapter, results chapter, discussion chapter, thesis timeline, committee, thesis formatting, or dissertation proposal. Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read Write Edit WebFetch WebSearch
compatibility: Uses built-in Claude tools only (Read/Write/Edit/WebFetch/WebSearch); no external API key or account required
metadata:
  skill-author: AlterLab
  version: "1.0.0"
  last_updated: "2026-03-18"
---

# Thesis Supervisor — Dissertation & Thesis Supervision Agent

A comprehensive thesis and dissertation supervision tool for faculty advisors and graduate students. Covers the full dissertation lifecycle from initial topic selection through successful defense, providing chapter-by-chapter guidance, supervision strategies, timeline management, and defense preparation.

## Overview

Supervising a thesis or dissertation is one of the most complex and consequential activities in academic life. This skill supports both supervisors and students through every stage of the process: defining a viable research question, structuring a proposal, writing each chapter to disciplinary standards, preparing for committee meetings and defenses, and navigating the human dimensions of the supervisory relationship.

The skill is designed to be discipline-flexible, with examples drawn from social sciences, humanities, STEM, and professional fields. Formatting guidance covers APA 7, Chicago/Turabian, and generic university styles.

## When to Use This Skill

This skill should be used when:
- Beginning thesis/dissertation topic exploration
- Writing a research proposal for committee approval
- Structuring any chapter of a thesis or dissertation
- Preparing for a proposal defense or final defense (viva voce)
- Managing the supervisor-student relationship
- Creating or adjusting a thesis timeline
- Giving feedback on student drafts
- Preparing students for committee meetings
- Troubleshooting common thesis problems (writer's block, scope creep, data issues)
- Teaching thesis writing seminars or workshops

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Writing a journal article (not thesis) | `alterlab-paper-writer` |
| Statistical analysis of thesis data | Data science skills |
| Literature search strategy | `alterlab-deep-research` |
| Survey/instrument design for thesis | `alterlab-survey-design` |

---

## Core Capabilities

### 1. Dissertation Structure Overview

**Standard Five-Chapter Model (Social Sciences, Education, Business):**

```
PROPOSAL (Chapters 1-3)
│
├── Chapter 1: Introduction
│   ├── Background and context
│   ├── Problem statement
│   ├── Purpose of the study
│   ├── Research questions (and hypotheses, if applicable)
│   ├── Significance of the study
│   ├── Scope and delimitations
│   ├── Definition of key terms
│   └── Organization of the dissertation
│
├── Chapter 2: Literature Review
│   ├── Introduction and search strategy
│   ├── Theoretical/conceptual framework
│   ├── Thematic review of literature
│   ├── Synthesis and identification of gaps
│   └── Summary and connection to research questions
│
├── Chapter 3: Methodology
│   ├── Research design and rationale
│   ├── Setting and context
│   ├── Population and sample
│   ├── Data collection methods and instruments
│   ├── Data analysis procedures
│   ├── Trustworthiness/validity and reliability
│   ├── Ethical considerations
│   ├── Researcher positionality (qualitative)
│   └── Limitations
│
COMPLETED AFTER DATA COLLECTION (Chapters 4-5)
│
├── Chapter 4: Results/Findings
│   ├── Data screening and preparation
│   ├── Participant/sample description
│   ├── Results organized by research question
│   ├── Tables and figures
│   └── Summary of findings
│
└── Chapter 5: Discussion and Conclusions
    ├── Summary of the study
    ├── Discussion of findings (connected to literature)
    ├── Implications (theoretical, practical, policy)
    ├── Limitations
    ├── Recommendations for future research
    └── Conclusion
```

**Alternative Structures by Discipline:**

| Discipline | Structure | Notes |
|-----------|-----------|-------|
| Social Sciences | 5-chapter model (above) | Most common for EdD, PhD in education, psychology, management |
| STEM (experimental) | Introduction, Literature Review, Methods, Results, Discussion (IMRaD variant) | May include multiple studies as separate chapters |
| Humanities | Introduction, literature/theory chapters (2-4), analysis chapters (2-4), conclusion | More flexible; argument-driven rather than question-driven |
| Three-paper model | Introduction, Paper 1, Paper 2, Paper 3, Conclusion | Each paper is publishable; increasingly popular in STEM and social sciences |
| Practice-based (professional doctorate) | Introduction, Literature Review, Methods, Findings, Action Plan/Recommendations | Emphasis on practical application |
| Creative arts | Creative work + exegesis (critical reflection) | Varies widely by institution |

### 2. Chapter-by-Chapter Guidance

#### Chapter 1: Introduction

**Purpose:** Establish the problem, justify the study, and frame the research questions.

**Section-by-Section Guide:**

```markdown
## Background and Context (1-3 pages)
- Start broad: What is the general area of concern?
- Narrow progressively: What specific aspect will you study?
- Use recent (last 5-10 years) citations to establish currency
- Establish that this is a real-world problem, not just an academic curiosity

## Problem Statement (1-2 paragraphs — the most critical paragraph in the dissertation)
The problem statement must:
- Identify a gap, conflict, or need in the literature or practice
- Be supported by evidence (citations to studies showing the gap)
- Be specific enough to study but significant enough to matter
- Connect logically to the research questions

FORMULA: "Despite [what we know], [what we don't know] remains unclear.
This gap is problematic because [consequences]. Therefore, this study
investigates [specific focus]."

## Purpose Statement (1 paragraph)
"The purpose of this [qualitative/quantitative/mixed methods] study is to
[verb: explore, examine, compare, describe] [what] among [whom] at [where]."

## Research Questions (bulleted list)
- Number them (RQ1, RQ2, RQ3)
- Align each with a specific method of analysis
- Quantitative: Include hypotheses (H1a, H1b, etc.)
- Qualitative: Open-ended, exploratory questions

## Significance of the Study (1-2 pages)
Three levels of significance:
1. Theoretical: How does this advance theory?
2. Practical: How does this help practitioners?
3. Methodological: Does this introduce a new approach?

## Scope and Delimitations
- Delimitations: Boundaries you chose (population, time frame, location)
- Do NOT confuse with limitations (weaknesses you acknowledge)

## Definition of Key Terms
- Define all technical terms, abbreviations, and concepts used in RQs
- Use operational definitions (how measured in YOUR study), not just dictionary definitions
```

**Common Chapter 1 Mistakes:**

| Mistake | Fix |
|---------|-----|
| Problem statement is too broad | Narrow to a specific, researchable gap with citations |
| Purpose statement does not match RQs | Ensure 1:1 alignment between purpose, RQs, and methods |
| Too much literature in Chapter 1 | Save detailed review for Chapter 2; Chapter 1 is a preview |
| Research questions are yes/no | Rewrite as open-ended (how, what, to what extent) |
| Missing significance | Articulate who cares and why — reviewers always check |

#### Chapter 2: Literature Review

**Purpose:** Situate your study within existing knowledge, identify gaps, and establish a theoretical framework.

**Literature Review Architecture:**

```
THEORETICAL/CONCEPTUAL FRAMEWORK
│   Present the theory or model that frames your study
│   Explain key constructs and relationships
│   Justify why this framework is appropriate
│   Show how your RQs map onto the framework
│
THEMATIC REVIEW
│
├── Theme 1: [Major topic related to your study]
│   ├── Subtheme 1a
│   ├── Subtheme 1b
│   └── Summary and connection to your study
│
├── Theme 2: [Major topic related to your study]
│   ├── Subtheme 2a
│   ├── Subtheme 2b
│   └── Summary and connection to your study
│
├── Theme 3: [Major topic related to your study]
│   ├── Subtheme 3a
│   ├── Subtheme 3b
│   └── Summary and connection to your study
│
GAP ANALYSIS AND SYNTHESIS
    Synthesize across themes
    Identify what is known, what is contested, what is unknown
    Connect the gap directly to your research questions
    "This study addresses this gap by..."
```

**Literature Review Quality Checklist:**

```markdown
## Quality Indicators

### Coverage
- [ ] Includes seminal works in the field
- [ ] Includes recent studies (last 5 years)
- [ ] Covers international perspectives (if relevant)
- [ ] Addresses conflicting findings

### Synthesis (not just summary)
- [ ] Groups studies by theme, not by author
- [ ] Compares and contrasts findings across studies
- [ ] Identifies patterns, contradictions, and gaps
- [ ] Critically evaluates methodological quality

### Organization
- [ ] Clear logical structure with transitions
- [ ] Each section builds toward the research questions
- [ ] Theoretical framework is well-integrated
- [ ] Chapter ends with a clear justification for the study

### Writing
- [ ] Uses reporting verbs appropriately (found, argued, demonstrated, claimed)
- [ ] Balances direct quotes with paraphrasing (prefer paraphrasing)
- [ ] Maintains the student's analytical voice (not just reporting others)
- [ ] Follows citation style consistently
```

#### Chapter 3: Methodology

**Purpose:** Describe your research design in sufficient detail that another researcher could replicate the study.

**Methodology Chapter Template:**

```markdown
## Research Design and Rationale
- Name and justify your approach (experimental, quasi-experimental,
  correlational, case study, phenomenological, etc.)
- Explain why this design answers your RQs
- Cite methodological authorities

## Setting and Context
- Describe the research site(s)
- Why this setting is appropriate

## Population and Sample
- Define the target population
- Describe sampling strategy and justify it
- Sample size: justify with power analysis (quantitative) or
  saturation rationale (qualitative)
- Inclusion/exclusion criteria

## Instrumentation
- For each instrument:
  - Name, author, year
  - What it measures
  - Number of items, response format, subscales
  - Published reliability (Cronbach's alpha)
  - Published validity evidence
  - Permission to use (if proprietary)
  - Any modifications you made (and why)
- For researcher-developed instruments:
  - Development process
  - Content validity evidence (expert review)
  - Pilot test results

## Data Collection Procedures
- Step-by-step chronological description
- IRB approval (protocol number)
- Informed consent process
- Timeline of data collection
- How data were recorded and stored

## Data Analysis
- For EACH research question:
  - RQ#: [Question text]
  - Analysis method: [Name]
  - Software: [Name and version]
  - Assumptions tested: [List]
  - Decision criteria: [Alpha level, effect size thresholds]
- For qualitative:
  - Coding approach (with citation: Braun & Clarke, Strauss & Corbin, etc.)
  - Phases of analysis
  - Software (NVivo, Atlas.ti, or manual)

## Trustworthiness / Validity and Reliability
- Quantitative: Internal validity threats and controls; external validity;
  reliability measures
- Qualitative: Credibility, transferability, dependability, confirmability
  (Lincoln & Guba); specific strategies used

## Ethical Considerations
- IRB approval details
- Informed consent
- Confidentiality/anonymity measures
- Data storage and destruction plan
- Researcher positionality (qualitative)

## Limitations
- Methodological limitations you acknowledge from the outset
- How you mitigate each limitation
```

#### Chapter 4: Results/Findings

**Purpose:** Present findings objectively, organized by research question.

**Results Chapter Structure:**

```markdown
## Data Preparation
- Response rate and dropout analysis
- Data screening (missing data, outliers, assumptions)
- Reliability of instruments with YOUR sample

## Participant Description
- Demographics table
- Comparison to target population (representativeness)

## Results by Research Question

### RQ1: [Question text]
[Analysis results — statistical tests, themes, or other findings]
[Tables and figures]
[Brief factual interpretation — what the data show, not what it means]

### RQ2: [Question text]
[Same structure]

### RQ3: [Question text]
[Same structure]

## Summary of Findings
- Brief recapitulation (no interpretation yet — save for Chapter 5)
- Table summarizing findings by RQ
```

**Results Presentation Guidelines:**

| Quantitative | Qualitative |
|-------------|------------|
| Report test statistic, df, p-value, effect size | Present themes with supporting quotes |
| Use tables for complex results | Use tables for theme summaries |
| Use figures for visual patterns | Use figures for thematic maps |
| Report exact p-values (not just p < .05) | Indicate how many participants endorsed each theme |
| Report confidence intervals where appropriate | Present disconfirming evidence |
| Follow APA tables/figures formatting | Use participant pseudonyms consistently |

#### Chapter 5: Discussion and Conclusions

**Purpose:** Interpret findings, connect to literature, and articulate contributions.

**Discussion Chapter Framework:**

```markdown
## Summary of the Study
- Brief recap: problem, purpose, method, key findings (1-2 pages)

## Discussion of Findings

### Finding 1: [Key finding related to RQ1]
- How does this finding relate to existing literature?
  - Consistent with: [Studies that found similar results — explain why]
  - Inconsistent with: [Studies that found different results — explain why]
- How does this finding relate to the theoretical framework?
- What might explain this finding?

### Finding 2: [Key finding related to RQ2]
[Same structure]

### Finding 3: [Key finding related to RQ3]
[Same structure]

## Implications

### Theoretical Implications
- How does this study advance theory?
- What modifications to existing theory do the findings suggest?

### Practical Implications
- What should practitioners do differently based on these findings?
- How can organizations, policymakers, or educators use these results?

### Methodological Implications (if applicable)
- What did this study contribute to research methods in the field?

## Limitations
- Be honest and specific
- Distinguish between limitations (weaknesses beyond your control) and
  delimitations (boundaries you chose)
- For each limitation, explain how it might affect interpretation

## Recommendations for Future Research
- Directly tied to your findings and limitations
- Specific and actionable (not "more research is needed")
- Example: "Future studies should examine this phenomenon in [different
  context/population] to test the transferability of these findings."

## Conclusion
- The final 1-2 paragraphs
- Restate the significance of the study
- End with the enduring takeaway — what should the reader remember?
```

### 3. Thesis Timeline Planning

**Typical PhD Timeline (4-6 years, social sciences):**

```
Year 1: Coursework + Topic Exploration
├── Semester 1: Core courses; identify broad area of interest
├── Semester 2: Methods courses; narrow topic; identify advisor
└── Summer: Preliminary literature review; draft topic statement

Year 2: Coursework + Proposal Development
├── Semester 1: Advanced courses; comprehensive/qualifying exams
├── Semester 2: Draft Chapters 1-3 (proposal)
└── Summer: Revise proposal; IRB application

Year 3: Proposal Defense + Data Collection
├── Semester 1: Proposal defense; begin data collection
├── Semester 2: Continue/complete data collection
└── Summer: Begin data analysis

Year 4: Analysis + Writing
├── Semester 1: Complete analysis; draft Chapter 4
├── Semester 2: Draft Chapter 5; revise all chapters
└── Summer: Defense preparation; submit to committee
```

**Master's Thesis Timeline (1-2 years):**

```
Semester 1
├── Month 1-2: Topic selection, advisor match, literature review begins
├── Month 3: Draft proposal outline; committee formation
└── Month 4: Proposal defense (or approval by advisor)

Semester 2
├── Month 5: IRB submission (if needed); data collection begins
├── Month 6-7: Data collection; begin analysis
└── Month 8: Complete analysis; draft results

Semester 3 (or end of Semester 2)
├── Month 9-10: Complete full draft; advisor review
├── Month 11: Revisions based on feedback; submit to committee
└── Month 12: Defense; final revisions; submit to graduate school
```

**Thesis Milestone Tracker:**

```markdown
## Thesis Timeline: [Student Name]

| Milestone | Target Date | Actual Date | Status | Notes |
|-----------|------------|-------------|--------|-------|
| Topic approved by advisor | [Date] | | [ ] | |
| Committee formed | [Date] | | [ ] | |
| Chapter 1 draft to advisor | [Date] | | [ ] | |
| Chapter 2 draft to advisor | [Date] | | [ ] | |
| Chapter 3 draft to advisor | [Date] | | [ ] | |
| Proposal to committee | [Date] | | [ ] | 2 weeks before defense |
| Proposal defense | [Date] | | [ ] | |
| IRB approval | [Date] | | [ ] | |
| Data collection complete | [Date] | | [ ] | |
| Chapter 4 draft to advisor | [Date] | | [ ] | |
| Chapter 5 draft to advisor | [Date] | | [ ] | |
| Full draft to committee | [Date] | | [ ] | 4 weeks before defense |
| Final defense | [Date] | | [ ] | |
| Revisions complete | [Date] | | [ ] | |
| Submit to graduate school | [Date] | | [ ] | Check formatting deadlines |
| Graduation | [Date] | | [ ] | |
```

### 4. Supervision Strategies

**Supervisory Meeting Structure:**

```markdown
## Meeting Agenda Template

### Pre-Meeting (Student Prepares)
- [ ] Submit written work 48+ hours before meeting
- [ ] Prepare 2-3 specific questions or decision points
- [ ] Update progress log since last meeting
- [ ] List any obstacles or concerns

### During Meeting (30-60 minutes)
1. Check-in (5 min): How are you doing? Any concerns?
2. Progress review (10 min): What has been accomplished since last meeting?
3. Discussion of submitted work (20-30 min): Feedback, questions, direction
4. Next steps (10 min): Clear action items with deadlines
5. Next meeting date confirmed

### Post-Meeting (Student Documents)
- [ ] Written summary of decisions and action items
- [ ] Shared with supervisor within 24 hours
- [ ] Filed in shared thesis folder
```

**Feedback Strategies for Supervisors:**

| Level of Draft | Feedback Focus | Approach |
|---------------|---------------|----------|
| Outline | Structure, logic, scope | "Is this the right story to tell?" Focus on architecture, not sentences. |
| First draft | Argument, evidence, gaps | "Does the argument work?" Focus on content and organization. Do NOT line-edit. |
| Second draft | Clarity, coherence, depth | "Is this clear and convincing?" Address paragraph-level issues. |
| Near-final draft | Polish, formatting, citations | "Is this ready for the committee?" Line-level editing now appropriate. |

**Difficult Supervision Conversations:**

| Situation | Approach |
|-----------|----------|
| Student is not making progress | "I've noticed that [specific observation]. What's getting in the way? How can I help?" |
| Draft quality is very poor | Focus on the most important 2-3 issues; do not overwhelm with a red ocean of tracked changes |
| Student wants to change topic mid-stream | Explore reasons; assess feasibility; help weigh costs vs. benefits; document the decision |
| Student disagrees with feedback | "Help me understand your reasoning. Let's look at what the literature says." |
| Student is struggling emotionally | Express concern; refer to counseling services; adjust timeline if needed; distinguish pastoral from academic role |
| Student is ready to defend but lacks confidence | Mock defense; emphasize strengths; normalize nervousness; remind them they are the world expert on their study |

### 5. Defense Preparation

#### Proposal Defense

**What Examiners Expect:**

```markdown
## Proposal Defense Checklist

### The Document
- [ ] Clear, researchable problem statement with evidence
- [ ] Research questions that are answerable with the proposed methods
- [ ] Comprehensive literature review that justifies the study
- [ ] Methodology that is detailed, appropriate, and feasible
- [ ] Realistic timeline and ethical approval plan

### The Presentation (15-20 minutes typically)
- [ ] Slide 1: Title, your name, committee members, date
- [ ] Slides 2-3: Background and problem statement
- [ ] Slide 4: Purpose and research questions
- [ ] Slide 5-6: Theoretical framework
- [ ] Slides 7-9: Key literature and gap
- [ ] Slides 10-13: Methodology (design, sample, data collection, analysis)
- [ ] Slide 14: Timeline
- [ ] Slide 15: Expected contributions
- [ ] Slide 16: References (selected)

### Common Proposal Defense Questions
1. "Why is this study needed? Who cares?"
2. "How does your theoretical framework inform your research questions?"
3. "Why did you choose [method] over [alternative]?"
4. "How will you ensure trustworthiness/validity?"
5. "What will you do if you cannot recruit enough participants?"
6. "What are the limitations of this design?"
7. "How does this contribute to the field?"
8. "What is your timeline, and is it realistic?"
```

#### Final Defense (Viva Voce)

**Preparation Protocol:**

```markdown
## Viva Voce Preparation (4-6 weeks before)

### Week 1-2: Re-Read and Reflect
- [ ] Re-read the entire dissertation critically
- [ ] Note any weaknesses you would challenge as a reviewer
- [ ] Prepare a 1-page summary of key contributions
- [ ] Identify the 3-5 most important findings

### Week 3: Anticipate Questions
- [ ] Prepare answers for common viva questions (see below)
- [ ] Prepare answers for discipline-specific methodological challenges
- [ ] Know your data inside out — expect questions about specific numbers/quotes
- [ ] Prepare a response for "What would you do differently?"

### Week 4: Practice
- [ ] Mock viva with supervisor (or peers)
- [ ] Practice explaining your study to a non-specialist in 5 minutes
- [ ] Practice answering "What is the main contribution?" in 2 sentences
- [ ] Time your presentation (if one is required)

### Week 5-6: Polish and Rest
- [ ] Prepare any visual aids
- [ ] Check all page references, table numbers, citation accuracy
- [ ] Prepare a printed copy with tabs for quick reference
- [ ] Get adequate rest the night before
```

**Common Viva Questions by Category:**

```markdown
## Opening Questions
- "Can you summarize your thesis in 5 minutes?"
- "What motivated you to study this topic?"
- "What is the main argument/contribution of your thesis?"

## Theoretical Questions
- "Why did you choose [framework]? What alternatives did you consider?"
- "How does [theory] inform your interpretation of the findings?"
- "Where does your work fit in the broader theoretical landscape?"

## Methodology Questions
- "Justify your choice of [qualitative/quantitative/mixed methods]."
- "How did you address [specific validity threat]?"
- "If you could redesign the study, what would you change?"
- "How do you respond to the limitation of [specific limitation]?"

## Findings Questions
- "Which finding surprised you the most? Why?"
- "How do you explain the discrepancy between your finding and [prior study]?"
- "What is the practical significance of [specific finding]?"

## Broader Questions
- "What are the implications for policy/practice?"
- "What would you recommend for future research?"
- "How would you turn this into journal publications?"
- "Where do you see this research going in the next 5 years?"

## Closing Questions
- "Is there anything you wish you had included?"
- "What would you tell a student beginning a similar project?"
- "What has this process taught you as a researcher?"
```

### 6. Formatting Requirements

**APA 7 Dissertation Formatting Essentials:**

```markdown
## APA 7 Formatting Checklist

### Page Layout
- [ ] 1-inch margins on all sides
- [ ] 12-point Times New Roman, 11-point Calibri, or 11-point Arial
- [ ] Double-spaced throughout (including references)
- [ ] Page numbers: Top right, starting from title page
- [ ] Running head: NOT required in student papers (APA 7 change)

### Headings (5 levels)
Level 1: Centered, Bold, Title Case
Level 2: Left-aligned, Bold, Title Case
Level 3: Left-aligned, Bold Italic, Title Case
Level 4: Indented, Bold, Title Case, Ending With a Period.
Level 5: Indented, Bold Italic, Title Case, Ending With a Period.

### Tables
- [ ] Table number (bold): Table 1
- [ ] Title (italic, title case): below table number
- [ ] Body: Single or 1.5-spaced within; horizontal lines for header and bottom only
- [ ] Note: Below table; General note, specific notes, probability notes

### Figures
- [ ] Figure number (bold): Figure 1
- [ ] Title (italic, title case): below figure number
- [ ] Legend within figure
- [ ] Note: Below figure

### Citations
- 1-2 authors: Always cite both names (Smith & Jones, 2024)
- 3+ authors: First author et al. (Smith et al., 2024) from first citation
- Direct quotes: Author, year, page number (Smith, 2024, p. 15)
- Block quotes: 40+ words, indented 0.5", no quotation marks

### Reference List
- Hanging indent (0.5")
- Alphabetical by first author's last name
- Include DOIs as https://doi.org/xxxxx
- Italicize journal names and volume numbers
```

**Chicago/Turabian Dissertation Formatting:**

```markdown
## Chicago/Turabian Key Differences from APA

### Citations: Two Systems
1. Notes-Bibliography (humanities): Footnotes/endnotes + bibliography
2. Author-Date (sciences): Parenthetical citations + reference list

### Notes-Bibliography Example
First citation (footnote):
  1. Jane Smith, Title of Book (Place: Publisher, 2024), 45.

Subsequent citations:
  2. Smith, Title of Book, 50.
  (or: Smith, 50. — if no ambiguity)

Bibliography entry:
  Smith, Jane. Title of Book. Place: Publisher, 2024.

### Formatting
- Margins: 1 inch (some universities require 1.5" left for binding)
- Font: Same as APA recommendations
- Spacing: Double-spaced text; single-spaced block quotes and footnotes
- Block quotes: 100+ words (Chicago) or 5+ lines; indented 0.5"
- Chapter titles: Begin on new page, 2 inches from top
```

---

## Best Practices

1. **Establish expectations early.** At the first meeting, discuss communication frequency, feedback turnaround times, draft submission expectations, and working styles. Put it in writing.

2. **Require written work at every meeting.** Meetings without written deliverables become unproductive check-ins. Even a one-page outline moves the thesis forward more than a conversation.

3. **Give feedback at the right level for the right stage.** Do not copy-edit a first draft. Do not give structural feedback on a near-final draft. Match your feedback to the draft's maturity.

4. **Protect the student's ownership.** The thesis is the student's work, not yours. Guide and challenge, but do not dictate. The student must be able to defend every decision in the viva.

5. **Front-load the methodology.** The methodology chapter is where most students struggle and most proposals fail. Invest disproportionate time getting Chapter 3 right before data collection.

6. **Build in buffer time.** Every thesis timeline should include contingency time for illness, data collection delays, committee scheduling, and revision cycles. Add 20-30% to estimated timelines.

7. **Normalize difficulty.** Writing a thesis is hard. Periods of frustration, confusion, and self-doubt are normal. Acknowledge this and help students develop coping strategies.

8. **Connect chapters with threads.** Each chapter should explicitly link to the research questions and to adjacent chapters. The thesis is one coherent argument, not five separate papers.

9. **Practice the defense.** No student should walk into a defense without at least one mock defense. Practice reduces anxiety and reveals gaps in argumentation.

10. **Celebrate milestones.** Acknowledge completed chapters, successful proposal defenses, and the final defense. The journey is long; recognition sustains motivation.

---

## Common Pitfalls

| Pitfall | Why It Happens | How to Avoid |
|---------|---------------|--------------|
| Scope creep | Student keeps adding research questions or variables | Lock research questions at proposal defense; resist expansion |
| Literature review never ends | Student keeps finding new sources | Set a deadline; focus on saturation of key themes, not exhaustiveness |
| Methods chapter too vague | Student has not yet grasped the details of their chosen approach | Require students to work through a methods textbook chapter-by-chapter |
| Results chapter interprets findings | Student mixes results with discussion | Enforce the rule: Chapter 4 reports what you found; Chapter 5 says what it means |
| Discussion chapter re-summarizes results | Student does not know how to interpret | Require explicit connection to literature for every major finding |
| Inconsistent formatting | Student writes over months/years with changing habits | Use a template from day one; format check before each submission |
| Committee surprises at defense | Committee members have not read the full document | Send the complete document 4+ weeks in advance; follow up to confirm receipt |
| Student disappears | Life events, mental health, loss of motivation | Regular scheduled meetings (even brief); early intervention when pattern breaks |
| Advisor rewrites instead of guides | Frustration with slow progress | Ask questions instead of providing answers; use margin comments, not rewriting |
| Timeline pressure leads to poor work | External deadlines (funding, visa, job) | Plan realistically from the start; discuss timeline pressures openly |

---

## References

- Bolker, J. (1998). *Writing your dissertation in fifteen minutes a day: A guide to starting, revising, and finishing your doctoral thesis*. Holt.
- Dunleavy, P. (2003). *Authoring a PhD: How to plan, draft, write, and finish a doctoral thesis or dissertation*. Palgrave Macmillan.
- Murray, R. (2011). *How to write a thesis* (3rd ed.). Open University Press.
- Paltridge, B., & Starfield, S. (2020). *Thesis and dissertation writing in a second language: A handbook for students and their supervisors* (2nd ed.). Routledge.
- Roberts, C. M. (2010). *The dissertation journey: A practical and comprehensive guide to planning, writing, and defending your dissertation* (2nd ed.). Corwin.
- Turabian, K. L. (2018). *A manual for writers of research papers, theses, and dissertations* (9th ed.). University of Chicago Press.
- Wisker, G. (2012). *The good supervisor: Supervising postgraduate and undergraduate research for doctoral theses and dissertations* (2nd ed.). Palgrave Macmillan.

See also: `references/thesis-guidelines.md` for expanded formatting and process details.
