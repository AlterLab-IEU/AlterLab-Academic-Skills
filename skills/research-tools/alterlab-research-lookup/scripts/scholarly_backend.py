#!/usr/bin/env python3
"""Keyless scholarly backend for research_lookup.py: index records, not a synthesis.

Searches four open scholarly indexes that need no API key and merges the hits:

  - Crossref          api.crossref.org/works       every discipline; is-referenced-by-count
  - Europe PMC        ebi.ac.uk/europepmc REST     life sciences + preprints; abstracts
  - arXiv             export.arxiv.org/api/query   physics, CS, maths, q-bio preprints
  - Semantic Scholar  api.semanticscholar.org      every discipline, strong on CS venues;
                                                   BEST EFFORT: its shared keyless search pool
                                                   is often spent (HTTP 429 for minutes), so
                                                   it gets one retry, is then skipped for the
                                                   rest of the run, and is reported as "not
                                                   checked". An optional S2_API_KEY (or
                                                   SEMANTIC_SCHOLAR_API_KEY) raises its limit.

Crossref, Europe PMC and arXiv carry every query on their own, so a refused Semantic
Scholar never empties a search. A source that fails is listed under "did not answer"; the
others still return. A rate-limited source was not checked, which is not the same as "no
results".
(OpenAlex was removed in v1.2.1: its keyless searches now share a small per-IP daily
budget, so dependable use needed an account.)

Query handling (details: references/search_semantics.md):
  - A natural-language request is reduced to its topic words (English routing words such as
    "find papers on" are dropped); words in every script are kept as written (NFC), never
    transliterated or translated.
  - Explicit search syntax -- passed with --terms, or quotes / upper-case AND OR NOT /
    parentheses / a leading '-' inside the request -- is parsed into an expression tree and
    translated per index. An index that cannot express it is skipped (exclusions) or queried
    with an approximate keyword version; each index's translation is reported in
    ``query_translation`` and printed.
  - --since / --until (YYYY or YYYY-MM-DD) go to every index and are re-checked on the
    returned dates. Wording such as "recent" is never turned into a date filter.

Records are merged by DOI, then arXiv id / PMID / PMCID, then full title + year + first
author (``merged_from`` keeps the provenance). The default order is relevance; "cited" orders
by ONE declared index's citation count. Claude reads the records, opens the papers it will
cite, and writes the synthesis; this module never generates prose.

Stdlib only. Run directly for a quick check:

    python scholarly_backend.py "testing effect retrieval practice classroom" --limit 5
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from typing import Any, Callable, Dict, List, Optional, Tuple

USER_AGENT = "alterlab-research-lookup/1.3 (https://github.com/AlterLab-IEU)"
TIMEOUT = 30
SCHEMA_VERSION = 2  # 2: query_translation, skipped, date_filter, notes, merged_from, rank_basis
SOURCES = ("crossref", "europepmc", "arxiv", "semanticscholar")
RANKS = ("relevance", "cited")
CITE_INDEXES = ("crossref", "europepmc", "semanticscholar")
S2_BASE = "https://api.semanticscholar.org/"
# Optional: raises Semantic Scholar's shared keyless rate limit. Sent as a header, never logged.
S2_API_KEY = (os.environ.get("S2_API_KEY") or os.environ.get("SEMANTIC_SCHOLAR_API_KEY") or "").strip()
# Seconds to wait before each retry when a source answers HTTP 429. Semantic Scholar's keyless
# search pool is shared by every unauthenticated caller, sends no Retry-After and is often
# spent for minutes, so it gets one retry; Crossref's public pool allows one request in flight.
BACKOFF = {"semanticscholar": (2.0,), "crossref": (1.0, 2.0)}
# After Semantic Scholar search answers 429 past its retry, skip it for this long (s), so a
# batch of queries is not slowed by a pool that keeps refusing; each skip is reported.
S2_PAUSE = 300.0
_S2_PAUSED_UNTIL = 0.0
# arXiv requires every word of a natural-language query to match, so long requests are cut.
ARXIV_MAX_WORDS = 8
# Open ends of a date window for the indexes that need both bounds.
_EARLIEST = date(1800, 1, 1)


class RateLimited(Exception):
    """A source was skipped because it answered HTTP 429 earlier in this run (not checked)."""


class QuerySyntaxError(ValueError):
    """Explicit search syntax that cannot be parsed (unbalanced quotes or parentheses, ...)."""


# Words that steer routing or describe the wanted output, not the topic. Dropped before a
# natural-language query reaches the indexes, whose relevance ranking treats every word as a
# search term. English only: words in other languages are always kept. Never applied to
# --terms, nor to operands of an explicit operator.
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

# --------------------------------------------------------------------------------------------
# Tokenization (Unicode-preserving)
# --------------------------------------------------------------------------------------------

_JOINERS = "-'’+."  # kept inside a word: öz-yeterlik, O'Brien, C++, U.S.


def _word_char(ch: str) -> bool:
    """Letters, combining marks and digits of every script (Unicode categories L, M, N)."""
    return unicodedata.category(ch)[0] in "LMN"


def _words(text: str) -> List[str]:
    """Split text into words without dropping any script; NFC-composes, never transliterates."""
    out: List[str] = []
    cur: List[str] = []
    for ch in unicodedata.normalize("NFC", text) + " ":
        if _word_char(ch) or (cur and ch in _JOINERS):
            cur.append(ch)
            continue
        word = "".join(cur).rstrip("-'’.")
        if word:
            out.append(word)
        cur = []
    return out


def _is_filler(word: str) -> bool:
    return word.casefold().strip(".") in _FILLER


def _natural_words(query: str) -> List[str]:
    words = _words(query)
    return [w for w in words if not _is_filler(w)] or words


def search_terms(query: str) -> str:
    """Reduce a natural-language request to its topic words ("find papers on X" -> "X")."""
    return " ".join(_natural_words(query)) or query.strip()


# --------------------------------------------------------------------------------------------
# Explicit search syntax: a small expression tree
#   ("term", w) | ("phrase", "w1 w2") | ("and", (n, ...)) | ("or", (n, ...)) | ("not", n)
# Precedence: OR binds tighter than AND (adjacent words are ANDed), as in Google Scholar:
# "exercise depression OR anxiety" = exercise AND (depression OR anxiety). Parentheses group.
# --------------------------------------------------------------------------------------------

Node = Tuple[Any, ...]
_QUOTES = str.maketrans({"“": '"', "”": '"', "„": '"', "‟": '"'})
_SYNTAX = re.compile(r'["“”„‟()]|(?<!\S)(?:AND|OR|NOT)(?!\S)'
                     r'|(?:^|(?<=[\s(]))-(?=[^\W\d_]|["(])')


def has_explicit_syntax(text: str) -> bool:
    """Quotes, parentheses, upper-case AND/OR/NOT, or a leading '-' before a word."""
    return bool(_SYNTAX.search(text))


def _lex(text: str, strict: bool) -> List[Tuple[str, str, int]]:
    text = unicodedata.normalize("NFC", text).translate(_QUOTES)
    toks: List[Tuple[str, str, int]] = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
        elif ch == '"':
            j = text.find('"', i + 1)
            if j < 0:
                raise QuerySyntaxError(f'unbalanced double quote at position {i + 1}: close the '
                                       'phrase with a second "')
            words = _words(text[i + 1:j])
            if not words:
                raise QuerySyntaxError(f'empty phrase "" at position {i + 1}')
            toks.append(("PHRASE", " ".join(words), i))
            i = j + 1
        elif ch in "()":
            toks.append((ch, ch, i))
            i += 1
        elif ch == "-" and i + 1 < n and (text[i + 1] in '"(' or unicodedata.category(text[i + 1])[0] == "L"):
            toks.append(("-", "-", i))
            i += 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in '"()':
                j += 1
            raw = text[i:j]
            if raw in ("AND", "OR", "NOT"):
                toks.append((raw, raw, i))
            elif strict and raw in ("and", "or", "not"):
                raise QuerySyntaxError(
                    f"lowercase '{raw}' at position {i + 1}: write {raw.upper()} in capitals for "
                    f'the operator, or "{raw}" in quotes to search for the word')
            elif strict and raw in ("&&", "||", "!"):
                raise QuerySyntaxError(f"'{raw}' at position {i + 1} is not supported: use AND, "
                                       "OR or NOT")
            else:
                toks.extend(("TERM", w, i) for w in _words(raw))
            i = j
    return toks


class _Parser:
    def __init__(self, toks: List[Tuple[str, str, int]], drop_filler: bool):
        self.toks, self.i, self.drop_filler = toks, 0, drop_filler

    def peek(self) -> Optional[str]:
        return self.toks[self.i][0] if self.i < len(self.toks) else None

    def take(self) -> Tuple[str, str, int]:
        tok = self.toks[self.i]
        self.i += 1
        return tok

    def parse(self) -> Node:
        if not self.toks:
            raise QuerySyntaxError("no search words")
        node = self.and_expr()
        if self.i < len(self.toks):
            kind, val, pos = self.toks[self.i]
            if kind == ")":
                raise QuerySyntaxError(f"unexpected ')' at position {pos + 1}: unbalanced "
                                       "parentheses")
            raise QuerySyntaxError(f"unexpected '{val}' at position {pos + 1}")
        return node

    def and_expr(self) -> Node:
        items: List[List[Any]] = []  # [node, bound to an explicit operator]
        bound_next = False
        while self.peek() not in (None, ")"):
            kind = self.peek()
            if kind in ("AND", "OR"):
                pos = self.take()[2]
                if kind == "OR" or not items or self.peek() in (None, ")", "AND", "OR"):
                    raise QuerySyntaxError(f"{kind} at position {pos + 1} needs a term on both "
                                           "sides")
                items[-1][1] = bound_next = True
            elif kind in ("NOT", "-"):
                pos = self.take()[2]
                if self.peek() in (None, ")", "AND", "OR", "NOT", "-"):
                    raise QuerySyntaxError(f"{kind} at position {pos + 1} needs a term after it")
                operand = self.or_expr() if kind == "NOT" else self.atom()
                if items:
                    items[-1][1] = True
                items.append([("not", operand), True])
                bound_next = False
            else:
                items.append([self.or_expr(), bound_next])
                bound_next = False
        if not items:
            raise QuerySyntaxError("no search words")
        if self.drop_filler:  # routing words joined only by adjacency, never operands
            kept = [it for it in items if it[1] or it[0][0] != "term" or not _is_filler(it[0][1])]
            if any(it[0][0] != "not" for it in kept):
                items = kept
        nodes = tuple(it[0] for it in items)
        return nodes[0] if len(nodes) == 1 else ("and", nodes)

    def or_expr(self) -> Node:
        alts = [self.atom()]
        while self.peek() == "OR":
            pos = self.take()[2]
            if self.peek() in ("NOT", "-"):
                raise QuerySyntaxError(f"an excluded term cannot be an OR alternative (position "
                                       f"{pos + 1}): write 'a NOT b', or '(a OR b) NOT c'")
            if self.peek() in (None, ")", "AND", "OR"):
                raise QuerySyntaxError(f"OR at position {pos + 1} needs a term on both sides")
            alts.append(self.atom())
        return alts[0] if len(alts) == 1 else ("or", tuple(alts))

    def atom(self) -> Node:
        kind, val, pos = self.take()
        if kind == "TERM":
            return ("term", val)
        if kind == "PHRASE":
            return ("phrase", val)
        if kind == "(":
            if self.peek() == ")":
                raise QuerySyntaxError(f"empty parentheses at position {pos + 1}")
            node = self.and_expr()
            if self.peek() != ")":
                raise QuerySyntaxError(f"unbalanced parentheses: '(' at position {pos + 1} is "
                                       "never closed")
            self.take()
            return node
        raise QuerySyntaxError(f"unexpected '{val}' at position {pos + 1}")


def _check_negations(node: Node, parent: str = "top") -> None:
    kind = node[0]
    if kind == "not":
        if parent != "and":
            raise QuerySyntaxError("only excluded terms: NOT / '-' needs something to search "
                                   "for beside it ('a NOT b')" if parent == "top" else
                                   "an excluded term cannot be an OR alternative")
        _check_negations(node[1], "not")
    elif kind in ("and", "or"):
        if kind == "and" and all(c[0] == "not" for c in node[1]):
            raise QuerySyntaxError("only excluded terms: NOT / '-' needs something to search "
                                   "for beside it ('a NOT b')")
        for child in node[1]:
            _check_negations(child, kind)


def parse_query(text: str, strict: bool = True) -> Node:
    """Parse explicit search syntax into an expression tree; raise QuerySyntaxError if malformed.

    strict (--terms): no routing-word removal; lower-case and/or/not are refused as ambiguous.
    Not strict (syntax found inside a request): routing words that are only adjacent to other
    words (not operands of AND/OR/NOT) are dropped.
    """
    tree = _Parser(_lex(text, strict), drop_filler=not strict).parse()
    _check_negations(tree)
    return tree


def _has(node: Node, kind: str) -> bool:
    if node[0] == kind:
        return True
    if node[0] in ("and", "or"):
        return any(_has(c, kind) for c in node[1])
    return node[0] == "not" and _has(node[1], kind)


def _leaves(node: Node) -> List[str]:
    """Positive words in order (phrases split), skipping excluded parts."""
    if node[0] in ("term", "phrase"):
        return node[1].split()
    if node[0] in ("and", "or"):
        return [w for c in node[1] for w in _leaves(c)]
    return []


def _safe(term: str) -> bool:
    return all(_word_char(ch) for ch in term)


def _boolean(node: Node, leaf: Callable[[Node], str], andnot: bool, top: bool = False) -> str:
    """Fully parenthesised boolean string; ``andnot`` uses arXiv's binary ANDNOT."""
    kind = node[0]
    if kind in ("term", "phrase"):
        return leaf(node)
    if kind == "or":
        body = " OR ".join(_boolean(c, leaf, andnot) for c in node[1])
    else:
        pos = [_boolean(c, leaf, andnot) for c in node[1] if c[0] != "not"]
        neg = [_boolean(c[1], leaf, andnot) for c in node[1] if c[0] == "not"]
        if andnot:
            body = " AND ".join(pos)
            if neg:
                body = (f"({body})" if len(pos) > 1 else body) + "".join(f" ANDNOT {n}" for n in neg)
        else:
            body = " AND ".join(pos + [f"NOT {n}" for n in neg])
    return body if top else f"({body})"


