# Multiparametric Imaging

## Overview

PathML provides specialized support for multiparametric imaging technologies that simultaneously measure multiple markers at single-cell resolution. These techniques include CODEX, Vectra multiplex immunofluorescence, MERFISH, and other spatial proteomics and transcriptomics platforms. PathML handles the unique data structures, processing requirements, and quantification workflows specific to each technology.

## Supported Technologies

### CODEX (CO-Detection by indEXing)
- Cyclic immunofluorescence imaging
- 40+ protein markers simultaneously
- Single-cell spatial proteomics
- Multi-cycle acquisition with antibody barcoding

### Vectra Polaris
- Multispectral multiplex immunofluorescence
- 6-8 markers per slide
- Spectral unmixing
- Whole-slide scanning

### MERFISH (Multiplexed Error-Robust FISH)
- Spatial transcriptomics
- 100s-1000s of genes
- Single-molecule resolution
- Error-correcting barcodes

### Other Platforms
- CycIF (Cyclic Immunofluorescence)
- IMC (Imaging Mass Cytometry)
- MIBI (Multiplexed Ion Beam Imaging)

## CODEX Workflows

### Loading CODEX Data

CODEX data is typically organized in multi-channel image stacks from multiple acquisition cycles:

```python
from pathml.core import CODEXSlide

# Load CODEX dataset (uses the Bio-Formats backend internally)
codex_slide = CODEXSlide("path/to/codex_directory", stain="IF")

# Inspect dimensions
print(f"Image shape: {codex_slide.shape}")
```

**CODEX directory structure:**
```
codex_directory/
├── cyc001_reg001/
│   ├── 1_00001_Z001_CH1.tif
│   ├── 1_00001_Z001_CH2.tif
│   └── ...
├── cyc002_reg001/
│   └── ...
└── channelnames.txt
```

### CODEX Preprocessing Pipeline

Complete pipeline for CODEX data processing:

```python
from pathml.preprocessing import Pipeline, CollapseRunsCODEX, SegmentMIF, QuantifyMIF

# Create CODEX-specific pipeline
codex_pipeline = Pipeline([
    # 1. Collapse the z-stack to a single multi-channel image
    CollapseRunsCODEX(z=0),

    # 2. Cell segmentation using Mesmer (integer channel indices)
    SegmentMIF(
        model="mesmer",
        nuclear_channel=0,        # e.g. DAPI index
        cytoplasm_channel=29,     # e.g. membrane/cytoplasm marker index
        image_resolution=0.377,   # microns per pixel
    ),

    # 3. Quantify per-cell marker expression across all channels
    QuantifyMIF(segmentation_mask="cell_segmentation"),
])

# Run pipeline on the slide
codex_slide.run(codex_pipeline)

# Access results
segmentation_mask = codex_slide.masks["cell_segmentation"]
cell_data = codex_slide.counts  # AnnData object (cells x markers)
```

### CollapseRunsCODEX

Consolidates multi-cycle CODEX acquisitions into a single multi-channel image:

```python
from pathml.preprocessing import CollapseRunsCODEX

transform = CollapseRunsCODEX(z=0)  # select the focal plane (0-indexed)
```

**Parameters:**
- `z`: which z-plane to extract from the CODEX z-stack (0-indexed)

**Output:** Single multi-channel image with all markers stacked along the channel axis.

### Cell Segmentation with Mesmer

DeepCell Mesmer provides accurate cell segmentation for multiparametric imaging:

```python
from pathml.preprocessing import SegmentMIF

transform = SegmentMIF(
    model="mesmer",            # DeepCell Mesmer model
    nuclear_channel=0,         # integer index of the nuclear marker (e.g. DAPI)
    cytoplasm_channel=29,      # integer index of a membrane/cytoplasm marker
    image_resolution=0.377,    # microns per pixel (important for accuracy)
)
```

`SegmentMIF` produces both `nuclear_segmentation` and `cell_segmentation` (whole-cell) masks. Tune behavior via `preprocess_kwargs`, `postprocess_kwargs_nuclear`, and `postprocess_kwargs_whole_cell`; there is no `compartment`/`min_cell_size`/`max_cell_size` argument.

**Choosing the cytoplasm channel** (pick the index of a marker that outlines cells):
- A pan-leukocyte marker (e.g. CD45) for immune-rich tissues
- A pan-cytokeratin marker (e.g. panCK) for epithelial tissues
- A universal membrane marker, or an averaged membrane channel

### Remote Segmentation

Use the DeepCell service for segmentation without a local GPU:

