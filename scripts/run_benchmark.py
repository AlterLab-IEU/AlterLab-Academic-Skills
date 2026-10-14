#!/usr/bin/env python3
"""Run the small live behavioral benchmark in ``benchmarks/<task>/task.json``.

Each task names an existing skill and holds a few cases. Each case has realistic fixtures and a
list of items, each with an expected label (or a number) and an evidence anchor. Both arms — the
skilled arm (SKILL.md appended, skill files in ./skill/) and the bare arm (task only) — answer the
same prompt in isolated workspaces through the ``claude`` CLI (the same isolation as
``run_evals.py --behavioral``). The harness appends the item list and asks for a JSON block, then
scores every item **deterministically** against the expected answers. No LLM judge is involved.

Per arm it measures: correct items; false approvals (a problem labelled as fine — e.g. a
fabricated reference marked VERIFIED, an ineligible record INCLUDED); false accusations (a fine
item labelled as a problem — e.g. a real reference called fabricated); abstentions, split into
correct abstentions (the input really lacks the answer) and unnecessary ones; overconfident
answers on incomplete input; missing items; completion (a parseable answer covering every item);
runtime, turns, CLI-reported cost, and permission denials.

This is a small benchmark of five tasks. Its numbers describe these cases only; they do not
validate the other skills in the catalog. Simulated runs (``--dry-run``) print prompts and never
produce results.

    uv run python scripts/run_benchmark.py                      # every task, 1 run per arm
    uv run python scripts/run_benchmark.py --task screening --runs 2
    uv run python scripts/run_benchmark.py --dry-run            # show prompts, call nothing

Exit codes: 0 = measured (every arm of every case returned a parseable answer); 3 = partial
(some arms failed or were unparseable — reported, never scored as correct); 2 = blocked
(nothing usable, or no ``claude`` CLI); 64 = a task file is invalid.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_evals as rv  # noqa: E402  (shared isolation, CLI call, workspace and metadata)

REPO = rv.REPO
BENCH = REPO / "benchmarks"


# --- Task loading and validation ---------------------------------------------------------
def task_files() -> list[Path]:
    return sorted(BENCH.glob("*/task.json"))


def validate_task(path: Path) -> list[str]:
    """Structural problems in one task file (empty list = valid)."""
    errs: list[str] = []
    try:
        task = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{path}: unreadable JSON ({exc})"]
    for key in ("id", "title", "skill_dir", "label_semantics", "cases"):
        if key not in task:
            errs.append(f"{path}: missing '{key}'")
    if errs:
        return errs
    if task["id"] != path.parent.name:
        errs.append(f"{path}: id '{task['id']}' must equal its directory name")
    skill_dir = REPO / task["skill_dir"]
    if not (skill_dir / "SKILL.md").is_file():
        errs.append(f"{path}: skill_dir {task['skill_dir']} has no SKILL.md")
    sem = task["label_semantics"]
    approve, abstain = set(sem.get("approve", [])), set(sem.get("abstain", []))
    if not approve or not abstain:
        errs.append(f"{path}: label_semantics needs non-empty 'approve' and 'abstain'")
    seen_cases: set[str] = set()
    for case in task["cases"]:
        cid = case.get("id", "?")
        where = f"{path}:{cid}"
        if cid in seen_cases:
            errs.append(f"{where}: duplicate case id")
        seen_cases.add(cid)
        labels = set(case.get("labels", []))
        if not case.get("prompt") or not labels or not case.get("items"):
            errs.append(f"{where}: needs prompt, labels, and items")
            continue
        if not approve <= labels or not abstain <= labels:
            errs.append(f"{where}: approve/abstain labels must be in the case's labels")
        for f in case.get("files", []):
            if not (path.parent / f).is_file():
                errs.append(f"{where}: fixture {f} does not exist")
        seen_items: set[str] = set()
        for item in case["items"]:
            iid = item.get("id", "?")
            if iid in seen_items:
                errs.append(f"{where}:{iid}: duplicate item id")
            seen_items.add(iid)
            if not item.get("question") or not item.get("anchor"):
                errs.append(f"{where}:{iid}: needs question and anchor")
            if item.get("kind") == "number":
                if not isinstance(item.get("expected"), (int, float)) or not isinstance(
                        item.get("tolerance"), (int, float)):
                    errs.append(f"{where}:{iid}: number items need numeric expected/tolerance")
            else:
                accept = set(item.get("accept") or [item.get("expected")])
                if item.get("expected") not in labels or not accept <= labels:
                    errs.append(f"{where}:{iid}: expected/accept must be among the labels")
                if item.get("expected") not in accept:
                    errs.append(f"{where}:{iid}: expected must be in accept")
    return errs


# --- Prompt and parsing ------------------------------------------------------------------
def build_case_prompt(case: dict, fixture_paths: list[str]) -> str:
    lines = [case["prompt"].rstrip(), ""]
    if fixture_paths:
        lines += ["Input files (read them):", *[f"- {p}" for p in fixture_paths], ""]
    labels = ", ".join(case["labels"])
    lines.append("Answer each item below.")
    for item in case["items"]:
        kind = "a number" if item.get("kind") == "number" else f"one label from: {labels}"
        lines.append(f"- {item['id']} ({kind}): {item['question']}")
    lines += [
        "",
        "Finish your reply with one fenced ```json block of exactly this form, covering every "
        "item id above:",
        '{"items": [{"id": "<item id>", "label": "<one allowed label, or null for number '
        'items>", "value": <number or null>, "evidence": "<short reason, quoting the input>"}]}',
        "Use a label meaning that the answer cannot be determined whenever the input does not "
        "establish it; do not guess.",
    ]
    return "\n".join(lines)


_FENCE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def parse_answer(text: str) -> dict[str, dict] | None:
    """{item id: {"label", "value"}} from the last JSON block, or None if there is none."""
    candidates = _FENCE.findall(text)
    if not candidates:
        start = text.rfind('{"items"')
        candidates = [text[start:]] if start >= 0 else []
    for raw in reversed(candidates):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        items = data.get("items") if isinstance(data, dict) else None
        if not isinstance(items, list):
            continue
        out: dict[str, dict] = {}
        for it in items:
            if isinstance(it, dict) and isinstance(it.get("id"), str) and it["id"] not in out:
                out[it["id"]] = {"label": it.get("label"), "value": it.get("value")}
        return out
    return None


# --- Scoring -----------------------------------------------------------------------------
def score_case(case: dict, semantics: dict, answer: dict[str, dict] | None) -> dict:
    """Deterministic per-item scoring of one arm's answer to one case."""
    approve, abstain = set(semantics["approve"]), set(semantics["abstain"])
    labels = set(case["labels"])
    items: list[dict] = []
    tally = {"items": 0, "correct": 0, "false_approval": 0, "false_accusation": 0,
             "abstained": 0, "correct_abstention": 0, "unnecessary_abstention": 0,
             "overconfident_on_incomplete": 0, "wrong_other": 0, "missing": 0,
             "invalid_label": 0}
    for item in case["items"]:
        tally["items"] += 1
        got = (answer or {}).get(item["id"])
        rec = {"id": item["id"], "expected": item.get("expected"), "got": None, "result": None}
        if got is None:
            rec["result"] = "missing"
            tally["missing"] += 1
            items.append(rec)
            continue
        label = got.get("label")
        label = label.strip().upper() if isinstance(label, str) else None
        rec["got"] = label if item.get("kind") != "number" else got.get("value", label)
        if item.get("kind") == "number":
            value = got.get("value")
            if label in abstain or value is None:
                rec["result"] = "abstained"
                tally["abstained"] += 1
                tally["unnecessary_abstention"] += 1
            else:
                try:
                    ok = abs(float(value) - float(item["expected"])) <= float(item["tolerance"])
                except (TypeError, ValueError):
                    ok = False
                rec["result"] = "correct" if ok else "wrong_other"
                tally["correct" if ok else "wrong_other"] += 1
            items.append(rec)
            continue
        expected = item["expected"]
        accept = set(item.get("accept") or [expected])
        if label not in labels:
            rec["result"] = "invalid_label"
            tally["invalid_label"] += 1
        elif label in accept:
            rec["result"] = "correct"
            tally["correct"] += 1
            if label in abstain:
                tally["abstained"] += 1
                tally["correct_abstention"] += 1
        elif label in abstain:
            rec["result"] = "unnecessary_abstention"
            tally["abstained"] += 1
            tally["unnecessary_abstention"] += 1
        elif expected in abstain:
            # Incomplete input answered definitely. An approval here is also a false approval.
            rec["result"] = "overconfident_on_incomplete"
            tally["overconfident_on_incomplete"] += 1
            if label in approve:
                tally["false_approval"] += 1
        elif expected not in approve and label in approve:
            rec["result"] = "false_approval"
            tally["false_approval"] += 1
        elif expected in approve and label not in approve:
            rec["result"] = "false_accusation"
            tally["false_accusation"] += 1
        else:
            rec["result"] = "wrong_other"  # e.g. PAC called TF: wrong, but neither error type
            tally["wrong_other"] += 1
        items.append(rec)
    answered = tally["items"] - tally["missing"]
    tally["complete"] = answer is not None and tally["missing"] == 0 and not tally["invalid_label"]
    tally["answered"] = answered
    return {"tally": tally, "items": items}


