#!/usr/bin/env python3
"""Generate the repo-root ``skills.json`` catalog from the ``skills/`` tree.

Walks every ``skills/<domain>/<skill>/SKILL.md``, parses its YAML frontmatter,
and emits a flat, machine-readable inventory of the suite: one record per skill
plus a ``summary`` block. The catalog is the single structured source other
tooling (and humans) can query for "how many skills, in which domains, with what
eval coverage" without re-walking the tree or re-parsing 180+ markdown files.

## What a skill record contains

For each skill (a directory that contains a ``SKILL.md``):

* ``name``           - frontmatter ``name`` (== leaf dir name by convention)
* ``domain``         - the ``skills/<domain>/`` folder it lives under
* ``description``    - frontmatter ``description`` (the trigger text)
* ``license``        - frontmatter ``license``
* ``version``        - frontmatter ``metadata.version`` (nested; AlterLab convention)
* ``compatibility``  - frontmatter top-level ``compatibility`` (null if absent)
* ``allowed_tools``  - frontmatter ``allowed-tools``, split into a list of tokens
* ``has_scripts``    - whether a non-empty ``scripts/`` dir ships with the skill
* ``has_evals``      - whether ``evals/evals.json`` exists (the eval marker)
* ``body_lines``     - line count of the SKILL.md body (after frontmatter)
* ``references``     - sorted list of files under the skill's ``references/`` dir
                       (relative to that dir), e.g. ``["api.md", "workflow.md"]``

## The summary block

* ``version``        - the suite version, read from ``pyproject.toml`` ``[project].version``
                       (the release tag is ``v<version>``; the catalog site builds
                       per-skill install links from it)
* ``generated_at``   - ISO date (not time) the catalog file was last written
* ``total``          - number of skills discovered (load-bearing: README counts)
* ``per_domain``     - {domain: count} map
* ``eval_coverage``  - {with_evals, without_evals, total, fraction} for evals.json

## --check mode (CI gate)

Regenerates the catalog to memory and:
  1. diffs it against the committed ``skills.json`` (fails on drift) — with the
     committed ``summary.generated_at`` carried over, so the date stamp alone can
     never fail the gate (it only refreshes when the file is actually rewritten), AND
  2. tolerantly extracts the skill count printed in ``README.md`` and
     ``README.tr-TR.md`` and verifies it equals ``summary.total``.

The README extraction is deliberately tolerant: it scans for any integer that
appears next to a skill-count signal (a badge like ``Skills-180``/``Beceri-180``,
or a number adjacent to the words "skill"/"beceri"). It collects every such
candidate and requires the catalog total to be among them, so cosmetic prose
changes elsewhere in the README do not break CI, but a stale headline count does.

Regenerate after adding/removing/moving skills:  uv run python scripts/gen_catalog.py
Verify it is up to date + READMEs agree (CI):     uv run python scripts/gen_catalog.py --check
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
OUT = REPO / "skills.json"
README = REPO / "README.md"
README_TR = REPO / "README.tr-TR.md"
PYPROJECT = REPO / "pyproject.toml"


def read_version() -> str | None:
    """``[project].version`` from pyproject.toml — the single source of truth
    (release.yml and gen_marketplace.py read the same field). None if absent."""
    if not PYPROJECT.is_file():
        return None
    try:
        return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]
    except (tomllib.TOMLDecodeError, KeyError, TypeError):
        return None


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Naive YAML frontmatter parser — flat keys + one indented ``metadata`` block.

    Mirrors scripts/audit_skills.py so the catalog and the auditor agree on what
    a field "is". Returns (frontmatter dict, body). Nested keys under a block are
    flattened as ``block.key`` (e.g. ``metadata.version``). Returns ({}, text) if
    there is no frontmatter.
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, text
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return {}, text

    fm: dict[str, str] = {}
    current_block_key: str | None = None
    for line in lines[1:end_idx]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z][A-Za-z0-9_-]*)\s*:\s*(.*)$", line)
        if m and not line.startswith(" ") and not line.startswith("\t"):
            key, val = m.group(1), m.group(2).strip()
            current_block_key = key if val == "" else None
            fm[key] = val
        elif current_block_key:
            m2 = re.match(r"^\s+([A-Za-z][A-Za-z0-9_-]*)\s*:\s*(.*)$", line)
            if m2:
                fm[f"{current_block_key}.{m2.group(1)}"] = m2.group(2).strip().strip('"')
    body = "\n".join(lines[end_idx + 1 :])
    return fm, body


def _clean(value: str | None) -> str | None:
    """Strip surrounding quotes/whitespace; return None for empty/missing."""
    if value is None:
        return None
    v = value.strip().strip('"').strip("'").strip()
    return v or None


def _list_references(skill_dir: Path) -> list[str]:
    """Sorted relative paths of files under the skill's ``references/`` dir.

    Returns names relative to ``references/`` (e.g. ``api_reference.md``). Empty
    if the skill ships no references directory. Nested files keep their subpath.
    """
    ref_dir = skill_dir / "references"
    if not ref_dir.is_dir():
        return []
    return sorted(
        str(p.relative_to(ref_dir)) for p in ref_dir.rglob("*") if p.is_file()
    )


def _has_nonempty_dir(skill_dir: Path, sub: str) -> bool:
    d = skill_dir / sub
    return d.is_dir() and any(p.is_file() for p in d.rglob("*"))


def build_record(skill_md: Path) -> dict:
    """Build one catalog record from a SKILL.md path."""
    skill_dir = skill_md.parent
    domain = skill_dir.parent.name
    text = skill_md.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)

    name = _clean(fm.get("name")) or skill_dir.name
    allowed_raw = _clean(fm.get("allowed-tools"))
    allowed_tools = allowed_raw.split() if allowed_raw else []

    return {
        "name": name,
        "domain": domain,
        "description": _clean(fm.get("description")),
        "license": _clean(fm.get("license")),
        # AlterLab convention stores version nested under metadata.
        "version": _clean(fm.get("metadata.version")),
        # compatibility is a top-level field (1 skill in the corpus lacks it).
        "compatibility": _clean(fm.get("compatibility")),
        "allowed_tools": allowed_tools,
        "has_scripts": _has_nonempty_dir(skill_dir, "scripts"),
        # The eval marker is an evals/evals.json file, not merely an evals/ dir.
        "has_evals": (skill_dir / "evals" / "evals.json").is_file(),
        # Body line count after the frontmatter (matches audit_skills.py semantics).
        "body_lines": body.count("\n") + 1 if body else 0,
        "references": _list_references(skill_dir),
    }


def iter_skill_files() -> list[Path]:
    """Every SKILL.md under skills/, sorted. A directory IS a skill iff it has one
    — this naturally skips non-skill dirs like skills/core/{shared,scripts,hooks}."""
    return sorted(SKILLS.rglob("SKILL.md"))


def build_catalog() -> dict:
    skills = [build_record(p) for p in iter_skill_files()]
    skills.sort(key=lambda s: (s["domain"], s["name"]))

    per_domain: dict[str, int] = {}
    for s in skills:
        per_domain[s["domain"]] = per_domain.get(s["domain"], 0) + 1

    with_evals = sum(1 for s in skills if s["has_evals"])
    total = len(skills)
    summary = {
        "version": read_version(),
        "generated_at": _dt.date.today().isoformat(),
        "total": total,
        "per_domain": dict(sorted(per_domain.items())),
        "eval_coverage": {
            "with_evals": with_evals,
            "without_evals": total - with_evals,
            "total": total,
            "fraction": round(with_evals / total, 4) if total else 0.0,
        },
    }
    return {"summary": summary, "skills": skills}


# --- README count extraction (tolerant) -------------------------------------
#
# The READMEs sprinkle many numbers next to the word "skill"/"beceri" — section
# headers ("Core Pipeline — 7 Skills"), feature rows ("39 Database ... Skills"),
# etc. Those are per-section, not the suite total. We therefore extract only the
# HEADLINE total signals, which are unambiguous:
#
#   1. the shield badge   ``Skills-180`` / ``Beceri-180``      (machine-readable)
#   2. the hero/summary prose ``180 ... skills`` / ``180 ... beceri`` qualified by
#      a "whole-suite" word (purpose-built / Claude AI / Toplam / purpose ...),
#
# and require the catalog total to be among them. This stays tolerant of prose
# rewording while ignoring the incidental per-section counts.
_BADGE_RE = re.compile(r"(?:Skills|Beceri)-(\d{2,4})", re.IGNORECASE)
# EN hero/footer totals. Each alternative pins a whole-suite qualifier so the
# per-section headers ("(39 Skills)", "(25 Skills)") are NOT matched:
#   - "180 purpose-built ... skills"      (hero + summary prose)
#   - "180 ... Claude AI skills"          (hero variant)
#   - "180 skills ·"                      (footer "180 skills · 13 domains")
_HERO_EN_RE = re.compile(
    r"(\d{2,4})\s+purpose-built\b"
    r"|(\d{2,4})\s+(?:[\w-]+\s+){0,3}Claude\s+AI\s+skills?\b"
    r"|(\d{2,4})\s+skills?\s*[·•|]",
    re.IGNORECASE,
)
# Turkish total: only the explicit "Toplam: 180 beceri" / "180 ... Claude AI
# becerisi" headline forms — not the per-folder comments ("25 ... beceri").
_HERO_TR_RE = re.compile(
    r"Toplam[:\s]+(\d{2,4})\s+(?:adet\s+)?beceri\b"
    r"|(\d{2,4})\s+(?:adet\s+)?(?:[\w-]+\s+){0,3}Claude\s+AI\s+beceri",
    re.IGNORECASE,
)


def _first_group(m: re.Match) -> int:
    """Return the single populated capture group of an alternation match as int."""
    return int(next(g for g in m.groups() if g is not None))


def extract_readme_counts(path: Path) -> set[int]:
    """Return the HEADLINE skill-count integers declared in ``path``.

    Looks only at the badge (``Skills-180``/``Beceri-180``) and the hero/summary
    prose ("180 purpose-built Claude AI skills" / "180 ... beceri" / "Toplam:
    180 beceri"), which state the whole-suite total — not the per-section counts
    scattered through headers and feature rows. Empty set if the file is absent."""
    if not path.is_file():
        return set()
    text = path.read_text(encoding="utf-8")
    found: set[int] = set()
    for m in _BADGE_RE.finditer(text):
        found.add(int(m.group(1)))
    for rx in (_HERO_EN_RE, _HERO_TR_RE):
        for m in rx.finditer(text):
            found.add(_first_group(m))
    return found


def render(catalog: dict) -> str:
    return json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"


def run_check(catalog: dict, rendered: str) -> int:
    problems: list[str] = []

    current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
    # Carry the committed date stamp over so --check is deterministic across days.
    try:
        committed_stamp = json.loads(current)["summary"].get("generated_at")
    except (json.JSONDecodeError, KeyError, TypeError):
        committed_stamp = None
    if committed_stamp:
        catalog["summary"]["generated_at"] = committed_stamp
        rendered = render(catalog)
    if current != rendered:
        problems.append(
            "skills.json is stale — run: uv run python scripts/gen_catalog.py"
        )

    total = catalog["summary"]["total"]
    for label, path in (("README.md", README), ("README.tr-TR.md", README_TR)):
        counts = extract_readme_counts(path)
        if not counts:
            problems.append(f"{label}: no skill-count number found to verify against total={total}")
        elif total not in counts:
            problems.append(
                f"{label}: headline skill count {sorted(counts)} does not include catalog total={total}"
            )

    if problems:
        print("gen_catalog --check FAILED:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    cov = catalog["summary"]["eval_coverage"]
    print(
        f"gen_catalog --check OK: {total} skills, "
        f"{cov['with_evals']}/{cov['total']} with evals, "
        f"READMEs agree on total={total}."
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument(
        "--check",
        action="store_true",
        help="verify skills.json is current AND README skill counts match (CI gate)",
    )
    args = ap.parse_args()

    catalog = build_catalog()
    rendered = render(catalog)

    if args.check:
        return run_check(catalog, rendered)

    OUT.write_text(rendered, encoding="utf-8")
    s = catalog["summary"]
    cov = s["eval_coverage"]
    print(
        f"Wrote {OUT.relative_to(REPO)}: {s['total']} skills across "
        f"{len(s['per_domain'])} domains, {cov['with_evals']}/{cov['total']} with evals."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
