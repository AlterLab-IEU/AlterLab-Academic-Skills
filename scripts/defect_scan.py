#!/usr/bin/env python3
"""Find eval and environment defects in behavioral results — no model, no judge.

Reads ``run_evals.py --behavioral`` (or ``--collect-only``) results files and flags, per case
and arm, the problems that do not depend on which model answered:

  input_missing     the answer says the input the prompt refers to never arrived
  tool_denied       the CLI denied one or more tool calls (permission_denials > 0)
  install_blocked   the answer tried to install a package and was stopped
  script_error      a traceback, ModuleNotFoundError or missing bundled file in the answer
  network_blocked   a host was unreachable, reset the connection, or needed approval
  no_answer         the call timed out, failed, was refused, or was not run

These are the failures a fix to the eval or the environment removes (a fixture, an
allowed-tools entry, a `uv run --with` recipe, a `requires` tag); they say nothing about
whether a skill's answer is good. Usage:

    uv run python scripts/defect_scan.py eval-results/sweep183            # a directory
    uv run python scripts/defect_scan.py results.json --json defects.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

PATTERNS = {
    "input_missing": re.compile(
        r"didn'?t come through|did not come through|nothing (?:was |is )?(?:attached|shared|"
        r"provided)|no (?:file|attachment|data(?:set)?|draft|manuscript) (?:was |is )?(?:attached|"
        r"provided|included|here)|`?fixtures/?`? (?:folder |directory )?is empty|"
        r"(?:don'?t|do not) (?:have|see) (?:your|the) (?:draft|data|list|file|abstract|"
        r"references|publication|materials|dataset|studies|cases|reviews?|manuscript|cv|"
        r"proposal|paper|repo(?:sitory)?|docs|sequences?|structure|results)|haven'?t (?:received|"
        r"got) (?:your|the|any)|doesn'?t (?:actually )?include the|wasn'?t included|"
        r"bana ulaşmadı|ekli değil|dosya (?:yok|eklenmemiş)|paylaşmadınız", re.I),
    "install_blocked": re.compile(
        r"(?:pip|uv pip|conda|npm|apt(?:-get)?|install)[^.\n]{0,80}(?:needs?|requires?|"
        r"requested) (?:your )?(?:approval|permission)|install(?:ing|ation)?[^.\n]{0,60}"
        r"(?:was )?(?:denied|declined|blocked|not (?:allowed|permitted|approved))|"
        r"couldn'?t install|could not install|isn'?t installed (?:here|in this environment)",
        re.I),
    "script_error": re.compile(
        r"Traceback \(most recent call last\)|ModuleNotFoundError|ImportError: |"
        r"No such file or directory: '(?:\./)?(?:skill/)?scripts/|command not found|"
        r"SyntaxError: |exited with (?:code|status) [1-9]", re.I),
    "network_blocked": re.compile(
        r"connection (?:reset|refused)|could not resolve|name resolution|network (?:access |"
        r"call |request )?(?:approval|is (?:not )?(?:approved|available))|needs? network "
        r"approval|not reachable|unreachable|timed out connecting|ECONNREFUSED|SSL: |"
        r"blocked by (?:the )?(?:proxy|sandbox|network policy)", re.I),
}
CATEGORIES = [*PATTERNS, "tool_denied", "no_answer"]


def scan_run(run: dict) -> list[str]:
    """Defect categories for one arm run."""
    if run.get("call_outcome") != "answer":
        return ["no_answer"]
    text = (run.get("response") or run.get("response_excerpt") or "")[:6000]
    found = [name for name, pat in PATTERNS.items() if pat.search(text)]
    if (run.get("permission_denials") or 0) > 0:
        found.append("tool_denied")
    return found


def scan_file(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for case in data.get("cases", []):
        for arm in ("skilled", "bare"):
            a = case.get(arm) or {}
            runs = a.get("runs") or []
            cats = sorted({c for r in runs for c in scan_run(r)} or
                          ({"no_answer"} if a.get("outcome") in ("NOT_RUN", "INFRA_ERROR",
                                                                  "REFUSED") else set()))
            if cats:
                denied = sorted({t for r in runs for t in (r.get("denied_tools") or [])})
                rows.append({"skill": case.get("skill"), "eval_id": case.get("eval_id"),
                             "arm": arm, "outcome": a.get("outcome"), "defects": cats,
                             "denied_tools": denied,
                             "reason": (a.get("reason") or "")[:160], "file": path.name})
    return rows


def main(argv: list[str] | None = None) -> int:
    if hasattr(__import__("signal"), "SIGPIPE"):  # quiet when piped to head
        __import__("signal").signal(__import__("signal").SIGPIPE, __import__("signal").SIG_DFL)
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("paths", nargs="+", help="results JSON files or directories of them")
    ap.add_argument("--json", metavar="OUT", help="also write every finding to this file")
    args = ap.parse_args(argv)
    files: list[Path] = []
    for p in map(Path, args.paths):
        files += sorted(p.glob("behavioral-*.json")) if p.is_dir() else [p]
    if not files:
        print("no results files found", file=sys.stderr)
        return 2
    rows = [r for f in files for r in scan_file(f)]
    by_cat = Counter(c for r in rows for c in r["defects"])
    cases = {(r["skill"], r["eval_id"]) for r in rows}
    print(f"{len(files)} results file(s); {len(cases)} case(s) with at least one defect")
    for cat in CATEGORIES:
        print(f"  {cat:16} {by_cat.get(cat, 0):4} arm(s)")
    print()
    for r in sorted(rows, key=lambda r: (r["skill"] or "", str(r["eval_id"]), r["arm"])):
        print(f"{r['skill']:38} {str(r['eval_id'])[:40]:40} {r['arm']:7} "
              f"{r['outcome'] or '-':12} {','.join(r['defects'])}"
              + (f"  [{'; '.join(r['denied_tools'])[:150]}]" if r["denied_tools"] else ""))
    if args.json:
        Path(args.json).write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n",
                                   encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