```python
from pathml.preprocessing import SegmentMIFRemote

transform = SegmentMIFRemote(
    model="mesmer",
    nuclear_channel=0,
    cytoplasm_channel=29,
)
```

### Marker Quantification

Extract single-cell marker expression from segmented images:

```python
from pathml.preprocessing import QuantifyMIF

# Quantify per-cell expression across all channels of the segmented mask.
transform = QuantifyMIF(segmentation_mask="cell_segmentation")
```

**Output:** an AnnData object written to `slide.counts`:
- `adata.X`: marker expression matrix (cells x channels)
- `adata.obs`: per-cell metadata (coordinates, area, etc.)
- `adata.var`: channel/marker metadata
- `adata.obsm["spatial"]`: cell centroid coordinates

### Integration with AnnData

Process multiple CODEX slides into unified AnnData object:

```python
from pathml.core import CODEXSlide, SlideDataset
from dask.distributed import Client
import anndata as ad

# Process multiple slides
slide_paths = ["slide1", "slide2", "slide3"]
dataset = SlideDataset([CODEXSlide(p, stain="IF") for p in slide_paths])

client = Client(n_workers=8, threads_per_worker=2)
dataset.run(codex_pipeline, client=client)

# Concatenate the per-slide AnnData objects (each lives on slide.counts)
combined_adata = ad.concat(
    [s.counts for s in dataset.slides],
    join="outer",
    label="Region",
    keys=slide_paths,
    index_unique="_",
)

# Save for downstream analysis
combined_adata.write("codex_dataset.h5ad")
```

## Vectra Workflows

### Loading Vectra Data

Vectra stores data in proprietary `.qptiff` format:

```python
from pathml.core import VectraSlide

# Load Vectra slide (.qptiff); VectraSlide uses the Bio-Formats backend
vectra_slide = VectraSlide("path/to/slide.qptiff")

print(f"Shape: {vectra_slide.shape}")
```

### Vectra Preprocessing

```python
from pathml.preprocessing import Pipeline, CollapseRunsVectra, SegmentMIF, QuantifyMIF

vectra_pipeline = Pipeline([
    # 1. Collapse the Vectra multi-channel data into a single image
    CollapseRunsVectra(),

    # 2. Cell segmentation (integer channel indices)
    SegmentMIF(
        model="mesmer",
        nuclear_channel=0,
        cytoplasm_channel=4,
        image_resolution=0.5,
    ),

    # 3. Quantification -> AnnData on slide.counts
    QuantifyMIF(segmentation_mask="cell_segmentation"),
])

vectra_slide.run(vectra_pipeline)
```

## Downstream Analysis

### Cell Type Annotation

Annotate cells based on marker expression:

```python
import anndata as ad
import numpy as np

# Load quantified data
adata = ad.read_h5ad('codex_dataset.h5ad')

# Define cell types by marker thresholds
def annotate_cell_types(adata, thresholds):
    cell_types = np.full(adata.n_obs, 'Unknown', dtype=object)

    # T cells: CD3+
    cd3_pos = adata[:, 'CD3'].X.flatten() > thresholds['CD3']
    cell_types[cd3_pos] = 'T cell'

    # CD4 T cells: CD3+ CD4+ CD8-
    cd4_tcells = (
        (adata[:, 'CD3'].X.flatten() > thresholds['CD3']) &
        (adata[:, 'CD4'].X.flatten() > thresholds['CD4']) &
        (adata[:, 'CD8'].X.flatten() < thresholds['CD8'])
    )
    cell_types[cd4_tcells] = 'CD4 T cell'

    # CD8 T cells: CD3+ CD8+ CD4-
    cd8_tcells = (
        (adata[:, 'CD3'].X.flatten() > thresholds['CD3']) &
        (adata[:, 'CD8'].X.flatten() > thresholds['CD8']) &
        (adata[:, 'CD4'].X.flatten() < thresholds['CD4'])
    )
    cell_types[cd8_tcells] = 'CD8 T cell'

    # B cells: CD20+
    b_cells = adata[:, 'CD20'].X.flatten() > thresholds['CD20']
    cell_types[b_cells] = 'B cell'

    # Macrophages: CD68+
    macrophages = adata[:, 'CD68'].X.flatten() > thresholds['CD68']
    cell_types[macrophages] = 'Macrophage'

    # Tumor cells: panCK+
    tumor = adata[:, 'panCK'].X.flatten() > thresholds['panCK']
    cell_types[tumor] = 'Tumor'

    return cell_types

# Apply annotation
thresholds = {
    'CD3': 0.5,
    'CD4': 0.4,
    'CD8': 0.4,
    'CD20': 0.3,
    'CD68': 0.3,
    'panCK': 0.5
}

adata.obs['cell_type'] = annotate_cell_types(adata, thresholds)

# Visualize cell type composition
import matplotlib.pyplot as plt
cell_type_counts = adata.obs['cell_type'].value_counts()
plt.figure(figsize=(10, 6))
cell_type_counts.plot(kind='bar')
plt.xlabel('Cell Type')
plt.ylabel('Count')
plt.title('Cell Type Composition')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

### Clustering

Unsupervised clustering to identify cell populations:

```python
import scanpy as sc

