"""SKILL.md body length checks — spec says keep main file under 500 lines.

Two gates:

* Hard cap (1500 lines) — content that big belongs in `references/`; a body
  over it fails (with a temporary `known_failures.BODY_TOO_LONG` escape hatch).
* Soft cap (500 lines) — a *ratchet*. Every SKILL.md whose body still exceeds
  500 lines after the slimming wave is enumerated in ``BODY_OVER_SOFT_LIMIT``
  below. The ratchet only moves down:

    - a body over 500 lines that is **not** in the set fails (you grew a new
      offender, or added a fat skill — slim it or split into references/);
    - an entry in the set whose body is now **≤500** fails as a *stale ratchet
      entry* (you fixed it — delete the line so it can't silently regress).

  Net effect: the soft cap is enforced for everything except the frozen
  backlog, and the backlog can only shrink.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import audit_skills
from tests.known_failures import BODY_TOO_LONG

# Frozen backlog of SKILL.md bodies still over the 500-line soft cap as of the
# v2.0 slimming wave. Measured live (body = lines after the closing `---`, via
# audit_skills.parse_frontmatter). Target was 0; the slimming agents left these
# 21. Ratchet rule: this set may only shrink. When you slim one of these below
# 500 lines, REMOVE its entry — the stale-entry gate will fail until you do.
BODY_OVER_SOFT_LIMIT: frozenset[str] = frozenset(
    {
        "skills/cheminformatics/alterlab-datamol/SKILL.md",
        "skills/cheminformatics/alterlab-deepchem/SKILL.md",
        "skills/cheminformatics/alterlab-molfeat/SKILL.md",
        "skills/cheminformatics/alterlab-rdkit/SKILL.md",
        "skills/core/alterlab-deep-research/SKILL.md",
        "skills/core/alterlab-research-pipeline/SKILL.md",
        "skills/core/alterlab-teaching-design/SKILL.md",
        "skills/core/alterlab-thesis-supervisor/SKILL.md",
        "skills/domain-specific/alterlab-hypogenic/SKILL.md",
        "skills/lab-integrations/alterlab-opentrons/SKILL.md",
        "skills/research-tools/alterlab-mixed-methods/SKILL.md",
        "skills/research-tools/alterlab-open-science/SKILL.md",
        "skills/research-tools/alterlab-qualitative-methods/SKILL.md",
        "skills/research-tools/alterlab-research-ethics/SKILL.md",
        "skills/research-tools/alterlab-scientific-thinking/SKILL.md",
        "skills/research-tools/alterlab-survey-design/SKILL.md",
        "skills/writing-tools/alterlab-academic-career/SKILL.md",
    }
)


def _body_lines(skill_md: Path) -> int:
    _, body = audit_skills.parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    return body.count("\n") + 1


def test_body_below_hard_limit(skill_md: Path, repo_root: Path) -> None:
    rel = str(skill_md.relative_to(repo_root))
    if rel in BODY_TOO_LONG:
        pytest.xfail(f"known content debt: {BODY_TOO_LONG[rel]}")
    n = _body_lines(skill_md)
    assert n <= audit_skills.BODY_LINES_HARD_LIMIT, (
        f"body is {n} lines (hard limit {audit_skills.BODY_LINES_HARD_LIMIT}). "
        "Split detail into references/ to keep the main file scannable."
    )


def test_body_soft_cap_ratchet(skill_md: Path, repo_root: Path) -> None:
    """Gate the 500-line soft cap against the frozen backlog (ratchet down only)."""
    rel = str(skill_md.relative_to(repo_root))
    n = _body_lines(skill_md)
    over = n > audit_skills.BODY_LINES_SOFT_LIMIT
    listed = rel in BODY_OVER_SOFT_LIMIT

    if listed and not over:
        pytest.fail(
            f"stale ratchet entry — remove it: {rel} body is now {n} lines "
            f"(≤{audit_skills.BODY_LINES_SOFT_LIMIT} soft cap). Delete it from "
            "BODY_OVER_SOFT_LIMIT in tests/test_body_length.py so it can't regress."
        )
    if over and not listed:
        pytest.fail(
            f"{rel} body is {n} lines (>{audit_skills.BODY_LINES_SOFT_LIMIT} soft "
            "cap) and is not in the ratchet. Slim it or split detail into "
            "references/ — do not add it to BODY_OVER_SOFT_LIMIT (the ratchet "
            "only moves down)."
        )


def test_ratchet_entries_all_exist(repo_root: Path) -> None:
    """Every ratchet path must point at a real SKILL.md (guards against typos/renames)."""
    missing = sorted(p for p in BODY_OVER_SOFT_LIMIT if not (repo_root / p).is_file())
    assert not missing, (
        "BODY_OVER_SOFT_LIMIT references files that don't exist (renamed/deleted?): "
        + ", ".join(missing)
    )
