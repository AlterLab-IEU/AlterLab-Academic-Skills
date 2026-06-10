---
name: alterlab-teaching-design
description: "Designs courses and teaching materials using backward design (Wiggins & McTighe), constructive alignment (Biggs), and Bloom's taxonomy alignment, generating rubrics, formative and summative assessments, syllabi, lesson plans, inclusive-pedagogy guidance, and online/hybrid course architecture. Use when the request mentions course design, syllabus, learning outcomes, rubric, assessment design, lesson plan, backward design, constructive alignment, Bloom's taxonomy, curriculum mapping, course redesign, inclusive pedagogy, hybrid course, or online course design. Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read Write Edit Bash WebFetch WebSearch
compatibility: Uses built-in Claude tools only (Read/Write/Edit/Bash/WebFetch/WebSearch); no external API key or account required
metadata:
  skill-author: AlterLab
  version: "1.0.0"
  last_updated: "2026-03-18"
---

# Teaching Design — Course & Curriculum Design Agent

A comprehensive teaching design tool for faculty at all career stages. Covers the full course design lifecycle: from articulating learning outcomes through backward design, to constructing aligned assessments, building rubrics, drafting syllabi, and planning individual lessons. Supports face-to-face, online, and hybrid modalities with inclusive pedagogy principles throughout.

## Overview

Teaching design is the systematic process of creating educational experiences that lead to measurable learning. This skill guides faculty through evidence-based frameworks for course design, helping transform disciplinary expertise into effective, equitable, and engaging learning experiences.

The skill integrates three foundational frameworks:
1. **Backward Design** (Wiggins & McTighe, 2005) — Start with desired results, then determine acceptable evidence, then plan learning experiences
2. **Constructive Alignment** (Biggs & Tang, 2011) — Align intended learning outcomes, teaching/learning activities, and assessment tasks
3. **Bloom's Revised Taxonomy** (Anderson & Krathwohl, 2001) — Classify cognitive complexity of learning outcomes across six levels

## When to Use This Skill

This skill should be used when:
- Designing a new course from scratch
- Redesigning or revising an existing course
- Writing or refining learning outcomes and objectives
- Creating assessment instruments (exams, projects, portfolios)
- Building rubrics for grading consistency
- Drafting or updating a course syllabus
- Planning individual class sessions or lesson sequences
- Transitioning a face-to-face course to online or hybrid format
- Conducting curriculum mapping across a program
- Implementing inclusive and accessible pedagogy
- Preparing for course accreditation reviews
- Mentoring junior faculty on teaching practices

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Writing an academic paper | `alterlab-paper-writer` |
| Reviewing a research paper | `alterlab-paper-reviewer` |
| Statistical analysis of student/grade data | a `data-science/` skill (e.g. `alterlab-statistical-analysis`) |
| Creating presentation slides | `alterlab-pptx-posters` |

---

## Core Capabilities

### 1. Learning Outcome Design with Bloom's Taxonomy

Learning outcomes are the foundation of all course design. Every outcome should be specific, measurable, and aligned to an appropriate cognitive level.

**Bloom's Revised Taxonomy — Six Cognitive Levels:**

| Level | Category | Key Verbs | Example Outcome |
|-------|----------|-----------|-----------------|
| 1 | Remember | Define, list, recall, identify, name | List the five principles of effective survey design |
| 2 | Understand | Explain, summarize, paraphrase, classify | Explain the difference between formative and summative assessment |
| 3 | Apply | Implement, use, execute, demonstrate | Apply backward design to create a course module |
| 4 | Analyze | Differentiate, organize, compare, deconstruct | Analyze alignment between outcomes, activities, and assessments in a syllabus |
| 5 | Evaluate | Judge, critique, justify, appraise | Evaluate the validity of a rubric using inter-rater reliability data |
| 6 | Create | Design, construct, produce, formulate | Design an inclusive assessment strategy for a hybrid graduate seminar |

**ABCD Framework for Writing Outcomes:**

```
A — Audience:    Who is the learner? (e.g., "By the end of this course, students will...")
B — Behavior:    What will they do? (Use observable, measurable verbs)
C — Condition:   Under what conditions? (e.g., "Given a dataset...", "Without references...")
D — Degree:      To what standard? (e.g., "with 80% accuracy", "meeting APA 7 standards")
```

