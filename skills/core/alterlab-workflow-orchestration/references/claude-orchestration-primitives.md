# Claude Code + Agent SDK Orchestration Primitives (verified reference)

Verified against the official documentation on **2026-09-23** (Claude Code v2.1.280):

- `code.claude.com/docs/en/agents` — Run agents in parallel (the overview)
- `code.claude.com/docs/en/sub-agents` — Create custom subagents
- `code.claude.com/docs/en/workflows` — Orchestrate subagents at scale with dynamic workflows
- `code.claude.com/docs/en/agent-teams` — Orchestrate teams of Claude Code sessions
- `code.claude.com/docs/en/plugins-reference` — plugin components, including `workflows`
- `code.claude.com/docs/en/agent-sdk/overview` — Agent SDK

Load this file and quote it rather than restating orchestration mechanics from memory; version
gates are noted inline because the behavior changed several times during 2026.

## Table of Contents

1. [Choosing a mechanism](#1-choosing-a-mechanism)
2. [Subagents](#2-subagents)
3. [Subagent frontmatter fields](#3-subagent-frontmatter-fields)
4. [Built-in subagents](#4-built-in-subagents)
5. [Nesting, background, and fork mode](#5-nesting-background-and-fork-mode)
6. [Dynamic workflows](#6-dynamic-workflows)
7. [Agent teams (experimental)](#7-agent-teams-experimental)
8. [Claude Agent SDK](#8-claude-agent-sdk)
9. [Limits and gotchas](#9-limits-and-gotchas)

---

## 1. Choosing a mechanism

The overview page lists five ways to run work in parallel. The deciding question is **who holds
the plan**:

| Mechanism | Who decides what runs next | Where intermediate results live | Scale |
|---|---|---|---|
| Subagents | Claude, turn by turn | Claude's context (summaries) | a few delegated tasks per turn |
| Agent view (`claude agents`, research preview) | you | each background session | independent sessions you dispatch |
| Agent teams (experimental) | a lead agent, turn by turn | a shared task list + messages | a handful of long-running peers |
| **Dynamic workflows** | **the script** | **script variables** | **dozens to hundreds of agents per run** |
| Projects (claude.ai/code, beta) | Claude, across cloud threads | the project | long-running work over days |

> "A workflow moves the plan into code. … A workflow script holds the loop, the branching, and
> the intermediate results itself, so Claude's context holds only the final answer."

## 2. Subagents

> "Each subagent runs in its own context window with a custom system prompt, specific tool
> access, and independent permissions."

Defined as Markdown files with YAML frontmatter. Scopes, highest priority first: managed
settings, the `--agents` CLI flag (JSON), project `.claude/agents/` (every such directory between
the working directory and the repo root; the closest wins), user `~/.claude/agents/`, and a
plugin's agents (namespaced `plugin-name:agent-name`). Identity comes from the `name` field, which
may not contain `:` (reserved for plugin scoping). `/agents` no longer opens an editor panel
(v2.1.198+); ask Claude or edit the files.

Claude delegates when a task matches a subagent's `description`; you can also name it, @-mention
it, or run a whole session as it with `claude --agent <name>`.

## 3. Subagent frontmatter fields

Only `name` and `description` are required.

| Field | Notes |
|---|---|
| `tools` | Comma-separated string (`Read, Grep, Bash`) or YAML list; inherits all tools if omitted. `allowed-tools` is a **skill** field, not a subagent field |
| `disallowedTools` | Removed from the inherited or listed set |
| `model` | `sonnet`, `opus`, `haiku`, `fable`, a full ID such as `claude-opus-5-5`, or `inherit` |
| `permissionMode` | `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan` (`manual` = `default`, v2.1.200+); **ignored for plugin subagents** |
| `maxTurns` | Cap on agentic turns; output returned as partial and resumable (v2.1.246+) |
| `skills` | Skills preloaded in full at startup; unlisted skills stay invocable via the Skill tool |
| `mcpServers`, `hooks` | Scoped to the subagent; **ignored for plugin subagents** |
| `memory` | `user`, `project`, or `local` persistent memory |
| `background` | Always run in the background |
| `effort` | `low` … `max`, overriding the session effort |
| `isolation` | `worktree` for an isolated git checkout |
| `omitClaudeMd` | Start without CLAUDE.md files (v2.1.271+) |
| `color`, `initialPrompt`, `experimental.cacheTtl` | Display color; first turn when run via `--agent` (ignored for plugin subagents); prompt-cache TTL `5m`/`1h` (v2.1.248+) |

> "Subagents receive only this system prompt (plus basic environment details like working
> directory), not the full Claude Code system prompt."

## 4. Built-in subagents

| Agent | Model | Tools | Purpose |
|---|---|---|---|
| **Explore** | inherits the main model (v2.1.198+; on the Claude API capped at Opus) | read-only | file discovery, code search |
| **Plan** | inherits | read-only | research for plan mode |
| **general-purpose** | inherits | all | multi-step exploration and action |

Explore and Plan skip CLAUDE.md. To keep exploration cheap, define a project subagent named
`Explore` with `model: haiku` — it overrides the built-in.

## 5. Nesting, background, and fork mode

- **Nesting is on.** "By default, a subagent can spawn subagents of its own, up to three layers
  below the main conversation." Change with `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` (`1` turns
  nesting off). Keep a subagent from spawning by omitting `Agent` from its `tools`. (History:
  five layers fixed in v2.1.172–216; one layer in v2.1.217–218; three since v2.1.219.)
- **Fork mode** is on by default in interactive sessions (v2.1.232+) and off in `-p` and the
  Agent SDK; `CLAUDE_CODE_FORK_SUBAGENT=1|0` overrides. With it on, Claude can spawn a `fork`
  subagent that inherits the whole conversation (and reuses its prompt cache), and all subagents
  run in the background. Start a forked subagent yourself with `/subtask` (or `/fork` when agent
  view is off); with agent view on, `/fork` copies the session into a new background session.
- **Background vs. foreground**: background subagents run concurrently with permissions already
  granted; `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` forces the foreground.

## 6. Dynamic workflows

> "A dynamic workflow is a JavaScript script that orchestrates many subagents at once. Claude
> writes the script for the task you describe, and a runtime executes it in the background while
> your session stays responsive."

- **Availability:** all paid plans, API access, Bedrock, Google Cloud, Foundry; on Pro, enable in
  `/config`. Disable with `disableWorkflows` / `CLAUDE_CODE_DISABLE_WORKFLOWS=1`.
- **Starting one:** ask for a workflow in your own words, include the keyword `ultracode`, or set
  `/effort ultracode` (v2.1.203+) so Claude plans workflows for every substantive task. Bundled:
  `/deep-research <question>`.
- **Saved workflows:** from `/workflows`, press `s` to save a run's script to
  `.claude/workflows/` (shared with the repo) or `~/.claude/workflows/`; it then runs as
  `/<name>`. **Plugins** ship scripts in a `workflows/` directory (or the `workflows` manifest
  field); they run as `/<plugin>:<meta.name>` — e.g. `/alterlab-workflows:citation-audit`.
- **Script shape:** `export const meta = { name, description, whenToUse?, phases? }` must be the
  first statement and a pure literal. The body is plain JavaScript with top-level `await`:
  `agent(prompt, {schema?, label?, phase?, model?, effort?, isolation?, agentType?})`,
  `parallel(thunks)` (barrier), `pipeline(items, ...stages)` (no barrier), `phase()`, `log()`,
  the `args` global, `budget`, and one-level `workflow()` composition. A `schema` makes the agent
  return validated JSON. `Date.now()`, `Math.random()`, argless `new Date()`, and `import()` are
  unavailable (they would break resume); there is no direct filesystem access — agents read and
  write files.
- **Approval:** a per-run prompt lists the phases (auto mode asks once); in `-p`/SDK use a
  `Workflow` or `Workflow(<name>)` allow rule.
- **Limits:** up to 16 concurrent agents by default (`CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS`,
  v2.1.269+), 4,096 items per `parallel()`/`pipeline()` call, 1,000 agents per run. A size
  guideline (`workflowSizeGuideline`: small < 5, medium < 10, large < 50 agents; default medium)
  steers how big Claude writes them. No mid-run user input: for sign-off between stages, run each
  stage as its own workflow.
- **Resume:** relaunching a stopped run in the same session replays finished agents from cache.

## 7. Agent teams (experimental)

> "Agent teams are experimental and disabled by default. Enable them by setting
> `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`."

A lead session coordinates teammates (separate Claude Code instances, each with its own context)
through a shared task list and direct messaging; you can talk to teammates directly. Teams need an
interactive session — in `-p` and the SDK a named subagent runs as an ordinary subagent. While
enabled, a subagent that Claude *names* launches as a teammate, so teams can form unasked.

The docs' adversarial example (verbatim):

> "Spawn 5 agent teammates to investigate different hypotheses. Have them talk to each other to
> try to disprove each other's theories, like a scientific debate. Update the findings doc with
> whatever consensus emerges."

Teams "use significantly more tokens than a single session"; for sequential or tightly coupled
work, a single session or subagents are more effective.

## 8. Claude Agent SDK

> "The Agent SDK gives you the same tools, agent loop, and context management that power Claude
> Code, programmable in Python and TypeScript."

- Python `claude-agent-sdk` (`query(...)` + `ClaudeAgentOptions`); TypeScript
  `@anthropic-ai/claude-agent-sdk` (`query({ prompt, options })`).
- Subagents: the `agents` option maps names to `AgentDefinition(description, prompt, tools)`;
  include `"Agent"` in `allowed_tools` to auto-approve delegation. Messages from a subagent carry
  `parent_tool_use_id`.
- Sessions: capture `session_id` from the `init` message and `resume` it.
- The SDK loads `.claude/` configuration by default (restrict with `setting_sources` /
  `settingSources`); fork mode and agent teams are off by default there; workflows run through
  the same `Workflow` tool with permission rules instead of a prompt.

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

async def main():
    async for message in query(
        prompt="Use the methodology-reviewer agent to review paper.md",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Glob", "Grep", "Agent"],
            agents={
                "methodology-reviewer": AgentDefinition(
                    description="Reviews study design, measurement, and analysis choices.",
                    prompt="Review the methods of the manuscript you are given; quote the text you critique.",
                    tools=["Read", "Glob", "Grep"],
                )
            },
        ),
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

## 9. Limits and gotchas

- **Fresh context:** a non-fork subagent sees only its delegation prompt — pass the paths,
  criteria, and output format it needs.
- **Results re-enter context:** many verbose subagents still flood the main conversation; ask
  for summaries, or move the loop into a workflow so intermediate results stay in script variables.
- **Plugin subagents ignore** `permissionMode`, `hooks`, `mcpServers`, and `initialPrompt`.
- **Teams:** one team per session, no nested teams, fixed lead, no resumption of in-process
  teammates, split panes need tmux or iTerm2.
- **Workflows:** no mid-run input, no filesystem access from the script, deterministic scripts
  only (no clock or randomness).
- **Match degrees of freedom to fragility:** prose for open exploration; explicit ordered stages,
  a stop condition, and an iteration cap for fragile sequences.
