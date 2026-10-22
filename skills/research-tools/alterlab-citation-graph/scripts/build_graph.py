#!/usr/bin/env python3
"""Build a citation/co-citation graph from a seed DOI using open citation data.

A free ResearchRabbit analog that needs no API key. Starting from one or more
seed works (DOI, OpenAlex ID, or arXiv ID), this walks the citation graph in
both directions:

  - references  (works the seed *cites*, i.e. its backward edges), and
  - citations   (works that *cite* the seed, i.e. its forward / "cited_by" edges).

It then ranks the discovered neighbourhood by **co-citation strength** — how many
of the seed set a candidate work connects to — surfacing the papers most central
to the seed's local literature, like ResearchRabbit's "Similar Work" panels but
with no subscription.

Data sources, all keyless (policy checked 2026-10-22):
  - OpenAlex single-work lookups (/works/<id>) are free and unmetered: seeds,
    their referenced_works, citer metadata and title hydration can all use them.
  - OpenAlex list/filter calls (cites:, openalex:A|B) cost $0.0001 each against a
    daily budget. Keyless calls share $0.10/day per IP address (`mailto=` no
    longer changes that), which a campus or cloud network often spends early
    (HTTP 429 "Insufficient budget"). A free key (OPENALEX_API_KEY, from
    https://openalex.org/settings/api) gives a private $1/day; it is optional.
  - OpenCitations Index v2 (api.opencitations.net) lists the works citing a DOI
    with their OpenAlex ids, no key. Its answer is one unpaginated JSON array, so
    the script reads it as a stream and stops after --per-seed records.
With --citers-source auto (default) the walk uses OpenAlex list calls while they
work and switches to OpenCitations plus free single-work lookups when a list call
returns 429, saying so on stderr. The key, when set, is sent as a Bearer header.

Outputs:
  - GraphML (.graphml)  — open in Gephi / Cytoscape / yEd / networkx.
  - JSON    (.json)     — nodes + edges + ranked co-citation table, for code.

Stdlib only (urllib, json, argparse) — no third-party dependency, so it runs in
a bare `uv run python` with nothing installed.

Examples
--------
    # One seed DOI, default depth, write both formats next to a basename:
    export OPENALEX_API_KEY=...        # free; recommended
    uv run python build_graph.py --seed 10.1038/nphys1170 --out graph/seed1

    # Several seeds (mix DOI / OpenAlex / arXiv), deeper walk, more neighbours:
    uv run python build_graph.py \
        --seed 10.1038/nphys1170 --seed W2741809807 --seed arXiv:2310.06825 \
        --depth 2 --per-seed 50 --top 40 --out graph/transformer

    # Never touch the metered OpenAlex list budget (citers from OpenCitations):
    uv run python build_graph.py --seed 10.1038/nature14539 --citers-source opencitations

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
from typing import Any, Dict, List, Optional, Tuple

OPENALEX_BASE = "https://api.openalex.org/works"
OPENCITATIONS_BASE = "https://api.opencitations.net/index/v2"
USER_AGENT = "alterlab-citation-graph/1.2 (https://github.com/AlterLab-IEU)"
DEFAULT_TIMEOUT = 30
# OpenAlex caps per_page (and OR-values per filter) at 100; 200 is deprecated legacy.
MAX_PER_PAGE = 100
# Fields a single-work lookup needs for a graph node plus its backward edges.
WORK_FIELDS = "id,doi,title,publication_year,cited_by_count,referenced_works,ids"
_CITING_RE = re.compile(r'"citing"\s*:\s*"([^"]*)"')
_OC_OPENALEX_RE = re.compile(r"\bopenalex:(W\d+)")
_OC_DOI_RE = re.compile(r"\bdoi:(10\.\S+)")


# --------------------------------------------------------------------------- #
# Seed normalisation                                                          #
# --------------------------------------------------------------------------- #

_DOI_RE = re.compile(r"10\.\d{4,9}/\S+", re.IGNORECASE)
_OPENALEX_ID_RE = re.compile(r"^W\d+$", re.IGNORECASE)
_ARXIV_RE = re.compile(r"^(arxiv:)?(\d{4}\.\d{4,5})(v\d+)?$", re.IGNORECASE)


def normalize_seed(raw: str) -> str:
    """Turn a user-supplied seed into an OpenAlex `/works/<id>` selector.

    Accepts a bare DOI, a DOI URL, an OpenAlex work ID (W...), an OpenAlex URL,
    or an arXiv ID (with or without the ``arXiv:`` prefix). Raises ValueError on
    anything unrecognisable.
    """
    s = raw.strip()
    if not s:
        raise ValueError("empty seed")

    # Full OpenAlex URL -> trailing work id.
    if "openalex.org/" in s.lower():
        s = s.rstrip("/").split("/")[-1]

    if _OPENALEX_ID_RE.match(s):
        return s.upper()

    # arXiv -> OpenAlex indexes arXiv preprints under their DataCite DOI
    # (10.48550/arXiv.<id>), so resolve via the DOI namespace. The bare
    # https://arxiv.org/abs/<id> URL is NOT an OpenAlex selector and 404s.
    # Coverage caveat: if a preprint was later merged into a published-version
    # record, OpenAlex may carry only the publisher DOI; pass that DOI instead.
    m = _ARXIV_RE.match(s)
    if m:
        return f"https://doi.org/10.48550/arXiv.{m.group(2)}"

    # DOI URL or bare DOI.
    doi = s
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.lower().startswith(prefix):
            doi = doi[len(prefix):]
            break
    if _DOI_RE.search(doi):
        return f"https://doi.org/{doi}"

    raise ValueError(f"unrecognised seed (not a DOI, OpenAlex W-id, or arXiv id): {raw!r}")


# --------------------------------------------------------------------------- #
# OpenAlex client                                                             #
# --------------------------------------------------------------------------- #

@dataclass
class OpenAlexClient:
    api_key: Optional[str] = None  # optional free key from openalex.org/settings/api
    timeout: int = DEFAULT_TIMEOUT
    sleep: float = 0.0  # optional inter-request delay (OpenAlex allows <=100 req/s)
    citers_source: str = "auto"  # auto | openalex | opencitations
    _fetch: Optional[Any] = None  # injectable for tests: url -> parsed JSON
    _stream: Optional[Any] = None  # injectable for tests: url -> iterable of byte chunks
    list_budget_spent: bool = False  # set once a keyless list call returns 429

    @staticmethod
    def _params(extra: Dict[str, str]) -> str:
        return urllib.parse.urlencode(extra)

    def _get(self, url: str) -> Dict[str, Any]:
        if self._fetch is not None:  # test seam
            return self._fetch(url)
        headers = {"User-Agent": USER_AGENT}
        if self.api_key and url.startswith(OPENALEX_BASE):
            # Bearer header rather than ?api_key= so the key never shows up in
            # logged or printed URLs, and only ever sent to OpenAlex.
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            payload = resp.read().decode("utf-8")
        if self.sleep:
            time.sleep(self.sleep)
        return json.loads(payload)

    def get_work(self, selector: str, select: Optional[str] = None) -> Dict[str, Any]:
        """Fetch a single work by OpenAlex id / DOI url / arXiv url selector (free call)."""
        quoted = urllib.parse.quote(selector, safe=":/")
        url = f"{OPENALEX_BASE}/{quoted}"
        if select:
            url += "?" + self._params({"select": select})
        return self._get(url)

    def opencitations_citers(self, ids: List[str], limit: int) -> List[str]:
        """Keyless forward edges: up to `limit` works citing any of `ids` (``doi:``/``pmid:``).

        Returns OpenAlex selectors (W-ids, or DOI URLs when OpenCitations has no
        OpenAlex id for the citer). The endpoint returns every citation as one
        unpaginated array — tens of thousands for a classic paper — so the body is
        read in chunks and the connection closed once `limit` citers are found.
        """
        found: List[str] = []
        seen: set = set()
        for oc_id in ids:
            url = f"{OPENCITATIONS_BASE}/citations/{urllib.parse.quote(oc_id, safe=':/')}"
            decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
            buf = ""
            try:
                for chunk in self._chunks(url):
                    buf += decoder.decode(chunk)
                    last = 0
                    for m in _CITING_RE.finditer(buf):
                        last = m.end()
                        w = _OC_OPENALEX_RE.search(m.group(1))
                        d = _OC_DOI_RE.search(m.group(1))
                        sel = w.group(1) if w else (f"https://doi.org/{d.group(1)}" if d else "")
                        if sel and sel not in seen:
                            seen.add(sel)
                            found.append(sel)
                        if len(found) >= limit:
                            return found
                    buf = buf[last:]
            except (OSError, http.client.HTTPException):
                if not found:
                    raise  # nothing usable; a cut after some records still counts
            if found:
                return found  # first id that OpenCitations knows is enough
        return found

    def _chunks(self, url: str, size: int = 65536):
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

    def cited_by(self, openalex_id: str, per_page: int) -> List[Dict[str, Any]]:
        """Forward edges: works that cite `openalex_id` (its cited_by set)."""
        per_page = max(1, min(per_page, MAX_PER_PAGE))
        qs = self._params(
            {
                "filter": f"cites:{openalex_id}",
                "per_page": str(per_page),
                "select": "id,doi,title,publication_year,cited_by_count,referenced_works",
            }
        )
        data = self._get(f"{OPENALEX_BASE}?{qs}")
        return data.get("results", [])

    def get_many(self, ids: List[str]) -> List[Dict[str, Any]]:
        """Batch-fetch metadata for W-ids: one OR-filter list call per 100 ids."""
        out: List[Dict[str, Any]] = []
        for start in range(0, len(ids), MAX_PER_PAGE):
            chunk = ids[start:start + MAX_PER_PAGE]
            qs = self._params(
                {
                    "filter": "openalex:" + "|".join(chunk),
                    "per_page": str(len(chunk)),
                    "select": "id,doi,title,publication_year,cited_by_count",
                }
            )
            out.extend(self._get(f"{OPENALEX_BASE}?{qs}").get("results", []))
        return out

    def get_many_singly(self, ids: List[str]) -> List[Dict[str, Any]]:
        """Keyless hydration: one free single-work lookup per W-id (no list budget used)."""
        out: List[Dict[str, Any]] = []
        for wid in ids:
            try:
                out.append(self.get_work(wid, select="id,doi,title,publication_year,cited_by_count"))
            except urllib.error.URLError as exc:  # includes HTTPError
                print(f"warning: could not look up {wid} ({exc}); left untitled", file=sys.stderr)
        return out

    def note_list_budget_spent(self) -> None:
        if not self.list_budget_spent:
            self.list_budget_spent = True
            who = "this key's" if self.api_key else "the shared per-IP (keyless)"
            print(f"note: OpenAlex list calls returned HTTP 429 ({who} daily budget is spent); "
                  "continuing keyless: citing works from OpenCitations, metadata from free "
                  "OpenAlex single-work lookups.", file=sys.stderr)


def _oc_ids(work: Dict[str, Any], raw_seed: Optional[str] = None) -> List[str]:
    """OpenCitations identifiers to try for a work: the DOI the user gave, OpenAlex's DOI, PMID."""
    ids: List[str] = []
    if raw_seed:
        sel = normalize_seed(raw_seed)
        if sel.startswith("https://doi.org/"):
            ids.append("doi:" + sel[len("https://doi.org/"):].lower())
    doi = (work.get("doi") or "").lower()
    if doi.startswith("https://doi.org/"):
        ids.append("doi:" + doi[len("https://doi.org/"):])
    pmid = ((work.get("ids") or {}).get("pmid") or "").rstrip("/").split("/")[-1]
    if pmid.isdigit():
        ids.append("pmid:" + pmid)
    return list(dict.fromkeys(ids))