**Example — Well-Written vs. Poorly Written Outcomes:**

```
POOR:   "Students will understand research ethics."
         (Problem: "understand" is not observable or measurable)

BETTER: "Students will identify three ethical violations in a given research scenario
         and propose corrections consistent with the Belmont Report principles."
         (A: Students, B: identify and propose, C: given a scenario, D: consistent with Belmont)
```

**Outcome Mapping Template:**

```markdown
## Course: [Title]
## Program Learning Outcome Alignment

| Course Learning Outcome | Bloom's Level | Program Outcome | Assessment Method | Week(s) |
|------------------------|---------------|-----------------|-------------------|---------|
| CLO1: [outcome text]   | Apply (3)     | PLO2            | Project Phase 1   | 4-6     |
| CLO2: [outcome text]   | Analyze (4)   | PLO3            | Case Study Report | 8-10    |
| CLO3: [outcome text]   | Evaluate (5)  | PLO5            | Peer Review       | 12-14   |
| CLO4: [outcome text]   | Create (6)    | PLO1, PLO4      | Final Portfolio   | 15-16   |
```

### 2. Backward Design Process

Backward design inverts the traditional approach of starting with content and ending with a test. Instead, it begins with the end in mind.

**Stage 1 — Identify Desired Results**

Ask:
- What should students know, understand, and be able to do?
- What enduring understandings should they retain years later?
- What essential questions will guide inquiry?

```markdown
## Desired Results Template

### Established Goals
- [Institutional/program goals this course addresses]

### Enduring Understandings
Students will understand that...
1. [Big idea that transcends the course]
2. [Transferable principle]

### Essential Questions
1. [Open-ended question that provokes deep thinking]
2. [Question that recurs throughout the course]

### Knowledge and Skills
Students will know...              Students will be able to...
- [Key facts/concepts]             - [Key skills/processes]
- [Vocabulary/definitions]         - [Procedures/techniques]
```

**Stage 2 — Determine Acceptable Evidence**

Ask:
- How will I know students have achieved the outcomes?
- What performances or products will demonstrate understanding?
- What criteria distinguish levels of quality?

```markdown
## Evidence Plan

| Learning Outcome | Assessment Type | Format | Weight | Timing |
|-----------------|-----------------|--------|--------|--------|
| CLO1            | Summative       | Research proposal | 25% | Week 8 |
| CLO2            | Formative       | Weekly reflections | 10% | Ongoing |
| CLO3            | Summative       | Peer review exercise | 20% | Week 12 |
| CLO4            | Summative       | Final portfolio | 35% | Week 16 |
| CLO1-4          | Formative       | In-class activities | 10% | Ongoing |
```

**Stage 3 — Plan Learning Experiences (WHERETO)**

```
W — Where is the course headed? Help students see the big picture.
H — Hook students early. Engage curiosity with a provocative question or problem.
E — Equip students with knowledge, skills, and tools.
R — Rethink. Provide opportunities to revise and reflect.
E — Evaluate. Let students self-assess and get feedback.
T — Tailor. Differentiate for diverse learners.
O — Organize. Sequence for maximum coherence and engagement.
```

### 3. Constructive Alignment

Constructive alignment (Biggs & Tang, 2011) ensures that what you teach, how you teach it, and how you assess it are all pointing in the same direction.

**Alignment Audit Template:**

```markdown
## Alignment Check

| Learning Outcome | Teaching/Learning Activity | Assessment Task | Aligned? |
|-----------------|---------------------------|-----------------|----------|
| CLO1: Analyze... | Case study discussions, worked examples | Case analysis report | Yes |
| CLO2: Create... | Lectures only | Multiple-choice exam | NO — misaligned |
```

**Common Misalignment Patterns:**

| Problem | Symptom | Fix |
|---------|---------|-----|
| Outcome says "create" but assessment is MCQ | Students memorize instead of producing | Replace with project-based assessment |
| Activities are passive but outcome requires application | Students cannot transfer to new contexts | Add active learning: problem sets, simulations |
| High-level outcomes but only low-level activities | Students plateau at remember/understand | Scaffold activities up Bloom's levels progressively |
| Assessment tests content not in outcomes | Students feel blindsided; grade disputes | Map every assessment item to a specific CLO |

### 4. Assessment Design

#### Formative Assessment (Assessment FOR Learning)

