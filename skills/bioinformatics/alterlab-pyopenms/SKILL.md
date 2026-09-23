---
name: alterlab-pyopenms
description: Build complete mass-spectrometry workflows with pyOpenMS — feature detection, peptide identification, protein quantification, and full LC-MS/MS pipelines across many MS file formats (mzML, mzXML) and algorithms. Use for comprehensive proteomics and MS data processing — for simple spectral comparison and metabolite identification use matchms. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*)
compatibility: "Self-contained — runs under `uv run python` with the skill's Python package installed; no API key or account required. Written for pyOpenMS 3.x (current 3.5.0 as of 2026-09); wheels ship the compiled OpenMS library, so no separate OpenMS install is needed."
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    last_updated: "2026-09-23"
---

# PyOpenMS

## Overview

PyOpenMS provides Python bindings to the OpenMS library for computational mass spectrometry, enabling analysis of proteomics and metabolomics data. Use for handling mass spectrometry file formats, processing spectral data, detecting features, identifying peptides/proteins, and performing quantitative analysis.

## Installation

Install using uv (pyOpenMS 3.x — examples here are verified against 3.5):

```bash
uv pip install "pyopenms>=3.4"
```

Verify installation:

```python
import pyopenms
print(pyopenms.__version__)
```

> Version note: pyOpenMS 3.x removed the old `FeatureFinder` facade. Use
> `FeatureFinderAlgorithmPicked` (the former `"centroided"` algorithm) or, for
> metabolomics, the `MassTraceDetection` → `ElutionPeakDetection` →
> `FeatureFindingMetabo` chain. See `references/feature_detection.md`.

## When to Use This Skill

Use this skill when the user wants to:
- Read, convert, or inspect MS file formats (mzML, mzXML, idXML, featureXML, consensusXML, mzTab).
- Process raw spectra — smoothing, baseline removal, centroiding/peak picking, normalization.
- Run **feature detection** and label-free quantification on LC-MS runs.
- Do **peptide/protein identification** and FDR control (search-engine adapters, PeptideIndexer,
  FalseDiscoveryRate) or build a full LC-MS/MS pipeline.
- Do untargeted **metabolomics** feature finding (MassTraceDetection -> ElutionPeakDetection ->
  FeatureFindingMetabo) and adduct/formula work.
- Drive OpenMS algorithms programmatically with `Param` objects instead of TOPP command lines.

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Spectral similarity scoring / library matching of small-molecule MS/MS | `alterlab-matchms` |
| Cheminformatics on the identified molecules (descriptors, substructures, SMILES) | `alterlab-rdkit` |
| Statistics on an already-quantified abundance matrix (tests, PCA, clustering) | `alterlab-statistical-analysis` |
| Protein sequence/structure work rather than the mass spectra | `alterlab-biopython` or `alterlab-alphafold` |
| Transcript quantification from RNA-seq reads | `alterlab-rnaseq-quant` |

## Core Capabilities

PyOpenMS organizes functionality into these domains:

### 1. File I/O and Data Formats

Handle mass spectrometry file formats and convert between representations.

**Supported formats**: mzML, mzXML, TraML, mzTab, FASTA, pepXML, protXML, mzIdentML, featureXML, consensusXML, idXML

Basic file reading:

```python
import pyopenms as ms

# Read mzML file
exp = ms.MSExperiment()
ms.MzMLFile().load("data.mzML", exp)

# Access spectra
for spectrum in exp:
    mz, intensity = spectrum.get_peaks()
    print(f"Spectrum: {len(mz)} peaks")
```

**For detailed file handling**: See `references/file_io.md`

### 2. Signal Processing

Process raw spectral data with smoothing, filtering, centroiding, and normalization.

Basic spectrum processing:

```python
# Smooth spectrum with Gaussian filter
gaussian = ms.GaussFilter()
params = gaussian.getParameters()
params.setValue("gaussian_width", 0.1)
gaussian.setParameters(params)
gaussian.filterExperiment(exp)
```

**For algorithm details**: See `references/signal_processing.md`

### 3. Feature Detection

Detect and link features across spectra and samples for quantitative analysis.

