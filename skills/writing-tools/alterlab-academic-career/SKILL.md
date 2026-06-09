---
name: alterlab-academic-career
description: "Prepares academic career documents and professional-development materials for faculty and researchers. Use when drafting academic CVs, research statements, teaching philosophies, diversity statements, faculty-position cover letters, tenure dossiers, promotion narratives, academic portfolios, or mentorship statements, and when planning conference-networking strategy, building academic web presence, setting up ORCID profiles, or understanding impact metrics. Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read Write Edit
compatibility: No external tools, API keys, or services required — produces documents from the Read/Write/Edit tools alone
metadata:
  skill-author: AlterLab
  version: "1.0.1"
  last_updated: "2026-06-09"
---

# Academic Career Documents and Professional Development

## Overview

Academic career advancement depends on a portfolio of carefully crafted documents that communicate scholarly identity, research vision, teaching effectiveness, and service commitment. Unlike industry resumes that emphasize brevity and skills keywords, academic career documents are comprehensive narratives that position a scholar within their discipline, articulate the significance of their contributions, and demonstrate alignment with institutional missions. This skill covers the full lifecycle of academic career documents — from the first job application through tenure and promotion — along with professional development strategies for building visibility, networks, and impact.

The academic job market operates on distinct norms: CVs can be 20+ pages, statements are read by committees with diverse disciplinary expertise, and evaluation criteria vary dramatically across institution types (R1, SLAC, community college, professional school). Mastering these documents is not about self-promotion but about clearly communicating the significance, trajectory, and potential of your scholarly work.

This skill covers *personal career documents* — the narratives a scholar writes about themselves. For adjacent tasks, defer to the right sibling: substantive grant content (Specific Aims, significance/innovation/approach) → `alterlab-research-grants`; venue LaTeX classes and page-limit/formatting rules → `alterlab-venue-templates`; full manuscript drafting → `alterlab-scientific-writing`.

## Core Capabilities

### 1. The Academic Curriculum Vitae (CV)

The academic CV is a comprehensive record of scholarly activity, fundamentally different from an industry resume.

```
Academic CV vs. Industry Resume:

| Dimension       | Academic CV                    | Industry Resume             |
|-----------------|--------------------------------|-----------------------------|
| Length          | No limit (5-30+ pages)         | 1-2 pages                   |
| Content         | Comprehensive record           | Curated highlights          |
| Education       | Detailed with advisors         | Degrees only                |
| Publications    | Complete list, categorized     | Rarely included             |
| Presentations   | All listed                     | Rarely included             |
| Grants          | Full details with amounts      | Rarely included             |
| Service         | Committees, reviews, boards    | Brief or omitted            |
| Format          | Dense, text-heavy              | Design-forward, scannable   |
| Updates         | Every time you add an entry    | Per application             |
```

#### CV Section Order and Content

```markdown
## Standard Academic CV Structure

### 1. Header
- Full name (no nicknames unless that is your professional name)
- Title and department
- Institutional address
- Email (institutional preferred), phone
- Website URL, ORCID iD
- Do NOT include: photo, age, marital status, citizenship (unless required)

### 2. Education
- Reverse chronological order
- Include: degree, institution, year, dissertation/thesis title, advisor name
- Example:
  Ph.D. in Cognitive Psychology, University of Michigan, 2019
    Dissertation: "Attentional Mechanisms in Bilingual Language Switching"
    Advisor: Dr. Jane Smith

### 3. Academic Appointments
- Current position first
- Include: title, department, institution, dates
- List visiting positions and postdocs separately or together

### 4. Publications
  Organize into clear categories:
  a. Peer-Reviewed Journal Articles (numbered, reverse chronological)
  b. Books and Edited Volumes
  c. Book Chapters
  d. Conference Proceedings (if peer-reviewed and valued in your field)
  e. Manuscripts Under Review (be honest about status)
  f. Working Papers / Preprints
  g. Non-Peer-Reviewed Publications (commentaries, reviews, etc.)

  Formatting conventions:
  - Bold your name in author lists
  - Include DOI when available
  - Note corresponding authorship if relevant
  - Mark student co-authors with asterisk (*) and note convention
  - Include journal impact factor ONLY if your field values this

### 5. Grants and Funding
  - Funded grants (role, agency, title, amount, dates)
  - Pending grants
  - Internal grants and fellowships

  Example:
  Co-PI, National Science Foundation (SES-2345678), "Computational Models
  of Decision-Making Under Uncertainty," $450,000, 2024-2027

### 6. Awards and Honors
  - Reverse chronological
  - Include the granting body and brief description if not self-evident

### 7. Invited Talks and Presentations
  a. Invited Keynotes and Plenaries
  b. Invited Talks / Colloquia
  c. Conference Presentations (oral)
  d. Conference Posters

### 8. Teaching Experience
  - Courses taught with institution and term
  - Note if new course development, graduate vs. undergraduate
  - Include enrollment numbers if impressive

### 9. Mentoring and Advising
  - Doctoral students (current and completed, with placement)
  - Master's students
  - Undergraduate thesis students
  - Postdoctoral scholars supervised

### 10. Service
  a. Departmental (committees, roles)
  b. University (senate, task forces)
  c. Professional (journal editor, reviewer, conference organizer)
  d. Community and public engagement

### 11. Professional Memberships

### 12. Skills and Training (optional)
  - Languages, software, methodological training
  - Only if relevant and not obvious from your work
```