Purpose: Monitor learning in progress, provide feedback, adjust teaching.

**Techniques by Class Size:**

| Technique | Small (<30) | Medium (30-100) | Large (100+) | Digital? |
|-----------|-------------|-----------------|--------------|----------|
| Muddiest Point | Write on cards | Poll Everywhere | LMS poll | Yes |
| Think-Pair-Share | Verbal | With microphone | With clickers | Optional |
| Concept Maps | Paper, share in groups | Digital (Miro) | LMS submission | Yes |
| One-Minute Paper | End of class | End of class | LMS auto-collect | Yes |
| Exit Tickets | Paper slips | Google Form | LMS quiz | Yes |
| Peer Instruction | Clickers + discussion | Clickers + discussion | Clickers + discussion | Yes |
| Draft Submissions | Written feedback | Rubric + comments | Peer review + spot-check | Yes |

#### Summative Assessment (Assessment OF Learning)

Purpose: Evaluate achievement at the end of a learning period.

**Assessment Type Selection Guide:**

```
Does the outcome require PRODUCTION of an artifact?
├── Yes → Project, portfolio, paper, presentation, design
│         Does it require COLLABORATION?
│         ├── Yes → Group project with individual accountability
│         └── No  → Individual project with milestones
└── No  → Does the outcome require PERFORMANCE in real-time?
          ├── Yes → Oral exam, demonstration, simulation, practicum
          └── No  → Does it require ANALYSIS or JUDGMENT?
                    ├── Yes → Case study, essay, critique, problem set
                    └── No  → Selected-response (MCQ, matching, T/F)
                              Use ONLY for Remember/Understand outcomes
```

**Exam Blueprint Template:**

```markdown
## Exam Blueprint: [Course] Midterm

| Topic | Weight | CLO | Bloom's Level | # Items | Item Type |
|-------|--------|-----|---------------|---------|-----------|
| Topic A | 25% | CLO1 | Remember (1) | 10 | MCQ |
| Topic B | 30% | CLO2 | Apply (3) | 3 | Short answer |
| Topic C | 25% | CLO3 | Analyze (4) | 2 | Case analysis |
| Topic D | 20% | CLO4 | Evaluate (5) | 1 | Essay |
| **Total** | **100%** | | | **16** | |
```

### 5. Rubric Design

Rubrics communicate expectations and ensure grading consistency.

**Analytic Rubric Template:**

```markdown
## Rubric: [Assignment Name]

| Criterion (Weight) | Exemplary (4) | Proficient (3) | Developing (2) | Beginning (1) |
|--------------------|---------------|-----------------|-----------------|----------------|
| Thesis/Argument (30%) | Original, nuanced argument with clear position; anticipates counterarguments | Clear argument with identifiable position; acknowledges alternatives | Argument present but vague or inconsistent; limited engagement with alternatives | No clear argument; position unclear or absent |
| Evidence Use (25%) | Integrates 5+ scholarly sources; evidence directly supports claims; synthesizes across sources | Uses 3-4 scholarly sources; evidence supports most claims | Uses 1-2 sources or relies on non-scholarly sources; evidence loosely connected | No evidence or evidence does not support claims |
| Analysis (25%) | Deep analysis connecting evidence to argument; identifies implications and limitations | Adequate analysis; connects evidence to argument | Surface-level analysis; describes rather than analyzes | No analysis; summary only |
| Writing Quality (20%) | Clear, precise, professional prose; no errors; appropriate disciplinary register | Generally clear writing; minor errors; appropriate tone | Unclear in places; multiple errors; inconsistent tone | Difficult to follow; pervasive errors |
```

**Holistic Rubric Template (for quick grading):**

```markdown
| Score | Description |
|-------|-------------|
| A (90-100) | Exceeds expectations. Demonstrates mastery of all learning outcomes. Work is original, well-supported, and professionally presented. |
| B (80-89) | Meets expectations. Demonstrates competence across all outcomes. Work is solid with minor areas for improvement. |
| C (70-79) | Approaches expectations. Demonstrates partial competence. Significant areas need development. |
| D (60-69) | Below expectations. Demonstrates limited competence. Major revisions needed. |
| F (<60) | Does not meet expectations. Fails to demonstrate competence in core outcomes. |
```

**Single-Point Rubric (for feedback-rich contexts):**

