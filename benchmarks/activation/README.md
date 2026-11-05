# Activation case set

Hand-written cases for `scripts/activation_eval.py`, which measures whether a model picks the
right **installed** skill for a request from skill descriptions alone. What the harness does
and does not measure is in [docs/activation.md](../../docs/activation.md).

This directory deliberately has no `task.json`: `scripts/run_benchmark.py` treats every
`benchmarks/*/task.json` as a behavioral benchmark task, and this is not one.

## `cases.json`

```jsonc
{
  "version": 1,
  "default_seed": 20261105,          // shuffle/sample seed unless --seed is given
  "profiles": {                      // installed profiles: plugin names only
    "essentials": {"plugins": ["alterlab-essentials"], "note": "..."}
  },
  "cases": [{
    "id": "distractor-citation-verifier",       // kebab-case, unique
    "prompt": "...",                            // the user's request, verbatim
    "language": "en",                           // "en" | "tr"
    "kind": "distractor",                       // clear | ambiguous | distractor | unavailable
    "installed_profile": "essentials",
    "expected": "alterlab-citation-verifier",   // a skill name, or "none"
    "acceptable": ["alterlab-research-workflows"],  // other answers that also count
    "distractors": ["alterlab-citation-mgmt"],  // hand-picked plausible confusers
    "note": "why the label is what it is"
  }]
}
```

A profile lists plugins, never skills. The harness reads `.claude-plugin/marketplace.json`,
each plugin's `.claude-plugin/plugin.json` and the `plugins/` bundles, follows their
`dependencies`, and computes the installed skill list. The listed bundle plugins, such as
`alterlab-essentials`, therefore install exactly what a real install of them would.

Kinds:

- **clear**: one skill (or `none`) is plainly right.
- **ambiguous**: several answers are defensible. `expected` is the best one and `acceptable`
  must list at least one alternate.
- **distractor**: the case is built around the named `distractors`, which must be installed
  in the profile.
- **unavailable**: `expected` names the skill that would be right, and it must **not** be
  installed in the profile. The correct pick is `none`; a skill in `acceptable` (which must
  be installed) is a named fallback.

The loader rejects the file (exit 64) if any of these hold: a label names an unknown skill;
an expected skill is not installed in a non-unavailable case; the expected skill of an
unavailable case is installed; an acceptable alternate or distractor is not installed; an
ambiguous case has no alternate; a distractor case has no distractor.

## Adding or changing a case

1. Write the prompt the way a faculty member would type it (Turkish cases in Turkish).
2. Choose the profile in which the question is interesting, and check the candidates with
   `uv run python scripts/activation_eval.py --dry-run --case <id>`.
3. Explain the label in `note`. Labels are one author's judgement and should be reviewed by a
   maintainer before they are used to compare descriptions.
4. Run `uv run pytest tests/test_activation_eval.py -q`.

Do not delete a case, or change its label, because a model gets it wrong. Change a label only
when the label itself is wrong, and say why in the commit.
