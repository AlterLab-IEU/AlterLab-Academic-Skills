---
name: alterlab-citation-graph
description: "Free ResearchRabbit / Connected Papers analog — builds a citation and co-citation graph around one or more seed papers from open citation data (the OpenCitations index and Semantic Scholar, with titles from Crossref), with no API key, account or subscription. Walks both directions of the citation network (works the seed cites and works that cite the seed), ranks the discovered neighbourhood by co-citation strength and bibliographic coupling to surface the papers most central to a topic's literature, and exports the network as GraphML (Gephi / Cytoscape / yEd) and JSON. Use when mapping a literature landscape, finding seminal or highly co-cited papers from a seed DOI, snowballing a reference network, building a citation map / co-citation analysis, or visualizing how a research area's papers connect. Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read Write Edit Bash(python:*) Bash(python3:*) Bash(uv run:*)
compatibility: "No API key required: references and citing works come from the keyless OpenCitations Index v2, with the keyless Semantic Scholar Graph API for works OpenCitations has no data for (backs off on HTTP 429), and titles from Crossref and doi.org. Optional S2_API_KEY only raises Semantic Scholar's rate limit. Network access to api.opencitations.net, api.semanticscholar.org, api.crossref.org and doi.org; stdlib-only, runs under bare `uv run python`."
metadata:
  skill-author: AlterLab
  version: "1.3.0"
  last_updated: "2026-11-02"
  credentials: "optional: S2_API_KEY or SEMANTIC_SCHOLAR_API_KEY (a dedicated Semantic Scholar rate limit instead of the shared keyless pool; never needed for a graph)"
---

# Citation Graph — Free ResearchRabbit Analog

## Overview

