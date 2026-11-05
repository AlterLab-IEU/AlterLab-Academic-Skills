#!/usr/bin/env python3
"""Aggregate behavioral eval result records into a reproducible summary (no model calls).

Reads the JSON records that ``scripts/run_evals.py --behavioral`` (``behavioral-*.json``) and
``--regrade`` (``regrade-*.json``) write, checks each one against an explicit schema for
``schema_version`` 1 or 2, picks one run per case with a named selection rule, and writes a
Markdown and/or JSON summary. The same inputs and options always give byte-identical output:
everything is sorted, and the only timestamps printed are the ones recorded in the inputs.

    uv run python scripts/aggregate_results.py eval-results/            # Markdown to stdout
    uv run python scripts/aggregate_results.py eval-results/final_* --selection latest-clean \\
        --require-ancestor d7d26cc --skills-root skills --md-out summary.md --json-out summary.json
    uv run python scripts/aggregate_results.py --list-rules             # print every rule

Rules this script never breaks:

* An unknown ``schema_version`` is rejected, never guessed at; a malformed file is reported
  and skipped, never a crash.
* v1 records carry one combined outcome per arm (methodology ``v1-combined-<judge>-judge``);
  v2 records add routing / substantive dimensions. Each methodology gets its own tables; no
  figure ever adds v1 and v2 (or literal- and substance-judge) counts together.
* Every rate is printed with its numerator and denominator.

Exit codes: 0 = summary produced and every input was valid; 2 = no valid input (nothing to
summarise); 3 = some inputs were rejected (the summary of the valid ones is still produced).
Full documentation: docs/eval-aggregation.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

SUMMARY_VERSION = 1
SUPPORTED_SCHEMA_VERSIONS = (1, 2)
BEHAVIORAL_KINDS = ("behavioral", "behavioral-regrade")
OUTCOMES = ("PASS", "FAIL", "INCONCLUSIVE", "REFUSED", "INFRA_ERROR", "NOT_RUN")
VERDICTS = ("PASS", "FAIL")
SUBSTANTIVE_VALUES = ("PASS", "FAIL", "NA")
OPTIONAL_DIM_VALUES = ("PASS", "FAIL", "NA", None)
DIMENSIONS = ("substantive", "routing", "skill_vocabulary", "artifacts")
GATING_DIMENSIONS = ("substantive", "routing", "artifacts")  # skill_vocabulary is reported only
JUDGE_NAMES = ("literal", "substance")
CLI_ENDPOINT = "claude-cli-login"
HEX64 = re.compile(r"^[0-9a-f]{64}$")

_RULE_SUPERSEDE = (
    "A case inside a behavioral-regrade record supersedes the same case in the record it was "
    "regraded from (`regraded_from` = that file's name; a source in the regrade's own "
    "directory is preferred when several inputs share the name).")
_RULE_COLLECT = ("Collect-only runs (kind `behavioral`, `collect_only: true`) called no judge: "
                 "they are ungraded and never counted.")
_RULE_SUITE = "With --skills-root, cases of skills that are no longer in the suite are left out."
_RULE_CLEAN = ("Only runs that recorded namespace confinement (`isolation.confinement.mode` = "
               "`namespace`) and a clean working tree (`repo_dirty: false`) are eligible; a "
               "run that recorded neither is not eligible.")
_RULE_ANY_TREE = ("Confinement and working-tree state are NOT checked: every remaining run is "
                  "eligible.")
_RULE_ANCESTOR = ("With --require-ancestor COMMIT, only runs whose `repo_commit` contains COMMIT "
                  "(git merge-base --is-ancestor) are eligible; an unverifiable commit is not.")
_RULE_TIE = ("Eligible runs tied at that time with identical outcomes and methodology: the one "
             "from the lexicographically first file is counted, the others are duplicates. "
             "Tied runs that disagree are an unresolved conflict, and the case is not counted.")
_RULE_LATEST = ("Per case_id, the eligible run with the LATEST `finished_at` (else "
                "`started_at`) is counted.")
_RULE_EARLIEST = ("Per case_id, the eligible run with the EARLIEST `finished_at` (else "
                  "`started_at`) is counted: the first-run baseline.")
SELECTION_RULES = {
    "latest-clean": [_RULE_SUPERSEDE, _RULE_COLLECT, _RULE_SUITE, _RULE_CLEAN, _RULE_ANCESTOR,
                     _RULE_LATEST, _RULE_TIE],
    "latest": [_RULE_SUPERSEDE, _RULE_COLLECT, _RULE_SUITE, _RULE_ANY_TREE, _RULE_ANCESTOR,
               _RULE_LATEST, _RULE_TIE],
    "earliest": [_RULE_SUPERSEDE, _RULE_COLLECT, _RULE_SUITE, _RULE_ANY_TREE, _RULE_ANCESTOR,
                 _RULE_EARLIEST, _RULE_TIE],
}


# --------------------------------------------------------------------------- schema checks
def _type_name(types: tuple) -> str:
    return " or ".join("null" if t is type(None) else t.__name__ for t in types)


def _is(value: object, types: tuple) -> bool:
    """isinstance, except that a bool is never accepted as an int."""
    if isinstance(value, bool):
        return bool in types
    return isinstance(value, types)


def _field(errors: list[str], obj: dict, key: str, types: tuple, where: str,
           required: bool = True) -> None:
    if key not in obj:
        if required:
            errors.append(f"{where}: missing required key '{key}'")
        return
    if not _is(obj[key], types):
        errors.append(f"{where}.{key}: expected {_type_name(types)}, "
                      f"got {type(obj[key]).__name__}")


def parse_ts(value: object) -> datetime | None:
    """An ISO-8601 timestamp as an aware UTC datetime (a naive one is read as UTC)."""
    if not isinstance(value, str):
        return None
    try:
        ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def _hex(errors: list[str], obj: dict, key: str, where: str, required: bool) -> None:
    if key not in obj:
        if required:
            errors.append(f"{where}: missing required key '{key}'")
        return
    v = obj[key]
    if v is not None and not (isinstance(v, str) and HEX64.match(v)):
        errors.append(f"{where}.{key}: expected a 64-character lowercase hex sha256 or null")


def _check_dimensions(errors: list[str], arm: dict, arm_name: str, where: str) -> None:
    outcome = arm.get("outcome")
    dims = arm.get("dimensions")
    if dims is None:
        if outcome in VERDICTS:
            errors.append(f"{where}: v2 arm with outcome {outcome} has no 'dimensions'")
        return
    if not isinstance(dims, dict):
        errors.append(f"{where}.dimensions: expected dict")
        return
    if dims.get("substantive") not in SUBSTANTIVE_VALUES:
        errors.append(f"{where}.dimensions.substantive: expected one of PASS, FAIL, NA")
    for d in DIMENSIONS[1:]:
        if dims.get(d) not in OPTIONAL_DIM_VALUES:
            errors.append(f"{where}.dimensions.{d}: expected PASS, FAIL, NA or null")
    if arm_name == "bare" and dims.get("routing") in VERDICTS:
        errors.append(f"{where}.dimensions.routing: the bare arm has no routing verdict "
                      "(must be null or NA)")
    gating_fail = any(dims.get(d) == "FAIL" for d in GATING_DIMENSIONS)
    if outcome == "PASS" and (gating_fail or dims.get("substantive") != "PASS"):
        errors.append(f"{where}: outcome PASS contradicts its dimensions {_dims_text(dims)}")
    if outcome == "FAIL" and not gating_fail:
        errors.append(f"{where}: outcome FAIL but no gating dimension FAILed "
                      f"{_dims_text(dims)}")


def _dims_text(dims: dict) -> str:
    return "(" + ", ".join(f"{d}={dims.get(d)}" for d in DIMENSIONS) + ")"


def _check_case(errors: list[str], case: object, idx: int, version: int) -> None:
    where = f"cases[{idx}]"
    if not isinstance(case, dict):
        errors.append(f"{where}: expected dict, got {type(case).__name__}")
        return
    _field(errors, case, "case_id", (str,), where)
    if isinstance(case.get("case_id"), str) and not case["case_id"].strip():
        errors.append(f"{where}.case_id: empty")
    _field(errors, case, "skill", (str,), where)
    _field(errors, case, "skill_version", (str, type(None)), where, required=False)
    _field(errors, case, "eval_id", (str, int, type(None)), where, required=False)
    _field(errors, case, "requires_unmet", (list,), where, required=False)
    _field(errors, case, "rubric_delta", (str,), where, required=False)
    for arm_name in ("skilled", "bare"):
        arm = case.get(arm_name)
        aw = f"{where}.{arm_name}"
        if not isinstance(arm, dict):
            errors.append(f"{aw}: missing or not a dict")
            continue
        if arm.get("outcome") not in OUTCOMES:
            errors.append(f"{aw}.outcome: {arm.get('outcome')!r} is not one of "
                          f"{', '.join(OUTCOMES)}")
        _field(errors, arm, "reason", (str, type(None)), aw, required=False)
        _field(errors, arm, "answered_runs", (int,), aw, required=False)
        _field(errors, arm, "runs", (list,), aw, required=False)
        if version == 2:
            _check_dimensions(errors, arm, arm_name, aw)
    if version == 2 and "hashes" in case:
        h = case["hashes"]
        if not isinstance(h, dict):
            errors.append(f"{where}.hashes: expected dict")
        else:
            _hex(errors, h, "skill_md_sha256", f"{where}.hashes", required=False)
            _hex(errors, h, "rubric_sha256", f"{where}.hashes", required=False)
            fx = h.get("fixtures_sha256", {})
            if not isinstance(fx, dict) or not all(
                    isinstance(v, str) and HEX64.match(v) for v in fx.values()):
                errors.append(f"{where}.hashes.fixtures_sha256: expected {{name: sha256}}")


def validate_record(data: object) -> list[str]:
    """Schema errors of one behavioral / behavioral-regrade record ([] = valid).

    Required keys are only those the aggregation depends on; every other documented key is
    type-checked when present (v1 records gained keys over time without a version bump).
    """
    if not isinstance(data, dict):
        return [f"top level: expected a JSON object, got {type(data).__name__}"]
    version = data.get("schema_version")
    if "schema_version" not in data:
        return ["top level: missing required key 'schema_version'"]
    if not _is(version, (int,)) or version not in SUPPORTED_SCHEMA_VERSIONS:
        return [f"unsupported schema_version {version!r} (this reader knows "
                f"{', '.join(map(str, SUPPORTED_SCHEMA_VERSIONS))})"]
    errors: list[str] = []
    kind = data.get("kind")
    if kind not in BEHAVIORAL_KINDS:
        errors.append(f"top level.kind: {kind!r} is not one of {', '.join(BEHAVIORAL_KINDS)}")
    _field(errors, data, "status", (str,), "top level")
    _field(errors, data, "cases", (list,), "top level")
    for key in ("model", "endpoint", "claude_cli_version", "repo_commit", "started_at",
                "finished_at"):
        _field(errors, data, key, (str, type(None)), "top level", required=False)
    for key in ("repo_dirty", "collect_only"):
        _field(errors, data, key, (bool,), "top level", required=False)
    for key in ("isolation", "summary"):
        _field(errors, data, key, (dict,), "top level", required=False)
    for key in ("started_at", "finished_at"):
        if data.get(key) is not None and parse_ts(data.get(key)) is None:
            errors.append(f"top level.{key}: not an ISO-8601 timestamp: {data.get(key)!r}")
    conf = (data.get("isolation") or {}).get("confinement") if isinstance(
        data.get("isolation"), dict) else None
    if conf is not None and not (isinstance(conf, dict) and isinstance(conf.get("mode"), str)):
        errors.append("top level.isolation.confinement: expected {mode: str, ...}")
    if kind == "behavioral-regrade":
        _field(errors, data, "regraded_from", (str,), "top level")
        _field(errors, data, "flips", (list,), "top level", required=False)
        if version == 1:
            _field(errors, data, "judge", (str,), "top level")
    if version == 2:
        judge = data.get("judge")
        if not isinstance(judge, dict):
            errors.append("top level.judge: v2 requires {name, prompt_version, prompt_sha256}")
        else:
            if judge.get("name") not in JUDGE_NAMES:
                errors.append(f"top level.judge.name: {judge.get('name')!r} is not one of "
                              f"{', '.join(JUDGE_NAMES)}")
            _field(errors, judge, "prompt_version", (str,), "top level.judge")
            _hex(errors, judge, "prompt_sha256", "top level.judge", required=True)
            _hex(errors, judge, "trigger_prompt_sha256", "top level.judge", required=False)
        runner = data.get("runner")
        if not isinstance(runner, dict):
            errors.append("top level.runner: v2 requires {script, script_sha256}")
        else:
            _field(errors, runner, "script", (str,), "top level.runner")
            _hex(errors, runner, "script_sha256", "top level.runner", required=True)
    seen: set[str] = set()
    for i, case in enumerate(data.get("cases") if isinstance(data.get("cases"), list) else []):
        _check_case(errors, case, i, version)
        cid = case.get("case_id") if isinstance(case, dict) else None
        if isinstance(cid, str):
            if cid in seen:
                errors.append(f"cases[{i}]: duplicate case_id {cid!r} in one record")
            seen.add(cid)
    return errors


def methodology(data: dict) -> str:
    """The label a record's outcomes are reported under; different labels are never summed."""
    if data["schema_version"] == 1:
        judge = data.get("judge") if data.get("kind") == "behavioral-regrade" else "literal"
        label = f"v1-combined-{judge}-judge"
    else:
        label = f"v2-dimensions-{data['judge']['name']}-judge/{data['judge']['prompt_version']}"
    endpoint = data.get("endpoint")
    if endpoint and endpoint != CLI_ENDPOINT:
        label += f" @ {endpoint}"  # another model: never mixed into Claude numbers
    return label


