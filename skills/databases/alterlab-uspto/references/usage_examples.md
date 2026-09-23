# USPTO Usage Examples

> **Status (verified 2026-09-23).** PEDS, the Assignment Search API, and the PatentsView PatentSearch API are offline (see the status table in `SKILL.md`). The examples below use the Open Data Portal (`https://api.uspto.gov`, `X-API-KEY` header, `USPTO_ODP_API_KEY`) and TSDR (`USPTO-API-KEY` header, `USPTO_TSDR_API_KEY`).

Worked Python examples for the helper scripts and direct API calls, grouped by
task. For full API references see `patentsearch_api.md`, `peds_api.md`,
`trademark_api.md`, and `additional_apis.md`.

Set API keys as environment variables before running:

```bash
export USPTO_ODP_API_KEY="..."    # Open Data Portal key (data.uspto.gov)
export USPTO_TSDR_API_KEY="..."   # TSDR key (account.uspto.gov/api-manager)
```

---

## Task 1: Searching Patents (ODP Patent File Wrapper)

The PatentsView PatentSearch API is offline (see `SKILL.md`), so searches go to
the ODP Patent File Wrapper: bibliographic data for applications filed from
2001-01-01, granted or pending. Set `USPTO_ODP_API_KEY` first.

### Basic Patent Search

```python
from scripts.patent_search import PatentSearchClient

client = PatentSearchClient()

# Invention-title phrase, newest grants first
results = client.search_by_title(
    "machine learning",
    sort=[{"field": "applicationMetaData.grantDate", "order": "desc"}],
    limit=50,
)
for rec in results["patentFileWrapperDataBag"]:
    meta = rec["applicationMetaData"]
    print(rec["applicationNumberText"], meta.get("patentNumber"), meta.get("inventionTitle"))
```

```python
client.search_by_inventor("John Smith")            # first-named inventor
client.search_by_applicant("Google LLC")           # first-named applicant (not current owner)
client.search_by_date_range("2024-01-01", "2024-12-31")   # grant dates
client.get_patent("11234567")                      # one granted patent's file wrapper
```

### Advanced Search (direct API)

```python
import os
import requests

body = {
    "q": 'applicationMetaData.inventionTitle:"neural network" AND applicationMetaData.firstApplicantName:Microsoft*',
    "filters": [{"name": "applicationMetaData.applicationStatusDescriptionText", "value": ["Patented Case"]}],
    "rangeFilters": [{"field": "applicationMetaData.grantDate", "valueFrom": "2023-01-01", "valueTo": "2024-12-31"}],
    "fields": ["applicationNumberText", "applicationMetaData"],
    "pagination": {"offset": 0, "limit": 100},
}
r = requests.post("https://api.uspto.gov/api/v1/patent/applications/search",
                  headers={"X-API-KEY": os.environ["USPTO_ODP_API_KEY"]}, json=body, timeout=60)
data = r.json() if r.status_code != 404 else {"count": 0, "patentFileWrapperDataBag": []}
print(data["count"])
```

A simple GET form also exists:
`GET /api/v1/patent/applications/search?q=applicationMetaData.inventionTitle:lidar&limit=25`.
CPC codes are in `applicationMetaData.cpcClassificationBag`. Claims, abstracts,
and descriptions are not in the file wrapper — use the ODP bulk grant /
pre-grant XML products for full text.

The PatentsView query operators (`_text_all`, `_gte`, `_and`, …) and endpoints
(`/patent`, `/inventor`, `/assignee`, …) are documented in
`patentsearch_api.md` for reading older code; they do not apply to ODP.

---

## Task 2: Patent Examination Data (ODP Patent File Wrapper)

PEDS was retired on 2025-03-14; the same prosecution data comes from the
Patent File Wrapper endpoints. `scripts/peds_client.py` keeps the old
`PEDSHelper` name as an alias of `FileWrapperClient`.

### Basic Usage

```python
from scripts.peds_client import FileWrapperClient

client = FileWrapperClient()          # reads USPTO_ODP_API_KEY

record = client.get_application("16123456")        # full file-wrapper record
meta = record["applicationMetaData"]
print(meta["inventionTitle"], "|", meta["applicationStatusDescriptionText"])

patent_record = client.get_patent("11234567")      # look up by granted patent number
```

```python
# Transaction history: eventDataBag items
for event in client.get_transaction_history("16123456"):
    print(event["eventDate"], event["eventCode"], event["eventDescriptionText"])

# Office-action events only (CTNF, CTFR, AOPF, NOA)
for event in client.get_office_actions("16123456"):
    print(event["eventDate"], event["eventCode"])
```

```python
summary = client.get_status_summary("16123456")
print(summary["status"], summary["filing_date"], summary["days_since_filing"])
if summary["is_patented"]:
    print(summary["patent_number"], summary["grant_date"])

family = client.get_continuity("16123456")          # {"parents": [...], "children": [...]}
owners = client.get_assignments("16123456")         # assignmentBag records
```

### Prosecution Analysis

