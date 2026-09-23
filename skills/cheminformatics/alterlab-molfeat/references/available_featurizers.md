# Available Featurizers in Molfeat

This document provides a comprehensive catalog of all featurizers available in molfeat, organized by category.

> **molfeat 1.0 (2026-09) removed the DGL-based pretrained GNNs (GIN variants, JTVAE) and Graphormer.**
> Their model-store cards still list them, but loading fails in 1.x; they are kept below only as
> legacy entries (usable with `molfeat<1`, Python ≤ 3.10). 1.0 added the foundation-model
> featurizers `CheMeleonTransformer` and `MolJEPATransformer` (see "Foundation Models").

## Transformer-Based Language Models

Pre-trained transformer models for molecular embeddings using SMILES/SELFIES representations.

### RoBERTa-style Models
- **Roberta-Zinc480M-102M** - RoBERTa masked language model trained on ~480M SMILES strings from ZINC database
- **ChemBERTa-77M-MLM** - Masked language model based on RoBERTa trained on 77M PubChem compounds
- **ChemBERTa-77M-MTR** - Multitask regression version trained on PubChem compounds

### GPT-style Autoregressive Models
- **GPT2-Zinc480M-87M** - GPT-2 autoregressive language model trained on ~480M SMILES from ZINC
- **ChemGPT-1.2B** - Large transformer (1.2B parameters) pretrained on PubChem10M
- **ChemGPT-19M** - Medium transformer (19M parameters) pretrained on PubChem10M
- **ChemGPT-4.7M** - Small transformer (4.7M parameters) pretrained on PubChem10M

### Specialized Transformer Models
- **MolT5** - Self-supervised framework for molecule captioning and text-based generation

## Foundation Models (molfeat 1.x)

- **CheMeleonTransformer** — CheMeleon descriptor-foundation-model fingerprints (2,048-d); weights downloaded from the authors' Zenodo record and MD5-verified (`from molfeat.trans.pretrained import CheMeleonTransformer`)
- **MolJEPATransformer** — Mol-JEPA embeddings from the authors' Hugging Face checkpoint (CC BY-NC 4.0, custom model code); requires `trust_remote_code=True` and `accept_noncommercial_license=True`; uses the `transformer` + `pyg` extras

## Graph Neural Networks (GNNs) — legacy, removed in molfeat 1.0

Pre-trained graph neural network models operating on molecular graph structures.

### GIN (Graph Isomorphism Network) Variants
All pre-trained on ChEMBL molecules with different objectives:
- **gin-supervised-masking** - Supervised with node masking objective
- **gin-supervised-infomax** - Supervised with graph-level mutual information maximization
- **gin-supervised-edgepred** - Supervised with edge prediction objective
- **gin-supervised-contextpred** - Supervised with context prediction objective

### Other Graph-Based Models
- **JTVAE_zinc_no_kl** - Junction-tree VAE for molecule generation (trained on ZINC)
- **Graphormer-pcqm4mv2** - Graph transformer pretrained on PCQM4Mv2 quantum chemistry dataset for HOMO-LUMO gap prediction

## Molecular Descriptors

Calculators for physico-chemical properties and molecular characteristics.

### 2D Descriptors
- **desc2D** / **rdkit2D** - 200+ RDKit 2D molecular descriptors including:
  - Molecular weight, logP, TPSA
  - H-bond donors/acceptors
  - Rotatable bonds
  - Ring counts and aromaticity
  - Molecular complexity metrics

### 3D Descriptors
- **desc3D** / **rdkit3D** - RDKit 3D molecular descriptors (requires conformer generation)
  - Inertial moments
  - PMI (Principal Moments of Inertia) ratios
  - Asphericity, eccentricity
  - Radius of gyration

### Comprehensive Descriptor Sets
- **mordred** - Over 1800 molecular descriptors covering:
  - Constitutional descriptors
  - Topological indices
  - Connectivity indices
  - Information content
  - 2D/3D autocorrelations
  - WHIM descriptors
  - GETAWAY descriptors
  - And many more

### Electrotopological Descriptors
- **estate** - Electrotopological state (E-State) indices encoding:
  - Atomic environment information
  - Electronic and topological properties
  - Heteroatom contributions

## Molecular Fingerprints

Binary or count-based fixed-length vectors representing molecular substructures.

