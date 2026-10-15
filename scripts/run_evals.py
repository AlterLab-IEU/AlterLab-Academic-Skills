#!/usr/bin/env python3
"""Validate (and optionally behaviorally grade) per-skill eval files.

Every skill ships an eval file at ``skills/<domain>/<skill>/evals/evals.json``. Evals are
how we answer the loudest objection to academic skills — *"these are just prompts with no
evals"* — with something executable. This script is the executable check.

Two modes:

* **Default / ``--strict`` (validation).** Discover every skill dir, validate its
  ``evals/evals.json`` against ``docs/evals.schema.json`` *and* the coverage convention
  (>=3 ``should_trigger`` cases + >=1 ``should_not_trigger`` near-miss per skill), and report
  per skill. A skill with no eval file at all is a violation. ``--strict`` exits non-zero if
  any skill is in violation; without it the exit code is always 0 (report-only).

* **``--behavioral``.** Actually exercise the *skill*, not bare Claude. For every eval this
  mode (1) injects the target skill's ``SKILL.md`` into the call via
  ``claude --append-system-prompt <contents>`` so the model is primed with the skill;
  (2) materializes any eval ``files`` fixtures to a temp dir and references them in the
  prompt; (3) runs each eval **N=3 times** and takes a **majority verdict** to absorb judge
  non-determinism; (4) evaluates the structured ``assertions`` deterministically —
  ``output_contains`` as a case-insensitive substring check, ``should_trigger`` /
  ``should_not_trigger`` by asking the judge whether the response actually *engages* with the
  skill's workflow vs. *declines and names the right sibling skill*; and (5) additionally
  reports a **bare-vs-skill delta** per eval (same prompt with no skill injected) so we can
  see whether the SKILL.md changed behavior at all. The ``behavior`` rubric clause and the
  whole-response ``expected_output`` are still LLM-judged. The judge/target model follows the
  ``ALTERLAB_MODEL`` convention — see ``skills/core/shared/model_env.md``; the model id is
  **never** hardcoded as a call argument (only the dated default constant below). Slow and
  environment-specific, so this is not run per-PR in CI.

  Isolation: every call runs from a fresh temporary directory with ``--safe-mode
  --disable-slash-commands --strict-mcp-config`` (no CLAUDE.md, plugins, skills, hooks or MCP
  servers), so the bare arm is genuinely bare; the skilled arm gets the skill's files in
  ``./skill/`` (never its ``evals/``) and the task fixtures in ``./fixtures/``. Auth is the
  CLI's normal login — run it inside an authenticated Claude Code environment.

  Each case ends in one outcome: PASS, FAIL, INCONCLUSIVE (answered but no settled verdict),
  REFUSED (runner usage-policy refusal), INFRA_ERROR (CLI/auth/timeout/missing fixture), or
  NOT_RUN (run aborted). Exit codes: 0 = passed (EVERY selected case PASS); 1 = a case
  failed; 2 = blocked (no usable verdict at all); 3 = partial (some cases unverdicted). JSON
  results go to ``eval-results/`` (``--results-dir``).

Dependency-light by design: standard library ``json`` / ``subprocess`` plus ``jsonschema``.
``jsonschema`` is optional — if it is not importable the validator falls back to an
equivalent built-in structural check, so the script runs in a bare ``uv run`` env.

    uv run python scripts/run_evals.py             # validate all, per-skill report
    uv run python scripts/run_evals.py --strict    # non-zero exit on any violation
    uv run --with jsonschema python scripts/run_evals.py --strict   # full schema validation
    uv run python scripts/run_evals.py --behavioral                 # skill-injected grading (needs claude CLI)
    uv run python scripts/run_evals.py --behavioral --skill citation-verifier --runs 3
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
SCHEMA_PATH = REPO / "docs" / "evals.schema.json"

# Coverage convention (see docs/evals.md "Conventions"):
MIN_TRIGGERS = 3
MIN_NEGATIVES = 1

# --- Model convention -------------------------------------------------------------------
# AlterLab model convention — default reviewed 2026-09-23; override via ALTERLAB_MODEL.
# See skills/core/shared/model_env.md before changing the default. Never inline a bare id.
DEFAULT_MODEL = "claude-opus-5-5"


def alterlab_model() -> str:
    """Return the model id to use: $ALTERLAB_MODEL if set/non-empty, else the dated default."""
    return os.environ.get("ALTERLAB_MODEL") or DEFAULT_MODEL


# --- Discovery --------------------------------------------------------------------------
def skill_dirs() -> list[Path]:
    """Every skill directory (one that contains a SKILL.md), sorted by path."""
    return sorted(p.parent for p in SKILLS.rglob("SKILL.md"))


def eval_path(skill_dir: Path) -> Path:
    return skill_dir / "evals" / "evals.json"


def parse_shard(spec: str | None) -> tuple[int, int] | None:
    """Parse an ``i/n`` shard spec into (i, n). Returns None for no sharding."""
    if not spec:
        return None
    i_str, _, n_str = spec.partition("/")
    i, n = int(i_str), int(n_str)
    if n < 1 or not (0 <= i < n):
        raise ValueError(f"--shard must be i/n with 0<=i<n (got {spec!r})")
    return (i, n)


def target_dirs(skill_filter: str | None, shard: tuple[int, int] | None) -> list[Path]:
    """Skill dirs to grade after applying the name filter, then a deterministic shard.

    Sharding splits a slow CLI-graded run into deterministic parts (``--shard 3/7``) so the
    corpus can be graded across several sittings without grading every skill at once.
    """
    dirs = [d for d in skill_dirs() if not (skill_filter and skill_filter not in d.name)]
    if shard:
        i, n = shard
        dirs = [d for k, d in enumerate(dirs) if k % n == i]
    return dirs


# --- Schema validation ------------------------------------------------------------------
def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def schema_errors(data: object) -> list[str]:
    """Validate ``data`` against docs/evals.schema.json.

    Uses ``jsonschema`` (Draft 2020-12) when importable; otherwise falls back to a built-in
    structural check that enforces the same load-bearing constraints (required keys, kebab
    ids, assertion type/value coupling). Returns a list of human-readable error strings.
    """
    try:
        from jsonschema import Draft202012Validator  # type: ignore
    except ModuleNotFoundError:
        return _structural_errors(data)
    validator = Draft202012Validator(_load_schema())
    errs = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    out = []
    for e in errs:
        loc = "/".join(str(p) for p in e.path) or "<root>"
        out.append(f"{loc}: {e.message}")
    return out


_KEBAB = __import__("re").compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_TRIGGER_TYPES = {"should_trigger", "should_not_trigger"}
_STRING_TYPES = {"output_contains", "behavior"}
_ASSERTION_TYPES = _TRIGGER_TYPES | _STRING_TYPES


def _structural_errors(data: object) -> list[str]:
    """jsonschema-free fallback mirroring docs/evals.schema.json's load-bearing rules."""
    errs: list[str] = []
    if not isinstance(data, dict):
        return ["<root>: must be a JSON object"]
    for key in ("skill", "evals"):
        if key not in data:
            errs.append(f"<root>: missing required key {key!r}")
    skill = data.get("skill")
    if isinstance(skill, str):
        if not _KEBAB.match(skill):
            errs.append(f"skill: {skill!r} is not kebab-case")
    elif "skill" in data:
        errs.append("skill: must be a string")
    evals = data.get("evals")
    if not isinstance(evals, list):
        if "evals" in data:
            errs.append("evals: must be an array")
        return errs
    if not evals:
        errs.append("evals: must have at least one item")
    seen_ids: set[str] = set()
    for i, e in enumerate(evals):
        where = f"evals/{i}"
        if not isinstance(e, dict):
            errs.append(f"{where}: must be an object")
            continue
        for key in ("id", "prompt", "expected_output"):
            v = e.get(key)
            if key not in e:
                errs.append(f"{where}: missing required key {key!r}")
            elif not isinstance(v, str) or not v:
                errs.append(f"{where}/{key}: must be a non-empty string")
        eid = e.get("id")
        if isinstance(eid, str) and eid:
            if not _KEBAB.match(eid):
                errs.append(f"{where}/id: {eid!r} is not kebab-case")
            if eid in seen_ids:
                errs.append(f"{where}/id: duplicate id {eid!r}")
            seen_ids.add(eid)
        for j, a in enumerate(e.get("assertions", []) or []):
            aw = f"{where}/assertions/{j}"
            if not isinstance(a, dict):
                errs.append(f"{aw}: must be an object")
                continue
            atype, aval = a.get("type"), a.get("value")
            if atype not in _ASSERTION_TYPES:
                errs.append(f"{aw}/type: {atype!r} not in {sorted(_ASSERTION_TYPES)}")
                continue
            if atype in _TRIGGER_TYPES and aval is not True:
                errs.append(f"{aw}/value: {atype} must have value true")
            if atype in _STRING_TYPES and (not isinstance(aval, str) or not aval):
                errs.append(f"{aw}/value: {atype} must be a non-empty string")
    return errs


