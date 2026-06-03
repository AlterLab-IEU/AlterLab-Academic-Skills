#!/usr/bin/env python3
"""Audit SKILL.md files in this repository against the Agent Skills spec.

Checks performed:
  - Frontmatter present and well-formed
  - `name` matches parent directory, lowercase regex, 1-64 chars
  - `description` present, 1-1024 chars
  - `license` present and from the controlled vocabulary (see LICENSE_VOCAB)
  - `allowed-tools` present (warning only — optional, space-separated per the spec)
  - `name` free of reserved words ('claude'/'anthropic')
  - `description` leads with triggers (not the suite boilerplate), has a 'Use when' clause, third person
  - `metadata.skill-author` present (AlterLab convention)
  - Suite-label footer present in body (AlterLab convention)
  - All `references/*.md` paths cited in the body actually exist on disk
  - Body length warning over 500 lines (spec recommendation)

Run modes:
  python3 scripts/audit_skills.py              # report errors+warnings, exit non-zero on errors
  python3 scripts/audit_skills.py --json       # machine-readable JSON report
  python3 scripts/audit_skills.py --strict     # treat warnings as errors

This is a single-file, stdlib-only script — no dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

# Spec constraints (https://agentskills.io/specification)
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
NAME_MAX = 64
DESCRIPTION_MAX = 1536  # current Claude Code listing truncation (description + when-to-use)
# Heuristics for description-quality lints
TRIGGER_PHRASES = ("use when", "use this", "use for", "use whenever", "when the user", "triggers on", "use to ")
FIRST_SECOND_PERSON = re.compile(r"\b(I can|I will|I'll|you can|you should|use me to|let me|we will|we'll)\b", re.IGNORECASE)
RESERVED_NAME_WORDS = ("claude", "anthropic")
BODY_LINES_SOFT_LIMIT = 500  # spec recommends < 500 lines
BODY_LINES_HARD_LIMIT = 1500  # error past this — definitely belongs in references/

# AlterLab project conventions
ALTERLAB_PREFIX = "alterlab-"
SUITE_LABEL = "Part of the AlterLab Academic Skills suite."
SUITE_LABEL_LOOSE = "AlterLab Academic Skills suite"  # substring sufficient

# Controlled license vocabulary (SPDX-style + project-specific). Issue #3.
LICENSE_VOCAB = {
    "MIT",
    "Apache-2.0",
    "GPL-2.0",
    "GPL-3.0",
    "LGPL-3.0",
    "BSD-3-Clause",
    "CC-BY-3.0",
    "CC-BY-4.0",
    "CC0-1.0",
    "CeCILL-2.1",
    "Proprietary",
}

# Aliases from current repo state → canonical vocabulary
LICENSE_ALIASES = {
    "mit": "MIT",
    "mit license": "MIT",
    "apache license, version 2.0": "Apache-2.0",
    "apache-2.0 license": "Apache-2.0",
    "gpl-2.0 license": "GPL-2.0",
    "gpl-3.0 license": "GPL-3.0",
    "gplv3 license": "GPL-3.0",
    "cecill free software license agreement": "CeCILL-2.1",
}


@dataclass
class Finding:
    skill: str
    severity: str  # "error" or "warning"
    code: str
    message: str


@dataclass
class SkillReport:
    path: Path
    name: str | None = None
    findings: list[Finding] = field(default_factory=list)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Naive YAML frontmatter parser — flat keys + indented metadata block only.

    Returns (frontmatter dict, body). Returns ({}, full text) if no frontmatter.
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
        # Top-level "key: value" or "key:" (start of nested block)
        m = re.match(r"^([A-Za-z][A-Za-z0-9_-]*)\s*:\s*(.*)$", line)
        if m and not line.startswith(" ") and not line.startswith("\t"):
            key, val = m.group(1), m.group(2).strip()
            current_block_key = key if val == "" else None
            fm[key] = val
        elif current_block_key:
            # Indented value under a parent block, e.g. metadata.skill-author
            m2 = re.match(r"^\s+([A-Za-z][A-Za-z0-9_-]*)\s*:\s*(.*)$", line)
            if m2:
                fm[f"{current_block_key}.{m2.group(1)}"] = m2.group(2).strip().strip('"')

    body = "\n".join(lines[end_idx + 1 :])
    return fm, body


def normalize_license(value: str) -> str | None:
    """Return canonical license string if recognized, else None."""
    if not value:
        return None
    v = value.strip().strip('"').strip("'")
    if v in LICENSE_VOCAB:
        return v
    lowered = v.lower()
    if lowered in LICENSE_ALIASES:
        return LICENSE_ALIASES[lowered]
    if v.startswith("https://"):  # URL-based — caller should resolve
        return None
    if v.startswith("Proprietary"):
        return "Proprietary"
    return None


_SKILL_INDEX: dict[str, Path] | None = None


def skill_index() -> dict[str, Path]:
    """Map every skill `name` (== leaf dir name) to its directory, for resolving
    cross-skill `references/*.md` citations (e.g. one skill pointing at another's refs)."""
    global _SKILL_INDEX
    if _SKILL_INDEX is None:
        _SKILL_INDEX = {
            sk.name: sk
            for sk in SKILLS_DIR.glob("*/*")
            if sk.is_dir() and (sk / "SKILL.md").exists()
        }
    return _SKILL_INDEX


_REF_RE = re.compile(r"(?:(alterlab-[a-z0-9-]+)/)?(references/[A-Za-z0-9_.\-/]+\.md)")
_SKILL_NAME_RE = re.compile(r"alterlab-[a-z0-9-]+")


def missing_references(body: str, skill_dir: Path) -> list[str]:
    """Return cited references/*.md paths that resolve to no file on disk.

    A citation resolves if the file exists in (a) this skill, (b) a skill named as
    an explicit path prefix (`alterlab-foo/references/x.md`), or (c) any other
    `alterlab-*` skill mentioned on the same line ("the alterlab-seaborn skill's
    `references/examples.md`"). Cross-skill references are legitimate, not errors."""
    index = skill_index()
    missing: list[str] = []
    seen: set[str] = set()
    for line in body.splitlines():
        line_skills = set(_SKILL_NAME_RE.findall(line))
        for prefix, relref in _REF_RE.findall(line):
            cited = (f"{prefix}/" if prefix else "") + relref
            if cited in seen:
                continue
            seen.add(cited)
            if prefix:  # explicit cross-skill path
                d = index.get(prefix)
                if not (d and (d / relref).exists()):
                    missing.append(cited)
                continue
            if (skill_dir / relref).exists():  # self reference
                continue
            if any((index.get(sn) and (index[sn] / relref).exists()) for sn in line_skills):
                continue  # resolved against a sibling skill named on this line
            missing.append(cited)
    return missing


def audit_skill(skill_md: Path) -> SkillReport:
    rel = skill_md.relative_to(REPO_ROOT)
    report = SkillReport(path=rel)

    text = skill_md.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    if not fm:
        report.findings.append(Finding(str(rel), "error", "no-frontmatter", "Missing YAML frontmatter"))
        return report

    name = fm.get("name", "").strip().strip('"')
    report.name = name
    parent_dir = skill_md.parent.name

    # name field
    if not name:
        report.findings.append(Finding(str(rel), "error", "name-missing", "Missing `name` field"))
    else:
        if len(name) > NAME_MAX:
            report.findings.append(Finding(str(rel), "error", "name-too-long", f"`name` exceeds {NAME_MAX} chars ({len(name)})"))
        if not NAME_RE.match(name):
            report.findings.append(Finding(str(rel), "error", "name-invalid", f"`name` does not match required pattern: {name}"))
        if name != parent_dir:
            report.findings.append(Finding(str(rel), "error", "name-mismatch", f"`name` ({name}) does not match parent directory ({parent_dir})"))
        if not name.startswith(ALTERLAB_PREFIX) and "shared" not in parent_dir:
            report.findings.append(Finding(str(rel), "warning", "name-no-prefix", f"`name` does not start with '{ALTERLAB_PREFIX}'"))
        if any(w in name.lower() for w in RESERVED_NAME_WORDS):
            report.findings.append(Finding(str(rel), "error", "name-reserved-word", f"`name` contains a reserved word ('claude'/'anthropic'): {name}"))

    # description field — the single most important field for skill triggering.
    desc = fm.get("description", "").strip().strip('"')
    if not desc:
        report.findings.append(Finding(str(rel), "error", "description-missing", "Missing `description` field"))
    else:
        if len(desc) > DESCRIPTION_MAX:
            report.findings.append(Finding(str(rel), "error", "description-too-long", f"`description` exceeds {DESCRIPTION_MAX} chars ({len(desc)})"))
        # The suite label belongs anywhere EXCEPT the front — leading boilerplate wastes
        # the highest-signal trigger tokens (Anthropic: the description decides selection).
        if desc.lstrip('"').startswith(SUITE_LABEL_LOOSE) or desc.lstrip('"').startswith(SUITE_LABEL):
            report.findings.append(Finding(str(rel), "error", "description-leading-boilerplate", "`description` starts with the AlterLab suite label — move it to the END so triggers lead"))
        if not any(p in desc.lower() for p in TRIGGER_PHRASES):
            report.findings.append(Finding(str(rel), "warning", "description-no-trigger", "`description` has no explicit 'Use when ...' trigger clause"))
        if FIRST_SECOND_PERSON.search(desc):
            report.findings.append(Finding(str(rel), "warning", "description-not-third-person", "`description` uses first/second person — Anthropic requires third person"))

    # license field
    raw_license = fm.get("license", "").strip()
    if not raw_license:
        report.findings.append(Finding(str(rel), "error", "license-missing", "Missing `license` field"))
    else:
        canonical = normalize_license(raw_license)
        if canonical is None:
            report.findings.append(Finding(str(rel), "error", "license-not-canonical", f"`license` not in controlled vocabulary: {raw_license!r}"))
        elif canonical != raw_license:
            report.findings.append(Finding(str(rel), "warning", "license-needs-normalize", f"`license` should be canonical form {canonical!r} (currently {raw_license!r})"))

    # allowed-tools (experimental — warning only when missing)
    if "allowed-tools" not in fm:
        report.findings.append(Finding(str(rel), "warning", "allowed-tools-missing", "Missing `allowed-tools` field (per Anthropic skill spec)"))

    # metadata.skill-author (AlterLab convention)
    if "metadata.skill-author" not in fm:
        report.findings.append(Finding(str(rel), "warning", "skill-author-missing", "Missing `metadata.skill-author` field"))

    # Suite-label — convention is the description mentions the AlterLab suite.
    # Accept any phrasing containing the loose label.
    if SUITE_LABEL_LOOSE not in desc and SUITE_LABEL_LOOSE not in body:
        report.findings.append(Finding(str(rel), "warning", "suite-label-missing", f"Suite mention not found (looking for {SUITE_LABEL_LOOSE!r})"))

    # Reference path existence (self + cross-skill)
    for ref in missing_references(body, skill_md.parent):
        report.findings.append(Finding(str(rel), "error", "reference-missing", f"Cited reference file does not exist: {ref}"))

    # Body length
    body_lines = body.count("\n") + 1
    if body_lines > BODY_LINES_HARD_LIMIT:
        report.findings.append(Finding(str(rel), "error", "body-too-long", f"Body is {body_lines} lines (>{BODY_LINES_HARD_LIMIT} hard limit) — split into references/"))
    elif body_lines > BODY_LINES_SOFT_LIMIT:
        report.findings.append(Finding(str(rel), "warning", "body-long", f"Body is {body_lines} lines (>{BODY_LINES_SOFT_LIMIT} soft limit) — consider splitting"))

    return report


def iter_skill_files() -> Iterable[Path]:
    for p in sorted(SKILLS_DIR.rglob("SKILL.md")):
        yield p


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--json", action="store_true", help="Output JSON instead of text")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    parser.add_argument("--quiet", action="store_true", help="Suppress per-finding output, summary only")
    args = parser.parse_args()

    reports = [audit_skill(p) for p in iter_skill_files()]
    errors = [f for r in reports for f in r.findings if f.severity == "error"]
    warnings = [f for r in reports for f in r.findings if f.severity == "warning"]

    if args.json:
        out = {
            "summary": {
                "total_skills": len(reports),
                "errors": len(errors),
                "warnings": len(warnings),
            },
            "findings": [
                {"skill": f.skill, "severity": f.severity, "code": f.code, "message": f.message}
                for r in reports
                for f in r.findings
            ],
        }
        print(json.dumps(out, indent=2))
    else:
        if not args.quiet:
            by_code: dict[str, int] = {}
            for r in reports:
                for f in r.findings:
                    by_code[f.code] = by_code.get(f.code, 0) + 1
                    print(f"[{f.severity.upper():7}] {f.code:30} {f.skill}: {f.message}")
            print()
            print("=== Findings by code ===")
            for code, n in sorted(by_code.items(), key=lambda x: -x[1]):
                print(f"  {n:4}  {code}")
        print()
        print(f"=== Audit summary ===")
        print(f"Total skills: {len(reports)}")
        print(f"Errors:       {len(errors)}")
        print(f"Warnings:     {len(warnings)}")

    has_failures = bool(errors) or (args.strict and bool(warnings))
    return 1 if has_failures else 0


if __name__ == "__main__":
    sys.exit(main())