# --------------------------------------------------------------------------- loading
@dataclass
class InputFile:
    label: str
    path: Path
    sha256: str | None = None
    status: str = "valid"  # valid | rejected | ignored
    errors: list[str] = field(default_factory=list)
    data: dict | None = None

    @property
    def name(self) -> str:
        return self.path.name


@dataclass
class Run:
    file: InputFile
    case: dict
    ts: datetime | None
    methodology: str

    @property
    def case_id(self) -> str:
        return self.case["case_id"]

    def outcome(self, arm: str) -> str:
        return self.case[arm]["outcome"]


def discover(paths: list[str]) -> list[tuple[str, Path]]:
    """(label, path) for each input; a directory contributes every *.json below it, sorted.
    The label is the path as given (normalised, '/'-separated), so it is stable across runs."""
    out: dict[Path, str] = {}
    for raw in paths:
        p = Path(raw)
        base = Path(os.path.normpath(raw)).as_posix()
        if p.is_dir():
            for f in sorted(p.rglob("*.json")):
                out.setdefault(f.resolve(), f"{base}/{f.relative_to(p).as_posix()}")
        else:
            out.setdefault(p.resolve() if p.exists() else p, base)
    return sorted(((label, path) for path, label in out.items()), key=lambda x: x[0])


def load_file(label: str, path: Path) -> InputFile:
    f = InputFile(label=label, path=path)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        f.status, f.errors = "rejected", [f"cannot read: {exc.strerror or exc}"]
        return f
    f.sha256 = hashlib.sha256(raw).hexdigest()
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        f.status, f.errors = "rejected", [f"not valid UTF-8 JSON: {exc}"]
        return f
    kind = data.get("kind") if isinstance(data, dict) else None
    if isinstance(kind, str) and kind not in BEHAVIORAL_KINDS:
        f.status, f.errors = "ignored", [f"kind {kind!r} is not a behavioral record"]
        return f
    errors = validate_record(data)
    if errors:
        f.status, f.errors = "rejected", errors
        return f
    f.data = data
    return f


