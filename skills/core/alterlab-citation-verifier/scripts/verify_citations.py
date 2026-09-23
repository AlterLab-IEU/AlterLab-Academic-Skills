#!/usr/bin/env python3
"""verify_citations.py — Existence-verify a bibliography against public scholarly APIs.

Given a bibliography (BibTeX, a list of DOIs/arXiv IDs, or free-form references),
this checks whether each entry ACTUALLY EXISTS by querying four public scholarly
APIs (Crossref, OpenAlex, Semantic Scholar, arXiv), plus the doi.org Handle API to
confirm whether a cited DOI is registered at all. It resolves DOI / arXiv
identifiers, fuzzy-matches title and authors (difflib SequenceMatcher ratio —
Ratcliff/Obershelp, not edit-distance — default threshold 0.70), flags retractions
(Crossref ``updated-by`` / ``update-to`` records, which since 2025 include the
Retraction Watch database, and OpenAlex ``is_retracted``), and emits a JSON verdict
per entry mapped to the AlterLab citation hallucination taxonomy (TF / PAC / IH / PH / SH).

Design constraints:
- NO API key required. Optional keys only raise rate limits: ``OPENALEX_API_KEY``
  (OpenAlex retired its ``mailto`` polite pool in Feb 2026; keyless calls share a
  small per-IP daily budget in which DOI lookups are free but searches are metered)
  and ``S2_API_KEY`` (Semantic Scholar). Keys are sent as headers, never logged.
- NO third-party deps required: uses ``requests`` if present, else the stdlib
  (``urllib``). Mirrors the integrity_verification_agent taxonomy exactly (see
  ../SKILL.md and skills/core/alterlab-research-pipeline/agents/integrity_verification_agent.md).
- GRACEFUL DEGRADATION: with no network, or when every source errors (rate limits,
  5xx), the entry gets an ``unverified`` verdict plus manual-verification
  instructions. It never silently passes an entry, and it never reports a Total
  Fabrication that rests only on sources that failed to answer.

Taxonomy (codes mirror the canonical Five-Type Taxonomy):
  TF  Total Fabrication           — entry exists in no source
  PAC Partial Attribute Corruption — entry found but ≥1 metadata field is wrong
  IH  Identifier Hijacking         — DOI/arXiv ID resolves to an unrelated paper
  PH  Placeholder Hallucination    — entry is an unresolved template/placeholder
  SH  Semantic Hallucination       — entry resolves but does not support its claim
                                      (claim-vs-source check is out of scope here;
                                       emitted only as an advisory flag)

Usage:
  uv run python verify_citations.py INPUT [--format auto|bibtex|doi|freeform]
                                          [--mailto you@example.com]
                                          [--threshold 0.70]
                                          [--out report.json] [--offline]
  uv run python verify_citations.py - < refs.bib        # read stdin

Optional environment: OPENALEX_API_KEY (free key, openalex.org/settings/api; sent
as an Authorization: Bearer header), S2_API_KEY (Semantic Scholar, x-api-key header).
A rate-limited source (HTTP 429) is reported in ``source_status`` and
``summary.notes``; it never counts as "not found".

Exit codes: 0 = ran (see JSON ``summary.verdict``); 2 = bad input/usage.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any, Callable, Optional

# --------------------------------------------------------------------------- #
# HTTP layer — prefer requests, fall back to urllib (stdlib). Keys optional.  #
# --------------------------------------------------------------------------- #

TOOL_VERSION = "1.1.0"
DEFAULT_MAILTO = "alterlab.ieu@gmail.com"
USER_AGENT = (
    "alterlab-citation-verifier/" + TOOL_VERSION + " (https://github.com/AlterLab-IEU/"
    "AlterLab-Academic-Skills; mailto:{mailto})"
)
HTTP_TIMEOUT = 15
RETRIES = 2
BACKOFF = 1.5
# A 429 asking us to wait longer than this (e.g. OpenAlex's exhausted daily budget
# returns Retry-After of many hours) is reported as a source error, not retried.
MAX_RETRY_AFTER = 30

# Optional credentials — never required; they only raise rate limits.
OPENALEX_API_KEY = os.environ.get("OPENALEX_API_KEY", "").strip()
S2_API_KEY = (os.environ.get("S2_API_KEY") or os.environ.get("SEMANTIC_SCHOLAR_API_KEY") or "").strip()

# Minimum spacing between calls to one host. arXiv's API terms ask for >= 3 s
# between calls; Semantic Scholar's key tier is 1 request/second.
MIN_INTERVAL = {"export.arxiv.org": 3.0, "arxiv.org": 3.0, "api.semanticscholar.org": 1.0}
_LAST_CALL: dict[str, float] = {}

try:  # pragma: no cover - environment dependent
    import requests as _requests  # type: ignore
    _HAS_REQUESTS = True
except Exception:  # pragma: no cover
    _requests = None
    _HAS_REQUESTS = False

import urllib.error
import urllib.parse
import urllib.request


class NetworkUnavailable(Exception):
    """Raised when a request cannot reach the network (DNS / connection error)."""


class SourceError(Exception):
    """One source could not answer (rate limit, 5xx, auth, timeout).

    Distinct from "no match": a source that errored says nothing about whether
    the cited work exists, so it must never count as evidence of fabrication.
    """


class _TransientHTTP(Exception):
    def __init__(self, status: int, retry_after: float = 0.0) -> None:
        super().__init__(f"transient HTTP {status}")
        self.status = status
        self.retry_after = retry_after


def _retry_after(value: Optional[str]) -> float:
    try:
        return float(value) if value else 0.0
    except ValueError:
        return 0.0


def _throttle(url: str) -> None:
    host = urllib.parse.urlsplit(url).hostname or ""
    gap = MIN_INTERVAL.get(host, 0.0)
    if gap:
        wait = _LAST_CALL.get(host, 0.0) + gap - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _LAST_CALL[host] = time.monotonic()


# What a rate limit means per host, so a 429 is reported with its remedy instead
# of silently reading as "no match".
_RATE_LIMIT_HINTS = {
    "api.openalex.org": ("OpenAlex rate limit: the keyless daily budget shared by this IP is "
                         "spent (or the request rate is too high); set a free OPENALEX_API_KEY "
                         "or retry after the reset at midnight UTC"),
    "api.semanticscholar.org": ("Semantic Scholar rate limit: the keyless pool is shared by all "
                                "unauthenticated users; set S2_API_KEY or retry later"),
    "api.crossref.org": "Crossref rate limit: slow down (polite pool allows 10 req/s, 3 concurrent)",
}


def _http_get(url: str, mailto: str, accept: str = "application/json",
              extra_headers: Optional[dict] = None) -> Any:
    """GET ``url`` and parse JSON (or return raw text for XML endpoints).

    Returns None when the API answered "not found / no match" (404, other 4xx).
    Raises SourceError when the API could not answer (429/5xx after retries,
    401/403, timeout) and NetworkUnavailable on a DNS/connection failure, so the
    caller can tell "offline" and "this source failed" apart from "not found".
    """
    headers = {"User-Agent": USER_AGENT.format(mailto=mailto), "Accept": accept}
    headers.update(extra_headers or {})
    last_exc: Optional[Exception] = None
    for attempt in range(RETRIES + 1):
        _throttle(url)
        try:
            if _HAS_REQUESTS:
                resp = _requests.get(url, headers=headers, timeout=HTTP_TIMEOUT)
                status = resp.status_code
                if status == 429 or 500 <= status < 600:
                    raise _TransientHTTP(status, _retry_after(resp.headers.get("Retry-After")))
                if status in (401, 403):
                    raise SourceError(f"HTTP {status} (access denied)")
                if status >= 400:
                    return None  # 404 and other 4xx → the API answered "no match"
                return resp.json() if "json" in accept else resp.text
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
                body = r.read().decode("utf-8", "replace")
                return json.loads(body) if "json" in accept else body
        except _TransientHTTP as exc:
            last_exc = exc
            if exc.retry_after > MAX_RETRY_AFTER:
                break
        except urllib.error.HTTPError as exc:  # urllib path
            if exc.code == 429 or 500 <= exc.code < 600:
                last_exc = exc
                if _retry_after(exc.headers.get("Retry-After") if exc.headers else None) > MAX_RETRY_AFTER:
                    break
            elif exc.code in (401, 403):
                raise SourceError(f"HTTP {exc.code} (access denied)") from exc
            else:
                return None  # 404 and other 4xx → "no match"
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, (socket.timeout, TimeoutError)):
                last_exc = exc  # slow source, not an offline machine
            else:
                raise NetworkUnavailable(str(exc.reason)) from exc  # DNS / no route
        except (socket.timeout, TimeoutError) as exc:
            last_exc = exc
        except ValueError as exc:  # malformed JSON body
            raise SourceError(f"unparseable response: {exc}") from exc
        except SourceError:
            raise
        except Exception as exc:  # requests ConnectionError, Timeout, SSLError, etc.
            name = type(exc).__name__
            if "Timeout" in name:
                last_exc = exc
            elif any(k in name for k in ("Connection", "DNS", "SSL")):
                raise NetworkUnavailable(str(exc)) from exc
            else:
                last_exc = exc
        if attempt < RETRIES:
            time.sleep(BACKOFF * (attempt + 1))
    code = getattr(last_exc, "status", None) or getattr(last_exc, "code", None)
    if code == 429:
        host = urllib.parse.urlsplit(url).hostname or ""
        raise SourceError("HTTP 429 — " + _RATE_LIMIT_HINTS.get(host, "rate limited; retry later"))
    raise SourceError(f"no answer after retries ({last_exc})")


# --------------------------------------------------------------------------- #
# Fuzzy matching                                                              #
# --------------------------------------------------------------------------- #

_WS = re.compile(r"\s+")
_NONWORD = re.compile(r"[^\w\s]")


def _normalize(text: str) -> str:
    text = (text or "").lower().strip()
    text = _NONWORD.sub(" ", text)
    return _WS.sub(" ", text).strip()


def title_ratio(a: str, b: str) -> float:
    """Similarity ratio (0..1) via difflib SequenceMatcher on normalized titles.

    Some records drop the subtitle (OpenAlex / Semantic Scholar often store only
    "Main title"), so a title with a subtitle also counts as matching when its main
    title is essentially identical (ratio >= 0.9) to the other title *as a whole*.
    Comparing main titles loosely would match unrelated works that merely share a
    generic main title ("Education and technology: ..."), so that is not done.
    """
    na, nb = _normalize(a), _normalize(b)
    best = SequenceMatcher(None, na, nb).ratio()
    for x, other in ((a, nb), (b, na)):
        m = re.match(r"(.+?)(?::|\s[-—]\s|\?)", x or "")
        if m:
            head = _normalize(m.group(1))
            if len(head) >= 20 and SequenceMatcher(None, head, other).ratio() >= 0.9:
                best = max(best, SequenceMatcher(None, head, other).ratio())
    return best


def _surname(name: str) -> str:
    """Best-effort surname extraction from 'Last, First' or 'First Last'."""
    name = name.strip()
    if "," in name:
        return _normalize(name.split(",", 1)[0])
    parts = _normalize(name).split()
    return parts[-1] if parts else ""


def author_overlap(cited: list[str], found_surnames: list[str]) -> Optional[float]:
    """Fraction of cited author surnames that appear among the found surnames.

    None when either side has no author list: the record can neither confirm nor
    disprove the cited authors, which is different from a 0% overlap.
    """
    cited_s = {_surname(a) for a in cited if a.strip()}
    found_s = {_normalize(s) for s in found_surnames if s.strip()}
    if not cited_s or not found_s:
        return None
    hits = sum(1 for c in cited_s if any(c and (c in f or f in c) for f in found_s))
    return hits / len(cited_s)


def _year_match(entry: "Entry", rec: dict) -> bool:
    return bool(entry.year) and entry.year in (rec.get("years") or [rec.get("year")])


def _rank(entry: "Entry", rec: dict) -> tuple:
    """Sort key for "which returned record is the cited work": title match first,
    then author agreement, then year — so a same-titled paper by other authors, or
    another edition, loses to the record that matches the citation."""
    r = title_ratio(entry.title, rec.get("title") or "") if entry.title else 1.0
    ov = author_overlap(entry.authors, rec.get("authors") or [])
    return (r >= 0.7, 0.5 if ov is None else ov, _year_match(entry, rec), r)


# --------------------------------------------------------------------------- #
# Parsing: BibTeX / DOI list / free-form                                      #
# --------------------------------------------------------------------------- #

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
# New-style IDs (2007+) anywhere; old-style (archive/YYMMNNN) only with an explicit
# arXiv prefix or abs/ URL, so ordinary URL paths are not mistaken for arXiv IDs.
ARXIV_RE = re.compile(
    r"(?<![\w.])(\d{4}\.\d{4,5})(?:v\d+)?(?![\w.])"
    r"|(?:arxiv:\s*|arxiv\.org/(?:abs|pdf)/)([a-z\-]+(?:\.[A-Z]{2})?/\d{7})",
    re.IGNORECASE,
)
OLD_ARXIV_BARE_RE = re.compile(r"^\s*([a-z\-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?\s*$", re.IGNORECASE)
# "M. K." / "J. P" / "A.-B." / "L" — author initials, not a surname ("OECD" is kept).
_INITIALS_RE = re.compile(r"^(?:[A-Z]\.?-?\s*){1,4}$")


# Start of a new reference on its own line: "[12] ", "12. ", "Surname, I." /
# "Surname, Name", or a capitalised author/organisation followed soon by "(YYYY".
_NEW_REF_LINE_RE = re.compile(
    r"^\s*(?:\[?\d{1,3}[\].)]\s|[A-Z][\w'’\-]+(?:\s[A-Z][\w'’\-]+)?,\s+[A-Z]"
    r"|[A-Z][^\n]{0,120}?\((?:19|20)\d{2}[a-z]?[),])"
)
PLACEHOLDER_RE = re.compile(
    r"(\[(?:citation|ref|cite|todo|xx+|author|year)[^\]]*\]"
    r"|\\cite\{[^}]*\}"
    r"|\bTODO\b|\bTKTK\b|\bXX+\b"
    r"|et al\.,?\s*\(?(?:YYYY|n\.d\.|\?\?\?\?)\)?"
    r"|\(\s*(?:year|date)\s*\)"
    r"|\bforthcoming\b|\bin press\b)",
    re.IGNORECASE,
)


def _is_initials(token: str) -> bool:
    letters = re.sub(r"[\s.\-]", "", token)
    if not _INITIALS_RE.match(token):
        return False
    return "." in token or len(letters) <= 2


@dataclass
class Entry:
    raw: str
    key: str = ""
    title: str = ""
    authors: list[str] = field(default_factory=list)
    year: str = ""
    doi: str = ""
    arxiv_id: str = ""
    venue: str = ""


def _looks_like_bibtex(text: str) -> bool:
    return bool(re.search(r"@\w+\s*\{", text))


def parse_bibtex(text: str) -> list[Entry]:
    entries: list[Entry] = []
    for m in re.finditer(r"@(\w+)\s*\{([^,]*),(.*?)\n\}", text, re.DOTALL):
        body = m.group(3)
        key = m.group(2).strip()

        def fld(name: str) -> str:
            # (?<![\w-]) keeps "title" from matching inside "booktitle"/"shorttitle";
            # braces/quotes are optional so bare values such as `year = 2019,` parse.
            fm = re.search(
                rf"(?<![\w-]){name}\s*=\s*[{{\"]?(.+?)[}}\"]?\s*,?\s*$",
                body,
                re.IGNORECASE | re.MULTILINE | re.DOTALL,
            )
            return _WS.sub(" ", fm.group(1)).strip() if fm else ""

        authors_raw = fld("author")
        authors = [a.strip() for a in re.split(r"\s+and\s+", authors_raw) if a.strip()]
        year_raw = fld("year") or fld("date")
        ym = re.search(r"(?:19|20)\d{2}", year_raw)
        eprint = fld("eprint")
        bare_old = OLD_ARXIV_BARE_RE.match(eprint) if eprint else None
        e = Entry(
            raw=m.group(0),
            key=key,
            title=fld("title").replace("{", "").replace("}", ""),
            authors=authors,
            year=ym.group(0) if ym else year_raw,
            doi=_first_doi(fld("doi") or body),
            arxiv_id=bare_old.group(1) if bare_old else _first_arxiv(eprint or body),
            venue=fld("journal") or fld("booktitle") or fld("publisher"),
        )
        entries.append(e)
    return entries


def _first_doi(text: str) -> str:
    m = DOI_RE.search(text or "")
    return m.group(0).rstrip(".,;") if m else ""


def _first_arxiv(text: str) -> str:
    # arXiv's own DOIs (10.48550/arXiv.<id>) name the ID; every other DOI is
    # stripped first so "10.1016/j.compedu.2020.103998" cannot yield "2020.10399".
    text = re.sub(r"10\.48550/arxiv\.", "arXiv:", text or "", flags=re.IGNORECASE)
    text = DOI_RE.sub(" ", text)
    m = ARXIV_RE.search(text)
    if not m:
        return ""
    return (m.group(1) or m.group(2) or "").strip()


def _is_bare_identifier_line(line: str) -> bool:
    """True for lines that are just an identifier ("doi:10.x/y", a doi.org URL, an arXiv ID)."""
    rest = DOI_RE.sub(" ", line)
    rest = ARXIV_RE.sub(" ", rest)
    rest = re.sub(r"(?i)https?://(dx\.)?doi\.org/|https?://arxiv\.org/(abs|pdf)/|\bdoi:|\barxiv:", " ", rest)
    return len(re.sub(r"[\W_]+", "", rest)) <= 3


def _clean_authors(names: list[str]) -> list[str]:
    """Drop initials-only fragments ("M. K.") and 'et al.' produced by comma splitting."""
    out = []
    for n in names:
        n = n.strip(" ,&")
        if not n or n.lower().startswith("et al") or _is_initials(n):
            continue
        n = n.strip(" .")
        out.append(n)
    return out


def parse_doi_list(text: str) -> list[Entry]:
    entries: list[Entry] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        doi = _first_doi(line)
        arxiv = _first_arxiv(line) if not doi else ""
        if doi or arxiv:
            entries.append(Entry(raw=line, doi=doi, arxiv_id=arxiv))
    return entries


def _split_references(text: str) -> list[str]:
    """One block per reference: blank lines, numbered markers, or — for a list pasted
    one reference per line — a new line that starts like a reference ("Surname, I.")."""
    text = text.strip()
    if re.search(r"\n\s*\n", text):
        return re.split(r"\n\s*\n|\n(?=\s*\[?\d{1,3}[\].)]\s)", text)
    blocks: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        starts_new = (_NEW_REF_LINE_RE.match(line) or _is_bare_identifier_line(line)
                      or (blocks and _is_bare_identifier_line(blocks[-1])))
        if blocks and not starts_new:
            blocks[-1] += " " + line.strip()  # hard-wrapped continuation line
        else:
            blocks.append(line.strip())
    return blocks


def parse_freeform(text: str) -> list[Entry]:
    """One reference per block (see _split_references); heuristic field extraction."""
    blocks = _split_references(text)
    entries: list[Entry] = []
    for block in blocks:
        block = _WS.sub(" ", block).strip()
        if not block:
            continue
        if _is_bare_identifier_line(block):  # a lone DOI / arXiv ID inside a pasted list
            entries.append(Entry(raw=block, doi=_first_doi(block), arxiv_id=_first_arxiv(block)))
            continue
        ym = re.search(r"\(?((?:19|20)\d{2})\)?", block)
        # Title heuristic: first quoted span, else the sentence after the year
        # (split on ". " but not after an initial, so "Web 2.0" / "J. Smith" survive).
        tm = re.search(r"[\"“](.+?)[\"”]", block)
        if tm:
            title = tm.group(1)
        elif ym:
            after = block[ym.end():].lstrip(" .)")
            title = re.split(r"(?<!\s[A-Z])\.\s", after, maxsplit=1)[0] if after else block
        else:
            title = block
        title = re.sub(r"[*_]", "", title)  # Markdown emphasis around book titles
        title = re.sub(r"\s*\(\s*(?:\d+(?:st|nd|rd|th)|rev(?:ised)?\.?)\s*(?:ed\.?|edition)?\s*\)?\s*$",
                       "", title, flags=re.IGNORECASE)
        authors: list[str] = []
        if ym and ym.start() > 0:
            head = block[: ym.start()].strip(" .,(")
            head = re.sub(r"^\s*\[?\d{1,3}[\].)]\s+", "", head)  # drop "12." / "[12]" markers
            authors = _clean_authors(re.split(r",| & | and ", head))[:6]
        entries.append(
            Entry(
                raw=block,
                title=title.strip(" .,"),
                authors=authors,
                year=ym.group(1) if ym else "",
                doi=_first_doi(block),
                arxiv_id=_first_arxiv(block),
            )
        )
    return entries


def parse_bibliography(text: str, fmt: str) -> list[Entry]:
    if fmt == "auto":
        if _looks_like_bibtex(text):
            fmt = "bibtex"
        else:
            # "doi" only when the lines are bare identifiers; a full reference that
            # merely contains a DOI stays free-form, so its title and authors are kept
            # for the Identifier Hijacking check.
            non_empty = [ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
            id_lines = sum(1 for ln in non_empty
                           if (_first_doi(ln) or _first_arxiv(ln)) and _is_bare_identifier_line(ln))
            fmt = "doi" if non_empty and id_lines >= max(1, len(non_empty) * 0.6) else "freeform"
    if fmt == "bibtex":
        return parse_bibtex(text)
    if fmt == "doi":
        return parse_doi_list(text)
    if fmt == "freeform":
        return parse_freeform(text)
    raise ValueError(f"unknown format: {fmt}")


# --------------------------------------------------------------------------- #
# API adapters → normalized record {title, authors[surnames], year, doi, retracted} #
# --------------------------------------------------------------------------- #


def crossref_by_doi(doi: str, mailto: str) -> Optional[dict]:
    q_mailto = urllib.parse.quote(mailto)
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}?mailto={q_mailto}"
    data = _http_get(url, mailto)
    if not data or "message" not in data:
        return None
    rec = _crossref_norm(data["message"])
    rec["method"] = "id"  # resolved BY the cited identifier
    return rec


def crossref_by_title(entry: "Entry", mailto: str) -> Optional[dict]:
    # query.bibliographic is built for citation strings: title + first author + year
    # ranks the cited work above same-titled works and other editions.
    biblio = " ".join(x for x in (entry.title, _surname(entry.authors[0]) if entry.authors else "",
                                  entry.year) if x)
    url = (
        f"https://api.crossref.org/works?query.bibliographic={urllib.parse.quote(biblio)}"
        f"&rows=5&mailto={urllib.parse.quote(mailto)}"
    )
    data = _http_get(url, mailto)
    items = (data or {}).get("message", {}).get("items", []) if data else []
    if not items:
        return None
    # Relevance order is not match order: keep the record that best matches the citation.
    rec = max((_crossref_norm(it) for it in items[:5]), key=lambda r: _rank(entry, r))
    rec["method"] = "title"  # found by a fuzzy title/biblio search
    return rec


# Crossref update types that mean "do not rely on this work" (retraction notices,
# withdrawals, removals). Expressions of concern are surfaced as a separate flag.
_RETRACTION_TYPES = ("retraction", "partial_retraction", "withdrawal", "removal")


def _crossref_title(msg: dict) -> str:
    title = (msg.get("title") or [""])[0] or ""
    sub = (msg.get("subtitle") or [""])[0] or ""
    return f"{title}: {sub}" if title and sub else title


def _crossref_norm(msg: dict) -> dict:
    # Organisational authors ("OECD") carry `name` instead of `family`.
    surnames = [a.get("family") or a.get("name") or "" for a in msg.get("author", []) or []]
    surnames = [s for s in surnames if s]
    years = []
    for key in ("issued", "published-print", "published-online", "published"):
        parts = (msg.get(key, {}) or {}).get("date-parts", [[None]])
        if parts and parts[0] and parts[0][0]:
            years.append(str(parts[0][0]))
    year = years[0] if years else ""  # `issued` = earliest of print/online
    # `updated-by` on the cited work lists notices that update it, from the
    # publisher or (source "retraction-watch") the Retraction Watch database,
    # which Crossref serves in its REST API since 2025. `update-to` appears when the
    # matched record is itself a notice (or a publisher deposited the link there).
    updates = list(msg.get("updated-by", []) or []) + list(msg.get("update-to", []) or [])
    types = {(u.get("type") or "").lower() for u in updates}
    retracted = any(t in _RETRACTION_TYPES or "retract" in t for t in types)
    return {
        "source": "crossref",
        "title": _crossref_title(msg),
        "authors": surnames,
        "year": year,
        "years": sorted(set(years)),  # online-first vs print years can differ by one
        "doi": (msg.get("DOI") or "").lower(),
        "retracted": retracted,
        "concern": "expression_of_concern" in types,
    }


def _openalex_headers() -> dict:
    # OpenAlex ignores `mailto` since Feb 2026; a free key raises the daily budget.
    return {"Authorization": f"Bearer {OPENALEX_API_KEY}"} if OPENALEX_API_KEY else {}


def openalex_lookup(entry: Entry, mailto: str) -> Optional[dict]:
    if entry.doi:
        # Singleton DOI lookups are free even without a key.
        url = f"https://api.openalex.org/works/doi:{urllib.parse.quote(entry.doi)}"
        data = _http_get(url, mailto, extra_headers=_openalex_headers())
        if data and data.get("id"):
            rec = _openalex_norm(data)
            rec["method"] = "id"
            return rec
    if entry.title:
        # Searches draw on the metered budget (shared per IP when keyless).
        q = urllib.parse.quote(entry.title)
        url = f"https://api.openalex.org/works?search={q}&per-page=5"
        data = _http_get(url, mailto, extra_headers=_openalex_headers())
        results = (data or {}).get("results", []) if data else []
        if results:
            rec = max((_openalex_norm(w) for w in results[:5]), key=lambda r: _rank(entry, r))
            rec["method"] = "title"
            return rec
    return None


def _openalex_norm(w: dict) -> dict:
    surnames = []
    for au in w.get("authorships", []):
        disp = (au.get("author", {}) or {}).get("display_name", "")
        if disp:
            surnames.append(disp.split()[-1])
    return {
        "source": "openalex",
        "title": w.get("title") or w.get("display_name") or "",
        "authors": surnames,
        "year": str(w.get("publication_year") or ""),
        "doi": (w.get("doi") or "").replace("https://doi.org/", "").lower(),
        "retracted": bool(w.get("is_retracted")),
    }


def semanticscholar_lookup(entry: Entry, mailto: str) -> Optional[dict]:
    fields = "title,year,authors,externalIds"
    hdrs = {"x-api-key": S2_API_KEY} if S2_API_KEY else {}
    if entry.doi:
        url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{urllib.parse.quote(entry.doi)}?fields={fields}"
        data = _http_get(url, mailto, extra_headers=hdrs)
        if data and data.get("title"):
            rec = _ss_norm(data)
            rec["method"] = "id"
            return rec
    if entry.arxiv_id:
        url = f"https://api.semanticscholar.org/graph/v1/paper/ARXIV:{entry.arxiv_id}?fields={fields}"
        data = _http_get(url, mailto, extra_headers=hdrs)
        if data and data.get("title"):
            rec = _ss_norm(data)
            rec["method"] = "id"
            return rec
    if entry.title:
        q = urllib.parse.quote(entry.title)
        url = (
            f"https://api.semanticscholar.org/graph/v1/paper/search?query={q}"
            f"&limit=5&fields={fields}"
        )
        data = _http_get(url, mailto, extra_headers=hdrs)
        items = (data or {}).get("data", []) if data else []
        if items:
            rec = max((_ss_norm(p) for p in items[:5]), key=lambda r: _rank(entry, r))
            rec["method"] = "title"
            return rec
    return None


def _ss_norm(p: dict) -> dict:
    surnames = []
    for au in p.get("authors", []) or []:
        nm = au.get("name", "")
        if nm:
            surnames.append(nm.split()[-1])
    ext = p.get("externalIds", {}) or {}
    return {
        "source": "semanticscholar",
        "title": p.get("title") or "",
        "authors": surnames,
        "year": str(p.get("year") or ""),
        "doi": (ext.get("DOI") or "").lower(),
        "retracted": False,  # S2 does not expose a retraction flag
    }


def arxiv_lookup(entry: Entry, mailto: str) -> Optional[dict]:
    if entry.arxiv_id:
        url = f"https://export.arxiv.org/api/query?id_list={urllib.parse.quote(entry.arxiv_id)}&max_results=1"
    elif entry.title:
        q = urllib.parse.quote(f'ti:"{entry.title}"')
        url = f"https://export.arxiv.org/api/query?search_query={q}&max_results=5"
    else:
        return None
    text = _http_get(url, mailto, accept="application/atom+xml")
    if not text or "<entry>" not in text:
        return None
    method = "id" if entry.arxiv_id else "title"
    recs = []
    for block in text.split("<entry>")[1:]:
        block = block.split("</entry>", 1)[0]
        tm = re.search(r"<title>(.*?)</title>", block, re.DOTALL)
        title = _WS.sub(" ", tm.group(1)).strip() if tm else ""
        surnames = [
            _WS.sub(" ", n).strip().split()[-1]
            for n in re.findall(r"<name>(.*?)</name>", block, re.DOTALL)
            if n.strip()
        ]
        ym = re.search(r"<published>(\d{4})", block)
        aid = re.search(r"<id>.*?abs/([^<]+)</id>", block)
        recs.append({
            "source": "arxiv",
            "title": title,
            "authors": surnames,
            "year": ym.group(1) if ym else "",
            "doi": "",
            "arxiv_id": aid.group(1) if aid else (entry.arxiv_id or ""),
            "retracted": False,
            "method": method,
        })
    if not recs:
        return None
    if method == "title" and entry.title:
        return max(recs, key=lambda r: _rank(entry, r))
    return recs[0]


def arxiv_id_exists(arxiv_id: str, mailto: str) -> Optional[bool]:
    """The arXiv abstract page answers 200 for a real ID and 404 for a nonexistent
    one — authoritative, unlike the query API, which can return an empty feed
    under load. True / False, or None if arXiv could not answer."""
    try:
        page = _http_get(f"https://arxiv.org/abs/{urllib.parse.quote(arxiv_id, safe='/.')}",
                         mailto, accept="text/html")
    except (SourceError, NetworkUnavailable):
        return None
    return page is not None


def doi_registered(doi: str, mailto: str) -> Optional[bool]:
    """Ask the doi.org Handle API whether a DOI exists with ANY registration agency
    (Crossref, DataCite, mEDRA, ...). True / False, or None if it could not answer."""
    url = f"https://doi.org/api/handles/{urllib.parse.quote(doi)}"
    try:
        data = _http_get(url, mailto)
    except (SourceError, NetworkUnavailable):
        return None
    if data is None:  # HTTP 404 (responseCode 100) is how the Handle API says "not found"
        return False
    code = data.get("responseCode")
    # 1 = found; 200 = handle exists but has no values of the queried type; 100 = not found.
    return True if code in (1, 200) else False if code == 100 else None


# --------------------------------------------------------------------------- #
# Verdict engine                                                              #
# --------------------------------------------------------------------------- #

VERDICTS = {
    "verified": "Entry exists; title+authors match an authoritative record.",
    "TF": "Total Fabrication — entry found in NO source.",
    "PAC": "Partial Attribute Corruption — entry found but metadata fields disagree.",
    "IH": "Identifier Hijacking — DOI/arXiv ID resolves to an unrelated paper.",
    "PH": "Placeholder Hallucination — unresolved citation template/placeholder.",
    "SH": "Semantic Hallucination — resolves but claim-support unverified (advisory).",
    "unverified": "Could not verify (offline or all APIs failed); manual check required.",
}
SEVERITY = {
    "verified": "NONE",
    "TF": "SERIOUS",
    "PAC": "MEDIUM",
    "IH": "SERIOUS",
    "PH": "SERIOUS",
    "SH": "SERIOUS",
    "unverified": "MEDIUM",
}


def _is_placeholder(entry: Entry) -> bool:
    if PLACEHOLDER_RE.search(entry.raw):
        return True
    if not entry.doi and not entry.arxiv_id and len(_normalize(entry.title)) < 6 and not entry.authors:
        return True
    return False


def verify_entry(entry: Entry, mailto: str, threshold: float, offline: bool) -> dict:
    ref_id = entry.key or entry.doi or entry.arxiv_id or (entry.title[:40] or entry.raw[:40])

    # PH check first — placeholders never reach the network.
    if _is_placeholder(entry):
        return _verdict(entry, ref_id, "PH",
                        detail="Citation is an unresolved placeholder/template.",
                        matches=[])

    if offline:
        return _unverified(entry, ref_id, reason="offline mode requested (--offline)")

    matches: list[dict] = []
    status: dict[str, str] = {}  # source -> record | no_record | error: ... | offline
    network_failed = False
    has_identifier = bool(entry.doi or entry.arxiv_id)

    def _crossref() -> Optional[dict]:
        if entry.doi:
            rec = crossref_by_doi(entry.doi, mailto)
            # A DOI that does not resolve may still belong to a real work cited
            # with a wrong identifier; the title search lets that surface as PAC.
            return rec or (crossref_by_title(entry, mailto) if entry.title else None)
        return crossref_by_title(entry, mailto) if entry.title else None

    sources: list[tuple[str, Callable[[], Optional[dict]]]] = [
        ("crossref", _crossref),
        ("openalex", lambda: openalex_lookup(entry, mailto)),
        ("semanticscholar", lambda: semanticscholar_lookup(entry, mailto)),
        ("arxiv", lambda: arxiv_lookup(entry, mailto)),
    ]
    for name, fn in sources:
        try:
            rec = fn()
        except NetworkUnavailable:
            network_failed = True
            status[name] = "offline"
            break
        except SourceError as exc:
            status[name] = f"error: {exc}"
            continue
        status[name] = "record" if rec else "no_record"
        if rec:
            matches.append(rec)

    def answered(name: str) -> bool:
        return status.get(name) in ("record", "no_record")

    # An arXiv ID that no source resolved: settle existence on arxiv.org/abs, and
    # retry the query API once if the ID is real (its feed is sometimes empty).
    arxiv_exists: Optional[bool] = None
    if entry.arxiv_id and not network_failed and not any(m.get("method") == "id" for m in matches):
        arxiv_exists = arxiv_id_exists(entry.arxiv_id, mailto)
        status["arxiv.org/abs"] = {True: "exists", False: "not_found", None: "error"}[arxiv_exists]
        if arxiv_exists:
            try:
                rec = arxiv_lookup(entry, mailto)
            except (SourceError, NetworkUnavailable):
                rec = None
            if rec:
                matches.append(rec)
                status["arxiv"] = "record"

    if network_failed and not matches:
        return _unverified(entry, ref_id, reason="network unavailable (DNS/connection failure)",
                           status=status)
    if not any(answered(s) for s in status):
        return _unverified(entry, ref_id,
                           reason="every source failed to answer (rate limits / server errors)",
                           status=status)

    id_matches = [m for m in matches if m.get("method") == "id"]
    title_matches = [m for m in matches if m.get("method") == "title"]

    def r_of(m: dict) -> float:
        return title_ratio(entry.title, m["title"]) if entry.title and m.get("title") else 0.0

    # Identifier Hijacking: the cited DOI/arXiv id actually RESOLVED (method=id),
    # but the resolved record's title does not match the cited title.
    # This must be checked against id-resolved records only — a coincidental
    # title-search hit on a fabricated DOI is NOT hijacking, it is fabrication.
    if has_identifier and entry.title and id_matches:
        best_id = max(id_matches, key=r_of)
        if best_id["title"]:
            r = r_of(best_id)
            if r < threshold:
                return _verdict(entry, ref_id, "IH",
                                detail=(f"Cited identifier resolved to '{best_id['title']}' "
                                        f"(title ratio {r:.2f} < {threshold:.2f}) — unrelated paper."),
                                matches=matches, status=status)

    pac_reasons: list[str] = []

    # The cited identifier resolved nowhere. Decide TF only on authoritative
    # evidence: doi.org says the DOI is unregistered, or arXiv says the ID does
    # not exist. A registered DOI that no index returned, or an identifier whose
    # authoritative source errored, is `unverified` (manual check), never TF.
    if has_identifier and not id_matches:
        best_loose = max(title_matches, key=r_of, default=None) if entry.title else None
        loose_ok = bool(best_loose and r_of(best_loose) >= threshold)
        if loose_ok:
            pac_reasons.append(
                "cited identifier does not resolve to this work"
                + (f" (records list DOI {best_loose['doi']})" if best_loose.get("doi") else ""))
        else:
            if entry.doi:
                registered = doi_registered(entry.doi, mailto)
                status["doi.org"] = {True: "registered", False: "not_registered", None: "error"}[registered]
                if registered is False:
                    return _verdict(entry, ref_id, "TF",
                                    detail=(f"DOI {entry.doi} is not registered with any DOI agency "
                                            "(doi.org Handle API) and no close title match was found "
                                            "— entry appears fabricated."),
                                    matches=matches, status=status)
                why = ("DOI is registered at doi.org but no metadata source returned it "
                       "(non-Crossref DOI or index gap)" if registered
                       else "the cited DOI did not resolve and doi.org could not be reached")
                return _unverified(entry, ref_id, reason=why, status=status, matches=matches)
            if arxiv_exists is False:
                return _verdict(entry, ref_id, "TF",
                                detail=(f"arXiv ID {entry.arxiv_id} does not exist (arxiv.org/abs "
                                        "returns 404) and no close title match was found — entry "
                                        "appears fabricated."),
                                matches=matches, status=status)
            why = ("the arXiv ID exists but its record could not be retrieved" if arxiv_exists
                   else "arXiv could not be reached to resolve the cited ID")
            return _unverified(entry, ref_id, reason=why, status=status, matches=matches)

    # Which returned record is the cited work? Rank by title, then authors, then
    # year. A fuzzy search always returns its closest hit, so a hit only counts as
    # "found" when the title matches — and a same-titled record by entirely
    # different authors is a different work unless the titles are near-identical.
    pool = id_matches or matches  # a resolved identifier anchors the comparison
    best = max(pool, key=lambda m: _rank(entry, m)) if pool else None
    t_ratio = r_of(best) if (best and entry.title) else (1.0 if best else 0.0)
    a_overlap = author_overlap(entry.authors, best["authors"]) if best else None
    found = best is not None and t_ratio >= threshold and not (a_overlap == 0.0 and t_ratio < 0.95)
    if not has_identifier and not found:
        # Garbled/mashup title whose closest record shares the cited authors → PAC.
        near_mashup = (best is not None and a_overlap is not None and a_overlap >= 0.5
                       and t_ratio >= 0.5)
        if not near_mashup:
            # TF needs Crossref plus a broad index (OpenAlex or Semantic Scholar) to
            # have answered: Crossref alone misses books and grey literature.
            if answered("crossref") and (answered("openalex") or answered("semanticscholar")):
                closest = (f" Closest record: '{best['title']}' (title ratio {t_ratio:.2f})."
                           if best else "")
                return _verdict(entry, ref_id, "TF",
                                detail=("No source returned a record matching the cited title and "
                                        "authors — entry appears fabricated." + closest),
                                matches=matches, status=status)
            limited = [f"{src} {'rate-limited (HTTP 429)' if '429' in st else 'failed'}"
                       for src, st in status.items()
                       if src in ("openalex", "semanticscholar") and st.startswith("error")]
            return _unverified(entry, ref_id,
                               reason=("no matching record in the sources that answered, and "
                                       "OpenAlex / Semantic Scholar could not be queried to rule "
                                       "out books or grey literature"
                                       + (" (" + ", ".join(limited) + "; see summary.notes)"
                                          if limited else "")),
                               status=status, matches=matches)
        pac_reasons.append(f"title ratio {t_ratio:.2f} < {threshold:.2f} but the closest record "
                           f"shares the cited authors — possible mashup of real references")

    def same_work(m: dict) -> bool:
        if m is best or m.get("method") == "id":
            return True  # id matches already passed the IH title check
        return r_of(m) >= threshold and author_overlap(entry.authors, m["authors"]) != 0.0

    same = [m for m in matches if same_work(m)]
    # Retraction / concern flags come only from records of the cited work itself,
    # never from an unrelated closest hit.
    retracted = any(m.get("retracted") for m in same)
    concern = any(m.get("concern") for m in same)

    # Metadata corruption checks (PAC): year, authors.
    years = {y for m in same for y in (m.get("years") or [m.get("year")]) if y}
    if entry.year and years and entry.year not in years:
        pac_reasons.append(f"year cited={entry.year} vs source={'/'.join(sorted(years))}")
    if a_overlap is not None and a_overlap < 0.5:
        pac_reasons.append(f"author overlap {a_overlap:.0%} below 50%")

    verdict_code = "verified"
    detail = f"Matched in {', '.join(sorted({m['source'] for m in same}))}."
    if pac_reasons:
        verdict_code = "PAC"
        detail = "Found but metadata disagrees: " + "; ".join(pac_reasons) + "."

    result = _verdict(entry, ref_id, verdict_code, detail=detail, matches=matches, status=status)
    result["title_ratio"] = round(t_ratio, 3)
    result["author_overlap"] = round(a_overlap, 3) if a_overlap is not None else None
    result["retracted"] = retracted
    if retracted:
        result["flags"] = result.get("flags", []) + ["RETRACTED"]
        # Retraction does not change existence verdict but is a SERIOUS flag.
        result["severity"] = "SERIOUS"
        result["detail"] += (" RETRACTED: Crossref (publisher or Retraction Watch notice) and/or "
                             "OpenAlex mark this work as retracted.")
    if concern:
        result["flags"] = result.get("flags", []) + ["EXPRESSION_OF_CONCERN"]
        result["detail"] += " An expression of concern is on record for this work."
    return result


def _verdict(entry: Entry, ref_id: str, code: str, detail: str, matches: list[dict],
             status: Optional[dict] = None) -> dict:
    return {
        "ref_id": ref_id,
        "verdict": code,
        "verdict_meaning": VERDICTS[code],
        "severity": SEVERITY[code],
        "detail": detail,
        "cited": {
            "title": entry.title,
            "authors": entry.authors,
            "year": entry.year,
            "doi": entry.doi,
            "arxiv_id": entry.arxiv_id,
        },
        "sources_checked": sorted(status or {}),
        "source_status": dict(status or {}),
        "matches": [{k: m.get(k) for k in ("source", "method", "title", "year", "doi", "retracted")}
                    for m in matches],
        "flags": [],
    }


def _unverified(entry: Entry, ref_id: str, reason: str, status: Optional[dict] = None,
                matches: Optional[list[dict]] = None) -> dict:
    r = _verdict(entry, ref_id, "unverified",
                 detail=f"{reason}. NOT confirmed — do not treat as passing.",
                 matches=matches or [], status=status)
    r["manual_instructions"] = (
        "Verify manually: (1) search the exact title + first author + year on Google "
        "Scholar; (2) if a DOI is given, resolve https://doi.org/<DOI> and confirm the "
        "landing page title matches; (3) for arXiv IDs, open https://arxiv.org/abs/<id>; "
        "(4) confirm the venue, year, and author list field-by-field. Re-run this script "
        "with network access to obtain an automated verdict."
    )
    return r


# --------------------------------------------------------------------------- #
# Report assembly                                                             #
# --------------------------------------------------------------------------- #


def build_report(results: list[dict], mailto: str, threshold: float, offline: bool) -> dict:
    counts = {k: 0 for k in VERDICTS}
    sev = {"SERIOUS": 0, "MEDIUM": 0, "MINOR": 0}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        s = r["severity"]
        if s in sev:
            sev[s] += 1
    n = len(results) or 1
    fabricated = counts["TF"] + counts["IH"] + counts["PH"]
    fabrication_risk = round(fabricated / n, 3)
    integrity = round((counts["verified"]) / n, 3)

    # SERIOUS findings (TF / IH / PH / retraction) dominate; otherwise any entry that
    # could not be checked makes the run UNVERIFIED — never a (conditional) pass.
    if sev["SERIOUS"] > 0:
        verdict = "FAIL"
    elif counts["unverified"]:
        verdict = "UNVERIFIED"
    elif counts["PAC"] > 0 or sev["MEDIUM"] > 0:
        verdict = "PASS_WITH_CONDITIONS"
    else:
        verdict = "PASS"

    # Surface source failures at the top of the report, so a rate-limited index
    # is visible even when other sources carried the verdicts.
    source_errors: dict[str, int] = {}
    notes: list[str] = []
    for r in results:
        for src, st in (r.get("source_status") or {}).items():
            if isinstance(st, str) and st.startswith("error"):
                source_errors[src] = source_errors.get(src, 0) + 1
                hint = st.split("HTTP 429 — ", 1)[1] if "HTTP 429 — " in st else ""
                if hint and hint not in notes:
                    notes.append(hint)

    return {
        "tool": "alterlab-citation-verifier/verify_citations.py",
        "version": TOOL_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "config": {"mailto": mailto, "threshold": threshold, "offline": offline,
                   "http_backend": "requests" if _HAS_REQUESTS else "urllib",
                   # whether optional keys were present — never the keys themselves
                   "openalex_api_key": bool(OPENALEX_API_KEY),
                   "s2_api_key": bool(S2_API_KEY)},
        "taxonomy": VERDICTS,
        "summary": {
            "total": len(results),
            "verdict": verdict,
            "verdict_counts": counts,
            "severity_counts": sev,
            "citation_integrity_score": integrity,
            "fabrication_risk_score": fabrication_risk,
            "retracted": sum(1 for r in results if r.get("retracted")),
            "source_errors": source_errors,
            "notes": notes,
        },
        "entries": results,
    }


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #


def _read_input(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    import os
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    return path  # treat the argument itself as inline text


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Verify that bibliography entries exist via public scholarly APIs.")
    ap.add_argument("input", help="Path to a .bib/.txt file, '-' for stdin, or inline text.")
    ap.add_argument("--format", choices=["auto", "bibtex", "doi", "freeform"], default="auto")
    ap.add_argument("--mailto", default=DEFAULT_MAILTO, help="Polite-pool contact email.")
    ap.add_argument("--threshold", type=float, default=0.70, help="Fuzzy title-match ratio (0..1).")
    ap.add_argument("--out", default=None, help="Write JSON report to this path (default stdout).")
    ap.add_argument("--offline", action="store_true", help="Skip the network; emit 'unverified' verdicts.")
    args = ap.parse_args(argv)

    text = _read_input(args.input)
    try:
        entries = parse_bibliography(text, args.format)
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not parse bibliography: {exc}", file=sys.stderr)
        return 2
    if not entries:
        print("error: no bibliography entries parsed from input.", file=sys.stderr)
        return 2

    results = [verify_entry(e, args.mailto, args.threshold, args.offline) for e in entries]
    report = build_report(results, args.mailto, args.threshold, args.offline)
    out = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(out + "\n")
        print(f"wrote {report['summary']['total']} verdicts → {args.out} "
              f"(verdict={report['summary']['verdict']})", file=sys.stderr)
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
