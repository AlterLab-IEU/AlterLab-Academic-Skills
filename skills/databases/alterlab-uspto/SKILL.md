---
name: alterlab-uspto
description: Access USPTO APIs for patent and trademark searches, examination history (PEDS), assignments, citations, office actions, and trademark status (TSDR). Use when searching patents or trademarks, conducting prior art searches, retrieving patent examination or assignment records, or doing intellectual property (IP) analysis. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read WebFetch Bash(curl:*) Bash(python:*)
compatibility: Requires a USPTO API key (free registration)
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# USPTO Database

## Overview

USPTO provides specialized APIs for patent and trademark data. Search patents by keywords/inventors/assignees, retrieve examination history via PEDS, track assignments, analyze citations and office actions, access TSDR for trademarks, for IP analysis and prior art searches.

## When to Use This Skill

This skill should be used when:

- **Patent Search**: Finding patents by keywords, inventors, assignees, classifications, or dates
- **Patent Details**: Retrieving full patent data including claims, abstracts, citations
- **Trademark Search**: Looking up trademarks by serial or registration number
- **Trademark Status**: Checking trademark status, ownership, and prosecution history
- **Examination History**: Accessing patent prosecution data from PEDS (Patent Examination Data System)
- **Office Actions**: Retrieving office action text, citations, and rejections
- **Assignments**: Tracking patent/trademark ownership transfers
- **Citations**: Analyzing patent citations (forward and backward)
- **Litigation**: Accessing patent litigation records
- **Portfolio Analysis**: Analyzing patent/trademark portfolios for companies or inventors

## USPTO API Ecosystem

The USPTO provides multiple specialized APIs for different data needs:

### Core APIs

1. **PatentSearch API** - Modern ElasticSearch-based patent search (replaced legacy PatentsView in May 2025)
   - Search patents by keywords, inventors, assignees, classifications, dates
   - Access to patent data through June 30, 2025
   - 45 requests/minute rate limit
   - **Base URL**: `https://search.patentsview.org/api/v1/`

2. **PEDS (Patent Examination Data System)** - Patent examination history
   - Application status and transaction history from 1981-present
   - Office action dates and examination events
   - Use `uspto-opendata-python` Python library
   - **Replaced**: PAIR Bulk Data (PBD) - decommissioned

3. **TSDR (Trademark Status & Document Retrieval)** - Trademark data
   - Trademark status, ownership, prosecution history
   - Search by serial or registration number
   - **Base URL**: `https://tsdrapi.uspto.gov/ts/cd/`

### Additional APIs

4. **Patent Assignment Search** - Ownership records and transfers
5. **Trademark Assignment Search** - Trademark ownership changes
6. **Enriched Citation API** - Patent citation analysis
7. **Office Action Text Retrieval** - Full text of office actions
8. **Office Action Citations** - Citations from office actions
9. **Office Action Rejection** - Rejection reasons and types
10. **PTAB API** - Patent Trial and Appeal Board proceedings
11. **Patent Litigation Cases** - Federal district court litigation data
12. **Cancer Moonshot Data Set** - Cancer-related patents

## Quick Start

### API Key Registration

USPTO APIs require an API key. Register at:
**https://account.uspto.gov/api-manager/**

API key for **PatentSearch API** is provided by PatentsView. Register at:
**https://patentsview.org/api-v01-information-page**

Set the API key as an environment variable:
```bash
export USPTO_API_KEY="your_api_key_here"
export PATENTSVIEW_API_KEY="your_api_key_here"
```

### Helper Scripts

This skill includes Python scripts for common operations:

- **`scripts/patent_search.py`** - PatentSearch API client for searching patents
- **`scripts/peds_client.py`** - PEDS client for examination history
- **`scripts/trademark_client.py`** - TSDR client for trademark data

## Task 1: Searching Patents

### Using the PatentSearch API

The PatentSearch API uses a JSON query language with various operators
(`_text_all`/`_text_any`/`_text_phrase`, comparison `_gte`/`_lte`, logical
`_and`/`_or`/`_not`). **Best practice**: use `_text_*` operators for text fields
(more performant than `_contains`/`_begins`).

The `scripts/patent_search.py` `PatentSearchClient` wraps the common cases:
search by keywords, inventor, assignee, date range, or CPC classification, plus
`advanced_search(...)` to combine criteria. For full control, POST a JSON query
to `https://search.patentsview.org/api/v1/patent` with an `X-Api-Key` header.

**Available patent endpoints**: `/patent` (granted), `/publication` (pregrant),
`/inventor`, `/assignee`, `/cpc_subclass`, `/cpc_at_issue`, `/uspc`, `/ipc`, and
text endpoints `/claims`, `/brief_summary_text`, `/detail_description_text`
(beta).

See `references/usage_examples.md` (Task 1) for worked client and direct-API
code, and `references/patentsearch_api.md` for the complete endpoint/field
reference, query syntax, response formats, rate limits, and best practices.

## Task 2: Retrieving Patent Examination Data

### Using PEDS (Patent Examination Data System)

PEDS provides comprehensive prosecution history: transaction events, status
changes, and examination timeline. Install the library with
`uv pip install uspto-opendata-python`.

The `scripts/peds_client.py` `PEDSHelper` covers application/patent lookup,
transaction history, office actions, status summary, and `analyze_prosecution`.

**Common transaction codes**: `CTNF` (non-final rejection), `CTFR` (final
rejection), `NOA` (notice of allowance), `WRIT` (response filed), `ISS.FEE`
(issue fee), `ABND` (abandoned), `AOPF` (office action mailed).

