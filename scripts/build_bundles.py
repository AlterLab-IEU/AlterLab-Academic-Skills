#!/usr/bin/env python3
"""The single packaging path for AlterLab Academic Skills: plain installs and release archives.

Everything that ships a skill outside the git checkout goes through this module, so the
dependency, rendering and verification rules exist exactly once:

* ``scripts/install.sh`` (plain install into a skills directory) calls ``install``;
* ``.github/workflows/release.yml`` calls ``release`` and then ``verify``;
* ``scripts/check_claudeai_compat.py --package`` calls ``materialize`` for the claude.ai target;
* ``tests/test_bundles.py`` and ``tests/test_install.py`` build into a temp dir and inspect
  the actual output (zip members / installed files), never the checkout.

Layout conventions (what "a reference resolves" means)
------------------------------------------------------
* Every relative path in a skill's markdown is relative to the skill's own folder (the folder
  holding ``SKILL.md``), never to the repository root. ``skills/<domain>/...`` paths are
  repository-layout paths; they resolve in no installed layout and are rejected.
* Shared handoff resources: the canonical copies live in ``skills/core/shared/``. A skill that
  cites ``shared/<file>`` carries a byte-identical copy at ``<skill>/shared/<file>``. The copies
  are committed (``sync-shared`` writes them, ``sync-shared --check`` and the tests catch drift)
  so the citation resolves in the checkout, in a Claude Code plugin install, in a plain install
  and in every archive. ``<skill>/shared/`` is reserved for these copies.
* Sibling skills are addressed as ``../<skill>/<path>`` (or, in prose, ``<skill>/<path>``). Such
  a reference is a dependency: the installer installs the sibling as well, domain archives
  include it, and per-skill archives list it as a companion upload.
* Plugin components (``agents/*.md``, ``commands/*.md``) run without a skill folder of their own,
  so they address siblings as ``${CLAUDE_PLUGIN_ROOT}/<skill>/<path>``. Claude Code substitutes
  ``${CLAUDE_PLUGIN_ROOT}`` in plugin skill, agent and command content (code.claude.com/docs/en/
  plugins-reference, "Environment variables"); nothing substitutes it outside a plugin, so the
  non-plugin targets below write it out.

Targets
-------
==================  ==========================================  ==============================
target              output                                      transformation
==================  ==========================================  ==============================
``install``         ``<dest>/<skill>/`` (+ dependency skills)   ``${CLAUDE_PLUGIN_ROOT}`` ->
                                                                absolute ``<dest>``
``claudeai``        ``skill-<name>-<version>.zip``: one         frontmatter sanitized with the
                    top-level ``<name>/`` folder                ``check_claudeai_compat`` rules;
                                                                ``${CLAUDE_PLUGIN_ROOT}`` -> ``..``
``skills-bundle``   ``alterlab-<domain>-<version>.zip``: skill  ``${CLAUDE_PLUGIN_ROOT}`` -> ``..``
                    folders at the archive root (domain +
                    dependency closure); unzip into a skills
                    directory. Plugin-only domain files
                    (.mcp.json, hooks/, workflows/*.js,
                    .claude-plugin/) are not included.
``plugin``          ``alterlab-academic-skills-<version>.zip``: none — Claude Code substitutes
                    the marketplace snapshot (``.claude-        the variable itself
                    plugin/``, ``skills/``, ``plugins/``)
==================  ==========================================  ==============================

Every installed skill folder and every archive carries the repository's ``LICENSE``, ``NOTICE``
and ``THIRD_PARTY_NOTICES.md`` (inside each skill folder for the first three targets, at the
archive root for ``plugin``); each skill's own ``license:`` frontmatter is kept by every target.

Limits
------
Only the claude.ai target has platform limits, and only some are documented:

* ``CLAUDEAI_MAX_UNCOMPRESSED_BYTES`` (30 MB, uncompressed) — documented for custom-skill
  uploads through the Claude API (platform.claude.com/docs/en/build-with-claude/skills-guide,
  read 2026-10-14). claude.ai's own uploader limit is not published (its help article only says
  "ZIP file exceeds size limits"), so applying the API figure to claude.ai is UNVERIFIED.
* ``CLAUDEAI_MAX_FILES`` (200 files) — UNVERIFIED. It comes from this repository's earlier
  release notes; no Anthropic source states a file-count limit. Kept as a conservative guard.
* ``name`` <= 64 chars, ``[a-z0-9-]``, no "anthropic"/"claude"; ``description`` <= 1024 chars —
  documented (platform.claude.com/docs/en/agents-and-tools/agent-skills/overview). The claude.ai
  help article "How to create custom skills" states a 200-character description limit; that
  conflicts with the platform docs, is not enforced here, and is UNVERIFIED.

The other targets have no platform limit; ``MAX_ARCHIVE_BYTES`` is this repository's own
regression ceiling (runaway bloat, an accidentally vendored binary), not a platform rule.

What is verified here vs. untested platform behaviour
-----------------------------------------------------
``verify`` (and the tests) check archive structure, sanitized frontmatter, presence of shared
and legal files, reference resolution inside the archive or install directory, determinism and
the limits above. Whether claude.ai accepts a given archive, and where claude.ai places
uploaded skills relative to each other (which decides whether a companion's ``../<skill>/``
path resolves there), have NOT been tested against the live service.

Usage::

    python3 scripts/build_bundles.py release [--out dist] [--version V] [--verify]
    python3 scripts/build_bundles.py verify dist/
    python3 scripts/build_bundles.py notes dist/release-manifest.json
    python3 scripts/build_bundles.py install --dest DIR [--dry-run] SKILL_DIR...
    python3 scripts/build_bundles.py sync-shared [--check]

Stdlib only; runs on Python 3.9+ so ``install.sh`` works on older systems.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
SHARED = SKILLS / "core" / "shared"
DIST = REPO / "dist"
PYPROJECT = REPO / "pyproject.toml"

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_claudeai_compat as cc  # noqa: E402  (frontmatter rules live there)

# Repository legal files shipped with every installed or packaged skill.
LEGAL_FILES = ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md")
# Top-level files of the plugin-marketplace snapshot (besides skills/, plugins/, .claude-plugin/).
COLLECTION_TOP_FILES = LEGAL_FILES + ("PROVENANCE.md", "README.md")

PLUGIN_ROOT_VAR = "${CLAUDE_PLUGIN_ROOT}"

# --- limits (see module docstring for sources) ---------------------------------------------
CLAUDEAI_MAX_UNCOMPRESSED_BYTES = 30_000_000  # documented for the Claude API upload
CLAUDEAI_MAX_FILES = 200  # UNVERIFIED conservative guard
NAME_MAX = 64
DESCRIPTION_MAX = 1024
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
RESERVED_NAME_WORDS = ("anthropic", "claude")
MAX_ARCHIVE_BYTES = 30 * 1024 * 1024  # repo regression ceiling for every archive

# Cruft never belongs in an install or archive.
EXCLUDE_DIR_NAMES = {"__pycache__", ".pytest_cache", ".ruff_cache"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}
EXCLUDE_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}

# Fixed mtime for every zip member (1980-01-01 00:00:00, the zip epoch floor).
FIXED_DATE_TIME = (1980, 1, 1, 0, 0, 0)

# Pre-existing content debt: path-shaped tokens in packaged markdown that do not name a file
# bundled with the skill. Most are illustrative paths in the user's own project (a training
# script, an analysis pipeline); a few cite files that never existed. They are not packaging
# defects, so verification tolerates exactly these (skill, reference) pairs — any NEW
# unresolved reference fails. tests/test_bundles.py fails when an entry starts resolving, so
# the list only shrinks. Fix path: bundle the file, or reword the token so it is not a path.
_UPSTREAM = "illustrative path in the upstream package's repository, not a bundled file"
_USER_PROJECT = "illustrative path in the user's own project, not a bundled file"
KNOWN_UNRESOLVED: dict[tuple[str, str], str] = {
    ("alterlab-hypogenic", "examples/generation.py"): _UPSTREAM,
    ("alterlab-hypogenic", "examples/inference.py"): _UPSTREAM,
    ("alterlab-hypogenic", "examples/multi_hyp_inference.py"): _UPSTREAM,
    ("alterlab-hypogenic", "examples/pdf_preprocess.py"): _UPSTREAM,
    ("alterlab-hypogenic", "examples/union_generation.py"): _UPSTREAM,
    ("alterlab-open-notebook", "examples/docker-compose-ollama.yml"): _UPSTREAM,
    ("alterlab-scgpt", "examples/finetune_integration.py"): _UPSTREAM,
    ("alterlab-open-science", "scripts/01_clean_data.R"): _USER_PROJECT,
    ("alterlab-open-science", "scripts/02_analysis.R"): _USER_PROJECT,
    ("alterlab-open-science", "scripts/03_figures.R"): _USER_PROJECT,
    ("alterlab-link-health", "../references/X.md"): "illustrative link in a sed recipe",
    ("alterlab-link-health", "../references/markdown_style_guide.md"):
        "illustrative link in a sed recipe",
    ("alterlab-parallel-web", "scripts/generate_schematic.py"):
        "commented-out call into alterlab-scientific-schematics without naming it",
    ("alterlab-scientific-slides", "scripts/inventory.py"):
        "DANGLING: pptx helper the skill cites but never bundled",
    ("alterlab-scientific-slides", "scripts/rearrange.py"):
        "DANGLING: pptx helper the skill cites but never bundled",
    ("alterlab-scientific-slides", "scripts/replace.py"):
        "DANGLING: pptx helper the skill cites but never bundled",
    ("alterlab-scientific-slides", "scripts/thumbnail.py"):
        "DANGLING: pptx helper the skill cites but never bundled",
    ("alterlab-research-workflows", "scripts/workflow_dryrun.mjs"):
        "repository-root maintainer script named in skills/workflows (owned elsewhere)",
    ("alterlab-skill-finder", "scripts/gen_skill_index.py"):
        "repository-root generator named in a generated header (fix in gen_skill_index.py)",
}


# ===========================================================================================
# Discovery
# ===========================================================================================

def domains() -> list[str]:
    """Sorted domain directory names under skills/ that hold at least one skill."""
    return sorted(d.name for d in SKILLS.iterdir() if d.is_dir() and any(d.glob("*/SKILL.md")))


def skill_dirs() -> list[Path]:
    """Every skill directory (one with a top-level SKILL.md), sorted by skill name."""
    return sorted((p.parent for p in SKILLS.glob("*/*/SKILL.md")), key=lambda d: d.name)


def skill_index() -> dict[str, Path]:
    return {d.name: d for d in skill_dirs()}


def domain_skill_dirs(domain: str) -> list[Path]:
    return sorted(p.parent for p in (SKILLS / domain).glob("*/SKILL.md"))


def read_version() -> str:
    """[project].version from pyproject.toml (the single source of truth)."""
    in_project = False
    for line in PYPROJECT.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            in_project = s == "[project]"
            continue
        m = re.match(r'version\s*=\s*"([^"]+)"', s) if in_project else None
        if m:
            return m.group(1)
    raise SystemExit("error: no [project].version in pyproject.toml")


def _excluded(rel: Path) -> bool:
    if rel.name in EXCLUDE_NAMES or rel.suffix in EXCLUDE_SUFFIXES:
        return True
    return any(part in EXCLUDE_DIR_NAMES for part in rel.parts)


def tree_files(root: Path) -> list[Path]:
    """All non-cruft files under *root*, sorted."""
    return sorted(p for p in root.rglob("*") if p.is_file() and not _excluded(p.relative_to(root)))


# ===========================================================================================
# References
# ===========================================================================================

_DOMAIN_ALT = "|".join(sorted((re.escape(d.name) for d in SKILLS.iterdir() if d.is_dir()),
                              key=len, reverse=True)) or "core"
# `skills/<domain>` anywhere that is not the tail of a longer path (`~/.claude/skills/x`).
REPO_LAYOUT_RE = re.compile(rf"(?<![\w./-])skills/(?:{_DOMAIN_ALT})(?![\w-])(?:/[\w.*\-]+)*/?")
LOCAL_DIRS = ("references", "shared", "schemas", "scripts", "agents", "commands", "assets",
              "examples", "templates")
_EXT = r"(?:md|json|py|js|mjs|sh|R|r|txt|ya?ml|csv|tsv|tex|bib|ipynb|html|toml|cfg|ini)"
REF_RE = re.compile(
    r"(?<![\w./$-])"
    r"(?P<lead>\$\{CLAUDE_PLUGIN_ROOT\}/|\.\./)?"
    r"(?:(?P<skill>alterlab-[a-z0-9-]+)/)?"
    rf"(?P<rel>(?:{'|'.join(LOCAL_DIRS)})/[\w.\-/]*?[\w\-]\.{_EXT})(?![\w/])"
)


_SKILL_NAME_RE = re.compile(r"alterlab-[a-z0-9-]+")


@dataclass(frozen=True)
class Ref:
    file: str  # posix path of the citing file, relative to the skill folder
    line: int
    raw: str  # the matched text
    lead: str  # "", "../" or "${CLAUDE_PLUGIN_ROOT}/"
    sibling: str  # sibling skill name, "" for a local reference
    rel: str  # path inside the (sibling) skill folder
    mentions: tuple[str, ...] = ()  # skill names on this line or the line before


def _skill_markdown(skill_dir: Path) -> list[Path]:
    """Markdown Claude may read from a skill folder (legal texts at its root excluded)."""
    out = []
    for p in tree_files(skill_dir):
        rel = p.relative_to(skill_dir)
        if p.suffix.lower() != ".md" or (len(rel.parts) == 1 and rel.name in LEGAL_FILES):
            continue
        out.append(p)
    return out


def iter_refs(skill_dir: Path) -> list[Ref]:
    refs: list[Ref] = []
    for md in _skill_markdown(skill_dir):
        rel_file = md.relative_to(skill_dir).as_posix()
        prev = ""
        for n, line in enumerate(md.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            line = REPO_LAYOUT_RE.sub(" ", line)  # reported separately; never a mention
            mentions = tuple(sorted(set(_SKILL_NAME_RE.findall(prev + " " + line))))
            for m in REF_RE.finditer(line):
                refs.append(Ref(rel_file, n, m.group(0), m.group("lead") or "",
                                m.group("skill") or "", m.group("rel"), mentions))
            prev = line
    return refs


def repo_layout_paths(skill_dir: Path) -> list[tuple[str, int, str]]:
    found = []
    for md in _skill_markdown(skill_dir):
        rel_file = md.relative_to(skill_dir).as_posix()
        for n, line in enumerate(md.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            found += [(rel_file, n, m.group(0)) for m in REPO_LAYOUT_RE.finditer(line)]
    return found


def placeholder_lines(skill_dir: Path) -> list[tuple[str, int]]:
    found = []
    for md in _skill_markdown(skill_dir):
        rel_file = md.relative_to(skill_dir).as_posix()
        for n, line in enumerate(md.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if PLUGIN_ROOT_VAR in line:
                found.append((rel_file, n))
    return found


def sibling_dependencies(skill_dir: Path, index: dict[str, Path] | None = None) -> set[str]:
    """Names of other skills whose files *skill_dir*'s markdown points into."""
    index = skill_index() if index is None else index
    return {r.sibling for r in iter_refs(skill_dir)
            if r.sibling and r.sibling != skill_dir.name and r.sibling in index}


