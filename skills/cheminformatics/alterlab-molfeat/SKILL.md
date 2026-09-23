---
name: alterlab-molfeat
description: Featurizes molecules for machine learning with molfeat — ECFP/MACCS/MAP4 fingerprints, RDKit and Mordred physicochemical descriptors, pharmacophore and shape descriptors, and pretrained embeddings (ChemBERTa, ChemGPT, CheMeleon) exposed as scikit-learn transformers that convert SMILES into feature vectors. Use when turning molecules into ML-ready feature matrices for QSAR/QSPR or virtual screening, or benchmarking fingerprint against descriptor and embedding representations; for training models and MoleculeNet benchmarks on those features prefer alterlab-deepchem, and for low-level fingerprint or descriptor primitives prefer alterlab-rdkit. Part of the AlterLab Academic Skills suite.
license: Apache-2.0
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*)
compatibility: "Self-contained — runs under `uv run python` with the skill's Python package installed; no API key or account required."
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# Molfeat - Molecular Featurization Hub

## Overview

Molfeat is a comprehensive Python library for molecular featurization that unifies 100+ pre-trained embeddings and hand-crafted featurizers. Convert chemical structures (SMILES strings or RDKit molecules) into numerical representations for machine learning tasks including QSAR modeling, virtual screening, similarity searching, and deep learning applications. Features fast parallel processing, scikit-learn compatible transformers, and built-in caching.

## When to Use This Skill

This skill should be used when working with:
- **Molecular machine learning**: Building QSAR/QSPR models, property prediction
- **Virtual screening**: Ranking compound libraries for biological activity
- **Similarity searching**: Finding structurally similar molecules
- **Chemical space analysis**: Clustering, visualization, dimensionality reduction
- **Deep learning**: Training neural networks on molecular data
- **Featurization pipelines**: Converting SMILES to ML-ready representations
- **Cheminformatics**: Any task requiring molecular feature extraction

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Training/evaluating models end-to-end on MoleculeNet benchmarks with built-in loaders and GNNs | `alterlab-deepchem` |
| Sourcing a labeled benchmark dataset with scaffold/cold splits | `alterlab-pytdc` |
| Low-level fingerprint or descriptor primitives, custom sanitization, SMARTS | `alterlab-rdkit` |
| Standardizing and cleaning molecule tables before featurization | `alterlab-datamol` |

## Installation

```bash
uv pip install molfeat            # molfeat 1.0.0 (current as of 2026-09); Python >= 3.11, pulls torch + datamol

# Optional extras (molfeat 1.x)
uv pip install "molfeat[transformer]"   # Hugging Face models: ChemBERTa, ChemGPT, MolT5, ...
uv pip install "molfeat[mordred]"       # Mordred descriptors (mordredcommunity)
uv pip install "molfeat[fcd]"           # FCD / ChemNet embeddings
uv pip install "molfeat[pyg]"           # PyTorch Geometric (used by Mol-JEPA)
uv pip install "molfeat[all]"
```

**molfeat 1.0 breaking changes.** The DGL-based pretrained GNNs (`gin_supervised_*`, `jtvae_zinc_no_kl`), Graphormer, and the protein featurizers were removed, along with the `dgl` and `graphormer` extras (there has never been a `map4` extra); loading those model-store entries now fails. New foundation-model featurizers are `CheMeleonTransformer` (2,048-d, weights fetched from Zenodo and checksum-verified) and `MolJEPATransformer` (CC BY-NC 4.0; requires `trust_remote_code=True` and `accept_noncommercial_license=True`). If you must reproduce legacy GIN/Graphormer embeddings, pin `molfeat<1` (0.11.x requires Python ≤ 3.10) in a separate environment. MAP4 needs the `map4` package from https://github.com/reymond-group/map4 (not on PyPI).

## Core Concepts

Molfeat organizes featurization into three hierarchical classes:

### 1. Calculators (`molfeat.calc`)

Callable objects that convert individual molecules into feature vectors. Accept RDKit `Chem.Mol` objects or SMILES strings.

**Use calculators for:**
- Single molecule featurization
- Custom processing loops
- Direct feature computation

**Example:**
```python
from molfeat.calc import FPCalculator

calc = FPCalculator("ecfp", radius=3, fpSize=2048)
features = calc("CCO")  # Returns numpy array (2048,)
```

### 2. Transformers (`molfeat.trans`)

Scikit-learn compatible transformers that wrap calculators for batch processing with parallelization.

**Use transformers for:**
- Batch featurization of molecular datasets
- Integration with scikit-learn pipelines
- Parallel processing (automatic CPU utilization)

**Example:**
```python
import numpy as np
from molfeat.trans import MoleculeTransformer
from molfeat.calc import FPCalculator

transformer = MoleculeTransformer(FPCalculator("ecfp"), n_jobs=-1, dtype=np.float32)
features = transformer(smiles_list)  # (n_mols, 2048) array; without dtype you get a list of arrays
```

