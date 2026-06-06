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

* **``--behavioral``.** Shell to the ``claude`` CLI once per eval prompt, then LLM-judge the
  response against the eval's ``expected_output`` rubric. The judge model follows the
  ``ALTERLAB_MODEL`` convention — see ``skills/core/shared/model_env.md``; the model id is
  **never** hardcoded as a call argument (only the dated default constant below). Slow and
  environment-specific, so this is not run in CI.

Dependency-light by design: standard library ``json`` / ``subprocess`` plus ``jsonschema``.
``jsonschema`` is optional — if it is not importable the validator falls back to an
equivalent built-in structural check, so the script runs in a bare ``uv run`` env.

    uv run python scripts/run_evals.py             # validate all, per-skill report
    uv run python scripts/run_evals.py --strict    # non-zero exit on any violation
    uv run --with jsonschema python scripts/run_evals.py --strict   # full schema validation
    uv run python scripts/run_evals.py --behavioral                 # LLM-judge (needs claude CLI)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
SCHEMA_PATH = REPO / "docs" / "evals.schema.json"

# Coverage convention (see docs/evals.md "Conventions"):
MIN_TRIGGERS = 3
MIN_NEGATIVES = 1

# --- Model convention -------------------------------------------------------------------
# AlterLab model convention — default reviewed 2026-06-06; override via ALTERLAB_MODEL.
# See skills/core/shared/model_env.md before changing the default. NEVER inline a bare id.
DEFAULT_MODEL = "claude-opus-4-8"


def alterlab_model() -> str:
    """Return the model id to use: $ALTERLAB_MODEL if set/non-empty, else the dated default."""
    return os.environ.get("ALTERLAB_MODEL") or DEFAULT_MODEL


# --- Discovery --------------------------------------------------------------------------
def skill_dirs() -> list[Path]:
    """Every skill directory (one that contains a SKILL.md), sorted by path."""
    return sorted(p.parent for p in SKILLS.rglob("SKILL.md"))


def eval_path(skill_dir: Path) -> Path:
    return skill_dir / "evals" / "evals.json"


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
def _claude(prompt: str, model: str, timeout: int) -> str:
    """Run a one-shot prompt through the claude CLI and return stdout text."""
    proc = subprocess.run(
        ["claude", "--model", model, "-p", prompt],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude CLI exited {proc.returncode}: {proc.stderr.strip()[:300]}")
    return proc.stdout.strip()


_JUDGE_TEMPLATE = """You are grading a model response against an expected-behavior rubric.

RUBRIC (what a correct response should do):
{rubric}

ACTUAL RESPONSE:
{response}

Decide whether the ACTUAL RESPONSE satisfies the RUBRIC. Reply with a single line:
VERDICT: PASS
or
VERDICT: FAIL
followed by one sentence of justification."""


def _judge(rubric: str, response: str, model: str, timeout: int) -> tuple[bool, str]:
    out = _claude(_JUDGE_TEMPLATE.format(rubric=rubric, response=response), model, timeout)
    passed = "VERDICT: PASS" in out.upper()
    return passed, out


def run_behavioral(skill_filter: str | None, timeout: int) -> int:
    """Shell each eval prompt to claude, LLM-judge against expected_output. Returns exit code."""
    model = alterlab_model()
    print(f"Behavioral grading with model: {model} "
          f"(ALTERLAB_MODEL convention; see skills/core/shared/model_env.md)\n")
    if subprocess.run(["which", "claude"], capture_output=True).returncode != 0:
        print("ERROR: the `claude` CLI is not on PATH; behavioral grading needs it.",
              file=sys.stderr)
        return 2

    graded = failed = 0
    for d in skill_dirs():
        if skill_filter and skill_filter not in d.name:
            continue
        f = eval_path(d)
        if not f.exists():
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for e in data.get("evals", []) or []:
            prompt = e.get("prompt")
            rubric = e.get("expected_output")
            if not prompt or not rubric:
                continue
            graded += 1
            label = f"{d.name}:{e.get('id', '?')}"
            try:
                response = _claude(prompt, model, timeout)
                passed, detail = _judge(rubric, response, model, timeout)
            except (RuntimeError, subprocess.TimeoutExpired) as exc:
                failed += 1
                print(f"✗ {label}: ERROR {exc}")
                continue
            mark = "✓" if passed else "✗"
            if not passed:
                failed += 1
            first_line = detail.splitlines()[0] if detail else ""
            print(f"{mark} {label}: {first_line}")
    print(f"\n{graded} eval(s) graded, {failed} failed.")
    return 1 if failed else 0


# --- Validation reporting ---------------------------------------------------------------
def run_validation(strict: bool) -> int:
    results = validate_all()
    using_jsonschema = "jsonschema" in sys.modules or _jsonschema_available()
    bad = [r for r in results if not r.ok]
    for r in results:
        if r.ok:
            print(f"✓ {r.skill}")
        else:
            print(f"✗ {r.skill}: {'; '.join(r.errors)}")
    print(f"\n{len(results)} skill(s); {len(bad)} with issues; "
          f"{len(results) - len(bad)} clean.")
    print(f"Schema validation: {'jsonschema (full)' if using_jsonschema else 'built-in fallback'}"
          f" — run with `uv run --with jsonschema ...` for full Draft 2020-12 validation.")
    print("Behavioral execution (running each prompt through the claude CLI and LLM-judging "
          "expected_output) is not performed here; use --behavioral.")
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
    ap.add_argument("--skill", metavar="SUBSTR", default=None,
                    help="(behavioral) only grade skills whose dir name contains SUBSTR")
    ap.add_argument("--timeout", type=int, default=600,
                    help="(behavioral) per-claude-call timeout in seconds (default 600)")
    args = ap.parse_args(argv)

    if args.behavioral:
        return run_behavioral(args.skill, args.timeout)
    return run_validation(args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
