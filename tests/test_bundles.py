"""Release archives, built by the one packaging helper, inspected as built.

`scripts/build_bundles.py release` is what `.github/workflows/release.yml` runs. These tests
build the whole release into a temp dir once, then open the archives with `zipfile` /
extract them and check what a user actually downloads:

* per-skill claude.ai archives (`skill-<name>-<v>.zip`): one top-level `<name>/` folder,
  frontmatter reduced to the uploader whitelist, the cited `shared/` files and the license
  notices inside, every reference resolving inside the archive (or inside a declared
  companion archive extracted next to it), counts within the documented/guard limits;
* per-domain skills bundles (`alterlab-<domain>-<v>.zip`): skill folders at the root, the
  domain's dependency closure included, everything resolving inside the archive;
* the plugin-marketplace snapshot (`alterlab-academic-skills-<v>.zip`): verbatim plugin
  layout that the real `claude plugin validate` accepts.

Resolution is always computed inside the extracted archive — a file that exists only in the
checkout cannot make a test pass.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

import build_bundles as bb
import check_claudeai_compat as cc

REPO_ROOT = Path(__file__).resolve().parent.parent
VERSION = "0.0.0-test"


@pytest.fixture(scope="module")
def release(tmp_path_factory) -> tuple[Path, dict]:
    out = tmp_path_factory.mktemp("dist")
    manifest = bb.build_release(out, VERSION)
    return out, manifest


@pytest.fixture(scope="module")
def records(release) -> dict[str, dict]:
    return {r["archive"]: r for r in release[1]["archives"]}


def _names(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as zf:
        return zf.namelist()


def _files(path: Path) -> list[str]:
    return [n for n in _names(path) if not n.endswith("/")]


def _read(path: Path, member: str) -> str:
    with zipfile.ZipFile(path) as zf:
        return zf.read(member).decode("utf-8")


def _skill_archives(release) -> list[tuple[Path, dict]]:
    out, manifest = release
    return [(out / r["archive"], r) for r in manifest["archives"] if r["target"] == "claudeai"]


# --------------------------------------------------------------------------- inventory

def test_release_has_every_target(release, skill_files) -> None:
    out, manifest = release
    by_target: dict[str, list[dict]] = {}
    for r in manifest["archives"]:
        by_target.setdefault(r["target"], []).append(r)
    assert {r["skills"][0] for r in by_target["claudeai"]} == {p.parent.name for p in skill_files}
    assert {r["domain"] for r in by_target["skills-bundle"]} == set(bb.domains())
    assert [r["archive"] for r in by_target["plugin"]] == [bb.collection_archive_name(VERSION)]
    assert {p.name for p in out.glob("*.zip")} == {r["archive"] for r in manifest["archives"]}
    on_disk = json.loads((out / "release-manifest.json").read_text(encoding="utf-8"))
    assert on_disk == manifest


def test_full_verification_passes(release, tmp_path) -> None:
    """The exact check release.yml runs after building (`release --verify`)."""
    problems = bb.verify_release(release[0], tmp_path)
    assert not problems, "\n".join(problems[:40])


# --------------------------------------------------------------------------- per-skill archives

def test_skill_archives_have_one_top_level_folder(release) -> None:
    bad = []
    for path, rec in _skill_archives(release):
        name = rec["skills"][0]
        tops = {n.split("/", 1)[0] for n in _names(path)}
        if tops != {name} or f"{name}/SKILL.md" not in _names(path):
            bad.append(f"{path.name}: {sorted(tops)}")
    assert not bad, "\n".join(bad)


def test_skill_archive_frontmatter_is_sanitized(release, tmp_path) -> None:
    """Only the claude.ai whitelist survives; name/description/license are kept intact."""
    bad = []
    for path, rec in _skill_archives(release):
        name = rec["skills"][0]
        md = tmp_path / f"{name}.md"
        md.write_text(_read(path, f"{name}/SKILL.md"), encoding="utf-8")
        keys = cc.top_level_keys(md)
        extra = [k for k in keys if k not in cc.CLAUDEAI_WHITELIST]
        if extra or "name" not in keys or "description" not in keys:
            bad.append(f"{path.name}: keys {keys}")
    assert not bad, "\n".join(bad[:20])


def test_source_frontmatter_needed_sanitizing(skill_files) -> None:
    """Guard against a vacuous sanitization test: the source does carry `compatibility`."""
    assert any("compatibility" in cc.top_level_keys(p) for p in skill_files)


def test_skill_archives_carry_cited_shared_files(release) -> None:
    """Every `shared/...` a packaged skill cites is inside its archive, byte-identical."""
    checked = 0
    bad = []
    for path, rec in _skill_archives(release):
        name = rec["skills"][0]
        members = set(_files(path))
        with zipfile.ZipFile(path) as zf:
            text = "\n".join(zf.read(n).decode("utf-8", "replace")
                             for n in members if n.endswith(".md"))
            for rel in sorted(set(re.findall(r"(?<![\w./-])shared/[\w./-]+\.(?:md|json)", text))):
                checked += 1
                member = f"{name}/{rel}"
                if member not in members:
                    bad.append(f"{path.name}: cites {rel}, no {member}")
                elif zf.read(member) != (bb.SHARED / rel[len("shared/"):]).read_bytes():
                    bad.append(f"{path.name}: {member} differs from the canonical copy")
    assert checked, "no shared/ citation found in any archive — the check is vacuous"
    assert not bad, "\n".join(bad)


def test_deep_research_archive_ships_handoff_schemas(release) -> None:
    """Regression: the v3.0.1 deep-research archive cited shared/handoff_schemas.md without it."""
    path = release[0] / bb.skill_archive_name("alterlab-deep-research", VERSION)
    assert "alterlab-deep-research/shared/handoff_schemas.md" in _names(path)


def test_skill_archives_carry_license_notices(release) -> None:
    bad = [f"{p.name}: {legal}" for p, rec in _skill_archives(release) for legal in bb.LEGAL_FILES
           if f"{rec['skills'][0]}/{legal}" not in _names(p)]
    assert not bad, "\n".join(bad[:20])


def test_cc_by_nc_skills_keep_their_license_and_attribution(release) -> None:
    """The CC-BY-NC-4.0 core pipeline skills keep `license:` and ship the required attribution.

    The upstream's verbatim attribution lives in NOTICE, which every packaged skill carries."""
    nc = []
    for path, rec in _skill_archives(release):
        name = rec["skills"][0]
        if re.search(r"(?m)^license:\s*CC-BY-NC-4\.0\s*$", _read(path, f"{name}/SKILL.md")):
            nc.append(name)
            notice = _read(path, f"{name}/NOTICE")
            assert "Based on Academic Research Skills by Cheng-I Wu" in notice, name
            assert f"skills/core/{name}" in notice, f"NOTICE does not name {name}"
    assert sorted(nc) == ["alterlab-deep-research", "alterlab-paper-reviewer",
                          "alterlab-paper-writer", "alterlab-research-pipeline"], nc