```python
analysis = client.analyze_prosecution("16123456")
print(analysis["non_final_rejections"], analysis["final_rejections"],
      analysis["responses_filed"], analysis["allowed"], analysis["abandoned"])
```

### Common Transaction Codes

- **CTNF** — Non-final rejection mailed
- **CTFR** — Final rejection mailed
- **NOA** — Notice of allowance mailed
- **WRIT** — Response filed
- **ISS.FEE** — Issue fee payment
- **ABND** — Application abandoned
- **AOPF** — Office action mailed

---

## Task 3: Trademarks (TSDR)

Access trademark status, ownership, and prosecution history.

### Basic Trademark Usage

```python
from scripts.trademark_client import TrademarkClient

client = TrademarkClient()

# By serial number
tm_data = client.get_trademark_by_serial("87654321")

# By registration number
tm_data = client.get_trademark_by_registration("5678901")
```

```python
# Trademark status
status = client.get_trademark_status("87654321")
print(f"Mark: {status['mark_text']}")
print(f"Status: {status['status']}")
print(f"Filing date: {status['filing_date']}")

if status['is_registered']:
    print(f"Registration #: {status['registration_number']}")
    print(f"Registration date: {status['registration_date']}")
```

```python
# Trademark health
health = client.check_trademark_health("87654321")
print(f"Mark: {health['mark']}")
print(f"Status: {health['status']}")

for alert in health['alerts']:
    print(alert)

if health['needs_attention']:
    print("⚠️  This mark needs attention!")
```

### Trademark Portfolio Monitoring

```python
def monitor_portfolio(serial_numbers, api_key):
    """Monitor trademark portfolio health."""
    client = TrademarkClient(api_key)

    results = {
        'active': [],
        'pending': [],
        'problems': []
    }

    for sn in serial_numbers:
        health = client.check_trademark_health(sn)

        if 'REGISTERED' in health['status']:
            results['active'].append(health)
        elif 'PENDING' in health['status'] or 'PUBLISHED' in health['status']:
            results['pending'].append(health)
        elif health['needs_attention']:
            results['problems'].append(health)

    return results
```

### Common Trademark Statuses

- **REGISTERED** — Active registered mark
- **PENDING** — Under examination
- **PUBLISHED FOR OPPOSITION** — In opposition period
- **ABANDONED** — Application abandoned
- **CANCELLED** — Registration cancelled
- **SUSPENDED** — Examination suspended
- **REGISTERED AND RENEWED** — Registration renewed

---

## Task 4: Assignments & Ownership

The Assignment Search API (`assignment-api.uspto.gov`) no longer resolves.
Recorded assignments for an application come from the Patent File Wrapper:

```python
from scripts.peds_client import FileWrapperClient

client = FileWrapperClient()
for a in client.get_assignments("16123456"):          # assignmentBag records
    assignors = ", ".join(x.get("assignorName", "?") for x in a.get("assignorBag") or [])
    assignees = ", ".join(x.get("assigneeNameText", "?") for x in a.get("assigneeBag") or [])
    print(a.get("assignmentRecordedDate"), a.get("reelAndFrameNumber"), a.get("conveyanceText"))
    print(f"  {assignors} -> {assignees}")
```

The key names inside `assignorBag` / `assigneeBag` above are illustrative —
print one record first and adjust. For company-wide ownership questions (all
patents assigned to a firm), use the assignment datasets in the ODP bulk-data
catalog rather than per-application calls.

### Common Assignment Types

- **ASSIGNMENT OF ASSIGNORS INTEREST** — Ownership transfer
- **SECURITY AGREEMENT** — Collateral/security interest
- **MERGER** — Corporate merger
- **CHANGE OF NAME** — Name change
- **ASSIGNMENT OF PARTIAL INTEREST** — Partial ownership

---

## Complete Analysis Example

Combine the file-wrapper sections for a full picture of one patent:

```python
from scripts.peds_client import FileWrapperClient


def comprehensive_patent_analysis(patent_number: str) -> dict:
    """Bibliographic data, prosecution, family, and ownership for one US patent."""
    client = FileWrapperClient()                       # USPTO_ODP_API_KEY
    record = client.get_patent(patent_number)
    if not record:
        return {}
    app = record["applicationNumberText"]
    meta = record["applicationMetaData"]
    results = {
        "application": app,
        "title": meta.get("inventionTitle"),
        "applicant": meta.get("firstApplicantName"),
        "filed": meta.get("filingDate"),
        "granted": meta.get("grantDate"),
        "cpc": meta.get("cpcClassificationBag"),
        "prosecution": client.analyze_prosecution(app),
        "family": client.get_continuity(app),
        "assignments": client.get_assignments(app),
    }
    p = results["prosecution"]
    print(f"{patent_number}: {results['title']} ({results['applicant']})")
    print(f"  filed {results['filed']}, granted {results['granted']}")
    print(f"  {p['non_final_rejections']} non-final / {p['final_rejections']} final rejections, "
          f"{p['responses_filed']} responses")
    return results
```

Forward/backward patent citations were a PatentsView feature; until that API
returns, take them from the ODP bulk grant XML (references cited) or from the
office-action citations API for examiner-cited art.
