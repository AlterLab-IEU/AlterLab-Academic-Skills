# Document Format and Best Practices

Detailed length options, the mandatory first-page summary model, concise-documentation
rules, and citation guidance for treatment plans. The SKILL.md body summarizes these;
this file is the full specification.

## Document Length Options

Treatment plans come in three format options based on clinical complexity and use case.

### Option 1: One-Page Treatment Plan (PREFERRED for most cases)

**When to use**: Straightforward clinical scenarios, standard protocols, busy clinical settings

**Format**: Single page containing all essential treatment information in scannable sections
- No table of contents needed
- No extensive narratives
- Focused on actionable items only
- Similar to precision oncology reports or treatment recommendation cards

**Required sections** (all on one page):
1. **Header Box**: Patient info, diagnosis, date, molecular/risk profile if applicable
2. **Treatment Regimen**: Numbered list of specific interventions
3. **Supportive Care**: Brief bullet points
4. **Rationale**: 1-2 sentence justification (optional for standard protocols)
5. **Monitoring**: Key parameters and frequency
6. **Evidence Level**: Guideline reference or evidence grade (e.g., "Level 1, FDA approved")
7. **Expected Outcome**: Timeline and success metrics

**Design principles**:
- Use small boxes/tables for organization (like the clinical treatment recommendation card format)
- Eliminate all non-essential text
- Use abbreviations familiar to clinicians
- Dense information layout - maximize information per square inch
- Think "quick reference card" not "comprehensive documentation"

**Example structure**:
```latex
[Patient ID/Diagnosis Box at top]

TARGET PATIENT POPULATION
  Number of patients, demographics, key features

PRIMARY TREATMENT REGIMEN
  • Medication 1: dose, frequency, duration
  • Procedure: specific details
  • Monitoring: what and when

SUPPORTIVE CARE
  • Key supportive medications

RATIONALE
  Brief clinical justification

MOLECULAR TARGETS / RISK FACTORS
  Relevant biomarkers or risk stratification

EVIDENCE LEVEL
  Guideline reference, trial data

MONITORING REQUIREMENTS
  Key labs/vitals, frequency

EXPECTED CLINICAL BENEFIT
  Primary endpoint, timeline
```

### Option 2: Standard 3-4 Page Format

**When to use**: Moderate complexity, need for patient education materials, multidisciplinary coordination

Uses the Foundation Medicine first-page summary model with 2-3 additional pages of details.

### Option 3: Extended 5-6 Page Format

**When to use**: Complex comorbidities, research protocols, extensive safety monitoring required

## First Page Summary (Foundation Medicine Model)

**CRITICAL REQUIREMENT: All treatment plans MUST have a complete executive summary on the first page ONLY, before any table of contents or detailed sections.**

Following the Foundation Medicine model for precision medicine reporting and clinical summary documents, treatment plans begin with a one-page executive summary that provides immediate access to key actionable information. This entire summary must fit on the first page.

**Required First Page Structure (in order):**

1. **Title and Subtitle**
   - Main title: Treatment plan type (e.g., "Comprehensive Treatment Plan")
   - Subtitle: Specific condition or focus (e.g., "Type 2 Diabetes Mellitus - Young Adult Patient")

2. **Report Information Box** (using `\begin{infobox}` or `\begin{patientinfo}`)
   - Report type/document purpose
   - Date of plan creation
   - Patient demographics (age, sex, de-identified)
   - Primary diagnosis with ICD-10 code
   - Report author/clinic (if applicable)
   - Analysis approach or framework used

3. **Key Findings or Treatment Highlights** (2-4 colored boxes using appropriate box types)
   - **Primary Treatment Goals** (using `\begin{goalbox}`)
     - 2-3 SMART goals in bullet format
   - **Main Interventions** (using `\begin{keybox}` or `\begin{infobox}`)
     - 2-3 key interventions (pharmacological, non-pharmacological, monitoring)
   - **Critical Decision Points** (using `\begin{warningbox}` if urgent)
     - Important monitoring thresholds or safety considerations
   - **Timeline Overview** (using `\begin{infobox}`)
     - Brief treatment duration/phases
     - Key milestone dates

