#!/usr/bin/env python3
"""check_site.py - pre-publication checks for a static project website (stdlib only, keyless).

    python scripts/check_site.py site/            # checks site/index.html and every *.html under it
    uv run --python ">=3.11" --with weasyprint --with pymupdf python scripts/check_site.py site/ \
        --preview site_preview.png                # also renders an approximate screen preview

Errors (exit 1): a local link, image or stylesheet that does not exist; an <img> without alt
text; an unreplaced template placeholder ({{...}}); a missing <title> or viewport meta tag.
Warnings: headings that skip a level, images over 1 MB, more than one <h1>. External URLs are
listed (not fetched) so they can be checked with lychee or WebFetch before the site goes live.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs: list[tuple[str, str]] = []  # (tag, url)
        self.imgs_without_alt = 0
        self.headings: list[int] = []
        self.title = False
        self.viewport = False
        self.ids: set[str] = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "a" and a.get("href"):
            self.refs.append(("a", a["href"]))
        elif tag in ("img", "script", "source") and a.get("src"):
            self.refs.append((tag, a["src"]))
            if tag == "img" and not (a.get("alt") or "").strip():
                self.imgs_without_alt += 1
        elif tag == "link" and a.get("href"):
            self.refs.append(("link", a["href"]))
        elif tag == "meta" and a.get("name") == "viewport":
            self.viewport = True
        elif tag == "title":
            self.title = True
        elif re.fullmatch(r"h[1-6]", tag):
            self.headings.append(int(tag[1]))


def check(path: Path, root: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    p = Page()
    p.feed(text)
    errors, warnings, external = [], [], []
    rel = str(path.relative_to(root))
    for tag, url in p.refs:
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https"):
            external.append(url)
            continue
        if parsed.scheme in ("mailto", "tel", "data") or url.startswith("#"):
            if url.startswith("#") and len(url) > 1 and url[1:] not in p.ids:
                errors.append(f"{rel}: in-page link {url} has no matching id")
            continue
        target = (path.parent / unquote(parsed.path)).resolve()
        if parsed.path and not target.exists():
            errors.append(f"{rel}: {tag} -> {url} does not exist")
        elif tag == "img" and target.is_file() and target.stat().st_size > 1_000_000:
            warnings.append(f"{rel}: {url} is {target.stat().st_size // 1024} KB (compress it)")
    if p.imgs_without_alt:
        errors.append(f"{rel}: {p.imgs_without_alt} <img> without alt text")
    placeholders = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", text)))
    if placeholders:
        errors.append(f"{rel}: unreplaced placeholders {placeholders[:6]}")
    if not p.title:
        errors.append(f"{rel}: no <title>")
    if not p.viewport:
        errors.append(f"{rel}: no viewport meta tag (breaks on phones)")
    if p.headings.count(1) != 1:
        warnings.append(f"{rel}: {p.headings.count(1)} <h1> elements (use exactly one)")
    for a, b in zip(p.headings, p.headings[1:]):
        if b > a + 1:
            warnings.append(f"{rel}: heading jumps from h{a} to h{b}")
            break
    return {"errors": errors, "warnings": warnings, "external": external}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("site", type=Path, help="site folder (or a single .html file)")
    ap.add_argument("--preview", type=Path,
                    help="render the first page to this PNG (needs weasyprint + pymupdf; an "
                         "approximation of a browser, good enough to Read and judge the layout)")
    args = ap.parse_args(argv)
    root = args.site if args.site.is_dir() else args.site.parent
    pages = sorted(root.rglob("*.html")) if args.site.is_dir() else [args.site]
    if not pages:
        print(f"error: no .html files under {args.site}", file=sys.stderr)
        return 2
    report = {"pages": [str(p.relative_to(root)) for p in pages], "errors": [], "warnings": [],
              "external_links": []}
    for page in pages:
        r = check(page, root)
        report["errors"] += r["errors"]
        report["warnings"] += r["warnings"]
        report["external_links"] += [u for u in r["external"] if u not in report["external_links"]]
    if args.preview:
        report["preview"] = preview(pages[0], args.preview)
    print(json.dumps(report, indent=2))
    return 1 if report["errors"] else 0


def preview(page: Path, out: Path) -> str:
    try:
        import pymupdf
        import weasyprint
    except ImportError:
        return "skipped: run with `uv run --with weasyprint --with pymupdf` (weasyprint needs Pango)"
    pdf = out.with_suffix(".pdf")
    css = weasyprint.CSS(string="@page { size: 1280px 2400px; margin: 0 }")
    weasyprint.HTML(str(page), media_type="screen").write_pdf(str(pdf), stylesheets=[css])
    doc = pymupdf.open(str(pdf))
    doc[0].get_pixmap(dpi=48).save(str(out))
    return f"{out} (first 2400 px of {doc.page_count} screen-height page(s); full render {pdf})"


if __name__ == "__main__":
    sys.exit(main())
