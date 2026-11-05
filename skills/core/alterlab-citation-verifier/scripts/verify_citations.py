#!/usr/bin/env python3
"""verify_citations.py — Existence-verify a bibliography against public scholarly APIs.

Given a bibliography (BibTeX, a list of DOIs/arXiv IDs, or free-form references),
this checks whether each entry ACTUALLY EXISTS by querying public scholarly indexes
(Crossref, Semantic Scholar, Europe PMC, arXiv, and Open Library for books), plus the
doi.org Handle API to confirm whether a cited DOI is registered at all. It resolves DOI / arXiv
identifiers, fuzzy-matches title and authors (difflib SequenceMatcher ratio —
Ratcliff/Obershelp, not edit-distance — default threshold 0.70), flags retractions
(Crossref ``updated-by`` / ``update-to`` records, which since 2025 include the
Retraction Watch database), and emits a JSON verdict per entry.

Report schema 2 (tool 2.0.0) answers four questions separately for every entry:
  existence   found | identifier_mismatch | identifier_invalid | not_found | not_determined |
              unavailable | placeholder | not_checked  (+ which sources answered / failed)
  identifier  per DOI and arXiv ID: resolves_to_cited_work | resolves_to_other_work |
              does_not_resolve_to_cited_work | unregistered | registered_unindexed | malformed |
              not_found | not_cited | unknown
  metadata    title / authors / year: agrees | disagrees | not_checked (nothing cited) |
              unknown (the record lacks the field). A cited author the record does not support is
              listed in metadata.authors.unsupported; "et al." / "and others" is honoured.
  retraction  flagged | not_flagged_in_checked_sources | unknown, with sources_answered and
              checked_at. ``retracted`` (v1 key) is true / false / null (null = unknown).

Design constraints:
- NO API key required. The optional ``S2_API_KEY`` only gives Semantic Scholar a
  dedicated rate limit instead of the shared keyless pool; it is sent as a header,
  never logged. (OpenAlex was removed in v1.3.0: its keyless searches now draw on a
  small per-IP daily budget, so real use needed an account.)
- Semantic Scholar's keyless pool is shared by every unauthenticated caller and often
  answers HTTP 429 — its *search* endpoint almost always does from busy networks, while
  DOI / arXiv-ID lookups mostly answer. The script backs off and, if the pool is still
  busy, records Semantic Scholar as *not checked* for that entry and pauses that endpoint
  (search and lookups separately) for the rest of the run. A rate-limited source is
  never read as "not found", and no verdict depends on Semantic Scholar search: a Total
  Fabrication without an identifier needs Crossref plus at least one other index that
  actually answered (Semantic Scholar, Europe PMC, arXiv or Open Library) before an entry
  is reported NOT_FOUND — and NOT_FOUND is never reported as fabrication.
- NO third-party deps required: uses ``requests`` if present, else the stdlib
  (``urllib``). Mirrors the integrity_verification_agent taxonomy exactly (see
  ../SKILL.md and ../../alterlab-research-pipeline/agents/integrity_verification_agent.md).
- GRACEFUL DEGRADATION: with no network, or when every source errors (rate limits,
  5xx), the entry gets an ``unverified`` verdict plus manual-verification
  instructions. It never silently passes an entry. One unreachable host is recorded as
  not checked and the remaining sources are still asked (the host is then paused for
  HOST_DOWN_PAUSE seconds so it does not stall every entry).

Verdict codes (``verdict``; the canonical Five-Type Taxonomy plus two v2 codes):
  verified    found; every supplied field that could be checked agrees
  PAC         Partial Attribute Corruption — found, but ≥1 supplied field disagrees
              (an unsupported author, wrong year, an identifier that points elsewhere)
  IH          Identifier Hijacking — DOI/arXiv ID resolves to an unrelated paper
  ID_INVALID  the cited DOI is unregistered / arXiv ID does not exist and no title match was
              found: the identifier is wrong; whether the work exists is undetermined
  NOT_FOUND   no source that answered holds a matching record. Absence from indexes is NOT
              evidence of fabrication (books, grey literature, regional venues); check manually
  PH          Placeholder Hallucination — an unresolved template/placeholder
  TF          Total Fabrication — reserved for an analyst's conclusion after a documented
              manual search; this script never emits it (v1 emitted it for index absence)
  SH          Semantic Hallucination — advisory; claim support is out of scope here
  unverified  could not be decided (offline, sources failed, too little structure)
Run verdict (``summary.verdict``): FAIL > PARTIAL > REVIEW_REQUIRED (a NOT_FOUND entry) >
UNVERIFIED > PASS_WITH_CONDITIONS > PASS.

Usage:
  uv run python verify_citations.py INPUT [--format auto|bibtex|doi|freeform]
                                          [--mailto you@example.com]
                                          [--threshold 0.70]
                                          [--out report.json] [--offline]
  uv run python verify_citations.py - < refs.bib        # read stdin

Optional environment: S2_API_KEY (Semantic Scholar, x-api-key header: raises its shared
keyless rate limit);
ALTERLAB_CONTACT_EMAIL (opt-in contact address for Crossref's polite pool).
A rate-limited source (HTTP 429) is reported in ``source_status`` and
``summary.notes`` as not checked; it never counts as "not found".

Input formats (``--format auto`` detects them, and a mixed file is handled piecewise):
- BibTeX / BibLaTeX: a dependency-free, brace-depth-aware tokenizer. Single-line and
  multiline entries, any closing-brace indentation, nested braces, quoted values
  (braces and ``{\\"o}`` inside), ``@type(...)`` entries, several entries per line,
  trailing commas, case-insensitive types and field names. ``@string`` macros and
  ``#`` concatenation are expanded (plus the standard ``jan``..``dec`` month macros);
  ``@comment`` / ``@preamble`` / ``@string`` / ``@set`` / ``@xdata`` blocks are
  skipped as non-references and listed. LaTeX accents pass through unchanged and are
  folded to Unicode only when titles and surnames are compared.
- A bare DOI / arXiv-ID list (one per line, ``#`` comments).
- Free-form references (APA-style lines, numbered lists, blank-line-separated blocks).
  In ``auto`` mode, reference-like text outside BibTeX entries is verified as free-form.
- Text that is not a reference is skipped, never checked: Markdown headings, prose
  paragraphs, and text with no year, identifier (DOI / arXiv / ISBN / URL) or author
  name (see ``not_a_reference``). It is listed in ``input_accounting.ignored_text`` as
  "skipped: not a reference", counted in ``ignored_text_segments``, and gets no verdict.
  As a second safety net a free-form entry is TF only with a title plus an author or year.

Input accounting: every detected entry ends up in exactly one bucket. It is either
*parsed* (and then verified, unverified, or flagged), *rejected* (malformed, with a
line number, the key if any, and the reason: unbalanced braces, missing citation key,
missing comma, unterminated quote, an undefined macro in a field the check needs, or
stray field text outside an entry), or *unsupported* (well-formed but not handled,
with the reason, e.g. an unknown ``@type``). The JSON report carries a top-level
``status`` ("complete" | "partial"), a ``warning`` banner, ``summary.input`` counts,
and an ``input_accounting`` object with every diagnostic. A run where any entry was
rejected, unsupported, or left unprocessed can never return PASS or
PASS_WITH_CONDITIONS: its ``summary.verdict`` is PARTIAL (or FAIL when a SERIOUS
finding dominates), and a warning banner is printed to stderr ahead of the report.

Exit codes:
  0  complete audit: every detected entry was parsed and got a verdict; read
     ``summary.verdict`` (PASS / PASS_WITH_CONDITIONS / FAIL / UNVERIFIED).
  2  bad input or usage: unreadable input, unknown option, or no entry could be
     parsed (when entries were detected but all were rejected or unsupported, the
     report is still written so the diagnostics are available).
  3  partial audit: the report was written, but at least one detected entry was
     rejected, unsupported, or left unprocessed (``status`` = "partial"). Fix the
     input using ``input_accounting`` and re-run before relying on the verdict.
"""

from __future__ import annotations

import argparse
import bisect
import json
import os
import re
import socket
import sys
import time
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any, Callable, Optional, Sequence

# --------------------------------------------------------------------------- #
# HTTP layer — prefer requests, fall back to urllib (stdlib). Keys optional.  #
# --------------------------------------------------------------------------- #

TOOL_VERSION = "2.0.0"
REPORT_SCHEMA_VERSION = 2
# Contact email for Crossref's polite pool: opt-in (--mailto or ALTERLAB_CONTACT_EMAIL). With
# none, requests carry no address and use the public pool; no default address is ever sent.
DEFAULT_MAILTO = os.environ.get("ALTERLAB_CONTACT_EMAIL", "").strip()
USER_AGENT = (
    "alterlab-citation-verifier/" + TOOL_VERSION + " (https://github.com/AlterLab-IEU/"
    "AlterLab-Academic-Skills{contact})"
)


def _user_agent(mailto: str) -> str:
    return USER_AGENT.format(contact=f"; mailto:{mailto}" if mailto else "")


def _mailto_param(mailto: str, sep: str) -> str:
    """``sep + 'mailto=...'`` when a contact email was given, else ''."""
    return f"{sep}mailto={urllib.parse.quote(mailto)}" if mailto else ""
HTTP_TIMEOUT = 15
RETRIES = 2
BACKOFF = 1.5
# A 429 asking us to wait longer than this (an exhausted daily quota can return a
# Retry-After of many hours) is reported as a source error, not retried.
MAX_RETRY_AFTER = 30

# Optional credential — never required; it only raises Semantic Scholar's rate limit.
S2_API_KEY = (os.environ.get("S2_API_KEY") or os.environ.get("SEMANTIC_SCHOLAR_API_KEY") or "").strip()

# Minimum spacing between calls to one host. arXiv's API terms ask for >= 3 s
# between calls; Semantic Scholar's key tier is 1 request/second; Crossref's public
# pool allows 5 requests/s with one in flight (checked 2026-11-02).
MIN_INTERVAL = {"export.arxiv.org": 3.0, "arxiv.org": 3.0, "api.semanticscholar.org": 1.0,
                "api.crossref.org": 0.25, "openlibrary.org": 1.0, "www.ebi.ac.uk": 0.1}
_LAST_CALL: dict[str, float] = {}

# Retry policy for HTTP 429 / 5xx per rate-limit key (a host, or host + "/search" for
# Semantic Scholar search): (retries, base backoff in seconds), doubling per attempt.
# Semantic Scholar's keyless pool is shared by every unauthenticated caller and sends no
# Retry-After, so lookups get the longest backoff (2 + 4 + 8 s). Its search pool is
# usually spent from busy networks (checked 2026-11-02: 429 on every try for minutes), so
# search gets one retry and then a long pause. Crossref's public pool answers 429
# whenever a second request from the same IP is in flight.
RETRY_POLICY = {"api.semanticscholar.org": (3, 2.0), "api.semanticscholar.org/search": (1, 2.0),
                "api.crossref.org": (3, 1.0)}
# After a key's retries are spent on HTTP 429, calls to it fail fast for this long (s),
# so one busy shared pool cannot stall a long bibliography. Each skipped call is
# reported as rate-limited (not checked), never as "not found".
# A host that refused connections or failed DNS is skipped (reported as not checked) for this
# long, so one unreachable index neither stops the other sources nor stalls every entry.
HOST_DOWN_PAUSE = 60.0
RATE_LIMIT_COOLDOWN = {"api.semanticscholar.org": 30.0, "api.semanticscholar.org/search": 300.0}
_COOLDOWN_UNTIL: dict[str, float] = {}


def _rate_key(url: str) -> str:
    """Rate-limit bucket for a URL: its host, with Semantic Scholar search kept separate
    from its lookups (they are limited separately, and search is far more often refused)."""
    parts = urllib.parse.urlsplit(url)
    host = parts.hostname or ""
    if host == "api.semanticscholar.org" and parts.path.rstrip("/").endswith("/search"):
        return host + "/search"
    return host

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
    "api.semanticscholar.org": ("Semantic Scholar rate limit: not checked (which is not 'not found'); "
                                "the keyless pool is shared by all unauthenticated users, so retry "
                                "later or set the optional S2_API_KEY"),
    "api.crossref.org": ("Crossref rate limit: not checked; slow down (public pool 5 req/s with one "
                         "request in flight; polite pool with --mailto 10 req/s)"),
    "www.ebi.ac.uk": "Europe PMC rate limit: not checked; retry later",
    "openlibrary.org": "Open Library rate limit: not checked; retry later",
}


