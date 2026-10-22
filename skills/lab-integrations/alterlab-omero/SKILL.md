---
name: alterlab-omero
description: Works with microscopy image data via the OMERO Python API (BlitzGateway) — writes and validates the integration code, analyses local OME-TIFF/microscopy pixels, ROIs and channels with tifffile offline, and browses or pulls from public OMERO servers (the IDR JSON API, webgateway and OME-Zarr) with no credentials. Connecting to the user's own OMERO server to read, write or batch-process their images is an optional step with their host, port and login. Use when writing OMERO/BlitzGateway code, analysing microscopy pixels or ROIs, pulling images or datasets, managing annotations, or running high-content screening and microscopy workflows. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(uv:*) Bash(python:*) Bash(curl:*)
compatibility: "No API key required to write the BlitzGateway integration, analyse local microscopy images with tifffile, and browse/pull public OMERO data (IDR JSON API + webgateway + OME-Zarr). Optional: the user's own OMERO server host/port and login for omero-py (current 5.23.0; Python >=3.10, needs the ZeroC Ice 3.6 bindings) to reach their private images."
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-10-22"
    credentials: "optional: OMERO_USER, OMERO_PASSWORD, OMERO_HOST, OMERO_PORT (the user's own OMERO server login — adds reading, writing and batch-processing images on their private tenant; the public IDR server needs none)"
---

# OMERO Integration

## Overview

OMERO is an open-source platform for managing, visualizing, and analyzing microscopy images and metadata. This skill's core job needs no credentials: it writes and checks the BlitzGateway integration code, analyses microscopy pixels/ROIs/channels from local files, and reads public OMERO data over HTTP. Only reaching the user's own private server uses their login.

## Keyless Path (default — no OMERO account)

1. **Write and check the BlitzGateway integration.** Author the code against omero-py's documented API (hierarchy `Project -> Dataset -> Image`, screening `Screen -> Plate -> Well -> WellSample -> Image`; `conn.getObject`, `image.getPrimaryPixels().getPlane(z, c, t)` -> NumPy, ROI shapes, `omero.gateway.BlitzGateway` as a context manager). omero-py pins `zeroc-ice>=3.6.5,<3.7`, whose wheels are scarce, so verify method names from the docs rather than assuming an import works.
2. **Analyse microscopy images locally.** OME-TIFF and most vendor formats read with `tifffile` (or Bio-Formats via `bioio`/`python-bioformats`) into a NumPy array with no server — compute per-channel intensity statistics, extract an ROI by coordinates and measure it, inspect dimensions and channel names. This is the same pixel analysis the BlitzGateway code will do on the server, proven on a local file first:

```python
import numpy as np, tifffile
arr = tifffile.imread("field.ome.tif")          # e.g. (c, y, x)
roi = arr[:, 20:40, 30:50]                        # a rectangular ROI by coordinates
for c in range(arr.shape[0]):
    print(f"channel {c}: whole mean {arr[c].mean():.1f}, ROI mean {roi[c].mean():.1f}")
```

3. **Browse and pull public OMERO data keyless.** The public Image Data Resource (IDR, `idr.openmicroscopy.org`) serves its OMERO over HTTP with no login (verified 2026-10-22):
   - JSON API `https://idr.openmicroscopy.org/api/v0/m/{projects,datasets,images,plates,rois}/` and `.../images/<id>/` return the hierarchy, pixel sizes and channel names.
   - `webgateway/imgData/<id>/` and `webgateway/render_thumbnail/<id>/` give image metadata and a thumbnail.
   - Pixel data for IDR images is read from their public **OME-Zarr** over HTTPS with `zarr`/`fsspec` — no server session.
4. **Hand over the private-server step.** Give the `BlitzGateway(user, password, host=..., port=4064)` code and the install note (prebuilt ZeroC Ice 3.6 wheel first, then `omero-py`); it runs only against the user's own server with their login. If `OMERO_USER`/`OMERO_PASSWORD` are not set, stop at the validated code and the local/public analysis — never invent server contents.

