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
  environment-specific, so this is not run in CI.

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
import subprocess
import sys
import tempfile
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
# Sentinel returned by _claude when a call could not produce a gradeable answer. Treated as a
# non-verdict (counts toward neither PASS nor FAIL in the majority vote) so a flaky CLI run or
# a skill that legitimately stalls on live tool use does not silently masquerade as a FAIL.
_NO_ANSWER = "<no-answer>"


def _claude(prompt: str, model: str, timeout: int, system: str | None = None) -> str:
    """Run a one-shot prompt through the claude CLI and return stdout text.

    When ``system`` is given it is injected via ``--append-system-prompt`` — this is how the
    target skill's SKILL.md is primed into the call so we grade the *skill*, not bare Claude.
    Errors/timeouts are returned as a ``_NO_ANSWER``-prefixed marker rather than raised, so a
    single bad run degrades to a non-verdict instead of aborting the whole eval.
    """
    cmd = ["claude", "--model", model]
    if system:
        cmd += ["--append-system-prompt", system]
    cmd += ["-p", prompt]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return f"{_NO_ANSWER} TIMEOUT after {timeout}s"
    if proc.returncode != 0:
        return f"{_NO_ANSWER} claude CLI exited {proc.returncode}: {proc.stderr.strip()[:300]}"
    return proc.stdout.strip()


def _is_answer(response: str) -> bool:
    """True if ``response`` is a real model answer (not a _NO_ANSWER error/timeout marker)."""
    return bool(response) and not response.startswith(_NO_ANSWER)


# --- Fixture materialization ------------------------------------------------------------
def materialize_fixtures(eval_obj: dict, evals_dir: Path, dest: Path) -> list[str]:
    """Write every eval ``files`` fixture into ``dest`` and return the materialized paths.

    Two fixture forms are supported (see docs/evals.schema.json):
      * a string  -> path to a fixture file, relative to the eval file's directory; copied.
      * an object  -> {"name", "content"}; the inline content is written verbatim.
    Returns absolute paths (as strings, forward-slashed) so the caller can reference them in
    the prompt. Missing on-disk fixtures are skipped with a note appended to the returned list
    via a sentinel comment — callers should treat a short return as "fixture unavailable".
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


def _judge_rubric(rubric: str, response: str, model: str, timeout: int) -> tuple[str, str]:
    """LLM-judge a response against a prose rubric. Returns ('PASS'|'FAIL'|'NA', first_line)."""
    if not _is_answer(response):
        return "NA", response
    out = _claude(_RUBRIC_JUDGE.format(rubric=rubric, response=response), model, timeout)
    if not _is_answer(out):
        return "NA", out
    verdict = "PASS" if "VERDICT: PASS" in out.upper() else "FAIL"
    return verdict, (out.splitlines()[0] if out else "")


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
    engaged = "YES" if "ENGAGED: YES" in out.upper() else "NO"
    return engaged, (out.splitlines()[0] if out else "")


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


def run_behavioral(skill_filter: str | None, timeout: int, runs: int) -> int:
    """Grade each eval by injecting its SKILL.md, materializing fixtures, and voting over N runs.

    Reports, per eval: the skilled majority verdict and the bare-vs-skill delta. Returns 1 if
    any eval's skilled majority verdict is FAIL, else 0 (NA evals do not fail the run).
    """
    model = alterlab_model()
    print(f"Behavioral grading with model: {model} "
          f"(ALTERLAB_MODEL convention; see skills/core/shared/model_env.md)")
    print(f"Each eval is run {runs}x with the skill's SKILL.md injected via "
          f"--append-system-prompt; majority verdict is reported.\n")
    if subprocess.run(["which", "claude"], capture_output=True).returncode != 0:
        print("ERROR: the `claude` CLI is not on PATH; behavioral grading needs it.",
              file=sys.stderr)
        return 2

    graded = failed = 0
    for d in skill_dirs():
        if skill_filter and skill_filter not in d.name:
            continue
        f = eval_path(d)
        skill_md_path = d / "SKILL.md"
        if not f.exists() or not skill_md_path.exists():
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        skill_md = skill_md_path.read_text(encoding="utf-8")
        evals_dir = f.parent
        for e in data.get("evals", []) or []:
            prompt0 = e.get("prompt")
            rubric = e.get("expected_output")
            if not prompt0 or not rubric:
                continue
            graded += 1
            label = f"{d.name}:{e.get('id', '?')}"

            with tempfile.TemporaryDirectory(prefix="alterlab-eval-") as tmp:
                fixtures = materialize_fixtures(e, evals_dir, Path(tmp))
                prompt = build_prompt(e, fixtures)

                # --- Skilled arm: SKILL.md injected, run N times, vote ---
                skilled_runs: list[list[tuple[str, str, str]]] = []
                skilled_rubric: list[str] = []
                for _ in range(runs):
                    resp = _claude(prompt, model, timeout, system=skill_md)
                    skilled_runs.append(grade_assertions(e, d.name, resp, model, timeout))
                    skilled_rubric.append(_judge_rubric(rubric, resp, model, timeout)[0])

                # --- Bare arm: same prompt, no skill, run N times, vote ---
                bare_rubric: list[str] = []
                for _ in range(runs):
                    resp = _claude(prompt, model, timeout)
                    bare_rubric.append(_judge_rubric(rubric, resp, model, timeout)[0])

            # Skilled eval verdict = assertions roll-up AND overall-rubric majority must hold.
            assertion_verdict = _eval_verdict_from_assertions(skilled_runs)
            skilled_overall = _majority(skilled_rubric)
            bare_overall = _majority(bare_rubric)

            if "FAIL" in (assertion_verdict, skilled_overall):
                verdict = "FAIL"
            elif assertion_verdict == "PASS" and skilled_overall == "PASS":
                verdict = "PASS"
            else:
                verdict = "NA"

            delta = _delta(bare_overall, skilled_overall)
            mark = {"PASS": "✓", "FAIL": "✗", "NA": "?"}[verdict]
            if verdict == "FAIL":
                failed += 1
            print(f"{mark} {label}: skilled={verdict} "
                  f"(assertions {assertion_verdict}, rubric {skilled_overall}) | "
                  f"bare rubric {bare_overall} -> {delta}")

    print(f"\n{graded} eval(s) graded, {failed} failed.")
    return 1 if failed else 0


def _delta(bare: str, skilled: str) -> str:
    """One-line characterization of the bare-vs-skill delta for an eval's overall rubric."""
    if bare == "FAIL" and skilled == "PASS":
        return "SKILL HELPED (bare FAIL -> skilled PASS)"
    if bare == "PASS" and skilled == "FAIL":
        return "SKILL HURT (bare PASS -> skilled FAIL)"
    if "NA" in (bare, skilled):
        return f"INCONCLUSIVE (bare={bare}, skilled={skilled})"
    return f"NO DELTA (both {bare})"


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
    ap.add_argument("--runs", type=int, default=3,
                    help="(behavioral) times to run each eval per arm; majority verdict wins "
                         "(default 3)")
    args = ap.parse_args(argv)

    if args.behavioral:
        if args.runs < 1:
            ap.error("--runs must be >= 1")
        return run_behavioral(args.skill, args.timeout, args.runs)
    return run_validation(args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
