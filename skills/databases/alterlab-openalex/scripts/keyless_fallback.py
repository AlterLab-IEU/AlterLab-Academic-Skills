#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Keyless fallbacks for when OpenAlex list/search calls hit the shared per-IP budget (429).

OpenAlex single-entity lookups (/works/doi:..., /works/W..., /authors/orcid:...) cost $0 and
keep working; list, filter, search and group_by calls share $0.10/day per IP without a key.
When those return 429, these keyless sources cover the common needs. Every record carries a
"source" field: say which service answered, never present it as OpenAlex output.

  crossref   Crossref REST /works — keyword/bibliographic search with date and type filters,
             sortable by citation count (is-referenced-by-count). Query matching is loose:
             post-filter titles. Optional polite-pool contact: --mailto or $CROSSREF_MAILTO.
  europepmc  Europe PMC REST search — life sciences, sortable by citations (CITED desc).
  citations  OpenCitations Index v2 — DOIs citing a DOI (incoming) or cited by it (--references).
  enrich     Free OpenAlex single-entity lookups for a list of DOIs (OA status, cited_by_count).

    python keyless_fallback.py crossref "quantum computing" --from 2020-01-01 --rows 20
    python keyless_fallback.py europepmc "CRISPR base editing" --rows 10
    python keyless_fallback.py citations 10.7717/peerj.4375 --count-only
    python keyless_fallback.py enrich 10.7717/peerj.4375 10.1038/s41586-021-03819-2
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "AlterLab-Academic-Skills/1.0 (alterlab-openalex keyless fallback)"


def _get(url: str, params: dict | None = None, tries: int = 4):
    if params:
        url = f"{url}?{urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})}"
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            if exc.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            raise SystemExit(f"HTTP {exc.code} from {url.split('?')[0]}")
        except urllib.error.URLError as exc:
            if attempt < tries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            raise SystemExit(f"Cannot reach {url.split('?')[0]}: {exc.reason}")
    return None


def _crossref_items(d: dict) -> list[dict]:
    out = []
    for it in ((d or {}).get("message") or {}).get("items", []):
        parts = ((it.get("published") or {}).get("date-parts") or [[None]])[0]
        out.append({"doi": it.get("DOI"), "title": (it.get("title") or [""])[0],
                    "year": parts[0] if parts else None,
                    "venue": (it.get("container-title") or [""])[0],
                    "first_author": ((it.get("author") or [{}])[0]).get("family"),
                    "citations_crossref": it.get("is-referenced-by-count"), "type": it.get("type"),
                    "source": "Crossref"})
    return out


def crossref(query: str, date_from=None, date_to=None, work_type="journal-article", rows=20,
             sort="is-referenced-by-count", mailto=None, title_filter=True) -> list[dict]:
    """Crossref search. Crossref matches loosely, so with title_filter (default) it pulls a
    citation-ranked pool and a relevance-ranked pool (1,000 + 500 records), keeps works
    whose title contains every query word, merges by DOI and sorts locally. The result is a
    keyless approximation of an OpenAlex "most cited" query, not the same ranking."""
    filters = [f for f in (f"from-pub-date:{date_from}" if date_from else None,
                           f"until-pub-date:{date_to}" if date_to else None,
                           f"type:{work_type}" if work_type else None) if f]
    base = {"query.bibliographic": query, "filter": ",".join(filters) or None,
            "select": "DOI,title,author,published,container-title,is-referenced-by-count,type",
            "mailto": mailto or os.environ.get("CROSSREF_MAILTO")}
    if not title_filter:
        return _crossref_items(_get("https://api.crossref.org/works", {
            **base, "rows": rows, "sort": sort, "order": "desc" if sort else None}))[:rows]
    pools = []
    if sort:
        pools.append(_get("https://api.crossref.org/works",
                          {**base, "rows": 1000, "sort": sort, "order": "desc"}))
    pools.append(_get("https://api.crossref.org/works", {**base, "rows": 500}))
    words = [w.lower() for w in query.split() if len(w) > 2]
    merged: dict = {}
    for pool in pools:
        for o in _crossref_items(pool):
            if all(w in (o["title"] or "").lower() for w in words):
                merged.setdefault((o["doi"] or o["title"]).lower(), o)
    out = list(merged.values())
    if sort == "is-referenced-by-count":
        out.sort(key=lambda o: -(o["citations_crossref"] or 0))
    return out[:rows]


