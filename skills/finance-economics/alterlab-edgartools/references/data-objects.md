# edgartools — Data Objects Reference

Every SEC filing can be parsed into a structured Python object:

```python
obj = filing.obj()  # returns TenK, EightK, ThirteenF, Form4, etc.
```

## Supported Forms

### Annual & Quarterly Reports (10-K / 10-Q) → TenK / TenQ

```python
tenk = filing.obj()  # or tenq for 10-Q

# Financial statements
tenk.income_statement    # formatted income statement
tenk.balance_sheet       # balance sheet
tenk.financials          # Financials object with all statements

# Document sections
tenk.risk_factors        # full risk factors text
tenk.business            # business description
tenk.management_discussion  # MD&A (also tenk.sections['mda'])

# Usage via Financials (these are methods on the Financials object)
if tenk.financials:
    income = tenk.financials.income_statement()
    balance = tenk.financials.balance_sheet()
    cashflow = tenk.financials.cash_flow_statement()
```

**Note:** Always check `tenk.financials` before accessing — not all filings have XBRL data.

---

### Current Events (8-K) → EightK

```python
eightk = filing.obj()

eightk.items           # list of reported event codes (e.g. ["2.02", "9.01"])
eightk.press_releases  # attached press releases

print(f"Items: {eightk.items}")
```

Common 8-K item codes:
- `1.01` — Entry into material agreement
- `2.02` — Results of operations (earnings)
- `5.02` — Director/officer changes
- `8.01` — Other events

---

### Insider Trades (Form 4) → Form4 (Ownership)

```python
form4 = filing.obj()

form4.insider_name          # reporting owner name(s)
form4.reporting_owners      # ReportingOwners (names, positions)
form4.market_trades         # open-market buys/sells with prices, shares, dates
form4.to_dataframe()        # all transactions as a DataFrame

# Get HTML table
html = form4.to_html()
```

Also covers:
- Form 3 — Initial ownership statement
- Form 5 — Annual changes in beneficial ownership

---

### Beneficial Ownership (SC 13D / SC 13G) → Schedule13D / Schedule13G

```python
schedule = filing.obj()

schedule.total_shares                          # aggregate beneficial ownership
schedule.items.item4_purpose_of_transaction    # activist intent (13D only)
schedule.items.item5_percentage_of_class       # ownership percentage (13D)
schedule.total_percent                         # aggregate percent of class
```

- **SC 13D**: Activist investors (5%+ with intent to influence)
- **SC 13G**: Passive holders (5%+)

---

### Institutional Portfolios (13F-HR) → ThirteenF

```python
thirteenf = filing.obj()

thirteenf.infotable    # full holdings DataFrame
thirteenf.total_value  # portfolio market value

# Analyze holdings
holdings_df = thirteenf.infotable
print(holdings_df.head())
print(f"Total AUM: ${thirteenf.total_value/1e9:.1f}B")
```

---

### Proxy & Governance (DEF 14A) → ProxyStatement

```python
proxy = filing.obj()

proxy.executive_compensation  # pay tables (5-year DataFrame)
proxy.voting_proposals        # shareholder vote items
proxy.peo_name                # "Mr. Cook" (principal exec officer)
proxy.peo_total_comp          # CEO total compensation
```

---

### Private Offerings (Form D) → FormD

```python
formd = filing.obj()

formd.offering_data     # offering details and amounts
formd.related_persons   # executives, directors, promoters
formd.primary_issuer    # issuer details
```

---

### Crowdfunding Offerings (Form C) → FormC

```python
formc = filing.obj()

formc.offering_information       # target amount, deadline, securities
formc.annual_report_disclosure   # issuer financials (C-AR)
```

---

### Insider Sale Notices (Form 144) → Form144

```python
form144 = filing.obj()

form144.units_to_be_sold      # units proposed for sale
form144.market_value          # aggregate market value of the proposed sale
form144.securities_to_be_sold # security-level details
```

---

### Fund Voting Records (N-PX) → NPX

```python
npx = filing.obj()

npx.proxy_votes  # vote records by proposal
```

---

### ABS Distribution Reports (Form 10-D) → TenD (CMBS only)

```python
ten_d = filing.obj()

ten_d.loans           # loan-level DataFrame
ten_d.properties      # property-level DataFrame
ten_d.asset_data.summary()  # pool statistics
```

---

### Municipal Advisors (MA-I) → MunicipalAdvisorForm

```python
mai = filing.obj()
mai.applicant  # applicant/advisor details (also mai.filer)
```

---

### Foreign Private Issuers (20-F) → TwentyF

```python
twentyf = filing.obj()
twentyf.financials  # financial data for foreign issuers
```

---

## Complete Form → Class Mapping

| Form | Class | Key Attributes |
|------|-------|----------------|
| 10-K | TenK | `financials`, `income_statement`, `risk_factors`, `business`, `management_discussion` |
| 10-Q | TenQ | `financials`, `income_statement`, `balance_sheet` |
| 8-K | EightK | `items`, `press_releases` |
| 20-F | TwentyF | `financials` |
| 3 | Form3 | initial ownership |
| 4 | Form4 | `reporting_owners`, `market_trades`, `to_dataframe()` |
| 5 | Form5 | annual ownership changes |
| DEF 14A | ProxyStatement | `executive_compensation`, `voting_proposals`, `peo_name` |
| 13F-HR | ThirteenF | `infotable`, `total_value` |
| SC 13D | Schedule13D | `total_shares`, `items` |
| SC 13G | Schedule13G | `total_shares` |
| NPORT-P | FundReport | fund portfolio |
| 144 | Form144 | `units_to_be_sold`, `market_value`, `securities_to_be_sold` |
| N-PX | NPX | `proxy_votes` |
| Form D | FormD | `offering_data`, `related_persons` |
| Form C | FormC | `offering_information` |
| 10-D | TenD | `loans`, `properties`, `asset_data` |
| MA-I | MunicipalAdvisorForm | `applicant`, `filer` |

---

## How It Works

```python
from edgar import Company

apple = Company("AAPL")
filing = apple.latest("10-K")   # or apple.get_filings(form="10-K").latest()
tenk = filing.obj()          # returns TenK with all sections and financials
```

If a form type is not supported, `filing.obj()` returns `None` (or the filing's raw XBRL object when XBRL is present) — it does not raise. Always guard with `if obj is None`.

## Pattern for Unknown Form Types

```python
obj = filing.obj()
if obj is None:
    # Fallback to raw content
    text = filing.text()
    html = filing.html()
    xbrl = filing.xbrl()
```
