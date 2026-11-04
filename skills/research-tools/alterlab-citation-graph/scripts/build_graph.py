#!/usr/bin/env python3
"""Build a citation/co-citation graph from seed papers using open, keyless citation data.

A free ResearchRabbit analog that needs no API key, account or subscription. Starting from
one or more seed works (DOI or arXiv ID), this walks the citation graph in both directions:

  - references  (works the seed *cites*, i.e. its backward edges), and
  - citations   (works that *cite* the seed, i.e. its forward edges).

It then ranks the discovered neighbourhood by **co-citation strength** — how many of the
seed set a candidate work connects to — surfacing the papers most central to the seed's
local literature, like ResearchRabbit's "Similar Work" panels but with no subscription.

Data sources, all keyless (checked live 2026-11-02):
  - OpenCitations Index v2 (api.opencitations.net/index/v2): ``/references/doi:<doi>`` and
    ``/citations/doi:<doi>`` list the DOIs a work cites and the DOIs citing it (open
    Crossref, DataCite and PubMed citation data). The citations answer is one unpaginated
    JSON array — tens of thousands of records for a classic paper — so it is read as a
    stream and cut at --per-seed.
  - Semantic Scholar Graph API (api.semanticscholar.org/graph/v1): references and citations
    (with titles, years and citation counts) for works OpenCitations has no data for —
    typically preprints and works whose publisher deposits no reference list — and
    metadata for DOIs Crossref does not register. Its keyless pool is shared and often
    answers HTTP 429: the script backs off (2, 4, 8 s), then pauses Semantic Scholar for
    30 s and says on stderr which works it could not check. An optional S2_API_KEY gives
    a dedicated rate limit; it is never needed.
  - Crossref (api.crossref.org/works?filter=doi:...): titles, years and citation counts of
    the seeds and the ranked works, 40 DOIs per call; doi.org content negotiation fills
    in any DOI that neither Crossref nor Semantic Scholar described (e.g. DataCite DOIs).
OpenAlex is no longer used (removed in v1.3.0): its keyless list calls now share a small
per-IP daily budget, so dependable use needed an account.

Node ids are lowercase DOIs (an arXiv preprint is ``10.48550/arxiv.<id>``, its DataCite
DOI); a work with no DOI is ``pmid:<n>`` or ``s2:<paperId>``.

Outputs:
  - GraphML (.graphml)  — open in Gephi / Cytoscape / yEd / networkx.
  - JSON    (.json)     — nodes + edges + ranked co-citation table, for code.

Stdlib only (urllib, json, argparse) — no third-party dependency, so it runs in a bare
`uv run python` with nothing installed.

Examples
--------
    # One seed DOI, default depth, write both formats next to a basename:
    uv run python build_graph.py --seed 10.1038/nphys1170 --out graph/seed1

    # Several seeds (DOI / arXiv), deeper walk, more neighbours:
    uv run python build_graph.py \\
        --seed 10.1038/nphys1170 --seed 10.18653/v1/N19-1423 --seed arXiv:1706.03762 \\
        --depth 2 --per-seed 50 --top 40 --out graph/transformer

    # Citing works from Semantic Scholar only (never OpenCitations):
    uv run python build_graph.py --seed 10.1038/nature14539 --citers-source semanticscholar

    # Offline / CI smoke test with no network:
    uv run python build_graph.py --self-test
"""

from __future__ import annotations

import argparse
import codecs
import http.client
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

OPENCITATIONS_BASE = "https://api.opencitations.net/index/v2"
S2_BASE = "https://api.semanticscholar.org/graph/v1"
CROSSREF_BASE = "https://api.crossref.org/works"
USER_AGENT = "alterlab-citation-graph/1.3 (https://github.com/AlterLab-IEU)"
DEFAULT_TIMEOUT = 30
S2_FIELDS = "externalIds,title,year,citationCount"
S2_MAX_LIMIT = 1000  # Semantic Scholar's page cap for /references and /citations
S2_BACKOFF = (2.0, 4.0, 8.0)  # seconds between retries on HTTP 429 (no Retry-After is sent)
S2_PAUSE = 30.0  # after the backoff is spent, skip Semantic Scholar for this long
CROSSREF_BACKOFF = (1.0, 2.0, 4.0)  # public pool: one request in flight per IP
CROSSREF_BATCH = 40  # DOIs per filter=doi:... call (keeps the URL short)
_CITING_RE = re.compile(r'"citing"\s*:\s*"([^"]*)"')
_OC_DOI_RE = re.compile(r"\bdoi:(10\.\S+)")
_OC_PMID_RE = re.compile(r"\bpmid:(\d+)")
_ARXIV_DOI_RE = re.compile(r"^10\.48550/arxiv\.(.+)$", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Seed normalisation and node ids                                             #
# --------------------------------------------------------------------------- #

_DOI_RE = re.compile(r"10\.\d{4,9}/\S+", re.IGNORECASE)
_ARXIV_RE = re.compile(r"^(arxiv:)?(\d{4}\.\d{4,5})(v\d+)?$", re.IGNORECASE)
_W_ID_RE = re.compile(r"^W\d+$", re.IGNORECASE)


def arxiv_doi(arxiv_id: str) -> str:
    """arXiv's DataCite DOI for an arXiv id (version suffix dropped)."""
    return "10.48550/arxiv." + re.sub(r"v\d+$", "", arxiv_id.strip()).lower()


def normalize_seed(raw: str) -> str:
    """Turn a user-supplied seed into a node id: a lowercase DOI.

    Accepts a bare DOI, a DOI URL, ``doi:<doi>``, or an arXiv id (with or without the
    ``arXiv:`` prefix, which becomes its DataCite DOI ``10.48550/arxiv.<id>``). Raises
    ValueError on anything else, including the OpenAlex work ids an older version took.
    """
    s = raw.strip()
    if not s:
        raise ValueError("empty seed")
    if _W_ID_RE.match(s) or "openalex.org/" in s.lower():
        raise ValueError(f"{raw!r} is an OpenAlex work id; OpenAlex is no longer used (its keyless "
                         "access is metered per IP). Pass the work's DOI or arXiv id instead.")
    m = _ARXIV_RE.match(s)
    if m:
        return arxiv_doi(m.group(2))
    doi = s
    for prefix in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "doi:"):
        if doi.lower().startswith(prefix):
            doi = doi[len(prefix):]
            break
    if _DOI_RE.fullmatch(doi):
        return doi.lower()
    raise ValueError(f"unrecognised seed (not a DOI or arXiv id): {raw!r}")


