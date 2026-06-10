# Preprocessing Pipelines & Transforms

## Overview

PathML provides a modular preprocessing architecture based on composable transforms organized into pipelines. Transforms are individual operations that modify images, create masks, or extract features. Pipelines chain transforms together to create reproducible, scalable preprocessing workflows for computational pathology.

## Pipeline Architecture

### Pipeline Class

The `Pipeline` class composes a sequence of transforms applied consecutively:

A `Pipeline` is a reusable, serializable list of transforms. You apply it by passing it to a slide's or dataset's `run()` method (the slide/dataset drives execution, not the pipeline):

```python
from pathml.preprocessing import Pipeline, Transform1, Transform2

# Create pipeline
pipeline = Pipeline([
    Transform1(param1=value1),
    Transform2(param2=value2),
    # ... more transforms
])

# Run on a single slide
slide_data.run(pipeline)

# Run on a dataset (parallelized via a Dask client)
dataset.run(pipeline, client=client)
```

**Key features:**
- Sequential execution of transforms
- Automatic handling of tiles and masks
- Distributed processing support with Dask
- Reproducible workflows with serializable configuration

### Transform Base Class

All transforms inherit from the `Transform` base class and implement:
- `apply()` - Core transformation logic
- `input_type` - Expected input (tile, mask, etc.)
- `output_type` - Produced output

## Transform Categories

PathML provides transforms in six major categories:

1. **Image Modification** - Blur, rescale, histogram equalization
2. **Mask Creation** - Tissue detection, nucleus detection, thresholding
3. **Mask Modification** - Morphological operations on masks
4. **Stain Processing** - H&E stain normalization and separation
5. **Quality Control** - Artifact detection, white space labeling
6. **Specialized** - Multiparametric imaging, cell segmentation

## Image Modification Transforms

### Blur Operations

Apply various blurring kernels for noise reduction:

**MedianBlur:**
```python
from pathml.preprocessing import MedianBlur

# Apply median filter
transform = MedianBlur(kernel_size=5)
```
- Effective for salt-and-pepper noise
- Preserves edges better than Gaussian blur

**GaussianBlur:**
```python
from pathml.preprocessing import GaussianBlur

# Apply Gaussian blur
transform = GaussianBlur(kernel_size=5, sigma=1.0)
```
- Smooth noise reduction
- Adjustable sigma controls blur strength

**BoxBlur:**
```python
from pathml.preprocessing import BoxBlur

# Apply box filter
transform = BoxBlur(kernel_size=5)
```
- Fastest blur operation
- Uniform averaging within kernel

### Intensity Adjustments

**RescaleIntensity:**
```python
from pathml.preprocessing import RescaleIntensity

# Rescale intensity to [0, 255]
transform = RescaleIntensity(
    in_range=(0, 1.0),
    out_range=(0, 255)
)
```

**HistogramEqualization:**
```python
from pathml.preprocessing import HistogramEqualization

# Global histogram equalization
transform = HistogramEqualization()
```
- Enhances global contrast
- Spreads out intensity distribution

**AdaptiveHistogramEqualization (CLAHE):**
```python
from pathml.preprocessing import AdaptiveHistogramEqualization

# Contrast Limited Adaptive Histogram Equalization
transform = AdaptiveHistogramEqualization(
    clip_limit=0.03,
    tile_grid_size=(8, 8)
)
```
- Enhances local contrast
- Prevents over-amplification with clip_limit
- Better for images with varying local contrast

### Superpixel Processing

**SuperpixelInterpolation:**
```python
from pathml.preprocessing import SuperpixelInterpolation

# Divide into superpixels using SLIC
transform = SuperpixelInterpolation(
    n_segments=100,
    compactness=10.0
)
```
- Segments image into perceptually meaningful regions
- Useful for feature extraction and segmentation

## Mask Creation Transforms

### H&E Tissue and Nucleus Detection

