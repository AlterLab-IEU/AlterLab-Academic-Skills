#!/usr/bin/env python3
"""Build a citation/co-citation graph from a seed DOI using the free OpenAlex API.

A free, key-less ResearchRabbit analog. Starting from one or more seed works
(DOI, OpenAlex ID, or arXiv ID), this walks the OpenAlex citation graph in both
directions:

  - references  (works the seed *cites*, i.e. its backward edges), and
  - citations   (works that *cite* the seed, i.e. its forward / "cited_by" edges).

It then ranks the discovered neighbourhood by **co-citation strength** — how many
of the seed set a candidate work connects to — surfacing the papers most central
to the seed's local literature, exactly like ResearchRabbit's "Similar Work" /
"These authors" panels but with no account, no API key, and no rate-limit cost.

OpenAlex etiquette: this is the *polite pool*. Pass --mailto (or set the
OPENALEX_MAILTO env var) so requests carry a `mailto=` parameter; OpenAlex then
gives you faster, more reliable service. No API key exists or is required.

Outputs:
  - GraphML (.graphml)  — open in Gephi / Cytoscape / yEd / networkx.
  - JSON    (.json)     — nodes + edges + ranked co-citation table, for code.

Stdlib only (urllib, json, argparse) — no third-party dependency, so it runs in
a bare `uv run python` with nothing installed.

Examples
--------
    # One seed DOI, default depth, write both formats next to a basename:
    uv run python build_graph.py --seed 10.1038/nphys1170 \
        --mailto alterlab.ieu@gmail.com --out graph/seed1

    # Several seeds (mix DOI / OpenAlex / arXiv), deeper walk, more neighbours:
    uv run python build_graph.py \
        --seed 10.1038/nphys1170 --seed W2741809807 --seed arXiv:2310.06825 \
        --depth 2 --per-seed 50 --top 40 --mailto alterlab.ieu@gmail.com \
        --out graph/transformer

    # Offline / CI smoke test with no network:
    uv run python build_graph.py --self-test
"""

from __future__ import annotations

import argparse
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
USER_AGENT = "alterlab-citation-graph/1.0 (https://github.com/AlterLab-IEU)"
DEFAULT_TIMEOUT = 30


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
    mailto: Optional[str] = None
    timeout: int = DEFAULT_TIMEOUT
    sleep: float = 0.0  # polite inter-request delay
    _fetch: Optional[Any] = None  # injectable for tests

    def _params(self, extra: Dict[str, str]) -> str:
        params = dict(extra)
        if self.mailto:
            params["mailto"] = self.mailto
        return urllib.parse.urlencode(params)

    def _get(self, url: str) -> Dict[str, Any]:
        if self._fetch is not None:  # test seam
            return self._fetch(url)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            payload = resp.read().decode("utf-8")
        if self.sleep:
            time.sleep(self.sleep)
        return json.loads(payload)

    def get_work(self, selector: str) -> Dict[str, Any]:
        """Fetch a single work by OpenAlex id / DOI url / arXiv url selector."""
        quoted = urllib.parse.quote(selector, safe=":/")
        url = f"{OPENALEX_BASE}/{quoted}?{self._params({})}"
        return self._get(url)

    def cited_by(self, openalex_id: str, per_page: int) -> List[Dict[str, Any]]:
        """Forward edges: works that cite `openalex_id` (its cited_by set)."""
        per_page = max(1, min(per_page, 200))
        qs = self._params(
            {
                "filter": f"cites:{openalex_id}",
                "per-page": str(per_page),
                "select": "id,doi,title,publication_year,cited_by_count,referenced_works",
            }
        )
        data = self._get(f"{OPENALEX_BASE}?{qs}")
        return data.get("results", [])


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

    # Resolve seeds first so we have canonical OpenAlex ids to expand from.
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
        _expand_work(work, graph)

    visited: set = set(seed_ids)
    for _level in range(max(0, depth - 1) + 1):
        next_frontier: List[str] = []
        for wid in frontier:
            # Forward edges: who cites this work.
            try:
                citers = client.cited_by(wid, per_page=per_seed)
            except urllib.error.URLError:
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
        if _level + 1 >= depth:
            break
        frontier = next_frontier

    return graph


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

    def fake_fetch(url: str) -> Dict[str, Any]:
        if "filter=cites%3A" in url or "filter=cites:" in url:
            wid = re.search(r"cites%3A(W\d+)|cites:(W\d+)", url)
            key = (wid.group(1) or wid.group(2)) if wid else ""
            return {"results": cites_index.get(key, [])}
        for selector, work in works.items():
            if url.startswith(selector):
                return work
        # DOI/normalised selector path.
        return works["https://api.openalex.org/works/W1"]

    client = OpenAlexClient(mailto="test@example.com", _fetch=fake_fetch)
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

    graphml = to_graphml(graph)
    parsed = ET.fromstring(graphml)
    assert parsed.tag.endswith("graphml"), "GraphML root malformed"

    payload = to_json(graph, ["W1"], ranking)
    round_trip = json.loads(json.dumps(payload))
    assert round_trip["node_count"] == len(graph.nodes)
    assert round_trip["edge_count"] == len(graph.edges)
    assert round_trip["cocitation_ranking"], "empty ranking in JSON"

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
    p.add_argument("--mailto", default=os.environ.get("OPENALEX_MAILTO"),
                   help="contact email for the OpenAlex polite pool "
                        "(or set OPENALEX_MAILTO). No API key exists.")
    p.add_argument("--depth", type=int, default=1,
                   help="how many citation hops to expand (default 1).")
    p.add_argument("--per-seed", type=int, default=25,
                   help="max citing works fetched per work (default 25, OpenAlex max 200).")
    p.add_argument("--top", type=int, default=25,
                   help="size of the co-citation ranking table (default 25).")
    p.add_argument("--out", default="citation_graph",
                   help="output basename; writes <out>.graphml and <out>.json.")
    p.add_argument("--sleep", type=float, default=0.0,
                   help="seconds to sleep between API calls (politeness throttle).")
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
    if not args.mailto:
        print("warning: no --mailto / OPENALEX_MAILTO set; using OpenAlex common pool "
              "(slower, less reliable). Pass --mailto you@example.com to be polite.",
              file=sys.stderr)

    client = OpenAlexClient(mailto=args.mailto, sleep=args.sleep)
    try:
        graph = build_graph(args.seed, client, depth=args.depth, per_seed=args.per_seed)
    except urllib.error.HTTPError as exc:
        print(f"error: OpenAlex HTTP {exc.code} — {exc.reason}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"error: network failure contacting OpenAlex — {exc.reason}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    seed_ids = [n.id for n in graph.nodes.values() if n.role == "seed"]
    ranking = cocitation_ranking(graph, seed_ids, top=args.top)
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