def _oc_node_id(ids: str) -> str:
    """Node id from an OpenCitations id list ("omid:br/1 pmid:2 doi:10.x/y ...")."""
    d = _OC_DOI_RE.search(ids)
    if d:
        return d.group(1).lower()
    p = _OC_PMID_RE.search(ids)
    return f"pmid:{p.group(1)}" if p else ""


def _oc_selector(node_id: str) -> Optional[str]:
    if node_id.startswith("10."):
        return "doi:" + node_id
    if node_id.startswith("pmid:"):
        return node_id
    return None


def _s2_selector(node_id: str) -> Optional[str]:
    m = _ARXIV_DOI_RE.match(node_id)
    if m:
        return "ARXIV:" + m.group(1)
    if node_id.startswith("10."):
        return "DOI:" + node_id
    if node_id.startswith("pmid:"):
        return "PMID:" + node_id[5:]
    if node_id.startswith("s2:"):
        return node_id[3:]
    return None


def _s2_work(p: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise a Semantic Scholar paper to {id, doi, title, year, cited_by_count}."""
    ext = p.get("externalIds") or {}
    doi = (ext.get("DOI") or "").lower()
    if not doi and ext.get("ArXiv"):
        doi = arxiv_doi(str(ext["ArXiv"]))
    pmid = str(ext.get("PubMed") or "")
    nid = doi or (f"pmid:{pmid}" if pmid else "") or (f"s2:{p['paperId']}" if p.get("paperId") else "")
    return {"id": nid, "doi": doi or None, "title": p.get("title") or "",
            "year": p.get("year"), "cited_by_count": p.get("citationCount") or 0}


class RateLimited(Exception):
    """A shared keyless pool answered HTTP 429 after backoff: the call was not checked."""


# --------------------------------------------------------------------------- #
# Keyless client: OpenCitations + Semantic Scholar + Crossref (+ doi.org)      #
# --------------------------------------------------------------------------- #

@dataclass
class CitationClient:
    timeout: int = DEFAULT_TIMEOUT
    sleep: float = 0.0  # optional delay after every request (politeness throttle)
    citers_source: str = "auto"  # auto | opencitations | semanticscholar
    s2_api_key: Optional[str] = None  # optional; only raises Semantic Scholar's rate limit
    _fetch: Optional[Callable[..., Any]] = None  # test seam: (url, data=None, accept=...) -> parsed JSON
    _stream: Optional[Callable[[str], Iterable[bytes]]] = None  # test seam: url -> byte chunks
    _sleep: Callable[[float], None] = time.sleep
    s2_paused_until: float = 0.0
    s2_skipped: List[str] = field(default_factory=list)  # works whose S2 lookup was not checked
    _noted: set = field(default_factory=set)

    # -- transport ---------------------------------------------------------
    def _request(self, url: str, data: Optional[dict] = None,
                 accept: str = "application/json") -> Any:
        if self._fetch is not None:
            return self._fetch(url, data=data, accept=accept)
        headers = {"User-Agent": USER_AGENT, "Accept": accept}
        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if self.s2_api_key and url.startswith(S2_BASE):
            headers["x-api-key"] = self.s2_api_key  # header, so it never shows in a URL
        req = urllib.request.Request(url, data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            payload = resp.read().decode("utf-8")
        if self.sleep:
            time.sleep(self.sleep)
        return json.loads(payload)

    def _with_backoff(self, url: str, backoff: Tuple[float, ...], data: Optional[dict] = None,
                      accept: str = "application/json") -> Any:
        for attempt in range(len(backoff) + 1):
            try:
                return self._request(url, data=data, accept=accept)
            except urllib.error.HTTPError as exc:
                if exc.code != 429:
                    raise
                if attempt == len(backoff):
                    raise RateLimited(url) from exc
                self._sleep(backoff[attempt])
        raise RateLimited(url)  # pragma: no cover - loop always returns or raises

    def note(self, key: str, text: str) -> None:
        if key not in self._noted:
            self._noted.add(key)
            print("note: " + text, file=sys.stderr)

    def _s2(self, url: str, data: Optional[dict] = None, what: str = "") -> Any:
        """Semantic Scholar call with backoff; None on 404; RateLimited when the pool stays busy."""
        if time.monotonic() < self.s2_paused_until:
            self.s2_skipped.append(what or url)
            raise RateLimited(url)
        try:
            return self._with_backoff(url, S2_BACKOFF, data=data)
        except RateLimited:
            self.s2_paused_until = time.monotonic() + S2_PAUSE
            self.s2_skipped.append(what or url)
            self.note("s2-429", "Semantic Scholar's shared keyless pool answered HTTP 429 after "
                      "backoff; works OpenCitations has no data for are listed as not checked "
                      "(retry later, or set the optional S2_API_KEY).")
            raise
        except urllib.error.HTTPError as exc:
            if exc.code in (400, 404):
                return None  # unknown id: Semantic Scholar answered "no such paper"
            raise

    # -- OpenCitations -----------------------------------------------------
    def _chunks(self, url: str, size: int = 65536) -> Iterable[bytes]:
        if self._stream is not None:  # test seam
            yield from self._stream(url)
            return
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            while True:
                chunk = resp.read(size)
                if not chunk:
                    return
                yield chunk

    def oc_references(self, node_id: str) -> Optional[List[str]]:
        """Node ids the work cites, per OpenCitations; None when it cannot be asked (no DOI/PMID)."""
        sel = _oc_selector(node_id)
        if not sel:
            return None
        rows = self._request(f"{OPENCITATIONS_BASE}/references/{urllib.parse.quote(sel, safe=':/')}")
        ids = [_oc_node_id(r.get("cited", "")) for r in rows or []]
        return list(dict.fromkeys(i for i in ids if i and i != node_id))

    def oc_citers(self, node_id: str, limit: int) -> Optional[List[str]]:
        """Up to `limit` node ids citing the work, per OpenCitations (read as a stream)."""
        sel = _oc_selector(node_id)
        if not sel:
            return None
        url = f"{OPENCITATIONS_BASE}/citations/{urllib.parse.quote(sel, safe=':/')}"
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        found: List[str] = []
        buf = ""
        try:
            for chunk in self._chunks(url):
                buf += decoder.decode(chunk)
                last = 0
                for m in _CITING_RE.finditer(buf):
                    last = m.end()
                    nid = _oc_node_id(m.group(1))
                    if nid and nid != node_id and nid not in found:
                        found.append(nid)
                    if len(found) >= limit:
                        return found
                buf = buf[last:]
        except (OSError, http.client.HTTPException):
            if not found:
                raise  # nothing usable; a cut after some records still counts
        return found

    # -- Semantic Scholar --------------------------------------------------
    def s2_references(self, node_id: str) -> Optional[List[Dict[str, Any]]]:
        sel = _s2_selector(node_id)
        if not sel:
            return None
        url = (f"{S2_BASE}/paper/{urllib.parse.quote(sel, safe=':/')}/references?"
               + urllib.parse.urlencode({"fields": S2_FIELDS, "limit": S2_MAX_LIMIT}))
        data = self._s2(url, what=node_id)
        if data is None:
            return []
        works = [_s2_work(r.get("citedPaper") or {}) for r in data.get("data") or []]
        return [w for w in works if w["id"] and w["id"] != node_id]

    def s2_citers(self, node_id: str, limit: int) -> Optional[List[Dict[str, Any]]]:
        sel = _s2_selector(node_id)
        if not sel:
            return None
        url = (f"{S2_BASE}/paper/{urllib.parse.quote(sel, safe=':/')}/citations?"
               + urllib.parse.urlencode({"fields": S2_FIELDS, "limit": max(1, min(limit, S2_MAX_LIMIT))}))
        data = self._s2(url, what=node_id)
        if data is None:
            return []
        works = [_s2_work(r.get("citingPaper") or {}) for r in data.get("data") or []]
        return [w for w in works if w["id"] and w["id"] != node_id][:limit]

    def s2_batch(self, node_ids: List[str]) -> List[Dict[str, Any]]:
        sels = {_s2_selector(n): n for n in node_ids if _s2_selector(n)}
        out: List[Dict[str, Any]] = []
        keys = list(sels)
        for start in range(0, len(keys), 500):
            chunk = keys[start:start + 500]
            data = self._s2(f"{S2_BASE}/paper/batch?fields={S2_FIELDS}", data={"ids": chunk},
                            what=f"metadata for {len(chunk)} works")
            for sel, p in zip(chunk, data or []):
                if p:
                    w = _s2_work(p)
                    w["id"] = sels[sel]  # keep the node id it was asked under
                    out.append(w)
        return out

    # -- Crossref and doi.org ---------------------------------------------
    def crossref_batch(self, dois: List[str]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for start in range(0, len(dois), CROSSREF_BATCH):
            chunk = dois[start:start + CROSSREF_BATCH]
            qs = urllib.parse.urlencode({
                "filter": ",".join(f"doi:{d}" for d in chunk), "rows": len(chunk),
                "select": "DOI,title,issued,is-referenced-by-count"})
            data = self._with_backoff(f"{CROSSREF_BASE}?{qs}", CROSSREF_BACKOFF)
            for it in (data.get("message") or {}).get("items", []):
                year = ((it.get("issued") or {}).get("date-parts") or [[None]])[0][0]
                out.append({"id": (it.get("DOI") or "").lower(), "doi": (it.get("DOI") or "").lower(),
                            "title": " ".join(((it.get("title") or [""])[0] or "").split()),
                            "year": year, "cited_by_count": it.get("is-referenced-by-count") or 0})
        return out

    def doi_csl(self, doi: str) -> Optional[Dict[str, Any]]:
        """Title and year from doi.org content negotiation (any registration agency)."""
        data = self._with_backoff(f"https://doi.org/{urllib.parse.quote(doi, safe='/')}",
                                  CROSSREF_BACKOFF, accept="application/vnd.citationstyles.csl+json")
        if not data:
            return None
        title = data.get("title") or ""
        title = " ".join((title[0] if isinstance(title, list) else title).split())
        year = ((data.get("issued") or {}).get("date-parts") or [[None]])[0][0]
        return {"id": doi, "doi": doi, "title": title, "year": year, "cited_by_count": 0}


# --------------------------------------------------------------------------- #
# Edges: OpenCitations first, Semantic Scholar where it has nothing            #
# --------------------------------------------------------------------------- #

_NET_ERRORS = (urllib.error.URLError, OSError, http.client.HTTPException, ValueError, RateLimited)


def _edges(client: CitationClient, node_id: str, oc_call: Callable[[], Optional[List[str]]],
           s2_call: Callable[[], Optional[List[Dict[str, Any]]]], order: Tuple[str, ...]
           ) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    """Ask the sources in `order` until one returns edges. Returns (works, answered, failed):
    `answered` names the sources that answered (possibly with nothing), `failed` those that
    could not be checked, with the reason."""
    answered: List[str] = []
    failed: List[str] = []
    for src in order:
        try:
            res = oc_call() if src == "opencitations" else s2_call()
        except RateLimited:
            failed.append(f"{src}: rate-limited (HTTP 429), not checked")
            continue
        except _NET_ERRORS as exc:
            failed.append(f"{src}: {exc}")
            continue
        if res is None:  # this source cannot be asked about this id
            continue
        answered.append(src)
        if res:
            works = [{"id": r} if isinstance(r, str) else r for r in res]
            return works, answered, failed
    return [], answered, failed


def fetch_references(client: CitationClient, node_id: str) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    return _edges(client, node_id, lambda: client.oc_references(node_id),
                  lambda: client.s2_references(node_id), ("opencitations", "semanticscholar"))


def fetch_citers(client: CitationClient, node_id: str, per_seed: int
                 ) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    order = {"opencitations": ("opencitations",), "semanticscholar": ("semanticscholar",)}.get(
        client.citers_source, ("opencitations", "semanticscholar"))
    return _edges(client, node_id, lambda: client.oc_citers(node_id, per_seed),
                  lambda: client.s2_citers(node_id, per_seed), order)


# --------------------------------------------------------------------------- #
# Graph model                                                                 #
# --------------------------------------------------------------------------- #

@dataclass
class Node:
    id: str
    title: str = ""
    year: Optional[int] = None
    doi: Optional[str] = None
    cited_by_count: int = 0
    role: str = "neighbor"  # seed | reference | citation | neighbor


@dataclass
class Graph:
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Tuple[str, str]] = field(default_factory=list)  # (citing, cited)
    _edge_set: set = field(default_factory=set)

    def add_node(self, node: Node) -> None:
        existing = self.nodes.get(node.id)
        if existing is None:
            self.nodes[node.id] = node
        else:
            # Seeds and richer metadata win.
            if node.role == "seed":
                existing.role = "seed"
            if node.title and not existing.title:
                existing.title = node.title
            if node.year and not existing.year:
                existing.year = node.year
            if node.doi and not existing.doi:
                existing.doi = node.doi
            if node.cited_by_count:
                existing.cited_by_count = max(existing.cited_by_count, node.cited_by_count)

    def add_edge(self, citing: str, cited: str) -> None:
        if not citing or not cited or citing == cited:
            return
        key = (citing, cited)
        if key in self._edge_set:
            return
        self._edge_set.add(key)
        self.edges.append(key)


def _mk_node(work: Dict[str, Any], role: str) -> Node:
    nid = work.get("id", "")
    doi = work.get("doi") or (nid if nid.startswith("10.") else None)
    return Node(id=nid, title=work.get("title") or "", year=work.get("year"), doi=doi,
                cited_by_count=work.get("cited_by_count") or 0, role=role)


# --------------------------------------------------------------------------- #
# Graph builder                                                               #
# --------------------------------------------------------------------------- #

def _expand_refs(client: CitationClient, graph: Graph, node_id: str, fatal: bool) -> None:
    """Add a work's references as backward edges (work -> reference)."""
    refs, answered, failed = fetch_references(client, node_id)
    if not answered and failed:
        msg = f"could not fetch the references of {node_id} ({'; '.join(failed)})"
        if fatal:
            raise urllib.error.URLError(msg)
        print(f"warning: {msg}; skipped", file=sys.stderr)
    for ref in refs:
        graph.add_node(_mk_node(ref, "reference"))
        graph.add_edge(node_id, ref["id"])


def build_graph(seeds: List[str], client: CitationClient, depth: int = 1, per_seed: int = 25) -> Graph:
    """Walk outward from each seed and assemble a citation graph.

    For every seed we add:
      - backward edges from the seed's reference list (seed -> reference),
      - forward edges from the works citing it      (citation -> seed),
    and the reference list of every citing work, which is what co-citation and
    bibliographic coupling are computed from. With ``depth >= 2`` the forward
    expansion is applied to first-hop citers too. ``per_seed`` caps the forward fan-out
    per work to keep the walk bounded and polite.

    A seed whose citing works or references no source could answer for stops the run
    (URLError) instead of yielding a silently truncated graph; deeper nodes warn and skip.
    """
    graph = Graph()
    seed_ids: List[str] = []
    for raw in seeds:
        nid = normalize_seed(raw)
        graph.add_node(Node(id=nid, doi=nid, role="seed"))
        if nid not in seed_ids:
            seed_ids.append(nid)
    for nid in seed_ids:
        _expand_refs(client, graph, nid, fatal=True)

    frontier = list(seed_ids)
    visited: set = set(seed_ids)
    for _level in range(max(1, depth)):
        next_frontier: List[str] = []
        for wid in frontier:
            citers, answered, failed = fetch_citers(client, wid, per_seed)
            if not answered:
                why = "; ".join(failed) or "it has no DOI or PMID the citation sources know"
                if wid in seed_ids:
                    raise urllib.error.URLError(f"no source could list the works citing seed {wid} ({why})")
                print(f"warning: could not fetch citers of {wid} ({why}); skipped", file=sys.stderr)
                continue
            for citer in citers:
                cnode = _mk_node(citer, "citation")
                if not cnode.id:
                    continue
                graph.add_node(cnode)
                graph.add_edge(cnode.id, wid)  # citer cites wid
                if cnode.id not in visited:
                    visited.add(cnode.id)
                    _expand_refs(client, graph, cnode.id, fatal=False)
                    next_frontier.append(cnode.id)
        frontier = next_frontier
    return graph


def hydrate(graph: Graph, ids: List[str], client: CitationClient) -> int:
    """Fill title / year / DOI / cited_by_count for nodes known only by their id.

    OpenCitations lists bare DOIs, so without this step the most co-cited works would print
    as untitled. Crossref answers first (40 DOIs per call, with its citation count); works it
    does not describe go to Semantic Scholar's batch endpoint, then doi.org content
    negotiation. Returns the number of nodes filled. A source that fails is skipped with a
    warning; the node keeps its id.
    """
    missing = [i for i in dict.fromkeys(ids) if i in graph.nodes and not graph.nodes[i].title]
    filled = 0

    def apply(works: List[Dict[str, Any]]) -> None:
        nonlocal filled
        for w in works:
            node = graph.nodes.get(w.get("id", ""))
            if node is None or not w.get("title"):
                continue
            if not node.title:
                filled += 1
            node.title = w["title"]
            node.year = w.get("year") or node.year
            node.doi = w.get("doi") or node.doi
            node.cited_by_count = max(node.cited_by_count, w.get("cited_by_count") or 0)

    def still() -> List[str]:
        return [i for i in missing if not graph.nodes[i].title]

    dois = [i for i in missing if i.startswith("10.") and not _ARXIV_DOI_RE.match(i)]
    if dois:
        try:
            apply(client.crossref_batch(dois))
        except _NET_ERRORS as exc:
            print(f"warning: Crossref titles unavailable ({exc}); trying Semantic Scholar", file=sys.stderr)
    if still():
        try:
            apply(client.s2_batch(still()))
        except _NET_ERRORS as exc:
            print(f"warning: Semantic Scholar metadata not checked ({exc})", file=sys.stderr)
    for nid in [i for i in still() if i.startswith("10.")][:50]:
        try:
            w = client.doi_csl(nid)
        except _NET_ERRORS:
            continue
        if w:
            apply([w])
    return filled


# --------------------------------------------------------------------------- #
# Co-citation ranking                                                         #
# --------------------------------------------------------------------------- #

def cocitation_ranking(graph: Graph, seeds: List[str], top: int = 25) -> List[Dict[str, Any]]:
    """Rank non-seed nodes by how strongly they co-cite with the seed set.

    Co-citation strength of a candidate node = the number of *distinct seeds*
    whose citation neighbourhood (the candidate's references plus the works that
    cite the candidate) overlaps the candidate. Concretely we score a node by:

      - shared_refs : how many seeds it shares a reference target with, and
      - shared_citers: how many seeds are co-cited *with* it by a common citer.

    The combined ``cocitation`` count is the primary sort key; ties break on the
    node's global ``cited_by_count`` so canonical works float up. This mirrors the
    co-citation analysis that powers ResearchRabbit's similarity panels.
    """
    seed_set = set(seeds)

    # adjacency: who each node cites, and who cites each node.
    cites: Dict[str, set] = {}
    cited_by: Dict[str, set] = {}
    for citing, cited in graph.edges:
        cites.setdefault(citing, set()).add(cited)
        cited_by.setdefault(cited, set()).add(citing)

    # References made by each seed, and citers of each seed.
    seed_refs = {s: cites.get(s, set()) for s in seed_set}
    seed_citers = {s: cited_by.get(s, set()) for s in seed_set}

    scores: Dict[str, Dict[str, Any]] = {}
    for nid, node in graph.nodes.items():
        if nid in seed_set:
            continue
        node_refs = cites.get(nid, set())
        node_citers = cited_by.get(nid, set())

        shared_refs = sum(1 for s in seed_set if seed_refs[s] & node_refs)
        # co-cited together: a citer that cites both this node and a seed.
        shared_citers = sum(1 for s in seed_set if seed_citers[s] & node_citers)
        # bibliographic coupling via direct seed adjacency.
        direct = sum(1 for s in seed_set if nid in seed_refs[s] or nid in seed_citers[s])

        cocite = shared_refs + shared_citers + direct
        if cocite <= 0:
            continue
        scores[nid] = {
            "id": nid,
            "title": node.title,
            "year": node.year,
            "doi": node.doi,
            "role": node.role,
            "cited_by_count": node.cited_by_count,
            "cocitation": cocite,
            "shared_refs": shared_refs,
            "shared_citers": shared_citers,
            "direct_seed_links": direct,
        }

    ranked = sorted(
        scores.values(),
        key=lambda r: (r["cocitation"], r["cited_by_count"]),
        reverse=True,
    )
    return ranked[: max(0, top)] if top else ranked


# --------------------------------------------------------------------------- #
# Export                                                                       #
# --------------------------------------------------------------------------- #

def to_graphml(graph: Graph) -> str:
    """Serialise the graph to GraphML (string) with node attribute keys."""
    ns = "http://graphml.graphdrawing.org/xmlns"
    ET.register_namespace("", ns)
    root = ET.Element(f"{{{ns}}}graphml")

    keys = [
        ("d_title", "title", "string"),
        ("d_year", "year", "long"),
        ("d_doi", "doi", "string"),
        ("d_role", "role", "string"),
        ("d_cited", "cited_by_count", "long"),
    ]
    for kid, name, typ in keys:
        k = ET.SubElement(root, f"{{{ns}}}key")
        k.set("id", kid)
        k.set("for", "node")
        k.set("attr.name", name)
        k.set("attr.type", typ)

    g = ET.SubElement(root, f"{{{ns}}}graph")
    g.set("edgedefault", "directed")

    for nid, node in graph.nodes.items():
        n = ET.SubElement(g, f"{{{ns}}}node")
        n.set("id", nid)
        _data(n, ns, "d_title", node.title)
        if node.year is not None:
            _data(n, ns, "d_year", str(node.year))
        if node.doi:
            _data(n, ns, "d_doi", node.doi)
        _data(n, ns, "d_role", node.role)
        _data(n, ns, "d_cited", str(node.cited_by_count))

    for i, (src, dst) in enumerate(graph.edges):
        e = ET.SubElement(g, f"{{{ns}}}edge")
        e.set("id", f"e{i}")
        e.set("source", src)
        e.set("target", dst)

    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")


def _data(parent: ET.Element, ns: str, key: str, value: str) -> None:
    d = ET.SubElement(parent, f"{{{ns}}}data")
    d.set("key", key)
    d.text = value


def to_json(graph: Graph, seeds: List[str], ranking: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "schema": "alterlab-citation-graph/1.0",
        "seeds": seeds,
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges),
        "nodes": [
            {
                "id": n.id,
                "title": n.title,
                "year": n.year,
                "doi": n.doi,
                "role": n.role,
                "cited_by_count": n.cited_by_count,
            }
            for n in graph.nodes.values()
        ],
        "edges": [{"source": s, "target": t} for s, t in graph.edges],
        "cocitation_ranking": ranking,
    }


