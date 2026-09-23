---
name: alterlab-grant-reporting
description: Drafts post-award grant deliverables across funder formats — NIH RPPR (Annual, multi-year-funded, Interim, Final via eRA Commons), NSF annual/final project reports and the public Project Outcomes Report (Research.gov), and Horizon Europe / ERC periodic and final reports (technical Part A/B + financial statements on the EU Funding & Tenders Portal) — plus milestone and deliverable tracking, budget-vs-actual variance narratives, no-cost-extension and rebudgeting justifications, and effort/closeout reporting. Computes report due dates from the award period with scripts/report_deadlines.py. Use when the user needs a grant progress or final report, post-award reporting, an RPPR, a periodic report, a no-cost-extension request, milestone tracking, or a budget-variance narrative. For writing new proposals prefer alterlab-research-grants; for TÜBİTAK proposals prefer alterlab-tubitak-proposal. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*) Bash
compatibility: No API key, account, or network required — report-format guidance plus a stdlib-only deadline calculator (scripts/report_deadlines.py); the user still submits through the funder's own portal (eRA Commons / Research.gov / EU Funding & Tenders Portal)
metadata:
  skill-author: AlterLab
  version: "1.1.0"
  last_updated: "2026-09-23"
---

# Grant Reporting — Post-Award Deliverables Across Funder Formats

Post-award is where money already won has to be *kept*: funders release the next
tranche only when a compliant progress report lands on time, and they claw back
or flag awards when reports slip or numbers don't reconcile. This skill drafts
those deliverables — progress/annual reports, final reports, milestone and
deliverable tracking, budget-vs-actual narratives, and no-cost-extension (NCE)
and rebudgeting justifications — in the exact shape each major funder demands.

It is the **post-award** counterpart to the pre-award proposal skills: it never
writes a new proposal or a fresh budget request. It reports against an award
that already exists.

## When to Use This Skill

Use this skill when the user needs to:

- Draft an **NIH RPPR** (Research Performance Progress Report) — Annual
  (SNAP, non-SNAP, or multi-year funded), Interim, or Final — section by section.
- Draft an **NSF annual or final project report**, or the public-audience
  **Project Outcomes Report**.
- Draft a **Horizon Europe / ERC periodic or final report** — the technical
  narrative (Part B) and the structured-table / financial-statement framing.
- Track **milestones and deliverables** against a workplan and write the status
  narrative.
- Write a **budget-vs-actual (variance) narrative** explaining over/under-spend
  by category.
- Justify a **no-cost extension** or a **rebudgeting / virement** request.
- Work out **when** each report is due from the award start/end dates
  (`scripts/report_deadlines.py`).

### Does NOT Trigger — route these elsewhere

| The request is really about… | Route to |
|------------------------------|----------|
| Writing a **new** proposal / project description for NSF, NIH, DOE, DARPA, NSTC (pre-award) | `alterlab-research-grants` |
| A **TÜBİTAK** proposal (1001, 1002, etc.) — Turkish funder, pre-award | `alterlab-tubitak-proposal` |
| **Akademik Teşvik** annual incentive-points application (ÜAK) | `alterlab-akademik-tesvik` |
| A **data management plan** / KVKK-compliant DMP for the proposal stage | `alterlab-kvkk-dmp` |
| A **recommendation / reference letter** for a student or colleague | `alterlab-recommendation-letters` |
| Program / department **accreditation** assessment & assurance-of-learning reports | `alterlab-accreditation-aol` |
| Verifying that the **citations** in the report actually exist | `alterlab-citation-verifier` |

This skill assumes the award is already made. If the user is still competing for
funding, stop and route to the pre-award skill above.

## The funder formats (verified)

Each funder fixes the structure; do not invent sections. Deep per-funder detail —
every section, what goes in it, and which sections apply to which report type —
lives in [`references/funder_formats.md`](references/funder_formats.md). The
essentials:

### NIH — RPPR (submitted in eRA Commons)

Three report types share one section skeleton (**A–I**), per the NIH RPPR
Instruction Guide (eRA, January 2026):

| § | Title | Note |
|---|-------|------|
| A | Cover Page | |
| B | Accomplishments | goals, what was done (B.2 ≤ 2 pages for most awards), training, dissemination, next-period plans |
| C | Products | C.1 publications (each must comply with the NIH Public Access Policy), datasets, software, IP; **C.5.c** progress against the Data Management and Sharing Plan |
| D | Participants | personnel + effort; Common Form Biosketch / Current and Pending (Other) Support (SciENcv) for new or changed senior/key personnel — enforced since 8 May 2026; **only D.1 on Interim/Final** |
| E | Impact | impact on the field, other disciplines, society |
| F | Changes | challenges/delays and significant changes to human subjects, animals, biohazards, select agents; **Annual only — not on Interim/Final** |
| G | Special Reporting Requirements | G.1 award-term items, incl. each senior/key person's annual malign-foreign-talent-program certification (RPPRs submitted on or after 25 Jan 2026); G.10 unobligated balance > 25% |
| H | Budget | **Annual non-SNAP only** — not on Interim/Final |
| I | Outcomes | **required on Interim & Final**, public-facing |

Report types: **Annual** (next budget period; SNAP, non-SNAP, or multi-year funded
(MYF) — NIH has fully funded many new awards up front since FY2025, and those
file an annual RPPR on each award anniversary), **Interim** (filed when a Type 2
renewal is submitted — becomes the Final report if the renewal is not funded),
**Final** (closeout). The RPPR is not a vehicle for requesting a change of scope;
that needs separate prior approval. See the references file before drafting.

### NSF — project reports (submitted in Research.gov)

- **Annual project report** — that year's activities and broader impacts.
- **Final project report** — refers only to the final funded year (it is *not*
  cumulative).
- **Project Outcomes Report (POR)** — a public-audience summary of **no more than
  800 words**, separate from the final report.
- Policy base: PAPPG NSF 24-1 plus Supplements 1–2 (NSF deferred a 26-1 edition).
  Since Supplement 2 (awards issued on or after 22 Jan 2026) journal articles go
  to the NSF Public Access Repository (NSF-PAR) by the publication date with no
  embargo, PAR metadata auto-populates the report's products, and datasets can no
  longer be typed directly into a project report.

### Horizon Europe / ERC — periodic & final reports (EU Funding & Tenders Portal)

- A **Technical Report** in two parts: **Part A** (structured tables, generated by
  the Portal from the Continuous Reporting module) and **Part B** (the narrative,
  mirroring the application form and reporting differences/deviations).
- A **Financial Report**: individual and consolidated **Financial Statements**
  (plus a Certificate on the Financial Statements where the threshold applies).
- A **Continuous Reporting** module that stays open for the whole project and
  feeds Part A automatically.
- **Lump-sum grants** declare completed work packages instead of actual costs:
  the financial statement is generated from the work packages declared complete,
  and the use-of-resources explanation and CFS do not apply.
- **ERC** splits reporting into a **scientific report** (interim, typically after
  month 24 of a 5-year grant) and a **periodic (financial) report** (typically
  after month 30), each due within 60 days of its own period end; for the final
  period both are submitted together.

## Deadlines — compute them, don't guess

Reporting deadlines are deterministic functions of the award dates, and missing
one can suspend payments. Use the helper instead of recalling rules from memory:

```bash
uv run python skills/faculty-life/alterlab-grant-reporting/scripts/report_deadlines.py \
    --funder nih-snap --budget-period-start 2026-09-01 --project-end 2028-08-31
```

It encodes only the verified rules (sourced in `references/funder_formats.md`):

