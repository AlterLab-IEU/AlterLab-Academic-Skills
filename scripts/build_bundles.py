#!/usr/bin/env python3
"""Build one distributable zip per domain into ``dist/<domain>.zip``.

Each bundle is **self-contained**: alongside the domain's own ``skills/<domain>/``
tree it vendors a copy of ``skills/core/shared/`` (the JSON Schemas plus
``model_env.md`` / ``handoff_schemas.md``). Skills cross-reference that shared
tree by its repo-relative path, e.g.::

    # Model ID via the ALTERLAB_MODEL convention (skills/core/shared/model_env.md):

so the vendored copy is written under the SAME path inside the zip
(``skills/core/shared/...``). That makes every such reference resolve when a
consumer unzips a single domain bundle on its own — no other domain needed.

The ``core`` domain already *contains* ``skills/core/shared/`` (it owns it), so
for that one bundle the shared tree is not vendored a second time.

## Determinism

Re-running this script on an unchanged tree produces byte-identical zips:

* members are added in sorted (path) order;
* every member's mtime is pinned to a fixed epoch (no wall-clock leakage);
* Unix permission bits are normalised (0644 files / 0755 dirs);
* a fixed deflate level is used and the "extended local header" flag is off.

This keeps release artifacts diffable and lets CI cache / compare them.

## Verify

``--verify`` re-reads each freshly built zip and asserts hard safety ceilings,
then reports the per-bundle size + file-count table. See ``MAX_SIZE_BYTES`` /
``WARN_*`` below for the exact thresholds and why the 200-file bound is a loud
warning rather than a hard failure for two legitimately large domains.

Usage::

    uv run python scripts/build_bundles.py                 # build all domain bundles
    uv run python scripts/build_bundles.py --verify        # build, then assert + report
    uv run python scripts/build_bundles.py --clean         # remove dist/ first
    uv run python scripts/build_bundles.py --skills        # + one zip per skill in dist/skills/
    uv run python scripts/build_bundles.py --skills-only   # ONLY the per-skill zips
"""
from __future__ import annotations

import argparse
import shutil
import stat
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
SHARED = SKILLS / "core" / "shared"
DIST = REPO / "dist"
# Per-skill single-skill bundles land here (one zip per skill), structured so the
# claude.ai "Customize ▸ Skills → Upload a skill" uploader accepts them directly:
# each zip contains the skill folder at its top level (``<name>/SKILL.md`` …).
SKILLS_DIST = DIST / "skills"

# --- thresholds -------------------------------------------------------------
# Hard ceiling: a bundle larger than this is a build error (runaway bloat /
# accidentally-vendored binary). Comfortably above the observed ~1MB-compressed
# worst case, so it only ever fires on a genuine regression.
MAX_SIZE_BYTES = 30 * 1024 * 1024  # 30 MB — HARD fail

# Soft expectations (loud WARNING, non-fatal). Real-world counts: two domains
# (databases ~39 skills, data-science ~22 skills, both with rich references/
# examples) legitimately exceed 200 files even before the ~14-file shared vendor.
# Making 200 a hard fail would break a valid release, so it is surfaced loudly
# instead. The size expectation is comfortably met by every domain today.
WARN_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB  — expect under this
WARN_FILE_COUNT = 200  # files — expect under this

# Cruft never belongs in a distributable bundle.
EXCLUDE_DIR_NAMES = {"__pycache__"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}
EXCLUDE_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}

# Fixed mtime for every zip member (1980-01-01 00:00:00, the zip epoch floor).
FIXED_DATE_TIME = (1980, 1, 1, 0, 0, 0)


def domains() -> list[str]:
    """Return the sorted list of domain directory names under skills/."""
    return sorted(d.name for d in SKILLS.iterdir() if d.is_dir())


def skill_dirs() -> list[Path]:
    """Every skill directory (one containing a top-level ``SKILL.md``), sorted by name.

    Discovery is by ``SKILL.md`` presence — the same rule the rest of the tooling
    uses — so shared/support trees (e.g. ``skills/core/shared/``) are ignored.
    """
    return sorted((p.parent for p in SKILLS.rglob("SKILL.md")), key=lambda d: d.name)


def _excluded(path: Path) -> bool:
    """True if *path* (a file) is cruft that must not enter a bundle."""
    if path.name in EXCLUDE_NAMES:
        return True
    if path.suffix in EXCLUDE_SUFFIXES:
        return True
    return any(part in EXCLUDE_DIR_NAMES for part in path.parts)


