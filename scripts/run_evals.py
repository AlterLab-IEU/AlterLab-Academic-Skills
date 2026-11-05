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
  results (schema_version 2, see docs/evals.md) go to ``eval-results/`` (``--results-dir``).

  Grading (schema v2): both arms are graded on IDENTICAL substantive criteria — the
  ``expected_output`` rubric, ``behavior`` clauses and substantive ``output_contains`` — by the
  judge chosen with ``--judge`` (default ``substance``). Routing (``should_trigger`` /
  ``should_not_trigger``, skilled arm only), skill-vocabulary assertions (needles that only name
  internal skills or apparatus; reported, never gating) and declared ``artifact_checks`` (files
  the arm had to write, checked before its workspace is deleted; scripts/artifact_checks.py)
  are separate dimensions. ``--regrade`` re-judges saved answers with the same rules and the
  same exit codes; ``--audit-rubrics`` lists rubrics that require internal names (no model).

Dependency-light by design: standard library ``json`` / ``subprocess`` plus ``jsonschema``.
``jsonschema`` is optional — if it is not importable the validator falls back to an
equivalent built-in structural check, so the script runs in a bare ``uv run`` env.

    uv run python scripts/run_evals.py             # validate all, per-skill report
    uv run python scripts/run_evals.py --strict    # non-zero exit on any violation
    uv run --with jsonschema python scripts/run_evals.py --strict   # full schema validation
    uv run python scripts/run_evals.py --behavioral                 # skill-injected grading (needs claude CLI)
    uv run python scripts/run_evals.py --behavioral --skill citation-verifier --runs 3
    uv run python scripts/run_evals.py --regrade eval-results/behavioral-*.json --judge substance
    uv run python scripts/run_evals.py --audit-rubrics              # static; no model calls
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(Path(__file__).resolve().parent) not in sys.path:  # sibling module, also when imported
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import artifact_checks  # noqa: E402  (scripts/artifact_checks.py)

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
    # Cross-field artifact rules (a check kind must suit the file type, csv number_within needs
    # a row selector, ...) are beyond the JSON Schema; both validators apply them.
    return out + [x for x in _artifact_errors(data) if x not in out]


def _artifact_errors(data: object) -> list[str]:
    if not isinstance(data, dict) or not isinstance(data.get("evals"), list):
        return []
    return [err for i, e in enumerate(data["evals"]) if isinstance(e, dict)
            and "artifact_checks" in e
            for err in artifact_checks.declaration_errors(e["artifact_checks"],
                                                          f"evals/{i}/artifact_checks")]


_KEBAB = __import__("re").compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_TRIGGER_TYPES = {"should_trigger", "should_not_trigger"}
_STRING_TYPES = {"output_contains", "behavior"}
_ASSERTION_TYPES = _TRIGGER_TYPES | _STRING_TYPES
_REQ = __import__("re").compile(r"^(env|cmd|net|mcp):[A-Za-z0-9_.:-]+$")


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
            if atype == "output_contains" and isinstance(aval, list):
                if not aval or not all(isinstance(x, str) and x for x in aval):
                    errs.append(f"{aw}/value: output_contains list must hold non-empty strings")
            elif atype in _STRING_TYPES and (not isinstance(aval, str) or not aval):
                errs.append(f"{aw}/value: {atype} must be a non-empty string")
    for i, e in enumerate(evals if isinstance(evals, list) else []):
        req = e.get("requires") if isinstance(e, dict) else None
        if req is not None and (not isinstance(req, list) or not all(
                isinstance(r, str) and _REQ.match(r) for r in req)):
            errs.append(f"evals/{i}/requires: each entry must look like env:NAME, cmd:NAME, "
                        "net:HOST or mcp:NAME")
    return errs + _artifact_errors(data)


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
# Newer CLI builds print the API's acceptable-use refusal instead: "API Error: ... can't help
# with this. ... Learn more: https://www.anthropic.com/legal/aup ... Details: `[bio]`". It counts
# only with a failed exit and both markers, so an answer that merely says "can't help" is not one.
_AUP_REFUSAL_MARKERS = ("API Error", "anthropic.com/legal/aup")
_AUP_CATEGORY = re.compile(r"Details: `\[([a-z_-]+)\]`")

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
    denied_tools: list | None = None  # what was refused: "Bash: uv pip install x", ...


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


# Answers can echo the account's e-mail address from the CLI login context, and saved results
# are meant to be shareable, so every address is replaced when a result is written. The
# reserved example domains (RFC 2606/6761) stay: evals use them as placeholders. Grading reads
# the unredacted text in-process; only the files on disk (and so --regrade) see the redaction.
_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@([A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,})")
_EXAMPLE_DOMAIN = re.compile(r"(?i)(?:^|\.)(?:example\.(?:com|org|net|edu)|example|invalid|test|localhost)$")


def _scrub_emails(text):
    if not isinstance(text, str):
        return text
    return _EMAIL.sub(lambda m: m.group(0) if _EXAMPLE_DOMAIN.search(m.group(1))
                      else "[email redacted]", text)


def _redact(text: str) -> str:
    for pat in _SECRET_PATTERNS:
        text = pat.sub("[REDACTED]", text)
    return _scrub_emails(text)


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


# --- Answer-arm confinement ------------------------------------------------------------
# An answer arm is granted the skill's allowed-tools (Write, Edit, Bash, ...). On 2026-10-15
# the bare arm of an alterlab-link-health case ("close out the remaining residual broken
# links") went looking for a repository, found this checkout, and edited 29 files in it. A
# temporary working directory is not a sandbox. Three layers now stand between an arm and the
# repository:
#   1. namespace — on Linux, each CLI call runs in a private mount namespace in which this
#      checkout and every worktree of it are covered by an empty read-only tmpfs;
#   2. scoped grants — a bare Write/Edit/MultiEdit/NotebookEdit grant is rewritten to an
#      absolute rule for the arm's own workspace (checked live: a bare `Write` grant wrote
#      outside the workspace; `Write(//<workspace>/**)` allowed the inside write and denied the
#      outside one), and environment variables that point into the checkout are dropped;
#   3. tripwire — the checkout is fingerprinted before the run and after every case; any
#      change aborts the run as an isolation breach, lists what changed, and reverts nothing.
# Shell grants (Bash, Bash(python:*), Bash(uv run:*)) can still write anywhere the namespace
# does not hide, so on a platform without it run behavioral evals in a disposable checkout.
_PATH_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
_CONFINE: dict = {"request": "auto", "mode": None, "hidden": [], "why": ""}
_TRIPWIRE_ROOT = REPO
# Run inside the namespace, in order: (1) cover each protected path with an empty read-only
# tmpfs (deepest first, so a worktree inside the checkout is covered before its parent);
# (2) give the arm a private temp root that holds only its own workspace — every other arm's
# workspace, a skilled sibling's ./skill/ copy, and other sessions' scratch files lived there
# and arms that search the disk found them; (3) fresh /var/tmp and /dev/shm; (4) cover
# private state dirs (installed plugins and skills, session transcripts) with empty tmpfs.
_HIDE_SCRIPT = (
    'n=$1; shift; i=0; while [ "$i" -lt "$n" ]; do '
    'mount -t tmpfs -o ro,size=4k alterlab-hidden "$1" || exit 97; shift; i=$((i+1)); done; '
    'ws=$1; t=$2; shift 2; '
    'if [ -n "$ws" ]; then '
    '  mount --bind "$ws" /mnt || exit 96; mount -t tmpfs alterlab-tmp "$t" || exit 96; '
    '  mkdir -p "$ws" && mount --bind /mnt "$ws" || exit 96; umount -l /mnt 2>/dev/null; '
    'fi; '
    'for d in /var/tmp /dev/shm; do [ -d "$d" ] && mount -t tmpfs alterlab-scratch "$d"; done; '
    'm=$1; shift; i=0; while [ "$i" -lt "$m" ]; do '
    '[ -d "$1" ] && { mount -t tmpfs alterlab-private "$1" || exit 95; }; shift; i=$((i+1)); '
    'done; exec "$@"')
# What an arm must not read even though it is outside the checkout: the user's installed
# plugins and skills (this suite included — a bare arm would find the SKILL.md it is being
# compared against) and other sessions' transcripts.
_PRIVATE_STATE = ["~/.claude/plugins", "~/.claude/skills", "~/.claude/projects",
                  "~/.claude/todos", "/home/*/.claude/plugins", "/home/*/.claude/skills",
                  "/home/*/.claude/projects", "/home/*/.claude/todos", "/mnt/skills"]


_COLLECT = {"on": False}
_WAIT = {"on": False, "max_s": 6 * 3600, "sleep": time.sleep, "now": None}
_LIMIT_RE = re.compile(r"hit your (?:session |usage |weekly )?limit[^\n]*?resets\s+"
                       r"(\d{1,2})(?::(\d{2}))?\s*([ap]m)\s*\(UTC\)", re.I)


def _limit_wait_seconds(text: str) -> float | None:
    """Seconds until a usage limit the CLI reported resets ('resets 11:30am (UTC)'), plus one
    minute; None when the text is not a limit message."""
    m = _LIMIT_RE.search(text or "")
    if not m:
        return None
    hour, minute, ampm = int(m.group(1)) % 12, int(m.group(2) or 0), m.group(3).lower()
    hour += 12 if ampm == "pm" else 0
    now = (_WAIT["now"] or (lambda: datetime.now(timezone.utc)))()
    reset = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if reset <= now:
        reset = reset.replace(day=now.day) + __import__("datetime").timedelta(days=1)
    return (reset - now).total_seconds() + 60
_NET_CACHE: dict[str, str | None] = {}