def fetch_citers(client: OpenAlexClient, wid: str, oc_ids: List[str], per_seed: int) -> List[Dict[str, Any]]:
    """Works citing `wid`, as OpenAlex work dicts (with referenced_works).

    OpenAlex ``cites:`` list call first (unless --citers-source opencitations, or an
    earlier call already hit 429); on 429 switch to OpenCitations for the citer ids
    and free single-work lookups for their metadata. Raises the last error when no
    source answers, so a seed never silently loses its forward edges.
    """
    use_openalex = client.citers_source == "openalex" or (
        client.citers_source == "auto" and not client.list_budget_spent)
    if use_openalex:
        try:
            return client.cited_by(wid, per_page=per_seed)
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or client.citers_source == "openalex":
                raise
            client.note_list_budget_spent()
    if not oc_ids:
        raise ValueError(f"{wid} has no DOI or PMID, so OpenCitations cannot list its citers")
    try:
        selectors = client.opencitations_citers(oc_ids, per_seed)
    except (urllib.error.URLError, OSError) as exc:  # OSError covers a stream cut mid-read
        raise urllib.error.URLError(f"OpenCitations: {exc}") from exc
    works: List[Dict[str, Any]] = []
    for sel in selectors:
        try:
            works.append(client.get_work(sel, select=WORK_FIELDS))
        except urllib.error.URLError as exc:
            print(f"warning: could not look up citer {sel} ({exc}); skipped", file=sys.stderr)
    return works


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