def _http_get(url: str, mailto: str, accept: str = "application/json",
              extra_headers: Optional[dict] = None) -> Any:
    """GET ``url`` and parse JSON (or return raw text for XML endpoints).

    Returns None when the API answered "not found / no match" (404, other 4xx).
    Raises SourceError when the API could not answer (429/5xx after retries,
    401/403, timeout) and NetworkUnavailable on a DNS/connection failure, so the
    caller can tell "offline" and "this source failed" apart from "not found".

    HTTP 429 / 5xx are retried with backoff (``RETRY_POLICY`` per host, honouring a short
    ``Retry-After``). A host listed in ``RATE_LIMIT_COOLDOWN`` that is still answering
    429 once its retries are spent fails fast for a while, with the same rate-limit
    SourceError, so the entry records that source as not checked.
    """
    host = urllib.parse.urlsplit(url).hostname or ""
    key = _rate_key(url)
    if time.monotonic() < _COOLDOWN_UNTIL.get("down:" + host, 0.0):
        raise NetworkUnavailable(f"{host} was unreachable earlier in this run; not retried for "
                                 f"{HOST_DOWN_PAUSE:.0f} s (other sources are still asked)")
    if time.monotonic() < _COOLDOWN_UNTIL.get(key, 0.0):
        raise SourceError("HTTP 429 — " + _RATE_LIMIT_HINTS.get(host, "rate limited; retry later"))
    retries, base = RETRY_POLICY.get(key, (RETRIES, BACKOFF))
    headers = {"User-Agent": _user_agent(mailto), "Accept": accept}
    headers.update(extra_headers or {})
    last_exc: Optional[Exception] = None
    wait_hint = 0.0  # a short Retry-After the server asked for
    reset_retried = False  # one connection reset is retried before "offline" is concluded
    for attempt in range(retries + 1):
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
            wait_hint = exc.retry_after
        except urllib.error.HTTPError as exc:  # urllib path
            if exc.code == 429 or 500 <= exc.code < 600:
                last_exc = exc
                wait_hint = _retry_after(exc.headers.get("Retry-After") if exc.headers else None)
                if wait_hint > MAX_RETRY_AFTER:
                    break
            elif exc.code in (401, 403):
                raise SourceError(f"HTTP {exc.code} (access denied)") from exc
            else:
                return None  # 404 and other 4xx → "no match"
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, (socket.timeout, TimeoutError)):
                last_exc = exc  # slow source, not an offline machine
            elif reset_retried or attempt >= retries:
                _COOLDOWN_UNTIL["down:" + host] = time.monotonic() + HOST_DOWN_PAUSE
                raise NetworkUnavailable(str(exc.reason)) from exc  # DNS / no route
            else:
                reset_retried, last_exc = True, exc  # a dropped connection: try once more
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
                if reset_retried or attempt >= retries:
                    _COOLDOWN_UNTIL["down:" + host] = time.monotonic() + HOST_DOWN_PAUSE
                    raise NetworkUnavailable(str(exc)) from exc
                reset_retried, last_exc = True, exc
            else:
                last_exc = exc
        if attempt < retries:
            delay = base * (2 ** attempt) if key in RETRY_POLICY else BACKOFF * (attempt + 1)
            time.sleep(max(delay, wait_hint))
    code = getattr(last_exc, "status", None) or getattr(last_exc, "code", None)
    if code == 429:
        if key in RATE_LIMIT_COOLDOWN:
            _COOLDOWN_UNTIL[key] = time.monotonic() + RATE_LIMIT_COOLDOWN[key]
        raise SourceError("HTTP 429 — " + _RATE_LIMIT_HINTS.get(host, "rate limited; retry later"))
    raise SourceError(f"no answer after retries ({last_exc})")


# --------------------------------------------------------------------------- #
# Fuzzy matching                                                              #
# --------------------------------------------------------------------------- #

_WS = re.compile(r"\s+")
_NONWORD = re.compile(r"[^\w\s]")

# LaTeX accent commands -> Unicode combining marks, so a BibTeX surname such as
# M{\"u}ller compares equal to the "Müller" an API returns. Used only for comparison;
# the cited values themselves are passed through unchanged.
_TEX_ACCENT_MARKS = {
    '"': "\u0308", "'": "\u0301", "`": "\u0300", "^": "\u0302", "~": "\u0303", "=": "\u0304",
    ".": "\u0307", "u": "\u0306", "v": "\u030c", "H": "\u030b", "c": "\u0327", "k": "\u0328",
    "r": "\u030a", "d": "\u0323", "b": "\u0331",
}
_TEX_SPECIAL_LETTERS = {
    "ss": "ß", "aa": "å", "AA": "Å", "ae": "æ", "AE": "Æ", "oe": "œ", "OE": "Œ",
    "o": "ø", "O": "Ø", "l": "ł", "L": "Ł",
}
_TEX_DOTLESS_RE = re.compile(r"\\([ij])(?![A-Za-z])")
_TEX_SYMBOL_ACCENT_RE = re.compile(r"\\([\"'`^~=.])\s*(?:\{\s*([A-Za-z])\s*\}|([A-Za-z]))")
_TEX_LETTER_ACCENT_RE = re.compile(r"\\([uvHckrdb])(?:\s*\{\s*([A-Za-z])\s*\}|\s+([A-Za-z])(?![A-Za-z]))")
_TEX_SPECIAL_RE = re.compile(r"\\(ss|aa|AA|ae|AE|oe|OE|o|O|l|L)(?![A-Za-z])")


def _fold_latex(text: str) -> str:
    """Best-effort LaTeX accent/special-letter folding to NFC Unicode (comparison only)."""
    def accent(m: re.Match) -> str:
        return (m.group(2) or m.group(3)) + _TEX_ACCENT_MARKS[m.group(1)]

    text = _TEX_DOTLESS_RE.sub(r"\1", text)
    text = _TEX_SYMBOL_ACCENT_RE.sub(accent, text)
    text = _TEX_LETTER_ACCENT_RE.sub(accent, text)
    text = _TEX_SPECIAL_RE.sub(lambda m: _TEX_SPECIAL_LETTERS[m.group(1)], text)
    return unicodedata.normalize("NFC", text)


def _normalize(text: str) -> str:
    text = text or ""
    if "\\" in text:
        text = _fold_latex(text)
    # BibTeX grouping braces ("{DNA}", "M{\"u}ller") are not word boundaries.
    text = text.replace("{", "").replace("}", "").lower().strip()
    text = _NONWORD.sub(" ", text)
    return _WS.sub(" ", text).strip()


def title_ratio(a: str, b: str) -> float:
    """Similarity ratio (0..1) via difflib SequenceMatcher on normalized titles.

    Some records drop the subtitle (Semantic Scholar and arXiv often store only
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


# --- Author names ------------------------------------------------------------
# Surnames are compared token by token after normalisation, never by substring: "Li" must
# not match "Williams". Accepted variants are explicit and listed here:
#   * case, Unicode composition, accents and LaTeX accent commands (Müller = Muller);
#   * the German umlaut transliteration (Müller = Mueller) and a few letters NFKD does not
#     decompose (ı ø ł đ æ œ ß);
#   * apostrophes dropped (O'Brien = OBrien); hyphens and spaces equivalent;
#   * surname particles (van, de, al, ...) are optional, and a compound surname matches one
#     of its parts (García Márquez ~ Márquez), because indexes often store only the last word;
#   * organisations match by full name, by acronym (WHO = World Health Organization), or by
#     near-identical word sets — never by sharing one generic word ("Organization").
_PARTICLES = frozenset("van von der den de del della degli da das dos du di la le les ter ten "
                       "bin ibn al el st".split())
_NAME_LETTERS = str.maketrans({"ı": "i", "ø": "o", "Ø": "O", "ł": "l", "Ł": "L", "đ": "d", "Đ": "D",
                               "ð": "d", "þ": "th", "æ": "ae", "Æ": "AE", "œ": "oe", "Œ": "OE",
                               "ß": "ss"})
_GERMAN_UMLAUTS = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue"})
_ORG_WORDS_RE = re.compile(
    r"(?i)\b(?:organi[sz]ation|association|society|institute|institution|ministry|committee|"
    r"council|consortium|collaboration|agency|university|office|bureau|department|foundation|"
    r"commission|group|network|centre|center|board|federation|union|bank|programme|program|"
    r"administration|authority|team|working party|task force)\b")
_ACRONYM_RE = re.compile(r"^[A-Z][A-Z&]{1,9}$")
_ORG_STOP = frozenset("of for and the on in at to".split())


def _strip_marks(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def _name_folds(text: str) -> set[str]:
    """Normalised spellings of one name (comparison only): accents folded, and with the German
    umlaut transliteration applied — so 'Müller' yields {'muller', 'mueller'}."""
    t = text or ""
    if "\\" in t:
        t = _fold_latex(t)
    t = unicodedata.normalize("NFC", t.replace("{", "").replace("}", ""))
    out = set()
    for variant in (t, t.translate(_GERMAN_UMLAUTS)):
        v = _strip_marks(variant.translate(_NAME_LETTERS)).casefold()
        v = re.sub(r"['’`´]", "", v)
        v = _WS.sub(" ", re.sub(r"[\W_]+", " ", v)).strip()
        if v:
            out.add(v)
    return out


def _is_org_name(name: str) -> bool:
    n = (name or "").strip()
    return bool(_ORG_WORDS_RE.search(n) or _ACRONYM_RE.match(n))


def _surname_of(name: str) -> str:
    """The surname part of one cited or indexed name, unnormalised.

    'Last, First' -> Last; 'Roediger HL' (Vancouver) -> Roediger; 'J. D. van der Waals' ->
    van der Waals; 'Ludwig van Beethoven' -> van Beethoven; an organisation -> its full name.
    """
    name = _WS.sub(" ", (name or "").strip(" ,;"))
    if not name:
        return ""
    if _is_org_name(name):
        return name
    if "," in name:
        return name.split(",", 1)[0].strip()
    tokens = name.split()
    if len(tokens) > 1 and _is_initials(tokens[-1]):          # "Roediger HL"
        while len(tokens) > 1 and _is_initials(tokens[-1]):
            tokens.pop()
        return " ".join(tokens)
    while len(tokens) > 1 and _is_initials(tokens[0]):         # "J. D. Smith"
        tokens.pop(0)
    i = len(tokens) - 1
    while i > 0 and tokens[i - 1].lower() in _PARTICLES:       # keep "van der"
        i -= 1
    return " ".join(tokens[i:])


def _surname(name: str) -> str:
    """Normalised surname, as used in search queries (lower case, punctuation removed)."""
    return _normalize(_surname_of(name))


def _acronym(tokens: list[str]) -> str:
    return "".join(t[0] for t in tokens if t and t not in _ORG_STOP)


def names_match(cited_surname: str, found_surname: str) -> bool:
    """True when two surnames (or organisation names) denote the same author under the
    explicit variants above. Never a substring test."""
    org = _is_org_name(cited_surname) or _is_org_name(found_surname)
    for a in _name_folds(cited_surname):
        for b in _name_folds(found_surname):
            if a == b or a.replace(" ", "") == b.replace(" ", ""):
                return True
            ta, tb = a.split(), b.split()
            if org:
                if _acronym(ta) == b.replace(" ", "") or _acronym(tb) == a.replace(" ", ""):
                    return True
                sa, sb = set(ta) - _ORG_STOP, set(tb) - _ORG_STOP
                if sa and sb and len(sa & sb) / len(sa | sb) >= 0.8:
                    return True
                continue
            ca = {t for t in ta if t not in _PARTICLES} or set(ta)
            cb = {t for t in tb if t not in _PARTICLES} or set(tb)
            if ca and cb and (ca <= cb or cb <= ca):
                return True
    return False


def author_support(cited: Sequence[str], found_surnames: Sequence[str]) -> tuple[list[str], list[str]]:
    """Split the cited authors into (supported, unsupported) by the record's surnames."""
    found = [s for s in found_surnames if s and s.strip()]
    supported, unsupported = [], []
    for a in cited:
        if not a.strip():
            continue
        sn = _surname_of(a)
        (supported if any(names_match(sn, f) for f in found) else unsupported).append(a)
    return supported, unsupported


def author_overlap(cited: list[str], found_surnames: list[str]) -> Optional[float]:
    """Fraction of cited authors whose surname the record's author list supports.

    None when either side has no author list: the record can neither confirm nor
    disprove the cited authors, which is different from a 0% overlap.
    """
    names = [a for a in cited if a.strip()]
    if not names or not any(s and s.strip() for s in found_surnames):
        return None
    supported, _ = author_support(names, found_surnames)
    return len(supported) / len(names)


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
    # The cited author list is explicitly abbreviated ("et al.", BibTeX "and others", or a
    # free-form list cut at six names), so record authors missing from it are not an error.
    authors_et_al: bool = False
    # A DOI-like string that is not a valid DOI (e.g. "10.12/x"); the identifier is malformed.
    doi_malformed: str = ""
    # Provenance, for input accounting and diagnostics.
    fmt: str = ""            # "bibtex" | "doi" | "freeform"
    line: int = 0            # 1-based line where the entry starts (0 = unknown)
    entry_type: str = ""     # lower-cased BibTeX entry type ("article", ...)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ParseResult:
    """Everything the parser found in one input.

    Every detected entry lands in exactly one of ``entries`` (parsed), ``rejected``
    (malformed) or ``unsupported`` (well-formed but not handled), so
    ``detected == len(entries) + len(rejected) + len(unsupported)``. Non-reference
    BibTeX blocks (``skipped``) and prose that is not a reference (``ignored_text``)
    are listed for transparency but are not entries.
    """

    format_requested: str = "auto"
    format_detected: str = ""
    entries: list[Entry] = field(default_factory=list)
    rejected: list[dict] = field(default_factory=list)
    unsupported: list[dict] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)
    ignored_text: list[dict] = field(default_factory=list)
    warnings: list[dict] = field(default_factory=list)

    @property
    def detected(self) -> int:
        return len(self.entries) + len(self.rejected) + len(self.unsupported)

    @property
    def complete(self) -> bool:
        return not (self.rejected or self.unsupported)


def _excerpt(text: str, limit: int = 100) -> str:
    text = _WS.sub(" ", text or "").strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _diag(fmt: str, line: int, reason: str, *, key: str = "", entry_type: str = "",
          end_line: int = 0, error_line: int = 0, excerpt: str = "") -> dict:
    """One machine-readable diagnostic for a rejected / unsupported entry or a warning."""
    return {
        "format": fmt,
        "line": line,
        "end_line": max(end_line, line),
        "error_line": error_line or line,
        "key": key or None,
        "entry_type": entry_type or None,
        "reason": reason,
        "excerpt": _excerpt(excerpt),
    }


class _LineIndex:
    """Offset -> 1-based line number."""

    def __init__(self, text: str) -> None:
        self._nl = [m.start() for m in re.finditer("\n", text)]

    def __call__(self, pos: int) -> int:
        return bisect.bisect_left(self._nl, pos) + 1