def runs_of(f: InputFile) -> list[Run]:
    d = f.data or {}
    ts = parse_ts(d.get("finished_at")) or parse_ts(d.get("started_at"))
    label = methodology(d)
    return [Run(file=f, case=c, ts=ts, methodology=label) for c in d.get("cases", [])]


# --------------------------------------------------------------------------- selection
class AncestryChecker:
    """git merge-base --is-ancestor, cached; a commit git cannot resolve is unverifiable."""

    def __init__(self, ancestor: str, repo: str) -> None:
        self.ancestor, self.repo, self._cache = ancestor, repo, {}

    def check(self, commit: object) -> str | None:
        """None if ``commit`` contains the ancestor, else the exclusion reason."""
        if not isinstance(commit, str) or not commit:
            return f"no repo_commit recorded, so containing {self.ancestor} is unverifiable"
        if commit not in self._cache:
            try:
                proc = subprocess.run(
                    ["git", "-C", self.repo, "merge-base", "--is-ancestor", self.ancestor,
                     commit], capture_output=True, text=True, timeout=30)
                code = proc.returncode
            except (OSError, subprocess.TimeoutExpired):
                code = -1
            self._cache[commit] = (
                None if code == 0 else
                f"repo_commit {commit[:12]} does not contain {self.ancestor}" if code == 1 else
                f"repo_commit {commit[:12]}: ancestry of {self.ancestor} unverifiable "
                f"in {self.repo}")
        return self._cache[commit]