def write_outputs(graph: Graph, seeds: List[str], ranking: List[Dict[str, Any]], out_base: str) -> Tuple[str, str]:
    graphml_path = out_base + ".graphml"
    json_path = out_base + ".json"
    out_dir = os.path.dirname(os.path.abspath(graphml_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(graphml_path, "w", encoding="utf-8") as fh:
        fh.write(to_graphml(graph))
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(to_json(graph, seeds, ranking), fh, indent=2, ensure_ascii=False)
    return graphml_path, json_path


# --------------------------------------------------------------------------- #
# Self-test (offline, no network)                                             #
# --------------------------------------------------------------------------- #

def _self_test() -> int:
    """Exercise the full pipeline against in-memory fakes of the keyless APIs."""
    # Seed S cites R10 and R11; A and B cite S and R10; arXiv preprint P cites S but
    # OpenCitations knows none of P's references, so they come from Semantic Scholar.
    seed, r10, r11, a, b = "10.1000/seed", "10.1000/r10", "10.1000/r11", "10.1000/a", "10.1000/b"
    p = arxiv_doi("2401.00001")
    oc_refs = {seed: [r10, r11], a: [seed, r10], b: [seed, r10], p: []}
    oc_cites = {seed: [a, b, p, "10.1000/capped"]}
    s2_refs = {"ARXIV:2401.00001": [{"externalIds": {"DOI": r10}, "title": "Shared reference",
                                     "year": 2015, "citationCount": 500}]}
    crossref = {r10: ("Shared reference", 2015, 500), seed: ("Seed paper", 2020, 99),
                a: ("Citing paper A", 2022, 5), b: ("Citing paper B", 2023, 3)}

    def oc_body(ids: List[str], field_name: str, me: str) -> List[Dict[str, str]]:
        # Real OpenCitations rows also list omid: and openalex: ids; only doi:/pmid: are used.
        other = "cited" if field_name == "citing" else "citing"
        return [{field_name: f"omid:br/{i} doi:{x} openalex:W{i}", other: f"doi:{me}"}
                for i, x in enumerate(ids)]

    def make_fetch(s2_rate_limited: bool) -> Callable[..., Any]:
        def fetch(url: str, data: Optional[dict] = None, accept: str = "") -> Any:
            calls.append(url)
            if url.startswith(OPENCITATIONS_BASE + "/references/doi:"):
                me = urllib.parse.unquote(url.split("/references/doi:", 1)[1])
                return oc_body(oc_refs.get(me, []), "cited", me)
            if url.startswith(S2_BASE):
                if s2_rate_limited:
                    raise urllib.error.HTTPError(url, 429, "Too Many Requests", None, None)
                if "/references?" in url:
                    sel = urllib.parse.unquote(url.split("/paper/", 1)[1].split("/references", 1)[0])
                    return {"data": [{"citedPaper": w} for w in s2_refs.get(sel, [])]}
                if "/citations?" in url:
                    return {"data": [{"citingPaper": {"externalIds": {"DOI": x}, "title": x}}
                                     for x in oc_cites[seed]]}
                return [None for _ in (data or {}).get("ids", [])]
            if url.startswith(CROSSREF_BASE):
                wanted = re.findall(r"doi:([^,&]+)", urllib.parse.unquote(url))
                return {"message": {"items": [
                    {"DOI": d, "title": [crossref[d][0]], "issued": {"date-parts": [[crossref[d][1]]]},
                     "is-referenced-by-count": crossref[d][2]} for d in wanted if d in crossref]}}
            if url.startswith("https://doi.org/"):
                raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
            raise AssertionError(f"unexpected URL {url}")
        return fetch

    def stream(url: str):
        calls.append(url)
        me = urllib.parse.unquote(url.split("/citations/doi:", 1)[1])
        body = json.dumps(oc_body(oc_cites.get(me, []), "citing", me)).encode()
        yield from (body[i:i + 40] for i in range(0, len(body), 40))  # split mid-record

    calls: List[str] = []
    client = CitationClient(_fetch=make_fetch(False), _stream=stream, _sleep=lambda s: None)
    graph = build_graph(["https://doi.org/10.1000/SEED"], client, depth=1, per_seed=3)

    assert graph.nodes[seed].role == "seed", "seed missing"
    assert (seed, r10) in graph._edge_set, "seed->reference edge missing"
    assert {(a, seed), (b, seed), (p, seed)} <= graph._edge_set, "citer->seed edge missing"
    assert "10.1000/capped" not in graph.nodes, "per-seed cap ignored on the stream"
    assert (p, r10) in graph._edge_set, "Semantic Scholar did not fill OpenCitations' gap"
    assert not any("openalex" in c for c in calls), "an OpenAlex URL was requested"

    ranking = cocitation_ranking(graph, [seed], top=10)
    ranked_ids = [r["id"] for r in ranking]
    assert r10 in ranked_ids, f"co-cited reference missing from ranking: {ranked_ids}"
    assert graph.nodes[a].title == "", "OpenCitations node unexpectedly pre-titled"
    assert hydrate(graph, [seed] + ranked_ids, client) >= 3, "hydration filled too little"
    assert graph.nodes[seed].title == "Seed paper" and graph.nodes[a].year == 2022
    ranking = cocitation_ranking(graph, [seed], top=10)
    assert ranking[0]["id"] == r10 and ranking[0]["cited_by_count"] == 500, ranking[0]

    parsed = ET.fromstring(to_graphml(graph))
    assert parsed.tag.endswith("graphml"), "GraphML root malformed"
    payload = json.loads(json.dumps(to_json(graph, [seed], ranking)))
    assert payload["node_count"] == len(graph.nodes) and payload["edge_count"] == len(graph.edges)
    assert payload["cocitation_ranking"], "empty ranking in JSON"

    # Semantic Scholar rate-limited throughout: backoff, then pause; OpenCitations still
    # answers, so the graph is built and only the preprint's references are not checked.
    calls.clear()
    slept: List[float] = []
    limited = CitationClient(_fetch=make_fetch(True), _stream=stream, _sleep=slept.append)
    g2 = build_graph([seed], limited, depth=1, per_seed=3)
    assert slept == list(S2_BACKOFF), f"no exponential backoff on 429: {slept}"
    assert limited.s2_skipped == [p], limited.s2_skipped
    assert {(a, seed), (b, seed), (seed, r10)} <= g2._edge_set and (p, r10) not in g2._edge_set

    # Citers from Semantic Scholar only.
    calls.clear()
    s2_only = CitationClient(_fetch=make_fetch(False), _stream=stream, citers_source="semanticscholar",
                             _sleep=lambda s: None)
    g3 = build_graph([seed], s2_only, depth=1, per_seed=2)
    assert {(a, seed), (b, seed)} <= g3._edge_set and (p, seed) not in g3._edge_set
    assert not any("/citations/" in c for c in calls), "OpenCitations used despite --citers-source"

    # normalize_seed coverage.
    assert normalize_seed("10.1038/nphys1170") == "10.1038/nphys1170"
    assert normalize_seed("https://doi.org/10.1038/X") == "10.1038/x"
    assert normalize_seed("arXiv:1706.03762v5") == "10.48550/arxiv.1706.03762"
    assert _s2_selector("10.48550/arxiv.1706.03762") == "ARXIV:1706.03762"
    for bad in ("not-an-id", "W2741809807"):
        try:
            normalize_seed(bad)
        except ValueError:
            pass
        else:  # pragma: no cover
            raise AssertionError(f"normalize_seed accepted {bad!r}")

    print("SELF-TEST OK:", len(graph.nodes), "nodes,", len(graph.edges), "edges,",
          len(ranking), "ranked")
    return 0


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build a citation / co-citation graph from seed DOIs with keyless open "
                    "citation data (OpenCitations, Semantic Scholar, Crossref).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--seed", action="append", default=[], metavar="DOI|arXiv",
                   help="seed work (repeatable): a DOI, DOI URL, or arXiv id.")
    p.add_argument("--citers-source", choices=["auto", "opencitations", "semanticscholar", "openalex"],
                   default="auto", metavar="{auto,opencitations,semanticscholar}",
                   help="where citing works come from: auto (default) = OpenCitations, then "
                        "Semantic Scholar for works it has none for; opencitations or "
                        "semanticscholar = that source only.")
    p.add_argument("--api-key", default=None, help=argparse.SUPPRESS)  # retired OpenAlex key: ignored
    p.add_argument("--mailto", default=None, help=argparse.SUPPRESS)  # retired: no source needs it
    p.add_argument("--depth", type=int, default=1,
                   help="how many citation hops to expand (default 1).")
    p.add_argument("--per-seed", type=int, default=25,
                   help="max citing works fetched per work (default 25).")
    p.add_argument("--top", type=int, default=25,
                   help="size of the co-citation ranking table (default 25).")
    p.add_argument("--out", default="citation_graph",
                   help="output basename; writes <out>.graphml and <out>.json.")
    p.add_argument("--sleep", type=float, default=0.0,
                   help="seconds to sleep after each API call (extra politeness throttle).")
    p.add_argument("--self-test", action="store_true",
                   help="run the offline self-test and exit (no network).")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    if args.self_test:
        return _self_test()

    if not args.seed:
        print("error: at least one --seed is required (or use --self-test).", file=sys.stderr)
        return 2
    if args.api_key or args.citers_source == "openalex":
        print("note: OpenAlex is no longer used (its keyless access is metered per IP); "
              "--api-key is ignored and --citers-source openalex runs as auto.", file=sys.stderr)
        args.citers_source = "auto" if args.citers_source == "openalex" else args.citers_source
    if args.mailto:
        print("note: --mailto is ignored; no source needs a contact address.", file=sys.stderr)
    s2_key = os.environ.get("S2_API_KEY") or os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    print("note: keyless run: edges from OpenCitations (Semantic Scholar where it has none), "
          "titles from Crossref" + (" (S2_API_KEY set: dedicated Semantic Scholar limit)." if s2_key
                                   else "; no account or key needed."), file=sys.stderr)

    client = CitationClient(sleep=args.sleep, citers_source=args.citers_source, s2_api_key=s2_key)
    try:
        graph = build_graph(args.seed, client, depth=args.depth, per_seed=args.per_seed)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except urllib.error.HTTPError as exc:
        print(f"error: HTTP {exc.code} — {exc.reason} ({exc.url})", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"error: network failure — {exc.reason}", file=sys.stderr)
        return 1

    seed_ids = [n.id for n in graph.nodes.values() if n.role == "seed"]
    ranking = cocitation_ranking(graph, seed_ids, top=args.top)
    # OpenCitations nodes carry only DOIs; fetch titles for the seeds and ranked works,
    # then re-rank because hydrated cited_by_count values break ties.
    if hydrate(graph, seed_ids + [r["id"] for r in ranking], client):
        ranking = cocitation_ranking(graph, seed_ids, top=args.top)
    if client.s2_skipped:
        print(f"note: Semantic Scholar was rate-limited (HTTP 429) for {len(client.s2_skipped)} "
              "lookup(s), which were not checked: " + ", ".join(client.s2_skipped[:8])
              + (" ..." if len(client.s2_skipped) > 8 else ""), file=sys.stderr)
    graphml_path, json_path = write_outputs(graph, args.seed, ranking, args.out)

    print(f"nodes={len(graph.nodes)} edges={len(graph.edges)} ranked={len(ranking)}")
    print(f"wrote {graphml_path}")
    print(f"wrote {json_path}")
    if ranking:
        print("\nTop co-citation neighbours:")
        for r in ranking[:10]:
            title = (r["title"] or "(untitled)")[:70]
            print(f"  {r['cocitation']:>3}  {r['id']:<30} {title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
