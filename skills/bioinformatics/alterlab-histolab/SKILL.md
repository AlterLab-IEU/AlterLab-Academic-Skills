---
name: alterlab-histolab
description: Extract and preprocess tiles from whole-slide images (WSI) with histolab — OpenSlide-backed slide loading, tissue detection and masks, Random/Grid/Score tile extraction, and image/morphological filters for H&E preprocessing. Use when the user needs lightweight WSI slide preprocessing — building tile datasets for ML training, tissue segmentation, or quick tile-based inspection of histopathology slides. For end-to-end computational-pathology, deep-learning model training, nucleus segmentation, or multiplexed/spatial-proteomics (CODEX, Vectra) pipelines prefer alterlab-pathml instead. Part of the AlterLab Academic Skills suite.
license: Apache-2.0
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*)
compatibility: "Runs under `uv run python` with histolab 0.7.0 (still the latest release, Feb 2024) in a **dedicated environment**: it requires Python >= 3.8, < 3.12 and pins numpy <= 1.24.4, scipy < 1.10.1, scikit-image < 0.19.4 and openslide-python 1.3.1 — it will not co-install with a modern numpy 2.x / Python 3.12+ stack. The OpenSlide C library must also be present (`uv pip install openslide-bin`, or `brew install openslide` / `apt install libopenslide0`). No API key or account required."
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# Histolab

## Overview

Histolab is a Python library for processing whole slide images (WSI) in digital pathology. It automates tissue detection, extracts informative tiles from gigapixel images, and prepares datasets for deep learning pipelines. The library handles multiple WSI formats, implements sophisticated tissue segmentation, and provides flexible tile extraction strategies.

## When to Use This Skill

Use histolab for lightweight WSI tile pipelines: tissue detection, building tile datasets for ML training, H&E stain handling, and quick tile-based analysis of histopathology slides. For advanced spatial proteomics, multiplexed imaging, or full deep-learning pathology pipelines, use `alterlab-pathml` instead.

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| End-to-end computational pathology, nucleus segmentation, multiplexed imaging (CODEX/Vectra) | `alterlab-pathml` |
| Training the downstream classifier on the extracted tiles | `alterlab-pytorch-lightning` |
| DICOM whole-slide or radiology images rather than SVS/NDPI | `alterlab-pydicom`, `alterlab-imaging-data-commons` |
| Spatial transcriptomics on tissue sections | `alterlab-squidpy-spatial` |
| Managing/versioning the slide collection itself | `alterlab-omero`, `alterlab-lamindb` |

## Installation

```bash
# histolab 0.7.0 needs Python >= 3.8, < 3.12 and numpy 1.x — give it its own env
uv venv --python 3.11 .venv-histolab
uv pip install --python .venv-histolab "histolab==0.7.0" openslide-bin
```

Two constraints that bite in a 2026 toolchain:

1. **Pinned scientific stack.** 0.7.0 (Feb 2024, still the latest release) requires
   `numpy <= 1.24.4`, `scipy < 1.10.1`, `scikit-image < 0.19.4` and
   `openslide-python 1.3.1`. It cannot share an environment with a numpy 2.x / Python
   3.12+ project — resolve this with a separate venv rather than by loosening pins.
2. **OpenSlide is a C library**, not bundled with the wheel. The simplest fix is the
   `openslide-bin` wheel (prebuilt binaries); otherwise `brew install openslide` on macOS
   or `apt install libopenslide0` on Debian/Ubuntu. Without it, `import histolab.slide`
   fails with `Couldn't locate OpenSlide dylib`.

The examples below target histolab 0.7.0; the API differs in older releases.

## Core Workflow

1. **Load** the slide with `Slide(path, processed_path=...)` and inspect dimensions/levels.
2. **Detect tissue** with a mask (`TissueMask` or `BiggestTissueBoxMask`).
3. **Preview** tile locations with `tiler.locate_tiles(slide)` before committing.
4. **Extract** tiles with one of three tilers (Random/Grid/Score).

Minimal example:

```python
from histolab.slide import Slide
from histolab.tiler import RandomTiler

slide = Slide("slide.svs", processed_path="output/")
# n_tiles, level, seed are CONSTRUCTOR args — not args to locate_tiles/extract.
tiler = RandomTiler(tile_size=(512, 512), n_tiles=100, level=0, seed=42)
tiler.locate_tiles(slide)   # preview locations on the thumbnail first
tiler.extract(slide)        # writes PNGs into processed_path
```

**API gotcha (histolab 0.7.0):** `locate_tiles()` and `extract()` take only
`slide`, an optional `extraction_mask`, and logging/styling kwargs — they do
**not** accept `n_tiles`. Set `n_tiles` (and `seed`, `level`, `tile_size`,
`check_tissue`, `tissue_percent`) on the tiler constructor. The
`extraction_mask` is passed to `extract()`/`locate_tiles()`, never to the
constructor.

