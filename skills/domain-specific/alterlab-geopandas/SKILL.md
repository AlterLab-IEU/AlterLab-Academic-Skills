---
name: alterlab-geopandas
description: Reads, writes, and analyzes geospatial vector data with the GeoPandas Python library (shapefiles, GeoJSON, GeoPackage), with PostGIS support and integration with matplotlib, folium, and cartopy. Use for spatial analysis and geometric operations — buffer analysis, spatial joins and overlays between datasets, dissolving boundaries, clipping, calculating areas and distances, reprojecting coordinate systems, choropleth mapping, or converting between vector file formats. This is for tabular vector data; for raster/satellite/DEM work, spectral indices (NDVI), or spatial ML on earth observation prefer the geomaster skill. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*)
compatibility: No API key required. Runs locally via `uv run python`; requires the geopandas Python package.
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# GeoPandas

GeoPandas extends pandas to enable spatial operations on geometric types. It combines the capabilities of pandas and shapely for geospatial data analysis.

## When to Use This Skill

Use this skill when the user wants to:
- Read, write, or convert vector data (Shapefile, GeoJSON, GeoPackage, GeoParquet, PostGIS)
- Run spatial joins, overlays, buffers, dissolves, clipping, or nearest-neighbour joins
- Reproject between coordinate reference systems and measure areas/lengths/distances correctly
- Make static or interactive (folium) choropleth maps from tabular vector data

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Raster, satellite imagery, DEMs, spectral indices, STAC/COG, or EO machine learning | `alterlab-geomaster` |
| Network/graph analysis of relationships with no geometry (centrality, communities) | `alterlab-networkx` |
| Genomic interval overlaps (BED files) — "spatial" joins along a chromosome | `alterlab-gtars` |
| Celestial coordinates, FITS/WCS sky positions | `alterlab-astropy` |

## Installation

```bash
uv pip install geopandas   # 1.x (current 1.1.x as of 2026-09); shapely 2 + pyogrio
```

GeoPandas 1.x requires shapely ≥ 2 and reads/writes through **pyogrio** by default
(fiona is optional). Removed or deprecated in the 1.x line: `sjoin(op=...)` (use
`predicate=`), `unary_union` (use `union_all()`), and the bundled `geopandas.datasets`
files (use the `geodatasets` package).

### Optional Dependencies

```bash
# For interactive maps
uv pip install folium

# For classification schemes in mapping
uv pip install mapclassify

# For faster I/O operations (2-4x speedup)
uv pip install pyarrow

# For PostGIS database support (SQLAlchemy engine + driver; geoalchemy2 for to_postgis)
uv pip install sqlalchemy "psycopg[binary]" geoalchemy2

# For basemaps
uv pip install contextily

# For cartographic projections
uv pip install cartopy
```

## Quick Start

```python
import geopandas as gpd

# Read spatial data
gdf = gpd.read_file("data.geojson")

# Basic exploration
print(gdf.head())
print(gdf.crs)
print(gdf.geometry.geom_type)

# Simple plot
gdf.plot()

# Reproject to a metric CRS suited to the data (local UTM zone)
gdf_projected = gdf.to_crs(gdf.estimate_utm_crs())

# Calculate area in m² (use an equal-area CRS such as EPSG:6933 for continental extents;
# never Web Mercator EPSG:3857 — it inflates areas ~4x at 60° latitude)
gdf_projected['area'] = gdf_projected.geometry.area

# Save to file
gdf.to_file("output.gpkg")
```

## Core Concepts

### Data Structures

- **GeoSeries**: Vector of geometries with spatial operations
- **GeoDataFrame**: Tabular data structure with geometry column

See [data-structures.md](references/data-structures.md) for details.

### Reading and Writing Data

GeoPandas reads/writes multiple formats: Shapefile, GeoJSON, GeoPackage, PostGIS, Parquet.

```python
# Read with filtering
gdf = gpd.read_file("data.gpkg", bbox=(xmin, ymin, xmax, ymax))

# Write with Arrow acceleration
gdf.to_file("output.gpkg", use_arrow=True)
```

See [data-io.md](references/data-io.md) for comprehensive I/O operations.

### Coordinate Reference Systems

Always check and manage CRS for accurate spatial operations:

```python
# Check CRS
print(gdf.crs)

# Reproject (transforms coordinates). EPSG:3857 (Web Mercator) is for web tiles only;
# measure in a local UTM (gdf.estimate_utm_crs()) or an equal-area CRS
gdf_projected = gdf.to_crs("EPSG:3857")

# Set CRS (only when metadata missing)
gdf = gdf.set_crs("EPSG:4326")
```

See [crs-management.md](references/crs-management.md) for CRS operations.

## Common Operations

### Geometric Operations

Buffer, simplify, centroid, convex hull, affine transformations:

