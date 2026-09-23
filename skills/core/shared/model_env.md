# Model Environment Convention — `ALTERLAB_MODEL`

## Purpose

A single, dated, override-able convention for **which Claude model ID** every AlterLab
script and agent uses. It exists because:

1. **Hardcoded model IDs rot.** The v1 corpus shipped ~20 hardcoded model strings scattered
   across helper scripts. When a model is renamed or retired, each one is a silent breakage
   and a separate edit.
2. **There was no single source of truth.** The behavioral eval judge (`run_evals.py
   --behavioral`), any script that shells to the `claude` CLI, any script that reaches Claude
   through OpenRouter, and any agent that names a model all need to agree on one ID — and on
   one place to change it.

The rule: **never hardcode a bare model ID in a script.** Read `ALTERLAB_MODEL` from the
environment, falling back to a **dated default constant** that lives in exactly one place
per language.

## The convention

- **Env var:** `ALTERLAB_MODEL` — always an **Anthropic model ID** (e.g. `claude-opus-5-5`),
  never a gateway slug. Gateway-specific forms are derived from it (see OpenRouter below).
- **Default (reviewed 2026-09-23):** `claude-opus-5-5` — Claude Opus 5.5.
- **Override:** export `ALTERLAB_MODEL` in the shell, CI job, or `.envrc`; the default is
  only used when the env var is unset or empty. `claude-fable-5-1` (most capable, pricier),
  `claude-opus-5`, `claude-sonnet-5`, and `claude-haiku-4-5` are all valid overrides.

The default carries a **date stamp in a comment next to it** so the "last reviewed" date is
visible at the point of use. When Anthropic ships a newer model, you change the default
constant in the few canonical spots below (and bump the date) — every consumer picks it up.

> Model IDs are dated facts, not folklore. Before changing the default, confirm the exact
> current ID against the `claude-api` skill / Anthropic docs — do not guess from memory, and
> never append a date suffix to an ID that doesn't carry one.

## Reference implementation

### Python (the canonical `run_evals.py` behavioral judge + any helper script)

```python
import os

# AlterLab model convention — default reviewed 2026-09-23; override via ALTERLAB_MODEL.
# See skills/core/shared/model_env.md before changing the default.
DEFAULT_MODEL = "claude-opus-5-5"


def alterlab_model() -> str:
    """Return the model ID to use: $ALTERLAB_MODEL if set/non-empty, else the dated default."""
    return os.environ.get("ALTERLAB_MODEL") or DEFAULT_MODEL
```

Usage (e.g. shelling to the `claude` CLI for behavioral grading):

```python
import subprocess

subprocess.run(["claude", "--model", alterlab_model(), "-p", prompt], check=True)
```

### OpenRouter / OpenAI-compatible gateways

OpenRouter names Claude models with a provider prefix and a **dotted** version
(`anthropic/claude-opus-5.5`, `anthropic/claude-haiku-4.5`) — the Anthropic ID
`claude-opus-5-5` is not a valid OpenRouter slug. Scripts that talk to a gateway keep the
same Anthropic-ID default and translate at call time, so one `ALTERLAB_MODEL` value works
for every script:

```python
import re


def openrouter_slug(model: str) -> str:
    """Map an Anthropic model ID to its OpenRouter slug; pass anything else through.

    claude-opus-5-5 -> anthropic/claude-opus-5.5, claude-sonnet-5 -> anthropic/claude-sonnet-5,
    claude-sonnet-4-5-20250929 -> anthropic/claude-sonnet-4.5. Slugs that already carry a
    provider prefix ("anthropic/...", "google/...") are returned unchanged.
    """
    if "/" in model:
        return model
    m = re.fullmatch(r"claude-([a-z]+)-(\d+)(?:-(\d{1,2}))?(?:-\d{8})?", model)
    if not m:
        return model
    family, major, minor = m.groups()
    return f"anthropic/claude-{family}-{major}" + (f".{minor}" if minor else "")
```

Verify a slug exists with `curl -s https://openrouter.ai/api/v1/models` (public, no key).

### Bash (scripts that call the `claude` CLI directly)

