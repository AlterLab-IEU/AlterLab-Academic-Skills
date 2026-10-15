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

### Assertion types

| `type` | `value` | Meaning |
|--------|---------|---------|
| `should_trigger` | `true` | This skill **should** activate on the prompt. |
| `should_not_trigger` | `true` | This skill should **not** activate (near-miss / another skill's job). |
| `output_contains` | string | The response must contain this substring/phrase (case-insensitive by convention). |
| `behavior` | string | A free-text rubric clause the behavioral LLM judge grades. |

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
   assert it with `output_contains` (e.g. `"defers to alterlab-paper-writer"`). Avoid
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
```

### Three separate things this harness measures

| Mode | What it shows | What it does **not** show |
|------|---------------|---------------------------|
| default / `--strict` (static) | every skill ships a schema-valid `evals.json` with ≥3 trigger and ≥1 near-miss cases | that any skill behaves correctly — no model is called |
| `--behavioral` (live) | per case, whether the skilled answer met its assertions and LLM-judged rubric, and how the bare model did on the same rubric | research correctness beyond what the rubric checks; the judge is the same model family |
| `--activation` (live) | whether the model picks the right skill from its description among same-domain distractors | that the picked skill then does the task well |

Keep the three apart when reporting: "242 skills have evals" is a statement about the static
check only.

### Isolation

Each behavioral case runs both arms from fresh temporary directories, never from this
repository, with `--safe-mode --disable-slash-commands --strict-mcp-config
--no-session-persistence`: no CLAUDE.md, installed plugins, skills, hooks, or MCP servers. The
**skilled arm** gets the SKILL.md through `--append-system-prompt`, the skill's own files in
`./skill/` (its `evals/` folder is never copied, so expected outputs stay hidden), the domain's
`shared/` resources in `./shared/`, and the task fixtures in `./fixtures/`. The **bare arm**
gets only `./fixtures/`. The judges run in their own empty directories. Both arms' answer calls are granted the
skill's `allowed-tools` frontmatter (`--allowedTools`), the set Claude Code pre-approves when
the skill is active; the bare arm gets the same set so the comparison isolates the skill's
instructions, and the judges get no tools. Without this, a skill that must run its script or
query a live service fails by construction and a correct refusal to answer from memory is
scored FAIL. Auth is the CLI's normal
login, so the harness runs inside an authenticated Claude Code environment with no API key.
(`--bare` would be stricter, but it ignores OAuth logins and requires `ANTHROPIC_API_KEY`.)

### Reading a `--behavioral` run

Every case ends in exactly one outcome, printed with its reason:

| Outcome | Meaning |
|---------|---------|
| `PASS` / `FAIL` | the usable verdicts: assertions and rubric majority agree on PASS, or any FAIL |
| `INCONCLUSIVE` | the model answered, but the judges settled no verdict (tie, or an unparseable judge reply — which is never scored as a silent FAIL) |
| `REFUSED` | the runner environment's usage-policy classifier refused the prompt |
| `INFRA_ERROR` | the CLI failed, timed out, could not authenticate, a judge call failed, or a fixture file was missing (the case is never run without its input) |
| `NOT_RUN` | the run aborted after `--max-infra-errors` (default 6) consecutive infrastructure errors |

The summary reports **selected, attempted, answered, and usable verdicts**, the coverage
(usable ÷ selected), both arms' outcome counts, the rubric delta, CLI calls, wall-clock time,
and the cost the CLI reports. Exit codes:

| Exit | Status | Meaning |
|------|--------|---------|
| `0` | `passed` | **every** selected case produced a verdict and passed |
| `1` | `failed` | at least one case failed |
| `2` | `blocked` | no case produced a usable verdict (no CLI, no login, every call refused or timed out, or the filter matched nothing). The run verified nothing |
| `3` | `partial` | some cases produced verdicts and none failed, but others did not — the selection is **not** fully evaluated |

### Two rubric judges, and checking them

Many rubrics name the skill's own vocabulary ("invokes alterlab-…", "applies the Iron Law").
The default **literal** judge grades the rubric as written, so a correct answer that never uses
those words can FAIL. The **substance** judge (`--judge substance`) grades what the response
does: the decision, the numbers, the refusal or the request for missing input, the named
sibling skill when the rubric asks for a hand-off. It ignores whether the skill's vocabulary
appears. It still fails a wrong answer that recites the vocabulary.

Before trusting either judge, run it on the hand-labelled pairs in
[`judge_calibration.json`](judge_calibration.json). This costs judge calls only and exits `1`
if any label is missed:

```bash
uv run python scripts/run_evals.py --calibrate-judge
```

On 2026-10-15 (`claude-opus-5-5`): literal 7/8, substance 8/8. The literal judge failed a
correct answer that asked for the missing abstract instead of inventing one.

Every run record keeps the full response text, so a finished run can be re-judged without new
answer calls. `--regrade` writes `regrade-*.json` with every flipped verdict and the original
verdict next to it:

```bash
uv run python scripts/run_evals.py --regrade eval-results/behavioral-<UTC>.json --judge substance
```

Report which judge produced a number.

Only exit `0` may be described as "the selected cases pass", and only for the selected cases.
A sharded or filtered run validates its shard, not the suite.

Every run writes a JSON results file to `eval-results/` (git-ignored; `--results-dir` to change,
`--results-dir ''` to skip) with the model id, `claude` CLI version, repo commit and dirty flag,
isolation flags, and per case: the case ID, skill version, fixtures, each run's outcome, error
(redacted — token-shaped strings are stripped), assertion and rubric verdicts, response
excerpt, duration, reported cost, and the bare arm's results. Failure diagnostics name the
likely cause (authentication, rate limit, timeout, missing CLI) without echoing credentials.

**`REFUSED`** cases: the `claude` *Claude Code CLI* applies a conservative dual-use
usage-policy classifier that the raw API does not, so benign **biomedical / clinical /
genomics** prompts (PubMed E-utilities, variant calling, clinical-statistics test selection)
are sometimes refused. Those cases are reported as refused, never graded; they make a run
`partial` or `blocked`.

The per-eval **`rubric:` delta** (`SKILL HELPED` / `HURT` / `NO DELTA`) compares the two
arms on the *overall rubric only* — the bare arm carries no `should_trigger` assertions — so
it is labelled `rubric:` and never contradicts an assertion-driven `FAIL` verdict.

### Harness self-check (`benchmarks/harness-canary/`)

A test-only canary proves the live path end to end: one case passes only if the skill's
bundled reference file reached the skilled arm, the other is designed to fail. Its expected
result is `1 PASS, 1 FAIL`, exit `1`:

```bash
uv run python scripts/run_evals.py --behavioral --skill-dir benchmarks/harness-canary --runs 1
```

The fault paths (all-inconclusive, infrastructure failure, refusal, missing fixture, partial
runs, redaction, isolation) are covered without a model by `tests/test_behavioral_runner.py`,
which drives the real subprocess path against a fake `claude` executable.

### Activation harness (`--activation`)

The `description` is the trigger surface, so the metric that matters for a 242-skill suite is
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
skilled arm also gets the skill. The model must end with a JSON block of per-item labels, and
the harness scores it deterministically — no LLM judge. Per arm it reports correct items,
**false approvals** (a problem passed as fine), **false accusations** (a fine item flagged),
correct and unnecessary abstentions, overconfident answers on incomplete input, missing items,
completion, time, turns, CLI-reported cost, and tool-permission denials.

```bash
uv run python scripts/run_benchmark.py --dry-run          # validate tasks, print prompts
uv run python scripts/run_benchmark.py --runs 2           # all tasks, live
uv run python scripts/run_benchmark.py --task docentlik   # one task
```

Results go to `eval-results/benchmark-<UTC>.json`; the latest reported run is summarised in
[`benchmark-results.md`](benchmark-results.md). `tests/test_benchmark.py` validates every task
file and unit-tests the scorer on hand-written answers; it never produces benchmark numbers.

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
  "type": "object",
  "additionalProperties": false,
  "required": ["skill", "evals"],
  "properties": {
    "skill": {
      "type": "string",
      "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$",
      "minLength": 1
    },
    "evals": {
      "type": "array",
      "minItems": 1,
      "items": { "$ref": "#/$defs/eval" }
    }
  },
  "$defs": {
    "eval": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "prompt", "expected_output"],
      "properties": {
        "id": { "type": "string", "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$", "minLength": 1 },
        "prompt": { "type": "string", "minLength": 1 },
        "expected_output": { "type": "string", "minLength": 1 },
        "files": {
          "type": "array",
          "items": {
            "oneOf": [
              { "type": "string" },
              {
                "type": "object",
                "additionalProperties": false,
                "required": ["name", "content"],
                "properties": {
                  "name": { "type": "string", "minLength": 1 },
                  "content": { "type": "string" }
                }
              }
            ]
          }
        },
        "assertions": {
          "type": "array",
          "items": { "$ref": "#/$defs/assertion" }
        }
      }
    },
    "assertion": {
      "type": "object",
      "additionalProperties": false,
      "required": ["type", "value"],
      "properties": {
        "type": {
          "type": "string",
          "enum": ["should_trigger", "should_not_trigger", "output_contains", "behavior"]
        },
        "value": { "type": ["string", "boolean"] }
      },
      "allOf": [
        {
          "if": { "properties": { "type": { "enum": ["should_trigger", "should_not_trigger"] } } },
          "then": { "properties": { "value": { "const": true } } }
        },
        {
          "if": { "properties": { "type": { "enum": ["output_contains", "behavior"] } } },
          "then": { "properties": { "value": { "type": "string", "minLength": 1 } } }
        }
      ]
    }
  }
}
```