# --- Convention check -------------------------------------------------------------------
def _count_triggers(data: dict) -> tuple[int, int]:
    """Return (#should_trigger, #should_not_trigger) assertions across all evals."""
    pos = neg = 0
    for e in data.get("evals", []) or []:
        if not isinstance(e, dict):
            continue
        for a in e.get("assertions", []) or []:
            if not isinstance(a, dict):
                continue
            if a.get("type") == "should_trigger" and a.get("value") is True:
                pos += 1
            elif a.get("type") == "should_not_trigger" and a.get("value") is True:
                neg += 1
    return pos, neg


def convention_errors(data: dict) -> list[str]:
    pos, neg = _count_triggers(data)
    errs: list[str] = []
    if pos < MIN_TRIGGERS:
        errs.append(f"only {pos} should_trigger case(s) (>={MIN_TRIGGERS} required)")
    if neg < MIN_NEGATIVES:
        errs.append(f"only {neg} should_not_trigger near-miss(es) (>={MIN_NEGATIVES} required)")
    return errs


@dataclass
class SkillResult:
    skill: str
    rel: str
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_skill(skill_dir: Path) -> SkillResult:
    """Validate one skill's eval file: existence + schema + convention."""
    skill = skill_dir.name
    f = eval_path(skill_dir)
    rel = str(f.relative_to(REPO))
    res = SkillResult(skill=skill, rel=rel)
    if not f.exists():
        res.errors.append("no eval file (skills/.../evals/evals.json missing)")
        return res
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        res.errors.append(f"invalid JSON: {e}")
        return res
    res.errors.extend(schema_errors(data))
    if isinstance(data, dict):
        # 'skill' field should match the directory name (caught loosely; schema already
        # enforces kebab-case). A mismatch is a real authoring bug worth surfacing.
        declared = data.get("skill")
        if isinstance(declared, str) and declared != skill:
            res.errors.append(f"skill field {declared!r} != directory name {skill!r}")
        res.errors.extend(convention_errors(data))
    return res


def validate_all() -> list[SkillResult]:
    return [validate_skill(d) for d in skill_dirs()]


# --- Behavioral grading -----------------------------------------------------------------
# Sentinel returned by _claude when a call could not produce a gradeable answer. Treated as a
# non-verdict (counts toward neither PASS nor FAIL in the majority vote) so a flaky CLI run or
# a skill that legitimately stalls on live tool use does not silently masquerade as a FAIL.
_NO_ANSWER = "<no-answer>"

# A _NO_ANSWER subtype: the runner environment (the `claude` CLI's usage-policy classifier)
# *refused* the prompt before the skill could be exercised — distinct from a timeout or a
# crash. Common on benign biomedical / clinical / genomics prompts via the Claude Code CLI,
# which applies a conservative dual-use classifier the raw API does not. Surfaced separately
# so an environment refusal is never silently scored as a generic inconclusive, and so a
# corpus whose prompts are mostly refused is loudly visible rather than reading as "0 failed".
_REFUSED = f"{_NO_ANSWER} ENV-REFUSED"
# Signatures of the CLI usage-policy refusal — printed to *stdout* with a non-zero exit.
_REFUSAL_SIGNATURES = ("violate our Usage Policy", "unable to respond to this request")

# Per-case outcomes. Only PASS and FAIL are usable verdicts; the other three say *why* a case
# could not be graded, and none of them can make a run read as successful.
PASS, FAIL = "PASS", "FAIL"
INCONCLUSIVE = "INCONCLUSIVE"  # answered, but the judges could not settle a verdict (tie / NA)
REFUSED = "REFUSED"            # the runner environment refused the prompt
INFRA_ERROR = "INFRA_ERROR"    # CLI missing/failed/timed out, auth error, missing fixture
NOT_RUN = "NOT_RUN"            # selected but never attempted (run aborted early)
OUTCOMES = (PASS, FAIL, INCONCLUSIVE, REFUSED, INFRA_ERROR, NOT_RUN)

# --- Isolated CLI execution ---------------------------------------------------------------
# Every behavioral / activation / judge call runs the claude CLI from a fresh temporary working
# directory with customizations disabled, so neither arm is primed by this repository's
# CLAUDE.md or by AlterLab plugins installed on the machine:
#   --safe-mode               no CLAUDE.md, installed plugins, hooks, MCP servers, custom agents
#   --disable-slash-commands  no skills at all (the skill under test arrives only through
#                             --append-system-prompt, and only in the skilled arm)
#   --strict-mcp-config       no MCP servers from any configuration
#   --no-session-persistence  nothing written to the session store
# Auth is the CLI's normal login (a Claude Code session or ANTHROPIC_API_KEY). `--bare` would be
# stricter still, but it ignores OAuth logins and requires an API key, so it is not used.
ISOLATION_FLAGS = ("--safe-mode", "--disable-slash-commands", "--strict-mcp-config",
                   "--no-session-persistence")


@dataclass
class CallResult:
    """One claude CLI call. ``text`` is the answer, or a _NO_ANSWER marker when there is none."""
    text: str
    outcome: str  # "answer" | "refused" | "infra_error"
    error: str = ""  # redacted diagnostic when outcome != "answer"
    duration_ms: int | None = None
    cost_usd: float | None = None
    usage: dict | None = None
    num_turns: int | None = None
    permission_denials: int | None = None  # tool calls the permission rules refused


# Accumulates CLI usage for the current run (answer and judge calls alike). Reset per run.
_USAGE: dict = {"calls": 0, "duration_ms": 0, "cost_usd": 0.0, "cost_reported_calls": 0}


def _reset_usage() -> None:
    _USAGE.update(calls=0, duration_ms=0, cost_usd=0.0, cost_reported_calls=0)


# Diagnostics must be actionable without leaking credentials: strip anything token-shaped.
_SECRET_PATTERNS = (
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{6,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{8,}"),
    re.compile(r"(?i)\b(api[_-]?key|token|secret|password|authorization)\b\s*[=:]\s*\S+"),
    re.compile(r"[A-Za-z0-9+_\-]{40,}"),
)


def _redact(text: str) -> str:
    for pat in _SECRET_PATTERNS:
        text = pat.sub("[REDACTED]", text)
    return text


_DIAGNOSES = (
    (("invalid api key", "not logged in", "please run /login", "authentication", "401",
      "oauth"),
     "authentication failed — log in to Claude Code (`claude`, then /login); in CI, set the "
     "ANTHROPIC_API_KEY repo secret"),
    (("rate limit", "rate_limit", "429", "usage limit", "overloaded", "529"),
     "rate or usage limit — wait and re-run, or lower --runs / grade fewer skills"),
    (("credit balance", "billing"), "billing/credit problem on the account the CLI uses"),
    (("timeout",), "the call timed out — raise --timeout or simplify the prompt"),
    (("could not start", "no such file", "not found on path"),
     "the claude CLI is not installed or not on PATH"),
)


def _diagnose(detail: str) -> str:
    low = detail.lower()
    for needles, hint in _DIAGNOSES:
        if any(n in low for n in needles):
            return hint
    return "unrecognized CLI failure — run the printed command by hand to see the full error"


def _parse_cli_json(stdout: str) -> dict | None:
    """The CLI's --output-format json result object, or None if stdout is not that."""
    for line in reversed([ln for ln in stdout.strip().splitlines() if ln.strip()]):
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and ("result" in data or "is_error" in data):
            return data
    return None


def _usage_summary(usage: object) -> dict | None:
    if not isinstance(usage, dict):
        return None
    keys = ("input_tokens", "output_tokens", "cache_read_input_tokens",
            "cache_creation_input_tokens")
    return {k: usage.get(k) for k in keys if k in usage}


def _claude_call(prompt: str, model: str, timeout: int, system: str | None = None,
                 cwd: Path | None = None, extra_args: list[str] | None = None) -> CallResult:
    """Run one prompt through the claude CLI in an isolated working directory.

    When ``system`` is given it is injected via ``--append-system-prompt`` — this is how the
    target skill's SKILL.md is primed into the call so we grade the *skill*, not bare Claude.
    ``cwd`` is the arm's prepared workspace; without one the call runs in a fresh empty
    temporary directory. Errors, timeouts and refusals are returned as structured outcomes
    (never raised), so one bad call degrades to a non-verdict instead of aborting the run.
    ``extra_args`` adds CLI flags such as ``--allowedTools`` (used by scripts/run_benchmark.py).
    """
    cmd = ["claude", "--model", model, *ISOLATION_FLAGS, "--output-format", "json",
           *(extra_args or [])]
    if system:
        cmd += ["--append-system-prompt", system]
    cmd += ["-p", prompt]
    with tempfile.TemporaryDirectory(prefix="alterlab-eval-call-") as fallback_cwd:
        run_dir = str(cwd) if cwd else fallback_cwd
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                                  cwd=run_dir)
        except subprocess.TimeoutExpired:
            _USAGE["calls"] += 1
            return CallResult(f"{_NO_ANSWER} TIMEOUT after {timeout}s", "infra_error",
                              f"timeout after {timeout}s")
        except OSError as exc:
            return CallResult(f"{_NO_ANSWER} could not start claude CLI", "infra_error",
                              _redact(f"could not start claude CLI: {exc}"))
    _USAGE["calls"] += 1
    data = _parse_cli_json(proc.stdout)
    if data:
        if isinstance(data.get("duration_ms"), (int, float)):
            _USAGE["duration_ms"] += int(data["duration_ms"])
        if isinstance(data.get("total_cost_usd"), (int, float)):
            _USAGE["cost_usd"] += float(data["total_cost_usd"])
            _USAGE["cost_reported_calls"] += 1
    denials = (data or {}).get("permission_denials")
    meta = {
        "duration_ms": (data or {}).get("duration_ms"),
        "cost_usd": (data or {}).get("total_cost_usd"),
        "usage": _usage_summary((data or {}).get("usage")),
        "num_turns": (data or {}).get("num_turns"),
        "permission_denials": len(denials) if isinstance(denials, list) else None,
    }
    # The CLI prints usage-policy refusals to stdout and exits non-zero, so check both streams.
    combined = f"{proc.stdout} {proc.stderr}"
    if any(sig in combined for sig in _REFUSAL_SIGNATURES):
        return CallResult(_REFUSED, "refused", "usage-policy refusal by the runner environment",
                          **meta)
    if proc.returncode != 0 or data is None or data.get("is_error"):
        raw = str((data or {}).get("result") or "") or proc.stderr.strip() or proc.stdout.strip()
        detail = _redact(raw)[:300] or "no output"
        return CallResult(f"{_NO_ANSWER} claude CLI exited {proc.returncode}: {detail}",
                          "infra_error", f"claude CLI exited {proc.returncode}: {detail}", **meta)
    text = str(data.get("result", "")).strip()
    if not text:
        return CallResult(f"{_NO_ANSWER} empty response", "infra_error",
                          "claude CLI returned an empty result", **meta)
    return CallResult(text, "answer", **meta)