def dependency_closure(names: list[str], index: dict[str, Path] | None = None) -> list[str]:
    """*names* plus every skill they transitively depend on, in first-seen order."""
    index = skill_index() if index is None else index
    seen: list[str] = []
    stack = list(reversed(names))
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.append(n)
        stack += sorted(sibling_dependencies(index[n], index) - set(seen), reverse=True)
    return seen


_KNOWN_NAMES: set[str] = set()


def _known_skill_names() -> set[str]:
    """Names of this repository's skills (names only — never used to resolve files)."""
    if not _KNOWN_NAMES:
        _KNOWN_NAMES.update(skill_index())
    return _KNOWN_NAMES


# Problem kinds that fail verification; "mention-absent" (a prose mention of a sibling skill
# that is not part of this install/archive) is informational only.
FATAL_KINDS = frozenset({"repo-layout", "placeholder", "unresolved", "missing-companion"})


def fatal(problems: list) -> list:
    return [p for p in problems if p.kind in FATAL_KINDS]


@dataclass(frozen=True)
class Problem:
    skill: str
    file: str
    line: int
    kind: str  # repo-layout | placeholder | unresolved | missing-companion | mention-absent
    detail: str

    def __str__(self) -> str:
        return f"{self.skill}/{self.file}:{self.line}: {self.kind}: {self.detail}"