def _collect(root: Path) -> list[Path]:
    """All non-excluded files under *root*, returned absolute, sorted."""
    files = [p for p in root.rglob("*") if p.is_file() and not _excluded(p)]
    return sorted(files)


def _add(zf: zipfile.ZipFile, src: Path, arcname: str, seen: set[str]) -> None:
    """Add *src* to *zf* under *arcname* with deterministic metadata."""
    if arcname in seen:
        return  # never write the same member twice (shared vendored once)
    seen.add(arcname)
    data = src.read_bytes()
    info = zipfile.ZipInfo(filename=arcname, date_time=FIXED_DATE_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    # Normalise perms: 0755 for executable-by-owner, else 0644. The high 16 bits
    # of external_attr carry the Unix mode.
    mode = 0o755 if (src.stat().st_mode & stat.S_IXUSR) else 0o644
    info.external_attr = (mode & 0o7777) << 16
    zf.writestr(info, data, compresslevel=9)


def build_one(domain: str) -> Path:
    """Build dist/<domain>.zip and return its path."""
    DIST.mkdir(parents=True, exist_ok=True)
    out = DIST / f"{domain}.zip"
    seen: set[str] = set()

    # 1) the domain's own tree, archived under skills/<domain>/...
    domain_root = SKILLS / domain
    members: list[tuple[Path, str]] = []
    for f in _collect(domain_root):
        arc = f.relative_to(REPO).as_posix()  # skills/<domain>/...
        members.append((f, arc))

    # 2) vendor skills/core/shared/ under its real repo path so that
    #    "skills/core/shared/..." cross-references resolve self-contained.
    #    The 'core' domain already owns that tree, so skip the duplicate there.
    if domain != "core":
        for f in _collect(SHARED):
            arc = f.relative_to(REPO).as_posix()  # skills/core/shared/...
            members.append((f, arc))

    # Sort by archive name for byte-stable ordering across runs.
    members.sort(key=lambda t: t[1])

    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for src, arc in members:
            _add(zf, src, arc, seen)

    return out


def build_skill(skill_dir: Path, out_dir: Path = SKILLS_DIST) -> Path:
    """Build ``<out_dir>/<name>.zip`` for a single skill and return its path.

    The archive contains the skill folder at its top level (``<name>/SKILL.md``,
    ``<name>/references/…``, ``<name>/scripts/…``) — exactly the shape the
    claude.ai "Upload a skill" flow expects, so a non-technical user can download
    one file and upload it as-is. Uses the same deterministic member metadata as
    the domain bundles, so re-runs are byte-identical.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    name = skill_dir.name
    out = out_dir / f"{name}.zip"
    seen: set[str] = set()

    members: list[tuple[Path, str]] = []
    for f in _collect(skill_dir):
        arc = f"{name}/{f.relative_to(skill_dir).as_posix()}"
        members.append((f, arc))
    members.sort(key=lambda t: t[1])

    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for src, arc in members:
            _add(zf, src, arc, seen)

    return out


def verify_skill(path: Path) -> tuple[int, int, list[str]]:
    """Re-read a per-skill zip; return (size_bytes, file_count, problems).

    A valid single-skill bundle must be intact and carry its ``SKILL.md`` at the
    top level of the archived folder (``<name>/SKILL.md``) so the uploader finds it.
    """
    size = path.stat().st_size
    problems: list[str] = []
    with zipfile.ZipFile(path) as zf:
        bad = zf.testzip()
        if bad is not None:
            problems.append(f"HARD: corrupt member {bad!r}")
        names = zf.namelist()
    count = len(names)

    if f"{path.stem}/SKILL.md" not in names:
        problems.append(f"HARD: missing {path.stem}/SKILL.md at archive top level")
    if size >= MAX_SIZE_BYTES:
        problems.append(f"HARD: {size / 1e6:.2f}MB exceeds {MAX_SIZE_BYTES / 1e6:.0f}MB ceiling")

    return size, count, problems


def build_all_skills(out_dir: Path = SKILLS_DIST) -> list[Path]:
    """Build every per-skill zip into *out_dir*; return the sorted list of paths."""
    return [build_skill(d, out_dir) for d in skill_dirs()]


def verify_one(path: Path) -> tuple[int, int, list[str]]:
    """Re-read *path*; return (size_bytes, file_count, problems).

    A non-empty ``problems`` list with a HARD entry means the build must fail.
    Soft expectation breaches are prefixed ``WARN``.
    """
    size = path.stat().st_size
    problems: list[str] = []

    with zipfile.ZipFile(path) as zf:
        bad = zf.testzip()
        if bad is not None:
            problems.append(f"HARD: corrupt member {bad!r}")
        names = zf.namelist()
    count = len(names)

    # Self-containment sanity: a non-core bundle must carry the shared tree.
    if path.stem != "core":
        if not any(n.startswith("skills/core/shared/") for n in names):
            problems.append("HARD: missing vendored skills/core/shared/ tree")

    if size >= MAX_SIZE_BYTES:
        problems.append(f"HARD: {size / 1e6:.2f}MB exceeds {MAX_SIZE_BYTES / 1e6:.0f}MB ceiling")
    elif size >= WARN_SIZE_BYTES:
        problems.append(f"WARN: {size / 1e6:.2f}MB exceeds {WARN_SIZE_BYTES / 1e6:.0f}MB expectation")

    if count >= WARN_FILE_COUNT:
        problems.append(f"WARN: {count} files exceeds {WARN_FILE_COUNT}-file expectation")

    return size, count, problems


def _fmt_mb(n: int) -> str:
    return f"{n / 1e6:.2f}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verify", action="store_true", help="re-read each bundle, assert ceilings, print a report")
    ap.add_argument("--clean", action="store_true", help="remove dist/ before building")
    ap.add_argument("--skills", action="store_true",
                    help="also build one zip per skill into dist/skills/ (for the claude.ai uploader)")
    ap.add_argument("--skills-only", action="store_true",
                    help="build ONLY the per-skill zips (implies --skills), skipping domain bundles")
    args = ap.parse_args()

    if args.clean and DIST.exists():
        shutil.rmtree(DIST)

    built: list[Path] = []
    if not args.skills_only:
        for d in domains():
            built.append(build_one(d))
        print(f"Built {len(built)} domain bundle(s) into {DIST.relative_to(REPO)}/")

    skill_built: list[Path] = []
    if args.skills or args.skills_only:
        skill_built = build_all_skills()
        print(f"Built {len(skill_built)} per-skill bundle(s) into {SKILLS_DIST.relative_to(REPO)}/")

    if not args.verify:
        for p in built:
            print(f"  {p.name}")
        if skill_built:
            print(f"  … + {len(skill_built)} per-skill zips in {SKILLS_DIST.relative_to(REPO)}/")
        return 0

    # --- verify + report -----------------------------------------------------
    rows: list[tuple[str, int, int, list[str]]] = []
    hard_failures: list[str] = []
    warnings: list[str] = []
    for p in built:
        size, count, problems = verify_one(p)
        rows.append((p.name, size, count, problems))
        for pr in problems:
            if pr.startswith("HARD"):
                hard_failures.append(f"{p.name}: {pr}")
            else:
                warnings.append(f"{p.name}: {pr}")

    if rows:
        name_w = max(len(r[0]) for r in rows)
        print()
        print(f"{'bundle'.ljust(name_w)}  {'size(MB)':>8}  {'files':>5}  status")
        print(f"{'-' * name_w}  {'-' * 8}  {'-' * 5}  {'-' * 6}")
        for name, size, count, problems in sorted(rows):
            if any(pr.startswith('HARD') for pr in problems):
                status = "FAIL"
            elif problems:
                status = "warn"
            else:
                status = "ok"
            print(f"{name.ljust(name_w)}  {_fmt_mb(size):>8}  {count:>5}  {status}")

    # Per-skill zips are many (one per skill); summarise rather than list each.
    if skill_built:
        skill_hard = 0
        biggest = 0
        for p in skill_built:
            size, _count, problems = verify_skill(p)
            biggest = max(biggest, size)
            for pr in problems:
                if pr.startswith("HARD"):
                    skill_hard += 1
                    hard_failures.append(f"skills/{p.name}: {pr}")
        print(f"\nPer-skill zips: {len(skill_built)} built, {len(skill_built) - skill_hard} "
              f"valid (largest {_fmt_mb(biggest)}MB); each carries <name>/SKILL.md at top level.")

    if warnings:
        print(f"\n{len(warnings)} expectation warning(s) (non-fatal):")
        for w in warnings:
            print(f"  WARN {w}")

    if hard_failures:
        print(f"\n{len(hard_failures)} HARD failure(s):", file=sys.stderr)
        for f in hard_failures:
            print(f"  FAIL {f}", file=sys.stderr)
        return 1

    total = len(built) + len(skill_built)
    print(f"\nAll {total} bundles within hard ceilings "
          f"(<{MAX_SIZE_BYTES // (1024 * 1024)}MB, intact, self-contained).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