def suite_skills(root: Path) -> set[str]:
    """Skill folder names under a skills/ tree (folder name = skill name, by convention)."""
    return {p.parent.name for p in root.glob("*/*/SKILL.md")}


def exclusion(run: Run, mode: str, superseded: dict, skills: set[str] | None,
              ancestry: AncestryChecker | None) -> tuple[str, str] | None:
    """(category, reason) if ``run`` may not be counted under ``mode``, else None."""
    d = run.file.data or {}
    by = superseded.get((run.file.label, run.case_id))
    if by:
        return "superseded", f"superseded by regrade {by}"
    if d.get("kind") == "behavioral" and d.get("collect_only") is True:
        return "ungraded", "collect-only run: answers saved, no judge called"
    if skills is not None and run.case.get("skill") not in skills:
        return "not-in-suite", f"skill {run.case.get('skill')!r} is not in --skills-root"
    if mode == "latest-clean":
        conf = (d.get("isolation") or {}).get("confinement") or {}
        mode_rec = conf.get("mode")
        if mode_rec != "namespace":
            return "unclean", ("not namespace-confined (confinement "
                               f"{'not recorded' if mode_rec is None else repr(mode_rec)})")
        if d.get("repo_dirty") is not False:
            return "unclean", ("working tree not recorded clean (repo_dirty="
                               f"{json.dumps(d.get('repo_dirty'))})")
    if ancestry is not None:
        why = ancestry.check(d.get("repo_commit"))
        if why:
            return "ancestry", why
    if run.ts is None:
        return "no-timestamp", "record has neither finished_at nor started_at"
    return None


def _supersessions(runs: list[Run]) -> dict[tuple[str, str], str]:
    """(source file label, case_id) -> label of the regrade that supersedes it."""
    files = {r.file.label: r.file for r in runs}
    out: dict[tuple[str, str], str] = {}
    for r in runs:
        d = r.file.data or {}
        src = d.get("regraded_from")
        if d.get("kind") != "behavioral-regrade" or not src:
            continue
        named = [f for f in files.values() if f.name == src and f is not r.file]
        near = [f for f in named if f.path.parent == r.file.path.parent]
        for f in near or named:
            key = (f.label, r.case_id)
            out[key] = min(out.get(key, r.file.label), r.file.label)
    return out


