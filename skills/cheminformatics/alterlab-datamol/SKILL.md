---
name: alterlab-datamol
description: Wraps RDKit in a high-level, pandas-friendly datamol interface with sensible defaults for everyday drug discovery — SMILES/SDF loading into DataFrames, molecule standardization, descriptors, fingerprints, Butina clustering, 3D conformer generation, scaffold analysis, and parallel batch processing, returning native rdkit.Chem.Mol objects. Use when running standard cheminformatics pipelines on molecule tables with minimal boilerplate; for low-level control, custom sanitization, or specialized algorithms prefer alterlab-rdkit. Part of the AlterLab Academic Skills suite.
license: Apache-2.0
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*)
compatibility: "Self-contained — runs under `uv run python` with the skill's Python package installed; no API key or account required."
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# Datamol Cheminformatics Skill

## Overview

Datamol is a Python library that provides a lightweight, Pythonic abstraction layer over RDKit for molecular cheminformatics. Simplify complex molecular operations with sensible defaults, efficient parallelization, and modern I/O capabilities. All molecular objects are native `rdkit.Chem.Mol` instances, ensuring full compatibility with the RDKit ecosystem.

**Key capabilities**:
- Molecular format conversion (SMILES, SELFIES, InChI)
- Structure standardization and sanitization
- Molecular descriptors and fingerprints
- 3D conformer generation and analysis
- Clustering and diversity selection
- Scaffold and fragment analysis
- Chemical reaction application
- Visualization and alignment
- Batch processing with parallelization
- Cloud storage support via fsspec

## When to Use This Skill

Use this skill when the user wants to:
- Load, standardize, and de-duplicate molecule tables (CSV/SDF/Excel/Parquet, local or cloud) with little boilerplate
- Compute datamol's descriptor set, fingerprints, and Tanimoto distance matrices for a compound set
- Cluster, pick diverse subsets, extract Murcko scaffolds, or fragment (BRICS/RECAP) a library
- Generate and cluster 3D conformers, or render aligned molecule grids for SAR review

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Low-level control: custom sanitization flags, atom-mapped reaction details, specialised fingerprint/descriptor algorithms | `alterlab-rdkit` |
| ML-ready feature matrices, pretrained embeddings, or featurizer benchmarking | `alterlab-molfeat` |
| Drug-likeness rule sets, PAINS / structural-alert and complexity filtering | `alterlab-medchem` |
| Downloading curated ADMET/DTI benchmark datasets with scaffold or cold splits | `alterlab-pytdc` |

## Installation and Setup

Guide users to install datamol:

```bash
uv pip install datamol
```

Examples here are verified against **datamol 0.13.0** (current as of 2026-09; requires Python ≥ 3.11 and pulls in RDKit). 0.13 fixed the misspelled heterocycle descriptors: the `compute_many_descriptors` keys are now `n_aromatic_heterocycles` / `n_aliphatic_heterocycles` / `n_saturated_heterocycles` (formerly `..._heterocyles`; the old function names survive only as deprecated aliases). Pin `'datamol>=0.13'` if you depend on those keys.

**Import convention**:
```python
import datamol as dm
```

## Core Workflows

Each subsection below shows the primary call pattern. Full API signatures, parameters, and secondary examples live in the per-module reference files cited under each; complete multi-step pipelines live in `references/workflow_recipes.md`.

### 1. Basic Molecule Handling

```python
import datamol as dm

# Parse SMILES (returns None on failure)
mol = dm.to_mol("CCO")                        # Ethanol
mols = [dm.to_mol(smi) for smi in ["CCO", "c1ccccc1", "CC(=O)O"]]
if dm.to_mol("invalid_smiles") is None:
    print("Failed to parse SMILES")

# Export to common formats (canonical + isomeric by default)
smiles   = dm.to_smiles(mol)                  # keeps stereochemistry
flat     = dm.to_smiles(mol, isomeric=False)  # drops stereochemistry
inchi    = dm.to_inchi(mol)
inchikey = dm.to_inchikey(mol)
selfies  = dm.to_selfies(mol)

# Standardize user-provided molecules (recommended for datasets)
mol = dm.sanitize_mol(mol)
mol = dm.standardize_mol(mol, disconnect_metals=True, normalize=True, reionize=True)
clean_smiles = dm.standardize_smiles(smiles)
```

