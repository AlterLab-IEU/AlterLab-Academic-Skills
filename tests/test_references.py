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


# --------------------------------------------------------------------------- #
# Unit coverage for the extended _REF_RE / resolver behavior.
# --------------------------------------------------------------------------- #

def _mk_skill(root: Path, name: str) -> Path:
    d = root / "skills" / "cat" / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text("---\nname: " + name + "\n---\n", encoding="utf-8")
    return d


def test_ref_re_matches_shared_scripts_and_schemas() -> None:
    """_REF_RE now captures shared/, scripts/, and *.schema.json citations, not just refs."""
    line = (
        "see `references/api.md`, `shared/model_env.md`, "
        "`shared/schemas/rq_brief.schema.json`, and `scripts/run.py`"
    )
    matches = {relref for _prefix, relref in audit_skills._REF_RE.findall(line)}
    assert "references/api.md" in matches
    assert "shared/model_env.md" in matches
    assert "shared/schemas/rq_brief.schema.json" in matches
    assert "scripts/run.py" in matches


def test_resolves_self_scripts_reference(tmp_path: Path, monkeypatch) -> None:
    """A skill-local scripts/*.py citation resolves against the skill's own dir."""
    monkeypatch.setattr(audit_skills, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(audit_skills, "SKILLS_DIR", tmp_path / "skills")
    monkeypatch.setattr(audit_skills, "_SHARED_ROOT", tmp_path / "skills" / "core")
    monkeypatch.setattr(audit_skills, "_SKILL_INDEX", None)
    skill = _mk_skill(tmp_path, "alterlab-demo")
    (skill / "scripts").mkdir()
    (skill / "scripts" / "run.py").write_text("# ok\n", encoding="utf-8")

    assert audit_skills.missing_references("uses `scripts/run.py` here", skill) == []
    assert audit_skills.missing_references("uses `scripts/missing.py`", skill) == ["scripts/missing.py"]


def test_resolves_bare_shared_against_core(tmp_path: Path, monkeypatch) -> None:
    """A bare `shared/...` citation from any skill resolves under skills/core/shared/."""
    monkeypatch.setattr(audit_skills, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(audit_skills, "SKILLS_DIR", tmp_path / "skills")
    monkeypatch.setattr(audit_skills, "_SHARED_ROOT", tmp_path / "skills" / "core")
    monkeypatch.setattr(audit_skills, "_SKILL_INDEX", None)
    consumer = _mk_skill(tmp_path, "alterlab-consumer")
    shared = tmp_path / "skills" / "core" / "shared"
    (shared / "schemas").mkdir(parents=True)
    (shared / "model_env.md").write_text("env\n", encoding="utf-8")
    (shared / "schemas" / "rq_brief.schema.json").write_text("{}\n", encoding="utf-8")

    body = "follows `shared/model_env.md` and `shared/schemas/rq_brief.schema.json`"
    assert audit_skills.missing_references(body, consumer) == []
    assert audit_skills.missing_references("see `shared/nope.md`", consumer) == ["shared/nope.md"]


def test_resolves_full_repo_relative_shared(tmp_path: Path, monkeypatch) -> None:
    """A full `skills/core/shared/...` path resolves against the repo root."""
    monkeypatch.setattr(audit_skills, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(audit_skills, "SKILLS_DIR", tmp_path / "skills")
    monkeypatch.setattr(audit_skills, "_SHARED_ROOT", tmp_path / "skills" / "core")
    monkeypatch.setattr(audit_skills, "_SKILL_INDEX", None)
    consumer = _mk_skill(tmp_path, "alterlab-consumer")
    shared = tmp_path / "skills" / "core" / "shared"
    shared.mkdir(parents=True)
    (shared / "model_env.md").write_text("env\n", encoding="utf-8")

    body = "(`skills/core/shared/model_env.md`)"
    # The full path embeds `shared/model_env.md`, which resolves under _SHARED_ROOT.
    assert audit_skills.missing_references(body, consumer) == []


def test_deep_references_flags_nested_only() -> None:
    """references/ one-level-deep guard flags nested paths, leaves flat ones alone."""
    flat = "see `references/api.md` and `references/templates.md`"
    assert audit_skills.deep_references(flat) == []

    nested = "see `references/v2/api.md`"
    assert audit_skills.deep_references(nested) == ["references/v2/api.md"]
    assert audit_skills.REFERENCES_MAX_DEPTH == 1