def _sum(tallies: list[dict]) -> dict:
    keys = [k for k in (tallies[0] if tallies else {}) if isinstance(tallies[0][k], int)
            and not isinstance(tallies[0][k], bool)]
    out = {k: sum(t[k] for t in tallies) for k in keys}
    out["cases"] = len(tallies)
    out["complete_cases"] = sum(bool(t.get("complete")) for t in tallies)
    return out


# --- Running -----------------------------------------------------------------------------
def run_arm(task: dict, case: dict, task_dir: Path, arm: str, model: str, timeout: int,
            run_no: int) -> dict:
    skill_dir = REPO / task["skill_dir"] if arm == "skilled" else None
    with tempfile.TemporaryDirectory(prefix=f"alterlab-bench-{arm}-") as tmp:
        ws = Path(tmp)
        fixtures = rv.prepare_workspace(ws, {"files": case.get("files", [])}, task_dir, skill_dir)
        prompt = build_case_prompt(case, fixtures)
        system = None
        if skill_dir is not None:
            system = (skill_dir / "SKILL.md").read_text(encoding="utf-8") + rv._SKILL_RUNTIME_NOTE
        tools = task.get("allowed_tools") or ["Read", "Glob", "Grep"]
        call = rv._claude_call(prompt, model, timeout, system=system, cwd=ws,
                               extra_args=["--allowedTools", *tools])
    answer = parse_answer(call.text) if call.outcome == "answer" else None
    scored = score_case(case, task["label_semantics"], answer)
    status = ("answered" if answer is not None else
              "unparseable" if call.outcome == "answer" else call.outcome)
    return {"arm": arm, "run": run_no, "status": status, "error": call.error or None,
            "duration_ms": call.duration_ms, "cost_usd": call.cost_usd,
            "num_turns": call.num_turns, "permission_denials": call.permission_denials,
            "tally": scored["tally"], "items": scored["items"],
            "response_excerpt": call.text[-2500:] if call.outcome == "answer" else None}


