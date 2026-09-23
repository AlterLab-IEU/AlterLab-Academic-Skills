---
name: alterlab-fred
description: Queries the FRED (Federal Reserve Economic Data) API for 800,000+ economic time series from 100+ sources, covering GDP, unemployment, inflation, interest rates, exchange rates, housing, and regional data. Use for macroeconomic analysis, financial research, policy studies, economic forecasting, fetching U.S. or international economic indicators by FRED series ID, and academic research requiring historical economic time series. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read WebFetch Bash(curl:*) Bash(python:*)
compatibility: Requires a free FRED_API_KEY from a FRED account (fredaccount.stlouisfed.org) and network access to the FRED API (up to 120 requests/minute per key). Bundled scripts need requests; pandas for DataFrame examples.
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# FRED Economic Data Access

## Overview

Access comprehensive economic data through FRED (Federal Reserve Economic Data), a database maintained by the Federal Reserve Bank of St. Louis containing over 800,000 economic time series from over 100 sources.

**Key capabilities:**
- Query economic time series data (GDP, unemployment, inflation, interest rates)
- Search and discover series by keywords, tags, and categories
- Access historical data and vintage (revision) data via ALFRED
- Retrieve release schedules and data publication dates
- Map regional economic data with GeoFRED
- Apply data transformations (percent change, log, etc.)
- Bulk-download every series in a release (API v2)

## When to Use This Skill

- Fetching U.S. or international macro/financial series by FRED series ID (GDPC1, UNRATE, CPIAUCSL, DGS10, ...)
- Server-side transformations (`pc1`, `pch`, `log`) or frequency aggregation before analysis
- Real-time (vintage) data from ALFRED to avoid look-ahead bias in forecasting studies
- Release calendars, series discovery by keyword/tag/category, and state/county data for maps

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Stock/ETF prices, OHLCV bars, or technical indicators (RSI, MACD) | `alterlab-alpha-vantage` |
| Debt to the Penny, Daily/Monthly Treasury Statements, or auction results from the Treasury | `alterlab-usfiscaldata` |
| Company-level financial statements from SEC filings | `alterlab-edgartools` |
| Place-resolved public statistics (demographics, health, non-FRED global indicators) | `alterlab-datacommons` |
| Econometric modelling (ARIMA, VAR, regressions) of series you already downloaded | `alterlab-statsmodels` |

## API Key Setup

**Required:** All FRED API requests require an API key.

1. Create an account at https://fredaccount.stlouisfed.org
2. Log in and request an API key through the account portal
3. Set as environment variable:

```bash
export FRED_API_KEY="your_32_character_key_here"
```

Or in Python:
```python
import os
os.environ["FRED_API_KEY"] = "your_key_here"
```

## Quick Start

### Using the FREDQuery Class

```python
from scripts.fred_query import FREDQuery

# Initialize with API key
fred = FREDQuery(api_key="YOUR_KEY")  # or uses FRED_API_KEY env var

# get_series returns METADATA (title, units, frequency) under "seriess".
# For the actual data values, use get_observations (returns "observations").
meta = fred.get_series("GDP")
print(meta["seriess"][0]["title"])  # "Gross Domestic Product"

# Get the latest GDP value
gdp = fred.get_observations("GDP", limit=1, sort_order="desc")
print(f"Latest GDP: {gdp['observations'][0]}")

# Get unemployment rate observations
unemployment = fred.get_observations("UNRATE", limit=12)
for obs in unemployment["observations"]:
    print(f"{obs['date']}: {obs['value']}%")

# Search for inflation series
inflation_series = fred.search_series("consumer price index")
for s in inflation_series["seriess"][:5]:
    print(f"{s['id']}: {s['title']}")
```

### Direct API Calls

```python
import requests
import os

API_KEY = os.environ.get("FRED_API_KEY")
BASE_URL = "https://api.stlouisfed.org/fred"

# Get series observations
response = requests.get(
    f"{BASE_URL}/series/observations",
    params={
        "api_key": API_KEY,
        "series_id": "GDP",
        "file_type": "json"
    }
)
data = response.json()
```

## Popular Economic Series

| Series ID | Description | Frequency |
|-----------|-------------|-----------|
| GDP | Gross Domestic Product | Quarterly |
| GDPC1 | Real Gross Domestic Product | Quarterly |
| UNRATE | Unemployment Rate | Monthly |
| CPIAUCSL | Consumer Price Index (All Urban) | Monthly |
| FEDFUNDS | Federal Funds Effective Rate | Monthly |
| DGS10 | 10-Year Treasury Constant Maturity | Daily |
| HOUST | Housing Starts | Monthly |
| PAYEMS | Total Nonfarm Payrolls | Monthly |
| INDPRO | Industrial Production Index | Monthly |
| M2SL | M2 Money Stock | Monthly |
| UMCSENT | Consumer Sentiment | Monthly |
| SP500 | S&P 500 | Daily |