### 3. Pretrained Transformers (`molfeat.trans.pretrained`)

Specialized transformers for deep learning models with batched inference and caching.

**Use pretrained transformers for:**
- State-of-the-art molecular embeddings
- Transfer learning from large chemical datasets
- Deep learning feature extraction

**Example** (`PretrainedMolTransformer` is the abstract base class — instantiate a concrete subclass):
```python
import numpy as np
from molfeat.trans.pretrained import PretrainedHFTransformer

transformer = PretrainedHFTransformer(kind="ChemBERTa-77M-MLM", notation="smiles", dtype=np.float32)
embeddings = transformer(smiles_list)  # (n_mols, 384) mean-pooled embeddings
```

## Quick Start Workflow

### Basic Featurization

```python
import numpy as np
from molfeat.calc import FPCalculator
from molfeat.trans import MoleculeTransformer

# Load molecular data
smiles = ["CCO", "CC(=O)O", "c1ccccc1", "CC(C)O"]

# Create calculator and transformer (dtype makes the output a single array)
calc = FPCalculator("ecfp", radius=3)
transformer = MoleculeTransformer(calc, n_jobs=-1, dtype=np.float32)

# Featurize molecules
features = transformer(smiles)
print(f"Shape: {features.shape}")  # (4, 2048)
```

### Save and Load Configuration

```python
# Save featurizer configuration for reproducibility
transformer.to_state_yaml_file("featurizer_config.yml")

# Reload exact configuration
loaded = MoleculeTransformer.from_state_yaml_file("featurizer_config.yml")
```

### Handle Errors Gracefully

```python
# ignore_errors is an argument of the CALL, not the constructor
# (a constructor kwarg is silently swallowed and the call still raises)
transformer = MoleculeTransformer(calc, n_jobs=-1, dtype=np.float32, verbose=True)

features, valid_ids = transformer(smiles_with_errors, ignore_errors=True)
# features: rows for the molecules that featurized; valid_ids: their input positions
# transformer.transform(smiles_with_errors, ignore_errors=True) instead keeps None placeholders
```

## Choosing the Right Featurizer

### For Traditional Machine Learning (RF, SVM, XGBoost)

**Start with fingerprints:**
```python
# ECFP - Most popular, general-purpose
FPCalculator("ecfp", radius=3, fpSize=2048)

# MACCS - Fast, good for scaffold hopping
FPCalculator("maccs")

# MAP4 - Efficient for large-scale screening (needs the map4 package from GitHub)
FPCalculator("map4")
```

**For interpretable models:**
```python
# RDKit 2D descriptors (200+ named properties)
from molfeat.calc import RDKitDescriptors2D
RDKitDescriptors2D()

# Mordred (1800+ comprehensive descriptors)
from molfeat.calc import MordredDescriptors
MordredDescriptors()
```

**Combine multiple featurizers** (`FeatConcat` takes fingerprint names or `FPVecTransformer` objects, not `FPCalculator`s):
```python
from molfeat.trans import FeatConcat

concat = FeatConcat(
    ["maccs", "ecfp"],                    # 167 + 2048 dimensions
    params={"ecfp": {"length": 2048}},    # FPVecTransformer's ecfp default length is 2000
    dtype=np.float32,
)
X = concat(smiles)                        # (n_mols, 2215); concat.length == 2215
```

### For Deep Learning

**Transformer-based embeddings:**
```python
# ChemBERTa - Pre-trained on 77M PubChem compounds
PretrainedHFTransformer(kind="ChemBERTa-77M-MLM", notation="smiles")

# ChemGPT - Autoregressive language model (SELFIES input)
PretrainedHFTransformer(kind="ChemGPT-1.2B", notation="selfies")
```

**Foundation-model embeddings (molfeat 1.x):**
```python
from molfeat.trans.pretrained import CheMeleonTransformer, MolJEPATransformer

CheMeleonTransformer()                    # 2,048-d descriptor-foundation-model fingerprints
MolJEPATransformer(trust_remote_code=True,
                   accept_noncommercial_license=True)   # CC BY-NC 4.0 weights
```
The legacy DGL GIN (`gin_supervised_*`) and Graphormer models were removed in molfeat 1.0.

### For Similarity Searching

```python
# ECFP - General purpose, most widely used
FPCalculator("ecfp")

# MACCS - Fast, scaffold-based similarity
FPCalculator("maccs")

# MAP4 - Efficient for large databases
FPCalculator("map4")

# USR/USRCAT - 3D shape similarity
from molfeat.calc import USRDescriptors
USRDescriptors()
```

### For Pharmacophore-Based Approaches

```python
# FCFP - Functional group based
FPCalculator("fcfp")

# CATS - Pharmacophore pair distributions (189-d in 2D)
from molfeat.calc import CATS
CATS()                      # CATS(use_3d_distances=True) for the 3D variant

# Gobbi - Explicit 2D pharmacophore features
from molfeat.calc import Pharmacophore2D
Pharmacophore2D(factory="gobbi")
```