```python
# Detect features in centroided data (pyOpenMS 3.x API)
ff = ms.FeatureFinderAlgorithmPicked()
params = ff.getParameters()          # defaults for the "centroided" algorithm
ff.setParameters(params)

features = ms.FeatureMap()
seeds = ms.FeatureMap()              # empty seeds = detect de novo
ff.run(exp, features, params, seeds)
```

**For complete workflows**: See `references/feature_detection.md`

### 4. Peptide and Protein Identification

Integrate with search engines and process identification results.

**Supported engines**: Comet, Mascot, MSGFPlus, XTandem, OMSSA, Myrimatch

Basic identification workflow:

```python
# Load identification data.
# pyOpenMS 3.x: protein_ids is a plain list, peptide_ids MUST be a
# PeptideIdentificationList (a plain [] is rejected by load()).
protein_ids = []
peptide_ids = ms.PeptideIdentificationList()
ms.IdXMLFile().load("identifications.idXML", protein_ids, peptide_ids)

# Compute q-values (target-decoy FDR), then filter at 1%.
# fdr.apply() requires target/decoy hits annotated with a 'target_decoy'
# meta value (run PeptideIndexer on a concatenated target-decoy search first).
fdr = ms.FalseDiscoveryRate()
fdr.apply(peptide_ids)               # rewrites scores to q-values (lower = better)
ms.IDFilter().filterHitsByScore(peptide_ids, 0.01)
ms.IDFilter().removeEmptyIdentifications(peptide_ids)
```

**For detailed workflows**: See `references/identification.md`

### 5. Metabolomics Analysis

Perform untargeted metabolomics preprocessing and analysis.

Typical workflow:
1. Load and process raw data
2. Detect features
3. Align retention times across samples
4. Link features to consensus map
5. Annotate with compound databases

**For complete metabolomics workflows**: See `references/metabolomics.md`

## Data Structures

PyOpenMS uses these primary objects:

- **MSExperiment**: Collection of spectra and chromatograms
- **MSSpectrum**: Single mass spectrum with m/z and intensity pairs
- **MSChromatogram**: Chromatographic trace
- **Feature**: Detected chromatographic peak with quality metrics
- **FeatureMap**: Collection of features
- **PeptideIdentification**: Search results for peptides
- **ProteinIdentification**: Search results for proteins

**For detailed documentation**: See `references/data_structures.md`

## Common Workflows

### Quick Start: Load and Explore Data

```python
import pyopenms as ms

# Load mzML file
exp = ms.MSExperiment()
ms.MzMLFile().load("sample.mzML", exp)

# Get basic statistics
print(f"Number of spectra: {exp.getNrSpectra()}")
print(f"Number of chromatograms: {exp.getNrChromatograms()}")

# Examine first spectrum
spec = exp.getSpectrum(0)
print(f"MS level: {spec.getMSLevel()}")
print(f"Retention time: {spec.getRT()}")
mz, intensity = spec.get_peaks()
print(f"Peaks: {len(mz)}")
```

### Parameter Management

Most algorithms use a parameter system:

```python
# Get algorithm parameters
algo = ms.GaussFilter()
params = algo.getParameters()

# View available parameters
for param in params.keys():
    print(f"{param}: {params.getValue(param)}")

# Modify parameters
params.setValue("gaussian_width", 0.2)
algo.setParameters(params)
```

### Export to Pandas

Convert data to pandas DataFrames for analysis:

```python
import pyopenms as ms
import pandas as pd

# Load feature map
fm = ms.FeatureMap()
ms.FeatureXMLFile().load("features.featureXML", fm)

# Convert to DataFrame
df = fm.get_df()
print(df.head())
```

## Integration with Other Tools

PyOpenMS integrates with:
- **Pandas**: Export data to DataFrames
- **NumPy**: Work with peak arrays
- **Scikit-learn**: Machine learning on MS data
- **Matplotlib/Seaborn**: Visualization
- **R**: Via rpy2 bridge

## Resources

- **Official documentation**: https://pyopenms.readthedocs.io
- **OpenMS documentation**: https://www.openms.org
- **GitHub**: https://github.com/OpenMS/OpenMS

## References

- `references/file_io.md` - Comprehensive file format handling
- `references/signal_processing.md` - Signal processing algorithms
- `references/feature_detection.md` - Feature detection and linking
- `references/identification.md` - Peptide and protein identification
- `references/metabolomics.md` - Metabolomics-specific workflows
- `references/data_structures.md` - Core objects and data structures