**TissueDetectionHE:**
```python
from pathml.preprocessing import TissueDetectionHE

# Detect tissue regions in H&E slides
transform = TissueDetectionHE(
    use_saturation=True,  # Use HSV saturation channel
    threshold=10,  # Intensity threshold
    min_region_size=500  # Minimum tissue region size in pixels
)
```
- Creates binary tissue mask
- Filters small regions and artifacts
- Stores mask in `tile.masks['tissue']`

**NucleusDetectionHE:**
```python
from pathml.preprocessing import NucleusDetectionHE

# Detect nuclei in H&E images
transform = NucleusDetectionHE(
    stain='hematoxylin',  # Use hematoxylin channel
    threshold=0.3,
    min_nucleus_size=10
)
```
- Separates hematoxylin stain
- Thresholds to create nucleus mask
- Stores mask in `tile.masks['nucleus']`

### Binary Thresholding

**BinaryThreshold:**
```python
from pathml.preprocessing import BinaryThreshold

# Threshold using Otsu's method
transform = BinaryThreshold(
    method='otsu',  # 'otsu' or manual threshold value
    invert=False
)

# Or specify manual threshold
transform = BinaryThreshold(threshold=128)
```

### Foreground Detection

**ForegroundDetection:**
```python
from pathml.preprocessing import ForegroundDetection

# Detect foreground regions
transform = ForegroundDetection(
    threshold=0.5,
    min_region_size=1000,  # Minimum size in pixels
    use_saturation=True
)
```

## Mask Modification Transforms

Apply morphological operations to clean up masks:

**MorphOpen:**
```python
from pathml.preprocessing import MorphOpen

# Remove small objects and noise
transform = MorphOpen(
    kernel_size=5,
    mask_name='tissue'  # Which mask to modify
)
```
- Erosion followed by dilation
- Removes small objects and noise

**MorphClose:**
```python
from pathml.preprocessing import MorphClose

# Fill small holes
transform = MorphClose(
    kernel_size=5,
    mask_name='tissue'
)
```
- Dilation followed by erosion
- Fills small holes in mask

## Stain Normalization

### StainNormalizationHE

Normalize H&E staining across slides to account for variations in staining procedure and scanners:

```python
from pathml.preprocessing import StainNormalizationHE

# Normalize to reference stain vectors
transform = StainNormalizationHE(
    target="normalize",  # "normalize", "hematoxylin", or "eosin"
    stain_estimation_method="macenko",  # "macenko" or "vahadane"
)
```

**Target modes:**
- `"normalize"` - Normalize both stains to reference
- `"hematoxylin"` - Extract hematoxylin channel only
- `"eosin"` - Extract eosin channel only

**Stain estimation methods:**
- `"macenko"` - Macenko et al. 2009 method (faster, more stable)
- `"vahadane"` - Vahadane et al. 2016 method (more accurate, slower)

**Other documented parameters** (confirm against the API docs for your version):
```python
transform = StainNormalizationHE(
    target="normalize",
    stain_estimation_method="macenko",
    optical_density_threshold=0.15,   # OD cutoff separating tissue from background
    angular_percentile=0.01,          # robust percentile for stain-vector estimation
    regularizer=0.01,                 # regularization for the vahadane method
    background_intensity=245,          # assumed background intensity
    stain_matrix_target_od=None,       # reference stain matrix in OD space (optional)
    max_c_target=None,                 # reference max stain concentrations (optional)
)
```

Note: `StainNormalizationHE` does not take a `tissue_mask_name` argument; it estimates stain vectors from the tile's optical-density distribution.

**Workflow:**
1. Convert RGB to optical density (OD)
2. Estimate stain matrix (H&E vectors)
3. Decompose into stain concentrations
4. Normalize to reference stain distribution
5. Reconstruct normalized RGB image

**Example: detect tissue, then normalize:**
```python
from pathml.preprocessing import Pipeline, TissueDetectionHE, StainNormalizationHE

pipeline = Pipeline([
    TissueDetectionHE(),  # creates the 'tissue' mask
    StainNormalizationHE(
        target="normalize",
        stain_estimation_method="macenko",
    ),
])
```