def select(runs: list[Run], mode: str, skills: set[str] | None = None,
           ancestry: AncestryChecker | None = None) -> dict:
    """Apply the selection rule. Returns counted runs, not-counted runs with reasons, cases
    with no eligible run, and unresolved conflicts."""
    superseded = _supersessions(runs)
    by_case: dict[str, list[Run]] = defaultdict(list)
    for r in runs:
        by_case[r.case_id].append(r)
    counted: list[Run] = []
    not_counted: list[tuple[Run, str, str]] = []
    no_eligible: list[str] = []
    conflicts: list[dict] = []
    for cid in sorted(by_case):
        eligible: list[Run] = []
        for r in sorted(by_case[cid], key=lambda x: x.file.label):
            why = exclusion(r, mode, superseded, skills, ancestry)
            if why:
                not_counted.append((r, *why))
            else:
                eligible.append(r)
        if not eligible:
            no_eligible.append(cid)
            continue
        best = (min if mode == "earliest" else max)(r.ts for r in eligible)
        tied = [r for r in eligible if r.ts == best]
        for r in eligible:
            if r.ts != best:
                not_counted.append((r, "not-selected", "an earlier run is counted"
                                    if mode == "earliest" else "a later run is counted"))
        if len({(r.outcome("skilled"), r.outcome("bare"), r.methodology) for r in tied}) > 1:
            conflicts.append({"case_id": cid, "timestamp": best.isoformat(),
                              "runs": [{"file": r.file.label, "methodology": r.methodology,
                                        "skilled": r.outcome("skilled"),
                                        "bare": r.outcome("bare")} for r in tied]})
            for r in tied:
                not_counted.append((r, "conflict", "tied with a run that disagrees; "
                                    "case not counted"))
            continue
        counted.append(tied[0])
        for r in tied[1:]:
            not_counted.append((r, "duplicate", f"identical to the counted run from "
                                f"{tied[0].file.label}"))
    return {"counted": counted, "not_counted": not_counted, "no_eligible": no_eligible,
            "conflicts": conflicts}


# --------------------------------------------------------------------------- summary
def _counter_rows(c: Counter) -> list[list]:
    return [[k, c[k]] for k in sorted(c, key=lambda x: (x is None, str(x)))]


def summarize_group(label: str, runs: list[Run]) -> dict:
    """Counts and denominators for the counted cases of one methodology."""
    version = runs[0].file.data["schema_version"]
    skilled = Counter(r.outcome("skilled") for r in runs)
    bare = Counter(r.outcome("bare") for r in runs)
    selected = len(runs)
    not_runnable = sum(1 for r in runs if r.outcome("skilled") == "NOT_RUN"
                       and r.case.get("requires_unmet"))
    graded = [r for r in runs if r.outcome("skilled") in VERDICTS]
    deltas = Counter()
    for r in runs:
        d = r.case.get("rubric_delta") or ""
        deltas["helped" if "HELPED" in d else "hurt" if "HURT" in d
               else "no_delta" if "NO DELTA" in d else "inconclusive_or_missing"] += 1
    out = {
        "methodology": label,
        "schema_version": version,
        "denominators": {
            "selected": selected,
            "attempted": selected - skilled["NOT_RUN"],
            "answered": sum(1 for r in runs if (r.case["skilled"].get("answered_runs") or 0) > 0),
            "usable_verdicts": len(graded),
        },
        "skilled": {o: skilled[o] for o in OUTCOMES},
        "bare": {o: bare[o] for o in OUTCOMES},
        "not_run": {"not_runnable_here": not_runnable,
                    "aborted_or_other": skilled["NOT_RUN"] - not_runnable},
        "graded_cases": {
            "skilled_pass": sum(r.outcome("skilled") == "PASS" for r in graded),
            "bare_pass_same_cases": sum(r.outcome("bare") == "PASS" for r in graded),
            "helped": sum(r.outcome("skilled") == "PASS" and r.outcome("bare") == "FAIL"
                          for r in graded),
            "hurt": sum(r.outcome("skilled") == "FAIL" and r.outcome("bare") == "PASS"
                        for r in graded),
            "denominator": len(graded),
        },
        "rubric_delta_recorded": {k: deltas[k] for k in
                                  ("helped", "hurt", "no_delta", "inconclusive_or_missing")},
        "dimensions": _dimensions(runs) if version == 2 else None,
        "provenance": _provenance(runs),
    }
    return out


def _dimensions(runs: list[Run]) -> dict:
    def dim(r: Run, arm: str, d: str) -> str:
        dims = r.case[arm].get("dimensions")
        if not isinstance(dims, dict):
            return "absent"
        v = dims.get(d)
        return "null" if v is None else v

    per = {arm: {d: Counter(dim(r, arm, d) for r in runs) for d in DIMENSIONS}
           for arm in ("skilled", "bare")}
    both = [r for r in runs if dim(r, "skilled", "substantive") in VERDICTS
            and dim(r, "bare", "substantive") in VERDICTS]
    routed = [r for r in runs if dim(r, "skilled", "routing") in VERDICTS]
    return {
        "counts": {arm: {d: {k: per[arm][d][k] for k in sorted(per[arm][d])}
                         for d in DIMENSIONS} for arm in per},
        "substantive": {
            "denominator_both_arms_verdict": len(both),
            "skilled_pass": sum(dim(r, "skilled", "substantive") == "PASS" for r in both),
            "bare_pass": sum(dim(r, "bare", "substantive") == "PASS" for r in both),
            "helped": sum(dim(r, "skilled", "substantive") == "PASS"
                          and dim(r, "bare", "substantive") == "FAIL" for r in both),
            "hurt": sum(dim(r, "skilled", "substantive") == "FAIL"
                        and dim(r, "bare", "substantive") == "PASS" for r in both),
        },
        "routing": {"denominator_skilled_verdict": len(routed),
                    "skilled_pass": sum(dim(r, "skilled", "routing") == "PASS" for r in routed)},
    }


