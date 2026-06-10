# Tissue Masks

## Overview

Tissue masks are binary representations that identify tissue regions within whole slide images. They are essential for filtering out background, artifacts, and non-tissue areas during tile extraction. Histolab provides several mask classes to accommodate different tissue segmentation needs.

## Mask Classes

### BinaryMask

**Purpose:** Generic base class for creating custom binary masks.

```python
from histolab.masks import BinaryMask

class CustomMask(BinaryMask):
    def _mask(self, obj):
        # Implement custom masking logic
        # Return binary numpy array
        pass
```

**Use cases:**
- Custom tissue segmentation algorithms
- Region-specific analysis (e.g., excluding annotations)
- Integration with external segmentation models

### TissueMask

**Purpose:** Segments all tissue regions in the slide using automated filters.

```python
from histolab.masks import TissueMask

# Create tissue mask
tissue_mask = TissueMask()

# Apply to slide
mask_array = tissue_mask(slide)
```

**How it works:**
1. Converts image to grayscale
2. Applies Otsu thresholding to separate tissue from background
3. Performs binary dilation to connect nearby tissue regions
4. Removes small holes within tissue regions
5. Filters out small objects (artifacts)

**Returns:** Binary NumPy array where:
- `True` (or 1): Tissue pixels
- `False` (or 0): Background pixels

**Best for:**
- Slides with multiple separate tissue sections
- Comprehensive tissue analysis
- When all tissue regions are important

### BiggestTissueBoxMask (Default)

**Purpose:** Identifies and returns the bounding box of the largest connected tissue region.

```python
from histolab.masks import BiggestTissueBoxMask

# Create mask for largest tissue region
biggest_mask = BiggestTissueBoxMask()

# Apply to slide
mask_array = biggest_mask(slide)
```

**How it works:**
1. Applies same filtering pipeline as TissueMask
2. Identifies all connected tissue components
3. Selects the largest connected component
4. Returns bounding box encompassing that region

**Best for:**
- Slides with a single primary tissue section
- Excluding small artifacts or tissue fragments
- Focusing on main tissue area (default for most tilers)

## Customizing Masks with Filters

Masks accept custom filters for specialized tissue detection. Pass the filters
as **positional varargs** (`TissueMask(*filters)`) — not as a `filters=` keyword
and not as a single `Compose` object. They replace the default filter chain.

```python
from histolab.masks import TissueMask
from histolab.filters.image_filters import RgbToGrayscale, OtsuThreshold
from histolab.filters.morphological_filters import BinaryDilation, RemoveSmallHoles

custom_mask = TissueMask(
    RgbToGrayscale(),
    OtsuThreshold(),
    BinaryDilation(disk_size=5),
    RemoveSmallHoles(area_threshold=500),
)
```

## Visualizing Masks

### Using locate_mask()

```python
from histolab.slide import Slide
from histolab.masks import TissueMask

slide = Slide("slide.svs", processed_path="output/")
mask = TissueMask()

# Visualize mask boundaries on thumbnail
slide.locate_mask(mask)
```

This displays the slide thumbnail with mask boundaries overlaid in a contrasting color.

### Manual Visualization

```python
import matplotlib.pyplot as plt
from histolab.masks import TissueMask

slide = Slide("slide.svs", processed_path="output/")
tissue_mask = TissueMask()

# Generate mask
mask_array = tissue_mask(slide)

# Plot side by side
fig, axes = plt.subplots(1, 2, figsize=(15, 7))

axes[0].imshow(slide.thumbnail)
axes[0].set_title("Original Slide")
axes[0].axis('off')

axes[1].imshow(mask_array, cmap='gray')
axes[1].set_title("Tissue Mask")
axes[1].axis('off')

plt.show()
```

## Creating Custom Rectangular Masks

Define specific regions of interest:

```python
from histolab.masks import BinaryMask
import numpy as np

class RectangularMask(BinaryMask):
    def __init__(self, x_start, y_start, width, height):
        self.x_start = x_start
        self.y_start = y_start
        self.width = width
        self.height = height

    def _mask(self, obj):
        # Create mask with specified rectangular region
        thumb = obj.thumbnail
        mask = np.zeros(thumb.shape[:2], dtype=bool)
        mask[self.y_start:self.y_start+self.height,
             self.x_start:self.x_start+self.width] = True
        return mask

# Use custom mask
roi_mask = RectangularMask(x_start=1000, y_start=500, width=2000, height=1500)
```

## Excluding Annotations

Pathology slides often contain pen markings or digital annotations. Exclude them using custom masks:

```python
import cv2
import numpy as np
from histolab.masks import TissueMask, BinaryMask

class AnnotationExclusionMask(BinaryMask):
    def _mask(self, obj):
        # Run the default tissue detection first; its output sets the target shape.
        tissue_mask = TissueMask()(obj)            # bool ndarray (H, W)
        h, w = tissue_mask.shape[:2]

        # Build a pen-mark mask at the SAME resolution as tissue_mask so the
        # arrays line up for the boolean combine below.
        thumb = np.array(obj.thumbnail.convert("RGB"))
        thumb = cv2.resize(thumb, (w, h), interpolation=cv2.INTER_NEAREST)
        hsv = cv2.cvtColor(thumb, cv2.COLOR_RGB2HSV)

        # HSV range for blue/green pen marks (OpenCV hue is 0-179)
        lower_blue = np.array([100, 50, 50])
        upper_blue = np.array([130, 255, 255])
        pen_mask = cv2.inRange(hsv, lower_blue, upper_blue).astype(bool)

        # Keep tissue, drop pen marks
        return tissue_mask & ~pen_mask
```

## Integration with Tile Extraction

Masks integrate with tilers through the `extraction_mask` parameter of
`extract()` / `locate_tiles()` — **not** the tiler constructor:

```python
from histolab.tiler import RandomTiler
from histolab.masks import TissueMask, BiggestTissueBoxMask

random_tiler = RandomTiler(tile_size=(512, 512), n_tiles=100, level=0, seed=42)

# Extract from ALL tissue sections
random_tiler.extract(slide, extraction_mask=TissueMask())

# Default behavior (largest tissue bounding box) — extraction_mask defaults to
# BiggestTissueBoxMask(), so this is equivalent to omitting it
random_tiler.extract(slide, extraction_mask=BiggestTissueBoxMask())
```

## Best Practices

1. **Preview masks before extraction**: Use `locate_mask()` or manual visualization to verify mask quality
2. **Choose appropriate mask type**: Use `TissueMask` for multiple tissue sections, `BiggestTissueBoxMask` for single main sections
3. **Customize for specific stains**: Different stains (H&E, IHC) may require adjusted threshold parameters
4. **Handle artifacts**: Use custom filters or masks to exclude pen marks, bubbles, or folds
5. **Test on diverse slides**: Validate mask performance across slides with varying quality and artifacts
6. **Consider computational cost**: `TissueMask` is more comprehensive but computationally intensive than `BiggestTissueBoxMask`

## Common Issues and Solutions

### Issue: Mask includes too much background
**Solution:** Adjust Otsu threshold or increase small object removal threshold

### Issue: Mask excludes valid tissue
**Solution:** Reduce small object removal threshold or modify dilation parameters

### Issue: Multiple tissue sections, but only largest is captured
**Solution:** Switch from `BiggestTissueBoxMask` to `TissueMask`

### Issue: Pen annotations included in mask
**Solution:** Implement custom annotation exclusion mask (see example above)
