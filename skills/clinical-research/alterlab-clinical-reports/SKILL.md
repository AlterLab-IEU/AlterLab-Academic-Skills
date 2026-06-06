---
name: alterlab-clinical-reports
description: Writes comprehensive clinical reports — case reports (CARE guidelines), diagnostic reports (radiology, pathology, lab), clinical trial reports (ICH-E3, SAE, CSR), and patient documentation (SOAP notes, H&P, discharge summaries) — with templates, regulatory compliance (HIPAA, FDA, ICH-GCP), and validation tools. Use when drafting a case report for journal publication, a radiology/pathology/lab diagnostic report, an ICH-E3 clinical study report (CSR) or SAE narrative, or SOAP/H&P/discharge patient records needing regulatory-compliant formatting. Part of the AlterLab Academic Skills suite.
allowed-tools: Read Write Edit Bash
license: MIT
compatibility: "Runs with Read/Write/Edit/Bash; producing PDF/report output requires a local LaTeX toolchain. No API key required."
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# Clinical Report Writing

## Overview

Document medical information with precision, accuracy, and regulatory compliance.
This skill covers four report families: **case reports** for journal publication,
**diagnostic reports** for clinical practice (radiology, pathology, lab),
**clinical trial reports** for regulatory submission (SAE, CSR), and **patient
documentation** for medical records (SOAP, H&P, discharge).

**Critical principle: clinical reports must be accurate, complete, objective, and
compliant with applicable regulations (HIPAA, FDA, ICH-GCP).** Patient privacy and
data integrity are paramount.

## When to Use This Skill

Use when:
- Writing a clinical case report for journal submission (CARE guidelines)
- Creating a diagnostic report (radiology, pathology, laboratory)
- Documenting clinical trial data, SAE narratives, or a CSR (ICH-E3)
- Writing SOAP notes, H&P, discharge summaries, or consult notes
- Ensuring HIPAA compliance and proper de-identification
- Validating clinical documentation for completeness and accuracy

## Core Workflow

1. **Pick the report family** and load its detailed reference (see index below).
2. **Draft from the template** in `assets/` for that report type.
3. **Apply regulatory controls** — de-identify, document consent, meet timelines.
4. **Validate** with the matching `scripts/` validator before sign-out.
5. **Final QA** against the checklist at the end of this file.

### 1. Case reports for journal publication
Follow the CARE (CAse REport) checklist: title, keywords, structured abstract,
introduction, patient information, clinical findings, timeline, diagnostic
assessment, therapeutic interventions, follow-up/outcomes, discussion, patient
perspective, and informed consent. Mind journal-specific limits (word count,
figures, reference style) and de-identify before submission.
→ Element-by-element detail, journal requirements, and the 18 HIPAA identifiers:
`references/care_report_sections.md`. High-level checklist: `references/case_report_guidelines.md`.

### 2. Diagnostic reports (radiology, pathology, laboratory)
Each uses a standardized section structure (demographics → indication → technique →
comparison → findings → impression for radiology; gross/microscopic/diagnosis for
pathology; results with reference ranges and critical-value reporting for lab).
Use structured-reporting templates (BI-RADS, Lung-RADS, CAP synoptic) where they apply.
→ Full section templates: `references/diagnostic_report_templates.md`.
Standards and lexicons (ACR, CAP, LOINC): `references/diagnostic_reports_standards.md`.

### 3. Clinical trial reports (SAE, CSR, deviations)
SAE reports document serious adverse events with causality and expectedness, on
strict regulatory timelines (7/15 days). CSRs follow the ICH-E3 section structure
for regulatory submission. Protocol deviations are categorized (minor/major/violation)
with CAPA documentation.
→ Component-by-component structures: `references/clinical_trial_report_structures.md`.
Regulatory framing (ICH-E3, CONSORT, timelines): `references/clinical_trial_reporting.md`.

### 4. Patient documentation (SOAP, H&P, discharge)
SOAP notes for progress, H&P for admission/initial encounters, discharge summaries
for handoff to outpatient providers. Use standard abbreviations, sign and date,
document medical necessity for billing.
→ Format structures: `references/patient_record_formats.md`.
Coding and documentation guidance: `references/patient_documentation.md`.

## Regulatory Compliance and Privacy

- **HIPAA**: minimum-necessary disclosure; de-identify via Safe Harbor (remove 18
  identifiers) or Expert Determination; Business Associate Agreements for third parties.
- **FDA**: 21 CFR Part 11 (e-records/signatures), Part 50 (consent), Part 56 (IRB),
  Part 312 (IND).
- **ICH-GCP**: protocol adherence, consent documentation, source-document requirements,
  audit trails, investigator responsibilities.

> **⚠️ Caveat — automated de-identification is NOT a compliance guarantee.** The bundled `scripts/check_deidentification.py` is a *pure regex* scan. Pattern matching has known, substantial false-negative rates: it misses unconventional name spellings, free-text dates, narrative addresses, rare identifiers, and anything outside its fixed patterns. It is a rough first-pass screen only — **not** a substitute for line-by-line manual review by a qualified person, and **not** a validated de-identification tool (e.g., Microsoft Presidio, Philter, or a certified Expert Determination). Passing this script does not establish HIPAA Safe Harbor compliance and must never be relied upon as a privacy guarantee. Always perform manual review before any disclosure or publication.

