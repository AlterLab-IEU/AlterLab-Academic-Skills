"""Per-skill distributable bundles build correctly.

`scripts/build_bundles.py --skills` emits one zip per skill into `dist/skills/`,
structured so the claude.ai "Customize ▸ Skills → Upload a skill" flow accepts it:
the skill folder sits at the archive's top level (`<name>/SKILL.md` …). These tests
lock that contract (every skill covered, each archive valid + correctly shaped, and
byte-deterministic) so a non-technical, one-file-download install path stays reliable.
"""

from __future__ import annotations

import zipfile

import build_bundles


def test_every_skill_gets_one_bundle(tmp_path, skill_files) -> None:
    built = build_bundles.build_all_skills(out_dir=tmp_path)
    assert len(built) == len(skill_files), "one per-skill zip per SKILL.md expected"
    names = {p.stem for p in built}
    expected = {p.parent.name for p in skill_files}
    assert names == expected, f"bundle set diverges from skills: {names ^ expected}"


def test_each_bundle_is_valid_and_top_level(tmp_path) -> None:
    built = build_bundles.build_all_skills(out_dir=tmp_path)
    problems: list[str] = []
    for p in built:
        _size, _count, probs = build_bundles.verify_skill(p)
        problems += [f"{p.name}: {pr}" for pr in probs if pr.startswith("HARD")]
        with zipfile.ZipFile(p) as zf:
            names = zf.namelist()
        # SKILL.md must live under the skill folder at the archive top level.
        if f"{p.stem}/SKILL.md" not in names:
            problems.append(f"{p.name}: SKILL.md not at <name>/ top level")
        # Nothing must escape the single top-level folder.
        stray = [n for n in names if not n.startswith(f"{p.stem}/")]
        if stray:
            problems.append(f"{p.name}: members outside {p.stem}/: {stray[:3]}")
    assert not problems, "invalid per-skill bundles:\n" + "\n".join(problems)


def test_bundles_exclude_cruft(tmp_path) -> None:
    built = build_bundles.build_all_skills(out_dir=tmp_path)
    for p in built:
        with zipfile.ZipFile(p) as zf:
            names = zf.namelist()
        assert not any(n.endswith(".pyc") or "__pycache__" in n for n in names), (
            f"{p.name} contains build cruft"
        )


def test_bundle_is_byte_deterministic(tmp_path, skill_files) -> None:
    sample = skill_files[0].parent  # any skill directory
    a = build_bundles.build_skill(sample, out_dir=tmp_path / "a")
    b = build_bundles.build_skill(sample, out_dir=tmp_path / "b")
    assert a.read_bytes() == b.read_bytes(), "per-skill zip must be reproducible"