def _provenance(runs: list[Run]) -> dict:
    def tally(fn) -> list[list]:
        return _counter_rows(Counter(fn(r) for r in runs))

    def meta(key):
        return lambda r: (r.file.data or {}).get(key)

    return {
        "model": tally(meta("model")),
        "endpoint": tally(meta("endpoint")),
        "claude_cli_version": tally(meta("claude_cli_version")),
        "repo_commit": tally(meta("repo_commit")),
        "judge_prompt_sha256": tally(lambda r: ((r.file.data or {}).get("judge") or {}).get(
            "prompt_sha256") if isinstance((r.file.data or {}).get("judge"), dict) else None),
        "runner_script_sha256": tally(lambda r: ((r.file.data or {}).get("runner") or {}).get(
            "script_sha256") if isinstance((r.file.data or {}).get("runner"), dict) else None),
        "cases_without_hashes": sum(1 for r in runs if not isinstance(r.case.get("hashes"),
                                                                      dict)),
    }


def _case_row(r: Run) -> dict:
    d = r.file.data or {}
    h = r.case.get("hashes") if isinstance(r.case.get("hashes"), dict) else {}
    return {
        "case_id": r.case_id,
        "skill": r.case.get("skill"),
        "methodology": r.methodology,
        "file": r.file.label,
        "file_sha256": r.file.sha256,
        "finished_at": d.get("finished_at") or d.get("started_at"),
        "skilled": r.outcome("skilled"),
        "bare": r.outcome("bare"),
        "skilled_reason": r.case["skilled"].get("reason"),
        "requires_unmet": r.case.get("requires_unmet"),
        "skill_version": r.case.get("skill_version"),
        "model": d.get("model"),
        "claude_cli_version": d.get("claude_cli_version"),
        "repo_commit": d.get("repo_commit"),
        "skill_md_sha256": h.get("skill_md_sha256"),
        "rubric_sha256": h.get("rubric_sha256"),
        "fixtures_sha256": h.get("fixtures_sha256"),
    }


def build_summary(files: list[InputFile], mode: str, skills_root: str | None = None,
                  require_ancestor: str | None = None, git_repo: str = ".") -> dict:
    valid = [f for f in files if f.status == "valid"]
    runs = [r for f in valid for r in runs_of(f)]
    skills = suite_skills(Path(skills_root)) if skills_root else None
    ancestry = AncestryChecker(require_ancestor, git_repo) if require_ancestor else None
    sel = select(runs, mode, skills, ancestry)
    groups: dict[str, list[Run]] = defaultdict(list)
    for r in sel["counted"]:
        groups[r.methodology].append(r)
    rules = list(SELECTION_RULES[mode])
    return {
        "summary_version": SUMMARY_VERSION,
        "generator": "scripts/aggregate_results.py",
        "synthetic_inputs": sum(1 for f in valid if (f.data or {}).get("synthetic_example")),
        "selection": {"mode": mode, "rules": rules, "skills_root": skills_root,
                      "require_ancestor": require_ancestor},
        "inputs": [{
            "file": f.label, "sha256": f.sha256, "status": f.status, "errors": f.errors,
            "kind": (f.data or {}).get("kind"),
            "schema_version": (f.data or {}).get("schema_version"),
            "methodology": methodology(f.data) if f.data else None,
            "run_status": (f.data or {}).get("status"),
            "finished_at": (f.data or {}).get("finished_at"),
            "cases": len((f.data or {}).get("cases", [])),
            "regraded_from": (f.data or {}).get("regraded_from"),
            "arms_not_regraded": (f.data or {}).get("arms_not_regraded"),
            "synthetic_example": bool((f.data or {}).get("synthetic_example")),
        } for f in files],
        "totals": {
            "files": len(files),
            "files_valid": len(valid),
            "files_rejected": sum(f.status == "rejected" for f in files),
            "files_ignored": sum(f.status == "ignored" for f in files),
            "files_blocked_status": sum((f.data or {}).get("status") == "blocked"
                                        for f in valid),
            "case_runs": len(runs),
            "cases_seen": len({r.case_id for r in runs}),
            "cases_counted": len(sel["counted"]),
            "cases_without_eligible_run": len(sel["no_eligible"]),
            "cases_in_conflict": len(sel["conflicts"]),
        },
        "methodologies": [summarize_group(k, groups[k]) for k in sorted(groups)],
        "conflicts": sel["conflicts"],
        "cases_without_eligible_run": sel["no_eligible"],
        "runs_not_counted": sorted(
            ({"case_id": r.case_id, "file": r.file.label, "category": cat, "reason": why}
             for r, cat, why in sel["not_counted"]),
            key=lambda x: (x["case_id"], x["file"], x["category"])),
        "counted_cases": [_case_row(r) for r in sorted(sel["counted"],
                                                        key=lambda x: x.case_id)],
    }


# --------------------------------------------------------------------------- rendering
def frac(n: int, d: int) -> str:
    """'n / d (p%)' — a rate is never printed without its denominator."""
    return f"{n} / {d} ({n / d:.1%})" if d else f"{n} / 0 (no denominator)"


def _md_cell(v: object) -> str:
    s = "—" if v is None or v == "" else str(v)
    return s.replace("|", "\\|").replace("\n", " ")