#### CV Tailoring by Position Type

```
Research-Intensive (R1) University:
  Priority order: Publications → Grants → Research Statement → Teaching
  Emphasize: Publication record, funding trajectory, research impact
  De-emphasize: Teaching volume (quality matters more than quantity)

Primarily Undergraduate Institution (PUI/SLAC):
  Priority order: Teaching → Student Mentoring → Scholarship → Service
  Emphasize: Teaching philosophy, course development, undergraduate research mentoring
  De-emphasize: Grant amounts (show scholarly activity, not funding totals)

Teaching-Focused / Community College:
  Priority order: Teaching → Service → Professional Development
  Emphasize: Courses taught, pedagogical training, student outcomes
  De-emphasize: Publication count (relevant publications still matter)

Professional School (Med, Law, Business):
  Priority order: Practice experience → Research → Teaching → Service
  Emphasize: Professional experience, applied research, clinical work
  Include: Licensures, certifications, professional appointments
```

### 2. Research Statement

The research statement (1-3 pages typically) articulates your research program's past accomplishments, current projects, and future vision.

```markdown
## Research Statement Structure

### Opening Paragraph: The Big Picture
- State your overarching research question or program in one sentence
- Explain why this matters (significance to field and/or society)
- Preview the key threads of your research program
- Hook the non-specialist reader

### Body: Research Threads (2-4 threads)
For each thread:
  1. Motivating question or problem
  2. Your approach or innovation
  3. Key findings (cite 2-3 of your publications)
  4. Significance and contribution to the field
  5. Connection to other threads (show coherence)

### Current and Ongoing Work
- What you are working on right now
- Preliminary findings or expected outcomes
- Funding status (funded, under review, planned)

### Future Directions (Critical Section)
- Where your research is going in the next 3-5 years
- Specific projects you plan to pursue
- How these build on your track record
- What resources you need (equipment, collaborators, students)
- How this aligns with the hiring department's strengths

### Broader Impacts
- Interdisciplinary connections
- Societal relevance
- Student training opportunities
- Potential for external funding
```

**Key principles for research statements:**
```
DO:
  ✓ Write for an educated non-specialist (search committees are diverse)
  ✓ Use clear topic sentences — skimming should convey your program
  ✓ Show a coherent arc, not a list of disconnected projects
  ✓ Quantify impact where possible (citations, adoptions, downloads)
  ✓ Name specific funding agencies you plan to target
  ✓ Connect your future work to the department you are applying to
  ✓ Demonstrate independence from your advisor/postdoc mentor

DON'T:
  ✗ List every paper — select the most impactful
  ✗ Use dense jargon without explanation
  ✗ Be vague about future plans ("I hope to continue my work...")
  ✗ Ignore the institution type (R1 wants fundability; SLAC wants student involvement)
  ✗ Exceed the page limit
  ✗ Forget to proofread (errors signal carelessness)
```

### 3. Teaching Philosophy Statement

```markdown
## Teaching Philosophy Structure (1-2 pages)

### Opening: Your Core Teaching Belief
- State your pedagogical values in a clear thesis
- Ground in your discipline and experience
- Example: "I believe that learning statistics is fundamentally about
  developing critical thinking, not memorizing formulas. My teaching
  centers on authentic data analysis experiences that build students'
  confidence as independent investigators."

### Principles and Practices (2-3 principles)
For each principle:
  1. State the principle
  2. Explain why it matters (connect to learning science if possible)
  3. Give a SPECIFIC example from your teaching
  4. Describe the outcome or evidence of effectiveness

  Example:
  "Active Learning Through Real Data"
  I structure each class session around a genuine research question
  with real data. In my Intro Statistics course, students analyzed
  local public health data from the county health department. This
  approach increased exam performance by 12% compared to the previous
  lecture-based format, and student evaluations of the course rose
  from 3.8 to 4.5 out of 5.

### Inclusive Teaching
- How you create an equitable learning environment
- Specific strategies (Universal Design for Learning, culturally
  responsive pedagogy, multiple assessment modes)
- Evidence of impact (disaggregated evaluations, DFW rates, etc.)

### Assessment and Evidence
- How you assess student learning (beyond exams)
- Evidence that your approach works
- Teaching awards, evaluation data, student feedback quotes

### Growth and Future Goals
- How your teaching has evolved
- What you want to try next
- Professional development in pedagogy
- Courses you would like to develop
```

