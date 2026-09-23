---
name: alterlab-uspto
description: Access USPTO patent and trademark data through the Open Data Portal (ODP) APIs — Patent File Wrapper search, examination history (the PEDS successor), continuity, assignments, office actions, PTAB decisions — and trademark status via TSDR. Use when searching patents or trademarks, conducting prior art searches, retrieving patent examination or assignment records, or doing intellectual property (IP) analysis. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read WebFetch Bash(curl:*) Bash(python:*)
compatibility: Requires free keys — an ODP API key (data.uspto.gov, USPTO.gov account; X-API-KEY header) for patent data and a TSDR key (account.uspto.gov/api-manager; USPTO-API-KEY header) for trademarks. PEDS, the Assignment Search API, and the PatentsView PatentSearch API are offline as of 2026-09.
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# USPTO Database

## Overview

USPTO data for patents and trademarks: application and patent bibliographic
search, examination (prosecution) history, continuity, assignments, office
actions, PTAB proceedings, and trademark status (TSDR), for IP analysis and prior
art searches. Most patent APIs now live on the **USPTO Open Data Portal (ODP)**
at `https://api.uspto.gov`; several older services were retired in 2025–2026, so
check the status table below before reusing older code.

## When to Use This Skill

- **Patent/application search**: by title keywords, applicant, inventor, dates, status
- **Examination history**: transactions, office actions, allowance/abandonment, pendency
- **Continuity and ownership**: parent/child applications, recorded assignments
- **Office actions**: text, cited references, and rejection types (101/102/103/112)
- **PTAB**: IPR/PGR trials, appeal and interference decisions
- **Trademarks**: status, owner, goods/services, and prosecution history via TSDR
- **Portfolio analysis**: patents and marks of a company or inventor

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Scholarly literature (non-patent prior art), citation counts | `alterlab-openalex` |
| Biomedical literature search | `alterlab-pubmed` |
| FDA drug/device approvals, labels, 510(k)/PMA | `alterlab-fda` |
| Company filings and financials from SEC EDGAR | `alterlab-edgartools` |
| Market sizing / competitive-landscape reports | `alterlab-market-research` |

## USPTO API Status (verified 2026-09-23)

| Need | Current service | Auth | Status |
|------|-----------------|------|--------|
| Bibliographic search, status, transactions, continuity, assignments, documents (applications filed 2001-01-01 onward, refreshed daily) | ODP **Patent File Wrapper**: `https://api.uspto.gov/api/v1/patent/applications/search` (GET `q=` or POST JSON) and `/{applicationNumberText}` plus `/meta-data`, `/transactions`, `/continuity`, `/assignment`, `/documents`, `/adjustment`, `/attorney`, `/foreign-priority`, `/associated-documents` | `X-API-KEY` (ODP key) | Live — replaces PEDS |
| Office actions: text, citations, rejections, enriched citations | ODP `POST https://api.uspto.gov/api/v1/patent/oa/{oa_actions/v1, oa_citations/v2, oa_rejections/v2, enriched_cited_reference_metadata/v3}/records` (form fields `criteria` [Lucene], `start`, `rows`) | ODP key | Live on the ODP host since early 2026 |
| PTAB trials, trial decisions/documents, appeals, interferences | ODP `/api/v1/patent/trials/proceedings/search`, `/trials/decisions/search`, `/trials/documents/search`, `/appeals/decisions/search`, `/interferences/decisions/search` | ODP key | Live |
| Petition decisions | ODP `/api/v1/petition/decisions/search` | ODP key | Live |
| Bulk data (grant / pre-grant XML full text, PatentsView tables, OA weekly archives, etc.) | ODP `/api/v1/datasets/products/search`, `/api/v1/datasets/products/{productIdentifier}` | ODP key | Live |
| Trademark status and documents | TSDR `https://tsdrapi.uspto.gov/ts/cd/casestatus/sn{serial}/info` (XML; `info.json` also served) | `USPTO-API-KEY` header (TSDR key) | Live; 60 requests/min per key, 4/min for PDF/ZIP |
| Full-text patent search with disambiguated inventors/assignees | PatentsView PatentSearch API (`search.patentsview.org`) | — | **Offline**: paused when PatentsView moved to ODP on 2026-03-20; hostname no longer resolves; no announced return date; old PatentsView keys do not work on ODP |
| Examination history | PEDS (`ped.uspto.gov`), `uspto-opendata-python` PEDS client | — | **Retired** 2025-03-14 (host gone) — use Patent File Wrapper |
| Patent / trademark assignment search | `assignment-api.uspto.gov` | — | **Gone** (host no longer resolves) — use `/{app}/assignment` or assignment bulk data |
| Legacy DSAPI endpoints (`developer.uspto.gov/ds-api/...`) | — | — | **Retired** — the host redirects to data.uspto.gov |

