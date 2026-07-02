"""Per-skill frontmatter checks — one parametrized test per SKILL.md.

Failures are easy to read: pytest shows the failing skill path and the
exact assertion message. This complements the bulk audit script by
producing structured per-skill output suitable for PR comments.
"""

from __future__ import annotations

from pathlib import Path

import audit_skills


def test_frontmatter_present(skill_md: Path) -> None:
    fm, _ = audit_skills.parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    assert fm, f"{skill_md} is missing YAML frontmatter"


def test_name_matches_parent_dir(skill_md: Path) -> None:
    fm, _ = audit_skills.parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    assert fm.get("name") == skill_md.parent.name, (
        f"frontmatter `name` ({fm.get('name')!r}) must match parent dir "
        f"({skill_md.parent.name!r})"
    )


def test_name_matches_spec_pattern(skill_md: Path) -> None:
    fm, _ = audit_skills.parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    name = fm.get("name", "")
    assert audit_skills.NAME_RE.match(name), (
        f"`name` {name!r} fails spec regex {audit_skills.NAME_RE.pattern!r}"
    )
    assert len(name) <= audit_skills.NAME_MAX


def test_description_within_spec_limit(skill_md: Path) -> None:
    fm, _ = audit_skills.parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    desc = fm.get("description", "")
    assert desc, "missing `description`"
    assert len(desc) <= audit_skills.DESCRIPTION_MAX, (
        f"description is {len(desc)} chars, spec max is "
        f"{audit_skills.DESCRIPTION_MAX}"
    )


def test_license_in_controlled_vocabulary(skill_md: Path) -> None:
    fm, _ = audit_skills.parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    raw = fm.get("license", "")
    assert raw, "missing `license` field"
    canonical = audit_skills.normalize_license(raw)
    assert canonical is not None, (
        f"license {raw!r} is not in the controlled vocabulary "
        f"({sorted(audit_skills.LICENSE_VOCAB)})"
    )
    assert canonical == raw, (
        f"license {raw!r} should be canonical form {canonical!r}; "
        f"run `python3 scripts/normalize_skills.py`"
    )


def test_allowed_tools_field_present(skill_md: Path) -> None:
    fm, _ = audit_skills.parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    assert "allowed-tools" in fm, (
        "missing `allowed-tools` (Anthropic spec, experimental field); "
        "run `python3 scripts/normalize_skills.py` to add a default"
    )


def test_alterlab_naming_convention(skill_md: Path) -> None:
    fm, _ = audit_skills.parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    name = fm.get("name", "")
    if "shared" in skill_md.parent.name:
        return
    assert name.startswith(audit_skills.ALTERLAB_PREFIX), (
        f"`name` {name!r} should start with {audit_skills.ALTERLAB_PREFIX!r}"
    )


def test_frontmatter_keys_are_canonical(skill_md: Path) -> None:
    """No ad-hoc frontmatter keys (Issue #3). Every top-level and metadata key must be in the
    canonical schema; a one-off key is drift to consolidate (provenance -> metadata.skill-source,
    version pin -> compatibility)."""
    fm, _ = audit_skills.parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    unknown_top = [
        k for k in fm if "." not in k and k not in audit_skills.KNOWN_TOPLEVEL_KEYS
    ]
    unknown_meta = [
        k.split(".", 1)[1]
        for k in fm
        if k.startswith("metadata.")
        and k.split(".", 1)[1] not in audit_skills.KNOWN_METADATA_KEYS
    ]
    assert not unknown_top, (
        f"non-canonical top-level frontmatter key(s) {unknown_top}; "
        f"allowed: {sorted(audit_skills.KNOWN_TOPLEVEL_KEYS)}"
    )
    assert not unknown_meta, (
        f"non-canonical metadata key(s) {unknown_meta}; consolidate into a canonical field "
        f"(skill-source / compatibility). allowed: {sorted(audit_skills.KNOWN_METADATA_KEYS)}"
    )


def test_frontmatter_is_strict_yaml_safe(skill_md: Path) -> None:
    """No unquoted scalar may contain ': ' (colon+space) or a trailing ':' — the tolerant
    audit parser accepts these but strict YAML (the external skills-ref validator) rejects them."""
    text = skill_md.read_text(encoding="utf-8")
    unsafe = audit_skills.yaml_unsafe_frontmatter_keys(text)
    assert not unsafe, (
        f"frontmatter key(s) {unsafe} contain an unquoted ': ' or trailing ':' that breaks "
        "strict YAML parsers (skills-ref). Quote the value or rephrase (e.g. use ' — ')."
    )


def test_suite_mention_in_description_or_body(skill_md: Path) -> None:
    text = skill_md.read_text(encoding="utf-8")
    fm, body = audit_skills.parse_frontmatter(text)
    desc = fm.get("description", "")
    assert (
        audit_skills.SUITE_LABEL_LOOSE in desc
        or audit_skills.SUITE_LABEL_LOOSE in body
    ), (
        f"skill should mention {audit_skills.SUITE_LABEL_LOOSE!r} in "
        f"description or body"
    )