def unmet_requirements(eval_obj: dict) -> list[str]:
    """Why this case cannot be judged on this runner (empty when it can). See ``requires`` in
    docs/evals.schema.json; a case with an unmet requirement is NOT_RUN, never FAIL."""
    out = []
    for req in eval_obj.get("requires", []) or []:
        kind, _, name = str(req).partition(":")
        if kind == "env" and not os.environ.get(name):
            out.append(f"environment variable {name} is not set")
        elif kind == "cmd" and shutil.which(name) is None:
            out.append(f"`{name}` is not on PATH")
        elif kind == "mcp":
            out.append(f"MCP server {name} (answer arms run with --strict-mcp-config and none)")
        elif kind == "net":
            if name not in _NET_CACHE:
                import urllib.error
                import urllib.request
                try:
                    urllib.request.urlopen(urllib.request.Request(f"https://{name}/",
                                                                  method="HEAD"), timeout=10)
                    _NET_CACHE[name] = None
                except urllib.error.HTTPError:
                    _NET_CACHE[name] = None  # it answered; the host is reachable
                except Exception as exc:  # noqa: BLE001 — any failure means unreachable here
                    _NET_CACHE[name] = f"{name} is not reachable from this runner ({type(exc).__name__})"
            if _NET_CACHE[name]:
                out.append(_NET_CACHE[name])
    return out


def _endpoint() -> str:
    """Which backend answers: the CLI's own login, or a base URL (e.g. a local model server).

    A base URL on Anthropic's own API host (some managed environments set one) is still the
    login's Claude endpoint; anything else — a proxy, a local server — is labelled by its URL.
    """
    base = os.environ.get("ANTHROPIC_BASE_URL")
    from urllib.parse import urlparse
    u = urlparse(base or "")
    if not base or (u.scheme == "https" and u.hostname == "api.anthropic.com" and not u.port):
        return "claude-cli-login"
    return f"base-url:{u.scheme}://{u.hostname}{':' + str(u.port) if u.port else ''}"


def _protected_paths() -> list[str]:
    """This checkout and every worktree of its repository, deepest first."""
    paths = {str(REPO.resolve())}
    listing = _quiet(["git", "-C", str(REPO), "worktree", "list", "--porcelain"]) or ""
    for line in listing.splitlines():
        if line.startswith("worktree "):
            wt = Path(line[len("worktree "):])
            if wt.is_dir():
                paths.add(str(wt.resolve()))
    return sorted(paths, key=lambda x: (-len(Path(x).parts), x))


def _namespace_prefix(paths: list[str], workspace: str = "") -> list[str]:
    root = hasattr(os, "geteuid") and os.geteuid() == 0
    base = ["unshare", "-m"] if root else ["unshare", "-r", "-m"]
    tmp_root = str(Path(tempfile.gettempdir()).resolve())
    ws = str(Path(workspace).resolve()) if workspace else ""
    if ws and not Path(ws).is_relative_to(tmp_root):
        ws = ""  # only a workspace under the temp root can be carried into the private one
    import glob as _glob
    private = sorted({str(Path(m).resolve()) for p in _PRIVATE_STATE
                      for m in _glob.glob(str(Path(p).expanduser())) if Path(m).is_dir()})
    return [*base, "--propagation", "private", "sh", "-c", _HIDE_SCRIPT, "sh",
            str(len(paths)), *paths, ws, tmp_root, str(len(private)), *private]


def configure_confinement(request: str = "auto") -> str:
    """Pick how answer arms are confined: 'namespace' when a private mount namespace can hide
    the checkout (probed, not assumed), else 'none'. ``request='namespace'`` makes the probe's
    failure fatal; ``request='none'`` skips it."""
    paths = _protected_paths()
    _CONFINE.update(request=request, mode="none", hidden=[], why="not requested")
    if request == "none":
        return "none"
    why = "not Linux" if not sys.platform.startswith("linux") else (
        "`unshare` not found" if not shutil.which("unshare") else "")
    if not why:
        ws = tempfile.mkdtemp(prefix="alterlab-eval-probe-")
        Path(ws, "own.txt").write_text("x")
        top = Path(ws).name
        probe = [*_namespace_prefix(paths, ws), "sh", "-c",
                 'for p in "$@"; do [ -z "$(ls -A "$p")" ] || exit 1; done; '
                 f'[ "$(ls -A {shlex.quote(tempfile.gettempdir())})" = {shlex.quote(top)} ] '
                 f'|| exit 2; [ -f {shlex.quote(ws)}/own.txt ] || exit 3; '
                 f'touch {shlex.quote(ws)}/w || exit 4', "sh", *paths]
        try:
            res = subprocess.run(probe, capture_output=True, text=True, timeout=30)
            why = "" if res.returncode == 0 else (
                f"mount namespace unavailable ({_redact(res.stderr.strip())[:120] or res.returncode})")
        except (OSError, subprocess.TimeoutExpired) as exc:
            why = f"mount namespace probe failed ({exc})"
        finally:
            shutil.rmtree(ws, ignore_errors=True)
    if why and request == "namespace":
        raise SystemExit(f"--isolation namespace requested, but {why}")
    if not why:
        _CONFINE.update(mode="namespace", hidden=paths, why="")
        return "namespace"
    _CONFINE["why"] = why
    return "none"


def _confinement() -> dict:
    if _CONFINE["mode"] is None:
        configure_confinement(_CONFINE["request"])
    return _CONFINE


def _scoped_args(extra_args: list[str], workspace: str) -> list[str]:
    """Rewrite bare path-tool grants to the arm's own workspace (absolute ``//`` rule)."""
    root = "/" + str(Path(workspace).resolve()).lstrip("/")
    return [f"{a}(/{root}/**)" if a in _PATH_TOOLS else a for a in extra_args]


def _arm_env() -> dict:
    """The CLI's environment minus anything that points into the checkout: PATH-like
    variables lose those entries, any other variable naming a protected path is dropped."""
    prot = [str(REPO.resolve()), *_CONFINE.get("hidden", [])]
    env = {}
    for k, v in os.environ.items():
        if not any(pp in v for pp in prot):
            env[k] = v
        elif k.endswith("PATH"):
            env[k] = os.pathsep.join(e for e in v.split(os.pathsep)
                                     if not any(e.startswith(pp) for pp in prot))
    return env


def _repo_fingerprint() -> str | None:
    """HEAD + tracked changes (content) + untracked files (size, mtime) of the checkout."""
    root = str(_TRIPWIRE_ROOT)
    head = _quiet(["git", "-C", root, "rev-parse", "HEAD"])
    if head is None:
        return None
    diff = subprocess.run(["git", "-C", root, "diff", "HEAD", "--binary"], capture_output=True)
    others = _quiet(["git", "-C", root, "ls-files", "--others", "--exclude-standard"]) or ""
    h = hashlib.sha256(head.encode() + diff.stdout)
    for rel in sorted(others.splitlines()):
        try:
            st = (Path(root) / rel).stat()
            h.update(f"{rel}:{st.st_size}:{st.st_mtime_ns}".encode())
        except OSError:
            h.update(rel.encode())
    return h.hexdigest()


def _changed_paths() -> list[str]:
    out = _quiet(["git", "-C", str(_TRIPWIRE_ROOT), "status", "--porcelain",
                  "--untracked-files=all"]) or ""
    return [line[3:] for line in out.splitlines()][:20]


def _denial_summary(d: object) -> str:
    """'Tool: what it tried' for one permission denial the CLI reported."""
    if not isinstance(d, dict):
        return _redact(str(d))[:120]
    inp = d.get("tool_input") if isinstance(d.get("tool_input"), dict) else {}
    what = inp.get("command") or inp.get("file_path") or inp.get("url") or inp.get("path") \
        or json.dumps(inp, ensure_ascii=False)
    return _redact(f"{d.get('tool_name', '?')}: {' '.join(str(what).split())}")[:120]


def _run_contained(cmd: list[str], cwd: str, timeout: int) -> subprocess.CompletedProcess:
    """Run one CLI call in its own session and, when it returns or times out, kill its process
    group and everything else it left running, so nothing an arm started in the background
    outlives the call (a leftover download kept writing into a deep-research workspace and
    crashed its cleanup; leftover training jobs ran for an hour and starved later arms)."""
    _SUBREAPER["on"] = _SUBREAPER["on"] or _become_subreaper()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            cwd=cwd, env=_arm_env(), start_new_session=hasattr(os, "killpg"))
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_group(proc)
        proc.communicate()
        _reap_leftovers()
        raise
    _kill_group(proc)
    _reap_leftovers()
    return subprocess.CompletedProcess(cmd, proc.returncode, out, err)


_SUBREAPER = {"on": False}


def _become_subreaper() -> bool:
    """Linux: make orphans of this process's descendants re-parent to it instead of init.

    Claude Code's Bash tool starts each command in a session of its own, so a job an arm puts
    in the background is out of reach of the call's process group, and is orphaned when the
    CLI exits. As a subreaper, this process still finds it among its descendants."""
    if not sys.platform.startswith("linux"):
        return False
    try:
        import ctypes
        return ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) == 0  # PR_SET_CHILD_SUBREAPER
    except (OSError, AttributeError):
        return False