def _short_id(openalex_url: str) -> str:
    """OpenAlex ids are URLs; keep the bare W-id for compactness."""
    if not openalex_url:
        return ""
    return openalex_url.rstrip("/").split("/")[-1]


def _mk_node(work: Dict[str, Any], role: str) -> Node:
    return Node(
        id=_short_id(work.get("id", "")),
        title=work.get("title") or work.get("display_name") or "",
        year=work.get("publication_year"),
        doi=work.get("doi"),
        cited_by_count=work.get("cited_by_count") or 0,
        role=role,
    )


# --------------------------------------------------------------------------- #
# Graph builder                                                               #
# --------------------------------------------------------------------------- #

def build_graph(
    seeds: List[str],
    client: OpenAlexClient,
    depth: int = 1,
    per_seed: int = 25,
) -> Graph:
    """Walk OpenAlex outward from each seed and assemble a citation graph.

    For every seed we add:
      - backward edges from the seed's ``referenced_works`` (seed -> reference),
      - forward edges from the seed's cited_by set    (citation -> seed).

    With ``depth >= 2`` the same expansion is applied to first-hop neighbours,
    growing the local neighbourhood. ``per_seed`` caps the forward fan-out per
    work to keep the walk bounded and polite.
    """
    graph = Graph()
    seed_ids: List[str] = []
    oc_ids: Dict[str, List[str]] = {}  # OpenCitations ids per node, for the keyless route

    # Resolve seeds first so we have canonical OpenAlex ids to expand from.
    # Single-work lookups are free, even when the keyless list budget is spent.
    frontier: List[str] = []
    for raw in seeds:
        selector = normalize_seed(raw)
        work = client.get_work(selector)
        node = _mk_node(work, "seed")
        if not node.id:
            continue
        graph.add_node(node)
        seed_ids.append(node.id)
        frontier.append(node.id)
        oc_ids[node.id] = _oc_ids(work, raw)
        _expand_work(work, graph)

    visited: set = set(seed_ids)
    for _level in range(max(0, depth - 1) + 1):
        next_frontier: List[str] = []
        for wid in frontier:
            # Forward edges: who cites this work.
            try:
                citers = fetch_citers(client, wid, oc_ids.get(wid, []), per_seed)
            except (urllib.error.URLError, ValueError) as exc:
                if wid in seed_ids:
                    # A seed with no forward edges is a broken graph: stop instead
                    # of silently writing a truncated one.
                    raise
                print(f"warning: could not fetch citers of {wid} ({exc}); skipped",
                      file=sys.stderr)
                citers = []
            for citer in citers:
                cnode = _mk_node(citer, "citation")
                if not cnode.id:
                    continue
                graph.add_node(cnode)
                graph.add_edge(cnode.id, wid)  # citer cites wid
                _expand_work(citer, graph, mark_refs="reference")
                if cnode.id not in visited:
                    next_frontier.append(cnode.id)
                    visited.add(cnode.id)
                    oc_ids[cnode.id] = _oc_ids(citer)
        if _level + 1 >= depth:
            break
        frontier = next_frontier

    return graph