See `references/usage_examples.md` (Task 2) for worked code and
`references/peds_api.md` for the full data-field and transaction-code reference,
library usage, and portfolio-analysis examples.

## Task 3: Searching and Monitoring Trademarks

### Using TSDR (Trademark Status & Document Retrieval)

Access trademark status, ownership, and prosecution history. The
`scripts/trademark_client.py` `TrademarkClient` looks up marks by serial or
registration number, fetches status, runs `check_trademark_health`, and supports
portfolio monitoring.

**Common statuses**: `REGISTERED`, `PENDING`, `PUBLISHED FOR OPPOSITION`,
`ABANDONED`, `CANCELLED`, `SUSPENDED`, `REGISTERED AND RENEWED`.

See `references/usage_examples.md` (Task 3) for worked code and
`references/trademark_api.md` for the TSDR + Trademark Assignment Search
references, status codes, prosecution history, and ownership tracking.

## Task 4: Tracking Assignments and Ownership

Both patents and trademarks have Assignment Search APIs for tracking ownership
changes.

**Patent Assignment API base URL**: `https://assignment-api.uspto.gov/patent/v1.4/`
— search by patent number (returns XML) or by company name (`assigneeName`
criteria). Use an `X-Api-Key` header.

**Common assignment types**: `ASSIGNMENT OF ASSIGNORS INTEREST` (ownership
transfer), `SECURITY AGREEMENT`, `MERGER`, `CHANGE OF NAME`, `ASSIGNMENT OF
PARTIAL INTEREST`.

See `references/usage_examples.md` (Task 4) for worked request/XML-parsing code.

## Task 5: Accessing Additional USPTO Data

### Office Actions, Citations, and Litigation

Multiple specialized APIs provide additional patent data.

#### Office Action Text Retrieval

Retrieve full text of office actions using application number. Integrate with PEDS to identify which office actions exist, then retrieve full text.

#### Enriched Citation API

Analyze patent citations:
- Forward citations (patents citing this patent)
- Backward citations (prior art cited)
- Examiner vs. applicant citations
- Citation context

#### Patent Litigation Cases API

Access federal district court patent litigation records:
- 74,623+ litigation records
- Patents asserted
- Parties and venues
- Case outcomes

#### PTAB API

Patent Trial and Appeal Board proceedings:
- Inter partes review (IPR)
- Post-grant review (PGR)
- Appeal decisions

### Reference Documentation

See `references/additional_apis.md` for comprehensive documentation on:
- Enriched Citation API
- Office Action APIs (Text, Citations, Rejections)
- Patent Litigation Cases API
- PTAB API
- Cancer Moonshot Data Set
- OCE Status/Event Codes

## Complete Analysis Example

For full patent intelligence, combine APIs: use PatentSearch for the patent
record, PEDS (`analyze_prosecution` + `get_status_summary`) for examination
history, and the Patent Assignment API for ownership, then merge for citations
and pendency. A complete `comprehensive_patent_analysis(...)` implementation is
in `references/usage_examples.md` (Complete Analysis Example).

## Best Practices

1. **API Key Management**
   - Store API key in environment variables
   - Never commit keys to version control
   - Use same key across all USPTO APIs

2. **Rate Limiting**
   - PatentSearch: 45 requests/minute
   - Implement exponential backoff for rate limit errors
   - Cache responses when possible

3. **Query Optimization**
   - Use `_text_*` operators for text fields (more performant)
   - Request only needed fields to reduce response size
   - Use date ranges to narrow searches

4. **Data Handling**
   - Not all fields populated for all patents/trademarks
   - Handle missing data gracefully
   - Parse dates consistently

5. **Combining APIs**
   - Use PatentSearch for discovery
   - Use PEDS for prosecution details
   - Use Assignment APIs for ownership tracking
   - Combine data for comprehensive analysis

## Important Notes

- **Legacy API Sunset**: PatentsView legacy API discontinued May 1, 2025 - use PatentSearch API
- **PAIR Bulk Data Decommissioned**: Use PEDS instead
- **Data Coverage**: PatentSearch has data through June 30, 2025; PEDS from 1981-present
- **Text Endpoints**: Claims and description endpoints are in beta with ongoing backfilling
- **Rate Limits**: Respect rate limits to avoid service disruptions

## Resources

### API Documentation
- **PatentSearch API (ODP transition guidance)**: https://data.uspto.gov/support/transition-guidance/patentsview — the legacy `search.patentsview.org/docs/` host is being retired as part of the USPTO Open Data Portal (ODP) consolidation; consult this page for the migration path and current endpoint references.
- **USPTO Developer Portal**: https://developer.uspto.gov/
- **USPTO Open Data Portal**: https://data.uspto.gov/
- **API Key Registration**: https://account.uspto.gov/api-manager/

### Python Libraries
- **uspto-opendata-python**: https://pypi.org/project/uspto-opendata-python/
- **USPTO Docs**: https://docs.ip-tools.org/uspto-opendata-python/

### Reference Files
- `references/usage_examples.md` - Worked Python examples per task (search, PEDS, trademarks, assignments, full analysis)
- `references/patentsearch_api.md` - Complete PatentSearch API reference
- `references/peds_api.md` - PEDS API and library documentation
- `references/trademark_api.md` - Trademark APIs (TSDR and Assignment)
- `references/additional_apis.md` - Citations, Office Actions, Litigation, PTAB

### Scripts
- `scripts/patent_search.py` - PatentSearch API client
- `scripts/peds_client.py` - PEDS examination data client
- `scripts/trademark_client.py` - Trademark search client