def _descendants(root: int) -> list[int]:
    kids: dict[int, list[int]] = {}
    for entry in os.listdir("/proc") if os.path.isdir("/proc") else []:
        if not entry.isdigit():
            continue
        try:
            with open(f"/proc/{entry}/stat", encoding="utf-8", errors="replace") as fh:
                ppid = int(fh.read().rsplit(")", 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            continue
        kids.setdefault(ppid, []).append(int(entry))
    found, todo = [], list(kids.get(root, []))
    while todo:
        pid = todo.pop()
        found.append(pid)
        todo.extend(kids.get(pid, []))
    return found


def _reap_leftovers() -> None:
    """Kill every process still descending from this one. Calls run one at a time, so once a
    call has returned, all of them are what it left behind."""
    for _ in range(5):
        pids = _descendants(os.getpid())
        if not pids:
            return
        for pid in pids:
            try:
                os.kill(pid, 9)
            except (ProcessLookupError, PermissionError):
                pass
        time.sleep(0.2)
        while True:  # collect the zombies that re-parented to us
            try:
                pid, _ = os.waitpid(-1, os.WNOHANG)
            except ChildProcessError:
                break
            if pid == 0:
                break


def _kill_group(proc: subprocess.Popen) -> None:
    if hasattr(os, "killpg"):
        try:
            os.killpg(proc.pid, 9)
        except (ProcessLookupError, PermissionError):
            pass
    elif proc.poll() is None:
        proc.kill()


def _claude_call(prompt: str, model: str, timeout: int, system: str | None = None,
                 cwd: Path | None = None, extra_args: list[str] | None = None) -> CallResult:
    """One CLI call (see _claude_call_once). With --wait-on-limit, a usage-limit refusal that
    names its reset time is waited out and the call retried, instead of being scored."""
    call = _claude_call_once(prompt, model, timeout, system, cwd, extra_args)
    for _ in range(3):
        wait = _limit_wait_seconds(call.error) if call.outcome == "infra_error" else None
        if not (_WAIT["on"] and wait is not None and wait <= _WAIT["max_s"]):
            break
        print(f"USAGE LIMIT: waiting {wait / 60:.0f} min for the reset, then retrying.",
              file=sys.stderr, flush=True)
        _WAIT["sleep"](wait)
        call = _claude_call_once(prompt, model, timeout, system, cwd, extra_args)
    return call


def _claude_call_once(prompt: str, model: str, timeout: int, system: str | None = None,
                      cwd: Path | None = None, extra_args: list[str] | None = None) -> CallResult:
    """Run one prompt through the claude CLI in an isolated working directory.

    When ``system`` is given it is injected via ``--append-system-prompt`` — this is how the
    target skill's SKILL.md is primed into the call so we grade the *skill*, not bare Claude.
    ``cwd`` is the arm's prepared workspace; without one the call runs in a fresh empty
    temporary directory. Errors, timeouts and refusals are returned as structured outcomes
    (never raised), so one bad call degrades to a non-verdict instead of aborting the run.
    ``extra_args`` adds CLI flags such as ``--allowedTools`` (used by scripts/run_benchmark.py).
    """
    conf = _confinement()
    with tempfile.TemporaryDirectory(prefix="alterlab-eval-call-",
                                     ignore_cleanup_errors=True) as fallback_cwd:
        run_dir = str(cwd) if cwd else fallback_cwd
        if any(Path(run_dir).resolve().is_relative_to(h) for h in conf["hidden"]):
            return CallResult(f"{_NO_ANSWER} workspace inside the protected checkout",
                              "infra_error", f"workspace {run_dir} is inside a path hidden "
                              "from answer arms; set TMPDIR outside the repository")
        cmd = ["claude", "--model", model, *ISOLATION_FLAGS, "--output-format", "json",
               *_scoped_args(extra_args or [], run_dir)]
        if system:
            cmd += ["--append-system-prompt", system]
        cmd += ["-p", prompt]
        if conf["mode"] == "namespace":
            cmd = [*_namespace_prefix(conf["hidden"], run_dir), *cmd]
        try:
            proc = _run_contained(cmd, run_dir, timeout)
        except subprocess.TimeoutExpired:
            _USAGE["calls"] += 1
            return CallResult(f"{_NO_ANSWER} TIMEOUT after {timeout}s", "infra_error",
                              f"timeout after {timeout}s")
        except OSError as exc:
            return CallResult(f"{_NO_ANSWER} could not start claude CLI", "infra_error",
                              _redact(f"could not start claude CLI: {exc}"))
    _USAGE["calls"] += 1
    if conf["mode"] == "namespace" and proc.returncode in (95, 96, 97) \
            and not proc.stdout.strip():
        return CallResult(f"{_NO_ANSWER} could not set up the private view", "infra_error",
                          f"namespace setup failed (exit {proc.returncode}): could not hide "
                          "the checkout, the other workspaces, or private state")
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
        "denied_tools": [_denial_summary(d) for d in denials][:20]
        if isinstance(denials, list) else None,
    }
    # The CLI prints usage-policy refusals to stdout and exits non-zero, so check both streams.
    combined = f"{proc.stdout} {proc.stderr}"
    aup = proc.returncode != 0 and all(m in combined for m in _AUP_REFUSAL_MARKERS)
    if aup or any(sig in combined for sig in _REFUSAL_SIGNATURES):
        cat = _AUP_CATEGORY.search(combined) if aup else None
        return CallResult(_REFUSED, "refused", "usage-policy refusal by the runner environment"
                          + (f" (category: {cat.group(1)})" if cat else ""), **meta)
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
      * a string  -> path to a fixture file or directory, relative to the eval file's
        directory; copied (a directory as a whole tree, e.g. a small repository checkout).
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
            if src.is_dir():
                shutil.copytree(src, target, symlinks=False)
            else:
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
    if eval_obj.get("artifact_checks"):  # same note for both arms: where to save, never the checks
        prompt += artifact_checks.prompt_note(eval_obj["artifact_checks"])
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

JUDGES = {"literal": _RUBRIC_JUDGE, "substance": _RUBRIC_JUDGE_SUBSTANCE}
# Bump a version whenever its template text changes; the sha256 is recorded with every run.
JUDGE_PROMPT_VERSIONS = {"literal": "literal-v1", "substance": "substance-v1"}
TRIGGER_PROMPT_VERSION = "trigger-v1"
# --behavioral / --regrade default: the substance judge. It is the one that agreed with every
# hand label in docs/judge_calibration.json (literal 7/8 on 2026-10-15: it failed a correct
# answer that asked for missing input), and v2 already reports skill vocabulary as its own
# dimension, so the rubric judge should grade substance only. --judge literal reproduces the
# v1 rubric judge for comparisons with older runs (the outcome rule is still v2's).
DEFAULT_JUDGE = "substance"


def judge_record(name: str, applied: bool = True) -> dict:
    """What graded a run: the rubric judge's name, prompt version and prompt hash, and the hash
    of the trigger (routing) judge prompt. ``applied`` is False for a collect-only run."""
    return {"name": name, "prompt_version": JUDGE_PROMPT_VERSIONS[name],
            "prompt_sha256": _sha256_bytes(JUDGES[name].encode("utf-8")),
            "trigger_prompt_version": TRIGGER_PROMPT_VERSION,
            "trigger_prompt_sha256": _sha256_bytes(_TRIGGER_JUDGE.encode("utf-8")),
            "applied": applied}


# --- Assertion dimensions -------------------------------------------------------------------
# Every assertion is scored in exactly one dimension:
#   routing           should_trigger / should_not_trigger (skilled arm only: the bare arm has no
#                     skill to engage or decline);
#   skill_vocabulary  an output_contains whose EVERY needle is an internal name (rule below) —
#                     a bare arm can never write it, so it is reported but never gates;
#   substantive       everything else: behavior clauses and output_contains of user-visible
#                     content (numbers, identifiers, API names, public tools and libraries).
# A needle is an internal name when, lower-cased and stripped (a leading "/" and an
# "alterlab-workflows:" prefix removed), it
#   (a) contains an ``alterlab-<name>`` identifier, or
#   (b) equals a suite skill's short name that contains a hyphen ("citation-mgmt") and is not
#       also a public name or ordinary hyphenated term (_PUBLIC_HYPHENATED: "scikit-learn",
#       "meta-analysis", ...), or
#   (c) equals a hyphenated packaged-workflow name ("citation-audit"; the one-word "rebuttal"
#       stays substantive), or
#   (d) equals an internal apparatus term (_APPARATUS_TERMS) or one of the citation verifier's
#       own taxonomy codes (_TAXONOMY_CODES).
# When in doubt a needle stays substantive, so the classifier can only relax gating for needles
# that name the suite itself — never for content a correct answer must contain.
_APPARATUS_TERMS = ("iron law", "excuse-vs-reality", "excuse vs reality", "excuse-vs-reality table",
                    "revision roadmap", "chapter plan", "design passport", "insight collection",
                    "rq brief", "methodology blueprint", "fully_addressed",
                    "partially_addressed", "not_addressed", "made_worse")
_TAXONOMY_CODES = ("tf", "pac", "ih", "ph", "sh")  # alterlab-citation-verifier's labels
_PUBLIC_HYPHENATED = frozenset({
    "scikit-bio", "scvi-tools", "scikit-learn", "scikit-survival", "pytorch-lightning",
    "stable-baselines3", "torch-geometric", "string-db", "meta-analysis", "peer-review",
    "text-as-data", "causal-inference", "missing-data", "mixed-methods", "open-science"})
_ALTERLAB_ID = re.compile(r"alterlab-[a-z0-9]+(?:-[a-z0-9]+)*")
_VOCAB_CACHE: dict = {}


def _internal_names() -> frozenset[str]:
    if "names" not in _VOCAB_CACHE:
        short = {d.name[len("alterlab-"):] for d in skill_dirs() if d.name.startswith("alterlab-")}
        wf_dir = SKILLS / "workflows" / "workflows"
        flows = {p.stem for p in wf_dir.glob("*.js")} if wf_dir.is_dir() else set()
        _VOCAB_CACHE["names"] = frozenset(
            n for n in short | flows if "-" in n and n not in _PUBLIC_HYPHENATED)
    return _VOCAB_CACHE["names"]


def vocabulary_reason(needle: object) -> str | None:
    """Why ``needle`` is an internal name (rule a-d above), or None when it is substantive."""
    if not isinstance(needle, str):
        return None
    n = needle.strip().lower().lstrip("/")
    n = n[len("alterlab-workflows:"):] if n.startswith("alterlab-workflows:") else n
    if _ALTERLAB_ID.search(n):
        return "names an alterlab- skill"
    if n in _internal_names():
        return "a suite skill or workflow name"
    if n in _APPARATUS_TERMS:
        return "an internal apparatus term"
    if n in _TAXONOMY_CODES:
        return "a skill-internal taxonomy code"
    return None


def assertion_dimension(a: dict) -> str:
    """'routing', 'skill_vocabulary' or 'substantive' for one assertion (see the rule above)."""
    atype, aval = a.get("type"), a.get("value")
    if atype in _TRIGGER_TYPES:
        return "routing"
    if atype == "output_contains":
        needles = aval if isinstance(aval, list) else [aval]
        if needles and all(vocabulary_reason(x) for x in needles):
            return "skill_vocabulary"
    return "substantive"


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
def _contains_hit(value: object, response: str) -> bool:
    """``output_contains``: a string must occur in the response (case-insensitive); a list
    passes when any one of its strings occurs — for answers that may be written in Turkish or
    English (``["Art. 28", "m. 28", "madde 28"]``)."""
    needles = value if isinstance(value, list) else [value]
    low = response.lower()
    return any(isinstance(n, str) and n and n.lower() in low for n in needles)


DIMENSIONS = ("substantive", "routing", "skill_vocabulary", "artifacts")
_GATING = ("substantive", "routing", "artifacts")  # skill_vocabulary is reported, never gating


def _grade_run(eval_obj: dict, skill: str, response: str, model: str, timeout: int, *,
               skilled: bool, template: str | None = None, collect: bool = False,
               saved: dict | None = None) -> tuple[str, str, list[tuple]]:
    """Grade one answer. Returns (rubric_verdict, rubric_detail, items); each item is
    (label, dimension, 'PASS'|'FAIL'|'NA', detail, judged) in the eval's assertion order.

    * ``output_contains``  -> deterministic case-insensitive substring check (both arms).
    * ``behavior`` and the ``expected_output`` rubric -> the rubric judge ``template`` (both arms).
    * ``should_trigger`` / ``should_not_trigger`` -> the trigger judge: the response must (not)
      ENGAGE the skill's workflow; skilled arm only. ``saved`` maps a label to verdicts kept
      from an earlier grading (``--regrade`` reuses them instead of re-asking the judge).
    ``collect`` (collect-only runs) skips every judge call; deterministic checks still run.
    """
    answered = _is_answer(response)
    items: list[tuple] = []
    for a in eval_obj.get("assertions", []) or []:
        if not isinstance(a, dict):
            continue
        atype, aval = a.get("type"), a.get("value")
        dim = assertion_dimension(a)
        if atype == "output_contains":
            label = f"output_contains[{aval!r}]"
            if not answered:
                items.append((label, dim, "NA", "no answer", False))
            else:
                hit = _contains_hit(aval, response)
                items.append((label, dim, "PASS" if hit else "FAIL",
                              "substring present" if hit else "substring absent", False))
        elif atype in _TRIGGER_TYPES:
            if not skilled:
                continue
            kept = (saved or {}).get(atype) or []
            prev = kept.pop(0) if kept else None
            if prev and prev[0] in (PASS, FAIL):
                items.append((atype, dim, prev[0], prev[1], False))
            elif collect:
                items.append((atype, dim, "NA", "collect-only: not judged", False))
            else:
                engaged, detail = _judge_engaged(skill, eval_obj["prompt"],
                                                 eval_obj.get("expected_output", ""),
                                                 response, model, timeout)
                if engaged == "NA":
                    items.append((atype, dim, "NA", detail, answered))
                else:
                    ok = (engaged == "YES") == (atype == "should_trigger")
                    items.append((atype, dim, "PASS" if ok else "FAIL", detail, True))
        elif atype == "behavior" and isinstance(aval, str):
            if collect:
                items.append(("behavior", dim, "NA", "collect-only: not judged", False))
            else:
                verdict, detail = _judge_rubric(aval, response, model, timeout, template)
                items.append(("behavior", dim, verdict, detail, answered))
    if collect:
        return "NA", "collect-only: answer saved, not judged", items
    rv, rd = _judge_rubric(eval_obj.get("expected_output", ""), response, model, timeout, template)
    return rv, rd, items


def grade_assertions(eval_obj: dict, skill: str, response: str,
                     model: str, timeout: int) -> list[tuple[str, str, str]]:
    """Grade every assertion on one skilled-arm response with the literal judge, as
    (label, 'PASS'|'FAIL'|'NA', detail). Kept for callers of the v1 API; the runner uses
    ``_grade_run``."""
    _rv, _rd, items = _grade_run(eval_obj, skill, response, model, timeout, skilled=True,
                                 template=_RUBRIC_JUDGE)
    return [(label, v, d) for (label, _dim, v, d, _j) in items]


def _rollup(per_run: list[list[str]]) -> str:
    """Per criterion (by position) the majority across runs; FAIL if any criterion's majority
    is FAIL, PASS if all are PASS, else NA."""
    width = max((len(r) for r in per_run), default=0)
    if not width:
        return "NA"
    majorities = [_majority([r[i] for r in per_run if i < len(r)]) for i in range(width)]
    if FAIL in majorities:
        return FAIL
    return PASS if all(m == PASS for m in majorities) else "NA"


def _dimensions(per_run: list[dict], *, skilled: bool, eval_obj: dict) -> dict:
    """Roll each dimension up over the runs. ``None`` = the dimension does not apply to this
    arm/case (bare-arm routing, no vocabulary assertions, no artifact_checks)."""
    applies = {
        "substantive": True,
        "routing": skilled and any(isinstance(a, dict) and a.get("type") in _TRIGGER_TYPES
                                   for a in eval_obj.get("assertions", []) or []),
        "skill_vocabulary": any(isinstance(a, dict) and assertion_dimension(a) ==
                                "skill_vocabulary" for a in eval_obj.get("assertions", []) or []),
        "artifacts": bool(eval_obj.get("artifact_checks")),
    }
    return {d: (_rollup([r.get(d, []) for r in per_run]) if per_run else "NA")
            if applies[d] else None for d in DIMENSIONS}


def _gated_verdict(dims: dict) -> str:
    """The v2 arm verdict: substantive + routing + artifacts (those that apply). Any FAIL ->
    FAIL; all PASS -> PASS; otherwise NA. skill_vocabulary never gates."""
    gating = [dims[d] for d in _GATING if dims.get(d) is not None]
    if FAIL in gating:
        return FAIL
    return PASS if gating and all(v == PASS for v in gating) else "NA"


def _run_criteria(rv: str, items: list[tuple], artifacts: list[dict]) -> dict:
    crit: dict[str, list[str]] = {"substantive": [rv], "routing": [], "skill_vocabulary": [],
                                  "artifacts": artifact_checks.verdicts(artifacts)}
    for (_label, dim, v, _d, _j) in items:
        crit[dim].append(v)
    return crit


def _unrun_dimensions(eval_obj: dict | None, skilled: bool) -> dict:
    """Dimensions of an arm that never ran (NOT_RUN, missing fixture): NA where they apply."""
    if eval_obj is None:
        return {d: "NA" if d == "substantive" else None for d in DIMENSIONS}
    return _dimensions([], skilled=skilled, eval_obj=eval_obj)


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
    return _answered_outcome(verdict, grading_notes)


def _answered_outcome(verdict: str, grading_notes: list[str]) -> str:
    if verdict in (PASS, FAIL):
        return verdict
    if any(str(n).startswith(_NO_ANSWER) for n in grading_notes):
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


# Results-record schema. v1 (<= v4.0.0): one combined outcome per arm, literal judge, the bare
# arm graded on the rubric only. v2: per-arm dimensions, identical substantive criteria for
# both arms, recorded judge + prompt hashes, artifact checks. See docs/evals.md.
SCHEMA_VERSION = 2
SUPPORTED_RESULT_VERSIONS = (1, 2)
METHODOLOGY = "v2-dimensions"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _runner_record() -> dict:
    here = Path(__file__).resolve()
    return {"script": "scripts/run_evals.py", "script_sha256": _sha256_bytes(here.read_bytes()),
            "artifact_checks_sha256": _sha256_bytes(
                (here.parent / "artifact_checks.py").read_bytes())}


def _run_metadata(kind: str, model: str, runs: int, timeout: int) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": kind,
        "runner": _runner_record(),
        "model": model,
        "model_source": "ALTERLAB_MODEL" if os.environ.get("ALTERLAB_MODEL") else "default",
        "endpoint": _endpoint(),
        "collect_only": _COLLECT["on"],
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
            "answer_tools": "the skill's allowed-tools frontmatter, granted to both arms "
                            "(Write/Edit scoped to the arm's workspace); judges get none",
            "confinement": {"mode": _confinement()["mode"],
                            "hidden_paths": len(_confinement()["hidden"]),
                            "why_not_namespace": _confinement()["why"] or None,
                            "tripwire": "checkout fingerprinted before the run and after "
                                        "every case; a change aborts the run"},
            "bare_arm_files": ["fixtures/"],
            "artifact_checks": "declared in evals/evals.json, which is never copied into a "
                               "workspace; both arms are told only each file's path, type and "
                               "description, and the files are checked before the workspace "
                               "is deleted",
        },
    }