def _first_doi(text: str) -> str:
    m = DOI_RE.search(text or "")
    return m.group(0).rstrip(".,;") if m else ""


_DOI_LIKE_RE = re.compile(r"(?i)(?:\bdoi\s*:?\s*|doi\.org/)(10\.[^\s,;]*)")


def _malformed_doi(text: str) -> str:
    """A DOI-like string ('doi: 10.12/x', 'doi.org/10.x') that is not a valid DOI, else ''."""
    m = _DOI_LIKE_RE.search(text or "")
    return m.group(1).rstrip(".") if m and not DOI_RE.search(m.group(1)) else ""


def _first_arxiv(text: str) -> str:
    # arXiv's own DOIs (10.48550/arXiv.<id>) name the ID; every other DOI is
    # stripped first so "10.1016/j.compedu.2020.103998" cannot yield "2020.10399".
    text = re.sub(r"10\.48550/arxiv\.", "arXiv:", text or "", flags=re.IGNORECASE)
    text = DOI_RE.sub(" ", text)
    m = ARXIV_RE.search(text)
    if not m:
        return ""
    return (m.group(1) or m.group(2) or "").strip()


# --------------------------------------------------------------------------- #
# BibTeX tokenizer — stdlib only, brace-depth and quote aware                 #
# --------------------------------------------------------------------------- #

# Citable entry types: classic BibTeX, BibLaTeX, and aliases reference managers write
# (JabRef @electronic, IEEEtran @www, @webpage, @preprint). Matched case-insensitively.
BIBTEX_REFERENCE_TYPES = frozenset({
    "article", "book", "booklet", "conference", "inbook", "incollection", "inproceedings",
    "manual", "mastersthesis", "misc", "phdthesis", "proceedings", "techreport", "unpublished",
    "artwork", "audio", "bookinbook", "collection", "commentary", "dataset", "image",
    "inreference", "jurisdiction", "legal", "legislation", "letter", "movie", "music",
    "mvbook", "mvcollection", "mvproceedings", "mvreference", "online", "patent",
    "performance", "periodical", "reference", "report", "review", "software", "standard",
    "suppbook", "suppcollection", "suppperiodical", "thesis", "video",
    "electronic", "www", "webpage", "preprint",
})
# Blocks that are not references: skipped, but listed in the input accounting.
_BIB_NON_REFERENCE = {
    "comment": "@comment block (not a reference)",
    "preamble": "@preamble block (LaTeX preamble, not a reference)",
    "string": "@string macro definition (expanded into the entries that use it)",
    "set": "@set entry set (groups other entries; each member is verified on its own)",
    "xdata": "@xdata container (fields shared by other entries; not itself a reference)",
}
_BIB_KNOWN_TYPES = BIBTEX_REFERENCE_TYPES | frozenset(_BIB_NON_REFERENCE)
# Fields the existence check relies on: an undefined @string macro in one of them
# would make the verdict rest on a macro name, so such an entry is rejected instead.
_BIB_CRITICAL_FIELDS = ("title", "author", "year", "date", "doi", "eprint")
_BIB_MONTHS = {m[:3].lower(): m for m in (
    "January", "February", "March", "April", "May", "June", "July", "August",
    "September", "October", "November", "December")}

_BIB_ENTRY_START_RE = re.compile(r"@[ \t]*([A-Za-z][\w\-]*)[ \t\r\n]*([{(]?)")
_BIB_LINE_ENTRY_RE = re.compile(r"[ \t]*@[ \t]*[A-Za-z][\w\-]*[ \t]*[{(]")
_BIB_NEXT_LINE_ENTRY_RE = re.compile(r"^[ \t]*@[ \t]*[A-Za-z][\w\-]*[ \t]*[{(]", re.MULTILINE)
_BIB_SPECIAL_RE = re.compile(r"[{}\"@\n)]")
_BIB_KEY_RE = re.compile(r"[^\s,{}()\"#=%]+")
_BIB_FIELD_RE = re.compile(r"[^\s,{}()\"#=%]+")
_BIB_NUMBER_RE = re.compile(r"[0-9]+")
_BIB_MACRO_RE = re.compile(r"[A-Za-z_][\w\-:.+/']*")
_BIB_FIELD_DEBRIS_RE = re.compile(r"(?m)^[\s,]*[A-Za-z][\w\-]*\s*=\s*[{\"\w]")
_BIB_COMMENTED_ENTRY_RE = re.compile(r"%+\s*@\s*[A-Za-z][\w\-]*\s*[{(]\s*([^\s,{}()\"#=%]*)")
_BIB_EMAILISH = frozenset("._%+-")


class _BibSyntaxError(Exception):
    def __init__(self, reason: str, pos: int, key: str = "") -> None:
        super().__init__(reason)
        self.reason = reason
        self.pos = pos
        self.key = key


@dataclass
class _BibBlock:
    entry_type: str          # as written ("ARTICLE", "Comment", ...)
    start: int               # offset of the '@'
    end: int                 # offset just past the block (where scanning resumes)
    body_start: int = 0      # offset just past the opening '{' / '('
    body_end: int = 0        # offset of the closing delimiter (end of the body)
    error: str = ""
    error_pos: int = -1

    @property
    def kind(self) -> str:
        return self.entry_type.lower()


def _bib_entry_at(text: str, at: int) -> Optional[re.Match]:
    """The '@type' match at ``at`` if it starts a BibTeX block, else None.

    '@' inside a word (an e-mail address) is ignored; '@word' without a following
    '{' / '(' counts only for known types (so "@handle" in prose is not an entry); and
    an '@' on a line that starts with '%' is a commented-out entry (listed, not parsed —
    BibTeX itself would still read it, but the author meant to exclude it).
    """
    if at > 0 and (text[at - 1].isalnum() or text[at - 1] in _BIB_EMAILISH):
        return None
    if text[text.rfind("\n", 0, at) + 1:at].lstrip().startswith("%"):
        return None
    m = _BIB_ENTRY_START_RE.match(text, at)
    if not m:
        return None
    if m.group(2) or m.group(1).lower() in _BIB_KNOWN_TYPES:
        return m
    return None


def _bib_next_line_entry(text: str, pos: int) -> int:
    """Offset of the next line (after ``pos``) that starts with '@type{' / '@type(', or EOF."""
    m = _BIB_NEXT_LINE_ENTRY_RE.search(text, pos)
    return m.start() if m else len(text)


_BIB_CLOSING_LINE_RE = re.compile(r"^[ \t]*[})][ \t]*$", re.MULTILINE)


def _bib_headerless_end(text: str, pos: int) -> int:
    """Where an '@type' with no '{' / '(' ends: past the first line holding only '}' or
    ')', or at the next '@type{' line, whichever comes first (else the end of input)."""
    nxt = _bib_next_line_entry(text, pos)
    m = _BIB_CLOSING_LINE_RE.search(text, pos, nxt)
    return m.end() if m else nxt


def _bib_find_block_end(text: str, at: int, body_start: int, etype: str, delim: str,
                        li: _LineIndex) -> _BibBlock:
    """Find where the block opened at ``at`` closes, tracking brace depth and quotes.

    Recovery: a line that starts a new '@type{' / '@type(' while this block is still
    open, or an '@type{' between fields, ends this block as malformed, so one broken
    entry cannot swallow the entries after it.
    """
    is_comment = etype.lower() == "comment"
    close = "}" if delim == "{" else ")"
    base = 1 if delim == "{" else 0
    depth, in_quote, quote_pos = base, False, -1
    first_err, first_err_pos = "", -1
    opened = li(at)

    def unclosed(where: str) -> str:
        if in_quote:
            return f"unterminated quote: the '\"' opened at line {li(quote_pos)} is never closed {where}"
        if depth > 0:  # for a '{' entry the count includes the entry's own brace
            extra = "" if delim == "{" else " (and the entry's closing ')')"
            return (f"unbalanced braces: the entry opened at line {opened} still has {depth} "
                    f"unclosed '{{'{extra} {where}")
        return f"missing closing ')' for the entry opened at line {opened} {where}"

    for m in _BIB_SPECIAL_RE.finditer(text, body_start):
        j = m.start()
        c = text[j]
        if c == "\n":
            if not is_comment and _BIB_LINE_ENTRY_RE.match(text, j + 1):
                return _BibBlock(etype, at, j + 1, body_start, j,
                                 unclosed(f"when the next entry starts at line {li(j + 1)}"),
                                 quote_pos if in_quote else at)
        elif c == '"':
            if not is_comment and depth == base and text[j - 1] != "\\":
                in_quote, quote_pos = not in_quote, j
        elif c == "{":
            depth += 1
        elif c == "}":
            if in_quote and depth == base:
                return _BibBlock(etype, at, j + 1, body_start, j,
                                 (f"unterminated quote or unbalanced '}}' inside a quoted value "
                                  f"(the '\"' opened at line {li(quote_pos)})"), quote_pos)
            depth -= 1
            if delim == "{" and depth == 0:
                return _BibBlock(etype, at, j + 1, body_start, j, first_err, first_err_pos)
            if depth < 0:  # only possible in a '(' entry
                if not first_err:
                    first_err = f"unbalanced braces: '}}' at line {li(j)} has no matching '{{'"
                    first_err_pos = j
                depth = 0
        elif c == ")":
            if delim == "(" and depth == 0 and not in_quote:
                return _BibBlock(etype, at, j + 1, body_start, j, first_err, first_err_pos)
        elif c == "@":
            if not is_comment and depth == base and not in_quote:
                nxt = _bib_entry_at(text, j)
                if nxt and nxt.group(2):
                    return _BibBlock(etype, at, j, body_start, j,
                                     (f"missing closing '{close}' before the next entry "
                                      f"'@{nxt.group(1)}' at line {li(j)}"), j)
    resume = _bib_next_line_entry(text, body_start)
    return _BibBlock(etype, at, resume, body_start, resume, unclosed("at the end of the input"),
                     quote_pos if in_quote else at)


def _scan_bibtex_blocks(text: str, li: _LineIndex) -> list[_BibBlock]:
    """Split ``text`` into BibTeX blocks (well-formed or not), in input order."""
    blocks: list[_BibBlock] = []
    n, pos = len(text), 0
    while pos < n:
        at = text.find("@", pos)
        if at < 0:
            break
        m = _bib_entry_at(text, at)
        if not m:
            pos = at + 1
            continue
        etype, delim = m.group(1), m.group(2)
        if not delim:
            if etype.lower() == "comment":  # "@comment text": BibTeX skips it like inter-entry text
                eol = text.find("\n", at)
                eol = n if eol < 0 else eol
                blocks.append(_BibBlock(etype, at, eol))
                pos = eol
                continue
            resume = _bib_headerless_end(text, m.end(1))
            blocks.append(_BibBlock(etype, at, resume, m.end(1), resume,
                                    error=f"missing '{{' or '(' after '@{etype}'",
                                    error_pos=m.end(1)))
            pos = max(resume, at + 1)
            continue
        blk = _bib_find_block_end(text, at, m.end(), etype, delim, li)
        blocks.append(blk)
        pos = max(blk.end, at + 1)
    return blocks


def _skip_ws(text: str, i: int, end: int) -> int:
    while i < end and text[i].isspace():
        i += 1
    return i


def _snippet(text: str, i: int, end: int) -> str:
    return _excerpt(text[i:min(end, i + 24)].split("\n", 1)[0], 24)


