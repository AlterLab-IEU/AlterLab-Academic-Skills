# Playbook — review-panel

**Goal:** a peer review from reviewers who never see each other's reports, with no major concern
that misreads the manuscript. **Default output:** `alterlab-review-panel.md`.

## Inputs

| Field | Default | Meaning |
|---|---|---|
| `path` (or the string argument) | required | manuscript file |
| `venue` | none | target journal or conference; shapes norms and length expectations |
| `field` | detected | override the detected field |
| `lenses` | chosen for the paper | list of reviewer roles (strings or `{key, title, focus}`), max 6 |
| `out` | `alterlab-review-panel.md` | report path |

## Stages and acceptance rules

1. **Profile** — field, paper type, design, and the applicable reporting guideline (CONSORT,
   STROBE, PRISMA, COREQ/SRQR, ARRIVE, TRIPOD, …). Choose 4–5 lenses specific to this paper:
   methodology; domain contribution; statistics and reproducibility (analytic rigor for
   qualitative work); a devil's advocate on the central claim; ethics and reporting standards when
   humans/animals are involved or a guideline applies.
2. **Review** — one reviewer per lens, each in its own context, each reading the whole paper.
   Every concern has a location and, where possible, a verbatim quote and a resolution. Major
   means it threatens a main conclusion.
3. **Verify** — each major concern is re-read against the manuscript (methods, supplements,
   limitations) by a fresh agent; a concern is withdrawn if the paper already addresses it or the
   reviewer misread it, with the settling quote either way.
4. **Decide** — the editor weighs the validated concerns and the recommendation tally (computed,
   not estimated), maps agreement and disagreement, and writes a revision roadmap.

## Sequential playbook

Profile first. Then write each lens's review **completely, one at a time, saving each before
starting the next**, and do not edit an earlier review after reading a later one — that is the
anchoring the separate agents prevent. Re-read the manuscript for every major concern before
keeping it. Tally recommendations with a counter, then write the decision.

## Report skeleton

```markdown
# Editorial decision — <title>  (simulated panel)
Decision: major_revision   Tally: {major_revision: 3, minor_revision: 1}
## Where reviewers agree / disagree
## Revision roadmap
### Must address (validated major concerns, grouped by theme)
### Should address (minor)
## Reviewer reports (1…n)
## Concerns withdrawn after re-reading the manuscript
## AI-assistance disclosure
```

## Pitfalls

- One context playing five reviewers produces one opinion in five voices.
- Reviewers asking for work the paper already did (check the supplement before keeping the concern).
- Treating the simulated decision as a prediction of the journal's decision.
