# bioRxiv API Reference

## Overview

The bioRxiv API provides programmatic access to preprint metadata from the bioRxiv server. The API returns JSON-formatted data with comprehensive metadata about life sciences preprints.

## Base URL

```
https://api.biorxiv.org
```

## Rate Limiting

Be respectful of the API:
- Add delays between requests (minimum 0.5 seconds recommended)
- Use appropriate User-Agent headers
- Cache results when possible

## API Endpoints

### 1. Details by Date Range

Retrieve preprints posted within a specific date range, optionally restricted to one
subject category with the `?category=` query parameter (see the note below). The same
paths work for medRxiv by replacing `biorxiv` with `medrxiv`.

**Endpoint:**
```
GET /details/biorxiv/{start_date}/{end_date}/{cursor}/{format}
```

**Parameters:**
- `start_date`: Start date in YYYY-MM-DD format
- `end_date`: End date in YYYY-MM-DD format
- `cursor`: Absolute record offset for pagination (0, then 30, 60, ...). The
  endpoint returns **30 records per call**; iterate the cursor until it reaches
  `messages[0].total`.
- `format`: `json` (default) or `xml`

**Pagination:** the `/details` endpoint is capped at 30 records per request.
`messages[0]` reports `count` (records in this page), `cursor` (current offset),
and `total` (records in the whole range). To retrieve everything, loop the cursor
by 30 until `cursor >= total`.

**Category filtering:** pass the subject as a **query-string parameter**, with
underscores (or `%20`) for spaces — `?category=cell_biology`. It is applied
server-side, so `messages[0].total` and the number of pages shrink to that subject
(one week in March 2025: 1,267 preprints overall vs. 77 in cell biology). A category
path segment (`/details/biorxiv/{start}/{end}/neuroscience`) does **not** work. In
records the category is **lowercase with spaces** (e.g. `cell biology`), whereas the
script's CLI form is **hyphenated** (e.g. `cell-biology`); normalize between the two.

Other interval forms: `/details/biorxiv/{N}` (the N most recent posts) and
`/details/biorxiv/{N}d` (posts from the last N days).

**Example:**
```
GET https://api.biorxiv.org/details/biorxiv/2024-01-01/2024-01-31/0/json
GET https://api.biorxiv.org/details/biorxiv/2024-01-01/2024-01-31/30/json
GET https://api.biorxiv.org/details/biorxiv/2025-03-21/2025-03-28/0/json?category=cell_biology
```

**Response:**
```json
{
  "messages": [
    {
      "status": "ok",
      "category": "all",
      "interval": "2024-01-01:2024-01-31",
      "funder": "all",
      "cursor": 0,
      "count": 30,
      "count_new_papers": "590",
      "total": "801"
    }
  ],
  "collection": [
    {
      "doi": "10.1101/2024.01.15.123456",
      "title": "Example Paper Title",
      "authors": "Smith, J.; Doe, J.; Johnson, A.",
      "author_corresponding": "Smith J",
      "author_corresponding_institution": "University Example",
      "date": "2024-01-15",
      "version": "1",
      "type": "new results",
      "license": "cc_by",
      "category": "neuroscience",
      "jatsxml": "https://www.biorxiv.org/content/...",
      "abstract": "This is the abstract...",
      "funder": "NA",
      "published": "NA",
      "server": "bioRxiv"
    }
  ]
}
```

Note: `authors` is **semicolon-separated** (`"Smith, J.; Doe, J."`), not
comma-separated. `total` and `count_new_papers` may be returned as strings.
`published` holds the journal DOI once the preprint has been published, else `NA`.
(Values above are illustrative; field names match the live API as of 2026-09.)

### 2. Details by DOI

Retrieve details for a specific preprint by DOI. The response `collection`
contains one entry per version (ordered ascending), so the last entry is the
latest version.

**Endpoint:**
```
GET /details/biorxiv/{doi}/na/{format}
```

**Parameters:**
- `doi`: The DOI of the preprint — `10.1101/…` (e.g. `10.1101/2024.01.15.123456`) for
  older preprints, `10.64898/…` (e.g. `10.64898/2026.08.28.747819`) for those posted
  since the move to openRxiv in December 2025. Accept both prefixes in any DOI
  validation or regex.
- `format`: `json` or `xml`

**Example:**
```
GET https://api.biorxiv.org/details/biorxiv/10.1101/2024.01.15.123456/na/json
GET https://api.biorxiv.org/details/biorxiv/10.64898/2026.08.28.747819/na/json
```

### 3. Published-Article Metadata (Pubs)

Retrieve metadata for the **published (journal) version** of bioRxiv preprints
that have subsequently been published. Useful for linking a preprint to its
peer-reviewed DOI; it is not a feed of arbitrary preprints. The per-DOI form
(`/pubs/biorxiv/{doi}/na/json`) returns nothing for `10.64898` preprint DOIs (checked
2026-09) — read the `published` field from `/details/` instead.

**Endpoint:**
```
GET /pubs/biorxiv/{interval}/{cursor}
```

**Parameters:**
- `interval`: A date range (`YYYY-MM-DD/YYYY-MM-DD`) or a numeric value for the N
  most recent published records.
- `cursor`: Pagination cursor. This endpoint returns **100 records per call**;
  increment the cursor by 100 for subsequent pages.

