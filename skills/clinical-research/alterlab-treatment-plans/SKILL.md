---
name: alterlab-treatment-plans
description: Generates concise (3-4 page), focused medical treatment plans in LaTeX/PDF format across all clinical specialties — general medical treatment, rehabilitation therapy, mental health care, chronic disease management, perioperative care, and pain management — using SMART goal frameworks, evidence-based interventions with minimal citations, HIPAA compliance, and professional formatting. Use when drafting a brief, actionable patient treatment or care plan with measurable SMART goals and structured follow-up for any specialty. Part of the AlterLab Academic Skills suite.
allowed-tools: Read Write Edit Bash
license: MIT
compatibility: "Runs with Read/Write/Edit/Bash; producing PDF output requires a local LaTeX toolchain (pdflatex/xelatex). No API key required."
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# Treatment Plan Writing

## Overview

Treatment plan writing is the systematic documentation of clinical care strategies designed to address patient health conditions through evidence-based interventions, measurable goals, and structured follow-up. This skill provides LaTeX templates and validation tools for creating **concise, focused** treatment plans (3-4 pages standard) across all medical specialties with full regulatory compliance.

**Critical Principles:**
1. **CONCISE & ACTIONABLE**: Treatment plans default to 3-4 pages maximum (1 page preferred for standard cases), focusing only on clinically essential information that impacts care decisions
2. **Patient-Centered**: Plans must be evidence-based, measurable, and compliant with healthcare regulations (HIPAA, documentation standards)
3. **Minimal Citations**: Use brief in-text citations only when needed; avoid extensive bibliographies (0-3 citations max in a 3-4 page plan)

Every treatment plan should include clear goals, specific interventions, defined timelines, monitoring parameters, and expected outcomes that align with patient preferences and current clinical guidelines — all presented as efficiently as possible.

## When to Use This Skill

Use this skill when:
- Creating individualized treatment plans for patient care
- Documenting therapeutic interventions for chronic disease management
- Developing rehabilitation programs (physical, occupational, cardiac)
- Writing mental health and psychiatric treatment plans
- Planning perioperative and surgical care pathways
- Establishing pain management protocols
- Setting patient-centered goals using SMART criteria
- Coordinating multidisciplinary care across specialties
- Ensuring regulatory compliance in treatment documentation

## Core Workflow

1. **Choose format and length.** Default to the 1-page quick-reference card; expand to the 3-4 page standard format (first-page summary + details) only when complexity demands. See `references/document_formats.md`.
2. **Build the mandatory first-page executive summary.** Title + report info box + 2-4 colored key-findings boxes (goals, interventions, decision points). This page can often stand alone. Full spec and LaTeX skeleton in `references/document_formats.md`.
3. **Pick the specialty template** from `assets/` and fill its component sections. Component checklists per specialty (general medical, rehab, mental health, chronic disease, perioperative, pain) are in `references/specialty_components.md`.
4. **Write SMART goals** (Specific, Measurable, Achievable, Relevant, Time-bound) for short- and long-term horizons.
5. **Apply professional styling** with the `medical_treatment_plan.sty` package — see `references/latex_styling.md`.
6. **Validate, then generate PDF.** Run completeness and quality checks, compare against the quality checklist, then compile. See `references/templates_and_validation.md`.

## Six Specialty Plan Types

| # | Type | Template (`assets/`) | Use for |
|---|------|----------------------|---------|
| 1 | General Medical | `general_medical_treatment_plan.tex` | Chronic disease, acute medical, primary care |
| 2 | Rehabilitation | `rehabilitation_treatment_plan.tex` | PT/OT/SLP, post-surgery, injury recovery |
| 3 | Mental Health | `mental_health_treatment_plan.tex` | Psychiatric conditions, behavioral health |
| 4 | Chronic Disease | `chronic_disease_management_plan.tex` | Complex multi-condition long-term care |
| 5 | Perioperative | `perioperative_care_plan.tex` | Surgical/procedural pre-, peri-, post-op |
| 6 | Pain Management | `pain_management_plan.tex` | Acute/chronic pain, opioid-sparing multimodal |

Per-specialty required component breakdowns (assessments, goals, interventions, monitoring, education, risk mitigation) are documented in **[`references/specialty_components.md`](references/specialty_components.md)**.

## Quick Generation

```bash
# Interactive template selection
python scripts/generate_template.py

# Or specify type directly. Default to one_page (the preferred quick-reference
# format) for most cases; pick a specialty template when complexity demands it.
python scripts/generate_template.py --type one_page --output diabetes_plan.tex
python scripts/generate_template.py --type mental_health --output depression_treatment_plan.tex

# Type choices: one_page, general_medical, rehabilitation, mental_health,
#               chronic_disease, perioperative, pain_management

# Validate, then compile
python scripts/check_completeness.py plan.tex
python scripts/validate_treatment_plan.py plan.tex
pdflatex plan.tex
```

## Professional Document Styling

Treatment plans can be enhanced with professional medical document styling using the `medical_treatment_plan.sty` LaTeX package (in `assets/`), which provides a color-coded clinical look with custom box environments (`infobox`, `warningbox`, `goalbox`, `keybox`, `emergencybox`, `patientinfo`) and styled medical tables.

For the full styling guide — color scheme, every box environment with examples, table formatting, compilation (XeLaTeX/PDFLaTeX), customization, installation, troubleshooting, and a worked styled-document example — see **[`references/latex_styling.md`](references/latex_styling.md)**.

## Reference Index

| File | Contents |
| ---- | -------- |
| [`references/document_formats.md`](references/document_formats.md) | Length options (1-page / 3-4 / 5-6), Foundation-Medicine first-page summary model with LaTeX skeleton, concise-documentation rules, citation guidance, full best-practices (brevity, SMART, patient-centered, compliance, coordination) |
| [`references/specialty_components.md`](references/specialty_components.md) | Full required-component checklists for all six specialty plan types |
| [`references/worked_examples.md`](references/worked_examples.md) | Five end-to-end scenarios (diabetes, post-stroke rehab, MDD, TKA, chronic low back pain) with template, goals, interventions |
| [`references/templates_and_validation.md`](references/templates_and_validation.md) | Template selection/structure, PDF generation, completeness & quality validation scripts, quality checklist, timeline generation, professional standards, cross-skill integration |
| [`references/latex_styling.md`](references/latex_styling.md) | Styling package guide: colors, box environments, tables, compilation, troubleshooting |
| [`references/goal_setting_frameworks.md`](references/goal_setting_frameworks.md) | SMART and related goal-setting frameworks |
| [`references/intervention_guidelines.md`](references/intervention_guidelines.md) | Evidence-based intervention guidance |
| [`references/regulatory_compliance.md`](references/regulatory_compliance.md) | HIPAA and documentation compliance detail |
| [`references/specialty_specific_guidelines.md`](references/specialty_specific_guidelines.md) | Specialty society guideline references |
| [`references/treatment_plan_standards.md`](references/treatment_plan_standards.md) | Treatment-plan documentation standards |

## Ethical Considerations

- **Informed Consent**: All plans should involve patient understanding and voluntary agreement to proposed interventions.
- **Cultural Sensitivity**: Respect diverse cultural beliefs, health practices, and communication styles.
- **Health Equity**: Consider social determinants of health, access barriers, and disparities.
- **Privacy Protection**: Maintain strict HIPAA compliance; de-identify all protected health information in shared documents.
- **Autonomy and Beneficence**: Balance medical recommendations with patient autonomy and values while promoting patient welfare.

## License

Part of the Claude Scientific Writer project. See main LICENSE file.