def test_skill_archives_render_plugin_root(release) -> None:
    """`${CLAUDE_PLUGIN_ROOT}` means nothing outside a plugin; archives write it out."""
    bad = []
    for path, _rec in _skill_archives(release):
        with zipfile.ZipFile(path) as zf:
            for n in zf.namelist():
                if n.endswith(".md") and bb.PLUGIN_ROOT_VAR in zf.read(n).decode("utf-8", "replace"):
                    bad.append(f"{path.name}:{n}")
    assert not bad, "\n".join(bad)


def test_skill_archives_have_no_repository_layout_paths(release, tmp_path) -> None:
    bad = []
    for path, rec in _skill_archives(release):
        root = bb.safe_extract(path, tmp_path / rec["skills"][0])
        bad += [f"{path.name}: {f}:{n}: {raw}"
                for f, n, raw in bb.repo_layout_paths(root / rec["skills"][0])]
    assert not bad, "\n".join(bad[:20])


def test_references_resolve_inside_each_skill_archive(release, tmp_path) -> None:
    """Alone, an archive may only miss files that live in its declared companion skills."""
    bad = []
    for path, rec in _skill_archives(release):
        name = rec["skills"][0]
        root = bb.safe_extract(path, tmp_path / name)
        for p in bb.fatal(bb.check_skill_refs(root / name)):
            sibling = re.search(r"needs sibling skill (\S+)\)", p.detail)
            if p.kind == "missing-companion" and sibling and sibling.group(1) in rec["companions"]:
                continue
            bad.append(f"{path.name}: {p}")
    assert not bad, "\n".join(bad[:40])


