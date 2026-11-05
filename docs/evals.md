# Eval Authoring Guide

Every skill ships an eval file at `skills/<domain>/<skill>/evals/evals.json`. Evals are how
we answer the loudest objection to academic skills — *"these are just prompts with no
evals"* — with something executable. This guide is the single source of truth for **what an
eval file must contain, how to phrase cases, and how they are checked.**

The canonical shape is defined by [`docs/evals.schema.json`](./evals.schema.json) (reproduced
in full at the bottom of this file). It is validated per-PR by
`scripts/run_evals.py --strict`; the behavioral judge (`run_evals.py --behavioral`) shells to
the `claude` CLI and LLM-grades each `expected_output`.

## The canonical shape

```json
{
  "skill": "alterlab-deep-research",
  "evals": [
    {
      "id": "full-research",
      "prompt": "A realistic researcher ask, phrased the way a faculty member would type it.",
      "expected_output": "Prose description of the correct behavior — the rubric the judge grades against.",
      "files": [],
      "assertions": [
        { "type": "should_trigger", "value": true }
      ]
    }
  ]
}
```

- **`skill`** (required) — must match the skill's frontmatter `name` and its directory name.
- **`evals`** (required, ≥1) — the array of cases.
- Per eval: **`id`**, **`prompt`**, **`expected_output`** are required; **`files`** and
  **`assertions`** are optional but `assertions` is effectively mandatory (see below).
- **`files`** — the input the prompt refers to. A path may name a file or a whole directory
  (copied as a tree, e.g. a small repository checkout), relative to the eval file's directory.
  A prompt that says "here is my draft" must ship the draft: without it a correct answer can
  only ask for it.
- **`requires`** — optional preconditions the case cannot be judged without: `env:NAME` (an
  environment variable such as an API key), `cmd:NAME` (an executable, e.g. `cmd:Rscript`),
  `net:HOST` (a host the runner must reach), `mcp:NAME` (an MCP server — never available,
  since answer arms run with `--strict-mcp-config`). A case whose requirement is unmet is
  `NOT_RUN` with reason "not runnable here", never `FAIL`, and the summary counts it under
  `not_runnable_here`.
