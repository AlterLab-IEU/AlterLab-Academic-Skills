---
name: review-paper
description: Run a full multi-perspective peer review of a manuscript, simulating an Editor-in-Chief plus three peer reviewers and a Devil's Advocate, and produce a structured editorial decision and revision roadmap. Invokes the alterlab-paper-reviewer skill.
argument-hint: [path to manuscript, or paste the paper]
disable-model-invocation: true
allowed-tools: Read Write Edit Bash WebFetch WebSearch
---

**Review the paper**: $ARGUMENTS

Use the `alterlab-paper-reviewer` skill in **full review mode**.

Steps:
1. **Identify the field** and configure the 5-member review team (Editor-in-Chief +
   3 peer reviewers + Devil's Advocate), each covering a non-overlapping perspective:
   methodology, domain expertise, cross-disciplinary viewpoint, and core-argument
   challenge.
2. **Review** — Each reviewer produces specific, line-referenced comments against the
   review-criteria framework and statistical-reporting standards. The Devil's Advocate
   actively hunts logical fallacies and the strongest counter-arguments.
3. **Synthesize** — The Editor-in-Chief reconciles the reviews into one structured
   **Editorial Decision** (accept / minor / major / reject) and a prioritized
   **Revision Roadmap**.
4. **Output** — A peer-review report plus the editorial decision, using the skill's
   templates.

If no manuscript was provided in $ARGUMENTS, ask for the file or text first.

To verify the manuscript's citations before or after review, hand off to
`/cite-check`. For the full research-to-publication workflow, use `/research-pipeline`.