```bash
# AlterLab model convention — default reviewed 2026-09-23; override via ALTERLAB_MODEL.
: "${ALTERLAB_MODEL:=claude-opus-5-5}"

claude --model "$ALTERLAB_MODEL" -p "$PROMPT"
```

### Agent prose (`.md` agent definitions that must name a model)

Agent definitions should refer to **"the model configured via `ALTERLAB_MODEL`
(default `claude-opus-5-5` as of 2026-09-23)"** rather than embedding a bare ID in
instructions. Claude Code subagent files may also leave `model` unset (they inherit the
session model), which is usually what you want.

## Calling Claude directly — what the current models require

Scripts that build Anthropic API requests themselves (rather than shelling to the `claude`
CLI) must use the request shape the default model accepts. For Claude Opus 5.5 (and
Fable 5.1), per Anthropic's migration guide:

| Old pattern | Current requirement |
|-------------|---------------------|
| `thinking: {type: "disabled"}` or `{type: "enabled", budget_tokens: N}` | Both return 400 — thinking is always on. Omit `thinking` (or send `{type: "adaptive"}`) and control depth with `output_config: {effort: ...}`. |
| Relying on the default effort | Opus 5.5 defaults to `medium` (one level below Opus 5's `high`). Set `effort` explicitly; `low` for extraction/classification, `high`+ for hard reasoning. |
| `temperature` / `top_p` / `top_k` | Rejected (400) from Opus 4.7 onward. Remove them; determinism comes from the prompt and structured outputs. |
| Assistant-turn prefill (e.g. a trailing `{"role": "assistant", "content": "{"}`) | Rejected. Use structured outputs (`output_config.format`) for JSON. |
| `tool_choice: {type: "any"}` / `{type: "tool", ...}` | Rejected on Opus 5.5. Use `tool_choice: auto` + `strict: true` on the tool, name the tool in the prompt, and check that a call happened. |
| Reading `response.content[0].text` | Responses can start with `thinking` blocks — select blocks by `type`. |
| `max_tokens` sized for a no-thinking reply | Thinking counts toward `max_tokens`; leave room (e.g. 16K non-streaming, 64K streaming). |
| Ignoring `stop_reason` | Check for `stop_reason == "refusal"` (categories include `cyber`, `bio`, `reasoning_extraction`) before reading content. |

Prompts written for older models also deserve a look: instructions that ask the model to
"think step by step" or to write its reasoning into the answer are redundant with adaptive
thinking, and asking it to reproduce its internal reasoning can be declined
(`reasoning_extraction`).

## Who references this

- **`scripts/run_evals.py --behavioral`** — the LLM judge that grades `expected_output`
  shells to the `claude` CLI with `alterlab_model()`. See `docs/evals.md`.
- **`skills/core/alterlab-citation-verifier/scripts/claim_faithfulness.py`** — the optional
  LLM-judge tier shells to `claude --model "$(alterlab_model)"`.
- **`skills/research-tools/alterlab-pdf-extract/scripts/extract_to_table.py`** and
  **`skills/document-tools/alterlab-markitdown/scripts/convert_with_ai.py`** — reach Claude
  through OpenRouter with `openrouter_slug(alterlab_model())`.
- **Any new helper script or agent** that needs a model ID — use this convention from day
  one; do not introduce a new bare literal.

## Rules

1. **No bare model literals in executable code.** A grep for `claude-opus-`, `claude-sonnet-`,
   `claude-haiku-`, `claude-fable-` in `scripts/` and skill `*.py` should only hit the
   single `DEFAULT_MODEL` constant (and this doc), never an inline call argument. Non-Claude
   models used by third-party tools (e.g. image models) get their own `ALTERLAB_*_MODEL`
   variables with a dated default.
2. **Empty is unset.** Treat `ALTERLAB_MODEL=""` the same as unset (`os.environ.get(...) or
   DEFAULT_MODEL`, `${VAR:=default}`), so a blank CI variable does not break runs.
3. **Date the default.** Every place the default constant is defined carries a
   `reviewed YYYY-MM-DD` comment; bump it when you change the ID.
4. **One ID, one place per language.** Do not redefine `DEFAULT_MODEL` per script with a
   different value; copy the canonical snippet above so a model bump is a one-line change per
   language. Gateway slugs are derived with `openrouter_slug()`, never stored.