def _claude(prompt: str, model: str, timeout: int, system: str | None = None) -> str:
    """Text-only wrapper over ``_claude_call`` (used by the judges and the activation harness):
    the answer, or a ``_NO_ANSWER``-prefixed marker (``_REFUSED`` for a usage-policy refusal)."""
    return _claude_call(prompt, model, timeout, system=system).text


def _is_answer(response: str) -> bool:
    """True if ``response`` is a real model answer (not a _NO_ANSWER error/timeout marker)."""
    return bool(response) and not response.startswith(_NO_ANSWER)


def _is_refusal(response: str) -> bool:
    """True if ``response`` is an environment (usage-policy) refusal rather than a real answer."""
    return response.startswith(_REFUSED)


# --- Fixture materialization ------------------------------------------------------------
def missing_fixtures(eval_obj: dict, evals_dir: Path) -> list[str]:
    """On-disk fixtures an eval names that do not exist. A case with a missing fixture is an
    infrastructure error: it is never run without its input and graded as if complete."""
    missing = []
    for item in eval_obj.get("files", []) or []:
        if isinstance(item, str) and not (evals_dir / item).resolve().exists():
            missing.append(item)
    return missing


def materialize_fixtures(eval_obj: dict, evals_dir: Path, dest: Path) -> list[str]:
    """Write every eval ``files`` fixture into ``dest`` and return the materialized paths.

    Two fixture forms are supported (see docs/evals.schema.json):
      * a string  -> path to a fixture file, relative to the eval file's directory; copied.
      * an object  -> {"name", "content"}; the inline content is written verbatim.
    Returns the written paths. A missing on-disk fixture is skipped here; callers must check
    ``missing_fixtures`` first (run_behavioral records such a case as INFRA_ERROR).
    """
    dest.mkdir(parents=True, exist_ok=True)
    out: list[str] = []
    for item in eval_obj.get("files", []) or []:
        if isinstance(item, str):
            src = (evals_dir / item).resolve()
            target = dest / Path(item).name
            if not src.exists():
                continue
            target.write_bytes(src.read_bytes())
            out.append(str(target))
        elif isinstance(item, dict) and item.get("name"):
            target = dest / Path(item["name"]).name
            target.write_text(item.get("content", ""), encoding="utf-8")
            out.append(str(target))
    return out


def build_prompt(eval_obj: dict, fixture_paths: list[str]) -> str:
    """The user prompt sent to claude, with any materialized fixtures referenced by path."""
    prompt = eval_obj["prompt"]
    if fixture_paths:
        listing = "\n".join(f"- {p}" for p in fixture_paths)
        prompt = (
            f"{prompt}\n\n"
            f"The following input file(s) have been provided for this task; read them as "
            f"needed:\n{listing}"
        )
    return prompt


_SKILL_RUNTIME_NOTE = """

---
Evaluation harness note: this skill's bundled files are in ./skill/ (paths written relative to
the skill directory resolve there), shared suite resources, if any, are in ./shared/, and task
input files are in ./fixtures/."""