def check_skill_refs(skill_dir: Path, *, plugin_root: Path | None = None,
                     abs_root: Path | None = None, allow_known: bool = True) -> list[Problem]:
    """Check every path reference in one installed/extracted skill folder.

    Resolution uses only the tree *skill_dir* lives in — never the repository checkout:
    local paths against *skill_dir*, sibling paths against ``skill_dir.parent``, and
    ``${CLAUDE_PLUGIN_ROOT}`` against *plugin_root* (plugin layout only; anywhere else an
    unrendered placeholder is a problem). With *abs_root* (plain install), absolute paths the
    installer wrote under that root must exist too.
    """
    name = skill_dir.name
    problems: list[Problem] = []
    for f, n, raw in repo_layout_paths(skill_dir):
        problems.append(Problem(name, f, n, "repo-layout", raw))
    if plugin_root is None:
        for f, n in placeholder_lines(skill_dir):
            problems.append(Problem(name, f, n, "placeholder", f"unrendered {PLUGIN_ROOT_VAR}"))
    for r in iter_refs(skill_dir):
        md_dir = (skill_dir / r.file).parent
        if r.lead == PLUGIN_ROOT_VAR + "/":
            if plugin_root is None:
                continue  # already reported as a placeholder
            sib_dir = plugin_root / r.sibling if r.sibling else None
            cands = [(sib_dir or plugin_root) / r.rel]
        elif r.sibling:
            sib_dir = skill_dir.parent / r.sibling
            cands = [sib_dir / r.rel]
            if r.lead == "../":  # also accept the markdown-link reading (relative to the file)
                cands.append(md_dir.parent / r.sibling / r.rel)
        elif r.lead == "../":
            sib_dir = None
            cands = [skill_dir.parent / r.rel, md_dir.parent / r.rel]
        else:
            sib_dir = None
            cands = [skill_dir / r.rel, md_dir / r.rel]
        if any(c.is_file() for c in cands):
            continue
        if sib_dir is not None and r.sibling != name and not sib_dir.is_dir():
            problems.append(Problem(name, r.file, r.line, "missing-companion", f"{r.raw} "
                                    f"(needs sibling skill {r.sibling})"))
            continue
        if not r.lead and not r.sibling and not r.rel.startswith("shared/"):
            # Prose mention: "`alterlab-x` (`scripts/y.py`)" — the convention audit_skills.py
            # resolves too. It resolves when the named sibling is present; it is never a
            # dependency, so an absent sibling is not a packaging defect. (In a full install
            # every sibling is present, so a dangling path cannot hide behind a mention.)
            # shared/ files are always the skill's own copy and never a mention.
            named = [s for s in r.mentions if s != name and s in _known_skill_names()]
            if any((skill_dir.parent / s / r.rel).is_file() for s in named):
                continue
            if any(not (skill_dir.parent / s).is_dir() for s in named):
                problems.append(Problem(name, r.file, r.line, "mention-absent", r.raw))
                continue
        if allow_known and (name, r.raw) in KNOWN_UNRESOLVED:
            continue
        problems.append(Problem(name, r.file, r.line, "unresolved", r.raw))
    if abs_root is not None:
        prefix = re.escape(abs_root.as_posix().rstrip("/") + "/")
        abs_re = re.compile(prefix + r"[\w.\-/]+")
        for md in _skill_markdown(skill_dir):
            rel_file = md.relative_to(skill_dir).as_posix()
            text = md.read_text(encoding="utf-8", errors="replace")
            for n, line in enumerate(text.splitlines(), 1):
                for m in abs_re.finditer(line):
                    if not Path(m.group(0).rstrip(".")).exists():
                        problems.append(Problem(name, rel_file, n, "unresolved", m.group(0)))
    return problems


