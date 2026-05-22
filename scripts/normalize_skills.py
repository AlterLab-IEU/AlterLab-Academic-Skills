#!/usr/bin/env python3
"""Normalize SKILL.md frontmatter to the controlled schema.

Fixes applied (idempotent):
  - License field cased/normalized to controlled vocabulary
  - Missing `license` added (defaults to MIT — repo's top-level license)
  - URL-based or long-form license values mapped to SPDX equivalents
  - `allowed-tools` field added with a category-based default if missing
  - Frontmatter key ordering preserved on rewrite (best-effort)

Run modes:
  python3 scripts/normalize_skills.py --dry-run  # show what would change
  python3 scripts/normalize_skills.py            # apply changes

Coordinates with audit_skills.py: after running this, baseline errors should drop
to zero for license-* and allowed-tools-missing should drop to zero warnings.

stdlib-only, no deps.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

# Same vocabulary + aliases as audit_skills.py (kept in sync manually for now).
LICENSE_VOCAB = {
    "MIT", "Apache-2.0", "GPL-2.0", "GPL-3.0", "LGPL-3.0",
    "BSD-3-Clause", "CC-BY-3.0", "CC-BY-4.0", "CC0-1.0",
    "CeCILL-2.1", "Proprietary",
}

LICENSE_ALIASES_LOWER = {
    "mit": "MIT",
    "mit license": "MIT",
    "apache license, version 2.0": "Apache-2.0",
    "apache-2.0 license": "Apache-2.0",
    "gpl-2.0 license": "GPL-2.0",
    "gpl-3.0 license": "GPL-3.0",
    "gplv3 license": "GPL-3.0",
    "cecill free software license agreement": "CeCILL-2.1",
}

# Manual URL → canonical (these are upstream tool licenses, all known)
LICENSE_URL_MAP = {
    "https://github.com/matplotlib/matplotlib/tree/main/LICENSE": "BSD-3-Clause",  # Matplotlib uses PSF/BSD
    "https://github.com/pola-rs/polars/blob/main/LICENSE": "MIT",
    "https://github.com/pydicom/pydicom/blob/main/LICENSE": "MIT",
    "https://github.com/sympy/sympy/blob/master/LICENSE": "BSD-3-Clause",
}

# Long-form license blobs → canonical fallback to Proprietary
LICENSE_LONGFORM_PREFIXES = (
    "HMDB is offered",
    "This skill is provided under",  # IDC case — skill is MIT, data has separate terms
    "Non-academic use of KEGG",
)

# Per-category default for `allowed-tools` when none is set.
# Patterns follow the Anthropic spec: space-separated tokens, optional fine-grained
# permissions via `Bash(prog:*)`.
ALLOWED_TOOLS_BY_CATEGORY = {
    "core":               "Read Write Edit Bash WebFetch WebSearch",
    "bioinformatics":     "Read Write Edit Bash(python:*) Bash(uv:*)",
    "cheminformatics":    "Read Write Edit Bash(python:*) Bash(uv:*)",
    "clinical-research":  "Read Write Edit Bash(python:*)",
    "data-science":       "Read Write Edit Bash(python:*) Bash(uv:*)",
    "databases":          "Read WebFetch Bash(curl:*) Bash(python:*)",
    "document-tools":     "Read Write Edit Bash(python:*)",
    "domain-specific":    "Read Write Edit Bash(python:*)",
    "finance-economics":  "Read WebFetch Bash(curl:*) Bash(python:*)",
    "lab-integrations":   "Read Write Edit Bash(curl:*) Bash(python:*)",
    "research-tools":     "Read WebFetch WebSearch Bash(python:*)",
    "visualization":      "Read Write Edit Bash(python:*)",
    "writing-tools":      "Read Write Edit",
}
ALLOWED_TOOLS_DEFAULT = "Read Write Edit"


def parse_blocks(text: str) -> tuple[list[str], list[str], list[str]] | None:
    """Split a file into pre-frontmatter, frontmatter lines, body. Returns None if no frontmatter."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None
    return lines[:1], lines[1:end], lines[end:]