def prepare_workspace(root: Path, eval_obj: dict, evals_dir: Path,
                      skill_dir: Path | None) -> list[str]:
    """Build one arm's isolated working directory under ``root`` and return the fixture paths
    (relative to ``root``) to cite in the prompt.

    Both arms get the task's fixtures in ``fixtures/``. Only the skilled arm (``skill_dir``
    given) also gets the skill's own files in ``skill/`` — minus ``evals/``, so the model
    never sees expected outputs — and the domain's ``shared/`` resources in ``shared/``. The
    bare arm therefore cannot read the skill, and neither arm sees this repository.
    """
    root.mkdir(parents=True, exist_ok=True)
    written = materialize_fixtures(eval_obj, evals_dir, root / "fixtures")
    if skill_dir is not None:
        shutil.copytree(skill_dir, root / "skill",
                        ignore=shutil.ignore_patterns("evals", "__pycache__", "*.pyc"))
        shared = skill_dir.parent / "shared"
        if shared.is_dir():
            shutil.copytree(shared, root / "shared",
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return [Path(p).relative_to(root).as_posix() for p in written]


# --- Judges -----------------------------------------------------------------------------
_RUBRIC_JUDGE = """You are grading a model response against an expected-behavior rubric.

RUBRIC (what a correct response should do):
{rubric}

ACTUAL RESPONSE:
{response}

Decide whether the ACTUAL RESPONSE satisfies the RUBRIC. Reply with a single line:
VERDICT: PASS
or
VERDICT: FAIL
followed by one sentence of justification."""

_TRIGGER_JUDGE = """A user sent a prompt to an AI assistant. We are checking whether the
assistant treated this prompt as IN-SCOPE for a particular skill.

SKILL UNDER TEST: {skill}
EXPECTED BEHAVIOR FOR THIS PROMPT:
{rubric}

USER PROMPT:
{prompt}

ASSISTANT RESPONSE:
{response}

Question: Did the assistant ENGAGE with the task — i.e. actually start doing the {skill}
workflow (running its checks, producing its outputs, applying its method) rather than
declining, deferring, or redirecting the user to a different/sibling skill or tool?

Answer with a single line:
ENGAGED: YES   (the assistant took on and performed the task itself)
or
ENGAGED: NO    (the assistant declined, deferred, or redirected to something else)
followed by one sentence of justification."""


# A judge that grades what a response DOES, not whether it recites the skill's internal names.
# Many rubrics say a response "invokes" a skill or "states the Iron Law" / "uses the
# Excuse-vs-Reality table"; a correct answer that never names that apparatus failed them, and
# the bare arm could never pass them — so the skill-vs-bare delta partly measured vocabulary.
_RUBRIC_JUDGE_SUBSTANCE = """You are grading a research assistant's response against a rubric.

Grade SUBSTANCE, not vocabulary:
- The rubric may name a skill's internal apparatus (laws, named tables, checklists, phases,
  modes, agents) or say the response "invokes" a skill. The response need not use those names
  or announce any skill. Such a requirement is met if the response does the substantive thing
  it stands for (for example, refuses to treat data-mined results as confirmatory).
- Concrete content the rubric requires IS required: a correct classification or number, a
  specific statement or section, a refusal, a caveat, or naming another skill or tool to
  route the user to.
- If the task depends on input the user did not provide (a file, a list, a text), asking for
  it and saying what will be done with it is correct for the parts that depend on it.
- Anything false, a required step skipped, or a requirement contradicted is a FAIL. Do not
  reward length or confidence.

RUBRIC:
{rubric}

RESPONSE:
{response}

Reply with a single line:
VERDICT: PASS
or
VERDICT: FAIL
followed by one sentence naming the requirement that decided it."""

JUDGES = {"literal": None, "substance": _RUBRIC_JUDGE_SUBSTANCE}  # None = _RUBRIC_JUDGE


def _judge_rubric(rubric: str, response: str, model: str, timeout: int,
                  template: str | None = None) -> tuple[str, str]:
    """LLM-judge a response against a prose rubric. Returns ('PASS'|'FAIL'|'NA', first_line)."""
    if not _is_answer(response):
        return "NA", response
    out = _claude((template or _RUBRIC_JUDGE).format(rubric=rubric, response=response),
                  model, timeout)
    if not _is_answer(out):
        return "NA", out
    m = re.search(r"VERDICT:\s*(PASS|FAIL)\b", out.upper())
    if not m:  # an unparseable judge reply is no verdict — never a silent FAIL (or PASS)
        return "NA", f"judge reply had no VERDICT line: {out.splitlines()[0][:120] if out else ''}"
    return m.group(1), (out.splitlines()[0] if out else "")


def _judge_engaged(skill: str, prompt: str, rubric: str, response: str,
                   model: str, timeout: int) -> tuple[str, str]:
    """LLM-judge whether the response engaged the skill's workflow. Returns ('YES'|'NO'|'NA', ...)."""
    if not _is_answer(response):
        return "NA", response
    out = _claude(
        _TRIGGER_JUDGE.format(skill=skill, prompt=prompt, rubric=rubric, response=response),
        model, timeout,
    )
    if not _is_answer(out):
        return "NA", out
    m = re.search(r"ENGAGED:\s*(YES|NO)\b", out.upper())
    if not m:
        return "NA", f"judge reply had no ENGAGED line: {out.splitlines()[0][:120] if out else ''}"
    return m.group(1), (out.splitlines()[0] if out else "")


# --- Deterministic assertion grading ----------------------------------------------------
def grade_assertions(eval_obj: dict, skill: str, response: str,
                     model: str, timeout: int) -> list[tuple[str, str, str]]:
    """Grade every assertion on one response. Returns (label, 'PASS'|'FAIL'|'NA', detail) list.

    * ``output_contains``  -> deterministic case-insensitive substring check (no LLM).
    * ``should_trigger``  -> the response must ENGAGE the skill's workflow (LLM-judged).
    * ``should_not_trigger`` -> the response must NOT engage (decline/defer); paired
      ``output_contains`` assertions independently verify the right sibling is named.
    * ``behavior``  -> prose rubric clause, LLM-judged.
    """
    results: list[tuple[str, str, str]] = []
    answered = _is_answer(response)
    for a in eval_obj.get("assertions", []) or []:
        if not isinstance(a, dict):
            continue
        atype, aval = a.get("type"), a.get("value")
        if atype == "output_contains":
            if not answered:
                results.append((f"output_contains[{aval!r}]", "NA", "no answer"))
            else:
                hit = isinstance(aval, str) and aval.lower() in response.lower()
                results.append((
                    f"output_contains[{aval!r}]",
                    "PASS" if hit else "FAIL",
                    "substring present" if hit else "substring absent",
                ))
        elif atype in ("should_trigger", "should_not_trigger"):
            engaged, detail = _judge_engaged(
                skill, eval_obj["prompt"], eval_obj.get("expected_output", ""),
                response, model, timeout,
            )
            if engaged == "NA":
                results.append((atype, "NA", detail))
            else:
                want_engaged = atype == "should_trigger"
                ok = (engaged == "YES") == want_engaged
                results.append((atype, "PASS" if ok else "FAIL", detail))
        elif atype == "behavior" and isinstance(aval, str):
            verdict, detail = _judge_rubric(aval, response, model, timeout)
            results.append(("behavior", verdict, detail))
    return results


def _majority(verdicts: list[str]) -> str:
    """Majority verdict over N runs, ignoring 'NA' non-verdicts. Ties / all-NA -> 'NA'."""
    real = [v for v in verdicts if v != "NA"]
    if not real:
        return "NA"
    passes = real.count("PASS")
    fails = real.count("FAIL")
    if passes > fails:
        return "PASS"
    if fails > passes:
        return "FAIL"
    return "NA"  # exact tie -> inconclusive


def _eval_verdict_from_assertions(per_run: list[list[tuple[str, str, str]]]) -> str:
    """Roll N runs of per-assertion results up to one PASS/FAIL/NA eval verdict.

    For each assertion we take the majority verdict across the N runs; the eval passes only if
    every assertion's majority verdict is PASS. Any FAIL -> FAIL; otherwise (some NA, no FAIL,
    not all PASS) -> NA.
    """
    if not per_run or not per_run[0]:
        return "NA"
    n_assertions = len(per_run[0])
    assertion_verdicts: list[str] = []
    for idx in range(n_assertions):
        runs = [run[idx][1] for run in per_run if idx < len(run)]
        assertion_verdicts.append(_majority(runs))
    if any(v == "FAIL" for v in assertion_verdicts):
        return "FAIL"
    if all(v == "PASS" for v in assertion_verdicts):
        return "PASS"
    return "NA"


def _behavioral_status(selected: int, passed: int, failed: int) -> tuple[str, int]:
    """Run status and exit code. A run is ``passed`` only when EVERY selected case produced a
    usable verdict and none failed; any FAIL is ``failed`` (1); no usable verdict at all is
    ``blocked`` (2) — missing credentials, every call refused or timed out, a filter that
    matched nothing; some usable verdicts but not all is ``partial`` (3). Only ``passed`` exits
    0, so an all-inconclusive or infrastructure-failure run can never read as success."""
    if failed:
        return "failed", 1
    if passed == 0:
        return "blocked", 2
    if passed < selected:
        return "partial", 3
    return "passed", 0


def _arm_outcome(calls: list[CallResult], verdict: str, grading_notes: list[str]) -> str:
    """Outcome of one arm from its answer calls, its PASS/FAIL/NA vote, and the NA reasons
    the graders left (a judge call that itself failed is an infrastructure error, not a tie)."""
    if not any(c.outcome == "answer" for c in calls):
        return REFUSED if any(c.outcome == "refused" for c in calls) else INFRA_ERROR
    if verdict in (PASS, FAIL):
        return verdict
    if any(n.startswith(_NO_ANSWER) for n in grading_notes):
        return INFRA_ERROR
    return INCONCLUSIVE


def _frontmatter_value(skill_md: str, key: str) -> str | None:
    if not skill_md.startswith("---"):
        return None
    block = skill_md.split("---", 2)[1] if skill_md.count("---") >= 2 else ""
    m = re.search(rf"^\s*{re.escape(key)}:\s*\"?([^\"\n]+)\"?\s*$", block, re.MULTILINE)
    return m.group(1).strip() if m else None


def _quiet(cmd: list[str], cwd: Path | None = None) -> str | None:
    """stdout of a small metadata command, or None — never raises."""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=cwd)
        return (proc.stdout or "").strip() or None
    except Exception:  # noqa: BLE001 — metadata only; absence is recorded as null
        return None


def _run_metadata(kind: str, model: str, runs: int, timeout: int) -> dict:
    return {
        "schema_version": 1,
        "kind": kind,
        "model": model,
        "model_source": "ALTERLAB_MODEL" if os.environ.get("ALTERLAB_MODEL") else "default",
        "claude_cli_version": _quiet(["claude", "--version"]),
        "repo_commit": _quiet(["git", "rev-parse", "HEAD"], REPO),
        "repo_dirty": bool(_quiet(["git", "status", "--porcelain"], REPO)),
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "runs_per_arm": runs,
        "timeout_s": timeout,
        "isolation": {
            "cli_flags": list(ISOLATION_FLAGS),
            "working_directory": "fresh temporary directory per arm (not this repository)",
            "skilled_arm_files": ["fixtures/", "skill/ (skill files minus evals/)", "shared/"],
            "answer_tools": "the skill's allowed-tools frontmatter, granted to both arms; "
                            "judges get none",
            "bare_arm_files": ["fixtures/"],
        },
    }


