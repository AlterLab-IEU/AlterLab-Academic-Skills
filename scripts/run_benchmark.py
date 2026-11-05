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

Scoring schema 2 (``scoring_schema_version`` in the payload and in every task): an item id given
twice with different answers is an **unresolved conflict** — never correct, counted separately,
case incomplete, every answer kept; identical repeats collapse (``duplicate_ids_collapsed``);
ids the case does not know are listed per arm (``unknown_ids``). Each answer's evidence text is
kept and checked deterministically, separately from label accuracy: ``quote_in_fixture`` (a
quoted span of at least ``min_quote_chars`` occurs verbatim in a fixture) and
``quote_in_item_region`` (it occurs in the lines the item's anchor cites, or in the item's
reference entry). Evidence that passes neither is ``needs_review``, not wrong; these checks do
not judge whether evidence supports a label. ``--export-evidence-review PATH`` writes every
answered item as JSONL for a human or model reviewer (``--from-results`` rebuilds it from a saved
results file without any model call). Schema-1 results (label-only, first duplicate wins) are
not directly comparable.

This is a small benchmark of five tasks. Its numbers describe these cases only; they do not
validate the other skills in the catalog. Simulated runs (``--dry-run``) print prompts and never
produce results.

    uv run python scripts/run_benchmark.py                      # every task, 1 run per arm
    uv run python scripts/run_benchmark.py --task screening --runs 2
    uv run python scripts/run_benchmark.py --dry-run            # show prompts, call nothing
    uv run python scripts/run_benchmark.py --runs 2 --export-evidence-review review.jsonl
    uv run python scripts/run_benchmark.py --from-results eval-results/benchmark-X.json \
        --export-evidence-review review.jsonl                   # no model calls

Exit codes: 0 = measured (every arm of every case returned a parseable answer); 3 = partial
(some arms failed or were unparseable — reported, never scored as correct); 2 = blocked
(nothing usable, or no ``claude`` CLI); 64 = a task file is invalid, or the ``--from-results``
file is unreadable or predates scoring schema 2.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
import time
import unicodedata
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
    ev = task.get("evidence_checks", {})
    if not isinstance(ev, dict) or set(ev) - {"min_quote_chars", "item_region", "note"}:
        errs.append(f"{path}: evidence_checks may hold only min_quote_chars, item_region, note")
    elif ev.get("item_region", "anchor_line_refs") not in ITEM_REGION_MODES or not (
            isinstance(ev.get("min_quote_chars", 20), int) and ev.get("min_quote_chars", 20) >= 8):
        errs.append(f"{path}: evidence_checks needs item_region in {ITEM_REGION_MODES} and an "
                    "integer min_quote_chars >= 8")
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
        if "allowed_tools" in case and not isinstance(case["allowed_tools"], list):
            errs.append(f"{where}: allowed_tools must be a list")
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
                if "truth" in item and item["truth"] not in labels:
                    errs.append(f"{where}:{iid}: truth must be among the labels")
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


def _norm_label(label: object) -> str | None:
    return label.strip().upper() if isinstance(label, str) else None


def _answer_key(entry: dict) -> str:
    """What two entries for the same id must share to count as the same answer: the label
    (trimmed, upper-cased) and the value (numbers compared as floats). Evidence is not part of
    it — two identical answers with different reasons are the same answer."""
    value = entry.get("value")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        value = float(value)
    elif isinstance(value, str):
        try:
            value = float(value.strip())
        except ValueError:
            value = value.strip()
    return json.dumps([_norm_label(entry.get("label")), value], sort_keys=True, default=str)


def _merge_duplicates(entries: list[dict]) -> dict:
    """One id given several times. Identical answers collapse (``duplicates`` counts the extra
    copies; differing evidence is kept in ``alternate_evidence``). Different answers are an
    unresolved conflict: ``{"conflict": [every entry, in order]}``, which is never scored."""
    first = entries[0]
    if len(entries) == 1:
        return first
    if len({_answer_key(e) for e in entries}) > 1:
        return {"conflict": entries}
    merged = {**first, "duplicates": len(entries) - 1}
    alternates = [e["evidence"] for e in entries[1:]
                  if e["evidence"] and e["evidence"] != first["evidence"]]
    if alternates:
        merged["alternate_evidence"] = alternates
    return merged


