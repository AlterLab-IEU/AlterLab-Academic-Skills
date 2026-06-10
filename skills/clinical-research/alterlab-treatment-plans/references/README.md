# Treatment Plans — reference index

This `references/` directory holds the progressive-disclosure material for the
**alterlab-treatment-plans** skill. Start from the skill root `SKILL.md`; it
links to each file below as needed. Do not read everything up front — load only
the reference the current task calls for.

| File | When to read it |
| ---- | --------------- |
| `document_formats.md` | Choosing length (1-page / 3-4 / 5-6), the mandatory first-page executive-summary model with LaTeX skeleton, concise-documentation and citation rules |
| `specialty_components.md` | Required-component checklists for each of the six specialty plan types |
| `worked_examples.md` | Five end-to-end scenarios (T2DM, post-stroke rehab, MDD, TKA, chronic low back pain) |
| `templates_and_validation.md` | Template selection/structure, PDF generation, the completeness/quality scripts, quality checklist, timeline generation |
| `latex_styling.md` | `medical_treatment_plan.sty` guide: colors, box environments, tables, compilation, troubleshooting |
| `goal_setting_frameworks.md` | SMART and related goal-setting frameworks |
| `intervention_guidelines.md` | Evidence-based intervention guidance (pharmacologic and non-pharmacologic) |
| `regulatory_compliance.md` | HIPAA Safe Harbor de-identification and documentation compliance |
| `specialty_specific_guidelines.md` | Specialty-society guideline references per plan type |
| `treatment_plan_standards.md` | Treatment-plan documentation standards and medical-necessity requirements |

## Templates and scripts

The seven LaTeX templates and the four helper scripts live outside this
directory:

- Templates: `assets/*.tex` (`one_page_treatment_plan.tex` is the preferred
  default for most cases) plus the `medical_treatment_plan.sty` styling package.
- Scripts: `scripts/generate_template.py`, `check_completeness.py`,
  `validate_treatment_plan.py`, `timeline_generator.py`. Invoke them from the
  skill root, e.g. `python scripts/generate_template.py --type one_page`.

De-identification: this skill expects PHI to be removed per the HIPAA Safe
Harbor method (18 identifiers) before any plan is shared. See
`regulatory_compliance.md` for the full identifier list and guidance.
