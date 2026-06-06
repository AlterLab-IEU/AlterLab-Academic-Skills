# Clinical Trial Report Structures (SAE, CSR, deviations)

Section-by-section structure for clinical-trial reporting, extracted from the
skill body. Regulatory framing (ICH-E3, CONSORT, timelines) is also summarized in
`clinical_trial_reporting.md`; this file is the long-form component breakdown.

## Serious Adverse Event (SAE) Reports

SAE reports document unexpected serious adverse reactions during clinical trials.
Regulatory requirements mandate timely reporting to IRBs, sponsors, and regulatory agencies.

**Definition of Serious Adverse Event:**
An adverse event is serious if it:
- Results in death
- Is life-threatening
- Requires inpatient hospitalization or prolongation of existing hospitalization
- Results in persistent or significant disability/incapacity
- Is a congenital anomaly/birth defect
- Requires intervention to prevent permanent impairment or damage

**SAE Report Components:**

**1. Study Information**
- Protocol number and title
- Study phase
- Sponsor name
- Principal investigator
- IND/IDE number (if applicable)
- Clinical trial registry number (NCT number)

**2. Patient Information (De-identified)**
- Subject ID or randomization number
- Age, sex, race/ethnicity
- Study arm or treatment group
- Date of informed consent
- Date of first study intervention

**3. Event Information**
- Event description (narrative)
- Date of onset
- Date of resolution (or ongoing)
- Severity (mild, moderate, severe)
- Seriousness criteria met
- Outcome (recovered, recovering, not recovered, fatal, unknown)

**4. Causality Assessment**
- Relationship to study intervention (unrelated, unlikely, possible, probable, definite)
- Relationship to study procedures
- Relationship to underlying disease
- Rationale for causality determination

**5. Action Taken**
- Modification of study intervention (dose reduction, temporary hold, permanent discontinuation)
- Concomitant medications or treatments administered
- Hospitalization details
- Outcome and follow-up plan

**6. Expectedness**
- Expected per protocol or investigator's brochure
- Unexpected event requiring expedited reporting
- Comparison to known safety profile

**7. Narrative**
- Detailed description of the event
- Timeline of events
- Clinical course and management
- Laboratory and diagnostic test results
- Final diagnosis or conclusion

**8. Reporter Information**
- Name and contact of reporter
- Report date
- Signature

**Regulatory Timelines:**
- Fatal or life-threatening unexpected SAEs: 7 days for preliminary report, 15 days for complete report
- Other serious unexpected events: 15 days
- IRB notification: per institutional policy, typically within 5-10 days

## Clinical Study Reports (CSR) — ICH-E3

Clinical study reports are comprehensive documents summarizing the design, conduct,
and results of clinical trials. They are submitted to regulatory agencies as part of
drug approval applications. The ICH E3 guideline defines the structure and content.

**Main Sections:**

**1. Title Page**
- Study title and protocol number
- Sponsor and investigator information
- Report date and version

**2. Synopsis** (5-15 pages)
- Brief summary of entire study
- Objectives, methods, results, conclusions
- Key efficacy and safety findings
- Can stand alone

**3. Table of Contents**

**4. List of Abbreviations and Definitions**

**5. Ethics** (Section 2)
- IRB/IEC approvals
- Informed consent process
- GCP compliance statement

**6. Investigators and Study Administrative Structure** (Section 3)
- List of investigators and sites
- Study organization
- Monitoring and quality assurance

**7. Introduction** (Section 4)
- Background and rationale
- Study objectives and purpose

**8. Study Objectives and Plan** (Section 5)
- Overall design and plan
- Objectives (primary and secondary)
- Endpoints (efficacy and safety)
- Sample size determination

**9. Study Patients** (Section 6)
- Inclusion and exclusion criteria
- Patient disposition
- Protocol deviations
- Demographic and baseline characteristics

**10. Efficacy Evaluation** (Section 7)
- Data sets analyzed (ITT, PP, safety)
- Demographic and other baseline characteristics
- Efficacy results for primary and secondary endpoints
- Subgroup analyses
- Dropouts and missing data

**11. Safety Evaluation** (Section 8)
- Extent of exposure
- Adverse events (summary tables)
- Serious adverse events (narratives)
- Laboratory values
- Vital signs and physical findings
- Deaths and other serious events

**12. Discussion and Overall Conclusions** (Section 9)
- Interpretation of results
- Benefit-risk assessment
- Clinical implications

**13. Tables, Figures, and Graphs** (Section 10)

**14. Reference List** (Section 11)

**15. Appendices** (Section 12)
- Study protocol and amendments
- Sample case report forms
- List of investigators and ethics committees
- Patient information and consent forms
- Investigator's brochure references
- Publications based on the study

**Key Principles:**
- Objectivity and transparency
- Comprehensive data presentation
- Adherence to statistical analysis plan
- Clear presentation of safety data
- Integration of appendices

See also `assets/clinical_trial_csr_template.md`.

## Protocol Deviations

Protocol deviations are departures from the approved study protocol. They must be
documented, assessed, and reported.

**Categories:**
- **Minor deviation**: Does not significantly impact patient safety or data integrity
- **Major deviation**: May impact patient safety, data integrity, or study conduct
- **Violation**: Serious deviation requiring immediate action and reporting

**Documentation Requirements:**
- Description of deviation
- Date of occurrence
- Subject ID affected
- Impact on safety and data
- Corrective and preventive actions (CAPA)
- Root cause analysis
- Preventive measures implemented