Microscopy data can be unpublished or regulated; follow your institution's data-handling rules before exporting pixels or metadata off a private server.

## When to Use This Skill

This skill should be used when:
- Working with OMERO Python API (omero-py) to access microscopy data
- Retrieving images, datasets, projects, or screening data programmatically
- Analyzing pixel data and creating derived images
- Creating or managing ROIs (regions of interest) on microscopy images
- Adding annotations, tags, or metadata to OMERO objects
- Storing measurement results in OMERO tables
- Creating server-side scripts for batch processing
- Performing high-content screening analysis

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Downloading public cancer radiology/pathology DICOM from NCI Imaging Data Commons | `alterlab-imaging-data-commons` |
| Tiling or preprocessing whole-slide images from local files | `alterlab-histolab` |
| End-to-end computational pathology models (segmentation, graphs, training) | `alterlab-pathml` |
| Reading or anonymizing clinical DICOM files | `alterlab-pydicom` |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-imaging-data-commons`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

## Core Capabilities

This skill covers eight major capability areas. Each is documented in detail in the references/ directory:

### 1. Connection & Session Management
**File**: `references/connection.md`

Establish secure connections to OMERO servers, manage sessions, handle authentication, and work with group contexts. Use this for initial setup and connection patterns.

**Common scenarios:**
- Connect to OMERO server with credentials
- Use existing session IDs
- Switch between group contexts
- Manage connection lifecycle with context managers

### 2. Data Access & Retrieval
**File**: `references/data_access.md`

Navigate OMERO's hierarchical data structure (Projects → Datasets → Images) and screening data (Screens → Plates → Wells). Retrieve objects, query by attributes, and access metadata.

**Common scenarios:**
- List all projects and datasets for a user
- Retrieve images by ID or dataset
- Access screening plate data
- Query objects with filters

### 3. Metadata & Annotations
**File**: `references/metadata.md`

Create and manage annotations including tags, key-value pairs, file attachments, and comments. Link annotations to images, datasets, or other objects.

**Common scenarios:**
- Add tags to images
- Attach analysis results as files
- Create custom key-value metadata
- Query annotations by namespace

### 4. Image Processing & Rendering
**File**: `references/image_processing.md`

Access raw pixel data as NumPy arrays, manipulate rendering settings, create derived images, and manage physical dimensions.

**Common scenarios:**
- Extract pixel data for computational analysis
- Generate thumbnail images
- Create maximum intensity projections
- Modify channel rendering settings

### 5. Regions of Interest (ROIs)
**File**: `references/rois.md`

Create, retrieve, and analyze ROIs with various shapes (rectangles, ellipses, polygons, masks, points, lines). Extract intensity statistics from ROI regions.

**Common scenarios:**
- Draw rectangular ROIs on images
- Create polygon masks for segmentation
- Analyze pixel intensities within ROIs
- Export ROI coordinates

### 6. OMERO Tables
**File**: `references/tables.md`

Store and query structured tabular data associated with OMERO objects. Useful for analysis results, measurements, and metadata.

**Common scenarios:**
- Store quantitative measurements for images
- Create tables with multiple column types
- Query table data with conditions
- Link tables to specific images or datasets

### 7. Scripts & Batch Operations
**File**: `references/scripts.md`

Create OMERO.scripts that run server-side for batch processing, automated workflows, and integration with OMERO clients.

**Common scenarios:**
- Process multiple images in batch
- Create automated analysis pipelines
- Generate summary statistics across datasets
- Export data in custom formats

### 8. Advanced Features
**File**: `references/advanced.md`

Covers permissions, filesets, cross-group queries, delete operations, and other advanced functionality.

**Common scenarios:**
- Handle group permissions
- Access original imported files
- Perform cross-group queries
- Delete objects with callbacks

## Installation

```bash
# 1. Install a prebuilt ZeroC Ice 3.6 wheel for your Python version and OS first
#    (Glencoe Software builds; links on the OMERO.py page below)
uv pip install /path/to/zeroc_ice-3.6.5-<python>-<platform>.whl
# 2. Then OMERO.py
uv pip install omero-py
```

**Requirements (omero-py 5.23.x, current as of 2026-09):**
- Python 3.10+ and NumPy 2
- ZeroC Ice: omero-py pins `zeroc-ice>=3.6.5,<3.7`. PyPI only has 3.6.5 wheels for Python 2.7/3.7, so without a prebuilt wheel pip tries to compile Ice from source; Ice 3.7/3.8 are not supported. See https://omero.readthedocs.io/en/stable/developers/Python.html for the wheel list.
- Access to an OMERO server (host, port, credentials) is needed only to reach a private server; the keyless path above covers code authoring, local analysis and public IDR data. Set `OMERODIR` if you use the `omero` CLI

## Quick Start

Basic connection pattern:

```python
from omero.gateway import BlitzGateway

