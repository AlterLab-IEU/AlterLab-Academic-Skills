---
name: alterlab-uspto
description: Access USPTO patent and trademark data — keyless full-text patent search through USPTO Patent Public Search, patent legal events and recorded assignments from Google Patents pages, and trademark status, owners, goods/services and prosecution history from TSDR status pages — with optional Open Data Portal (ODP) and TSDR API keys for Patent File Wrapper examination history, continuity, office actions and PTAB data. Use when searching patents or trademarks, conducting prior art searches, retrieving patent examination or assignment records, or doing intellectual property (IP) analysis. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read WebFetch Bash(curl:*) Bash(python:*)
compatibility: No API key required. Keyless — USPTO Patent Public Search (ppubs.uspto.gov, anonymous session, full-text grants and applications) and TSDR status pages (tsdr.uspto.gov/statusview) via scripts/uspto_public.py, plus Google Patents pages through WebFetch for legal events and assignments. Optional USPTO_ODP_API_KEY (Patent File Wrapper, office actions, PTAB) and USPTO_TSDR_API_KEY (TSDR API). PEDS, Assignment Search and PatentsView are offline (2026).
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    last_updated: "2026-10-22"
    credentials: "optional: USPTO_ODP_API_KEY (ODP Patent File Wrapper transactions, continuity, office actions, PTAB, bulk-data catalog), USPTO_TSDR_API_KEY (TSDR API instead of the public status page), USPTO_API_KEY (fallback name read for either)"
---

# USPTO Database

## Overview

USPTO data for patents and trademarks, for IP analysis and prior art searches.
**Without any key** the skill searches full text of US grants and applications in
USPTO's own Patent Public Search, reads a patent's legal events (status changes,
recorded assignments with reel/frame) from its Google Patents page, and reads a
trademark's status, owner, goods/services and prosecution history from its TSDR
status page. The keyed **USPTO Open Data Portal (ODP)** at `https://api.uspto.gov`
adds the complete file-wrapper transaction list, continuity, office actions and
PTAB data; several older services were retired in 2025–2026, so check the status
table below before reusing older code.

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

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-openalex`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

## Keyless Routes (default — verified live 2026-10-22)

| Need | Keyless route | Notes |
|------|---------------|-------|
| Patent / publication search (title, abstract, claims, assignee, inventor, CPC, dates) | `python scripts/uspto_public.py search 'google.as. AND G06N$.cpc. AND @pd>=20230101<=20241231'` (or `--assignee google --cpc G06N --from 2023-01-01 --to 2024-12-31`) → 916 grants | USPTO Patent Public Search backend (anonymous session); undocumented JSON, keep volumes modest. Syntax: `.ti. .ab. .clm. .as. .aanm. .in. .cpc. .pn.`, `$` truncation, `@pd`/`@ad` date ranges; `--db USPAT,US-PGPUB` |
| One patent: bibliographic data, abstract, claims, cited US references | `python scripts/uspto_public.py doc 11234567` | assignee at grant, application number, CPC |
| Application number → grant / pre-grant publication | `python scripts/uspto_public.py app 16/123,456` | unpublished or abandoned-before-publication applications are not in Patent Public Search |
| Legal events: USPTO status changes (STPP/STCF), recorded assignments (AS, reel/frame), fees | WebFetch `https://patents.google.com/patent/US11234567B2/en` ("Legal events" table) | Google blocks scripted fetches; WebFetch worked on 2026-10-22 but later calls got HTTP 503 — retry, and if it stays blocked say so (do not guess events). STPP rows are status snapshots, not the full transaction list |
| Trademark status, owner, goods/services, classes, prosecution history | `python scripts/uspto_public.py trademark 87654321` (`--registration` for a reg. no.) or `trademark_client.py --health 87654321` | parses `https://tsdr.uspto.gov/statusview/sn87654321` |
| EP bibliographic data (EPO, linked open data) | `https://data.epo.org/linked-data/data/publication/EP/1000000/A1/-.json` | keyless; EPO OPS needs registration |

Not reachable keylessly from here: the full file-wrapper transaction list of pending
applications, office-action text/rejections, PTAB records (ODP key), and the PatentsView
and `bulkdata.uspto.gov` hosts. Say which route produced each fact.

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

### Optional API Keys (keyless routes above need none)

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

- **`scripts/uspto_public.py`** — keyless: Patent Public Search (`search`, `doc`) and
  TSDR status pages (`trademark`); standard library only
