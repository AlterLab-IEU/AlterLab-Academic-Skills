---
name: lit-review
description: Run a systematic, reproducible literature review on a topic and return an APA 7.0 annotated bibliography with a documented search strategy. Invokes the alterlab-deep-research pipeline in lit-review mode.
argument-hint: [topic or research question]
disable-model-invocation: true
allowed-tools: Read Write Edit Bash WebFetch WebSearch
---

Run a **literature review** on: $ARGUMENTS

Use the `alterlab-deep-research` skill in **lit-review mode**. Do not run the full
6-phase research pipeline or compile a standalone report — scope the work to a
reproducible literature search and synthesis only.

Steps:
1. **Scope** — Restate the topic as a searchable question. List target databases,
   primary keywords plus synonyms, the Boolean strategy, date range, and
   inclusion/exclusion criteria *before* searching (delegate to the
   `bibliography_agent`).
2. **Search & verify** — Execute the documented search. For every source you intend
   to cite, confirm it actually exists (title/author/DOI) rather than asserting it
   from memory. Screen out predatory and retracted sources.
3. **Synthesize** — Group findings into themes, surface agreements/contradictions,
   and identify the gap the literature leaves open. Build a literature matrix.
4. **Output** — An APA 7.0 annotated bibliography plus a short thematic synthesis and
   the exact search strategy used, so another researcher can reproduce it.

If no topic was provided in $ARGUMENTS, ask for one before searching.

For deep-source verification of any specific claim or citation, hand off to
`/cite-check`. To carry the review forward into a full manuscript, hand off to
`/research-pipeline`.
