# LaTeX Templates, Validation, and Workflow Tooling

Template selection, PDF generation, completeness/quality validation scripts, timeline
generation, and the end-to-end workflow. Templates live in `assets/`; scripts in `scripts/`.

## LaTeX Template Usage

### Template Selection

Choose the appropriate template based on clinical context and desired length.

#### Concise Templates (PREFERRED)

1. **one_page_treatment_plan.tex** - **FIRST CHOICE** for most cases
   - All clinical specialties
   - Standard protocols and straightforward cases
   - Quick-reference format similar to precision oncology reports
   - Dense, scannable, clinician-focused
   - Use this unless complexity demands more detail

#### Standard Templates (3-4 pages)

Use only when one-page format is insufficient due to complexity:

2. **general_medical_treatment_plan.tex** - Primary care, chronic disease, general medicine
3. **rehabilitation_treatment_plan.tex** - PT/OT, post-surgery, injury recovery
4. **mental_health_treatment_plan.tex** - Psychiatric conditions, behavioral health
5. **chronic_disease_management_plan.tex** - Complex chronic diseases, multiple conditions
6. **perioperative_care_plan.tex** - Surgical patients, procedural care
7. **pain_management_plan.tex** - Acute or chronic pain conditions

**Note**: Even when using standard templates, adapt them to be concise (3-4 pages max) by removing non-essential sections.

### Template Structure

All LaTeX templates include:
- Professional formatting with appropriate margins and fonts
- Structured sections for all required components
- Tables for medications, interventions, timelines
- Goal-tracking sections with SMART criteria
- Space for provider signatures and dates
- HIPAA-compliant de-identification guidance
- Comments with detailed instructions

### Generating PDFs

```bash
# Compile LaTeX template to PDF
pdflatex general_medical_treatment_plan.tex

# For templates with references
pdflatex treatment_plan.tex
bibtex treatment_plan
pdflatex treatment_plan.tex
pdflatex treatment_plan.tex
```

## Validation and Quality Assurance

### Completeness Checking

Use validation scripts to ensure all required sections are present:

```bash
python check_completeness.py my_treatment_plan.tex
```

The script checks for:
- Patient information section
- Diagnosis and assessment
- SMART goals (short-term and long-term)
- Interventions (pharmacological, non-pharmacological)
- Timeline and schedule
- Monitoring parameters
- Expected outcomes
- Follow-up plan
- Patient education
- Risk mitigation

### Treatment Plan Validation

Comprehensive validation of treatment plan quality:

```bash
python validate_treatment_plan.py my_treatment_plan.tex
```

Validation includes:
- SMART goal criteria assessment
- Evidence-based intervention verification
- Timeline feasibility check
- Monitoring parameter adequacy
- Safety and risk mitigation review
- Regulatory compliance check

### Quality Checklist

Review treatment plans against the quality checklist (`assets/quality_checklist.md`):

**Clinical Quality**
- [ ] Diagnosis is accurate and properly coded (ICD-10)
- [ ] Goals are SMART and patient-centered
- [ ] Interventions are evidence-based and guideline-concordant
- [ ] Timeline is realistic and clearly defined
- [ ] Monitoring plan is comprehensive
- [ ] Safety considerations are addressed

**Patient-Centered Care**
- [ ] Patient preferences and values incorporated
- [ ] Shared decision-making documented
- [ ] Health literacy appropriate language
- [ ] Cultural considerations addressed
- [ ] Patient education plan included

**Regulatory Compliance**
- [ ] HIPAA-compliant de-identification
- [ ] Medical necessity documented
- [ ] Informed consent noted
- [ ] Provider signature and credentials
- [ ] Date of plan creation/revision

**Coordination and Communication**
- [ ] Specialist referrals documented
- [ ] Care team roles defined
- [ ] Follow-up schedule clear
- [ ] Emergency contacts provided
- [ ] Transition planning addressed

## Timeline Generation

Use the timeline generator script to create visual treatment timelines:

```bash
python timeline_generator.py --plan my_treatment_plan.tex --output timeline.pdf
```

Generates:
- Gantt chart of treatment phases
- Milestone markers for goal assessments
- Medication titration schedules
- Follow-up appointment calendar
- Intervention intensity over time

## Support and Resources

### Template Generation

Interactive template selection:

```bash
# Run from the skill directory
python scripts/generate_template.py

# Or specify type directly (one_page is the preferred default for most cases)
python scripts/generate_template.py --type mental_health --output depression_treatment_plan.tex
```

### Validation Workflow

1. **Create treatment plan** using appropriate LaTeX template
2. **Check completeness**: `python check_completeness.py plan.tex`
3. **Validate quality**: `python validate_treatment_plan.py plan.tex`
4. **Review checklist**: Compare against `assets/quality_checklist.md`
5. **Generate PDF**: `pdflatex plan.tex`
6. **Review with patient**: Ensure understanding and agreement
7. **Implement and document**: Track progress in clinical notes

### Additional Resources

- Clinical practice guidelines from specialty societies
- AHRQ Effective Health Care Program
- Cochrane Library for intervention evidence
- UpToDate and DynaMed for treatment recommendations
- CMS Quality Measures and HEDIS specifications

## Professional Standards and Guidelines

Treatment plans should align with:

### General Medicine
- American Diabetes Association (ADA) Standards of Care
- ACC/AHA Cardiovascular Guidelines
- GOLD COPD Guidelines
- JNC-8 Hypertension Guidelines
- KDIGO Chronic Kidney Disease Guidelines

### Rehabilitation
- APTA Clinical Practice Guidelines
- AOTA Practice Guidelines
- Cardiac Rehabilitation Guidelines (AHA/AACVPR)
- Stroke Rehabilitation Guidelines

### Mental Health
- APA Practice Guidelines
- VA/DoD Clinical Practice Guidelines
- NICE Guidelines (National Institute for Health and Care Excellence)
- Cochrane Reviews for psychiatric interventions

### Pain Management
- CDC Opioid Prescribing Guidelines
- AAPM/APS Chronic Pain Guidelines
- WHO Pain Ladder
- Multimodal Analgesia Best Practices

## Integration with Other Skills

### Clinical Reports Integration

Treatment plans often accompany other clinical documentation:

- **SOAP Notes** (`clinical-reports` skill): Document ongoing implementation
- **H&P** (`clinical-reports` skill): Initial assessment informs treatment plan
- **Discharge Summaries** (`clinical-reports` skill): Summarize treatment plan execution
- **Progress Notes**: Track goal achievement and plan modifications

### Scientific Writing Integration

Evidence-based treatment planning requires literature support:

- **Citation Management** (`citation-management` skill): Reference clinical guidelines
- **Literature Review** (`literature-review` skill): Understand treatment evidence base
- **Research Lookup** (`research-lookup` skill): Find current best practices

### Research Integration

Treatment plans may be developed for clinical trials or research studies:

- **Research Grants** (`research-grants` skill): Treatment protocols for funded studies
- **Clinical Trial Reports** (`clinical-reports` skill): Intervention documentation