Full copy-pasteable pipelines (quick start, 5 end-to-end workflows, and per-capability examples) live in `references/workflows.md`.

## Core Capabilities

### 1. Slide Management

Load, inspect, and work with WSI files (SVS, TIFF, NDPI, etc.): access metadata
(dimensions, magnification, properties), generate thumbnails, and work with
pyramidal/multi-level structures. Key class: `Slide`.

See `references/slide_management.md` for slide initialization, built-in sample
datasets (`prostate_tissue`, `ovarian_tissue`, `breast_tissue`, `heart_tissue`,
`aorta_tissue`, plus pen-marked and IHC samples), pyramid levels, and
multi-slide processing.

### 2. Tissue Detection and Masks

Automatically identify tissue regions and filter background/artifacts. Key
classes: `TissueMask` (all tissue regions), `BiggestTissueBoxMask` (bounding box
of largest region — the default), and `BinaryMask` (base class for custom masks).

Choosing a mask:
- `TissueMask`: multiple tissue sections, comprehensive analysis
- `BiggestTissueBoxMask`: single main section, exclude artifacts (default)
- Custom `BinaryMask`: specific ROI, exclude annotations, custom segmentation

See `references/tissue_masks.md` for how detection filters work, visualizing
masks with `locate_mask()`, and custom rectangular / annotation-exclusion masks.

### 3. Tile Extraction

Extract smaller regions from large WSI using one of three strategies:

- **RandomTiler** — fixed number of randomly positioned tiles. Best for sampling
  diverse regions, exploration, training data. Key params: `n_tiles`, `seed`.
- **GridTiler** — systematic grid across tissue. Best for complete coverage,
  spatial analysis, reconstruction. Key param: `pixel_overlap`.
- **ScoreTiler** — top-ranked tiles by scoring function. Best for informative
  regions, quality-driven selection. Key param: `scorer` (NucleiScorer,
  CellularityScorer, custom).

Common parameters: `tile_size`, `level` (0 = highest res), `check_tissue`,
`tissue_percent` (default 80%), `extraction_mask`. **Always preview with
`locate_tiles()` before extracting.**

See `references/tile_extraction.md` for scorers, reporting, and advanced
(multi-level, hierarchical) extraction patterns.

### 4. Filters and Preprocessing

Apply image-processing filters for tissue detection, QC, and preprocessing:
- **Image filters** — `RgbToGrayscale`, `RgbToHsv`, `RgbToHed`, `OtsuThreshold`,
  `Invert`, `StretchContrast`, `HistogramEqualization`, `Lambda`.
- **Morphological filters** — `BinaryDilation`, `BinaryErosion`, `BinaryOpening`,
  `BinaryClosing`, `RemoveSmallObjects`, `RemoveSmallHoles`.
- **Composition** — `Compose` (in `histolab.filters.image_filters`) chains
  filters into pipelines. Pass custom filters to a mask as positional varargs:
  `TissueMask(RgbToGrayscale(), OtsuThreshold(), ...)`.

See `references/filters_preprocessing.md` for filter chaining, common pipelines
(tissue detection, pen removal, nuclei enhancement), and QC filters.

### 5. Visualization

Display slides, masks, tile locations, and extraction quality: thumbnails, mask
overlays via `locate_mask()`, tile-location previews via `locate_tiles()`, tile
mosaics, and score distributions.

See `references/visualization.md` for mosaics, quality-assessment plots,
multi-slide comparison, and exporting high-resolution figures / PDF reports.

## Reference Index

- `references/workflows.md` — quick start, per-capability examples, and 5
  end-to-end worked workflows (exploratory, grid, score-driven, multi-slide,
  custom tissue detection).
- `references/slide_management.md` — loading/inspecting slides, sample datasets,
  pyramid levels, multi-slide processing.
- `references/tissue_masks.md` — `TissueMask`/`BiggestTissueBoxMask`/`BinaryMask`,
  custom masks, mask visualization and integration.
- `references/tile_extraction.md` — Random/Grid/Score tiler comparison, scorers,
  CSV reporting, advanced extraction patterns.
- `references/filters_preprocessing.md` — image + morphological filters, filter
  composition, preprocessing pipelines, QC filters.
- `references/visualization.md` — thumbnails, mask/tile previews, mosaics,
  quality plots, figure export.
- `references/best_practices.md` — best practices, common use cases, and
  troubleshooting (no tiles, background tiles, slow extraction, artifacts).

Load the specific reference file you need for detailed implementation guidance,
troubleshooting, or advanced features.

Part of the AlterLab Academic Skills suite.