def hydrate(graph: Graph, ids: List[str], client: OpenAlexClient) -> int:
    """Fill title/year/DOI/cited_by_count for nodes known only by their W-id.

    Reference nodes come from ``referenced_works``, which lists bare ids, so
    without this step the most co-cited works would print as untitled. Costs one
    list call per 100 ids; once the list budget is spent (or with --citers-source
    opencitations) it uses one free single-work lookup per id instead. Returns the
    number of nodes filled.
    """
    missing = [i for i in dict.fromkeys(ids) if i in graph.nodes and not graph.nodes[i].title]
    filled = 0
    works: List[Dict[str, Any]] = []
    if missing and (client.list_budget_spent or client.citers_source == "opencitations"):
        works = client.get_many_singly(missing)
    elif missing:
        try:
            works = client.get_many(missing)
        except urllib.error.HTTPError as exc:
            if exc.code != 429:
                raise
            client.note_list_budget_spent()
            works = client.get_many_singly(missing)
    for work in works:
        node = graph.nodes.get(_short_id(work.get("id", "")))
        if node is None:
            continue
        node.title = work.get("title") or work.get("display_name") or node.title
        node.year = work.get("publication_year") or node.year
        node.doi = work.get("doi") or node.doi
        node.cited_by_count = max(node.cited_by_count, work.get("cited_by_count") or 0)
        filled += 1
    return filled


