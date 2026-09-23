---
name: cite-check
description: Verify that citations actually exist and that the claims they support are faithful to the cited source. Runs deterministic existence checks (Crossref / OpenAlex / Semantic Scholar / arXiv) plus a claim-faithfulness pass via the alterlab-citation-verifier skill.
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
2. **Existence check** — Run `scripts/verify_citations.py` over the references. It
   resolves each one against Crossref, OpenAlex, Semantic Scholar, and arXiv (no API
   key required; optional `OPENALEX_API_KEY` / `S2_API_KEY` raise rate limits),
   checks DOI registration at doi.org, matches title and authors with the difflib
   `SequenceMatcher` ratio (≥ 0.70), and maps each entry to the TF / PAC / IH / PH
   taxonomy.
3. **Retraction screen** — Surface every `RETRACTED` flag (Crossref `updated-by` /
   `update-to` notices, including Retraction Watch data, or OpenAlex
   `is_retracted`) and any expression of concern.
4. **Claim faithfulness** — Where a sentence is tied to a citation, run
   `scripts/claim_faithfulness.py` on the (claim, DOI) pair; report `contradict` as
   SH and escalate `unsupported` claims (the abstract does not establish them) to the
   `--tier llm` judge or full-text reading.
5. **Report** — A per-citation table: verdict code (`verified` / `TF` / `PAC` / `IH`
   / `PH` / `SH` / `unverified`), flags, the source that confirmed it, and the matched
   DOI/ID. Summarize how many of N citations could not be verified and why
   (`source_status`).

If the network or a source is unavailable, say so explicitly: the script returns
`unverified` rather than a pass. For those entries, run the WebSearch fallback from
the SKILL.md "Graceful Degradation and the Fallback" section (three distinct
queries); anything still not found is reported as TF (NOT_FOUND), never as
"difficult to verify".
