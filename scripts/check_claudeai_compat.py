#!/usr/bin/env python3
"""Guard SKILL.md frontmatter against the claude.ai custom-skill ``.zip`` uploader.

Why this exists
---------------
The open Agent Skills standard and Claude Code accept arbitrary extra frontmatter
keys (this suite deliberately ships ``compatibility`` to document each skill's target
runtime / required env). But the **claude.ai** custom-skill ``.zip`` validator has
historically rejected any top-level frontmatter key outside a fixed whitelist
(anthropics/skills#37, Oct 2025):

    {name, description, license, allowed-tools, metadata}

If claude.ai upload is a supported distribution channel, a single *unexpected* key
fails the upload for **every** skill at once. This script makes that failure mode
visible and catchable in CI before a user hits it.

Two facts it encodes:

* ``CLAUDEAI_WHITELIST`` — the keys the claude.ai uploader accepts.
* ``KNOWN_KEYS`` — the whitelist PLUS the one extra key this suite intentionally and
  uniformly carries (``compatibility``). Anything outside ``KNOWN_KEYS`` is *drift*:
  a new non-whitelisted key that nobody signed off on, which would silently break
  claude.ai uploads. ``--strict`` fails only on drift, so the deliberate
  ``compatibility`` field is preserved while accidental key-creep is caught.

Modes
-----
    python3 scripts/check_claudeai_compat.py             # report per-skill non-whitelist keys
    python3 scripts/check_claudeai_compat.py --strict    # exit non-zero on UNEXPECTED (drift) keys
    python3 scripts/check_claudeai_compat.py --json       # machine-readable
    python3 scripts/check_claudeai_compat.py --package OUT # write claude.ai-safe SKILL.md copies

``--package`` writes, for every skill, a copy of its ``SKILL.md`` with all
non-whitelisted top-level frontmatter keys stripped, under
``OUT/<domain>/<skill>/SKILL.md`` (plus ``references/``/``scripts/`` copied verbatim),
so the tree can be zipped and uploaded to claude.ai without rejection. Single-file,
stdlib-only.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

# The keys the claude.ai custom-skill .zip uploader accepts (anthropics/skills#37).
CLAUDEAI_WHITELIST = frozenset({"name", "description", "license", "allowed-tools", "metadata"})

# The extra top-level key(s) this suite intentionally, uniformly ships. Everything in
# KNOWN_KEYS is "expected"; anything outside it is unreviewed drift.
INTENTIONAL_EXTRA = frozenset({"compatibility"})
KNOWN_KEYS = CLAUDEAI_WHITELIST | INTENTIONAL_EXTRA


def top_level_keys(skill_md: Path) -> list[str]:
    """Return the top-level (column-0) frontmatter keys of a SKILL.md, in order.

    Nested keys under a block (e.g. ``metadata.skill-author``) are intentionally NOT
    returned — the claude.ai whitelist applies to top-level keys only.
    """
    lines = skill_md.read_text(encoding="utf-8").split("\n")
    if not lines or lines[0].strip() != "---":
        return []
    keys: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if not line or line[0] in " \t#":
            continue  # blank, indented (nested), or comment
        key, _, _ = line.partition(":")
        key = key.strip()
        if key:
            keys.append(key)
    return keys


def _strip_non_whitelisted(skill_md_text: str) -> str:
    """Return SKILL.md text with all non-whitelisted top-level frontmatter keys removed.

    Removes the offending ``key:`` line and any immediately-following indented block
    lines that belong to it. Body and whitelisted keys are untouched.
    """
    lines = skill_md_text.split("\n")
    if not lines or lines[0].strip() != "---":
        return skill_md_text
    # Find frontmatter bounds.
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return skill_md_text

    out = [lines[0]]
    i = 1
    while i < end:
        line = lines[i]
        is_top = bool(line) and line[0] not in " \t#"
        if is_top:
            key = line.partition(":")[0].strip()
            if key and key not in CLAUDEAI_WHITELIST:
                i += 1
                # drop any indented continuation block belonging to this key
                while i < end and (not lines[i] or lines[i][0] in " \t"):
                    i += 1
                continue
        out.append(line)
        i += 1
    out.extend(lines[end:])
    return "\n".join(out)


def skill_files() -> list[Path]:
    return sorted(SKILLS_DIR.rglob("SKILL.md"))


def scan() -> list[dict]:
    rows = []
    for p in skill_files():
        keys = top_level_keys(p)
        non_wl = [k for k in keys if k not in CLAUDEAI_WHITELIST]
        drift = [k for k in keys if k not in KNOWN_KEYS]
        rows.append({
            "skill": str(p.relative_to(REPO_ROOT)),
            "keys": keys,
            "non_whitelisted": non_wl,   # informational: known extras like `compatibility`
            "drift": drift,              # unexpected: fails --strict
        })
    return rows


def package(out_dir: Path) -> int:
    out_dir = out_dir.resolve()
    n = 0
    for p in skill_files():
        rel = p.relative_to(SKILLS_DIR)          # e.g. databases/alterlab-pubmed/SKILL.md
        dest = out_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(_strip_non_whitelisted(p.read_text(encoding="utf-8")), encoding="utf-8")
        # Copy bundled resource dirs verbatim so the packaged skill still resolves.
        for sub in ("references", "scripts", "evals"):
            src_sub = p.parent / sub
            if src_sub.is_dir():
                shutil.copytree(src_sub, dest.parent / sub, dirs_exist_ok=True)
        n += 1
    print(f"Wrote {n} claude.ai-safe skill(s) to {out_dir} "
          f"(non-whitelisted top-level keys stripped: {sorted(INTENTIONAL_EXTRA)}).")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero if any skill carries an UNEXPECTED (drift) top-level key")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--package", metavar="OUTDIR", default=None,
                    help="write claude.ai-safe SKILL.md copies (non-whitelist keys stripped) to OUTDIR")
    args = ap.parse_args(argv)

    if args.package:
        return package(Path(args.package))

    rows = scan()
    drift_rows = [r for r in rows if r["drift"]]

    if args.json:
        print(json.dumps({
            "whitelist": sorted(CLAUDEAI_WHITELIST),
            "intentional_extra": sorted(INTENTIONAL_EXTRA),
            "total_skills": len(rows),
            "with_drift": len(drift_rows),
            "rows": rows,
        }, indent=2))
    else:
        extra_counts: dict[str, int] = {}
        for r in rows:
            for k in r["non_whitelisted"]:
                extra_counts[k] = extra_counts.get(k, 0) + 1
        print("claude.ai custom-skill .zip frontmatter whitelist check")
        print(f"  whitelist         : {sorted(CLAUDEAI_WHITELIST)}")
        print(f"  intentional extra : {sorted(INTENTIONAL_EXTRA)} (Claude-Code/SDK only; "
              "stripped by --package for claude.ai upload)")
        print(f"  skills scanned    : {len(rows)}")
        print(f"  non-whitelist keys in use: "
              f"{ {k: extra_counts[k] for k in sorted(extra_counts)} }")
        if drift_rows:
            print("\nUNEXPECTED (drift) keys — these would break claude.ai uploads and are "
                  "not the sanctioned `compatibility`:")
            for r in drift_rows:
                print(f"  {r['skill']}: {r['drift']}")
        else:
            print("\nNo drift: every skill's top-level keys are within the known set "
                  f"{sorted(KNOWN_KEYS)}.")

    return 1 if (args.strict and drift_rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
