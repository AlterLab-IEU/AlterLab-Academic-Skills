# Reliability review of 4.0.0: findings, repairs and what remains

An external review examined v4.0.0 at commit `6fa26160d28f14ba3daf22a8cb30b91ea3d46837`
(241 skills; full suite 5,426 passed / 25 skipped on the reviewer's machine). This page maps
each of its 20 findings to what was found on that commit, what changed, the evidence, and
what is still not established. It was written on 2026-11-05 as part of the repair.

Baseline on this runner, before any change: `uv run pytest tests/` → **5,428 passed, 23
skipped** (the two-test difference from the review is environment-dependent skips).

How to read the evidence column:

- **fail → pass** — a regression test written before the fix failed on the unmodified code
  and passes now.
- **live** — a real run against public APIs or the Claude Code CLI on 2026-11-05, with no
  mock. Live results are listed separately in [Live results](#live-results).
- **static** — established by reading code or documents only.

Classification vocabulary: *confirmed defect* (wrong behaviour reproduced), *evaluation gap*
(the measurement could not see the problem), *already fixed*, *not reproduced*, *intentional
behaviour needing clearer documentation*.

## Findings

| # | Finding | Classification | Status | Main files | Evidence | Remaining limits |
|---|---|---|---|---|---|---|
| A1 | A resolving DOI cleared an invented co-author (PASS, overlap 0.667) | confirmed defect | fixed: existence, identifier, metadata and retraction reported separately; unsupported authors → `PAC` | `skills/core/alterlab-citation-verifier/scripts/verify_citations.py` | fail → pass (`tests/test_verify_citations_reliability.py`, 36 of 46 failed before); live: the review's exact case now `PAC` naming `Inventedauthor, Alice` | Free-form author lists are split heuristically; a lone given name is recognised only when the record supplies given names |
| A2 | `author_overlap(["Li"], ["Williams"]) == 1.0` | confirmed defect | fixed: token-wise matching with an explicit, documented list of variants | same | fail → pass (6 unrelated-name and 15 variant cases) | Transliteration beyond the listed variants (e.g. Chinese romanisations, Cyrillic) is not matched |
| A3 | Index absence reported as Total Fabrication | confirmed defect | fixed: `NOT_FOUND` (`REVIEW_REQUIRED`) and `ID_INVALID`; `TF` never emitted | same; `skills/workflows/workflows/citation-audit.js`; consumers | fail → pass (grey literature, obscure book, unregistered DOI, nonexistent arXiv ID, malformed DOI, source outage); live: unregistered DOI → `ID_INVALID`, unindexed report → `NOT_FOUND` | A fabricated reference is now `NOT_FOUND`, not `FAIL`; a human still has to decide. Existing tests that asserted `TF` were relabelled with the same evidence bar |
| A4 | One source's `NetworkUnavailable` stopped the loop | confirmed defect | fixed: per-source failure recorded, remaining sources asked, host paused 60 s | `verify_citations.py` | fail → pass (first source down/second verifies, all down, 429 then alternate, all answer no match, host pause) | The pause is per process; a long batch run after an outage waits up to 60 s per host |
| A5 | `retracted: false` reported when Crossref never answered | confirmed defect | fixed: `retraction.status` flagged / not_flagged_in_checked_sources / unknown; `retracted` null when unknown | `verify_citations.py`, `citation-audit.js`, integrity schemas | fail → pass; workflow fault test for `retraction_unknown` | Crossref is the only retraction source; works without a Crossref record (books, arXiv-only) are always `unknown` |
| B1 | Turkish characters stripped from search terms | confirmed defect | fixed | `skills/research-tools/alterlab-research-lookup/scripts/scholarly_backend.py` | fail → pass (`tests/test_research_lookup_query.py`, 48 of 55 failed before); live: Turkish query returned Turkish-language records | Filler-word removal is English-only |
| B2 | `OR` dropped; arXiv turned OR into AND | confirmed defect | fixed: parsed expression, per-index translation labelled exact / approximate / skipped | same; `research_lookup.py` | fail → pass; live: OR and NOT reached Europe PMC and arXiv exactly, Crossref labelled approximate or skipped | OR binds tighter than AND (documented, not standard precedence) |
| B3 | DOI-less dedup on 80 ASCII chars; empty keys merged | confirmed defect | fixed: identifier, then full Unicode title + year ± 1 + first author; never an empty key; provenance kept | `scholarly_backend.py` | fail → pass | Preprint/published pairs with different DOIs stay separate unless a relation is known |
| B4 | Citation-count default outranked relevant papers; mixed-index counts | confirmed defect | fixed: relevance default; `--rank cited` uses one declared index | same | fail → pass; nDCG@5 on a synthetic fixture (see limits) | The relevance fixture was written by the repair pass to reproduce the failure and awaits independent review; it does **not** show better search quality in general |
| B5 | "recent" changed order but applied no date filter | confirmed defect | fixed: `--since` / `--until` per index, client-side re-check, disclosure | `scholarly_backend.py`, `research_lookup.py` | fail → pass; live: `--since 2023` returned only 2024+ records; "recent" disclosed | Records without dates are kept (marked), so a dated window can still include undated items |
| C1 | Garbage `.pptx` passed when python-pptx was missing; `.docx` passed | confirmed defect | fixed: status valid / invalid / blocked / partial, check tracking, exit 0 / 1 / 2 / 3 | `skills/writing-tools/alterlab-scientific-slides/scripts/validate_presentation.py` | fail → pass (`tests/test_validate_presentation.py`, 26 of 28 new tests failed before) | Exit 2 is shared with argparse usage errors |
| C2 | Inherited font sizes never checked | confirmed defect | fixed: inheritance chain resolved; groups and tables traversed; unresolved runs make the check incomplete | same | fail → pass (master, layout, list-style, group, table, footer, autofit fixtures) | Charts, SmartArt and OLE text are not inspected; group scaling is not applied to font size |
| D1 | Conflicting duplicate answers: first one won | confirmed defect | fixed: `unresolved_conflict`, never correct | `scripts/run_benchmark.py` | fail → pass; the test that enshrined first-answer-wins was replaced | — |
| D2 | Evidence requested but discarded | evaluation gap | fixed: evidence kept; label accuracy separate from deterministic quote checks; `needs_review` + export for human review; scoring schema 2 | `run_benchmark.py`, `benchmarks/*/task.json` (metadata only) | fail → pass | Paraphrased or computed evidence is always `needs_review`; reviewer verdicts are tallied by hand. No benchmark was re-run with schema 2 |
| D3 | Blocked regrade exited 0 | confirmed defect | fixed: aggregated over files; 0 / 1 / 2 / 3 | `scripts/run_evals.py` | fail → pass (`tests/test_regrade_exit.py`, 14 of 15 failed before) | — |
| D4 | Literal judge on the normal path; vocabulary mixed into substance | evaluation gap | fixed: `--judge` explicit and recorded (default substance); identical substantive criteria for both arms; routing and vocabulary as separate dimensions; `--audit-rubrics` | `run_evals.py`, `docs/judge_calibration.json` | unit tests; live calibration: substance 13 / 13, literal 12 / 13 | 505 of 1,353 `output_contains` assertions are vocabulary-only (audit); rubrics were not edited. No behavioral sweep was re-run with the new grading |
| D5 | Generated files never inspected | evaluation gap | fixed: `scripts/artifact_checks.py`, results keep copies + sha256 | `run_evals.py`, `scripts/artifact_checks.py`, 4 eval cases | unit tests on real files and runner wiring | Only 4 eval cases declare artifact checks; none has been run live with them |
| D6 | Published summaries not reproducible | evaluation gap | fixed for future runs: `scripts/aggregate_results.py` | `scripts/aggregate_results.py`, `docs/eval-aggregation.md` | unit tests, deterministic output | **The raw records behind the published 4.0.0 totals are not in the repository; those totals cannot be reconstructed from this checkout** |
| E1 | Activation not validated live; idealised catalog | evaluation gap | harness built and run live | `scripts/activation_eval.py`, `benchmarks/activation/` | live: 39 / 40 (one vote per case) | Description-only proxy, not Claude Code's loader; 40 hand-written cases near ceiling; labels need maintainer review |
| E2 | Seven workflows not validated live | evaluation gap | fixtures + output checker built; live runs listed below | `scripts/check_workflow_run.py`, `docs/workflow-validation.md` | live: see below; failure/recovery covered by dry-run fault tests (mock) | Workflows not listed as run live remain dry-run only |

## Live results

All live runs used the Claude Code CLI login (no API key) or keyless public APIs, on
2026-11-05. Costs are as reported by the CLI on a subscription login, i.e. estimates.

| What | Result | Record |
|---|---|---|
| Citation verifier, 5 references against Crossref / S2 / Europe PMC / arXiv / Open Library / doi.org | review's invented co-author → `PAC`; correct citation → `verified`; "and others" → `verified`; unregistered DOI → `ID_INVALID`; unindexed report → `NOT_FOUND`; Semantic Scholar answered HTTP 429 throughout and was reported as not checked | [`examples/live-2026-11-05/`](examples/live-2026-11-05/) (input `.bib` and the JSON report) |
| Research lookup, 6 queries | Turkish query preserved and answered; OR / NOT exact on Europe PMC and arXiv; `--since 2023` applied on three indexes; "recent" disclosed; Greek query returned no records and no error | terminal output only (not saved) |
| Activation set, 40 cases × 1 vote (+ 14 repeated) | 39 / 40 counted successes; 1 false activation (reproduced); $4.11 | `benchmarks/activation/results/` |
| Judge calibration, 13 pairs × 2 judges | substance 13 / 13; literal 12 / 13 | `docs/evals.md` |
| Dynamic workflow `claim-stress-test`, 1 claim | status complete; 3 / 3 lenses; report file present (13,886 bytes), opens with the same status as the payload; 5 agents, 152 s | [`examples/live-2026-11-05/`](examples/live-2026-11-05/) (payload and report) |

## What is not established

- No full behavioral sweep was re-run, so no skilled-vs-bare percentage was re-measured; the
  4.0.0 figures (literal judge, v1 grading) stand as published and are not comparable with
  schema-2 runs.
- The five benchmark tasks were not re-run under scoring schema 2.
- Workflows other than those marked live in `docs/workflow-validation.md` have only dry-run
  (mocked) evidence.
- Hand labels added in this repair (relevance fixture, activation cases, five calibration
  pairs) were written by the repair pass and need independent review.