def render_query(node: Node) -> str:
    """The expression as the backend understood it (shown as the search terms)."""
    return _boolean(node, lambda n: f'"{n[1]}"' if n[0] == "phrase" else n[1], False, top=True)


def _lucene_leaf(n: Node) -> str:
    return n[1] if n[0] == "term" and _safe(n[1]) else f'"{n[1]}"'


def _arxiv_leaf(n: Node) -> str:
    return f"all:{_lucene_leaf(n)}"


def plan_query(query: str, terms: Optional[str] = None) -> Dict[str, Any]:
    """Decide how the request is searched: natural words, --terms, or syntax in the request."""
    notes: List[str] = []
    tree: Optional[Node] = None
    syntax = "natural"
    if terms is not None:
        tree, syntax = parse_query(terms, strict=True), "terms"
    elif has_explicit_syntax(query):
        try:
            tree, syntax = parse_query(query, strict=False), "query-syntax"
        except QuerySyntaxError as exc:
            notes.append(f"The request contains search-syntax characters but could not be parsed "
                         f"({exc}); it was searched as plain words. Pass --terms to use quotes, "
                         "AND/OR/NOT and parentheses.")
    if tree is None:
        words = _natural_words(query)
        if not words:
            raise QuerySyntaxError("no search words in the request")
        tree = ("term", words[0]) if len(words) == 1 else ("and", tuple(("term", w) for w in words))
    shown = " ".join(_leaves(tree)) if syntax == "natural" else render_query(tree)
    return {"syntax": syntax, "tree": tree, "terms": shown, "notes": notes}


