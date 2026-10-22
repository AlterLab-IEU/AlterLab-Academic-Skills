---
name: alterlab-citation-graph
description: "Free ResearchRabbit / Connected Papers analog — builds a citation and co-citation graph around one or more seed papers from open citation data (OpenAlex plus the OpenCitations index), with no API key, account or subscription. Walks both directions of the citation network (works the seed cites and works that cite the seed), ranks the discovered neighbourhood by co-citation strength and bibliographic coupling to surface the papers most central to a topic's literature, and exports the network as GraphML (Gephi / Cytoscape / yEd) and JSON. Use when mapping a literature landscape, finding seminal or highly co-cited papers from a seed DOI, snowballing a reference network, building a citation map / co-citation analysis, or visualizing how a research area's papers connect. A free OpenAlex key is optional and only speeds up large walks. Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read Write Edit Bash(python:*) Bash(python3:*) Bash(uv run:*)
compatibility: "No API key required: seeds, references and titles come from free OpenAlex single-work lookups, and citing works from OpenAlex list calls or, once the shared per-IP list budget is spent (HTTP 429), from the keyless OpenCitations index. Optional free OPENALEX_API_KEY gives a private daily budget. Network access to api.openalex.org and api.opencitations.net; stdlib-only, runs under bare `uv run python`."
metadata:
  skill-author: AlterLab
  version: "1.2.0"
  last_updated: "2026-10-22"
  credentials: "optional: OPENALEX_API_KEY (free; a private $1/day OpenAlex budget so list calls never hit the shared per-IP limit — faster large walks; never needed for a graph)"
---

# Citation Graph — Free ResearchRabbit Analog

## Overview

A free alternative to ResearchRabbit and Connected Papers that needs no API key, account or
subscription. Given a **seed DOI** (or several seeds), this skill walks the open citation
network ([OpenAlex](https://openalex.org) records, with [OpenCitations](https://opencitations.net)
for citing works when OpenAlex's shared budget is spent) outward in both directions and
assembles a citation / **co-citation** graph of the local literature:

- **Backward edges** — the works each seed *cites* (its `referenced_works`).
- **Forward edges** — the works that *cite* each seed (its `cited_by` set).

It then **ranks the discovered neighbourhood by co-citation strength** — how many of the seed
papers a candidate work connects to, via shared references, shared citers, and direct seed
links — surfacing the papers most central to the topic, just like ResearchRabbit's "Similar
Work" panels. The whole graph is exported as **GraphML** (open in Gephi, Cytoscape, yEd, or
networkx) and **JSON** (for downstream code).

**No key needed — how the keyless walk stays reliable.** OpenAlex data is open (CC0). Since
February 2026 OpenAlex meters *list/filter* calls ($0.0001 each) against a daily budget, and
keyless callers share $0.10/day **per IP address** (`mailto=` no longer changes that); on a
campus or cloud network that budget is often spent by mid-morning (HTTP 429 "Insufficient
budget"). *Single-work* lookups stay free and unmetered. So the script, by default
(`--citers-source auto`):

1. resolves seeds and reads their reference lists with free single-work lookups;
2. asks OpenAlex for citing works with a `cites:` list call while the budget lasts;
3. on a 429, switches (and says so on stderr) to the keyless **OpenCitations Index v2**, which
   lists the works citing a DOI with their OpenAlex ids, then reads each citer's references and
   the ranked works' titles with free single-work lookups.

`--citers-source opencitations` skips step 2 entirely. Checked live on 2026-10-22 with the
shared budget at $0: the Deep learning, LSTM + BERT + Transformer, and Ryan & Deci seeds all
built full graphs keyless in 7–25 s. A free key (`OPENALEX_API_KEY`, from
openalex.org/settings/api) is optional: it adds a private $1/day, so it is recommended for large
`--depth 2` walks or many graphs a day (faster list calls), and it is never needed to build a
graph. Don't suggest `mailto=`; it no longer changes any limit.

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

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-research-lookup`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

## Quick Start

```bash
# No key, no setup. One seed DOI, default 1-hop walk, both formats next to a basename:
uv run python scripts/build_graph.py \
    --seed 10.1038/nphys1170 \
    --out graph/seed1
# -> graph/seed1.graphml  +  graph/seed1.json
# (optional: export OPENALEX_API_KEY=... for a private budget on big walks)
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
   `citer -> seed` edges (capped at `--per-seed`; OpenAlex returns at most 100 per page). On a
   429 the citers come from OpenCitations (`/index/v2/citations/doi:<doi>`, read as a stream
   and cut at `--per-seed`) and each one's references from a free single-work lookup.
4. **Walk deeper.** With `--depth N`, repeat the expansion on first-hop neighbours (`N >= 2`).
5. **Rank by co-citation.** Each non-seed node is scored by `shared_refs + shared_citers +
   direct_seed_links` — bibliographic coupling and co-citation against the seed set — with
   global `cited_by_count` as the tie-breaker so canonical works float to the top.
6. **Hydrate.** References arrive as bare W-ids, so the ranked works' titles, years, and DOIs
   are fetched in batched `filter=openalex:W…|W…` calls (100 ids per call), or one free
   single-work lookup per id once the list budget is spent, and the table is re-ranked.
7. **Export.** Write `<out>.graphml` and `<out>.json`.

## Options

| Flag | Default | Meaning |
|------|---------|---------|
| `--seed` (repeatable) | — | Seed DOI, OpenAlex W-id, or arXiv id. At least one required. |
| `--citers-source` | `auto` | `auto`: OpenAlex list calls, switching to OpenCitations on 429. `opencitations`: never spend the OpenAlex list budget. `openalex`: list calls only (errors on 429). |
| `--api-key` | `$OPENALEX_API_KEY` | Optional free OpenAlex key, sent as a Bearer header to OpenAlex only. Prefer the env var (keeps the key out of shell history). |
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

- **Just run it.** Don't stop to ask for a key: the default run is keyless and prints a note
  saying which route it took. If the user wants a key for big walks, ask them to set
  `OPENALEX_API_KEY` (openalex.org/settings/api) themselves rather than paste it into chat or a
  committed file.
- **HTTP 429** from OpenAlex list calls means the daily budget is spent (it resets at midnight
  UTC); `auto` then continues on OpenCitations. A seed whose citers no source can supply (no
  DOI or PMID, or both services down) stops the run with an explicit error instead of writing
  a silently truncated graph; for deeper hops the script warns and skips that one node.
- **Bound the walk.** `--depth 2` with a large `--per-seed` fans out fast (one citer query plus
  up to `--per-seed` single-work lookups per frontier work on the keyless route); keep
  `--per-seed` reasonable and raise `--sleep` if you hit rate limits.
- **Coverage caveat.** OpenAlex and OpenCitations coverage is broad but imperfect; very new
  preprints may have sparse `cited_by` sets, and the keyless route returns the first
  `--per-seed` citers OpenCitations lists (not a ranked sample), so the neighbourhood can differ
  from a list-call run. Say which route was used when you report the ranking.
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
