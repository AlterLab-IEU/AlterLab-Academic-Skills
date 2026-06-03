"""Every references/*.md path cited in a SKILL.md body must exist on disk."""

from __future__ import annotations

from pathlib import Path

import pytest

import audit_skills
from tests.known_failures import REFERENCES_MISSING


def test_cited_references_exist(skill_md: Path, repo_root: Path) -> None:
    rel = str(skill_md.relative_to(repo_root))
    if rel in REFERENCES_MISSING:
        pytest.xfail(f"known content debt: {REFERENCES_MISSING[rel]}")
    text = skill_md.read_text(encoding="utf-8")
    _, body = audit_skills.parse_frontmatter(text)
    # Cross-skill aware: a citation resolves if the file exists in this skill or in
    # a sibling skill named on the same line (see audit_skills.missing_references).
    missing = audit_skills.missing_references(body, skill_md.parent)
    assert not missing, (
        f"{skill_md.name} cites reference files that do not exist on disk: "
        f"{missing}. Either create the files or fix the citation."
    )
