"""Every skill ships a schema-valid eval file meeting the coverage convention.

This is the pytest face of ``scripts/run_evals.py``'s default (validation) mode: one
parametrized test per skill directory asserting that ``evals/evals.json`` exists, validates
against ``docs/evals.schema.json``, and meets the coverage bar (>=3 ``should_trigger`` cases
+ >=1 ``should_not_trigger`` near-miss). Failures name the failing skill and the exact
problem, so they read cleanly in CI / PR comments.

Reusing ``run_evals`` keeps a single source of truth: schema rules, the convention, and the
jsonschema-optional fallback all live in the script, and this test just drives it over the
live filesystem.

## known_failures ratchet (drains itself)

The eval files are being authored in parallel **today** (ws-* backfill), so a handful of
skills legitimately lack a valid eval file at this instant. Hard-failing those would block
unrelated PRs, so ``EVAL_KNOWN_FAILURES`` is a frozen snapshot of the skills pending as of
2026-06-06. Semantics:

* A skill **not** in the ratchet that is invalid → **hard failure** (a regression, or a new
  skill that must meet the bar on day one).
* A skill **in** the ratchet that is still invalid → **xfail** (known content debt; CI stays
  green but the debt is visible).
* A skill **in** the ratchet that now validates → simply **passes**. We use a *non-strict*
  xfail, so a now-valid ratcheted skill does not turn into an XPASS error.

Because the test reads the live filesystem, the ratchet **drains naturally**: as each
backfill PR lands a valid eval file, that skill stops being xfailed and starts passing — with
no edit to this list required. The list only needs touching to *remove* entries once they are
permanently authored.

> **ws-14 empties this ratchet.** Once every skill has a committed, valid eval file, ws-14
> deletes every entry from ``EVAL_KNOWN_FAILURES`` (leaving ``frozenset()``), at which point
> any invalid eval file anywhere becomes a hard failure. Do not *add* new entries here for new
> skills — new work must pass the full schema + convention immediately.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import run_evals  # noqa: E402  (path injected above)

# Snapshot of skills whose eval files are still being authored as of 2026-06-06. This is a
# *ratchet*: it only ever shrinks. Entries drain automatically as valid files land (the test
# reads the live filesystem); ws-14 removes the remainder, leaving frozenset().
EVAL_KNOWN_FAILURES: frozenset[str] = frozenset(
    {
        "alterlab-link-health",
        "alterlab-open-science",
        "alterlab-pdf-extract",
        "alterlab-peer-review",
        "alterlab-primekg",
        "alterlab-pylabrobot",
        "alterlab-rdkit",
        "alterlab-scientific-viz",
        "alterlab-shap",
    }
)


def _skill_dirs() -> list[Path]:
    return run_evals.skill_dirs()


def pytest_generate_tests(metafunc):
    """Parametrize ``skill_dir`` over every live skill directory, id'd by skill name."""
    if "skill_dir" in metafunc.fixturenames:
        dirs = _skill_dirs()
        metafunc.parametrize("skill_dir", dirs, ids=[d.name for d in dirs])


def test_skill_has_valid_eval_file(skill_dir: Path) -> None:
    """The skill's evals.json exists, is schema-valid, and meets the coverage convention."""
    result = run_evals.validate_skill(skill_dir)
    if not result.ok and skill_dir.name in EVAL_KNOWN_FAILURES:
        # Known, tracked content debt — backfill in flight. Non-strict so a now-valid
        # ratcheted skill passes instead of erroring as XPASS (ratchet drains itself).
        pytest.xfail(
            f"eval file pending (ws-* backfill; in EVAL_KNOWN_FAILURES): "
            f"{'; '.join(result.errors)}"
        )
    assert result.ok, (
        f"{result.rel} is not a valid eval file: {'; '.join(result.errors)}. "
        f"It must exist, validate against docs/evals.schema.json, and carry "
        f">={run_evals.MIN_TRIGGERS} should_trigger + >={run_evals.MIN_NEGATIVES} "
        f"should_not_trigger assertion(s). See docs/evals.md."
    )


def test_known_failures_is_a_subset_of_real_skills() -> None:
    """Guard: every ratcheted name is a real skill dir (catches typos / renamed skills).

    If a ratchet entry no longer names a real skill, it is dead weight that can never drain —
    remove it. This keeps the ratchet honest as skills are renamed.
    """
    real = {d.name for d in _skill_dirs()}
    stale = EVAL_KNOWN_FAILURES - real
    assert not stale, (
        f"EVAL_KNOWN_FAILURES references skills that no longer exist: {sorted(stale)}. "
        f"Remove them from tests/test_evals.py."
    )


def test_ratchet_has_no_passing_entries_that_should_be_removed() -> None:
    """Informational drain check: report ratcheted skills that now validate.

    These no longer need to be xfailed; they should be removed from EVAL_KNOWN_FAILURES (ws-14
    does this wholesale). This test never fails — leaving a drained entry in the ratchet is
    harmless (it just passes) — but it surfaces drained entries via a skip message so the
    cleanup is visible.
    """
    drained = sorted(
        name
        for name in EVAL_KNOWN_FAILURES
        if run_evals.validate_skill(REPO_ROOT / "skills" / _domain_of(name) / name).ok
        if _domain_of(name) is not None
    )
    if drained:
        pytest.skip(
            f"{len(drained)} ratcheted skill(s) now validate and can be removed from "
            f"EVAL_KNOWN_FAILURES (ws-14): {drained}"
        )


def _domain_of(skill_name: str) -> str | None:
    """Return the domain dir name for a skill, or None if the skill dir is absent."""
    for d in _skill_dirs():
        if d.name == skill_name:
            return d.parent.name
    return None