def normalize_license_value(raw: str) -> str | None:
    """Return a canonical license string or None if we can't decide."""
    v = raw.strip().strip('"').strip("'")
    if v in LICENSE_VOCAB:
        return v
    lower = v.lower()
    if lower in LICENSE_ALIASES_LOWER:
        return LICENSE_ALIASES_LOWER[lower]
    if v.startswith("https://"):
        return LICENSE_URL_MAP.get(v)
    for prefix in LICENSE_LONGFORM_PREFIXES:
        if v.startswith(prefix):
            # IDC explicitly says "skill provided under MIT" — preserve that
            if "MIT License" in v:
                return "MIT"
            return "Proprietary"
    if v.startswith("Proprietary"):
        return "Proprietary"
    return None


def category_for(skill_md: Path) -> str:
    # skills/<category>/<skill>/SKILL.md
    rel = skill_md.relative_to(SKILLS_DIR)
    return rel.parts[0]


def normalize_file(skill_md: Path, dry_run: bool) -> dict[str, str]:
    """Apply fixes; return a dict of {finding_code: description} for changes made/skipped."""
    text = skill_md.read_text(encoding="utf-8")
    parsed = parse_blocks(text)
    if parsed is None:
        return {"skipped": "no frontmatter"}
    head, fm_lines, tail = parsed

    # Build a key index over top-level frontmatter lines
    changes: dict[str, str] = {}
    new_fm_lines = list(fm_lines)

    # --- License normalization ---
    license_idx = None
    license_val = None
    for i, line in enumerate(new_fm_lines):
        m = re.match(r"^license:\s*(.*)$", line)
        if m and not (line.startswith(" ") or line.startswith("\t")):
            license_idx = i
            license_val = m.group(1)
            break

    if license_val is None:
        # Missing license → inject MIT after `description:` line
        canonical = "MIT"
        # Find description line to insert after
        for i, line in enumerate(new_fm_lines):
            if re.match(r"^description:", line) and not (line.startswith(" ") or line.startswith("\t")):
                new_fm_lines.insert(i + 1, f"license: {canonical}")
                changes["license-added"] = f"added license: {canonical}"
                break
    else:
        canonical = normalize_license_value(license_val)
        if canonical is None:
            changes["license-unmappable"] = f"could not normalize license value: {license_val!r}"
        elif canonical != license_val.strip().strip('"').strip("'"):
            new_fm_lines[license_idx] = f"license: {canonical}"
            changes["license-normalized"] = f"{license_val.strip()!r} -> {canonical!r}"

    # --- allowed-tools insertion ---
    has_allowed = any(
        re.match(r"^allowed-tools:", ln) and not (ln.startswith(" ") or ln.startswith("\t"))
        for ln in new_fm_lines
    )
    if not has_allowed:
        cat = category_for(skill_md)
        value = ALLOWED_TOOLS_BY_CATEGORY.get(cat, ALLOWED_TOOLS_DEFAULT)
        # Insert after license, else after description
        anchor_idx = None
        for i, line in enumerate(new_fm_lines):
            if re.match(r"^license:", line) and not (line.startswith(" ") or line.startswith("\t")):
                anchor_idx = i
                break
        if anchor_idx is None:
            for i, line in enumerate(new_fm_lines):
                if re.match(r"^description:", line) and not (line.startswith(" ") or line.startswith("\t")):
                    anchor_idx = i
                    break
        if anchor_idx is not None:
            new_fm_lines.insert(anchor_idx + 1, f"allowed-tools: {value}")
            changes["allowed-tools-added"] = f"added allowed-tools (category={cat})"

    if new_fm_lines == fm_lines:
        return changes

    new_text = "\n".join(head + new_fm_lines + tail)
    if not dry_run:
        skill_md.write_text(new_text, encoding="utf-8")
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing files")
    args = parser.parse_args()

    total = 0
    by_code: dict[str, int] = {}
    unmappable: list[tuple[Path, str]] = []

    for skill_md in sorted(SKILLS_DIR.rglob("SKILL.md")):
        total += 1
        changes = normalize_file(skill_md, dry_run=args.dry_run)
        for code, desc in changes.items():
            by_code[code] = by_code.get(code, 0) + 1
            if code == "license-unmappable":
                unmappable.append((skill_md.relative_to(REPO_ROOT), desc))

    mode = "DRY RUN" if args.dry_run else "APPLIED"
    print(f"=== Normalize {mode} ===")
    print(f"Total skills processed: {total}")
    for code, n in sorted(by_code.items(), key=lambda x: -x[1]):
        print(f"  {n:4}  {code}")
    if unmappable:
        print()
        print("Unmappable license values (manual review needed):")
        for path, desc in unmappable:
            print(f"  {path}: {desc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
