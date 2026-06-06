# Model Environment Convention — `ALTERLAB_MODEL`

## Purpose

A single, dated, override-able convention for **which Claude model ID** every AlterLab
script and agent uses. This kills two recurring problems:

1. **Hardcoded model IDs rot.** The v1 corpus shipped ~20 hardcoded `claude-opus-4.5` /
   `gemini-3-pro-preview` strings scattered across helper scripts. When a model is renamed
   or retired, each one is a silent breakage and a separate edit.
2. **No single source of truth.** The behavioral eval judge (`run_evals.py --behavioral`),
   any script that shells to the `claude` CLI, and any agent that names a model all need to
   agree on one ID — and on one place to change it.

The rule: **never hardcode a bare model ID in a script.** Read `ALTERLAB_MODEL` from the
environment, falling back to a **dated default constant** that lives in exactly one place
per language.

## The convention

- **Env var:** `ALTERLAB_MODEL`
- **Default (as of 2026-06-06):** `claude-opus-4-8`
- **Override:** export `ALTERLAB_MODEL` in the shell, CI job, or `.envrc`; the default is
  only used when the env var is unset or empty.

The default carries a **date stamp in a comment next to it** so the "last reviewed" date is
visible at the point of use. When Anthropic ships a newer model, you change the default
constant in the few canonical spots below (and bump the date) — every consumer picks it up.

> Model IDs are dated facts, not folklore. Before changing the default, confirm the exact
> current ID against the `claude-api` skill / Anthropic docs — do not guess from memory.

## Reference implementation

### Python (the canonical `run_evals.py` behavioral judge + any helper script)

```python
import os

# AlterLab model convention — default reviewed 2026-06-06; override via ALTERLAB_MODEL.
# See skills/core/shared/model_env.md before changing the default.
DEFAULT_MODEL = "claude-opus-4-8"


def alterlab_model() -> str:
    """Return the model ID to use: $ALTERLAB_MODEL if set/non-empty, else the dated default."""
    return os.environ.get("ALTERLAB_MODEL") or DEFAULT_MODEL
```

Usage (e.g. shelling to the `claude` CLI for behavioral grading):

```python
import subprocess

subprocess.run(["claude", "--model", alterlab_model(), "-p", prompt], check=True)
```

### Bash (scripts that call the `claude` CLI directly)

```bash
# AlterLab model convention — default reviewed 2026-06-06; override via ALTERLAB_MODEL.
: "${ALTERLAB_MODEL:=claude-opus-4-8}"

claude --model "$ALTERLAB_MODEL" -p "$PROMPT"
```

### Agent prose (`.md` agent definitions that must name a model)

Agent definitions should refer to **"the model configured via `ALTERLAB_MODEL`
(default `claude-opus-4-8` as of 2026-06-06)"** rather than embedding a bare ID in
instructions. This keeps agent text from going stale and points the reader to this file.

## Who references this

- **`scripts/run_evals.py --behavioral`** — the LLM judge that grades `expected_output`
  shells to the `claude` CLI with `alterlab_model()`. See `docs/evals.md`.
- **ws-5 model-ID fixes** — the sweep that replaces the ~20 hardcoded
  `claude-opus-4.5` / `gemini-3-pro-preview` IDs replaces each with this convention
  (`alterlab_model()` in Python, `${ALTERLAB_MODEL:=…}` in Bash), so there is exactly one
  dated default per language to maintain.
- **Any new helper script or agent** that needs a model ID — use this convention from day
  one; do not introduce a new bare literal.

## Rules

1. **No bare model literals in executable code.** A grep for `claude-opus-`, `claude-sonnet-`,
   `claude-haiku-`, `gemini-`, `gpt-` in `scripts/` and skill `*.py` should only hit the
   single `DEFAULT_MODEL` constant (and this doc), never an inline call argument.
2. **Empty is unset.** Treat `ALTERLAB_MODEL=""` the same as unset (`os.environ.get(...) or
   DEFAULT_MODEL`, `${VAR:=default}`), so a blank CI variable does not break runs.
3. **Date the default.** Every place the default constant is defined carries a
   `reviewed YYYY-MM-DD` comment; bump it when you change the ID.
4. **One ID, one place per language.** Do not redefine `DEFAULT_MODEL` per script; import or
   copy the canonical snippet above so a model bump is a one-line change per language.