def test_companion_archives_complete_cross_skill_paths(release, records, tmp_path) -> None:
    """research-pipeline's agents call the citation verifier; side by side it resolves."""
    out = release[0]
    rec = records[bb.skill_archive_name("alterlab-research-pipeline", VERSION)]
    assert "alterlab-citation-verifier" in rec["companions"]
    for name in ["alterlab-research-pipeline", *rec["companions"]]:
        bb.safe_extract(out / bb.skill_archive_name(name, VERSION), tmp_path)
    agent = tmp_path / "alterlab-research-pipeline" / "agents" / "integrity_verification_agent.md"
    text = agent.read_text(encoding="utf-8")
    assert '"../alterlab-citation-verifier/scripts/verify_citations.py"' in text
    skill_dir = agent.parent.parent
    assert (skill_dir / "../alterlab-citation-verifier/scripts/verify_citations.py").is_file()
    assert not bb.fatal(bb.check_skill_refs(skill_dir))


def test_skill_archives_within_limits(release) -> None:
    bad = []
    for path, _rec in _skill_archives(release):
        with zipfile.ZipFile(path) as zf:
            infos = [i for i in zf.infolist() if not i.is_dir()]
        if len(infos) > bb.CLAUDEAI_MAX_FILES:
            bad.append(f"{path.name}: {len(infos)} files")
        if sum(i.file_size for i in infos) >= bb.CLAUDEAI_MAX_UNCOMPRESSED_BYTES:
            bad.append(f"{path.name}: uncompressed size")
    assert not bad, "\n".join(bad)


def test_archives_exclude_cruft(release) -> None:
    bad = [f"{p.name}: {n}" for p in release[0].glob("*.zip") for n in _names(p)
           if n.endswith((".pyc", ".pyo", ".DS_Store")) or "__pycache__" in n]
    assert not bad, "\n".join(bad[:20])


def test_archives_are_byte_deterministic(tmp_path) -> None:
    sd = bb.skill_index()["alterlab-deep-research"]
    a = bb.build_skill_archive(sd, tmp_path / "a", VERSION)
    b = bb.build_skill_archive(sd, tmp_path / "b", VERSION)
    assert a.read_bytes() == b.read_bytes()
    a = bb.build_domain_archive("methodology", tmp_path / "a", VERSION)
    b = bb.build_domain_archive("methodology", tmp_path / "b", VERSION)
    assert a.read_bytes() == b.read_bytes()


# --------------------------------------------------------------------------- domain bundles

def test_domain_bundles_hold_only_skill_folders(release, tmp_path) -> None:
    bad = []
    for r in release[1]["archives"]:
        if r["target"] != "skills-bundle":
            continue
        root = bb.safe_extract(release[0] / r["archive"], tmp_path / r["domain"])
        entries = sorted(p.name for p in root.iterdir())
        if entries != sorted(r["skills"]):
            bad.append(f"{r['archive']}: {entries} != {r['skills']}")
        bad += [f"{r['archive']}:{e}: no SKILL.md" for e in entries if not (root / e / "SKILL.md").is_file()]
    assert not bad, "\n".join(bad[:20])


def test_domain_bundles_include_dependency_skills(records) -> None:
    """Regression for cross-skill commands: the core bundle is closed under its references."""
    rec = records[bb.domain_archive_name("methodology", VERSION)]
    assert "alterlab-statistical-analysis" in rec["dependencies_included"]
    core = records[bb.domain_archive_name("core", VERSION)]
    assert "alterlab-citation-verifier" in core["skills"]


def test_data_science_bundle_contents(release, records, tmp_path) -> None:
    """Regression: the v3.0.1 data-science zip had 222 files and no license notices.

    Domain bundles are skills-directory bundles (unzip into ~/.claude/skills), not claude.ai
    uploads, so the per-upload file guard does not apply; they stay under the repo ceiling."""
    rec = records[bb.domain_archive_name("data-science", VERSION)]
    path = release[0] / rec["archive"]
    assert path.stat().st_size < bb.MAX_ARCHIVE_BYTES
    expected = {d.name for d in bb.domain_skill_dirs("data-science")}
    assert expected <= set(rec["skills"])
    root = bb.safe_extract(path, tmp_path)
    for sd in sorted(p for p in root.iterdir()):
        for legal in bb.LEGAL_FILES:
            assert (sd / legal).is_file(), f"{sd.name} lacks {legal}"
        assert not bb.fatal(bb.check_skill_refs(sd)), sd.name


# --------------------------------------------------------------------------- plugin snapshot

