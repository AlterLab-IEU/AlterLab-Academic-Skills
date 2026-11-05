# Aggregating behavioral results

`scripts/aggregate_results.py` turns the run records that `run_evals.py --behavioral` and
`--regrade` write into one summary, in Markdown and JSON. It makes no model calls and uses only
the Python standard library. Given the same input files and options, it writes byte-identical
output. Every count it prints names the file it came from, and every rate is printed with its
numerator and denominator.

The totals in [`behavioral-results.md`](behavioral-results.md) were aggregated before this
script existed, from records that are not in the repository (`eval-results/` is git-ignored).
Those totals cannot be rebuilt from this checkout. Generate future summaries with this script,
from the versioned records, and publish the records or their hashes next to the summary.

## Usage

```bash
# Markdown summary of every record under a results directory, to stdout
uv run python scripts/aggregate_results.py eval-results/

# The rule used for the published 4.0.0 figures, as far as the records can express it
uv run python scripts/aggregate_results.py eval-results/after4 eval-results/sweep183 \
    eval-results/final_* --selection latest-clean --require-ancestor d7d26cc \
    --skills-root skills --md-out summary.md --json-out summary.json

# First-run baseline instead of the final run
uv run python scripts/aggregate_results.py eval-results/priority eval-results/sweep183 \
    --selection earliest

# Print every selection rule, word for word
uv run python scripts/aggregate_results.py --list-rules
```