- **`artifact_checks`** — optional files the answer must produce, checked deterministically
  after each run (see [Artifact checks](#artifact-checks)).

### Assertion types

| `type` | `value` | Meaning | Dimension (v2) |
|--------|---------|---------|----------------|
| `should_trigger` | `true` | This skill **should** activate on the prompt. | `routing` |
| `should_not_trigger` | `true` | This skill should **not** activate (near-miss / another skill's job). | `routing` |
| `output_contains` | string, or list of strings | The response must contain this substring (case-insensitive). A list passes when any one entry occurs — use it when a correct answer may be written in Turkish or English (`["Art. 28", "m. 28", "madde 28"]`). | `substantive`, or `skill_vocabulary` when every needle is an internal name |
| `behavior` | string | A free-text rubric clause the behavioral LLM judge grades. | `substantive` |

Prefer `output_contains` needles a correct answer from *any* assistant would contain: a
number, an identifier, a public tool or API name. A needle that is only a suite skill name
(`alterlab-paper-writer`, `citation-mgmt`) or internal apparatus (`Iron Law`, `Revision
Roadmap`) is scored as `skill_vocabulary`: reported, but it never decides a case (see
[Dimensions](#dimensions-and-the-outcome-rule)).

Every eval carries **exactly one** `should_trigger` *or* `should_not_trigger` assertion
declaring whether the skill should fire. `output_contains` and `behavior` are additional,
optional refinements — use them to pin down *how* a triggering skill should respond, or to
assert the specific deferral target on a near-miss.

> The legacy `{query, expected_behavior, should_trigger}` shape is gone. `should_trigger`
> survives **as an assertion type**, so migrated files keep their trigger/near-miss coverage.
> Run `uv run python scripts/migrate_eval_schema.py` to convert any remaining legacy file.

## Conventions (these are enforced)

1. **Coverage bar: ≥3 trigger evals + ≥1 near-miss negative per skill.** `run_evals.py
   --strict` fails a file with fewer than 3 `should_trigger` cases or zero
   `should_not_trigger` cases. In practice author 4-8 cases: cover the skill's distinct
   **modes/intents** with the triggers, and 1-3 near-misses.
2. **IDs are kebab-case** (`^[a-z0-9]+(-[a-z0-9]+)*$`), unique within the file, and
   descriptive of the case (`full-research`, `socratic-guided`, `near-miss-paper-writer`).
   Prefix every near-miss with `near-miss-<adjacent-skill>` so the deferral target is obvious.
3. **Prompts are realistic researcher asks.** Write what a faculty member or grad student
   would actually type — first person, concrete domain, real artifacts ("Here is a
   colleague's finished manuscript…", "I already have my synthesis and bibliography ready…").
   No meta-phrasing like "test whether the skill triggers."
4. **A near-miss is an adjacent skill's territory.** The strongest negative is a prompt that
   is *plausibly* this skill but is correctly handled by a sibling: e.g. for
   `alterlab-deep-research`, "write me the full journal paper from my finished synthesis" is
   `alterlab-paper-writer`'s job. State the deferral in `expected_output` and, where useful,
   assert it with `output_contains` (e.g. `"defers to alterlab-paper-writer"` — scored in the
   `skill_vocabulary` dimension, reported but not gating, since only the suite knows that
   name). Avoid
   off-topic negatives (e.g. "book me a flight") — they prove nothing about boundary
   discrimination.
5. **`expected_output` is the judge's rubric.** Describe the observable behavior precisely
   enough to grade: which mode runs, which agents/phases fire, what artifacts come out, what
   standards apply (PRISMA, APA 7, FINER). For negatives, name the skill it should defer to
   and *why* this one should not fire.
6. **`files` for fixtures.** When the ask needs an attached manuscript, dataset, or
   bibliography, list fixture paths (relative to the `evals/` dir) or inline
   `{name, content}` objects. Keep fixtures small.

## Validate locally

```bash
# Shape + coverage gate (the per-PR CI check):
uv run python scripts/run_evals.py --strict

# Schema-validate one file against the canonical schema:
uv run --with jsonschema python -c "import json,sys; from jsonschema import Draft202012Validator as V; \
s=json.load(open('docs/evals.schema.json')); \
V(s).validate(json.load(open(sys.argv[1])))" \
  skills/core/alterlab-deep-research/evals/evals.json

# Behavioral grading (slow; live model calls through the claude CLI's login). Uses the model
# from ALTERLAB_MODEL — see skills/core/shared/model_env.md. Grade one skill at a time:
uv run python scripts/run_evals.py --behavioral --skill alterlab-docentlik-eligibility
# Re-test only the cases whose eval changed (the skill itself unchanged); repeatable:
uv run python scripts/run_evals.py --behavioral --skill alterlab-trdizin --case audit-venue-list-before-dossier
# The v1 rubric judge, for comparison with results written before schema v2:
uv run python scripts/run_evals.py --behavioral --skill alterlab-trdizin --judge literal

# Static report of rubrics/assertions that require internal names (no model calls):
uv run python scripts/run_evals.py --audit-rubrics --audit-out rubric-audit.json
```

`--case` is for re-testing a fixed eval, not for picking favourable cases: when a skill's
`SKILL.md` or bundled files change, every case of that skill needs a fresh run, because the
skilled arm reads them in all of them.

### Three separate things this harness measures

| Mode | What it shows | What it does **not** show |
|------|---------------|---------------------------|
| default / `--strict` (static) | every skill ships a schema-valid `evals.json` with ≥3 trigger and ≥1 near-miss cases | that any skill behaves correctly — no model is called |
| `--behavioral` (live) | per case and arm, four dimensions: substantive (rubric, `behavior`, substantive `output_contains` — identical for both arms), routing (skilled arm), skill vocabulary (reported only), and declared output files | research correctness beyond what the rubric checks; the judge is the same model family |
| `--activation` (live) | whether the model picks the right skill from its description among same-domain distractors | that the picked skill then does the task well |

Keep the three apart when reporting: "241 skills have evals" is a statement about the static
check only.

The latest live `--behavioral` run of the suite, skilled vs bare, is reported in
[`behavioral-results.md`](behavioral-results.md).

### Isolation

Each behavioral case runs both arms from fresh temporary directories, never from this
repository, with `--safe-mode --disable-slash-commands --strict-mcp-config
--no-session-persistence`: no CLAUDE.md, installed plugins, skills, hooks, or MCP servers. The
**skilled arm** gets the SKILL.md through `--append-system-prompt`, the skill's own files in
`./skill/` (its `evals/` folder is never copied, so expected outputs stay hidden), the domain's
`shared/` resources in `./shared/`, and the task fixtures in `./fixtures/`. The **bare arm**
gets only `./fixtures/`. Neither arm ever sees `evals/evals.json`, so expected outputs, assertions and
`artifact_checks` (with their expected values) stay hidden; the only part of an eval an arm
sees besides its prompt is the save-here note for declared artifacts. The judges run in their own empty directories. Both arms' answer calls are granted the
skill's `allowed-tools` frontmatter (`--allowedTools`), the set Claude Code pre-approves when
the skill is active; the bare arm gets the same set so the comparison isolates the skill's
instructions, and the judges get no tools. Without this, a skill that must run its script or
query a live service fails by construction and a correct refusal to answer from memory is
scored FAIL. Auth is the CLI's normal
login, so the harness runs inside an authenticated Claude Code environment with no API key.
(`--bare` would be stricter, but it ignores OAuth logins and requires `ANTHROPIC_API_KEY`.)

**A temporary directory is not a sandbox.** On 2026-10-15 the bare arm of a link-health case
("close out the remaining residual broken links"), holding that skill's `Write Edit Bash`
grants, found this checkout on disk and edited 29 files in it. Answer arms are now kept away
from the repository in three layers:

1. **Namespace** (`--isolation auto`, the default; `namespace` makes it mandatory). On Linux
   each CLI call runs in a private mount namespace (`unshare -m`, or `unshare -r -m` without
   root) in which this checkout and every worktree of it are covered by an empty read-only
   tmpfs. The arm sees an empty directory, and a write there fails with "Read-only file system".
   The arm also gets a **private temp root** that holds only its own workspace, fresh
   `/var/tmp` and `/dev/shm`, and empty installed-plugin, skill and session-transcript folders
   (`~/.claude/{plugins,skills,projects,todos}` for every home, and `/mnt/skills`). Arms that
   could not find their input searched the whole disk; before this layer one bare arm reported
   "a sibling folder (`../skilled/skill/`) containing a literature-review skill", the very skill
   it was the baseline for, and others listed other sessions' scratch files.
2. **Scoped grants.** A bare `Write`, `Edit`, `MultiEdit` or `NotebookEdit` grant becomes an
   absolute rule for the arm's workspace (`Write(//tmp/alterlab-eval-…/**)`). Environment
   variables that point into the checkout are dropped, and PATH loses those entries.
3. **Tripwire.** The checkout is fingerprinted (HEAD, tracked diff, untracked files) before
   the run and after every case. Any change aborts the run as `blocked` with
   `isolation breach: …`, lists the changed paths, and reverts nothing.

Checked live: a real arm granted bare `Write` and `Bash`, told to write into the checkout,
was denied by the Write tool and got "Read-only file system" from the shell. Without the
namespace (macOS, or a runner that forbids user namespaces) shell grants such as `Bash`,
`Bash(python:*)` or `Bash(uv run:*)` can still write anywhere. The tripwire then catches
changes to the checkout but nothing else, so run behavioral evals in a disposable checkout or
container. The run record's `isolation.confinement` says which mode was in effect.

### Reading a `--behavioral` run

Every case ends in exactly one outcome per arm, printed with its reason:

| Outcome | Meaning |
|---------|---------|
| `PASS` / `FAIL` | the usable verdicts, derived from the gating dimensions (rule below) |
| `INCONCLUSIVE` | the model answered, but the gating dimensions settled no verdict (a judge tie, or an unparseable judge reply — never scored as a silent FAIL) |
| `REFUSED` | the runner environment's usage-policy classifier refused the prompt |
| `INFRA_ERROR` | the CLI failed, timed out, could not authenticate, a judge call failed, or a fixture file was missing (the case is never run without its input) |
| `NOT_RUN` | the run aborted after `--max-infra-errors` (default 6) consecutive infrastructure errors, or the case's `requires` are not met here |

#### Dimensions and the outcome rule

Results files written by this runner carry `schema_version: 2`. Each arm of each case has four
`dimensions`, each `PASS`, `FAIL`, `NA` (no settled verdict) or `null` (does not apply):

| Dimension | Criteria | Skilled arm | Bare arm | Gates the outcome |
|-----------|----------|-------------|----------|-------------------|
| `substantive` | the `expected_output` rubric, every `behavior` clause, every substantive `output_contains` | yes | yes — **the same criteria** | yes |
| `routing` | `should_trigger` / `should_not_trigger` (trigger judge: did the answer engage the skill's workflow, or decline?) | when the case has one | `null` (no skill to engage) | yes |
| `skill_vocabulary` | `output_contains` whose every needle is an internal name | when the case has one | same as skilled | **no** — reported only |
| `artifacts` | every check of every declared `artifact_checks` file | when declared | same as skilled | yes |

Within a dimension, each criterion is majority-voted over the `--runs` runs (ties and
all-NA give `NA`); the dimension is `FAIL` if any criterion's majority is `FAIL`, `PASS` if
all are `PASS`, else `NA`. The arm's verdict is `FAIL` if any gating dimension that applies is
`FAIL`, `PASS` if all of them are `PASS`, otherwise no verdict. The outcome is that verdict
when the arm answered; an arm that never answered is `REFUSED` or `INFRA_ERROR`; an answered
arm without a verdict is `INFRA_ERROR` when a judge call itself failed, else `INCONCLUSIVE`.

**Why vocabulary does not gate.** Many rubrics and needles name the suite itself ("defers to
`alterlab-paper-writer`", "applies the Iron Law"). A bare arm can never write those names, so
under v1 the skilled-vs-bare delta partly measured vocabulary. An `output_contains` assertion
is `skill_vocabulary` when every needle — lower-cased, stripped, a leading `/` and an
`alterlab-workflows:` prefix removed — (a) contains an `alterlab-<name>` identifier, (b) equals
a suite skill's hyphenated short name (`citation-mgmt`, `research-lookup`) that is not also a
public name or ordinary hyphenated term (`scikit-learn`, `scvi-tools`, `meta-analysis`,
`peer-review`, … — the `_PUBLIC_HYPHENATED` list), (c) equals a hyphenated packaged-workflow
name (`citation-audit`; the one-word `rebuttal` stays substantive), or (d) equals an internal
apparatus term (`Iron Law`, `Excuse-vs-Reality`, `Revision Roadmap`, `Chapter Plan`, `Design
Passport`, `INSIGHT Collection`, `RQ Brief`, `Methodology Blueprint`, the re-review statuses
`FULLY_ADDRESSED` / `PARTIALLY_ADDRESSED` / `NOT_ADDRESSED` / `MADE_WORSE`) or one of the
citation verifier's taxonomy codes (`TF`, `PAC`, `IH`, `PH`, `SH`). A list with any other
needle (`["clinvar", "alterlab-cosmic"]`) stays substantive: when in doubt, a needle gates.
`behavior` clauses and `expected_output` always stay substantive; the substance judge is told
to grade what a named apparatus stands for, and concrete requirements (a number, a refusal, a
named tool or skill to route the user to) remain required. A rubric that requires naming a
sibling skill therefore still cannot be met by a bare arm — `--audit-rubrics` lists them:

```bash
uv run python scripts/run_evals.py --audit-rubrics --audit-out rubric-audit.json
```

On the corpus at the time of writing it reported 505 of 1,353 `output_contains` assertions as
vocabulary-only, 1,389 `expected_output` rubrics naming an `alterlab-` skill (835 of them a
self-invocation, "Invokes alterlab-<this skill>"), 17 naming internal apparatus, and 22
`behavior` clauses naming skills or apparatus. These are counts from the static audit, not
measurements of grading quality. The rubrics were not mass-edited.

The per-case **`rubric:` delta** (`SKILL HELPED` / `HURT` / `NO DELTA` / `INCONCLUSIVE`)
compares the two arms' `substantive` dimensions — identical criteria for both arms — so it is
no longer confounded by assertions only one arm was graded on. (In v1 it compared the rubric
majorities only.)

The summary reports **selected, attempted, answered, and usable verdicts**, the coverage
(usable ÷ selected), both arms' outcome counts, per-dimension counts (`summary.dimensions`),
the rubric delta, CLI calls, wall-clock time, and the cost the CLI reports. Exit codes:

| Exit | Status | Meaning |
|------|--------|---------|
| `0` | `passed` | **every** selected case produced a verdict and passed |
| `1` | `failed` | at least one case failed |
| `2` | `blocked` | no case produced a usable verdict (no CLI, no login, every call refused or timed out, or the filter matched nothing). The run verified nothing |
| `3` | `partial` | some cases produced verdicts and none failed, but others did not — the selection is **not** fully evaluated |

### Artifact checks

Grading the final message alone cannot tell an answer that *says* it saved `figure.png` from
one that did. An eval may declare the files its answer must produce:

```json
"artifact_checks": [
  {"path": "out/multipanel.png", "type": "png",
   "description": "the three-panel figure, exported as a 300 DPI PNG",
   "checks": [{"kind": "png_dpi", "expected": 300, "tolerance": 1},
              {"kind": "png_min_size", "min_width": 900, "min_height": 600}]}
]
```

- **Both arms get the same note** appended to the prompt: save each file at its relative path
  (with its type and `description`). They never see the checks or expected values, which live
  in `evals/evals.json` — a folder `prepare_workspace` never copies.
- **After every run, before the temporary workspace is deleted**, each declared file is
  inspected by `scripts/artifact_checks.py`, hashed, and copied to
  `<results-dir>/artifacts/<run-stamp>/<case>/<arm>/run-N/<path>` (files over 25 MB are graded
  but not copied). Declared outputs left by an earlier run of the same arm are deleted before
  the next run, so a run is never credited with them.
- `exists` and `parseable` are always checked. A missing file, a symlink (never followed), a
  directory, an unreadable or unparseable file fails **every** check declared for it: it can
  never count as completed artifact work. A run that produced no answer records its files but
  its checks are `NA`.
- Expected values (`value`, `expected`, `tolerance`, `min`, …) are written by the eval author
  from the fixture, never computed from the model's output.

| `kind` | Types | Parameters |
|--------|-------|------------|
| `exists`, `parseable` | all | — (`parseable`: JSON parses; CSV has a header and no ragged rows; PNG chunks pass their CRCs and the pixel stream decompresses to the size the header says; PDF has a header, `%%EOF` and ≥1 page; PPTX is a zip with `ppt/presentation.xml`; BibTeX has ≥1 entry and balanced braces; md/txt are non-empty UTF-8) |
| `json_keys` | json | `keys`, optional `path` (dotted; integer segments index arrays) |
| `json_path_equals` | json | `path`, `value` (exact JSON equality; `true` ≠ `1`) |
| `csv_columns` | csv | `columns` (header names, case-insensitive) |
| `min_rows` | csv, json, bib, md, txt | `min`, optional `max`, optional `path` (json array); rows = data rows, array items, BibTeX entries, or non-blank lines |
| `number_within` | json, csv | `expected`, `tolerance`; json: `path`; csv: `column` and either `row` (0-based) or `match` (`{"column": "od600"}`) |
| `contains_text` | json, csv, md, txt, bib, pptx, pdf | `text` (string or any-of list, case-insensitive); PDF text needs `pypdf` (else `NA`) |
| `png_min_size` | png | `min_width`, `min_height` (pixels) |
| `png_dpi` | png | `expected`, `tolerance` (from the PNG's `pHYs` chunk; none recorded = `FAIL`) |
| `pdf_min_pages` | pdf | `min` (pypdf when installed, else counted page objects) |
| `pptx_min_slides` | pptx | `min` |

The schema (`docs/evals.schema.json`) and the built-in validator both check declarations;
the built-in one also checks that each kind suits its file type. Cases that declare artifacts
today: `alterlab-matplotlib` (`mpl-multipanel-gridspec`: 300 DPI PNG;
`mpl-publication-export-pdf`: PDF + 300 DPI PNG), `alterlab-eda` (`csv-tabular-eda`: a
per-column summary CSV whose missing counts must match the fixture — od600 12, ph 5,
temperature_c 0), and `alterlab-citation-mgmt` (`format-deduplicate-bibtex`: a cleaned `.bib`
with exactly 4 entries and `--` page ranges).

### Collect-only runs and other endpoints

`--collect-only` runs the answer arms, saves every response in full, and calls no judge; it
exits `0` when every arm answered. Deterministic checks (`output_contains`, artifacts) are
still recorded. Grade the saved answers later with `--regrade` and a judge that passed
`--calibrate-judge`. This is meant for defect sweeps: whether a prompt is missing its input, a
tool was denied, or a script crashed does not depend on a judge.

The run record's `endpoint` says who answered: `claude-cli-login`, or `base-url:<host>` when
`ANTHROPIC_BASE_URL` points the CLI at another server (for example a local model behind
llama-swap). Results from another endpoint describe that model, not Claude — keep them in a
separate results directory and never mix them into Claude numbers.

### Two rubric judges, and checking them

`--judge` selects the rubric judge for `--behavioral` and `--regrade` (it grades the
`expected_output` rubric and every `behavior` clause; routing has its own trigger judge):

- **`substance`** (default) grades what a response does: the decision, the numbers, the refusal
  or the request for missing input, the named sibling skill when the rubric asks for a
  hand-off. It does not require the skill's own vocabulary, and still fails a wrong answer that
  recites it. It is the default because it agreed with every hand label on its last calibration
  (below), and because v2 already reports vocabulary as its own dimension.
- **`literal`** grades the rubric as written — the v1 judge. Use it to compare with results
  written before schema v2; the outcome rule is still v2's, so a `--judge literal` run is not a
  v1 run either.

Every results file records `judge: {name, prompt_version, prompt_sha256,
trigger_prompt_version, trigger_prompt_sha256, applied}` (`applied: false` for collect-only).
Report which judge produced a number.

Before trusting a judge, run it on the hand-labelled pairs in
[`judge_calibration.json`](judge_calibration.json). Judge calls only:

```bash
uv run python scripts/run_evals.py --calibrate-judge --judge substance   # one judge
uv run python scripts/run_evals.py --calibrate-judge                     # both
```

Exit `0`: every calibrated judge agreed with every label; `1`: a judge contradicted a label;
`2`: blocked — the calibration file is unusable or no judge call returned a verdict; `3`:
partial — no contradiction, but some pairs got no verdict. Only `0` makes a judge usable.

On 2026-10-15 (`claude-opus-5-5`, 8 pairs): literal 7/8, substance 8/8. The literal judge failed
a correct answer that asked for the missing abstract instead of inventing one. Five pairs were
added later for the vocabulary-vs-substance split (a correct answer without the skill's jargon,
and a wrong answer that recites it); they are marked `"labelled_by": "repair agent, pending
maintainer review"`.

On 2026-11-05 (`claude-opus-5-5`, CLI 2.1.318, all 13 pairs, one judge call per pair and
judge): literal 12/13, substance 13/13; the literal judge again failed
`asks-for-missing-input`. Both judges graded the five new pairs as labelled. Two limits: those
five labels were written by the same repair pass that wrote the classifier, and the substance
template was written with the original eight pairs in view, so this is a consistency check on a
small set, not an independent validation of the judge.

#### Re-grading saved answers (`--regrade`)

Every run record keeps the full response text, so a finished run can be re-judged without new
answer calls:

```bash
uv run python scripts/run_evals.py --regrade eval-results/behavioral-<UTC>.json --judge substance
uv run python scripts/run_evals.py --regrade eval-results/sweep/*.json      # many files
```

Each file is regraded with the v2 rules and written as `regrade-*.json` (`schema_version: 2`,
`kind: behavioral-regrade`, `regraded_from`, `regraded_from_schema_version`, every flipped
outcome in `flips`, every original verdict next to its new one). `output_contains` is
recomputed and the rubric and `behavior` clauses re-judged on **both** arms, so a v1 file's
bare arm is graded on the full substantive criteria for the first time. Saved routing verdicts
are reused; routing assertions that were never judged (collect-only runs) are judged now.
Saved artifact-check verdicts are reused; a v1 run of a case that now declares
`artifact_checks` has an `NA` artifacts dimension (its files were never checked). Per case,
`hashes.rubric_sha256` is the rubric used now and `hashes.rubric_sha256_at_run` the one the run
recorded (`null` for v1) — when they differ, the eval changed after the answers were made.

The exit code means **answer quality, as for `--behavioral`**, aggregated over every requested
file: `0` every regraded case PASS in every file; `1` some regraded case FAILed; `2` blocked —
nothing could be regraded or judged (every file unreadable, malformed, not a behavioral results
file, of an unknown `schema_version`, or the judge returned no verdict at all); `3` partial —
some files, cases or arms have no usable regraded verdict. Unusable files are reported
(`<file>: BLOCKED — malformed JSON …`), never raised. An arm whose answers were saved without
full text is counted in `arms_not_regraded` and reported `INCONCLUSIVE` with its old outcome in
`outcome_original`; it is never shown with its v1 verdict as if regraded. A per-file status line
and a final `REGRADE RESULT:` line are printed.

Only exit `0` may be described as "the selected cases pass", and only for the selected cases.
A sharded or filtered run validates its shard, not the suite.

### The results record (schema v2)

Every run writes a JSON results file to `eval-results/` (git-ignored; `--results-dir` to
change, `--results-dir ''` to skip). Top level: `schema_version` (2), `kind`, `methodology`
(`v2-dimensions`), `judge` (above), `runner` (`script`, `script_sha256`,
`artifact_checks_sha256`), the model id, `claude` CLI version, repo commit and dirty flag,
isolation flags, `artifacts_dir`, `status`, `status_reasons`, `summary`, `usage`, `cases`.
Per case: the case ID, skill version, fixtures, `hashes` (`skill_md_sha256`, `rubric_sha256` —
canonical JSON of `expected_output` + `assertions` + `artifact_checks` — and
`fixtures_sha256`), and per arm `outcome`, `reason`, `dimensions`, `assertion_verdict`,
`rubric_majority`, `answered_runs` and `runs`. Each run records its outcome, error (redacted —
token-shaped strings are stripped), rubric verdict, every assertion with its `dimension`,
`artifacts` (`path`, `type`, `exists`, `parseable`, `sha256`, `bytes`, `stored_as`, `checks`),
response excerpt and full response, duration, turns, reported cost and denied tools. Failure
diagnostics name the likely cause (authentication, rate limit, timeout, missing CLI) without
echoing credentials.

Records written before this change have `schema_version: 1`: one combined outcome per arm from
the literal judge, the bare arm graded on the rubric only. Read them as the
`v1-combined-literal-judge` methodology and never mix their outcomes with v2 outcomes;
`--regrade` turns one into a v2 record. [`eval-aggregation.md`](eval-aggregation.md) describes
`scripts/aggregate_results.py`, which summarises these records and keeps the two apart.

**`REFUSED`** cases: the `claude` *Claude Code CLI* applies a conservative dual-use
usage-policy classifier that the raw API does not, so benign **biomedical / clinical /
genomics** prompts (PubMed E-utilities, variant calling, clinical-statistics test selection)
are sometimes refused. Those cases are reported as refused, never graded; they make a run
`partial` or `blocked`.

### Harness self-check (`benchmarks/harness-canary/`)

A test-only canary proves the live path end to end: one case passes only if the skill's
bundled reference file reached the skilled arm, the other is designed to fail. Its expected
result is `1 PASS, 1 FAIL`, exit `1`:

```bash
uv run python scripts/run_evals.py --behavioral --skill-dir benchmarks/harness-canary --runs 1
```

The fault paths (all-inconclusive, infrastructure failure, refusal, missing fixture, partial
runs, redaction, isolation, judge selection, identical substantive criteria for both arms) are
covered without a model by `tests/test_behavioral_runner.py`, which drives the real subprocess
path against a fake `claude` executable. `tests/test_regrade_exit.py` covers `--regrade` and
`--calibrate-judge` exit codes (unavailable judge, missing responses, malformed and
non-behavioral files, mixed outcomes, several files), and `tests/test_artifact_checks.py` every
artifact check kind on real small files plus the wiring into the runner.

### Activation harness (`--activation`)

The `description` is the trigger surface, so the metric that matters for a 241-skill suite is
*auto-selection rate*: given a realistic request, does the model pick the **right** skill from
its description when the true skill sits among plausible same-domain distractors? That is both
the activation rate (Anthropic's bar: **90%+**) and, via wrong picks, the **cross-fire rate**.

```bash
uv run python scripts/run_evals.py --activation                 # whole corpus
uv run python scripts/run_evals.py --activation --skill qiskit  # one cluster
uv run python scripts/run_evals.py --activation --distractors 8 # harder discrimination
```

It reuses the `should_trigger` prompts already in every `evals.json` (with `should_not_trigger`
as a cross-fire control) and reports activation rate, cross-fire rate, and a per-category
breakdown. Needs the `claude` CLI, so it runs on demand (a `workflow_dispatch` **activation**
job), not per-PR. Pair it with `scripts/confusion_matrix.py`, which statically ranks the
sibling pairs most at risk of cross-firing (no CLI needed) — sharpen the descriptions of the
top-overlap pairs, then re-run `--activation` to measure the before/after.

`--activation` assumes every skill is installed and picks distractors alphabetically. For a
hand-labelled set with installed-profile candidates, plausible distractors, Turkish requests
and "the right skill is not installed" cases, see [`activation.md`](activation.md)
(`scripts/activation_eval.py`).

### Where behavioral grading runs (manual only)

Behavioral grading is **manual** — there is no scheduled CI run. A full pass makes roughly
12–15 model calls per eval (3 skilled + 3 bare runs, each LLM-judged), so it is run
deliberately, not nightly. Two ways to run it:

- **Locally in Claude Code** (the usual way): the `claude` CLI uses your Claude Code login, so
  no API key is needed. Grade one skill, or split the corpus into deterministic parts:

  ```bash
  uv run python scripts/run_evals.py --behavioral --skill alterlab-docentlik-eligibility
  uv run python scripts/run_evals.py --behavioral --shard 3/7 --runs 1   # cheaper partial pass
  ```

- **In CI** via `workflow_dispatch` (the **behavioral** and **activation** jobs). These need
  the `ANTHROPIC_API_KEY` repo secret and stop at once with an error if it is not set.

## The five-task benchmark (`scripts/run_benchmark.py`)

Eval files say what a skill should do; the benchmark measures whether it does better than the
bare model on realistic, deliberately tricky inputs. Each task in `benchmarks/<task>/task.json`
names an existing skill and holds a standard case, a difficult-negative case (things that look
wrong but are right, and the reverse), and an incomplete-input case (where the right answer is
"cannot be determined"). Every item has an expected label or number and an evidence anchor
(fixture line numbers plus the source that makes it right).

Both arms answer the same prompt in isolated workspaces with the same allowed tools; the
skilled arm also gets the skill. The model must end with a JSON block of per-item labels (each
with a short evidence quote), and the harness scores it deterministically — no LLM judge. Per
arm it reports correct items (**label accuracy**), **false approvals** (a problem passed as
fine), **false accusations** (a fine item flagged), correct and unnecessary abstentions,
overconfident answers on incomplete input, missing items, completion, time, turns,
CLI-reported cost, and tool-permission denials.

Scoring schema 2 (`scoring_schema_version` in the payload and in every task file):

- **Evidence is checked separately from the label.** `quote_in_fixture`: the evidence contains
  a quoted span (at least `min_quote_chars`) that occurs verbatim in a fixture.
  `quote_in_item_region`: such a span occurs in the lines the item's anchor cites, or in the
  item's reference entry. Evidence that passes neither is `needs_review`, not wrong. Neither
  check judges whether the evidence *supports* the label, and neither changes an item's label
  result. `--export-evidence-review PATH` writes every answered item as JSONL for a human or
  model reviewer; `--from-results` rebuilds it from a saved results file without model calls.
- **Duplicate ids:** an item id answered twice with different answers is
  `unresolved_conflict` — never correct, counted separately, and the case is incomplete;
  identical repeats collapse (`duplicate_ids_collapsed`); ids the case does not know are listed
  per arm (`unknown_ids`).
- Schema-1 benchmark results (label-only, first duplicate wins) are not directly comparable.

```bash
uv run python scripts/run_benchmark.py --dry-run          # validate tasks, print prompts
uv run python scripts/run_benchmark.py --runs 2           # all tasks, live
uv run python scripts/run_benchmark.py --task docentlik   # one task
uv run python scripts/run_benchmark.py --runs 2 --export-evidence-review review.jsonl
```

Exit codes: `0` measured (every arm of every case returned a parseable answer), `3` partial,
`2` blocked, `64` an invalid task file or an unreadable / pre-schema-2 `--from-results` file.

Results go to `eval-results/benchmark-<UTC>.json`; the latest reported run is summarised in
[`benchmark-results.md`](benchmark-results.md). `tests/test_benchmark.py` validates every task
file and unit-tests the scorer on hand-written answers; it never produces benchmark numbers.

To summarise many behavioral and regrade records (selection rules, v1/v2 separation, every
rate with its numerator and denominator), see [`eval-aggregation.md`](eval-aggregation.md).

## Worked example

A complete, schema-valid eval file for a representative skill. It shows the full convention:
distinct trigger modes, a near-miss that defers to an adjacent skill, and the optional
`output_contains` / `behavior` assertions used to pin down responses.

```json
{
  "skill": "alterlab-deep-research",
  "evals": [
    {
      "id": "full-research",
      "prompt": "Research the impact of generative AI tutoring tools on undergraduate writing quality in higher education, and give me a full cited report.",
      "expected_output": "Invokes alterlab-deep-research in full mode: runs the 6-phase pipeline (FINER-scored research question and methodology blueprint, systematic literature search with source verification, cross-source synthesis with devil's-advocate checkpoints, editorial and ethics review), and compiles a full APA 7.0 report with citations, limitations, and an AI-disclosure statement.",
      "assertions": [
        { "type": "should_trigger", "value": true },
        { "type": "behavior", "value": "Produces a FINER-scored research question before searching, and ends with a limitations section plus an AI-disclosure statement." }
      ]
    },
    {
      "id": "socratic-guided",
      "prompt": "I'm interested in how declining birth rates affect private universities but I'm not sure what my actual research question should be. Can you guide my thinking?",
      "expected_output": "Invokes alterlab-deep-research in socratic mode: the socratic_mentor_agent guides the user through layered questioning (problem framing, methodology reflection, evidence design) without giving direct answers, converging toward a refined research question rather than producing a finished report.",
      "assertions": [
        { "type": "should_trigger", "value": true },
        { "type": "behavior", "value": "Asks guiding questions and does NOT hand over a finished research report." }
      ]
    },
    {
      "id": "systematic-review-meta",
      "prompt": "I need a PRISMA-compliant systematic review with a meta-analysis on the effectiveness of flipped-classroom interventions on student exam performance.",
      "expected_output": "Invokes alterlab-deep-research in systematic-review mode: PICOS question, PRISMA-P protocol, a PRISMA 2020 flow diagram, risk-of-bias assessment (RoB 2 / ROBINS-I), meta-analysis (effect sizes, heterogeneity, GRADE) or narrative synthesis, and a full PRISMA report.",
      "assertions": [
        { "type": "should_trigger", "value": true },
        { "type": "output_contains", "value": "PRISMA" }
      ]
    },
    {
      "id": "fact-check-claims",
      "prompt": "Can you fact-check these three claims about international student enrollment trends before I cite them in a policy memo?",
      "expected_output": "Invokes alterlab-deep-research in fact-check mode: the source_verification_agent verifies each claim against at least 3 sources per claim, grades evidence quality, screens for predatory sources, and returns a per-claim verification report with verdicts.",
      "assertions": [
        { "type": "should_trigger", "value": true }
      ]
    },
    {
      "id": "near-miss-paper-writer",
      "prompt": "I already have my research synthesis and bibliography ready. Now write me the full journal paper in IMRaD with a bilingual abstract and LaTeX output.",
      "expected_output": "Does NOT invoke this skill; defers to alterlab-paper-writer. The user wants a publishable paper draft with multi-format and bilingual output, not original research or evidence synthesis.",
      "assertions": [
        { "type": "should_not_trigger", "value": true },
        { "type": "output_contains", "value": "alterlab-paper-writer" }
      ]
    },
    {
      "id": "near-miss-paper-reviewer",
      "prompt": "Here is a colleague's finished manuscript. Give me a structured peer review with section-by-section comments and an accept/revise/reject verdict.",
      "expected_output": "Does NOT invoke this skill; defers to alterlab-paper-reviewer. The user wants a structured review of an existing paper, not original research or evidence synthesis.",
      "assertions": [
        { "type": "should_not_trigger", "value": true },
        { "type": "output_contains", "value": "alterlab-paper-reviewer" }
      ]
    }
  ]
}
```

## Canonical schema (inline)

The authoritative copy is [`docs/evals.schema.json`](./evals.schema.json). Reproduced here so
the contract is readable in one place:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/AlterLab-IEU/AlterLab-Academic-Skills/docs/evals.schema.json",
  "title": "AlterLab Skill Eval File",
  "description": "Canonical schema for per-skill eval files at skills/<domain>/<skill>/evals/evals.json. One file per skill. Each eval is a realistic researcher ask plus the behavior we expect, encoded as machine-checkable assertions. Validated per-PR by scripts/run_evals.py --strict; behavioral grading (run_evals.py --behavioral) shells to the claude CLI and LLM-judges expected_output.",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "skill",
    "evals"
  ],
  "properties": {
    "skill": {
      "type": "string",
      "description": "The skill name this eval file targets. MUST match the skill's frontmatter `name` and its directory name (e.g. alterlab-deep-research).",
      "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$",
      "minLength": 1
    },
    "evals": {
      "type": "array",
      "description": "All eval cases for this skill. Convention: >=3 should_trigger cases and >=1 near-miss should_not_trigger case (an adjacent skill's territory).",
      "minItems": 1,
      "items": {
        "$ref": "#/$defs/eval"
      }
    }
  },
  "$defs": {
    "eval": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "id",
        "prompt",
        "expected_output"
      ],
      "properties": {
        "id": {
          "type": "string",
          "description": "Stable, unique-within-file identifier in kebab-case (e.g. full-research, near-miss-paper-writer).",
          "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$",
          "minLength": 1
        },
        "prompt": {
          "type": "string",
          "description": "The realistic researcher ask sent to the model, verbatim. Phrase it the way a faculty member or grad student would actually type it.",
          "minLength": 1
        },
        "expected_output": {
          "type": "string",
          "description": "Prose description of the correct behavior/output. Used as the rubric for the behavioral LLM judge. For near-miss negatives, describe the deferral (which adjacent skill should handle it and why this one should not).",
          "minLength": 1
        },
        "files": {
          "type": "array",
          "description": "Optional input fixtures the eval supplies to the model (paths relative to the skill's evals/ dir, or inline content). Use when the ask requires an attached manuscript, dataset, bibliography, etc.",
          "items": {
            "oneOf": [
              {
                "type": "string",
                "description": "Path to a fixture file, relative to the eval file's directory."
              },
              {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "name",
                  "content"
                ],
                "properties": {
                  "name": {
                    "type": "string",
                    "minLength": 1
                  },
                  "content": {
                    "type": "string"
                  }
                }
              }
            ]
          }
        },
        "requires": {
          "type": "array",
          "description": "Optional preconditions the case cannot be judged without: env:NAME (an environment variable, e.g. an API key), cmd:NAME (an executable on PATH, e.g. Rscript), net:HOST (a host reachable from the runner), mcp:NAME (an MCP server; never available under the harness's --strict-mcp-config). An unmet requirement makes the case NOT_RUN ('not runnable here'), never FAIL.",
          "items": {
            "type": "string",
            "pattern": "^(env|cmd|net|mcp):[A-Za-z0-9_.:-]+$"
          }
        },
        "assertions": {
          "type": "array",
          "description": "Machine-checkable expectations. At minimum every eval carries one should_trigger / should_not_trigger assertion declaring whether this skill should fire on the prompt.",
          "items": {
            "$ref": "#/$defs/assertion"
          }
        },
        "artifact_checks": {
          "type": "array",
          "description": "Optional files the answer must produce, checked deterministically (scripts/artifact_checks.py) after each run and before the arm's temporary workspace is deleted. Both arms are told each file's path, type and description (never the checks); the eval file itself is never copied into a workspace. A missing, unreadable or unparseable file fails every check declared for it. Expected values are supplied here by the eval author, never computed from the model's output.",
          "items": {
            "$ref": "#/$defs/artifact"
          }
        }
      }
    },
    "assertion": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "type",
        "value"
      ],
      "properties": {
        "type": {
          "type": "string",
          "description": "should_trigger / should_not_trigger gate skill activation (value is boolean true). output_contains checks the response includes a substring/phrase (value is the string, case-insensitive by convention). behavior is a free-text rubric clause the LLM judge grades (value is the prose criterion).",
          "enum": [
            "should_trigger",
            "should_not_trigger",
            "output_contains",
            "behavior"
          ]
        },
        "value": {
          "description": "Boolean true for should_trigger/should_not_trigger; for output_contains, the required substring or a list of alternatives (any one must occur, e.g. the Turkish and English form of a legal citation); a string for behavior (the rubric clause).",
          "type": [
            "string",
            "boolean",
            "array"
          ]
        }
      },
      "allOf": [
        {
          "if": {
            "properties": {
              "type": {
                "enum": [
                  "should_trigger",
                  "should_not_trigger"
                ]
              }
            }
          },
          "then": {
            "properties": {
              "value": {
                "const": true
              }
            }
          }
        },
        {
          "if": {
            "properties": {
              "type": {
                "const": "behavior"
              }
            }
          },
          "then": {
            "properties": {
              "value": {
                "type": "string",
                "minLength": 1
              }
            }
          }
        },
        {
          "if": {
            "properties": {
              "type": {
                "const": "output_contains"
              }
            }
          },
          "then": {
            "properties": {
              "value": {
                "oneOf": [
                  {
                    "type": "string",
                    "minLength": 1
                  },
                  {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                      "type": "string",
                      "minLength": 1
                    }
                  }
                ]
              }
            }
          }
        }
      ]
    },
    "artifact": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "path",
        "type"
      ],
      "properties": {
        "path": {
          "type": "string",
          "minLength": 1,
          "pattern": "^(?!/)(?!.*(^|/)\\.\\.(/|$))[^\\\\]+$",
          "description": "Path relative to the arm's working directory (no leading '/', no '..'), e.g. out/report.json."
        },
        "type": {
          "type": "string",
          "enum": [
            "json",
            "csv",
            "png",
            "pdf",
            "pptx",
            "md",
            "txt",
            "bib"
          ]
        },
        "description": {
          "type": "string",
          "minLength": 1,
          "description": "What the file should contain, as the user would specify it; shown to both arms."
        },
        "checks": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/artifact_check"
          },
          "description": "Checks beyond the implicit exists + parseable. Which kinds suit which type, and the csv row selector rules, are enforced by run_evals.py."
        }
      }
    },
    "artifact_check": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "kind"
      ],
      "properties": {
        "kind": {
          "type": "string",
          "enum": [
            "exists",
            "parseable",
            "json_keys",
            "json_path_equals",
            "csv_columns",
            "min_rows",
            "number_within",
            "contains_text",
            "png_min_size",
            "png_dpi",
            "pdf_min_pages",
            "pptx_min_slides"
          ]
        },
        "keys": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string",
            "minLength": 1
          }
        },
        "columns": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string",
            "minLength": 1
          }
        },
        "path": {
          "type": "string",
          "minLength": 1,
          "description": "Dotted JSON path; integer segments index arrays (entries.0.verdict)."
        },
        "value": {
          "description": "json_path_equals: the exact expected JSON value."
        },
        "min": {
          "type": "integer",
          "minimum": 0
        },
        "max": {
          "type": "integer",
          "minimum": 0
        },
        "expected": {
          "type": "number"
        },
        "tolerance": {
          "type": "number",
          "minimum": 0
        },
        "column": {
          "type": "string",
          "minLength": 1
        },
        "row": {
          "type": "integer",
          "minimum": 0,
          "description": "number_within on csv: 0-based data-row index."
        },
        "match": {
          "type": "object",
          "minProperties": 1,
          "additionalProperties": {
            "type": "string"
          },
          "description": "number_within on csv: pick the first row whose named columns equal these values."
        },
        "text": {
          "oneOf": [
            {
              "type": "string",
              "minLength": 1
            },
            {
              "type": "array",
              "minItems": 1,
              "items": {
                "type": "string",
                "minLength": 1
              }
            }
          ]
        },
        "min_width": {
          "type": "integer",
          "minimum": 0
        },
        "min_height": {
          "type": "integer",
          "minimum": 0
        }
      }
    }
  }
}
```