```markdown
| Areas for Growth | Criterion | Evidence of Excellence |
|-----------------|-----------|----------------------|
| [Specific feedback] | **Clear research question** — The paper articulates a focused, researchable question appropriate to the discipline | [Specific feedback] |
| [Specific feedback] | **Methodological rigor** — Methods are appropriate, clearly described, and reproducible | [Specific feedback] |
| [Specific feedback] | **Critical analysis** — Findings are interpreted with nuance, connected to literature, and limitations acknowledged | [Specific feedback] |
```

### 6. Syllabus Design

A syllabus serves as a learning contract, a course map, and a motivational document.

**Essential Syllabus Components:**

```markdown
## [Course Code]: [Course Title]
### [Semester, Year] | [Meeting Pattern] | [Location/Modality]

### Instructor Information
- Name, title, pronouns
- Office location and hours (in-person and virtual)
- Email and response time policy
- Preferred contact method

### Course Description
[Catalog description + your expanded context for why this course matters]

### Learning Outcomes
By the end of this course, students will be able to:
1. [CLO1 — verb + content + condition + standard]
2. [CLO2]
3. [CLO3]
4. [CLO4]

### Required Materials
- [Textbook with ISBN, edition, and whether earlier editions work]
- [Software with free/paid status and alternatives]
- [Access codes — with cost and duration]

### Assessment and Grading

| Component | Weight | Due | CLO Addressed |
|-----------|--------|-----|---------------|
| Participation & in-class activities | 10% | Ongoing | CLO1-4 |
| Reading responses (10 x 2%) | 20% | Weekly | CLO1, CLO2 |
| Midterm project | 25% | Week 8 | CLO1, CLO3 |
| Final portfolio | 35% | Finals week | CLO2, CLO4 |
| Peer review contributions | 10% | Weeks 6, 12 | CLO3 |

### Grading Scale
[Institution-specific scale]

### Course Policies
- Attendance and participation
- Late work policy (with grace provisions)
- Academic integrity statement
- Technology policy
- Communication expectations

### Accessibility Statement
[Institution's disability services information]
[Your commitment to accommodations]
[How to request accommodations]

### Diversity and Inclusion Statement
[Your commitment to inclusive learning]

### Weekly Schedule
| Week | Topic | Readings | Due |
|------|-------|----------|-----|
| 1 | Introduction and course overview | Ch. 1 | — |
| 2 | [Topic] | [Readings] | Reading Response 1 |
| ... | ... | ... | ... |
```

### 7. Lesson Plan Design

**Single Session Lesson Plan Template:**

```markdown
## Lesson Plan: [Topic]
### Course: [Code] | Date: [Date] | Duration: [Minutes]

### Learning Objectives (session-level)
By the end of this session, students will be able to:
1. [Objective aligned to CLO]
2. [Objective aligned to CLO]

### Pre-Class Preparation
- Students: [Reading, video, pre-quiz]
- Instructor: [Materials, slides, handouts, tech setup]

### Session Flow

| Time | Activity | Purpose | Materials |
|------|----------|---------|-----------|
| 0:00-0:10 | Opening hook: [provocative question, demo, news item] | Engage, activate prior knowledge | Slides 1-3 |
| 0:10-0:25 | Mini-lecture: [key concept] | Equip with foundational knowledge | Slides 4-12 |
| 0:25-0:45 | Active learning: [think-pair-share, case analysis, problem set] | Apply and practice | Handout A |
| 0:45-0:55 | Whole-class debrief and synthesis | Consolidate understanding | Whiteboard |
| 0:55-1:00 | Closing: muddiest point + preview next session | Assess and bridge | Exit ticket |

### Contingency Plan
- If discussion stalls: [backup prompt or activity]
- If activity finishes early: [extension question]
- If technology fails: [analog backup]

### Post-Session Reflection
- What worked well?
- What would I change?
- What do students still struggle with?
```

### 8. Online and Hybrid Course Design

**Modality Comparison:**

| Feature | Face-to-Face | Hybrid/Blended | Fully Online (Sync) | Fully Online (Async) |
|---------|-------------|----------------|---------------------|---------------------|
| Interaction | Real-time, in-person | Mix of in-person and online | Real-time via video | Discussion boards, email |
| Flexibility | Low (fixed time/place) | Medium | Medium (fixed time) | High (any time) |
| Community building | Natural | Requires intentional design | Possible with effort | Challenging |
| Technology dependence | Low | Medium | High | High |
| Best for | Labs, discussions, performances | Blending lecture and application | Geographically distributed cohorts | Working professionals |