# Connect to OMERO server
conn = BlitzGateway(username, password, host=host, port=port)
connected = conn.connect()

if connected:
    # Perform operations
    for project in conn.listProjects():
        print(project.getName())

    # Always close connection
    conn.close()
else:
    print("Connection failed")
```

**Recommended pattern with context manager:**

```python
from omero.gateway import BlitzGateway

with BlitzGateway(username, password, host=host, port=port) as conn:
    # Connection automatically managed
    for project in conn.listProjects():
        print(project.getName())
    # Automatically closed on exit
```

## Selecting the Right Capability

**For data exploration:**
- Start with `references/connection.md` to establish connection
- Use `references/data_access.md` to navigate hierarchy
- Check `references/metadata.md` for annotation details

**For image analysis:**
- Use `references/image_processing.md` for pixel data access
- Use `references/rois.md` for region-based analysis
- Use `references/tables.md` to store results

**For automation:**
- Use `references/scripts.md` for server-side processing
- Use `references/data_access.md` for batch data retrieval

**For advanced operations:**
- Use `references/advanced.md` for permissions and deletion
- Check `references/connection.md` for cross-group queries

## Common Workflows

### Workflow 1: Retrieve and Analyze Images

1. Connect to OMERO server (`references/connection.md`)
2. Navigate to dataset (`references/data_access.md`)
3. Retrieve images from dataset (`references/data_access.md`)
4. Access pixel data as NumPy array (`references/image_processing.md`)
5. Perform analysis
6. Store results as table or file annotation (`references/tables.md` or `references/metadata.md`)

### Workflow 2: Batch ROI Analysis

1. Connect to OMERO server
2. Retrieve images with existing ROIs (`references/rois.md`)
3. For each image, get ROI shapes
4. Extract pixel intensities within ROIs (`references/rois.md`)
5. Store measurements in OMERO table (`references/tables.md`)

### Workflow 3: Create Analysis Script

1. Design analysis workflow
2. Use OMERO.scripts framework (`references/scripts.md`)
3. Access data through script parameters
4. Process images in batch
5. Generate outputs (new images, tables, files)

## Error Handling

Always wrap OMERO operations in try-except blocks and ensure connections are properly closed:

```python
from omero.gateway import BlitzGateway
import traceback

conn = None  # bind first so the finally block is safe if the constructor raises
try:
    conn = BlitzGateway(username, password, host=host, port=port)
    if not conn.connect():
        raise Exception("Connection failed")

    # Perform operations

except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
finally:
    if conn:
        conn.close()
```

## Additional Resources

- **Official Documentation**: https://omero.readthedocs.io/en/stable/developers/Python.html
- **BlitzGateway API**: https://omero.readthedocs.io/en/stable/developers/Python.html#omero-blitzgateway
- **OMERO Model**: https://omero.readthedocs.io/en/stable/developers/Model.html
- **Community Forum**: https://forum.image.sc/tag/omero

## Notes

- OMERO uses group-based permissions (READ-ONLY, READ-ANNOTATE, READ-WRITE)
- Images in OMERO are organized hierarchically: Project > Dataset > Image
- Screening data uses: Screen > Plate > Well > WellSample > Image
- Always close connections to free server resources
- Use context managers for automatic resource management
- Pixel data is returned as NumPy arrays for analysis

Part of the AlterLab Academic Skills suite.
