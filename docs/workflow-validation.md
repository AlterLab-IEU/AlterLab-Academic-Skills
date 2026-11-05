# Validating the dynamic workflows

The seven `alterlab-workflows` scripts (`skills/workflows/workflows/*.js`) are checked in two
separate ways. Keep them apart when reporting results:

| | What runs | What it shows | Where |
|---|---|---|---|
| **Mock runtime** (dry run) | `node scripts/workflow_dryrun.mjs` executes the script against a fake `agent()` that returns schema-shaped data, optionally with injected faults. No model, no tokens, no files written. | The control flow, the accounting (counts, coverage, status), and the failure handling are correct *given* the agent results. | `tests/test_workflows.py`, `tests/test_workflow_faults.py`, `tests/test_check_workflow_run.py` |
| **Live run** | Claude Code runs the workflow with real agents on a fixture. | Whether real agents produce the files and payload the script expects, and whether the payload, the files, and the report agree. | This page; results go in the table at the end. |

Nothing produced by the mock runtime is a live result. `scripts/check_workflow_run.py` refuses to
record a dry-run payload as live (exit 2).

## Fixtures

Each workflow has a small fixture in
`skills/workflows/alterlab-research-workflows/evals/fixtures/workflows/<workflow>/`:

- `args.json` — the exact args to pass. Paths are relative to the repository root; every output
  goes to the placeholder `${OUT_DIR}`, which the checker substitutes (`--print-args`).
- `expect.json` — what a live run must produce: the output files and their types, the required
  payload keys (`required_keys`, plus `required_keys_when_delivered` for a `complete` or `partial`
  run), retired keys that must not appear (`counts.TF` for citation-audit), the coverage stages,
  and `findings` — the answer key, which the checker reports but never counts toward pass/fail.
- `mock-scenario.json` — **mock runtime only**: pinned agent results shaped like a correct run on
  the fixture. The tests use it, and the agent counts below come from it.

The inputs are synthetic and say so in their headers. They are kept as small as each script
allows:

| Workflow | Input | Why it is minimal |
|---|---|---|
| `citation-audit` | `_shared/synthetic-manuscript.md`: a 2-page quasi-experiment with 3 references — one real and correct (Roediger & Karpicke 2006), one real with a wrong year (Cohen, *A power primer*, cited as 1994; it is 1992), one invented | one reference batch, one claim batch, 3 flags × 2 re-checks |
| `review-panel` | the same manuscript, two supplied lenses (methodology, devil's advocate) | the script's default panel is 4–5 lenses; supplying 2 skips that |
| `claim-stress-test` | the same manuscript, `max_claims: 2` | 2 claims × 3 lenses is fixed by the script |
| `rebuttal` | the same manuscript + `rebuttal/reviews.md` (2 reviewers, 4 actionable comments, 1 praise item) | one drafter per actionable comment |
| `grant-mock-panel` | the existing fictional NIH R01 A1 (`fixtures/r01_resubmission_a1.md`, also used by `evals.json`), `funder: NIH`, `mechanism: R01` | the script always seats 4 reviewers |
| `literature-map` | a narrow topic (weekly quizzing and exam performance in undergraduate statistics), `years: 2010-2025` | the script plans 4–6 angles and checks up to 12 gaps; a narrow topic keeps both low |
| `systematic-review-screening` | `records.csv`: 8 synthetic records (1 duplicate), team-supplied include/exclude criteria, no database search | 7 records fit one batch per screener |

## Running a fixture live

Run each workflow in a Claude Code session at the repository root. To validate the scripts in
this checkout (not the last published release), load the plugin from the clone:
`claude --plugin-dir skills/workflows` (the folder carries its own `.claude-plugin/plugin.json`);
the workflows call `alterlab-core` skills (citation verifier, paper reviewer), so have
`alterlab-core` installed too. `/plugin install alterlab-workflows@alterlab-academic-skills`
validates the published version instead — record which one you ran. Dynamic workflows must be
enabled (see `skills/workflows/alterlab-research-workflows/references/running-workflows.md`).

1. **Pick an output directory** — an absolute path, so agents and the checker agree on it.
   `eval-results/` is git-ignored:

   ```bash
   OUT_DIR="$PWD/eval-results/workflows/citation-audit/run-1"; mkdir -p "$OUT_DIR"
   python3 scripts/check_workflow_run.py --workflow citation-audit --out-dir "$OUT_DIR" --print-args
   ```

2. **Launch the workflow with exactly those args** (paste the printed JSON):

   | Workflow | Command |
   |---|---|
   | citation-audit | `/alterlab-workflows:citation-audit <args JSON>` |
   | review-panel | `/alterlab-workflows:review-panel <args JSON>` |
   | claim-stress-test | `/alterlab-workflows:claim-stress-test <args JSON>` |
   | rebuttal | `/alterlab-workflows:rebuttal <args JSON>` |
   | grant-mock-panel | `/alterlab-workflows:grant-mock-panel <args JSON>` |
   | literature-map | `/alterlab-workflows:literature-map <args JSON>` |
   | systematic-review-screening | `/alterlab-workflows:systematic-review-screening <args JSON>` |

   Or, in plain words: *"Run the alterlab-workflows `<name>` workflow with exactly these args,
   unchanged: `<args JSON>`"* — Claude then calls the Workflow tool with that object. Check in the
   approval prompt (or in `/workflows`) that the args were passed unchanged. Allow `Bash`,
   `WebFetch`, `WebSearch`, and `Write` for the run (or use auto mode) so it is not stopped by
   permission prompts. In `claude -p`, add a `Workflow(<name>)` allow rule.

3. **Save the return value verbatim** as `$OUT_DIR/payload.json` — copy the Workflow tool's
   result as returned, without editing it. The checker cannot tell a hand-edited payload from a
   real one, so also note the session and the run's entry in `/workflows`.

4. **Record the run's cost and size** from `/workflows` (agents, tokens) and the session's cost
   readout, and the wall-clock time.

5. **Check it**:

   ```bash
   python3 scripts/check_workflow_run.py --workflow citation-audit \
     --result "$OUT_DIR/payload.json" --out-dir "$OUT_DIR" --live \
     --runtime-s 412 --cost-usd 2.31 --agents 11 --output "$OUT_DIR/verdict.json"
   ```

   Pass `--live` only for a payload a real run returned. Report the verdict's `overall`, its
   failed checks, and the `findings` it lists.

## What the checker verifies

`scripts/check_workflow_run.py` reads the payload and the files on disk itself; it does not
trust the workflow's own read-back agent.

| Check | Rule |
|---|---|
| `payload_schema` | `status`, `status_reasons`, `report`, `coverage` with the right types; the fixture's required keys; no retired keys |
| `status_value`, `status_allowed`, `status_consistent` | status is `complete`, `partial`, or `blocked`; `complete` has no reasons and a report path; `partial` has reasons and a report path; `blocked` has reasons and `report: null` |
| `coverage_accounting` | every coverage stage: `completed ≤ dispatched ≤ requested`, `unresolved = requested − completed`, `failed = dispatched − completed`, `resolved + unresolved = requested`; agents within the 1,000 cap |
| per-workflow invariants (`ca_*`, `rp_*`, `cst_*`, `rb_*`, `gmp_*`, `lm_*`, `srs_*`) | counts never exceed their denominators; checked + unchecked = total; nothing listed as unchecked, unverified, unresolved, or provisional is also counted as checked; a claim rated `survives` had all three lenses; a consistency pass that did not run reports `null`, not 0; the grant mean is recomputed; PRISMA arithmetic (identified − duplicates = after de-duplication; screened + unresolved = submitted; screened − excluded = sought for retrieval) |
| `incomplete_work_visible` | if any coverage shows unfinished work (unresolved, missing, provisional, unrated, unchecked, unanswered), the status is not `complete` and `status_reasons` is not empty |
| `file:<name>` | each declared output exists, is non-empty (unless the fixture allows an empty file, e.g. `unresolved.jsonl` with no unresolved records) and parses: Markdown has a heading, CSV has the declared columns and no ragged rows, JSON parses, JSON Lines has one object per line; line counts match the payload where it states one (`included.jsonl` = `included_sids`) |
| `payload_file:<key>` | a companion path the payload returns exists in the out dir; a `complete` run returns none as `null` |
| `report_path`, `report_states_payload_status` | the report path is the expected one, and its first 40 lines contain `Status: COMPLETE / PARTIAL / BLOCKED` equal to the payload's status (for a `blocked` run, an unconfirmed file must not claim `COMPLETE`) |
| `read_back_matches_file` | the read-back agent's account (exists, stated status) matches the file |

Verdict: `{workflow, checks: [{name, verdict: PASS|FAIL|NA, detail}], overall, live, provenance,
runtime_s, cost_usd, agents, agents_reported, files: [{path, sha256, bytes}], findings}`.
`overall` is `fail` if any check fails, `pass` if none fails and the run is `complete`, and
`incomplete` if none fails but the run reported itself `partial` or `blocked`.

Exit codes: `0` pass, `1` fail, `2` could not check (unreadable result, unknown workflow, or a
mock payload offered with `--live`), `3` incomplete (the same convention as `run_evals.py`).

**Mock is never live.** `live` is set only by `--live`. With `--live`, the checker exits 2 when the
result is `workflow_dryrun.mjs` output (its `ok`/`mode`/`calls` keys), contains the mock runtime's
text (`mock agent text`, `injected fault`, …), or carries three or more of its placeholder strings
(`s0`, `s1`, `s2`).

## Agent counts and cost (mock-derived)

The counts below come from the **mock runtime**: the dry run of each fixture's args with its
`mock-scenario.json` (a correct, fault-free run shaped like the fixture), and with the harness's
default fake data in modes `a` and `b`. The live range is the script's own arithmetic applied to
the fixture (fixed stages + one agent per item the fixture should yield), before retries; each
failed call adds at most one retry. These are estimates, not measurements.

| Workflow | Mock agents (fixture scenario) | Mock agents, default fake data (a / b) | Expected live range | How the count is built |
|---|---|---|---|---|
| `citation-audit` | 11 | 7 / 10 | 7–15 | extract + 1 reference batch + 1 claim batch + 2 re-checks per flag (3 flags expected) + report + read-back |
| `review-panel` | 9 | 9 / 7 | 7–13 | field analyst + 2 reviewers + 1 check per major concern (2–8) + editor + read-back |
| `claim-stress-test` | 9 | 9 / 8 | 9 | extract + 2 claims × 3 lenses + report + read-back |
| `rebuttal` | 8 | 5 / 5 | 8–9 | split + 1 drafter per actionable comment (4–5) + consistency pass + assembler + read-back |
| `grant-mock-panel` | 10 | 15 / 9 | 9–15 | criteria + 4 reviewers + 1 check per major weakness (2–8) + summary + read-back |
| `literature-map` | 12 | 10 / 8 | 12–22 | plan + 4–6 sweeps + clustering + 1 search per candidate gap (4–12) + map + read-back |
| `systematic-review-screening` | 7 | 8 / 10 | 6–7 | protocol + de-duplication + 2 screeners (one batch each) + adjudication if any conflict + report + read-back |

**Cost.** The mock runtime spends no tokens, so it gives agent counts only; no dollar figure is
derived from it. Record the live cost from the session and `/workflows`. All seven fixtures stay
under Claude Code's 25-agent "Large workflow" warning unless retries pile up; literature-map is
the closest.

## Failure and recovery scenarios (mock runtime, not live runs)

Each workflow has one bounded fault test that runs in the **mock runtime**: the named agent
returns `null` on its call and on its one retry. The test checks that the workflow reports the
unfinished work and returns `partial`, and that the checker then says `incomplete` with no failed
check (`test_null_agent_is_reported_partial_and_checker_says_incomplete`). The same payload
relabelled `complete` fails `incomplete_work_visible`
(`test_partial_payload_relabelled_complete_fails`), and a read-back agent that returns nothing
makes every workflow `blocked` with `report: null`
(`test_report_that_cannot_be_read_back_is_blocked`). These are mock-runtime checks of the
scripts' accounting; they do not show how a live run fails or recovers.

| Workflow | Injected fault (mock) | Expected payload |
|---|---|---|
| `citation-audit` | the claim-faithfulness batch fails twice | `partial`; 4 checkable claims listed under `unchecked.claims_without_verdict`; `claims_checked` 0 |
| `review-panel` | the devil's-advocate reviewer fails twice | `partial`; that reviewer in `reviewers.missing`; its concerns never reach the roadmap |
| `claim-stress-test` | the inference lens on claim C2 fails twice | `partial`; C2 judged on 2 of 3 lenses, its missing lens named |
| `rebuttal` | the drafter for comment R2.2 fails twice | `partial`; R2.2 in `unanswered`, no author action invented for it |
| `grant-mock-panel` | the check of the secondary reviewer's major weakness fails twice | `partial`; that weakness in `unverified_weaknesses`, not counted as standing |
| `literature-map` | the existing-work search for one candidate gap fails twice | `partial`; the gap in `unchecked_gaps`, never in `open_gaps` |
| `systematic-review-screening` | the adjudicator fails twice on the one screener conflict | `partial`; that record `UNRESOLVED`, not screened, included, or excluded |

`tests/test_workflow_faults.py` holds the wider fault matrix (thrown agents, omitted, duplicate,
and unknown ids, caps, failed searches), also in the mock runtime.

## Known limits

- The checker cannot prove a payload came from a real run: `--live` is the caller's statement,
  and only mock payloads are detected and refused.
- `findings` (did the audit catch the wrong year, did the panel raise the confound) are an answer
  key for a human reading the verdict. Live agents may word or count things differently, so they
  never change `overall`.
- In `rebuttal` and `systematic-review-screening`, a companion file that fails its read-back turns
  the run `partial` after the report was written with `Status: COMPLETE`. Found by this harness and
  fixed: the workflow now has one agent amend the report's status line, confirms it with a second
  read-back (`coverage.report.status_amended`), and, if that cannot be confirmed, says in
  `status_reasons` that the file is stale and the payload status is authoritative
  (`tests/test_workflow_faults.py`, mock runtime). The checker still compares the file with the
  payload, so a stale file in a live run is caught either way
  (`test_status_downgraded_after_the_report_was_written_is_caught`).

## Live results

Fill in one row per live run, from the checker's verdict. Do not enter mock-runtime results here.

| Workflow | Fixture | Live status | Payload status | Checker overall | Agents | Runtime | Cost (USD) | Failed checks | Verdict file |
|---|---|---|---|---|---|---|---|---|---|
| citation-audit | `citation-audit/` | not yet run | — | — | — | — | — | — | — |
| review-panel | `review-panel/` | not yet run | — | — | — | — | — | — | — |
| claim-stress-test | `claim-stress-test/` | not yet run | — | — | — | — | — | — | — |
| rebuttal | `rebuttal/` | not yet run | — | — | — | — | — | — | — |
| grant-mock-panel | `grant-mock-panel/` | not yet run | — | — | — | — | — | — | — |
| literature-map | `literature-map/` | not yet run | — | — | — | — | — | — | — |
| systematic-review-screening | `systematic-review-screening/` | not yet run | — | — | — | — | — | — | — |
