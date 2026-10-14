# Playbook — review-panel

**Goal:** a peer review from reviewers who never see each other's reports, with no major concern
that misreads the manuscript, and no concern presented as validated unless its re-read completed.
**Default output:** `alterlab-review-panel.md`.

## Inputs

| Field | Default | Meaning |
|---|---|---|
| `path` (or the string argument) | required | manuscript file |
| `venue` | none | target journal or conference; shapes norms and length expectations |
| `field` | detected | override the detected field |
| `lenses` | chosen for the paper | list of reviewer roles (strings or `{key, title, focus}`), max 6 — extra lenses are counted and the run is `partial` |
| `out` | `alterlab-review-panel.md` | report path |

## Stages and acceptance rules

1. **Profile** — field, paper type, design, and the applicable reporting guideline (CONSORT,
   STROBE, PRISMA, COREQ/SRQR, ARRIVE, TRIPOD, …). Choose 4–5 lenses specific to this paper:
   methodology; domain contribution; statistics and reproducibility (analytic rigor for
   qualitative work); a devil's advocate on the central claim; ethics and reporting standards when
   humans/animals are involved or a guideline applies. If profiling fails twice the run is `blocked`.
2. **Review** — one reviewer per lens, each in its own context, each reading the whole paper.
   Every concern has a location and, where possible, a verbatim quote and a resolution. Major
   means it threatens a main conclusion. A reviewer that fails is retried once; reviewers still
   missing are named, and the tally covers reporting reviewers only. The same concern listed twice
   counts once; two different concerns sharing an id are both kept.
3. **Verify** — each major concern is re-read against the manuscript (methods, supplements,
   limitations) by a fresh agent, retried once on failure. Three outcomes, kept apart:
   **validated** (re-read completed, concern stands), **withdrawn** (re-read completed, the paper
   already addresses it or the reviewer misread it — with the settling quote), and **unverified**
   (the check did not complete). Unverified concerns reach the editor in their own labelled list,
   never as validated.
4. **Decide** — the editor weighs the validated concerns and the recommendation tally (computed,
   not estimated), maps agreement and disagreement, and writes a revision roadmap. The package
   opens with its status and coverage, says the reviewers are separate agents of one model (their
   agreement is not independent confirmation), and is read back from disk before its path is returned.

The run is `partial` when a reviewer did not report, a major concern is unverified, or the lens cap
applied; `blocked` when profiling or every reviewer failed, or the package could not be written or found.

## Returned payload

| Field | Contents |
|---|---|
| `status`, `status_reasons`, `report` | see `running-workflows.md` |
| `reviewers` | `requested`, `used` (after the 6-lens cap), `completed`, `missing` (titles) |
| `major_concerns` | `raised`, `validated`, `unverified`, `withdrawn` |
| `concerns` | the `validated`, `unverified`, and `withdrawn` lists (reviewer, id, issue, location) |
| `recommendations`, `decision` | tally of reporting reviewers; the editor's one-word decision and rationale |
| `coverage` | `reviewers` and `concern_checks` (requested / dispatched / completed / failed / unresolved / retried), `report`, `id_issues`, agent totals |

## Sequential playbook

Profile first. Then write each lens's review **completely, one at a time, saving each before
starting the next**, and do not edit an earlier review after reading a later one — that is the
anchoring the separate agents prevent. Re-read the manuscript for every major concern before
keeping it; a concern you did not re-read is unverified. Tally recommendations with a counter,
then write the decision.

## Report skeleton

```markdown
# Editorial decision — <title>  (simulated panel)
Status: PARTIAL — 4 of 5 reviewers reported; 1 of 7 major concerns unverified
Decision: major_revision   Tally: {major_revision: 3, minor_revision: 1}
## Where reviewers agree / disagree
## Revision roadmap
### Must address (validated major concerns, grouped by theme)
### Raised but not yet checked (unverified major concerns)
### Should address (minor — not re-checked)
## Reviewer reports (1…n), and reviewers who did not report
## Concerns withdrawn after re-reading the manuscript
## AI-assistance disclosure (simulated panel; same-model reviewers are not independent)
```

## Pitfalls

- One context playing five reviewers produces one opinion in five voices.
- Five separate agents of one model are still one model: agreement is not independent confirmation.
- Reviewers asking for work the paper already did (check the supplement before keeping the concern).
- Treating a concern whose check failed as validated.
- Treating the simulated decision as a prediction of the journal's decision.
