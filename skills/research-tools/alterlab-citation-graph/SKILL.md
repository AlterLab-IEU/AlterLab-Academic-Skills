---
name: alterlab-citation-graph
description: "Free ResearchRabbit / Connected Papers analog — builds a citation and co-citation graph around one or more seed papers using the OpenAlex API. Walks both directions of the citation network (works the seed cites and works that cite the seed), ranks the discovered neighbourhood by co-citation strength and bibliographic coupling to surface the papers most central to a topic's literature, and exports the network as GraphML (Gephi / Cytoscape / yEd) and JSON. Use when mapping a literature landscape, finding seminal or highly co-cited papers from a seed DOI, snowballing a reference network, building a citation map / co-citation analysis, or visualizing how a research area's papers connect — no subscription needed (a free OpenAlex API key is recommended). Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read Write Edit Bash(python:*)
compatibility: "Free OpenAlex API key recommended (OPENALEX_API_KEY or --api-key; openalex.org/settings/api) — keyless requests share a small per-IP daily budget and can hit HTTP 429. Needs network access to api.openalex.org. Stdlib-only — runs under bare `uv run python`."
metadata:
  skill-author: AlterLab
  version: "1.1.0"
  last_updated: "2026-09-23"
---

# Citation Graph — Free ResearchRabbit Analog

## Overview

A free, subscription-free alternative to ResearchRabbit and Connected Papers. Given a
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

OpenAlex data is open (CC0) and the API is free for this scale of use, but since February 2026
requests are metered against a daily budget and the old mailto "polite pool" is gone. Keyless
calls share $0.10/day **per IP address** — on a campus or cloud network that budget is often
already spent, which surfaces as HTTP 429. A free API key (`OPENALEX_API_KEY`, from
openalex.org/settings/api) gives $1/day of your own. A typical walk costs a fraction of a cent:
seed lookups are free and each list/filter call costs $0.0001.

## When to Use This Skill

- **Map a literature landscape** from a starting paper — "I have one key paper, show me the
  field around it."
- **Find seminal / highly co-cited papers** in an area without manually chasing references.
- **Snowball a reference network** (forward and backward citation chasing) for a review.
- **Build a citation map or run a co-citation analysis** for a methods/visualization figure.
- **Visualize how a research area connects** — export to Gephi/Cytoscape for a network figure.

This is the *graph-building / discovery* tool; it needs a seed work to walk from.

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Free-text research question with no seed paper | `alterlab-research-lookup` |
| Checking that each bibliography entry exists / spotting hallucinated or retracted refs | `alterlab-citation-verifier` |
| Querying OpenAlex for works, authors, institutions, or bibliometric trends (no graph) | `alterlab-openalex` |
| Systematic review with PRISMA screening and risk-of-bias | `alterlab-literature-review` |
| Centrality or community analysis of your own (non-citation) relational data | `alterlab-sna` |

## Quick Start

```bash
export OPENALEX_API_KEY=...   # free at openalex.org/settings/api; recommended

# One seed DOI, default 1-hop walk, write both formats next to a basename:
uv run python scripts/build_graph.py \
    --seed 10.1038/nphys1170 \
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
   `citer -> seed` edges (capped at `--per-seed`; OpenAlex returns at most 100 per page).
4. **Walk deeper.** With `--depth N`, repeat the expansion on first-hop neighbours (`N >= 2`).
5. **Rank by co-citation.** Each non-seed node is scored by `shared_refs + shared_citers +
   direct_seed_links` — bibliographic coupling and co-citation against the seed set — with
   global `cited_by_count` as the tie-breaker so canonical works float to the top.
6. **Hydrate.** References arrive as bare W-ids, so the ranked works' titles, years, and DOIs
   are fetched in batched `filter=openalex:W…|W…` calls (100 ids per call) and the table is
   re-ranked.
7. **Export.** Write `<out>.graphml` and `<out>.json`.

## Options

| Flag | Default | Meaning |
|------|---------|---------|
| `--seed` (repeatable) | — | Seed DOI, OpenAlex W-id, or arXiv id. At least one required. |
| `--api-key` | `$OPENALEX_API_KEY` | Free OpenAlex key, sent as a Bearer header. Prefer the env var (keeps the key out of shell history). |
| `--mailto` | — | Deprecated no-op; OpenAlex ignores mailto since Feb 2026. |
| `--depth` | `1` | Citation hops to expand. |
| `--per-seed` | `25` | Max citing works fetched per work (OpenAlex max 100). |
| `--top` | `25` | Size of the co-citation ranking table. |
| `--out` | `citation_graph` | Output basename; writes `<out>.graphml` and `<out>.json`. |
| `--sleep` | `0.0` | Seconds between API calls (OpenAlex allows up to 100 requests/s). |
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

## Access & Limits

- **Use a free key.** Ask the user to set `OPENALEX_API_KEY` (openalex.org/settings/api) rather
  than pasting the key into chat or a committed file. Without one the run still works when the
  shared per-IP budget has room, and the script prints a note.
- **HTTP 429** means the daily budget is spent (it resets at midnight UTC) or the run exceeded
  100 requests/s. The script stops with an explicit error instead of writing a silently
  truncated graph; add a key or retry later.
- **Bound the walk.** `--depth 2` with a large `--per-seed` fans out fast (one list call per
  frontier work); keep `--per-seed` reasonable and raise `--sleep` if you hit rate limits.
- **Coverage caveat.** OpenAlex citation coverage is broad but imperfect; very new
  preprints may have sparse `cited_by` sets.
- **arXiv seeds.** An `arXiv:<id>` seed is resolved via its DataCite DOI
  (`10.48550/arXiv.<id>`). If a preprint was later merged into its published-version
  record, OpenAlex may carry only the publisher DOI — pass that DOI as the seed instead.

## Complementary Tools

| Task | Tool |
|------|------|
| Add the papers you pick from the ranking to Zotero (DOI → item, collections) | `alterlab-pyzotero` |
| Check link/DOI health in a manuscript | `alterlab-link-health` |
| Draw or restyle the network figure beyond Gephi defaults | `alterlab-networkx` |

Part of the AlterLab Academic Skills suite.
