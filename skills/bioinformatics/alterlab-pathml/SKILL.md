---
name: alterlab-pathml
description: Run full computational-pathology workflows with PathML — whole-slide-image (WSI) analysis across 160+ slide formats, multiplexed immunofluorescence (CODEX, Vectra, MERFISH), nucleus segmentation/classification (HoVer-Net, HACTNet), tissue- and cell-graph construction, HDF5 dataset management, and deep-learning model training on pathology data. Use when the user builds end-to-end deep-learning pathology pipelines, analyzes multiplexed or spatial-proteomics slides, or segments nuclei. For lightweight H&E slide preprocessing, tissue masking, or plain Random/Grid/Score tile extraction prefer alterlab-histolab instead. Part of the AlterLab Academic Skills suite.
license: GPL-2.0
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*)
compatibility: "Runs under `uv run python`, but not in a shared environment: PathML 3.0.x (current 3.0.8, released 2026-08) hard-pins an older scientific stack (numpy<2, pandas<=2.1.4, scanpy==1.9.6, anndata<=0.10.3, torch==2.12.0) and needs native OpenSlide plus a JDK for Bio-Formats. Give it a dedicated environment. No API key or account required."
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# PathML

## Overview

PathML is a comprehensive Python toolkit for computational pathology workflows, designed to facilitate machine learning and image analysis for whole-slide pathology images. The framework provides modular, composable tools for loading diverse slide formats, preprocessing images, constructing spatial graphs, training deep learning models, and analyzing multiparametric imaging data from technologies like CODEX and multiplex immunofluorescence.

## When to Use This Skill

Apply this skill for:
- Loading and processing whole-slide images (WSI) in various proprietary formats
- Preprocessing H&E stained tissue images with stain normalization
- Nucleus detection, segmentation, and classification workflows
- Building cell and tissue graphs for spatial analysis
- Training or deploying machine learning models (HoVer-Net, HACTNet) on pathology data
- Analyzing multiparametric imaging (CODEX, Vectra, MERFISH) for spatial proteomics
- Quantifying marker expression from multiplex immunofluorescence
- Managing large-scale pathology datasets with HDF5 storage
- Tile-based analysis and stitching operations

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Lightweight H&E preprocessing, tissue masking, Random/Grid/Score tile extraction | `alterlab-histolab` |
| Spatial transcriptomics neighborhood stats on Visium/Xenium/MERFISH tables | `alterlab-squidpy-spatial` |
| Single-cell expression analysis of the resulting cell x marker matrix | `alterlab-scanpy` |
| Training a general vision model with no pathology-specific I/O or transforms | `alterlab-pytorch-lightning` |
| Graph neural networks on a graph you already built | `alterlab-torch-geometric` |

## Core Capabilities

PathML provides six major capability areas documented in detail within reference files:

### 1. Image Loading & Formats

Load whole-slide images from 160+ proprietary formats including Aperio SVS, Hamamatsu NDPI, Leica SCN, Zeiss ZVI, DICOM, and OME-TIFF. PathML automatically handles vendor-specific formats and provides unified interfaces for accessing image pyramids, metadata, and regions of interest.

**See:** `references/image_loading.md` for supported formats, loading strategies, and working with different slide types.

### 2. Preprocessing Pipelines

Build modular preprocessing pipelines by composing transforms for image manipulation, quality control, stain normalization, tissue detection, and mask operations. PathML's Pipeline architecture enables reproducible, scalable preprocessing across large datasets.

**Key transforms:**
- `StainNormalizationHE` - Macenko/Vahadane stain normalization
- `TissueDetectionHE`, `NucleusDetectionHE` - Tissue/nucleus segmentation
- `MedianBlur`, `GaussianBlur` - Noise reduction
- `LabelArtifactTileHE` - Quality control for artifacts

**See:** `references/preprocessing.md` for complete transform catalog, pipeline construction, and preprocessing workflows.

### 3. Graph Construction

Construct spatial graphs representing cellular and tissue-level relationships. Extract features from segmented objects to create graph-based representations suitable for graph neural networks and spatial analysis.

**See:** `references/graphs.md` for graph construction methods, feature extraction, and spatial analysis workflows.

### 4. Machine Learning

Train and deploy deep learning models for nucleus detection, segmentation, and classification. PathML integrates PyTorch with pre-built models (HoVer-Net, HACTNet), custom DataLoaders, and ONNX support for inference.

**Key models:**
- **HoVer-Net** - Simultaneous nucleus segmentation and classification
- **HACTNet** - Hierarchical cell-type classification

**See:** `references/machine_learning.md` for model training, evaluation, inference workflows, and working with public datasets.