# ===========================================================================================
# Shared resources (committed per-skill copies)
# ===========================================================================================

def shared_citations(skill_dir: Path) -> set[str]:
    """``shared/...`` paths a skill cites that exist in the canonical shared tree.

    Followed transitively through the cited shared files themselves."""
    wanted = {r.rel for r in iter_refs(skill_dir)
              if not r.sibling and not r.lead and r.rel.startswith("shared/")
              and (SHARED / r.rel[len("shared/"):]).is_file()}
    frontier = set(wanted)
    while frontier:
        nxt: set[str] = set()
        for rel in frontier:
            src = SHARED / rel[len("shared/"):]
            if src.suffix == ".md":
                for m in REF_RE.finditer(src.read_text(encoding="utf-8")):
                    r = m.group("rel")
                    if (not m.group("skill") and not m.group("lead") and r.startswith("shared/")
                            and (SHARED / r[len("shared/"):]).is_file() and r not in wanted):
                        nxt.add(r)
        wanted |= nxt
        frontier = nxt
    return wanted


def sync_shared(*, check: bool = False) -> list[str]:
    """Make every ``<skill>/shared/`` an exact copy of the shared files the skill cites.

    Returns the list of changes (``check=False``) or discrepancies (``check=True``)."""
    changes: list[str] = []
    for sd in skill_dirs():
        wanted = {sd / rel: SHARED / rel[len("shared/"):] for rel in shared_citations(sd)}
        present = set(tree_files(sd / "shared")) if (sd / "shared").is_dir() else set()
        for dest, src in sorted(wanted.items()):
            rel = dest.relative_to(REPO).as_posix()
            if dest.is_file() and dest.read_bytes() == src.read_bytes():
                continue
            changes.append(f"{'stale' if dest.is_file() else 'missing'}: {rel}")
            if not check:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dest)
        for extra in sorted(present - set(wanted)):
            changes.append(f"not cited (remove): {extra.relative_to(REPO).as_posix()}")
            if not check:
                extra.unlink()
        if not check and (sd / "shared").is_dir():
            for d in sorted((p for p in (sd / "shared").rglob("*") if p.is_dir()), reverse=True):
                if not any(d.iterdir()):
                    d.rmdir()
            if not any((sd / "shared").iterdir()):
                (sd / "shared").rmdir()
    return changes