def translate(plan: Dict[str, Any], source: str) -> Dict[str, str]:
    """{"mode": exact|approximate|skipped, "query": what the index receives, "note": why}."""
    tree, natural = plan["tree"], plan["syntax"] == "natural"
    if source == "europepmc":
        return {"mode": "exact", "query": f"TITLE_ABS:({_boolean(tree, _lucene_leaf, False, True)})",
                "note": "boolean query on title and abstract"}
    if source == "arxiv":
        if natural and len(_leaves(tree)) > ARXIV_MAX_WORDS:
            cut = ("and", tuple(("term", w) for w in _leaves(tree)[:ARXIV_MAX_WORDS]))
            return {"mode": "approximate", "query": _boolean(cut, _arxiv_leaf, True, True),
                    "note": f"only the first {ARXIV_MAX_WORDS} words were sent (arXiv requires "
                            "every word to match)"}
        return {"mode": "exact", "query": _boolean(tree, _arxiv_leaf, True, True),
                "note": "arXiv boolean query (AND/OR/ANDNOT, quoted phrases) on all fields"}
    label = "Crossref query.bibliographic" if source == "crossref" else "Semantic Scholar /paper/search"
    if _has(tree, "not"):
        return {"mode": "skipped", "query": "",
                "note": f"{label} has no exclusion operator; searching without the excluded "
                        "term(s) would return the excluded topic, so this index was not queried"}
    query = " ".join(_leaves(tree))
    notes = ["relevance-ranked keywords"]
    if source == "semanticscholar" and "-" in query:
        query = " ".join(query.replace("-", " ").split())
        notes.append("hyphens sent as spaces (its search does not match hyphenated words)")
    if natural or tree[0] == "term":
        return {"mode": "exact", "query": query, "note": "; ".join(notes)}
    lost = []
    if _has(tree, "or"):
        lost.append("OR alternatives sent as plain keywords")
    if _has(tree, "and"):
        lost.append("AND not enforced (a record may match only some words)")
    if _has(tree, "phrase"):
        lost.append("phrase word order not enforced")
    return {"mode": "approximate", "query": query,
            "note": f"{label} has no boolean or phrase search: " + "; ".join(lost + notes[1:])}


