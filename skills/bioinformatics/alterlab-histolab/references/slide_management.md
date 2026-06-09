# Slide Management

## Overview

The `Slide` class is the primary interface for working with whole slide images (WSI) in histolab. It provides methods to load, inspect, and process large histopathology images stored in various formats.

## Initialization

```python
from histolab.slide import Slide

# Initialize a slide with a WSI file and output directory.
# The first positional/keyword arg is `path` (not `slide_path`).
slide = Slide(path="path/to/slide.svs",
              processed_path="path/to/processed/output")
```

**Parameters:**
- `path`: Path to the whole slide image file (supports multiple formats: SVS, TIFF, NDPI, etc.)
- `processed_path`: Directory where processed outputs (tiles, thumbnails, etc.) will be saved (required — cannot be `None`)
- `use_largeimage` (default `False`): use the `large_image` backend instead of OpenSlide, enabling exact microns-per-pixel tile fetching

## Loading Sample Data

Histolab provides built-in sample datasets from TCGA for testing and demonstration:

```python
from histolab.data import prostate_tissue, ovarian_tissue, breast_tissue, heart_tissue

# Each loader returns (OpenSlide object, path); pass the path to Slide.
prostate_svs, prostate_path = prostate_tissue()
slide = Slide(prostate_path, processed_path="output/")
```

Available sample datasets (histolab 0.7.0):
- `prostate_tissue()`, `ovarian_tissue()`, `breast_tissue()`, `heart_tissue()`,
  `aorta_tissue()`: H&E tissue samples
- `breast_tissue_diagnostic_green_pen()` / `_red_pen()` / `_black_pen()`: slides
  with pen-mark artifacts (handy for testing artifact-removal masks)
- `ihc_breast()`, `ihc_kidney()`: IHC-stained samples
- `cmu_small_region()`: tiny region for quick smoke tests

> There is no `kidney_tissue()`; the kidney sample is `ihc_kidney()`.

## Key Properties

### Slide Dimensions
```python
# Get slide dimensions at level 0 (highest resolution)
width, height = slide.dimensions

# level_dimensions is a METHOD that takes a level and returns (width, height)
w1, h1 = slide.level_dimensions(level=1)
```

### Magnification Information
```python
# Microns per pixel at level 0 (resolution, not objective magnification)
mpp = slide.base_mpp

# `levels` is a LIST of available pyramid levels (e.g. [0, 1, 2]), not a count.
available_levels = slide.levels
num_levels = len(slide.levels)
```

### Slide Properties
```python
# Access OpenSlide properties dictionary
properties = slide.properties

# Common properties include:
# - slide.properties['openslide.objective-power']: Objective power
# - slide.properties['openslide.mpp-x']: Microns per pixel in X
# - slide.properties['openslide.mpp-y']: Microns per pixel in Y
# - slide.properties['openslide.vendor']: Scanner vendor
```

## Thumbnail Generation

```python
# `thumbnail` is a property returning a PIL.Image
thumbnail = slide.thumbnail

# There is no save_thumbnail() method — save the PIL image directly
slide.thumbnail.save("output/thumbnail.png")

# scaled_image(scale_factor) is a method returning a downscaled PIL.Image
scaled = slide.scaled_image(scale_factor=32)
```

## Slide Visualization

```python
# Display slide thumbnail with matplotlib
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 10))
plt.imshow(slide.thumbnail)
plt.title(f"Slide: {slide.name}")
plt.axis('off')
plt.show()
```

## Extracting a Single Tile

```python
from histolab.types import CoordinatePair

# Extract one tile at given level-0 coordinates. The method is extract_tile()
# (there is no extract_region). coords is a CoordinatePair(x_ul, y_ul, x_br, y_br).
tile = slide.extract_tile(
    coords=CoordinatePair(x_ul=0, y_ul=0, x_br=512, y_br=512),
    tile_size=(512, 512),
    level=0,
)
```

## Working with Pyramid Levels

WSI files use a pyramidal structure with multiple resolution levels:
- Level 0: Highest resolution (native scan resolution)
- Level 1+: Progressively lower resolutions for faster access

```python
# `levels` is a list, so iterate it directly (don't wrap it in range()).
for level in slide.levels:
    dims = slide.level_dimensions(level=level)  # method call, not subscript
    print(f"Level {level}: {dims}")
```

## Slide Name

```python
# Get slide filename without extension
slide_name = slide.name
```

## Best Practices

1. **Always specify processed_path**: Organize outputs in dedicated directories
2. **Check dimensions before processing**: Large slides can exceed memory limits
3. **Use appropriate pyramid levels**: Extract tiles at levels matching your analysis resolution
4. **Preview with thumbnails**: Use thumbnails for quick visualization before heavy processing
5. **Monitor memory usage**: Level 0 operations on large slides require significant RAM

## Common Workflows

### Slide Inspection Workflow
```python
from histolab.slide import Slide

# Load slide
slide = Slide("slide.svs", processed_path="output/")

# Inspect properties
print(f"Dimensions: {slide.dimensions}")
print(f"Levels: {slide.levels}")
print(f"Magnification: {slide.properties.get('openslide.objective-power', 'N/A')}")

# Save thumbnail for review
slide.thumbnail.save("output/thumbnail.png")
```

### Multi-Slide Processing
```python
import os
from pathlib import Path

slide_dir = Path("slides/")
output_dir = Path("processed/")

for slide_path in slide_dir.glob("*.svs"):
    slide = Slide(slide_path, processed_path=output_dir / slide_path.stem)
    # Process each slide
    print(f"Processing: {slide.name}")
```
