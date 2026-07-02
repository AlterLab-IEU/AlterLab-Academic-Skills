#!/usr/bin/env python3
"""Generate docs/portability.md — what transfers to other Agent-Skills runtimes.

The Agent Skills format is a cross-platform open standard, so most of this suite runs
unchanged on any conformant runtime (Codex, Cursor, Gemini CLI, the SDK, …). But a few
fields and bundled assets are Claude-Code/SDK-specific. This doc states, per field and per
bundled asset, what is **portable core** vs **Claude-Code/SDK-specific**, and lists exactly
which skills carry Claude-only enhancements — so a Codex/Cursor/Gemini user knows what
transfers before installing.

Deterministic output (no timestamps) so CI can enforce currency:

    python3 scripts/gen_portability.py            # (re)write docs/portability.md
    python3 scripts/gen_portability.py --check     # fail if the doc is stale

Single-file, stdlib-only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
OUT = REPO_ROOT / "docs" / "portability.md"

# (field/asset, tier, note). Tiers: "core" | "open" | "claude".
PORTABILITY_ROWS = [
    ("`name` frontmatter", "core", "Required by the open standard; identical everywhere."),
    ("`description` frontmatter", "core", "The trigger surface; required by the open standard."),
    ("Markdown body", "core", "Plain instructions; runtime-agnostic."),
    ("`references/*.md`", "core", "Loaded-on-demand detail; plain Markdown, fully portable."),
    ("`scripts/*.py`", "core", "Plain Python helpers; run anywhere Python is available."),
    ("`license` frontmatter", "core", "Open standard, SPDX-style."),
    ("`allowed-tools` frontmatter", "open", "In the open standard, but tool names/scoping "
     "(e.g. `Bash(python:*)`) are Claude-Code idioms other runtimes may map differently."),
    ("`metadata` frontmatter", "open", "Open standard permits a metadata block; the "
     "`skill-author`/`version` keys are an AlterLab convention."),
    ("`compatibility` frontmatter", "claude", "Valid in the open standard and Claude Code, but "
     "rejected by the claude.ai uploader — stripped via "
     "`scripts/check_claudeai_compat.py --package`."),
    ("`.mcp.json`", "claude", "MCP is portable to any MCP host, but here it is wired via the "
     "Claude plugin manifest (domain-level)."),
    ("`agents/*.md`", "claude", "Claude Code subagents; the composition (see "
     "docs/agents-and-teams.md) is Claude-Code/SDK-specific."),
    ("`commands/`", "claude", "Claude Code slash commands; not part of the portable core."),
    ("`hooks/hooks.json`", "claude", "Claude Code hooks; Claude-Code-specific."),
]

_TIER_LABEL = {
    "core": "✅ Portable core",
    "open": "🟨 Open standard, Claude-leaning",
    "claude": "🟦 Claude-Code / SDK",
}


def scan() -> dict:
    skills = [p.parent for p in SKILLS_DIR.rglob("SKILL.md")]
    with_scripts = sorted(d.name for d in skills if (d / "scripts").is_dir())
    with_refs = sorted(d.name for d in skills if (d / "references").is_dir())
    with_agents = sorted(d.name for d in skills if (d / "agents").is_dir())
    with_commands = sorted(d.name for d in skills if (d / "commands").is_dir())
    domain_mcp = sorted(p.parent.name for p in SKILLS_DIR.glob("*/.mcp.json"))
    domain_hooks = sorted(p.parent.name for p in SKILLS_DIR.glob("*/hooks"))
    return {
        "total": len(skills),
        "with_scripts": with_scripts,
        "with_refs": with_refs,
        "with_agents": with_agents,
        "with_commands": with_commands,
        "domain_mcp": domain_mcp,
        "domain_hooks": domain_hooks,
    }


def render() -> str:
    s = scan()
    claude_only = sorted(set(s["with_agents"]) | set(s["with_commands"]))
    L: list[str] = []
    L.append("# Portability")
    L.append("")
    L.append("> **Generated** — do not edit by hand. Regenerate with "
             "`python3 scripts/gen_portability.py`; CI fails if this file is stale.")
    L.append("")
    L.append(f"All **{s['total']}** skills are authored on the cross-platform "
             "[Agent Skills open standard](https://agentskills.io). Every skill's **required "
             "trigger surface — `name`, `description`, and the Markdown body — is 100% "
             "portable** and runs unchanged on any conformant runtime (Codex, Cursor, Gemini "
             "CLI, the Claude Agent SDK, …). The table below states what else transfers.")
    L.append("")
    L.append("## What transfers")
    L.append("")
    L.append("| Field / asset | Portability | Notes |")
    L.append("|---------------|-------------|-------|")
    for field, tier, note in PORTABILITY_ROWS:
        L.append(f"| {field} | {_TIER_LABEL[tier]} | {note} |")
    L.append("")
    L.append("## By the numbers")
    L.append("")
    L.append(f"- **{s['total']}/{s['total']}** skills: portable-core frontmatter only "
             "(`name`/`description` required; plus the `compatibility` convention).")
    L.append(f"- **{len(s['with_refs'])}** bundle `references/*.md` — portable Markdown.")
    L.append(f"- **{len(s['with_scripts'])}** bundle `scripts/*.py` — portable plain Python.")
    L.append(f"- **{len(s['with_agents'])}** bundle Claude Code `agents/` and "
             f"**{len(s['with_commands'])}** bundle `commands/` — Claude-Code/SDK-specific.")
    L.append(f"- Domain-level Claude extras: `.mcp.json` in "
             f"{', '.join('`'+c+'`' for c in s['domain_mcp'])}; "
             f"`hooks/` in {', '.join('`'+c+'`' for c in s['domain_hooks'])}.")
    L.append("")
    L.append("## Skills with Claude-Code-only enhancements")
    L.append("")
    L.append("These skills carry Claude Code subagents and/or slash commands. Their core "
             "skill (name + description + body + references + scripts) still ports; only the "
             "orchestration extras do not:")
    L.append("")
    for name in claude_only:
        extras = []
        if name in s["with_agents"]:
            extras.append("agents")
        if name in s["with_commands"]:
            extras.append("commands")
        L.append(f"- `{name}` ({', '.join(extras)})")
    L.append("")
    L.append("To produce a maximally-portable copy for a non-Claude runtime, run "
             "`python3 scripts/check_claudeai_compat.py --package OUT` (strips the "
             "`compatibility` key) and drop the `agents/`, `commands/`, `hooks/`, and "
             "`.mcp.json` assets your target runtime does not consume.")
    L.append("")
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="fail if docs/portability.md is stale")
    args = ap.parse_args(argv)

    rendered = render()
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != rendered:
            print("docs/portability.md is out of date — run: python3 scripts/gen_portability.py",
                  file=sys.stderr)
            return 1
        print("docs/portability.md up to date.")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(rendered, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(REPO_ROOT)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
