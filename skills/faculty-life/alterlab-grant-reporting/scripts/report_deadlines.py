#!/usr/bin/env python3
"""report_deadlines.py — Compute post-award report due dates from award dates.

Reporting deadlines for the major funders are deterministic functions of the
award's budget-period / project dates, and missing one can suspend payments. This
helper computes them from the published general rules so the user does not have
to recall them from memory. It does NO network I/O and depends only on the Python
standard library.

The encoded rules (each sourced in ../references/funder_formats.md):

  NIH SNAP      Annual RPPR  15th of the month BEFORE the month in which the
                             current budget period ends (ends 11/30 -> due 10/15)
  NIH non-SNAP  Annual RPPR  1st of the month BEFORE the month in which the
                             current budget period ends (ends 11/30 -> due 10/1)
  NIH MYF       Annual RPPR  on or before each anniversary of the budget/project
                             period start date
  NIH Final / Interim RPPR   within 120 days AFTER the period-of-performance end
  NSF Annual                 90 days BEFORE the budget-period end
  NSF Final report           within 120 days AFTER award end
  NSF Project Outcomes Rpt   within 120 days AFTER award end
  Horizon Europe / ERC       within 60 days AFTER each reporting-period end
  (periodic and final)

NIH moves an annual due date that lands on a weekend or US federal holiday to the
next business day. This script applies the weekend shift only; if the result is
a federal holiday the real deadline is one business day later, so the date shown
is never later than the true one.

IMPORTANT: these are the funders' GENERAL rules. A specific Notice of Award,
cooperative agreement, or Grant Agreement can override them. The output always
restates this — confirm every computed date against the award's own documents.

Usage:
  uv run python report_deadlines.py --funder nih-snap \
      --budget-period-start 2026-09-01 --project-end 2028-08-31
  uv run python report_deadlines.py --funder nih-myf \
      --budget-period-start 2025-09-01 --project-end 2030-08-31 --json
  uv run python report_deadlines.py --funder nsf \
      --budget-period-end 2027-05-31 --project-end 2028-08-31 --json
  uv run python report_deadlines.py --funder eu --period-end 2027-06-30 --json

Exit codes: 0 = computed; 2 = bad/missing arguments.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

FUNDERS = ("nih-snap", "nih-nonsnap", "nih-myf", "nsf", "eu")

DISCLAIMER = (
    "General funder rule only — confirm against the Notice of Award / Grant "
    "Agreement; specific programs can override these defaults."
)


def _parse_date(s: str | None, flag: str) -> date | None:
    if s is None:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        print(f"error: {flag} must be ISO date YYYY-MM-DD, got {s!r}", file=sys.stderr)
        raise SystemExit(2)


def _next_weekday(d: date) -> date:
    """Shift a Saturday/Sunday due date to the following Monday."""
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def _nih_annual_due(budget_period_end: date, day: int) -> date:
    """Day `day` of the month preceding the month in which the budget period ends."""
    first_of_end_month = budget_period_end.replace(day=1)
    prev_month = first_of_end_month - timedelta(days=1)
    return prev_month.replace(day=day)


def _anniversary(start: date, years: int) -> date:
    try:
        return start.replace(year=start.year + years)
    except ValueError:  # 29 Feb start date in a non-leap year
        return start.replace(year=start.year + years, day=28)


@dataclass
class Deadline:
    report: str
    due: date
    rule: str

    def as_dict(self) -> dict:
        return {"report": self.report, "due": self.due.isoformat(), "rule": self.rule}


@dataclass
class Result:
    funder: str
    deadlines: list[Deadline] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _nih_final(res: Result, pend: date | None) -> None:
    if pend is None:
        res.notes.append("Final RPPR needs --project-end.")
        return
    res.deadlines.append(
        Deadline(
            "Final RPPR",
            pend + timedelta(days=120),
            f"within 120 days after period-of-performance end ({pend.isoformat()})",
        )
    )
    res.notes.append(
        "If a Type 2 renewal was submitted, file an Interim RPPR on the same "
        "120-day clock instead; it becomes the Final RPPR if the renewal is not "
        "funded, or the last annual report if it is."
    )


def compute(args: argparse.Namespace) -> Result:
    funder = args.funder
    res = Result(funder=funder)

    bps = _parse_date(args.budget_period_start, "--budget-period-start")
    bpe = _parse_date(args.budget_period_end, "--budget-period-end")
    pend = _parse_date(args.project_end, "--project-end")
    pend_eu = _parse_date(args.period_end, "--period-end")

    if funder in ("nih-snap", "nih-nonsnap"):
        # The current budget period ends the day before the next one starts;
        # --budget-period-end (the current period's end) is accepted as well.
        current_end = bps - timedelta(days=1) if bps is not None else bpe
        if current_end is not None:
            snap = funder == "nih-snap"
            nominal = _nih_annual_due(current_end, 15 if snap else 1)
            due = _next_weekday(nominal)
            rule = (
                f"{'15th' if snap else '1st'} of the month before the month in which "
                f"the budget period ends ({current_end.isoformat()})"
            )
            if due != nominal:
                rule += f"; nominal {nominal.isoformat()} falls on a weekend"
            res.deadlines.append(
                Deadline(f"Annual RPPR ({'SNAP' if snap else 'non-SNAP'})", due, rule)
            )
        else:
            res.notes.append(
                "Annual RPPR needs --budget-period-start (start of the NEXT budget "
                "period) or --budget-period-end (end of the current one)."
            )
        _nih_final(res, pend)
        res.notes.append(
            "A due date on a US federal holiday moves to the next business day; "
            "holidays are not computed here, so the real deadline can be one day later."
        )

    elif funder == "nih-myf":
        if bps is not None:
            if pend is not None:
                years = 1
                while _anniversary(bps, years) < pend:
                    ann = _anniversary(bps, years)
                    res.deadlines.append(
                        Deadline(
                            f"Annual RPPR (MYF) #{years}",
                            ann,
                            f"on or before anniversary {years} of the budget/project "
                            f"period start ({bps.isoformat()}); covers the preceding year",
                        )
                    )
                    years += 1
            else:
                res.deadlines.append(
                    Deadline(
                        "Annual RPPR (MYF) #1",
                        _anniversary(bps, 1),
                        f"on or before the first anniversary of {bps.isoformat()}; "
                        "repeats every anniversary (pass --project-end to list them all)",
                    )
                )
        else:
            res.notes.append(
                "MYF RPPR needs --budget-period-start (the award's budget/project "
                "period start date)."
            )
        _nih_final(res, pend)
        res.notes.append(
            "An MYF award in a no-cost extension generally files no annual RPPR "
            "unless the funding IC requires one."
        )

    elif funder == "nsf":
        if bpe is not None:
            res.deadlines.append(
                Deadline(
                    "Annual project report",
                    bpe - timedelta(days=90),
                    f"90 days before the budget-period end ({bpe.isoformat()})",
                )
            )
        else:
            res.notes.append("Annual project report needs --budget-period-end.")
        if pend is not None:
            res.deadlines.append(
                Deadline(
                    "Final project report",
                    pend + timedelta(days=120),
                    f"within 120 days after award end ({pend.isoformat()})",
                )
            )
            res.deadlines.append(
                Deadline(
                    "Project Outcomes Report",
                    pend + timedelta(days=120),
                    f"within 120 days after award end ({pend.isoformat()}); <=800 words, public",
                )
            )
        else:
            res.notes.append("Final report / Project Outcomes Report need --project-end.")

    elif funder == "eu":
        ref_end = pend_eu or pend
        if ref_end is not None:
            label = "Periodic / final report"
            res.deadlines.append(
                Deadline(
                    label,
                    ref_end + timedelta(days=60),
                    f"within 60 days after the reporting-period end ({ref_end.isoformat()})",
                )
            )
        else:
            res.notes.append(
                "Horizon Europe / ERC report needs --period-end (or --project-end)."
            )
        res.notes.append(
            "ERC runs scientific and periodic (financial) reports on separate "
            "periods (typically after month 24 and month 30 of a 5-year grant); "
            "both are due within 60 days of their own period end and are filed "
            "together for the final period."
        )

    res.notes.append(DISCLAIMER)
    return res


def render_table(res: Result) -> str:
    lines = [f"Funder: {res.funder}", ""]
    if res.deadlines:
        wr = max(len(d.report) for d in res.deadlines)
        lines.append(f"{'Report'.ljust(wr)}  {'Due'.ljust(10)}  Rule")
        lines.append(f"{'-' * wr}  {'-' * 10}  {'-' * 4}")
        for d in res.deadlines:
            lines.append(f"{d.report.ljust(wr)}  {d.due.isoformat()}  {d.rule}")
    else:
        lines.append("(no deadlines computed — see notes)")
    if res.notes:
        lines.append("")
        for n in res.notes:
            lines.append(f"NOTE: {n}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Compute post-award report due dates from award dates (stdlib only, no network)."
    )
    p.add_argument("--funder", required=True, choices=FUNDERS,
                   help="nih-snap | nih-nonsnap | nih-myf | nsf | eu")
    p.add_argument("--budget-period-start", metavar="YYYY-MM-DD",
                   help="NIH SNAP/non-SNAP: start of the NEXT budget period; "
                        "NIH MYF: the award's budget/project period start date")
    p.add_argument("--budget-period-end", metavar="YYYY-MM-DD",
                   help="NSF: end of the current reporting budget period "
                        "(NIH SNAP/non-SNAP: accepted instead of --budget-period-start)")
    p.add_argument("--project-end", metavar="YYYY-MM-DD",
                   help="Award / period-of-performance end date (final reports)")
    p.add_argument("--period-end", metavar="YYYY-MM-DD",
                   help="EU: end of the reporting period (periodic/final report)")
    p.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    res = compute(args)
    if args.json:
        print(json.dumps(
            {
                "funder": res.funder,
                "deadlines": [d.as_dict() for d in res.deadlines],
                "notes": res.notes,
            },
            indent=2,
        ))
    else:
        print(render_table(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