**Visual Format Requirements:**
- Use `\thispagestyle{empty}` to remove page numbers from first page
- All content must fit on page 1 (before `\newpage`)
- Use colored boxes (tcolorbox package) with different colors for different information types
- Boxes should be visually prominent and easy to scan
- Use concise, bullet-point format
- Table of contents (if included) starts on page 2
- Detailed sections start on page 3

**Example First Page Structure:**
```latex
\maketitle
\thispagestyle{empty}

% Report Information Box
\begin{patientinfo}
  Report Type, Date, Patient Info, Diagnosis, etc.
\end{patientinfo}

% Key Finding #1: Treatment Goals
\begin{goalbox}[Primary Treatment Goals]
  • Goal 1
  • Goal 2
  • Goal 3
\end{goalbox}

% Key Finding #2: Main Interventions
\begin{keybox}[Core Interventions]
  • Intervention 1
  • Intervention 2
  • Intervention 3
\end{keybox}

% Key Finding #3: Critical Monitoring (if applicable)
\begin{warningbox}[Critical Decision Points]
  • Decision point 1
  • Decision point 2
\end{warningbox}

\newpage
\tableofcontents  % TOC on page 2
\newpage  % Detailed content starts page 3
```

## Concise Documentation

**CRITICAL: Treatment plans MUST prioritize brevity and clinical relevance. Default to 3-4 pages maximum unless clinical complexity absolutely demands more detail.**

Treatment plans should prioritize **clarity and actionability** over exhaustive detail:

- **Focused**: Include only clinically essential information that impacts care decisions
- **Actionable**: Emphasize what needs to be done, when, and why
- **Efficient**: Facilitate quick decision-making without sacrificing clinical quality
- **Target length options**:
  - **1-page format** (preferred for straightforward cases): Quick-reference card with all essential information
  - **3-4 pages standard**: Standard format with first-page summary + supporting details
  - **5-6 pages** (rare): Only for highly complex cases with multiple comorbidities or multidisciplinary interventions

**Streamlining Guidelines:**
- **First Page Summary**: Use individual colored boxes to consolidate key information (goals, interventions, decision points) - this alone can often convey the essential treatment plan
- **Eliminate Redundancy**: If information is in the first-page summary, don't repeat it verbatim in detailed sections
- **Patient Education section**: 3-5 key bullet points on critical topics and warning signs only
- **Risk Mitigation section**: Highlight only critical medication safety concerns and emergency actions (not exhaustive lists)
- **Expected Outcomes section**: 2-3 concise statements on anticipated responses and timelines
- **Interventions**: Focus on primary interventions; secondary/supportive measures in brief bullet format
- **Use tables and bullet points** extensively for efficient presentation
- **Avoid narrative prose** where structured lists suffice
- **Combine related sections** when appropriate to reduce page count

### Quality Over Quantity

The goal is professional, clinically complete documentation that respects clinicians' time while ensuring comprehensive patient care. Every section should add value; remove or condense sections that don't directly inform treatment decisions.

## Citations and Evidence Support

**Use minimal, targeted citations to support clinical recommendations:**

- **Text Citations Preferred**: Use brief in-text citations (Author Year) or simple references rather than extensive bibliographies unless specifically requested
- **When to Cite**:
  - Clinical practice guideline recommendations (e.g., "per ADA 2024 guidelines")
  - Specific medication dosing or protocols (e.g., "ACC/AHA recommendations")
  - Novel or controversial interventions requiring evidence support
  - Risk stratification tools or validated assessment scales
- **When NOT to Cite**:
  - Standard-of-care interventions widely accepted in the field
  - Basic medical facts and routine clinical practices
  - General patient education content
