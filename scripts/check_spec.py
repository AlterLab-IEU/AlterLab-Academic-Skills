#!/usr/bin/env python3
"""Spec-conformance checker for Agent Skills (agentskills.io standard).

Two layers, both run by default:

1. **External, PINNED reference validator.** If ``npx`` is available, every skill
   directory is run through ``skills-ref@<PINNED>`` (the published Agent Skills
   reference library). This is the authoritative parse-level check (frontmatter
   present, ``name``/``description`` non-empty). Pinned so CI is reproducible.
   If ``npx`` / network is unavailable, this layer is SKIPPED (not failed) and a
   notice is printed — the native layer below still runs.

2. **Native agentskills.io rule checks.** Enforced in-process, no network:
     * ``name`` matches ``^[a-z0-9]+(-[a-z0-9]+)*$`` and is 1-64 chars.
     * ``name`` equals the skill's directory name.
     * ``description`` is present and <= 1024 characters.
     * ``references/*`` citations in the body are at most one directory level deep.
     * directory layout: a ``SKILL.md`` exists at the skill root with valid
       ``---`` YAML frontmatter containing both required keys.

Exit non-zero if any skill fails any check. Intended for the spec-conformance CI
workflow; complements (does not replace) ``scripts/audit_skills.py`` (which adds
house-style/quality lints on top of these spec rules).

    uv run python scripts/check_spec.py            # check every skill
    uv run python scripts/check_spec.py --skill pubmed   # only matching dir names
    uv run python scripts/check_spec.py --no-external     # skip the npx reference pass
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"

# Pinned reference-validator version: bump deliberately, never floating, so the
# conformance gate is reproducible across machines and CI runs.
SKILLS_REF_PIN = "skills-ref@0.1.5"

# Canonical agentskills.io frontmatter rules.
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
NAME_MAX = 64
DESCRIPTION_MAX = 1024
REFERENCES_MAX_DEPTH = 1  # references/<file> is depth 1; references/<sub>/<file> is depth 2.

# Pull `references/...md` style relative citations out of the body for the depth check.
_REF_CITATION_RE = re.compile(r"(?<![\w./-])references/[A-Za-z0-9_./-]+\.(?:md|json|py)")


def find_skill_dirs(substr: str | None) -> list[Path]:
    dirs = sorted(p.parent for p in SKILLS.rglob("SKILL.md"))
    if substr:
        dirs = [d for d in dirs if substr in d.name]
    return dirs


def parse_frontmatter(skill_md: Path) -> tuple[dict[str, str], list[str]]:
    """Minimal YAML frontmatter parse (flat ``key: value`` pairs only).

    Returns (fields, errors). Mirrors the tolerant parse the repo's audit uses so
    both tools agree on what 'name'/'description' resolve to.
    """
    errors: list[str] = []
    text = skill_md.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, ["SKILL.md does not start with '---' frontmatter"]
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, ["frontmatter '---' is not closed"]
    fields: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z][A-Za-z0-9_-]*)\s*:\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            # strip matching surrounding quotes
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            fields[key] = val
    body = "\n".join(lines[end + 1 :])
    fields["__body__"] = body
    return fields, errors


def ref_depth(citation: str) -> int:
    """`references/a.md` -> 1, `references/sub/a.md` -> 2."""
    parts = citation.split("/")
    # drop the leading 'references' segment; remaining segments minus the file = depth
    return len(parts) - 1  # 'references' + file -> 1; 'references'+sub+file -> 2


def check_native(skill_dir: Path) -> list[str]:
    """Return a list of spec violations for one skill (empty == conformant)."""
    problems: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return ["missing SKILL.md at skill root"]

    fields, fm_errors = parse_frontmatter(skill_md)
    problems += fm_errors
    if fm_errors:
        return problems  # can't reason about fields if frontmatter is broken

    name = fields.get("name", "")
    desc = fields.get("description", "")
    body = fields.get("__body__", "")

    # name rules
    if not name:
        problems.append("missing required frontmatter field: name")
    else:
        if not NAME_RE.match(name):
            problems.append(f"name '{name}' is not lowercase kebab-case (^[a-z0-9]+(-[a-z0-9]+)*$)")
        if len(name) > NAME_MAX:
            problems.append(f"name '{name}' exceeds {NAME_MAX} chars ({len(name)})")
        if name != skill_dir.name:
            problems.append(f"name '{name}' does not match directory '{skill_dir.name}'")

    # description rules
    if not desc:
        problems.append("missing required frontmatter field: description")
    elif len(desc) > DESCRIPTION_MAX:
        problems.append(f"description exceeds {DESCRIPTION_MAX} chars ({len(desc)})")

    # references depth rule
    for citation in _REF_CITATION_RE.findall(body):
        if ref_depth(citation) > REFERENCES_MAX_DEPTH:
            problems.append(
                f"reference '{citation}' is deeper than {REFERENCES_MAX_DEPTH} level(s)"
            )

    return problems


def run_external(skill_dirs: list[Path]) -> tuple[list[str], bool]:
    """Run the pinned skills-ref validator over each skill.

    Returns (failures, ran). ``ran`` is False when npx is unavailable (layer
    skipped, not failed).
    """
    if shutil.which("npx") is None:
        return [], False
    failures: list[str] = []
    for d in skill_dirs:
        try:
            proc = subprocess.run(
                ["npx", "-y", SKILLS_REF_PIN, "validate", str(d)],
                capture_output=True,
                text=True,
                timeout=120,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            failures.append(f"{d.relative_to(REPO)}: skills-ref invocation error: {exc}")
            continue
        if proc.returncode != 0:
            msg = (proc.stdout + proc.stderr).strip().splitlines()
            detail = msg[-1] if msg else f"exit {proc.returncode}"
            failures.append(f"{d.relative_to(REPO)}: {detail}")
    return failures, True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skill", metavar="SUBSTR", default=None,
                    help="only check skills whose directory name contains SUBSTR")
    ap.add_argument("--no-external", action="store_true",
                    help="skip the pinned skills-ref reference-validator pass")
    args = ap.parse_args(argv)

    skill_dirs = find_skill_dirs(args.skill)
    if not skill_dirs:
        print("no skills found", file=sys.stderr)
        return 1

    # Layer 2: native rules (always run).
    native_failures: list[str] = []
    for d in skill_dirs:
        for problem in check_native(d):
            native_failures.append(f"{d.relative_to(REPO)}: {problem}")

    # Layer 1: external pinned validator (unless suppressed / unavailable).
    external_failures: list[str] = []
    external_ran = False
    if not args.no_external:
        external_failures, external_ran = run_external(skill_dirs)
        if not external_ran:
            print(f"note: npx not found — skipped {SKILLS_REF_PIN} reference pass "
                  "(native checks still ran).", file=sys.stderr)

    all_failures = external_failures + native_failures
    for f in all_failures:
        print(f"FAIL {f}", file=sys.stderr)

    ext = f"{SKILLS_REF_PIN}{'' if external_ran else ' (skipped)'}"
    print(
        f"\nspec-conformance: {len(skill_dirs)} skill(s); "
        f"{len(all_failures)} violation(s) "
        f"[external={len(external_failures)} via {ext}, native={len(native_failures)}]."
    )
    return 1 if all_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
