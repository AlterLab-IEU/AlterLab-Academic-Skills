"""No __pycache__ artifacts may be tracked by git."""

from __future__ import annotations

import subprocess
from pathlib import Path


def test_no_pycache_tracked(repo_root: Path) -> None:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    tracked = [
        line for line in result.stdout.splitlines() if "__pycache__" in line
    ]
    assert not tracked, (
        "git is tracking __pycache__ artifacts; they must be untracked and "
        f"gitignored: {tracked}"
    )
