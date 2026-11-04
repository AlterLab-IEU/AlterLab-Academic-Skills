"""`scripts/install.sh`, run for real into a temp directory / temp HOME.

The installer is checked by what lands on disk: shared handoff files inside each skill,
dependency skills pulled in, `${CLAUDE_PLUGIN_ROOT}` written out as the install directory,
license notices present, and every reference in the installed markdown resolving against
the install directory. Nothing installed may point back into the checkout.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import build_bundles as bb

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALL_SH = REPO_ROOT / "scripts" / "install.sh"

pytestmark = pytest.mark.skipif(
    sys.platform == "win32" or shutil.which("bash") is None, reason="install.sh needs bash"
)


def _run(*args: str, home: Path, cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "HOME": str(home)}
    return subprocess.run(["bash", str(INSTALL_SH), *args], capture_output=True, text=True,
                          env=env, cwd=cwd or home, timeout=300)


def _ok(proc: subprocess.CompletedProcess) -> subprocess.CompletedProcess:
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return proc


@pytest.fixture(scope="module")
def full_install(tmp_path_factory) -> Path:
    home = tmp_path_factory.mktemp("home")
    dest = home / "skills-dest"
    _ok(_run("--dest", str(dest), home=home))
    return dest


def test_full_install_lands_every_skill(full_install, skill_files) -> None:
    assert {p.name for p in full_install.iterdir()} == {p.parent.name for p in skill_files}


def test_full_install_references_resolve_in_install_dir(full_install) -> None:
    problems = []
    for sd in sorted(full_install.iterdir()):
        problems += bb.fatal(bb.check_skill_refs(sd, abs_root=full_install))
    assert not problems, "\n".join(map(str, problems[:40]))


def test_full_install_ships_shared_and_notices(full_install) -> None:
    for sd in sorted(full_install.iterdir()):
        for legal in bb.LEGAL_FILES:
            assert (sd / legal).is_file(), f"{sd.name} lacks {legal}"
    for name, rel in [("alterlab-deep-research", "shared/handoff_schemas.md"),
                      ("alterlab-research-pipeline", "shared/handoff_schemas.md"),
                      ("alterlab-citation-verifier", "shared/schemas/integrity_report.schema.json"),
                      ("alterlab-markitdown", "shared/model_env.md")]:
        assert (full_install / name / rel).is_file(), f"{name}/{rel}"


def test_installed_markdown_never_points_into_the_checkout(full_install) -> None:
    checkout = REPO_ROOT.as_posix()
    hits = [str(p) for p in full_install.rglob("*.md")
            if checkout in p.read_text(encoding="utf-8", errors="replace")]
    assert not hits, hits[:10]


def test_single_skill_install_pulls_its_dependencies(tmp_path) -> None:
    dest = tmp_path / "dest"
    proc = _ok(_run("--dest", str(dest), "alterlab-research-pipeline", home=tmp_path))
    assert "alterlab-citation-verifier (dependency)" in proc.stdout
    installed = {p.name for p in dest.iterdir()}
    assert {"alterlab-research-pipeline", "alterlab-citation-verifier"} <= installed
    agent = dest / "alterlab-research-pipeline" / "agents" / "integrity_verification_agent.md"
    text = agent.read_text(encoding="utf-8")
    assert bb.PLUGIN_ROOT_VAR not in text
    script = f"{dest.resolve().as_posix()}/alterlab-citation-verifier/scripts/verify_citations.py"
    assert f'"{script}"' in text
    assert Path(script).is_file()
    for sd in dest.iterdir():
        assert not bb.fatal(bb.check_skill_refs(sd, abs_root=dest.resolve())), sd.name


def test_no_deps_leaves_the_dependency_visible(tmp_path) -> None:
    dest = tmp_path / "dest"
    _ok(_run("--no-deps", "--dest", str(dest), "alterlab-research-pipeline", home=tmp_path))
    assert [p.name for p in dest.iterdir()] == ["alterlab-research-pipeline"]
    probs = bb.fatal(bb.check_skill_refs(dest / "alterlab-research-pipeline", abs_root=dest.resolve()))
    assert probs and all("alterlab-citation-verifier" in p.detail for p in probs)


def test_target_claude_installs_under_home(tmp_path) -> None:
    _ok(_run("--target", "claude", "databases/alterlab-pubmed", home=tmp_path))
    assert (tmp_path / ".claude" / "skills" / "alterlab-pubmed" / "SKILL.md").is_file()
    assert not (tmp_path / ".agents").exists()


def test_project_install(tmp_path) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    _ok(_run("--project", "methodology", home=tmp_path, cwd=project))
    dest = project / ".claude" / "skills"
    assert (dest / "alterlab-results-transparency" / "SKILL.md").is_file()
    # cross-domain dependency of the methodology gate, installed alongside it
    assert (dest / "alterlab-statistical-analysis" / "SKILL.md").is_file()


def test_reinstall_is_idempotent_and_drops_stale_files(tmp_path) -> None:
    dest = tmp_path / "dest"
    _ok(_run("--dest", str(dest), "alterlab-pubmed", home=tmp_path))
    stale = dest / "alterlab-pubmed" / "stale.md"
    stale.write_text("left over from an old version", encoding="utf-8")
    first = sorted(p.relative_to(dest).as_posix() for p in dest.rglob("*") if p != stale)
    _ok(_run("--dest", str(dest), "alterlab-pubmed", home=tmp_path))
    assert not stale.exists()
    assert sorted(p.relative_to(dest).as_posix() for p in dest.rglob("*")) == first


def test_dry_run_writes_nothing(tmp_path) -> None:
    dest = tmp_path / "dest"
    proc = _ok(_run("--dry-run", "--dest", str(dest), "core", home=tmp_path))
    assert "would install alterlab-deep-research" in proc.stdout
    assert not dest.exists()


def test_refuses_to_install_into_the_source_tree(tmp_path) -> None:
    before = sorted(p.name for p in (REPO_ROOT / "skills" / "core").iterdir())
    proc = _run("--dry-run", "--dest", str(REPO_ROOT / "skills" / "core"), "alterlab-pubmed",
                home=tmp_path)
    assert proc.returncode != 0 and "refusing" in proc.stderr
    assert sorted(p.name for p in (REPO_ROOT / "skills" / "core").iterdir()) == before


def test_unknown_selector_fails(tmp_path) -> None:
    proc = _run("--dest", str(tmp_path / "d"), "no-such-skill", home=tmp_path)
    assert proc.returncode != 0 and "selector not found" in proc.stderr