The response carries both preprint and publication fields (e.g. `biorxiv_doi`,
`published_doi`, `published_journal`, publication dates).

**Example:**
```
GET https://api.biorxiv.org/pubs/biorxiv/2024-01-01/2024-01-31/0
```

**Response includes pagination:**
```json
{
  "messages": [
    {
      "status": "ok",
      "count": 100,
      "total": 250,
      "cursor": 100
    }
  ],
  "collection": [...]
}
```

## Valid Categories

bioRxiv organizes preprints into the following categories:

- `animal-behavior-and-cognition`
- `biochemistry`
- `bioengineering`
- `bioinformatics`
- `biophysics`
- `cancer-biology`
- `cell-biology`
- `clinical-trials`
- `developmental-biology`
- `ecology`
- `epidemiology`
- `evolutionary-biology`
- `genetics`
- `genomics`
- `immunology`
- `microbiology`
- `molecular-biology`
- `neuroscience`
- `paleontology`
- `pathology`
- `pharmacology-and-toxicology`
- `physiology`
- `plant-biology`
- `scientific-communication-and-education`
- `synthetic-biology`
- `systems-biology`
- `zoology`

## Paper Metadata Fields

Each paper in the `collection` array contains:

| Field | Description | Type |
|-------|-------------|------|
| `doi` | Digital Object Identifier | string |
| `title` | Paper title | string |
| `authors` | Semicolon-separated author list (e.g. `"Smith, J.; Doe, J."`) | string |
| `author_corresponding` | Corresponding author name | string |
| `author_corresponding_institution` | Corresponding author's institution | string |
| `date` | Publication date (YYYY-MM-DD) | string |
| `version` | Version number | string |
| `type` | Type of submission (e.g., "new results") | string |
| `license` | License type (e.g., "cc_by") | string |
| `category` | Subject category | string |
| `jatsxml` | URL to JATS XML | string |
| `abstract` | Paper abstract | string |
| `published` | Journal publication info (if published) | string |

## Downloading Full Papers

### PDF Download

PDFs can be downloaded directly (not through the API). `www.biorxiv.org` is behind
Cloudflare and may return **HTTP 429** to scripted clients; space requests out and
treat a 429 as "retry later", not "missing". For bulk full text use the requester-pays
text-mining bucket `s3://biorxiv-src-monthly` (us-east-1; `.meca` zip packages with
PDF + JATS XML; https://www.biorxiv.org/tdm).

```
https://www.biorxiv.org/content/{doi}v{version}.full.pdf
```

Example:
```
https://www.biorxiv.org/content/10.1101/2024.01.15.123456v1.full.pdf
```

### HTML Version

```
https://www.biorxiv.org/content/{doi}v{version}
```

### JATS XML

Full structured XML is available via the `jatsxml` field in the API response.

## Common Search Patterns

### Author Search

1. Get papers from date range
2. Filter by author name (case-insensitive substring match in `authors` field)

### Keyword Search

1. Get papers from date range (optionally filtered by category)
2. Search in title, abstract, or both fields
3. Filter papers containing keywords (case-insensitive)

### Recent Papers by Category

1. Use the `/details` date-range endpoint over a recent window with `?category=<subject_with_underscores>`
2. Paginate with the cursor until `cursor >= total`

### Papers by Funder (since 2025-04-10)

`GET /funder/{server}/{start}/{end}/{ROR_ID_suffix}/{cursor}/{format}` returns preprints
whose funding declaration names that funder (ROR ID suffix, e.g. `00k4n6c32` for the
European Commission); 100 records per page, also accepts `?category=`. Funder metadata
starts on 2025-04-10, so earlier dates return nothing. Records from `/details` carry a
`funder` field as well.

## Error Handling

Common HTTP status codes:
- `200`: Success
- `404`: Resource not found
- `500`: Server error

Always check the `messages` array in the response:
```json
{
  "messages": [
    {
      "status": "ok",
      "count": 100
    }
  ]
}
```

## Best Practices

1. **Cache results**: Store retrieved papers to avoid repeated API calls
2. **Use appropriate date ranges**: Smaller date ranges return faster
3. **Filter by category**: Pass `?category=` so the server does the filtering (fewer pages)
4. **Batch processing**: When downloading multiple PDFs, add delays between requests
5. **Error handling**: Always check response status and handle errors gracefully
6. **Version tracking**: Note that papers can have multiple versions

## Python Usage Example

```python
from biorxiv_search import BioRxivSearcher

searcher = BioRxivSearcher(verbose=True)

# Search by keywords
papers = searcher.search_by_keywords(
    keywords=["CRISPR", "gene editing"],
    start_date="2024-01-01",
    end_date="2024-12-31",
    category="genomics"
)

# Search by author
papers = searcher.search_by_author(
    author_name="Smith",
    start_date="2023-01-01",
    end_date="2024-12-31"
)

# Get specific paper
paper = searcher.get_paper_details("10.1101/2024.01.15.123456")

# Download PDF
searcher.download_pdf("10.1101/2024.01.15.123456", "paper.pdf")
```

## External Resources

- bioRxiv homepage: https://www.biorxiv.org/
- API documentation: https://api.biorxiv.org/ (also covers `/pubs`, `/publisher`, `/funder`, `/sum`, `/usage`)
- Text and data mining (bulk full text): https://www.biorxiv.org/tdm
- JATS XML specification: https://jats.nlm.nih.gov/