# --------------------------------------------------------------------------------------------
# Dates
# --------------------------------------------------------------------------------------------

_DATE = re.compile(r"^(\d{4})(?:-(\d{2})-(\d{2}))?$")


def _parse_date(value: str, end: bool, flag: str) -> date:
    m = _DATE.match(str(value).strip())
    if not m:
        raise ValueError(f"{flag} {value!r}: use YYYY or YYYY-MM-DD")
    year = int(m[1])
    if not m[2]:
        return date(year, 12, 31) if end else date(year, 1, 1)
    try:
        return date(year, int(m[2]), int(m[3]))
    except ValueError as exc:
        raise ValueError(f"{flag} {value!r}: {exc}") from None


def parse_window(since: Optional[str] = None, until: Optional[str] = None) -> Optional[Dict[str, Optional[date]]]:
    """--since / --until as inclusive dates (a bare year covers the whole year); None if unset."""
    if not since and not until:
        return None
    lo = _parse_date(since, False, "--since") if since else None
    hi = _parse_date(until, True, "--until") if until else None
    if lo and hi and lo > hi:
        raise ValueError(f"--since {since} is after --until {until}")
    return {"since": lo, "until": hi}


def _bounds(window: Dict[str, Optional[date]]) -> Tuple[date, date]:
    return window["since"] or _EARLIEST, window["until"] or date.today()


def _date_span(rec: Dict[str, Any]) -> Optional[Tuple[date, date]]:
    """The interval a record's (possibly partial) publication date covers, or None if unknown."""
    parts = re.findall(r"\d+", rec.get("pub_date") or "")[:3] or ([str(rec["year"])] if rec.get("year") else [])
    try:
        y = int(parts[0])
        if len(parts) == 1:
            return date(y, 1, 1), date(y, 12, 31)
        m = int(parts[1])
        if len(parts) == 2:
            nxt = date(y + (m == 12), m % 12 + 1, 1)
            return date(y, m, 1), date.fromordinal(nxt.toordinal() - 1)
        d = date(y, m, int(parts[2]))
        return d, d
    except (IndexError, ValueError):
        return None


def _in_window(rec: Dict[str, Any], window: Dict[str, Optional[date]]) -> Optional[bool]:
    """True/False when the record's date overlaps the window or not; None when it is unknown."""
    span = _date_span(rec)
    if span is None:
        return None
    lo, hi = window["since"], window["until"]
    return (lo is None or span[1] >= lo) and (hi is None or span[0] <= hi)


# --------------------------------------------------------------------------------------------
# Sources
# --------------------------------------------------------------------------------------------

def _http_get(url: str) -> bytes:
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if S2_API_KEY and url.startswith(S2_BASE):
        headers["x-api-key"] = S2_API_KEY
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def _get_with_backoff(get: Callable[[str], bytes], url: str, delays: tuple) -> bytes:
    """``get(url)``, retried after each delay while the source answers HTTP 429."""
    for delay in delays:
        try:
            return get(url)
        except urllib.error.HTTPError as exc:
            if exc.code != 429:
                raise
            time.sleep(delay)
    return get(url)


def _doi(value: Optional[str]) -> str:
    if not value:
        return ""
    v = value.strip()
    v = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", v, flags=re.I)
    return v.lower()


def _arxiv_id(value: Optional[str]) -> str:
    v = re.sub(r"^(arxiv:)", "", (value or "").strip(), flags=re.I)
    return re.sub(r"v\d+$", "", v).lower()


