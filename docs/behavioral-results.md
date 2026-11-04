# Behavioral evaluation results

The live behavioral evaluation of the suite: every skill's eval cases, answered with the skill
and without it, and graded against each case's assertions and rubric. The method is in
[`evals.md`](evals.md); the five-task benchmark, which is scored without an LLM judge, is
reported separately in [`benchmark-results.md`](benchmark-results.md).

> **Status, 2026-11-04.** Every one of the 241 skills has a final run made at its current
> content. `alterlab-openalex` was removed in 4.0.0 (OpenAlex now needs an account for real
> use), so its cases are no longer counted, and every skill that used OpenAlex was rewritten and
> re-run (see [Known limits](#known-limits)).

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
| Claude Code CLI | 2.1.300, 2.1.308, 2.1.309, 2.1.316 and 2.1.318 (see [Known limits](#known-limits)) |
| Runner | Linux, answer arms namespace-confined |
| Runs | one run per arm per case (`--runs 1`) |
| Timeout | 600 s per CLI call (400 s in some runs of 2026-10-15; 900 s for the one re-run of cases that had timed out or hit an infrastructure error) |
| First runs | 2026-10-15 to 2026-10-23 |
| Final runs | 2026-10-15 to 2026-11-04 |
| Raw results | `eval-results/` (git-ignored; not in the repository) |

### Which runs are counted

A case can have several run records, because defects found in one round were fixed and the
case was run again. Two runs per case are used:

- **Final run:** the latest run of the case among the rounds made after the isolation fix of
  2026-10-15 (commit `d7d26cc`, which stopped arms from reading other workspaces and installed
  skills). Those rounds are the result folders `after4`, `sweep183`, `final59`, `retest1`,
  `final_a`, `final_b` and `final_c` under `eval-results/`, plus `final_d` (one re-run, with a
  900 s timeout, of the cases whose last run was an infrastructure error, a timeout or
  inconclusive), `final_e` (a full re-run of five skills after the routing fix described in
  [Where the skill made answers worse](#where-the-skill-made-answers-worse)), `final_f` (one
  more try, on an idle runner, of three light look-ups that had timed out only under load), and
  `final_g` to `final_m` (full re-runs of every skill changed by the removal of
  OpenAlex, the login fixes, the later routing and timeout fixes, and the second pass over the
  hurt cases).
  A refusal that runs before commit `8ffe74c` recorded as INFRA_ERROR (the CLI's newer
  acceptable-use wording) is counted as REFUSED, which is how the runner records it now. A run counts only if the commit it
  recorded contains `d7d26cc`; collect-only runs, which call no judge, are skipped. Each case's
  final run is its latest run made at the skill's current content (the skill's files outside
  `evals/` identical to this release); every counted case has one. Cases of skills no longer in
  the suite are left out.
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

**Headline numbers (2026-11-04):**

<!-- BEGIN generated:summary -->
- **241 of 241 skills** have a final run, covering **1,598 cases**.
- **1,532 cases graded** (skilled arm PASS or FAIL); 50 not runnable here; 16 skilled-arm outcomes that are neither (infrastructure error, refusal, inconclusive).
- **Skilled arm: 1,380 of 1,532 graded cases passed (90.1%).** Bare arm on the same 1,532 cases: 804 passed (52.5%).
- **The skill helped on 571 cases and hurt on 2.**
- Claude Code CLI version, by number of final cases answered: 2.1.300 (101), 2.1.308 (184), 2.1.309 (571), 2.1.316 (574), 2.1.318 (168).
<!-- END generated:summary -->

By domain:

<!-- BEGIN generated:domain-table -->
| Domain | Skills | Cases | Graded | Skilled PASS | Bare PASS (same cases) | Skill helped / hurt | Not runnable here | Infra / inconclusive |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| bioinformatics | 38 | 224 | 220 | 205 (93%) | 116 (53%) | 88 / 0 | 1 | 3 |
| cheminformatics | 12 | 74 | 69 | 63 (91%) | 28 (41%) | 34 / 0 | 5 | 0 |
| clinical-research | 7 | 48 | 46 | 43 (93%) | 24 (52%) | 19 / 0 | 0 | 2 |
| core | 10 | 80 | 79 | 67 (85%) | 41 (52%) | 25 / 0 | 0 | 1 |
| data-science | 22 | 142 | 135 | 121 (90%) | 69 (51%) | 52 / 0 | 0 | 7 |
| databases | 38 | 242 | 231 | 213 (92%) | 146 (63%) | 67 / 0 | 10 | 1 |
| document-tools | 3 | 19 | 19 | 18 (95%) | 9 (47%) | 9 / 0 | 0 | 0 |
| domain-specific | 18 | 120 | 116 | 106 (91%) | 63 (54%) | 43 / 0 | 4 | 0 |
| faculty-life | 6 | 39 | 39 | 37 (95%) | 20 (51%) | 17 / 0 | 0 | 0 |
| finance-economics | 7 | 59 | 57 | 47 (82%) | 31 (54%) | 14 / 0 | 2 | 0 |
| lab-integrations | 9 | 77 | 74 | 66 (89%) | 27 (36%) | 40 / 1 | 3 | 0 |
| methodology | 3 | 19 | 19 | 17 (89%) | 7 (37%) | 10 / 0 | 0 | 0 |
| research-tools | 14 | 107 | 91 | 80 (88%) | 53 (58%) | 26 / 0 | 15 | 1 |
| social-science-workflow | 17 | 91 | 91 | 89 (98%) | 54 (59%) | 36 / 1 | 0 | 0 |
| turkish-academia | 13 | 93 | 87 | 77 (89%) | 41 (47%) | 36 / 0 | 6 | 0 |
| visualization | 9 | 63 | 60 | 56 (93%) | 30 (50%) | 26 / 0 | 3 | 0 |
| workflows | 1 | 7 | 7 | 6 (86%) | 3 (43%) | 3 / 0 | 0 | 0 |
| writing-tools | 14 | 94 | 92 | 69 (75%) | 42 (46%) | 26 / 0 | 1 | 1 |
| **All** | **241** | **1598** | **1532** | **1380 (90%)** | **804 (52%)** | **571 / 2** | **50** | **16** |
<!-- END generated:domain-table -->

*Cases* counts every case with a final run, and *Graded* those with a PASS or FAIL in the
skilled arm. *Infra / inconclusive* counts skilled-arm outcomes that are neither a verdict nor
not runnable here: INFRA_ERROR, INCONCLUSIVE, REFUSED, or NOT_RUN after an aborted run. The
*workflows* row is the `alterlab-research-workflows` playbook skill answering its own eval
prompts; none of the seven dynamic workflows was run.

### Reading the table

<!-- This reading describes the 2026-11-04 numbers. Re-check it whenever the generated blocks are regenerated. -->

- With the skill, about nine in ten graded cases passed; without it, about half of the same
  cases did.
- Most of that gap is on cases where the skill should do the task. On near-miss cases, where the
  right answer is to hand the request to a sibling skill, both arms passed most of the time.
- Hurt cases are few next to helped ones (2 against 571), after two passes of fixes over every
  case the skill made worse. See
  [Where the skill made answers worse](#where-the-skill-made-answers-worse).
- Writing-tools has the lowest skilled pass rate in this snapshot (75%); its long-form cases
  (literature reviews, slides, posters) carry many rubric points. Methodology, document-tools
  and workflows have 19 cases or fewer, so a single case moves their percentages by five points
  or more.
- The table is per domain. A high domain rate does not mean that every skill in the domain
  passed all its cases.

## Where the skill made answers worse

Every *hurt* case (skilled FAIL, bare PASS) in the final set after round `final_c` was read by
hand: both answers, the case's rubric and its assertion verdicts. There were 32. Each got one
cause:

| Cause | Cases | What it means |
|---|---:|---|
| Skill defect | 13 | the skill's own instructions or scripts led to the wrong answer |
| Check too strict | 8 | the answer was right, but a required phrase or a narrow rubric missed it |
| One-off model slip | 7 | an error in that answer that the skill's text does not explain |
| Runner environment | 2 | a cut-off reply, or a sibling skill the single-skill harness cannot load |
| Outside service | 1 | OpenAlex refused the search (its shared daily budget; OpenAlex has since been removed) |
| Judge error | 1 | the rubric verdict contradicts the answer, and a behavior check on the same point passed |

Two things inflate the hurt count. In 17 of the 32, the skilled answer passed the same rubric
the bare answer passed and failed only a check the bare arm is never given (see
[How answers are graded](#how-answers-are-graded)). And 14 of the 32 are near-miss cases, where
the right answer is to hand the request on.

**Fixed and re-run.** Six of the 13 skill defects were the same gap: the skill's *Does NOT
Trigger* table did not list the sibling the request belonged to, so the answer handed off
nowhere or did the work itself. The missing rows were added to `alterlab-deep-research` (thesis
supervision), `alterlab-jaspar` (protein-protein interaction networks), `alterlab-literature-review`
(BibTeX handling; manuscript prose), `alterlab-scientific-slides` (manuscript prose) and
`alterlab-uspto` (compound look-ups), and those five skills were re-run in full (`final_e`).
All six now pass with the skill. No other case in those five skills got worse because of the
change: one `alterlab-uspto` case failed on the re-run only because the answer wrote the patent
number as "10,902,286" where the check wanted "10902286"; the check now takes either spelling of
the same number, and the case passes.

A static check of every near-miss eval against its skill's routing table then found five more
skills that never named the expected sibling; one of them, `alterlab-aeon`, had just failed
the same way (it wrote its own Navier-Stokes solver instead of naming `alterlab-fluidsim`). Rows
were added to `alterlab-aeon`, `alterlab-datacommons`, `alterlab-histolab`, `alterlab-primekg`
and `alterlab-tiledbvcf`. Two timeouts turned out to be skill defects too: `alterlab-chembl`
iterated 10,665 activity records 20 at a time (it now counts first and pages the REST API at
1,000), and `alterlab-biorxiv` scanned a year of bioRxiv to find one author (it now asks Europe
PMC's server-side author filter). `alterlab-alpha-vantage` no longer stops to ask for a contact
e-mail: its SEC fundamentals now come from contact-free endpoints. All of these skills were
re-run.

Those last re-runs (`final_g` to `final_i`, 239 cases in the 33 skills changed by the removal of
OpenAlex and the fixes above) moved 12 cases from not passing to PASS and 17 from PASS to not
passing. Of the 17, five failed only a required phrase and one only a behavior check while the
rubric passed, five ended in a timeout or infrastructure error, and six failed the rubric. Four
of those six were read by hand and look reasonable (a seed paper asked for when the prompt
gives none, a correct hand-off, a correct import file, a correct TR Dizin result table); the
other two were not investigated: `alterlab-denario`'s, and `alterlab-alpha-vantage`'s daily-prices
case, which passed when that skill was re-run once more (`final_j`). The rewritten `build_graph.py`
finishes in under 20 s on the seeds tried, including a paper with about 73,000 citations, so the
`alterlab-citation-graph` timeout comes from what that answer chose to run, not from the script.
With one run per case, part of this movement in both directions is run-to-run variation.

**Second pass (2026-11-04).** The 27 cases that were still hurt after the rounds above were
read again, skill by skill, and the cause fixed where it lay in the skill:

- **Hand-offs** (arxiv, preregistration-discipline, ssci-design-gate, omero, research-workflows,
  tubitak-bideb, hypothesis-gen): each skill now says what is in scope for it, after the shared
  hand-off paragraph (which is unchanged), so a request that only mentions this skill's topic as
  context gets a clean hand-off, and hypothesis-gen still gives a short list of directions
  when it hands off. A first version for tubitak-bideb put 3501's evaluation criteria in its
  routing row; the re-run showed answers reciting them instead of handing off, so the row went
  back to naming the programmes and the scope sentence was tightened.
- **Reporting** (datacommons, ena, fred, hedgefund-monitor, pdb, plotly, matplotlib, scvi-tools,
  pdf-extract, protocolsio, pyzotero): answers now end with how the result was obtained (the
  call or endpoint with its parameters, the files written, the retrieval date), which a reader
  needs to reproduce it.
- **Defects in scripts and instructions:** datacommons' coordinate resolve now asks Data Commons'
  keyless v1 resolver as well as v2 before falling back to a geocoder; scientific-slides'
  validator now finds text past a slide's edge in a PDF (it only counted pages); matchms now
  explains greedy vs Hungarian peak matching; pdb gained a keyless structure-similarity command
  that matches rcsb-api's counts; scientific-brainstorm puts the gaps in one reply; scvi-tools'
  install commands pin Python >= 3.12 (an older interpreter silently installs 1.1.6).
- **A wrong eval:** pubmed's citation-match case used an unregistered DOI (doi.org 404, PubMed 0
  hits), so no answer could pass; it now uses a real one (PMID 33301246), assertions unchanged.
- **Left alone:** `alterlab-pyzotero:near-miss-citation-mgmt` and
  `alterlab-ssci-measurement-gate:reliability-is-not-validity`, where other runs with
  equivalent answers passed and the failing verdict contradicts the answer.

Every changed skill was re-run in full (`final_k`, `final_l`, `final_m`).

<!-- BEGIN generated:second-pass -->
- Of the 27 hurt cases, **25 now pass with the skill**; 2 are still hurt: `alterlab-omero:near-miss-opentrons`, `alterlab-ssci-measurement-gate:reliability-is-not-validity`.
- The re-runs covered 168 cases in 24 skills: 35 moved to PASS and 4 moved away from it (`alterlab-pdb:sequence-similarity-search`, `alterlab-pubmed:batch-efetch-abstracts`, `alterlab-ssci-design-gate:observational-causal-overreach`, `alterlab-tubitak-bideb:conference-2224a-points-timing-turkish`). Without the skill, all of those also fail. With one run per case, part of that movement is run-to-run variation.
- Suite-wide, the skill now helps on 571 cases and hurts on 2.
<!-- END generated:second-pass -->

## Before and after the fixes

The first live run of a case exposed defects, which were fixed before the final run: in skills
(scripts, instructions, `allowed-tools`), in eval cases (missing input files, wrong expected
answers, assertions, `requires` tags), and in the harness itself (see the
[`CHANGELOG.md`](../CHANGELOG.md) `[4.0.0]` section). This section compares the first run
and the final run on the cases that have both.

<!-- BEGIN generated:before-after -->
- **1,525 cases** have both a first run and a final run.
- Skilled arm PASS: **1,109 → 1,325**. Bare arm PASS: **788 → 789**.
- Skilled-arm outcome changes: FAIL → PASS 249, PASS → FAIL 42, FAIL → NOT_RUN 37, INFRA_ERROR → PASS 17, PASS → NOT_RUN 9, INFRA_ERROR → FAIL 8, FAIL → INFRA_ERROR 4, PASS → INFRA_ERROR 3, NOT_RUN → PASS 3, INFRA_ERROR → NOT_RUN 1, INCONCLUSIVE → PASS 1.
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
| API key or account (env) | 38 | ADAPTYV_API_KEY, BGPT_API_KEY, COSMIC_PASSWORD, DRUGBANK_PASSWORD, DX_SECURITY_CONTEXT, FRED_API_KEY, MP_API_KEY, OMERO_HOST, OMERO_PASSWORD, OMERO_USER, OPENROUTER_API_KEY, PARALLEL_API_KEY, ROWAN_API_KEY, USPTO_ODP_API_KEY, ZOTERO_API_KEY, ZOTERO_LIBRARY_ID |
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
  2.1.308 (2026-10-22), 2.1.309 (2026-10-23), 2.1.316 (2026-11-02) and 2.1.318 (2026-11-04).
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
  [Licensing](../README.md#-licensing) in the README).
- **ÜAK website unreachable.** The ÜAK website (uak.gov.tr) was unreachable from the runner.
  Cases that would read the current doçentlik criteria there carry no `net:` tag, so they ran
  and were graded without live access to the site.
- **`bcftools` not installed.** `bcftools` is not installed on the runner; the case that needs
  it is not runnable here.
- **OpenAlex removed; Semantic Scholar search best-effort.** OpenAlex's budget for requests
  without a key ($0.10 a day, shared by everyone on the same IP address) ran out during the
  final round, so real use needs an account. 4.0.0 removes `alterlab-openalex` and every use of
  OpenAlex, and the skills that used it were rewritten on keyless sources and re-run. A probe of
  every host on the skills' default paths then found Semantic Scholar's shared keyless search
  pool exhausted from this runner too; its search is now best-effort and never a precondition.
  Answers in the final runs still report Semantic Scholar rate limits on some look-ups.
- **Denied tool calls.** The arms get exactly the skill's `allowed-tools`. In the final set after
  `final_c`, 429 of 1,529 answered skilled runs had at least one tool call denied, mostly commands that began with
  `cd …;`, which patterns such as `Bash(python:*)` do not match. Arms usually retried with a
  full path, at the cost of turns. This weighs on the skilled arm more than the bare arm, which
  runs fewer scripts.
- **Refusals.** The CLI's usage-policy classifier refused a few prompts: 1 skilled-arm and 3
  bare-arm answers in the final set (one glycoengineering case in both arms). Those are
  REFUSED, not graded.
- **Raw results not in the repository.** The run records (full answers, verdicts, reasons and
  costs per case) are in `eval-results/`, which is git-ignored. Answers can echo the account's
  e-mail address from the login context, so the runner replaces every e-mail address in saved
  results with `[email redacted]` (reserved example domains excepted), and the records behind
  this page were scrubbed the same way.

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
