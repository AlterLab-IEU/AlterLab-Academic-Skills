---
name: alterlab-edgartools
description: Accesses, analyzes, and extracts data from SEC EDGAR filings using the edgartools Python library. Use when working with SEC filings, financial statements (income statement, balance sheet, cash flow), XBRL financial data, insider trading (Form 4), institutional holdings (13F), company financials, annual/quarterly reports (10-K, 10-Q), proxy statements (DEF 14A), 8-K current events, company screening by ticker/CIK/industry, multi-period financial analysis, or any SEC regulatory filings. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read WebFetch Bash(curl:*) Bash(python:*)
compatibility: Requires edgartools 5.x (current 5.58.0, Python >=3.10). No API key, but SEC fair-access rules require an identity (name + email) sent as the User-Agent and at most 10 requests/second. Needs network access to SEC EDGAR.
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# edgartools — SEC EDGAR Data

Python library for accessing all SEC filings since 1994 with structured data extraction.

## When to Use This Skill

- Retrieving specific filings (10-K, 10-Q, 8-K, DEF 14A, S-1, 13F, Form 4, SC 13D/G, Form D) for a company or period
- Extracting financial statements or XBRL facts exactly as filed, including multi-period stitching
- Insider-trading, institutional-holdings, or proxy/compensation data at the filer level
- Company metadata from EDGAR (CIK, SIC, fiscal year end, filer status)

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Market prices, OHLCV, quotes, or technical indicators | `alterlab-alpha-vantage` |
| Macroeconomic time series (GDP, corporate profits, rates) by FRED series ID | `alterlab-fred` |
| Aggregate hedge-fund statistics from Form PF published by the OFR | `alterlab-hedgefund-monitor` |
| Federal debt, Treasury statements, or auction results | `alterlab-usfiscaldata` |

## Authentication (Required)

The SEC requires identification for API access. Always set identity before any operations:

```python
from edgar import set_identity
set_identity("Your Name your.email@example.com")
```

Set via environment variable to avoid hardcoding: `EDGAR_IDENTITY="Your Name your@email.com"`.

edgartools sends this identity as the HTTP User-Agent the SEC asks for ("Sample Company Name AdminContact@<domain>.com") and throttles itself to 9 requests/second by default (`EDGAR_RATE_LIMIT_PER_SEC`), under the SEC's 10 requests/second fair-access ceiling — keep that default for sec.gov, because the SEC may block IP addresses that exceed it.

## Installation

```bash
uv pip install edgartools
# For AI/MCP features:
uv pip install "edgartools[ai]"
```

API examples here are checked against edgartools 5.58.0 (current as of 2026-09). To run a one-off without a venv: `uv run --with edgartools python ...`. In 5.x, `cashflow_statement()` is a deprecated alias (removed in 6.0) — use `cash_flow_statement()`.

## Core Workflow

### Find a Company

```python
from edgar import Company, find

company = Company("AAPL")        # by ticker
company = Company(320193)         # by CIK (fastest)
results = find("Apple")           # by name search
```

### Get Filings

```python
# Company filings
filings = company.get_filings(form="10-K")
filing = filings.latest()

# Global search across all filings
from edgar import get_filings
filings = get_filings(2024, 1, form="10-K")

# By accession number
from edgar import get_by_accession_number
filing = get_by_accession_number("0000320193-23-000106")
```

### Extract Structured Data

```python
# Form-specific object (most common approach)
tenk = filing.obj()              # Returns TenK, EightK, Form4, ThirteenF, etc.

# Financial statements (10-K/10-Q)
financials = company.get_financials()     # annual
financials = company.get_quarterly_financials()  # quarterly
income = financials.income_statement()
balance = financials.balance_sheet()
cashflow = financials.cash_flow_statement()

# XBRL data
xbrl = filing.xbrl()
income = xbrl.statements.income_statement()
```

### Access Filing Content

```python
text = filing.text()             # plain text
html = filing.html()             # HTML
md = filing.markdown()           # markdown (good for LLM processing)
filing.open()                    # open in browser
```

## Key Company Properties

```python
company.name                     # "Apple Inc."
company.cik                      # 320193
company.get_ticker()             # "AAPL" (primary); company.tickers -> list
company.industry                 # "ELECTRONIC COMPUTERS"
company.sic                      # "3571"
company.shares_outstanding       # 15115785000.0
company.public_float             # 2899948348000.0
company.fiscal_year_end          # "0930"
company.get_exchanges()          # ["Nasdaq"]
```

## Form → Object Mapping

| Form | Object | Key Properties |
|------|--------|----------------|
| 10-K | TenK | `financials`, `income_statement`, `balance_sheet`, `risk_factors` |
| 10-Q | TenQ | `financials`, `income_statement`, `balance_sheet` |
| 8-K | EightK | `items`, `press_releases` |
| Form 4 | Form4 | `reporting_owners`, `insider_name`, `market_trades`, `to_dataframe()` |
| 13F-HR | ThirteenF | `infotable`, `total_value`, `holdings` |
| DEF 14A | ProxyStatement | `executive_compensation`, `voting_proposals`, `peo_total_comp` |
| SC 13D/G | Schedule13D / Schedule13G | `total_shares`, `total_percent`, `items` (13D) |
| Form D | FormD | `offering_data`, `related_persons`, `primary_issuer` |

**Important:** `filing.financials` does NOT exist. Use `filing.obj().financials`.

## Common Pitfalls

- `filing.financials` → AttributeError; use `filing.obj().financials`
- `get_filings()` has no `limit` param; use `.head(n)` or `.latest(n)`
- Prefer `amendments=False` for multi-period analysis (amended filings may be incomplete)
- Always check for `None` before accessing optional data

## Reference Files

Load these when you need detailed information:

- **[companies.md](references/companies.md)** — Finding companies, screening, batch lookups, Company API
- **[filings.md](references/filings.md)** — Working with filings, attachments, exhibits, Filings collection API
- **[financial-data.md](references/financial-data.md)** — Financial statements, convenience methods, DataFrame export, multi-period analysis
- **[xbrl.md](references/xbrl.md)** — XBRL parsing, fact querying, multi-period stitching, standardization
- **[data-objects.md](references/data-objects.md)** — All supported form types and their structured objects
- **[entity-facts.md](references/entity-facts.md)** — EntityFacts API, FactQuery, FinancialStatement, FinancialFact
- **[ai-integration.md](references/ai-integration.md)** — MCP server setup, Skills installation, `.docs` and `.to_context()` properties

Cite the filing (company, form, accession number, filing date) for every figure you report.

Part of the AlterLab Academic Skills suite.
