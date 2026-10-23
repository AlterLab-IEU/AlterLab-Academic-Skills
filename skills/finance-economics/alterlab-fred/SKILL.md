---
name: alterlab-fred
description: Retrieves FRED (Federal Reserve Economic Data) time series with no API key — 800,000+ series from 100+ sources (GDP, unemployment, inflation, interest rates, exchange rates, housing, state data) via FRED's public CSV download, with server-side transformations, frequency aggregation, ALFRED real-time vintages and site search; an optional free FRED_API_KEY adds the JSON API (filtered search, categories, releases, tags, GeoFRED maps). Use for macroeconomic analysis, financial research, policy studies, economic forecasting, fetching U.S. or international economic indicators by FRED series ID, and academic research requiring historical economic time series. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read WebFetch Bash(curl:*) Bash(python:*) Bash(uv run:*)
compatibility: No API key required. Series data, transformations, aggregation, ALFRED vintages and search come keyless from fred.stlouisfed.org and alfred.stlouisfed.org (scripts/fred_keyless.py, standard library only). An optional free FRED_API_KEY adds the JSON API (scripts/fred_query.py, with requests). Network access to those hosts.
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    credentials: "optional: FRED_API_KEY (adds the JSON API: filtered series search, full metadata, categories, releases, tags, sources, vintage-date lists, bulk release download and GeoFRED maps/shapes, up to 120 requests/minute)"
    last_updated: "2026-09-23"
---

# FRED Economic Data Access

## Overview

Access comprehensive economic data through FRED (Federal Reserve Economic Data), a database maintained by the Federal Reserve Bank of St. Louis containing over 800,000 economic time series from over 100 sources.

**Key capabilities (keyless):**
- Download any series' observations as CSV, with server-side transformations (percent change, log, ...) and frequency aggregation
- Data as first published on a given date (ALFRED vintages), to avoid look-ahead bias
- Find series IDs by keyword and tag via FRED's site search; read title, units and frequency
- Per-state series (e.g. state unemployment `CAUR`, `TXUR`) for regional comparisons and maps

**With the optional `FRED_API_KEY`:** filtered JSON search, categories, release calendars, tags,
sources, vintage-date lists, GeoFRED regional data and shapes, and bulk release download (API v2).

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

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-alpha-vantage`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

## Access: keyless first

Start keyless; reach for the JSON API only when the user needs something the right column lists
and has (or wants) a free key.

| Need | Keyless route (default) | With optional `FRED_API_KEY` |
|------|-------------------------|------------------------------|
| Values | `fred.stlouisfed.org/graph/fredgraph.csv?id=UNRATE&cosd=2024-01-01&coed=2024-12-01` | `series/observations` |
| Transformation | add `&transformation=pc1` (lin, chg, ch1, pch, pc1, pca, cch, cca, log) | `units=pc1` |
| Lower frequency | add `&fq=Monthly&fam=avg` (fam: avg, sum, eop) | `frequency=m&aggregation_method=avg` |
| As published on a date | `alfred.stlouisfed.org/graph/alfredgraph.csv?id=GDP&vintage_date=2020-01-30` | `realtime_start`/`realtime_end`, `get_vintage_dates` |
| Find a series ID | `fred.stlouisfed.org/searchresults/?st=consumer+price+index&t=monthly` | `series/search` + filters |
| Title, units, frequency | `fred.stlouisfed.org/series/CPIAUCSL` | `series` |
| State map | per-state series `{ST}UR` (50 states + `DCUR`), plotted with plotly `locationmode="USA-states"` or Census cartographic boundaries | GeoFRED `series/data` + `shapes/file` |
| Categories, releases, tags, sources | WebFetch the matching fred.stlouisfed.org pages | JSON endpoints below |

```bash
python scripts/fred_keyless.py obs GDPC1 --transformation pc1 --start 2023-01-01
python scripts/fred_keyless.py obs DGS10 --frequency m --aggregation avg --start 2024-01-01 --csv dgs10_monthly.csv
python scripts/fred_keyless.py obs GDP --vintage-date 2020-01-30 --start 2019-07-01   # 2019Q4 advance: 21734.266
python scripts/fred_keyless.py search "consumer price index" --tag monthly
python scripts/fred_keyless.py info CPIAUCSL
python scripts/fred_keyless.py states UR --date 2026-08-01
```

`fred_keyless.py` needs only the standard library (`observations()`, `observations_many()`,
`search()`, `series_info()` in Python). `pd.read_csv` also reads the CSV URLs directly. Missing
values come back as "." or blank. Fetching several IDs in one fredgraph URL returns a zip when
their frequencies differ, so request one ID per URL.

**Optional key.** For JSON-only endpoints, a free key comes from https://fredaccount.stlouisfed.org;
set `export FRED_API_KEY=...` and use `scripts/fred_query.py`. It raises a clear error naming the
variable and the keyless alternative when the key is missing.

## Quick Start

### JSON API client (optional key)

```python
from scripts.fred_query import FREDQuery

fred = FREDQuery()  # reads FRED_API_KEY; without it, use scripts/fred_keyless.py

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
gdp_growth = fred.get_observations("GDP", units="pc1")          # JSON API
gdp_growth = observations("GDP", transformation="pc1")          # keyless (fred_keyless)
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
monthly = observations("DGS10", frequency="m", aggregation="avg")  # keyless: fq=Monthly&fam=avg
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

# Keyless: the series as published on 2020-01-30 (ALFRED CSV, column GDP_20200130)
first_print = observations("GDP", vintage_date="2020-01-30", start="2019-10-01")
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

### `scripts/fred_keyless.py` (default, no key)

Standard-library client for the keyless routes in "Access: keyless first": `obs` (values,
transformations, aggregation, `--vintage-date`, `--csv`), `search`, `info`, `states`. Run with
plain `python`; exits non-zero with the HTTP status on an unknown series ID.

### `scripts/fred_query.py` (optional key)

JSON-API query module with `FREDQuery` class providing:
- Unified interface to the v1 FRED and GeoFRED (Maps API) endpoints
- In-memory response caching
- Retry with backoff on 429/5xx; FRED error messages surfaced for other failures
- Type hints and documentation

The community `fredapi` package (`uv run --python ">=3.11" --with fredapi ...`; `Fred(api_key=...).get_series("GDP")` returns a pandas Series; needs the key) is a lighter alternative for plain series pulls; it has had no release since 0.5.2 (2024-05).

### `scripts/fred_examples.py`

Examples; without `FRED_API_KEY` it runs the keyless ones and skips the JSON-API ones:
- Economic indicator retrieval
- Time series analysis
- Release calendar monitoring
- Regional data mapping
- Data transformation and aggregation

Run examples:
```bash
uv run --python ">=3.11" --with requests python scripts/fred_examples.py
```

## Additional Resources

- **FRED Homepage**: https://fred.stlouisfed.org/
- **API Documentation**: https://fred.stlouisfed.org/docs/api/fred/
- **GeoFRED Maps**: https://geofred.stlouisfed.org/
- **ALFRED (Vintage Data)**: https://alfred.stlouisfed.org/
- **Terms of Use**: https://fred.stlouisfed.org/legal/

Cite FRED (series ID, source agency, and retrieval date) for every series used in a paper.

Part of the AlterLab Academic Skills suite.
