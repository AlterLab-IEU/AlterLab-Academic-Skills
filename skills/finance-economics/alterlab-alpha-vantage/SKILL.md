---
name: alterlab-alpha-vantage
description: Retrieves market and company data with no API key — daily OHLCV price history with splits and dividends (Yahoo Finance chart endpoint, unofficial), company fundamentals from SEC EDGAR XBRL (revenue, net income, EPS, shares), FX, crypto, commodity and macro series from FRED's public CSV — and computes technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands) locally; an optional ALPHAVANTAGE_API_KEY adds the Alpha Vantage REST API (news sentiment, earnings transcripts, options, server-side indicators). Use when fetching stock prices (OHLCV), company fundamentals (income statement, EPS, P/E, market cap), forex rates, Bitcoin/crypto prices, oil/gas/gold prices, CPI or treasury yields for finance research, calculating technical indicators, building news-sentiment event studies, or when the Alpha Vantage API is named. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write WebFetch WebSearch Bash(curl:*) Bash(python:*) Bash(uv run:*)
compatibility: No API key required. Prices come from Yahoo's unofficial chart endpoint, fundamentals from SEC EDGAR (a User-Agent with a contact email, no key), FX, crypto, commodity and macro series from FRED's public CSV, and indicators are computed locally (scripts/market_data.py, standard library only). An optional ALPHAVANTAGE_API_KEY adds Alpha Vantage's own endpoints.
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    credentials: "optional: ALPHAVANTAGE_API_KEY (adds Alpha Vantage's /query API: news sentiment, earnings-call transcripts, insider transactions, options, server-side technical indicators and its pre-computed fundamentals; free tier 25 requests/day, premium for intraday, outputsize=full and options)"
    last_updated: "2026-09-23"
---

# Alpha Vantage — Financial Market Data (keyless first)

Market and company data for research without any API key: 20+ years of daily prices with splits
and dividends, fundamentals from the companies' own SEC filings, FX, crypto, commodity and macro
series from FRED, and technical indicators computed locally from those prices. Alpha Vantage
itself has no keyless access (its `demo` key answers only the documented demo symbols, e.g.
`GLOBAL_QUOTE` for IBM; AAPL returns an "Information" refusal), so its REST API is the optional
extra described further down.

## When to Use This Skill

