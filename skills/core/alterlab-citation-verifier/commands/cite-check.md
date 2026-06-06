---
name: cite-check
description: Verify that citations actually exist and that the claims they support are faithful to the cited source. Runs deterministic existence checks (Crossref / OpenAlex / Semantic Scholar / arXiv) plus a claim-faithfulness pass via the alterlab-citation-verifier skill.
argument-hint: [path to .bib / manuscript, or pasted references]
disable-model-invocation: true
allowed-tools: Read Write Edit Bash WebFetch WebSearch
---

**Cite-check** the citations in: $ARGUMENTS

Use the `alterlab-citation-verifier` skill. This is a deterministic gate, not a
vibe check — do not assert that a reference is real because it *looks* plausible.

Steps:
1. **Collect** — Parse the references from $ARGUMENTS (a `.bib` file, a manuscript
   path, or a pasted list). If nothing was given, ask for the references or file.
2. **Existence check** — For each reference resolve it against Crossref, OpenAlex,
   Semantic Scholar, and arXiv (via the bundled academic MCP servers when enabled,
   otherwise the documented `requests`/WebSearch fallback). Match title and authors
   with a Levenshtein similarity threshold (≥ 0.70) and resolve any DOI / arXiv ID.
   Flag anything that matches nothing as **likely hallucinated**.
3. **Retraction screen** — Flag retracted or expression-of-concern items.
4. **Claim faithfulness** — Where a claim is tied to a citation, check the claim is
   actually supported by that source and map any mismatch to the
   TF / PAC / IH / PH / SH taxonomy.
5. **Report** — A per-citation table: verdict (verified / unverified / hallucinated /
   retracted), the resolver that confirmed it, and the matched DOI/ID. Summarize how
   many of N citations could not be verified.

Degrade gracefully and say so explicitly when no MCP server or network is available
(see `references/mcp_setup.md` for the fallback contract).