# ===========================================================================================
# Rendering and members
# ===========================================================================================

@dataclass(frozen=True)
class Member:
    path: str  # posix path inside the install dir / archive
    data: bytes
    mode: int  # 0o644 or 0o755


def _mode(src: Path) -> int:
    return 0o755 if src.stat().st_mode & stat.S_IXUSR else 0o644


def render(rel: str, data: bytes, target: str, plugin_root_value: str) -> bytes:
    """Apply *target*'s transformation to one skill file (``rel`` is relative to the skill)."""
    if target == "plugin" or not rel.lower().endswith(".md"):
        return data
    text = data.decode("utf-8")
    text = text.replace(PLUGIN_ROOT_VAR, plugin_root_value)
    if target == "claudeai" and rel == "SKILL.md":
        text = cc.strip_non_whitelisted(text)
    return text.encode("utf-8")


def skill_members(skill_dir: Path, target: str, plugin_root_value: str, prefix: str) -> list[Member]:
    """Files of one skill for *target*, placed under *prefix* (e.g. ``"<name>/"``)."""
    members: list[Member] = []
    names = set()
    for f in tree_files(skill_dir):
        rel = f.relative_to(skill_dir).as_posix()
        names.add(rel)
        members.append(Member(prefix + rel, render(rel, f.read_bytes(), target, plugin_root_value),
                              _mode(f)))
    for legal in LEGAL_FILES:
        if legal in names:
            raise SystemExit(f"error: {skill_dir.name} ships its own {legal}; "
                             "rename it so the repository notice is not overwritten")
        members.append(Member(prefix + legal, (REPO / legal).read_bytes(), 0o644))
    return members


# ===========================================================================================
# Zip writing / reading
# ===========================================================================================

def write_zip(out: Path, members: list[Member]) -> Path:
    """Deterministic zip: sorted members, fixed mtimes, normalised modes, explicit dir entries."""
    out.parent.mkdir(parents=True, exist_ok=True)
    by_path: dict[str, Member] = {}
    for m in members:
        if m.path in by_path and by_path[m.path].data != m.data:
            raise SystemExit(f"error: conflicting contents for {m.path} in {out.name}")
        by_path[m.path] = m
    dirs = {"/".join(p.split("/")[:i]) + "/" for p in by_path for i in range(1, p.count("/") + 1)}
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in sorted(dirs | set(by_path)):
            info = zipfile.ZipInfo(filename=name, date_time=FIXED_DATE_TIME)
            info.create_system = 3  # Unix, so the mode bits below are honoured
            if name.endswith("/"):
                info.external_attr = (0o40755 << 16) | 0x10
                zf.writestr(info, b"")
                continue
            m = by_path[name]
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = ((0o100000 | m.mode) & 0xFFFF) << 16
            zf.writestr(info, m.data, compresslevel=9)
    return out


def safe_extract(archive: Path, dest: Path) -> Path:
    """Extract *archive* into *dest*, refusing absolute or parent-escaping member names."""
    dest.mkdir(parents=True, exist_ok=True)
    root = dest.resolve()
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            target = (dest / info.filename).resolve()
            if root != target and root not in target.parents:
                raise SystemExit(f"error: {archive.name}: member escapes the archive: {info.filename}")
        zf.extractall(dest)
    return dest


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ===========================================================================================
# Archives
# ===========================================================================================

def skill_archive_name(name: str, version: str) -> str:
    return f"skill-{name}-{version}.zip"


def domain_archive_name(domain: str, version: str) -> str:
    return f"alterlab-{domain}-{version}.zip"


def collection_archive_name(version: str) -> str:
    return f"alterlab-academic-skills-{version}.zip"


def build_skill_archive(skill_dir: Path, out_dir: Path, version: str) -> Path:
    """claude.ai upload archive: ``<name>/...`` only, sanitized frontmatter, notices inside."""
    name = skill_dir.name
    return write_zip(out_dir / skill_archive_name(name, version),
                     skill_members(skill_dir, "claudeai", "..", f"{name}/"))


def build_domain_archive(domain: str, out_dir: Path, version: str,
                         index: dict[str, Path] | None = None) -> Path:
    """Skills bundle: the domain's skills plus their dependency closure, skill folders at root."""
    index = skill_index() if index is None else index
    names = dependency_closure([d.name for d in domain_skill_dirs(domain)], index)
    members: list[Member] = []
    for n in names:
        members += skill_members(index[n], "skills-bundle", "..", f"{n}/")
    return write_zip(out_dir / domain_archive_name(domain, version), members)


def build_collection_archive(out_dir: Path, version: str) -> Path:
    """Plugin-marketplace snapshot: verbatim ``.claude-plugin/``, ``skills/``, ``plugins/``."""
    members: list[Member] = []
    for top in (".claude-plugin", "skills", "plugins"):
        for f in tree_files(REPO / top):
            members.append(Member(f.relative_to(REPO).as_posix(), f.read_bytes(), _mode(f)))
    for name in COLLECTION_TOP_FILES:
        members.append(Member(name, (REPO / name).read_bytes(), 0o644))
    return write_zip(out_dir / collection_archive_name(version), members)