def _write_results(results_dir: Path | None, kind: str, payload: dict) -> Path | None:
    if results_dir is None:
        return None
    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    body = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    # Exclusive create: parallel runs (eval_sweep.sh) finishing in the same second must
    # each get their own file; an exists-then-write check let one overwrite the other.
    for n in range(10_000):
        path = results_dir / (f"{kind}-{stamp}.json" if n == 0 else f"{kind}-{stamp}-{n}.json")
        try:
            with open(path, "x", encoding="utf-8") as fh:
                fh.write(body)
            return path
        except FileExistsError:
            continue
    raise RuntimeError(f"could not create a unique results file in {results_dir}")


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
             skilled: bool, tools: list[str] | None = None, *, judge: str = DEFAULT_JUDGE,
             artifact_dir: Path | None = None, results_dir: Path | None = None) -> dict:
    """Run one arm ``runs`` times in ``workspace`` and grade every run (schema v2).

    Both arms are graded on the same substantive criteria; routing assertions only on the
    skilled arm (``skilled``). Declared ``artifact_checks`` are checked after each run, while
    the workspace still exists, and the files are copied to ``artifact_dir/run-N/``; outputs a
    previous run left behind are deleted first so a run is never credited with them.
    """
    calls: list[CallResult] = []
    per_run_assertions: list[list[tuple[str, str, str]]] = []
    per_run_criteria: list[dict] = []
    rubric_votes: list[str] = []
    notes: list[str] = []
    run_records: list[dict] = []
    declared = eval_obj.get("artifact_checks") or []
    template = JUDGES[judge]
    for i in range(runs):
        if declared:
            artifact_checks.clear_artifacts(workspace, declared)
        call = _claude_call(prompt, model, timeout, system=system, cwd=workspace,
                            extra_args=["--allowedTools", *tools] if tools else None)
        calls.append(call)
        answered = call.outcome == "answer"
        rv, rd, items = _grade_run(eval_obj, skill, call.text, model, timeout, skilled=skilled,
                                   template=template, collect=_COLLECT["on"])
        arts = artifact_checks.check_artifacts(
            workspace, declared, store_dir=artifact_dir / f"run-{i + 1}" if artifact_dir else None,
            results_dir=results_dir, graded=answered) if declared else []
        if answered:
            notes += [d for (_, _, v, d, _) in items if v == "NA"] + ([rd] if rv == "NA" else [])
        per_run_assertions.append([(label, v, d) for (label, _dim, v, d, _j) in items])
        per_run_criteria.append(_run_criteria(rv, items, arts))
        rubric_votes.append(rv)
        run_records.append({
            "run": i + 1,
            "call_outcome": call.outcome,
            "error": call.error or None,
            "duration_ms": call.duration_ms,
            "num_turns": call.num_turns,
            "permission_denials": call.permission_denials,
            "denied_tools": call.denied_tools,
            "cost_usd": call.cost_usd,
            "usage": call.usage,
            "rubric_verdict": rv,
            "assertions": [{"assertion": a, "dimension": dim, "verdict": v,
                            "detail": _redact(str(d))[:300]} for (a, dim, v, d, _j) in items],
            "artifacts": arts,
            "response_excerpt": _scrub_emails(call.text[:1500]) if answered else None,
            # Full text, so a run can be re-graded later (e.g. with a revised judge) without
            # repeating the answer calls.
            "response": _scrub_emails(call.text) if answered else None,
        })
    dims = _dimensions(per_run_criteria, skilled=skilled, eval_obj=eval_obj)
    outcome = _arm_outcome(calls, _gated_verdict(dims), notes)
    reason = None
    if outcome not in (PASS, FAIL):
        errs = [c.error for c in calls if c.error]
        reason = (errs or notes or ["judges returned no majority verdict"])[0]
        reason = _redact(str(reason))[:300]
    has_assertions = any(per_run_assertions)
    return {
        "outcome": outcome,
        "reason": reason,
        "dimensions": dims,
        "assertion_verdict": (_eval_verdict_from_assertions(per_run_assertions)
                              if has_assertions else None),
        "rubric_majority": _majority(rubric_votes),
        "answered_runs": sum(c.outcome == "answer" for c in calls),
        "runs": run_records,
        "_calls": calls,
    }


