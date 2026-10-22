#!/usr/bin/env python3
"""check_keyless.py — every skill must do what it claims without an external API key.

Keyless-first rule (CLAUDE.md, "Quality Standards for New Skills"): a skill's core job
works with no credentials at all — Claude's own tools, keyless public APIs, local
libraries. A credential may only *add* something: the user's own private account or data,
a higher rate limit, or a paid service the user explicitly asks for. Checks, per skill:

  K1  Every credential the skill names — read by a bundled script (os.getenv /
      os.environ), named in SKILL.md or references/ (``*_API_KEY``, ``*_TOKEN``,
      ``*_SECRET``, ``*_PASSWORD``, ``*_ACCESS_KEY``), or required by an eval — is listed in
      ``metadata.credentials``, which reads ``"optional: NAME (what it adds), ..."``.
      A skill that names none may omit the field or say ``"none"``.
  K2  ``compatibility`` and ``description`` never make a credential, account, licence or
      subscription a precondition ("Requires an API key", "needs an account").
  K3  At least 3 ``should_trigger`` eval cases run without any ``env:`` requirement, so
      the keyless path is what the behavioral harness actually grades.

  python3 scripts/check_keyless.py            # report; exit 1 on any violation
  python3 scripts/check_keyless.py --json     # machine-readable
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from audit_skills import parse_frontmatter  # noqa: E402

CRED_SUFFIX = r"(?:API_KEY|ACCESS_KEY|SECRET_KEY|SECRET|TOKEN|PASSWORD|LIBRARY_ID|APP_KEY)"
ENV_READ = re.compile(r"""os\.(?:getenv|environ\.get|environ\.setdefault)\(\s*["']([A-Z][A-Z0-9_]*)["']"""
                      r"""|os\.environ\[\s*["']([A-Z][A-Z0-9_]*)["']\s*\]""")
NAMED = re.compile(r"\b([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*_" + CRED_SUFFIX + r")\b")
IS_CRED = re.compile(r"_" + CRED_SUFFIX + r"$")
# Placeholders in code samples and diagram labels, not credentials the skill asks for.
PLACEHOLDER = re.compile(r"^(?:YOUR|MY|EXAMPLE|DUMMY|FAKE|TEST|PROD|STAGING)_|^(?:API|AUTH|ACCESS|REFRESH|"
                         r"BEARER|SECRET|ID)_(?:TOKEN|KEY)$")
# "Requires a free FOO_API_KEY", "needs an account", "must have a licence" — not
# "No API key required" or "optional ... key".
PRECONDITION = re.compile(
    r"\b(?:requires?|needs?|must (?:have|supply|set))\b(?![^.;]{0,25}\bnothing\b)[^.;]{0,70}?"
    r"\b(?:api[ _-]?keys?|[A-Z][A-Z0-9_]*_" + CRED_SUFFIX + r"|access tokens?|api tokens?|accounts?|"
    r"licen[cs]es?|subscriptions?|credentials|passwords?|registration)\b", re.I)

NEGATED = re.compile(r"\b(?:no|not|without|optional(?:ly)?)\b", re.I)


def skill_dirs() -> list[Path]:
    return sorted(p.parent for p in REPO.glob("skills/*/alterlab-*/SKILL.md"))


def _shipped(d: Path, pattern: str) -> list[Path]:
    return [p for p in d.rglob(pattern) if "evals" not in p.relative_to(d).parts]


def credentials_named(d: Path) -> set[str]:
    names: set[str] = set()
    for py in _shipped(d, "*.py"):
        for a, b in ENV_READ.findall(py.read_text(encoding="utf-8", errors="replace")):
            if IS_CRED.search(a or b):
                names.add(a or b)
    for md in [d / "SKILL.md", *_shipped(d, "references/*.md"), *_shipped(d, "references/**/*.md")]:
        if md.exists():
            names |= set(NAMED.findall(md.read_text(encoding="utf-8", errors="replace")))
    ev = d / "evals" / "evals.json"
    if ev.exists():
        for e in json.loads(ev.read_text(encoding="utf-8")).get("evals", []):
            names |= {r[4:] for r in e.get("requires", []) if r.startswith("env:")}
    return {n for n in names if not PLACEHOLDER.search(n)}


def check(d: Path) -> list[str]:
    text = (d / "SKILL.md").read_text(encoding="utf-8")
    fm, _ = parse_frontmatter(text)
    out = []
    named = credentials_named(d)
    declared = fm.get("metadata.credentials", "").strip().strip('"')
    if named:
        if not declared.lower().startswith("optional:"):
            out.append(f"K1 names {', '.join(sorted(named))} but metadata.credentials does not "
                       f"say 'optional: ...' (is: {declared or 'absent'!r})")
        else:
            missing = sorted(n for n in named if n not in declared)
            if missing:
                out.append(f"K1 metadata.credentials omits {', '.join(missing)}")
    elif declared and declared.lower() not in ("none", "none required"):
        if not declared.lower().startswith("optional:"):
            out.append(f"K1 metadata.credentials must be 'none' or 'optional: ...' (is: {declared!r})")
    for field in ("compatibility", "description"):
        for m in PRECONDITION.finditer(fm.get(field, "") or fm.get(f"metadata.{field}", "")):
            if NEGATED.search(m.group(0)):
                continue  # "need no API key", "requires nothing but ... optional key"
            out.append(f"K2 {field} makes a credential a precondition: {m.group(0)!r}")
    ev = d / "evals" / "evals.json"
    keyless = 0
    if ev.exists():
        for e in json.loads(ev.read_text(encoding="utf-8")).get("evals", []):
            trig = any(a.get("type") == "should_trigger" and a.get("value") is True
                       for a in e.get("assertions", []))
            if trig and not any(r.startswith("env:") for r in e.get("requires", [])):
                keyless += 1
    if keyless < 3:
        out.append(f"K3 only {keyless} should_trigger case(s) run without an env: requirement "
                   "(need 3)")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--skill", action="append", metavar="NAME",
                    help="only check this skill (repeatable), e.g. alterlab-perplexity")
    args = ap.parse_args()
    dirs = [d for d in skill_dirs() if not args.skill or d.name in args.skill]
    report = {d.name: v for d in dirs if (v := check(d))}
    if args.json:
        print(json.dumps(report, indent=1))
    else:
        for name, violations in report.items():
            for v in violations:
                print(f"{name}: {v}")
        print(f"{len(report)} skill(s) violate the keyless-first rule "
              f"({sum(map(len, report.values()))} finding(s)); {len(dirs)} checked.")
    return 1 if report else 0


if __name__ == "__main__":
    sys.exit(main())