### 4. Diversity Statement

**Check whether the document is requested first.** Required DEI/diversity statements in faculty hiring have been rolled back or banned at many U.S. institutions since 2024-2025 (driven by state legislation and federal pressure). Some institutions still request them, some have dropped them, and some have replaced them with a "contributions to a diverse community" or pedagogy/mentoring prompt. Read the job ad: write the statement only if asked, and address whatever framing the ad actually specifies rather than assuming a standalone DEI statement. The structure below applies wherever such a statement is requested.

```markdown
## Diversity, Equity, and Inclusion Statement (1-2 pages)

### Framework
Address three dimensions:
  1. Your understanding of diversity and its importance in academia
  2. Your track record of actions (not just beliefs)
  3. Your future plans for advancing equity and inclusion

### Structure

Opening: Personal and Scholarly Context
  - Your relationship to diversity (be authentic, not performative)
  - How diversity connects to your intellectual work
  - Avoid: trauma narratives (unless you choose to share),
    savior language, treating diversity as a problem to solve

Research Contributions:
  - How your research addresses inequity or includes diverse perspectives
  - Inclusive research practices (community engagement, diverse samples)
  - Mentoring scholars from underrepresented groups

Teaching Contributions:
  - Inclusive pedagogy practices (specific examples)
  - Curriculum diversification efforts
  - Supporting students from marginalized backgrounds
  - Accessibility accommodations and Universal Design

Service and Institutional Contributions:
  - Committee work related to DEI
  - Community partnerships
  - Mentoring and pipeline programs
  - Professional development in DEI

Future Plans:
  - Specific, actionable goals (not vague aspirations)
  - How you would contribute to the hiring institution's DEI efforts
  - Programs you would develop or expand
```

### 5. Academic Cover Letter

```markdown
## Academic Cover Letter Structure (1-2 pages)

### Paragraph 1: Introduction
- Position you are applying for (with reference number if applicable)
- Where you saw the advertisement
- Your current position and institution
- One-sentence summary of why you are a strong fit

### Paragraph 2: Research
- Concise summary of your research program
- 2-3 key accomplishments (publications, grants, impact)
- How your research aligns with the department
- Name specific faculty you could collaborate with (carefully)

### Paragraph 3: Teaching
- Teaching experience and philosophy in brief
- Courses you can teach from the ad
- New courses you could develop
- Evidence of teaching effectiveness

### Paragraph 4: Service and Fit (if space)
- Institutional service contributions
- DEI commitments
- Why this specific institution excites you (be genuine and specific)

### Closing Paragraph
- Materials enclosed/attached
- Availability for interview
- Contact information
- Thank the committee

### Tailoring Checklist
□ Department name is correct (triple-check after copy-pasting)
□ Position title matches the advertisement exactly
□ Specific courses from the ad are mentioned
□ Research alignment with department strengths is explicit
□ Institution type is matched (R1 emphasize research; SLAC emphasize teaching)
□ Named faculty are actually still at the institution
□ Page limit is respected
□ All requested materials are referenced
```

### 6. Tenure and Promotion Dossier

```markdown
## Tenure Dossier Components

### 1. Personal Statement / Candidate's Narrative (3-10 pages)
  Structure:
  - Research accomplishments and trajectory
  - Teaching effectiveness and evolution
  - Service contributions
  - Integration of research, teaching, and service
  - Future vision

  Tone: Confident, evidence-based, reflective (not defensive or boastful)

### 2. CV (updated, comprehensive)

### 3. External Review Letters (solicited by department)
  - You may suggest names (and names to exclude)
  - Choose reviewers who:
    ● Know your subfield but are not collaborators
    ● Are at peer or aspirational institutions
    ● Are themselves tenured (ideally full professors)
    ● Represent the breadth of your work

### 4. Teaching Portfolio
  - Summary of courses taught
  - Student evaluation data (quantitative and qualitative)
  - Peer observation reports
  - Sample syllabi (especially for new courses)
  - Evidence of student mentoring outcomes
  - Teaching awards

### 5. Publications Portfolio
  - Copies of published work (or a selected subset)
  - Statements of contribution for multi-author work

### 6. Letters from Department Chair and Committees
  - Department vote
  - Chair's letter
  - College committee recommendation
```

