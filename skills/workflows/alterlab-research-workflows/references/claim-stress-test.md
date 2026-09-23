# Playbook — claim-stress-test

**Goal:** find out which headline claims survive, and rewrite the rest to what the evidence
supports. **Default output:** `alterlab-claim-stress-test.md`.

## Inputs

| Field | Default | Meaning |
|---|---|---|
| `path` (or the string argument) | — | manuscript to extract headline claims from |
| `claims` | — | explicit claims to test instead (one of `path`/`claims` is required) |
| `max_claims` | 8 (max 20) | cap on claims tested; the remainder is logged |
| `out` | `alterlab-claim-stress-test.md` | report path |

## Stages and acceptance rules

1. **Claims** — the claims the contribution rests on (title, abstract, conclusions), verbatim,
   with the evidence and design offered for each.
2. **Attack** — three skeptics per claim, each with one lens:
   - **counter-evidence** — disconfirming, null, or failed-replication findings, and systematic
     reviews/meta-analyses, weighed by the evidence hierarchy;
   - **citation-support** — do the cited sources support the claim at the stated strength
     (population, measure, direction, size)? Sources are retrieved, never recalled;
   - **inference** — does the design license the claim (causal language from correlational data,
     generalization beyond the frame, multiplicity, effect size vs. significance, confounding)?
   Each returns refuted (yes/no), severity (none / weakening / fatal), argument, and retrieved evidence.
3. **Verdict** (computed): ≥2 fatal → **refuted**; ≥2 refuted → **weakened**; exactly 1 fatal →
   **contested** (present both sides); otherwise **survives**. Each non-surviving claim gets a
   calibrated rewrite the evidence supports.

## Sequential playbook

Run the three lenses per claim as separate passes, finishing and saving each before the next.
Apply the rating rule mechanically from the saved results — don't re-judge while tallying.

## Report skeleton

```markdown
| Claim | Rating | Decisive argument | Calibrated rewrite |
## C1 — <claim>
### Counter-evidence  ### Citation support  ### Inference
## Three changes that most strengthen the paper
## AI-assistance disclosure
```

## Pitfalls

- A skeptic "refuting" with sources it did not retrieve — reject such arguments.
- Mistaking a narrower-but-true claim for a false one: that is "weakened", with a rewrite.