def build_release(out_dir: Path, version: str) -> dict:
    """Build every release archive into *out_dir*; write and return the manifest."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in out_dir.glob("*.zip"):
        stale.unlink()
    index = skill_index()
    records: list[dict] = []
    for sd in skill_dirs():
        p = build_skill_archive(sd, out_dir, version)
        records.append({"archive": p.name, "target": "claudeai", "skills": [sd.name],
                        "companions": sorted(set(dependency_closure([sd.name], index)) - {sd.name})})
    for dom in domains():
        p = build_domain_archive(dom, out_dir, version, index)
        own = [d.name for d in domain_skill_dirs(dom)]
        records.append({"archive": p.name, "target": "skills-bundle", "domain": dom,
                        "skills": sorted(dependency_closure(own, index)),
                        "dependencies_included": sorted(set(dependency_closure(own, index)) - set(own))})
    p = build_collection_archive(out_dir, version)
    records.append({"archive": p.name, "target": "plugin", "skills": sorted(index)})
    for rec in records:
        path = out_dir / rec["archive"]
        with zipfile.ZipFile(path) as zf:
            infos = [i for i in zf.infolist() if not i.is_dir()]
        rec.update({"files": len(infos), "bytes": path.stat().st_size,
                    "uncompressed_bytes": sum(i.file_size for i in infos), "sha256": _sha256(path)})
    manifest = {"version": version, "archives": sorted(records, key=lambda r: r["archive"])}
    (out_dir / "release-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                                    encoding="utf-8")
    return manifest


# ===========================================================================================
# Verification of built archives (reads only the archives)
# ===========================================================================================

def _frontmatter(text: str) -> dict[str, str]:
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    fm: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line and line[0] not in " \t#" and ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


def _check_legal(skill_dir: Path, label: str) -> list[str]:
    return [f"{label}: missing {legal}" for legal in LEGAL_FILES if not (skill_dir / legal).is_file()]


def _check_shared(skill_dir: Path, label: str) -> list[str]:
    """Every ``shared/...`` the packaged skill cites is present inside the packaged skill."""
    return [f"{label}: cites {r.rel} but the archive has no {skill_dir.name}/{r.rel}"
            for r in iter_refs(skill_dir)
            if not r.sibling and not r.lead and r.rel.startswith("shared/")
            and not (skill_dir / r.rel).is_file()]


def verify_skill_archive(path: Path, work: Path, name: str,
                         companions: list[Path] | None = None) -> list[str]:
    """Problems with one claude.ai archive (empty list == valid).

    *companions* are the archives of the skills this one depends on; they are extracted next
    to it (as if uploaded side by side) so sibling paths are resolved against their contents.
    Without them, sibling paths are reported only through the manifest's companion list."""
    problems: list[str] = []
    with zipfile.ZipFile(path) as zf:
        if zf.testzip() is not None:
            return [f"{path.name}: corrupt member"]
        infos = zf.infolist()
    files = [i for i in infos if not i.is_dir()]
    tops = {i.filename.split("/", 1)[0] for i in infos}
    if tops != {name}:
        problems.append(f"{path.name}: archive root must be exactly one folder {name}/, got {sorted(tops)}")
    if len(files) > CLAUDEAI_MAX_FILES:
        problems.append(f"{path.name}: {len(files)} files > {CLAUDEAI_MAX_FILES} (unverified guard)")
    size = sum(i.file_size for i in files)
    if size >= CLAUDEAI_MAX_UNCOMPRESSED_BYTES:
        problems.append(f"{path.name}: {size} uncompressed bytes >= {CLAUDEAI_MAX_UNCOMPRESSED_BYTES}")
    root = safe_extract(path, work)
    for comp in companions or []:
        safe_extract(comp, work)
    sd = root / name
    skill_md = sd / "SKILL.md"
    if not skill_md.is_file():
        return problems + [f"{path.name}: no {name}/SKILL.md"]
    text = skill_md.read_text(encoding="utf-8")
    extra = [k for k in cc.top_level_keys(skill_md) if k not in cc.CLAUDEAI_WHITELIST]
    if extra:
        problems.append(f"{path.name}: non-whitelisted frontmatter keys {extra}")
    fm = _frontmatter(text)
    if fm.get("name") != name:
        problems.append(f"{path.name}: frontmatter name {fm.get('name')!r} != folder {name!r}")
    if not (len(name) <= NAME_MAX and NAME_RE.match(name)
            and not any(w in name for w in RESERVED_NAME_WORDS)):
        problems.append(f"{path.name}: name {name!r} violates the documented name rules")
    if not fm.get("description") or len(fm["description"]) > DESCRIPTION_MAX:
        problems.append(f"{path.name}: description empty or > {DESCRIPTION_MAX} chars")
    problems += _check_legal(sd, path.name)
    problems += _check_shared(sd, path.name)
    problems += [f"{path.name}: {p}" for p in fatal(check_skill_refs(sd))
                 if companions is not None or p.kind != "missing-companion"]
    return problems


def verify_domain_archive(path: Path, work: Path) -> list[str]:
    with zipfile.ZipFile(path) as zf:
        if zf.testzip() is not None:
            return [f"{path.name}: corrupt member"]
    problems: list[str] = []
    if path.stat().st_size >= MAX_ARCHIVE_BYTES:
        problems.append(f"{path.name}: {path.stat().st_size} bytes >= repo ceiling {MAX_ARCHIVE_BYTES}")
    root = safe_extract(path, work)
    loose = [p.name for p in root.iterdir() if not (p / "SKILL.md").is_file()]
    if loose:
        problems.append(f"{path.name}: archive root holds non-skill entries {loose}")
    for sd in sorted(p for p in root.iterdir() if (p / "SKILL.md").is_file()):
        problems += _check_legal(sd, f"{path.name}:{sd.name}")
        problems += _check_shared(sd, f"{path.name}:{sd.name}")
        problems += [f"{path.name}: {p}" for p in fatal(check_skill_refs(sd))]
    return problems