### 7. Building an Academic Web Presence

```
Essential Components:

1. Personal Academic Website
   - Clean, professional design (no flashy themes)
   - Key pages: About, Research, Publications, Teaching, CV, Contact
   - Host options: GitHub Pages (free), WordPress, Squarespace, university page
   - Update at least once per semester
   - Include a professional headshot
   - Make publications accessible (link to PDFs where copyright allows)

2. Google Scholar Profile
   - Claim your profile and verify your email
   - Merge duplicate entries
   - Monitor for incorrect attributions
   - Your h-index and citation counts are publicly visible here

3. ORCID (Open Researcher and Contributor ID)
   - Register at orcid.org — it's free and takes 5 minutes
   - Use your ORCID iD on all manuscripts, grants, and reviews
   - Connect to CrossRef, Scopus, and Web of Science for auto-updates
   - Include in your CV header and email signature

4. Social Media for Academics
   - Twitter/X: Share papers, engage in scholarly discussion, live-tweet conferences
   - LinkedIn: Professional network, especially for interdisciplinary work
   - Mastodon (academicmastodon): Growing scholarly community
   - ResearchGate: Paper sharing, but be cautious about copyright
   - Bluesky: Emerging academic community

5. Institutional Profile Page
   - Keep updated (many are neglected)
   - Ensure it links to your personal website
   - Include a recent photo and accurate information
```

### 8. Understanding Impact Metrics

```
Common Metrics and Their Limitations:

h-index
  Definition: h papers have been cited at least h times each
  Strengths: Balances productivity and impact; single number
  Weaknesses: Field-dependent, career-length dependent, cannot decrease,
              penalizes early-career researchers, ignores author position
  Use: Context-dependent comparison within subfield and career stage

i10-index
  Definition: Number of publications with at least 10 citations
  Strengths: Simple, easy to understand
  Weaknesses: Same field and career biases as h-index

Journal Impact Factor (JIF)
  Definition: Average citations per article in a journal over 2 years
  Strengths: Quick journal quality heuristic
  Weaknesses: Skewed by a few highly cited papers, gaming by journals,
              varies dramatically across fields, says nothing about
              individual paper quality
  DORA declaration: Many institutions now discourage using JIF for
                    evaluation of individuals

Altmetrics
  Definition: Non-traditional impact indicators (social media mentions,
              news coverage, policy citations, downloads, bookmarks)
  Strengths: Captures broader societal impact, faster than citations
  Weaknesses: Gameable, noisy, not yet widely accepted for evaluation

Field-Weighted Citation Impact (FWCI)
  Definition: Ratio of actual citations to expected citations for the field
  Strengths: Normalizes across fields
  Weaknesses: Requires Scopus access, still citation-focused

Contextualizing your metrics:
  - Always compare within your subfield and career stage
  - Present metrics alongside narrative context
  - Use DORA-aligned framing: discuss the contribution, not the journal
  - Include qualitative indicators: invited talks, awards, adoption by others
```

### 9. Conference Networking

```
Before the Conference:
  - Review the program; identify 5-10 people whose work you want to discuss
  - Email 1-2 people in advance to suggest a brief meeting
  - Prepare a 30-second description of your research (elevator pitch)
  - Bring business cards or have a QR code to your website
  - Update your conference app profile if applicable

During the Conference:
  - Attend talks by people you want to meet (sit near the front)
  - Ask thoughtful questions after talks (brief, genuine, not showing off)
  - Introduce yourself after sessions: "I enjoyed your talk on X.
    I work on Y, and I see a connection with Z. Could we chat more?"
  - Attend receptions, dinners, and informal gatherings
  - Include junior and senior people in your networking
  - Take notes on conversations (names, topics, follow-ups)
  - Share insights on social media (tag presenters, use conference hashtag)

After the Conference:
  - Send follow-up emails within one week
  - Connect on LinkedIn or Twitter
  - Share papers you discussed
  - Propose concrete next steps (collaboration, review, invitation)
  - Add contacts to your professional network file

Networking for Introverts:
  - Use structured events (workshops, poster sessions) where conversation
    is built in
  - Volunteer for session chair or organizer roles
  - Attend smaller satellite events rather than large receptions
  - Set a goal (e.g., "have three genuine conversations today")
  - It's okay to take breaks; sustained networking is exhausting
```

### 10. Mentorship Statements