def parse_answer(text: str) -> dict[str, dict] | None:
    """{item id: {"label", "value", "evidence"}} from the last parseable JSON block, or None if
    there is none.

    The last block wins (a reply may show drafts before its final answer). Within that block a
    repeated id is resolved by ``_merge_duplicates``: identical copies collapse, conflicting
    copies become ``{"conflict": [...]}``. Ids are kept even when the case does not know them,
    so the scorer can report them.
    """
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
        groups: dict[str, list[dict]] = {}
        for it in items:
            if isinstance(it, dict) and isinstance(it.get("id"), str):
                evidence = it.get("evidence")
                groups.setdefault(it["id"], []).append({
                    "label": it.get("label"), "value": it.get("value"),
                    "evidence": evidence if isinstance(evidence, str) and evidence.strip()
                    else None})
        return {iid: _merge_duplicates(entries) for iid, entries in groups.items()}
    return None


# --- Evidence checks (deterministic; they never decide whether a label is right) ---------
# Each check is named for exactly what it tests. Neither check judges whether the evidence
# *supports* the label: evidence that passes no check is ``needs_review`` (not "wrong"), and
# ``--export-evidence-review`` writes every answer out for a human or model reviewer.
#
# quote_in_fixture      the evidence contains a quoted span (">= min_quote_chars" after
#                       normalisation) that occurs verbatim in one of the case's fixture files.
# quote_in_item_region  such a span occurs inside the item's own region of the fixtures:
#                       "anchor_line_refs" = the fixture lines the item's anchor cites right
#                       after naming a fixture file ("records_batch_A.txt L16-L22"; see
#                       anchor_line_refs);
#                       "entry_prefix" = the fixture paragraph that starts "<item id>." (the
#                       reference-list entry of a citation item).
# Normalisation: Unicode NFKC, curly quotes and dashes made plain, "*" and "`" dropped,
# fixture line labels ("L12: ") removed from fixtures and quotes alike, whitespace collapsed,
# case folded. A quote may be split by an ellipsis; each fragment counts on its own.
SCORING_SCHEMA_VERSION = 2
DEFAULT_EVIDENCE_CONFIG = {"min_quote_chars": 20, "item_region": "anchor_line_refs"}
ITEM_REGION_MODES = ("anchor_line_refs", "entry_prefix", "none")
EVIDENCE_STATUSES = ("quote_in_item_region", "quote_in_fixture", "needs_review", "missing")

_STRAIGHTEN = str.maketrans({"\u201c": '"', "\u201d": '"', "\u201e": '"', "\u2033": '"',
                             "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u2032": "'"})
_PLAIN = str.maketrans({"\u00a0": " ", "\u2010": "-", "\u2011": "-", "\u2012": "-",
                        "\u2013": "-", "\u2014": "-", "\u2212": "-", "*": None, "`": None})
_QUOTED = (re.compile(r'"([^"\n]+)"'), re.compile(r"(?<!\w)'([^\n]+?)'(?!\w)"),
           re.compile("\u00ab([^\u00bb\n]+)\u00bb"), re.compile(r"`([^`\n]+)`"))
_ELLIPSIS = re.compile("\\[?(?:\\.\\.\\.|\u2026)\\]?")
_LINE_LABEL = re.compile(r"^L\d+:\s?")
_INLINE_LABEL = re.compile(r"(?<!\w)L\d+:\s?")  # "L19: " copied into a quote
_CHAIN_GAP = re.compile(r"[\s,]*(?:and\s+)?")
_REF = re.compile(r"(?P<file>[\w./-]*\w\.(?:md|txt|csv|tsv|json|py|ya?ml))\b"
                  r"|(?<!\w)L(?P<a>\d+)(?:\s*[-\u2013]\s*L?(?P<b>\d+))?"
                  r"|(?<!\w)[Ll]ines?\s+(?P<c>\d+)(?:\s*[-\u2013]\s*(?P<d>\d+))?")


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).translate(_STRAIGHTEN).translate(_PLAIN)
    return " ".join(text.split()).casefold()


def quoted_spans(evidence: str, min_chars: int) -> list[str]:
    """Normalised quoted fragments of ``evidence`` at least ``min_chars`` long."""
    text = unicodedata.normalize("NFKC", evidence).translate(_STRAIGHTEN)
    spans: list[str] = []
    for rx in _QUOTED:
        for m in rx.finditer(text):
            for frag in _ELLIPSIS.split(_INLINE_LABEL.sub("", m.group(1))):
                frag = _norm(frag).strip(" .,;:!?()[]")
                if len(frag) >= min_chars and frag not in spans:
                    spans.append(frag)
    return spans