def _rubric_sha256(eval_obj: dict) -> str:
    """Hash of everything an answer is graded against (canonical JSON)."""
    body = {"expected_output": eval_obj.get("expected_output"),
            "assertions": eval_obj.get("assertions", []) or [],
            "artifact_checks": eval_obj.get("artifact_checks", []) or []}
    return _sha256_bytes(json.dumps(body, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False).encode("utf-8"))


def _fixture_hashes(eval_obj: dict, evals_dir: Path) -> dict:
    out: dict[str, str | None] = {}
    for item in eval_obj.get("files", []) or []:
        if isinstance(item, dict) and item.get("name"):
            out[item["name"]] = _sha256_bytes(str(item.get("content", "")).encode("utf-8"))
        elif isinstance(item, str):
            src = evals_dir / item
            if src.is_file():
                out[item] = _sha256_bytes(src.read_bytes())
            elif src.is_dir():
                h = hashlib.sha256()
                for f in sorted(x for x in src.rglob("*") if x.is_file()):
                    h.update(f.relative_to(src).as_posix().encode() + b"\0"
                             + _sha256_bytes(f.read_bytes()).encode())
                out[item] = h.hexdigest()
            else:
                out[item] = None
    return out


def _case_hashes(case: dict) -> dict:
    e = case["eval"]
    return {"skill_md_sha256": _sha256_bytes(case["skill_md"].encode("utf-8")),
            "rubric_sha256": _rubric_sha256(e),
            "fixtures_sha256": _fixture_hashes(e, case["evals_dir"])}


def _case_dir_name(case_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "__", case_id)


def _unrun_case(case: dict, outcome: str, reason: str, **extra) -> dict:
    e = case["eval"]
    arm = {"outcome": outcome, "reason": reason, "answered_runs": 0, "runs": []}
    return {"case_id": f"{case['skill']}:{e.get('id', '?')}", "skill": case["skill"],
            "skill_version": case["skill_version"], "eval_id": e.get("id"),
            "hashes": _case_hashes(case), **extra,
            "skilled": {**arm, "dimensions": _unrun_dimensions(e, True)},
            "bare": {**arm, "dimensions": _unrun_dimensions(e, False)},
            "rubric_delta": "rubric: INCONCLUSIVE (case not run)"}


def _grade_case(case: dict, model: str, timeout: int, runs: int, *,
                judge: str = DEFAULT_JUDGE, results_dir: Path | None = None,
                run_stamp: str | None = None) -> dict:
    e = case["eval"]
    record = {
        "case_id": f"{case['skill']}:{e.get('id', '?')}",
        "skill": case["skill"],
        "skill_version": case["skill_version"],
        "eval_id": e.get("id"),
        "fixtures": [f if isinstance(f, str) else f.get("name") for f in e.get("files", []) or []],
        "allowed_tools": case.get("allowed_tools", []),
        "hashes": _case_hashes(case),
    }
    missing = missing_fixtures(e, case["evals_dir"])
    if missing:
        reason = f"missing fixture file(s): {', '.join(missing)}"
        empty = {"outcome": INFRA_ERROR, "reason": reason, "answered_runs": 0, "runs": [],
                 "_calls": []}
        return {**record, "skilled": {**empty, "dimensions": _unrun_dimensions(e, True)},
                "bare": {**empty, "dimensions": _unrun_dimensions(e, False)},
                "rubric_delta": "rubric: INCONCLUSIVE (case not run)"}
    store = (results_dir / "artifacts" / run_stamp / _case_dir_name(record["case_id"])
             if results_dir is not None and run_stamp and e.get("artifact_checks") else None)
    with tempfile.TemporaryDirectory(prefix="alterlab-eval-", ignore_cleanup_errors=True) as tmp:
        skilled_ws, bare_ws = Path(tmp) / "skilled", Path(tmp) / "bare"
        fixtures = prepare_workspace(skilled_ws, e, case["evals_dir"], case["skill_dir"])
        prepare_workspace(bare_ws, e, case["evals_dir"], None)
        prompt = build_prompt(e, fixtures)
        skilled = _run_arm(prompt, model, timeout, runs, skilled_ws, e, case["skill"],
                           e["expected_output"], case["skill_md"] + _SKILL_RUNTIME_NOTE, True,
                           tools=case.get("allowed_tools"), judge=judge,
                           artifact_dir=store / "skilled" if store else None,
                           results_dir=results_dir)
        # The bare arm has no skill to engage, so it carries no routing assertions; every
        # substantive criterion (rubric, behavior, substantive output_contains) and every
        # artifact check is the same as the skilled arm's, which is what the delta compares.
        bare = _run_arm(prompt, model, timeout, runs, bare_ws, e, case["skill"],
                        e["expected_output"], None, False, tools=case.get("allowed_tools"),
                        judge=judge, artifact_dir=store / "bare" if store else None,
                        results_dir=results_dir)
    return {**record, "skilled": skilled, "bare": bare,
            "rubric_delta": _delta(bare["dimensions"]["substantive"],
                                   skilled["dimensions"]["substantive"])}