A free alternative to ResearchRabbit and Connected Papers that needs no API key, account or
subscription. Given a **seed DOI** (or several seeds), this skill walks the open citation
network ([OpenCitations](https://opencitations.net), with the
[Semantic Scholar](https://www.semanticscholar.org/product/api) Graph API where OpenCitations
has no data) outward in both directions and assembles a citation / **co-citation** graph of the
local literature:

- **Backward edges** — the works each seed *cites* (its reference list).
- **Forward edges** — the works that *cite* each seed.

It then **ranks the discovered neighbourhood by co-citation strength** — how many of the seed
papers a candidate work connects to, via shared references, shared citers, and direct seed
links — surfacing the papers most central to the topic, just like ResearchRabbit's "Similar
Work" panels. The whole graph is exported as **GraphML** (open in Gephi, Cytoscape, yEd, or
networkx) and **JSON** (for downstream code).

**No key needed — where the data comes from.** Every source is keyless (checked live
2026-11-02):

1. **OpenCitations Index v2** (`/index/v2/references/doi:<doi>` and `/citations/doi:<doi>`)
   lists the DOIs a work cites and the DOIs citing it — open Crossref, DataCite and PubMed
   citation data, arXiv preprints included under their `10.48550/arXiv.<id>` DOI. The
   citations answer is one unpaginated array, so the script reads it as a stream and stops at
   `--per-seed`.
2. **Semantic Scholar** (`/graph/v1/paper/<id>/references`, `/citations`, `/paper/batch`)
   fills the gaps: works OpenCitations has no reference list for (preprints, publishers that
   deposit none) and metadata for DOIs Crossref does not register. Its keyless pool is shared
   and often answers HTTP 429; the script backs off 2 + 4 + 8 s, then pauses Semantic Scholar
   for 30 s and lists on stderr which works it could not check (not checked, never "no
   references"). An optional `S2_API_KEY` gives a dedicated rate limit.
3. **Crossref** (`/works?filter=doi:…`, 40 DOIs per call) supplies titles, years and citation
   counts for the seeds and ranked works; **doi.org** content negotiation covers the rest.

Checked live on 2026-11-02: the Ryan & Deci seed built a 972-node graph in 17 s, and BERT +
`arXiv:1706.03762` a merged 422-node graph in 15 s, keyless. OpenAlex is no longer used: since
2026 its keyless list calls share a small per-IP daily budget, so dependable use needed an
account. Don't suggest `mailto=` or a key; neither is needed.

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
| Searching PubMed for biomedical records (MeSH terms, PMIDs, PubMed's own related-articles list) | `alterlab-pubmed` |
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
```

```bash
# Several seeds (DOI / arXiv id), deeper walk, larger ranking:
uv run python scripts/build_graph.py \
    --seed 10.1038/nphys1170 \
    --seed 10.18653/v1/N19-1423 \
    --seed arXiv:2310.06825 \
    --depth 2 --per-seed 50 --top 40 \
    --out graph/transformer
```

```bash
# Offline smoke test (no network) — verifies the pipeline end-to-end:
uv run python scripts/build_graph.py --self-test
```

## How It Works

1. **Resolve seeds.** Each `--seed` becomes a node id, its lowercase DOI. Accepted forms: a
   bare DOI (`10.1038/nphys1170`), a DOI URL, `doi:<doi>`, or an arXiv id (`arXiv:1706.03762`
   / `1706.03762`, which becomes its DataCite DOI `10.48550/arxiv.1706.03762`). OpenAlex work
   ids (`W…`) are refused with a message asking for the DOI.
2. **Expand backward.** Each seed's reference list from OpenCitations, or from Semantic
   Scholar when OpenCitations has none, adds `seed -> reference` edges.
3. **Expand forward.** The works citing the seed (OpenCitations stream cut at `--per-seed`,
   or Semantic Scholar's `/citations` when OpenCitations has none) add `citer -> seed` edges,
   and each citer's own reference list is read the same way, so co-citation and coupling
   can be counted.
4. **Walk deeper.** With `--depth N`, repeat the forward expansion on first-hop citers (`N >= 2`).
5. **Rank by co-citation.** Each non-seed node is scored by `shared_refs + shared_citers +
   direct_seed_links` — bibliographic coupling and co-citation against the seed set — with
   global `cited_by_count` as the tie-breaker so canonical works float to the top.
6. **Hydrate.** OpenCitations returns bare DOIs, so the seeds' and ranked works' titles, years
   and citation counts come from Crossref (`filter=doi:…`, 40 per call), then Semantic
   Scholar's batch endpoint and doi.org for what Crossref lacks, and the table is re-ranked.
7. **Export.** Write `<out>.graphml` and `<out>.json`.

## Options

| Flag | Default | Meaning |
|------|---------|---------|
| `--seed` (repeatable) | — | Seed DOI, DOI URL, or arXiv id. At least one required. |
| `--citers-source` | `auto` | `auto`: OpenCitations, then Semantic Scholar for works it has none for. `opencitations` or `semanticscholar`: that source only. |
| `--depth` | `1` | Citation hops to expand. |
| `--per-seed` | `25` | Max citing works fetched per work. |
| `--top` | `25` | Size of the co-citation ranking table. |
| `--out` | `citation_graph` | Output basename; writes `<out>.graphml` and `<out>.json`. |
| `--sleep` | `0.0` | Extra seconds to wait after each API call. |
| `--self-test` | — | Run the offline self-test and exit (no network). |

The retired `--api-key` and `--mailto` flags are still accepted and ignored, so older commands
run. `S2_API_KEY` (environment only, sent as a header) is the one optional credential.

## Output

**GraphML** (`<out>.graphml`) — a directed graph with node attributes `title`, `year`,
`doi`, `role` (`seed` / `reference` / `citation` / `neighbor`), and `cited_by_count`. Open it
directly in Gephi, Cytoscape, yEd, or `networkx.read_graphml`.

**JSON** (`<out>.json`) — schema `alterlab-citation-graph/1.0`. Node ids are lowercase DOIs
(an arXiv preprint is `10.48550/arxiv.<id>`); a work with no DOI is `pmid:<n>` or
`s2:<paperId>`. `cited_by_count` comes from Crossref, or Semantic Scholar for works Crossref
does not register, so counts are comparable only roughly:

```json
{
  "schema": "alterlab-citation-graph/1.0",
  "seeds": ["10.1038/nphys1170"],
  "node_count": 142,
  "edge_count": 318,
  "nodes": [ { "id": "10.…", "title": "…", "year": 2017, "doi": "10.…", "role": "citation", "cited_by_count": 8123 } ],
  "edges": [ { "source": "10.…", "target": "10.…" } ],
  "cocitation_ranking": [
    { "id": "10.…", "title": "…", "cocitation": 4, "shared_refs": 2,
      "shared_citers": 1, "direct_seed_links": 1, "cited_by_count": 8123 }
  ]
}
```

## Access & Limits

- **Just run it.** Don't stop to ask for a key or an account: the run is keyless and prints a
  note naming its sources. `S2_API_KEY` only helps when Semantic Scholar keeps answering 429;
  if the user wants one, ask them to set it themselves rather than paste it into chat.
- **HTTP 429 from Semantic Scholar** means its shared keyless pool is busy. The script backs
  off, then pauses that source and reports the works it could not check on stderr; edges
  OpenCitations supplied are unaffected. Say so when you report the graph, and re-run later if
  a preprint seed's references were among them.
- **No silent truncation.** A seed whose references or citing works no source could answer for
  (both services down, or no DOI they know) stops the run with an explicit error instead of
  writing a truncated graph; for deeper hops the script warns and skips that one node.
- **Bound the walk.** Each citer costs one reference-list call, so `--depth 2` with a large
  `--per-seed` fans out fast; keep `--per-seed` reasonable and raise `--sleep` if a service
  slows you down.
- **Coverage caveat.** OpenCitations and Semantic Scholar coverage is broad but imperfect: very
  new preprints may have few citing works, and the script takes the first `--per-seed` citers
  OpenCitations lists (not a ranked sample), so a single-seed ranking can lean on the seed's own
  references. A published paper and its arXiv preprint are separate nodes (different DOIs).
- **arXiv seeds.** An `arXiv:<id>` seed is walked under its DataCite DOI
  (`10.48550/arXiv.<id>`), with Semantic Scholar supplying its reference list. If the preprint
  has a published version, add that DOI as a second seed to merge both citation sets.

## Complementary Tools

| Task | Tool |
|------|------|
| Add the papers you pick from the ranking to Zotero (DOI → item, collections) | `alterlab-pyzotero` |
| Check link/DOI health in a manuscript | `alterlab-link-health` |
| Draw or restyle the network figure beyond Gephi defaults | `alterlab-networkx` |

Part of the AlterLab Academic Skills suite.
