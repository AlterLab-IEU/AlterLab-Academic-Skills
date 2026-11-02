# Behavioral evaluation results

The live behavioral evaluation of the suite: every skill's eval cases, answered with the skill
and without it, and graded against each case's assertions and rubric. The method is in
[`evals.md`](evals.md); the five-task benchmark, which is scored without an LLM judge, is
reported separately in [`benchmark-results.md`](benchmark-results.md).

> **Preliminary numbers.** The last round of the final run was still finishing when these
> numbers were taken on 2026-11-02. The generated blocks on this page will be regenerated when
> it ends. Until then, treat every number here as provisional.

A PASS means an answer met the checks its case's author wrote, on this runner, on the day it
ran. It does not show research correctness beyond what those checks ask, and it is not a
guarantee that a skill's output is right for your data. Check what a skill produces as you
would check a research assistant's draft.

## What was measured

Each eval case (`skills/<domain>/<skill>/evals/evals.json`) was answered twice through the
Claude Code CLI on the maintainer's existing Claude Code login, with no API key: once with the
skill loaded (the **skilled arm**) and once without it (the **bare arm**), on the same prompt,
with the same input files and the same tool grants. The difference between the two arms is what
the skill adds.

Both arms run from fresh temporary directories, never from this repository, with
`--safe-mode --disable-slash-commands --strict-mcp-config --no-session-persistence`, so no
CLAUDE.md, installed plugin, skill, hook or MCP server reaches either arm. The skilled arm gets
the `SKILL.md` appended to its system prompt and the skill's own files (never its `evals/`
folder); the bare arm gets only the task's input files. Both arms are granted the skill's
`allowed-tools`. On Linux each call also runs in a private mount namespace that hides this
checkout, its worktrees and the installed skills, and a tripwire aborts the run if the checkout
changes. Every run counted in the final results recorded namespace confinement and a clean
working tree. Details: [Isolation](evals.md#isolation) in `evals.md`.

| | |
|---|---|
| Model | the Claude model served by the Claude Code login, for both the answers and the judges |
| Claude Code CLI | 2.1.300, 2.1.308, 2.1.309 and 2.1.316 (see [Known limits](#known-limits)) |
| Runner | Linux, answer arms namespace-confined |
| Runs | one run per arm per case (`--runs 1`) |
| Timeout | 600 s per CLI call (400 s in some runs of 2026-10-15) |
| First runs | 2026-10-15 to 2026-10-23 |
| Final runs | 2026-10-15 to 2026-11-02 (the last round still finishing) |
| Raw results | `eval-results/` (git-ignored; not in the repository) |

### Which runs are counted

A case can have several run records, because defects found in one round were fixed and the
case was run again. Two runs per case are used:

- **Final run:** the latest run of the case among the rounds made after the isolation fix of
  2026-10-15 (commit `d7d26cc`, which stopped arms from reading other workspaces and installed
  skills). Those rounds are the result folders `after4`, `sweep183`, `final59`, `retest1`,
  `final_a`, `final_b` and `final_c` under `eval-results/`. A run counts only if the commit it
  recorded contains `d7d26cc`; collect-only runs, which call no judge, are skipped. Each case's
  final run comes from whichever commit it was last run at, so the final results mix commits.
- **First run (baseline):** for the 59 priority skills, the case's earliest run in the
  `priority` round of 2026-10-15, made before the isolation fix; for the other skills, its
  earliest run in `sweep183`.

## How answers are graded

The **skilled arm** is checked against every assertion in the case and against the case's
rubric:

- `output_contains`: a case-insensitive substring check on the answer; no model is involved.
- `should_trigger` / `should_not_trigger`: a judge call decides whether the answer took on the
  task itself or declined and handed off to another skill or tool.
- `behavior`: a rubric clause, judged by a model.
- `expected_output`: the whole-answer rubric, judged by a model.

It passes only when every assertion and the rubric pass; any failed check makes it FAIL.

The **bare arm** is judged on the `expected_output` rubric only. It has no skill, so the
trigger assertions do not apply to it, and the `output_contains` and `behavior` assertions are
not applied either. On the same case, the skilled arm has more checks to pass.

The rubric and `behavior` judge is the literal template that `run_evals.py --behavioral` uses:
it grades the rubric as written. None of these results was re-graded with `--regrade` or the
substance judge (see [Two rubric judges](evals.md#two-rubric-judges-and-checking-them)).

Every case ends in exactly one outcome per arm:

| Outcome | Meaning |
|---|---|
| `PASS` | the answer met every check above |
| `FAIL` | at least one check failed |
| `INCONCLUSIVE` | the model answered, but the judges settled no verdict (a tie, or a judge reply with no verdict line) |
| `REFUSED` | the CLI's usage-policy classifier refused the prompt; never graded |
| `INFRA_ERROR` | the CLI failed or timed out, a judge call failed, or an input file was missing |
| `NOT_RUN` | not attempted: either **not runnable here** (the case declares a `requires` precondition this runner does not meet: an API key or account, an MCP connector, a reachable host, an installed executable), or the run aborted after repeated infrastructure errors |

The tables use these terms:

- **Graded:** the skilled arm's outcome is PASS or FAIL. Every percentage on this page is out
  of graded cases.
- **Bare PASS (same cases):** the bare arm passed on those same graded cases. Any other bare
  outcome counts as not passing.
- **Helped:** a graded case in which the skilled arm passed and the bare arm failed.
  **Hurt:** the skilled arm failed and the bare arm passed. Cases where the arms agree, or where
  the bare arm got no verdict, count as neither. These are case outcomes; the `rubric:` delta
  that `run_evals.py` prints compares rubric verdicts only and can differ.

## Results

**Headline numbers (preliminary, 2026-11-02):**

<!-- BEGIN generated:summary -->
- **241 of 242 skills** have a final run so far, covering **1,595 cases**. No final run yet:
  `alterlab-dergipark`.
- **1,528 cases graded** (skilled arm PASS or FAIL); 48 not runnable here; 19 infrastructure
  errors in the skilled arm.
- **Skilled arm: 1,343 of 1,528 graded cases passed (87.9%).** Bare arm on the same 1,528
  cases: 811 passed (53.1%).
- **The skill helped on 555 cases and hurt on 32.**
- Claude Code CLI version, by number of final cases answered: 2.1.300 (158), 2.1.308 (216),
  2.1.309 (679), 2.1.316 (542).
<!-- END generated:summary -->

By domain:

<!-- BEGIN generated:domain-table -->
| Domain | Skills | Cases | Graded | Skilled PASS | Bare PASS (same cases) | Skill helped / hurt | Not runnable here | Infra / inconclusive |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| bioinformatics | 38 | 224 | 220 | 206 (94%) | 117 (53%) | 88 / 1 | 1 | 3 |
| cheminformatics | 12 | 74 | 69 | 62 (90%) | 28 (41%) | 34 / 1 | 5 | 0 |
| clinical-research | 7 | 48 | 47 | 44 (94%) | 23 (49%) | 21 / 0 | 0 | 1 |
| core | 10 | 80 | 80 | 65 (81%) | 40 (50%) | 27 / 2 | 0 | 0 |
| data-science | 22 | 142 | 135 | 121 (90%) | 70 (52%) | 51 / 1 | 0 | 7 |
| databases | 39 | 249 | 235 | 206 (88%) | 147 (63%) | 65 / 8 | 10 | 4 |
| document-tools | 3 | 19 | 19 | 18 (95%) | 9 (47%) | 9 / 0 | 0 | 0 |
| domain-specific | 18 | 120 | 115 | 104 (90%) | 62 (54%) | 42 / 0 | 4 | 1 |
| faculty-life | 6 | 39 | 39 | 37 (95%) | 20 (51%) | 17 / 0 | 0 | 0 |
| finance-economics | 7 | 59 | 56 | 44 (79%) | 35 (62%) | 11 / 3 | 2 | 1 |
| lab-integrations | 9 | 77 | 74 | 64 (86%) | 29 (39%) | 37 / 2 | 3 | 0 |
| methodology | 3 | 19 | 19 | 12 (63%) | 7 (37%) | 7 / 2 | 0 | 0 |
| research-tools | 14 | 107 | 92 | 77 (84%) | 56 (61%) | 23 / 3 | 15 | 0 |
| social-science-workflow | 17 | 91 | 91 | 89 (98%) | 55 (60%) | 36 / 2 | 0 | 0 |
| turkish-academia | 12 | 87 | 81 | 72 (89%) | 37 (46%) | 36 / 1 | 6 | 0 |
| visualization | 9 | 61 | 60 | 53 (88%) | 32 (53%) | 23 / 2 | 1 | 0 |
| workflows | 1 | 7 | 7 | 6 (86%) | 3 (43%) | 3 / 0 | 0 | 0 |
| writing-tools | 14 | 92 | 89 | 63 (71%) | 41 (46%) | 25 / 4 | 1 | 2 |
| **All** | **241** | **1595** | **1528** | **1343 (88%)** | **811 (53%)** | **555 / 32** | **48** | **19** |
<!-- END generated:domain-table -->

*Cases* counts every case with a final run, and *Graded* those with a PASS or FAIL in the
skilled arm. *Infra / inconclusive* counts skilled-arm outcomes that are neither a verdict nor
not runnable here: INFRA_ERROR, INCONCLUSIVE, REFUSED, or NOT_RUN after an aborted run. The
*workflows* row is the `alterlab-research-workflows` playbook skill answering its own eval
prompts; none of the seven dynamic workflows was run.

### Reading the table

<!-- This reading describes the 2026-11-02 preliminary numbers. Re-check it whenever the generated blocks are regenerated. -->

- With the skill, about seven in eight graded cases passed; without it, about half of the same
  cases did.
- Most of that gap is on cases where the skill should do the task. On near-miss cases, where the
  right answer is to hand the request to a sibling skill, both arms passed most of the time.
- Hurt cases are few next to helped ones. In about half of them the skilled answer's rubric
  verdict was PASS and it failed only an assertion, most often a required phrase
  (`output_contains`), that the bare arm is never checked against. They still count as
  failures.
- Methodology has the lowest skilled pass rate in this snapshot. It, document-tools and
  workflows have 19 cases or fewer, so a single case moves their percentages by five points or
  more.
- The table is per domain. A high domain rate does not mean that every skill in the domain
  passed all its cases.

## Before and after the fixes

The first live run of a case exposed defects, which were fixed before the final run: in skills
(scripts, instructions, `allowed-tools`), in eval cases (missing input files, wrong expected
answers, assertions, `requires` tags), and in the harness itself (see the
[`CHANGELOG.md`](../CHANGELOG.md) `[Unreleased]` section). This section compares the first run
and the final run on the cases that have both.

<!-- BEGIN generated:before-after -->
- **1,529 cases** have both a first run and a final run.
- Skilled arm PASS: **1,109 → 1,296**. Bare arm PASS: **791 → 794**.
- Skilled-arm outcome changes: FAIL → PASS 229, PASS → FAIL 48, FAIL → NOT_RUN 37,
  INFRA_ERROR → PASS 14, INFRA_ERROR → FAIL 9, PASS → NOT_RUN 9, FAIL → INFRA_ERROR 5,
  PASS → INFRA_ERROR 3, NOT_RUN → PASS 3, INFRA_ERROR → NOT_RUN 1, INCONCLUSIVE → PASS 1.
<!-- END generated:before-after -->

**This is not a controlled comparison.** Read it as a record of what changed, not as a measure
of how much the fixes improved the skills:

- Skills, eval cases and the harness changed between the two runs, all at once. The change in
  pass counts is not attributed to any one of them.
- The first runs of the 59 priority skills were made before the isolation fix (`d7d26cc`), so
  the harness those arms ran under differed from the final one.
- A case that ran only once, in `sweep183`, and was never re-run is the same run in both
  columns, so it cannot change.
- Each arm ran once per case in both runs. Some changes in both directions are expected from
  run-to-run variation alone, and these data cannot say how many.
- The bare arm never sees a skill's text, but it does get the skill's `allowed-tools`, the same
  input files and the same rubric, so eval and harness changes reach it too.
- A move to NOT_RUN is a case the first run graded and the final run did not attempt because a
  `requires` precondition was unmet. Cases added after the first run, and cases with no final
  run yet, are left out of this section.

## Not runnable here

A case that declares a `requires` precondition this runner does not meet is NOT_RUN with the
reason "not runnable here", never FAIL, and it is left out of every percentage on this page.
A case can need more than one thing, so it can appear in more than one row.

<!-- BEGIN generated:not-runnable -->
| Why a case is not runnable here | Cases | What it needs |
|---|---:|---|
| API key or account (env) | 36 | ADAPTYV_API_KEY, BGPT_API_KEY, COSMIC_PASSWORD, DRUGBANK_PASSWORD, DX_SECURITY_CONTEXT, FRED_API_KEY, MP_API_KEY, OMERO_HOST, OMERO_PASSWORD, OMERO_USER, OPENROUTER_API_KEY, PARALLEL_API_KEY, ROWAN_API_KEY, USPTO_ODP_API_KEY, ZOTERO_API_KEY, ZOTERO_LIBRARY_ID |
| host unreachable from this runner (net) | 5 | akademik.yok.gov.tr, cartblanche22.docking.org, sw.docking.org |
| executable not installed (cmd) | 4 | bcftools, colabfold_batch, iwdemerit, nvidia-smi |
| MCP connector (mcp) | 3 | MCP server yoktez |
<!-- END generated:not-runnable -->

- **API key or account (`env:`):** the case exercises a keyed or account-based path, and the
  runner has no such variable set. Under the keyless-first rule (`scripts/check_keyless.py`) a
  key only *adds* something: the user's own account or data, a higher rate limit, or a paid
  service the user asks for by name. Every skill also has at least three trigger cases with no
  `env:` requirement, so each skill's keyless path is tested by cases that need no key.
- **MCP connector (`mcp:`):** answer arms run with `--strict-mcp-config` and no MCP servers, so
  a case that needs a connector cannot run in this harness at all.
- **Host unreachable (`net:`):** the runner could not reach the host over HTTPS (one request,
  10 s timeout) when the case came up.
- **Executable not installed (`cmd:`):** the program is not on the runner's `PATH`.

## Known limits

- **Final message only.** The judges see each arm's final message, not its intermediate tool
  output or the files it wrote. What an answer says a script returned is not checked against
  what the script actually returned.
- **One run per case.** The final rounds ran each case once (`--runs 1`; the default is three
  runs with a majority verdict), so there is no estimate of run-to-run variance. A single case
  can change outcome on a re-run.
- **Claude grading Claude.** The judge is a Claude model grading Claude answers: the same model,
  through the same login. Blind spots they share do not show up as failures. The literal rubric
  judge agreed with 7 of 8 hand-labelled pairs in its 2026-10-15 calibration
  ([`evals.md`](evals.md#two-rubric-judges-and-checking-them)).
- **Different checks per arm.** The skilled arm must pass every assertion and the rubric; the
  bare arm is judged on the rubric only. The pass rates compare the two arms on the same cases,
  but not under the same checks.
- **Mixed CLI versions.** The final results mix Claude Code CLI 2.1.300 (runs of 2026-10-15),
  2.1.308 (2026-10-22), 2.1.309 (2026-10-23) and 2.1.316 (2026-11-02).
- **Heavy cases count as infrastructure errors.** In the later rounds, a watchdog on this
  runner stopped any arm whose workspace grew past 1.5 GB (model weights, bulk downloads), and
  each CLI call had a 600 s timeout (400 s in some runs of 2026-10-15). The runner has no GPU
  tooling (`nvidia-smi` is not installed). GPU and very heavy cases that hit these limits are
  INFRA_ERROR: they are not passes, and they are not in the graded percentages. The watchdog
  belongs to this runner, not to the harness.
- **Skill activation not tested live.** The activation harness (`run_evals.py --activation`:
  does the model pick the right skill from its description?) was not run. Here the skilled arm
  is always given its skill.
- **Dynamic workflows not run live.** The seven dynamic workflows were checked only by dry runs
  of `scripts/workflow_dryrun.mjs` against a mocked runtime.
- **claude.ai not tested.** Uploading the skills to claude.ai was not tested; every result here
  comes from the Claude Code CLI.
- **Licensing.** A GPL/LGPL licensing decision is pending for some bundled material (see
  [Licensing](../README.md#licensing) in the README).
- **ÜAK website unreachable.** The ÜAK website (uak.gov.tr) was unreachable from the runner.
  Cases that would read the current doçentlik criteria there carry no `net:` tag, so they ran
  and were graded without live access to the site.
- **`bcftools` not installed.** `bcftools` is not installed on the runner; the case that needs
  it is not runnable here.
- **OpenAlex budget.** *Status 2026-11-02:* OpenAlex's free daily request budget, shared per IP
  address, ran out during the final round. Cases that need an OpenAlex search were affected. A
  re-run after the daily reset is pending.
- **Raw results not in the repository.** The run records (full answers, verdicts, reasons and
  costs per case) are in `eval-results/`, which is git-ignored.

## How to reproduce

```bash
# One skill, both arms, with the settings of the final rounds
# (--skill matches a substring of the skill's directory name)
uv run python scripts/run_evals.py --behavioral --skill <name> --runs 1 --timeout 600 --wait-on-limit

# Many skills, N at a time. LIST holds one skill directory per line (skills/<domain>/<skill>),
# optionally followed by arguments for that skill only; OUTDIR gets one results file per skill.
scripts/eval_sweep.sh LIST N OUTDIR --runs 1 --timeout 600 --wait-on-limit

# Defects in saved results, without a model: missing inputs, denied tools, crashed scripts,
# blocked hosts
uv run python scripts/defect_scan.py RESULTS_DIR
```

- Run inside an authenticated Claude Code environment: the harness uses the CLI's own login.
  Use Linux for namespace confinement, and a disposable checkout.
- `run_evals.py --behavioral` without `--runs` runs each arm three times and takes the majority
  verdict. `--wait-on-limit` sleeps until a reported usage limit resets (at most 6 h) and
  retries the call instead of scoring an infrastructure error.
- `eval_sweep.sh` without extra arguments passes `--runs 1 --timeout 400 --wait-on-limit`;
  arguments you give replace that set. `EVAL_ROOT` chooses which checkout's skills and harness
  are used.
- A behavioral run exits `0` only if every selected case produced a verdict and passed; `1`
  means a case failed, `2` blocked, `3` partial ([details](evals.md#reading-a---behavioral-run)).
- Run records go to `eval-results/` (or `--results-dir`). The tables on this page were
  aggregated from those records with the rules in [Which runs are counted](#which-runs-are-counted);
  that aggregation is not yet a script in this repository.
