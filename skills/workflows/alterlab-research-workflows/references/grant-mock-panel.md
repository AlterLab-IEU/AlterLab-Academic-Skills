# Playbook — grant-mock-panel

**Goal:** see how a review panel is likely to read a proposal, on the funder's own criteria and
scale, and what to fix first. A simulation, not a funding prediction. **Default output:**
`alterlab-grant-panel.md`.

## Inputs

| Field | Default | Meaning |
|---|---|---|
| `path` | required | the proposal (full application where possible) |
| `funder` | required | e.g. `NIH`, `NSF`, `ERC`, `Horizon Europe`, `TUBITAK 1001` |
| `mechanism` | none | e.g. `R01`, `CAREER`, `StG`, `1002-A` |
| `out` | `alterlab-grant-panel.md` | report path |

## Stages and acceptance rules

1. **Criteria** — the current review criteria, guidance, and scoring scale from the funder's
   official source (cite it with date/version), via `alterlab-research-grants` or
   `alterlab-tubitak-proposal`. Scale direction matters (NIH 1–9: lower is better).
2. **Review** — primary, secondary, and tertiary reviewers plus a skeptical panelist, each
   scoring every criterion independently with rationale anchored in the proposal.
3. **Challenge** — every major weakness is re-checked against the proposal (approach,
   alternatives, preliminary data, letters); weaknesses the proposal already answers are
   withdrawn, each with the smallest fix for those that stand.
4. **Summary** (computed) — per-criterion mean and spread; a spread of at least a third of the
   scale marks a criterion a real panel would discuss. Summary statement, standing weaknesses in
   priority order, withdrawn weaknesses (make that text easier to find), 5-item revision plan.

## Sequential playbook

Establish criteria first. Write the four reviews one at a time, saving scores before the next
review. Compute means and spreads with a script. Check each major weakness against the text.

## Report skeleton

```markdown
# Mock panel — <program>   (AI-simulated; not a funding prediction)
Overall: mean 3.2 on 1–9 (lower is better)   Scores: [3, 3, 4, 3]
| Criterion | Scores | Mean | Spread | Discuss? |
## Consensus strengths
## Standing weaknesses (priority order, each with its smallest fix)
## Weaknesses already addressed — make them easier to find
## Revision plan (5 items)
## Criteria source · AI-assistance disclosure
```

## Pitfalls

- Using last cycle's criteria: funders revise review frameworks; cite the version used.
- Averaging across different scales or criteria sets.
- Presenting the simulated score as a likely payline outcome.
