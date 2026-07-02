# Portability

> **Generated** — do not edit by hand. Regenerate with `python3 scripts/gen_portability.py`; CI fails if this file is stale.

All **239** skills are authored on the cross-platform [Agent Skills open standard](https://agentskills.io). Every skill's **required trigger surface — `name`, `description`, and the Markdown body — is 100% portable** and runs unchanged on any conformant runtime (Codex, Cursor, Gemini CLI, the Claude Agent SDK, …). The table below states what else transfers.

## What transfers

| Field / asset | Portability | Notes |
|---------------|-------------|-------|
| `name` frontmatter | ✅ Portable core | Required by the open standard; identical everywhere. |
| `description` frontmatter | ✅ Portable core | The trigger surface; required by the open standard. |
| Markdown body | ✅ Portable core | Plain instructions; runtime-agnostic. |
| `references/*.md` | ✅ Portable core | Loaded-on-demand detail; plain Markdown, fully portable. |
| `scripts/*.py` | ✅ Portable core | Plain Python helpers; run anywhere Python is available. |
| `license` frontmatter | ✅ Portable core | Open standard, SPDX-style. |
| `allowed-tools` frontmatter | 🟨 Open standard, Claude-leaning | In the open standard, but tool names/scoping (e.g. `Bash(python:*)`) are Claude-Code idioms other runtimes may map differently. |
| `metadata` frontmatter | 🟨 Open standard, Claude-leaning | Open standard permits a metadata block; the `skill-author`/`version` keys are an AlterLab convention. |
| `compatibility` frontmatter | 🟦 Claude-Code / SDK | Valid in the open standard and Claude Code, but rejected by the claude.ai uploader — stripped via `scripts/check_claudeai_compat.py --package`. |
| `.mcp.json` | 🟦 Claude-Code / SDK | MCP is portable to any MCP host, but here it is wired via the Claude plugin manifest (domain-level). |
| `agents/*.md` | 🟦 Claude-Code / SDK | Claude Code subagents; the composition (see docs/agents-and-teams.md) is Claude-Code/SDK-specific. |
| `commands/` | 🟦 Claude-Code / SDK | Claude Code slash commands; not part of the portable core. |
| `hooks/hooks.json` | 🟦 Claude-Code / SDK | Claude Code hooks; Claude-Code-specific. |

## By the numbers

- **239/239** skills: portable-core frontmatter only (`name`/`description` required; plus the `compatibility` convention).
- **231** bundle `references/*.md` — portable Markdown.
- **130** bundle `scripts/*.py` — portable plain Python.
- **4** bundle Claude Code `agents/` and **4** bundle `commands/` — Claude-Code/SDK-specific.
- Domain-level Claude extras: `.mcp.json` in `core`, `databases`; `hooks/` in `core`.

## Skills with Claude-Code-only enhancements

These skills carry Claude Code subagents and/or slash commands. Their core skill (name + description + body + references + scripts) still ports; only the orchestration extras do not:

- `alterlab-citation-verifier` (commands)
- `alterlab-deep-research` (agents, commands)
- `alterlab-paper-reviewer` (agents, commands)
- `alterlab-paper-writer` (agents)
- `alterlab-research-pipeline` (agents, commands)

To produce a maximally-portable copy for a non-Claude runtime, run `python3 scripts/check_claudeai_compat.py --package OUT` (strips the `compatibility` key) and drop the `agents/`, `commands/`, `hooks/`, and `.mcp.json` assets your target runtime does not consume.

