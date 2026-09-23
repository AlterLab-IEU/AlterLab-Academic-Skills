# Playbook — citation-audit

**Goal:** every reference exists with correct metadata, and every cited claim says what its
source says. **Default output:** `alterlab-citation-audit.md`.

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
   the uncapped count is reported.
2. **Verify** — batches of ~12 references through `verify_citations.py`
   (alterlab-citation-verifier): `VERIFIED`, `PAC` (real work, wrong field — give the correction),
   `IH` (identifier resolves to a different work), `NOT_FOUND` (title search, author+year search,
   and identifier resolution all fail), or `UNVERIFIED` (the lookup itself failed). Retractions are
   flagged.
3. **Faithfulness** — claims whose sources exist are checked with `claim_faithfulness.py` or by
   reading the source: `SUPPORTED`, `PARTIAL`, `UNSUPPORTED`, `CONTRADICTED`, `UNCHECKABLE`, with a
   verbatim quote and, when not supported, a calibrated rewrite.
4. **Challenge** — every `PAC`, `IH`, `NOT_FOUND`, `UNVERIFIED`, `UNSUPPORTED`, and `CONTRADICTED`
   item gets **two independent re-checks** with different strategies (exact-title database search
   vs. author publication list / venue table of contents). A flag is withdrawn if either re-check
   finds concrete evidence (URL/DOI + quote) that it is wrong. Flags accuse authors of serious
   errors, so they must survive both.
5. **Report** — counts by taxonomy, one table per category with evidence and fix, the withdrawn
   flags, the method (sources, date), and an AI-assistance disclosure.

Taxonomy: **TF** total fabrication (NOT_FOUND after re-checks), **PAC** partial attribute
corruption, **IH** identifier hijacking, **PH** placeholder, **SH** semantic hallucination (real
source, claim unsupported or contradicted).

## Sequential playbook (no Workflow runtime)

1. Extract as above; save `references.json` and `claims.json`.
2. Run `verify_citations.py` on the whole reference list in one batch file.
3. Run `claim_faithfulness.py --input` on the claim pairs whose references exist.
4. For each flag, run the two re-check strategies **one after the other, writing each result down
   before starting the next**; withdraw the flag if either finds evidence.
5. Count categories with a short script over the saved verdicts; write the report.
If the document is long, audit in chunks (e.g. per chapter) and say which chunks were covered.

## Report skeleton

```markdown
# Citation integrity report — <manuscript>
| References | Claims checked | TF | PAC | IH | PH | SH | Unverified | Retracted |
## Fabricated references (TF)      | id | reference | searches run | action |
## Corrupted metadata (PAC)        | id | as cited | corrected | source |
## Identifier hijacking (IH)       | id | identifier | resolves to | fix |
## Placeholders (PH)
## Unsupported claims (SH)         | claim | source says (quote) | calibrated rewrite |
## Could not verify (re-run)       | id | reason |
## Withdrawn on re-check
## Method and AI disclosure
```

## Pitfalls

- Verifying from memory: the same training data that produced a plausible fake will "recognize" it.
- Treating `UNVERIFIED` (network failure) as `NOT_FOUND`.
- Book chapters: a real book with an invented chapter is a common fabrication — check the table of contents.
- Preprint vs. published version mismatches are `PAC`, not `TF`; cite the version of record.
