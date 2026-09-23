# Playbook — systematic-review-screening

**Goal:** title/abstract screening that meets PRISMA 2020 and Cochrane expectations — two
independent screeners per record, disagreements resolved by a third reviewer, agreement reported.
**Default output folder:** `alterlab-screening/` (`codebook.md`, `records-*.jsonl`,
`records.jsonl`, `prisma-screening.md`, `included.jsonl`).

## Inputs

| Field | Default | Meaning |
|---|---|---|
| `question` (or the string argument) | required | the review question |
| `include` / `exclude` | derived | the team's criteria, kept verbatim in the codebook |
| `records` | none | an existing export (RIS, BibTeX, nbib, CSV, JSONL); skips searching |
| `databases` | `["pubmed", "openalex"]` | databases to search when no export is given |
| `max_per_database` | 300 (max 2000) | retrieval cap per database; hitting it is logged |
| `batch` | 25 (5–60) | records per screening batch |
| `out_dir` | `alterlab-screening` | output folder |

## Stages and acceptance rules

1. **Protocol** — PICO(S), coded criteria (I1…, E1…) with a borderline example each, and the
   title/abstract rule: a record that cannot be excluded with confidence goes forward to full text.
   Database-native search strings (MeSH for PubMed). Saved as `codebook.md`.
2. **Search** (only without `records`) — one agent per database via the AlterLab database skills;
   exact query strings and total hit counts are kept for a PRISMA-S appendix.
3. **Deduplicate** — deterministic script: DOI, then PMID, then normalized title + year; stable
   `sid` numbering; per-source counts.
4. **Screen** — each batch is screened by screener A and screener B independently: include /
   exclude (with E-code) / unsure. Unsure counts as include at this stage.
5. **Adjudicate** (conflicts computed in code) — every disagreement, and every record a screener
   skipped, goes to a third reviewer. A record without a final decision goes forward by default —
   nothing is silently excluded.
6. **Report** — PRISMA 2020 flow: identified (per source) → duplicates removed → screened →
   excluded at title/abstract (by criterion) → sought for retrieval. Percent agreement and Cohen's κ.

## Agreement statistics (computed, not estimated)

With `a`, `b` = each screener's pass/exclude decision on the records both decided:

```
po = agreements / n
pe = (A_pass/n)(B_pass/n) + (A_excl/n)(B_excl/n)
κ  = (po − pe) / (1 − pe)        # not defined when pe = 1 (one category used throughout)
```

κ ≥ 0.6 is commonly read as substantial agreement; low κ usually means the codebook needs a
clearer rule, not that a screener is wrong.

## Sequential playbook

Build the codebook. Screen all records as screener A and save the decisions; then, **without
reopening A's decisions**, screen them again as screener B from the codebook alone and save.
Compute conflicts and κ with a script, adjudicate conflicts, and produce the flow table. For
more than ~150 records, do it in batches and report which batches were completed.

## Next steps (outside this workflow)

Full-text eligibility, data extraction, and risk of bias (`alterlab-literature-review`), pooling
(`alterlab-meta-analysis`), preregistration of the protocol (PROSPERO / OSF via
`alterlab-open-science`).

## Pitfalls

- Letting the second pass see the first — dual screening only means something if it is independent.
- Excluding on "unsure" at title/abstract stage.
- Reporting κ without the percent agreement and the number of records it is computed on.
- Silent retrieval caps: always report `total_hits` next to what was retrieved.
