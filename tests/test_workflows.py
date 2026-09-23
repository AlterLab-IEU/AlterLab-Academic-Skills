"""Checks for the Claude Code dynamic-workflow scripts the repo ships.

* Plugin workflows: ``skills/<domain>/workflows/*.js`` (run as ``/alterlab-<domain>:<name>``).
* Maintainer workflows: ``.claude/workflows/*.js`` (run as ``/<name>`` inside this repo).

Every script goes through ``scripts/workflow_dryrun.mjs``, which validates the pure-literal
``meta`` block, compiles the body, rejects runtime-forbidden calls, and executes the whole control
flow against a mocked runtime (schema-conforming fake agent results) in three fake-data modes so
both sides of each branch run. Skipped when Node.js is not installed.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DRYRUN = REPO_ROOT / "scripts" / "workflow_dryrun.mjs"
PLUGIN_WORKFLOWS = sorted(REPO_ROOT.glob("skills/*/workflows/*.js"))
MAINTAINER_WORKFLOWS = sorted((REPO_ROOT / ".claude" / "workflows").glob("*.js"))
ALL_WORKFLOWS = PLUGIN_WORKFLOWS + MAINTAINER_WORKFLOWS
NODE = shutil.which("node")

# Representative arguments per workflow. A new workflow needs an entry here so the dry run
# exercises its real input path.
SAMPLE_ARGS: dict[str, object] = {
    "citation-audit": {"path": "paper.md", "mailto": "lab@example.edu"},
    "review-panel": {"path": "paper.pdf", "venue": "PLOS ONE"},
    "claim-stress-test": {"path": "paper.md"},
    "systematic-review-screening": {"question": "Does mindfulness training reduce burnout in nurses?", "databases": ["pubmed", "openalex"]},
    "rebuttal": {"manuscript": "paper.docx", "reviews": ["reviewer1.pdf", "reviewer2.pdf"]},
    "grant-mock-panel": {"path": "proposal.pdf", "funder": "NIH", "mechanism": "R01"},
    "literature-map": {"topic": "LLM-assisted qualitative coding"},
    "skill-freshness-audit": {"domains": ["databases"]},
}
# Workflows that must refuse to start without their required input.
REQUIRES_ARGS = {
    "citation-audit", "review-panel", "claim-stress-test", "systematic-review-screening",
    "rebuttal", "grant-mock-panel", "literature-map",
}

needs_node = pytest.mark.skipif(NODE is None, reason="Node.js not installed")


def _dryrun(script: Path, args: object | None, mode: str) -> dict:
    cmd = [NODE, str(DRYRUN), str(script), "" if args is None else json.dumps(args), mode]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=REPO_ROOT)
    line = (proc.stdout.strip().splitlines() or ["{}"])[-1]
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return {"ok": False, "error": proc.stdout + proc.stderr}


def test_workflows_discovered() -> None:
    assert PLUGIN_WORKFLOWS, "no plugin workflow scripts found under skills/*/workflows/"


@pytest.mark.parametrize("script", ALL_WORKFLOWS, ids=lambda p: p.stem)
def test_has_sample_args(script: Path) -> None:
    assert script.stem in SAMPLE_ARGS, f"add representative args for {script.stem} to SAMPLE_ARGS"


@needs_node
@pytest.mark.parametrize("mode", ["a", "b", "mixed"])
@pytest.mark.parametrize("script", ALL_WORKFLOWS, ids=lambda p: p.stem)
def test_dry_run(script: Path, mode: str) -> None:
    result = _dryrun(script, SAMPLE_ARGS.get(script.stem), mode)
    assert result.get("ok"), f"{script.relative_to(REPO_ROOT)} [{mode}]: {result.get('error')}"
    assert result["agents"] >= 1


@needs_node
@pytest.mark.parametrize("script", [p for p in ALL_WORKFLOWS if p.stem in REQUIRES_ARGS], ids=lambda p: p.stem)
def test_refuses_to_run_without_input(script: Path) -> None:
    result = _dryrun(script, None, "a")
    assert not result.get("ok"), f"{script.stem} should stop with a usage message when args are missing"
    assert script.stem in result.get("error", ""), "the usage message should name the workflow"


@pytest.mark.parametrize("script", PLUGIN_WORKFLOWS, ids=lambda p: p.stem)
def test_plugin_workflow_is_documented(script: Path) -> None:
    """Each plugin workflow appears in its domain skill's catalog and has a staged playbook."""
    domain = script.parent.parent
    plugin = f"alterlab-{domain.name}"
    skills = [p for p in domain.glob("*/SKILL.md")]
    assert skills, f"{domain.name} ships workflows but no skill documents them"
    text = "\n".join(p.read_text(encoding="utf-8") for p in skills)
    assert f"/{plugin}:{script.stem}" in text, f"{script.stem} is missing from the {domain.name} skill's workflow table"
    playbooks = [p.parent / "references" / f"{script.stem}.md" for p in skills]
    assert any(p.is_file() for p in playbooks), f"no references/{script.stem}.md playbook for the non-workflow fallback"
