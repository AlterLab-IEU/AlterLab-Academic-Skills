#!/usr/bin/env python3
"""score_docentlik.py — Score a publication list against the ÜAK doçentlik gate.

Given a publication list (JSON), this computes whether a candidate meets the
Turkish associate-professorship (doçentlik) point thresholds set by ÜAK
(Üniversitelerarası Kurul / the Inter-University Council). It applies the
per-field point table, the author-share rule (paylaşım kuralı), and pass-fail
checks every mandatory minimum, returning an ELIGIBLE / NOT_ELIGIBLE verdict
with the exact shortfall on each failed check.

Design constraints:
- PURE STDLIB. No network, no third-party deps — fully reproducible offline.
- NO FABRICATION. Ships only the verified Sağlık Bilimleri (Health Sciences)
  TABLO 10 table (see ../references/uak_criteria.md). For any other field the
  caller must supply that field's table; the script never invents point values.
  An unknown index tier is flagged as unscored, never guessed.
- ÜAK criteria change each application term. Every report carries a
  verify-against-current-period disclaimer.

Author-share rule (paylaşım kuralı):
  1 author            -> 1.0  x face points
  2 authors, lead      -> 0.8  x face points (başlıca yazar)
  2 authors, non-lead  -> 0.5  x face points
  >=3, lead author    -> 0.5  x face points
  >=3, non-lead        -> (0.5 / (N - 1)) x face points

Mandatory minimums (all must pass):
  total points        >= 100   (all scored work)
  post-doctorate pts  >=  90   (items with post_doc == true)
  lead-author Q arts  >=   3   (Q1-Q4 articles where the candidate is lead)

Usage:
  uv run python score_docentlik.py INPUT [--field saglik]
                                         [--table TABLE.json]
                                         [--out report.json]
  uv run python score_docentlik.py - < publications.json   # read stdin

INPUT is a JSON object:
  {"field": "saglik", "publications": [
     {"title": "...", "index": "Q1", "authors": 3, "is_lead": true, "post_doc": true}
  ]}

Exit codes: 0 = ran (see JSON summary.verdict); 2 = bad input/usage.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

# --------------------------------------------------------------------------- #
# Bundled, dated criteria. Sağlık Bilimleri (Health Sciences) TABLO 10 only.    #
# Mirror of ../references/uak_criteria.md. Verify against the live ÜAK source   #
# (https://www.uak.gov.tr/) before relying on any verdict.                      #
# --------------------------------------------------------------------------- #

VERSION = "1.0.0"
TABLE_LAST_VERIFIED = "2026-06-06"

# Index tiers that count as quartile-ranked "Q articles" for the lead-author min.
# Sağlık: Q1-Q4 all qualify (Q4 included) — verified against the live ÜAK Sağlık
# criteria ("SCIE/SSCI kapsamındaki dergilerden (Q1, Q2, Q3 veya Q4) ... en az 3
# makalede başlıca yazar"). The live rule additionally requires >=40 points from
# SCIE/SSCI articles, which this scorer does NOT enforce — see ../references.
Q_TIERS = ("Q1", "Q2", "Q3", "Q4")

# field -> {index tier -> face points}
FIELD_TABLES: dict[str, dict[str, int]] = {
    "saglik": {
        "Q1": 30,
        "Q2": 20,
        "Q3": 15,
        "Q4": 10,
        "AHCI": 20,
        "ESCI": 10,
        "TRDizin": 10,
    },
}

# Mandatory minimums (all must pass).
MIN_TOTAL = 100
MIN_POST_DOC = 90
MIN_LEAD_Q = 3

DISCLAIMER = (
    "ÜAK doçentlik criteria change each application term and differ per field — "
    "verify against the current period for your field at https://www.uak.gov.tr/ "
    "before relying on this verdict. This is an objective points pre-check, not "
    "the official doçentlik decision."
)


# --------------------------------------------------------------------------- #
# Scoring                                                                       #
# --------------------------------------------------------------------------- #

def share_factor(authors: int, is_lead: bool) -> float:
    """Author-share factor (paylaşım kuralı) for one publication.

    1 author              -> 1.0
    2 authors, lead       -> 0.8   (başlıca yazar)
    2 authors, non-lead   -> 0.5
    >=3, lead             -> 0.5
    >=3, non-lead         -> 0.5 / (authors - 1)
    """
    if authors <= 1:
        return 1.0
    if authors == 2:
        # Başlıca yazar of a 2-author paper gets 0.8; the other author gets 0.5.
        return 0.8 if is_lead else 0.5
    # authors >= 3
    if is_lead:
        return 0.5
    return 0.5 / (authors - 1)


def score_publication(pub: dict, table: dict[str, int]) -> dict:
    """Score one publication; flag it unscorable if its index tier is unknown."""
    title = str(pub.get("title", "")).strip() or "(untitled)"
    index = str(pub.get("index", "")).strip()
    try:
        authors = int(pub.get("authors", 1))
    except (TypeError, ValueError):
        authors = 1
    if authors < 1:
        authors = 1
    is_lead = bool(pub.get("is_lead", False))
    post_doc = bool(pub.get("post_doc", False))

    if index not in table:
        return {
            "title": title,
            "index": index or "(unknown)",
            "authors": authors,
            "is_lead": is_lead,
            "post_doc": post_doc,
            "scorable": False,
            "face_points": None,
            "share_factor": None,
            "scaled": 0.0,
            "counts_lead_q": False,
            "note": "unknown index tier — resolve and re-run (do not guess)",
        }

    face = table[index]
    factor = share_factor(authors, is_lead)
    scaled = face * factor
    counts_lead_q = is_lead and index in Q_TIERS
    return {
        "title": title,
        "index": index,
        "authors": authors,
        "is_lead": is_lead,
        "post_doc": post_doc,
        "scorable": True,
        "face_points": face,
        "share_factor": round(factor, 4),
        "scaled": scaled,
        "counts_lead_q": counts_lead_q,
    }


def _check(value: float, threshold: float) -> dict:
    passed = value >= threshold
    out = {"pass": passed, "value": round(value, 1), "threshold": threshold}
    if not passed:
        out["short"] = round(threshold - value, 1)
    return out


def score(data: dict, table: dict[str, int], field: str) -> dict:
    pubs = data.get("publications", [])
    if not isinstance(pubs, list):
        raise ValueError("'publications' must be a list")

    scored = [score_publication(p, table) for p in pubs]

    total = sum(p["scaled"] for p in scored)
    post_doc_total = sum(p["scaled"] for p in scored if p["post_doc"])
    lead_q = sum(1 for p in scored if p["counts_lead_q"])
    unscored = [p["title"] for p in scored if not p["scorable"]]

    checks = {
        "total_ge_100": _check(total, MIN_TOTAL),
        "post_doc_ge_90": _check(post_doc_total, MIN_POST_DOC),
        "lead_q_articles_ge_3": _check(lead_q, MIN_LEAD_Q),
    }
    verdict = "ELIGIBLE" if all(c["pass"] for c in checks.values()) else "NOT_ELIGIBLE"

    return {
        "tool": "alterlab-docentlik-eligibility/score_docentlik.py",
        "version": VERSION,
        "field": field,
        "table_last_verified": TABLE_LAST_VERIFIED,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": {
            "verdict": verdict,
            "total_points": round(total, 1),
            "post_doc_points": round(post_doc_total, 1),
            "lead_q_articles": lead_q,
            "unscored_count": len(unscored),
            "checks": checks,
        },
        "unscored": unscored,
        "publications": [
            {**p, "scaled": round(p["scaled"], 2)} for p in scored
        ],
        "disclaimer": DISCLAIMER,
    }


# --------------------------------------------------------------------------- #
# I/O                                                                           #
# --------------------------------------------------------------------------- #

def load_input(arg: str) -> dict:
    if arg == "-":
        raw = sys.stdin.read()
    else:
        try:
            with open(arg, "r", encoding="utf-8") as fh:
                raw = fh.read()
        except OSError:
            # Treat the argument itself as inline JSON.
            raw = arg
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"input is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("input JSON must be an object with a 'publications' list")
    return data


def resolve_table(field: str, table_path: str | None) -> dict[str, int]:
    if table_path:
        with open(table_path, "r", encoding="utf-8") as fh:
            table = json.load(fh)
        if not isinstance(table, dict) or not all(
            isinstance(v, (int, float)) for v in table.values()
        ):
            raise ValueError("--table must be a JSON object of {index_tier: points}")
        return {str(k): int(v) for k, v in table.items()}
    if field not in FIELD_TABLES:
        raise ValueError(
            f"no bundled table for field '{field}'. Only '"
            + "', '".join(FIELD_TABLES)
            + "' is shipped (verified). Supply this field's table with --table "
            "from the live ÜAK source — values are NOT invented."
        )
    return FIELD_TABLES[field]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Score a publication list against the ÜAK doçentlik gate."
    )
    parser.add_argument("input", help="JSON file, '-' for stdin, or inline JSON")
    parser.add_argument(
        "--field",
        default="saglik",
        help="ÜAK field selector (default: saglik — the only bundled table)",
    )
    parser.add_argument(
        "--table",
        default=None,
        help="path to a {index_tier: points} JSON table for a non-bundled field",
    )
    parser.add_argument("--out", default=None, help="write report JSON to this path")
    args = parser.parse_args(argv)

    try:
        data = load_input(args.input)
        field = str(data.get("field", args.field)).strip() or args.field
        table = resolve_table(field, args.table)
        report = score(data, table, field)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(payload + "\n")
        print(f"wrote {args.out} — verdict: {report['summary']['verdict']}")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