def evidence_config(task: dict) -> dict:
    return {**DEFAULT_EVIDENCE_CONFIG, **(task.get("evidence_checks") or {})}


def load_fixtures(task_dir: Path, case: dict) -> dict[str, str]:
    """{fixture file name: text} for one case, read from the task directory."""
    return {Path(f).name: (task_dir / f).read_text(encoding="utf-8")
            for f in case.get("files", [])}


def _fixture_lines(text: str) -> list[str]:
    return [_LINE_LABEL.sub("", line) for line in text.splitlines()]


def anchor_line_refs(anchor: str, fixture_names: set[str]) -> list[tuple[str, int, int]]:
    """(fixture, first line, last line) for the line references an anchor attaches to a
    fixture file by name.

    Only references written right after a file name count ("analysis_log_A.md L8-L9",
    "x.csv lines 3-14", "x.md L9 and L27", "x.md L2, L14-L15"); they are dropped when the file
    is not one of the case's fixtures (e.g. "SKILL.md L101-L113"). Free-standing references
    such as "(L19)" or "; L44-L45" are ignored: in free-text anchors they refer sometimes to
    the record, sometimes to a protocol or a skill file, and guessing would make the check
    unsound.
    """
    refs: list[tuple[str, int, int]] = []
    chain: str | None = None  # file of the current run of adjacent references
    prev_end = 0
    for m in _REF.finditer(anchor):
        gap = anchor[prev_end:m.start()]
        prev_end = m.end()
        if m.group("file"):
            name = Path(m.group("file")).name
            chain = name if name in fixture_names else None
            continue
        if chain is None or not _CHAIN_GAP.fullmatch(gap):
            chain = None
            continue
        a = int(m.group("a") or m.group("c"))
        b = int(m.group("b") or m.group("d") or a)
        ref = (chain, min(a, b), max(a, b))
        if ref not in refs:
            refs.append(ref)
    return refs


def _entry_refs(item_id: str, fixtures: dict[str, str]) -> list[tuple[str, int, int]]:
    head = re.compile(rf"{re.escape(item_id)}\.\s")
    refs = []
    for name, text in fixtures.items():
        lines = _fixture_lines(text)
        for i, line in enumerate(lines):
            if head.match(line):
                j = i
                while j + 1 < len(lines) and lines[j + 1].strip():
                    j += 1
                refs.append((name, i + 1, j + 1))
    return refs


def item_region(item: dict, fixtures: dict[str, str], mode: str) -> list[tuple[str, int, int]]:
    if mode == "anchor_line_refs":
        return anchor_line_refs(item.get("anchor", ""), set(fixtures))
    if mode == "entry_prefix":
        return _entry_refs(item["id"], fixtures)
    return []


def _span_check(spans: list[str], texts: list[str]) -> dict:
    if not texts:
        return {"result": "not_applicable", "matched": None}
    if not spans:
        return {"result": "no_quote", "matched": None}
    matched = next((s for s in spans if any(s in t for t in texts)), None)
    return {"result": "pass" if matched else "no_match", "matched": matched}


def check_evidence(evidence: str | None, item: dict, fixtures: dict[str, str],
                   config: dict) -> tuple[str, dict]:
    """(evidence_status, per-check results) for one answered item."""
    if not evidence:
        return "missing", {}
    spans = quoted_spans(evidence, int(config["min_quote_chars"]))
    lines = {name: _fixture_lines(text) for name, text in fixtures.items()}
    whole = _span_check(spans, [_norm(" ".join(v)) for v in lines.values()])
    whole["spans_checked"] = len(spans)
    region = item_region(item, fixtures, config["item_region"]) if fixtures else []
    local = _span_check(spans, [_norm(" ".join(lines[n][a - 1:b])) for n, a, b in region])
    local["source"] = config["item_region"]
    local["region"] = [{"file": n, "lines": [a, b]} for n, a, b in region] or None
    checks = {"quote_in_fixture": whole, "quote_in_item_region": local}
    status = ("quote_in_item_region" if local["result"] == "pass" else
              "quote_in_fixture" if whole["result"] == "pass" else "needs_review")
    return status, checks