def _record(**kw: Any) -> Dict[str, Any]:
    rec = {"title": "", "authors": [], "year": None, "pub_date": "", "venue": "", "doi": "",
           "url": "", "cited_by": {}, "abstract": "", "found_in": [], "pmid": "", "pmcid": "",
           "arxiv_id": ""}
    rec.update(kw)
    rec["arxiv_id"] = _arxiv_id(rec["arxiv_id"])
    if not rec["arxiv_id"] and rec["doi"].startswith("10.48550/arxiv."):
        rec["arxiv_id"] = rec["doi"].split("arxiv.", 1)[1]
    rec["pmcid"] = (rec["pmcid"] or "").upper()
    return rec


Window = Optional[Dict[str, Optional[date]]]


def crossref(q: str, n: int, get: Callable[[str], bytes], rank: str = "relevance",
             window: Window = None) -> List[Dict[str, Any]]:
    filters = "type:journal-article,type:proceedings-article,type:posted-content,type:book-chapter"
    if window and window["since"]:
        filters += f",from-pub-date:{window['since'].isoformat()}"
    if window and window["until"]:
        filters += f",until-pub-date:{window['until'].isoformat()}"
    qs = urllib.parse.urlencode({
        "query.bibliographic": q, "rows": n, "filter": filters,
        "select": "DOI,title,author,issued,container-title,is-referenced-by-count,type,URL",
    })
    items = json.loads(_get_with_backoff(get, f"https://api.crossref.org/works?{qs}",
                                         BACKOFF["crossref"]))["message"]["items"]
    out = []
    for it in items:
        parts = [p for p in ((it.get("issued") or {}).get("date-parts") or [[None]])[0] if p]
        authors = [f"{a.get('family', '')}, {a.get('given', '')[:1]}.".strip(", .")
                   for a in it.get("author", [])[:3] if a.get("family")]
        out.append(_record(
            title=" ".join((it.get("title") or [""])[0].split()), authors=authors,
            year=parts[0] if parts else None, pub_date="-".join(f"{p:02d}" for p in parts),
            venue=(it.get("container-title") or [""])[0], doi=_doi(it.get("DOI")),
            url=it.get("URL", ""), cited_by={"crossref": it.get("is-referenced-by-count", 0)},
            found_in=["crossref"]))
    return out


def europepmc(q: str, n: int, get: Callable[[str], bytes], rank: str = "relevance",
              window: Window = None) -> List[Dict[str, Any]]:
    # TITLE_ABS keeps full-text-only mentions out (a bare query also matches body text,
    # so PRISMA and similar method papers flood a citation-sorted list).
    if window:
        lo, hi = _bounds(window)
        q = f"{q} AND FIRST_PDATE:[{lo.isoformat()} TO {hi.isoformat()}]"
    params = {"query": q, "format": "json", "pageSize": n, "resultType": "core"}
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
            pub_date=it.get("firstPublicationDate", "") or "",
            venue=(it.get("journalInfo") or {}).get("journal", {}).get("title", "")
            or it.get("bookOrReportDetails", {}).get("publisher", ""),
            doi=_doi(it.get("doi")), url=f"https://europepmc.org/article/{src}/{ext}",
            cited_by={"europepmc": it.get("citedByCount", 0)}, abstract=abstract[:600],
            found_in=["europepmc"], pmid=it.get("pmid", ""), pmcid=it.get("pmcid", "")))
    return out


def arxiv(q: str, n: int, get: Callable[[str], bytes], rank: str = "relevance",
          window: Window = None) -> List[Dict[str, Any]]:
    if window:
        lo, hi = _bounds(window)
        q = f"({q}) AND submittedDate:[{lo:%Y%m%d}0000 TO {hi:%Y%m%d}2359]"
    qs = urllib.parse.urlencode({"search_query": q, "max_results": n})
    root = ET.fromstring(get(f"https://export.arxiv.org/api/query?{qs}"))
    ns = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
    out = []
    for e in root.findall("a:entry", ns):
        arx = (e.findtext("a:id", "", ns) or "").rsplit("/abs/", 1)[-1]
        arx_base = re.sub(r"v\d+$", "", arx)
        doi = e.findtext("x:doi", "", ns) or (f"10.48550/arxiv.{arx_base}" if arx_base else "")
        published = (e.findtext("a:published", "", ns) or "")[:10]
        out.append(_record(
            title=" ".join((e.findtext("a:title", "", ns) or "").split()),
            authors=[a.findtext("a:name", "", ns) for a in e.findall("a:author", ns)[:3]],
            year=int(published[:4]) if published[:4].isdigit() else None, pub_date=published,
            venue=e.findtext("x:journal_ref", "", ns) or "arXiv preprint", doi=_doi(doi),
            url=f"https://arxiv.org/abs/{arx_base}", arxiv_id=arx_base,
            abstract=" ".join((e.findtext("a:summary", "", ns) or "").split())[:600],
            found_in=["arxiv"]))
    return out


