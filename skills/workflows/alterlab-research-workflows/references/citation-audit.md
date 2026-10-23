# Playbook — citation-audit

**Goal:** every reference exists with correct metadata, and each cited claim checked (up to 150)
says what its source says — with an exact account of what was and was not checked.
**Default output:** `alterlab-citation-audit.md`.

## Inputs

| Field | Default | Meaning |
|---|---|---|
| `path` (or the string argument) | required | manuscript: `.md`, `.tex` (+ its `.bib`), `.docx`, or `.pdf` |
| `mailto` | none | contact email for Crossref's polite pool (OpenAlex ignores mailto since Feb 2026 — set `OPENALEX_API_KEY` instead) |
| `out` | `alterlab-citation-audit.md` | report path |

## Stages and acceptance rules

1. **Extract** — reference list (with DOI/arXiv ids), each citing sentence verbatim mapped to its
   reference ids, and unresolved placeholders (`[CITATION NEEDED]`, `(Author, YYYY)`, `??`). At
   most 150 citing sentences, chosen by consequence (quantitative, causal, abstract, discussion);
   the uncapped count (`claims_total`) is carried into the counts and the report, and a cap makes
   the run `partial`. Claims are numbered C1, C2, … by the workflow; a reference without an id, or
   with a repeated id, is still verified under a suffixed id and the repetition is reported.
2. **Verify** — batches of ~12 references through `verify_citations.py`
   (alterlab-citation-verifier): `VERIFIED`, `PAC` (real work, wrong field — give the correction),
   `IH` (identifier resolves to a different work), `NOT_FOUND` (title search, author+year search,
   and identifier resolution all fail), or `UNVERIFIED` (the lookup itself failed). Retractions are
   flagged. A failed batch is re-run once and references a batch left out are re-sent once; a
   reference still without a verdict is listed as unchecked, never as verified. If the verifier
   reports `status: partial` (exit 3), the entries listed as rejected or unsupported in its
   `input_accounting` were not checked: record them as `UNVERIFIED`, not as a pass.
3. **Faithfulness** — claims whose sources were not judged `NOT_FOUND`/`IH` are checked with
   `claim_faithfulness.py` or by reading the source: `SUPPORTED`, `PARTIAL`, `UNSUPPORTED`,
   `CONTRADICTED`, `UNCHECKABLE`, with a verbatim quote and, when not supported, a calibrated
   rewrite. Claims citing an id that is not in the reference list (or no id) are listed as not
   checkable. `claims_checked` counts claims that received a verdict — not claims sent.
4. **Challenge** — every `PAC`, `IH`, `NOT_FOUND`, `UNVERIFIED`, `UNSUPPORTED`, and `CONTRADICTED`
   item gets **two separate re-checks** with different strategies (exact-title database search
   vs. author publication list / venue table of contents); a failed re-check is retried once. A
   flag is withdrawn if a completed re-check finds concrete evidence (URL/DOI + quote) that it is
   wrong. It counts toward TF/PAC/IH/SH only when **both** re-checks completed without overturning
   it; with fewer than two completed re-checks it is **provisional** — listed with its count of
   completed re-checks and excluded from the category counts. Both re-checks are agents of the
   same model as the verifier, so surviving them is a stronger screen, not independent proof.
5. **Report** — opens with `Status: COMPLETE|PARTIAL` and a coverage table; counts by taxonomy,
   one table per category with evidence and fix, provisional flags, a "Not checked" section,
   withdrawn flags, the method (sources, date, the same-model caveat), and an AI-assistance
   disclosure. A separate agent then reads the file back; only then is its path returned.

Taxonomy: **TF** total fabrication (NOT_FOUND after both re-checks completed), **PAC** partial
attribute corruption, **IH** identifier hijacking, **PH** placeholder, **SH** semantic
hallucination (real source, claim unsupported or contradicted).

The run is `partial` when any reference or checkable claim has no verdict, a flag is provisional,
a reference stays `UNVERIFIED`, a claim is `UNCHECKABLE`, or the 150-claim cap applied; `blocked`
when extraction failed, there is no reference list, or the report could not be written or found.

## Returned payload

| Field | Contents |
|---|---|
| `status`, `status_reasons`, `report` | see `running-workflows.md`; `report` is `null` unless the file was read back |
| `counts` | `references`, `references_with_verdict`, `claims_total` (uncapped), `claims_extracted`, `claims_checkable`, `claims_checked` (with a verdict), `claims_uncheckable`, `TF`, `PAC`, `IH`, `PH`, `SH`, `unverified`, `retracted`, `flags_overturned_on_recheck`, `flags_recheck_incomplete` |
| `unchecked` | `references_without_verdict`, `claims_without_verdict`, `claims_not_checkable` (id + reason), `claims_not_extracted` (count beyond the cap), `flags_recheck_incomplete` (id, category, `rechecks_completed`) |
| `coverage` | `extraction`, `references`, `claims`, `rechecks` (`flags`, `requested` = 2 × flags, `dispatched`, `completed`, `failed`, `retried`, `flags_stood`, `flags_overturned`, `flags_recheck_incomplete`), `report`, `id_issues`, agent totals |

## Sequential playbook (no Workflow runtime)

1. Extract as above; save `references.json` and `claims.json`; note `claims_total`.
2. Run `verify_citations.py` on the whole reference list in one batch file.
3. Run `claim_faithfulness.py --input` on the claim pairs whose references exist.
4. For each flag, run the two re-check strategies **one after the other, writing each result down
   before starting the next**; withdraw the flag if either finds evidence. A flag with only one
   completed re-check is provisional, not confirmed.
5. Count categories with a short script over the saved verdicts, counting only verdicts actually
   returned; write the report, starting with the status and what was not checked.
If the document is long, audit in chunks (e.g. per chapter) and say which chunks were covered.

## Report skeleton

```markdown
# Citation integrity report — <manuscript>
Status: PARTIAL — 140 of 150 extracted claims checked; 212 citing sentences in total (cap 150)
| Stage | Requested | Dispatched | Completed | Failed | Unresolved | Retried |
| References | Claims checked | TF | PAC | IH | PH | SH | Unverified | Retracted |
## Fabricated references (TF)      | id | reference | searches run | action |
## Corrupted metadata (PAC)        | id | as cited | corrected | source |
## Identifier hijacking (IH)       | id | identifier | resolves to | fix |
## Placeholders (PH)
## Unsupported claims (SH)         | claim | source says (quote) | calibrated rewrite |
## Could not verify (re-run)       | id | reason |
## Provisional flags — re-check incomplete   | id | category | re-checks completed |
## Not checked                      references / claims without a verdict, not checkable, beyond the cap
## Withdrawn on re-check
## Method, same-model caveat, and AI disclosure
```

## Pitfalls

- Verifying from memory: the same training data that produced a plausible fake will "recognize" it.
- Treating `UNVERIFIED` (network failure) as `NOT_FOUND`.
- Counting a claim as checked because it was sent to a checker; count returned verdicts.
- Reporting a flag as confirmed when a re-check never ran.
- Book chapters: a real book with an invented chapter is a common fabrication — check the table of contents.
- Preprint vs. published version mismatches are `PAC`, not `TF`; cite the version of record.