def _expand_work(work: Dict[str, Any], graph: Graph, mark_refs: str = "reference") -> None:
    """Add a work's ``referenced_works`` as backward edges (work -> reference)."""
    src = _short_id(work.get("id", ""))
    if not src:
        return
    for ref_url in work.get("referenced_works", []) or []:
        ref_id = _short_id(ref_url)
        if not ref_id:
            continue
        graph.add_node(Node(id=ref_id, role=mark_refs))
        graph.add_edge(src, ref_id)


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
    """Exercise the full pipeline against an in-memory fake OpenAlex."""
    # Fake corpus: seed W1 cites W10, W11; W20 and W21 cite W1; both also cite W10.
    works = {
        "https://api.openalex.org/works/W1": {
            "id": "https://openalex.org/W1",
            "doi": "https://doi.org/10.1000/seed",
            "title": "Seed paper",
            "publication_year": 2020,
            "cited_by_count": 99,
            "referenced_works": ["https://openalex.org/W10", "https://openalex.org/W11"],
        },
    }
    cites_index = {
        "W1": [
            {
                "id": "https://openalex.org/W20",
                "title": "Citing paper A",
                "publication_year": 2022,
                "cited_by_count": 5,
                "referenced_works": ["https://openalex.org/W1", "https://openalex.org/W10"],
            },
            {
                "id": "https://openalex.org/W21",
                "title": "Citing paper B",
                "publication_year": 2023,
                "cited_by_count": 3,
                "referenced_works": ["https://openalex.org/W1", "https://openalex.org/W10"],
            },
        ]
    }

    batch_index = {
        "W10": {
            "id": "https://openalex.org/W10",
            "doi": "https://doi.org/10.1000/shared",
            "title": "Shared reference",
            "publication_year": 2015,
            "cited_by_count": 500,
        },
    }

    def fake_fetch(url: str) -> Dict[str, Any]:
        if "filter=cites%3A" in url or "filter=cites:" in url:
            wid = re.search(r"cites%3A(W\d+)|cites:(W\d+)", url)
            key = (wid.group(1) or wid.group(2)) if wid else ""
            return {"results": cites_index.get(key, [])}
        if "filter=openalex%3A" in url or "filter=openalex:" in url:
            wanted = set(re.findall(r"W\d+", urllib.parse.unquote(url.split("filter=", 1)[1])))
            return {"results": [w for k, w in batch_index.items() if k in wanted]}
        for selector, work in works.items():
            if url.startswith(selector):
                return work
        # DOI/normalised selector path.
        return works["https://api.openalex.org/works/W1"]

    client = OpenAlexClient(_fetch=fake_fetch)
    graph = build_graph(["10.1000/seed"], client, depth=1, per_seed=10)

    assert "W1" in graph.nodes, "seed missing"
    assert graph.nodes["W1"].role == "seed"
    assert ("W1", "W10") in graph._edge_set, "seed->reference edge missing"
    assert ("W20", "W1") in graph._edge_set, "citer->seed edge missing"
    assert ("W21", "W1") in graph._edge_set, "citer->seed edge missing"

    ranking = cocitation_ranking(graph, ["W1"], top=10)
    # W10 is co-cited by W20 and W21 alongside the seed -> should rank.
    ranked_ids = {r["id"] for r in ranking}
    assert "W10" in ranked_ids, f"co-cited W10 missing from ranking: {ranked_ids}"

    # Reference-only nodes arrive untitled; hydration fills them in one batch call.
    assert graph.nodes["W10"].title == "", "reference node unexpectedly pre-titled"
    assert hydrate(graph, [r["id"] for r in ranking], client) == 1, "hydration filled nothing"
    assert graph.nodes["W10"].title == "Shared reference", "W10 title not hydrated"
    ranking = cocitation_ranking(graph, ["W1"], top=10)
    assert any(r["id"] == "W10" and r["title"] for r in ranking), "hydrated title not ranked"

    graphml = to_graphml(graph)
    parsed = ET.fromstring(graphml)
    assert parsed.tag.endswith("graphml"), "GraphML root malformed"

    payload = to_json(graph, ["W1"], ranking)
    round_trip = json.loads(json.dumps(payload))
    assert round_trip["node_count"] == len(graph.nodes)
    assert round_trip["edge_count"] == len(graph.edges)
    assert round_trip["cocitation_ranking"], "empty ranking in JSON"

    # Keyless fallback: every list call answers 429 (shared per-IP budget spent), so
    # citers must come from a streamed OpenCitations answer and metadata from free
    # single-work lookups -- the same edges and ranking as the list-call route.
    singles = {f"https://api.openalex.org/works/{c['id'].split('/')[-1]}": c
               for c in cites_index["W1"]}
    singles.update({f"https://api.openalex.org/works/{k}": w for k, w in batch_index.items()})
    singles["https://api.openalex.org/works/W11"] = {
        "id": "https://openalex.org/W11", "title": "Other reference", "cited_by_count": 7}
    oc_calls: List[str] = []

    def fetch_429(url: str) -> Dict[str, Any]:
        if "filter=" in url:
            raise urllib.error.HTTPError(url, 429, "Insufficient budget", None, None)
        for selector, work in singles.items():
            if url.startswith(selector + "?") or url == selector:
                return work
        if "/works/W" in url:
            raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
        return works["https://api.openalex.org/works/W1"]

    def stream(url: str):
        oc_calls.append(url)
        body = ('[{"oci":"1-2","citing":"omid:br/1 openalex:W20 doi:10.1000/a",'
                '"cited":"doi:10.1000/seed"},{"oci":"3-2","citing":"omid:br/3 doi:10.1000/b '
                'openalex:W21","cited":"doi:10.1000/seed"},{"oci":"4-2","citing":"omid:br/4 '
                'openalex:W99","cited":"doi:10.1000/seed"}]').encode()
        yield from (body[i:i + 40] for i in range(0, len(body), 40))  # split mid-record

    keyless = OpenAlexClient(_fetch=fetch_429, _stream=stream)
    g2 = build_graph(["10.1000/seed"], keyless, depth=1, per_seed=2)
    assert keyless.list_budget_spent, "429 did not switch to the keyless route"
    assert oc_calls and oc_calls[0].endswith("/citations/doi:10.1000/seed"), oc_calls
    assert {("W20", "W1"), ("W21", "W1")} <= g2._edge_set, "OpenCitations citers missing"
    assert "W99" not in g2.nodes, "per-seed cap ignored on the stream"
    r2 = cocitation_ranking(g2, ["W1"], top=10)
    assert hydrate(g2, [r["id"] for r in r2], keyless) == 2, "single-lookup hydration failed"
    assert g2.nodes["W10"].title == "Shared reference"
    assert [r["id"] for r in cocitation_ranking(g2, ["W1"], top=10)] == \
        [r["id"] for r in cocitation_ranking(graph, ["W1"], top=10)], "routes rank differently"

    # normalize_seed coverage.
    assert normalize_seed("W2741809807") == "W2741809807"
    assert normalize_seed("10.1038/nphys1170") == "https://doi.org/10.1038/nphys1170"
    assert normalize_seed("https://doi.org/10.1038/x") == "https://doi.org/10.1038/x"
    assert normalize_seed("arXiv:1706.03762") == "https://doi.org/10.48550/arXiv.1706.03762"
    try:
        normalize_seed("not-an-id")
    except ValueError:
        pass
    else:  # pragma: no cover
        raise AssertionError("normalize_seed accepted garbage")

    print("SELF-TEST OK:", len(graph.nodes), "nodes,", len(graph.edges), "edges,",
          len(ranking), "ranked")
    return 0


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build an OpenAlex citation / co-citation graph from seed DOIs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--seed", action="append", default=[], metavar="DOI|W-id|arXiv",
                   help="seed work (repeatable): a DOI, OpenAlex W-id, or arXiv id.")
    p.add_argument("--api-key", default=os.environ.get("OPENALEX_API_KEY"),
                   help="optional OpenAlex API key (free at openalex.org/settings/api): a private "
                        "daily budget for list calls. Not needed; prefer the OPENALEX_API_KEY env "
                        "var so a key stays out of shell history.")
    p.add_argument("--citers-source", choices=["auto", "openalex", "opencitations"], default="auto",
                   help="where citing works come from: auto (default) = OpenAlex list calls, "
                        "switching to OpenCitations when they return 429; openalex = list calls "
                        "only; opencitations = never spend the OpenAlex list budget.")
    p.add_argument("--mailto", default=None,
                   help="deprecated no-op: OpenAlex has ignored mailto since Feb 2026, when "
                        "API keys replaced the polite pool. Accepted so older commands still run.")
    p.add_argument("--depth", type=int, default=1,
                   help="how many citation hops to expand (default 1).")
    p.add_argument("--per-seed", type=int, default=25,
                   help="max citing works fetched per work (default 25, OpenAlex max 100).")
    p.add_argument("--top", type=int, default=25,
                   help="size of the co-citation ranking table (default 25).")
    p.add_argument("--out", default="citation_graph",
                   help="output basename; writes <out>.graphml and <out>.json.")
    p.add_argument("--sleep", type=float, default=0.0,
                   help="seconds to sleep between API calls (throttle; OpenAlex allows <=100 req/s).")
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
    if args.mailto:
        print("note: --mailto is ignored by OpenAlex since Feb 2026 (it changes no limit); "
              "nothing else is needed.", file=sys.stderr)
    if not args.api_key:
        print("note: keyless mode (no OPENALEX_API_KEY). Single-work lookups are free; if the "
              "shared per-IP list budget is spent (HTTP 429), citing works come from "
              "OpenCitations instead. An optional free key only adds a private budget.",
              file=sys.stderr)

    client = OpenAlexClient(api_key=args.api_key, sleep=args.sleep,
                            citers_source=args.citers_source)
    try:
        graph = build_graph(args.seed, client, depth=args.depth, per_seed=args.per_seed)
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            print("error: OpenAlex HTTP 429 with --citers-source openalex (daily list budget "
                  "spent). Rerun with --citers-source auto or opencitations (keyless), or "
                  "retry after midnight UTC.", file=sys.stderr)
        else:
            print(f"error: HTTP {exc.code} — {exc.reason} ({exc.url})", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"error: network failure — {exc.reason}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    seed_ids = [n.id for n in graph.nodes.values() if n.role == "seed"]
    ranking = cocitation_ranking(graph, seed_ids, top=args.top)
    try:
        # Reference nodes carry only W-ids; fetch titles for the ranked ones, then
        # re-rank because hydrated cited_by_count values break ties.
        if hydrate(graph, [r["id"] for r in ranking], client):
            ranking = cocitation_ranking(graph, seed_ids, top=args.top)
    except urllib.error.URLError as exc:  # includes HTTPError (e.g. 429)
        print(f"warning: could not fetch titles for ranked works ({exc}); "
              "writing W-ids only.", file=sys.stderr)
    graphml_path, json_path = write_outputs(graph, args.seed, ranking, args.out)

    print(f"nodes={len(graph.nodes)} edges={len(graph.edges)} ranked={len(ranking)}")
    print(f"wrote {graphml_path}")
    print(f"wrote {json_path}")
    if ranking:
        print("\nTop co-citation neighbours:")
        for r in ranking[:10]:
            title = (r["title"] or "(untitled)")[:70]
            print(f"  {r['cocitation']:>3}  {r['id']:<14} {title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
