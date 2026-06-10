# USPTO Usage Examples

Worked Python examples for the helper scripts and direct API calls, grouped by
task. For full API references see `patentsearch_api.md`, `peds_api.md`,
`trademark_api.md`, and `additional_apis.md`.

Set API keys as environment variables before running:

```bash
export USPTO_API_KEY="your_api_key_here"
export PATENTSVIEW_API_KEY="your_api_key_here"
```

---

## Task 1: Searching Patents (PatentSearch API)

The PatentSearch API uses a JSON query language with various operators for
flexible searching.

### Basic Patent Search

```python
from scripts.patent_search import PatentSearchClient

client = PatentSearchClient()

# Search for machine learning patents (keywords in abstract)
results = client.search_patents({
    "patent_abstract": {"_text_all": ["machine", "learning"]}
})

for patent in results['patents']:
    print(f"{patent['patent_number']}: {patent['patent_title']}")
```

```python
# Search by inventor
results = client.search_by_inventor("John Smith")

# Search by assignee/company
results = client.search_by_assignee("Google")

# Search by date range
results = client.search_by_date_range("2024-01-01", "2024-12-31")

# Search by CPC classification (H04N = video/image tech)
results = client.search_by_classification("H04N")
```

### Advanced Patent Search

Combine multiple criteria with logical operators:

```python
results = client.advanced_search(
    keywords=["artificial", "intelligence"],
    assignee="Microsoft",
    start_date="2023-01-01",
    end_date="2024-12-31",
    cpc_codes=["G06N", "G06F"]  # AI and computing classifications
)
```

### Direct API Usage

For complex queries, use the API directly:

```python
import requests

url = "https://search.patentsview.org/api/v1/patent"
headers = {
    "X-Api-Key": "YOUR_API_KEY",
    "Content-Type": "application/json"
}

query = {
    "q": {
        "_and": [
            {"patent_date": {"_gte": "2024-01-01"}},
            {"assignee_organization": {"_text_any": ["Google", "Alphabet"]}},
            {"cpc_subclass_id": ["G06N", "H04N"]}
        ]
    },
    "f": ["patent_number", "patent_title", "patent_date", "inventor_name"],
    "s": [{"patent_date": "desc"}],
    "o": {"per_page": 100, "page": 1}
}

response = requests.post(url, headers=headers, json=query)
results = response.json()
```

### Query Operators

- **Equality**: `{"field": "value"}` or `{"field": {"_eq": "value"}}`
- **Comparison**: `_gt`, `_gte`, `_lt`, `_lte`, `_neq`
- **Text search**: `_text_all`, `_text_any`, `_text_phrase`
- **String matching**: `_begins`, `_contains`
- **Logical**: `_and`, `_or`, `_not`

**Best Practice**: Use `_text_*` operators for text fields (more performant than
`_contains` or `_begins`).

### Available Patent Endpoints

- `/patent` — Granted patents
- `/publication` — Pregrant publications
- `/inventor` — Inventor information
- `/assignee` — Assignee information
- `/cpc_subclass`, `/cpc_at_issue` — CPC classifications
- `/uspc` — US Patent Classification
- `/ipc` — International Patent Classification
- `/claims`, `/brief_summary_text`, `/detail_description_text` — Text data (beta)

---

## Task 2: Patent Examination Data (PEDS)

PEDS provides comprehensive prosecution history including transaction events,
status changes, and examination timeline.

### Installation

```bash
uv pip install uspto-opendata-python
```

### Basic PEDS Usage

```python
from scripts.peds_client import PEDSHelper

helper = PEDSHelper()

# By application number
app_data = helper.get_application("16123456")
print(f"Title: {app_data['title']}")
print(f"Status: {app_data['app_status']}")

# By patent number
patent_data = helper.get_patent("11234567")
```

```python
# Transaction history
transactions = helper.get_transaction_history("16123456")
for trans in transactions:
    print(f"{trans['date']}: {trans['code']} - {trans['description']}")
```

```python
# Office actions
office_actions = helper.get_office_actions("16123456")
for oa in office_actions:
    if oa['code'] == 'CTNF':
        print(f"Non-final rejection: {oa['date']}")
    elif oa['code'] == 'CTFR':
        print(f"Final rejection: {oa['date']}")
    elif oa['code'] == 'NOA':
        print(f"Notice of allowance: {oa['date']}")
```