# --- Scoring -----------------------------------------------------------------------------
def score_case(case: dict, semantics: dict, answer: dict[str, dict] | None,
               fixtures: dict[str, str] | None = None, evidence_cfg: dict | None = None) -> dict:
    """Deterministic per-item scoring of one arm's answer to one case.

    Labels and numbers are scored against the expected answers. Evidence is scored separately
    (``check_evidence``) and never changes an item's ``result``. An id given twice with
    different answers is ``unresolved_conflict``: never correct, and the case is incomplete.
    Ids the case does not know are listed in ``unknown_ids``.
    """
    approve, abstain = set(semantics["approve"]), set(semantics["abstain"])
    labels = set(case["labels"])
    fixtures = fixtures or {}
    cfg = {**DEFAULT_EVIDENCE_CONFIG, **(evidence_cfg or {})}
    items: list[dict] = []
    tally = {"items": 0, "correct": 0, "false_approval": 0, "false_accusation": 0,
             "abstained": 0, "correct_abstention": 0, "unnecessary_abstention": 0,
             "overconfident_on_incomplete": 0, "wrong_other": 0, "missing": 0,
             "invalid_label": 0, "unresolved_conflict": 0, "duplicate_ids_collapsed": 0,
             "unknown_ids": 0, **{f"evidence_{k}": 0 for k in EVIDENCE_STATUSES}}
    case_ids = [item["id"] for item in case["items"]]
    unknown_ids = [k for k in (answer or {}) if k not in case_ids]
    tally["unknown_ids"] = len(unknown_ids)
    for item in case["items"]:
        tally["items"] += 1
        got = (answer or {}).get(item["id"])
        rec = {"id": item["id"], "expected": item.get("expected"), "got": None, "result": None,
               "evidence": None, "evidence_status": "no_answer", "evidence_checks": {}}
        if got is None:
            rec["result"] = "missing"
            tally["missing"] += 1
            items.append(rec)
            continue
        if "conflict" in got:
            rec.update(result="unresolved_conflict", evidence_status="not_assessed",
                       answers=got["conflict"])
            tally["unresolved_conflict"] += 1
            items.append(rec)
            continue
        if got.get("duplicates"):
            rec["duplicates"] = got["duplicates"]
            tally["duplicate_ids_collapsed"] += got["duplicates"]
        if got.get("alternate_evidence"):
            rec["alternate_evidence"] = got["alternate_evidence"]
        rec["evidence"] = got.get("evidence")
        rec["evidence_status"], rec["evidence_checks"] = check_evidence(
            rec["evidence"], item, fixtures, cfg)
        tally[f"evidence_{rec['evidence_status']}"] += 1
        label = _norm_label(got.get("label"))
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
            # Incomplete input answered definitely. ``truth`` (default: expected) says what the
            # item really is, so a definite answer can still be typed as a false approval
            # (approving a problem) or a false accusation (flagging a fine item).
            rec["result"] = "overconfident_on_incomplete"
            tally["overconfident_on_incomplete"] += 1
            truth = item.get("truth", expected)
            if label in approve and truth not in approve:
                tally["false_approval"] += 1
            elif label not in approve and truth in approve:
                tally["false_accusation"] += 1
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
    tally["complete"] = (answer is not None and tally["missing"] == 0
                         and not tally["invalid_label"] and not tally["unresolved_conflict"])
    tally["answered"] = tally["items"] - tally["missing"] - tally["unresolved_conflict"]
    return {"tally": tally, "items": items, "unknown_ids": unknown_ids,
            "missing_ids": [r["id"] for r in items if r["result"] == "missing"]}


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
        # A case may narrow the tools (e.g. an offline variant with no network access).
        tools = case.get("allowed_tools") or task.get("allowed_tools") or ["Read", "Glob", "Grep"]
        call = rv._claude_call(prompt, model, timeout, system=system, cwd=ws,
                               extra_args=["--allowedTools", *tools])
    answer = parse_answer(call.text) if call.outcome == "answer" else None
    scored = score_case(case, task["label_semantics"], answer, load_fixtures(task_dir, case),
                        evidence_config(task))
    status = ("answered" if answer is not None else
              "unparseable" if call.outcome == "answer" else call.outcome)
    return {"arm": arm, "run": run_no, "status": status, "error": call.error or None,
            "duration_ms": call.duration_ms, "cost_usd": call.cost_usd,
            "num_turns": call.num_turns, "permission_denials": call.permission_denials,
            "tally": scored["tally"], "items": scored["items"],
            "unknown_ids": scored["unknown_ids"], "missing_ids": scored["missing_ids"],
            "response_excerpt": call.text[-2500:] if call.outcome == "answer" else None}


