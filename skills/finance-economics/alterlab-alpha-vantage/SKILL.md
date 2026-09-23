---
name: alterlab-alpha-vantage
description: Accesses stock market data, forex rates, cryptocurrency prices, commodities, economic indicators, company fundamentals, news sentiment, and 50+ technical indicators via the Alpha Vantage REST API (free API key from alphavantage.co; realtime/intraday data and full daily history need a premium key). Use when fetching stock prices (OHLCV), company fundamentals (income statement, balance sheet, cash flow), earnings, options data, market news/sentiment, insider transactions, GDP, CPI, treasury yields, gold/silver/oil prices, Bitcoin/crypto prices, forex exchange rates, or calculating technical indicators (SMA, EMA, MACD, RSI, Bollinger Bands). Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read WebFetch Bash(curl:*) Bash(python:*)
compatibility: Requires a free ALPHAVANTAGE_API_KEY from alphavantage.co and network access. The free tier allows 25 requests/day and excludes intraday, realtime, adjusted, outputsize=full daily history, options, VWAP/MACD and index data, which need a premium plan.
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# Alpha Vantage — Financial Market Data

Access 20+ years of global financial data: equities, options, forex, crypto, commodities, economic indicators, fundamentals, news sentiment, and 50+ technical indicators — all from one `/query` endpoint.

## When to Use This Skill

- Pulling OHLCV price history or a latest quote for a ticker, FX pair, or crypto asset
- Fetching pre-computed company fundamentals (overview ratios, statements, earnings, dividends, splits)
- Computing technical indicators server-side (SMA, EMA, RSI, BBANDS, ...)
- Retrieving commodity prices or headline US macro series (GDP, CPI, yields, unemployment)
- News-sentiment, earnings-call transcripts, or insider transactions for event studies

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Macro series by FRED ID (UNRATE, GDPC1), server-side `pc1` transforms, ALFRED vintages | `alterlab-fred` |
| Line items from the actual 10-K/10-Q, XBRL facts, Form 4/13F filings from SEC EDGAR | `alterlab-edgartools` |
| Treasury debt to the penny, Daily/Monthly Treasury Statements, auction results | `alterlab-usfiscaldata` |
| Aggregate hedge-fund leverage / SEC Form PF statistics | `alterlab-hedgefund-monitor` |
| Fitting ARIMA/regression models to the series you downloaded | `alterlab-statsmodels` |

## API Key Setup (Required)

1. Get a free key at https://www.alphavantage.co/support/#api-key (premium plans raise limits and unlock premium endpoints)
2. Set as environment variable:

```bash
export ALPHAVANTAGE_API_KEY="your_key_here"
```

If an Alpha Vantage MCP connector is configured (Alpha Vantage runs an official MCP server, see https://mcp.alphavantage.co/), prefer it for live lookups; the REST patterns below work everywhere.

## Installation

```bash
uv pip install requests pandas
```

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

Cite Alpha Vantage and the retrieval date for any figure used in a paper or report.

Part of the AlterLab Academic Skills suite.
