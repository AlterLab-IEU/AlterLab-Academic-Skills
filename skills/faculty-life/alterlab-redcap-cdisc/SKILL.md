---
name: alterlab-redcap-cdisc
description: "Designs validated research data-capture instruments and aligns them to CDISC submission standards. Builds REDCap projects from a requirements spec: instrument and field design, the 18-column data dictionary (Variable/Field Name, Form Name, Field Type, Choices, Branching Logic, Text Validation, Identifier?), field validation (date_ymd, integer, number, email, phone), branching/show-field logic, longitudinal events and survey settings, and lints a data dictionary for common errors. Maps a study to CDISC: CDASH collection fields, SDTM domain mapping (DM, AE, VS, LB, EX, CM, MH across Interventions/Events/Findings classes), and NCI-EVS controlled terminology. Use when the user wants to build a REDCap project, write or lint a data dictionary, set up branching logic or validation, or map a study to CDISC SDTM/CDASH/CDISC CT. For LabArchives ELN bridging use alterlab-labarchive; for Likert/sampling/reliability use alterlab-survey-design. Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read Write Edit Bash(python:*) Bash WebSearch WebFetch
compatibility: No API key required — designs REDCap data dictionaries as offline CSV and maps to CDISC standards from local rules; the bundled linter is stdlib-only `uv run python`. Pushing a dictionary into a live REDCap instance (the REDCap API) is out of scope and delegated to the instance owner.
metadata:
  skill-author: AlterLab
  version: "1.0.0"
  last_updated: "2026-06-06"
  depends_on: "alterlab-labarchive (ELN bridge), alterlab-survey-design (psychometrics)"
---

# REDCap & CDISC — Research Data Capture and Standards Alignment

Designs **validated electronic data capture (EDC)** instruments in REDCap and
aligns a study's variables to **CDISC** submission standards. It owns two jobs
that overlap with sibling skills only at the edges:

1. **REDCap project & instrument design** — turn a study's requirements into a
   REDCap **data dictionary** (the importable 18-column CSV), with correct field
   types, validation, branching logic, longitudinal events, and survey settings.
2. **CDISC alignment** — map collected variables to **CDASH** (collection) and
   **SDTM** (tabulation) domains, and tie coded values to **CDISC Controlled
   Terminology** (NCI-EVS), so the data is submission- and reuse-ready.

This is design + standards work, not a live-API connector. Producing the CSV and
the mapping is in scope; importing it into a running REDCap server is the
instance owner's job (REDCap's own API/UI).

## Quick Start

```
Build me a REDCap data dictionary for a 3-arm RCT screening + follow-up.
Add branching logic so the pregnancy question only shows when sex = female.
Lint this data_dictionary.csv before I import it.
Map my CRF variables to CDISC SDTM domains and CDASH fields.
Which SDTM domain and controlled-terminology codelist does "adverse event" go in?
```

→ Draft or read the dictionary, run `scripts/lint_data_dictionary.py` to catch
structural errors, then (for CDISC) produce a variable → CDASH → SDTM mapping
table. Always state which facts are design conventions vs. instance-specific.

---

## When to Use This Skill

Use it when the request is about **building the instrument or making it
standards-compliant**:

- "Build / design a REDCap project, form, or data dictionary."
- "Write the importable REDCap CSV for these variables."
- "Set up branching logic / show-field logic / field validation / required fields."
- "Configure longitudinal events / arms / repeating instruments / a survey."
- "Lint / validate / debug my data dictionary before import."
- "Map my study to CDISC — which SDTM domain / CDASH field / codelist?"
- "Make my CRF submission-ready (SDTM/CDASH/CDISC CT)."

### Does NOT Trigger — route to the right sibling