- Pulling OHLCV price history or a latest close for a ticker, FX pair, or crypto asset
- Company fundamentals for a teaching case or panel (revenue, net income, EPS, shares, P/E, market cap)
- Technical indicators (SMA, EMA, RSI, MACD, BBANDS) for a momentum or event study
- Commodity prices or headline US macro series (WTI, Brent, gas, CPI, yields)
- News sentiment for event studies, and any request that names the Alpha Vantage API

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Macro series by FRED ID (UNRATE, GDPC1), server-side `pc1` transforms, ALFRED vintages | `alterlab-fred` |
| Line items from the actual 10-K/10-Q, XBRL facts, Form 4/13F filings from SEC EDGAR | `alterlab-edgartools` |
| Treasury debt to the penny, Daily/Monthly Treasury Statements, auction results | `alterlab-usfiscaldata` |
| Aggregate hedge-fund leverage / SEC Form PF statistics | `alterlab-hedgefund-monitor` |
| Fitting ARIMA/regression models to the series you downloaded | `alterlab-statsmodels` |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-fred`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

## Keyless data routes (default)

| Need | Keyless source | Alpha Vantage equivalent (optional key) |
|------|----------------|------------------------------------------|
| Daily/weekly/monthly OHLCV, 20+ years | Yahoo chart `query1.finance.yahoo.com/v8/finance/chart/AAPL?period1=<epoch>&interval=1d&events=div,split` | `TIME_SERIES_DAILY(_ADJUSTED)` |
| Splits and dividends | same response, `events.splits` / `events.dividends` | `SPLITS`, `DIVIDENDS` |
| SMA, EMA, RSI, MACD, BBANDS | computed locally from the prices (`market_data.py rsi` / `indicators`) | `SMA`, `EMA`, `RSI`, `MACD`*, `BBANDS` |
| Revenue, net income, EPS, shares | SEC EDGAR `data.sec.gov/api/xbrl/companyfacts/CIK##########.json` | `INCOME_STATEMENT`, `EARNINGS`, `OVERVIEW` |
| P/E, market cap | latest close ÷ diluted EPS (say which: last fiscal year, or TTM from four 10-Qs); shares outstanding (dei) × close | `OVERVIEW` `PERatio`, `MarketCapitalization` |
| FX | FRED `DEXUSEU` (USD per EUR), `DEXJPUS`, `DEXUSUK`; Yahoo `EURUSD=X` | `FX_DAILY`, `CURRENCY_EXCHANGE_RATE` |
| Crypto | FRED `CBBTCUSD` (Coinbase BTC-USD); Yahoo `BTC-USD` | `DIGITAL_CURRENCY_DAILY` |
| Commodities | FRED `DCOILWTICO` (WTI), `DCOILBRENTEU` (Brent), `DHHNGSP` (Henry Hub gas); Yahoo `GC=F` (gold futures) | `WTI`, `BRENT`, `NATURAL_GAS`, `GOLD_SILVER_*` |
| Macro (CPI, GDP, yields) | FRED CSV `CPIAUCSL`, `GDPC1`, `DGS10` (`alterlab-fred` has the full keyless toolkit) | `CPI`, `REAL_GDP`, `TREASURY_YIELD` |
| News sentiment | WebSearch/WebFetch the headlines (and the company's 8-Ks), then score each article yourself with a stated rubric (e.g. -1/0/+1, with the quote that justifies it) and label the scores as your own coding | `NEWS_SENTIMENT` |
| Insider trades | SEC Form 4 (`alterlab-edgartools`) | `INSIDER_TRANSACTIONS` |
| Options chains, call transcripts | no verified keyless source; say so and offer the optional key | `HISTORICAL_OPTIONS`*, `EARNINGS_CALL_TRANSCRIPT` |

```bash
python scripts/market_data.py prices AAPL --start 2000-01-01 --csv aapl.csv      # + splits, dividends on stderr
python scripts/market_data.py rsi AAPL --period 14 --start 2024-01-01             # Wilder RSI on adjclose
python scripts/market_data.py indicators SPY --start 2025-01-01 --csv spy_ta.csv  # SMA/EMA20, RSI14, MACD, BB(20,2)
python scripts/market_data.py fundamentals MSFT --years 3 --user-agent "Your Name you@university.edu"
python scripts/market_data.py fred DCOILWTICO --frequency m --aggregation avg --start 2015-01-01
```

`market_data.py` needs only the Python standard library; in Python, import `prices`, `rsi`,
`sma`, `ema`, `macd`, `bbands`, `fundamentals`, `fred` from it.

**Disclose the sources.** Yahoo's chart endpoint is unofficial and undocumented: no SLA, it can
change or rate-limit without notice, and Yahoo's terms allow personal use, so say so in the
answer, keep request rates low, and for a publication cross-check prices against a licensed
source (CRSP/WRDS, the exchange). Yahoo's `close` is already split-adjusted and `adjclose` is
split- and dividend-adjusted. Use `adjclose` for returns and indicators; raw historical prints =
`close` × the product of all later split ratios. SEC EDGAR asks for a User-Agent with a contact
email (`--user-agent` or `EDGAR_IDENTITY`) and at most 10 requests/second; its XBRL facts are the
reported 10-K/10-Q values (cite form and accession number). FRED series are cited by series ID.

## Optional: the Alpha Vantage API (`ALPHAVANTAGE_API_KEY`)

Use it when the user asks for Alpha Vantage by name or needs what only it offers here (news
sentiment scores, transcripts, options). Get a free key at
https://www.alphavantage.co/support/#api-key (premium plans raise limits and unlock the starred
functions) and `export ALPHAVANTAGE_API_KEY=...`. `python scripts/market_data.py av FUNCTION
key=value ...` calls it and exits with an error naming the variable and the keyless subcommands
when the key is missing. If an Alpha Vantage MCP connector is configured (official server:
https://mcp.alphavantage.co/), prefer it. Run your own code with
`uv run --python ">=3.11" --with requests --with pandas python script.py` (no install step).

## Base URL & Request Pattern

All requests go to:

```
https://www.alphavantage.co/query?function=FUNCTION_NAME&apikey=YOUR_KEY&...params
```

```python
import os
import requests

API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"

def av_get(function, **params):
    response = requests.get(BASE_URL, params={"function": function, "apikey": API_KEY, **params}, timeout=30)
    response.raise_for_status()
    data = response.json()
    # Alpha Vantage reports errors and limit hits with HTTP 200 + one of these keys
    for key in ("Error Message", "Information", "Note"):
        if key in data:
            raise RuntimeError(f"Alpha Vantage {key}: {data[key]}")
    return data
```

## Quick Start Examples

```python
# Stock quote (latest price; end-of-day unless you have a realtime entitlement)
quote = av_get("GLOBAL_QUOTE", symbol="AAPL")
price = quote["Global Quote"]["05. price"]

# Daily OHLCV: compact = latest 100 points (free); outputsize="full" (25+ years) is premium-only
daily = av_get("TIME_SERIES_DAILY", symbol="AAPL", outputsize="compact")
ts = daily["Time Series (Daily)"]

# Company fundamentals
overview = av_get("OVERVIEW", symbol="AAPL")
print(overview["MarketCapitalization"], overview["PERatio"])

# Income statement
income = av_get("INCOME_STATEMENT", symbol="AAPL")
annual = income["annualReports"][0]  # Most recent annual

# Crypto price
crypto = av_get("DIGITAL_CURRENCY_DAILY", symbol="BTC", market="USD")

# Economic indicator
gdp = av_get("REAL_GDP", interval="annual")

# Technical indicator
rsi = av_get("RSI", symbol="AAPL", interval="daily", time_period=14, series_type="close")
```

## API Categories

| Category | Key Functions |
|----------|--------------|
| **Time Series (Stocks)** | GLOBAL_QUOTE, TIME_SERIES_INTRADAY*, TIME_SERIES_DAILY, TIME_SERIES_DAILY_ADJUSTED*, TIME_SERIES_WEEKLY(_ADJUSTED), TIME_SERIES_MONTHLY(_ADJUSTED), REALTIME_BULK_QUOTES*, MARKET_STATUS, SYMBOL_SEARCH |
| **Index Data** | INDEX_DATA*, INDEX_CATALOG* |
| **Options** | REALTIME_OPTIONS*, HISTORICAL_OPTIONS* (plus put-call and volume/OI ratio endpoints) |
| **Alpha Intelligence** | NEWS_SENTIMENT, EARNINGS_CALL_TRANSCRIPT, TOP_GAINERS_LOSERS, INSIDER_TRANSACTIONS, INSTITUTIONAL_HOLDINGS, ANALYTICS_FIXED_WINDOW, ANALYTICS_SLIDING_WINDOW |
| **Fundamentals** | OVERVIEW, ETF_PROFILE, INCOME_STATEMENT, BALANCE_SHEET, CASH_FLOW, SHARES_OUTSTANDING, EARNINGS, EARNINGS_ESTIMATES, DIVIDENDS, SPLITS, LISTING_STATUS, EARNINGS_CALENDAR, IPO_CALENDAR |
| **Forex (FX)** | CURRENCY_EXCHANGE_RATE, FX_INTRADAY*, FX_DAILY, FX_WEEKLY, FX_MONTHLY |
| **Crypto** | CURRENCY_EXCHANGE_RATE, CRYPTO_INTRADAY*, DIGITAL_CURRENCY_DAILY/WEEKLY/MONTHLY |
| **Commodities** | WTI, BRENT, NATURAL_GAS, COPPER, ALUMINUM, WHEAT, CORN, COTTON, SUGAR, COFFEE, GOLD_SILVER_SPOT, GOLD_SILVER_HISTORY, ALL_COMMODITIES |
| **Economic Indicators** | REAL_GDP, REAL_GDP_PER_CAPITA, TREASURY_YIELD, FEDERAL_FUNDS_RATE, CPI, INFLATION, RETAIL_SALES, DURABLES, UNEMPLOYMENT, NONFARM_PAYROLL |
| **Technical Indicators** | SMA, EMA, MACD*, RSI, BBANDS, STOCH, ADX, ATR, OBV, VWAP*, and 40+ more |

\* Premium-only (per the live documentation, checked 2026-09-23). Premium-gated parameters on free functions: `outputsize=full` on TIME_SERIES_DAILY, and `entitlement=realtime|delayed` on quotes.

## Common Parameters

| Parameter | Values | Notes |
|-----------|--------|-------|
| `outputsize` | `compact` / `full` | compact = last 100 points; full = 20+ years (premium for TIME_SERIES_DAILY) |
| `datatype` | `json` / `csv` | Default: json |
| `interval` | `1min`, `5min`, `15min`, `30min`, `60min`, `daily`, `weekly`, `monthly` | Depends on endpoint |
| `adjusted` | `true` / `false` | Adjust for splits/dividends |
| `entitlement` | `realtime` / `delayed` | Premium; omit for historical/end-of-day data |

## Rate Limits and Tiers

- **Free key: 25 requests/day.** Plan the calls before looping over symbols — a 30-ticker panel exhausts the daily quota. Cache responses to disk and reuse them.
- Premium plans are sold by requests per minute (75 to 1,200/min) and unlock the starred functions above.
- Limit hits and errors arrive as **HTTP 200** with an `Information` (older responses: `Note`) or `Error Message` key instead of data, so check the JSON body rather than the status code; the `av_get` helper above raises on them.

## Error Handling

```python
try:
    data = av_get("GLOBAL_QUOTE", symbol="AAPL")
except RuntimeError as err:
    # "Information" usually means the daily quota is used up or the call needs a premium key;
    # "Error Message" usually means a bad function/parameter/symbol.
    print(err)
```

## Reference Files

Load these for detailed endpoint documentation:

- **[time-series.md](references/time-series.md)** — Stock OHLCV data, quotes, bulk quotes, market status
- **[fundamentals.md](references/fundamentals.md)** — Company overview, financial statements, earnings, dividends, splits
- **[options.md](references/options.md)** — Realtime and historical options chain data
- **[intelligence.md](references/intelligence.md)** — News/sentiment, earnings transcripts, insider transactions, analytics
- **[forex-crypto.md](references/forex-crypto.md)** — Forex exchange rates and cryptocurrency prices
- **[commodities.md](references/commodities.md)** — Gold, silver, oil, natural gas, agricultural commodities
- **[economic-indicators.md](references/economic-indicators.md)** — GDP, CPI, interest rates, employment data
- **[technical-indicators.md](references/technical-indicators.md)** — 50+ technical analysis indicators (SMA, EMA, MACD, RSI, etc.)

The reference files document the optional Alpha Vantage API. Cite the actual source (Yahoo
Finance chart data, SEC EDGAR filing and accession, FRED series ID, or Alpha Vantage) and the
retrieval date for any figure used in a paper or report.

Part of the AlterLab Academic Skills suite.
