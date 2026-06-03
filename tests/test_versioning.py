"""Guard against version drift and stale skill counts in the docs."""

from __future__ import annotations

import json
from pathlib import Path


def _read_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def test_package_and_marketplace_versions_match(repo_root: Path) -> None:
    pkg = _read_json(repo_root / "package.json")["version"]
    mkt = _read_json(repo_root / ".claude-plugin" / "marketplace.json")["metadata"]["version"]
    assert pkg == mkt, (
        f"version drift: package.json={pkg} but marketplace.json metadata.version={mkt}. "
        "Keep them in sync (bump both on release)."
    )


def test_marketplace_lists_every_skill(repo_root: Path, skill_files: list[Path]) -> None:
    mkt = _read_json(repo_root / ".claude-plugin" / "marketplace.json")
    listed = {s for p in mkt["plugins"] for s in p["skills"]}
    actual = {
        f"./skills/{p.relative_to(repo_root / 'skills').parent.as_posix()}"
        for p in skill_files
    }
    missing = actual - listed
    extra = listed - actual
    assert not missing and not extra, (
        f"marketplace.json out of sync with skills/ — missing: {sorted(missing)[:5]}, "
        f"extra: {sorted(extra)[:5]}. Run: python scripts/gen_marketplace.py"
    )


def test_readme_skill_count_is_current(repo_root: Path, skill_files: list[Path]) -> None:
    n = len(skill_files)
    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    assert str(n) in readme, f"README.md should state the current skill count ({n})."
    # No stale pre-1.1.0 counts should linger.
    for stale in ("186+", "187 skills", "186 skills"):
        assert stale not in readme, f"README.md still contains a stale count: {stale!r}"