Full conversion, sanitization, and standardization API: see `references/core_api.md`.

### 2. Reading and Writing Molecular Files

```python
# Read (open_df auto-detects .sdf/.csv/.xlsx/.parquet/.json)
mols = dm.read_sdf("compounds.sdf")                              # default: list of Mols
df = dm.read_sdf("compounds.sdf", as_df=True, mol_column="mol")  # DataFrame instead
df = dm.read_csv("data.csv", smiles_column="SMILES", mol_column="mol")
df = dm.open_df("file.sdf")

# Write
dm.to_sdf(mols, "output.sdf")               # or dm.to_sdf(df, "output.sdf", mol_column="mol")
dm.to_smi(mols, "output.smi")
dm.to_xlsx(df, "output.xlsx", mol_column="mol")   # renders molecule images in cells

# Remote paths work everywhere via fsspec (S3, GCS, HTTP)
mols = dm.read_sdf("s3://bucket/compounds.sdf")
dm.to_sdf(mols, "s3://bucket/output.sdf")
```

Full reader/writer signatures (`read_smi`, `read_excel`, `read_mol2file`, `read_pdbfile`, `save_df`, shared parameters): see `references/io_module.md`.

### 3. Molecular Descriptors and Properties

```python
# Single molecule -> ~22 keys. Note datamol's naming (NOT rdkit's):
desc = dm.descriptors.compute_many_descriptors(mol)
#   {'mw': 46.04, 'clogp': -0.0, 'n_lipinski_hbd': 1, 'n_lipinski_hba': 1,
#    'tpsa': 20.23, 'n_rotatable_bonds': 0, 'qed': ..., 'fsp3': ..., 'sas': ..., ...}
# Gotcha: logP is 'clogp'; donors/acceptors are 'n_lipinski_hbd'/'n_lipinski_hba'.
# There is no 'logp', 'hbd', 'hba', or 'n_aromatic_atoms' key in this dict.

# Batch (parallel) -> DataFrame with the same keys. Pass an explicit batch_size
# when n_jobs != 1: the default batch_size=None is rejected by joblib >= 1.6
# ("batch_size must be 'auto' or a positive integer").
desc_df = dm.descriptors.batch_compute_many_descriptors(mols, n_jobs=-1, batch_size=256,
                                                        progress=True)

# Standalone descriptors not in the dict above
dm.descriptors.n_aromatic_atoms(mol)
dm.descriptors.n_stereo_centers(mol)
dm.descriptors.n_rigid_bonds(mol)

# Drug-likeness filter (Lipinski's Rule of Five) with datamol's exact key names
def is_druglike(mol):
    d = dm.descriptors.compute_many_descriptors(mol)
    return (d['mw'] <= 500 and d['clogp'] <= 5 and
            d['n_lipinski_hbd'] <= 5 and d['n_lipinski_hba'] <= 10)

druglike_mols = [m for m in mols if is_druglike(m)]
```

Full descriptor catalog, RDKit descriptor access, and ADME examples: see `references/descriptors_viz.md`.

### 4. Molecular Fingerprints and Similarity

```python
# Fingerprints (ECFP/Morgan is the default; datamol's ecfp default is radius=3, i.e. ECFP6)
# Extra kwargs go straight to RDKit's rdFingerprintGenerator: use fpSize, not n_bits/nBits.
fp       = dm.to_fp(mol, fp_type='ecfp', radius=2, fpSize=2048)
fp_maccs = dm.to_fp(mol, fp_type='maccs')
# Also available: 'topological', 'atompair', 'fcfp', 'rdkit', '*-count' variants
# (full list: dm.list_supported_fingerprints())

# Similarity as Tanimoto distance (distance = 1 - similarity; lower = more similar)
dist_matrix = dm.pdist(mols, n_jobs=-1)          # square N x N matrix (squareform=True default)
condensed   = dm.pdist(mols, squareform=False)   # condensed vector, SciPy-style
distances   = dm.cdist(query_mols, library_mols, n_jobs=-1)  # between two sets
```

Fingerprint types and `pdist` / `cdist` details: see `references/core_api.md`.

### 5. Clustering and Diversity Selection

