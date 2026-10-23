# Benchmark results

The latest reported run of the five-task benchmark (`scripts/run_benchmark.py`; design in
[`evals.md`](evals.md#the-five-task-benchmark-scriptsrun_benchmarkpy)). It describes these 16
cases only. It is not a validation of the other 237 skills, and it is not a validation of these
five skills beyond the inputs below.

## Run

| | |
|---|---|
| Date | 2026-10-14, 12:33–12:50 UTC (the five tasks ran in parallel) |
| Model | `claude-opus-5-5`, through the Claude Code CLI 2.1.299 (the CLI's own login; no API key) |
| Code | commit `ce052a4`, clean working tree |
| Runs | 2 runs per arm of each of 16 cases (three per task, plus an offline variant of a citation case) — 64 answers, every one returned and parsed |
| Isolation | each answer ran in a fresh temporary directory with `--safe-mode --disable-slash-commands --strict-mcp-config --no-session-persistence`; the skilled arm also had the SKILL.md appended and the skill's files (never its `evals/`) in `./skill/` |
| Tools | the same in both arms: `Read`, `Glob`, `Grep` for every task; plus `Bash(python3:*)` for analysis-check; plus `Bash(python3:*)`, `Bash(uv run:*)`, `WebFetch` for citation-integrity except its offline case (`Read` only) |
| Scoring | deterministic: each item's label or number against an expected answer with an evidence anchor; no LLM judge |
| Raw results | `eval-results/final/benchmark-20261014T1237…T1250Z.json` (git-ignored; regenerate with the command at the end) |

## Results

| Task (skill) | Arm | Items | Correct | False approvals | False accusations | Abstained correctly | Abstained unnecessarily | Overconfident on incomplete input | Time per answer | CLI-reported cost |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| citation-integrity (`alterlab-citation-verifier`) | skilled | 56 | **56** (100%) | 0 | 0 | 17 | 0 | 0 | 85 s | $1.87 |
| | bare | 56 | **55** (98%) | 0 | 0 | 15 | 1 | 0 | 41 s | $1.06 |
| manuscript-review (`alterlab-paper-reviewer`) | skilled | 40 | **40** (100%) | 0 | 0 | 6 | 0 | 0 | 33 s | $0.78 |
| | bare | 40 | **40** (100%) | 0 | 0 | 6 | 0 | 0 | 31 s | $0.66 |
| screening (`alterlab-research-workflows`) | skilled | 38 | **38** (100%) | 0 | 0 | 6 | 0 | 0 | 20 s | $0.55 |
| | bare | 38 | **38** (100%) | 0 | 0 | 6 | 0 | 0 | 19 s | $0.51 |
| analysis-check (`alterlab-test-selection-guard`) | skilled | 32 | **30** (94%) | 2 | 0 | 2 | 0 | 2 | 37 s | $0.86 |
| | bare | 32 | **30** (94%) | 2 | 0 | 2 | 0 | 2 | 34 s | $0.77 |
| docentlik (`alterlab-docentlik-eligibility`) | skilled | 42 | **41** (98%) | 0 | 0 | 6 | 0 | 0 | 57 s | $1.82 |
| | bare | 42 | **30** (71%) | 2 | 0 | 5 | 8 | 1 | 71 s | $1.21 |
| **All five** | skilled | 208 | **205** (98.6%) | 2 | 0 | 37 | 0 | 2 | — | $5.87 |
| | bare | 208 | **193** (92.8%) | 4 | 0 | 34 | 9 | 3 | — | $4.22 |

"False approval" = a problem passed as fine (a fabricated or mis-cited reference called
VERIFIED, an ineligible record included, an invalid analysis called valid, an unmet doçentlik
condition called met). "False accusation" = a fine item flagged as a problem. Number items count
as correct within the stated tolerance. Costs are the CLI's `total_cost_usd`, an estimate on a
subscription login.

### What the numbers say

- **Doçentlik pre-screening is the one task where the skill made a clear difference:** 41/42
  vs 30/42. Without the skill's bundled ÜAK 2026 Mart tables, the bare model declined to compute
  candidate A's point totals in both runs (4 number items), gave wrong totals for candidate B
  twice (154 and 176 against 132.67), abstained on four conditions the dossier did settle, and
  made two false approvals: it accepted international articles for a route the table does not
  allow (A5), and called a lead-author condition met when the dossier lacked the information to
  decide it (C4). With the skill, the one miss was a point total computed under the alternative
  author-share reading (123.75 instead of the table's equal-split 132.67).
- **On the other four tasks the bare model was already at or near the ceiling**, so the skills
  showed no measurable accuracy gain: identical scores on manuscript review, screening and
  analysis checking, and one item apart on citation integrity (an unnecessary abstention by the
  bare arm). These tasks give explicit criteria and closed label sets, which makes them easier
  than open-ended use; a harder or more open format might separate the arms, but this run does
  not show that.
- **Neither arm made a false accusation** in 416 scored items — no real reference was called
  fabricated, no eligible record excluded, no sound method flagged. In the offline citation case
  (no lookup tools), both arms marked the obscure Turkish articles and the fabricated one
  UNVERIFIED rather than guessing; both still caught the wrong co-author from memory, and the
  bare arm once named the wrong year from memory too (both accepted answers).
- **The skills cost more:** 39% more CLI-reported cost and 24% more total answer time overall.
  On citation integrity the skilled arm took about twice as long per answer, because it ran more
  lookups.
- **Tool-permission denials** occurred in both arms (citation-integrity: 22 skilled, 17 bare;
  analysis-check: 9 and 6; docentlik: 4 and 8), mostly shell commands outside the allowed
  patterns. Every answer still completed.

### Every scored error

| Task / case | Arm, run | Item | Expected | Answered | Kind |
|---|---|---|---|---|---|
| citation-integrity / incomplete-references | bare, 2 | U5 | VERIFIED | UNVERIFIED | unnecessary abstention |
| analysis-check / log-c-incomplete | skilled, 1 | C1 | CANNOT_ASSESS | VALID | overconfident (counted as false approval) |
| analysis-check / log-c-incomplete | skilled, 2 | C1 | CANNOT_ASSESS | VALID | overconfident (false approval) |
| analysis-check / log-c-incomplete | bare, 1 | C1 | CANNOT_ASSESS | VALID | overconfident (false approval) |
| analysis-check / log-c-incomplete | bare, 2 | C1 | CANNOT_ASSESS | VALID | overconfident (false approval) |
| docentlik / candidate A | bare, 1 | A2, A3 | 126.0, 117.0 | no number | unnecessary abstention |
| docentlik / candidate A | bare, 1 | A5 | NOT_ELIGIBLE | ELIGIBLE | false approval |
| docentlik / candidate A | bare, 2 | A1, A5 | ELIGIBLE, NOT_ELIGIBLE | CANNOT_DETERMINE | unnecessary abstention |
| docentlik / candidate A | bare, 2 | A2, A3 | 126.0, 117.0 | no number | unnecessary abstention |
| docentlik / candidate B | bare, 1 | B2 | 132.67 | 154 | wrong number |
| docentlik / candidate B | bare, 1 | B7 | ELIGIBLE | CANNOT_DETERMINE | unnecessary abstention |
| docentlik / candidate B | skilled, 2 | B2 | 132.67 | 123.75 | wrong number |
| docentlik / candidate B | bare, 2 | B2 | 132.67 | 176 | wrong number |
| docentlik / candidate C | bare, 1 | C7 | ELIGIBLE | CANNOT_DETERMINE | unnecessary abstention |
| docentlik / candidate C | bare, 2 | C4 | CANNOT_DETERMINE | ELIGIBLE | overconfident on incomplete input |

**Two items to read with care.** *Analysis C1* asks whether an independent-samples t-test is
valid when the log never says whether the same people were measured in both lighting conditions.
Both arms inferred an independent design from the analyst's own choice of test, which is
circular; the expected answer (cannot assess) is defensible but a judgement call, and it is the
very question `alterlab-test-selection-guard` exists to raise — the skill did not change the
answer. *Doçentlik B2* depends on the author-share rule for articles with no başlıca yazar; the
expected 132.67 follows the skill's own `references/scoring_rules.md` (1/N) and the TABLO 9 text
quoted there; 123.75 is the reading the anchor lists as the alternative.

## Earlier runs (pilot, not the reported result)

Pilot runs on the same tasks earlier on 2026-10-14 (1 run per arm, some on a working tree with
uncommitted changes) showed the same pattern: doçentlik 21/21 skilled vs 15/21 bare; the other
tasks tied or one item apart. The harness canary (`benchmarks/harness-canary/`) ran live the
same day and gave its designed result (1 PASS, 1 FAIL; the bare arm could not read the codeword
file).

## Limitations

- **Small and synthetic.** 16 cases, 2 runs per arm, one model. The fixtures (except the real
  references in citation-integrity, checked against Crossref and doi.org) are synthetic, and
  four of the five tasks' fixtures and expected answers were drafted by a Claude agent. Numeric
  answers were recomputed independently; label answers carry anchors but were not adjudicated
  by a second human expert. A same-family model wrote and answered them, so shared blind spots
  would not show up as errors.
- **Easier than real use.** Every case lists its items, gives a closed label set, and asks for a
  JSON answer. Real requests are open-ended; a skill's value in structuring an open task is not
  measured here.
- **Not measured:** live runs of the seven dynamic workflows (each spawns tens of agents; they
  were exercised only against a mocked runtime with injected failures — see
  `tests/test_workflow_faults.py`), skill auto-selection (`--activation`), and any skill outside
  these five.
- **Same model as judge of its own fixtures' difficulty:** the ceiling effect on four tasks may
  say as much about the fixtures as about the skills.

## Reproduce

```bash
uv run python scripts/run_benchmark.py --runs 2              # all tasks, sequentially
uv run python scripts/run_benchmark.py --task docentlik --runs 2
```

Run inside an authenticated Claude Code environment (the harness uses the `claude` CLI's own
login). Results are written to `eval-results/benchmark-<UTC>.json`; a run exits `0` only when
every arm of every case returned a parseable answer.
