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
   `alterlab-tubitak-proposal`. Scale direction matters (NIH 1–9: lower is better). Without a usable
   numeric scale the panel still runs, but scores cannot be range-checked or compared by spread, and
   the run is `partial`.
2. **Review** — primary, secondary, and tertiary reviewers plus a skeptical panelist, each scoring
   every criterion separately (blind to the others) with rationale anchored in the proposal. A
   reviewer that fails is retried once; missing reviewers are named. A score that is off the scale,
   for an unknown criterion, or given twice with different values is excluded and counted — never
   imputed — and each criterion reports how many reviewers scored it.
3. **Challenge** — every major weakness is re-checked against the proposal (approach,
   alternatives, preliminary data, letters), retried once on failure. **Standing** (check completed,
   it stands, with its smallest fix), **withdrawn** (the proposal already answers it), or
   **unverified** (the check did not complete) — unverified weaknesses are listed on their own,
   never as standing.
4. **Summary** (computed) — per-criterion mean and spread over valid scores; a spread of at least a
   third of the scale marks a criterion a real panel would discuss. Summary statement (opening with
   status and coverage), standing weaknesses in priority order, unverified weaknesses, withdrawn
   weaknesses (make that text easier to find), 5-item revision plan, and the caveat that the
   reviewers are separate agents of one model — close scores are not independent agreement. Read
   back from disk before its path is returned.

## Returned payload

| Field | Contents |
|---|---|
| `status`, `status_reasons`, `report`, `program`, `scale` | see `running-workflows.md` |
| `overall_mean`, `overall_scores` | over on-scale overall scores only |
| `criteria` | per criterion: `scores`, `n` (of `of` reviewers), `mean`, `spread`, `discuss` |
| `reviewers` | `requested`, `completed`, `missing` |
| `weaknesses` | `raised`, `standing`, `unverified`, `withdrawn`; plus `standing_weaknesses`, `withdrawn_weaknesses` (counts) and `unverified_weaknesses` (list) |
| `coverage` | `reviewers`, `scores` (requested / completed / missing / off_scale / conflicting), `overall_scores`, `weakness_checks`, `report`, `id_issues`, agent totals |

## Sequential playbook

Establish criteria first. Write the four reviews one at a time, saving scores before the next
review. Compute means and spreads with a script over valid scores only. Check each major weakness
against the text; one you did not check is unverified.

## Report skeleton

```markdown
# Mock panel — <program>   (AI-simulated; not a funding prediction)
Status: COMPLETE
Overall: mean 3.2 on 1–9 (lower is better), 4 of 4 reviewers   Scores: [3, 3, 4, 3]
| Criterion | Scores | n | Mean | Spread | Discuss? |
## Consensus strengths
## Standing weaknesses (priority order, each with its smallest fix)
## Unverified weaknesses (raised, not yet checked against the proposal)
## Weaknesses already addressed — make them easier to find
## Revision plan (5 items)
## Criteria source · same-model caveat · AI-assistance disclosure
```

## Pitfalls

- Using last cycle's criteria: funders revise review frameworks; cite the version used.
- Averaging across different scales or criteria sets, or averaging in off-scale scores.
- Presenting the simulated score as a likely payline outcome.
- Treating a weakness whose check failed as standing.