def run_behavioral(skill_filter: str | None, timeout: int, runs: int,
                   shard: tuple[int, int] | None = None, *,
                   results_dir: Path | None = None, skill_dir: Path | None = None,
                   max_infra_streak: int = 6, case_ids: list[str] | None = None,
                   judge: str = DEFAULT_JUDGE) -> int:
    """Grade each eval by running it in an isolated workspace, skilled arm vs bare arm.

    Per case, the skilled arm gets the skill's SKILL.md via --append-system-prompt plus its
    bundled files; the bare arm gets only the task. Each arm runs ``runs`` times; assertions and
    the rubric are judged per run and majority-voted. Every case ends in exactly one outcome —
    PASS, FAIL, INCONCLUSIVE, REFUSED, INFRA_ERROR, or NOT_RUN — with the first reason printed.
    After ``max_infra_streak`` consecutive infrastructure errors the run aborts and the
    remaining cases are NOT_RUN. ``case_ids`` keeps only the evals with those ids (an id that
    matches nothing is an error, not a silent empty run). Results (case IDs, model, versions, per-run outcomes, baseline
    comparison, usage) are written as JSON to ``results_dir``. Exit code: ``_behavioral_status``.
    """
    model = alterlab_model()
    _reset_usage()
    started = time.monotonic()
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    meta = _run_metadata("behavioral", model, runs, timeout)
    meta["judge"] = judge_record(judge, applied=not _COLLECT["on"])
    meta["methodology"] = METHODOLOGY
    run_stamp = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{os.getpid()}"
    meta["artifacts_dir"] = f"artifacts/{run_stamp}" if results_dir is not None else None
    meta["selection"] = {"skill_filter": skill_filter, "skill_dir": str(skill_dir) if skill_dir
                         else None, "shard": f"{shard[0]}/{shard[1]}" if shard else None,
                         "cases": sorted(case_ids) if case_ids else None}
    print("=== BEHAVIORAL EVALUATION (live model calls; not the static schema check) ===")
    if _endpoint() != "claude-cli-login":
        print(f"Endpoint: {_endpoint()} (not the claude CLI login) — these results describe "
              f"'{model}', not Claude; keep them apart from Claude runs.")
    if _COLLECT["on"]:
        print("COLLECT-ONLY: answer arms run and are saved in full; no judge is called.")
    print(f"Model: {model} (ALTERLAB_MODEL convention; see skills/core/shared/model_env.md). "
          f"Each case runs {runs}x per arm, skilled vs bare, in isolated temp workspaces "
          f"({' '.join(ISOLATION_FLAGS)}).")
    if not _COLLECT["on"]:
        print(f"Judge: {judge} ({JUDGE_PROMPT_VERSIONS[judge]}); both arms graded on the same "
              "substantive criteria; routing, skill vocabulary and artifacts reported separately.")

    if shutil.which("claude") is None:
        reason = "the `claude` CLI is not on PATH; behavioral grading needs it"
        print(f"BLOCKED: {reason}.", file=sys.stderr)
        _write_results(results_dir, "behavioral", {**meta, "started_at": started_at,
                       "status": "blocked", "status_reasons": [reason], "summary": {},
                       "cases": []})
        return 2

    cases, skipped = _behavioral_cases(skill_filter, shard, skill_dir)
    if case_ids:
        missing = sorted(set(case_ids) - {c["eval"].get("id") for c in cases})
        if missing:
            print(f"ERROR: no selected eval has id {', '.join(missing)}.", file=sys.stderr)
            return 2
        cases = [c for c in cases if c["eval"].get("id") in set(case_ids)]
    if shard:
        print(f"Shard {shard[0]}/{shard[1]} of the corpus.")
    print(f"{len(cases)} case(s) selected"
          + (f"; {skipped} eval(s) skipped for lacking a prompt or rubric" if skipped else "")
          + ".\n")

    conf = _confinement()
    if conf["mode"] != "namespace":
        print(f"WARNING: answer arms are NOT namespace-confined ({conf['why']}). Write/Edit are "
              "scoped to each workspace, but shell grants can reach this checkout; a tripwire "
              "aborts the run if it changes. Prefer a disposable checkout.", file=sys.stderr)
    fingerprint = _repo_fingerprint()
    records: list[dict] = []
    streak, aborted, breach = 0, None, None
    for case in cases:
        if aborted:
            records.append(_unrun_case(case, NOT_RUN, aborted))
            continue
        unmet = unmet_requirements(case["eval"])
        if unmet:
            why = "not runnable here: " + "; ".join(unmet)
            records.append(_unrun_case(case, NOT_RUN, why, requires_unmet=unmet))
            print(f"- {records[-1]['case_id']}: NOT_RUN [{why}]")
            continue
        rec = _grade_case(case, model, timeout, runs, judge=judge, results_dir=results_dir,
                          run_stamp=run_stamp)
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
              f"({_dims_text(s['dimensions'])}) | bare={b['outcome']} "
              f"({_dims_text(b['dimensions'])}) -> {rec['rubric_delta']}")
        records.append(rec)
        if fingerprint is not None and not breach and _repo_fingerprint() != fingerprint:
            changed = ", ".join(_changed_paths()) or "(content of already-modified files)"
            breach = (f"isolation breach: the checkout changed while {rec['case_id']} ran "
                      f"(now modified/untracked: {changed}); nothing was reverted — inspect "
                      "and restore it before trusting or re-running")
            aborted = aborted or breach
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
    not_runnable = sum(bool(r.get("requires_unmet")) for r in records)
    if _COLLECT["on"]:
        arms = [r[a] for r in records if not r.get("requires_unmet") for a in ("skilled", "bare")]
        got = sum(a.get("answered_runs", 0) == runs for a in arms)
        status, code = (("collected", 0) if arms and got == len(arms) else
                        ("partial", 3) if got else ("blocked", 2))
    if breach:
        status, code = "blocked", 2  # a run that touched the checkout validates nothing
    reasons: list[str] = [breach] if breach else []
    if not_runnable:
        reasons.append(f"{not_runnable} case(s) not runnable here (unmet `requires`)")
    if _COLLECT["on"]:
        reasons.append("collect-only: answers saved without judging; grade them with "
                       "--regrade (a calibrated judge) before reading anything into them")
    elif status != "passed":
        if selected == 0:
            reasons.append("no case matched the selection")
        if counts[FAIL]:
            reasons.append(f"{counts[FAIL]} case(s) failed")
        if usable < selected:
            reasons.append(f"{selected - usable} of {selected} case(s) produced no usable "
                           "verdict, so the selection is not fully evaluated")
        if aborted and aborted != breach:
            reasons.append(aborted)
    first_problem = next((r["skilled"]["reason"] for r in records
                          if r["skilled"]["outcome"] in (INFRA_ERROR, REFUSED)), None)
    summary = {
        "selected": selected, "attempted": attempted, "answered": answered,
        "usable_verdicts": usable,
        "coverage": round(usable / selected, 4) if selected else 0.0,
        "skilled": counts, "bare": bare_counts, "rubric_delta": deltas,
        "skipped_ungradeable_evals": skipped,
        "not_runnable_here": not_runnable,
        "dimensions": _dimension_counts(records),
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
    if breach:
        print(f"BLOCKED: {breach}", file=sys.stderr)
    elif status == "blocked":
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


def _dims_text(dims: dict) -> str:
    short = {"substantive": "substantive", "routing": "routing", "skill_vocabulary": "vocab",
             "artifacts": "artifacts"}
    return ", ".join(f"{short[d]} {dims.get(d)}" for d in DIMENSIONS if dims.get(d) is not None)


def _dimension_counts(records: list[dict]) -> dict:
    """Per arm and dimension: how many cases scored PASS / FAIL / NA (or not applicable)."""
    out: dict = {}
    for arm in ("skilled", "bare"):
        out[arm] = {}
        for d in DIMENSIONS:
            vals = [((r.get(arm) or {}).get("dimensions") or {}).get(d) for r in records]
            out[arm][d] = {"PASS": vals.count(PASS), "FAIL": vals.count(FAIL),
                           "NA": vals.count("NA"), "not_applicable": vals.count(None)}
    return out


def _delta(bare: str, skilled: str) -> str:
    """One-line characterization of the bare-vs-skill delta. In v2 the inputs are the arms'
    ``substantive`` dimensions (identical criteria for both arms); in v1 they were the rubric
    majorities. The wording is unchanged."""
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


def _load_behavioral(path: Path) -> tuple[dict | None, str | None]:
    """A behavioral results payload, or (None, why it cannot be regraded) — never raises."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return None, f"unreadable: {exc}"
    try:
        src = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, f"malformed JSON ({exc.msg} at line {exc.lineno})"
    if not isinstance(src, dict):
        return None, "not a results object"
    kind = src.get("kind")
    if kind not in ("behavioral", "behavioral-regrade"):
        return None, f"not a behavioral results file (kind={kind!r})"
    version = src.get("schema_version", 1)
    if version not in SUPPORTED_RESULT_VERSIONS:
        return None, f"unsupported schema_version {version!r} (this runner reads " \
                     f"{', '.join(map(str, SUPPORTED_RESULT_VERSIONS))})"
    if not isinstance(src.get("cases"), list):
        return None, "no cases list"
    return src, None


def _not_regraded(a: dict, why: str) -> None:
    """An arm with answers that could not be regraded: its old verdict is kept only as
    ``outcome_original``, never reported as a v2 verdict."""
    a["outcome_original"] = a.get("outcome")
    a["outcome"], a["reason"], a["regraded"] = INCONCLUSIVE, f"not regraded: {why}", False
    a["dimensions"] = {d: "NA" if d == "substantive" else None for d in DIMENSIONS}


def _regrade_arm(a: dict, e: dict, skill: str, arm: str, model: str, timeout: int,
                 template: str, stats: dict) -> tuple[str, str]:
    """Re-judge one arm's saved runs in place; returns (old outcome, new outcome)."""
    runs = a["runs"]
    per_run_assertions, per_run_criteria, rubric_votes, notes = [], [], [], []
    for r in runs:
        resp = r.get("response") or ""
        answered = r.get("call_outcome") == "answer"
        saved: dict[str, list] = {}
        original: dict[str, list] = {}
        for item in r.get("assertions", []) or []:
            original.setdefault(item.get("assertion"), []).append(item.get("verdict"))
            if item.get("assertion") in _TRIGGER_TYPES:
                saved.setdefault(item["assertion"], []).append(
                    (item.get("verdict"), item.get("detail", "")))
        if answered:
            rv, rd, items = _grade_run(e, skill, resp, model, timeout, skilled=arm == "skilled",
                                       template=template, saved=saved)
        else:
            rv, rd, items = "NA", r.get("error") or "no answer", []
        judged = [v for (_l, _d, v, _x, j) in items if j] + ([rv] if answered else [])
        stats["judge_calls"] += len(judged)
        stats["judge_verdicts"] += sum(v in (PASS, FAIL) for v in judged)
        if answered and rv == "NA" and not stats["first_judge_failure"]:
            stats["first_judge_failure"] = _redact(str(rd))[:200]
        r["rubric_verdict_original"] = r.get("rubric_verdict")
        r["rubric_verdict"] = rv
        new_items = []
        for (label, dim, v, d, _j) in items:
            prev = original.get(label) or []
            new_items.append({"assertion": label, "dimension": dim, "verdict": v,
                              "detail": _redact(str(d))[:300],
                              "verdict_original": prev.pop(0) if prev else None})
        r["assertions"] = new_items
        declared = e.get("artifact_checks") or []
        if declared and "artifacts" not in r:  # a v1 run: its files were never checked
            arts_v = ["NA"]
        else:
            arts_v = artifact_checks.verdicts(r.get("artifacts") or [])
        crit = _run_criteria(rv, items, [])
        crit["artifacts"] = arts_v if declared else []
        per_run_criteria.append(crit)
        per_run_assertions.append([(x["assertion"], x["verdict"], x["detail"]) for x in new_items])
        rubric_votes.append(rv)
        if answered:
            notes += [d for (_, _, v, d, _) in items if v == "NA"] + ([rd] if rv == "NA" else [])
    dims = _dimensions(per_run_criteria, skilled=arm == "skilled", eval_obj=e)
    old = a.get("outcome")
    if any(r.get("call_outcome") == "answer" for r in runs):
        new = _answered_outcome(_gated_verdict(dims), notes)
    else:
        new = old  # never answered (REFUSED / INFRA_ERROR): nothing to judge
    a["outcome_original"], a["outcome"] = old, new
    a["reason"] = None if new in (PASS, FAIL) else (
        _redact(str((notes or [a.get("reason") or "judges returned no majority verdict"])[0]))[:300])
    a["dimensions"] = dims
    a["rubric_majority"] = _majority(rubric_votes)
    a["assertion_verdict"] = (_eval_verdict_from_assertions(per_run_assertions)
                              if any(per_run_assertions) else None)
    a["regraded"] = True
    return old, new


def regrade_results(path: Path, judge: str, timeout: int,
                    results_dir: Path | None = None) -> dict:
    """Re-judge a behavioral results file's saved responses with the v2 rules and ``judge``.

    Only judge calls are made; no answer is regenerated. The rubric, ``behavior`` and
    ``output_contains`` assertions are graded on BOTH arms (identical substantive criteria);
    ``should_trigger`` / ``should_not_trigger`` verdicts are kept from the original run when it
    judged them, and judged now when it did not (collect-only runs). Saved artifact-check
    verdicts are reused; a v1 run of a case that now declares artifact_checks has an NA
    artifacts dimension. An arm whose answers were saved without full text is not regraded:
    it is counted in ``arms_not_regraded`` and reported INCONCLUSIVE (``outcome_original``
    keeps the old verdict). A file that cannot be read, is malformed, is not a behavioral
    results file, or has an unknown schema_version is reported, never raised.

    Status (same vocabulary and exit-code meaning as --behavioral): ``failed`` if a regraded
    case FAILs; ``blocked`` if the judge returned no verdict at all or no case could be
    regraded; ``partial`` if some cases or arms have no usable regraded verdict; else
    ``passed``. A v2 payload is written to ``results_dir`` unless the file was unusable.
    """
    src, err = _load_behavioral(path)
    if err:
        return {"kind": "behavioral-regrade", "regraded_from": path.name, "status": "blocked",
                "status_reasons": [err], "file_error": err, "complete": False, "flips": [],
                "arms_not_regraded": 0, "cases": [],
                "summary": {"selected": 0, "usable_verdicts": 0}}
    template = JUDGES[judge]
    model = alterlab_model()
    from_version = src.get("schema_version", 1)
    stats = {"judge_calls": 0, "judge_verdicts": 0, "first_judge_failure": None,
             "arms_regraded": 0}
    flips: list[dict] = []
    not_regraded = 0
    cases = [c for c in src["cases"] if isinstance(c, dict)]
    for case in cases:
        e = _find_eval(case, src)
        old_hashes = case.get("hashes") or {}
        case["hashes"] = {"skill_md_sha256": old_hashes.get("skill_md_sha256"),
                          "rubric_sha256": _rubric_sha256(e) if e else None,
                          "fixtures_sha256": old_hashes.get("fixtures_sha256") or {},
                          "rubric_sha256_at_run": old_hashes.get("rubric_sha256")}
        for arm in ("skilled", "bare"):
            a = case.get(arm)
            if not isinstance(a, dict):
                continue
            runs = a.get("runs") or []
            answered = [r for r in runs if r.get("call_outcome") == "answer"]
            if not runs:  # never ran (NOT_RUN, missing fixture): nothing to regrade
                a["dimensions"] = _unrun_dimensions(e, arm == "skilled")
                a["regraded"] = False
                continue
            if e is None:
                not_regraded += bool(answered)
                _not_regraded(a, "its eval no longer exists in evals.json")
                continue
            if any(r.get("response") is None for r in answered):
                not_regraded += 1
                _not_regraded(a, "a saved answer has no full response text")
                continue
            old, new = _regrade_arm(a, e, case.get("skill", ""), arm, model, timeout, template,
                                    stats)
            stats["arms_regraded"] += 1
            if new != old:
                flips.append({"case_id": case.get("case_id"), "arm": arm, "from": old, "to": new})
        sub = {arm: ((case.get(arm) or {}).get("dimensions") or {}).get("substantive") or "NA"
               for arm in ("skilled", "bare")}
        case["rubric_delta"] = _delta(sub["bare"], sub["skilled"])

    counts = {o: sum((c.get("skilled") or {}).get("outcome") == o for c in cases)
              for o in OUTCOMES}
    bare = {o: sum((c.get("bare") or {}).get("outcome") == o for c in cases) for o in OUTCOMES}
    regraded_skilled = [c["skilled"] for c in cases if isinstance(c.get("skilled"), dict)
                        and c["skilled"].get("regraded")]
    usable = sum(a["outcome"] in (PASS, FAIL) for a in regraded_skilled)
    failed = sum(a["outcome"] == FAIL for a in regraded_skilled)
    selected = len(cases)
    reasons: list[str] = []
    judge_dead = stats["judge_calls"] > 0 and stats["judge_verdicts"] == 0
    if judge_dead:
        status = "blocked"
        reasons.append(f"judge unavailable: none of {stats['judge_calls']} judge call(s) "
                       f"returned a verdict (first: {stats['first_judge_failure']})")
    elif failed:
        status = "failed"
    elif usable == 0:
        status = "blocked"
    elif usable < selected or not_regraded:
        status = "partial"
    else:
        status = "passed"
    if failed:
        reasons.append(f"{failed} case(s) failed")
    if usable < selected:
        reasons.append(f"{selected - usable} of {selected} case(s) have no usable regraded verdict")
    if not_regraded:
        reasons.append(f"{not_regraded} arm(s) not regraded (saved answer text missing or eval gone)")
    deltas = {"helped": 0, "hurt": 0, "no_delta": 0, "inconclusive": 0}
    for c in cases:
        d = c.get("rubric_delta", "")
        deltas["helped" if "HELPED" in d else "hurt" if "HURT" in d
               else "no_delta" if "NO DELTA" in d else "inconclusive"] += 1
    payload = {**src, "schema_version": SCHEMA_VERSION, "kind": "behavioral-regrade",
               "methodology": METHODOLOGY, "regraded_from": path.name,
               "regraded_from_schema_version": from_version,
               "regraded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "judge": judge_record(judge), "runner": _runner_record(),
               "judge_model": model,
               "status": status, "status_reasons": reasons, "flips": flips,
               "arms_not_regraded": not_regraded,
               "complete": usable == selected and not not_regraded and not judge_dead,
               "cases": cases,
               "summary": {**(src.get("summary") or {}), "selected": selected,
                           "skilled": counts, "bare": bare, "usable_verdicts": usable,
                           "coverage": round(usable / selected, 4) if selected else 0.0,
                           "rubric_delta": deltas, "dimensions": _dimension_counts(cases),
                           "regrade": {k: v for k, v in stats.items()}}}
    _write_results(results_dir, "regrade", payload)
    return payload


_STATUS_CODES = {"passed": 0, "failed": 1, "blocked": 2, "partial": 3}


def _regrade_overall(payloads: list[dict]) -> tuple[str, int]:
    """Aggregate per-file regrade statuses: any FAIL -> failed (1); nothing usable anywhere
    (every file blocked) -> blocked (2); any file not fully regraded -> partial (3); else 0."""
    if any(p["status"] == "failed" for p in payloads):
        return "failed", 1
    if not payloads or all(p["status"] == "blocked" for p in payloads):
        return "blocked", 2
    if any(p["status"] != "passed" for p in payloads):
        return "partial", 3
    return "passed", 0


def _regrade_line(name: str, res: dict) -> str:
    if res.get("file_error"):
        return f"{name}: BLOCKED — {res['file_error']}"
    sm = res["summary"]
    sk = ", ".join(f"{sm['skilled'][o]} {o}" for o in OUTCOMES if sm["skilled"].get(o))
    rg = sm.get("regrade", {})
    line = (f"{name}: {res['status'].upper()} | skilled: {sk or 'no cases'} | usable "
            f"{sm['usable_verdicts']}/{sm['selected']} | {len(res['flips'])} flip(s) | "
            f"{res['arms_not_regraded']} arm(s) not regraded | judge verdicts "
            f"{rg.get('judge_verdicts', 0)}/{rg.get('judge_calls', 0)}")
    if res["status"] != "passed" and res.get("status_reasons"):
        line += "\n  " + "; ".join(res["status_reasons"])
    return line


CALIBRATION = REPO / "docs" / "judge_calibration.json"


def calibrate_judge(judges: list[str], timeout: int) -> int:
    """Grade the hand-labelled pairs in docs/judge_calibration.json with each judge.

    Exit codes mirror --behavioral: 0 every judge agreed with every label; 1 a judge gave a
    verdict that contradicts a label; 2 blocked — the calibration file is unusable or no judge
    call returned a verdict (judge unavailable); 3 partial — no contradiction, but some pairs
    got no verdict, so the judge is not shown to be trustworthy."""
    try:
        pairs = json.loads(CALIBRATION.read_text(encoding="utf-8"))["pairs"]
        if not isinstance(pairs, list) or not pairs or not all(
                isinstance(pr, dict) and pr.get("expected") in (PASS, FAIL)
                and isinstance(pr.get("rubric"), str) and isinstance(pr.get("response"), str)
                for pr in pairs):
            raise ValueError("pairs must be a non-empty list of {id, rubric, response, expected}")
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"BLOCKED: calibration file {CALIBRATION} is unusable ({exc}).", file=sys.stderr)
        return 2
    model = alterlab_model()
    disagree = no_verdict = verdicts = 0
    for judge in judges:
        agree = missing = 0
        for pr in pairs:
            got, why = _judge_rubric(pr["rubric"], pr["response"], model, timeout, JUDGES[judge])
            if got == "NA":
                missing += 1
                print(f"  [{judge}] {pr.get('id')}: no verdict — {_redact(str(why))[:160]}")
                continue
            verdicts += 1
            if got == pr["expected"]:
                agree += 1
            else:
                disagree += 1
                print(f"  [{judge}] {pr.get('id')}: expected {pr['expected']}, got {got} — "
                      f"{why[:160]}")
        no_verdict += missing
        print(f"judge {judge}: {agree}/{len(pairs)} agree with the hand labels"
              + (f", {missing} without a verdict" if missing else ""))
    if disagree:
        return 1
    if not verdicts:
        print("BLOCKED: no judge call returned a verdict; the judge is unavailable.",
              file=sys.stderr)
        return 2
    return 3 if no_verdict else 0


