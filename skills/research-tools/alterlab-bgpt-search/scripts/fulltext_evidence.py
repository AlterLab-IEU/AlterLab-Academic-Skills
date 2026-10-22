#!/usr/bin/env python3
"""Keyless full-text evidence retrieval: open-access studies from Europe PMC / PubMed Central.

The keyless path of alterlab-bgpt-search. This script does the deterministic part — find
open-access studies whose full text Europe PMC serves, download the JATS XML, and turn each
paper into a compact Markdown file (metadata, abstract, every body section, tables as pipe
tables, figure captions; reference list dropped). Claude then reads those files and fills the
structured evidence record (methods, N, effect sizes, risk of bias, limitations, provenance)
that BGPT would return. No API key, no third-party packages.

  python fulltext_evidence.py search "mindfulness anxiety" --design rct --since 2018 --n 10
  python fulltext_evidence.py fetch PMC10123456 10.1002/hsr2.73154 34567890 --out evidence/
  python fulltext_evidence.py evidence "statin primary prevention" --design rct --n 5 --out evidence/

Identifiers for fetch may be PMCIDs, DOIs or PMIDs; DOIs and PMIDs are resolved through Europe
PMC. A paper with no open full text is reported (exit 1 if none could be fetched) — use its
abstract only with a label saying so, or ask the user for the PDF (alterlab-pdf-extract).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"
USER_AGENT = "alterlab-bgpt-search/1.2 (https://github.com/AlterLab-IEU)"
TIMEOUT = 60
DESIGNS = {
    "rct": '(PUB_TYPE:"randomized controlled trial" OR PUB_TYPE:"clinical trial")',
    "meta": '(PUB_TYPE:"meta-analysis" OR PUB_TYPE:"systematic review")',
    "any": "",
}
SORTS = {"relevance": "", "cited": "CITED desc", "date": "P_PDATE_D desc"}
# The evidence record Claude fills from each Markdown file (BGPT-style fields).
EVIDENCE_FIELDS = [
    "pmcid", "doi", "first_author_year", "title", "journal", "study_design", "setting_country",
    "population", "n_randomised_or_enrolled", "n_analysed", "intervention", "comparator",
    "primary_outcome", "outcome_measure_instrument", "follow_up", "effect_estimate",
    "effect_ci_95", "p_value", "secondary_outcomes", "adverse_events", "risk_of_bias_tool",
    "risk_of_bias_judgement", "funding", "conflicts_of_interest", "limitations_stated",
    "authors_conclusion", "provenance_quotes",
]


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def search(query: str, n: int = 10, design: str = "any", since: Optional[int] = None,
           sort: str = "relevance") -> List[Dict]:
    """Open-access, full-text-available studies matching `query` in title/abstract."""
    parts = [f"TITLE_ABS:({query})", "OPEN_ACCESS:y", "IN_EPMC:y"]
    if DESIGNS.get(design):
        parts.append(DESIGNS[design])
    if since:
        parts.append(f"PUB_YEAR:[{since} TO 3000]")
    qs = urllib.parse.urlencode({"query": " AND ".join(parts), "format": "json",
                                 "pageSize": max(1, min(n, 100)), "resultType": "lite",
                                 **({"sort": SORTS[sort]} if SORTS.get(sort) else {})})
    res = json.loads(_get(f"{EPMC}/search?{qs}"))
    return [{"pmcid": r.get("pmcid", ""), "doi": r.get("doi", ""), "pmid": r.get("pmid", ""),
             "year": r.get("pubYear", ""), "journal": r.get("journalTitle", ""),
             "cited_by": r.get("citedByCount", 0), "title": r.get("title", ""),
             "pub_type": r.get("pubType", "")}
            for r in res.get("resultList", {}).get("result", []) if r.get("pmcid")]


def resolve(identifier: str) -> Optional[str]:
    """PMCID for a PMCID / DOI / PMID, or None when Europe PMC has no full-text record."""
    s = identifier.strip()
    if re.fullmatch(r"PMC\d+", s, re.I):
        return s.upper()
    s = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", s, flags=re.I)
    q = f'DOI:"{s}"' if s.startswith("10.") else (f"EXT_ID:{s} AND SRC:MED" if s.isdigit() else "")
    if not q:
        return None
    qs = urllib.parse.urlencode({"query": q, "format": "json", "resultType": "lite"})
    hits = json.loads(_get(f"{EPMC}/search?{qs}")).get("resultList", {}).get("result", [])
    return next((h["pmcid"] for h in hits if h.get("pmcid")), None)


def _text(el: Optional[ET.Element]) -> str:
    return " ".join("".join(el.itertext()).split()) if el is not None else ""


def _table_md(tw: ET.Element) -> List[str]:
    out = [f"**{_text(tw.find('label'))} {_text(tw.find('caption'))}**".replace("** ", "**")]
    for table in tw.iter("table"):
        rows = [[_text(c).replace("|", "\\|") for c in tr if c.tag in ("td", "th")]
                for tr in table.iter("tr")]
        rows = [r for r in rows if any(r)]
        if not rows:
            continue
        width = max(len(r) for r in rows)
        rows = [r + [""] * (width - len(r)) for r in rows]
        out.append("| " + " | ".join(rows[0]) + " |")
        out.append("|" + " --- |" * width)
        out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    foot = _text(tw.find("table-wrap-foot"))
    if foot:
        out.append(f"_Table note: {foot}_")
    return out + [""]


def _section_md(sec: ET.Element, depth: int) -> List[str]:
    out: List[str] = []
    title = _text(sec.find("title"))
    if title:
        out += [f"{'#' * min(depth, 6)} {title}", ""]
    for child in sec:
        if child.tag == "p":
            # Tables and figures can sit inside a paragraph; render them separately.
            inner = [c for c in child if c.tag in ("table-wrap", "fig")]
            for c in inner:
                child.remove(c)
            if _text(child):
                out += [_text(child), ""]
            for c in inner:
                out += _table_md(c) if c.tag == "table-wrap" else [
                    f"_{_text(c.find('label')) or 'Figure'}: {_text(c.find('caption'))}_", ""]
        elif child.tag == "sec":
            out += _section_md(child, depth + 1)
        elif child.tag == "table-wrap":
            out += _table_md(child)
        elif child.tag == "fig":
            out += [f"_{_text(child.find('label')) or 'Figure'}: {_text(child.find('caption'))}_", ""]
        elif child.tag == "list":
            out += [f"- {_text(li)}" for li in child.iter("list-item")] + [""]
        elif child.tag in ("disp-quote", "boxed-text", "statement"):
            out += [f"> {_text(child)}", ""]
    return out


def jats_to_markdown(xml: bytes, pmcid: str) -> str:
    root = ET.fromstring(xml)
    meta = root.find(".//article-meta")
    ids = {a.get("pub-id-type"): (a.text or "").strip() for a in root.iter("article-id")}
    year = next((_text(d.find("year")) for d in root.iter("pub-date") if d.find("year") is not None), "")
    authors = [f"{_text(c.find('name/surname'))} {_text(c.find('name/given-names'))[:1]}".strip()
               for c in (meta.iter("contrib") if meta is not None else []) if c.get("contrib-type") == "author"]
    lic = root.find(".//permissions/license")
    lines = [f"# {_text(root.find('.//title-group/article-title'))}", "",
             f"- Authors: {', '.join(a for a in authors[:6] if a)}{' et al.' if len(authors) > 6 else ''}",
             f"- Journal: {_text(root.find('.//journal-title'))} ({year})",
             f"- DOI: {ids.get('doi', '')} | PMCID: {pmcid} | PMID: {ids.get('pmid', '')}",
             f"- Licence: {(lic.get('{http://www.w3.org/1999/xlink}href', '') or _text(lic))[:160] if lic is not None else 'not stated'}",
             f"- Source: {EPMC}/{pmcid}/fullTextXML (Europe PMC open-access full text)", ""]
    for ab in root.iter("abstract"):
        if ab.get("abstract-type") in (None, "", "summary"):
            lines += ["## Abstract", ""]
            sub = ab.findall("sec")
            lines += ([f"**{_text(s.find('title'))}** {_text(s).replace(_text(s.find('title')), '', 1).strip()}"
                       for s in sub] if sub else [_text(ab)]) + [""]
            break
    body = root.find("body")
    for sec in (list(body) if body is not None else []):
        if sec.tag == "sec":
            lines += _section_md(sec, 2)
        elif sec.tag == "p":
            lines += [_text(sec), ""]
    back = root.find("back")
    for sec in (back.iter("sec") if back is not None else []):
        t = _text(sec.find("title")).lower()
        if any(k in t for k in ("fund", "conflict", "competing", "declaration", "availability")):
            lines += _section_md(sec, 2)
    for fn in root.iter("fn-group"):
        lines += [f"_Footnote: {_text(fn)}_", ""]
    return "\n".join(lines).rstrip() + "\n"


def fetch(identifiers: List[str], out_dir: Path) -> List[Dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    report = []
    for ident in identifiers:
        rec = {"id": ident, "pmcid": None, "file": None, "error": None}
        try:
            rec["pmcid"] = resolve(ident)
            if not rec["pmcid"]:
                rec["error"] = "no PubMed Central record (no open full text in Europe PMC)"
            else:
                md = jats_to_markdown(_get(f"{EPMC}/{rec['pmcid']}/fullTextXML"), rec["pmcid"])
                path = out_dir / f"{rec['pmcid']}.md"
                path.write_text(md, encoding="utf-8")
                rec["file"], rec["chars"] = str(path), len(md)
        except urllib.error.HTTPError as exc:
            rec["error"] = ("full text not open-access in Europe PMC (HTTP 404)" if exc.code == 404
                            else f"HTTP {exc.code}")
        except (urllib.error.URLError, OSError, ET.ParseError) as exc:
            rec["error"] = str(exc)[:200]
        report.append(rec)
        print(f"{ident}: " + (f"wrote {rec['file']} ({rec['chars']:,} chars)" if rec["file"]
                              else f"SKIPPED - {rec['error']}"), file=sys.stderr)
    return report


def write_template(out_dir: Path, report: List[Dict]) -> Path:
    path = out_dir / "evidence_table.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=EVIDENCE_FIELDS)
        w.writeheader()
        for r in report:
            if r["file"]:
                w.writerow({"pmcid": r["pmcid"]})
    return path


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Keyless open-access full text from Europe PMC, "
                                 "as Markdown for structured evidence extraction.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search", help="list open-access full-text studies")
    s.add_argument("query")
    s.add_argument("--n", type=int, default=10)
    s.add_argument("--design", choices=sorted(DESIGNS), default="any")
    s.add_argument("--since", type=int, help="earliest publication year")
    s.add_argument("--sort", choices=sorted(SORTS), default="relevance")
    s.add_argument("--json", action="store_true")
    f = sub.add_parser("fetch", help="download full text (PMCID, DOI or PMID) as Markdown")
    f.add_argument("ids", nargs="+")
    f.add_argument("--out", type=Path, default=Path("evidence"))
    e = sub.add_parser("evidence", help="search, fetch the top N, write evidence_table.csv")
    e.add_argument("query")
    e.add_argument("--n", type=int, default=5)
    e.add_argument("--design", choices=sorted(DESIGNS), default="any")
    e.add_argument("--since", type=int)
    e.add_argument("--sort", choices=sorted(SORTS), default="relevance")
    e.add_argument("--out", type=Path, default=Path("evidence"))
    args = ap.parse_args(argv)
    try:
        if args.cmd == "search":
            hits = search(args.query, args.n, args.design, args.since, args.sort)
            if args.json:
                print(json.dumps(hits, indent=2, ensure_ascii=False))
            for h in [] if args.json else hits:
                print(f"{h['pmcid']}\t{h['year']}\tcited {h['cited_by']}\t{h['doi'] or '-'}\t"
                      f"{h['title'][:110]}")
            return 0 if hits else 1
        ids = args.ids if args.cmd == "fetch" else [
            h["pmcid"] for h in search(args.query, args.n, args.design, args.since, args.sort)]
        if not ids:
            print("no open-access full-text studies matched; broaden the query", file=sys.stderr)
            return 1
        report = fetch(ids, args.out)
        if args.cmd == "evidence":
            print(f"evidence template: {write_template(args.out, report)}", file=sys.stderr)
        print(json.dumps(report, indent=2))
        return 0 if any(r["file"] for r in report) else 1
    except (urllib.error.URLError, OSError) as exc:
        print(f"error: Europe PMC unreachable ({exc})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