def verify_collection_archive(path: Path, work: Path) -> list[str]:
    """Plugin layout: each marketplace plugin's source dir is checked as its own plugin root."""
    with zipfile.ZipFile(path) as zf:
        if zf.testzip() is not None:
            return [f"{path.name}: corrupt member"]
    problems: list[str] = []
    if path.stat().st_size >= MAX_ARCHIVE_BYTES:
        problems.append(f"{path.name}: {path.stat().st_size} bytes >= repo ceiling {MAX_ARCHIVE_BYTES}")
    root = safe_extract(path, work)
    problems += [f"{path.name}: missing {n}" for n in COLLECTION_TOP_FILES if not (root / n).is_file()]
    mp = root / ".claude-plugin" / "marketplace.json"
    if not mp.is_file():
        return problems + [f"{path.name}: missing .claude-plugin/marketplace.json"]
    all_skills = {p.parent.name for p in root.glob("skills/*/*/SKILL.md")}
    for entry in json.loads(mp.read_text(encoding="utf-8"))["plugins"]:
        src = root / entry["source"]
        if not src.is_dir():
            problems.append(f"{path.name}: plugin {entry['name']} source {entry['source']} missing")
            continue
        for sd in sorted(p.parent for p in src.glob("*/SKILL.md")):
            for p in fatal(check_skill_refs(sd, plugin_root=src)):
                # A prose/`../` path into a skill of another domain points into a different
                # plugin: not addressable by path in the plugin layout, so it is accepted only
                # when that skill exists in the marketplace. ${CLAUDE_PLUGIN_ROOT} paths must
                # always resolve inside their own plugin.
                needed = re.search(r"needs sibling skill (\S+)\)$", p.detail)
                if (p.kind == "missing-companion" and needed and needed.group(1) in all_skills
                        and not p.detail.startswith(PLUGIN_ROOT_VAR)):
                    continue
                problems.append(f"{path.name}: {p}")
    return problems


def verify_release(out_dir: Path, work: Path) -> list[str]:
    """Verify every archive listed in *out_dir*/release-manifest.json."""
    manifest = json.loads((out_dir / "release-manifest.json").read_text(encoding="utf-8"))
    problems: list[str] = []
    listed = {r["archive"] for r in manifest["archives"]}
    on_disk = {p.name for p in out_dir.glob("*.zip")}
    if listed != on_disk:
        problems.append(f"manifest/archives mismatch: {sorted(listed ^ on_disk)}")
    for i, rec in enumerate(manifest["archives"]):
        path = out_dir / rec["archive"]
        w = work / f"{i:04d}"
        if rec["target"] == "claudeai":
            comps = [out_dir / skill_archive_name(c, manifest["version"]) for c in rec["companions"]]
            missing = [c.name for c in comps if c.name not in on_disk]
            if missing:
                problems.append(f"{path.name}: companion archive(s) not in this release: {missing}")
                comps = None
            problems += verify_skill_archive(path, w, rec["skills"][0], comps)
        elif rec["target"] == "skills-bundle":
            problems += verify_domain_archive(path, w)
        else:
            problems += verify_collection_archive(path, w)
        if _sha256(path) != rec["sha256"]:
            problems.append(f"{path.name}: sha256 does not match the manifest")
    return problems


def release_notes(manifest: dict) -> str:
    """Markdown describing the attached archives (used by release.yml)."""
    v = manifest["version"]
    lines = [
        "**Attached archives** (built and verified by `scripts/build_bundles.py`; "
        "sizes and SHA-256 sums are in `release-manifest.json`):",
        "",
        f"- `skill-<name>-{v}.zip` — one skill per archive, the skill folder at the archive root, "
        "frontmatter reduced to the claude.ai upload whitelist, shared handoff files and license "
        "notices inside. For the Claude app: **Customize ▸ Skills → Upload a skill**. Packaging "
        "is tested; acceptance by the live claude.ai uploader is not.",
        f"- `alterlab-<domain>-{v}.zip` — every skill of one domain plus the skills they depend "
        "on, skill folders at the archive root: unzip into `~/.claude/skills/` (or "
        "`~/.agents/skills/`). Plugin-only components (MCP servers, hooks, dynamic-workflow "
        "scripts) are not in it — install the plugin for those. Not a claude.ai upload: the "
        "claude.ai help center describes an upload as a ZIP whose root is a single skill folder.",
        f"- `alterlab-academic-skills-{v}.zip` — the plugin marketplace snapshot "
        "(`.claude-plugin/`, `skills/`, `plugins/`): `/plugin marketplace add <unzipped folder>`.",
    ]
    needs = [r for r in manifest["archives"] if r["target"] == "claudeai" and r["companions"]]
    if needs:
        lines += ["", "Skills whose instructions call files in another skill — upload the "
                  "companion archives too:", ""]
        lines += [f"- `{r['skills'][0]}` → " + ", ".join(f"`{c}`" for c in r["companions"])
                  for r in needs]
    return "\n".join(lines) + "\n"


# ===========================================================================================
# Plain install
# ===========================================================================================

