"""claude.ai custom-skill uploader compatibility guard.

The claude.ai ``.zip`` validator rejects any top-level frontmatter key outside
``{name, description, license, allowed-tools, metadata}`` (anthropics/skills#37). One
unexpected key fails ALL skill uploads at once. This suite intentionally adds exactly
one extra top-level key, ``compatibility`` (Claude-Code/SDK-only; stripped for claude.ai
by ``scripts/check_claudeai_compat.py --package``).

These tests pin that contract: every skill's top-level keys stay within the known set,
so accidental key-drift is caught here instead of on a user's failed upload.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import check_claudeai_compat as cc  # noqa: E402


def test_no_unexpected_frontmatter_key_drift(skill_md: Path) -> None:
    """Every skill's top-level keys are within the known set (whitelist + compatibility)."""
    keys = cc.top_level_keys(skill_md)
    drift = [k for k in keys if k not in cc.KNOWN_KEYS]
    assert not drift, (
        f"{skill_md.relative_to(REPO_ROOT)} has top-level frontmatter key(s) {drift} "
        f"outside the known set {sorted(cc.KNOWN_KEYS)}. The claude.ai uploader would "
        "reject the whole suite. Remove the key, or (if intentional and Claude-Code-only) "
        "add it to INTENTIONAL_EXTRA in scripts/check_claudeai_compat.py after review."
    )


def test_packaging_strips_to_whitelist(skill_md: Path) -> None:
    """After --package stripping, only whitelisted top-level keys survive."""
    stripped = cc._strip_non_whitelisted(skill_md.read_text(encoding="utf-8"))
    # Re-parse the stripped text via a temp-free path: write nothing, reuse the parser.
    lines = stripped.split("\n")
    assert lines and lines[0].strip() == "---", "stripped output lost its frontmatter fence"
    keys = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line and line[0] not in " \t#":
            keys.append(line.partition(":")[0].strip())
    outside = [k for k in keys if k not in cc.CLAUDEAI_WHITELIST]
    assert not outside, (
        f"claude.ai packaging left non-whitelisted keys {outside} in "
        f"{skill_md.relative_to(REPO_ROOT)}"
    )
    # A stripped skill must still carry the load-bearing keys.
    assert "name" in keys and "description" in keys, "packaging dropped name/description"
