"""The generated agents/teams catalog must stay current and reference real agents."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import gen_agents_catalog as gac  # noqa: E402


def test_every_team_member_exists() -> None:
    missing = gac.missing_team_members()
    assert not missing, (
        "docs/agents-and-teams.md teams reference agent files that do not exist "
        f"(rename/removal?): {missing}"
    )


def test_agents_catalog_is_current() -> None:
    rendered = gac.render()
    on_disk = gac.OUT.read_text(encoding="utf-8") if gac.OUT.exists() else ""
    assert on_disk == rendered, (
        "docs/agents-and-teams.md is stale — regenerate with "
        "`python3 scripts/gen_agents_catalog.py` and commit the result."
    )