```python
# Buffer by 10 units
buffered = gdf.geometry.buffer(10)

# Simplify with tolerance
simplified = gdf.geometry.simplify(tolerance=5, preserve_topology=True)

# Get centroids
centroids = gdf.geometry.centroid
```

See [geometric-operations.md](references/geometric-operations.md) for all operations.

### Spatial Analysis

Spatial joins, overlay operations, dissolve:

```python
# Spatial join (intersects)
joined = gpd.sjoin(gdf1, gdf2, predicate='intersects')

# Nearest neighbor join
nearest = gpd.sjoin_nearest(gdf1, gdf2, max_distance=1000)

# Overlay intersection
intersection = gpd.overlay(gdf1, gdf2, how='intersection')

# Dissolve by attribute
dissolved = gdf.dissolve(by='region', aggfunc='sum')
```

See [spatial-analysis.md](references/spatial-analysis.md) for analysis operations.

### Visualization

Create static and interactive maps:

```python
# Choropleth map
gdf.plot(column='population', cmap='YlOrRd', legend=True)

# Interactive map
gdf.explore(column='population', legend=True).save('map.html')

# Multi-layer map
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
gdf1.plot(ax=ax, color='blue')
gdf2.plot(ax=ax, color='red')
```

See [visualization.md](references/visualization.md) for mapping techniques.

## Detailed Documentation

- **[Data Structures](references/data-structures.md)** - GeoSeries and GeoDataFrame fundamentals
- **[Data I/O](references/data-io.md)** - Reading/writing files, PostGIS, Parquet
- **[Geometric Operations](references/geometric-operations.md)** - Buffer, simplify, affine transforms
- **[Spatial Analysis](references/spatial-analysis.md)** - Joins, overlay, dissolve, clipping
- **[Visualization](references/visualization.md)** - Plotting, choropleth maps, interactive maps
- **[CRS Management](references/crs-management.md)** - Coordinate reference systems and projections

## Common Workflows

### Load, Transform, Analyze, Export

```python
# 1. Load data
gdf = gpd.read_file("data.shp")

# 2. Check and transform CRS (metric, local UTM zone)
print(gdf.crs)
gdf = gdf.to_crs(gdf.estimate_utm_crs())

# 3. Perform analysis
gdf['area'] = gdf.geometry.area
buffered = gdf.copy()
buffered['geometry'] = gdf.geometry.buffer(100)

# 4. Export results
gdf.to_file("results.gpkg", layer='original')
buffered.to_file("results.gpkg", layer='buffered')
```

### Spatial Join and Aggregate

```python
# Join points to polygons
points_in_polygons = gpd.sjoin(points_gdf, polygons_gdf, predicate='within')

# Aggregate by polygon (named aggregation: total value and number of points)
aggregated = points_in_polygons.groupby('index_right').agg(
    value_sum=('value', 'sum'),
    n_points=('value', 'size'),
)

# Merge back to polygons
result = polygons_gdf.merge(aggregated, left_index=True, right_index=True)
```

### Multi-Source Data Integration

```python
# Read from different sources
roads = gpd.read_file("roads.shp")
buildings = gpd.read_file("buildings.geojson")
parcels = gpd.read_postgis("SELECT * FROM parcels", con=engine, geom_col='geom')

# Ensure matching CRS
buildings = buildings.to_crs(roads.crs)
parcels = parcels.to_crs(roads.crs)

# Perform spatial operations
buildings_near_roads = buildings[buildings.geometry.distance(roads.union_all()) < 50]
```

## Performance Tips

1. **Use spatial indexing**: GeoPandas creates spatial indexes automatically for most operations
2. **Filter during read**: Use `bbox`, `mask`, or `where` parameters to load only needed data
3. **Use Arrow for I/O**: Add `use_arrow=True` for 2-4x faster reading/writing
4. **Simplify geometries**: Use `.simplify()` to reduce complexity when precision isn't critical
5. **Batch operations**: Vectorized operations are much faster than iterating rows
6. **Use appropriate CRS**: Equal-area CRS for areas, local UTM for distances/buffers, geographic for storage

## Best Practices

1. **Always check CRS** before spatial operations
2. **Use a suitable projected CRS** for measurements — equal-area (e.g. EPSG:6933, or a regional Albers) for areas, `estimate_utm_crs()` for distances; never EPSG:3857
3. **Match CRS** before spatial joins or overlays
4. **Validate geometries** with `.is_valid` before operations
5. **Use `.copy()`** when modifying geometry columns to avoid side effects
6. **Preserve topology** when simplifying for analysis
7. **Use GeoPackage** format for modern workflows (better than Shapefile)
8. **Set max_distance** in sjoin_nearest for better performance

Part of the AlterLab Academic Skills suite.

