#!/usr/bin/env python3
"""Generate docs/agents-and-teams.md — a first-class catalog of the suite's subagents & teams.

The core pipeline already ships ~35 first-class subagent definitions
(``skills/core/**/agents/*.md``), but they were only discoverable by walking the tree. Peers
like Agent Almanac pair skills with an explicit **agents + teams** layer; this makes ours
just as legible by:

1. cataloguing every core subagent (grouped by its host skill) from its own frontmatter, and
2. formalizing the **teams** — the named multi-agent compositions the pipeline actually runs
   (the reviewer panel, the research team, the writing team, the pipeline orchestrator) — as
   structured, validated data. Each team lists its member agents and its orchestration
   pattern. A team that names an agent which does not exist on disk fails ``--strict``.

Deterministic output (no timestamps) so CI can enforce currency:

    python3 scripts/gen_agents_catalog.py            # (re)write docs/agents-and-teams.md
    python3 scripts/gen_agents_catalog.py --check     # fail if the catalog is stale
    python3 scripts/gen_agents_catalog.py --strict     # fail if a team names a missing agent

Single-file, stdlib-only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CORE_DIR = REPO_ROOT / "skills" / "core"
OUT = REPO_ROOT / "docs" / "agents-and-teams.md"

# The named compositions the pipeline runs. Members are agent file stems under the host
# skill's agents/ dir. Curated (the orchestration semantics live in the SKILL bodies) but
# validated against disk, so a rename/removal breaks CI instead of rotting silently.
TEAMS = [
    {
        "name": "Research Team",
        "skill": "alterlab-deep-research",
        "orchestration": "6-phase pipeline: question framing → architecture → verified search "
                         "→ synthesis with adversarial checkpoints → ethics/editorial review → compile",
        "purpose": "Turn a raw topic into a verified, cited synthesis with devil's-advocate and "
                   "risk-of-bias checkpoints.",
        "members": [
            "research_question_agent", "research_architect_agent", "source_verification_agent",
            "synthesis_agent", "devils_advocate_agent", "risk_of_bias_agent",
            "meta_analysis_agent", "ethics_review_agent", "editor_in_chief_agent",
            "report_compiler_agent", "bibliography_agent",
        ],
    },
    {
        "name": "Writing Team",
        "skill": "alterlab-paper-writer",
        "orchestration": "sequential draft pipeline: intake → literature strategy → structure → "
                         "argument → draft → figures + citation compliance → peer read → revision → "
                         "bilingual abstract → format",
        "purpose": "Turn research materials into a publishable IMRaD draft with bilingual abstract "
                   "and multi-format output.",
        "members": [
            "intake_agent", "literature_strategist_agent", "structure_architect_agent",
            "argument_builder_agent", "draft_writer_agent", "visualization_agent",
            "citation_compliance_agent", "peer_reviewer_agent", "revision_coach_agent",
            "abstract_bilingual_agent", "formatter_agent",
        ],
    },
    {
        "name": "Reviewer Panel",
        "skill": "alterlab-paper-reviewer",
        "orchestration": "field analyst configures the panel → domain / methodology / perspective / "
                         "devil's-advocate reviewers run in parallel → editorial synthesizer merges → "
                         "editor-in-chief issues the decision",
        "purpose": "Multi-perspective peer review of a finished manuscript, auto-configured to the "
                   "detected field, ending in an accept/revise/reject decision letter.",
        "members": [
            "field_analyst_agent", "domain_reviewer_agent", "methodology_reviewer_agent",
            "perspective_reviewer_agent", "devils_advocate_reviewer_agent",
            "editorial_synthesizer_agent", "eic_agent",
        ],
    },
    {
        "name": "Pipeline Orchestration",
        "skill": "alterlab-research-pipeline",
        "orchestration": "meta-orchestration across the three teams above, tracking state and "
                         "verifying integrity at each handoff",
        "purpose": "Drive the end-to-end research → write → review → revise → finalize workflow and "
                   "keep the handoff artifacts consistent.",
        "members": [
            "pipeline_orchestrator_agent", "state_tracker_agent", "integrity_verification_agent",
        ],
    },
]


def _agent_meta(md: Path) -> tuple[str, str]:
    text = md.read_text(encoding="utf-8")
    name = re.search(r"^name:\s*(.+)$", text, re.M)
    desc = re.search(r"^description:\s*(.+)$", text, re.M)
    return (
        (name.group(1).strip().strip('"') if name else md.stem),
        (desc.group(1).strip().strip('"') if desc else ""),
    )


def agents_by_skill() -> dict[str, list[tuple[str, str, str]]]:
    """skill -> [(file_stem, name, description)] for every agents/*.md, sorted."""
    out: dict[str, list[tuple[str, str, str]]] = {}
    for agents_dir in sorted(CORE_DIR.glob("*/agents")):
        skill = agents_dir.parent.name
        rows = []
        for md in sorted(agents_dir.glob("*.md")):
            name, desc = _agent_meta(md)
            rows.append((md.stem, name, desc))
        if rows:
            out[skill] = rows
    return out