### 5. Multiparametric Imaging

Analyze spatial proteomics and gene expression data from CODEX, Vectra, MERFISH, and other multiplex imaging platforms. PathML provides specialized slide classes and transforms for processing multiparametric data, cell segmentation with Mesmer, and quantification workflows.

**See:** `references/multiparametric.md` for CODEX/Vectra workflows, cell segmentation, marker quantification, and integration with AnnData.

### 6. Data Management

Efficiently store and manage large pathology datasets using HDF5 format. PathML handles tiles, masks, metadata, and extracted features in unified storage structures optimized for machine learning workflows.

**See:** `references/data_management.md` for HDF5 integration, tile management, dataset organization, and batch processing strategies.

## Quick Start

### Installation

PathML needs native dependencies present first — **OpenSlide** and a **JDK** (Bio-Formats is
driven through JPype/javabridge) — so the maintainers recommend a conda environment; pure-pip
installs commonly fail on those native deps.

Give PathML its own environment, because 3.0.8 pins much of the scientific stack to exact or
upper-bounded versions:

| Pinned by PathML 3.0.8 | Current elsewhere |
|---|---|
| `numpy<2` | 2.5.x |
| `pandas<=2.1.4` | 3.0.x |
| `scanpy==1.9.6`, `anndata<=0.10.3` | scanpy 1.12.x, anndata 0.13.x |
| `scikit-image<=0.22.0`, `networkx<=3.2.1`, `h5py==3.10.0` | all newer |
| `torch==2.12.0`, `torch-geometric==2.8.0` | torch 2.14.x |

Installing PathML next to `alterlab-scanpy` or `alterlab-squidpy-spatial` will either fail to
resolve or silently downgrade those skills' stack. Move results between environments as files
(HDF5/AnnData written by PathML, read by a current-scanpy env) rather than trying to satisfy
both pin sets.

```bash
# In a dedicated env, with OpenSlide and a JDK already installed.
uv venv .venv-pathml && source .venv-pathml/bin/activate
uv pip install pathml
```

### Basic Workflow Example

```python
from pathml.core import HESlide
from pathml.preprocessing import Pipeline, StainNormalizationHE, TissueDetectionHE

# Load a whole-slide image. Use the HESlide convenience class for H&E,
# or SlideData(filepath=..., slide_type=types.HE) for the generic constructor.
# (There is no SlideData.from_slide.)
wsi = HESlide("path/to/slide.svs", name="example")

# Create preprocessing pipeline
pipeline = Pipeline([
    TissueDetectionHE(),
    StainNormalizationHE(target="normalize", stain_estimation_method="macenko"),
])

# Run the pipeline on the slide (SlideData.run handles tiling + transforms)
wsi.run(pipeline)

# Access processed tiles
for tile in wsi.tiles:
    processed_image = tile.image
    tissue_mask = tile.masks["tissue"]
```

### Common Workflows

**H&E Image Analysis:**
1. Load WSI with appropriate slide class
2. Apply tissue detection and stain normalization
3. Perform nucleus detection or train segmentation models
4. Extract features and build spatial graphs
5. Conduct downstream analysis

**Multiparametric Imaging (CODEX):**
1. Load CODEX slide with `CODEXSlide`
2. Collapse multi-run channel data with `CollapseRunsCODEX`
3. Segment cells using `SegmentMIF` (Mesmer)
4. Quantify per-cell marker expression with `QuantifyMIF`
5. Read the resulting AnnData from `slide.counts` for single-cell analysis

**Training ML Models:**
1. Prepare data with a `pathml.datasets` DataModule (e.g. `PanNukeDataModule`) or a `TileDataset`
2. Train `HoVerNet` (or another model) with a standard PyTorch loop
3. Post-process predictions with `post_process_batch_hovernet`
4. Evaluate on held-out test sets
5. Optionally export to ONNX for inference

## Reference Files

Load the relevant reference for detailed API, workflows, and gotchas:

- `references/image_loading.md` - WSI formats, slide classes, loading strategies
- `references/preprocessing.md` - transform catalog, pipeline construction, stain normalization
- `references/graphs.md` - graph builders, feature extraction, spatial analysis
- `references/machine_learning.md` - HoVer-Net/HACTNet, training, datasets, ONNX inference
- `references/multiparametric.md` - CODEX/Vectra/multiplex IF, cell segmentation, quantification
- `references/data_management.md` - h5path storage, tile management, batch processing

PathML's API surface shifts between releases; treat the reference code as workflow scaffolding and confirm exact class/method names against the version you have installed (`python -c "import pathml; print(pathml.__version__)"`) and the official API docs at https://pathml.readthedocs.io/.