def _table(head: list[str], rows: list[list]) -> list[str]:
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(_md_cell(c) for c in row) + " |" for row in rows]
    return out + [""]


def render_markdown(s: dict) -> str:
    t = s["totals"]
    L: list[str] = ["# Behavioral results summary", ""]
    if s["synthetic_inputs"]:
        L += [f"> **SYNTHETIC EXAMPLE DATA.** {s['synthetic_inputs']} input record(s) are "
              "marked `synthetic_example: true`. These figures test the aggregator; they are "
              "not results of any skill.", ""]
    L += [f"Generated by `{s['generator']}` (summary version {s['summary_version']}) with "
          f"selection rule `{s['selection']['mode']}`"
          + (f", `--require-ancestor {s['selection']['require_ancestor']}`"
             if s["selection"]["require_ancestor"] else "")
          + (f", `--skills-root {s['selection']['skills_root']}`"
             if s["selection"]["skills_root"] else "") + ".", "",
          "Methodologies are reported separately and never summed: `v1-combined-*` records "
          "carry one combined outcome per arm; `v2-dimensions-*` records also separate "
          "routing from substantive outcomes.", "", "## Selection rule", ""]
    L += [f"{i}. {rule}" for i, rule in enumerate(s["selection"]["rules"], 1)] + [""]
    L += ["## Inputs", "",
          f"{t['files']} file(s): {t['files_valid']} valid, {t['files_rejected']} rejected, "
          f"{t['files_ignored']} ignored (not behavioral records); {t['files_blocked_status']} "
          f"valid file(s) recorded run status `blocked`. {t['case_runs']} case run(s) of "
          f"{t['cases_seen']} distinct case(s): {t['cases_counted']} counted, "
          f"{t['cases_without_eligible_run']} with no eligible run, {t['cases_in_conflict']} "
          "in unresolved conflict.", ""]
    L += _table(["File", "Status", "Kind", "Schema", "Methodology", "Run status",
                 "finished_at", "Cases", "sha256 (12)"],
                [[i["file"], i["status"], i["kind"], i["schema_version"], i["methodology"],
                  i["run_status"], i["finished_at"], i["cases"],
                  (i["sha256"] or "")[:12]] for i in s["inputs"]])
    bad = [i for i in s["inputs"] if i["errors"]]
    if bad:
        L += ["### Rejected and ignored inputs", ""]
        L += _table(["File", "Status", "Problem(s)"],
                    [[i["file"], i["status"], "; ".join(i["errors"][:5])
                      + (f"; … {len(i['errors']) - 5} more" if len(i["errors"]) > 5 else "")]
                     for i in bad])
    for g in s["methodologies"]:
        L += _render_group(g)
    if not s["methodologies"]:
        L += ["## Results", "", "No case was counted.", ""]
    L += ["## Unresolved conflicts", ""]
    L += (_table(["Case", "Timestamp", "File", "Methodology", "Skilled", "Bare"],
                 [[c["case_id"], c["timestamp"], r["file"], r["methodology"], r["skilled"],
                   r["bare"]] for c in s["conflicts"] for r in c["runs"]])
          if s["conflicts"] else ["None.", ""])
    L += ["## Cases with no eligible run", ""]
    L += ([f"- `{c}`" for c in s["cases_without_eligible_run"]] + [""]
          if s["cases_without_eligible_run"] else ["None.", ""])
    L += ["## Runs not counted", ""]
    L += (_table(["Case", "File", "Category", "Reason"],
                 [[x["case_id"], x["file"], x["category"], x["reason"]]
                  for x in s["runs_not_counted"]]) if s["runs_not_counted"] else ["None.", ""])
    L += ["## Counted cases that did not pass (skilled arm)", ""]
    nonpass = [c for c in s["counted_cases"] if c["skilled"] != "PASS"]
    L += (_table(["Case", "Methodology", "Skilled", "Reason", "File"],
                 [[c["case_id"], c["methodology"], c["skilled"],
                   c["skilled_reason"] or (("not runnable here: " + "; ".join(
                       c["requires_unmet"])) if c["requires_unmet"] else None), c["file"]]
                  for c in nonpass]) if nonpass else ["None.", ""])
    L += ["## Counted cases and the file that supplied each", ""]
    L += _table(["Case", "Methodology", "Skilled", "Bare", "File", "finished_at",
                 "Skill version", "SKILL.md sha256 (12)", "Rubric sha256 (12)"],
                [[c["case_id"], c["methodology"], c["skilled"], c["bare"], c["file"],
                  c["finished_at"], c["skill_version"], (c["skill_md_sha256"] or "")[:12],
                  (c["rubric_sha256"] or "")[:12]] for c in s["counted_cases"]])
    return "\n".join(L).rstrip("\n") + "\n"