Detailed guidance: `references/regulatory_compliance.md`.

## Medical Terminology and Standards

Use standardized nomenclature: **SNOMED CT** (clinical terms), **LOINC** (lab/clinical
observations), **ICD-10-CM** (diagnosis coding), **CPT** (procedure coding). Respect the
Joint Commission "Do Not Use" abbreviation list (e.g. write "unit" not "U", always use a
leading zero, never a trailing zero).
Comprehensive standards: `references/medical_terminology.md`.

## Data Presentation

Tables for demographics, adverse events, lab values over time, and efficacy outcomes;
figures for Kaplan-Meier curves, forest plots, CONSORT flow diagrams, and case-report
timelines. Images must be ≥300 dpi, de-identified, with consent for recognizable
patients. Detail: `references/data_presentation.md`.

## Quality Assurance

Documentation must be **complete, accurate, timely, clear, and compliant**. Use the
per-type validation checklists (CARE, diagnostic completeness, SAE regulatory
compliance, billing requirements) and the `scripts/` validators.

## Workflows by Report Type

- **Case report**: identify case + consent → literature review → draft (CARE) → internal
  review → journal selection/submission → revision.
- **Diagnostic report**: review indication/priors → interpret → dictate structured report
  → peer review (complex cases) → sign-out → critical-value notification. STAT <1h,
  routine 24-48h.
- **SAE report**: identify → assess/document → causality + expectedness → review →
  submit to sponsor/IRB/FDA → follow-up to resolution (24h-15 days).
- **CSR**: database lock → analysis per SAP → medical-writer draft → biostat/clinical
  review → QC → approval/submission (6-12 months post-completion).

## Index of Bundled Resources

### References (`references/`)
- `care_report_sections.md` — CARE element-by-element, journal requirements, 18 HIPAA identifiers
- `case_report_guidelines.md` — CARE guidelines, journal requirements, writing tips
- `diagnostic_report_templates.md` — radiology/pathology/lab section templates
- `diagnostic_reports_standards.md` — ACR, CAP, laboratory reporting standards
- `clinical_trial_report_structures.md` — SAE/CSR/deviation component structures
- `clinical_trial_reporting.md` — ICH-E3, CONSORT, SAE reporting, CSR structure
- `patient_record_formats.md` — SOAP/H&P/discharge section formats
- `patient_documentation.md` — SOAP, H&P, discharge, coding
- `regulatory_compliance.md` — HIPAA, 21 CFR Part 11, ICH-GCP, FDA
- `medical_terminology.md` — SNOMED, LOINC, ICD-10, abbreviations
- `data_presentation.md` — tables, figures, safety data, CONSORT diagrams
- `peer_review_standards.md` — review criteria for clinical manuscripts

### Template assets (`assets/`)
`case_report_template.md`, `radiology_report_template.md`, `pathology_report_template.md`,
`lab_report_template.md`, `clinical_trial_sae_template.md`, `clinical_trial_csr_template.md`,
`soap_note_template.md`, `history_physical_template.md`, `discharge_summary_template.md`,
`consult_note_template.md`, `quality_checklist.md`, `hipaa_compliance_checklist.md`.

### Automation scripts (`scripts/`)
`validate_case_report.py`, `validate_trial_report.py`, `check_deidentification.py`,
`format_adverse_events.py`, `generate_report_template.py`, `extract_clinical_data.py`,
`compliance_checker.py`, `terminology_validator.py`.

## Integration with Other Skills

Pairs with scientific-writing (clear medical prose), peer-review (quality assessment),
citation-mgmt (literature references), research-grants (protocol development), and
literature-review (background sections).

## Common Pitfalls

- **Case reports**: privacy violations, lack of novelty, insufficient detail, weak
  literature review, overgeneralization from a single case.
- **Diagnostic reports**: vague language, incomplete comparison, missing clinical
  correlation, delayed critical-value notification.
- **Trial reports**: late SAE reporting, incomplete causality, data inconsistencies,
  unreported deviations, selective reporting.
- **Patient documentation**: copy-forward errors, insufficient detail affecting billing,
  missing medical necessity, unsigned/undated notes.

## Final Checklist

Before finalizing any clinical report, verify:

- [ ] All required sections complete
- [ ] Patient privacy protected (HIPAA compliance)
- [ ] Informed consent obtained (if applicable)
- [ ] Accurate and verified clinical data
- [ ] Appropriate medical terminology and coding
- [ ] Clear, professional language
- [ ] Proper formatting per guidelines
- [ ] References cited appropriately
- [ ] Figures and tables labeled correctly
- [ ] Spell-checked and proofread
- [ ] Regulatory requirements met
- [ ] Institutional policies followed
- [ ] Signatures and dates present
- [ ] Quality assurance review completed

**Final note**: clinical report quality directly impacts patient safety, healthcare
delivery, and medical knowledge. Always prioritize accuracy, privacy, and professionalism.