| The request is really about… | Route to |
|------------------------------|----------|
| Bridging an **ELN** to REDCap; reading/writing LabArchives notebook entries or attachments via its REST API | `alterlab-labarchive` |
| **Psychometrics** — Likert scale construction, response-bias mitigation, sampling strategy, pilot testing, reliability/validity (Cronbach's α, factor analysis) | `alterlab-survey-design` |
| Picking or running the **statistical test**, assumptions, power/sample size, APA results | `alterlab-statistical-analysis` |
| **KVKK / Turkish data-protection** plan, anonymization, VERBIS, açık rıza | `alterlab-kvkk-dmp` |
| **IRB / ethics application**, informed consent, GDPR/HIPAA, human-subjects protocol | `alterlab-research-ethics` (or `alterlab-tr-research-ethics` for Turkish etik kurul) |
| **Finding** registered trials by condition/NCT ID on ClinicalTrials.gov | `alterlab-clinicaltrials` |
| **ISO 13485** medical-device QMS documentation | `alterlab-iso13485` |

Routing rule of thumb: **survey-design owns the questions and their measurement
properties; this skill owns the database that captures them and its standards
mapping.** If the user asks for both (e.g. "design a validated depression scale
*and* the REDCap form for it"), do the scale work under `alterlab-survey-design`
and the dictionary/mapping here.

---

## REDCap Data Dictionary (the importable CSV)

REDCap projects are defined by a **data dictionary** — a CSV with **18 columns
in a fixed order**. Authoring or repairing this CSV is the core deliverable.

| # | Column header | Purpose |
|---|---------------|---------|
| 1 | Variable / Field Name | Lowercase machine name (export/analysis). |
| 2 | Form Name | Instrument the field belongs to. |
| 3 | Section Header | Visual section break above the field. |
| 4 | Field Type | One of the values below. |
| 5 | Field Label | Human-readable prompt shown on the form. |
| 6 | Choices, Calculations, OR Slider Labels | `1, Yes \| 0, No` for choice fields; the equation for `calc`. |
| 7 | Field Note | Helper text under the field. |
| 8 | Text Validation Type OR Show Slider Number | Validation for `text`; slider display. |
| 9 | Text Validation Min | Lower bound (integer/number/date). |
| 10 | Text Validation Max | Upper bound. |
| 11 | Identifier? | `y` marks PII/PHI (drives de-identified exports). |
| 12 | Branching Logic (Show field only if...) | Show-field condition. |
| 13 | Required Field? | `y` / blank. |
| 14 | Custom Alignment | Layout. |
| 15 | Question Number (surveys only) | Survey numbering. |
| 16 | Matrix Group Name | Groups matrix fields. |
| 17 | Matrix Ranking? | Matrix ranking flag. |
| 18 | Field Annotation | Action tags / annotations (e.g. `@HIDDEN`). |

**Field Type values:** `text`, `notes`, `dropdown`, `radio`, `checkbox`,
`calc`, `sql`, `descriptive`, `slider`, `yesno`, `truefalse`, `file`.

**Text Validation Type values:** `date_ymd`, `date_mdy`, `datetime_ymd`,
`time`, `integer`, `number`, `email`, `phone`, `zipcode`.

Deeper field-by-field rules, the choice-string grammar, branching-logic
operators, longitudinal/repeating-instrument design, and a worked dictionary are
in **[references/redcap_design.md](references/redcap_design.md)**.

### Lint before import

```bash
uv run python skills/faculty-life/alterlab-redcap-cdisc/scripts/lint_data_dictionary.py \
    path/to/data_dictionary.csv
```

The linter is **stdlib-only** (no network, no REDCap account). It checks the
18-column header, field-name syntax, field-type/validation legality, that choice
fields carry a choices string, that `calc`/branching fields reference variables
that exist, duplicate variable names, and PII fields left unflagged as
`Identifier?`. It exits non-zero and emits a JSON report when issues are found.
It is a **structural** linter — it does not validate against a live REDCap
server, so always tell the user a clean lint still needs a test import.

---

## CDISC Alignment (CDASH → SDTM → Controlled Terminology)

CDISC defines complementary standards across the data lifecycle. Map a study so
its collected data is regulator- and reuse-ready.

| Standard | Role | What you produce |
|----------|------|------------------|
| **CDASH** | *Collection* — standard fields to collect on CRFs; traces into SDTM. | The CRF/REDCap fields named to CDASH conventions. |
| **SDTM** | *Tabulation* — organizes submitted data into domains. | A variable → domain mapping. |
| **Controlled Terminology** | Codelists of valid values (NCI-EVS). | Coded values tied to the right codelist. |

**SDTM observation classes:** Interventions, Events, Findings, and Findings
About. Common domains and their two-letter codes: **DM** Demographics, **AE**
Adverse Events, **VS** Vital Signs, **LB** Laboratory, **EX** Exposure, **CM**
Concomitant Medications, **MH** Medical History.

**Controlled Terminology** is maintained with NCI's Enterprise Vocabulary
Services (NCI-EVS) and **updated quarterly**; do not invent codelist values —
cite the codelist and tell the user to pull the current quarterly release.

Versions are real but move — the skill records the latest it verified
(**SDTM v2.1**, 2024-06-10; **SDTMIG v3.4**, 2021-11-29; **CDASHIG v2.3**,
2023-09-28, referencing CDASH Model v1.3). **Confirm the current version with the
user / cdisc.org before asserting one in a deliverable**, because these are
re-released. The mapping recipe, the CDASH↔SDTM traceability idea, and the
worked AE/VS examples are in
**[references/cdisc_mapping.md](references/cdisc_mapping.md)**.

---

## Workflow

1. **Capture requirements.** Study design (cross-sectional / longitudinal /
   arms), the variables, value sets, PII fields, and whether it is a survey.
   If the *measurement properties* of the questions matter, hand the
   questionnaire design to `alterlab-survey-design` first.
2. **Draft the data dictionary.** Build the 18-column CSV: machine names, field
   types, choices, validation, `Identifier?` for every PII field, branching
   logic, and (longitudinal) the event/arm plan separately.
3. **Lint.** Run `scripts/lint_data_dictionary.py`; fix every error before the
   user imports.
4. **(If submission/standards needed) Map to CDISC.** Produce the variable →
   CDASH → SDTM table, flag value sets needing Controlled Terminology, and name
   the codelists — never fabricate codelist members.
5. **Report honestly.** State which choices are conventions vs. instance config,
   that the lint is structural (a test import is still required), and that CDISC
   versions must be confirmed against the current release.

---

## Self-Check Before Reporting

- Does the dictionary have exactly the **18 columns** in order, and is every
  field type one of the legal values?
- Is **every PII field** marked `Identifier? = y`?
- Do all **branching-logic** and **calc** expressions reference variables that
  actually exist in the dictionary?
- Did the **linter** run and pass — and did you tell the user a clean lint still
  needs a real test import?
- For CDISC: did you **name codelists/versions** rather than invent codelist
  values, and flag that versions must be confirmed against the current release?
- Did you route psychometrics to `alterlab-survey-design` and ELN bridging to
  `alterlab-labarchive` instead of doing them here?

---

## References

- [references/redcap_design.md](references/redcap_design.md) — full 18-column
  field reference, choice-string grammar, branching-logic operators, validation
  types, longitudinal/repeating-instrument design, and a worked dictionary.
- [references/cdisc_mapping.md](references/cdisc_mapping.md) — CDASH→SDTM→CT
  pipeline, SDTM observation classes and domains, controlled-terminology
  sourcing, and worked AE/VS/DM mappings, with verified versions and sources.

Part of the AlterLab Academic Skills suite.