## Common Workflows and Advanced Patterns

End-to-end recipes (QSAR model building, virtual screening, similarity search, scikit-learn pipeline integration, comparing featurizers), ModelStore discovery, and advanced usage (custom preprocessing, chunked batch processing, caching expensive embeddings) have moved to keep this body lean.

Full copy-ready workflow and advanced-pattern recipes: see `references/workflows_and_patterns.md`. Additional runnable examples (PyTorch training, grid search, 3D conformers) live in `references/examples.md`.

## Performance Tips

1. **Use parallelization**: Set `n_jobs=-1` to utilize all CPU cores
2. **Batch processing**: Process multiple molecules at once instead of loops
3. **Choose appropriate featurizers**: Fingerprints are faster than deep learning models
4. **Cache pretrained models**: Leverage built-in caching for repeated use
5. **Use float32**: Set `dtype=np.float32` when precision allows
6. **Handle errors efficiently**: Use `ignore_errors=True` for large datasets

## Common Featurizers Reference

**Quick reference for frequently used featurizers:**

| Featurizer | Type | Dimensions | Speed | Use Case |
|------------|------|------------|-------|----------|
| `ecfp` | Fingerprint | 2048 | Fast | General purpose |
| `maccs` | Fingerprint | 167 | Very fast | Scaffold similarity |
| `desc2D` | Descriptors | 223 | Fast | Interpretable models |
| `mordred` | Descriptors | 1800+ | Medium | Comprehensive features |
| `map4` | Fingerprint | 2048 | Fast | Large-scale screening |
| `ChemBERTa-77M-MLM` | Deep learning | 384 | Slow* | Transfer learning |
| `CheMeleonTransformer` | Foundation model | 2048 | Slow* | Descriptor-pretrained embeddings |

*First run is slow; subsequent runs benefit from caching

## Resources

This skill includes comprehensive reference documentation:

### references/api_reference.md
Complete API documentation covering:
- `molfeat.calc` - All calculator classes and parameters
- `molfeat.trans` - Transformer classes and methods
- `molfeat.store` - ModelStore usage
- Common patterns and integration examples
- Performance optimization tips

**When to load:** Reference when implementing specific calculators, understanding transformer parameters, or integrating with scikit-learn/PyTorch.

### references/available_featurizers.md
Comprehensive catalog of all 100+ featurizers organized by category:
- Transformer-based language models (ChemBERTa, ChemGPT)
- Graph neural networks (GIN, Graphormer — legacy, removed in molfeat 1.0)
- Molecular descriptors (RDKit, Mordred)
- Fingerprints (ECFP, MACCS, MAP4, and 15+ others)
- Pharmacophore descriptors (CATS, Gobbi)
- Shape descriptors (USR, ElectroShape)
- Scaffold-based descriptors

**When to load:** Reference when selecting the optimal featurizer for a specific task, exploring available options, or understanding featurizer characteristics.

**Search tip:** Use grep to find specific featurizer types:
```bash
grep -i "chembert" references/available_featurizers.md
grep -i "pharmacophore" references/available_featurizers.md
```

### references/examples.md
Practical code examples for common scenarios:
- Installation and quick start
- Calculator and transformer examples
- Pretrained model usage
- Scikit-learn and PyTorch integration
- Virtual screening workflows
- QSAR model building
- Similarity searching
- Troubleshooting and best practices

**When to load:** Reference when implementing specific workflows, troubleshooting issues, or learning molfeat patterns.

## Troubleshooting

### Invalid Molecules
Enable error handling to skip invalid SMILES:
```python
transformer = MoleculeTransformer(
    calc,
    ignore_errors=True,
    verbose=True
)
```

### Memory Issues with Large Datasets
Process in chunks or use streaming approaches for datasets > 100K molecules.

### Pretrained Model Dependencies
Some models require additional packages. Install specific extras:
```bash
uv pip install "molfeat[transformer]"  # For ChemBERTa/ChemGPT/MolT5
uv pip install "molfeat[pyg]"          # For Mol-JEPA (with the transformer extra)
```
There is no `dgl` extra in molfeat 1.x — the DGL GIN models were removed.

### Reproducibility
Save exact configurations and document versions:
```python
transformer.to_state_yaml_file("config.yml")
import molfeat
print(f"molfeat version: {molfeat.__version__}")
```

## Additional Resources

- **Official Documentation**: https://molfeat-docs.datamol.io/
- **GitHub Repository**: https://github.com/datamol-io/molfeat
- **PyPI Package**: https://pypi.org/project/molfeat/
- **Tutorial**: https://portal.valencelabs.com/datamol/post/types-of-featurizers-b1e8HHrbFMkbun6

Part of the AlterLab Academic Skills suite.