```python
# Butina clustering (cutoff = Tanimoto distance). Returns a TUPLE:
# (cluster_indices, cluster_mols) — one tuple of indices / list of Mols per cluster.
cluster_idx, cluster_mols = dm.cluster_mols(mols, cutoff=0.2, n_jobs=-1)
for i, members in enumerate(cluster_idx):
    print(i, len(members))

# Diversity / representative selection — both return (indices, mols)
diverse_idx, diverse = dm.pick_diverse(mols, npick=100)
centroid_idx, centroids = dm.pick_centroids(mols, npick=50)
```

**Scale note**: Butina builds a full distance matrix — fine for ~1,000 molecules, not 10,000+. Clustering parameters: see `references/core_api.md`.

### 6. Scaffold Analysis

```python
# Bemis-Murcko scaffold (core ring systems + linkers)
scaffold = dm.to_scaffold_murcko(mol)
scaffold_smiles = dm.to_smiles(scaffold)
```

Scaffold frequency counting, scaffold-to-molecule grouping, and scaffold-based train/test splitting for ML: see `references/workflow_recipes.md`. `fuzzy_scaffolding` and more: see `references/fragments_scaffolds.md`.

### 7. Molecular Fragmentation

```python
# BRICS (16 bond types) and RECAP (11 bond types) return lists of RDKit Mol
# fragments, parent molecule first unless remove_parent=True. The default
# fix=True caps the dummy atoms; pass fix=False to keep attachment points
# such as '[1*]C(C)=O' in the SMILES.
frags_brics = dm.fragment.brics(mol, remove_parent=True, fix=False)
frag_smiles = {dm.to_smiles(f) for f in frags_brics}
frags_recap = dm.fragment.recap(mol, remove_parent=True)
```

Cross-library fragment frequency analysis and fragment-overlap scoring recipes: see `references/workflow_recipes.md`. MMPA fragmentation and a method comparison table: see `references/fragments_scaffolds.md`.

### 8. 3D Conformer Generation

```python
# Generate 3D conformers (ETKDGv3 is the default method; minimize_energy defaults
# to False — pass True for UFF minimization)
mol_3d = dm.conformers.generate(mol, n_confs=50, rms_cutoff=0.5,
                                minimize_energy=True, method='ETKDGv3')
mol_3d.GetNumConformers()
conf = mol_3d.GetConformer(0)
positions = conf.GetPositions()          # Nx3 array of atom coordinates

# Cluster conformers by RMSD (Butina on symmetry-aware pairwise RMS)
centroid_mol = dm.conformers.cluster(mol_3d, rms_cutoff=1.0)       # one Mol holding the centroid conformers
per_cluster  = dm.conformers.cluster(mol_3d, rms_cutoff=1.0, centroids=False)  # list of Mols, one per cluster

# Solvent accessible surface area
sasa_values = dm.conformers.sasa(mol_3d, n_jobs=-1)
sasa = mol_3d.GetConformer(0).GetDoubleProp('rdkit_free_sasa')
```

Embedding methods, RMSD matrices, and low-level coordinate manipulation: see `references/conformers_module.md`.

### 9. Visualization

```python
# Grid image (SVG by default: use_svg=True). For a PNG file pass use_svg=False —
# otherwise SVG markup is written into the .png file.
dm.viz.to_image(mols[:20], legends=[dm.to_smiles(m) for m in mols[:20]],
                n_cols=5, mol_size=(300, 300))
dm.viz.to_image(mols, outfile="molecules.png", use_svg=False)
dm.viz.to_image(mols, outfile="molecules.svg")

# Align by MCS for SAR series; highlight atoms/bonds; render conformers
dm.viz.to_image(similar_mols, align=True, legends=activity_labels, n_cols=4)
dm.viz.to_image(mol, highlight_atom=[0, 1, 2, 3], highlight_bond=[0, 1, 2])
dm.viz.conformers(mol_3d, n_confs=10, align_conf=True, n_cols=3)
```

Full `to_image` / `conformers` / `circle_grid` parameters and best practices: see `references/descriptors_viz.md`.

### 10. Chemical Reactions

