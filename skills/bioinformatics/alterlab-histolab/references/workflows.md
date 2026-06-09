# Histolab Worked Workflows

End-to-end, copy-pasteable pipelines for histolab 0.7.0. Each is self-contained.

API reminders used throughout (verified against histolab 0.7.0):
- `n_tiles`, `seed`, `level`, `tile_size`, `check_tissue`, `tissue_percent` are
  **constructor** args. `locate_tiles()`/`extract()` take only `slide`, an
  optional `extraction_mask`, and logging/styling kwargs — no `n_tiles`.
- `Compose` lives in `histolab.filters.image_filters`, not `.compositions`.
- `TissueMask`/`BiggestTissueBoxMask` take custom filters as positional varargs,
  e.g. `TissueMask(RgbToGrayscale(), OtsuThreshold(), ...)` — not `filters=`.
- There is no `slide.save_thumbnail()`; use `slide.thumbnail.save(path)`.
- The `ScoreTiler` report CSV has columns `filename, score, scaled_score`.

## Quick Start

Basic workflow for extracting tiles from a whole slide image:

```python
from histolab.slide import Slide
from histolab.tiler import RandomTiler

# Load slide
slide = Slide("slide.svs", processed_path="output/")

# Configure tiler
tiler = RandomTiler(
    tile_size=(512, 512),
    n_tiles=100,
    level=0,
    seed=42
)

# Preview tile locations
tiler.locate_tiles(slide)

# Extract tiles
tiler.extract(slide)
```

## Slide management example

```python
from histolab.slide import Slide
from histolab.data import prostate_tissue

# Load sample data (returns an OpenSlide object and a path)
prostate_svs, prostate_path = prostate_tissue()

# Initialize slide
slide = Slide(prostate_path, processed_path="output/")

# Inspect properties
print(f"Dimensions: {slide.dimensions}")          # (width, height) at level 0
print(f"Levels: {slide.levels}")                  # list of available levels
print(f"Microns/pixel: {slide.base_mpp}")
print(f"Magnification: {slide.properties.get('openslide.objective-power')}")

# Save thumbnail (thumbnail is a PIL image; there is no save_thumbnail method)
slide.thumbnail.save("output/thumbnail.png")
```

## Tissue mask example

```python
from histolab.masks import TissueMask, BiggestTissueBoxMask

# Create tissue mask for all tissue regions
tissue_mask = TissueMask()

# Visualize mask on slide
slide.locate_mask(tissue_mask)

# Get mask array
mask_array = tissue_mask(slide)

# Use largest tissue region (default for most extractors)
biggest_mask = BiggestTissueBoxMask()
```

When to use each mask:
- `TissueMask`: Multiple tissue sections, comprehensive analysis
- `BiggestTissueBoxMask`: Single main tissue section, exclude artifacts (default)
- Custom `BinaryMask`: Specific ROI, exclude annotations, custom segmentation

## Tile extraction — three strategies

```python
from histolab.tiler import RandomTiler, GridTiler, ScoreTiler
from histolab.scorer import NucleiScorer

# Random sampling (fast, diverse)
random_tiler = RandomTiler(
    tile_size=(512, 512),
    n_tiles=100,
    level=0,
    seed=42,
    check_tissue=True,
    tissue_percent=80.0
)
random_tiler.extract(slide)

# Grid coverage (comprehensive)
grid_tiler = GridTiler(
    tile_size=(512, 512),
    level=0,
    pixel_overlap=0,
    check_tissue=True
)
grid_tiler.extract(slide)

# Score-based selection (most informative)
score_tiler = ScoreTiler(
    tile_size=(512, 512),
    n_tiles=50,
    scorer=NucleiScorer(),
    level=0
)
score_tiler.extract(slide, report_path="tiles_report.csv")
```

Always preview before extracting:

```python
# Preview tile locations on thumbnail (no n_tiles arg — set it on the tiler)
tiler.locate_tiles(slide)
```

## Filters / preprocessing example

```python
from histolab.filters.image_filters import RgbToGrayscale, OtsuThreshold, Compose
from histolab.filters.morphological_filters import (
    BinaryDilation, RemoveSmallHoles, RemoveSmallObjects
)

# Standard tissue detection pipeline (Compose takes a list of filters)
tissue_detection = Compose([
    RgbToGrayscale(),
    OtsuThreshold(),
    BinaryDilation(disk_size=5),
    RemoveSmallHoles(area_threshold=1000),
    RemoveSmallObjects(min_size=500)
])

# Use as a custom mask: TissueMask takes individual filters as *args, not a
# Compose object and not a filters= kwarg.
from histolab.masks import TissueMask
custom_mask = TissueMask(
    RgbToGrayscale(),
    OtsuThreshold(),
    BinaryDilation(disk_size=5),
    RemoveSmallHoles(area_threshold=1000),
    RemoveSmallObjects(min_size=500),
)

# Apply a composed filter to a tile
from histolab.tile import Tile
filtered_tile = tile.apply_filters(tissue_detection)
```

## Visualization example

