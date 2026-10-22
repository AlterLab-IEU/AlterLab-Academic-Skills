---
name: alterlab-datacommons
description: Query Google Data Commons for public statistical data aggregated from global sources, resolving geographic entities and pulling time-series statistics. Use when working with demographic data, economic indicators, health statistics, or environmental data — population counts, GDP figures, unemployment rates, disease prevalence — or when resolving places to DCIDs and exploring relationships between statistical entities. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read WebFetch Bash(curl:*) Bash(python:*)
compatibility: No API key required. Statistics come keyless from the JSON API behind the datacommons.org website (undocumented; provenance kept per record) and names/Wikidata IDs resolve through the keyless v2 resolve endpoint (scripts/query_datacommons.py, standard library only). An optional DC_API_KEY unlocks the documented api.datacommons.org v2 observation/node endpoints and datacommons-client >= 2.1 (current 2.1.6).
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    last_updated: "2026-10-22"
    credentials: "optional: DC_API_KEY (unlocks the documented api.datacommons.org v2 observation/node endpoints and the datacommons-client methods that use them; the keyless website API serves the same statistics)"
---

# Data Commons Client

## Overview

Data Commons aggregates data from census bureaus, health organizations, environmental agencies, and other authoritative sources into a unified knowledge graph. This skill answers statistical questions from it **without an API key**: `scripts/query_datacommons.py` reads observations from the JSON API that the datacommons.org website itself uses, and resolves names and Wikidata IDs through the keyless v2 resolve endpoint. The documented Python client (`datacommons-client`, below) is the optional keyed path — its observation and node methods return HTTP 401 without `DC_API_KEY`.

The keyed client is verified against `datacommons-client` 2.1.6 (current as of 2026-09; Python ≥ 3.10). This is the V2 client (package `datacommons_client`), not the legacy `datacommons` (V1) package — the two have different APIs; do not mix them. Keyword names matter: the place-hierarchy helpers take `place_dcids`, `fetch_entity_names` takes `entity_dcids`, and `fetch_property_values` takes `properties` — passing `node_dcids` to them raises `TypeError`.

## When to Use This Skill