# --- Rubric audit (static) -------------------------------------------------------------------
def audit_rubrics(out: Path | None = None) -> int:
    """List rubrics and assertions that require the suite's internal names rather than
    user-visible outcomes. Static: no model calls; always exits 0 (a report, not a gate).

    * vocabulary assertions: output_contains whose every needle is an internal name (the
      classifier above) — scored as the skill_vocabulary dimension, never gating;
    * rubric prose (expected_output / behavior) that names an alterlab- skill or an internal
      apparatus term — still graded by the rubric judge; the substance judge is told to grade
      what such a clause stands for, but a rubric that requires naming a sibling skill cannot
      be met by a bare arm.
    """
    rows: list[dict] = []
    totals = {"skills": 0, "evals": 0, "output_contains": 0, "vocabulary_output_contains": 0,
              "expected_output_naming_skills": 0, "expected_output_self_invocation": 0,
              "expected_output_naming_apparatus": 0, "behavior_naming_skills_or_apparatus": 0}
    prose_terms = [t for t in _APPARATUS_TERMS if len(t) > 4]
    for d in skill_dirs():
        try:
            evals = json.loads(eval_path(d).read_text(encoding="utf-8")).get("evals", []) or []
        except (OSError, json.JSONDecodeError):
            continue
        totals["skills"] += 1
        for e in evals:
            if not isinstance(e, dict):
                continue
            totals["evals"] += 1
            for a in e.get("assertions", []) or []:
                if not isinstance(a, dict):
                    continue
                if a.get("type") == "output_contains":
                    totals["output_contains"] += 1
                    if assertion_dimension(a) == "skill_vocabulary":
                        totals["vocabulary_output_contains"] += 1
                        needles = a["value"] if isinstance(a["value"], list) else [a["value"]]
                        rows.append({"skill": d.name, "eval_id": e.get("id"),
                                     "where": "output_contains", "value": a["value"],
                                     "why": sorted({vocabulary_reason(n) for n in needles})})
                elif a.get("type") == "behavior" and isinstance(a.get("value"), str):
                    low = a["value"].lower()
                    hits = sorted(set(_ALTERLAB_ID.findall(low))) + [t for t in prose_terms
                                                                      if t in low]
                    if hits:
                        totals["behavior_naming_skills_or_apparatus"] += 1
                        rows.append({"skill": d.name, "eval_id": e.get("id"),
                                     "where": "behavior", "names": hits})
            low = str(e.get("expected_output", "")).lower()
            names = sorted(set(_ALTERLAB_ID.findall(low)))
            terms = [t for t in prose_terms if t in low]
            selfinv = f"invokes {d.name}" in low
            totals["expected_output_naming_skills"] += bool(names)
            totals["expected_output_self_invocation"] += selfinv
            totals["expected_output_naming_apparatus"] += bool(terms)
            if names or terms:
                rows.append({"skill": d.name, "eval_id": e.get("id"), "where": "expected_output",
                             "names": names, "apparatus": terms, "self_invocation": selfinv})
    print("=== RUBRIC AUDIT (static; no model calls) ===")
    print(f"{totals['skills']} skill(s), {totals['evals']} eval(s)")
    print(f"output_contains: {totals['output_contains']}, of which "
          f"{totals['vocabulary_output_contains']} require only internal names "
          "(skill_vocabulary dimension: reported, not gating)")
    print(f"expected_output naming an alterlab- skill: {totals['expected_output_naming_skills']} "
          f"(self-invocation 'Invokes <this skill>': {totals['expected_output_self_invocation']})")
    print(f"expected_output naming internal apparatus: {totals['expected_output_naming_apparatus']}")
    print(f"behavior clauses naming skills/apparatus: "
          f"{totals['behavior_naming_skills_or_apparatus']}")
    per_skill: dict[str, dict[str, int]] = {}
    for r in rows:
        per_skill.setdefault(r["skill"], {}).setdefault(r["where"], 0)
        per_skill[r["skill"]][r["where"]] += 1
    print("\nper skill (vocabulary output_contains / expected_output / behavior):")
    for sk in sorted(per_skill):
        c = per_skill[sk]
        print(f"  {sk:42} {c.get('output_contains', 0):3} / {c.get('expected_output', 0):3} / "
              f"{c.get('behavior', 0):3}")
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"totals": totals, "rules": {
            "apparatus_terms": list(_APPARATUS_TERMS), "taxonomy_codes": list(_TAXONOMY_CODES),
            "public_hyphenated": sorted(_PUBLIC_HYPHENATED)}, "items": rows}, indent=2,
            ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"\nfull list: {out}")
    return 0


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
    ap.add_argument("--case", metavar="ID", action="append", default=None,
                    help="(behavioral) only run the eval with this id; repeatable. Use it to "
                         "re-test cases whose eval changed while the skill itself did not")
    ap.add_argument("--max-infra-errors", type=int, default=6,
                    help="(behavioral) abort after this many consecutive infrastructure errors; "
                         "remaining cases are NOT_RUN (default 6)")
    ap.add_argument("--wait-on-limit", action="store_true",
                    help="(live) when the CLI reports a usage limit with its reset time, sleep "
                         "until the reset (at most 6 h) and retry the call instead of scoring an "
                         "infrastructure error")
    ap.add_argument("--collect-only", action="store_true",
                    help="(behavioral) run and save the answer arms without judging them; exit 0 "
                         "when every arm answered. Grade later with --regrade.")
    ap.add_argument("--isolation", choices=["auto", "namespace", "none"], default="auto",
                    help="(live) how answer arms are kept away from this checkout: 'namespace' "
                         "hides it in a private mount namespace (Linux; failure is fatal), "
                         "'auto' uses it when available, 'none' relies on scoped grants and "
                         "the tripwire only (default auto)")
    ap.add_argument("--regrade", metavar="RESULTS_JSON", nargs="+", default=None,
                    help="re-judge saved responses in behavioral results file(s) with the v2 "
                         "rules; judge calls only. Exit codes as --behavioral, over all files")
    ap.add_argument("--calibrate-judge", action="store_true",
                    help="grade docs/judge_calibration.json with --judge (default: both judges); "
                         "judge calls only. 0 all agree, 1 a disagreement, 2 blocked, 3 partial")
    ap.add_argument("--judge", choices=sorted(JUDGES), default=None,
                    help=f"(behavioral/regrade/calibrate) rubric judge; default {DEFAULT_JUDGE} "
                         "for --behavioral and --regrade, both judges for --calibrate-judge. "
                         "substance grades what a response does; literal is the v1 judge, for "
                         "comparison with older runs")
    ap.add_argument("--audit-rubrics", action="store_true",
                    help="static report: rubrics/assertions that require internal skill names "
                         "or apparatus rather than user-visible outcomes (no model calls)")
    ap.add_argument("--audit-out", metavar="FILE", default=None,
                    help="(audit-rubrics) also write the full list as JSON to FILE")
    ap.add_argument("--shard", metavar="i/n", default=None,
                    help="(behavioral/activation) grade only a deterministic shard of skills "
                         "(e.g. 2/7) to split a long run into several sittings")
    args = ap.parse_args(argv)

    try:
        shard = parse_shard(args.shard)
    except ValueError as exc:
        ap.error(str(exc))

    results_dir = Path(args.results_dir) if args.results_dir else None
    _WAIT["on"] = bool(args.wait_on_limit)  # also for --regrade / --calibrate-judge calls
    if args.audit_rubrics:
        return audit_rubrics(Path(args.audit_out) if args.audit_out else None)
    if args.calibrate_judge:
        return calibrate_judge([args.judge] if args.judge else sorted(JUDGES), args.timeout)
    judge = args.judge or DEFAULT_JUDGE
    if args.regrade:
        payloads = []
        print(f"=== REGRADE (judge {judge}, {JUDGE_PROMPT_VERSIONS[judge]}; judge calls only) ===")
        for f in args.regrade:
            res = regrade_results(Path(f), judge, args.timeout, results_dir)
            payloads.append(res)
            print(_regrade_line(Path(f).name, res))
        status, code = _regrade_overall(payloads)
        complete = sum(bool(p.get("complete")) for p in payloads)
        usable = sum(p["summary"].get("usable_verdicts", 0) for p in payloads)
        selected = sum(p["summary"].get("selected", 0) for p in payloads)
        print(f"=== REGRADE RESULT: {status.upper()} === {complete} of {len(payloads)} file(s) "
              f"completely regraded | usable verdicts {usable}/{selected} case(s) | "
              f"{sum(len(p['flips']) for p in payloads)} flip(s)")
        if status != "passed":
            print({"failed": "FAILED: at least one regraded case failed.",
                   "blocked": "BLOCKED: nothing could be regraded or judged; this verifies "
                              "NOTHING.",
                   "partial": "PARTIAL: some files, cases or arms have no usable regraded "
                              "verdict."}[status], file=sys.stderr)
        return code
    if args.behavioral and args.activation:
        ap.error("choose one of --behavioral / --activation, not both")
    if args.behavioral or args.activation:
        configure_confinement(args.isolation)
    _COLLECT["on"] = bool(args.collect_only and args.behavioral)
    if args.behavioral:
        if args.runs < 1:
            ap.error("--runs must be >= 1")
        return run_behavioral(args.skill, args.timeout, args.runs, shard,
                              results_dir=results_dir,
                              skill_dir=Path(args.skill_dir).resolve() if args.skill_dir else None,
                              max_infra_streak=max(1, args.max_infra_errors),
                              case_ids=args.case, judge=judge)
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