def test_collection_is_a_verbatim_plugin_marketplace(release, tmp_path) -> None:
    path = release[0] / bb.collection_archive_name(VERSION)
    root = bb.safe_extract(path, tmp_path)
    marketplace = json.loads((root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    for entry in marketplace["plugins"]:
        assert (root / entry["source"]).is_dir(), entry["name"]
    for name in bb.COLLECTION_TOP_FILES:
        assert (root / name).is_file(), name
    agent = root / "skills/core/alterlab-research-pipeline/agents/integrity_verification_agent.md"
    assert bb.PLUGIN_ROOT_VAR in agent.read_text(encoding="utf-8"), "plugin target must not render"
    skill_md = root / "skills/core/alterlab-deep-research/SKILL.md"
    assert "compatibility" in cc.top_level_keys(skill_md), "plugin target must not sanitize"


@pytest.mark.skipif(shutil.which("claude") is None, reason="claude CLI not installed")
def test_collection_passes_claude_plugin_validate(release, tmp_path) -> None:
    root = bb.safe_extract(release[0] / bb.collection_archive_name(VERSION), tmp_path)
    proc = subprocess.run(["claude", "plugin", "validate", str(root)], capture_output=True,
                          text=True, timeout=180)
    assert proc.returncode == 0 and "Validation passed" in proc.stdout, proc.stdout + proc.stderr


# --------------------------------------------------------------------------- the checks have teeth

def test_v301_style_archive_fails_verification(tmp_path) -> None:
    """A raw copy of the skill folder (what the old `zip -r` release step produced) fails:
    unsanitized frontmatter, no shared copy, no notices."""
    sd = bb.skill_index()["alterlab-deep-research"]
    raw = [bb.Member(f"{sd.name}/{f.relative_to(sd).as_posix()}", f.read_bytes(), 0o644)
           for f in bb.tree_files(sd) if "shared" not in f.relative_to(sd).parts]
    path = bb.write_zip(tmp_path / "old.zip", raw)
    problems = "\n".join(bb.verify_skill_archive(path, tmp_path / "x", sd.name, []))
    assert "non-whitelisted frontmatter keys ['compatibility']" in problems
    assert "cites shared/handoff_schemas.md" in problems
    assert "missing LICENSE" in problems and "missing NOTICE" in problems


def test_checker_flags_repo_layout_placeholder_and_dangling_paths(tmp_path) -> None:
    sd = tmp_path / "alterlab-demo"
    (sd / "agents").mkdir(parents=True)
    (sd / "SKILL.md").write_text(
        "---\nname: alterlab-demo\ndescription: d\n---\n"
        "Run `uv run python skills/core/alterlab-citation-verifier/scripts/verify_citations.py`.\n"
        "Schemas: `shared/handoff_schemas.md`.\n\nHelper: `scripts/missing.py`.\n",
        encoding="utf-8")
    (sd / "agents" / "a.md").write_text(
        'uv run python "${CLAUDE_PLUGIN_ROOT}/alterlab-other/scripts/x.py"\n'
        "see ../alterlab-other/references/y.md\n", encoding="utf-8")
    probs = bb.check_skill_refs(sd)
    kinds = sorted({p.kind for p in probs})
    assert kinds == ["missing-companion", "placeholder", "repo-layout", "unresolved"], kinds
    unresolved = sorted(p.detail for p in probs if p.kind == "unresolved")
    assert unresolved == ["scripts/missing.py", "shared/handoff_schemas.md"], unresolved
    with_root = bb.check_skill_refs(sd, plugin_root=tmp_path)
    assert "placeholder" not in {p.kind for p in with_root}
    assert any("alterlab-other/scripts/x.py" in p.detail for p in with_root)


# --------------------------------------------------------------------------- bookkeeping

def test_known_unresolved_entries_still_apply(release, tmp_path) -> None:
    """The content-debt allowlist only shrinks: remove an entry once its reference resolves."""
    seen: set[tuple[str, str]] = set()
    for skill in sorted({s for s, _ in bb.KNOWN_UNRESOLVED}):
        path = release[0] / bb.skill_archive_name(skill, VERSION)
        root = bb.safe_extract(path, tmp_path / skill)
        for p in bb.check_skill_refs(root / skill, allow_known=False):
            if p.kind == "unresolved":
                seen.add((skill, p.detail))
    stale = sorted(set(bb.KNOWN_UNRESOLVED) - seen)
    assert not stale, f"these now resolve — delete them from KNOWN_UNRESOLVED: {stale}"


def test_release_workflow_calls_the_tested_helper() -> None:
    text = (REPO_ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert re.search(r"scripts/build_bundles\.py release .*--verify", text, re.S)
    assert "pytest tests/test_bundles.py tests/test_install.py" in text
    assert not re.search(r"(?m)^\s*(?:\(.*)?zip -r", text), "release.yml must not zip by hand"
    assert "dist/release-manifest.json" in text