## Quality Control Transforms

### Artifact Detection

**LabelArtifactTileHE:**
```python
from pathml.preprocessing import LabelArtifactTileHE

# Label tiles containing artifacts
transform = LabelArtifactTileHE(
    pen_threshold=0.5,  # Threshold for pen marking detection
    bubble_threshold=0.5  # Threshold for bubble detection
)
```
- Detects pen markings, bubbles, and other artifacts
- Labels affected tiles for filtering

**LabelWhiteSpaceHE:**
```python
from pathml.preprocessing import LabelWhiteSpaceHE

# Label tiles with excessive white space
transform = LabelWhiteSpaceHE(
    threshold=0.9,  # Fraction of white pixels
    mask_name='white_space'
)
```
- Identifies tiles with mostly background
- Useful for filtering uninformative tiles

## Multiparametric Imaging Transforms

### Cell Segmentation

**SegmentMIF:**
```python
from pathml.preprocessing import SegmentMIF

# Segment cells using the DeepCell Mesmer model.
# nuclear_channel / cytoplasm_channel are INTEGER indices into the
# (collapsed) channel stack, not marker name strings.
transform = SegmentMIF(
    model="mesmer",
    nuclear_channel=0,        # e.g. index of DAPI
    cytoplasm_channel=29,     # e.g. index of a membrane/cytoplasm marker
    image_resolution=0.377,   # microns per pixel
)
```
- Uses the DeepCell Mesmer model for whole-cell + nuclear segmentation
- Channels are specified by integer index into the channel stack
- Writes `cell_segmentation` and `nuclear_segmentation` masks
- Fine-grained control is via `preprocess_kwargs`, `postprocess_kwargs_nuclear`, and `postprocess_kwargs_whole_cell` (there is no `compartment` argument)

**SegmentMIFRemote:**
```python
from pathml.preprocessing import SegmentMIFRemote

# Remote inference using the DeepCell Kiosk API (no local GPU)
transform = SegmentMIFRemote(
    model="mesmer",
    nuclear_channel=0,
    cytoplasm_channel=29,
)
```
- Same functionality as SegmentMIF but offloads inference to the DeepCell service
- No local GPU required; suitable for batch processing

### Marker Quantification

**QuantifyMIF:**
```python
from pathml.preprocessing import QuantifyMIF

# Quantify marker expression per cell. The only argument is the name of
# the segmentation mask produced by SegmentMIF.
transform = QuantifyMIF(segmentation_mask="cell_segmentation")
```
- Extracts mean marker intensity per segmented cell across all channels
- Computes per-cell spatial/morphology info
- Writes an AnnData object to `slide.counts` for downstream single-cell analysis (read it back via `slide.counts`, or concatenate across a dataset with `anndata.concat([s.counts for s in dataset.slides], ...)`)

### CODEX/Vectra Specific

**CollapseRunsCODEX:**
```python
from pathml.preprocessing import CollapseRunsCODEX

# Consolidate a multi-cycle CODEX z-stack by selecting a focal plane.
transform = CollapseRunsCODEX(z=0)  # 'z' selects the z-plane index
```
- Collapses the CODEX z-stack/cycles into a single multi-channel image
- `z` selects the focal plane (0-indexed)

**CollapseRunsVectra:**
```python
from pathml.preprocessing import CollapseRunsVectra

# Process Vectra multiplex IF data
transform = CollapseRunsVectra(
    wavelengths=[520, 570, 620, 670, 780]  # Emission wavelengths
)
```

## Building Comprehensive Pipelines

### Basic H&E Preprocessing Pipeline

