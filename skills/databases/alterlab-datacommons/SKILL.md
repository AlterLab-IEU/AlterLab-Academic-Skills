---
name: alterlab-datacommons
description: Query Google Data Commons for public statistical data aggregated from global sources, resolving geographic entities and pulling time-series statistics. Use when working with demographic data, economic indicators, health statistics, or environmental data — population counts, GDP figures, unemployment rates, disease prevalence — or when resolving places to DCIDs and exploring relationships between statistical entities. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read WebFetch Bash(curl:*) Bash(python:*)
compatibility: Requires a Data Commons API key
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# Data Commons Client

## Overview

Provides comprehensive access to the Data Commons Python API v2 for querying statistical observations, exploring the knowledge graph, and resolving entity identifiers. Data Commons aggregates data from census bureaus, health organizations, environmental agencies, and other authoritative sources into a unified knowledge graph.

Verified against `datacommons-client` 2.x (the current major). This is the V2 client (package `datacommons_client`), not the legacy `datacommons` (V1) package — the two have different APIs; do not mix them.

## Installation

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

# Navigate hierarchy
children = client.node.fetch_place_children(
    node_dcids=["country/USA"]
)

# Get entity names
names = client.node.fetch_entity_names(
    node_dcids=["geoId/06", "geoId/48"]
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

# Resolve by coordinates
dcid = client.resolve.fetch_dcid_by_coordinates(
    latitude=37.7749,
    longitude=-122.4194
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
       names=["California", "Texas"]
   )
   dcids = [r["candidates"][0]["dcid"]
            for r in resolve_response.to_dict().values()
            if r["candidates"]]
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

   # As flat records (list of dataclasses: date, entity, variable, value + facet)
   records = response.to_observations_as_records()
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

If you already have a response object, flatten it with `to_observations_as_records()`
(note the method name) and wrap in a DataFrame:

```python
response = client.observation.fetch(
    variable_dcids=["Count_Person"],
    entity_dcids=["geoId/06", "geoId/48"],
    date="all",
)
df = pd.DataFrame(response.to_observations_as_records())
```

## API Authentication

**For datacommons.org (default):**
- An API key is required
- Set via environment variable: `export DC_API_KEY="your_key"`
- Or pass when initializing: `client = DataCommonsClient(api_key="your_key")`
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

`scripts/query_datacommons.py` — runnable helper for the Data Commons REST v2 API (needs a free key in `DC_API_KEY`):

```bash
python scripts/query_datacommons.py resolve "California" --type State
python scripts/query_datacommons.py observe Count_Person geoId/06 --date latest
```

