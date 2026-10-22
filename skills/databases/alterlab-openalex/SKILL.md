---
name: alterlab-openalex
description: Query and analyze scholarly literature using the OpenAlex API across 300M+ works, retrieving papers, authors, institutions, citations, and open access status. Use when searching academic papers, tracking citations, finding works by author or institution, analyzing research trends, discovering open access publications, or running bibliometric analysis. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read WebFetch Bash(curl:*) Bash(python:*)
compatibility: No API key required. OpenAlex REST API at api.openalex.org — single-entity lookups (OpenAlex ID, DOI, ORCID, ROR) and autocomplete cost nothing; list/filter/search calls share a $0.10/day keyless budget per IP (HTTP 429 until midnight UTC once spent; the skill then falls back to free lookups and keyless Crossref). An optional free OPENALEX_API_KEY gives your own $1/day. Max 100 requests/s, per_page ≤ 100 (as of 2026-10).
metadata:
    skill-author: AlterLab
    version: "1.2.1"
    last_updated: "2026-10-22"
    credentials: "optional: OPENALEX_API_KEY (free; your own $1/day budget instead of the $0.10/day keyless budget shared per IP)"
---

# OpenAlex Database

## Overview

OpenAlex is a comprehensive open catalog of 300M+ scholarly works (the default "core" corpus; `corpus=all` adds roughly 60% more, mostly datasets and repository records), authors, institutions, topics, sources, publishers, and funders. This skill provides tools and workflows for querying the OpenAlex API to search literature, analyze research output, track citations, and conduct bibliometric studies.

## When to Use This Skill

- Searching the scholarly literature across all disciplines (keyword, semantic, or filtered by year, OA status, type)
- Finding works by an author, institution, funder, or source via their OpenAlex/ORCID/ROR/ISSN IDs
- Citation counts, citing works, and bibliometric or trend analysis (group_by aggregations)
- Checking open-access status and locations of papers, or batch-resolving DOIs to metadata

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Biomedical literature search with MeSH terms, PMIDs, or PubMed Central full text | `alterlab-pubmed` |
| Building a citation / co-citation map around seed papers | `alterlab-citation-graph` |
| Checking that every reference in a bibliography exists or was retracted | `alterlab-citation-verifier` |
| Managing a Zotero library (items, collections, attachments) | `alterlab-pyzotero` |
| Writing a structured literature review from the papers found | `alterlab-literature-review` |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-pubmed`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

## Quick Start

### Basic Setup

OpenAlex needs no credentials. Its cost model (see "Rate Limits & Cost") decides what a keyless call can do:

- **Always free, keyless**: single-entity lookups — `/works/W…`, `/works/doi:10.…`, `/works/pmid:…`, `/authors/orcid:…`, `/institutions/ror:…`, `/sources/issn:…` — and `/autocomplete/{entity}?q=`. Verified 2026-10-22: these return 200 with `x-ratelimit-cost-usd: 0` even while the shared budget is spent.
- **Shared keyless budget**: list/filter (`$0.0001`/call), `search=` and `group_by` calls draw on $0.10/day shared by everyone on your IP. On university, VPN, or cloud networks it is often spent; such calls then return HTTP 429 with a `Retry-After` counting down to midnight UTC.

When that 429 arrives (the client prints a note on stderr and raises `BudgetExhausted`), say so, then keep working keylessly with `scripts/keyless_fallback.py` — and name the service that answered:
- known IDs/DOIs: free OpenAlex lookups (`batch_lookup` falls back automatically; `keyless_fallback.py enrich DOI ...`)
- discovery: `keyless_fallback.py crossref "quantum computing" --from 2020-01-01` (Crossref; title-filtered, citation-sorted locally — an approximation of the OpenAlex ranking) or, for life sciences, `europepmc "CRISPR base editing"` (Europe PMC, `CITED desc`)
- citation lists: `keyless_fallback.py citations 10.7717/peerj.4375` (OpenCitations Index v2; `--references` for outgoing)
- `group_by` aggregates have no keyless equivalent: rerun after midnight UTC or with the key. An optional **free API key** gives your own $1/day — get one at `openalex.org/settings/api`, export `OPENALEX_API_KEY`; the client sends it as an `Authorization: Bearer` header. `mailto=` buys nothing since the polite pool was retired (Feb 2026).

```python
from scripts.openalex_client import OpenAlexClient