def _markdown(payload: dict) -> str:
    lines = [f"Benchmark run {payload['started_at']} — model `{payload['model']}`, "
             f"CLI {payload['claude_cli_version']}, commit `{(payload['repo_commit'] or '')[:10]}`"
             f"{' (dirty)' if payload['repo_dirty'] else ''}, {payload['runs_per_arm']} run(s) "
             f"per arm, status **{payload['status']}**.", "",
             "| Task | Arm | Items | Correct | False approvals | False accusations | "
             "Correct abstentions | Unnecessary abstentions | Overconfident on incomplete | "
             "Missing | Complete cases | Time (s) | Cost (CLI-reported) |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for t in payload["tasks"]:
        for arm in ("skilled", "bare"):
            s = t["summary"][arm]
            lines.append(
                f"| {t['id']} | {arm} | {s['items']} | {s['correct']} | {s['false_approval']} | "
                f"{s['false_accusation']} | {s['correct_abstention']} | "
                f"{s['unnecessary_abstention']} | {s['overconfident_on_incomplete']} | "
                f"{s['missing']} | {s['complete_cases']}/{s['cases']} | "
                f"{s['duration_ms'] / 1000:.0f} | ${s['cost_usd']:.2f} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", action="append", help="only this task id (repeatable)")
    ap.add_argument("--case", action="append", help="only this case id (repeatable)")
    ap.add_argument("--runs", type=int, default=1, help="runs per arm (default 1)")
    ap.add_argument("--timeout", type=int, default=900, help="per-call timeout in seconds")
    ap.add_argument("--results-dir", default=str(REPO / "eval-results"),
                    help="where to write the JSON results ('' to skip)")
    ap.add_argument("--markdown", metavar="PATH", help="also write a Markdown summary table")
    ap.add_argument("--dry-run", action="store_true",
                    help="validate tasks and print prompts; make no model calls")
    args = ap.parse_args(argv)

    files = task_files()
    errors = [e for f in files for e in validate_task(f)]
    if errors:
        print("Invalid benchmark task file(s):\n  " + "\n  ".join(errors), file=sys.stderr)
        return 64
    tasks = [(f.parent, json.loads(f.read_text(encoding="utf-8"))) for f in files]
    if args.task:
        tasks = [(d, t) for d, t in tasks if t["id"] in args.task]
    if not tasks:
        print("No benchmark task selected.", file=sys.stderr)
        return 2

    if args.dry_run:
        for d, t in tasks:
            for c in t["cases"]:
                if args.case and c["id"] not in args.case:
                    continue
                print(f"===== {t['id']}:{c['id']} ({c.get('kind', 'standard')}) =====")
                print(build_case_prompt(c, [f"fixtures/{Path(f).name}" for f in c.get("files", [])]))
        print("\nDRY RUN: no model calls were made and no results were produced.")
        return 0

    if shutil.which("claude") is None:
        print("BLOCKED: the `claude` CLI is not on PATH.", file=sys.stderr)
        return 2

    model = rv.alterlab_model()
    rv._reset_usage()
    started = time.monotonic()
    meta = rv._run_metadata("benchmark", model, args.runs, args.timeout)
    meta["started_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print("=== LIVE BENCHMARK (deterministic item scoring; skilled vs bare) ===")
    task_payloads = []
    arm_statuses: list[str] = []
    for task_dir, task in tasks:
        case_payloads = []
        for case in task["cases"]:
            if args.case and case["id"] not in args.case:
                continue
            arms = []
            for run_no in range(1, args.runs + 1):
                for arm in ("skilled", "bare"):
                    res = run_arm(task, case, task_dir, arm, model, args.timeout, run_no)
                    arms.append(res)
                    arm_statuses.append(res["status"])
                    tl = res["tally"]
                    print(f"{task['id']}:{case['id']} [{arm} run {run_no}] {res['status']}: "
                          f"{tl['correct']}/{tl['items']} correct, FA={tl['false_approval']} "
                          f"FX={tl['false_accusation']} abstain={tl['abstained']} "
                          f"missing={tl['missing']} ({(res['duration_ms'] or 0) / 1000:.0f}s)"
                          + (f" — {res['error']}" if res["error"] else ""))
            case_payloads.append({"id": case["id"], "kind": case.get("kind", "standard"),
                                  "arms": arms})
        summary = {}
        for arm in ("skilled", "bare"):
            runs = [a for c in case_payloads for a in c["arms"] if a["arm"] == arm]
            s = _sum([a["tally"] for a in runs]) if runs else {}
            s["duration_ms"] = sum(a["duration_ms"] or 0 for a in runs)
            s["cost_usd"] = round(sum(a["cost_usd"] or 0 for a in runs), 4)
            s["unanswered_runs"] = sum(a["status"] != "answered" for a in runs)
            summary[arm] = s
        task_payloads.append({"id": task["id"], "title": task["title"],
                              "skill_dir": task["skill_dir"],
                              "label_semantics": task["label_semantics"],
                              "summary": summary, "cases": case_payloads})

    usable = sum(s == "answered" for s in arm_statuses)
    status = ("blocked" if usable == 0 else
              "measured" if usable == len(arm_statuses) else "partial")
    payload = {**meta, "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "status": status,
               "scope_note": "Five-task benchmark; results describe these cases only and do "
                             "not validate other skills.",
               "usage": {**rv._USAGE, "wall_clock_s": round(time.monotonic() - started, 1)},
               "tasks": task_payloads}
    path = rv._write_results(Path(args.results_dir) if args.results_dir else None,
                             "benchmark", payload)
    md = _markdown(payload)
    print("\n" + md)
    if args.markdown:
        Path(args.markdown).write_text(md, encoding="utf-8")
    if path:
        print(f"results: {path.relative_to(REPO) if path.is_relative_to(REPO) else path}")
    if status != "measured":
        print(f"{status.upper()}: {len(arm_statuses) - usable} of {len(arm_statuses)} arm runs "
              "returned no parseable answer; their items count as missing.", file=sys.stderr)
    return {"measured": 0, "partial": 3, "blocked": 2}[status]


if __name__ == "__main__":
    raise SystemExit(main())