def install(selected: list[Path], dest: Path, *, dry_run: bool = False,
            with_dependencies: bool = True, log=print) -> list[str]:
    """Install *selected* skill dirs (plus dependencies) into *dest*; return installed names.

    Idempotent: each target skill folder is replaced wholesale. ``${CLAUDE_PLUGIN_ROOT}`` in
    skill markdown is written out as the absolute *dest* (the folder holding the sibling
    skills) — what Claude Code substitutes for a plugin, here for a plain skills directory."""
    index = skill_index()
    dest = dest.expanduser()
    dest_abs = dest.resolve()
    if dest_abs == SKILLS.resolve() or SKILLS.resolve() in dest_abs.parents:
        raise SystemExit(f"error: refusing to install into the source tree ({dest})")
    names = [d.name for d in selected]
    unknown = [d for d in selected if d.name not in index or index[d.name].resolve() != d.resolve()]
    if unknown:
        raise SystemExit(f"error: not a skill of this repository: {unknown[0]}")
    order = dependency_closure(names, index) if with_dependencies else names
    for n in order:
        if n not in names:
            log(f"  + {n} (dependency)")
    if dry_run:
        for n in order:
            log(f"would install {n} -> {dest / n}")
        return order
    dest.mkdir(parents=True, exist_ok=True)
    for n in order:
        target = dest / n
        if target.is_symlink() or target.is_file():
            target.unlink()
        elif target.exists():
            shutil.rmtree(target)
        for m in skill_members(index[n], "install", dest_abs.as_posix(), ""):
            out = target / m.path
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(m.data)
            os.chmod(out, m.mode)
    return order


def materialize(out_dir: Path, target: str = "claudeai", *, layout: str = "domain") -> int:
    """Write every skill rendered for *target* as a plain tree (``check_claudeai_compat --package``).

    ``layout="domain"`` writes ``OUT/<domain>/<skill>/``; ``"flat"`` writes ``OUT/<skill>/``.
    Sibling paths are written relative to the skill folder, so use ``flat`` when siblings must
    resolve."""
    n = 0
    for sd in skill_dirs():
        base = out_dir / sd.parent.name if layout == "domain" else out_dir
        target_dir = base / sd.name
        if target_dir.exists():
            shutil.rmtree(target_dir)
        for m in skill_members(sd, target, "..", ""):
            p = target_dir / m.path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(m.data)
            os.chmod(p, m.mode)
        n += 1
    return n


# ===========================================================================================
# CLI
# ===========================================================================================

def _summary_table(manifest: dict) -> str:
    rows = [(r["archive"], r["target"], r["files"], r["bytes"]) for r in manifest["archives"]]
    w = max(len(r[0]) for r in rows)
    out = [f"{'archive'.ljust(w)}  {'target':13}  {'files':>5}  {'bytes':>9}"]
    out += [f"{a.ljust(w)}  {t:13}  {f:>5}  {b:>9}" for a, t, f, b in rows]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd")

    p_rel = sub.add_parser("release", help="build every release archive + release-manifest.json")
    p_rel.add_argument("--out", type=Path, default=DIST)
    p_rel.add_argument("--version", default=None, help="default: pyproject [project].version")
    p_rel.add_argument("--verify", action="store_true", help="verify the archives after building")
    p_rel.add_argument("--work", type=Path, default=None, help="scratch dir for --verify")

    p_ver = sub.add_parser("verify", help="verify archives listed in <dir>/release-manifest.json")
    p_ver.add_argument("dir", type=Path)
    p_ver.add_argument("--work", type=Path, default=None)

    p_notes = sub.add_parser("notes", help="print release-notes markdown for a manifest")
    p_notes.add_argument("manifest", type=Path)

    p_inst = sub.add_parser("install", help="plain install of skill dirs (+ dependencies)")
    p_inst.add_argument("--dest", type=Path, required=True)
    p_inst.add_argument("--dry-run", action="store_true")
    p_inst.add_argument("--no-deps", action="store_true", help="do not add dependency skills")
    p_inst.add_argument("skills", nargs="+", type=Path)

    p_sync = sub.add_parser("sync-shared", help="refresh the per-skill shared/ copies")
    p_sync.add_argument("--check", action="store_true", help="report drift, change nothing")

    args = ap.parse_args(argv)

    if args.cmd in (None, "release"):
        out = getattr(args, "out", DIST)
        version = getattr(args, "version", None) or read_version()
        manifest = build_release(out, version)
        print(_summary_table(manifest))
        print(f"\nbuilt {len(manifest['archives'])} archives into {out}")
        if getattr(args, "verify", False):
            return _run_verify(out, getattr(args, "work", None))
        return 0
    if args.cmd == "verify":
        return _run_verify(args.dir, args.work)
    if args.cmd == "notes":
        sys.stdout.write(release_notes(json.loads(args.manifest.read_text(encoding="utf-8"))))
        return 0
    if args.cmd == "install":
        installed = install([p.resolve() for p in args.skills], args.dest, dry_run=args.dry_run,
                            with_dependencies=not args.no_deps)
        verb = "would install" if args.dry_run else "installed"
        print(f"\n{verb} {len(installed)} skill(s) into {args.dest}")
        return 0
    if args.cmd == "sync-shared":
        changes = sync_shared(check=args.check)
        for c in changes:
            print(("DRIFT " if args.check else "") + c)
        if args.check and changes:
            print("run: python3 scripts/build_bundles.py sync-shared", file=sys.stderr)
            return 1
        print(f"{'checked' if args.check else 'synced'} per-skill shared/ copies "
              f"({len(changes)} change(s)).")
        return 0
    return 2


def _run_verify(out: Path, work: Path | None) -> int:
    import tempfile

    with tempfile.TemporaryDirectory(prefix="alterlab-verify-") as tmp:
        problems = verify_release(out, Path(work) if work else Path(tmp))
    if problems:
        print(f"\n{len(problems)} problem(s):", file=sys.stderr)
        for p in problems:
            print(f"  FAIL {p}", file=sys.stderr)
        return 1
    print("verified: structure, frontmatter, shared + legal files, references, limits.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