- **Citation Format**:
  - Inline: "Initiate metformin as first-line therapy (ADA Standards of Care 2024)"
  - Minimal: "Treatment follows ACC/AHA heart failure guidelines"
  - Avoid formal numbered references and extensive bibliography sections unless document is for academic/research purposes
- **Keep it Brief**: A 3-4 page treatment plan should have 0-3 citations maximum, only where essential for clinical credibility or novel recommendations

## Best Practices (Brevity, First Page, SMART, Patient-Centered)

### Brevity and Focus (HIGHEST PRIORITY)

**Treatment plans MUST be concise and focused on actionable clinical information:**

- **1-page format is PREFERRED**: For most clinical scenarios, a single-page treatment plan (like precision oncology reports) provides all necessary information
- **Default to shortest format possible**: Start with 1-page; only expand if clinical complexity genuinely requires it
- **Every sentence must add value**: If a section doesn't change clinical decision-making, omit it entirely
- **Think "quick reference card" not "comprehensive textbook"**: Busy clinicians need scannable, dense information
- **Avoid academic verbosity**: This is clinical documentation, not a literature review or teaching document
- **Maximum lengths by complexity**:
  - Simple/standard cases: 1 page
  - Moderate complexity: 3-4 pages (first-page summary + details)
  - High complexity (rare): 5-6 pages maximum

### First Page Summary (Most Important)

**ALWAYS create a one-page executive summary as the first page:**
- The first page must contain ONLY: Title, Report Info Box, and Key Findings boxes
- This provides an at-a-glance overview similar to precision medicine reports
- Table of contents and detailed sections start on page 2 or later
- Think of it as a "clinical highlights" page that a busy clinician can scan in 30 seconds
- Use 2-4 colored boxes for different key findings (goals, interventions, decision points)
- **A strong first page can often stand alone** - subsequent pages are for details, not repetition

### SMART Goal Setting

All treatment goals should meet SMART criteria:

- **Specific**: "Improve HbA1c to <7%" not "Better diabetes control"
- **Measurable**: Use quantifiable metrics, validated scales, objective measures
- **Achievable**: Consider patient capabilities, resources, social support
- **Relevant**: Align with patient values, priorities, and life circumstances
- **Time-bound**: Define clear timeframes for goal achievement and reassessment

### Patient-Centered Care

- **Shared Decision-Making**: Involve patients in goal-setting and treatment choices
- **Cultural Competence**: Respect cultural beliefs, language preferences, health literacy
- **Patient Preferences**: Honor treatment preferences and personal values
- **Individualization**: Tailor plans to patient's unique circumstances
- **Empowerment**: Support patient activation and self-management

### Evidence-Based Practice

- **Clinical Guidelines**: Follow current specialty society recommendations
- **Quality Measures**: Incorporate HEDIS, CMS quality measures
- **Comparative Effectiveness**: Use treatments with proven efficacy
- **Avoid Low-Value Care**: Eliminate unnecessary tests and interventions
- **Stay Current**: Update plans based on emerging evidence

### Documentation Standards

- **Completeness**: Include all required elements
- **Clarity**: Use clear, professional medical language
- **Accuracy**: Ensure factual correctness and current information
- **Timeliness**: Document plans promptly
- **Legibility**: Professional formatting and organization
- **Signature and Date**: Authenticate all treatment plans

### Regulatory Compliance

- **HIPAA Privacy**: De-identify all protected health information
- **Informed Consent**: Document patient understanding and agreement
- **Billing Support**: Include documentation to support medical necessity
- **Quality Reporting**: Enable extraction of quality metrics
- **Legal Protection**: Maintain defensible clinical documentation

### Multidisciplinary Coordination

- **Team Communication**: Share plans across care team
- **Role Clarity**: Define responsibilities for each team member
- **Care Transitions**: Ensure continuity across settings
- **Specialist Integration**: Coordinate with subspecialty care
- **Patient-Centered Medical Home**: Align with PCMH principles
