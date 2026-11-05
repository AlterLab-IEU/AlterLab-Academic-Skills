# Activation set: which installed skill does the model pick?

`scripts/activation_eval.py` runs a small, hand-labelled set of requests
(`benchmarks/activation/cases.json`). For each request it asks a model which single installed
skill it would load, or `none`, given only each skill's name and description. It complements
`run_evals.py --activation` (see [evals.md](evals.md#activation-harness---activation)). That
harness covers every skill's own eval prompts but has these limits:

| `run_evals.py --activation` | `activation_eval.py` |
|---|---|
| Candidates are the target plus the first N same-category siblings in **alphabetical** order. | Candidates come from an **installed profile**, and each case lists **hand-picked plausible distractors**. |
| Every skill is assumed installed. | Profiles are computed from the real plugin manifests and bundles. |
| A missing skill is never tested. | **unavailable** cases: the right skill is not installed, so the right answer is `none` or a named fallback. |
| English eval prompts only. | English and Turkish requests. |
| A pick is recorded without the list it was chosen from. | Every vote records the exact candidate list and its order. |

## What is measured

Each vote is one isolated `claude` CLI call through `run_evals._claude`. The call runs in a
fresh temporary directory with the same isolation flags as the other harnesses, and it gets
no skill files and no tools. The prompt holds the user's request and the shown candidates as
`name: description` lines. The model replies `CHOICE: <name or none>`. Over `--runs` votes the
majority choice wins. A tie takes the **worse** of the tied outcomes, so a tie never raises a
rate. Use an odd `--runs`.

| Outcome | Meaning |
|---|---|
| `correct` | Picked `expected` (or picked `none` when `expected` is `none`). |
| `acceptable_alternate` | Picked a skill listed in `acceptable`. |
| `wrong_skill` | Picked some other skill when an installed skill was expected. |
| `missed` | Picked `none` when an installed skill was expected. |
| `false_activation` | Picked a skill when `none` was expected, or a non-fallback skill on an unavailable case. A pick of a skill that was not shown counts here too. |
| `correct_unavailable_handling` | Picked `none` when the right skill is not installed. |
| `no_answer` | No usable vote: CLI error, timeout, refusal, or a reply without a `CHOICE:` line. |

The summary gives counts for every outcome. It splits them overall, by kind, by language, by
profile, and by expectation (installed skill, `none`, unavailable). Every rate is reported as
`{n, of, rate}`. The denominator `of` is the number of **answered** cases, which excludes
`no_answer`, so an infrastructure failure never counts as a miss. Two rates are given:

- `success`: correct, acceptable_alternate and correct_unavailable_handling;
- `strict`: correct and correct_unavailable_handling only.

## How profiles and candidates are built

A profile in `cases.json` names plugins, for example `["alterlab-essentials"]`. The harness
reads `.claude-plugin/marketplace.json`. For each plugin it uses the marketplace entry's
`skills`, or else the plugin's own `.claude-plugin/plugin.json`. It follows `dependencies`
transitively, which is how the `plugins/` bundles install their domain plugins. The result is
the installed skill list. An unknown plugin, a listed skill directory without a `SKILL.md`, or
a skill missing from the catalog stops the run with exit 64.

The shipped profiles are `full` (alterlab-complete, 241 skills), `essentials` (80),
`turkish-academia+core` (23), `core-only` (10) and `visualization-only` (9).

Candidate policy (recorded in each results file as `candidate_policy`):

1. A profile of at most **40** skills is shown in full.
2. In a larger profile the model sees:
   - every installed skill of each plugin that owns the expected skill, an acceptable
     alternate or a distractor;
   - every installed `alterlab-core` skill, because those general-purpose pipeline skills
     compete with every request;
   - every explicit distractor;
   - a seeded sample of **8** other installed skills, so the list is not built only from the
     label.
3. A skill that is not installed is never shown.

The list is sorted, then shuffled for each run with `Random(f"{seed}|{case_id}|run{n}")`, so
position bias averages out across runs and every order can be reproduced. Each vote stores the
exact order it was shown.

## Running it

```bash
uv run python scripts/activation_eval.py --estimate                  # CLI calls a run would make
uv run python scripts/activation_eval.py --dry-run --case tr-yok-tez-search   # prompt + candidates
uv run python scripts/activation_eval.py --runs 3                     # live (needs the claude CLI)
uv run python scripts/activation_eval.py --runs 3 --language tr --profile turkish-academia+core
uv run python scripts/activation_eval.py --runs 1 --kind unavailable --limit 3
```

Results go to `eval-results/activation-set-<UTC stamp>.json`. Each record holds
`schema_version` 1, `kind: "activation-set"`, the model, runs, seed, the case-file hash, the
resolved profiles and the candidate policy. For every case it also holds the candidates with
the reason each was shown, every vote with its order and raw reply, the majority choice, and
the outcome.

Exit codes follow `run_evals.py`. **0** means measured: every selected case got a usable
majority choice. **3** means partial: some cases are `no_answer`. **2** means blocked: no
usable choice, no `claude` CLI, or no case selected. **64** means the case file or a profile is
invalid. A low activation rate never fails a run, because this is a measurement and not a gate.

## Limits

- **This is a proxy, not Claude Code's skill loader.** It asks one model one question about a
  text list of descriptions. Claude Code decides whether to load a skill during a real
  session. That decision depends on the conversation, the tool context, its own description
  budget and truncation, and the listing format, none of which this harness reproduces. Use the
  results to compare descriptions with each other, not to predict real-world triggering.
- **The set is small and hand-written.** It has 40 cases. Most are in English, 11 are in
  Turkish, and they cover a few confusable clusters: citation tools, review skills, plotting
  libraries, research engines, survey and statistics skills, and Turkish-academia skills.
  Rates on this set say nothing about skills that the set does not cover.
- **Labels need maintainer review.** The expected answers, acceptable alternates and
  distractors are one author's judgement, explained in each case's `note`. Ambiguous cases in
  particular encode a choice about what counts as acceptable.
- **The subset policy shapes the task.** In large profiles the shown list depends on the
  label's plugins. The background sample softens this but does not remove it. Small profiles
  are shown in full.
- **Votes are not independent samples.** With a handful of runs per case, a rate on 40 cases
  has wide uncertainty. Report the counts and denominators, not only the percentage.