def _bib_match_brace(text: str, i: int, end: int) -> int:
    depth = 0
    for j in range(i, end):
        c = text[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return j
    return -1


def _bib_match_quote(text: str, i: int, end: int) -> int:
    """Index of the '"' closing the quote at ``i``; -1 unterminated, -2 unbalanced '}'."""
    depth = 0
    for j in range(i + 1, end):
        c = text[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth < 0:
                return -2
        elif c == '"' and depth == 0 and text[j - 1] != "\\":
            return j
    return -1


def _bib_parse_key(text: str, i: int, end: int) -> tuple[str, int]:
    """Parse the citation key; return (key, offset after the key's comma)."""
    i = _skip_ws(text, i, end)
    if i >= end:
        raise _BibSyntaxError("missing citation key: the entry is empty", i)
    if text[i] == ",":
        raise _BibSyntaxError("missing citation key: the entry starts with ','", i)
    m = _BIB_KEY_RE.match(text, i)
    if not m:
        raise _BibSyntaxError(f"missing citation key: found {_snippet(text, i, end)!r} "
                              "where the key should be", i)
    key = m.group(0)
    j = _skip_ws(text, m.end(), end)
    if j < end and text[j] == "=":
        raise _BibSyntaxError(f"missing citation key: the entry starts with the field "
                              f"'{key} = ...' (expected '@type{{key, {key} = ...')", i)
    if j >= end:
        return key, j
    if text[j] != ",":
        raise _BibSyntaxError(f"missing comma after citation key '{key}' (found "
                              f"{_snippet(text, j, end)!r}; keys cannot contain spaces)", j, key)
    return key, j + 1


def _bib_parse_value(text: str, i: int, end: int, name: str, li: _LineIndex,
                     key: str) -> tuple[list[tuple[str, str]], int]:
    """Parse ``{...}`` / ``"..."`` / number / macro parts joined by '#'."""
    parts: list[tuple[str, str]] = []
    while True:
        if i >= end or text[i] == ",":
            what = (f"dangling '#' at the end of field '{name}'" if parts
                    else f"field '{name}' has no value after '='")
            raise _BibSyntaxError(what, i, key)
        c = text[i]
        if c == "{":
            j = _bib_match_brace(text, i, end)
            if j < 0:
                raise _BibSyntaxError(f"unbalanced braces in field '{name}': the '{{' at line "
                                      f"{li(i)} is never closed", i, key)
            parts.append(("str", text[i + 1:j]))
            i = j + 1
        elif c == '"':
            j = _bib_match_quote(text, i, end)
            if j == -1:
                raise _BibSyntaxError(f"unterminated quote in field '{name}' (opened at line "
                                      f"{li(i)})", i, key)
            if j == -2:
                raise _BibSyntaxError(f"unbalanced braces inside the quoted value of field "
                                      f"'{name}' (line {li(i)})", i, key)
            parts.append(("str", text[i + 1:j]))
            i = j + 1
        elif "0" <= c <= "9":  # (not str.isdigit: "²" is a digit to Python but not a number)
            m = _BIB_NUMBER_RE.match(text, i)
            parts.append(("num", m.group(0)))
            i = m.end()
        else:
            m = _BIB_MACRO_RE.match(text, i)
            if not m:
                raise _BibSyntaxError(f"unexpected {c!r} in the value of field '{name}' at line "
                                      f"{li(i)}", i, key)
            parts.append(("macro", m.group(0)))
            i = m.end()
        j = _skip_ws(text, i, end)
        if j < end and text[j] == "#":
            i = _skip_ws(text, j + 1, end)
            continue
        return parts, i


def _bib_parse_fields(text: str, i: int, end: int, li: _LineIndex,
                      key: str = "") -> tuple[list[tuple[str, list, int]], list[str]]:
    """Parse ``name = value`` pairs separated by commas (a trailing comma is fine)."""
    fields: list[tuple[str, list, int]] = []
    warnings: list[str] = []
    while True:
        i = _skip_ws(text, i, end)
        if i >= end:
            return fields, warnings
        if text[i] == ",":
            warnings.append(f"extra ',' at line {li(i)} ignored")
            i += 1
            continue
        if text[i] == "%":  # BibTeX has no comments inside entries; skip the line, but say so
            eol = text.find("\n", i, end)
            eol = end if eol < 0 else eol
            warnings.append(f"'%' comment line inside the entry at line {li(i)} ignored")
            i = eol
            continue
        m = _BIB_FIELD_RE.match(text, i)
        if not m:
            raise _BibSyntaxError(f"expected a field name at line {li(i)}, found "
                                  f"{_snippet(text, i, end)!r}", i, key)
        name, name_pos = m.group(0), i
        i = _skip_ws(text, m.end(), end)
        if i >= end or text[i] == ",":
            raise _BibSyntaxError(f"field '{name}' at line {li(name_pos)} has no value "
                                  f"(expected '{name} = {{...}}')", name_pos, key)
        if text[i] != "=":
            raise _BibSyntaxError(f"missing '=' after field name '{name}' at line {li(name_pos)} "
                                  f"(found {_snippet(text, i, end)!r})", i, key)
        i = _skip_ws(text, i + 1, end)
        parts, i = _bib_parse_value(text, i, end, name, li, key)
        fields.append((name.lower(), parts, name_pos))
        bare_end = i
        i = _skip_ws(text, i, end)
        if i >= end:
            return fields, warnings
        if text[i] != ",":
            hint = ""
            if parts[-1][0] != "str" and i == bare_end:
                hint = (f"; only numbers and @string names may be unbraced — write "
                        f"{name} = {{...}}")
            raise _BibSyntaxError(f"missing comma after field '{name}' (found "
                                  f"{_snippet(text, i, end)!r} at line {li(i)}){hint}", i, key)
        i += 1


def _bib_resolve(parts: list[tuple[str, str]], macros: dict[str, str]) -> tuple[str, list[str]]:
    """Concatenate value parts, expanding @string macros; return (value, undefined names)."""
    out: list[str] = []
    undefined: list[str] = []
    for kind, val in parts:
        if kind == "macro":
            low = val.lower()
            if low in macros:
                val = macros[low]
            elif low in _BIB_MONTHS:
                val = _BIB_MONTHS[low]
            else:
                undefined.append(val)
        out.append(val)
    return "".join(out), undefined


def _split_bibtex_names(value: str) -> list[str]:
    """Split a BibTeX name list on 'and' at brace depth 0; drop the 'others' marker."""
    parts: list[str] = []
    depth = last = i = 0
    sep = re.compile(r"\s+and\s+", re.IGNORECASE)
    while i < len(value):
        c = value[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth = max(0, depth - 1)
        elif depth == 0 and c.isspace():
            m = sep.match(value, i)
            if m:
                parts.append(value[last:i])
                last = i = m.end()
                continue
        i += 1
    parts.append(value[last:])
    names = []
    for p in parts:
        p = _WS.sub(" ", p.replace("{", "").replace("}", "")).strip()
        if p and p.lower() != "others":
            names.append(p)
    return names


def _bibtex_entry(raw: str, body: str, key: str, kind: str, values: dict[str, str]) -> Entry:
    def g(name: str) -> str:
        return _WS.sub(" ", values.get(name, "")).strip()

    year_raw = g("year") or g("date")
    ym = re.search(r"(?:19|20)\d{2}", year_raw)
    eprint = g("eprint")
    bare_old = OLD_ARXIV_BARE_RE.match(eprint) if eprint else None
    doi = _first_doi(g("doi") or body)
    bad_doi = g("doi") if g("doi") and not _first_doi(g("doi")) else ""
    author_raw = values.get("author", "")
    entry = Entry(
        raw=raw,
        key=key,
        title=_WS.sub(" ", g("title").replace("{", "").replace("}", "")).strip(),
        authors=_split_bibtex_names(author_raw),
        authors_et_al=bool(re.search(r"(?i)\band\s+others\s*$", _WS.sub(" ", author_raw).strip())),
        doi_malformed=bad_doi if not doi else "",
        year=ym.group(0) if ym else year_raw,
        doi=doi,
        arxiv_id=bare_old.group(1) if bare_old else _first_arxiv(eprint or body),
        venue=g("journal") or g("journaltitle") or g("booktitle") or g("publisher"),
        fmt="bibtex",
        entry_type=kind,
    )
    if entry.doi_malformed:
        entry.warnings.append(f"doi field '{bad_doi}' is not a valid DOI (malformed identifier); "
                              "the entry is checked by title instead")
    return entry


_MD_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}(?:\s|$)")
_ISBN_RE = re.compile(r"(?i)\bISBN(?:-1[03])?:?\s*[0-9][0-9\s-]{8,}[0-9X]\b")
_YEAR_RE = re.compile(r"(?<!\d)(?:19|20)\d{2}(?!\d)")
# A year written the way references write it: "(2019)", "(2019a)", "(2019, May 3)", or
# "2019." / "2019," / "2019;" / "2019:" — not a year inside running text or a date.
_CITED_YEAR_RE = re.compile(r"\((?:19|20)\d{2}[a-z]?(?:,[^)]{0,30})?\)"
                            r"|(?<![\d-])(?:19|20)\d{2}[a-z]?(?=[.,;:](?:\s|$))")
# Author name shapes, looked for only in the part before the first year (where a
# reference puts its authors): "Surname, I." anywhere there; "Smith J." / "Smith JA,"
# (Vancouver); "J. Smith"; "et al".
_AUTHOR_SHAPES_RE = re.compile(
    r"[A-Z][\w'’\-]+,\s+(?:[A-Z]\.\s?){1,3}"
    r"|\b[A-Z][a-z][\w'’\-]+\s[A-Z]{1,3}[.,](?:\s|$)"
    r"|\b(?:[A-Z]\.\s?){1,3}[A-Z][a-z][\w'’\-]+"
    r"|\bet al\b")
_LIST_MARKER_RE = re.compile(r"^\s*\[?\d{1,3}[\].)]\s+")
# "compiled in 2019." — a year after a preposition is running text, not a citation year.
_RUNNING_YEAR_RE = re.compile(r"(?i)\b(?:in|since|until|till|during|from|by|before|after|of|on|"
                              r"around|circa|throughout|between|and|to)$")
_FUNCTION_WORDS = frozenset("""
a an the is are was were be been being it its this that these those and or but of to in on
for with by as at from into should may must will would can could not no when which who each
so has have had we you they our your their if then than only also more most here there such
""".split())


def _reads_as_prose(text: str) -> bool:
    """Running text rather than a citation: six or more words, at least 30% function words."""
    words = re.findall(r"[A-Za-z][A-Za-z'’\-]*", text)
    return len(words) >= 6 and sum(w.lower() in _FUNCTION_WORDS for w in words) / len(words) >= 0.3


def not_a_reference(text: str) -> Optional[str]:
    """Why ``text`` is not a reference (it is skipped, never checked), or None to check it.

    Deliberately conservative — anything that might be a reference is checked:
      * a Markdown heading ("# References") is skipped;
      * a DOI, arXiv ID, ISBN or URL, or an author name before the first year (or a
        numbered-list / "Surname, I." / "Organisation (2019)" lead), makes it a reference;
      * otherwise text with no year is skipped (no year, identifier or author name);
      * a list number alone ("1. Install the tool") is not an author name;
      * a year with no author name and no identifier is a reference when written as
        references write years ("(2019)", "Geneva: WHO; 2016.") and not after a
        preposition; otherwise it is skipped only when the text reads as prose ("The
        list was compiled in 2019 for the review"), and checked when it does not
        ("Annual Report 2019 World Health Organization").
    """
    t = _WS.sub(" ", text or "").strip()
    if not t:
        return "empty"
    if _MD_HEADING_RE.match(t):
        return "a Markdown heading"
    if (_first_doi(t) or _first_arxiv(t) or _ISBN_RE.search(t)
            or re.search(r"(?i)\bhttps?://|\bwww\.", t)):
        return None
    body = _LIST_MARKER_RE.sub("", t)  # a list number alone does not make a reference
    ym = _YEAR_RE.search(body)
    head = body[: ym.start()] if ym else body[:150]
    if _NEW_REF_LINE_RE.match(body) or _AUTHOR_SHAPES_RE.search(head[:200]):
        return None
    if not ym:
        return "no year, identifier or author name"
    cited = [m for m in _CITED_YEAR_RE.finditer(body[:200])
             if not _RUNNING_YEAR_RE.search(body[: m.start()].rstrip("( "))]
    if cited and not (len(body) > 250 and _reads_as_prose(body)):
        return None
    if _reads_as_prose(body):
        return "prose: a year, but no author name, identifier or citation-style year"
    return None


def _looks_like_reference(text: str) -> bool:
    """Heuristic: does stray text look like a citation? (see not_a_reference)"""
    return not_a_reference(text) is None


def _locate_blocks(text: str, blocks: Sequence[str], first_line: int = 1) -> list[tuple[int, str]]:
    """Pair each block from _split_references with the line it starts on."""
    out: list[tuple[int, str]] = []
    cursor = 0
    for blk in blocks:
        head = (blk or "").strip().split("\n", 1)[0].strip()
        idx = text.find(head, cursor) if head else -1
        if idx < 0:
            idx = cursor
        out.append((first_line + text.count("\n", 0, idx), blk))
        cursor = idx + len(head)
    return out


def _parse_bibtex_into(text: str, blocks: list[_BibBlock], res: ParseResult, li: _LineIndex,
                       allow_residual: bool) -> None:
    macros: dict[str, str] = {}
    # Pass 1: @string definitions in file order. BibTeX needs a macro defined before
    # use; resolving them all first is more lenient and never changes a defined value.
    for b in blocks:
        if b.kind != "string" or b.error or not b.body_start:
            continue
        try:
            defs, _ = _bib_parse_fields(text, b.body_start, b.body_end, li)
        except _BibSyntaxError as exc:
            b.error, b.error_pos = "malformed @string: " + exc.reason, exc.pos
            continue
        for name, parts, pos in defs:
            val, undefined = _bib_resolve(parts, macros)
            macros[name] = val
            if undefined:
                res.warnings.append(_diag("bibtex", li(pos), (
                    f"@string '{name}' uses undefined macro(s) {', '.join(undefined)}; "
                    "kept as the macro name"), entry_type="string"))

    seen_keys: dict[str, int] = {}
    prev_end, prev_key, prev_rejected = 0, "", False
    for b in blocks:
        _bib_residual(text, prev_end, b.start, res, li, allow_residual, prev_key, prev_rejected)
        prev_end = b.end
        prev_key, prev_rejected = _bib_block_into(text, b, macros, res, li, seen_keys)
    _bib_residual(text, prev_end, len(text), res, li, allow_residual, prev_key, prev_rejected)


def _bib_block_into(text: str, b: _BibBlock, macros: dict[str, str], res: ParseResult,
                    li: _LineIndex, seen_keys: dict[str, int]) -> tuple[str, bool]:
    """Classify one block into parsed / rejected / unsupported / skipped.

    Returns (citation key or "", whether the block was rejected).
    """
    kind = b.kind
    line, end_line = li(b.start), li(max(b.start, b.end - 1))
    raw = text[b.start:b.end]

    def reject(reason: str, key: str = "", pos: int = -1) -> tuple[str, bool]:
        res.rejected.append(_diag("bibtex", line, reason, key=key, entry_type=kind,
                                  end_line=end_line, error_line=li(pos) if pos >= 0 else line,
                                  excerpt=raw))
        return key, True

    if b.error:
        km = (re.compile(r"\s*([^\s,{}()\"#=%]+)\s*,").match(text, b.body_start)
              if b.body_start else None)
        return reject(b.error, km.group(1) if km else "", b.error_pos)
    if kind in ("comment", "preamble", "string"):
        res.skipped.append({"line": line, "end_line": end_line, "entry_type": kind, "key": None,
                            "reason": _BIB_NON_REFERENCE[kind]})
        return "", False
    try:
        key, i = _bib_parse_key(text, b.body_start, b.body_end)
        fields, warns = _bib_parse_fields(text, i, b.body_end, li, key)
    except _BibSyntaxError as exc:
        return reject(exc.reason, exc.key, exc.pos)
    if kind in ("set", "xdata"):
        res.skipped.append({"line": line, "end_line": end_line, "entry_type": kind, "key": key,
                            "reason": _BIB_NON_REFERENCE[kind]})
        return key, False
    if kind not in BIBTEX_REFERENCE_TYPES:
        res.unsupported.append(_diag("bibtex", line, (
            f"unknown entry type '@{b.entry_type}': not a BibTeX/BibLaTeX reference type, so it "
            "was not verified; change it to a standard type such as @misc, or check it by hand"),
            key=key, entry_type=kind, end_line=end_line, excerpt=raw))
        return key, False

    values: dict[str, str] = {}
    critical: list[tuple[str, list[str]]] = []
    for name, parts, pos in fields:
        if name in values:
            warns.append(f"duplicate field '{name}' at line {li(pos)} ignored (first value kept)")
            continue
        val, undefined = _bib_resolve(parts, macros)
        values[name] = val
        if undefined and name in _BIB_CRITICAL_FIELDS:
            critical.append((name, undefined))
        elif undefined:
            warns.append(f"field '{name}' uses undefined @string macro(s) "
                         f"{', '.join(undefined)}; kept as the macro name")
    if critical:
        name, undefined = critical[0]
        return reject(f"field '{name}' uses undefined @string macro {undefined[0]!r}; define it "
                      f"with @string{{{undefined[0]} = {{...}}}} or wrap the value in braces", key)

    low = key.lower()
    if low in seen_keys:
        warns.append(f"duplicate citation key '{key}' (also at line {seen_keys[low]}); both are verified")
    else:
        seen_keys[low] = line
    entry = _bibtex_entry(raw, text[i:b.body_end], key, kind, values)
    entry.line = line
    entry.warnings = warns + entry.warnings
    for w in warns:
        res.warnings.append(_diag("bibtex", line, w, key=key, entry_type=kind))
    res.entries.append(entry)
    return key, False


def _bib_residual(text: str, start: int, end: int, res: ParseResult, li: _LineIndex,
                  allow_refs: bool, prev_key: str, prev_rejected: bool) -> None:
    """Account for text between BibTeX blocks.

    BibTeX ignores it, but it must not vanish silently: stray field text (an entry
    closed early) is rejected; reference-like text is verified as free-form in auto
    mode (unsupported under --format bibtex); any other prose is listed as ignored.
    """
    seg = text[start:end]
    if not seg.strip():
        return
    first = li(start)
    paragraphs: list[list[tuple[int, str]]] = [[]]
    for k, ln in enumerate(seg.split("\n")):
        s = ln.strip()
        if not s or s.startswith("%"):  # blank line or a '%' comment line
            cm = _BIB_COMMENTED_ENTRY_RE.match(s)
            if cm:
                res.skipped.append({"line": first + k, "end_line": first + k,
                                    "entry_type": "commented-out", "key": cm.group(1) or None,
                                    "reason": ("commented-out entry (the line starts with '%'); "
                                               "not verified — note that BibTeX itself still reads it")})
            if k:  # (k == 0 is just the rest of the line the previous block ended on)
                paragraphs.append([])
        else:
            paragraphs[-1].append((first + k, ln))
    adjacent = True  # the first paragraph directly follows the previous block
    for para in paragraphs:
        if not para:
            adjacent = False
            continue
        ptext = "\n".join(ln for _, ln in para).strip()
        l0, l1 = para[0][0], para[-1][0]
        if not re.search(r"[A-Za-z0-9{}]", ptext):  # stray punctuation, e.g. "," leftovers
            adjacent = False
            continue
        if not re.search(r"[A-Za-z0-9]", ptext):  # only stray braces: no field text was lost
            res.warnings.append(_diag("bibtex", l0, "stray brace(s) outside any entry ignored",
                                      end_line=l1, excerpt=ptext))
            adjacent = False
            continue
        if "{" in ptext or "}" in ptext or _BIB_FIELD_DEBRIS_RE.search(ptext):
            if adjacent and prev_rejected and res.rejected:
                last = res.rejected[-1]  # the same malformed entry spilling over
                last["end_line"] = max(last["end_line"], l1)
                last["reason"] += f"; stray BibTeX text follows on lines {l0}-{l1}"
            else:
                why = "BibTeX field text outside any entry"
                why += (f": entry '{prev_key}' was probably closed early by an extra '}}', so these "
                        "fields were not read" if adjacent and prev_key
                        else ": an '@type{key,' header is missing or malformed")
                res.rejected.append(_diag("bibtex", l0, why, end_line=l1, excerpt=ptext))
            adjacent = False
            continue
        adjacent = False
        for lineno, blk in _locate_blocks(ptext, _split_references(ptext), l0):
            blk = _WS.sub(" ", blk).strip()
            if not blk:
                continue
            why = not_a_reference(blk)
            if why:
                res.ignored_text.append({"line": lineno, "excerpt": _excerpt(blk), "reason": (
                    f"skipped: not a reference ({why}); text outside any BibTeX entry, which "
                    "BibTeX ignores")})
            elif allow_refs:
                e = _parse_freeform_block(blk)
                if e:
                    e.line = lineno
                    res.entries.append(e)
            else:
                res.unsupported.append(_diag("freeform", lineno, (
                    "reference-like text outside any @entry: --format bibtex reads only @entries, "
                    "so it was not verified; re-run with --format auto to verify it as a "
                    "free-form reference"), excerpt=blk))


def _looks_like_bibtex(text: str) -> bool:
    return bool(_scan_bibtex_blocks(text, _LineIndex(text)))


def parse_bibtex(text: str) -> list[Entry]:
    """Parsed BibTeX entries only (see parse_input for rejected / unsupported ones)."""
    return parse_input(text, "bibtex").entries


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
    """Identifier lines only (``--format doi``); see parse_input for the other lines."""
    return parse_input(text, "doi").entries


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


def _parse_freeform_block(block: str) -> Optional[Entry]:
    """Heuristic field extraction from one free-form reference (None if empty)."""
    block = _WS.sub(" ", block).strip()
    if not block:
        return None
    if _is_bare_identifier_line(block):  # a lone DOI / arXiv ID inside a pasted list
        return Entry(raw=block, doi=_first_doi(block), arxiv_id=_first_arxiv(block), fmt="doi")
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
    et_al = False
    if ym and ym.start() > 0:
        head = block[: ym.start()].strip(" .,(")
        head = re.sub(r"^\s*\[?\d{1,3}[\].)]\s+", "", head)  # drop "12." / "[12]" markers
        et_al = bool(re.search(r"(?i)\bet\s+al\b", head))
        names = _clean_authors(re.split(r",| & | and ", head))
        et_al = et_al or len(names) > 6
        authors = names[:6]
    doi = _first_doi(block)
    bad = "" if doi else _malformed_doi(block)
    entry = Entry(
        raw=block,
        title=title.strip(" .,"),
        authors=authors,
        year=ym.group(1) if ym else "",
        doi=doi,
        doi_malformed=bad,
        authors_et_al=et_al,
        arxiv_id=_first_arxiv(block),
        fmt="freeform",
    )
    if bad:
        entry.warnings.append(f"'{bad}' looks like a DOI but is not a valid one (malformed identifier)")
    return entry


def parse_freeform(text: str) -> list[Entry]:
    """One reference per block (see _split_references); heuristic field extraction."""
    return parse_input(text, "freeform").entries


def _parse_plain_into(text: str, fmt: str, res: ParseResult) -> None:
    """Non-BibTeX input: a DOI / arXiv-ID list or free-form references."""
    if fmt == "auto":
        # "doi" only when the lines are mostly bare identifiers; a full reference that
        # merely contains a DOI stays free-form, so its title and authors are kept
        # for the Identifier Hijacking check.
        non_empty = [ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
        id_lines = sum(1 for ln in non_empty
                       if (_first_doi(ln) or _first_arxiv(ln)) and _is_bare_identifier_line(ln))
        mode = "doi" if non_empty and id_lines >= max(1, len(non_empty) * 0.6) else "freeform"
    else:
        mode = fmt
    res.format_detected = mode
    if mode == "freeform":
        for lineno, blk in _locate_blocks(text, _split_references(text)):
            why = not_a_reference(blk)
            if why and why != "empty":
                res.ignored_text.append({"line": lineno, "excerpt": _excerpt(blk),
                                         "reason": f"skipped: not a reference ({why})"})
                continue
            e = _parse_freeform_block(blk)
            if e:
                e.line = lineno
                res.entries.append(e)
        return
    strict = fmt == "doi"  # explicit --format doi reads identifiers only
    for lineno, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        doi = _first_doi(s)
        arxiv = _first_arxiv(s) if not doi else ""
        if (doi or arxiv) and (strict or _is_bare_identifier_line(s)):
            res.entries.append(Entry(raw=s, doi=doi, arxiv_id=arxiv, fmt="doi", line=lineno))
        elif not_a_reference(s):
            res.ignored_text.append({"line": lineno, "excerpt": _excerpt(s), "reason": (
                f"skipped: not a reference ({not_a_reference(s)}); neither an identifier nor a "
                "recognisable reference")})
        elif strict:
            res.unsupported.append(_diag("doi", lineno, (
                "no DOI or arXiv ID on this line: --format doi reads identifiers only, so it was "
                "not verified; re-run with --format auto or --format freeform"), excerpt=s))
        else:  # a full reference inside a mostly-identifier list
            e = _parse_freeform_block(s)
            if e:
                e.line = lineno
                res.entries.append(e)


def parse_input(text: str, fmt: str = "auto") -> ParseResult:
    """Parse ``text`` and account for every entry (see ParseResult)."""
    if fmt not in ("auto", "bibtex", "doi", "freeform"):
        raise ValueError(f"unknown format: {fmt}")
    res = ParseResult(format_requested=fmt)
    if fmt in ("auto", "bibtex"):
        li = _LineIndex(text)
        blocks = _scan_bibtex_blocks(text, li)
        if blocks or fmt == "bibtex":
            _parse_bibtex_into(text, blocks, res, li, allow_residual=fmt == "auto")
            mixed = any(e.fmt != "bibtex" for e in res.entries)
            res.format_detected = "mixed" if mixed else "bibtex"
            return res
    _parse_plain_into(text, fmt, res)
    return res


def parse_bibliography(text: str, fmt: str) -> list[Entry]:
    """Parsed entries only; use parse_input to see rejected / unsupported entries too."""
    return parse_input(text, fmt).entries


# --------------------------------------------------------------------------- #
# API adapters → normalized record {title, authors[surnames], year, doi, retracted} #
# --------------------------------------------------------------------------- #


# Returned by a lookup that had nothing to query with, so the source is not counted as
# having answered (an answer of "no match" is None).
NOT_ASKED: dict = {"not_asked": True}


def crossref_by_doi(doi: str, mailto: str) -> Optional[dict]:
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}{_mailto_param(mailto, '?')}"
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
        f"&rows=5{_mailto_param(mailto, '&')}"
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
    authors = [a for a in msg.get("author", []) or [] if a.get("family") or a.get("name")]
    surnames = [a.get("family") or a.get("name") for a in authors]
    full_names = [" ".join(x for x in (a.get("given"), a.get("family")) if x) or a.get("name")
                  for a in authors]
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
        "author_names": full_names,
        "year": year,
        "years": sorted(set(years)),  # online-first vs print years can differ by one
        "doi": (msg.get("DOI") or "").lower(),
        "retracted": retracted,
        "concern": "expression_of_concern" in types,
    }


def semanticscholar_lookup(entry: Entry, mailto: str) -> Optional[dict]:
    if not (entry.doi or entry.arxiv_id or entry.title):
        return NOT_ASKED
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
    names = [au.get("name", "") for au in p.get("authors", []) or [] if au.get("name")]
    ext = p.get("externalIds", {}) or {}
    return {
        "source": "semanticscholar",
        "title": p.get("title") or "",
        "authors": [_surname_of(n) for n in names],
        "author_names": names,
        "year": str(p.get("year") or ""),
        "doi": (ext.get("DOI") or "").lower(),
        "retracted": False,  # S2 does not expose a retraction flag
    }


_EPMC_SEARCH = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def _phrase(text: str) -> str:
    """Text safe inside a quoted search phrase: punctuation becomes spaces (the indexes
    tokenise on it anyway), so quotes or colons in a title cannot break the query."""
    t = text or ""
    if "\\" in t:
        t = _fold_latex(t)
    t = t.replace("{", "").replace("}", "")  # BibTeX grouping braces are not word breaks
    return _WS.sub(" ", re.sub(r"[^\w\s-]", " ", t)).strip()


def _main_title(title: str) -> str:
    """The title before a subtitle separator, when that part is long enough to search on."""
    m = re.match(r"(.+?)(?::|\s[-—]\s|\?)", title or "")
    return m.group(1).strip() if m and len(m.group(1).strip()) >= 12 else (title or "")


def europepmc_lookup(entry: Entry, mailto: str) -> Optional[dict]:
    """Europe PMC REST search: by DOI when cited, else by title phrase + first author.
    Life sciences first, but it also indexes many other journals and preprint servers."""
    def search(query: str) -> list:
        qs = urllib.parse.urlencode({"query": query, "format": "json", "resultType": "lite",
                                     "pageSize": 5})
        data = _http_get(f"{_EPMC_SEARCH}?{qs}", mailto)
        return ((data or {}).get("resultList") or {}).get("result") or []

    if entry.doi:
        hits = [r for r in search(f'DOI:"{entry.doi}"') if (r.get("doi") or "").lower() == entry.doi.lower()]
        if hits:
            rec = _epmc_norm(hits[0])
            rec["method"] = "id"
            return rec
    phrase = _phrase(entry.title)
    if len(phrase) < 6:
        return None if entry.doi else NOT_ASKED
    query = f'TITLE:"{phrase}"'
    if entry.authors and _surname(entry.authors[0]):
        query += f' AND AUTH:"{_surname(entry.authors[0])}"'
    items = search(query)
    if not items:
        return None
    rec = max((_epmc_norm(r) for r in items[:5]), key=lambda r: _rank(entry, r))
    rec["method"] = "title"
    return rec


def _epmc_norm(r: dict) -> dict:
    # authorString: "Roediger HL, van der Waals JD." -> surnames (trailing initials dropped)
    names = [a.strip() for a in (r.get("authorString") or "").rstrip(".").split(",") if a.strip()]
    return {
        "source": "europepmc",
        "title": (r.get("title") or "").strip().rstrip("."),
        "authors": [s for s in (_surname_of(n) for n in names) if s],
        "author_names": names,
        "year": str(r.get("pubYear") or ""),
        "doi": (r.get("doi") or "").lower(),
        "retracted": False,  # the lite record carries no retraction flag; Crossref supplies it
    }


def openlibrary_lookup(entry: Entry, mailto: str) -> Optional[dict]:
    """Open Library search (keyless) for books: main title + first author. Every edition's
    publication year is kept, so a later edition cited by its own year still matches."""
    if len(_phrase(entry.title)) < 6 or entry.doi or entry.arxiv_id:
        return NOT_ASKED
    params = {"title": _phrase(_main_title(entry.title)), "limit": 5,
              "fields": "title,subtitle,author_name,first_publish_year,publish_year"}
    if entry.authors and _surname(entry.authors[0]):
        params["author"] = _surname(entry.authors[0])
    data = _http_get("https://openlibrary.org/search.json?" + urllib.parse.urlencode(params), mailto)
    docs = (data or {}).get("docs") or []
    if not docs:
        return None
    rec = max((_openlibrary_norm(d) for d in docs[:5]), key=lambda r: _rank(entry, r))
    rec["method"] = "title"
    return rec


def _openlibrary_norm(d: dict) -> dict:
    title = d.get("title") or ""
    if d.get("subtitle"):
        title = f"{title}: {d['subtitle']}"
    years = sorted({str(y) for y in (d.get("publish_year") or []) if y})
    first = str(d.get("first_publish_year") or "")
    return {
        "source": "openlibrary",
        "title": title,
        "authors": [_surname_of(n) for n in d.get("author_name") or [] if n.split()],
        "author_names": [n for n in d.get("author_name") or [] if n.split()],
        "year": first or (years[0] if years else ""),
        "years": sorted(set(years) | ({first} if first else set())),
        "doi": "",
        "retracted": False,
    }


def arxiv_lookup(entry: Entry, mailto: str) -> Optional[dict]:
    if entry.arxiv_id:
        url = f"https://export.arxiv.org/api/query?id_list={urllib.parse.quote(entry.arxiv_id)}&max_results=1"
    elif entry.title:
        q = urllib.parse.quote(f'ti:"{entry.title}"')
        url = f"https://export.arxiv.org/api/query?search_query={q}&max_results=5"
    else:
        return NOT_ASKED
    text = _http_get(url, mailto, accept="application/atom+xml")
    if not text or "<entry>" not in text:
        return None
    method = "id" if entry.arxiv_id else "title"
    recs = []
    for block in text.split("<entry>")[1:]:
        block = block.split("</entry>", 1)[0]
        tm = re.search(r"<title>(.*?)</title>", block, re.DOTALL)
        title = _WS.sub(" ", tm.group(1)).strip() if tm else ""
        names = [_WS.sub(" ", n).strip() for n in re.findall(r"<name>(.*?)</name>", block, re.DOTALL)
                 if n.strip()]
        surnames = [_surname_of(n) for n in names]
        ym = re.search(r"<published>(\d{4})", block)
        aid = re.search(r"<id>.*?abs/([^<]+)</id>", block)
        recs.append({
            "source": "arxiv",
            "title": title,
            "authors": surnames,
            "author_names": names,
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

# Indexes that, besides Crossref, must also have answered (with no match) before an entry
# with no identifier is reported NOT_FOUND. Semantic Scholar search is one of them but never
# required: its keyless pool is often spent.
NOT_FOUND_SECOND_INDEXES = ("semanticscholar", "europepmc", "arxiv", "openlibrary")
TF_SECOND_INDEXES = NOT_FOUND_SECOND_INDEXES  # v1 name, kept for importers

VERDICTS = {
    "verified": "Entry exists; every supplied field that could be checked agrees with an "
                "authoritative record.",
    "PAC": "Partial Attribute Corruption — the work was found, but at least one supplied field "
           "(authors, year, title, identifier) disagrees with the record.",
    "IH": "Identifier Hijacking — the cited DOI/arXiv ID resolves to a different work.",
    "ID_INVALID": "Invalid identifier — the cited DOI is not registered with any DOI agency (or the "
                  "arXiv ID does not exist) and no matching work was found by title. The identifier "
                  "is wrong; whether the work itself exists is undetermined.",
    "NOT_FOUND": "Not found in the checked sources — the sources that answered returned no matching "
                 "record. Absence from these indexes is not evidence of fabrication (books, grey "
                 "literature and regional venues are often unindexed); verify manually.",
    "PH": "Placeholder Hallucination — unresolved citation template/placeholder.",
    "TF": "Total Fabrication — an analyst's conclusion after a documented manual search; never "
          "emitted by this script (index absence is NOT_FOUND).",
    "SH": "Semantic Hallucination — resolves but claim-support unverified (advisory).",
    "unverified": "Could not verify (offline, or the required sources failed to answer, or too "
                  "little structure to decide); manual check required.",
}
SEVERITY = {
    "verified": "NONE",
    "PAC": "MEDIUM",
    "IH": "SERIOUS",
    "ID_INVALID": "SERIOUS",
    "NOT_FOUND": "MEDIUM",
    "PH": "SERIOUS",
    "TF": "SERIOUS",
    "SH": "SERIOUS",
    "unverified": "MEDIUM",
}
# Run-level verdicts (summary.verdict), most severe first. Only PASS and
# PASS_WITH_CONDITIONS are passes, and both require a complete audit.
REPORT_VERDICTS = {
    "FAIL": "At least one SERIOUS finding (IH / ID_INVALID / PH / retraction).",
    "PARTIAL": ("Not every detected entry was parsed and verified (rejected, unsupported, or "
                "unprocessed entries; see input_accounting). Not a pass."),
    "REVIEW_REQUIRED": ("Nothing SERIOUS found, but at least one entry was not found in the checked "
                        "sources (NOT_FOUND). Absence is not proof of fabrication; check those "
                        "entries manually. Not a pass."),
    "UNVERIFIED": "Nothing SERIOUS found, but at least one entry could not be checked. Not a pass.",
    "PASS_WITH_CONDITIONS": "Every entry was found; only fixable metadata issues (PAC).",
    "PASS": ("Every detected entry was parsed and found, with every checkable field agreeing. "
             "Retraction status is reported separately (summary.retraction) and may be unknown "
             "for some entries."),
}
EXISTENCE_STATUSES = ("found", "identifier_mismatch", "identifier_invalid", "not_found",
                      "not_determined", "unavailable", "placeholder", "not_checked")
RETRACTION_STATUSES = ("flagged", "not_flagged_in_checked_sources", "unknown")
# The only retraction evidence source: Crossref `updated-by` / `update-to` records, which
# include publisher notices and (since 2025) the Retraction Watch database.
RETRACTION_SOURCES = ("crossref",)


def _is_placeholder(entry: Entry) -> bool:
    if PLACEHOLDER_RE.search(entry.raw):
        return True
    if not entry.doi and not entry.arxiv_id and len(_normalize(entry.title)) < 6 and not entry.authors:
        return True
    return False


def _ref_id(entry: Entry) -> str:
    return entry.key or entry.doi or entry.arxiv_id or (entry.title[:40] or entry.raw[:40])


def _tf_eligible(entry: Entry) -> bool:
    """Second safety net behind the parser: a free-form entry can be reported NOT_FOUND only
    when it has a title-like segment (two or more words, distinct from the whole text) plus
    an author or a year. Anything thinner is unverified at most. (Named for the v1 TF verdict.)"""
    if entry.fmt != "freeform":
        return True
    title = _normalize(entry.title)
    distinct = title and title != _normalize(entry.raw)
    return bool(distinct and len(title.split()) >= 2 and (entry.authors or entry.year))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _identifier_block(entry: Entry) -> dict:
    doi = ({"cited": entry.doi, "status": "not_checked"} if entry.doi else
           {"cited": entry.doi_malformed, "status": "malformed"} if entry.doi_malformed else
           {"cited": "", "status": "not_cited"})
    arxiv = ({"cited": entry.arxiv_id, "status": "not_checked"} if entry.arxiv_id
             else {"cited": "", "status": "not_cited"})
    return {"doi": doi, "arxiv": arxiv}


def _given_name_tokens(records: Sequence[dict]) -> set[str]:
    """Folded given-name words of the record authors (full names minus their surnames)."""
    out: set[str] = set()
    for m in records:
        for full in m.get("author_names") or []:
            sn = _surname_of(full)
            given = full.replace(sn, " ") if sn and sn in full else ""
            for g in given.split():
                out |= _name_folds(g.strip(".,"))
    return out


def _author_metadata(entry: Entry, records: Sequence[dict]) -> dict:
    """Do the record(s) of this work support each cited author? Never an invented mismatch:
    no cited authors -> not_checked; no record authors -> unknown."""
    cited = [a for a in entry.authors if a.strip()]
    found: list[str] = []
    for m in records:
        for s in m.get("authors") or []:
            if s and not any(names_match(s, f) for f in found):
                found.append(s)
    block = {"status": "not_checked", "supported": [], "unsupported": [], "et_al": entry.authors_et_al,
             "cited_count": len(cited), "record_count": len(found), "omitted_record_authors": 0,
             "read_as_given_names": []}
    if not cited:
        return block
    if not found:
        block["status"] = "unknown"
        return block
    supported, unsupported = author_support(cited, found)
    if entry.fmt == "freeform" and unsupported:
        # Free-form author lists are split heuristically, so "Selwyn, Neil" yields a fragment
        # "Neil". A single-word fragment that is a record author's given name is not an author.
        given = _given_name_tokens(records)
        as_given = [a for a in unsupported if len(a.split()) == 1 and _name_folds(a) & given]
        unsupported = [a for a in unsupported if a not in as_given]
        block["read_as_given_names"] = as_given
    matched = sum(1 for f in found if any(names_match(_surname_of(a), f) for a in supported))
    block.update(supported=supported, unsupported=unsupported,
                 status="disagrees" if unsupported else "agrees",
                 omitted_record_authors=0 if entry.authors_et_al else max(0, len(found) - matched))
    return block


def _retraction_block(same: Sequence[dict], status: dict, found: bool) -> dict:
    """Flagged / not flagged in the checked sources / unknown, with which sources answered."""
    block = {"status": "unknown", "sources_answered": [], "checked_at": _now(), "reason": ""}
    if not found:
        block["reason"] = "the cited work was not identified, so no retraction check applies"
        return block
    cr = [m for m in same if m.get("source") in RETRACTION_SOURCES]
    if any(m.get("retracted") for m in same):
        block.update(status="flagged", sources_answered=sorted({m["source"] for m in cr}) or ["crossref"],
                     reason="Crossref (publisher or Retraction Watch notice) marks this work as retracted")
    elif cr:
        block.update(status="not_flagged_in_checked_sources", sources_answered=["crossref"],
                     reason="Crossref holds a record of this work with no retraction notice; other "
                            "retraction databases were not checked")
    elif status.get("crossref") in ("record", "no_record"):
        block["reason"] = ("Crossref answered but holds no record of this work (common for books, "
                           "arXiv-only preprints and grey literature), so retraction status is unknown")
    else:
        block["reason"] = ("Crossref, the only retraction source checked, did not answer "
                           f"({status.get('crossref', 'not asked')}), so retraction status is unknown")
    return block


def verify_entry(entry: Entry, mailto: str, threshold: float, offline: bool) -> dict:
    """Verify one entry: does the work exist (existence), is its identifier sound (identifier),
    do the supplied fields agree with the record (metadata), and is it retracted (retraction).

    ``verdict`` summarises these for v1 consumers; the separate blocks carry the evidence."""
    ref_id = _ref_id(entry)
    ident = _identifier_block(entry)

    # PH check first — placeholders never reach the network.
    if _is_placeholder(entry):
        return _verdict(entry, ref_id, "PH", detail="Citation is an unresolved placeholder/template.",
                        matches=[], existence={"status": "placeholder"}, identifier=ident)

    if offline:
        return _unverified(entry, ref_id, reason="offline mode requested (--offline)",
                           existence="not_checked", identifier=ident)

    matches: list[dict] = []
    status: dict[str, str] = {}  # source -> record | no_record | error: ... | offline
    has_identifier = bool(entry.doi or entry.arxiv_id)

    def _crossref() -> Optional[dict]:
        if entry.doi:
            rec = crossref_by_doi(entry.doi, mailto)
            # A DOI that does not resolve may still belong to a real work cited
            # with a wrong identifier; the title search lets that surface as PAC.
            return rec or (crossref_by_title(entry, mailto) if entry.title else None)
        return crossref_by_title(entry, mailto) if entry.title else NOT_ASKED

    sources: list[tuple[str, Callable[[], Optional[dict]]]] = [
        ("crossref", _crossref),
        ("semanticscholar", lambda: semanticscholar_lookup(entry, mailto)),
        ("europepmc", lambda: europepmc_lookup(entry, mailto)),
        ("arxiv", lambda: arxiv_lookup(entry, mailto)),
    ]
    if not has_identifier:  # books rarely carry a DOI; a cited DOI is settled by Crossref / doi.org
        sources.append(("openlibrary", lambda: openlibrary_lookup(entry, mailto)))
    for name, fn in sources:
        try:
            rec = fn()
        except NetworkUnavailable:
            # One unreachable host says nothing about the others: record it and keep going.
            status[name] = "offline"
            continue
        except SourceError as exc:
            status[name] = f"error: {exc}"
            continue
        if rec is NOT_ASKED:
            continue  # nothing to query this source with: it neither answered nor failed
        status[name] = "record" if rec else "no_record"
        if rec:
            matches.append(rec)

    def answered(name: str) -> bool:
        return status.get(name) in ("record", "no_record")

    def failed() -> list[str]:
        return [f"{src} {'rate-limited (HTTP 429)' if '429' in st else 'unreachable' if st == 'offline' else 'failed'}"
                for src, st in status.items() if st.startswith("error") or st == "offline"]

    def existence(state: str, method: Optional[str] = None, matched: Sequence[dict] = ()) -> dict:
        return {"status": state, "method": method,
                "matched_in": sorted({m["source"] for m in matched}),
                "sources_answered": sorted(s for s in status if answered(s)),
                "sources_not_checked": sorted(s for s, st in status.items()
                                              if st.startswith("error") or st == "offline")}

    # An arXiv ID that no source resolved: settle existence on arxiv.org/abs, and
    # retry the query API once if the ID is real (its feed is sometimes empty).
    arxiv_exists: Optional[bool] = None
    if entry.arxiv_id and not any(m.get("method") == "id" for m in matches):
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

    lookups = [s for s in status if s != "arxiv.org/abs"]
    if not any(answered(s) for s in lookups):
        unreachable = bool(lookups) and all(status[s] == "offline" for s in lookups)
        reason = ("network unavailable: no source could be reached (DNS/connection failure)"
                  if unreachable else
                  "every source failed to answer (rate limits / server errors / unreachable hosts)")
        return _unverified(entry, ref_id, reason=reason, status=status,
                           existence=existence("unavailable"), identifier=ident)

    id_matches = [m for m in matches if m.get("method") == "id"]
    title_matches = [m for m in matches if m.get("method") == "title"]

    def r_of(m: dict) -> float:
        return title_ratio(entry.title, m["title"]) if entry.title and m.get("title") else 0.0

    # Identifier Hijacking: the cited DOI/arXiv id actually RESOLVED (method=id),
    # but the resolved record's title does not match the cited title.
    # This must be checked against id-resolved records only — a coincidental
    # title-search hit on an unregistered DOI is not hijacking.
    if has_identifier and entry.title and id_matches:
        best_id = max(id_matches, key=r_of)
        if best_id["title"]:
            r = r_of(best_id)
            if r < threshold:
                for k in ("doi", "arxiv"):
                    if ident[k]["status"] == "not_checked":
                        ident[k]["status"] = "resolves_to_other_work"
                return _verdict(entry, ref_id, "IH",
                                detail=(f"Cited identifier resolved to '{best_id['title']}' "
                                        f"(title ratio {r:.2f} < {threshold:.2f}) — unrelated paper."),
                                matches=matches, status=status,
                                existence=existence("identifier_mismatch", "id", [best_id]),
                                identifier=ident)

    pac_reasons: list[str] = []
    flags: list[str] = []

    # The cited identifier resolved nowhere. An unregistered DOI (doi.org) or a nonexistent
    # arXiv ID (arxiv.org/abs 404) is an identifier defect — ID_INVALID — which does not by
    # itself establish that the work is invented. A registered DOI that no index returned, or
    # an identifier whose authoritative source errored, is `unverified` (manual check).
    if has_identifier and not id_matches:
        best_loose = max(title_matches, key=r_of, default=None) if entry.title else None
        loose_ok = bool(best_loose and r_of(best_loose) >= threshold)
        if loose_ok:
            pac_reasons.append(
                "cited identifier does not resolve to this work"
                + (f" (records list DOI {best_loose['doi']})" if best_loose.get("doi") else ""))
            flags.append("IDENTIFIER_DOES_NOT_RESOLVE")
            for k in ("doi", "arxiv"):
                if ident[k]["status"] == "not_checked":
                    ident[k]["status"] = "does_not_resolve_to_cited_work"
        else:
            if entry.doi:
                registered = doi_registered(entry.doi, mailto)
                status["doi.org"] = {True: "registered", False: "not_registered", None: "error"}[registered]
                ident["doi"]["status"] = {True: "registered_unindexed", False: "unregistered",
                                          None: "unknown"}[registered]
                if registered is False:
                    return _verdict(entry, ref_id, "ID_INVALID",
                                    detail=(f"DOI {entry.doi} is not registered with any DOI agency "
                                            "(doi.org Handle API), so the identifier is wrong, and no "
                                            "close title match was found in the sources that answered. "
                                            "Whether the work itself exists is undetermined: correct the "
                                            "DOI or check the work manually."
                                            + (f" Not checked: {', '.join(failed())}." if failed() else "")),
                                    matches=matches, status=status,
                                    existence=existence("identifier_invalid"), identifier=ident)
                why = ("DOI is registered at doi.org but no metadata source returned it "
                       "(non-Crossref DOI or index gap)" if registered
                       else "the cited DOI did not resolve and doi.org could not be reached")
                return _unverified(entry, ref_id, reason=why, status=status, matches=matches,
                                   existence=existence("not_determined" if registered else "unavailable"),
                                   identifier=ident)
            ident["arxiv"]["status"] = {True: "exists_unretrieved", False: "not_found",
                                        None: "unknown"}[arxiv_exists]
            if arxiv_exists is False:
                return _verdict(entry, ref_id, "ID_INVALID",
                                detail=(f"arXiv ID {entry.arxiv_id} does not exist (arxiv.org/abs "
                                        "returns 404) and no close title match was found. The "
                                        "identifier is wrong; whether the work itself exists is "
                                        "undetermined."),
                                matches=matches, status=status,
                                existence=existence("identifier_invalid"), identifier=ident)
            why = ("the arXiv ID exists but its record could not be retrieved" if arxiv_exists
                   else "arXiv could not be reached to resolve the cited ID")
            return _unverified(entry, ref_id, reason=why, status=status, matches=matches,
                               existence=existence("not_determined" if arxiv_exists else "unavailable"),
                               identifier=ident)
    else:
        for k in ("doi", "arxiv"):
            if ident[k]["status"] == "not_checked":
                ident[k]["status"] = "resolves_to_cited_work"

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
            # NOT_FOUND needs Crossref plus at least one other index that actually answered,
            # with no match in any of them: Crossref alone misses books and grey literature. A
            # source that was rate-limited or failed never counts as having answered.
            others = [src for src in NOT_FOUND_SECOND_INDEXES if answered(src)]
            unchecked = failed()
            if answered("crossref") and others and not _tf_eligible(entry):
                return _unverified(entry, ref_id,
                                   reason=("no source returned a matching record, but this free-form "
                                           "entry has too little reference structure (a title plus an "
                                           "author or a year) to report it as not found"),
                                   status=status, matches=matches,
                                   existence=existence("not_determined"), identifier=ident)
            if answered("crossref") and others:
                closest = (f" Closest record: '{best['title']}' (title ratio {t_ratio:.2f})."
                           if best else "")
                return _verdict(entry, ref_id, "NOT_FOUND",
                                detail=("No record matching the cited title and authors in the "
                                        f"sources that answered: crossref, {', '.join(others)}. "
                                        "Absence from these indexes is not evidence of fabrication "
                                        "(books, grey literature, theses and regional or non-English "
                                        "venues are often unindexed); verify the reference manually."
                                        + (f" Not checked: {', '.join(unchecked)}." if unchecked else "")
                                        + closest),
                                matches=matches, status=status,
                                existence=existence("not_found"), identifier=ident)
            return _unverified(entry, ref_id,
                               reason=("no matching record in the sources that answered, but "
                                       + ("only Crossref answered" if answered("crossref")
                                          else "Crossref did not answer")
                                       + ", so books and grey literature cannot be ruled out"
                                       + (" (" + ", ".join(unchecked) + "; see summary.notes)"
                                          if unchecked else "")),
                               status=status, matches=matches,
                               existence=existence("unavailable"), identifier=ident)
        pac_reasons.append(f"title ratio {t_ratio:.2f} < {threshold:.2f} but the closest record "
                           f"shares the cited authors — possible mashup of real references")
        flags.append("POSSIBLE_MASHUP")

    def same_work(m: dict) -> bool:
        if m is best or m.get("method") == "id":
            return True  # id matches already passed the IH title check
        return r_of(m) >= threshold and author_overlap(entry.authors, m["authors"]) != 0.0

    same = [m for m in matches if same_work(m)]
    concern = any(m.get("concern") for m in same)
    retraction = _retraction_block(same, status, found=True)

    # Metadata agreement, field by field. Missing data is not_checked / unknown, never a mismatch.
    authors_md = _author_metadata(entry, same)
    if authors_md["status"] == "disagrees":
        pac_reasons.append("cited author(s) not in the record's author list: "
                           + "; ".join(authors_md["unsupported"]))
        flags.append("UNSUPPORTED_AUTHOR")
    years = sorted({y for m in same for y in (m.get("years") or [m.get("year")]) if y})
    year_md = {"cited": entry.year, "record": years,
               "status": ("not_checked" if not entry.year else "unknown" if not years
                          else "agrees" if entry.year in years else "disagrees")}
    if year_md["status"] == "disagrees":
        pac_reasons.append(f"year cited={entry.year} vs source={'/'.join(years)}")
    title_md = {"ratio": round(t_ratio, 3) if entry.title else None,
                "status": ("not_checked" if not entry.title or not best or not best.get("title")
                           else "agrees" if t_ratio >= threshold else "disagrees")}

    verdict_code = "verified"
    detail = f"Matched in {', '.join(sorted({m['source'] for m in same}))}."
    if authors_md["status"] == "unknown":
        detail += " The record lists no authors, so the cited authors were not checked."
    # An abbreviated author list without "et al." is recorded in metadata.authors
    # (omitted_record_authors) but is not an error and does not change the detail line.
    if pac_reasons:
        verdict_code = "PAC"
        detail = "Found but metadata disagrees: " + "; ".join(pac_reasons) + "."

    method = "id" if id_matches else "title"
    result = _verdict(entry, ref_id, verdict_code, detail=detail, matches=matches, status=status,
                      existence=existence("found", method, same), identifier=ident,
                      metadata={"title": title_md, "authors": authors_md, "year": year_md},
                      retraction=retraction)
    result["flags"] = flags
    result["title_ratio"] = round(t_ratio, 3)
    result["author_overlap"] = round(a_overlap, 3) if a_overlap is not None else None
    # v1 key: True / False, or None when the retraction status is unknown — never a false "clear".
    result["retracted"] = {"flagged": True, "not_flagged_in_checked_sources": False}.get(
        retraction["status"])
    if retraction["status"] == "flagged":
        result["flags"] = result["flags"] + ["RETRACTED"]
        # Retraction does not change existence verdict but is a SERIOUS flag.
        result["severity"] = "SERIOUS"
        result["detail"] += (" RETRACTED: Crossref (publisher or Retraction Watch notice) marks "
                             "this work as retracted.")
    if concern:
        result["flags"] = result["flags"] + ["EXPRESSION_OF_CONCERN"]
        result["detail"] += " An expression of concern is on record for this work."
    return result


def _verdict(entry: Entry, ref_id: str, code: str, detail: str, matches: list[dict],
             status: Optional[dict] = None, *, existence: Optional[dict] = None,
             identifier: Optional[dict] = None, metadata: Optional[dict] = None,
             retraction: Optional[dict] = None) -> dict:
    return {
        "ref_id": ref_id,
        "verdict": code,
        "verdict_meaning": VERDICTS[code],
        "severity": SEVERITY[code],
        "detail": detail,
        "cited": {
            "title": entry.title,
            "authors": entry.authors,
            "authors_et_al": entry.authors_et_al,
            "year": entry.year,
            "doi": entry.doi,
            "arxiv_id": entry.arxiv_id,
        },
        # v2: the separate questions behind the verdict.
        "existence": existence or {"status": "not_checked"},
        "identifier": identifier or _identifier_block(entry),
        "metadata": metadata or {
            "title": {"status": "not_checked", "ratio": None},
            "authors": {"status": "not_checked", "supported": [], "unsupported": [],
                        "et_al": entry.authors_et_al, "cited_count": len(entry.authors),
                        "record_count": 0, "omitted_record_authors": 0, "read_as_given_names": []},
            "year": {"status": "not_checked", "cited": entry.year, "record": []}},
        "retraction": retraction or _retraction_block([], status or {}, found=False),
        "sources_checked": sorted(status or {}),
        "source_status": dict(status or {}),
        "matches": [{k: m.get(k) for k in ("source", "method", "title", "year", "doi", "retracted")}
                    for m in matches],
        "flags": [],
        # Where the entry came from in the input, so a verdict can be traced to a line.
        "input": {
            "format": entry.fmt or None,
            "line": entry.line or None,
            "entry_type": entry.entry_type or None,
            "warnings": list(entry.warnings),
        },
    }


def _unverified(entry: Entry, ref_id: str, reason: str, status: Optional[dict] = None,
                matches: Optional[list[dict]] = None, *, existence: Any = None,
                identifier: Optional[dict] = None) -> dict:
    if isinstance(existence, str):
        existence = {"status": existence}
    r = _verdict(entry, ref_id, "unverified",
                 detail=f"{reason}. NOT confirmed — do not treat as passing.",
                 matches=matches or [], status=status,
                 existence=existence or {"status": "unavailable"}, identifier=identifier)
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


def input_accounting(res: ParseResult, processed: int,
                     unprocessed: Sequence[Entry] = ()) -> dict:
    """The report's ``input_accounting`` object.

    ``processed`` counts parsed entries that received a verdict; a parsed entry without
    one (for example, the run was interrupted) is ``unprocessed``. Invariants:
    ``detected == parsed + rejected + unsupported`` and
    ``parsed == processed + unprocessed``.
    """
    parsed = len(res.entries)
    unprocessed_n = max(parsed - processed, len(unprocessed), 0)
    return {
        "complete": res.complete and unprocessed_n == 0,
        "format_requested": res.format_requested,
        "format_detected": res.format_detected,
        "detected": res.detected,
        "parsed": parsed,
        "rejected": len(res.rejected),
        "unsupported": len(res.unsupported),
        "processed": processed,
        "unprocessed": unprocessed_n,
        "parsed_by_format": dict(sorted(Counter(e.fmt or "unknown" for e in res.entries).items())),
        "non_reference_blocks": dict(sorted(Counter(b["entry_type"] for b in res.skipped).items())),
        "ignored_text_segments": len(res.ignored_text),
        "rejected_entries": res.rejected,
        "unsupported_entries": res.unsupported,
        "unprocessed_entries": [{"ref_id": _ref_id(e), "line": e.line or None, "format": e.fmt or None}
                                for e in unprocessed],
        "skipped_blocks": res.skipped,
        "ignored_text": res.ignored_text,
        "warnings": res.warnings,
    }


def _results_only_accounting(n: int) -> dict:
    """Accounting for a caller that passes verdicts without parse information."""
    return {"complete": True, "format_requested": None, "format_detected": None,
            "detected": n, "parsed": n, "rejected": 0, "unsupported": 0, "processed": n,
            "unprocessed": 0, "parsed_by_format": {}, "non_reference_blocks": {},
            "ignored_text_segments": 0, "rejected_entries": [], "unsupported_entries": [],
            "unprocessed_entries": [], "skipped_blocks": [], "ignored_text": [], "warnings": []}


def _partial_warning(acc: dict) -> str:
    rej, uns, unp = acc.get("rejected", 0), acc.get("unsupported", 0), acc.get("unprocessed", 0)
    return (f"PARTIAL AUDIT: {rej + uns + unp} of {acc.get('detected', 0)} detected entries were "
            f"not verified ({rej} rejected as malformed, {uns} unsupported, {unp} unprocessed); "
            "see input_accounting. This run cannot pass until every entry is parsed and verified.")


def build_report(results: list[dict], mailto: str, threshold: float, offline: bool,
                 accounting: Optional[dict] = None) -> dict:
    """Assemble the JSON report.

    Pass ``accounting=input_accounting(parse_input(...), processed=len(results))`` (the
    CLI always does) so the verdict reflects the whole input. Without it — the v1.1
    call signature — the results are taken to be the entire input.
    """
    acc = dict(accounting) if accounting is not None else _results_only_accounting(len(results))
    # A complete audit needs every detected entry parsed AND given a verdict. Checked
    # here too (not only trusted from the caller), so PASS can never rest on a subset.
    complete = (bool(acc.get("complete")) and not acc.get("rejected") and not acc.get("unsupported")
                and not acc.get("unprocessed")
                and acc.get("parsed", len(results)) == len(results)
                and acc.get("processed", len(results)) == len(results))
    acc["complete"] = complete

    counts = {k: 0 for k in VERDICTS}
    sev = {"SERIOUS": 0, "MEDIUM": 0, "MINOR": 0}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        s = r["severity"]
        if s in sev:
            sev[s] += 1
    n = len(results) or 1
    # Share of entries carrying a fabrication *signal* (a wrong or hijacked identifier, a
    # placeholder, or absence from every index that answered) — a risk indicator, not proof.
    signals = counts["TF"] + counts["IH"] + counts["PH"] + counts["ID_INVALID"] + counts["NOT_FOUND"]
    fabrication_risk = round(signals / n, 3)
    integrity = round((counts["verified"]) / n, 3)

    # SERIOUS findings (IH / ID_INVALID / PH / retraction) dominate. Otherwise an incomplete
    # input makes the run PARTIAL, an entry absent from every checked index makes it
    # REVIEW_REQUIRED, and any entry that could not be checked (or no entry at all) makes it
    # UNVERIFIED — never a (conditional) pass.
    if sev["SERIOUS"] > 0:
        verdict = "FAIL"
    elif not complete:
        verdict = "PARTIAL"
    elif counts["NOT_FOUND"]:
        verdict = "REVIEW_REQUIRED"
    elif counts["unverified"] or not results:
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
    warning = None if complete else _partial_warning(acc)
    if warning:
        notes.insert(0, warning)
    if not results:
        notes.append("no entries were verified")
    if acc.get("ignored_text_segments"):
        notes.append(f"{acc['ignored_text_segments']} text segment(s) skipped: not a reference "
                     "(headings, prose), so not verified and given no verdict "
                     "(see input_accounting.ignored_text)")
    if acc.get("warnings"):
        notes.append(f"{len(acc['warnings'])} parser warning(s) (see input_accounting.warnings)")
    retraction = {k: 0 for k in RETRACTION_STATUSES}
    existence: dict[str, int] = {}
    for r in results:
        st = (r.get("existence") or {}).get("status", "not_checked")
        existence[st] = existence.get(st, 0) + 1
        if st == "found":
            rs = (r.get("retraction") or {}).get("status", "unknown")
            retraction[rs if rs in retraction else "unknown"] += 1
    if retraction["unknown"]:
        notes.append(f"retraction status unknown for {retraction['unknown']} found entr"
                     f"{'y' if retraction['unknown'] == 1 else 'ies'}: Crossref, the only retraction "
                     "source checked, did not answer or holds no record of the work. This is not "
                     "retraction clearance (see each entry's retraction block).")
    if counts["NOT_FOUND"]:
        notes.append(f"{counts['NOT_FOUND']} entr{'y was' if counts['NOT_FOUND'] == 1 else 'ies were'} "
                     "not found in the checked sources; absence from these indexes is not proof of "
                     "fabrication — check them manually")

    return {
        "tool": "alterlab-citation-verifier/verify_citations.py",
        "version": TOOL_VERSION,
        # 2 = existence / identifier / metadata / retraction blocks per entry, NOT_FOUND and
        # ID_INVALID verdicts (no TF from index absence), REVIEW_REQUIRED, retracted may be null.
        "schema_version": REPORT_SCHEMA_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        # "complete" only when every detected entry was parsed and verified.
        "status": "complete" if complete else "partial",
        "warning": warning,
        "config": {"mailto": mailto, "threshold": threshold, "offline": offline,
                   "http_backend": "requests" if _HAS_REQUESTS else "urllib",
                   # whether the optional key was present — never the key itself
                   "s2_api_key": bool(S2_API_KEY)},
        "taxonomy": VERDICTS,
        "summary": {
            "total": len(results),
            "verdict": verdict,
            "verdict_meaning": REPORT_VERDICTS[verdict],
            "status": "complete" if complete else "partial",
            "input": {k: acc.get(k, 0) for k in ("detected", "parsed", "rejected", "unsupported",
                                                 "processed", "unprocessed")},
            "verdict_counts": counts,
            "severity_counts": sev,
            "citation_integrity_score": integrity,
            "fabrication_risk_score": fabrication_risk,
            "retracted": sum(1 for r in results if r.get("retracted")),
            "retraction": retraction,
            "existence": dict(sorted(existence.items())),
            "source_errors": source_errors,
            "notes": notes,
        },
        "input_accounting": acc,
        "entries": results,
    }


def _stderr_banner(report: dict, limit: int = 12) -> str:
    """Human-readable warning printed to stderr ahead of the JSON report."""
    acc = report.get("input_accounting") or {}
    lines: list[str] = []
    if report.get("status") != "complete":
        bar = "=" * 78
        lines += [bar, "WARNING: " + (report.get("warning") or "PARTIAL AUDIT")]
        items = ([("rejected", d) for d in acc.get("rejected_entries", [])]
                 + [("unsupported", d) for d in acc.get("unsupported_entries", [])]
                 + [("unprocessed", d) for d in acc.get("unprocessed_entries", [])])
        for kind, d in items[:limit]:
            where = f"line {d.get('line') or '?'}"
            if d.get("error_line") and d.get("error_line") != d.get("line"):
                where += f" (problem at line {d['error_line']})"
            key = d.get("key") or d.get("ref_id")
            reason = d.get("reason") or "not verified (the run stopped before this entry)"
            lines.append(f"  - {where}{' [' + key + ']' if key else ''} {kind}: {reason}")
        if len(items) > limit:
            lines.append(f"  ... and {len(items) - limit} more (see input_accounting)")
        lines += [f"  summary.verdict = {report['summary']['verdict']}; status = partial", bar]
    ignored = acc.get("ignored_text") or []
    if ignored:
        where = ", ".join(f"line {d['line']}" for d in ignored[:5]) + (" ..." if len(ignored) > 5 else "")
        lines.append(f"note: {len(ignored)} text segment(s) skipped: not a reference (headings, "
                     f"prose); not verified ({where})")
    for w in (acc.get("warnings") or [])[:5]:
        lines.append(f"note: line {w.get('line')}{' [' + w['key'] + ']' if w.get('key') else ''}: "
                     f"{w.get('reason')}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #


def _read_input(path: str) -> str:
    if path == "-":
        text = sys.stdin.read()
    elif os.path.exists(path):
        with open(path, "r", encoding="utf-8-sig") as fh:  # utf-8-sig drops a BOM
            text = fh.read()
    else:
        text = path  # treat the argument itself as inline text
    return text[1:] if text.startswith("﻿") else text


def _verify_safely(entry: Entry, mailto: str, threshold: float, offline: bool) -> dict:
    """verify_entry, but an unexpected error on one entry yields `unverified` for that
    entry instead of aborting the run or silently dropping it."""
    try:
        return verify_entry(entry, mailto, threshold, offline)
    except Exception as exc:  # noqa: BLE001
        r = _unverified(entry, _ref_id(entry),
                        reason=f"internal error while verifying this entry ({type(exc).__name__}: {exc})")
        r["internal_error"] = True
        return r


_CLI_EPILOG = """\
input accounting:
  Every detected entry is parsed (then verified), rejected (malformed: line, key,
  reason), or unsupported (detected but not handled, with the reason). The JSON
  report carries status ("complete" | "partial"), warning, summary.input and
  input_accounting. A run with any rejected, unsupported, or unprocessed entry is
  PARTIAL (or FAIL), never PASS; a warning banner is printed to stderr.

exit codes:
  0  complete audit: every detected entry was parsed and got a verdict; read
     summary.verdict (PASS / PASS_WITH_CONDITIONS / FAIL / UNVERIFIED)
  2  bad input or usage: unreadable input, unknown option, or no entry could be
     parsed (the report is still written when entries were detected)
  3  partial audit: the report was written, but at least one detected entry was
     rejected, unsupported, or left unprocessed (status = "partial")
"""


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Verify that bibliography entries exist via public scholarly APIs.",
        epilog=_CLI_EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="Path to a .bib/.txt file, '-' for stdin, or inline text.")
    ap.add_argument("--format", choices=["auto", "bibtex", "doi", "freeform"], default="auto",
                    help="Input format (default auto: BibTeX, DOI/arXiv list, free-form, or a mix).")
    ap.add_argument("--mailto", default=DEFAULT_MAILTO,
                    help="Your contact email for Crossref's polite pool (optional; default: "
                         "$ALTERLAB_CONTACT_EMAIL, else none is sent).")
    ap.add_argument("--threshold", type=float, default=0.70, help="Fuzzy title-match ratio (0..1).")
    ap.add_argument("--out", default=None, help="Write JSON report to this path (default stdout).")
    ap.add_argument("--offline", action="store_true", help="Skip the network; emit 'unverified' verdicts.")
    args = ap.parse_args(argv)

    try:
        text = _read_input(args.input)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: could not read input: {exc}", file=sys.stderr)
        return 2
    try:
        parsed = parse_input(text, args.format)
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not parse bibliography: {exc}", file=sys.stderr)
        return 2
    if parsed.detected == 0:
        hint = (f" ({len(parsed.ignored_text)} text segment(s) skipped: not a reference.)"
                if parsed.ignored_text else "")
        print("error: no bibliography entries parsed from input." + hint, file=sys.stderr)
        return 2

    results: list[dict] = []
    try:
        for e in parsed.entries:
            results.append(_verify_safely(e, args.mailto, args.threshold, args.offline))
    except KeyboardInterrupt:
        print(f"interrupted: {len(parsed.entries) - len(results)} entries were not verified; "
              "writing a partial report.", file=sys.stderr)
    acc = input_accounting(parsed, processed=len(results), unprocessed=parsed.entries[len(results):])
    report = build_report(results, args.mailto, args.threshold, args.offline, accounting=acc)
    banner = _stderr_banner(report)
    if banner:
        print(banner, file=sys.stderr)
    out = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(out + "\n")
        print(f"wrote {report['summary']['total']} verdicts → {args.out} "
              f"(verdict={report['summary']['verdict']}, status={report['status']})", file=sys.stderr)
    else:
        print(out)
    if not parsed.entries:
        print(f"error: none of the {parsed.detected} detected entries could be parsed "
              "(see the diagnostics above).", file=sys.stderr)
        return 2
    return 0 if report["status"] == "complete" else 3


if __name__ == "__main__":
    raise SystemExit(main())