def _write_results(results_dir: Path | None, kind: str, payload: dict) -> Path | None:
    if results_dir is None:
        return None
    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = results_dir / f"{kind}-{stamp}.json"
    n = 1
    while path.exists():
        path = results_dir / f"{kind}-{stamp}-{n}.json"
        n += 1
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _behavioral_cases(skill_filter: str | None, shard: tuple[int, int] | None,
                      skill_dir: Path | None) -> tuple[list[dict], int]:
    """(gradeable cases, number of evals skipped for lacking a prompt or rubric)."""
    dirs = [skill_dir] if skill_dir else target_dirs(skill_filter, shard)
    cases: list[dict] = []
    skipped = 0
    for d in dirs:
        f = eval_path(d)
        skill_md_path = d / "SKILL.md"
        if not f.exists() or not skill_md_path.exists():
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        skill_md = skill_md_path.read_text(encoding="utf-8")
        name = _frontmatter_value(skill_md, "name") or d.name
        for e in data.get("evals", []) or []:
            if not e.get("prompt") or not e.get("expected_output"):
                skipped += 1
                continue
            cases.append({"skill": name, "skill_dir": d, "skill_md": skill_md,
                          "skill_version": _frontmatter_value(skill_md, "version"),
                          "allowed_tools": skill_allowed_tools(skill_md),
                          "evals_dir": f.parent, "eval": e})
    return cases, skipped


def skill_allowed_tools(skill_md: str) -> list[str]:
    """The tools a skill's frontmatter pre-approves (``allowed-tools: Read Bash(python:*) …``).

    In Claude Code an active skill's allowed-tools run without a permission prompt, so the
    harness grants exactly that set — to BOTH arms, so the comparison isolates the skill's
    instructions rather than its permissions. Without it, every skill that must run a script
    or query a live service fails by construction (the CLI's print mode denies unapproved
    tools), and the judge scores a correct refusal to answer from memory as a FAIL.
    """
    raw = _frontmatter_value(skill_md, "allowed-tools") or ""
    # Split on spaces/commas outside parentheses: ``Bash(uv run:*)`` is one rule, as Claude
    # Code reads it (checked live 2026-10-15), not ``Bash(uv`` and ``run:*)``.
    return [t for t in re.findall(r"[^\s,(]+(?:\([^)]*\))?", raw) if t]


def _run_arm(prompt: str, model: str, timeout: int, runs: int, workspace: Path,
             eval_obj: dict, skill: str, rubric: str, system: str | None,
             with_assertions: bool, tools: list[str] | None = None) -> dict:
    calls: list[CallResult] = []
    per_run_assertions: list[list[tuple[str, str, str]]] = []
    rubric_votes: list[str] = []
    notes: list[str] = []
    run_records: list[dict] = []
    for i in range(runs):
        call = _claude_call(prompt, model, timeout, system=system, cwd=workspace,
                            extra_args=["--allowedTools", *tools] if tools else None)
        calls.append(call)
        assertions = (grade_assertions(eval_obj, skill, call.text, model, timeout)
                      if with_assertions else [])
        rv, rd = _judge_rubric(rubric, call.text, model, timeout)
        if call.outcome == "answer":
            notes += [d for (_, v, d) in assertions if v == "NA"] + ([rd] if rv == "NA" else [])
        per_run_assertions.append(assertions)
        rubric_votes.append(rv)
        run_records.append({
            "run": i + 1,
            "call_outcome": call.outcome,
            "error": call.error or None,
            "duration_ms": call.duration_ms,
            "num_turns": call.num_turns,
            "permission_denials": call.permission_denials,
            "cost_usd": call.cost_usd,
            "usage": call.usage,
            "rubric_verdict": rv,
            "assertions": [{"assertion": a, "verdict": v, "detail": _redact(str(d))[:300]}
                           for (a, v, d) in assertions],
            "response_excerpt": call.text[:1500] if call.outcome == "answer" else None,
            # Full text, so a run can be re-graded later (e.g. with a revised judge) without
            # repeating the answer calls.
            "response": call.text if call.outcome == "answer" else None,
        })
    rubric_majority = _majority(rubric_votes)
    if with_assertions and eval_obj.get("assertions"):
        assertion_verdict = _eval_verdict_from_assertions(per_run_assertions)
    else:
        assertion_verdict = "PASS" if with_assertions else "NA"  # no assertions: rubric decides
    if not with_assertions:
        verdict = rubric_majority
    elif FAIL in (assertion_verdict, rubric_majority):
        verdict = FAIL
    elif assertion_verdict == PASS and rubric_majority == PASS:
        verdict = PASS
    else:
        verdict = "NA"
    outcome = _arm_outcome(calls, verdict, notes)
    reason = None
    if outcome not in (PASS, FAIL):
        errs = [c.error for c in calls if c.error]
        reason = (errs or notes or ["judges returned no majority verdict"])[0]
        reason = _redact(str(reason))[:300]
    return {
        "outcome": outcome,
        "reason": reason,
        "assertion_verdict": assertion_verdict if with_assertions else None,
        "rubric_majority": rubric_majority,
        "answered_runs": sum(c.outcome == "answer" for c in calls),
        "runs": run_records,
        "_calls": calls,
    }


def _grade_case(case: dict, model: str, timeout: int, runs: int) -> dict:
    e = case["eval"]
    record = {
        "case_id": f"{case['skill']}:{e.get('id', '?')}",
        "skill": case["skill"],
        "skill_version": case["skill_version"],
        "eval_id": e.get("id"),
        "fixtures": [f if isinstance(f, str) else f.get("name") for f in e.get("files", []) or []],
        "allowed_tools": case.get("allowed_tools", []),
    }
    missing = missing_fixtures(e, case["evals_dir"])
    if missing:
        reason = f"missing fixture file(s): {', '.join(missing)}"
        empty = {"outcome": INFRA_ERROR, "reason": reason, "answered_runs": 0, "runs": [],
                 "_calls": []}
        return {**record, "skilled": dict(empty), "bare": dict(empty),
                "rubric_delta": "rubric: INCONCLUSIVE (case not run)"}
    with tempfile.TemporaryDirectory(prefix="alterlab-eval-") as tmp:
        skilled_ws, bare_ws = Path(tmp) / "skilled", Path(tmp) / "bare"
        fixtures = prepare_workspace(skilled_ws, e, case["evals_dir"], case["skill_dir"])
        prepare_workspace(bare_ws, e, case["evals_dir"], None)
        prompt = build_prompt(e, fixtures)
        skilled = _run_arm(prompt, model, timeout, runs, skilled_ws, e, case["skill"],
                           e["expected_output"], case["skill_md"] + _SKILL_RUNTIME_NOTE, True,
                           tools=case.get("allowed_tools"))
        # The bare arm has no skill context, so it cannot carry should_trigger assertions; it is
        # judged on the overall rubric only, which is what the delta compares.
        bare = _run_arm(prompt, model, timeout, runs, bare_ws, e, case["skill"],
                        e["expected_output"], None, False, tools=case.get("allowed_tools"))
    return {**record, "skilled": skilled, "bare": bare,
            "rubric_delta": _delta(bare["rubric_majority"], skilled["rubric_majority"])}


