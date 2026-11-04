#!/usr/bin/env python3
"""Summarise a LabArchives notebook export offline — no account, no network.

`labapi`'s ``notebook.export(dest)`` writes a folder mirror of a notebook: one
directory per folder/page (named ``<order>_<name>``) holding ordered files
``NN_text.html`` (rich text), ``NN_text.txt`` (plain text) and ``NN_<filename>``
(attachments). This walks that tree — or any manual export in the same shape — and
reports structure and gaps a reviewer cares about, with no credentials:

  * pages (directories that directly hold NN_* files) and their depth
  * text entries vs attachment entries, and total words of text
  * pages that carry attachments but no text entry (a provenance gap: raw data with
    no note saying what it is)
  * attachment file types

Use it to audit an export before archiving, or to triage a backup you were handed.

  python3 analyze_export.py path/to/export_dir      # exit 0; 2 on a bad path
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ENTRY_RE = re.compile(r"^(\d+)_(.+)$")


class _Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def _words(html_or_text: str, is_html: bool) -> int:
    if is_html:
        p = _Text()
        p.feed(html_or_text)
        text = " ".join(p.parts)
    else:
        text = html_or_text
    return len(text.split())


def analyze(root: Path) -> dict:
    pages = 0
    text_entries = attachment_entries = total_words = 0
    gap_pages: list[str] = []
    attachment_types: Counter[str] = Counter()
    for d in sorted(p for p in root.rglob("*") if p.is_dir()):
        entries = [f for f in sorted(d.iterdir()) if f.is_file() and ENTRY_RE.match(f.name)]
        if not entries:
            continue
        pages += 1
        has_text = False
        has_attachment = False
        for f in entries:
            name = ENTRY_RE.match(f.name).group(2)
            if name in ("text.html", "text.txt"):
                has_text = True
                text_entries += 1
                total_words += _words(f.read_text(encoding="utf-8", errors="replace"),
                                       name.endswith(".html"))
            else:
                has_attachment = True
                attachment_entries += 1
                attachment_types[f.suffix.lower() or "(none)"] += 1
        if has_attachment and not has_text:
            gap_pages.append(str(d.relative_to(root)))
    return {
        "pages": pages, "text_entries": text_entries,
        "attachment_entries": attachment_entries, "total_words": total_words,
        "gap_pages": gap_pages, "attachment_types": dict(attachment_types),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("export_dir", type=Path, help="a labapi export (or same-shape) directory")
    args = ap.parse_args()
    if not args.export_dir.is_dir():
        print(f"error: {args.export_dir} is not a directory", file=sys.stderr)
        return 2
    r = analyze(args.export_dir)
    print(f"pages: {r['pages']}")
    print(f"text entries: {r['text_entries']} ({r['total_words']} words)")
    print(f"attachment entries: {r['attachment_entries']} {r['attachment_types']}")
    if r["gap_pages"]:
        print(f"PROVENANCE GAP — attachments with no text entry ({len(r['gap_pages'])}):")
        for p in r["gap_pages"]:
            print(f"  - {p}")
    else:
        print("no provenance gaps (every page with an attachment also has a text entry)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
