# REDCap Instrument & Data-Dictionary Design (Reference)

Deep detail for building a REDCap project from a requirements spec. The SKILL.md
body is the router; this file holds the field-by-field rules, the choice-string
and branching grammar, longitudinal design, and a worked example.

## Contents

- [The 18 data-dictionary columns](#the-18-data-dictionary-columns)
- [Field types](#field-types)
- [Choices / calculations / slider labels grammar](#choices--calculations--slider-labels-grammar)
- [Text validation types](#text-validation-types)
- [Branching logic](#branching-logic)
- [Identifiers and de-identification](#identifiers-and-de-identification)
- [Longitudinal events, arms, and repeating instruments](#longitudinal-events-arms-and-repeating-instruments)
- [Surveys](#surveys)
- [Worked dictionary](#worked-dictionary)
- [Sources](#sources)

---

## The 18 data-dictionary columns

A REDCap data dictionary is a CSV with these 18 columns, in this order. Importing
into REDCap requires the header to match.

1. `Variable / Field Name`
2. `Form Name`
3. `Section Header`
4. `Field Type`
5. `Field Label`
6. `Choices, Calculations, OR Slider Labels`
7. `Field Note`
8. `Text Validation Type OR Show Slider Number`
9. `Text Validation Min`
10. `Text Validation Max`
11. `Identifier?`
12. `Branching Logic (Show field only if...)`
13. `Required Field?`
14. `Custom Alignment`
15. `Question Number (surveys only)`
16. `Matrix Group Name`
17. `Matrix Ranking?`
18. `Field Annotation`

Design rules:

- **Variable / Field Name** — lowercase letters, digits, and underscores only;
  must not start with a digit; unique within the project. It is the analysis
  name (never shown to participants). Keep it short and meaningful (`age_yrs`,
  not `Q3`).
- **Form Name** — the lowercase machine name of the instrument; all rows for one
  instrument share it, and rows are grouped contiguously by form.
- Each form's **first field is conventionally a record identifier** (e.g.
  `record_id`); the first field in the whole project is the project's record ID.

---

## Field types

Legal `Field Type` values (machine names):

| Value | Renders as |
|-------|-----------|
| `text` | Single-line text box (use validation for dates/numbers/email/phone). |
| `notes` | Multi-line note box. |
| `dropdown` | Single-select dropdown. |
| `radio` | Single-select radio buttons. |
| `checkbox` | Multi-select checkboxes (each option becomes its own export column). |
| `calc` | Calculated field; equation lives in column 6. |
| `sql` | Dropdown populated by a SQL query (admin-only; do not hand-edit). |
| `descriptive` | Display-only text / attached file / link (no data captured). |
| `slider` | Visual analog slider. |
| `yesno` | Radio pair labelled Yes / No (`1`/`0`). |
| `truefalse` | Radio pair labelled True / False. |
| `file` | File upload. |

---

## Choices / calculations / slider labels grammar

Column 6 (`Choices, Calculations, OR Slider Labels`) is **required** for
`radio`, `dropdown`, `checkbox`, `calc`, and `slider` fields.

- **Choice fields** (`radio`/`dropdown`/`checkbox`): pipe-separated
  `code, label` pairs:

  ```
  1, Female | 2, Male | 3, Other | 99, Prefer not to say
  ```

  Codes are the stored/exported values; labels are shown. Keep codes stable —
  changing a code after data entry orphans existing data.

- **`calc` fields**: a REDCap calculation expression referencing other field
  names in `[brackets]`, e.g. `round([weight_kg]/([height_m]^2),1)`.

- **`slider` fields**: up to three labels for left / middle / right.

`yesno` and `truefalse` do **not** take a choices string (their codes are fixed:
`1`/`0`).

---

## Text validation types

Column 8 applies only to `text` (and slider display). Legal validation values:

`date_ymd`, `date_mdy`, `datetime_ymd`, `time`, `integer`, `number`, `email`,
`phone`, `zipcode`.

- For `integer` / `number`, also set `Text Validation Min` / `Max` (columns 9–10)
  to bound the value.
- For dates, prefer `date_ymd` (ISO-ordered, sorts and exports cleanly).
- A `slider` field's column 8 should be `NA` (hide the number) or `number`.

---

## Branching logic

Column 12 (`Branching Logic`) shows a field only when its condition is true.
Syntax mirrors REDCap's logic engine:

- Reference fields by name in brackets: `[sex] = "1"`.
- Checkbox options: `[symptoms(3)] = "1"` (option code 3 is checked).
- Operators: `=`, `<>`, `>`, `>=`, `<`, `<=`, combined with `and` / `or` and
  parentheses.
- Longitudinal event-specific reference: `[visit_1][weight_kg] > "100"`.

Example — show a pregnancy question only for female participants:

```
[sex] = "1"
```

Keep branching expressions referencing **only fields that exist earlier or in
the dictionary**; the linter flags references to unknown variables.

---

## Identifiers and de-identification

Column 11 (`Identifier?`) takes `y` for any field holding PII/PHI (name, MRN,
email, phone, address, exact dates of birth, etc.). REDCap uses this flag to
build **de-identified / limited data set exports** — an unflagged identifier
leaks into "de-identified" exports. Treat a PII-looking field with a blank
`Identifier?` as an error, not a warning.

---

## Longitudinal events, arms, and repeating instruments

The data dictionary defines **fields and instruments only**. Two project-level
structures are configured separately (in the REDCap UI or via the
instrument–event mapping), not in the 18-column CSV:

- **Longitudinal events / arms** — a longitudinal project has one or more *arms*,
  each with an ordered list of *events* (e.g. `screening`, `baseline`,
  `month_3`). Instruments are then mapped to the events where they are collected.
  Document the arm/event plan and the instrument→event mapping as a separate
  table alongside the dictionary.
- **Repeating instruments / events** — instruments or events that recur an
  unknown number of times per record (e.g. repeated adverse-event logs). Note
  which instruments repeat; this is a project setting, not a dictionary column.

When a study is longitudinal, deliver: (1) the data dictionary CSV, and (2) an
event/arm + instrument-mapping table. Do not try to encode events inside the
dictionary.

---

## Surveys

Any instrument can be enabled as a survey. Survey-only behavior:

- Column 15 (`Question Number`) is used only when survey auto-numbering is off.
- Survey settings (invitations, scheduling, completion text) are project config,
  not dictionary columns.
- For the *design of the survey questions themselves* (Likert scales, bias,
  ordering, validation of the instrument), defer to `alterlab-survey-design`;
  this skill only lays the questions into the REDCap dictionary.

---

## Worked dictionary

A minimal two-instrument example (header omitted for brevity; columns in order):

```
record_id,demographics,,text,Record ID,,,,,,,,y,,,,,
age_yrs,demographics,,text,Age in years,,,integer,18,120,,,y,,,,,
sex,demographics,,radio,Sex,"1, Female | 2, Male | 3, Other",,,,,,,y,,,,,
pregnant,demographics,,yesno,Currently pregnant?,,,,,,,"[sex] = ""1""",,,,,,
email,demographics,,text,Contact email,,,email,,,y,,,,,,,
ae_term,adverse_events,,text,Adverse event term,,,,,,,,,,,,,
ae_sev,adverse_events,,dropdown,Severity,"1, Mild | 2, Moderate | 3, Severe",,,,,,,,,,,,
```

Notes on the example:

- `email` is flagged `Identifier? = y` (PII).
- `pregnant` is shown only when `sex = 1` (branching logic).
- `age_yrs` carries `integer` validation with min 18 / max 120.
- `ae_term` / `ae_sev` map cleanly to the SDTM **AE** domain (see
  `cdisc_mapping.md`).

---

## Sources

- REDCap Data Dictionary structure (18 columns, field types, validation),
  Vanderbilt University REDCap documentation, as compiled by university REDCap
  support materials (e.g. University of Illinois "How to Use a REDCap Data
  Dictionary", 2021; University of Chicago CRI Data Dictionary handout).
- Field-type and `text_validation_type` machine values per the
  Sage-Bionetworks/`redcapdd` data-dictionary tooling documentation.

REDCap is developed by Vanderbilt University. Field/validation conventions above
reflect the data-dictionary import format; exact behavior can vary by instance
REDCap version — always confirm with a test import.
