# Playbook — systematic-review-screening

**Goal:** title/abstract screening that meets PRISMA 2020 and Cochrane expectations — two
separate blinded screeners per record, disagreements resolved by a third reviewer, agreement
reported — where a record whose screening did not complete is never counted as screened.
**Default output folder:** `alterlab-screening/` (`codebook.md`, `records-*.jsonl`,
`records.jsonl`, `prisma-screening.md`, `included.jsonl`, `unresolved.jsonl`).

## Inputs

| Field | Default | Meaning |
|---|---|---|
| `question` (or the string argument) | required | the review question |
| `include` / `exclude` | derived | the team's criteria, kept verbatim in the codebook |
| `records` | none | an existing export (RIS, BibTeX, nbib, CSV, JSONL); skips searching |
| `databases` | `["pubmed", "openalex"]` | databases to search when no export is given |
| `max_per_database` | 300 (max 2000) | retrieval cap per database; hitting it is logged and makes the run `partial` |
| `batch` | 25 (5–60) | records per screening batch (raised automatically for very large sets so the run fits the agent cap) |
| `out_dir` | `alterlab-screening` | output folder |

## Stages and acceptance rules

1. **Protocol** — PICO(S), coded criteria (I1…, E1…) with a borderline example each, and the
   title/abstract rule: a record that cannot be excluded with confidence goes forward to full text.
   Database-native search strings (MeSH for PubMed). Saved as `codebook.md`.
2. **Search** (only without `records`) — one agent per database via the AlterLab database skills;
   exact query strings and total hit counts are kept for a PRISMA-S appendix. A failed search is
   retried once; a database that still failed, or had no search string, is named and makes the run
   `partial` (identification is incomplete). All searches failing makes it `blocked`.
3. **Deduplicate** — deterministic script: DOI, then PMID, then normalized title + year; stable
   `sid` numbering; per-source counts.
4. **Screen** — each batch is screened by screener A and screener B separately: include /
   exclude (with E-code) / unsure. Unsure counts as include at this stage. A failed batch is re-run
   once, and records a screener left out (or answered twice with different decisions) are re-sent
   once. Answers for sids that were not sent, or without a sid, are ignored and counted.
5. **Adjudicate** (conflicts computed in code). Resolution rules — conservative, nothing is
   silently excluded:

   | Screener decisions | Outcome |
   |---|---|
   | both decided, agree | their decision |
   | both decided, disagree | the third reviewer's decision |
   | only one decided | the third reviewer reviews it as the second reviewer; the decision stands only if the two agree |
   | neither decided (after the retry) | **UNRESOLVED** — not adjudicated by one agent alone |
   | adjudication needed but did not complete (after one retry) | **UNRESOLVED** |
   | one decided, the stand-in second reviewer disagrees | **UNRESOLVED** |

   UNRESOLVED records are **retained**: written to `unresolved.jsonl` with the reason, and not
   counted as screened, included, or excluded.
6. **Report** — opens with its status and coverage. PRISMA 2020 flow: identified (per source) →
   duplicates removed → submitted for screening → **screened** (records with a resolved decision) and
   **unresolved** (own row) → excluded at title/abstract (by criterion) → sought for retrieval.
   `screened + unresolved = submitted for screening`; `screened − excluded = sought for retrieval`.
   Percent agreement and Cohen's κ on the dual-screened records, with their number. The report and
   both JSONL files are read back from disk; a JSONL file with the wrong number of lines is not
   returned and keeps the run `partial`.

The run is `partial` when any screener decision is missing, any record is unresolved, a search
failed or was capped, or the 2,000-record cap applied; `blocked` when the protocol, every search, or
de-duplication failed, there were no records, or the report could not be written or found.

## Agreement statistics (computed, not estimated)

With `a`, `b` = each screener's pass/exclude decision on the records both decided:

```
po = agreements / n
pe = (A_pass/n)(B_pass/n) + (A_excl/n)(B_excl/n)
κ  = (po − pe) / (1 − pe)        # not defined when pe = 1 (one category used throughout)
```

κ ≥ 0.6 is commonly read as substantial agreement; low κ usually means the codebook needs a
clearer rule, not that a screener is wrong. Both screeners are agents of the same model, so κ here
measures consistency between two runs of one model — not agreement between independent human
screeners — and the report says so.

## Returned payload

| Field | Contents |
|---|---|
| `status`, `status_reasons`, `report` | see `running-workflows.md` |
| `flow` | `identified`, `duplicates_removed`, `records_after_deduplication`, `submitted_for_screening`, `screened`, `unresolved`, `excluded_title_abstract`, `excluded_by_criterion`, `sought_for_retrieval`, `not_screened_this_run` |
| `included_sids`, `unresolved` | resolved includes; unresolved records with their reasons |
| `agreement_percent`, `kappa`, `kappa_records` | computed on dual-screened records only |
| `files` | `included` / `unresolved` JSONL paths, or `null` when not read back with the right line count |
| `coverage` | `searches`, `screening` (`screener_decisions` requested = 2 × records, records with both / one / no screener), `adjudication`, `records` (`resolved`, `unresolved`, `resolved_by`), `report`, `id_issues`, agent totals |

## Sequential playbook

Build the codebook. Screen all records as screener A and save the decisions; then, **without
reopening A's decisions**, screen them again as screener B from the codebook alone and save.
Compute conflicts and κ with a script, adjudicate conflicts, and produce the flow table with
unresolved records on their own row. For more than ~150 records, do it in batches and report which
batches were completed.

## Next steps (outside this workflow)

Screen the unresolved records by hand; then full-text eligibility, data extraction, and risk of
bias (`alterlab-literature-review`), pooling (`alterlab-meta-analysis`), preregistration of the
protocol (PROSPERO / OSF via `alterlab-open-science`).

## Pitfalls

- Letting the second pass see the first — dual screening only means something if the second pass is
  blind to the first; and two passes of one model still share its blind spots, unlike two human screeners.
- Excluding on "unsure" at title/abstract stage.
- Counting a record whose screening failed as screened, included, or excluded.
- Reporting κ without the percent agreement and the number of records it is computed on.
- Silent retrieval caps: always report `total_hits` next to what was retrieved.