def run_behavioral(skill_filter: str | None, timeout: int, runs: int,
                   shard: tuple[int, int] | None = None, *,
                   results_dir: Path | None = None, skill_dir: Path | None = None,
                   max_infra_streak: int = 6) -> int:
    """Grade each eval by running it in an isolated workspace, skilled arm vs bare arm.

    Per case, the skilled arm gets the skill's SKILL.md via --append-system-prompt plus its
    bundled files; the bare arm gets only the task. Each arm runs ``runs`` times; assertions and
    the rubric are judged per run and majority-voted. Every case ends in exactly one outcome —
    PASS, FAIL, INCONCLUSIVE, REFUSED, INFRA_ERROR, or NOT_RUN — with the first reason printed.
    After ``max_infra_streak`` consecutive infrastructure errors the run aborts and the
    remaining cases are NOT_RUN. Results (case IDs, model, versions, per-run outcomes, baseline
    comparison, usage) are written as JSON to ``results_dir``. Exit code: ``_behavioral_status``.
    """
    model = alterlab_model()
    _reset_usage()
    started = time.monotonic()
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    meta = _run_metadata("behavioral", model, runs, timeout)
    meta["selection"] = {"skill_filter": skill_filter, "skill_dir": str(skill_dir) if skill_dir
                         else None, "shard": f"{shard[0]}/{shard[1]}" if shard else None}
    print("=== BEHAVIORAL EVALUATION (live model calls; not the static schema check) ===")
    print(f"Model: {model} (ALTERLAB_MODEL convention; see skills/core/shared/model_env.md). "
          f"Each case runs {runs}x per arm, skilled vs bare, in isolated temp workspaces "
          f"({' '.join(ISOLATION_FLAGS)}).")

    if shutil.which("claude") is None:
        reason = "the `claude` CLI is not on PATH; behavioral grading needs it"
        print(f"BLOCKED: {reason}.", file=sys.stderr)
        _write_results(results_dir, "behavioral", {**meta, "started_at": started_at,
                       "status": "blocked", "status_reasons": [reason], "summary": {},
                       "cases": []})
        return 2

    cases, skipped = _behavioral_cases(skill_filter, shard, skill_dir)
    if shard:
        print(f"Shard {shard[0]}/{shard[1]} of the corpus.")
    print(f"{len(cases)} case(s) selected"
          + (f"; {skipped} eval(s) skipped for lacking a prompt or rubric" if skipped else "")
          + ".\n")

    records: list[dict] = []
    streak, aborted = 0, None
    for case in cases:
        if aborted:
            not_run = {"outcome": NOT_RUN, "reason": aborted, "answered_runs": 0, "runs": []}
            records.append({"case_id": f"{case['skill']}:{case['eval'].get('id', '?')}",
                            "skill": case["skill"], "skill_version": case["skill_version"],
                            "eval_id": case["eval"].get("id"), "skilled": dict(not_run),
                            "bare": dict(not_run), "rubric_delta": "rubric: INCONCLUSIVE "
                            "(case not run)"})
            continue
        rec = _grade_case(case, model, timeout, runs)
        for call in rec["skilled"].pop("_calls") + rec["bare"].pop("_calls"):
            streak = streak + 1 if call.outcome == "infra_error" else 0
            if streak >= max_infra_streak and not aborted:
                aborted = (f"aborted after {streak} consecutive infrastructure errors "
                           f"({call.error}) — {_diagnose(call.error)}")
        if rec["skilled"]["outcome"] == INFRA_ERROR and not rec["skilled"]["runs"]:
            streak += 1  # a missing fixture also counts toward the breaker
        s, b = rec["skilled"], rec["bare"]
        mark = {PASS: "✓", FAIL: "✗"}.get(s["outcome"], "?")
        why = f" [{s['reason']}]" if s.get("reason") else ""
        print(f"{mark} {rec['case_id']}: skilled={s['outcome']}{why} "
              f"(assertions {s.get('assertion_verdict')}, rubric {s.get('rubric_majority')}) | "
              f"bare={b['outcome']} -> {rec['rubric_delta']}")
        records.append(rec)
        if aborted:
            print(f"ABORTING: {aborted}", file=sys.stderr)

    counts = {o: sum(r["skilled"]["outcome"] == o for r in records) for o in OUTCOMES}
    bare_counts = {o: sum(r["bare"]["outcome"] == o for r in records) for o in OUTCOMES}
    deltas = {"helped": 0, "hurt": 0, "no_delta": 0, "inconclusive": 0}
    for r in records:
        d = r["rubric_delta"]
        key = ("helped" if "HELPED" in d else "hurt" if "HURT" in d
               else "no_delta" if "NO DELTA" in d else "inconclusive")
        deltas[key] += 1
    selected = len(records)
    attempted = selected - counts[NOT_RUN]
    answered = sum(r["skilled"].get("answered_runs", 0) > 0 for r in records)
    usable = counts[PASS] + counts[FAIL]
    status, code = _behavioral_status(selected, counts[PASS], counts[FAIL])
    reasons: list[str] = []
    if status != "passed":
        if selected == 0:
            reasons.append("no case matched the selection")
        if counts[FAIL]:
            reasons.append(f"{counts[FAIL]} case(s) failed")
        if usable < selected:
            reasons.append(f"{selected - usable} of {selected} case(s) produced no usable "
                           "verdict, so the selection is not fully evaluated")
        if aborted:
            reasons.append(aborted)
    first_problem = next((r["skilled"]["reason"] for r in records
                          if r["skilled"]["outcome"] in (INFRA_ERROR, REFUSED)), None)
    summary = {
        "selected": selected, "attempted": attempted, "answered": answered,
        "usable_verdicts": usable,
        "coverage": round(usable / selected, 4) if selected else 0.0,
        "skilled": counts, "bare": bare_counts, "rubric_delta": deltas,
        "skipped_ungradeable_evals": skipped,
    }
    usage = {**_USAGE, "wall_clock_s": round(time.monotonic() - started, 1),
             "cost_note": "total_cost_usd as reported by the claude CLI; on a subscription "
                          "login this is an estimate, not a bill"}
    payload = {**meta, "started_at": started_at,
               "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "status": status, "status_reasons": reasons, "summary": summary,
               "usage": usage, "cases": records}
    path = _write_results(results_dir, "behavioral", payload)

    print(f"\n=== BEHAVIORAL RESULT: {status.upper()} ===")
    print(f"selected {selected} | attempted {attempted} | answered {answered} | usable verdicts "
          f"{usable} ({summary['coverage']:.0%} coverage)")
    print("skilled arm: " + ", ".join(f"{counts[o]} {o}" for o in OUTCOMES))
    print("bare arm:    " + ", ".join(f"{bare_counts[o]} {o}" for o in OUTCOMES))
    print(f"rubric delta (skilled vs bare): {deltas['helped']} helped, {deltas['hurt']} hurt, "
          f"{deltas['no_delta']} no delta, {deltas['inconclusive']} inconclusive")
    cost = (f", ${_USAGE['cost_usd']:.2f} reported by the CLI"
            if _USAGE["cost_reported_calls"] else "")
    print(f"usage: {_USAGE['calls']} CLI call(s), {usage['wall_clock_s']}s wall clock{cost}")
    if path:
        print(f"results: {path.relative_to(REPO) if path.is_relative_to(REPO) else path}")
    if first_problem:
        print(f"First infrastructure/refusal reason: {first_problem} — {_diagnose(first_problem)}",
              file=sys.stderr)
    if status == "blocked":
        print("BLOCKED: no case produced a usable verdict; this run verifies NOTHING about the "
              "skills and exits non-zero.", file=sys.stderr)
    elif status == "partial":
        print("PARTIAL: only some selected cases produced a verdict; this is not a validation "
              "of the selection.", file=sys.stderr)
    if counts[REFUSED]:
        print(f"NOTE: {counts[REFUSED]} case(s) were refused by the runner environment "
              "(usage-policy classifier), not graded against the skill. Common for biomedical/"
              "clinical/genomics prompts via the Claude Code CLI.", file=sys.stderr)
    return code


def _delta(bare: str, skilled: str) -> str:
    """One-line characterization of the bare-vs-skill delta on the overall rubric."""
    if bare == "FAIL" and skilled == "PASS":
        return "rubric: SKILL HELPED (bare FAIL -> skilled PASS)"
    if bare == "PASS" and skilled == "FAIL":
        return "rubric: SKILL HURT (bare PASS -> skilled FAIL)"
    if "NA" in (bare, skilled):
        return f"rubric: INCONCLUSIVE (bare={bare}, skilled={skilled})"
    return f"rubric: NO DELTA (both {bare})"


