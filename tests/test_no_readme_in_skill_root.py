"""No `README.md` may sit at a skill root.

The Agent Skills spec is explicit: a skill folder's Claude-facing entry point is
``SKILL.md``; long-form Claude-facing detail lives in ``references/``. Human-facing
project docs belong at the repo root, not inside a skill. A ``README.md`` at a skill
root both violates the spec and can trip the claude.ai ``.zip`` uploader.

This guard forbids ``README.md`` (any case) *directly* in a skill directory (the one
that holds ``SKILL.md``). Reference material nested under ``references/`` or
``examples/`` is out of scope here — it is permitted-but-discouraged (prefer a
descriptive filename), and is not a spec violation.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"


def _skill_roots() -> list[Path]:
    """Every directory that directly contains a SKILL.md."""
    return sorted(p.parent for p in SKILLS_DIR.rglob("SKILL.md"))


def test_no_readme_at_any_skill_root() -> None:
    offenders: list[str] = []
    for root in _skill_roots():
        for entry in root.iterdir():
            if entry.is_file() and entry.name.lower() == "readme.md":
                offenders.append(str(entry.relative_to(REPO_ROOT)))
    assert not offenders, (
        "README.md found at a skill root — the spec forbids it (use SKILL.md for the "
        "Claude-facing entry point, references/ for detail, and the repo root for "
        f"human docs). Move or delete: {offenders}"
    )