client = OpenAlexClient()   # keyless; picks up the optional OPENALEX_API_KEY if set
```

### Installation Requirements

Install required package using uv:

```bash
uv pip install requests
```

## Core Capabilities

### 1. Search for Papers

**Use for**: Finding papers by title, abstract, or topic

```python
# Simple search
results = client.search_works(
    search="machine learning",
    per_page=100
)

# Semantic (embedding) search — matches meaning rather than words; accepts up to
# 2,000 characters (e.g. a grant aim), returns at most 50 results, 1 request/second
results = client._make_request('/works', {
    'search.semantic': 'predicting drug toxicity from molecular structure',
    'select': 'id,title,relevance_score',
})

# Search with filters
results = client.search_works(
    search="CRISPR gene editing",
    filter_params={
        "publication_year": ">2020",
        "is_oa": "true"
    },
    sort="cited_by_count:desc"
)
```

### 2. Find Works by Author

**Use for**: Getting all publications by a specific researcher

Use the two-step pattern (entity name → ID → works):

```python
from scripts.query_helpers import find_author_works

works = find_author_works(
    author_name="Jennifer Doudna",
    client=client,
    limit=100
)
```

**Manual two-step approach**:
```python
# Step 1: Get author ID
author_response = client._make_request(
    '/authors',
    params={'search': 'Jennifer Doudna', 'per-page': 1}
)
author_id = author_response['results'][0]['id'].split('/')[-1]

# Step 2: Get works
works = client.search_works(
    filter_params={"authorships.author.id": author_id}
)
```

### 3. Find Works from Institution

**Use for**: Analyzing research output from universities or organizations

```python
from scripts.query_helpers import find_institution_works

works = find_institution_works(
    institution_name="Stanford University",
    client=client,
    limit=200
)
```

### 4. Highly Cited Papers

**Use for**: Finding influential papers in a field

```python
from scripts.query_helpers import find_highly_cited_recent_papers

papers = find_highly_cited_recent_papers(
    topic="quantum computing",
    years=">2020",
    client=client,
    limit=100
)
```

### 5. Open Access Papers

**Use for**: Finding freely available research

```python
from scripts.query_helpers import get_open_access_papers

papers = get_open_access_papers(
    search_term="climate change",
    client=client,
    oa_status="any",  # or "gold", "green", "hybrid", "bronze"
    limit=200
)
```

### 6. Publication Trends Analysis

**Use for**: Tracking research output over time

```python
from scripts.query_helpers import get_publication_trends

trends = get_publication_trends(
    search_term="artificial intelligence",
    filter_params={"is_oa": "true"},
    client=client
)

# Sort and display
for trend in sorted(trends, key=lambda x: x['key'])[-10:]:
    print(f"{trend['key']}: {trend['count']} publications")
```

### 7. Research Output Analysis

**Use for**: Comprehensive analysis of author or institution research

```python
from scripts.query_helpers import analyze_research_output

analysis = analyze_research_output(
    entity_type='institution',  # or 'author'
    entity_name='MIT',
    client=client,
    years='>2020'
)

print(f"Total works: {analysis['total_works']}")
print(f"Open access: {analysis['open_access_percentage']}%")
print(f"Top topics: {analysis['top_topics'][:5]}")
```

### 8. Batch Lookups

**Use for**: Getting information for multiple DOIs, ORCIDs, or IDs efficiently

```python
dois = [
    "https://doi.org/10.1038/s41586-021-03819-2",
    "https://doi.org/10.1126/science.abc1234",
    # ... any number; sent in batches of 100 (the per-filter OR limit)
]

works = client.batch_lookup(
    entity_type='works',
    ids=dois,
    id_field='doi'
)
```

### 9. Random Sampling

**Use for**: Getting representative samples for analysis

```python
# Small sample
works = client.sample_works(
    sample_size=100,
    seed=42,  # For reproducibility
    filter_params={"publication_year": "2023"}
)

# Large sample (>10k) - automatically handles multiple requests
works = client.sample_works(
    sample_size=25000,
    seed=42,
    filter_params={"is_oa": "true"}
)
```

### 10. Citation Analysis

**Use for**: Finding papers that cite a specific work

```python
# Get the work
work = client.get_entity('works', 'https://doi.org/10.1038/s41586-021-03819-2')

# Get citing papers using cited_by_api_url
import requests
citing_response = requests.get(
    work['cited_by_api_url'],
    params={'per_page': 100},
    headers=client.auth_headers(),   # Bearer key, if one is configured
)
citing_works = citing_response.json()['results']
```

### 11. Topic and Subject Analysis

**Use for**: Understanding research focus areas

```python
# Get top topics for an institution
topics = client.group_by(
    entity_type='works',
    group_field='topics.id',
    filter_params={
        "authorships.institutions.id": "I136199984",  # MIT
        "publication_year": ">2020"
    }
)