## API Endpoint Categories

### Series Endpoints

Get economic data series metadata and observations.

**Key endpoints:**
- `fred/series` - Get series metadata
- `fred/series/observations` - Get data values (most commonly used)
- `fred/series/search` - Search for series by keywords
- `fred/series/updates` - Get recently updated series

```python
# Get observations with transformations
obs = fred.get_observations(
    series_id="GDP",
    units="pch",  # percent change
    frequency="q",  # quarterly
    observation_start="2020-01-01"
)

# Search with filters
results = fred.search_series(
    "unemployment",
    filter_variable="frequency",
    filter_value="Monthly"
)
```

**Reference:** See `references/series.md` for all 10 series endpoints

### Categories Endpoints

Navigate the hierarchical organization of economic data.

**Key endpoints:**
- `fred/category` - Get a category
- `fred/category/children` - Get subcategories
- `fred/category/series` - Get series in a category

```python
# Get root categories (category_id=0)
root = fred.get_category()

# Get Money Banking & Finance category and its series
category = fred.get_category(32991)
series = fred.get_category_series(32991)
```

**Reference:** See `references/categories.md` for all 6 category endpoints

### Releases Endpoints

Access data release schedules and publication information.

**Key endpoints:**
- `fred/releases` - Get all releases
- `fred/releases/dates` - Get upcoming release dates
- `fred/release/series` - Get series in a release

```python
# Get upcoming release dates
upcoming = fred.get_release_dates()

# Get GDP release info
gdp_release = fred.get_release(53)
```

**Reference:** See `references/releases.md` for all 9 release endpoints

### Tags Endpoints

Discover and filter series using FRED tags.

```python
# Find series with multiple tags
series = fred.get_series_by_tags(["gdp", "quarterly", "usa"])

# Get related tags
related = fred.get_related_tags("inflation")
```

**Reference:** See `references/tags.md` for all 3 tag endpoints

### Sources Endpoints

Get information about data sources (BLS, BEA, Census, etc.).

```python
# Get all sources
sources = fred.get_sources()

# Get Federal Reserve releases
fed_releases = fred.get_source_releases(source_id=1)
```

**Reference:** See `references/sources.md` for all 3 source endpoints

### GeoFRED Endpoints

Access geographic/regional economic data for mapping.

```python
# Get state unemployment data
regional = fred.get_regional_data(
    series_group="1220",  # Unemployment rate
    region_type="state",
    date="2023-01-01",
    units="Percent",
    season="NSA"
)

# Get GeoJSON shapes
shapes = fred.get_shapes("state")
```

**Reference:** See `references/geofred.md` for all 4 GeoFRED endpoints

### Bulk Release Download (API v2)

FRED API v2 has one endpoint, `fred/v2/release/observations`, which returns every series in a release (all history) in one paginated call. Unlike v1 it takes the key in a header:

```python
import os
import requests

url = "https://api.stlouisfed.org/fred/v2/release/observations"
headers = {"Authorization": f"Bearer {os.environ['FRED_API_KEY']}"}
params = {"release_id": 53, "limit": 500000}  # 53 = GDP release; limit max 500,000 observations
series = []
while True:
    page = requests.get(url, headers=headers, params=params, timeout=120).json()
    series.extend(page["series"])  # each series carries its observations
    if not page.get("has_more"):
        break
    params["next_cursor"] = page["next_cursor"]  # omit on the first request
```

## Data Transformations

Apply transformations when fetching observations:

| Value | Description |
|-------|-------------|
| `lin` | Levels (no transformation) |
| `chg` | Change from previous period |
| `ch1` | Change from year ago |
| `pch` | Percent change from previous period |
| `pc1` | Percent change from year ago |
| `pca` | Compounded annual rate of change |
| `cch` | Continuously compounded rate of change |
| `cca` | Continuously compounded annual rate of change |
| `log` | Natural log |

```python
# Get GDP percent change from year ago
gdp_growth = fred.get_observations("GDP", units="pc1")
```

## Frequency Aggregation

Aggregate data to different frequencies:

| Code | Frequency |
|------|-----------|
| `d` | Daily |
| `w` | Weekly |
| `m` | Monthly |
| `q` | Quarterly |
| `a` | Annual |

Aggregation methods: `avg` (average), `sum`, `eop` (end of period)

```python
# Convert daily to monthly average
monthly = fred.get_observations(
    "DGS10",
    frequency="m",
    aggregation_method="avg"
)
```

## Real-Time (Vintage) Data

Access historical vintages of data via ALFRED:

```python
# Get GDP as it was reported on a specific date
vintage_gdp = fred.get_observations(
    "GDP",
    realtime_start="2020-01-01",
    realtime_end="2020-01-01"
)

# Get all vintage dates for a series
vintages = fred.get_vintage_dates("GDP")
```

## Common Patterns

### Pattern 1: Economic Dashboard

```python
def get_economic_snapshot(fred):
    """Get current values of key indicators."""
    indicators = ["GDP", "UNRATE", "CPIAUCSL", "FEDFUNDS", "DGS10"]
    snapshot = {}

    for series_id in indicators:
        obs = fred.get_observations(series_id, limit=1, sort_order="desc")
        if obs.get("observations"):
            latest = obs["observations"][0]
            snapshot[series_id] = {
                "value": latest["value"],
                "date": latest["date"]
            }

    return snapshot
```

### Pattern 2: Time Series Comparison

```python
def compare_series(fred, series_ids, start_date):
    """Compare multiple series over time."""
    import pandas as pd

    data = {}
    for sid in series_ids:
        obs = fred.get_observations(
            sid,
            observation_start=start_date,
            units="pc1"  # Normalize as percent change
        )
        data[sid] = {
            o["date"]: float(o["value"])
            for o in obs["observations"]
            if o["value"] != "."
        }

    return pd.DataFrame(data)
```

### Pattern 3: Release Calendar

```python
def get_upcoming_releases(fred, days=7):
    """Get data releases in next N days."""
    from datetime import datetime, timedelta

    end_date = datetime.now() + timedelta(days=days)

    releases = fred.get_release_dates(
        realtime_start=datetime.now().strftime("%Y-%m-%d"),
        realtime_end=end_date.strftime("%Y-%m-%d"),
        include_release_dates_with_no_data="true"
    )

    return releases
```

### Pattern 4: Regional Analysis

```python
def map_state_unemployment(fred, date):
    """Get unemployment by state for mapping."""
    data = fred.get_regional_data(
        series_group="1220",
        region_type="state",
        date=date,
        units="Percent",
        frequency="a",
        season="NSA"
    )

    # Get GeoJSON for mapping
    shapes = fred.get_shapes("state")

    return data, shapes
```

## Error Handling

```python
result = fred.get_observations("INVALID_SERIES")

if "error" in result:
    print(f"Error {result['error']['code']}: {result['error']['message']}")
elif not result.get("observations"):
    print("No data available")
else:
    # Process data
    for obs in result["observations"]:
        if obs["value"] != ".":  # Handle missing values
            print(f"{obs['date']}: {obs['value']}")
```

## Rate Limits

- FRED allows up to **120 requests per minute** per key; beyond that it returns HTTP 429, and ignoring the throttling can get the key temporarily blocked.
- Cache repeated queries (FREDQuery keeps an in-memory cache, default TTL 1 hour) and prefer one v2 release download over hundreds of per-series calls.
- FREDQuery retries 429/5xx responses with exponential backoff and returns other errors immediately as `{"error": {"code": ..., "message": ...}}` (FRED's own `error_code`/`error_message`).

## Reference Documentation

For detailed endpoint documentation:
- **Series endpoints** - See `references/series.md`
- **Categories endpoints** - See `references/categories.md`
- **Releases endpoints** - See `references/releases.md`
- **Tags endpoints** - See `references/tags.md`
- **Sources endpoints** - See `references/sources.md`
- **GeoFRED endpoints** - See `references/geofred.md`
- **API basics** - See `references/api_basics.md`

## Scripts

### `scripts/fred_query.py`

Main query module with `FREDQuery` class providing:
- Unified interface to the v1 FRED and GeoFRED (Maps API) endpoints
- In-memory response caching
- Retry with backoff on 429/5xx; FRED error messages surfaced for other failures
- Type hints and documentation

The community `fredapi` package (`uv pip install fredapi`; `Fred(api_key=...).get_series("GDP")` returns a pandas Series) is a lighter alternative for plain series pulls; it has had no release since 0.5.2 (2024-05).

### `scripts/fred_examples.py`

Comprehensive examples demonstrating:
- Economic indicator retrieval
- Time series analysis
- Release calendar monitoring
- Regional data mapping
- Data transformation and aggregation

Run examples:
```bash
uv run python scripts/fred_examples.py
```

## Additional Resources

- **FRED Homepage**: https://fred.stlouisfed.org/
- **API Documentation**: https://fred.stlouisfed.org/docs/api/fred/
- **GeoFRED Maps**: https://geofred.stlouisfed.org/
- **ALFRED (Vintage Data)**: https://alfred.stlouisfed.org/
- **Terms of Use**: https://fred.stlouisfed.org/legal/

Cite FRED (series ID, source agency, and retrieval date) for every series used in a paper.

Part of the AlterLab Academic Skills suite.
