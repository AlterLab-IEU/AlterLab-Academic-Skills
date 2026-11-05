#!/usr/bin/env python3
"""Check a saved dynamic-workflow result against its validation fixture — no model, no network.

The seven AlterLab workflows (``skills/workflows/workflows/*.js``) return a payload
``{status, status_reasons, report, coverage, ...}`` and write their deliverables through agents.
After a run, save the returned payload as JSON and point this script at it and at the directory
the run wrote to. It checks, independently of the workflow's own read-back agent:

  * the payload schema and status vocabulary (complete / partial / blocked) and that the status
    agrees with ``status_reasons`` and ``report``;
  * every output file the fixture declares: present, non-empty, parseable as its type (Markdown has
    a heading, CSV has the expected columns, JSON / JSON Lines parse), with line counts that match
    the payload where the payload states one;
  * that the report's opening lines state the same status as the payload (read from the file here,
    not taken from the read-back agent), and that the read-back agent's account matches the file;
  * coverage accounting: per stage ``completed <= dispatched <= requested``,
    ``unresolved = requested - completed``, ``failed = dispatched - completed``, plus per-workflow
    invariants (counts never exceed their denominators, items listed as unchecked are not also
    counted as checked);
  * that incomplete agent work stays visible: if any coverage shows failed or unresolved work, the
    status is not ``complete`` and ``status_reasons`` is not empty.

Fixtures live in ``skills/workflows/alterlab-research-workflows/evals/fixtures/workflows/<name>/``
(``args.json``, ``expect.json``, the synthetic inputs, and a ``mock-scenario.json`` used only by the
mock-runtime tests). ``args.json`` writes to the placeholder ``${OUT_DIR}``; ``--print-args``
prints the args with it substituted.

``--live`` marks the verdict as a live run. It is accepted only from the caller, and the script
refuses it (exit 2) for a payload that looks like ``scripts/workflow_dryrun.mjs`` output, so a mock
can never be recorded as a live result.

Usage:

    python3 scripts/check_workflow_run.py --workflow citation-audit --out-dir OUT --print-args
    python3 scripts/check_workflow_run.py --workflow citation-audit --result payload.json \\
        --out-dir OUT [--live] [--runtime-s 312] [--cost-usd 1.9] [--agents 11] [--output verdict.json]

Prints a JSON verdict ``{workflow, checks: [{name, verdict: PASS|FAIL|NA, detail}], overall:
pass|fail|incomplete, live, runtime_s, cost_usd, agents, files: [{path, sha256, bytes}], ...}``.
Exit codes: 0 pass, 1 fail, 2 could not check (bad input, unknown workflow, mock offered as live),
3 incomplete (every check passed, but the run reported itself partial or blocked — the same
convention as ``run_evals.py``).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "skills" / "workflows" / "alterlab-research-workflows" / "evals" / "fixtures" / "workflows"
WORKFLOWS = (
    "citation-audit", "review-panel", "claim-stress-test", "rebuttal",
    "grant-mock-panel", "literature-map", "systematic-review-screening",
)
PLACEHOLDER = "${OUT_DIR}"
STATUSES = ("complete", "partial", "blocked")
CHECKER_VERSION = 1

EXIT_PASS, EXIT_FAIL, EXIT_CANNOT, EXIT_INCOMPLETE = 0, 1, 2, 3
PASS, FAIL, NA = "PASS", "FAIL", "NA"
MISSING = object()

# Strings the mocked runtime (scripts/workflow_dryrun.mjs) produces and a live agent would not.
MOCK_STRINGS = ("mock agent text", "injected text", "injected fault", "UNKNOWN-ID")
FAKE_POOL = re.compile(r"^s[0-2]$")
DRYRUN_KEYS = {"ok", "mode", "calls", "phases", "resultKeys", "faults"}
STATUS_LINE = re.compile(r"status\W{0,6}[:：]\W{0,6}(complete|partial|blocked)\b", re.IGNORECASE)
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+\S", re.MULTILINE)
OPENING_LINES = 40


class CannotCheck(Exception):
    """The inputs do not allow a check (exit 2)."""


# ---------------------------------------------------------------- small helpers
def get(obj: Any, path: str) -> Any:
    """Follow a dotted path through dicts; MISSING when any step is absent."""
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return MISSING
    return cur


def is_int(x: Any) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def is_num(x: Any) -> bool:
    return (isinstance(x, (int, float)) and not isinstance(x, bool)) and math.isfinite(x)


def substitute(obj: Any, out_dir: str) -> Any:
    if isinstance(obj, str):
        return obj.replace(PLACEHOLDER, out_dir)
    if isinstance(obj, list):
        return [substitute(x, out_dir) for x in obj]
    if isinstance(obj, dict):
        return {k: substitute(v, out_dir) for k, v in obj.items() if not k.startswith("_")}
    return obj


def load_json(path: Path, what: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise CannotCheck(f"{what} not found: {path}") from e
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise CannotCheck(f"{what} is not readable JSON ({path}): {e}") from e


def load_expect(workflow: str, override: Path | None = None) -> dict:
    if workflow not in WORKFLOWS and override is None:
        raise CannotCheck(f"unknown workflow {workflow!r} (one of: {', '.join(WORKFLOWS)})")
    exp = load_json(override or FIXTURES / workflow / "expect.json", "expect.json")
    if not isinstance(exp, dict) or exp.get("workflow") != workflow:
        raise CannotCheck(f"expect.json does not describe workflow {workflow!r}")
    return exp


def fixture_args(workflow: str, out_dir: str) -> Any:
    if workflow not in WORKFLOWS:
        raise CannotCheck(f"unknown workflow {workflow!r} (one of: {', '.join(WORKFLOWS)})")
    return substitute(load_json(FIXTURES / workflow / "args.json", "args.json"), out_dir)


def js_round1(x: float) -> float:
    """Math.round(x * 10) / 10, as the workflows compute means."""
    return math.floor(x * 10 + 0.5) / 10


# ---------------------------------------------------------------- provenance (mock vs live)
def _strings(obj: Any):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, list):
        for x in obj:
            yield from _strings(x)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield str(k)
            yield from _strings(v)


def unwrap(raw: Any) -> tuple[Any, bool]:
    """Return (payload, came_from_dryrun_wrapper). The dry-run harness prints {ok, mode, calls, result}."""
    if isinstance(raw, dict) and "result" in raw and len(DRYRUN_KEYS & set(raw)) >= 2:
        return raw["result"], True
    return raw, False


def mock_markers(raw: Any, wrapped: bool) -> list[str]:
    reasons = []
    if wrapped:
        reasons.append("the file is workflow_dryrun.mjs output (it has the harness's ok/mode/calls keys)")
    elif isinstance(raw, dict) and len(DRYRUN_KEYS & set(raw)) >= 2:
        reasons.append(f"the payload carries dry-run harness keys {sorted(DRYRUN_KEYS & set(raw))}")
    texts = list(_strings(raw))
    for marker in MOCK_STRINGS:
        if any(marker in t for t in texts):
            reasons.append(f"the payload contains the mock runtime's text {marker!r}")
    pool = sum(1 for t in texts if FAKE_POOL.match(t))
    if pool >= 3:
        reasons.append(f"{pool} values are the mock runtime's placeholder strings s0/s1/s2")
    return reasons


# ---------------------------------------------------------------- verdict collection
class Checks:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def add(self, name: str, ok: bool | None, detail: str = "") -> None:
        verdict = NA if ok is None else PASS if ok else FAIL
        self.items.append({"name": name, "verdict": verdict, "detail": detail})

    def failed(self) -> list[dict]:
        return [c for c in self.items if c["verdict"] == FAIL]


def _eq(checks: Checks, name: str, left: Any, right: Any, what: str) -> None:
    if left is MISSING or right is MISSING:
        checks.add(name, None, f"not applicable: {what} not in the payload")
    else:
        checks.add(name, left == right, f"{what}: {left!r} vs {right!r}")


# ---------------------------------------------------------------- generic checks
def check_schema(checks: Checks, p: Any, exp: dict) -> bool:
    if not isinstance(p, dict):
        checks.add("payload_schema", False, f"the payload is a {type(p).__name__}, not an object")
        return False
    problems = []
    for key, kind in (("status", str), ("status_reasons", list), ("coverage", dict)):
        if key not in p:
            problems.append(f"missing {key}")
        elif not isinstance(p[key], kind):
            problems.append(f"{key} is not a {kind.__name__}")
    if "report" not in p:
        problems.append("missing report")
    elif p["report"] is not None and not isinstance(p["report"], str):
        problems.append("report is neither a path nor null")
    if isinstance(p.get("status_reasons"), list) and not all(isinstance(r, str) and r.strip() for r in p["status_reasons"]):
        problems.append("status_reasons holds an empty or non-string entry")
    status = p.get("status")
    keyset = exp.get("payload", {})
    required = list(keyset.get("required_keys", []))
    if status in ("complete", "partial"):
        required += keyset.get("required_keys_when_delivered", [])
    for path in required:
        if get(p, path) is MISSING:
            problems.append(f"missing {path}")
    if status in ("complete", "partial"):
        for path in exp.get("coverage", {}).get("required_stages", []):
            if not isinstance(get(p, f"coverage.{path}"), dict):
                problems.append(f"coverage.{path} is missing")
    for path in keyset.get("forbidden_keys", []):
        if get(p, path) is not MISSING:
            problems.append(f"{path} is present but retired from the schema")
    checks.add("payload_schema", not problems, "; ".join(problems) or "required keys present with the right types")
    return isinstance(p.get("status"), str) and isinstance(p.get("coverage"), dict)


def check_status(checks: Checks, p: dict, exp: dict) -> None:
    status = p.get("status")
    checks.add("status_value", status in STATUSES, f"status {status!r}")
    allowed = exp.get("status", {}).get("allowed", list(STATUSES))
    checks.add("status_allowed", status in allowed, f"status {status!r}; this fixture allows {allowed}")
    reasons = p.get("status_reasons") or []
    report = p.get("report")
    if status == "complete":
        ok, detail = not reasons and report is not None, "complete needs no status_reasons and a confirmed report path"
    elif status == "partial":
        ok, detail = bool(reasons) and report is not None, "partial needs status_reasons and a confirmed report path"
    elif status == "blocked":
        ok, detail = bool(reasons) and report is None, "blocked needs status_reasons and report null"
    else:
        ok, detail = False, "unknown status"
    checks.add("status_consistent", ok, f"{detail}: {len(reasons)} reason(s), report={report!r}")
    cov_report = get(p, "coverage.report")
    if isinstance(cov_report, dict) and "confirmed" in cov_report:
        checks.add("report_confirmed_matches", bool(cov_report["confirmed"]) == (report is not None),
                   f"coverage.report.confirmed={cov_report['confirmed']!r}, report={report!r}")
    else:
        checks.add("report_confirmed_matches", None, "not applicable: the run stopped before the report stage")


def _stage_dicts(cov: dict):
    """Every coverage sub-object (two levels deep) that accounts for requested work."""
    for name, val in cov.items():
        if isinstance(val, dict):
            if is_int(val.get("requested")):
                yield name, val
            for sub, inner in val.items():
                if isinstance(inner, dict) and is_int(inner.get("requested")):
                    yield f"{name}.{sub}", inner


def check_stage_accounting(checks: Checks, p: dict) -> list[str]:
    """Generic per-stage arithmetic. Returns the stages that show unfinished work."""
    cov = p.get("coverage") or {}
    problems, unfinished = [], []
    for name, s in _stage_dicts(cov):
        counts = {k: s[k] for k in ("requested", "dispatched", "completed", "failed", "unresolved", "retried", "resolved") if k in s}
        for k, v in counts.items():
            if not is_int(v) or v < 0:
                problems.append(f"{name}.{k}={v!r} is not a non-negative integer")
        if problems:
            continue
        req = s["requested"]
        if "completed" in s:
            if s["completed"] > req:
                problems.append(f"{name}: completed {s['completed']} > requested {req}")
            if "unresolved" in s and s["unresolved"] != req - s["completed"]:
                problems.append(f"{name}: unresolved {s['unresolved']} != requested {req} - completed {s['completed']}")
            if "dispatched" in s:
                if not s["completed"] <= s["dispatched"] <= req:
                    problems.append(f"{name}: expected completed {s['completed']} <= dispatched {s['dispatched']} <= requested {req}")
                if "failed" in s and s["failed"] != s["dispatched"] - s["completed"]:
                    problems.append(f"{name}: failed {s['failed']} != dispatched {s['dispatched']} - completed {s['completed']}")
            if is_int(s.get("missing")) and "unresolved" not in s and s["missing"] != req - s["completed"]:
                problems.append(f"{name}: missing {s['missing']} != requested {req} - completed {s['completed']}")
        if "resolved" in s and "unresolved" in s and s["resolved"] + s["unresolved"] != req:
            problems.append(f"{name}: resolved {s['resolved']} + unresolved {s['unresolved']} != requested {req}")
        if (is_int(s.get("unresolved")) and s["unresolved"] > 0) or (is_int(s.get("missing")) and s["missing"] > 0):
            unfinished.append(name)
    agents = cov.get("agents")
    if agents is not None and (not is_int(agents) or not 0 <= agents <= 1000):
        problems.append(f"coverage.agents={agents!r} is outside 0..1000 (the runtime cap)")
    labels, failed_calls = cov.get("failed_call_labels"), cov.get("failed_calls")
    if is_int(failed_calls) and isinstance(labels, list) and len(labels) != min(failed_calls, 50):
        problems.append(f"coverage.failed_calls={failed_calls} but {len(labels)} failure label(s) are listed")
    checks.add("coverage_accounting", not problems, "; ".join(problems) or "every stage: completed <= dispatched <= requested, unresolved and failed add up")
    return unfinished


# ---------------------------------------------------------------- output files
def _file_entries(exp: dict, out_dir: Path) -> list[tuple[dict, list[Path]]]:
    entries = []
    for spec in exp.get("outputs", []):
        if "glob" in spec:
            entries.append((spec, sorted(out_dir.glob(spec["glob"])) if out_dir.is_dir() else []))
        else:
            entries.append((spec, [out_dir / spec["path"]]))
    return entries


def parse_file(path: Path, kind: str, spec: dict) -> tuple[bool, str, int | None]:
    """(ok, detail, record_count). record_count: non-blank lines for jsonl, rows for csv."""
    try:
        data = path.read_bytes()
    except OSError as e:
        return False, f"unreadable: {e}", None
    allow_empty = bool(spec.get("allow_empty"))
    if not data.strip():
        return (allow_empty, "empty (allowed)" if allow_empty else "empty", 0)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return False, "not UTF-8 text", None
    if kind == "md":
        if not HEADING.search(text):
            return False, "Markdown without any heading line", None
        return True, f"{len(text.splitlines())} lines, has a heading", None
    if kind == "json":
        try:
            json.loads(text)
        except json.JSONDecodeError as e:
            return False, f"invalid JSON: {e}", None
        return True, "valid JSON", None
    if kind == "jsonl":
        lines = [ln for ln in text.splitlines() if ln.strip()]
        for n, ln in enumerate(lines, 1):
            try:
                if not isinstance(json.loads(ln), dict):
                    return False, f"line {n} is JSON but not an object", None
            except json.JSONDecodeError as e:
                return False, f"line {n} is not JSON: {e}", None
        return True, f"{len(lines)} JSON object line(s)", len(lines)
    if kind == "csv":
        try:
            reader = csv.DictReader(io.StringIO(text))
            header = reader.fieldnames or []
            rows = list(reader)
        except csv.Error as e:
            return False, f"invalid CSV: {e}", None
        missing = [c for c in spec.get("columns", []) if c not in header]
        if missing:
            return False, f"CSV lacks column(s) {missing} (header: {header})", len(rows)
        if any(None in r for r in rows):
            return False, "a CSV row has more fields than the header", len(rows)
        return True, f"{len(rows)} row(s), columns ok", len(rows)
    return False, f"unknown declared type {kind!r}", None


def _expected_count(rule: Any, p: dict) -> Any:
    if not isinstance(rule, dict):
        return MISSING
    if "len" in rule:
        v = get(p, rule["len"])
        return len(v) if isinstance(v, list) else MISSING
    if "value" in rule:
        v = get(p, rule["value"])
        return v if is_int(v) else MISSING
    return MISSING


def check_files(checks: Checks, p: dict, exp: dict, out_dir: Path) -> list[dict]:
    delivered = p.get("status") in ("complete", "partial")
    hashed: list[dict] = []
    for spec, paths in _file_entries(exp, out_dir):
        label = spec.get("glob") or spec["path"]
        name = f"file:{label}"
        required = spec.get("required_when", "delivered") == "always" or delivered
        paths = [x for x in paths if x.is_file()]
        need = spec.get("min_count", 1) if "glob" in spec else 1
        if len(paths) < need:
            what = f"{len(paths)} file(s) match, need >= {need}" if "glob" in spec else "missing"
            checks.add(name, False if required else None, what + ("" if required else "; not required for a blocked run"))
            continue
        if not paths:
            checks.add(name, None, "no files match (none required)")
            continue
        results = []
        for path in paths:
            ok, detail, count = parse_file(path, spec["type"], spec)
            want = _expected_count(spec.get("count_equals"), p)
            if ok and want is not MISSING and count is not None and count != want:
                ok, detail = False, f"{detail}; expected {want} record(s) from {spec['count_equals']}"
            results.append((path, ok, detail))
            data = path.read_bytes()
            hashed.append({"path": str(path.relative_to(out_dir)), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
        bad = [f"{x.name}: {d}" for x, ok, d in results if not ok]
        checks.add(name, not bad, "; ".join(bad) or "; ".join(f"{x.name}: {d}" for x, _, d in results))
    for path_key, rel in exp.get("payload_files", {}).items():
        val = get(p, path_key)
        name = f"payload_file:{path_key}"
        if val is MISSING or (val is None and not delivered):
            checks.add(name, None, f"not applicable: {path_key} is {'absent' if val is MISSING else 'null'} in a {p.get('status')} payload")
        elif val is None:
            checks.add(name, p.get("status") != "complete", f"{path_key} is null: allowed only when the run is partial (it must then say why)")
        else:
            ok = str(val).replace("\\", "/").endswith(rel) and (out_dir / rel).is_file()
            checks.add(name, ok, f"{path_key}={val!r}; expected a path ending in {rel} that exists in the out dir")
    return hashed


def stated_status(path: Path) -> str | None:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[:OPENING_LINES]
    except OSError:
        return None
    m = STATUS_LINE.search("\n".join(lines))
    return m.group(1).lower() if m else None


def check_report(checks: Checks, p: dict, exp: dict, out_dir: Path) -> None:
    rel = exp["report"]
    report = p.get("report")
    path = out_dir / rel
    if report is None:
        checks.add("report_path", None, "not applicable: no confirmed report (blocked run)")
    else:
        checks.add("report_path", str(report).replace("\\", "/").endswith(rel), f"report={report!r}; expected a path ending in {rel}")
    if not path.is_file():
        if p.get("status") == "blocked":
            checks.add("report_states_payload_status", None, "not applicable: blocked run and no report file")
        else:
            checks.add("report_states_payload_status", False, f"{rel} is not in the out dir, so its status line cannot be read")
        read_back = get(p, "coverage.report.read_back")
        if isinstance(read_back, dict) and read_back.get("exists") is True:
            checks.add("read_back_matches_file", False, f"the read-back agent reported {rel} as existing, but it is not in the out dir")
        else:
            checks.add("read_back_matches_file", None, "not applicable: no report file and no read-back claiming one")
        return
    said = stated_status(path)
    status = p.get("status")
    if status == "blocked":
        # The payload is authoritative for a blocked run; an unconfirmed file must not claim completion.
        checks.add("report_states_payload_status", False if said == "complete" else None,
                   f"blocked payload; the unconfirmed file states {said!r}")
    else:
        checks.add("report_states_payload_status", said == status,
                   f"the file's opening states {said!r}; the payload says {status!r}" if said else
                   f"no 'Status: COMPLETE|PARTIAL|BLOCKED' line in the first {OPENING_LINES} lines")
    read_back = get(p, "coverage.report.read_back")
    if not isinstance(read_back, dict):
        checks.add("read_back_matches_file", None, "not applicable: no read-back recorded")
        return
    problems = []
    if read_back.get("exists") is not True:
        problems.append("the read-back agent reported the file missing, but it is there")
    rb = str(read_back.get("states_status", "")).lower()
    if rb in STATUSES and said and rb != said:
        problems.append(f"the read-back agent reported status {rb.upper()}, the file states {said.upper()}")
    if rb == "none" and said:
        problems.append(f"the read-back agent reported no status line, the file states {said.upper()}")
    checks.add("read_back_matches_file", not problems, "; ".join(problems) or "the read-back agent's account matches the file")


# ---------------------------------------------------------------- workflow invariants
Inv = Callable[[Checks, dict], list[str]]


def _len(p: dict, path: str) -> Any:
    v = get(p, path)
    return len(v) if isinstance(v, list) else MISSING


def _all_present(*vals: Any) -> bool:
    return all(v is not MISSING for v in vals)


def inv_citation_audit(c: Checks, p: dict) -> list[str]:
    k = lambda name: get(p, f"counts.{name}")  # noqa: E731
    refs, with_v = k("references"), k("references_with_verdict")
    if not isinstance(get(p, "counts"), dict):
        c.add("ca_counts", None, "not applicable: no counts (the run stopped before the report stage)")
        return []
    _eq(c, "ca_references_checked_plus_unchecked", with_v + _len(p, "unchecked.references_without_verdict") if _all_present(with_v, _len(p, "unchecked.references_without_verdict")) else MISSING, refs, "references with a verdict + references without one vs references listed")
    _eq(c, "ca_references_verdicts_match_coverage", with_v, get(p, "coverage.references.completed"), "counts.references_with_verdict vs coverage.references.completed")
    _eq(c, "ca_references_match_extraction", refs, get(p, "coverage.extraction.references_listed"), "counts.references vs coverage.extraction.references_listed")
    checked, checkable, extracted, total = k("claims_checked"), k("claims_checkable"), k("claims_extracted"), k("claims_total")
    _eq(c, "ca_claims_checked_match_coverage", checked, get(p, "coverage.claims.completed"), "counts.claims_checked vs coverage.claims.completed")
    if _all_present(checked, checkable, extracted, total):
        c.add("ca_claim_denominators", checked <= checkable <= extracted <= total, f"claims checked {checked} <= checkable {checkable} <= extracted {extracted} <= total {total}")
    _eq(c, "ca_claims_checked_plus_unchecked", checked + _len(p, "unchecked.claims_without_verdict") if _all_present(checked, _len(p, "unchecked.claims_without_verdict")) else MISSING, checkable, "claims with a verdict + claims without one vs checkable claims")
    _eq(c, "ca_claims_checkable_plus_not_checkable", checkable + _len(p, "unchecked.claims_not_checkable") if _all_present(checkable, _len(p, "unchecked.claims_not_checkable")) else MISSING, extracted, "checkable + not-checkable claims vs extracted claims")
    _eq(c, "ca_claims_not_extracted", get(p, "unchecked.claims_not_extracted"), total - extracted if _all_present(total, extracted) else MISSING, "unchecked.claims_not_extracted vs claims_total - claims_extracted")
    ref_flags = [k(x) for x in ("NOT_FOUND", "ID_INVALID", "PAC", "IH", "unverified")]
    if _all_present(with_v, *ref_flags) and all(is_int(x) for x in ref_flags):
        c.add("ca_reference_flags_within_verdicts", sum(ref_flags) <= with_v, f"NOT_FOUND+ID_INVALID+PAC+IH+unverified = {sum(ref_flags)} <= references with a verdict {with_v}")
    if _all_present(k("SH"), k("claims_uncheckable"), checked):
        c.add("ca_claim_flags_within_checked", k("SH") <= checked and k("claims_uncheckable") <= checked, f"SH {k('SH')} and UNCHECKABLE {k('claims_uncheckable')} <= claims checked {checked}")
    if _all_present(k("retracted"), k("retraction_unknown"), with_v):
        c.add("ca_retraction_within_verdicts", k("retracted") + k("retraction_unknown") <= with_v, f"retracted {k('retracted')} + retraction_unknown {k('retraction_unknown')} <= {with_v}")
    rc = get(p, "coverage.rechecks")
    if isinstance(rc, dict):
        _eq(c, "ca_provisional_flags_listed", k("flags_recheck_incomplete"), _len(p, "unchecked.flags_recheck_incomplete"), "counts.flags_recheck_incomplete vs flags listed as provisional")
        _eq(c, "ca_provisional_flags_match_coverage", k("flags_recheck_incomplete"), rc.get("flags_recheck_incomplete", MISSING), "counts vs coverage.rechecks.flags_recheck_incomplete")
        parts = [rc.get(x, MISSING) for x in ("flags_stood", "flags_overturned", "flags_recheck_incomplete")]
        _eq(c, "ca_flags_partition", sum(parts) if _all_present(*parts) else MISSING, rc.get("flags", MISSING), "stood + overturned + provisional vs flags")
        stood_parts = [k(x) for x in ("NOT_FOUND", "ID_INVALID", "PAC", "IH", "SH", "unverified")]
        _eq(c, "ca_counted_flags_all_stood", sum(stood_parts) if _all_present(*stood_parts) else MISSING, rc.get("flags_stood", MISSING), "NOT_FOUND+ID_INVALID+PAC+IH+SH+unverified (counted flags) vs flags that stood after both re-checks")
        _eq(c, "ca_overturned_matches", k("flags_overturned_on_recheck"), rc.get("flags_overturned", MISSING), "counts.flags_overturned_on_recheck vs coverage.rechecks.flags_overturned")
        prov = get(p, "unchecked.flags_recheck_incomplete")
        if isinstance(prov, list):
            c.add("ca_provisional_flags_lack_rechecks", all(isinstance(f, dict) and is_int(f.get("rechecks_completed")) and f["rechecks_completed"] < 2 for f in prov), "every provisional flag has fewer than 2 completed re-checks")
    signals = []
    for path in ("unchecked.references_without_verdict", "unchecked.claims_without_verdict", "unchecked.flags_recheck_incomplete"):
        if _len(p, path) not in (MISSING, 0):
            signals.append(path)
    for path in ("counts.unverified", "counts.claims_uncheckable", "unchecked.claims_not_extracted", "counts.flags_recheck_incomplete"):
        if is_int(get(p, path)) and get(p, path) > 0:
            signals.append(path)
    return signals


def inv_review_panel(c: Checks, p: dict) -> list[str]:
    mc = get(p, "major_concerns")
    if not isinstance(mc, dict):
        c.add("rp_major_concerns", None, "not applicable: the run stopped before the decision stage")
        return []
    parts = [mc.get(x, MISSING) for x in ("validated", "unverified", "withdrawn")]
    _eq(c, "rp_concerns_partition", sum(parts) if _all_present(*parts) else MISSING, mc.get("raised", MISSING), "validated + unverified + withdrawn vs raised")
    cc = get(p, "coverage.concern_checks")
    if isinstance(cc, dict):
        _eq(c, "rp_raised_match_coverage", mc.get("raised", MISSING), cc.get("requested", MISSING), "major_concerns.raised vs coverage.concern_checks.requested")
        _eq(c, "rp_checked_match_coverage", mc.get("validated", 0) + mc.get("withdrawn", 0), cc.get("completed", MISSING), "validated + withdrawn vs coverage.concern_checks.completed")
        _eq(c, "rp_unverified_match_coverage", mc.get("unverified", MISSING), cc.get("unresolved", MISSING), "unverified vs coverage.concern_checks.unresolved")
    for kind in ("validated", "unverified", "withdrawn"):
        _eq(c, f"rp_{kind}_listed", _len(p, f"concerns.{kind}"), mc.get(kind, MISSING), f"concerns listed as {kind} vs the count")
    key = lambda x: (x.get("reviewer"), x.get("id")) if isinstance(x, dict) else None  # noqa: E731
    val, unv = get(p, "concerns.validated"), get(p, "concerns.unverified")
    if isinstance(val, list) and isinstance(unv, list):
        both = {key(x) for x in val} & {key(x) for x in unv}
        c.add("rp_unverified_not_validated", not both, f"concerns both validated and unverified: {sorted(map(str, both))}" if both else "no concern is both validated and unverified")
    rv = get(p, "reviewers")
    if isinstance(rv, dict):
        _eq(c, "rp_reviewers_match_coverage", rv.get("completed", MISSING), get(p, "coverage.reviewers.completed"), "reviewers.completed vs coverage.reviewers.completed")
        if _all_present(rv.get("used", MISSING), rv.get("completed", MISSING), _len(p, "reviewers.missing"), rv.get("requested", MISSING)):
            c.add("rp_reviewers_accounted", rv["used"] - rv["completed"] == len(rv["missing"]) and rv["used"] <= rv["requested"], f"used {rv['used']} - completed {rv['completed']} = missing {len(rv['missing'])}; used <= requested {rv['requested']}")
        recs = get(p, "recommendations")
        if isinstance(recs, dict):
            _eq(c, "rp_recommendations_tally", sum(v for v in recs.values() if is_int(v)), rv.get("completed", MISSING), "recommendation tally vs reporting reviewers")
    signals = []
    if is_int(mc.get("unverified")) and mc["unverified"] > 0:
        signals.append("major_concerns.unverified")
    if _len(p, "reviewers.missing") not in (MISSING, 0):
        signals.append("reviewers.missing")
    return signals


def inv_claim_stress_test(c: Checks, p: dict) -> list[str]:
    claims = get(p, "claims")
    if not isinstance(claims, list):
        c.add("cst_claims", None, "not applicable: the run stopped before the attack stage")
        return []
    ratings = get(p, "ratings")
    if isinstance(ratings, dict):
        _eq(c, "cst_ratings_tally", sum(v for v in ratings.values() if is_int(v)), len(claims), "rating tally vs claims")
    _eq(c, "cst_claims_match_coverage", len(claims), get(p, "coverage.claims.requested"), "claims vs coverage.claims.requested")
    lens_ok = all(isinstance(x, dict) and is_int(x.get("lenses_completed")) and isinstance(x.get("lenses_missing"), list) and x["lenses_completed"] + len(x["lenses_missing"]) == 3 for x in claims)
    c.add("cst_lenses_per_claim", lens_ok, "each claim: lenses completed + lenses missing = 3")
    if lens_ok:
        _eq(c, "cst_lenses_match_coverage", sum(x["lenses_completed"] for x in claims), get(p, "coverage.lenses.completed"), "lenses completed across claims vs coverage.lenses.completed")
        _eq(c, "cst_lenses_requested", 3 * len(claims), get(p, "coverage.lenses.requested"), "3 x claims vs coverage.lenses.requested")
        bad = [x.get("id") for x in claims if x.get("rating") == "survives" and x["lenses_completed"] < 3]
        c.add("cst_survives_needs_all_lenses", not bad, f"claims rated 'survives' with a lens missing: {bad}" if bad else "no claim is rated 'survives' with a lens missing")
    unrated = sum(1 for x in claims if isinstance(x, dict) and x.get("rating") == "unrated")
    _eq(c, "cst_unrated_match_coverage", unrated, get(p, "coverage.claims.unrated"), "claims rated 'unrated' vs coverage.claims.unrated")
    cl = get(p, "coverage.claims")
    if isinstance(cl, dict) and _all_present(cl.get("found", MISSING), cl.get("requested", MISSING), cl.get("not_tested", MISSING)):
        c.add("cst_not_tested", cl["not_tested"] == cl["found"] - cl["requested"] and cl["requested"] <= cl["found"], f"not_tested {cl['not_tested']} = found {cl['found']} - tested {cl['requested']}")
    signals = []
    if unrated:
        signals.append("claims rated unrated")
    if any(isinstance(x, dict) and x.get("lenses_missing") for x in claims):
        signals.append("claims with missing lenses")
    if is_int(get(p, "coverage.claims.not_tested")) and get(p, "coverage.claims.not_tested") > 0:
        signals.append("coverage.claims.not_tested")
    return signals


def inv_grant_mock_panel(c: Checks, p: dict) -> list[str]:
    wk = get(p, "weaknesses")
    if not isinstance(wk, dict):
        c.add("gmp_weaknesses", None, "not applicable: the run stopped before the challenge stage")
        return []
    parts = [wk.get(x, MISSING) for x in ("standing", "unverified", "withdrawn")]
    _eq(c, "gmp_weaknesses_partition", sum(parts) if _all_present(*parts) else MISSING, wk.get("raised", MISSING), "standing + unverified + withdrawn vs raised")
    _eq(c, "gmp_standing_count", get(p, "standing_weaknesses"), wk.get("standing", MISSING), "standing_weaknesses vs weaknesses.standing")
    _eq(c, "gmp_withdrawn_count", get(p, "withdrawn_weaknesses"), wk.get("withdrawn", MISSING), "withdrawn_weaknesses vs weaknesses.withdrawn")
    _eq(c, "gmp_unverified_listed", _len(p, "unverified_weaknesses"), wk.get("unverified", MISSING), "unverified weaknesses listed vs counted")
    _eq(c, "gmp_unverified_match_coverage", wk.get("unverified", MISSING), get(p, "coverage.weakness_checks.unresolved"), "weaknesses.unverified vs coverage.weakness_checks.unresolved")
    _eq(c, "gmp_reviewers_match_coverage", get(p, "reviewers.completed"), get(p, "coverage.reviewers.completed"), "reviewers.completed vs coverage.reviewers.completed")
    overall = get(p, "overall_scores")
    if isinstance(overall, list):
        _eq(c, "gmp_overall_scores_match_coverage", len(overall), get(p, "coverage.overall_scores.completed"), "overall scores vs coverage.overall_scores.completed")
        mean = get(p, "overall_mean")
        if overall and all(is_num(x) for x in overall):
            want = js_round1(sum(overall) / len(overall))
            c.add("gmp_overall_mean_recomputed", is_num(mean) and abs(mean - want) < 1e-9, f"overall_mean {mean!r}; recomputed {want}")
        elif not overall:
            c.add("gmp_overall_mean_recomputed", mean is None, f"no overall scores, overall_mean {mean!r}")
    crit = get(p, "criteria")
    completed = get(p, "reviewers.completed")
    if isinstance(crit, list):
        ok = all(isinstance(x, dict) and isinstance(x.get("scores"), list) and x.get("n") == len(x["scores"]) and x.get("of") == completed and x["n"] <= x["of"] for x in crit)
        c.add("gmp_criterion_n", ok, "each criterion: n = scores listed <= of = reporting reviewers")
        if ok:
            _eq(c, "gmp_scores_match_coverage", sum(x["n"] for x in crit), get(p, "coverage.scores.completed"), "criterion scores vs coverage.scores.completed")
            _eq(c, "gmp_scores_requested", len(crit) * completed if is_int(completed) else MISSING, get(p, "coverage.scores.requested"), "criteria x reporting reviewers vs coverage.scores.requested")
            m = re.match(r"\s*(-?\d+(?:\.\d+)?)\s*[–-]\s*(-?\d+(?:\.\d+)?)", str(get(p, "scale")))
            if m:
                lo, hi = float(m.group(1)), float(m.group(2))
                scores = [s for x in crit for s in x["scores"]] + (overall if isinstance(overall, list) else [])
                off = [s for s in scores if not (is_num(s) and lo <= s <= hi)]
                c.add("gmp_scores_on_scale", not off, f"scores off the {lo:g}-{hi:g} scale: {off}" if off else f"every counted score is on the {lo:g}-{hi:g} scale")
    signals = []
    if is_int(wk.get("unverified")) and wk["unverified"] > 0:
        signals.append("weaknesses.unverified")
    if is_int(get(p, "coverage.overall_scores.off_scale")) and get(p, "coverage.overall_scores.off_scale") > 0:
        signals.append("coverage.overall_scores.off_scale")
    if _len(p, "reviewers.missing") not in (MISSING, 0):
        signals.append("reviewers.missing")
    return signals


def inv_literature_map(c: Checks, p: dict) -> list[str]:
    angles = get(p, "angles")
    if not isinstance(angles, list):
        c.add("lm_angles", None, "not applicable: the run stopped before the sweep stage")
        return []
    sw = get(p, "coverage.sweeps")
    if isinstance(sw, dict):
        _eq(c, "lm_angles_match_coverage", len(angles), sw.get("requested", MISSING), "angles vs coverage.sweeps.requested")
        _eq(c, "lm_failed_angles_listed", _len(p, "coverage.sweeps.failed_angles"), sw.get("unresolved", MISSING), "failed angles listed vs coverage.sweeps.unresolved")
    wk = get(p, "coverage.works")
    if isinstance(wk, dict):
        _eq(c, "lm_works_match_coverage", get(p, "works"), wk.get("merged", MISSING), "works vs coverage.works.merged")
        if _all_present(wk.get("clustered", MISSING), wk.get("merged", MISSING), wk.get("cap", MISSING)):
            c.add("lm_clustered_within_merged", wk["clustered"] <= min(wk["merged"], wk["cap"]), f"clustered {wk['clustered']} <= min(merged {wk['merged']}, cap {wk['cap']})")
    _eq(c, "lm_themes_match_coverage", _len(p, "themes"), get(p, "coverage.clustering.themes"), "themes vs coverage.clustering.themes")
    gp = get(p, "coverage.gaps")
    if isinstance(gp, dict):
        opened, answered = _len(p, "open_gaps"), get(p, "answered_gaps")
        _eq(c, "lm_gap_verdicts_match_coverage", opened + answered if _all_present(opened, answered) else MISSING, gp.get("completed", MISSING), "open + answered gaps vs coverage.gaps.completed")
        un, bc = gp.get("unresolved", MISSING), gp.get("beyond_cap", MISSING)
        _eq(c, "lm_unchecked_gaps_listed", _len(p, "unchecked_gaps"), un + bc if _all_present(un, bc) else MISSING, "unchecked gaps listed vs unresolved + beyond the cap")
        req = gp.get("requested", MISSING)
        _eq(c, "lm_candidates_partition", req + bc if _all_present(req, bc) else MISSING, gp.get("candidates", MISSING), "gaps checked + beyond cap vs candidates")
        if is_int(req):
            c.add("lm_gap_cap", req <= 12, f"{req} gaps searched (cap 12)")
    og, ug = get(p, "open_gaps"), get(p, "unchecked_gaps")
    if isinstance(og, list) and isinstance(ug, list):
        both = {g.get("question") for g in ug if isinstance(g, dict)} & {x for x in og if isinstance(x, str)}
        c.add("lm_unchecked_not_open", not both, f"gaps both open and unchecked: {sorted(both)}" if both else "no unchecked gap is reported as open")
    signals = []
    if _len(p, "unchecked_gaps") not in (MISSING, 0):
        signals.append("unchecked_gaps")
    if _len(p, "coverage.sweeps.failed_angles") not in (MISSING, 0):
        signals.append("coverage.sweeps.failed_angles")
    cl = get(p, "coverage.clustering")
    if isinstance(cl, dict) and is_int(cl.get("completed")) and is_int(cl.get("requested")) and cl["completed"] < cl["requested"]:
        signals.append("coverage.clustering")
    return signals


def inv_rebuttal(c: Checks, p: dict) -> list[str]:
    responded, actionable = get(p, "responded"), get(p, "actionable")
    if not is_int(responded):
        c.add("rb_responses", None, "not applicable: the run stopped before the respond stage")
        return []
    unanswered = get(p, "unanswered")
    _eq(c, "rb_responses_partition", responded + len(unanswered) if isinstance(unanswered, list) else MISSING, actionable, "responded + unanswered vs actionable comments")
    _eq(c, "rb_actionable_match_coverage", actionable, get(p, "coverage.responses.requested"), "actionable vs coverage.responses.requested")
    _eq(c, "rb_responded_match_coverage", responded, get(p, "coverage.responses.completed"), "responded vs coverage.responses.completed")
    if is_int(get(p, "comments")) and is_int(actionable):
        c.add("rb_actionable_within_comments", actionable <= get(p, "comments"), f"actionable {actionable} <= comments {get(p, 'comments')}")
    checked, issues = get(p, "consistency_checked"), get(p, "consistency_issues")
    if checked is not MISSING:
        ok = (checked is True and is_int(issues)) or (checked is False and issues is None)
        c.add("rb_consistency_not_run_is_not_zero", ok, f"consistency_checked={checked!r}, consistency_issues={issues!r} (a pass that did not run must report null, not 0)")
        done = get(p, "coverage.consistency.completed")
        _eq(c, "rb_consistency_match_coverage", checked is True, MISSING if done is MISSING else done == 1, "consistency_checked vs coverage.consistency.completed == 1")
    actions = get(p, "author_actions")
    if isinstance(actions, list) and isinstance(unanswered, list):
        both = {a.get("id") for a in actions if isinstance(a, dict)} & set(unanswered)
        c.add("rb_unanswered_have_no_drafted_actions", not both, f"comments both unanswered and with a drafted author action: {sorted(both)}" if both else "no unanswered comment carries a drafted author action")
    signals = []
    if isinstance(unanswered, list) and unanswered:
        signals.append("unanswered")
    if checked is False and responded > 0:
        signals.append("consistency_checked=false")
    return signals


def inv_screening(c: Checks, p: dict) -> list[str]:
    flow = get(p, "flow")
    if not isinstance(flow, dict):
        c.add("srs_flow", None, "not applicable: the run stopped before the report stage")
        return []
    f = lambda k: flow.get(k, MISSING)  # noqa: E731
    unresolved = get(p, "unresolved")
    included = get(p, "included_sids")
    _eq(c, "srs_screened_plus_unresolved", f("screened") + f("unresolved") if _all_present(f("screened"), f("unresolved")) else MISSING, f("submitted_for_screening"), "screened + unresolved vs submitted for screening")
    _eq(c, "srs_submitted_match_coverage", f("submitted_for_screening"), get(p, "coverage.records.requested"), "submitted vs coverage.records.requested")
    _eq(c, "srs_screened_match_coverage", f("screened"), get(p, "coverage.records.resolved"), "screened vs coverage.records.resolved")
    _eq(c, "srs_unresolved_listed", f("unresolved"), len(unresolved) if isinstance(unresolved, list) else MISSING, "flow.unresolved vs unresolved records listed")
    _eq(c, "srs_sought_is_included", f("sought_for_retrieval"), len(included) if isinstance(included, list) else MISSING, "sought for retrieval vs included sids")
    _eq(c, "srs_excluded_arithmetic", f("excluded_title_abstract"), f("screened") - f("sought_for_retrieval") if _all_present(f("screened"), f("sought_for_retrieval")) else MISSING, "excluded vs screened - sought for retrieval")
    by = f("excluded_by_criterion")
    if isinstance(by, dict):
        _eq(c, "srs_exclusion_reasons_sum", sum(v for v in by.values() if is_int(v)), f("excluded_title_abstract"), "exclusions by criterion vs excluded")
    _eq(c, "srs_not_screened_arithmetic", f("not_screened_this_run"), f("records_after_deduplication") - f("submitted_for_screening") if _all_present(f("records_after_deduplication"), f("submitted_for_screening")) else MISSING, "not screened vs after dedup - submitted")
    ident = f("identified")
    if isinstance(ident, list) and all(isinstance(x, dict) and is_int(x.get("n")) for x in ident) and _all_present(f("duplicates_removed"), f("records_after_deduplication")):
        n = sum(x["n"] for x in ident)
        c.add("srs_identification_arithmetic", n - f("duplicates_removed") == f("records_after_deduplication"), f"identified {n} - duplicates {f('duplicates_removed')} vs after dedup {f('records_after_deduplication')} (PRISMA identification)")
    if isinstance(included, list) and isinstance(unresolved, list):
        un_ids = {u.get("sid") for u in unresolved if isinstance(u, dict)}
        both = set(included) & un_ids
        c.add("srs_unresolved_not_included", not both, f"records both included and unresolved: {sorted(both)}" if both else "no unresolved record is counted as included")
        sub = f("submitted_for_screening")
        ids = list(included) + [u.get("sid") for u in unresolved if isinstance(u, dict)]
        if is_int(sub):
            c.add("srs_sids_valid", all(is_int(x) and 1 <= x <= sub for x in ids) and len(set(included)) == len(included), f"every sid is a distinct integer in 1..{sub}")
    kr = get(p, "kappa_records")
    if is_int(kr):
        _eq(c, "srs_kappa_records_match_coverage", kr, get(p, "coverage.screening.records_with_both_screeners"), "kappa_records vs dual-screened records")
    kappa, agree = get(p, "kappa"), get(p, "agreement_percent")
    c.add("srs_agreement_ranges", (kappa is None or (is_num(kappa) and -1 <= kappa <= 1)) and (agree is None or (is_num(agree) and 0 <= agree <= 100)), f"kappa {kappa!r} in [-1, 1] or null; agreement {agree!r} in [0, 100] or null")
    rb = get(p, "coverage.records.resolved_by")
    if isinstance(rb, dict):
        _eq(c, "srs_resolved_by_sum", sum(v for v in rb.values() if is_int(v)), get(p, "coverage.records.resolved"), "resolved by agreement/adjudication/second review vs resolved")
    signals = []
    if isinstance(unresolved, list) and unresolved:
        signals.append("unresolved records")
    if is_int(f("not_screened_this_run")) and f("not_screened_this_run") > 0:
        signals.append("flow.not_screened_this_run")
    if _len(p, "coverage.searches.failed_databases") not in (MISSING, 0):
        signals.append("coverage.searches.failed_databases")
    return signals


INVARIANTS: dict[str, Inv] = {
    "citation-audit": inv_citation_audit,
    "review-panel": inv_review_panel,
    "claim-stress-test": inv_claim_stress_test,
    "grant-mock-panel": inv_grant_mock_panel,
    "literature-map": inv_literature_map,
    "rebuttal": inv_rebuttal,
    "systematic-review-screening": inv_screening,
}


def check_incomplete_visible(checks: Checks, p: dict, unfinished: list[str], signals: list[str]) -> None:
    shown = [f"coverage.{s}" for s in unfinished] + signals
    status, reasons = p.get("status"), p.get("status_reasons") or []
    if not shown:
        checks.add("incomplete_work_visible", True, "no coverage shows failed or unresolved work")
        return
    ok = status != "complete" and bool(reasons)
    checks.add("incomplete_work_visible", ok, f"unfinished work in {shown}; status {status!r} with {len(reasons)} reason(s)" + ("" if ok else " — incomplete work is not surfaced"))


# ---------------------------------------------------------------- advisory findings
def _op(op: str, observed: Any, value: Any) -> bool | None:
    if op == "absent_or_zero":
        return observed is MISSING or observed in (0, None)
    if observed is MISSING:
        return None
    try:
        if op == "==":
            return observed == value
        if op == ">=":
            return observed >= value
        if op == "<=":
            return observed <= value
        if op == "in":
            return observed in value
        if op == "contains":
            return value in observed
        if op == "nonempty":
            return bool(observed)
    except TypeError:
        return False
    return None


def findings(p: dict, exp: dict, out_dir: Path) -> list[dict]:
    """Answer-key expectations about content. Reported for the reader; they never change overall."""
    out = []
    for f in exp.get("findings", []):
        if "file" in f:
            path = out_dir / f["file"]
            text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else None
            met = None if text is None else bool(re.search(f["pattern"], text, re.IGNORECASE | re.MULTILINE))
            out.append({"name": f["name"], "expected": f"{f['file']} matches /{f['pattern']}/", "observed": None if text is None else ("match" if met else "no match"), "met": met, "note": f.get("note", "")})
            continue
        observed = get(p, f["path"])
        out.append({"name": f["name"], "expected": f"{f['path']} {f['op']} {f.get('value')!r}", "observed": None if observed is MISSING else observed, "met": _op(f["op"], observed, f.get("value")), "note": f.get("note", "")})
    return out


# ---------------------------------------------------------------- main entry points
def check_payload(workflow: str, raw: Any, out_dir: Path, *, live: bool = False, expect_path: Path | None = None,
                  runtime_s: float | None = None, cost_usd: float | None = None, agents: int | None = None) -> dict:
    """Build the verdict. Raises CannotCheck when the inputs do not allow a check."""
    exp = load_expect(workflow, expect_path)
    payload, wrapped = unwrap(raw)
    markers = mock_markers(raw, wrapped)
    if live and markers:
        raise CannotCheck("refusing to mark this result live: " + "; ".join(markers))
    if isinstance(raw, dict) and wrapped and raw.get("ok") is not True:
        raise CannotCheck(f"the dry run itself failed: {raw.get('error')}")
    checks = Checks()
    files: list[dict] = []
    finds: list[dict] = []
    if check_schema(checks, payload, exp):
        check_status(checks, payload, exp)
        unfinished = check_stage_accounting(checks, payload)
        signals = INVARIANTS[workflow](checks, payload) if workflow in INVARIANTS else []
        check_incomplete_visible(checks, payload, unfinished, signals)
        files = check_files(checks, payload, exp, out_dir)
        check_report(checks, payload, exp, out_dir)
        finds = findings(payload, exp, out_dir)
    status = payload.get("status") if isinstance(payload, dict) else None
    if checks.failed():
        overall = "fail"
    elif status == "complete":
        overall = "pass"
    else:
        overall = "incomplete"
    return {
        "workflow": workflow,
        "checker_version": CHECKER_VERSION,
        "live": bool(live),
        "provenance": "live" if live else ("mock" if markers else "unspecified (not marked live)"),
        "mock_markers": markers,
        "payload_status": status,
        "status_reasons": payload.get("status_reasons") if isinstance(payload, dict) else None,
        "overall": overall,
        "checks": checks.items,
        "findings": finds,
        "findings_note": "answer-key expectations about content; reported only, never part of overall"
        + ("" if live else ". Not evidence of workflow quality unless the run was live"),
        "runtime_s": runtime_s,
        "cost_usd": cost_usd,
        "agents": agents,
        "agents_reported": get(payload, "coverage.agents") if isinstance(payload, dict) and get(payload, "coverage.agents") is not MISSING else None,
        "out_dir": str(out_dir),
        "files": files,
    }


EXIT_FOR = {"pass": EXIT_PASS, "fail": EXIT_FAIL, "incomplete": EXIT_INCOMPLETE}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--workflow", required=True, help=f"one of: {', '.join(WORKFLOWS)}")
    ap.add_argument("--out-dir", required=True, help="the directory the run wrote to (the value substituted for ${OUT_DIR})")
    ap.add_argument("--result", help="the workflow's returned payload, saved as JSON")
    ap.add_argument("--print-args", action="store_true", help="print the fixture args with ${OUT_DIR} substituted, then exit")
    ap.add_argument("--live", action="store_true", help="the result comes from a real Workflow run (refused for dry-run output)")
    ap.add_argument("--expect", help="an expect.json to use instead of the fixture's")
    ap.add_argument("--runtime-s", type=float)
    ap.add_argument("--cost-usd", type=float)
    ap.add_argument("--agents", type=int)
    ap.add_argument("--output", help="also write the verdict JSON here")
    a = ap.parse_args(argv)

    def cannot(msg: str) -> int:
        print(json.dumps({"workflow": a.workflow, "overall": "not_checked", "live": False, "error": msg}, indent=1))
        return EXIT_CANNOT

    try:
        if a.print_args:
            print(json.dumps(fixture_args(a.workflow, a.out_dir), indent=1, ensure_ascii=False))
            return EXIT_PASS
        if not a.result:
            return cannot("--result is required (or use --print-args)")
        raw = load_json(Path(a.result), "result")
        verdict = check_payload(a.workflow, raw, Path(a.out_dir), live=a.live, expect_path=Path(a.expect) if a.expect else None,
                                runtime_s=a.runtime_s, cost_usd=a.cost_usd, agents=a.agents)
    except CannotCheck as e:
        return cannot(str(e))
    text = json.dumps(verdict, indent=1, ensure_ascii=False)
    print(text)
    if a.output:
        Path(a.output).write_text(text + "\n", encoding="utf-8")
    return EXIT_FOR[verdict["overall"]]


if __name__ == "__main__":
    sys.exit(main())