def _find_eval(case: dict, meta: dict) -> dict | None:
    sel = (meta.get("selection") or {}).get("skill_dir")
    dirs = [Path(sel)] if sel else [d for d in skill_dirs() if d.name == case.get("skill")]
    for d in dirs:
        try:
            data = json.loads(eval_path(d).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for e in data.get("evals", []) or []:
            if e.get("id") == case.get("eval_id"):
                return e
    return None


def regrade_results(path: Path, judge: str, timeout: int,
                    results_dir: Path | None = None) -> dict:
    """Re-judge a behavioral results file's saved responses with another judge template.

    Only judge calls are made. Rubric and ``behavior`` verdicts are re-judged, and
    ``output_contains`` is recomputed; ``should_trigger`` / ``should_not_trigger`` verdicts are
    kept from the original run (their judge does not grade vocabulary). Runs saved without a
    full ``response`` (older files) are left as they were and counted as not re-graded.
    Returns the new results payload, which records every case whose outcome flipped.
    """
    src = json.loads(path.read_text(encoding="utf-8"))
    template = JUDGES[judge]
    model = alterlab_model()
    flips: list[dict] = []
    not_regraded = 0
    for case in src.get("cases", []):
        e = _find_eval(case, src)
        for arm in ("skilled", "bare"):
            a = case.get(arm) or {}
            runs = a.get("runs") or []
            if not runs or e is None:
                continue
            if any(r.get("call_outcome") == "answer" and r.get("response") is None for r in runs):
                not_regraded += 1
                continue
            rubric_votes, per_run, notes = [], [], []
            for r in runs:
                resp = r.get("response") or ""
                answered = r.get("call_outcome") == "answer"
                rv, rd = (_judge_rubric(e["expected_output"], resp, model, timeout, template)
                          if answered else ("NA", r.get("error") or "no answer"))
                r["rubric_verdict_original"] = r.get("rubric_verdict")
                r["rubric_verdict"] = rv
                rubric_votes.append(rv)
                new_asserts = []
                for item in r.get("assertions", []):
                    label = item["assertion"]
                    verdict = item["verdict"]
                    if answered and label.startswith("output_contains["):
                        needle = label[len("output_contains["):-1].strip("'\"")
                        verdict = "PASS" if needle.lower() in resp.lower() else "FAIL"
                    elif answered and label == "behavior":
                        spec = next((x.get("value") for x in e.get("assertions", [])
                                     if x.get("type") == "behavior"), "")
                        verdict, _ = _judge_rubric(spec, resp, model, timeout, template)
                    new_asserts.append({**item, "verdict": verdict,
                                        "verdict_original": item["verdict"]})
                    if verdict == "NA":
                        notes.append(item.get("detail", ""))
                r["assertions"] = new_asserts
                per_run.append([(x["assertion"], x["verdict"], x.get("detail", ""))
                                for x in new_asserts])
            majority = _majority(rubric_votes)
            if arm == "skilled" and e.get("assertions"):
                av = _eval_verdict_from_assertions(per_run)
                verdict = (FAIL if FAIL in (av, majority) else
                           PASS if av == PASS and majority == PASS else "NA")
            else:
                verdict = majority
            answered_any = any(r.get("call_outcome") == "answer" for r in runs)
            new_outcome = (a.get("outcome") if not answered_any else
                           verdict if verdict in (PASS, FAIL) else INCONCLUSIVE)
            if new_outcome != a.get("outcome"):
                flips.append({"case_id": case.get("case_id"), "arm": arm,
                              "from": a.get("outcome"), "to": new_outcome})
            a["outcome_original"], a["outcome"] = a.get("outcome"), new_outcome
            a["rubric_majority"] = majority
        case["rubric_delta"] = _delta((case.get("bare") or {}).get("rubric_majority", "NA"),
                                      (case.get("skilled") or {}).get("rubric_majority", "NA"))
    counts = {o: sum((c.get("skilled") or {}).get("outcome") == o for c in src.get("cases", []))
              for o in OUTCOMES}
    bare = {o: sum((c.get("bare") or {}).get("outcome") == o for c in src.get("cases", []))
            for o in OUTCOMES}
    selected = len(src.get("cases", []))
    status, _code = _behavioral_status(selected, counts[PASS], counts[FAIL])
    payload = {**src, "kind": "behavioral-regrade", "regraded_from": path.name,
               "judge": judge, "status": status, "flips": flips,
               "arms_not_regraded": not_regraded,
               "summary": {**src.get("summary", {}), "skilled": counts, "bare": bare,
                           "usable_verdicts": counts[PASS] + counts[FAIL]}}
    _write_results(results_dir, "regrade", payload)
    return payload


CALIBRATION = REPO / "docs" / "judge_calibration.json"


def calibrate_judge(judges: list[str], timeout: int) -> int:
    """Grade the hand-labelled pairs in docs/judge_calibration.json with each judge; exit 1 if any
    judge disagrees with a label (or returns no verdict), so an untrustworthy judge is caught
    before it grades a sweep."""
    pairs = json.loads(CALIBRATION.read_text(encoding="utf-8"))["pairs"]
    model = alterlab_model()
    bad = 0
    for judge in judges:
        agree = 0
        for pr in pairs:
            got, why = _judge_rubric(pr["rubric"], pr["response"], model, timeout, JUDGES[judge])
            ok = got == pr["expected"]
            agree += ok
            if not ok:
                print(f"  [{judge}] {pr['id']}: expected {pr['expected']}, got {got} — {why[:160]}")
        bad += len(pairs) - agree
        print(f"judge {judge}: {agree}/{len(pairs)} agree with the hand labels")
    return 1 if bad else 0


# --- Activation harness (auto-selection rate) -------------------------------------------
# The description is the trigger surface. This harness measures the metric that matters for
# a 210-skill suite: given a realistic request, does the model *select the right skill from
# its description* when the true skill sits among plausible same-domain distractors? That is
# both the activation rate (Anthropic's bar: 90%+) and, via wrong picks, the cross-firing
# rate. It reuses the `should_trigger` / `should_not_trigger` prompts already in every
# evals.json — turning a static coverage gate into a discovery metric. Needs the claude CLI
# (like --behavioral), so it runs on demand, not per-PR.

_ACTIVATION_JUDGE = """A user sent this request to an assistant that can activate ONE \
specialized skill from a catalog. Pick the single best skill BASED ONLY on the descriptions.

USER REQUEST:
{prompt}

CANDIDATE SKILLS (name — description):
{catalog}

Reply with exactly one line:
CHOICE: <one candidate name verbatim, or none>
then one sentence of justification."""


def _read_name_desc(skill_dir: Path) -> tuple[str, str]:
    """Return (name, description) from a SKILL.md's flat frontmatter (tolerant parse)."""
    lines = (skill_dir / "SKILL.md").read_text(encoding="utf-8").split("\n")
    name = desc = ""
    if not lines or lines[0].strip() != "---":
        return skill_dir.name, ""
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("name:"):
            name = line.partition(":")[2].strip().strip('"')
        elif line.startswith("description:"):
            desc = line.partition(":")[2].strip().strip('"')
    return (name or skill_dir.name), desc


def skill_catalog() -> dict[str, tuple[str, str]]:
    """name -> (category, description) for every skill."""
    cat: dict[str, tuple[str, str]] = {}
    for d in skill_dirs():
        name, desc = _read_name_desc(d)
        cat[name] = (d.parent.name, desc)
    return cat


def _candidates(target: str, catalog: dict[str, tuple[str, str]], n_distractors: int) -> list[str]:
    """target + up to n_distractors same-category siblings (fallback: other categories)."""
    tcat = catalog[target][0]
    siblings = sorted(n for n, (c, _) in catalog.items() if c == tcat and n != target)
    picked = siblings[:n_distractors]
    if len(picked) < n_distractors:  # small domain — pad from the wider corpus
        others = sorted(n for n, (c, _) in catalog.items() if c != tcat and n != target)
        picked += others[: n_distractors - len(picked)]
    return sorted([target, *picked])


def _choose(prompt: str, cand_names: list[str], catalog: dict[str, tuple[str, str]],
            model: str, timeout: int) -> str | None:
    listing = "\n".join(f"- {n}: {catalog[n][1]}" for n in cand_names)
    out = _claude(_ACTIVATION_JUDGE.format(prompt=prompt, catalog=listing), model, timeout)
    if not _is_answer(out):
        return None
    m = re.search(r"CHOICE:\s*(alterlab-[a-z0-9-]+|none)", out, re.IGNORECASE)
    return m.group(1).lower() if m else None


def run_activation(skill_filter: str | None, timeout: int, runs: int, n_distractors: int,
                   shard: tuple[int, int] | None = None, *,
                   results_dir: Path | None = None) -> int:
    """Measure auto-selection rate over should_trigger prompts (with should_not_trigger as a
    cross-fire control). Reports activation rate vs the 90% bar and the cross-fire rate.
    A discovery metric, separate from behavioral grading: it never fails on a low rate, but a
    run in which no prompt got a usable choice is blocked (exit 2), and results are persisted."""
    model = alterlab_model()
    _reset_usage()
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    picks: list[dict] = []
    if shutil.which("claude") is None:
        print("ERROR: the `claude` CLI is not on PATH; the activation harness needs it.",
              file=sys.stderr)
        return 2
    catalog = skill_catalog()
    targets = target_dirs(skill_filter, shard)
    print("=== ACTIVATION HARNESS (live model calls; separate from behavioral grading) ===")
    print(f"Activation harness with model: {model} (ALTERLAB_MODEL convention). "
          f"{runs}x/prompt, {n_distractors} same-domain distractors; majority pick.")
    if shard:
        print(f"Shard {shard[0]}/{shard[1]}: {len(targets)} of {len(skill_dirs())} skills.")
    print()

    hits = cross = miss = 0                    # should_trigger outcomes
    no_answer = 0                              # prompts where every call failed (not a miss)
    neg_ok = neg_bad = 0                       # should_not_trigger outcomes
    per_cat: dict[str, list[int]] = {}         # category -> [hits, total]
    for d in targets:
        f = eval_path(d)
        if not f.exists():
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        target = d.name
        if target not in catalog:
            continue
        cand = _candidates(target, catalog, n_distractors)
        for e in data.get("evals", []) or []:
            kinds = {a.get("type") for a in e.get("assertions", []) or []}
            is_pos = "should_trigger" in kinds
            is_neg = "should_not_trigger" in kinds
            if not (is_pos or is_neg) or not e.get("prompt"):
                continue
            votes = [_choose(e["prompt"], cand, catalog, model, timeout) for _ in range(runs)]
            real = [v for v in votes if v is not None]
            pick = {"case_id": f"{target}:{e.get('id', '?')}", "kind": "positive" if is_pos
                    else "near-miss", "votes": votes}
            picks.append(pick)
            if not real:
                no_answer += 1
                pick["outcome"] = INFRA_ERROR
                continue
            choice = max(set(real), key=real.count)
            pick["choice"] = choice
            if is_pos:
                bucket = per_cat.setdefault(d.parent.name, [0, 0])
                bucket[1] += 1
                if choice == target:
                    hits += 1
                    bucket[0] += 1
                elif choice in cand:
                    cross += 1
                else:
                    miss += 1
            else:  # near-miss: the target should NOT be chosen
                if choice == target:
                    neg_bad += 1
                else:
                    neg_ok += 1

    graded_pos = hits + cross + miss
    rate = (hits / graded_pos * 100) if graded_pos else 0.0
    print("=== Activation (should_trigger) ===")
    print(f"graded: {graded_pos} | correct: {hits} | cross-fired to sibling: {cross} | "
          f"missed/none: {miss}")
    print(f"activation rate: {rate:.1f}%  (Anthropic bar: 90%+)  "
          f"| cross-fire rate: {(cross/graded_pos*100) if graded_pos else 0:.1f}%")
    if per_cat:
        print("per category (correct/total):")
        for c in sorted(per_cat):
            h, t = per_cat[c]
            print(f"  {c:18} {h}/{t}")
    graded_neg = neg_ok + neg_bad
    if graded_neg:
        print("\n=== Cross-fire control (should_not_trigger) ===")
        print(f"graded: {graded_neg} | correctly NOT selected: {neg_ok} | "
              f"wrongly self-selected: {neg_bad} "
              f"({(neg_ok/graded_neg*100):.1f}% correct deferral)")
    if no_answer:
        print(f"\n{no_answer} prompt(s) got no usable answer from the CLI and are excluded "
              "from the rates above.", file=sys.stderr)
    blocked = graded_pos + graded_neg == 0
    payload = {**_run_metadata("activation", model, runs, timeout),
               "started_at": started_at,
               "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "status": "blocked" if blocked else ("partial" if no_answer else "measured"),
               "summary": {"prompts": len(picks), "no_usable_answer": no_answer,
                           "positive": {"graded": graded_pos, "correct": hits,
                                        "cross_fired": cross, "missed": miss,
                                        "activation_rate": round(rate / 100, 4)},
                           "near_miss": {"graded": graded_neg, "correctly_deferred": neg_ok,
                                         "wrongly_selected": neg_bad},
                           "per_category": per_cat},
               "distractors": n_distractors, "usage": dict(_USAGE), "picks": picks}
    path = _write_results(results_dir, "activation", payload)
    if path:
        print(f"results: {path.relative_to(REPO) if path.is_relative_to(REPO) else path}")
    if blocked:
        print("BLOCKED: no prompt produced a usable choice; this run measures NOTHING and "
              "exits non-zero.", file=sys.stderr)
        return 2
    # A discovery metric, not a gate: never fail the run on activation rate.
    return 0


# --- Validation reporting ---------------------------------------------------------------
def run_validation(strict: bool) -> int:
    results = validate_all()
    using_jsonschema = "jsonschema" in sys.modules or _jsonschema_available()
    bad = [r for r in results if not r.ok]
    print("=== SCHEMA & COVERAGE VALIDATION (static; no model calls) ===")
    for r in results:
        if r.ok:
            print(f"✓ {r.skill}")
        else:
            print(f"✗ {r.skill}: {'; '.join(r.errors)}")
    print(f"\n{len(results)} skill(s); {len(bad)} with issues; "
          f"{len(results) - len(bad)} clean.")
    print(f"Schema validation: {'jsonschema (full)' if using_jsonschema else 'built-in fallback'}"
          f" — run with `uv run --with jsonschema ...` for full Draft 2020-12 validation.")
    n_evals = n_fixture_evals = n_fixture_skills = 0
    for d in skill_dirs():
        try:
            evals = json.loads(eval_path(d).read_text(encoding="utf-8")).get("evals", []) or []
        except (OSError, json.JSONDecodeError):
            continue
        with_files = [e for e in evals if e.get("files")]
        n_evals += len(evals)
        n_fixture_evals += len(with_files)
        n_fixture_skills += bool(with_files)
    print(f"{n_evals} eval case(s); {n_fixture_evals} supply input-file fixtures "
          f"(in {n_fixture_skills} skill(s)).")
    print("This checks structure and trigger coverage only — it says nothing about whether a "
          "skill behaves correctly. Behavioral grading: --behavioral; activation: --activation.")
    return 1 if (bad and strict) else 0


def _jsonschema_available() -> bool:
    try:
        import jsonschema  # noqa: F401  # type: ignore
        return True
    except ModuleNotFoundError:
        return False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero if any skill violates the schema or coverage convention")
    ap.add_argument("--behavioral", action="store_true",
                    help="shell each eval prompt to the claude CLI and LLM-judge expected_output")
    ap.add_argument("--activation", action="store_true",
                    help="measure auto-selection rate: does the model pick the right skill "
                         "from its description among same-domain distractors (needs claude CLI)")
    ap.add_argument("--distractors", type=int, default=6,
                    help="(activation) number of same-domain sibling distractors per prompt "
                         "(default 6)")
    ap.add_argument("--skill", metavar="SUBSTR", default=None,
                    help="(behavioral/activation) only grade skills whose dir name contains SUBSTR")
    ap.add_argument("--timeout", type=int, default=600,
                    help="(behavioral/activation) per-claude-call timeout in seconds (default 600)")
    ap.add_argument("--runs", type=int, default=3,
                    help="(behavioral/activation) times to run each eval per arm; majority "
                         "verdict wins (default 3)")
    ap.add_argument("--results-dir", metavar="DIR", default=str(REPO / "eval-results"),
                    help="(behavioral/activation) write machine-readable JSON results here "
                         "(default: eval-results/, git-ignored); pass '' to skip")
    ap.add_argument("--skill-dir", metavar="DIR", default=None,
                    help="(behavioral) grade the skill in DIR (SKILL.md + evals/evals.json), "
                         "which may live outside skills/ — e.g. a benchmark or a test fixture")
    ap.add_argument("--max-infra-errors", type=int, default=6,
                    help="(behavioral) abort after this many consecutive infrastructure errors; "
                         "remaining cases are NOT_RUN (default 6)")
    ap.add_argument("--regrade", metavar="RESULTS_JSON", nargs="+", default=None,
                    help="re-judge saved responses in behavioral results file(s); judge calls only")
    ap.add_argument("--calibrate-judge", action="store_true",
                    help="grade docs/judge_calibration.json with both judges (judge calls only)")
    ap.add_argument("--judge", choices=sorted(JUDGES), default="substance",
                    help="(regrade) judge template: substance (default) or literal (original)")
    ap.add_argument("--shard", metavar="i/n", default=None,
                    help="(behavioral/activation) grade only a deterministic shard of skills "
                         "(e.g. 2/7) to split a long run into several sittings")
    args = ap.parse_args(argv)

    try:
        shard = parse_shard(args.shard)
    except ValueError as exc:
        ap.error(str(exc))

    results_dir = Path(args.results_dir) if args.results_dir else None
    if args.calibrate_judge:
        return calibrate_judge(sorted(JUDGES), args.timeout)
    if args.regrade:
        flipped = 0
        for f in args.regrade:
            res = regrade_results(Path(f), args.judge, args.timeout, results_dir)
            flipped += len(res["flips"])
            print(f"{Path(f).name}: {res['status']} | skilled {res['summary']['skilled']} | "
                  f"{len(res['flips'])} flip(s), {res['arms_not_regraded']} arm(s) not regraded")
        print(f"total flips: {flipped}")
        return 0
    if args.behavioral and args.activation:
        ap.error("choose one of --behavioral / --activation, not both")
    if args.behavioral:
        if args.runs < 1:
            ap.error("--runs must be >= 1")
        return run_behavioral(args.skill, args.timeout, args.runs, shard,
                              results_dir=results_dir,
                              skill_dir=Path(args.skill_dir).resolve() if args.skill_dir else None,
                              max_infra_streak=max(1, args.max_infra_errors))
    if args.activation:
        if args.runs < 1:
            ap.error("--runs must be >= 1")
        if args.distractors < 1:
            ap.error("--distractors must be >= 1")
        return run_activation(args.skill, args.timeout, args.runs, args.distractors, shard,
                              results_dir=results_dir)
    return run_validation(args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