def europepmc(query: str, rows=20, sort="CITED desc") -> list[dict]:
    d = _get("https://www.ebi.ac.uk/europepmc/webservices/rest/search",
             {"query": query, "format": "json", "pageSize": rows, "sort": sort, "resultType": "lite"}) or {}
    return [{"doi": r.get("doi"), "pmid": r.get("pmid"), "title": r.get("title"),
             "year": r.get("pubYear"), "venue": r.get("journalTitle"),
             "first_author": (r.get("authorString") or "").split(",")[0],
             "citations_europepmc": r.get("citedByCount"), "open_access": r.get("isOpenAccess"),
             "source": "Europe PMC"} for r in (d.get("resultList") or {}).get("result", [])]


def citations(doi: str, references: bool = False) -> list[dict]:
    kind = "references" if references else "citations"
    rows = _get(f"https://api.opencitations.net/index/v2/{kind}/doi:{doi}") or []
    side = "cited" if references else "citing"
    out = []
    for r in rows:
        ids = r.get(side, "").split()
        out.append({"doi": next((i[4:] for i in ids if i.startswith("doi:")), None),
                    "openalex": next((i[9:] for i in ids if i.startswith("openalex:")), None),
                    "creation": r.get("creation"), "source": "OpenCitations Index v2"})
    return out


def enrich(dois: list[str]) -> list[dict]:
    out = []
    for doi in dois:
        doi = doi.split("doi.org/")[-1]
        w = _get(f"https://api.openalex.org/works/doi:{doi}",
                 {"select": "id,doi,title,publication_year,cited_by_count,open_access"})
        if w:
            out.append({"doi": doi, "openalex": w.get("id"), "title": w.get("title"),
                        "year": w.get("publication_year"), "cited_by_count": w.get("cited_by_count"),
                        "oa_status": (w.get("open_access") or {}).get("oa_status"),
                        "source": "OpenAlex single-entity lookup (free)"})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Keyless fallbacks for OpenAlex list/search 429s.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    pc = sub.add_parser("crossref")
    pc.add_argument("query")
    pc.add_argument("--from", dest="date_from")
    pc.add_argument("--to", dest="date_to")
    pc.add_argument("--type", default="journal-article", help="'' for any type")
    pc.add_argument("--rows", type=int, default=20)
    pc.add_argument("--sort", default="is-referenced-by-count", help="'' for relevance")
    pc.add_argument("--mailto", help="contact for Crossref's polite pool (e.g. you@example.org)")
    pc.add_argument("--loose", action="store_true", help="skip the every-word title filter")
    pe = sub.add_parser("europepmc")
    pe.add_argument("query")
    pe.add_argument("--rows", type=int, default=20)
    pe.add_argument("--sort", default="CITED desc")
    pt = sub.add_parser("citations")
    pt.add_argument("doi")
    pt.add_argument("--references", action="store_true", help="outgoing references instead")
    pt.add_argument("--count-only", action="store_true")
    pn = sub.add_parser("enrich")
    pn.add_argument("dois", nargs="+")
    a = ap.parse_args()
    if a.cmd == "crossref":
        out = crossref(a.query, a.date_from, a.date_to, a.type or None, a.rows, a.sort or None,
                       a.mailto, not a.loose)
    elif a.cmd == "europepmc":
        out = europepmc(a.query, a.rows, a.sort)
    elif a.cmd == "citations":
        out = citations(a.doi, a.references)
        if a.count_only:
            out = {"doi": a.doi, "direction": "references" if a.references else "citations",
                   "count": len(out), "source": "OpenCitations Index v2"}
    else:
        out = enrich(a.dois)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
