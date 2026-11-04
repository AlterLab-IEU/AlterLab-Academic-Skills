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
    ("`compatibility` frontmatter", "claude", "Valid in the open standard and Claude Code; "
     "outside the claude.ai uploader whitelist reported in anthropics/skills#37 (not re-tested "
     "here), so it is stripped from the `skill-<name>-<version>.zip` upload archives."),
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
             "`python3 scripts/check_claudeai_compat.py --package OUT` (the claude.ai target "
             "of the packaging helper: `compatibility` stripped, shared files and notices "
             "included) and drop the `agents/`, `commands/`, `hooks/`, and `.mcp.json` assets "
             "your target runtime does not consume.")
    L.append("")
    L += _packaging_section()
    return "\n".join(L) + "\n"


def _packaging_section() -> list[str]:
    """Installation / packaging targets, generated from scripts/build_bundles.py."""
    import build_bundles as bb  # same directory

    index = bb.skill_index()
    shared = {sd.name: sorted(bb.shared_citations(sd)) for sd in bb.skill_dirs()}
    deps = {n: sorted(bb.sibling_dependencies(d, index)) for n, d in sorted(index.items())}
    L: list[str] = []
    L.append("## Installing and packaging")
    L.append("")
    L.append("Every route out of the repository checkout goes through one helper, "
             "`scripts/build_bundles.py`: `scripts/install.sh` calls it, "
             "`.github/workflows/release.yml` calls it to build and verify the release "
             "archives, and `check_claudeai_compat.py --package` calls it.")
    L.append("")
    L.append("| Target | How | Contents | Rewritten on the way |")
    L.append("|--------|-----|----------|----------------------|")
    L.append("| Claude Code plugin | `/plugin install alterlab-<domain>@alterlab-academic-skills`, "
             "or the `alterlab-academic-skills-<version>.zip` marketplace snapshot | the domain "
             "folder is the plugin root | nothing — Claude Code substitutes "
             "`${CLAUDE_PLUGIN_ROOT}` in skill, agent and command content |")
    L.append("| Plain install | `scripts/install.sh [selector …]` into `~/.claude/skills/`, "
             "`~/.agents/skills/` or `--dest` | the selected skills plus the skills they depend "
             "on | `${CLAUDE_PLUGIN_ROOT}` → the absolute install directory |")
    L.append("| Skills bundle | `alterlab-<domain>-<version>.zip`, unzipped into a skills "
             "directory | the domain's skills plus their dependency skills, skill folders at "
             "the archive root; plugin-only components (`.mcp.json`, hooks, dynamic-workflow "
             "scripts, plugin manifests) are not included — they work only in the plugin "
             "| `${CLAUDE_PLUGIN_ROOT}` → `..` |")
    L.append("| claude.ai upload | `skill-<name>-<version>.zip` → Customize ▸ Skills → Upload "
             "a skill | exactly one skill folder | frontmatter reduced to the uploader "
             "whitelist; `${CLAUDE_PLUGIN_ROOT}` → `..` |")
    L.append("")
    L.append("Every installed or packaged skill folder carries the repository `LICENSE`, "
             "`NOTICE` (with the upstream attributions, including the CC-BY-NC-4.0 notice for "
             "the four pipeline skills) and `THIRD_PARTY_NOTICES.md`; each skill keeps its own "
             "`license:` field.")
    L.append("")
    L.append("### Path rules")
    L.append("")
    L.append("- Paths in a skill's Markdown are relative to the skill folder (the one holding "
             "`SKILL.md`). Repository paths such as `skills/<domain>/…` are rejected by the "
             "tests because they resolve in no installed layout.")
    L.append("- A shared handoff file is cited as `shared/<file>`; the skill carries a "
             "byte-identical copy of the canonical file from the core domain's `shared/` "
             "folder at `<skill>/shared/<file>` (`python3 scripts/build_bundles.py "
             "sync-shared`).")
    L.append("- A file in a sibling skill is cited as `../<skill>/<path>`; agents and commands, "
             "which have no skill folder of their own at run time, use "
             "`${CLAUDE_PLUGIN_ROOT}/<skill>/<path>`. Either form makes the sibling a "
             "dependency.")
    L.append("")
    L.append("Skills carrying shared copies:")
    L.append("")
    for name in sorted(n for n, rels in shared.items() if rels):
        L.append(f"- `{name}`: " + ", ".join(f"`{r}`" for r in shared[name]))
    L.append("")
    L.append("Skills that depend on a sibling (installed with it; listed as companions of its "
             "upload archive):")
    L.append("")
    for name in sorted(n for n, d in deps.items() if d):
        L.append(f"- `{name}` → " + ", ".join(f"`{d}`" for d in deps[name]))
    L.append("")
    L.append("### Verified here vs. untested platform behaviour")
    L.append("")
    L.append("Verified by `tests/test_bundles.py`, `tests/test_install.py` and "
             "`tests/test_claudeai_compat.py`, which build into a temporary directory and "
             "inspect the output: archive structure; frontmatter of the upload archives; "
             "presence of shared files and notices; every path reference resolving inside the "
             "archive, the companion archives, or the install directory; dependency skills "
             "installed; byte-for-byte reproducible archives; the limits below; and, where the "
             "`claude` CLI is installed (the test skips otherwise), `claude plugin validate` on "
             "the extracted marketplace snapshot.")
    L.append("")
    L.append("Not tested: whether the live claude.ai uploader accepts these archives, and "
             "where claude.ai places uploaded skills relative to each other (which decides "
             "whether a companion's `../<skill>/` path resolves there). The frontmatter "
             "whitelist comes from anthropics/skills#37 and has not been re-checked against the "
             "live service.")
    L.append("")
    L.append("### Limits")
    L.append("")
    L.append(f"- Upload archives stay under {bb.CLAUDEAI_MAX_UNCOMPRESSED_BYTES // 1_000_000} MB "
             "uncompressed — the limit documented for custom-skill uploads through the Claude "
             "API (platform.claude.com, *Using Agent Skills with the API*). claude.ai does not "
             "publish its own figure, so applying it to claude.ai is unverified.")
    L.append(f"- Upload archives stay at or under {bb.CLAUDEAI_MAX_FILES} files. **Unverified:** "
             "no Anthropic document states a file-count limit; this is a conservative guard "
             "carried over from earlier releases.")
    L.append(f"- `name` ≤ {bb.NAME_MAX} characters of `[a-z0-9-]` without \"anthropic\"/"
             f"\"claude\", `description` ≤ {bb.DESCRIPTION_MAX} characters (platform docs). "
             "The claude.ai help article *How to create custom skills* states a 200-character "
             "description limit, which conflicts with the platform docs and with most "
             "descriptions here; it is unverified and not enforced.")
    L.append("- Skills bundles and the marketplace snapshot are not claude.ai uploads (the "
             "claude.ai help center describes an upload as a ZIP whose root is one skill "
             "folder), so no upload limit applies to them; "
             "`build_bundles.py` keeps every archive under a "
             f"{bb.MAX_ARCHIVE_BYTES // (1024 * 1024)} MB regression ceiling of its own.")
    L.append("")
    return L


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