Consequences: there is currently no public API for full-text claims/abstract
search with disambiguated assignees. Use ODP bibliographic search for discovery,
ODP bulk grant/pgpub XML (or the PatentsView bulk tables on ODP) for full text,
and say so when a user asks for PatentsView-style queries.

## Quick Start

### API Keys

- **ODP key** (Patent File Wrapper, office actions, PTAB, petitions, bulk data):
  sign in at https://data.uspto.gov with a USPTO.gov account (required for ODP
  since 2026-06-18) and request a key under APIs → Getting Started. Send it as
  `X-API-KEY`. ODP deletes keys that stay unused for 90 days.
- **TSDR key** (trademarks): request the TSDR product at
  https://account.uspto.gov/api-manager/ and send it as `USPTO-API-KEY` — an
  `X-Api-Key` header is ignored, so the call is treated as keyless (HTTP 401).

```bash
export USPTO_ODP_API_KEY="..."    # ODP scripts (USPTO_API_KEY is read as a fallback)
export USPTO_TSDR_API_KEY="..."   # trademark_client.py
```

### Helper Scripts

- **`scripts/patent_search.py`** — ODP Patent File Wrapper search (title,
  inventor, applicant, grant-date range, patent-number lookup)
- **`scripts/peds_client.py`** — ODP file-wrapper client, the PEDS successor
  (`FileWrapperClient`, alias `PEDSHelper`): status summary, transactions,
  office-action events, prosecution statistics, continuity, assignments
- **`scripts/trademark_client.py`** — TSDR client for trademark status, owners,
  goods/services, and prosecution history

The scripts were checked against the ODP OpenAPI spec and live endpoint routing
(401/403 without a key); run them with your own key before relying on them.

## Task 1: Searching Patents

POST a JSON body to `https://api.uspto.gov/api/v1/patent/applications/search`:

```python
import os, requests

body = {
    "q": 'applicationMetaData.inventionTitle:"lidar"',
    "filters": [{"name": "applicationMetaData.applicationTypeLabelName", "value": ["Utility"]}],
    "rangeFilters": [{"field": "applicationMetaData.grantDate",
                      "valueFrom": "2024-01-01", "valueTo": "2024-12-31"}],
    "sort": [{"field": "applicationMetaData.grantDate", "order": "desc"}],
    "pagination": {"offset": 0, "limit": 25},
}
r = requests.post("https://api.uspto.gov/api/v1/patent/applications/search",
                  headers={"X-API-KEY": os.environ["USPTO_ODP_API_KEY"]}, json=body, timeout=60)
for rec in r.json().get("patentFileWrapperDataBag", []):
    meta = rec["applicationMetaData"]
    print(rec["applicationNumberText"], meta.get("patentNumber"), meta.get("inventionTitle"))
```

The query language is Solr-like (`field:value`, `AND`/`OR`/`NOT`, wildcards,
quoted phrases). Useful `applicationMetaData` fields: `inventionTitle`,
`patentNumber`, `filingDate`, `grantDate`, `applicationStatusDescriptionText`,
`firstApplicantName`, `firstInventorName`, `cpcClassificationBag`,
`groupArtUnitNumber`, `examinerNameText`. A search with no matches returns HTTP
404 ("No matching records found"), not an empty 200. The file wrapper holds
bibliographic data only — not claims or abstracts.

`references/patentsearch_api.md` documents the offline PatentsView PatentSearch
API (query operators, fields) for reading older code and for when USPTO restores
it; `references/usage_examples.md` (Task 1) has worked code.

## Task 2: Retrieving Patent Examination Data

`GET https://api.uspto.gov/api/v1/patent/applications/{applicationNumberText}/transactions`
returns `eventDataBag[]` items of `{eventCode, eventDescriptionText, eventDate}`;
`/meta-data` returns status, dates, examiner, and art unit. `scripts/peds_client.py`
wraps these (`get_status_summary`, `get_transaction_history`,
`get_office_actions`, `analyze_prosecution`, `get_continuity`, `get_assignments`).

**Common transaction codes**: `CTNF` (non-final rejection), `CTFR` (final
rejection), `NOA` (notice of allowance), `WRIT` (response filed), `ISS.FEE`
(issue fee), `ABND` (abandoned), `AOPF` (office action mailed). Application
*status* codes (not event codes) are listed by `GET /api/v1/patent/status-codes`.

`references/peds_api.md` covers transaction codes and prosecution analysis;
its PEDS/library sections are historical.

## Task 3: Searching and Monitoring Trademarks