- **`scripts/patent_search.py`** — patent search; keyless Patent Public Search by
  default, ODP Patent File Wrapper with `USPTO_ODP_API_KEY` (`--backend odp` without
  a key exits 2 naming the variable instead of answering from another source)
- **`scripts/peds_client.py`** — ODP file-wrapper client, the PEDS successor
  (`FileWrapperClient`, alias `PEDSHelper`): status summary, transactions,
  office-action events, prosecution statistics, continuity, assignments
- **`scripts/trademark_client.py`** — trademark status, owners, goods/services,
  prosecution history, health check with the next Section 8/9 deadline; keyless
  TSDR status page by default, TSDR API with `USPTO_TSDR_API_KEY`

The keyed ODP/TSDR paths were checked against the ODP OpenAPI spec and live endpoint
routing (401 without a key); run them with your own key before relying on them.

## Task 1: Searching Patents

Keyless (default): `python scripts/uspto_public.py search '<query>' --limit 50` — see
"Keyless Routes". `.as.` matches the assignee printed at grant; for later ownership
changes read the patent's Google Patents legal events (Task 4).

With an ODP key, POST a JSON body to `https://api.uspto.gov/api/v1/patent/applications/search`:

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

Keyless: resolve the application to its grant or publication (`uspto_public.py app
16/123,456` → US 10902286 B2, filed 2018-09-06, granted 2021-01-26), then WebFetch its
Google Patents page and read the "Legal events"
STPP/STCF rows (e.g. "NON FINAL ACTION MAILED", "FINAL REJECTION MAILED", "NOTICE OF
ALLOWANCE MAILED", "PATENTED CASE"). Count rejections from them only as a lower bound —
they are status snapshots, and some actions appear only as the response that followed
them — and compute pendency from the filing and grant dates. The full transaction list
(event codes below) needs the ODP key:

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

### Keyless: the TSDR status page

`python scripts/uspto_public.py trademark 87654321` (or `trademark_client.py --health
87654321`) reads `https://tsdr.uspto.gov/statusview/sn87654321` — the page behind the
TSDR web app — and returns mark, TM5 status descriptor, status text and date,
filing/registration dates, owner, goods/services with classes and first use, and the
prosecution history. `--health` adds alerts and the next Section 8 / Sections 8 & 9
deadline. Verified: 87654321 = BENTOSTACK, Reg. 5553479 (2018-09-04), LIVE, Sections 8
& 15 accepted 2025-01-28, next renewal due 2028-09-04.

### Using the TSDR API (optional key)

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

Keyless: WebFetch the patent's Google Patents page (`https://patents.google.com/patent/US11234567B2/en`)
and read the "Legal events" rows with code **AS** — each gives the recorded date, owner
(assignee), assignors, conveyance and reel/frame (verified: US11234567B2 → assignment
from the inventors to SharkNinja Operating LLC, reel/frame 047902/0718; security interest
to Bank of America, N.A., 064600/0098, 2023-07-20). Report reel/frame so the record can be
checked at USPTO.

The Assignment Search API host (`assignment-api.uspto.gov`) is gone. With an ODP key, for a given
application, `GET https://api.uspto.gov/api/v1/patent/applications/{app}/assignment`
returns `assignmentBag[]` with `reelAndFrameNumber`, `conveyanceText`,
`assignmentRecordedDate`, `assignorBag`, and `assigneeBag`
(`scripts/peds_client.py --assignments {app}`). For company-wide ownership
questions use the assignment datasets in the ODP bulk-data catalog.

**Common conveyance types**: `ASSIGNMENT OF ASSIGNORS INTEREST` (ownership
transfer), `SECURITY AGREEMENT`, `MERGER`, `CHANGE OF NAME`, `ASSIGNMENT OF
PARTIAL INTEREST`.

## Task 5: Office Actions, Citations, and PTAB (ODP key)

No verified keyless route; without a key, say so and offer what the keyless routes give
(cited US references from `uspto_public.py doc`, status events from Google Patents).

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

1. **Keys (optional)**: keep ODP and TSDR keys in environment variables, never in code
   or version control; they are different keys sent in different headers.
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
- `scripts/uspto_public.py` - keyless Patent Public Search + TSDR status pages
- `scripts/patent_search.py` - patent search (keyless by default; ODP with a key)
- `scripts/peds_client.py` - ODP file-wrapper client (PEDS successor)
- `scripts/trademark_client.py` - trademark client (keyless status page; TSDR API with a key)
