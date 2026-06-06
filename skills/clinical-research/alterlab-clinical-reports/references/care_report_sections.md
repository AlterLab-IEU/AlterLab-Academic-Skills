# CARE Case-Report Sections (element-by-element)

Detailed breakdown of every CARE (CAse REport) section, plus journal-specific
requirements and HIPAA de-identification. The high-level CARE checklist lives in
`case_report_guidelines.md`; this file is the long-form, per-section content
extracted from the skill body.

## CARE Guidelines Compliance

The CARE guidelines provide a standardized framework for case report writing.
All case reports should follow this checklist.

**Title**
- Include the words "case report" or "case study"
- Indicate the area of focus
- Example: "Unusual Presentation of Acute Myocardial Infarction in a Young Patient: A Case Report"

**Keywords**
- 2-5 keywords for indexing and searchability
- Use MeSH (Medical Subject Headings) terms when possible

**Abstract** (structured or unstructured, 150-250 words)
- Introduction: What is unique or novel about the case?
- Patient concerns: Primary symptoms and key medical history
- Diagnoses: Primary and secondary diagnoses
- Interventions: Key treatments and procedures
- Outcomes: Clinical outcome and follow-up
- Conclusions: Main takeaway or clinical lesson

**Introduction**
- Brief background on the medical condition
- Why this case is novel or important
- Literature review of similar cases (brief)
- What makes this case worth reporting

**Patient Information**
- Demographics (age, sex, race/ethnicity if relevant)
- Medical history, family history, social history
- Relevant comorbidities
- **De-identification**: Remove or alter 18 HIPAA identifiers
- **Patient consent**: Document informed consent for publication

**Clinical Findings**
- Chief complaint and presenting symptoms
- Physical examination findings
- Timeline of symptoms (consider timeline figure or table)
- Relevant clinical observations

**Timeline**
- Chronological summary of key events
- Dates of symptoms, diagnosis, interventions, outcomes
- Can be presented as a table or figure
- Example format:
  - Day 0: Initial presentation with symptoms X, Y, Z
  - Day 2: Diagnostic test A performed, revealed finding B
  - Day 5: Treatment initiated with drug C
  - Day 14: Clinical improvement noted
  - Month 3: Follow-up examination shows complete resolution

**Diagnostic Assessment**
- Diagnostic tests performed (labs, imaging, procedures)
- Results and interpretation
- Differential diagnosis considered
- Rationale for final diagnosis
- Challenges in diagnosis

**Therapeutic Interventions**
- Medications (names, dosages, routes, duration)
- Procedures or surgeries performed
- Non-pharmacological interventions
- Reasoning for treatment choices
- Alternative treatments considered

**Follow-up and Outcomes**
- Clinical outcome (resolution, improvement, unchanged, worsened)
- Follow-up duration and frequency
- Long-term outcomes if available
- Patient-reported outcomes
- Adherence to treatment

**Discussion**
- Strengths and novelty of the case
- How this case compares to existing literature
- Limitations of the case report
- Potential mechanisms or explanations
- Clinical implications and lessons learned
- Unanswered questions or areas for future research

**Patient Perspective** (optional but encouraged)
- Patient's experience and viewpoint
- Impact on quality of life
- Patient-reported outcomes
- Quote from patient if appropriate

**Informed Consent**
- Statement documenting patient consent for publication
- If patient deceased or unable to consent, describe proxy consent
- For pediatric cases, parental/guardian consent
- Example: "Written informed consent was obtained from the patient for publication of this case report and accompanying images. A copy of the written consent is available for review by the Editor-in-Chief of this journal."

## Journal-Specific Requirements

Different journals have specific formatting requirements:
- Word count limits (typically 1500-3000 words)
- Number of figures/tables allowed
- Reference style (AMA, Vancouver, APA)
- Structured vs. unstructured abstract
- Supplementary materials policies

Check journal instructions for authors before submission.

## De-identification and Privacy

**18 HIPAA Identifiers to Remove or Alter:**
1. Names
2. Geographic subdivisions smaller than state
3. Dates (except year)
4. Telephone numbers
5. Fax numbers
6. Email addresses
7. Social Security numbers
8. Medical record numbers
9. Health plan beneficiary numbers
10. Account numbers
11. Certificate/license numbers
12. Vehicle identifiers and serial numbers
13. Device identifiers and serial numbers
14. Web URLs
15. IP addresses
16. Biometric identifiers
17. Full-face photographs
18. Any other unique identifying characteristic

**Best Practices:**
- Use "the patient" instead of names
- Report age ranges (e.g., "a woman in her 60s") or exact age if relevant
- Use approximate dates or time intervals (e.g., "3 months prior")
- Remove institution names unless necessary
- Blur or crop identifying features in images
- Obtain explicit consent for any potentially identifying information

> **⚠️ Caveat — automated de-identification is NOT a compliance guarantee.** The bundled `scripts/check_deidentification.py` is a *pure regex* scan. Pattern matching has known, substantial false-negative rates: it misses unconventional name spellings, free-text dates, narrative addresses, rare identifiers, and anything outside its fixed patterns. It is a rough first-pass screen only — **not** a substitute for line-by-line manual review by a qualified person, and **not** a validated de-identification tool (e.g., Microsoft Presidio, Philter, or a certified Expert Determination). Passing this script does not establish HIPAA Safe Harbor compliance and must never be relied upon as a privacy guarantee. Always perform manual review before any disclosure or publication.