**Community of Inquiry Framework (Garrison, Anderson, Archer):**

```
                    ┌─────────────────────┐
                    │   EDUCATIONAL        │
                    │   EXPERIENCE         │
                    │                      │
           ┌───────┤  Setting Climate     ├───────┐
           │       │  Supporting Discourse │       │
           │       │  Selecting Content    │       │
           │       └──────────┬───────────┘       │
           │                  │                    │
    ┌──────▼──────┐   ┌──────▼──────┐   ┌────────▼────────┐
    │   SOCIAL    │   │  COGNITIVE  │   │    TEACHING      │
    │  PRESENCE   │   │  PRESENCE   │   │    PRESENCE      │
    │             │   │             │   │                   │
    │ Open comm.  │   │ Triggering  │   │ Design &         │
    │ Group       │   │ Exploration │   │   organization   │
    │  cohesion   │   │ Integration │   │ Facilitating     │
    │ Affective   │   │ Resolution  │   │   discourse      │
    │  expression │   │             │   │ Direct           │
    │             │   │             │   │   instruction    │
    └─────────────┘   └─────────────┘   └─────────────────┘
```

**Online Module Design Checklist:**

```markdown
## Module [N]: [Title]

### Before the Module
- [ ] Learning objectives clearly stated
- [ ] Connection to prior module explicit
- [ ] All materials accessible (captioned videos, alt text, screen-reader compatible PDFs)
- [ ] Estimated time to complete provided

### Content Delivery
- [ ] Video lectures chunked into segments of 6-12 minutes
- [ ] Transcripts and/or closed captions available
- [ ] Key readings provided with guiding questions
- [ ] Interactive elements embedded (H5P, embedded quizzes)

### Active Learning
- [ ] Discussion prompt requires application, not summary
- [ ] Peer interaction required (reply to 2 classmates with substantive feedback)
- [ ] Practice activity with immediate feedback (auto-graded quiz, simulation)

### Assessment
- [ ] Aligned to module learning objectives
- [ ] Rubric published before assignment opens
- [ ] Submission method clear (file type, naming convention, LMS upload)
- [ ] Deadline and late policy stated

### Instructor Presence
- [ ] Announcement or video introduction to the module
- [ ] Discussion facilitation plan (when and how often to post)
- [ ] Feedback turnaround time communicated
```

### 9. Inclusive Pedagogy

Inclusive teaching ensures that all students, regardless of background, identity, ability, or prior preparation, have equitable opportunities to learn.

**Universal Design for Learning (UDL) — Three Principles:**

| Principle | Guideline | Implementation Examples |
|-----------|-----------|----------------------|
| **Multiple Means of Engagement** (the WHY of learning) | Provide options for self-regulation, sustaining effort, and recruiting interest | Choice in assignment topics; varied assessment formats; relevance to diverse experiences |
| **Multiple Means of Representation** (the WHAT of learning) | Provide options for perception, language/symbols, and comprehension | Videos with captions; diagrams with alt text; glossaries; multiple examples from different contexts |
| **Multiple Means of Action & Expression** (the HOW of learning) | Provide options for physical action, expression/communication, and executive function | Write or record; individual or group; scaffolded milestones; flexible deadlines with structure |

**Inclusive Assessment Strategies:**

- Offer assessment menus: "Choose 3 of 5 options to demonstrate CLO2"
- Use specifications grading to reduce bias in subjective evaluation
- Provide exemplars of strong, adequate, and weak work
- Allow revision and resubmission on major assignments
- Build in low-stakes practice before high-stakes assessments
- Ensure exam questions do not rely on culturally specific knowledge unrelated to the learning outcome

**Addressing Diverse Prior Knowledge:**

```
Pre-assessment at course start
├── Diagnostic quiz (not graded) → Identify prerequisite gaps
├── Background knowledge survey → Understand student contexts
└── Skills inventory → Map incoming competencies

Differentiated support
├── Remedial resources for students below threshold
├── Challenge extensions for advanced students
└── Flexible pathways through core content
```

### 10. Curriculum Mapping

Curriculum mapping ensures coherence across an entire program of study.