# Preprocessing for clustering
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)
sc.pp.scale(adata, max_value=10)

# PCA
sc.tl.pca(adata, n_comps=50)

# Neighborhood graph
sc.pp.neighbors(adata, n_neighbors=15, n_pcs=30)

# UMAP embedding
sc.tl.umap(adata)

# Leiden clustering
sc.tl.leiden(adata, resolution=0.5)

# Visualize
sc.pl.umap(adata, color=['leiden', 'CD3', 'CD8', 'CD20', 'panCK'])
```

### Spatial Visualization

Visualize cells in spatial context:

```python
import matplotlib.pyplot as plt

# Spatial scatter plot
fig, ax = plt.subplots(figsize=(15, 15))

# Color by cell type
cell_types = adata.obs['cell_type'].unique()
colors = plt.cm.tab10(np.linspace(0, 1, len(cell_types)))

for i, cell_type in enumerate(cell_types):
    mask = adata.obs['cell_type'] == cell_type
    coords = adata.obsm['spatial'][mask]
    ax.scatter(
        coords[:, 0],
        coords[:, 1],
        c=[colors[i]],
        label=cell_type,
        s=5,
        alpha=0.7
    )

ax.legend(markerscale=2)
ax.set_xlabel('X (pixels)')
ax.set_ylabel('Y (pixels)')
ax.set_title('Spatial Cell Type Distribution')
ax.axis('equal')
plt.tight_layout()
plt.show()
```

### Spatial Neighborhood Analysis

Analyze cell neighborhoods and interactions:

```python
import squidpy as sq

# Calculate spatial neighborhood enrichment
sq.gr.spatial_neighbors(adata, coord_type='generic', spatial_key='spatial')

# Neighborhood enrichment test
sq.gr.nhood_enrichment(adata, cluster_key='cell_type')

# Visualize interaction matrix
sq.pl.nhood_enrichment(adata, cluster_key='cell_type')

# Co-occurrence score
sq.gr.co_occurrence(adata, cluster_key='cell_type')
sq.pl.co_occurrence(
    adata,
    cluster_key='cell_type',
    clusters=['CD8 T cell', 'Tumor'],
    figsize=(8, 8)
)
```

### Spatial Autocorrelation

Test for spatial clustering of markers:

```python
# Moran's I spatial autocorrelation
sq.gr.spatial_autocorr(
    adata,
    mode='moran',
    genes=['CD3', 'CD8', 'PD1', 'PDL1', 'panCK']
)

# Visualize
results = adata.uns['moranI']
print(results.head())
```

## MERFISH and Other Platforms

PathML's most fully supported multiparametric workflows are CODEX and Vectra. MERFISH and related spatial-transcriptomics platforms do not have dedicated decoding/transcript-assignment transforms in the core `pathml.preprocessing` API at the time of writing, so do NOT assume classes like `MERFISHSlide`, `DecodeMERFISH`, or `AssignTranscripts` exist — verify against your installed version's API docs first.

A practical pattern for MERFISH-style data:
- Load the multi-channel image as a `MultiparametricSlide` (Bio-Formats backend).
- Segment cells with `SegmentMIF` (Mesmer) on the nuclear + a boundary channel (e.g. poly(T)).
- For barcode decoding and transcript-to-cell assignment, use a dedicated spatial-transcriptomics toolkit (e.g. a vendor pipeline or `squidpy`/`starfish`) and bring the resulting cell-by-gene matrix back into AnnData for downstream analysis.

## Quality Control

### Segmentation Quality

Inspect the instance segmentation mask directly with scikit-image (no PathML-specific QC helper is needed):

```python
import numpy as np
import matplotlib.pyplot as plt
from skimage.measure import regionprops

# segmentation_mask: integer label image (each cell a unique id)
props = regionprops(segmentation_mask)
cell_sizes = np.array([p.area for p in props])

print(f"Total cells: {len(cell_sizes)}")
print(f"Mean cell size: {cell_sizes.mean():.1f} pixels")

plt.hist(cell_sizes, bins=50)
plt.xlabel("Cell Size (pixels)")
plt.ylabel("Frequency")
plt.title("Cell Size Distribution")
plt.show()
```

### Marker Expression QC

```python
import scanpy as sc

