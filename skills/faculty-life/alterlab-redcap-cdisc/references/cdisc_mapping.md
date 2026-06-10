# CDISC Alignment: CDASH → SDTM → Controlled Terminology (Reference)

Deep detail for mapping a study's collected variables to CDISC standards so the
data is submission- and reuse-ready. The SKILL.md body routes here; this file
holds the standards model, the mapping recipe, worked domain examples, verified
versions, and sources.

## Contents

- [The three standards and how they relate](#the-three-standards-and-how-they-relate)
- [SDTM observation classes and common domains](#sdtm-observation-classes-and-common-domains)
- [Controlled Terminology](#controlled-terminology)
- [Mapping recipe (REDCap/CRF → CDASH → SDTM)](#mapping-recipe-redcapcrf--cdash--sdtm)
- [Worked mappings](#worked-mappings)
- [Verified versions](#verified-versions)
- [Sources](#sources)

---

## The three standards and how they relate

CDISC publishes complementary standards across the clinical-data lifecycle:

| Standard | Stage | One-line role |
|----------|-------|---------------|
| **CDASH** (Clinical Data Acquisition Standards Harmonization) | Collection | A standard way to **collect** data consistently across studies/sponsors, with clear traceability into SDTM. |
| **SDTM** (Study Data Tabulation Model) | Tabulation | A standard for **organizing/formatting** data into domains for review, sharing, and regulatory submission. |
| **Controlled Terminology** | Across all | The **codelists and valid values** used within CDISC datasets. |

Key relationship (from CDISC): **CDASH uses the same Observation Classes and
Domains as the SDTMIG**, which builds traceability from what you collect to what
you submit and enables (semi-)automated creation of SDTM datasets. So design
collection fields with their eventual SDTM domain in mind.

SDTM is one of the required standards for data submission to the **FDA (U.S.)**
and **PMDA (Japan)** per CDISC. CDASH governs collection, not submission.

The model vs. implementation-guide distinction matters:

- **CDASH Model** is the foundational structure; the **CDASHIG** is the
  implementation guide built on a specific Model version. The CDASH model is
  cumulative — each release builds on the prior one.
- Likewise, **SDTM** is the model and **SDTMIG** is its implementation guide.

---

## SDTM observation classes and common domains

SDTM domains are classified into observation classes:

- **Interventions** — things done to / taken by the subject (e.g. exposure,
  concomitant meds).
- **Events** — occurrences (e.g. adverse events, medical history).
- **Findings** — measurements/observations (e.g. vital signs, labs).
- **Findings About** — findings about an event or intervention.

Plus special-purpose, trial-design, and relationship datasets (not enumerated
here — confirm against the current SDTMIG before asserting names).

Common domains and their two-letter codes (verified from CDISC):

| Code | Domain | Observation class |
|------|--------|-------------------|
| `DM` | Demographics | Special-purpose |
| `AE` | Adverse Events | Events |
| `MH` | Medical History | Events |
| `VS` | Vital Signs | Findings |
| `LB` | Laboratory | Findings |
| `EX` | Exposure | Interventions |
| `CM` | Concomitant Medications | Interventions |

Use these only as the well-known core. For any domain not in this verified
list, pull the current SDTMIG rather than guessing a code.

---

## Controlled Terminology

CDISC **Controlled Terminology (CT)** is "the set of codelists and valid values
used with data items within CDISC-defined datasets." Operational facts:

- Maintained and distributed in collaboration with the **National Cancer
  Institute's Enterprise Vocabulary Services (NCI-EVS)**.
- Hosted on an NCI file site in multiple formats (Excel, text, XML, PDF, HTML,
  OWL/RDF).
- **Updated quarterly** — releases span ADaM, CDASH, DDF, Define-XML, SDTM, and
  SEND terminology files.

Rule for this skill: **never invent codelist members.** Name the relevant
codelist (e.g. the severity/intensity codelist used for `AESEV`) and instruct the
user to pull the current quarterly CT release from NCI-EVS for the exact valid
values. Coding terms to dictionaries like MedDRA (events) or WHODrug
(medications) is a separate, licensed activity — flag it, do not perform it.

---

## Mapping recipe (REDCap/CRF → CDASH → SDTM)

1. **Inventory the collected variables** (from the REDCap dictionary or CRF):
   name, label, type, value set.
2. **Classify each into an SDTM observation class** (Intervention / Event /
   Finding) — this picks the candidate domain.
3. **Assign the SDTM domain** (e.g. an "adverse event term" → `AE`).
4. **Name the CDASH collection field** that feeds it, keeping the CDASH↔SDTM
   traceability explicit.
5. **Tie coded value sets to a CT codelist** by name; defer exact members to the
   current CT release.
6. **Produce a mapping table**: `source variable | CDASH field | SDTM domain |
   SDTM variable | CT codelist`. Mark anything you could not confidently map as
   "needs SDTMIG/CDASHIG lookup" rather than fabricating a variable name.

---

## Worked mappings

Illustrative, conservative mappings tying the worked REDCap dictionary in
`redcap_design.md` to SDTM. SDTM variable names beyond the well-known core
(`AETERM`, `AESEV`, `VSTESTCD`, etc.) should be confirmed against the current
SDTMIG — they are shown here as the standard, widely-documented names.

| REDCap variable | Observation class | SDTM domain | Notes |
|-----------------|-------------------|-------------|-------|
| `record_id` | (identifier) | `DM` | Subject identifier (maps to `USUBJID`/`SUBJID` per study). |
| `age_yrs` | Special-purpose | `DM` | Demographics age. |
| `sex` | Special-purpose | `DM` | `SEX`; values tie to the Sex CT codelist. |
| `ae_term` | Events | `AE` | `AETERM` (verbatim term; MedDRA coding separate). |
| `ae_sev` | Events | `AE` | `AESEV`; values tie to the severity/intensity CT codelist. |

For vital signs collected as separate fields (e.g. systolic/diastolic BP, pulse),
SDTM `VS` is structured **long** (one row per measurement) with `VSTESTCD` /
`VSTEST` identifying the test — a wide REDCap layout must be pivoted to long on
the way to SDTM. Note this reshaping in the mapping deliverable.

---

## Verified versions

Versions are real but periodically re-released; **confirm the current version
with the user or cdisc.org before stating one in a deliverable.** Latest values
verified for this skill (as of 2026-06-06, from cdisc.org):

| Standard | Version | Released |
|----------|---------|----------|
| SDTM | v2.1 | 10 June 2024 |
| SDTMIG | v3.4 | 29 November 2021 |
| CDASHIG | v2.3 | 28 September 2023 (references CDASH Model v1.3) |
| CDISC Controlled Terminology | quarterly | latest release noted 27 March 2026 |

---

## Sources

- CDISC — SDTM overview (definition, observation classes, FDA/PMDA requirement,
  domain codes, latest versions): https://www.cdisc.org/standards/foundational/sdtm
- CDISC — CDASH overview (definition, SDTM relationship, Model vs IG, latest
  version): https://www.cdisc.org/standards/foundational/cdash
- CDISC — Controlled Terminology (definition, NCI-EVS maintenance, quarterly
  cadence): https://www.cdisc.org/standards/terminology/controlled-terminology

CDISC standards are governed by CDISC; NCI-EVS hosts the controlled terminology.
This skill maps to the standards; it does not redistribute codelist contents.