for topic in topics[:10]:
    print(f"{topic['key_display_name']}: {topic['count']} works")
```

### 12. Large-Scale Data Extraction

**Use for**: Downloading large datasets for analysis

```python
# Paginate through all results (the client uses cursor paging, so it can go past
# the 10,000-result limit of page-based paging; for whole-corpus pulls use the
# free OpenAlex snapshot instead of the API)
all_papers = client.paginate_all(
    endpoint='/works',
    params={
        'search': 'synthetic biology',
        'filter': 'publication_year:2020-2024'
    },
    max_results=10000
)

# Export to CSV
import csv
with open('papers.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Title', 'Year', 'Citations', 'DOI', 'OA Status'])

    for paper in all_papers:
        writer.writerow([
            paper.get('title', 'N/A'),
            paper.get('publication_year', 'N/A'),
            paper.get('cited_by_count', 0),
            paper.get('doi', 'N/A'),
            paper.get('open_access', {}).get('oa_status', 'closed')
        ])
```

## Critical Best Practices

### Optional: a Free API Key Raises the Daily Allowance
Keyless list/search calls share $0.10/day per IP (single-entity lookups stay free); `export OPENALEX_API_KEY=...` (free at openalex.org/settings/api) gives your own $1/day.

### Use Two-Step Pattern for Entity Lookups
Filter by IDs, not names — names are ambiguous ("Smith" is thousands of authors, "MIT" several institutions), so resolve the entity to its ID first:
```python
# ✅ Correct
# 1. Search for entity → get ID
# 2. Filter by ID

# ❌ Wrong
# filter=author_name:Einstein  # This doesn't work!
```

### Use Maximum Page Size
Use `per_page=100` (the supported maximum; `per_page=200` is deprecated legacy behavior that OpenAlex says will be removed). A list call costs the same whether it returns 1 or 100 results:
```python
results = client.search_works(search="topic", per_page=100)
```

### Batch Multiple IDs
Use batch_lookup() for multiple IDs instead of individual requests:
```python
# ✅ Correct - 1 request per 100 DOIs (falls back to free per-ID lookups if the
#    keyless budget is spent)
works = client.batch_lookup('works', doi_list, 'doi')

# ❌ Wrong - one request per DOI
for doi in doi_list:
    work = client.get_entity('works', doi)
```

### Use Sample Parameter for Random Data
Use `sample_works()` with seed for reproducible random sampling:
```python
# ✅ Correct
works = client.sample_works(sample_size=100, seed=42)

# ❌ Wrong - random page numbers bias results
# Using random page numbers doesn't give true random sample
```

### Select Only Needed Fields
Reduce response size by selecting specific fields:
```python
results = client.search_works(
    search="topic",
    select=['id', 'title', 'publication_year', 'cited_by_count']
)
```

## Common Filter Patterns

`filter_params` entries are joined with commas (AND). Full syntax, operators, and field names: `references/api_guide.md` (Filter Syntax).

```python
filter_params = {
    "publication_year": "2020-2024",        # also "2023", ">2020", "<2020"
    "is_oa": "true",                        # several keys = AND
    "cited_by_count": ">100",
    "authorships.institutions.id": "I136199984|I27837315",   # | = OR (≤100 values): MIT or Harvard
    # "authorships.institutions.id": "I136199984+I27837315", # + = AND within one attribute (co-authored)
    "type": "!paratext",                    # ! = negation
}
```

## Entity Types

OpenAlex provides these entity types:
- **works** - Scholarly documents (articles, books, datasets)
- **authors** - Researchers with disambiguated identities
- **institutions** - Universities and research organizations
- **sources** - Journals, repositories, conferences
- **topics** - Subject classifications
- **publishers** - Publishing organizations
- **funders** - Funding agencies

Access any entity type using consistent patterns:
```python
client.search_works(...)
client.get_entity('authors', author_id)
client.group_by('works', 'topics.id', filter_params={...})
```

## External IDs

Use external identifiers directly:
```python
# DOI for works
work = client.get_entity('works', 'https://doi.org/10.7717/peerj.4375')

# ORCID for authors
author = client.get_entity('authors', 'https://orcid.org/0000-0003-1613-5981')

