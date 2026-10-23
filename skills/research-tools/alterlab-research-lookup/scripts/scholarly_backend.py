#!/usr/bin/env python3
"""Keyless scholarly backend for research_lookup.py: index records, not a synthesis.

Searches five open scholarly indexes that need no API key and merges the hits by DOI:

  - Crossref          api.crossref.org/works       every discipline; is-referenced-by-count
  - Europe PMC        ebi.ac.uk/europepmc REST     life sciences + preprints; abstracts
  - arXiv             export.arxiv.org/api/query   physics, CS, maths, q-bio preprints
  - Semantic Scholar  api.semanticscholar.org      every discipline, strong on CS venues;
                                                   keyless pool 429s under load (one retry)
  - OpenAlex          api.openalex.org/works       every discipline; skipped with a note when
                                                   the shared per-IP keyless budget is spent

A source that fails is listed under "did not answer"; the others still return.

Each record keeps its title, first authors, year, venue, DOI, URL, the citation count each
index reports, and (Europe PMC / arXiv) an abstract snippet. Claude reads the records, opens
the papers it will cite, and writes the synthesis; this module never generates prose.

Stdlib only. Run directly for a quick check:

    python scholarly_backend.py "testing effect retrieval practice classroom" --limit 5
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from typing import Any, Callable, Dict, List, Optional

USER_AGENT = "alterlab-research-lookup/1.2 (https://github.com/AlterLab-IEU)"
TIMEOUT = 30
SOURCES = ("crossref", "europepmc", "arxiv", "semanticscholar", "openalex")

# Words that steer routing or describe the wanted output, not the topic. Dropped before the
# query reaches the indexes, whose relevance ranking treats every word as a search term.
_FILLER = set("""
a an and are as at be by can could do does for from get give how i in is it me my of on or
our please show so some that the their them these this to us want we what which with would
find search look lookup papers paper articles article studies study published publications
literature research peer reviewed peer-reviewed journal journals scholarly academic sources
source cite citation citations citing doi dois count counts pubmed pmid arxiv preprint
preprints list recent latest current seminal foundational landmark influential highly cited
most key major review reviews systematic meta analysis meta-analysis also include including
need route backend best whatever save sources folder lit intro introduction background section
chapter thesis dissertation manuscript draft overview list references bibliography give
provide help using about regarding related relevant good solid important top main up
""".split())


def search_terms(query: str) -> str:
    """Reduce a natural-language request to its topic words ("find papers on X" -> "X")."""
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-+.]*", query)
    kept = [w for w in words if w.lower().strip(".") not in _FILLER]
    return " ".join(kept) or query


def _http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def _doi(value: Optional[str]) -> str:
    if not value:
        return ""
    v = value.strip()
    v = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", v, flags=re.I)
    return v.lower()


def _record(**kw: Any) -> Dict[str, Any]:
    rec = {"title": "", "authors": [], "year": None, "venue": "", "doi": "", "url": "",
           "cited_by": {}, "abstract": "", "found_in": []}
    rec.update(kw)
    return rec


def crossref(terms: str, n: int, get: Callable[[str], bytes], rank: str = "relevance") -> List[Dict[str, Any]]:
    qs = urllib.parse.urlencode({
        "query.bibliographic": terms, "rows": n,
        "filter": "type:journal-article,type:proceedings-article,type:posted-content,type:book-chapter",
        "select": "DOI,title,author,issued,container-title,is-referenced-by-count,type,URL",
    })
    items = json.loads(get(f"https://api.crossref.org/works?{qs}"))["message"]["items"]
    out = []
    for it in items:
        year = ((it.get("issued") or {}).get("date-parts") or [[None]])[0][0]
        authors = [f"{a.get('family', '')}, {a.get('given', '')[:1]}.".strip(", .")
                   for a in it.get("author", [])[:3] if a.get("family")]
        out.append(_record(
            title=" ".join((it.get("title") or [""])[0].split()), authors=authors, year=year,
            venue=(it.get("container-title") or [""])[0], doi=_doi(it.get("DOI")),
            url=it.get("URL", ""), cited_by={"crossref": it.get("is-referenced-by-count", 0)},
            found_in=["crossref"]))
    return out


def europepmc(terms: str, n: int, get: Callable[[str], bytes], rank: str = "relevance") -> List[Dict[str, Any]]:
    # TITLE_ABS keeps full-text-only mentions out (a bare query also matches body text,
    # so PRISMA and similar method papers flood a citation-sorted list).
    params = {"query": f"TITLE_ABS:({terms})", "format": "json", "pageSize": n,
              "resultType": "core"}
    if rank == "cited":
        params["sort"] = "CITED desc"
    qs = urllib.parse.urlencode(params)
    res = json.loads(get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?{qs}"))
    out = []
    for it in res.get("resultList", {}).get("result", []):
        authors = [a.get("fullName", "") for a in (it.get("authorList") or {}).get("author", [])[:3]]
        src, ext = it.get("source", ""), it.get("id", "")
        abstract = re.sub(r"<[^>]+>", "", it.get("abstractText", "") or "")
        out.append(_record(
            title=re.sub(r"<[^>]+>", "", it.get("title", "")).strip(), authors=authors,
            year=int(it["pubYear"]) if str(it.get("pubYear", "")).isdigit() else None,
            venue=(it.get("journalInfo") or {}).get("journal", {}).get("title", "")
            or it.get("bookOrReportDetails", {}).get("publisher", ""),
            doi=_doi(it.get("doi")), url=f"https://europepmc.org/article/{src}/{ext}",
            cited_by={"europepmc": it.get("citedByCount", 0)}, abstract=abstract[:600],
            found_in=["europepmc"], pmid=it.get("pmid", ""), pmcid=it.get("pmcid", "")))
    return out


def arxiv(terms: str, n: int, get: Callable[[str], bytes], rank: str = "relevance") -> List[Dict[str, Any]]:
    words = [w for w in re.findall(r"[A-Za-z0-9\-]+", terms)
             if len(w) > 1 and w not in ("AND", "OR", "NOT")][:8]
    if not words:
        return []
    q = " AND ".join(f"all:{w}" for w in words)
    qs = urllib.parse.urlencode({"search_query": q, "max_results": n})
    root = ET.fromstring(get(f"https://export.arxiv.org/api/query?{qs}"))
    ns = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
    out = []
    for e in root.findall("a:entry", ns):
        arx = (e.findtext("a:id", "", ns) or "").rsplit("/abs/", 1)[-1]
        arx_base = re.sub(r"v\d+$", "", arx)
        doi = e.findtext("x:doi", "", ns) or (f"10.48550/arxiv.{arx_base}" if arx_base else "")
        out.append(_record(
            title=" ".join((e.findtext("a:title", "", ns) or "").split()),
            authors=[a.findtext("a:name", "", ns) for a in e.findall("a:author", ns)[:3]],
            year=int((e.findtext("a:published", "", ns) or "0000")[:4]) or None,
            venue=e.findtext("x:journal_ref", "", ns) or "arXiv preprint", doi=_doi(doi),
            url=f"https://arxiv.org/abs/{arx_base}",
            abstract=" ".join((e.findtext("a:summary", "", ns) or "").split())[:600],
            found_in=["arxiv"]))
    return out


def openalex(terms: str, n: int, get: Callable[[str], bytes], rank: str = "relevance") -> List[Dict[str, Any]]:
    qs = urllib.parse.urlencode({
        "search": terms, "per_page": n,
        "select": "id,doi,title,publication_year,cited_by_count,primary_location,authorships"})
    res = json.loads(get(f"https://api.openalex.org/works?{qs}"))
    out = []
    for w in res.get("results", []):
        loc = (w.get("primary_location") or {}).get("source") or {}
        out.append(_record(
            title=w.get("title") or "", year=w.get("publication_year"),
            authors=[(a.get("author") or {}).get("display_name", "")
                     for a in (w.get("authorships") or [])[:3]],
            venue=loc.get("display_name", ""), doi=_doi(w.get("doi")), url=w.get("id", ""),
            cited_by={"openalex": w.get("cited_by_count", 0)}, found_in=["openalex"]))
    return out


def semanticscholar(terms: str, n: int, get: Callable[[str], bytes], rank: str = "relevance") -> List[Dict[str, Any]]:
    qs = urllib.parse.urlencode({
        "query": terms.replace('"', ""), "limit": min(n, 100),
        "fields": "title,year,venue,externalIds,citationCount,authors,url"})
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?{qs}"
    try:
        res = json.loads(get(url))
    except urllib.error.HTTPError as exc:
        if exc.code != 429:
            raise
        time.sleep(2)  # the keyless pool is shared; one polite retry
        res = json.loads(get(url))
    out = []
    for p in res.get("data") or []:
        ext = p.get("externalIds") or {}
        doi = ext.get("DOI") or (f"10.48550/arxiv.{ext['ArXiv']}" if ext.get("ArXiv") else "")
        out.append(_record(
            title=p.get("title") or "", year=p.get("year"), venue=p.get("venue") or "",
            authors=[a.get("name", "") for a in (p.get("authors") or [])[:3]], doi=_doi(doi),
            url=p.get("url") or "", cited_by={"semanticscholar": p.get("citationCount") or 0},
            found_in=["semanticscholar"]))
    return out


SEARCHERS = {"crossref": crossref, "europepmc": europepmc, "arxiv": arxiv,
             "semanticscholar": semanticscholar, "openalex": openalex}


def _key(rec: Dict[str, Any]) -> str:
    return rec["doi"] or re.sub(r"[^a-z0-9]", "", rec["title"].lower())[:80]


def impact_label(year: Optional[int], cites: int, today: Optional[int] = None) -> str:
    """The working heuristic from SKILL.md 'Citation-Based Ranking' (not an established cut-off)."""
    if not year:
        return ""
    age = (today or date.today().year) - year
    if age <= 3:
        return "Highly Influential" if cites >= 100 else ("Noteworthy" if cites >= 20 else "")
    if age <= 7:
        return "Landmark Paper" if cites >= 500 else ("Significant" if cites >= 100 else "")
    return "Foundational" if cites >= 1000 else ("Seminal Work" if cites >= 500 else "")


_RECENT = re.compile(r"\b(recent|latest|newest|new|current|emerging|this year|last year|"
                     r"past (?:few|\d+|two|three|five) (?:months|years)|20[2-3]\d)\b", re.I)


def search(query: str, limit: int = 10, sources: Optional[List[str]] = None,
           terms: Optional[str] = None, rank: str = "auto",
           get: Callable[[str], bytes] = _http_get) -> Dict[str, Any]:
    """Query each source, merge by DOI (else normalised title), then order the records.

    rank="relevance" keeps each index's own relevance order (best rank across indexes);
    rank="cited" draws a larger pool (3x limit, max 50 per index; Europe PMC sorted by
    citations within title/abstract matches) and orders it by the highest citation count any
    index reports, which is how influential work surfaces (the SKILL's quality rule);
    rank="auto" uses "relevance" when the request asks for recent / latest / dated work (new
    papers have few citations yet) and "cited" otherwise.
    """
    terms = terms or search_terms(query)
    if rank == "auto":
        rank = "relevance" if _RECENT.search(query) else "cited"
    pool = min(50, limit * 3) if rank == "cited" else limit
    merged: Dict[str, Dict[str, Any]] = {}
    best_rank: Dict[str, int] = {}
    errors: Dict[str, str] = {}
    for name in sources or SOURCES:
        try:
            hits = SEARCHERS[name](terms, pool, get, rank)
        except urllib.error.HTTPError as exc:
            why = ("" if exc.code != 429 else " (keyless daily budget spent)"
                   if name == "openalex" else " (keyless pool rate-limited; retry later)")
            errors[name] = f"HTTP {exc.code}{why}"
            continue
        except (urllib.error.URLError, OSError, ValueError, KeyError, ET.ParseError) as exc:
            errors[name] = str(exc)[:200]
            continue
        for pos, rec in enumerate(hits):
            if not rec["title"]:
                continue
            k = _key(rec)
            if k in merged:
                m = merged[k]
                m["cited_by"].update(rec["cited_by"])
                m["found_in"] += [s for s in rec["found_in"] if s not in m["found_in"]]
                for field in ("abstract", "venue", "doi", "pmid", "pmcid"):
                    if rec.get(field) and not m.get(field):
                        m[field] = rec[field]
            else:
                merged[k] = rec
            best_rank[k] = min(best_rank.get(k, pos), pos)
    def cites(r: Dict[str, Any]) -> int:
        return max(r["cited_by"].values() or [0])

    if rank == "cited":
        records = sorted(merged.values(), key=lambda r: (-cites(r), best_rank[_key(r)]))
    else:
        records = sorted(merged.values(), key=lambda r: (best_rank[_key(r)], -len(r["found_in"])))
    for r in records:
        r["impact"] = impact_label(r["year"], cites(r))
    return {"terms": terms, "rank": rank, "records": records[:limit], "errors": errors,
            "queried": list(sources or SOURCES), "searched": date.today().isoformat()}


def to_markdown(res: Dict[str, Any]) -> str:
    lines = [f"Keyless scholarly backend — searched {res['searched']} for \"{res['terms']}\" "
             f"in {', '.join(s for s in res.get('queried', SOURCES) if s not in res['errors']) or 'no source'}"
             f" (order: {res.get('rank', 'relevance')}).",
             "These are index records, not a synthesis: open each paper before citing a finding "
             "from it. Citation counts differ by index; each is labelled with its source.", ""]
    for i, r in enumerate(res["records"], 1):
        who = "; ".join(a for a in r["authors"] if a) + (" et al." if len(r["authors"]) >= 3 else "")
        cites = " · ".join(f"{v:,} ({k})" for k, v in r["cited_by"].items())
        bits = [f"{i}. **{r['title']}** — {who or 'authors n/a'} ({r['year'] or 'n.d.'})."]
        if r["venue"]:
            bits.append(f"*{r['venue']}*.")
        if r["doi"]:
            bits.append(f"DOI: {r['doi']}")
        lines.append(" ".join(bits))
        meta = [f"cited {cites}" if cites else "", r.get("impact", ""), "found in: " +
                ", ".join(r["found_in"])]
        lines.append("   " + " — ".join(m for m in meta if m))
        lines.append(f"   {r['url'] or ('https://doi.org/' + r['doi'] if r['doi'] else '')}")
        if r["abstract"]:
            lines.append(f"   Abstract: {r['abstract'][:300]}{'…' if len(r['abstract']) > 300 else ''}")
    if res["errors"]:
        lines += ["", "Sources that did not answer: " +
                  "; ".join(f"{k}: {v}" for k, v in res["errors"].items())]
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Keyless scholarly search (Crossref, Europe PMC, "
                                 "arXiv, OpenAlex), merged by DOI.")
    ap.add_argument("query", help="topic or request; routing words are dropped")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--sources", default=",".join(SOURCES),
                    help=f"comma list from {','.join(SOURCES)}")
    ap.add_argument("--rank", choices=["auto", "relevance", "cited"], default="auto",
                    help="auto (default): 'relevance' for recent/latest/dated requests, else 'cited'")
    ap.add_argument("--terms", help="exact search terms (skips the routing-word filter)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    res = search(args.query, args.limit, [s for s in args.sources.split(",") if s in SEARCHERS],
                 terms=args.terms, rank=args.rank)
    print(json.dumps(res, indent=2, ensure_ascii=False) if args.json else to_markdown(res))
    return 0 if res["records"] else 1


if __name__ == "__main__":
    sys.exit(main())
