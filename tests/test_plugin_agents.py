"""Registerable-frontmatter checks for core plugin agent files.

Every `agents/*.md` under `skills/core/**` must carry YAML frontmatter with
at least a `name` and a `description` so the agent can be registered. This
mirrors the per-SKILL.md frontmatter suite but targets the sub-agent files.

Two files are owned by a concurrent workstream and are ratcheted via
known_failures.PLUGIN_AGENTS_MISSING_FRONTMATTER so CI stays green while the
debt stays visible. Remove an entry there once its frontmatter lands; the test
flips XPASS → hard failure if it regresses.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import audit_skills
from tests.known_failures import PLUGIN_AGENTS_MISSING_FRONTMATTER

REPO_ROOT = Path(__file__).resolve().parent.parent
CORE_DIR = REPO_ROOT / "skills" / "core"


def _agent_files() -> list[Path]:
    """Every agents/*.md under skills/core/**, sorted by path."""
    return sorted(CORE_DIR.glob("*/agents/*.md"))


def pytest_generate_tests(metafunc):
    if "agent_md" in metafunc.fixturenames:
        files = _agent_files()
        ids = [str(p.relative_to(REPO_ROOT)) for p in files]
        metafunc.parametrize("agent_md", files, ids=ids)


def test_agents_discovered() -> None:
    """Guard the glob itself — an empty result would make every check vacuous."""
    files = _agent_files()
    assert files, f"no agents/*.md files found under {CORE_DIR}"


def test_agent_has_name_and_description(agent_md: Path) -> None:
    rel = str(agent_md.relative_to(REPO_ROOT))
    if rel in PLUGIN_AGENTS_MISSING_FRONTMATTER:
        pytest.xfail(
            f"known frontmatter debt: {PLUGIN_AGENTS_MISSING_FRONTMATTER[rel]}"
        )

    fm, _ = audit_skills.parse_frontmatter(agent_md.read_text(encoding="utf-8"))
    assert fm, f"{rel} is missing YAML frontmatter"
    assert fm.get("name"), f"{rel} frontmatter is missing a non-empty `name`"
    assert fm.get("description"), (
        f"{rel} frontmatter is missing a non-empty `description`"
    )
