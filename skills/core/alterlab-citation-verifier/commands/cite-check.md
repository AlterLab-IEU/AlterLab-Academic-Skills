---
name: cite-check
description: Verify that citations actually exist and that the claims they support are faithful to the cited source. Runs deterministic existence checks (Crossref / Semantic Scholar / Europe PMC / arXiv) plus a claim-faithfulness pass via the alterlab-citation-verifier skill.
argument-hint: [path to .bib / manuscript, or pasted references]
disable-model-invocation: true
allowed-tools: Read Write Edit Bash WebFetch WebSearch
---

**Cite-check** the citations in: $ARGUMENTS

Use the `alterlab-citation-verifier` skill. Decide each verdict from the script
output and retrieved records, not from whether a reference looks plausible or
familiar: a model's memory shares the training data that produces fabricated
references, so it cannot confirm them.

Steps:
1. **Collect** — Parse the references from $ARGUMENTS (a `.bib` file, a manuscript
   path, or a pasted list). If nothing was given, ask for the references or file.
2. **Existence check** — Run
   `${CLAUDE_PLUGIN_ROOT}/alterlab-citation-verifier/scripts/verify_citations.py` over the references. It
   resolves each one against Crossref, Semantic Scholar, Europe PMC and arXiv, with
   Open Library for books (no API key
   required; an optional `S2_API_KEY` raises Semantic Scholar's rate limit),
   checks DOI registration at doi.org, matches title and authors with the difflib
   `SequenceMatcher` ratio (≥ 0.70), and maps each entry to the verified / PAC / IH /
   ID_INVALID / NOT_FOUND / PH / unverified verdicts. `NOT_FOUND` means absent from the
   indexes that answered — not proof of fabrication; `ID_INVALID` means the DOI / arXiv ID is
   wrong and the work is undetermined. The script never emits `TF` (since report schema 2).
3. **Retraction screen** — Surface every `RETRACTED` flag (Crossref `updated-by` /
   `update-to` notices, including Retraction Watch data) and any expression of
   concern. Report each found entry's `retraction.status` (`flagged` /
   `not_flagged_in_checked_sources` / `unknown`); `unknown` (`retracted: null`) means the
   check did not happen — never say "not retracted" for it.
4. **Claim faithfulness** — Where a sentence is tied to a citation, run
   `${CLAUDE_PLUGIN_ROOT}/alterlab-citation-verifier/scripts/claim_faithfulness.py` on the (claim, DOI) pair; report `contradict` as
   SH and escalate `unsupported` claims (the abstract does not establish them) to the
   `--tier llm` judge or full-text reading. Neither kind of `support` is a verification: a
   heuristic one (`LEXICAL_MATCH_REQUIRES_REVIEW`) is a word match and an llm-tier one
   (`MODEL_JUDGED_SUPPORT_REQUIRES_REVIEW`) is one model's reading of the abstract. Report
   both as "needs review"; count a claim as supported only after reading the cited passage.
5. **Report** — First the `input_accounting` counts (detected / parsed / rejected /
   unsupported) and any PARTIAL status — a partial run is not a pass, and neither is
   REVIEW_REQUIRED (≥ 1 `NOT_FOUND`) or UNVERIFIED. Then a per-citation table: verdict code
   (`verified` / `PAC` / `IH` / `ID_INVALID` / `NOT_FOUND` / `PH` / `SH` / `unverified`), flags, the source that confirmed it, and the matched
   DOI/ID. Summarize how many of N citations could not be verified and why
   (`source_status`).

If the network or a source is unavailable, say so explicitly: the script returns
`unverified` rather than a pass. For those entries and every `NOT_FOUND`, run the
WebSearch fallback from the SKILL.md "Graceful Degradation and the Fallback" section
(three distinct queries); anything still not found is reported as `NOT_FOUND` with the
queries documented, never as "difficult to verify". Call it fabricated (`TF`) only as the
analyst's conclusion on that documented search, never on the script's output alone.
