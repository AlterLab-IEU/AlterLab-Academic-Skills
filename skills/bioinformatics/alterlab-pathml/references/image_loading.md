# Image Loading & Formats

## Overview

PathML provides comprehensive support for loading whole-slide images (WSI) from 160+ proprietary medical imaging formats. The framework abstracts vendor-specific complexities through unified slide classes and interfaces, enabling seamless access to image pyramids, metadata, and regions of interest across different file formats.

## Supported Formats

PathML supports the following slide formats:

### Brightfield Microscopy Formats
- **Aperio SVS** (`.svs`) - Leica Biosystems
- **Hamamatsu NDPI** (`.ndpi`) - Hamamatsu Photonics
- **Leica SCN** (`.scn`) - Leica Biosystems
- **Zeiss ZVI** (`.zvi`) - Carl Zeiss
- **3DHISTECH** (`.mrxs`) - 3DHISTECH Ltd.
- **Ventana BIF** (`.bif`) - Roche Ventana
- **Generic tiled TIFF** (`.tif`, `.tiff`)

### Medical Imaging Standards
- **DICOM** (`.dcm`) - Digital Imaging and Communications in Medicine
- **OME-TIFF** (`.ome.tif`, `.ome.tiff`) - Open Microscopy Environment

### Multiparametric Imaging
- **CODEX** - Spatial proteomics imaging
- **Vectra** (`.qptiff`) - Multiplex immunofluorescence
- **MERFISH** - Multiplexed error-robust FISH

PathML leverages OpenSlide and other specialized libraries to handle format-specific nuances automatically.

## Core Classes for Loading Images

### SlideData

`SlideData` is the fundamental class for representing whole-slide images in PathML. You construct it directly (there is no `SlideData.from_slide` factory) or via a convenience subclass (`HESlide`, `VectraSlide`, `CODEXSlide`, `MultiparametricSlide`, `IHCSlide`).

**Loading from file:**
```python
from pathml.core import SlideData, HESlide, types

# Convenience subclass for H&E (recommended for brightfield H&E)
wsi = HESlide("path/to/slide.svs", name="example")

# Generic constructor. backend is a STRING ("openslide" | "bioformats" | "dicom");
# slide_type carries the stain/dimensionality (use a pathml.core.types instance).
wsi = SlideData("path/to/slide.svs", backend="openslide", slide_type=types.HE)

# OME-TIFF via the Bio-Formats backend
wsi = SlideData("path/to/slide.ome.tiff", backend="bioformats")
```

**Key attributes:**
- `wsi.slide` - Backend slide object (OpenSlide, BioFormats, etc.)
- `wsi.tiles` - Collection of image tiles (populated after a tiling/Pipeline run)
- `wsi.masks` - Slide-level masks
- `wsi.shape` - Image dimensions
- `wsi.name` - Slide name

**Methods:**
- `wsi.run(pipeline, ...)` - Run a preprocessing Pipeline (handles tiling + transforms)
- `wsi.generate_tiles()` - Generator over `Tile` objects
- `wsi.extract_region(location, size, ...)` - Read a specific region (delegates to the backend)
- `wsi.write(path)` - Write contents to disk in h5path format

### SlideType and types

`SlideType` describes a slide's stain/dimensionality (NOT the backend). The `pathml.core.types` module exposes pre-made instances you pass as `slide_type`:

```python
from pathml.core import types

types.HE       # H&E brightfield
types.IHC      # immunohistochemistry
types.IF       # immunofluorescence
types.CODEX    # CODEX multiplex IF
types.Vectra   # Vectra multiplex IF
```

The decoding backend is selected separately with the string `backend` argument (`"openslide"`, `"bioformats"`, or `"dicom"`).

### Specialized Slide Classes

PathML provides specialized slide classes for specific imaging modalities:

**CODEXSlide:**
```python
from pathml.core import CODEXSlide

# Load CODEX spatial proteomics data
codex_slide = CODEXSlide(
    path="path/to/codex_dir",
    stain="IF",  # Immunofluorescence
    backend="bioformats"
)
```

**VectraSlide:**
```python
from pathml.core import VectraSlide

# Load Vectra multiplex IF data (.qptiff); uses the Bio-Formats backend
vectra_slide = VectraSlide("path/to/vectra.qptiff")
```

**MultiparametricSlide:**
```python
from pathml.core import MultiparametricSlide

# Generic multiparametric imaging
mp_slide = MultiparametricSlide("path/to/multiparametric_data", backend="bioformats")
```

## Loading Strategies

### Tile-Based Loading

For large WSI files, tile-based loading enables memory-efficient processing. `generate_tiles` returns a generator over `Tile` objects; iterate it directly. To persist tiles on the slide, run a `Pipeline` (see `preprocessing.md`), after which they are available on `wsi.tiles`.