```python
from pathml.preprocessing import (
    Pipeline,
    TissueDetectionHE,
    StainNormalizationHE,
    NucleusDetectionHE,
    MedianBlur,
    LabelWhiteSpaceHE
)

pipeline = Pipeline([
    # 1. Quality control
    LabelWhiteSpaceHE(threshold=0.9),

    # 2. Noise reduction
    MedianBlur(kernel_size=3),

    # 3. Tissue detection
    TissueDetectionHE(min_region_size=500),

    # 4. Stain normalization
    StainNormalizationHE(
        target='normalize',
        stain_estimation_method='macenko',
        tissue_mask_name='tissue'
    ),

    # 5. Nucleus detection
    NucleusDetectionHE(threshold=0.3)
])
```

### CODEX Multiparametric Pipeline

```python
from pathml.preprocessing import (
    Pipeline,
    CollapseRunsCODEX,
    SegmentMIF,
    QuantifyMIF
)

codex_pipeline = Pipeline([
    # 1. Collapse the z-stack
    CollapseRunsCODEX(z=0),

    # 2. Cell segmentation (integer channel indices)
    SegmentMIF(
        model="mesmer",
        nuclear_channel=0,
        cytoplasm_channel=29,
        image_resolution=0.377,
    ),

    # 3. Quantify markers -> writes AnnData to slide.counts
    QuantifyMIF(segmentation_mask="cell_segmentation"),
])
```

### Advanced Pipeline with Quality Control

```python
from pathml.preprocessing import (
    Pipeline,
    LabelWhiteSpaceHE,
    LabelArtifactTileHE,
    TissueDetectionHE,
    MorphOpen,
    MorphClose,
    StainNormalizationHE,
    AdaptiveHistogramEqualization
)

advanced_pipeline = Pipeline([
    # Stage 1: Quality control
    LabelWhiteSpaceHE(threshold=0.85),
    LabelArtifactTileHE(pen_threshold=0.5, bubble_threshold=0.5),

    # Stage 2: Tissue detection
    TissueDetectionHE(threshold=10, min_region_size=1000),
    MorphOpen(kernel_size=5, mask_name='tissue'),
    MorphClose(kernel_size=7, mask_name='tissue'),

    # Stage 3: Stain normalization
    StainNormalizationHE(
        target='normalize',
        stain_estimation_method='vahadane',
        tissue_mask_name='tissue'
    ),

    # Stage 4: Contrast enhancement
    AdaptiveHistogramEqualization(clip_limit=0.03, tile_grid_size=(8, 8))
])
```

## Running Pipelines

### Single Slide Processing

```python
from pathml.core import HESlide

# Load slide
wsi = HESlide("slide.svs")

# Run the pipeline. SlideData.run handles tiling internally; pass tiling
# options through (e.g. tile_size / level) as supported by your version.
wsi.run(pipeline, tile_size=256, tile_stride=256, level=1)

# Access processed data
for tile in wsi.tiles:
    normalized_image = tile.image
    tissue_mask = tile.masks.get("tissue")
    nucleus_mask = tile.masks.get("nucleus")
```

### Batch Processing with Distributed Execution

```python
from pathml.core import HESlide, SlideDataset
from dask.distributed import Client
import glob

# Start Dask client
client = Client(n_workers=8, threads_per_worker=2, memory_limit="4GB")

# Create dataset from slide objects
slide_paths = glob.glob("data/*.svs")
dataset = SlideDataset([HESlide(p) for p in slide_paths])

# Run pipeline in parallel (tiling options passed through to run())
dataset.run(pipeline, client=client, tile_size=512, tile_stride=512, level=1)

# Persist results to h5path (one file per slide in the directory)
dataset.write("processed/")

client.close()
```

### Filtering Tiles After Processing

Filter on masks produced by the pipeline (e.g. keep only tissue tiles):

```python
wsi.run(pipeline, tile_size=256, level=1)

tissue_tiles = [
    tile for tile in wsi.tiles
    if tile.masks.get("tissue") is not None and tile.masks["tissue"].any()
]
```

## Performance Optimization

### Memory Management