def missing_team_members() -> list[str]:
    problems: list[str] = []
    for team in TEAMS:
        adir = CORE_DIR / team["skill"] / "agents"
        for stem in team["members"]:
            if not (adir / f"{stem}.md").is_file():
                problems.append(f"{team['name']}: {team['skill']}/agents/{stem}.md missing")
    return problems


def render() -> str:
    by_skill = agents_by_skill()
    total = sum(len(v) for v in by_skill.values())
    L: list[str] = []
    L.append("# Subagents & Teams")
    L.append("")
    L.append("> **Generated** — do not edit by hand. Regenerate with "
             "`python3 scripts/gen_agents_catalog.py`; CI fails if this file is stale.")
    L.append("")
    L.append(f"The core research-to-publication pipeline is a multi-agent system: **{total} "
             f"first-class subagents** across **{len(by_skill)} skills**, composed into named "
             "**teams**. Each subagent is a real artifact under "
             "`skills/core/<skill>/agents/*.md` with its own `name`/`description` frontmatter, "
             "loaded by its host skill; the plugin manifest wires them in via the `agents` field.")
    L.append("")

    L.append("## Teams (named compositions)")
    L.append("")
    for team in TEAMS:
        L.append(f"### {team['name']} — `{team['skill']}`")
        L.append("")
        L.append(f"{team['purpose']}")
        L.append("")
        L.append(f"**Orchestration:** {team['orchestration']}")
        L.append("")
        L.append("**Members:** " + ", ".join(f"`{m}`" for m in team["members"]))
        L.append("")

    L.append("## Full subagent roster")
    L.append("")
    for skill in sorted(by_skill):
        L.append(f"### `{skill}` ({len(by_skill[skill])} agents)")
        L.append("")
        L.append("| Agent | Purpose |")
        L.append("|-------|---------|")
        for _stem, name, desc in by_skill[skill]:
            short = (desc[:160] + "…") if len(desc) > 160 else desc
            L.append(f"| `{name}` | {short} |")
        L.append("")
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="fail if the catalog is out of date")
    ap.add_argument("--strict", action="store_true", help="fail if a team names a missing agent")
    args = ap.parse_args(argv)

    missing = missing_team_members()
    if missing:
        for m in missing:
            print(f"MISSING TEAM MEMBER: {m}", file=sys.stderr)
    rendered = render()

    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != rendered:
            print("docs/agents-and-teams.md is out of date — run: "
                  "python3 scripts/gen_agents_catalog.py", file=sys.stderr)
            return 1
        print(f"docs/agents-and-teams.md up to date ({len(TEAMS)} teams).")
        return 1 if (args.strict and missing) else 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(rendered, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(REPO_ROOT)} ({len(TEAMS)} teams, "
          f"{'members OK' if not missing else 'MISSING MEMBERS'}).")
    return 1 if (args.strict and missing) else 0


if __name__ == "__main__":
    raise SystemExit(main())