```python
from pathml.core import HESlide

# Load slide
wsi = HESlide("path/to/slide.svs")

# Iterate tiles lazily at a chosen level
for tile in wsi.generate_tiles(
    level=0,        # Pyramid level (0 = highest resolution)
    shape=256,      # Tile dimensions in pixels
    stride=256,     # Spacing between tiles (256 = no overlap)
    pad=False,      # Whether to pad edge tiles
):
    image = tile.image   # numpy array
    coords = tile.coords  # (i, j) coordinates
    # Process tile...
```

**Overlapping tiles:**
```python
# 50% overlap
for tile in wsi.generate_tiles(level=0, shape=256, stride=128):
    ...
```

Confirm the exact tiling keyword (`shape` vs `tile_size`) against your installed PathML version; it has differed across releases.

### Region-Based Loading

Extract specific regions of interest directly:

```python
# Read region at a specific location. extract_region delegates to the
# active backend (OpenSlide/Bio-Formats/DICOM); see your backend for the
# exact level/coordinate semantics.
region = wsi.extract_region(
    location=(10000, 15000),  # (x, y) coordinates
    size=(512, 512),          # width, height in pixels
)

# Returns a numpy array
```

### Pyramid Level Selection

Whole-slide images are stored in multi-resolution pyramids. Select the appropriate level based on desired magnification. Pyramid metadata lives on the backend object (`wsi.slide`); for OpenSlide it exposes `level_dimensions` and `level_downsamples`:

```python
# Inspect available levels via the OpenSlide backend
osh = wsi.slide.slide  # underlying openslide.OpenSlide handle
print(osh.level_dimensions)   # [(width0, height0), (width1, height1), ...]
print(osh.level_downsamples)  # [1.0, 4.0, 16.0, ...]

# Tile at a lower resolution for faster processing
for tile in wsi.generate_tiles(level=2, shape=256):  # level 2 (e.g. 16x downsampled)
    ...
```

**Common pyramid levels:**
- Level 0: Full resolution (e.g., 40x magnification)
- Level 1: 4x downsampled (e.g., 10x magnification)
- Level 2: 16x downsampled (e.g., 2.5x magnification)
- Level 3: 64x downsampled (thumbnail)

### Thumbnail Loading

Generate low-resolution thumbnails for visualization and quality control. PathML exposes `wsi.plot()` for a quick thumbnail view; for an array, pull one from the backend handle:

```python
import matplotlib.pyplot as plt

# Quick built-in thumbnail plot
wsi.plot()

# Or get an array via the OpenSlide backend handle
thumbnail = wsi.slide.slide.get_thumbnail((1024, 1024))
plt.imshow(thumbnail)
plt.axis("off")
plt.show()
```

## Batch Loading with SlideDataset

Process multiple slides efficiently using `SlideDataset`, which wraps a list of `SlideData` objects (not raw paths):

```python
from pathml.core import HESlide, SlideDataset
import glob

# Build slide objects, then a dataset
slide_paths = glob.glob("data/*.svs")
slides = [HESlide(p) for p in slide_paths]
dataset = SlideDataset(slides)

# Access individual slides
for slide in dataset.slides:
    print(slide.name)
```

**With preprocessing pipeline:**
```python
from pathml.preprocessing import Pipeline, StainNormalizationHE

pipeline = Pipeline([
    StainNormalizationHE(target="normalize"),
])

# Run across the dataset. PathML parallelizes with Dask via a client;
# pass a dask.distributed Client (see the distributed example below).
dataset.run(pipeline)
```

## Metadata Access

Extract slide metadata including acquisition parameters, magnification, and vendor-specific information. For OpenSlide-backed slides the vendor properties live on the backend handle:

```python
# OpenSlide properties dictionary
props = wsi.slide.slide.properties

print(props.get("openslide.objective-power"))  # Magnification
print(props.get("openslide.mpp-x"))            # Microns per pixel X
print(props.get("openslide.mpp-y"))            # Microns per pixel Y
print(props.get("openslide.vendor"))           # Scanner vendor

# Slide dimensions
print(wsi.shape)  # full-resolution dimensions
```

## Working with DICOM Slides

PathML supports DICOM WSI through specialized handling:

```python
from pathml.core import SlideData

# Load DICOM WSI (backend is the string "dicom")
dicom_slide = SlideData("path/to/slide.dcm", backend="dicom")
```

## Working with OME-TIFF

OME-TIFF provides an open standard for multi-dimensional imaging:

```python
from pathml.core import SlideData

# Load OME-TIFF via the Bio-Formats backend (requires a JDK / JVM)
ome_slide = SlideData("path/to/slide.ome.tiff", backend="bioformats")

# Inspect dimensions / channels
print(ome_slide.shape)
```