- Pulling population, economic, health, education, or environmental statistics for places (countries, states, counties, cities)
- Building cross-place or time-series comparisons from harmonized public sources (census, BLS, WHO, World Bank, EPA, …)
- Resolving place names, coordinates, or Wikidata IDs to Data Commons DCIDs
- Exploring the Data Commons knowledge graph (place hierarchies, properties, statistical-variable definitions)

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| A specific FRED economic series (GDP, CPI, interest rates) with vintage/revision data | `alterlab-fred` |
| U.S. Treasury fiscal data (debt, spending, revenue) | `alterlab-usfiscaldata` |
| NCI Imaging Data Commons (CT/MR/pathology images) — a different "Data Commons" | `alterlab-imaging-data-commons` |
| Spatial joins, buffers, or mapping of geometries | `alterlab-geopandas` |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-fred`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

## Keyless Path (default)

No key, no install (standard library only). Verified live 2026-10-22:

```bash
S=scripts/query_datacommons.py
python $S resolve California Texas --type State        # {"California": ["geoId/06"], ...}
python $S resolve --wikidata Q30 Q99                   # Q30 -> country/USA, Q99 -> geoId/06
python $S resolve --coords 37.7749,-122.4194           # -> geoId/06, geoId/06075, geoId/0667000
python $S observe Count_Person country/TUR --date 2020 # 83384680 (World Bank WDI)
python $S observe Count_Person geoId/06 geoId/48 --date all --csv > pop.csv   # full series
python $S within Median_Income_Household geoId/06 County --date 2020 --names  # all 58 counties
python $S vars-search "unemployment rate" --place country/USA
python $S has UnemploymentRate_Person Count_Person --entity country/USA
```

Every observation comes back as a tidy record — `variable, entity, date, value` plus the
facet's `provenanceId`, `provenanceUrl`, `measurementMethod`, `unit` — so it loads straight
into pandas (`pd.read_csv("pop.csv")`, then `pivot_table(index="date", columns="entity")`).

| Need | Keyless endpoint (GET unless noted) |
|------|-------------------------------------|
| Latest / one date | `https://datacommons.org/api/observations/point?entities=…&variables=…[&date=2020]` |
| Full time series (the client's `date="all"`) | `…/api/observations/series?entities=…&variables=…` |
| Every child of a place in one call (the client's `containedInPlace` expression) | `…/api/observations/point/within?parentEntity=geoId/06&childType=County&variables=…&date=2020` (or `series/within`) |
| Names, parents, descendants | `…/api/place/name?dcids=…`, `…/api/place/parent?dcid=…`, `…/api/place/descendent?dcids=…&descendentType=County` |
| Find / check variables | `…/api/stats/stat-var-search?query=…&places=…`; POST `…/api/observation/existence` `{"entities":[…],"variables":[…]}` |
| Name / Wikidata → DCID | POST `https://api.datacommons.org/v2/resolve` `{"nodes":[…],"property":"<-description{typeOf:State}->dcid"}` (or `<-wikidataId->dcid`) |

Know the limits of this route and say so in the answer:
- **Undocumented website API.** It serves the site's own charts (source: `github.com/datacommonsorg/website`, `server/routes/`), is not part of the documented REST API, and can change without notice. Cite the record's `provenanceUrl` and the retrieval date; robots.txt does not disallow it, but keep request rates modest.
- **One facet per series.** The website picks the preferred source per place/variable; the keyed `observation.fetch` can return every facet (`filter_facet_domains`).
- **Dates must match the period.** Monthly series (e.g. `UnemploymentRate_Person`, BLS) need `YYYY-MM`; `--date 2020` returns nothing for them — use `latest` or `all`.
- **Coordinates.** v2 resolve returned no candidates for coordinates keylessly (2026-10-22), so the script falls back to the keyless US Census geocoder (GEOID → `geoId/<GEOID>`) for US points and to OpenStreetMap Nominatim → Wikidata → resolve elsewhere (≤ 1 request/s).

`--backend api` forces the documented v2 API; without `DC_API_KEY` it exits with an error naming the key and the keyless default instead of answering from another source. With the key set and no `--backend`, `observe`/`within` use the v2 API.

## Optional Keyed Path: `datacommons-client` (needs DC_API_KEY)

The sections from here to "Working with Pandas" describe the documented Python client. Its
`resolve` methods work keyless; `observation` and `node` methods need `DC_API_KEY` (free at
https://apikeys.datacommons.org/). Use it when the user has a key or needs every facet.

Install the Data Commons V2 client with Pandas support (extra is lowercase `pandas`):

```bash
uv pip install "datacommons-client[pandas]"
```

For basic usage without Pandas:
```bash
uv pip install datacommons-client
```

## Core Capabilities

The Data Commons API consists of three main endpoints, each detailed in dedicated reference files:

### 1. Observation Endpoint - Statistical Data Queries

Query time-series statistical data for entities. See `references/observation.md` for comprehensive documentation.

**Primary use cases:**
- Retrieve population, economic, health, or environmental statistics
- Access historical time-series data for trend analysis
- Query data for hierarchies (all counties in a state, all countries in a region)
- Compare statistics across multiple entities
- Filter by data source for consistency

**Common patterns:**
```python
from datacommons_client import DataCommonsClient

client = DataCommonsClient()

# Get latest population data
response = client.observation.fetch(
    variable_dcids=["Count_Person"],
    entity_dcids=["geoId/06"],  # California
    date="latest"
)

# Get time series
response = client.observation.fetch(
    variable_dcids=["UnemploymentRate_Person"],
    entity_dcids=["country/USA"],
    date="all"
)

# Query by hierarchy
response = client.observation.fetch(
    variable_dcids=["Median_Income_Household"],
    entity_expression="geoId/06<-containedInPlace+{typeOf:County}",
    date="2020"
)
```

### 2. Node Endpoint - Knowledge Graph Exploration

Explore entity relationships and properties within the knowledge graph. See `references/node.md` for comprehensive documentation.

**Primary use cases:**
- Discover available properties for entities
- Navigate geographic hierarchies (parent/child relationships)
- Retrieve entity names and metadata
- Explore connections between entities
- List all entity types in the graph

**Common patterns:**
```python
# Discover properties
labels = client.node.fetch_property_labels(
    node_dcids=["geoId/06"],
    out=True
)

# Navigate hierarchy (dict: DCID -> list of {"dcid", "name", "types"})
children = client.node.fetch_place_children(
    place_dcids="country/USA",
    children_type="State",
)

# Get entity names (dict: DCID -> Name(value=..., language=...))
names = client.node.fetch_entity_names(
    entity_dcids=["geoId/06", "geoId/48"]
)
```

### 3. Resolve Endpoint - Entity Identification

Translate entity names, coordinates, or external IDs into Data Commons IDs (DCIDs). See `references/resolve.md` for comprehensive documentation.

**Primary use cases:**
- Convert place names to DCIDs for queries
- Resolve coordinates to places
- Map Wikidata IDs to Data Commons entities
- Handle ambiguous entity names

**Common patterns:**
```python
# Resolve by name
response = client.resolve.fetch_dcids_by_name(
    names=["California", "Texas"],
    entity_type="State"
)

# Resolve by coordinates (returns a ResolveResponse, not a bare DCID)
coord_response = client.resolve.fetch_dcid_by_coordinates(
    latitude="37.7749",
    longitude="-122.4194"
)

# Resolve Wikidata IDs
response = client.resolve.fetch_dcids_by_wikidata_id(
    wikidata_ids=["Q30", "Q99"]
)
```

## Typical Workflow

Most Data Commons queries follow this pattern:

1. **Resolve entities** (if starting with names):
   ```python
   resolve_response = client.resolve.fetch_dcids_by_name(
       names=["California", "Texas"], entity_type="State"
   )
   # to_dict() -> {"entities": [{"node": "California", "candidates": [{"dcid": ...}]}, ...]}
   dcids = [e["candidates"][0]["dcid"]
            for e in resolve_response.to_dict()["entities"]
            if e.get("candidates")]
   # or: resolve_response.to_flat_dict() -> {"California": "geoId/06", ...}
   #     (a list of DCIDs when the name is ambiguous)
   ```

2. **Discover available variables** (optional):
   ```python
   variables = client.observation.fetch_available_statistical_variables(
       entity_dcids=dcids
   )
   ```

3. **Query statistical data**:
   ```python
   response = client.observation.fetch(
       variable_dcids=["Count_Person", "UnemploymentRate_Person"],
       entity_dcids=dcids,
       date="latest"
   )
   ```

4. **Process results**:
   ```python
   # As dictionary
   data = response.to_dict()

   # As flat records (date, entity, variable, value + facet metadata).
   # to_observation_records() returns a pydantic model — dump it before
   # building a DataFrame, or the columns come out as 0..N.
   records = response.to_observation_records().model_dump()
   df = pd.DataFrame(records)
   ```

   To skip the manual conversion, the client also exposes a dedicated DataFrame
   accessor that runs the same query and returns a tidy DataFrame directly:
   ```python
   df = client.observations_dataframe(
       variable_dcids=["Count_Person"],
       entity_dcids=["geoId/06", "geoId/48"],
       date="all",
   )
   ```

## Finding Statistical Variables

Statistical variables use specific naming patterns in Data Commons:

**Common variable patterns:**
- `Count_Person` - Total population
- `Count_Person_Female` - Female population
- `UnemploymentRate_Person` - Unemployment rate
- `Median_Income_Household` - Median household income
- `Count_Death` - Death count
- `Median_Age_Person` - Median age

**Discovery methods:**
```python
# Check what variables are available for an entity
available = client.observation.fetch_available_statistical_variables(
    entity_dcids=["geoId/06"]
)

# Or explore via the web interface
# https://datacommons.org/tools/statvar
```

## Working with Pandas

The idiomatic path is the client's `observations_dataframe()` accessor, which mirrors
`observation.fetch()` arguments but returns a tidy DataFrame in one call (requires the
`pandas` extra):

```python
df = client.observations_dataframe(
    variable_dcids=["Count_Person"],
    entity_dcids=["geoId/06", "geoId/48"],
    date="all",
)
# Columns: date, entity, variable, value (plus facet/provenance columns)

# Reshape for analysis
pivot = df.pivot_table(
    values='value',
    index='date',
    columns='entity'
)
```

For every entity of a type under a parent place, pass `entity_dcids="all"` with
`entity_type` and `parent_entity`:

```python
df = client.observations_dataframe(
    variable_dcids=["Median_Income_Household"],
    date="latest",
    entity_dcids="all",
    entity_type="County",
    parent_entity="geoId/06",
)
```

If you already have a response object, flatten it with `to_observation_records()`
(singular "observation"; there is no `to_observations_as_records`) and dump it:

```python
response = client.observation.fetch(
    variable_dcids=["Count_Person"],
    entity_dcids=["geoId/06", "geoId/48"],
    date="all",
)
df = pd.DataFrame(response.to_observation_records().model_dump())
```

## API Authentication (keyed path only)

**For api.datacommons.org (the documented API):**
- Observation and node calls without a key return HTTP 401 `UNAUTHENTICATED`; name and
  Wikidata resolution answer without one. Everything statistical is also served keyless
  by the website API (see "Keyless Path")
- Optional key: `export DC_API_KEY="your_key"` or `DataCommonsClient(api_key="your_key")`
- Request keys at: https://apikeys.datacommons.org/

**For custom Data Commons instances:**
- No API key required
- Specify custom endpoint: `client = DataCommonsClient(url="https://custom.datacommons.org")`

## Reference Documentation

Comprehensive documentation for each endpoint is available in the `references/` directory:

- **`references/observation.md`**: Complete Observation API documentation with all methods, parameters, response formats, and common use cases
- **`references/node.md`**: Complete Node API documentation for graph exploration, property queries, and hierarchy navigation
- **`references/resolve.md`**: Complete Resolve API documentation for entity identification and DCID resolution
- **`references/getting_started.md`**: Quickstart guide with end-to-end examples and common patterns

## Additional Resources

- **Official Documentation**: https://docs.datacommons.org/api/python/v2/
- **Statistical Variable Explorer**: https://datacommons.org/tools/statvar
- **Data Commons Browser**: https://datacommons.org/browser/
- **GitHub Repository**: https://github.com/datacommonsorg/api-python

## Tips for Effective Use

1. **Always start with resolution**: Convert names to DCIDs before querying data
2. **Use relation expressions for hierarchies**: Query all children at once instead of individual queries
3. **Check data availability first**: Use `fetch_available_statistical_variables()` to see what's queryable
4. **Leverage Pandas integration**: Convert responses to DataFrames for analysis
5. **Cache resolutions**: If querying the same entities repeatedly, store name→DCID mappings
6. **Filter by facet for consistency**: Use `filter_facet_domains` to ensure data from the same source
7. **Read reference docs**: Each endpoint has extensive documentation in the `references/` directory

## Scripts

`scripts/query_datacommons.py` — keyless helper (standard library only): `resolve`
(names, `--wikidata`, `--coords`), `observe`, `within`, `names`, `parents`, `children`,
`vars-search`, `has`; `--csv` for tidy records; `--backend api` for the keyed v2 API.
Examples are under "Keyless Path".