```markdown
## Mentorship Statement Structure

### Philosophy
- Your approach to mentoring (developmental, cognitive apprenticeship,
  psychosocial support, or a combination)
- How mentoring connects to your values and career

### Track Record
- Number and diversity of mentees (graduate students, postdocs, undergrads)
- Outcomes: publications co-authored, grants secured, positions obtained
- Specific examples of mentoring impact (anonymized if needed)

### Approach and Methods
- Regular meeting structure (frequency, format)
- Individual development plans (IDPs) for each mentee
- Milestone planning (quals, proposal, defense timeline)
- Professional development support (conference attendance, networking,
  job market preparation)
- How you support mentees from underrepresented backgrounds

### Assessment and Growth
- How you solicit feedback from mentees
- How your mentoring has evolved over time
- Training you have completed (mentor training programs, workshops)

### Future Commitments
- Number of mentees you plan to support
- Specific initiatives for broadening participation
- Institutional mentoring contributions (peer mentoring programs, etc.)
```

## Best Practices

1. **Start your CV now and update continuously** — Add every publication, presentation, and service activity as it happens. Reconstructing a CV from memory is error-prone and stressful.

2. **Tailor every document to the institution** — A research statement for an R1 should differ substantially from one for a liberal arts college. Read the job ad carefully and research the department.

3. **Show, don't tell** — Instead of "I am an excellent teacher," write "My course redesign using team-based learning increased the pass rate from 68% to 89% while maintaining exam rigor."

4. **Get multiple readers** — Have your research statement read by someone in your subfield (for accuracy), someone outside (for accessibility), and a mentor who has served on search committees (for strategy).

5. **Maintain a "brag document"** — Keep a running file of accomplishments, compliments, impact stories, and metrics. Draw from this when writing statements.

6. **Separate identity from institution** — Build a personal website and ORCID profile that persist across career moves. Do not rely solely on institutional pages.

7. **Track your impact beyond citations** — Save emails from people who used your dataset, adopted your method, or built on your work. These narratives matter for tenure.

8. **Invest in professional development** — Attend grant writing workshops, teaching certificate programs, and leadership training. Document everything in your CV.

9. **Build your network intentionally** — Aim for a diverse network across career stages, institutions, and disciplines. Mentors, peers, and mentees all matter.

10. **Write the tenure narrative early** — Do not wait until your sixth year. Draft the narrative in year three and update annually. This keeps you focused on your trajectory.

## Common Pitfalls

1. **Using a resume format for an academic CV** — Omitting publications, trimming to two pages, or including an "objective" statement signals unfamiliarity with academic norms.

2. **Generic statements** — "I am passionate about research" or "I believe in diversity" without specific evidence. Every claim needs a concrete example.

3. **Not tailoring to the institution** — Sending an R1-focused research statement to a teaching college, or vice versa. This is the single most common mistake on the academic job market.

4. **Inflating or misrepresenting** — Listing papers as "under review" when they haven't been submitted, or claiming grant amounts that include indirect costs without noting this. Academic communities are small; misrepresentation is discovered.

5. **Ignoring the cover letter** — The cover letter is often the first thing read. A generic or sloppy letter can sink an otherwise strong application.

6. **Neglecting your web presence** — Search committees will Google you. An outdated or nonexistent web presence is a missed opportunity.

7. **Obsessing over metrics** — h-index comparisons across fields or career stages are meaningless. Focus on the quality and impact narrative, not the numbers.

8. **Waiting until tenure to document teaching** — If you don't collect evidence of teaching effectiveness early, you won't have it when you need it. Save evaluations, peer observations, and student outcomes every semester.

9. **Forgetting to acknowledge collaborators** — In multi-author work, be clear about your specific contribution without diminishing others. Search committees want to understand your independent scholarly identity.

10. **Writing in isolation** — Academic career documents benefit enormously from feedback. Join a writing group, find a mentor, or use your institution's career services for faculty.

## References

- Kelsky, K. (2015). *The Professor Is In: The Essential Guide to Turning Your Ph.D. into a Job*. Crown.
- Vick, J. M., & Furlong, J. S. (2016). *The Academic Job Search Handbook* (5th ed.). University of Pennsylvania Press.
- Kaplan, K. (2012). Writing a research plan. *Nature*, 491, 131-132.
- Lang, J. M. (2010). Writing a statement of teaching philosophy. *The Chronicle of Higher Education*.
- Matthew, P. A. (Ed.). (2016). *Written/Unwritten: Diversity and the Hidden Truths of Tenure*. UNC Press.
- San Francisco Declaration on Research Assessment (DORA). https://sfdora.org/
- National Center for Faculty Development & Diversity (NCFDD). https://www.ncfdd.org/

See also: `references/career-templates.md`