```python
# Status summary
summary = helper.get_status_summary("16123456")
print(f"Current status: {summary['current_status']}")
print(f"Filing date: {summary['filing_date']}")
print(f"Pendency: {summary['pendency_days']} days")

if summary['is_patented']:
    print(f"Patent number: {summary['patent_number']}")
    print(f"Issue date: {summary['issue_date']}")
```

### Prosecution Analysis

```python
analysis = helper.analyze_prosecution("16123456")

print(f"Total office actions: {analysis['total_office_actions']}")
print(f"Non-final rejections: {analysis['non_final_rejections']}")
print(f"Final rejections: {analysis['final_rejections']}")
print(f"Allowed: {analysis['allowance']}")
print(f"Responses filed: {analysis['responses']}")
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

Both patents and trademarks have Assignment Search APIs for tracking ownership
changes.

### Patent Assignment API

**Base URL**: `https://assignment-api.uspto.gov/patent/v1.4/`

```python
import requests
import xml.etree.ElementTree as ET

def get_patent_assignments(patent_number, api_key):
    url = f"https://assignment-api.uspto.gov/patent/v1.4/assignment/patent/{patent_number}"
    headers = {"X-Api-Key": api_key}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text  # Returns XML

assignments_xml = get_patent_assignments("11234567", api_key)
root = ET.fromstring(assignments_xml)

for assignment in root.findall('.//assignment'):
    recorded_date = assignment.find('recordedDate').text
    assignor = assignment.find('.//assignor/name').text
    assignee = assignment.find('.//assignee/name').text
    conveyance = assignment.find('conveyanceText').text

    print(f"{recorded_date}: {assignor} → {assignee}")
    print(f"  Type: {conveyance}\n")
```

```python
# Search by company name
def find_company_patents(company_name, api_key):
    url = "https://assignment-api.uspto.gov/patent/v1.4/assignment/search"
    headers = {"X-Api-Key": api_key}
    data = {"criteria": {"assigneeName": company_name}}

    response = requests.post(url, headers=headers, json=data)
    return response.text
```

### Common Assignment Types

- **ASSIGNMENT OF ASSIGNORS INTEREST** — Ownership transfer
- **SECURITY AGREEMENT** — Collateral/security interest
- **MERGER** — Corporate merger
- **CHANGE OF NAME** — Name change
- **ASSIGNMENT OF PARTIAL INTEREST** — Partial ownership

---

## Complete Analysis Example

Combine multiple APIs for full patent intelligence:

```python
def comprehensive_patent_analysis(patent_number, api_key):
    """
    Full patent analysis using multiple USPTO APIs.
    """
    from scripts.patent_search import PatentSearchClient
    from scripts.peds_client import PEDSHelper

    results = {}

    # 1. Get patent details
    patent_client = PatentSearchClient(api_key)
    patent_data = patent_client.get_patent(patent_number)
    results['patent'] = patent_data

    # 2. Get examination history
    peds = PEDSHelper()
    results['prosecution'] = peds.analyze_prosecution(patent_number)
    results['status'] = peds.get_status_summary(patent_number)

    # 3. Get assignment history
    import requests
    assign_url = f"https://assignment-api.uspto.gov/patent/v1.4/assignment/patent/{patent_number}"
    assign_resp = requests.get(assign_url, headers={"X-Api-Key": api_key})
    results['assignments'] = assign_resp.text if assign_resp.status_code == 200 else None

    # 4. Analyze results
    print(f"\n=== Patent {patent_number} Analysis ===\n")
    print(f"Title: {patent_data['patent_title']}")
    print(f"Assignee: {', '.join(patent_data.get('assignee_organization', []))}")
    print(f"Issue Date: {patent_data['patent_date']}")

    print(f"\nProsecution:")
    print(f"  Office Actions: {results['prosecution']['total_office_actions']}")
    print(f"  Rejections: {results['prosecution']['non_final_rejections']} non-final, {results['prosecution']['final_rejections']} final")
    print(f"  Pendency: {results['prosecution']['pendency_days']} days")

    # Analyze citations
    if 'cited_patent_number' in patent_data:
        print(f"\nCitations:")
        print(f"  Cites: {len(patent_data['cited_patent_number'])} patents")
    if 'citedby_patent_number' in patent_data:
        print(f"  Cited by: {len(patent_data['citedby_patent_number'])} patents")

    return results
```
