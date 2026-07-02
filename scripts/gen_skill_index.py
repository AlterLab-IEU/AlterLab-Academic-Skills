#!/usr/bin/env python3
"""Generate the AlterLab skill index consumed by the alterlab-skill-finder router.

Reads the generated ``skills.json`` catalog and writes a human-readable Markdown index —
every skill grouped by domain with a one-line summary — to the router skill's references/.
Keeps the router's catalog in sync with the corpus (drift-checked with ``--check``).

    python scripts/gen_skill_index.py           # write the index
    python scripts/gen_skill_index.py --check    # fail if the committed index is stale
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
CATALOG = REPO / "skills.json"
OUT = REPO / "skills" / "core" / "alterlab-skill-finder" / "references" / "skill_index.md"

# Canonical domain order + display label (mirrors the CLAUDE.md category table).
DOMAIN_ORDER = [
    ("core", "Core Pipeline"),
    ("databases", "Databases"),
    ("bioinformatics", "Bioinformatics"),
    ("cheminformatics", "Cheminformatics"),
    ("clinical-research", "Clinical Research"),
    ("data-science", "Data Science"),
    ("visualization", "Visualization"),
    ("writing-tools", "Writing Tools"),
    ("lab-integrations", "Lab Integrations"),
    ("domain-specific", "Domain-Specific"),
    ("document-tools", "Document Tools"),
    ("research-tools", "Research Tools"),
    ("finance-economics", "Finance & Economics"),
    ("turkish-academia", "Turkish Academia"),
    ("faculty-life", "Faculty Life"),
    ("methodology", "Methodology"),
    ("social-science-workflow", "Social-Science Workflow"),
]

# Markers that begin the trigger/boilerplate tail of a description; the "what it does" is
# everything before the earliest of these.
_TAIL_MARKERS = (" Use when", " Use this", " Use it when", " Use for", " Use the ")


def one_liner(description: str) -> str:
    """The 'what it does' clause: description text before the 'Use when …' trigger tail."""
    cut = len(description)
    for mark in _TAIL_MARKERS:
        i = description.find(mark)
        if i != -1:
            cut = min(cut, i)
    head = description[:cut].strip().rstrip(".")
    if not head:  # fallback: first sentence
        head = description.split(". ")[0].strip().rstrip(".")
    return head


def build_index(catalog: dict) -> str:
    skills = catalog["skills"] if isinstance(catalog, dict) else catalog
    by_domain: dict[str, list[dict]] = {}
    for s in skills:
        by_domain.setdefault(s["domain"], []).append(s)

    total = len(skills)
    domains = [d for d, _ in DOMAIN_ORDER if d in by_domain]
    # any domain not in the canonical list (defensive) goes last, alphabetically
    domains += sorted(d for d in by_domain if d not in {d for d, _ in DOMAIN_ORDER})
    labels = dict(DOMAIN_ORDER)

    lines = [
        "# AlterLab Skill Index",
        "",
        "> **Generated** — do not edit by hand. Regenerate with "
        "`python3 scripts/gen_skill_index.py`; kept in sync with `skills.json`.",
        "",
        f"Every AlterLab skill ({total}) across {len(domains)} domains, with a one-line summary. "
        "The `alterlab-skill-finder` router uses this to name the right skill for a task.",
        "",
    ]
    for dom in domains:
        entries = sorted(by_domain[dom], key=lambda s: s["name"])
        lines.append(f"## {labels.get(dom, dom)} — `{dom}` ({len(entries)})")
        lines.append("")
        for s in entries:
            lines.append(f"- **`{s['name']}`** — {one_liner(s['description'])}")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="fail if the committed index is stale")
    args = ap.parse_args()

    if not CATALOG.is_file():
        print("skills.json not found — run scripts/gen_catalog.py first", file=sys.stderr)
        return 1
    rendered = build_index(json.loads(CATALOG.read_text(encoding="utf-8")))

    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != rendered:
            print(
                f"out of date — run: python3 scripts/gen_skill_index.py\n  - "
                f"{OUT.relative_to(REPO)}",
                file=sys.stderr,
            )
            return 1
        print(f"{OUT.relative_to(REPO)} up to date.")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(rendered, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(REPO)} ({rendered.count(chr(10))} lines).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