### Using TSDR (Trademark Status & Document Retrieval)

`GET https://tsdrapi.uspto.gov/ts/cd/casestatus/sn{serial}/info` (or
`rn{registration}`) returns the ST96 XML status record; `casedocs/{caseid}/info`
lists the case documents, and `.../content.pdf` / `download.zip` fetch them
(4 per minute). The `scripts/trademark_client.py` `TrademarkClient` looks up
marks by serial or registration number, fetches status, runs
`check_trademark_health`, and supports portfolio monitoring.

**Common statuses**: `REGISTERED`, `PENDING`, `PUBLISHED FOR OPPOSITION`,
`ABANDONED`, `CANCELLED`, `SUSPENDED`, `REGISTERED AND RENEWED`.

See `references/usage_examples.md` (Task 3) for worked code and
`references/trademark_api.md` for status codes, prosecution history, and
ownership tracking.

## Task 4: Tracking Assignments and Ownership

The Assignment Search API host (`assignment-api.uspto.gov`) is gone. For a given
application, `GET https://api.uspto.gov/api/v1/patent/applications/{app}/assignment`
returns `assignmentBag[]` with `reelAndFrameNumber`, `conveyanceText`,
`assignmentRecordedDate`, `assignorBag`, and `assigneeBag`
(`scripts/peds_client.py --assignments {app}`). For company-wide ownership
questions use the assignment datasets in the ODP bulk-data catalog.

**Common conveyance types**: `ASSIGNMENT OF ASSIGNORS INTEREST` (ownership
transfer), `SECURITY AGREEMENT`, `MERGER`, `CHANGE OF NAME`, `ASSIGNMENT OF
PARTIAL INTEREST`.

## Task 5: Office Actions, Citations, and PTAB

- **Office actions** (text retrieval, citations from PTO-892/1449, rejections by
  statute 101/102/103/112/double patenting, and AI-extracted enriched citations)
  are served from the ODP host as form-encoded POSTs with a Lucene `criteria`
  string, e.g. `criteria=patentApplicationNumber:12190351`, `start=0`,
  `rows=25`, to `https://api.uspto.gov/api/v1/patent/oa/oa_rejections/v2/records`.
- **PTAB** proceedings (IPR, PGR, CBM), decisions, documents, and ex parte appeal
  decisions have ODP search endpoints (table above).
- **Litigation and Cancer Moonshot datasets** were DSAPI services on the retired
  developer.uspto.gov; look for them in the ODP bulk-data catalog.

`references/additional_apis.md` describes what each dataset contains and how to
combine them.

## Complete Analysis Example

For full patent intelligence: find the application through Patent File Wrapper
search, pull `/meta-data` and `/transactions` for prosecution history,
`/continuity` for the family, `/assignment` for ownership, then the office-action
rejections API for the grounds of rejection. `references/usage_examples.md`
(Complete Analysis Example) has a worked version.

## Best Practices

1. **Keys**: keep ODP and TSDR keys in environment variables, never in code or
   version control; they are different keys sent in different headers.
2. **Rate limits**: TSDR allows 60 requests/minute per key (4/minute for PDF/ZIP);
   back off exponentially on HTTP 429 for every USPTO API.
3. **Coverage**: Patent File Wrapper holds applications filed from 2001-01-01;
   use bulk data for older patents and for claims/description full text.
4. **Data handling**: many fields are absent for pending or older applications —
   handle missing keys, and parse dates as `YYYY-MM-DD` strings.
5. **Reproducibility**: ODP is refreshed daily; record the query date with results.

## Resources

- **Open Data Portal**: https://data.uspto.gov/ (APIs → Getting Started; interactive Swagger UI needs an ODP key)
- **PatentsView → ODP transition guide**: https://data.uspto.gov/support/transition-guide/patentsview
- **PEDS → ODP transition guide** (PEDS-to-ODP API mapping): https://data.uspto.gov/support/transition-guide/peds
- **TSDR key manager**: https://account.uspto.gov/api-manager/
- **ODP support**: data@uspto.gov

### Reference Files
- `references/usage_examples.md` - Worked Python examples per task
- `references/patentsearch_api.md` - PatentsView PatentSearch API (offline since 2026-03-20; historical)
- `references/peds_api.md` - Transaction codes and prosecution analysis (PEDS sections historical)
- `references/trademark_api.md` - TSDR trademark API
- `references/additional_apis.md` - Office actions, citations, PTAB, litigation datasets

### Scripts
- `scripts/patent_search.py` - ODP Patent File Wrapper search client
- `scripts/peds_client.py` - ODP file-wrapper client (PEDS successor)
- `scripts/trademark_client.py` - TSDR trademark client
