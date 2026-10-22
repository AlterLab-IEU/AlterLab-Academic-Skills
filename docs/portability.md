# Portability

> **Generated** — do not edit by hand. Regenerate with `python3 scripts/gen_portability.py`; CI fails if this file is stale.

All **242** skills are authored on the cross-platform [Agent Skills open standard](https://agentskills.io). Every skill's **required trigger surface — `name`, `description`, and the Markdown body — is 100% portable** and runs unchanged on any conformant runtime (Codex, Cursor, Gemini CLI, the Claude Agent SDK, …). The table below states what else transfers.

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
| `compatibility` frontmatter | 🟦 Claude-Code / SDK | Valid in the open standard and Claude Code; outside the claude.ai uploader whitelist reported in anthropics/skills#37 (not re-tested here), so it is stripped from the `skill-<name>-<version>.zip` upload archives. |
| `.mcp.json` | 🟦 Claude-Code / SDK | MCP is portable to any MCP host, but here it is wired via the Claude plugin manifest (domain-level). |
| `agents/*.md` | 🟦 Claude-Code / SDK | Claude Code subagents; the composition (see docs/agents-and-teams.md) is Claude-Code/SDK-specific. |
| `commands/` | 🟦 Claude-Code / SDK | Claude Code slash commands; not part of the portable core. |
| `hooks/hooks.json` | 🟦 Claude-Code / SDK | Claude Code hooks; Claude-Code-specific. |

## By the numbers

- **242/242** skills: portable-core frontmatter only (`name`/`description` required; plus the `compatibility` convention).
- **235** bundle `references/*.md` — portable Markdown.
- **141** bundle `scripts/*.py` — portable plain Python.
- **4** bundle Claude Code `agents/` and **4** bundle `commands/` — Claude-Code/SDK-specific.
- Domain-level Claude extras: `.mcp.json` in `core`, `databases`; `hooks/` in `core`.

## Skills with Claude-Code-only enhancements

These skills carry Claude Code subagents and/or slash commands. Their core skill (name + description + body + references + scripts) still ports; only the orchestration extras do not:

- `alterlab-citation-verifier` (commands)
- `alterlab-deep-research` (agents, commands)
- `alterlab-paper-reviewer` (agents, commands)
- `alterlab-paper-writer` (agents)
- `alterlab-research-pipeline` (agents, commands)

To produce a maximally-portable copy for a non-Claude runtime, run `python3 scripts/check_claudeai_compat.py --package OUT` (the claude.ai target of the packaging helper: `compatibility` stripped, shared files and notices included) and drop the `agents/`, `commands/`, `hooks/`, and `.mcp.json` assets your target runtime does not consume.

## Installing and packaging

Every route out of the repository checkout goes through one helper, `scripts/build_bundles.py`: `scripts/install.sh` calls it, `.github/workflows/release.yml` calls it to build and verify the release archives, and `check_claudeai_compat.py --package` calls it.

| Target | How | Contents | Rewritten on the way |
|--------|-----|----------|----------------------|
| Claude Code plugin | `/plugin install alterlab-<domain>@alterlab-academic-skills`, or the `alterlab-academic-skills-<version>.zip` marketplace snapshot | the domain folder is the plugin root | nothing — Claude Code substitutes `${CLAUDE_PLUGIN_ROOT}` in skill, agent and command content |
| Plain install | `scripts/install.sh [selector …]` into `~/.claude/skills/`, `~/.agents/skills/` or `--dest` | the selected skills plus the skills they depend on | `${CLAUDE_PLUGIN_ROOT}` → the absolute install directory |
| Skills bundle | `alterlab-<domain>-<version>.zip`, unzipped into a skills directory | the domain's skills plus their dependency skills, skill folders at the archive root; plugin-only components (`.mcp.json`, hooks, dynamic-workflow scripts, plugin manifests) are not included — they work only in the plugin | `${CLAUDE_PLUGIN_ROOT}` → `..` |
| claude.ai upload | `skill-<name>-<version>.zip` → Customize ▸ Skills → Upload a skill | exactly one skill folder | frontmatter reduced to the uploader whitelist; `${CLAUDE_PLUGIN_ROOT}` → `..` |

Every installed or packaged skill folder carries the repository `LICENSE`, `NOTICE` (with the upstream attributions, including the CC-BY-NC-4.0 notice for the four pipeline skills) and `THIRD_PARTY_NOTICES.md`; each skill keeps its own `license:` field.

### Path rules

- Paths in a skill's Markdown are relative to the skill folder (the one holding `SKILL.md`). Repository paths such as `skills/<domain>/…` are rejected by the tests because they resolve in no installed layout.
- A shared handoff file is cited as `shared/<file>`; the skill carries a byte-identical copy of the canonical file from the core domain's `shared/` folder at `<skill>/shared/<file>` (`python3 scripts/build_bundles.py sync-shared`).
- A file in a sibling skill is cited as `../<skill>/<path>`; agents and commands, which have no skill folder of their own at run time, use `${CLAUDE_PLUGIN_ROOT}/<skill>/<path>`. Either form makes the sibling a dependency.

Skills carrying shared copies:

- `alterlab-citation-verifier`: `shared/model_env.md`, `shared/schemas/integrity_report.schema.json`
- `alterlab-deep-research`: `shared/handoff_schemas.md`
- `alterlab-markitdown`: `shared/model_env.md`
- `alterlab-neuropixels`: `shared/model_env.md`
- `alterlab-pdf-extract`: `shared/model_env.md`
- `alterlab-research-pipeline`: `shared/handoff_schemas.md`

Skills that depend on a sibling (installed with it; listed as companions of its upload archive):

- `alterlab-citation-verifier` → `alterlab-research-pipeline`
- `alterlab-deep-research` → `alterlab-citation-verifier`
- `alterlab-paper-writer` → `alterlab-deep-research`
- `alterlab-peer-review` → `alterlab-scientific-slides`
- `alterlab-research-pipeline` → `alterlab-citation-verifier`
- `alterlab-results-transparency` → `alterlab-statistical-analysis`

### Verified here vs. untested platform behaviour

Verified by `tests/test_bundles.py`, `tests/test_install.py` and `tests/test_claudeai_compat.py`, which build into a temporary directory and inspect the output: archive structure; frontmatter of the upload archives; presence of shared files and notices; every path reference resolving inside the archive, the companion archives, or the install directory; dependency skills installed; byte-for-byte reproducible archives; the limits below; and, where the `claude` CLI is installed (the test skips otherwise), `claude plugin validate` on the extracted marketplace snapshot.

Not tested: whether the live claude.ai uploader accepts these archives, and where claude.ai places uploaded skills relative to each other (which decides whether a companion's `../<skill>/` path resolves there). The frontmatter whitelist comes from anthropics/skills#37 and has not been re-checked against the live service.

### Limits

- Upload archives stay under 30 MB uncompressed — the limit documented for custom-skill uploads through the Claude API (platform.claude.com, *Using Agent Skills with the API*). claude.ai does not publish its own figure, so applying it to claude.ai is unverified.
- Upload archives stay at or under 200 files. **Unverified:** no Anthropic document states a file-count limit; this is a conservative guard carried over from earlier releases.
- `name` ≤ 64 characters of `[a-z0-9-]` without "anthropic"/"claude", `description` ≤ 1024 characters (platform docs). The claude.ai help article *How to create custom skills* states a 200-character description limit, which conflicts with the platform docs and with most descriptions here; it is unverified and not enforced.
- Skills bundles and the marketplace snapshot are not claude.ai uploads (the claude.ai help center describes an upload as a ZIP whose root is one skill folder), so no upload limit applies to them; `build_bundles.py` keeps every archive under a 30 MB regression ceiling of its own.