### Circular Fingerprints (ECFP-style)
- **ecfp** / **ecfp:2** / **ecfp:4** / **ecfp:6** - Extended-connectivity fingerprints
  - Radius variants (2, 4, 6 correspond to diameter)
  - Default: radius=3, 2048 bits
  - Most popular for similarity searching
- **ecfp-count** - Count version of ECFP (non-binary)
- **fcfp** / **fcfp-count** - Functional-class circular fingerprints
  - Similar to ECFP but uses functional groups
  - Better for pharmacophore-based similarity

### Path-Based Fingerprints
- **rdkit** - RDKit topological fingerprints based on linear paths
- **pattern** - Pattern fingerprints (similar to MACCS but automated)
- **layered** - Layered fingerprints with multiple substructure layers

### Key-Based Fingerprints
- **maccs** - MACCS keys (166-bit structural keys)
  - Fixed set of predefined substructures
  - Good for scaffold hopping
  - Fast computation
- **avalon** - Avalon fingerprints
  - Similar to MACCS but more features
  - Optimized for similarity searching

### Atom-Pair Fingerprints
- **atompair** - Atom pair fingerprints
  - Encodes pairs of atoms and distance between them
  - Good for 3D similarity
- **atompair-count** - Count version of atom pairs

### Topological Torsion Fingerprints
- **topological** - Topological torsion fingerprints
  - Encodes sequences of 4 connected atoms
  - Captures local topology
- **topological-count** - Count version of topological torsions

### MinHashed Fingerprints
- **map4** - MinHashed Atom-Pair fingerprint up to 4 bonds
  - Combines atom-pair and ECFP concepts
  - Default: 2048 dimensions in molfeat 1.0 (`FPCalculator("map4")`)
  - Needs the `map4` package from https://github.com/reymond-group/map4 (not on PyPI)
  - Fast and efficient for large datasets
- **secfp** - SMILES Extended Connectivity Fingerprint
  - Operates directly on SMILES strings
  - Captures both substructure and atom-pair information

### Extended Reduced Graph
- **erg** - Extended Reduced Graph
  - Uses pharmacophoric points instead of atoms
  - Reduces graph complexity while preserving key features

## Pharmacophore Descriptors

Features based on pharmacologically relevant functional groups and their spatial relationships.

### CATS (Chemically Advanced Template Search)
- **cats2D** - 2D CATS descriptors
  - Pharmacophore point pair distributions
  - Distance based on shortest path
  - Calculator class `molfeat.calc.CATS` (189 values with default 2D settings)
- **cats3D** - 3D CATS descriptors
  - Euclidean distance based
  - Requires conformer generation
- **cats2D_pharm** / **cats3D_pharm** - Pharmacophore variants

### Gobbi Pharmacophores
- **pharm2D-gobbi** - 2D pharmacophore fingerprints (`Pharmacophore2D(factory="gobbi")`; there is no `FPCalculator("gobbi2D")`)
  - 8 pharmacophore feature types:
    - Hydrophobic
    - Aromatic
    - H-bond acceptor
    - H-bond donor
    - Positive ionizable
    - Negative ionizable
    - Lumped hydrophobe
  - Good for virtual screening

### Pmapper Pharmacophores
- **pmapper2D** - 2D pharmacophore signatures
- **pmapper3D** - 3D pharmacophore signatures
  - High-dimensional pharmacophore descriptors
  - Useful for QSAR and similarity searching

## Shape Descriptors

Descriptors capturing 3D molecular shape and electrostatic properties.

### USR (Ultrafast Shape Recognition)
- **usr** - Basic USR descriptors
  - 12 dimensions encoding shape distribution
  - Extremely fast computation
- **usrcat** - USR with pharmacophoric constraints
  - 60 dimensions (12 per feature type)
  - Combines shape and pharmacophore information

### Electrostatic Shape
- **electroshape** - ElectroShape descriptors
  - Combines molecular shape, chirality, and electrostatics
  - Useful for protein-ligand docking predictions

## Scaffold-Based Descriptors

Descriptors based on molecular scaffolds and core structures.

### Scaffold Keys
- **scaffoldkeys** - Scaffold key calculator
  - 40+ scaffold-based properties
  - Bioisosteric scaffold representation
  - Captures core structural features

## Graph Featurizers for GNN Input

Atom and bond-level features for constructing graph representations for Graph Neural Networks.

### Atom-Level Features
- **atom-onehot** - One-hot encoded atom features
- **atom-default** - Default atom featurization including:
  - Atomic number
  - Degree, formal charge
  - Hybridization
  - Aromaticity
  - Number of hydrogen atoms

