# Playbook — claim-stress-test

**Goal:** find out which headline claims survive, and rewrite the rest to what the evidence
supports. **Default output:** `alterlab-claim-stress-test.md`.

## Inputs

| Field | Default | Meaning |
|---|---|---|
| `path` (or the string argument) | — | manuscript to extract headline claims from |
| `claims` | — | explicit claims to test instead (one of `path`/`claims` is required) |
| `max_claims` | 8 (max 20) | cap on claims tested; the remainder is counted and makes the run `partial` |
| `out` | `alterlab-claim-stress-test.md` | report path |

## Stages and acceptance rules

1. **Claims** — the claims the contribution rests on (title, abstract, conclusions), verbatim,
   with the evidence and design offered for each. A failed extraction is retried once, then the run
   is `blocked` (it is never reported as "no claims").
2. **Attack** — three separate skeptics per claim, each with one lens (a failed lens is retried once):
   - **counter-evidence** — disconfirming, null, or failed-replication findings, and systematic
     reviews/meta-analyses, weighed by the evidence hierarchy;
   - **citation-support** — do the cited sources support the claim at the stated strength
     (population, measure, direction, size)? Sources are retrieved, never recalled;
   - **inference** — does the design license the claim (causal language from correlational data,
     generalization beyond the frame, multiplicity, effect size vs. significance, confounding)?
   Each returns refuted (yes/no), severity (none / weakening / fatal), argument, and retrieved evidence.
3. **Verdict** (computed): ≥2 fatal → **refuted**; ≥2 refuted → **weakened**; exactly 1 fatal →
   **contested** (present both sides); otherwise **survives**. The rule runs on the lenses that
   completed. When a lens is missing, the rating stands only if every answer the missing lens could
   have given leads to the same rating; otherwise the claim is **unrated** — a missing lens never
   counts as "no objection". Each non-surviving claim gets a calibrated rewrite the evidence supports.
   The three skeptics are separate agents of one model: their agreement is not independent verification.

The run is `partial` when a lens did not complete, a claim is unrated, or the claim cap applied.

## Returned payload

| Field | Contents |
|---|---|
| `status`, `status_reasons`, `report` | see `running-workflows.md` |
| `ratings` | tally, including `unrated` |
| `claims` | per claim: `id`, `rating`, `lenses_completed`, `lenses_missing` |
| `coverage` | `claims` (`found`, `requested`, `not_tested`, `rated`, `unrated`), `lenses` (requested = 3 × claims, dispatched, completed, failed, unresolved, retried), `report`, agent totals |

## Sequential playbook

Run the three lenses per claim as separate passes, finishing and saving each before the next.
Apply the rating rule mechanically from the saved results — don't re-judge while tallying, and
don't rate a claim whose missing lens could change the outcome.

## Report skeleton

```markdown
Status: COMPLETE
| Claim | Rating | Lenses (of 3) | Decisive argument | Calibrated rewrite |
## C1 — <claim>
### Counter-evidence  ### Citation support  ### Inference
## Three changes that most strengthen the paper
## Same-model caveat · AI-assistance disclosure
```

## Pitfalls

- A skeptic "refuting" with sources it did not retrieve — reject such arguments.
- Mistaking a narrower-but-true claim for a false one: that is "weakened", with a rewrite.
- Rating a claim "survives" because the lenses that would have objected never reported.