# ROR for institutions
institution = client.get_entity('institutions', 'https://ror.org/02y3ad647')

# ISSN for sources
source = client.get_entity('sources', 'issn:0028-0836')
```

## Reference Documentation

### Detailed API Reference
See `references/api_guide.md` for:
- Complete filter syntax
- All available endpoints
- Response structures
- Error handling
- Performance optimization
- Rate limiting details

### Common Query Examples
See `references/common_queries.md` for:
- Complete working examples
- Real-world use cases
- Complex query patterns
- Data export workflows
- Multi-step analysis procedures

## Scripts

### openalex_client.py
Main API client with:
- Automatic rate limiting
- Exponential backoff retry logic
- Pagination support
- Batch operations
- Error handling

Use for direct API access with full control.

### query_helpers.py
High-level helper functions for common operations:
- `find_author_works()` - Get papers by author
- `find_institution_works()` - Get papers from institution
- `find_highly_cited_recent_papers()` - Get influential papers
- `get_open_access_papers()` - Find OA publications
- `get_publication_trends()` - Analyze trends over time
- `analyze_research_output()` - Comprehensive analysis

Use for common research queries with simplified interfaces.

### keyless_fallback.py
Keyless stand-ins for list/search calls when the shared budget is spent: `crossref`,
`europepmc`, `citations` (OpenCitations), `enrich` (free OpenAlex DOI lookups).

## Troubleshooting

### Daily Limit / Throttling (429)
If encountering 429 (Too Many Requests) errors:
1. A 429 whose `Retry-After` is hours long means the keyless daily budget is spent — retrying won't help until midnight UTC; the client raises `BudgetExhausted` at once. Keep going keylessly (free single-entity lookups, Crossref for discovery — see Basic Setup) or add the optional free key for your own $1/day
2. Reduce cost: prefer single-entity and list+filter calls over `search=` (search costs more credits per call); use `select=` to keep responses cheap
3. Client automatically backs off and retries short throttles (429/403/5xx), e.g. exceeding 100 requests/second
4. Inspect the `x-ratelimit-remaining-usd` / `x-ratelimit-cost-usd` response headers to see remaining budget

### Empty Results
If searches return no results:
1. Check filter syntax (see `references/api_guide.md`)
2. Use two-step pattern for entity lookups (don't filter by names)
3. Verify entity IDs are correct format

### Timeout Errors
For large queries:
1. Use pagination with `per_page=100`
2. Use `select=` to limit returned fields
3. Break into smaller queries if needed

## Rate Limits & Cost

OpenAlex uses a daily cost budget plus a hard ceiling of 100 requests/second. Each call has a small USD cost; you get a free daily budget and pay only past it (prepaid top-ups or annual plans).

- **Keyless**: $0.10/day, shared by everyone on your IP address; single-entity lookups cost $0 and keep working after it is spent.
- **With the optional free API key** (`openalex.org/settings/api`, sent as `Authorization: Bearer <key>` or `?api_key=`): your own $1/day. `mailto=` is ignored since the polite pool was retired (Feb 2026).
- **Cost per 1,000 calls** (help.openalex.org, 2026-08): single-entity lookup by ID/DOI free; list+filter $0.10; `search=` $1; `search.semantic=` $1; content (PDF) download $10. So $1 buys ~10,000 filter calls (~1M results at `per_page=100`) or ~1,000 searches — filter when you can.
- **Query limits**: `per_page` ≤ 100; page-based paging stops at 10,000 results (use `cursor=*`); ≤ 100 OR values per filter; `sample` ≤ 10,000.
- Check your remaining budget with `GET /rate-limit?api_key=...`.
- Live budget is reported in response headers: `x-ratelimit-limit-usd`, `x-ratelimit-remaining-usd`, `x-ratelimit-cost-usd` (and the response `meta.cost_usd`).
- Exhausting the daily budget returns **429 Too Many Requests** with a `Retry-After` counting down to midnight UTC; bursts above 100 requests/second also return 429 (short wait). 403 can also signal "slow down".

## Notes

- All data is open and free; the daily budget is generous for typical research workloads.
- Keyless covers lookups and moderate list/search use; the optional free key is worth adding for bulk jobs or busy shared networks.
- Costs/limits apply per credential (per key, or per IP when keyless), not per request type alone — minimize `search=` and use `select=` to stretch the budget.
- Summarise, cluster, or screen the retrieved records in the conversation — no second LLM API is needed.
- Client handles pagination, retries, and backoff automatically.

