"""Shared fixtures for the skill-schema test suite."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
SCRIPTS_DIR = REPO_ROOT / "scripts"

# Allow `import audit_skills` from within the test modules
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def skills_dir() -> Path:
    return SKILLS_DIR


@pytest.fixture(scope="session")
def skill_files() -> list[Path]:
    """All SKILL.md files in the repo, sorted by path."""
    return sorted(SKILLS_DIR.rglob("SKILL.md"))


@pytest.fixture(scope="session")
def audit_reports(skill_files):
    """Run the audit once per session and expose the SkillReport list."""
    import audit_skills

    return [audit_skills.audit_skill(p) for p in skill_files]


def pytest_generate_tests(metafunc):
    """Parametrize tests that ask for `skill_md` over every SKILL.md."""
    if "skill_md" in metafunc.fixturenames:
        files = sorted(SKILLS_DIR.rglob("SKILL.md"))
        ids = [str(p.relative_to(REPO_ROOT)) for p in files]
        metafunc.parametrize("skill_md", files, ids=ids)