def semanticscholar(q: str, n: int, get: Callable[[str], bytes], rank: str = "relevance",
                    window: Window = None) -> List[Dict[str, Any]]:
    params = {"query": q, "limit": min(n, 100),
              "fields": "title,year,publicationDate,venue,externalIds,citationCount,authors,url"}
    if window:  # Semantic Scholar filters by year only; exact dates are re-checked afterwards
        lo = window["since"].year if window["since"] else None
        hi = window["until"].year if window["until"] else None
        params["year"] = str(lo) if lo == hi else f"{lo or ''}-{hi or ''}"
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?{urllib.parse.urlencode(params)}"
    global _S2_PAUSED_UNTIL
    if time.monotonic() < _S2_PAUSED_UNTIL:
        raise RateLimited("skipped: it answered HTTP 429 earlier in this run")
    try:
        res = json.loads(_get_with_backoff(get, url, BACKOFF["semanticscholar"]))
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            _S2_PAUSED_UNTIL = time.monotonic() + S2_PAUSE
        raise
    out = []
    for p in res.get("data") or []:
        ext = p.get("externalIds") or {}
        doi = ext.get("DOI") or (f"10.48550/arxiv.{ext['ArXiv']}" if ext.get("ArXiv") else "")
        pmcid = str(ext.get("PubMedCentral") or "")
        out.append(_record(
            title=p.get("title") or "", year=p.get("year"), pub_date=p.get("publicationDate") or "",
            venue=p.get("venue") or "",
            authors=[a.get("name", "") for a in (p.get("authors") or [])[:3]], doi=_doi(doi),
            url=p.get("url") or "", cited_by={"semanticscholar": p.get("citationCount") or 0},
            found_in=["semanticscholar"], arxiv_id=ext.get("ArXiv") or "",
            pmid=str(ext.get("PubMed") or ""),
            pmcid=(pmcid if pmcid.upper().startswith("PMC") or not pmcid else f"PMC{pmcid}")))
    return out


SEARCHERS = {"crossref": crossref, "europepmc": europepmc, "arxiv": arxiv,
             "semanticscholar": semanticscholar}


# --------------------------------------------------------------------------------------------
# Merging (dedup)
# --------------------------------------------------------------------------------------------

_PROVIDER_IDS = ("arxiv_id", "pmid", "pmcid")


def title_key(title: str) -> str:
    """Full title, NFKC + casefold, punctuation and whitespace collapsed; never truncated."""
    folded = unicodedata.normalize("NFKC", title).casefold()
    return " ".join("".join(ch if _word_char(ch) else " " for ch in folded).split())


def first_author_surname(authors: List[str]) -> str:
    """'Roediger, H.' / 'Karpicke JD' / 'H. Roediger' -> 'roediger' (accents folded for comparison)."""
    name = unicodedata.normalize("NFKC", authors[0] if authors else "").strip()
    if "," in name:
        surname = name.split(",", 1)[0]
    else:
        parts = name.split()
        initials = parts[-1].replace(".", "") if parts else ""
        if len(parts) > 1 and initials.isupper() and len(initials) <= 3:
            surname = " ".join(parts[:-1])  # Europe PMC style: "Karpicke JD"
        else:
            surname = parts[-1] if parts else ""
    folded = unicodedata.normalize("NFKD", surname.casefold())
    return "".join(ch for ch in folded if unicodedata.category(ch)[0] in "LN")