_MD_COLUMNS = (  # (header, summary key or callable)
    ("Items", "items"), ("Correct", "correct"),
    ("Label accuracy", lambda s: f"{100 * s['correct'] / s['items']:.1f}%" if s.get("items")
     else "—"),
    ("False approvals", "false_approval"), ("False accusations", "false_accusation"),
    ("Correct abstentions", "correct_abstention"),
    ("Unnecessary abstentions", "unnecessary_abstention"),
    ("Overconfident on incomplete", "overconfident_on_incomplete"), ("Missing", "missing"),
    ("Unresolved conflicts", "unresolved_conflict"),
    ("Evidence: quote in item region", "evidence_quote_in_item_region"),
    ("Evidence: quote elsewhere in fixtures", "evidence_quote_in_fixture"),
    ("Evidence: needs review", "evidence_needs_review"),
    ("Evidence: none given", "evidence_missing"),
    ("Complete cases", lambda s: f"{s.get('complete_cases', 0)}/{s.get('cases', 0)}"),
    ("Time (s)", lambda s: f"{(s.get('duration_ms') or 0) / 1000:.0f}"),
    ("Cost (CLI-reported)", lambda s: f"${s.get('cost_usd') or 0:.2f}"),
)


def _markdown(payload: dict) -> str:
    lines = [f"Benchmark run {payload['started_at']} — model `{payload['model']}`, "
             f"CLI {payload['claude_cli_version']}, commit `{(payload['repo_commit'] or '')[:10]}`"
             f"{' (dirty)' if payload['repo_dirty'] else ''}, {payload['runs_per_arm']} run(s) "
             f"per arm, status **{payload['status']}**, scoring schema "
             f"{payload.get('scoring_schema_version', 1)}.", "",
             "Label accuracy and evidence are reported separately. The evidence columns are "
             "deterministic checks of the quotes in each answer's evidence (see "
             "docs/benchmark-results.md); they do not judge whether the evidence supports the "
             "label, and \"needs review\" is not \"wrong\".", "",
             "| Task | Arm | " + " | ".join(h for h, _ in _MD_COLUMNS) + " |",
             "|---|---|" + "---|" * len(_MD_COLUMNS)]
    for t in payload["tasks"]:
        for arm in ("skilled", "bare"):
            s = t["summary"][arm]
            cells = [col(s) if callable(col) else str(s.get(col, 0)) for _, col in _MD_COLUMNS]
            lines.append(f"| {t['id']} | {arm} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


# --- Evidence review export --------------------------------------------------------------
def evidence_review_rows(payload: dict, tasks_by_id: dict[str, dict],
                         only_tasks: list[str] | None = None) -> list[dict]:
    """One row per answered item (every arm and run) for a human or model evidence review.

    ``review`` is left empty for the reviewer. Missing items have no evidence and are skipped;
    unresolved conflicts are included with every answer given.
    """
    rows = []
    for t in payload.get("tasks", []):
        if only_tasks and t["id"] not in only_tasks:
            continue
        task = tasks_by_id.get(t["id"], {})
        defs = {(c["id"], i["id"]): i for c in task.get("cases", []) for i in c["items"]}
        for c in t["cases"]:
            for arm in c["arms"]:
                for rec in arm["items"]:
                    if rec["result"] == "missing":
                        continue
                    item = defs.get((c["id"], rec["id"]), {})
                    rows.append({
                        "scoring_schema_version": SCORING_SCHEMA_VERSION,
                        "task": t["id"], "case": c["id"], "arm": arm["arm"], "run": arm["run"],
                        "item": rec["id"], "question": item.get("question"),
                        "expected": rec["expected"], "got": rec["got"],
                        "label_result": rec["result"], "answers": rec.get("answers"),
                        "evidence": rec.get("evidence"),
                        "evidence_status": rec.get("evidence_status"),
                        "deterministic_checks": rec.get("evidence_checks"),
                        "anchor": item.get("anchor"),
                        "review": {"verdict": None, "reviewer": None, "note": None}})
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                    encoding="utf-8")