### Bond-Level Features
- **bond-onehot** - One-hot encoded bond features
- **bond-default** - Default bond featurization including:
  - Bond type (single, double, triple, aromatic)
  - Conjugation
  - Ring membership
  - Stereochemistry

## Integrated Pretrained Model Collections

Molfeat integrates models from various sources:

### HuggingFace Models
Access to transformer models through HuggingFace hub:
- ChemBERTa variants
- ChemGPT variants
- MolT5
- Custom uploaded models

### DGL-LifeSci Models (legacy — removed in molfeat 1.0)
Pre-trained GNN models from DGL-Life:
- GIN variants with different pre-training tasks
- AttentiveFP models
- MPNN models

### FCD (Fréchet ChemNet Distance)
- **fcd** - Pre-trained CNN for molecular generation evaluation

### Graphormer Models (legacy — removed in molfeat 1.0)
- Graph transformers from Microsoft Research
- Pre-trained on quantum chemistry datasets

## Usage Notes

### Choosing a Featurizer

**For traditional ML (Random Forest, SVM, etc.):**
- Start with **ecfp** or **maccs** fingerprints
- Try **desc2D** for interpretable models
- Use **FeatConcat** to combine multiple fingerprints

**For deep learning:**
- Use **ChemBERTa** or **ChemGPT** for transformer embeddings
- Use **CheMeleonTransformer** for descriptor-pretrained foundation-model fingerprints
- (GIN / Graphormer embeddings are legacy: only available with `molfeat<1`)

**For similarity searching:**
- **ecfp** - General purpose, most popular
- **maccs** - Fast, good for scaffold hopping
- **map4** - Efficient for large-scale searches
- **usr** / **usrcat** - 3D shape similarity

**For pharmacophore-based approaches:**
- **fcfp** - Functional group based
- **cats2D/3D** - Pharmacophore pair distributions
- **pharm2D-gobbi** - Explicit pharmacophore features

**For interpretability:**
- **desc2D** / **mordred** - Named descriptors
- **maccs** - Interpretable substructure keys
- **scaffoldkeys** - Scaffold-based features

### Model Dependencies

Some featurizers require optional dependencies:

- **Transformers** (ChemBERTa, ChemGPT, MolT5): `uv pip install "molfeat[transformer]"`
- **Mordred**: `uv pip install "molfeat[mordred]"`
- **FCD**: `uv pip install "molfeat[fcd]"`
- **Mol-JEPA**: `uv pip install "molfeat[transformer,pyg]"`
- **MAP4**: install the `map4` package from https://github.com/reymond-group/map4 (no molfeat extra)
- **All dependencies**: `uv pip install "molfeat[all]"`
- DGL (gin-*, jtvae) and Graphormer models: removed in molfeat 1.0 (no `dgl`/`graphormer` extras)

### Accessing All Available Models

```python
from molfeat.store.modelstore import ModelStore

store = ModelStore()
all_models = store.available_models

# Print all available featurizers
for model in all_models:
    print(f"{model.name}: {model.description}")

# Search for specific types
transformers = [m for m in all_models if "transformer" in m.tags]
gnn_models = [m for m in all_models if "gnn" in m.tags]
fingerprints = [m for m in all_models if "fingerprint" in m.tags]
```

## Performance Characteristics

### Computational Speed (relative)
**Fastest:**
- maccs
- ecfp
- rdkit fingerprints
- usr

**Medium:**
- desc2D
- cats2D
- Most fingerprints

**Slower:**
- mordred (1800+ descriptors)
- desc3D (requires conformer generation)
- 3D descriptors in general

**Slowest (first run):**
- Pretrained models (ChemBERTa, ChemGPT, GIN)
- Note: Subsequent runs benefit from caching

### Dimensionality

**Low (< 200 dims):**
- maccs (167)
- usr (12)
- usrcat (60)

**Medium (200-2000 dims):**
- desc2D (223 in molfeat 1.0)
- ecfp (2048 default, configurable)
- map4 (2048 default in molfeat 1.0)

**High (> 2000 dims):**
- mordred (1800+)
- Concatenated fingerprints
- Some transformer embeddings

**Variable:**
- Transformer models (e.g. 384 for ChemBERTa-77M-MLM; larger models 768-1024)
- CheMeleon (2048); Mol-JEPA (512 for the default `cls` output)