**Program-Level Mapping Template:**

```markdown
## Program: [Degree Name]
## Program Learning Outcomes (PLOs)

| PLO | Description | Introduced (I) | Reinforced (R) | Mastered (M) |
|-----|-------------|-----------------|-----------------|----------------|
| PLO1 | [Description] | COURSE101 | COURSE201, COURSE301 | COURSE401 |
| PLO2 | [Description] | COURSE102 | COURSE202 | COURSE302, COURSE402 |
| PLO3 | [Description] | COURSE101 | COURSE301 | COURSE401 |

## Gap Analysis
- PLO4 is only addressed in one course — add reinforcement opportunity
- No course provides mastery-level assessment for PLO2 — revise capstone
- COURSE203 does not map to any PLO — justify or redesign
```

---

## Best Practices

1. **Start with outcomes, not content.** Content is a means to an outcome, not the goal itself. Resist the urge to design around topics you want to cover.

2. **Align everything.** Use the alignment audit template regularly. If an assessment does not map to an outcome, either the assessment or the outcome is wrong.

3. **Use formative assessment frequently.** Do not wait until the midterm to discover students are lost. Check understanding every session.

4. **Design for the margins.** When you design for students with the greatest barriers (disability, language, prior knowledge gaps), you improve learning for everyone (curb-cut effect).

5. **Scaffold complexity.** Do not jump from Remember to Create. Build through Bloom's levels progressively across the semester.

6. **Make the implicit explicit.** State expectations clearly. Provide rubrics before assignments. Explain why activities matter. Share the course design rationale with students.

7. **Iterate based on evidence.** Use student feedback, grade distributions, and your own reflections to revise. Teaching design is never finished.

8. **Balance workload.** Use a course workload estimator to ensure total student hours are reasonable (rule of thumb: 2-3 hours outside class per credit hour per week).

9. **Build community.** Learning is social. Design activities that require meaningful interaction, not just parallel work.

10. **Document your design.** Keep a course design portfolio for tenure review, accreditation, and sharing with colleagues.

---

## Common Pitfalls

| Pitfall | Why It Happens | How to Avoid |
|---------|---------------|--------------|
| Content overload | Faculty try to cover everything they know | Prioritize with backward design — cut what does not serve outcomes |
| Assessment pileup | Assignments accumulate without coordination | Map all due dates on a semester calendar; coordinate with colleagues |
| Misaligned assessments | Assessments inherited from previous instructor | Audit alignment annually; redesign assessments to match your outcomes |
| Vague rubrics | Written in a hurry without calibration | Pilot rubrics with colleagues; use student work samples to test criteria |
| Inaccessible materials | Default to PDF scans, image-heavy slides | Check accessibility before posting; use LMS accessibility checker |
| Ignoring student feedback | "Students don't know what's good for them" | Distinguish preference feedback from learning feedback; act on patterns |
| One-size-fits-all design | Single modality, single assessment type | Apply UDL principles; offer choices where possible |
| No low-stakes practice | Students' first attempt is the graded one | Add ungraded or low-weight practice before every major assessment |
| Isolation in design | Designing alone without peer input | Participate in teaching communities; invite a colleague to review your syllabus |

---

## References

- Anderson, L. W., & Krathwohl, D. R. (Eds.). (2001). *A taxonomy for learning, teaching, and assessing: A revision of Bloom's taxonomy of educational objectives*. Longman.
- Biggs, J., & Tang, C. (2011). *Teaching for quality learning at university* (4th ed.). Open University Press.
- Fink, L. D. (2013). *Creating significant learning experiences: An integrated approach to designing college courses* (2nd ed.). Jossey-Bass.
- Garrison, D. R., Anderson, T., & Archer, W. (2000). Critical inquiry in a text-based environment: Computer conferencing in higher education. *The Internet and Higher Education*, 2(2-3), 87-105.
- Meyer, A., Rose, D. H., & Gordon, D. (2014). *Universal design for learning: Theory and practice*. CAST Professional Publishing.
- Nilson, L. B. (2016). *Teaching at its best: A research-based resource for college instructors* (4th ed.). Jossey-Bass.
- Wiggins, G., & McTighe, J. (2005). *Understanding by design* (2nd ed.). ASCD.

See also: `references/teaching-frameworks.md` for expanded framework details.