## Performance Considerations

### Memory Management

For large WSI files (often >1GB), use tile-based loading to avoid memory exhaustion:

```python
# Efficient: stream tiles one at a time
for tile in wsi.generate_tiles(level=1, shape=256):
    process_tile(tile)

# Inefficient: pulling the whole level-0 image into memory may crash
full_image = wsi.extract_region(location=(0, 0), size=wsi.shape)
```

### Distributed Processing

Use Dask for parallel processing across multiple workers:

```python
from pathml.core import HESlide, SlideDataset
from dask.distributed import Client

# Start a Dask client and pass it to run()
client = Client(n_workers=8, threads_per_worker=2)

dataset = SlideDataset([HESlide(p) for p in slide_paths])
dataset.run(pipeline, client=client)
```

### Level Selection

Balance resolution and performance by selecting appropriate pyramid levels:

- **Level 0:** Use for final analysis requiring maximum detail
- **Level 1-2:** Use for most preprocessing and model training
- **Level 3+:** Use for thumbnails, quality control, and rapid exploration

## Common Issues and Solutions

**Issue: Slide fails to load**
- Verify file format is supported
- Check file permissions and path
- Try different backend: `backend="bioformats"` or `backend="openslide"`

**Issue: Out of memory errors**
- Use tile-based loading instead of full-slide loading
- Process at lower pyramid level (e.g., level=1 or level=2)
- Reduce tile_size parameter
- Enable distributed processing with Dask

**Issue: Color inconsistencies across slides**
- Apply stain normalization preprocessing (see `preprocessing.md`)
- Check scanner metadata for calibration information
- Use `StainNormalizationHE` transform in preprocessing pipeline

**Issue: Metadata missing or incorrect**
- Different vendors store metadata in different locations
- Use `wsi.metadata` to inspect available fields
- Some formats may have limited metadata support

## Best Practices

1. **Always inspect pyramid structure** before processing: Check `level_dimensions` and `level_downsamples` to understand available resolutions

2. **Use appropriate pyramid levels**: Process at level 1-2 for most tasks; reserve level 0 for final high-resolution analysis

3. **Tile with overlap** for segmentation tasks: Use stride < tile_size to avoid edge artifacts

4. **Verify magnification consistency**: Check `openslide.objective-power` metadata when combining slides from different sources

5. **Handle vendor-specific formats**: Use specialized slide classes (CODEXSlide, VectraSlide) for multiparametric data

6. **Implement quality control**: Generate thumbnails and inspect for artifacts before processing

7. **Use distributed processing** for large datasets: Leverage Dask for parallel processing across multiple workers

## Example Workflows

### Loading and Inspecting a New Slide

```python
from pathml.core import HESlide

# Load slide
wsi = HESlide("path/to/slide.svs", name="example")

# Inspect properties
print(f"Shape: {wsi.shape}")
props = wsi.slide.slide.properties  # OpenSlide properties
print(f"Magnification: {props.get('openslide.objective-power')}")

# Quick thumbnail for QC
wsi.plot()
```

### Processing Multiple Slides

```python
from pathml.core import HESlide, SlideDataset
from pathml.preprocessing import Pipeline, TissueDetectionHE
from dask.distributed import Client
import glob

# Find all slides
slide_paths = glob.glob("data/slides/*.svs")

# Create pipeline
pipeline = Pipeline([TissueDetectionHE()])

# Build dataset from slide objects and run with a Dask client
dataset = SlideDataset([HESlide(p) for p in slide_paths])
client = Client(n_workers=8, threads_per_worker=2)
dataset.run(pipeline, client=client)

# Persist each processed slide to h5path
dataset.write("processed/")
```

### Loading CODEX Multiparametric Data

```python
from pathml.core import CODEXSlide
from pathml.preprocessing import Pipeline, CollapseRunsCODEX, SegmentMIF

# Load CODEX slide
codex = CODEXSlide("path/to/codex_dir", stain="IF")

# Create CODEX-specific pipeline. SegmentMIF channels are integer indices
# into the collapsed channel stack (see multiparametric.md).
pipeline = Pipeline([
    CollapseRunsCODEX(z=0),  # select z-plane
    SegmentMIF(
        model="mesmer",
        nuclear_channel=0,
        cytoplasm_channel=29,
    ),
])

codex.run(pipeline)
```

## Additional Resources

- **PathML Documentation:** https://pathml.readthedocs.io/
- **OpenSlide:** https://openslide.org/ (underlying library for WSI formats)
- **Bio-Formats:** https://www.openmicroscopy.org/bio-formats/ (alternative backend)
- **DICOM Standard:** https://www.dicomstandard.org/