def _export_from_results(results: Path, out: Path, tasks_by_id: dict[str, dict],
                         only_tasks: list[str] | None) -> int:
    try:
        payload = json.loads(results.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read results file {results}: {exc}", file=sys.stderr)
        return 64
    if not isinstance(payload, dict) or payload.get("kind") != "benchmark":
        print(f"{results} is not a benchmark results file.", file=sys.stderr)
        return 64
    if payload.get("scoring_schema_version") != SCORING_SCHEMA_VERSION:
        print(f"{results} uses scoring schema {payload.get('scoring_schema_version', 1)} "
              "(label-only); it holds no evidence to review. Re-run the benchmark.",
              file=sys.stderr)
        return 64
    rows = evidence_review_rows(payload, tasks_by_id, only_tasks)
    write_jsonl(out, rows)
    print(f"evidence review: {len(rows)} row(s) -> {out} (no model calls were made)")
    return 0


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
    ap.add_argument("--export-evidence-review", metavar="PATH",
                    help="also write a JSONL file with every answered item's evidence, "
                         "deterministic checks and anchor, for a human or model reviewer")
    ap.add_argument("--from-results", metavar="JSON",
                    help="with --export-evidence-review: build the review file from a saved "
                         "scoring-schema-2 results file instead of running anything")
    args = ap.parse_args(argv)
    if args.from_results and not args.export_evidence_review:
        ap.error("--from-results needs --export-evidence-review")

    files = task_files()
    errors = [e for f in files for e in validate_task(f)]
    if errors:
        print("Invalid benchmark task file(s):\n  " + "\n  ".join(errors), file=sys.stderr)
        return 64
    tasks = [(f.parent, json.loads(f.read_text(encoding="utf-8"))) for f in files]
    tasks_by_id = {t["id"]: t for _, t in tasks}
    if args.from_results:
        return _export_from_results(Path(args.from_results), Path(args.export_evidence_review),
                                    tasks_by_id, args.task)
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
                          f"missing={tl['missing']} conflicts={tl['unresolved_conflict']} "
                          f"unknown_ids={tl['unknown_ids']}; evidence: "
                          f"region={tl['evidence_quote_in_item_region']} "
                          f"fixture={tl['evidence_quote_in_fixture']} "
                          f"review={tl['evidence_needs_review']} "
                          f"none={tl['evidence_missing']} "
                          f"({(res['duration_ms'] or 0) / 1000:.0f}s)"
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
            s["label_accuracy"] = round(s["correct"] / s["items"], 4) if s.get("items") else None
            summary[arm] = s
        task_payloads.append({"id": task["id"], "title": task["title"],
                              "skill_dir": task["skill_dir"],
                              "scoring_schema_version": SCORING_SCHEMA_VERSION,
                              "label_semantics": task["label_semantics"],
                              "evidence_checks": evidence_config(task),
                              "summary": summary, "cases": case_payloads})

    usable = sum(s == "answered" for s in arm_statuses)
    status = ("blocked" if usable == 0 else
              "measured" if usable == len(arm_statuses) else "partial")
    payload = {**meta, "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "status": status,
               "scoring_schema_version": SCORING_SCHEMA_VERSION,
               "scoring_note": "Schema 2: labels/numbers scored deterministically; a repeated "
                               "item id with different answers is an unresolved conflict "
                               "(never correct); evidence is kept per item and checked "
                               "deterministically (quote_in_fixture, quote_in_item_region), "
                               "reported separately from label accuracy. Schema-1 results "
                               "(label-only, first duplicate wins) are not directly "
                               "comparable.",
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
    if args.export_evidence_review:
        rows = evidence_review_rows(payload, tasks_by_id)
        write_jsonl(Path(args.export_evidence_review), rows)
        print(f"evidence review: {len(rows)} row(s) -> {args.export_evidence_review}")
    if path:
        print(f"results: {path.relative_to(REPO) if path.is_relative_to(REPO) else path}")
    if status != "measured":
        print(f"{status.upper()}: {len(arm_statuses) - usable} of {len(arm_statuses)} arm runs "
              "returned no parseable answer; their items count as missing.", file=sys.stderr)
    return {"measured": 0, "partial": 3, "blocked": 2}[status]


if __name__ == "__main__":
    raise SystemExit(main())