# Load AnnData
adata = ad.read_h5ad('codex_dataset.h5ad')

# Calculate QC metrics
adata.obs['total_intensity'] = adata.X.sum(axis=1)
adata.obs['n_markers_detected'] = (adata.X > 0).sum(axis=1)

# Filter low-quality cells
adata = adata[adata.obs['total_intensity'] > 100, :]
adata = adata[adata.obs['n_markers_detected'] >= 3, :]

# Visualize
sc.pl.violin(adata, ['total_intensity', 'n_markers_detected'], multi_panel=True)
```

## Batch Processing

Process large multiparametric datasets efficiently:

```python
from pathml.core import SlideDataset
from pathml.preprocessing import Pipeline
from dask.distributed import Client
import glob

# Start Dask cluster
client = Client(n_workers=16, threads_per_worker=2, memory_limit='8GB')

# Find all CODEX slides
slide_dirs = glob.glob('data/codex_slides/*/')

# Create dataset
codex_slides = [CODEXSlide(d, stain='IF') for d in slide_dirs]
dataset = SlideDataset(codex_slides)

# Run pipeline in parallel (pass the Dask client to run())
dataset.run(codex_pipeline, client=client)

# Save the per-slide AnnData (each on slide.counts)
for i, slide in enumerate(dataset.slides):
    slide.counts.write(f"processed/slide_{i}.h5ad")

client.close()
```

## Integration with Other Tools

### Export to Spatial Analysis Tools

```python
# Export to Giotto
def export_to_giotto(adata, output_dir):
    import os
    os.makedirs(output_dir, exist_ok=True)

    # Expression matrix
    pd.DataFrame(
        adata.X.T,
        index=adata.var_names,
        columns=adata.obs_names
    ).to_csv(f'{output_dir}/expression.csv')

    # Cell coordinates
    pd.DataFrame(
        adata.obsm['spatial'],
        columns=['x', 'y'],
        index=adata.obs_names
    ).to_csv(f'{output_dir}/spatial_locs.csv')

# Export to Seurat
def export_to_seurat(adata, output_file):
    adata.write_h5ad(output_file)
    # Read in R with: library(Seurat); ReadH5AD(output_file)
```

## Best Practices

1. **Channel selection for segmentation:**
   - Use brightest, most consistent nuclear marker (usually DAPI)
   - Choose membrane/cytoplasm marker based on tissue type
   - Test multiple options to optimize segmentation

2. **Background subtraction:**
   - Apply before quantification to reduce autofluorescence
   - Use blank/control images to model background

3. **Quality control:**
   - Visualize segmentation on sample regions
   - Check cell size distributions for outliers
   - Validate marker expression ranges

4. **Cell type annotation:**
   - Start with canonical markers (CD3, CD20, panCK)
   - Use multiple markers for robust classification
   - Consider unsupervised clustering to discover populations

5. **Spatial analysis:**
   - Account for tissue architecture (epithelium, stroma, etc.)
   - Consider local density when interpreting interactions
   - Use permutation tests for statistical significance

6. **Batch effects:**
   - Include batch information in AnnData.obs
   - Apply batch correction if combining multiple experiments
   - Visualize batch effects with UMAP colored by batch

## Common Issues and Solutions

**Issue: Poor segmentation quality**
- Verify nuclear and cytoplasm channels are correctly specified
- Adjust image_resolution parameter to match actual resolution
- Try different cytoplasm markers
- Manually tune min/max cell size parameters

**Issue: Low marker intensity**
- Check for background subtraction artifacts
- Verify channel names match actual channels
- Inspect raw images for technical issues (focus, exposure)

**Issue: Cell type annotations don't match expectations**
- Adjust marker thresholds (too high/low)
- Visualize marker distributions to set data-driven thresholds
- Check for antibody specificity issues

**Issue: Spatial analysis shows no significant interactions**
- Increase neighborhood radius
- Check for sufficient cell numbers per type
- Verify spatial coordinates are correctly scaled

## Additional Resources

- **PathML Multiparametric API:** https://pathml.readthedocs.io/en/latest/api_preprocessing_reference.html
- **CODEX:** https://www.akoyabio.com/codex/
- **Vectra:** https://www.akoyabio.com/phenoimager/instruments/vectra-3-0/
- **DeepCell Mesmer:** https://www.deepcell.org/
- **Scanpy:** https://scanpy.readthedocs.io/ (single-cell analysis)
- **Squidpy:** https://squidpy.readthedocs.io/ (spatial omics analysis)
