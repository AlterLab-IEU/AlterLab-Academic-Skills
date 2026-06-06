"""Guard against version drift and stale skill counts in the docs."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import audit_skills  # noqa: E402


def _read_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _pyproject_version(p: Path) -> str:
    """Pull `version = "..."` from the [project] table without a TOML dependency."""
    text = p.read_text(encoding="utf-8")
    m = re.search(r'^\s*version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert m, f"could not find a version string in {p}"
    return m.group(1)


def test_package_and_marketplace_versions_match(repo_root: Path) -> None:
    pkg = _read_json(repo_root / "package.json")["version"]
    mkt = _read_json(repo_root / ".claude-plugin" / "marketplace.json")["metadata"]["version"]
    assert pkg == mkt, (
        f"version drift: package.json={pkg} but marketplace.json metadata.version={mkt}. "
        "Keep them in sync (bump both on release)."
    )


def test_pyproject_package_marketplace_versions_all_match(repo_root: Path) -> None:
    """The three release-version sources of truth must agree exactly."""
    py = _pyproject_version(repo_root / "pyproject.toml")
    pkg = _read_json(repo_root / "package.json")["version"]
    mkt = _read_json(repo_root / ".claude-plugin" / "marketplace.json")["metadata"]["version"]
    assert py == pkg == mkt, (
        "release-version drift across the three sources of truth: "
        f"pyproject.toml={py}, package.json={pkg}, marketplace.json metadata.version={mkt}. "
        "Bump all three together on release."
    )


def test_marketplace_lists_every_skill(repo_root: Path, skill_files: list[Path]) -> None:
    """Every skill on disk is listed by exactly one plugin, via the v2.0 scoped shape.

    v2.0 (per docs/design/scoping-spike.md) points each plugin's `source` at its
    own domain folder and makes `skills` entries plugin-root-relative
    (`./alterlab-foo`, not `./skills/<domain>/alterlab-foo`). So the on-disk path
    is reconstructed as `<source>/<skill-entry>` and compared to actual skill dirs.
    """
    mkt = _read_json(repo_root / ".claude-plugin" / "marketplace.json")
    listed: set[str] = set()
    for plugin in mkt["plugins"]:
        source = plugin["source"].lstrip("./").rstrip("/")  # e.g. skills/databases
        for entry in plugin["skills"]:
            skill = entry.lstrip("./").rstrip("/")           # e.g. alterlab-pubmed
            # Guard the scoping: entries must be plugin-root-relative, not re-prefixed.
            assert not skill.startswith("skills/"), (
                f"{plugin['name']}: skill entry '{entry}' is not plugin-root-relative "
                "(should be './alterlab-foo', not './skills/<domain>/alterlab-foo')."
            )
            listed.add(f"{source}/{skill}")
    actual = {
        p.relative_to(repo_root).parent.as_posix()  # e.g. skills/databases/alterlab-pubmed
        for p in skill_files
    }
    missing = actual - listed
    extra = listed - actual
    assert not missing and not extra, (
        f"marketplace.json out of sync with skills/ — missing: {sorted(missing)[:5]}, "
        f"extra: {sorted(extra)[:5]}. Run: uv run python scripts/gen_marketplace.py"
    )


def test_every_skill_declares_metadata_version(skill_files: list[Path]) -> None:
    """Every SKILL.md must carry a `metadata.version` (quoted semver) — no exceptions."""
    missing: list[str] = []
    for p in skill_files:
        fm, _ = audit_skills.parse_frontmatter(p.read_text(encoding="utf-8"))
        if "metadata.version" not in fm:
            missing.append(str(p.relative_to(REPO_ROOT)))
    assert not missing, (
        f"{len(missing)} skill(s) are missing a `metadata.version` field: "
        f"{missing[:10]}. Add a quoted semver under `metadata:` (e.g. version: \"1.0.0\")."
    )


def test_readme_skill_count_is_current(repo_root: Path, skill_files: list[Path]) -> None:
    n = len(skill_files)
    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    assert str(n) in readme, f"README.md should state the current skill count ({n})."
    # No stale pre-1.1.0 counts should linger.
    for stale in ("186+", "187 skills", "186 skills"):
        assert stale not in readme, f"README.md still contains a stale count: {stale!r}"