| Option | Effect |
|---|---|
| `PATH ...` | Result files or directories. A directory contributes every `*.json` below it. |
| `--selection` | `latest-clean` (default), `latest` or `earliest`; see [Selection rules](#selection-rules). |
| `--require-ancestor COMMIT` | Count only runs whose `repo_commit` contains `COMMIT`. Uses `git merge-base --is-ancestor` in `--git-repo` (default: the current directory). |
| `--skills-root DIR` | Leave out cases of skills with no `DIR/<domain>/<skill>/SKILL.md`. |
| `--format md\|json` | What goes to stdout (default `md`). |
| `--md-out`, `--json-out` | Also write the Markdown or JSON summary to a file. |

Each input file is labelled by its path as you gave it on the command line, so run the script
from the same directory with the same arguments to get the same bytes.

### Exit codes

| Exit | Meaning |
|---|---|
| `0` | Summary produced, and every input file was valid. |
| `2` | No valid input: no path given, nothing found, or every file rejected or ignored. No summary is written. |
| `3` | Some input files were rejected. The summary of the valid ones is still produced, and lists each rejected file with its errors. |

A file whose `kind` is not a behavioral record (for example `activation`) is **ignored**: it is
listed, but it does not change the exit code. The exit code describes the inputs, not the
skills: a summary in which every case failed still exits `0`.

## What is accepted

Records must carry `schema_version` 1 or 2. Any other value, a missing value, or a value of
the wrong type (`"1"`, `true`, `1.0`) is rejected; it is never read as the nearest known
version. Files that are not UTF-8 JSON objects are rejected with the parser's message.

**v1** is what `run_evals.py` writes at 4.0.0 (`_run_metadata()`, `run_behavioral()`,
`regrade_results()`). Required: `schema_version`, `kind` (`behavioral` or
`behavioral-regrade`), `status`, `cases`, and per case `case_id` (unique in the file), `skill`,
and `skilled` / `bare` objects whose `outcome` is one of `PASS`, `FAIL`, `INCONCLUSIVE`,
`REFUSED`, `INFRA_ERROR`, `NOT_RUN`. A regrade also needs `regraded_from` and `judge` (the
judge's name). The other documented keys (`model`, `endpoint`, `claude_cli_version`,
`repo_commit`, `repo_dirty`, `collect_only`, `isolation.confinement.mode`, timestamps,
`skill_version`, `requires_unmet`, `answered_runs`, ...) are type-checked when present. They are
not required, because v1 gained some of them over time without a version change. A run that
lacks one of them can still be shut out by a rule that needs it (see below).

**v2** adds, following the results contract shared with `run_evals.py`:

- `judge: {name: literal|substance, prompt_version, prompt_sha256, trigger_prompt_sha256?}`
  and `runner: {script, script_sha256}`, both required, with 64-character hex hashes.
- Per arm, `dimensions: {substantive, routing, skill_vocabulary, artifacts}`. `substantive` is
  `PASS`, `FAIL` or `NA`; the others may also be `null`. An arm whose outcome is PASS or FAIL
  must carry them. The bare arm can have no routing verdict.
- The outcome must not contradict the dimensions. A PASS needs a substantive PASS and no failed
  gating dimension (substantive, routing, artifacts). A FAIL needs at least one failed gating
  dimension. `skill_vocabulary` is reported but never gates.
- Per case, optional `hashes: {skill_md_sha256, rubric_sha256, fixtures_sha256: {name: hex}}`.
  The summary counts the cases that lack them.

The exact rule that derives a v2 outcome from its dimensions is documented with the runner in
[`evals.md`](evals.md); the aggregator checks only the two consistency conditions above.

## Methodologies are never mixed

Every counted case is reported under the methodology of the record it came from:

| Label | Records | What the outcome is |
|---|---|---|
| `v1-combined-literal-judge` | v1 `behavioral` (and v1 regrades with `--judge literal`) | One combined outcome per arm: all assertions and the rubric, rubric and `behavior` clauses graded by the literal judge |
| `v1-combined-substance-judge` | v1 regrades with `--judge substance` | The same combination, with rubric and `behavior` clauses re-judged by the substance judge |
| `v2-dimensions-<judge>-judge/<prompt_version>` | v2 records | Outcome plus separate routing, substantive, skill-vocabulary and artifact dimensions |

A record whose `endpoint` is not `claude-cli-login` gets ` @ <endpoint>` appended to its
label: a local model's results are never added to Claude's.

Each methodology gets its own tables. No figure adds v1 and v2 counts together, and the summary
has no all-methodology outcome total. If a case's latest run is v2, the case is counted in the
v2 tables only. The case inventory at the top (cases seen, counted, not counted) spans all
methodologies, because it counts cases, not outcomes.

For v1 records the summary says that routing and substantive outcomes are not available. For
v2 records it adds:

- **Substantive:** skilled and bare PASS, helped and hurt, over the cases where both arms have
  a substantive verdict. Both arms are judged on the same criteria here.
- **Routing:** skilled-arm PASS over cases with a routing verdict. The bare arm has none.
- Counts of every dimension value (`PASS`, `FAIL`, `NA`, `null`, `absent`) per arm.

## Selection rules

A case can have several runs: rounds re-run after fixes, parallel runs, regrades. The selection
rule picks at most one run per `case_id`. The rules are applied in this order, and the summary
prints the rules it used (`--list-rules` prints all of them).

1. **A regrade supersedes its source.** A case in a `behavioral-regrade` record replaces the
   same case in the record named by its `regraded_from`, if that file is among the inputs. A
   source in the regrade's own directory is preferred when several inputs have that name.
2. **Collect-only runs are ungraded.** A `behavioral` record with `collect_only: true` called
   no judge, so its cases are never counted. Regrade them first.
3. **Skills no longer in the suite** are left out, when `--skills-root` is given.
4. **Clean runs only** (`latest-clean`). A run is eligible only if it recorded
   `isolation.confinement.mode` = `namespace` and `repo_dirty: false`. A record that did not
   record either is not eligible. `latest` and `earliest` skip this rule.
5. **Commit ancestry**, when `--require-ancestor COMMIT` is given. A run is eligible only if
   git confirms that its `repo_commit` contains `COMMIT`. A missing commit, or one the given
   repository does not have, is not eligible ("unverifiable").
6. **Latest (or earliest) run.** Among the eligible runs, the one with the latest
   `finished_at` is counted (`earliest`: the earliest). When `finished_at` is missing,
   `started_at` is used. A regrade keeps its source's timestamps.
7. **Ties.** Runs tied at that time with the same outcomes in both arms and the same
   methodology are duplicates: the one from the lexicographically first file label is
   counted. Tied runs that disagree are an **unresolved conflict**: the case is not counted,
   and both runs are listed.

Every run that is not counted is listed under *Runs not counted* with its category and
reason: `superseded`, `ungraded`, `not-in-suite`, `unclean`, `ancestry`, `no-timestamp`,
`not-selected` (another run is newer, or older for `earliest`), `duplicate` or `conflict`. A
case whose runs were all shut out is listed under *Cases with no eligible run*.

### How these rules relate to the published 4.0.0 figures

The [Which runs are counted](behavioral-results.md#which-runs-are-counted) section of
`behavioral-results.md` describes how the published totals chose runs. This script codifies
the parts that the records themselves can express:

| Published rule | In the script |
|---|---|
| Final run: the latest run of the case | `--selection latest-clean` (rule 6) |
| Every counted run recorded namespace confinement and a clean tree | rule 4 |
| A run counts only if its commit contains `d7d26cc` | `--require-ancestor d7d26cc` (rule 5), run inside this repository |
| Collect-only runs are skipped | rule 2 |
| Cases of skills no longer in the suite are left out | `--skills-root skills` (rule 3) |
| Only the rounds `after4`, `sweep183`, `final59`, `retest1`, `final_a` ... `final_m` | Not a rule: choose those directories as the input paths |
| First-run baseline: the earliest run in `priority` (59 skills) or `sweep183` | Approximated by `--selection earliest` over those two directories. The per-skill choice of round is not codified |
| Refusals recorded as INFRA_ERROR before commit `8ffe74c` are counted as REFUSED | **Not codified.** It reclassifies an outcome from the wording of its error, which a reader cannot do reliably; the summary reports the recorded outcome |
| The final run is made at the skill's current content | **Not codified.** v1 records carry only `skill_version`. v2 records carry `skill_md_sha256`, which covers `SKILL.md` only, not the skill's other files |

So even with the original records, this script would not necessarily reproduce the published
numbers exactly. It reports what the rule it states selects.

## What the summary reports

Per methodology:

- **Denominators:** *selected* (cases counted under this methodology), *attempted* (selected
  minus skilled-arm NOT_RUN), *answered* (the skilled arm answered at least once), *usable
  verdicts* (skilled arm PASS or FAIL, also called *graded*). NOT_RUN is split into *not
  runnable here* (the case recorded `requires_unmet`) and *aborted or other*.
- **Outcome counts** for both arms: PASS, FAIL, INCONCLUSIVE, REFUSED, INFRA_ERROR, NOT_RUN.
- **Rates,** always as `n / d (p%)`: coverage (usable / selected), skilled PASS of graded
  cases, bare PASS on the same graded cases, helped (skilled PASS, bare FAIL) and hurt (skilled
  FAIL, bare PASS). These follow the definitions in `behavioral-results.md`. With no
  denominator, the rate reads `n / 0 (no denominator)`.
- The `rubric:` delta each case recorded (rubric verdicts only), tallied as recorded.
- **Provenance:** the counted cases per model, endpoint, Claude Code CLI version, repository
  commit and, for v2, judge prompt hash and runner script hash; and how many counted cases have
  no per-case hashes.

Across methodologies: every input file with its sha256, status, kind, schema version, run
status (so `blocked` runs are visible) and errors; unresolved conflicts; cases with no eligible
run; every run not counted, with its reason; the counted cases that did not pass, with the
skilled arm's reason (FAIL, INCONCLUSIVE, REFUSED, INFRA_ERROR, NOT_RUN); and every counted
case with the file that supplied it, its timestamp, skill version and, for v2, the `SKILL.md`
and rubric hashes. The JSON summary also carries the full hashes and fixture hashes.

The output contains no timestamp of its own: the only times in it are `started_at` and
`finished_at` values read from the inputs. Ordering is by file label and `case_id`.

## Synthetic example records

[`examples/eval-records/`](examples/eval-records/) holds **synthetic** records for testing the
aggregator. Every file has `"synthetic_example": true` at the top level, the skills are named
`alterlab-example-*` (no real skill), and every commit, hash, answer and outcome is invented.
**They are not results of any skill.** When any input is marked synthetic, the summary opens
with a banner that says so.

| Directory | What it exercises |
|---|---|
| `round-1/` | A v1 run with every outcome (PASS, FAIL, INCONCLUSIVE, REFUSED, INFRA_ERROR, NOT_RUN with `requires_unmet`), and a later re-run of one case from a dirty, unconfined checkout |
| `round-2/` | A collect-only run and its substance-judge regrade; two parallel runs that finished in the same second and disagree on one case and agree on another |
| `round-3/` | A v2 run with judge and runner hashes, per-case hashes, artifacts and dimensions (a routing-only failure, an artifact-only failure) |
| `malformed/` | A v1 file with an unknown outcome and a case without `case_id`, and a file with `schema_version: 9` |

[`examples/eval-records/expected-summary.md`](examples/eval-records/expected-summary.md) is the
script's output for that directory. `tests/test_aggregate_results.py` regenerates it and fails
if it differs. After a deliberate change to the output, regenerate it from the repository
root:

```bash
python3 scripts/aggregate_results.py docs/examples/eval-records \
    --md-out docs/examples/eval-records/expected-summary.md   # exits 3: two files are rejected
```

## Limitations

- **The published 4.0.0 totals cannot be rebuilt from this checkout.** Their records are not
  in the repository, and some of the rules used to select them are not expressible from the
  records (see the table above).
- **No per-domain table.** Records name the skill, not its domain. Join the JSON
  summary's `counted_cases` with the skill tree for that.
- **No variance estimate.** A case counts once, from one run. If that run used `--runs 3`, the
  outcome is already the runner's majority; the aggregator does not re-vote.
- **Timestamps order runs.** Two runs of a case that finished in the same second count as a
  tie (rule 7). Records whose clocks disagree are ordered as recorded.
- **Regrade matching is by file name**, because that is all `regraded_from` records. Keep each
  round's files in their own directory.
- **v2 is read from the shared contract.** If `run_evals.py` writes v2 records that differ
  from it, the aggregator rejects them rather than guessing. Update both together.
