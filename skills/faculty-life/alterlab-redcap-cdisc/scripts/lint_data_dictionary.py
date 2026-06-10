#!/usr/bin/env python3
"""Lint a REDCap data dictionary CSV for structural errors before import.

This is a *structural* linter: it validates the importable 18-column data
dictionary format (column header, field-name syntax, legal field types and
validation, choice-string presence, expression references, duplicate names,
unflagged identifiers). It does NOT contact a REDCap server — a clean lint still
needs a real test import to confirm instance-specific behavior.

Stdlib only (csv, re, json, argparse). No network. No REDCap account.

Usage:
    uv run python lint_data_dictionary.py data_dictionary.csv
    uv run python lint_data_dictionary.py data_dictionary.csv --json
    cat dd.csv | uv run python lint_data_dictionary.py -

Exit code 0 when no errors are found, 1 when at least one error is found, 2 on a
usage/parse failure (file unreadable, no header row).

Column header / field-type / validation values per the REDCap data-dictionary
import format (Vanderbilt University REDCap; see references/redcap_design.md).
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from dataclasses import dataclass, field

# The 18 data-dictionary columns, in order. REDCap accepts minor punctuation
# variants in the header (e.g. "Field Note" vs "Field Notes"); we match on a
# normalized key, so the canonical labels below are for reporting only.
CANONICAL_COLUMNS = [
    "Variable / Field Name",
    "Form Name",
    "Section Header",
    "Field Type",
    "Field Label",
    "Choices, Calculations, OR Slider Labels",
    "Field Note",
    "Text Validation Type OR Show Slider Number",
    "Text Validation Min",
    "Text Validation Max",
    "Identifier?",
    "Branching Logic (Show field only if...)",
    "Required Field?",
    "Custom Alignment",
    "Question Number (surveys only)",
    "Matrix Group Name",
    "Matrix Ranking?",
    "Field Annotation",
]

# Legal Field Type machine values.
FIELD_TYPES = {
    "text", "notes", "dropdown", "radio", "checkbox", "calc", "sql",
    "descriptive", "slider", "yesno", "truefalse", "file",
}
# Field types whose Choices/Calc column (6) must be non-empty.
NEEDS_CHOICES = {"radio", "dropdown", "checkbox", "calc", "slider"}
# Field types that store data (used for the identifier heuristic).
DATA_FIELDS = FIELD_TYPES - {"descriptive"}

# Legal Text Validation Type machine values (column 8), plus slider display.
VALIDATION_TYPES = {
    "date_ymd", "date_mdy", "datetime_ymd", "time",
    "integer", "number", "email", "phone", "zipcode",
}

# Variable / Field Name: lowercase letters, digits, underscore; not digit-first.
FIELD_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")

# Heuristic PII field-name fragments — a data field matching these with a blank
# Identifier? is flagged as an ERROR (an unflagged identifier leaks into
# "de-identified" exports).
PII_HINTS = (
    "name", "mrn", "ssn", "email", "phone", "address", "addr", "dob",
    "birth", "fax", "zip", "postal", "ip_address",
)

# Reference fields like [other_var] inside branching logic / calc expressions.
VAR_REF_RE = re.compile(r"\[([a-z][a-z0-9_]*)(?:\([^)]*\))?\]")


def _norm(s: str) -> str:
    """Normalize a header cell for tolerant matching."""
    return re.sub(r"[^a-z0-9]+", "", (s or "").strip().lower())


CANONICAL_NORM = [_norm(c) for c in CANONICAL_COLUMNS]


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rows_checked: int = 0
    header_ok: bool = False

    def as_dict(self) -> dict:
        return {
            "tool": "alterlab-redcap-cdisc/lint_data_dictionary.py",
            "version": "1.0.0",
            "summary": {
                "rows_checked": self.rows_checked,
                "header_ok": self.header_ok,
                "errors": len(self.errors),
                "warnings": len(self.warnings),
                "verdict": "FAIL" if self.errors else "PASS",
            },
            "errors": self.errors,
            "warnings": self.warnings,
            "note": "Structural lint only — a clean result still requires a "
                    "REDCap test import to confirm instance-specific behavior.",
        }


def read_csv(path: str) -> list[list[str]]:
    if path == "-":
        text = sys.stdin.read()
    else:
        with open(path, "r", encoding="utf-8-sig", newline="") as fh:
            text = fh.read()
    return list(csv.reader(io.StringIO(text)))


def lint(rows: list[list[str]]) -> Report:
    rep = Report()
    if not rows:
        rep.errors.append("empty file: no header row found")
        return rep

    header = rows[0]
    hnorm = [_norm(c) for c in header]
    if len(header) < 18:
        rep.errors.append(
            f"header has {len(header)} columns; expected 18 "
            f"(missing: {', '.join(CANONICAL_COLUMNS[len(header):]) or 'none'})"
        )
    # Check the first 18 column labels against the canonical set, in order.
    for i, want in enumerate(CANONICAL_NORM):
        got = hnorm[i] if i < len(hnorm) else None
        if got != want:
            rep.errors.append(
                f"column {i + 1}: header is {header[i] if i < len(header) else '<missing>'!r}, "
                f"expected {CANONICAL_COLUMNS[i]!r}"
            )
    rep.header_ok = not rep.errors

    seen: dict[str, int] = {}
    declared: set[str] = set()
    # First pass: collect all declared variable names for reference checks.
    for r in rows[1:]:
        if r and r[0].strip():
            declared.add(r[0].strip())

    for idx, r in enumerate(rows[1:], start=2):  # 1-based, +1 for header
        if not any(cell.strip() for cell in r):
            continue  # blank line
        rep.rows_checked += 1
        # Pad short rows so indexing is safe.
        cells = (r + [""] * 18)[:18]
        (name, form, _sec, ftype, _label, choices, _note, valid,
         _vmin, _vmax, ident, branching, _req, _align, _qnum,
         _mgrp, _mrank, _annot) = [c.strip() for c in cells]

        loc = f"row {idx} ({name or '<no name>'})"

        # Variable / Field Name
        if not name:
            rep.errors.append(f"{loc}: missing Variable / Field Name")
        elif not FIELD_NAME_RE.match(name):
            rep.errors.append(
                f"{loc}: invalid field name {name!r} "
                "(use lowercase letters/digits/underscore, not digit-first)"
            )
        else:
            if name in seen:
                rep.errors.append(
                    f"{loc}: duplicate field name {name!r} "
                    f"(first seen row {seen[name]})"
                )
            seen[name] = idx

        if not form:
            rep.errors.append(f"{loc}: missing Form Name")

        # Field Type
        ft = ftype.lower()
        if not ft:
            rep.errors.append(f"{loc}: missing Field Type")
        elif ft not in FIELD_TYPES:
            rep.errors.append(
                f"{loc}: unknown Field Type {ftype!r} "
                f"(allowed: {', '.join(sorted(FIELD_TYPES))})"
            )

        # Choices required for choice/calc/slider fields
        if ft in NEEDS_CHOICES and not choices:
            rep.errors.append(
                f"{loc}: field type {ft!r} requires a "
                "'Choices, Calculations, OR Slider Labels' value"
            )

        # Text Validation Type legality (only meaningful for text/slider)
        if valid:
            vt = valid.lower()
            if ft == "slider":
                if vt not in {"na", "number"}:
                    rep.warnings.append(
                        f"{loc}: slider validation {valid!r} should be 'NA' or 'number'"
                    )
            elif vt not in VALIDATION_TYPES:
                rep.errors.append(
                    f"{loc}: unknown Text Validation Type {valid!r} "
                    f"(allowed: {', '.join(sorted(VALIDATION_TYPES))})"
                )
            if vt not in VALIDATION_TYPES and ft not in {"text", "slider"}:
                rep.warnings.append(
                    f"{loc}: validation set on field type {ft!r} (usually only 'text')"
                )

        # Branching-logic / calc references must point to declared variables.
        for expr_name, expr in (("Branching Logic", branching),
                                 ("Calculation", choices if ft == "calc" else "")):
            for ref in VAR_REF_RE.findall(expr or ""):
                if ref not in declared:
                    rep.errors.append(
                        f"{loc}: {expr_name} references unknown variable [{ref}]"
                    )

        # Unflagged identifier heuristic
        if ft in DATA_FIELDS and ident.lower() != "y":
            low = name.lower()
            if any(h in low for h in PII_HINTS):
                rep.errors.append(
                    f"{loc}: field {name!r} looks like PII but Identifier? is not 'y' "
                    "(would leak into de-identified exports)"
                )

    if rep.rows_checked == 0:
        rep.warnings.append("no field rows found below the header")

    return rep


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv_path", help="path to data_dictionary.csv, or '-' for stdin")
    ap.add_argument("--json", action="store_true", help="emit a JSON report")
    args = ap.parse_args(argv)

    try:
        rows = read_csv(args.csv_path)
    except OSError as exc:
        print(f"error: cannot read {args.csv_path}: {exc}", file=sys.stderr)
        return 2

    rep = lint(rows)

    if args.json:
        print(json.dumps(rep.as_dict(), indent=2))
    else:
        verdict = "FAIL" if rep.errors else "PASS"
        print(f"REDCap data-dictionary lint: {verdict} "
              f"({rep.rows_checked} field rows; "
              f"{len(rep.errors)} errors, {len(rep.warnings)} warnings)")
        for e in rep.errors:
            print(f"  ERROR   {e}")
        for w in rep.warnings:
            print(f"  warning {w}")
        if not rep.errors:
            print("  note: structural lint only — confirm with a REDCap test import.")

    return 1 if rep.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
