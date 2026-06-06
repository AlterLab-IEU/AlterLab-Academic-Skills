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

# Behavioral grading (slow; needs the claude CLI). Uses the model from ALTERLAB_MODEL —
# see skills/core/shared/model_env.md.
uv run python scripts/run_evals.py --behavioral
```

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