```python
from rdkit.Chem import rdChemReactions

# Build a reaction from SMARTS, then apply it to a reactant tuple. By default
# apply_reaction returns every product set (list of lists); ask for one Mol:
rxn = rdChemReactions.ReactionFromSmarts('[C:1](=[O:2])[OH:3]>>[C:1](=[O:2])[Cl:3]')
product = dm.reactions.apply_reaction(rxn, (dm.to_mol("CC(=O)O"),),
                                      single_product_group=True, product_index=0,
                                      sanitize=True)
product_smiles = dm.to_smiles(product)   # 'CC(=O)Cl' (or pass as_smiles=True)
```

Batch reaction application, common reaction templates (amide, Suzuki, esterification), and the toy `datamol.data` datasets: see `references/reactions_data.md`.

## Parallelization

Datamol includes built-in parallelization for many operations. Use `n_jobs` parameter:
- `n_jobs=1`: Sequential (no parallelization)
- `n_jobs=-1`: Use all available CPU cores
- `n_jobs=4`: Use 4 cores

**Functions supporting parallelization**:
- `dm.read_sdf(..., n_jobs=-1)`
- `dm.descriptors.batch_compute_many_descriptors(..., n_jobs=-1, batch_size=256)` (explicit `batch_size` needed with joblib ≥ 1.6)
- `dm.cluster_mols(..., n_jobs=-1)`
- `dm.pdist(..., n_jobs=-1)`
- `dm.conformers.sasa(..., n_jobs=-1)`

**Progress bars**: Many batch operations support `progress=True` parameter.

## Common Workflows and Patterns

Full copy-ready worked pipelines — data loading → filtering → analysis, Structure-Activity Relationship (SAR) analysis, and virtual screening — plus machine-learning feature generation and robust error-handling wrappers, have moved out of this file to keep it lean. See `references/workflow_recipes.md`.

## Reference Documentation

For detailed API documentation, consult these reference files:

- **`references/core_api.md`**: Core namespace functions (conversions, standardization, fingerprints, clustering)
- **`references/io_module.md`**: File I/O operations (read/write SDF, CSV, Excel, remote files)
- **`references/conformers_module.md`**: 3D conformer generation, clustering, SASA calculations
- **`references/descriptors_viz.md`**: Molecular descriptors and visualization functions
- **`references/fragments_scaffolds.md`**: Scaffold extraction, BRICS/RECAP fragmentation
- **`references/reactions_data.md`**: Chemical reactions and toy datasets
- **`references/workflow_recipes.md`**: End-to-end pipelines, SAR/screening recipes, ML integration, error handling

## Best Practices

1. **Always standardize molecules** from external sources:
   ```python
   mol = dm.standardize_mol(mol, disconnect_metals=True, normalize=True, reionize=True)
   ```

2. **Check for None values** after molecule parsing:
   ```python
   mol = dm.to_mol(smiles)
   if mol is None:
       ...  # log and skip the invalid SMILES
   ```

3. **Use parallel processing** for large datasets:
   ```python
   result = dm.operation(..., n_jobs=-1, progress=True)
   ```

4. **Leverage fsspec** for cloud storage:
   ```python
   df = dm.read_sdf("s3://bucket/compounds.sdf")
   ```

5. **Use appropriate fingerprints** for similarity:
   - ECFP (Morgan): General purpose, structural similarity
   - MACCS: Fast, smaller feature space
   - Atom pairs: Considers atom pairs and distances

6. **Consider scale limitations**:
   - Butina clustering: ~1,000 molecules (full distance matrix)
   - For larger datasets: Use diversity selection or hierarchical methods

7. **Scaffold splitting for ML**: Ensure proper train/test separation by scaffold

8. **Align molecules** when visualizing SAR series

## Troubleshooting

**Issue**: Molecule parsing fails
- **Solution**: Use `dm.standardize_smiles()` first or try `dm.fix_mol()`

**Issue**: Memory errors with clustering
- **Solution**: Use `dm.pick_diverse()` instead of full clustering for large sets

**Issue**: Slow conformer generation
- **Solution**: Reduce `n_confs` or increase `rms_cutoff` to generate fewer conformers

**Issue**: Remote file access fails
- **Solution**: Ensure fsspec and appropriate cloud provider libraries are installed (s3fs, gcsfs, etc.)

## Additional Resources

- **Datamol Documentation**: https://docs.datamol.io/
- **RDKit Documentation**: https://www.rdkit.org/docs/
- **GitHub Repository**: https://github.com/datamol-io/datamol

Part of the AlterLab Academic Skills suite.