- **NIH SNAP** Annual RPPR due the **15th of the month before the month in which
  the budget period ends** (ends 30 Nov → due 15 Oct); **non-SNAP** due the
  **1st** of that month (→ 1 Oct); a weekend or federal-holiday date moves to the
  next business day. **MYF** (`--funder nih-myf`) due on or before each award
  anniversary. **Final** or **Interim RPPR** within **120 days** of the
  period-of-performance end.
- **NSF** annual report **90 days before** the budget-period end; final report and
  Project Outcomes Report within **120 days** after the award end date.
- **Horizon Europe / ERC** periodic (and final) report within **60 days** after
  each reporting period ends.

The script prints the computed due dates as a table or JSON; it does no network
I/O and always tells the user to confirm against the funder's own notice of
award, because programs can override these defaults. It shifts weekend dates but
does not model US federal holidays, so a date it prints is never later than the
real deadline.

## How to draft a report

1. **Identify the funder and report type** first — that fixes the template. If the
   user hasn't said, ask (NIH vs NSF vs EU; Annual vs Final).
2. **Pull the deadline** with `report_deadlines.py` from the award dates and lead
   with it, so the user knows the time pressure.
3. **Gather the inputs** the sections need: aims/objectives and milestones,
   what was accomplished this period, products (publications, data, software),
   personnel and effort, and the budget figures (planned vs actual).
4. **Draft section by section** in the funder's own order and headings. Never
   merge or rename funder sections. For each accomplishment, tie it back to a
   stated aim or deliverable.
5. **Write the variance narrative** for any budget category off plan: state the
   planned vs actual amount, the *reason*, and the corrective action or the
   rebudgeting/NCE request it motivates. Detail and templates:
   [`references/budget_variance.md`](references/budget_variance.md).
6. **For an NCE or rebudgeting request**, use the justification structure in
   [`references/nce_rebudget.md`](references/nce_rebudget.md): unspent-funds
   status, the programmatic reason, the revised timeline, and the explicit
   confirmation that no new scope or new funds are requested.
7. **Flag, never fabricate.** Where a number, a publication, or an outcome is
   missing, mark it `[TODO: confirm]` for the user — do not invent figures,
   dates, DOIs, or results. If citations are involved, hand the reference list to
   `alterlab-citation-verifier`.

## Guardrails

- **No invented facts.** Budget figures, effort percentages, milestone dates,
  publication details, and award numbers come only from the user's materials. Mark
  anything missing as a `[TODO]` placeholder.
- **The user submits, not the skill.** This skill drafts text; the user files it
  through eRA Commons / Research.gov / the EU Funding & Tenders Portal. The skill
  has no portal access and claims none.
- **Confirm deadlines against the notice of award.** The calculator encodes the
  general rules; specific programs and cooperative agreements can override them.
- **Reporting period boundaries matter.** An NSF final report covers only the
  final funded year; an NIH Interim/Final RPPR adds Section I Outcomes and drops
  Sections F and H (and B.6 plans). Don't carry the wrong scope across report
  types.
- **Surface compliance items early.** Non-compliant NIH publications listed in
  C.1 have to be brought into Public Access compliance before the award renews
  on time, and NIH notes this generally takes weeks; the senior/key-personnel
  MFTRP certifications (G.1) and, for awards under the 2023 DMS Policy, DMS-plan
  progress (C.5.c) are required entries.
  Ask about all three before drafting rather than at submission.

## References

- [`references/funder_formats.md`](references/funder_formats.md) — full NIH RPPR
  A–I section guide (with which sections apply to Annual/Interim/Final), NSF
  report types, and Horizon Europe / ERC report structure, each with its source.
- [`references/budget_variance.md`](references/budget_variance.md) — budget-vs-actual
  narrative template, variance categories, and worked examples.
- [`references/nce_rebudget.md`](references/nce_rebudget.md) — no-cost-extension and
  rebudgeting/virement justification structures and the questions each funder asks.
- `scripts/report_deadlines.py` — stdlib-only report-deadline calculator.

Part of the AlterLab Academic Skills suite.