def _same_work_by_title(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    if not (a["year"] and b["year"]) or abs(int(a["year"]) - int(b["year"])) > 1:
        return False
    sa, sb_ = first_author_surname(a["authors"]), first_author_surname(b["authors"])
    return not (sa and sb_) or sa == sb_


def _provenance(rec: Dict[str, Any], how: str) -> Dict[str, str]:
    ident = (f"doi:{rec['doi']}" if rec["doi"] else f"arXiv:{rec['arxiv_id']}" if rec["arxiv_id"]
             else f"PMID:{rec['pmid']}" if rec["pmid"] else f"PMCID:{rec['pmcid']}" if rec["pmcid"]
             else rec["url"])
    return {"source": rec["found_in"][0] if rec["found_in"] else "", "id": ident,
            "title": rec["title"], "matched_on": how}


class _Merger:
    """Clusters records that are the same work; see references/search_semantics.md (Dedup)."""

    def __init__(self) -> None:
        self.records: List[Dict[str, Any]] = []
        self.best: List[int] = []
        self.ids: Dict[Tuple[str, str], int] = {}
        self.titles: Dict[str, List[int]] = {}

    def _register(self, i: int) -> None:
        rec = self.records[i]
        for field in ("doi",) + _PROVIDER_IDS:
            if rec.get(field):
                self.ids.setdefault((field, rec[field]), i)
        key = title_key(rec["title"])
        if key and i not in self.titles.setdefault(key, []):
            self.titles[key].append(i)

    def _find(self, rec: Dict[str, Any]) -> Tuple[Optional[int], str, List[int]]:
        match, how, related = None, "", []
        if rec["doi"] and ("doi", rec["doi"]) in self.ids:
            match, how = self.ids[("doi", rec["doi"])], "doi"
        for field in _PROVIDER_IDS:
            i = self.ids.get((field, rec[field])) if rec[field] else None
            if i is None or i == match:
                continue
            other = self.records[i]["doi"]
            if rec["doi"] and other and other != rec["doi"]:
                related.append(i)  # same provider id, different DOI: another version
            elif match is None:
                match, how = i, field
        if match is None:
            key = title_key(rec["title"])
            cands = [i for i in self.titles.get(key, []) if key
                     and not (rec["doi"] and self.records[i]["doi"] and self.records[i]["doi"] != rec["doi"])
                     and _same_work_by_title(self.records[i], rec)]
            if len(cands) == 1:
                match, how = cands[0], "title+year+author"
        return match, how, related

    def add(self, rec: Dict[str, Any], pos: int) -> None:
        match, how, related = self._find(rec)
        if match is None:
            rec["merged_from"] = [_provenance(rec, "first")]
            rec["related_versions"] = []
            self.records.append(rec)
            self.best.append(pos)
            match = len(self.records) - 1
        else:
            m = self.records[match]
            m["cited_by"].update(rec["cited_by"])
            m["found_in"] += [s for s in rec["found_in"] if s not in m["found_in"]]
            for field in ("abstract", "venue", "doi", "pmid", "pmcid", "arxiv_id", "pub_date",
                          "year", "authors"):
                if rec.get(field) and not m.get(field):
                    m[field] = rec[field]
            m["merged_from"].append(_provenance(rec, how))
            self.best[match] = min(self.best[match], pos)
        self._register(match)
        for i in related:
            a, b = self.records[match], self.records[i]
            if b["doi"] not in a["related_versions"]:
                a["related_versions"].append(b["doi"])
            if a["doi"] not in b["related_versions"]:
                b["related_versions"].append(a["doi"])


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


# Wording that asks for new work. It is never converted into a date filter (see notes).
_RECENT = re.compile(r"\b(recent|recently|latest|newest|up-to-date|this year|last year|"
                     r"(?:past|last) (?:few|\d+|two|three|five|ten) (?:months|years))\b", re.I)


def search(query: str, limit: int = 10, sources: Optional[List[str]] = None,
           terms: Optional[str] = None, rank: str = "relevance",
           get: Optional[Callable[[str], bytes]] = None, since: Optional[str] = None,
           until: Optional[str] = None, cite_index: str = "crossref") -> Dict[str, Any]:
    """Query each source, merge the same work, filter by date, then order the records.

    rank="relevance" (default) keeps each index's own relevance order (best position across
    indexes; ties: found in more indexes first). rank="cited" draws a larger pool (3x limit,
    max 50 per index; Europe PMC sorted by its citation count) and orders it by ONE index's
    count (``cite_index``, default crossref); records without that count follow in relevance
    order. Counts from different indexes are never compared with each other.

    Raises QuerySyntaxError for malformed --terms and ValueError for a bad rank, cite_index or
    date, before any request is sent.
    """
    if rank not in RANKS:
        raise ValueError(f"rank must be one of {', '.join(RANKS)} (got {rank!r})")
    if cite_index not in CITE_INDEXES:
        raise ValueError(f"cite_index must be one of {', '.join(CITE_INDEXES)} (got {cite_index!r})")
    window = parse_window(since, until)
    plan = plan_query(query, terms)
    get = get or _http_get  # looked up at call time, so the transport can be swapped in tests
    requested = list(sources or SOURCES)
    notes = list(plan["notes"])
    if not window and (_RECENT.search(query) or _RECENT.search(terms or "")):
        notes.append('The request asks for recent work; that wording was not converted into a '
                     'date filter (no date range is ever inferred). Pass --since YYYY (and '
                     '--until) to restrict publication dates.')
    translation = {name: translate(plan, name) for name in requested}
    pool = min(50, limit * 3) if rank == "cited" else limit
    merger = _Merger()
    errors: Dict[str, str] = {}
    skipped = {n: t["note"] for n, t in translation.items() if t["mode"] == "skipped"}
    for name in requested:
        if name in skipped:
            continue
        try:
            hits = SEARCHERS[name](translation[name]["query"], pool, get, rank, window)
        except RateLimited as exc:
            errors[name] = f"HTTP 429 ({exc}; not checked, which is not 'no results')"
            continue
        except urllib.error.HTTPError as exc:
            why = (" (rate-limited after backoff: not checked, which is not 'no results'; "
                   "retry later)" if exc.code == 429 else "")
            errors[name] = f"HTTP {exc.code}{why}"
            continue
        except (urllib.error.URLError, OSError, ValueError, KeyError, ET.ParseError) as exc:
            errors[name] = str(exc)[:200]
            continue
        for pos, rec in enumerate(hits):
            if rec["title"]:
                merger.add(rec, pos)

    order = sorted(range(len(merger.records)),
                   key=lambda i: (merger.best[i], -len(merger.records[i]["found_in"])))
    date_filter = None
    if window:
        verdicts = {i: _in_window(merger.records[i], window) for i in order}
        dropped = [i for i in order if verdicts[i] is False]
        unknown = [i for i in order if verdicts[i] is None]
        for i in unknown:
            merger.records[i]["date_unknown"] = True
        order = [i for i in order if verdicts[i] is not False]
        date_filter = {"since": window["since"].isoformat() if window["since"] else None,
                       "until": window["until"].isoformat() if window["until"] else None,
                       "dropped_out_of_range": len(dropped), "kept_unknown_date": len(unknown),
                       "unknown_dates": "kept and marked date_unknown"}
    if rank == "cited":
        have = sorted((i for i in order if cite_index in merger.records[i]["cited_by"]),
                      key=lambda i: -merger.records[i]["cited_by"][cite_index])
        order = have + [i for i in order if cite_index not in merger.records[i]["cited_by"]]
        basis = (f"{cite_index} citation count (one index; counts from different indexes are "
                 f"not compared); records without a {cite_index} count follow in relevance order")
    else:
        basis = ("relevance: each index's own order, best position across indexes; ties: "
                 "found in more indexes first")
    records = [merger.records[i] for i in order]
    for r in records:
        count = r["cited_by"].get(cite_index)
        r["impact"] = impact_label(r["year"], count) if count is not None else ""
    return {"schema_version": SCHEMA_VERSION, "query": query, "terms": plan["terms"],
            "syntax": plan["syntax"], "rank": rank, "rank_basis": basis, "cite_index": cite_index,
            "records": records[:limit], "errors": errors, "skipped": skipped,
            "query_translation": translation, "date_filter": date_filter, "notes": notes,
            "requested": requested, "queried": [s for s in requested if s not in skipped],
            "searched": date.today().isoformat()}


def to_markdown(res: Dict[str, Any]) -> str:
    skipped = res.get("skipped") or {}
    queried = res.get("queried", SOURCES)
    answered = [s for s in queried if s not in res["errors"] and s not in skipped]
    unchecked = f"; not checked: {', '.join(res['errors'])}" if res["errors"] else ""
    unchecked += f"; skipped: {', '.join(skipped)}" if skipped else ""
    rank = res.get("rank", "relevance")
    order = (f"cited — {res.get('cite_index', 'crossref')} citation count; records without one "
             "follow in relevance order" if rank == "cited" else rank)
    lines = [f"Keyless scholarly backend — searched {res['searched']} for \"{res['terms']}\" "
             f"in {', '.join(answered) or 'no source'}{unchecked} (order: {order}).",
             "These are index records, not a synthesis: open each paper before citing a finding "
             "from it. Citation counts differ by index; each is labelled with its source.", ""]
    qt = res.get("query_translation") or {}
    approx = {s for s, t in qt.items() if t["mode"] == "approximate"}
    if qt:
        lines.append(f"Query translation (syntax: {res.get('syntax', 'natural')}):")
        for src, t in qt.items():
            q = f" — `{t['query']}`" if t["query"] else ""
            lines.append(f"   - {src}: {t['mode']}{q}" + (f" — {t['note']}" if t["note"] else ""))
    df = res.get("date_filter")
    if df:
        lines.append(f"Date filter: {df['since'] or 'any'} to {df['until'] or 'any'} (--since/"
                     f"--until), sent to each index and re-checked on the returned dates: "
                     f"{df['dropped_out_of_range']} record(s) outside the range dropped; "
                     f"{df['kept_unknown_date']} record(s) with no date kept and marked "
                     "\"date unknown\".")
    for note in res.get("notes") or []:
        lines.append(f"Note: {note}")
    if qt or df or res.get("notes"):
        lines.append("")
    for i, r in enumerate(res["records"], 1):
        who = "; ".join(a for a in r["authors"] if a) + (" et al." if len(r["authors"]) >= 3 else "")
        cites = " · ".join(f"{v:,} ({k})" for k, v in r["cited_by"].items())
        bits = [f"{i}. **{r['title']}** — {who or 'authors n/a'} ({r['year'] or 'n.d.'})."]
        if r["venue"]:
            bits.append(f"*{r['venue']}*.")
        if r["doi"]:
            bits.append(f"DOI: {r['doi']}")
        lines.append(" ".join(bits))
        merged = r.get("merged_from") or []
        meta = [f"cited {cites}" if cites else "", r.get("impact", ""), "found in: " +
                ", ".join(r["found_in"]),
                "approximate query only" if approx and set(r["found_in"]) <= approx else "",
                "merged on " + ", ".join(m["matched_on"] for m in merged[1:]) if len(merged) > 1 else "",
                "other version(s): " + ", ".join(r["related_versions"]) if r.get("related_versions") else "",
                "date unknown (not checked against --since/--until)" if r.get("date_unknown") else ""]
        lines.append("   " + " — ".join(m for m in meta if m))
        lines.append(f"   {r['url'] or ('https://doi.org/' + r['doi'] if r['doi'] else '')}")
        if r["abstract"]:
            lines.append(f"   Abstract: {r['abstract'][:300]}{'…' if len(r['abstract']) > 300 else ''}")
    if res["errors"]:
        lines += ["", "Sources that did not answer: " +
                  "; ".join(f"{k}: {v}" for k, v in res["errors"].items())]
    if skipped:
        lines += ["", "Sources skipped for this query: " +
                  "; ".join(f"{k}: {v}" for k, v in skipped.items())]
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Keyless scholarly search (Crossref, Europe PMC, "
                                 "arXiv, Semantic Scholar), merged by DOI and provider ids.")
    ap.add_argument("query", help="topic or request; English routing words are dropped")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--sources", default=",".join(SOURCES),
                    help=f"comma list from {','.join(SOURCES)}")
    ap.add_argument("--rank", choices=RANKS, default="relevance",
                    help="relevance (default): each index's own relevance order; cited: by one "
                         "index's citation count (--cite-index), uncounted records last")
    ap.add_argument("--cite-index", choices=CITE_INDEXES, default="crossref",
                    help="the one index whose citation count orders --rank cited and the impact "
                         "labels (default crossref)")
    ap.add_argument("--terms", help="explicit search expression instead of the request's topic "
                    "words: words, \"quoted phrases\", AND, OR, NOT (capitals), -word, "
                    "parentheses; no routing-word filter; malformed syntax exits 2")
    ap.add_argument("--since", help="earliest publication date, YYYY or YYYY-MM-DD")
    ap.add_argument("--until", help="latest publication date, YYYY or YYYY-MM-DD")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    wanted = [s.strip() for s in args.sources.split(",") if s.strip()]
    unknown = [s for s in wanted if s not in SEARCHERS]
    if unknown or not wanted:
        # An explicitly named source that is not available must not be answered by the others.
        print(f"error: unknown source(s) {', '.join(unknown) or '(none given)'}; choose from "
              f"{','.join(SOURCES)}" + (" (OpenAlex was removed: its keyless search is metered "
                                        "per IP)" if "openalex" in unknown else ""), file=sys.stderr)
        return 2
    try:
        res = search(args.query, args.limit, wanted, terms=args.terms, rank=args.rank,
                     since=args.since, until=args.until, cite_index=args.cite_index)
    except ValueError as exc:  # QuerySyntaxError, bad date: nothing was sent
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(res, indent=2, ensure_ascii=False) if args.json else to_markdown(res))
    return 0 if res["records"] else 1


if __name__ == "__main__":
    sys.exit(main())
