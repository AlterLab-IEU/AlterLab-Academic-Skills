"""SKILL.md body length checks — spec says keep main file under 500 lines.

Soft cap is the spec recommendation (warn but pass). Hard cap of 1500 lines
is treated as a failure — content that big belongs in `references/`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import audit_skills
from tests.known_failures import BODY_TOO_LONG


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


@pytest.mark.xfail(reason="Pre-existing skills are being incrementally migrated below the 500-line soft cap.", strict=False)
def test_body_below_soft_limit(skill_md: Path) -> None:
    n = _body_lines(skill_md)
    assert n <= audit_skills.BODY_LINES_SOFT_LIMIT, (
        f"body is {n} lines (soft limit {audit_skills.BODY_LINES_SOFT_LIMIT})."
    )