def _render_group(g: dict) -> list[str]:
    d, gc = g["denominators"], g["graded_cases"]
    L = [f"## Methodology `{g['methodology']}`", ""]
    L += _table(["Selected", "Attempted", "Answered", "Usable verdicts (graded)",
                 "Not runnable here", "Not run (aborted/other)"],
                [[d["selected"], d["attempted"], d["answered"], d["usable_verdicts"],
                  g["not_run"]["not_runnable_here"], g["not_run"]["aborted_or_other"]]])
    L += _table(["Arm", *OUTCOMES], [["skilled", *[g["skilled"][o] for o in OUTCOMES]],
                                     ["bare", *[g["bare"][o] for o in OUTCOMES]]])
    L += [f"- Coverage (usable verdicts / selected): {frac(d['usable_verdicts'], d['selected'])}",
          f"- Skilled PASS of graded cases: {frac(gc['skilled_pass'], gc['denominator'])}",
          f"- Bare PASS on the same graded cases: "
          f"{frac(gc['bare_pass_same_cases'], gc['denominator'])}",
          f"- Skill helped (skilled PASS, bare FAIL): {frac(gc['helped'], gc['denominator'])}; "
          f"hurt (skilled FAIL, bare PASS): {frac(gc['hurt'], gc['denominator'])}",
          "- Recorded `rubric:` delta (rubric verdicts only) over "
          f"{d['selected']} selected: " + ", ".join(
              f"{k.replace('_', ' ')} {v}" for k, v in g["rubric_delta_recorded"].items()), ""]
    if g["dimensions"] is None:
        L += ["Routing vs substantive: not available — v1 records carry only the combined "
              "outcome.", ""]
    else:
        dm = g["dimensions"]
        sub, rt = dm["substantive"], dm["routing"]
        n = sub["denominator_both_arms_verdict"]
        L += ["### Routing vs substantive", "",
              f"- Substantive (same criteria, both arms; {n} cases with a verdict in both): "
              f"skilled {frac(sub['skilled_pass'], n)}, bare {frac(sub['bare_pass'], n)}; "
              f"helped {sub['helped']}, hurt {sub['hurt']} (of {n}).",
              f"- Routing (skilled arm only): "
              f"{frac(rt['skilled_pass'], rt['denominator_skilled_verdict'])}.", ""]
        values = ["PASS", "FAIL", "NA", "null", "absent"]
        L += _table(["Arm", "Dimension", *values],
                    [[arm, dim, *[dm["counts"][arm][dim].get(v, 0) for v in values]]
                     for arm in ("skilled", "bare") for dim in DIMENSIONS])
    p = g["provenance"]
    rows = [[k, _md_cell(v), n] for k in ("model", "endpoint", "claude_cli_version",
                                          "repo_commit", "judge_prompt_sha256",
                                          "runner_script_sha256") for v, n in p[k]]
    L += ["### Provenance (counted cases per value)", ""]
    L += _table(["Field", "Value", "Cases"], rows)
    L += [f"Counted cases without per-case hashes: {p['cases_without_hashes']} of "
          f"{d['selected']}.", ""]
    return L


def render_json(s: dict) -> str:
    return json.dumps(s, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


# --------------------------------------------------------------------------- CLI
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Aggregate behavioral eval records (schema v1/v2) into a reproducible "
                    "Markdown/JSON summary. See docs/eval-aggregation.md.")
    ap.add_argument("paths", nargs="*", help="result files or directories (*.json, recursive)")
    ap.add_argument("--selection", choices=sorted(SELECTION_RULES), default="latest-clean",
                    help="case-selection rule (default: latest-clean); see --list-rules")
    ap.add_argument("--require-ancestor", metavar="COMMIT",
                    help="count only runs whose repo_commit contains COMMIT (needs git)")
    ap.add_argument("--git-repo", default=".", metavar="DIR",
                    help="repository for --require-ancestor (default: current directory)")
    ap.add_argument("--skills-root", metavar="DIR",
                    help="leave out cases of skills with no DIR/<domain>/<skill>/SKILL.md")
    ap.add_argument("--format", choices=("md", "json"), default="md",
                    help="what to print on stdout (default: md)")
    ap.add_argument("--md-out", metavar="FILE", help="also write the Markdown summary here")
    ap.add_argument("--json-out", metavar="FILE", help="also write the JSON summary here")
    ap.add_argument("--list-rules", action="store_true",
                    help="print every selection rule and exit")
    args = ap.parse_args(argv)
    if args.list_rules:
        for mode in sorted(SELECTION_RULES):
            print(f"{mode}:")
            for i, rule in enumerate(SELECTION_RULES[mode], 1):
                print(f"  {i}. {rule}")
        return 0
    if not args.paths:
        print("error: give at least one results file or directory", file=sys.stderr)
        return 2
    files = [load_file(label, path) for label, path in discover(args.paths)]
    for f in files:
        if f.status == "rejected":
            print(f"REJECTED {f.label}: {'; '.join(f.errors[:3])}", file=sys.stderr)
    if not any(f.status == "valid" for f in files):
        print("error: no valid behavioral record among the inputs; nothing to summarise",
              file=sys.stderr)
        return 2
    summary = build_summary(files, args.selection, args.skills_root, args.require_ancestor,
                            args.git_repo)
    md, js = render_markdown(summary), render_json(summary)
    for path, text in ((args.md_out, md), (args.json_out, js)):
        if path:
            Path(path).write_text(text, encoding="utf-8", newline="\n")
    sys.stdout.write(js if args.format == "json" else md)
    return 3 if summary["totals"]["files_rejected"] else 0


if __name__ == "__main__":
    sys.exit(main())
