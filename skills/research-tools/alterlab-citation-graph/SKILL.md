---
name: alterlab-citation-graph
description: "Free, key-less ResearchRabbit analog — builds a citation and co-citation graph around one or more seed papers using the OpenAlex API. Walks both directions of the citation network (works the seed cites and works that cite the seed), ranks the discovered neighbourhood by co-citation strength and bibliographic coupling to surface the papers most central to a topic's literature, and exports the network as GraphML (Gephi / Cytoscape / yEd) and JSON. Use when mapping a literature landscape, finding seminal or highly co-cited papers from a seed DOI, snowballing a reference network, building a citation map / co-citation analysis, or visualizing how a research area's papers connect — no API key required (polite mailto only). Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read Write Edit Bash(python:*)
compatibility: "No API key required. Optional OPENALEX_MAILTO (or --mailto) for the OpenAlex polite pool. Needs network access to api.openalex.org. Stdlib-only — runs under bare `uv run python`."
metadata:
  skill-author: AlterLab
  version: "1.0.0"
  last_updated: "2026-06-06"
---

# Citation Graph — Free ResearchRabbit Analog

## Overview

A free, account-free, key-less alternative to ResearchRabbit and Connected Papers. Given a
**seed DOI** (or several seeds), this skill walks the [OpenAlex](https://openalex.org)
citation network outward in both directions and assembles a citation / **co-citation** graph
of the local literature:

- **Backward edges** — the works each seed *cites* (its `referenced_works`).
- **Forward edges** — the works that *cite* each seed (its `cited_by` set).

It then **ranks the discovered neighbourhood by co-citation strength** — how many of the seed
papers a candidate work connects to, via shared references, shared citers, and direct seed
links — surfacing the papers most central to the topic, just like ResearchRabbit's "Similar
Work" panels. The whole graph is exported as **GraphML** (open in Gephi, Cytoscape, yEd, or
networkx) and **JSON** (for downstream code).

OpenAlex is fully open and requires **no API key**. The only etiquette is the *polite pool*:
pass a contact email (`--mailto` or `OPENALEX_MAILTO`) and OpenAlex serves you faster.

## When to Use This Skill

- **Map a literature landscape** from a starting paper — "I have one key paper, show me the
  field around it."
- **Find seminal / highly co-cited papers** in an area without manually chasing references.
- **Snowball a reference network** (forward and backward citation chasing) for a review.
- **Build a citation map or run a co-citation analysis** for a methods/visualization figure.
- **Visualize how a research area connects** — export to Gephi/Cytoscape for a network figure.

This is the *graph-building / discovery* tool. It is **not** a backend router for free-text
research queries (that is `alterlab-research-lookup`) and **not** a citation/metadata
fact-checker (that is `alterlab-citation-verifier`).

## Quick Start

```bash
# One seed DOI, default 1-hop walk, write both formats next to a basename:
uv run python scripts/build_graph.py \
    --seed 10.1038/nphys1170 \
    --mailto alterlab.ieu@gmail.com \
    --out graph/seed1
# -> graph/seed1.graphml  +  graph/seed1.json
```

```bash
# Several seeds (DOI / OpenAlex W-id / arXiv id), deeper walk, larger ranking:
uv run python scripts/build_graph.py \
    --seed 10.1038/nphys1170 \
    --seed W2741809807 \
    --seed arXiv:2310.06825 \
    --depth 2 --per-seed 50 --top 40 \
    --mailto alterlab.ieu@gmail.com \
    --out graph/transformer
```

```bash
# Offline smoke test (no network) — verifies the pipeline end-to-end:
uv run python scripts/build_graph.py --self-test
```

## How It Works

1. **Resolve seeds.** Each `--seed` is normalized to an OpenAlex selector. Accepted forms:
   a bare DOI (`10.1038/nphys1170`), a DOI URL, an OpenAlex work id (`W2741809807`), an
   OpenAlex URL, or an arXiv id (`arXiv:1706.03762` / `1706.03762`).
2. **Expand backward.** From each seed's `referenced_works`, add `seed -> reference` edges.
3. **Expand forward.** Query `filter=cites:<id>` to find works that cite the seed, adding
   `citer -> seed` edges (capped at `--per-seed`, OpenAlex max 200).
4. **Walk deeper.** With `--depth N`, repeat the expansion on first-hop neighbours (`N >= 2`).
5. **Rank by co-citation.** Each non-seed node is scored by `shared_refs + shared_citers +
   direct_seed_links` — bibliographic coupling and co-citation against the seed set — with
   global `cited_by_count` as the tie-breaker so canonical works float to the top.
6. **Export.** Write `<out>.graphml` and `<out>.json`.

## Options

| Flag | Default | Meaning |
|------|---------|---------|
| `--seed` (repeatable) | — | Seed DOI, OpenAlex W-id, or arXiv id. At least one required. |
| `--mailto` | `$OPENALEX_MAILTO` | Contact email for the OpenAlex polite pool. No API key exists. |
| `--depth` | `1` | Citation hops to expand. |
| `--per-seed` | `25` | Max citing works fetched per work (OpenAlex max 200). |
| `--top` | `25` | Size of the co-citation ranking table. |
| `--out` | `citation_graph` | Output basename; writes `<out>.graphml` and `<out>.json`. |
| `--sleep` | `0.0` | Seconds between API calls (politeness throttle). |
| `--self-test` | — | Run the offline self-test and exit (no network). |

## Output

**GraphML** (`<out>.graphml`) — a directed graph with node attributes `title`, `year`,
`doi`, `role` (`seed` / `reference` / `citation` / `neighbor`), and `cited_by_count`. Open it
directly in Gephi, Cytoscape, yEd, or `networkx.read_graphml`.

**JSON** (`<out>.json`) — schema `alterlab-citation-graph/1.0`:

```json
{
  "schema": "alterlab-citation-graph/1.0",
  "seeds": ["10.1038/nphys1170"],
  "node_count": 142,
  "edge_count": 318,
  "nodes": [ { "id": "W…", "title": "…", "year": 2017, "doi": "…", "role": "citation", "cited_by_count": 8123 } ],
  "edges": [ { "source": "W…", "target": "W…" } ],
  "cocitation_ranking": [
    { "id": "W…", "title": "…", "cocitation": 4, "shared_refs": 2,
      "shared_citers": 1, "direct_seed_links": 1, "cited_by_count": 8123 }
  ]
}
```

## Etiquette & Limits

- **No API key.** OpenAlex is open; do not invent or request one.
- **Be polite.** Always pass `--mailto` / set `OPENALEX_MAILTO` to use the faster polite pool.
- **Bound the walk.** `--depth 2` with a large `--per-seed` can fan out fast; raise `--sleep`
  to throttle and keep `--per-seed` reasonable on shared networks.
- **Coverage caveat.** OpenAlex citation coverage is broad but imperfect; very new
  preprints may have sparse `cited_by` sets.
- **arXiv seeds.** An `arXiv:<id>` seed is resolved via its DataCite DOI
  (`10.48550/arXiv.<id>`). If a preprint was later merged into its published-version
  record, OpenAlex may carry only the publisher DOI — pass that DOI as the seed instead.

## Complementary Tools

| Task | Tool |
|------|------|
| Route a free-text research query to the best search backend | `alterlab-research-lookup` |
| Verify a citation's metadata / DOI / detect hallucinated refs | `alterlab-citation-verifier` |
| Manage references in Zotero (DOI → BibTeX, collections) | `alterlab-pyzotero` |
| Systematic literature review with PRISMA screening | `alterlab-literature-review` |
| Check link/DOI health in a manuscript | `alterlab-link-health` |