```python
import matplotlib.pyplot as plt
from histolab.masks import TissueMask

# Display slide thumbnail
plt.figure(figsize=(10, 10))
plt.imshow(slide.thumbnail)
plt.title(f"Slide: {slide.name}")
plt.axis('off')
plt.show()

# Visualize tissue mask
tissue_mask = TissueMask()
slide.locate_mask(tissue_mask)

# Preview tile locations (n_tiles is set on the tiler, not on locate_tiles)
tiler = RandomTiler(tile_size=(512, 512), n_tiles=50)
tiler.locate_tiles(slide)

# Display extracted tiles in grid
from pathlib import Path
from PIL import Image

tile_paths = list(Path("output/tiles/").glob("*.png"))[:16]
fig, axes = plt.subplots(4, 4, figsize=(12, 12))
axes = axes.ravel()

for idx, tile_path in enumerate(tile_paths):
    tile_img = Image.open(tile_path)
    axes[idx].imshow(tile_img)
    axes[idx].set_title(tile_path.stem, fontsize=8)
    axes[idx].axis('off')

plt.tight_layout()
plt.show()
```

## Workflow 1: Exploratory Tile Extraction

Quick sampling of diverse tissue regions for initial analysis.

```python
from histolab.slide import Slide
from histolab.tiler import RandomTiler
import logging

# Enable logging for progress tracking
logging.basicConfig(level=logging.INFO)

# Load slide
slide = Slide("slide.svs", processed_path="output/random_tiles/")

# Inspect slide
print(f"Dimensions: {slide.dimensions}")
print(f"Levels: {slide.levels}")
slide.thumbnail.save("output/random_tiles/thumbnail.png")

# Configure random tiler
random_tiler = RandomTiler(
    tile_size=(512, 512),
    n_tiles=100,
    level=0,
    seed=42,
    check_tissue=True,
    tissue_percent=80.0
)

# Preview locations
random_tiler.locate_tiles(slide)

# Extract tiles
random_tiler.extract(slide)
```

## Workflow 2: Comprehensive Grid Extraction

Complete tissue coverage for whole-slide analysis.

```python
from histolab.slide import Slide
from histolab.tiler import GridTiler
from histolab.masks import TissueMask

# Load slide
slide = Slide("slide.svs", processed_path="output/grid_tiles/")

# Use TissueMask for all tissue sections
tissue_mask = TissueMask()
slide.locate_mask(tissue_mask)

# Configure grid tiler
grid_tiler = GridTiler(
    tile_size=(512, 512),
    level=1,  # Use level 1 for faster extraction
    pixel_overlap=0,
    check_tissue=True,
    tissue_percent=70.0
)

# Preview grid
grid_tiler.locate_tiles(slide)

# Extract all tiles
grid_tiler.extract(slide, extraction_mask=tissue_mask)
```

## Workflow 3: Quality-Driven Tile Selection

Extract most informative tiles based on nuclei density.

```python
from histolab.slide import Slide
from histolab.tiler import ScoreTiler
from histolab.scorer import NucleiScorer
import pandas as pd
import matplotlib.pyplot as plt

# Load slide
slide = Slide("slide.svs", processed_path="output/scored_tiles/")

# Configure score tiler
score_tiler = ScoreTiler(
    tile_size=(512, 512),
    n_tiles=50,
    level=0,
    scorer=NucleiScorer(),
    check_tissue=True
)

# Preview top tiles
score_tiler.locate_tiles(slide)

# Extract with report (CSV columns: filename, score, scaled_score)
score_tiler.extract(slide, report_path="tiles_report.csv")

# Analyze scores
report_df = pd.read_csv("tiles_report.csv")
plt.hist(report_df['score'], bins=20, edgecolor='black')
plt.xlabel('Tile Score')
plt.ylabel('Frequency')
plt.title('Distribution of Tile Scores')
plt.show()
```

## Workflow 4: Multi-Slide Processing Pipeline

Process entire slide collection with consistent parameters.

```python
from pathlib import Path
from histolab.slide import Slide
from histolab.tiler import RandomTiler
import logging

logging.basicConfig(level=logging.INFO)

# Configure tiler once
tiler = RandomTiler(
    tile_size=(512, 512),
    n_tiles=50,
    level=0,
    seed=42,
    check_tissue=True
)

# Process all slides
slide_dir = Path("slides/")
output_base = Path("output/")

for slide_path in slide_dir.glob("*.svs"):
    print(f"\nProcessing: {slide_path.name}")

    # Create slide-specific output directory
    output_dir = output_base / slide_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load and process slide
    slide = Slide(slide_path, processed_path=output_dir)

    # Save thumbnail for review
    slide.thumbnail.save(output_dir / "thumbnail.png")

    # Extract tiles
    tiler.extract(slide)

    print(f"Completed: {slide_path.name}")
```

## Workflow 5: Custom Tissue Detection and Filtering

Handle slides with artifacts, annotations, or unusual staining.

```python
from histolab.slide import Slide
from histolab.masks import TissueMask
from histolab.tiler import RandomTiler
from histolab.filters.image_filters import RgbToGrayscale, OtsuThreshold
from histolab.filters.morphological_filters import (
    BinaryDilation, RemoveSmallObjects, RemoveSmallHoles
)

# Aggressive artifact removal: pass the individual filters as positional args.
# TissueMask(*filters) overrides the default tissue-detection chain.
custom_mask = TissueMask(
    RgbToGrayscale(),
    OtsuThreshold(),
    BinaryDilation(disk_size=10),
    RemoveSmallHoles(area_threshold=5000),
    RemoveSmallObjects(min_size=3000),  # Remove larger artifacts
)

# Load slide and visualize mask
slide = Slide("slide.svs", processed_path="output/")
slide.locate_mask(custom_mask)

# Extract with custom mask (extraction_mask is an extract() arg, not a constructor arg)
tiler = RandomTiler(tile_size=(512, 512), n_tiles=100, seed=42)
tiler.extract(slide, extraction_mask=custom_mask)
```