```python
from pathml.core import HESlide, SlideDataset

# Process large datasets in batches
batch_size = 100
for i in range(0, len(slide_paths), batch_size):
    batch_paths = slide_paths[i:i + batch_size]
    batch_dataset = SlideDataset([HESlide(p) for p in batch_paths])
    batch_dataset.run(pipeline, client=client)
    batch_dataset.write(f"processed/batch_{i}/")
```

### GPU Acceleration

Certain transforms leverage GPU acceleration when available:

```python
import torch

# Check GPU availability
print(f"CUDA available: {torch.cuda.is_available()}")

# Transforms that benefit from GPU:
# - SegmentMIF (Mesmer deep learning model)
# - StainNormalizationHE (matrix operations)
```

### Parallel Workers Configuration

```python
from dask.distributed import Client

# CPU-bound tasks (image processing)
client = Client(
    n_workers=8,
    threads_per_worker=1,  # Use processes, not threads
    memory_limit='8GB'
)

# GPU tasks (deep learning inference)
client = Client(
    n_workers=2,  # Fewer workers for GPU
    threads_per_worker=4,
    processes=True
)
```

## Custom Transforms

Create custom preprocessing operations by subclassing `Transform`:

```python
from pathml.preprocessing.transforms import Transform
import numpy as np

class CustomTransform(Transform):
    def __init__(self, param1, param2):
        self.param1 = param1
        self.param2 = param2

    def apply(self, tile):
        # Access tile image
        image = tile.image

        # Apply custom operation
        processed = self.custom_operation(image, self.param1, self.param2)

        # Update tile
        tile.image = processed

        return tile

    def custom_operation(self, image, param1, param2):
        # Implement custom logic
        return processed_image

# Use in pipeline
pipeline = Pipeline([
    CustomTransform(param1=10, param2=0.5),
    # ... other transforms
])
```

## Best Practices

1. **Order transforms appropriately:**
   - Quality control first (LabelWhiteSpace, LabelArtifact)
   - Noise reduction early (Blur)
   - Tissue detection before stain normalization
   - Stain normalization before color-dependent operations

2. **Use tissue masks for stain normalization:**
   - Improves accuracy by excluding background
   - `TissueDetectionHE()` then `StainNormalizationHE(tissue_mask_name='tissue')`

3. **Apply morphological operations to clean masks:**
   - `MorphOpen` to remove small false positives
   - `MorphClose` to fill small gaps

4. **Leverage distributed processing for large datasets:**
   - Use Dask for parallel execution
   - Configure workers based on available resources

5. **Save intermediate results:**
   - Store processed data to HDF5 for reuse
   - Avoid reprocessing computationally expensive transforms

6. **Validate preprocessing on sample images:**
   - Visualize intermediate steps
   - Tune parameters on representative samples before batch processing

7. **Handle edge cases:**
   - Check for empty masks before downstream operations
   - Validate tile quality before expensive computations

## Common Issues and Solutions

**Issue: Stain normalization produces artifacts**
- Use tissue mask to exclude background
- Try different stain estimation method (macenko vs. vahadane)
- Verify optical density parameters match your images

**Issue: Out of memory during pipeline execution**
- Reduce number of Dask workers
- Decrease tile size
- Process images at lower pyramid level
- Enable memory_limit parameter in Dask client

**Issue: Tissue detection misses tissue regions**
- Adjust threshold parameter
- Use saturation channel: `use_saturation=True`
- Reduce min_region_size to capture smaller tissue fragments

**Issue: Nucleus detection is inaccurate**
- Verify stain separation quality (visualize hematoxylin channel)
- Adjust threshold parameter
- Apply stain normalization before nucleus detection

## Additional Resources

- **PathML Preprocessing API:** https://pathml.readthedocs.io/en/latest/api_preprocessing_reference.html
- **Stain Normalization Methods:**
  - Macenko et al. 2009: "A method for normalizing histology slides for quantitative analysis"
  - Vahadane et al. 2016: "Structure-Preserving Color Normalization and Sparse Stain Separation"
- **DeepCell Mesmer:** https://www.deepcell.org/ (cell segmentation model)
