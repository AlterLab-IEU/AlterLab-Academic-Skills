# Datamol Core API Reference

This document covers the main functions available in the datamol namespace.

## Molecule Creation and Conversion

### `to_mol(mol, ...)`
Convert SMILES string or other molecular representations to RDKit molecule objects.
- **Parameters**: Accepts SMILES strings, InChI, or other molecular formats
- **Returns**: `rdkit.Chem.Mol` object
- **Common usage**: `mol = dm.to_mol("CCO")`

### `from_inchi(inchi)`
Convert InChI string to molecule object.

### `from_smarts(smarts)`
Convert SMARTS pattern to molecule object.

### `from_selfies(selfies)`
Convert SELFIES string to molecule object.

### `copy_mol(mol)`
Create a copy of a molecule object to avoid modifying the original.

## Molecule Export

### `to_smiles(mol, ...)`
Convert molecule object to SMILES string.
- **Common parameters**: `canonical=True`, `isomeric=True`

### `to_inchi(mol, ...)`
Convert molecule to InChI string representation.

### `to_inchikey(mol)`
Convert molecule to InChI key (fixed-length hash).

### `to_smarts(mol)`
Convert molecule to SMARTS pattern.

### `to_selfies(mol)`
Convert molecule to SELFIES (Self-Referencing Embedded Strings) format.

## Sanitization and Standardization

### `sanitize_mol(mol, ...)`
Enhanced version of RDKit's sanitize operation using mol→SMILES→mol conversion and aromatic nitrogen fixing.
- **Purpose**: Fix common molecular structure issues
- **Returns**: Sanitized molecule or None if sanitization fails

### `standardize_mol(mol, disconnect_metals=False, normalize=True, reionize=True, ...)`
Apply comprehensive standardization procedures including:
- Metal disconnection
- Normalization (charge corrections)
- Reionization
- Fragment handling (largest fragment selection)

### `standardize_smiles(smiles, ...)`
Apply SMILES standardization procedures directly to a SMILES string.

### `fix_mol(mol)`
Attempt to fix molecular structure issues automatically.

### `fix_valence(mol)`
Correct valence errors in molecular structures.

## Molecular Properties

### `reorder_atoms(mol, ...)`
Ensure consistent atom ordering for the same molecule regardless of original SMILES representation.
- **Purpose**: Maintain reproducible feature generation

### `remove_hs(mol, ...)`
Remove hydrogen atoms from molecular structure.

### `add_hs(mol, ...)`
Add explicit hydrogen atoms to molecular structure.

## Fingerprints and Similarity

### `to_fp(mol, fp_type='ecfp', ...)`
Generate molecular fingerprints for similarity calculations.
- **Fingerprint types**:
  - `'ecfp'` - Extended Connectivity Fingerprints (Morgan)
  - `'fcfp'` - Functional Connectivity Fingerprints
  - `'maccs'` - MACCS keys
  - `'topological'` - Topological fingerprints
  - `'atompair'` - Atom pair fingerprints
- **Common parameters**: `radius`, `fpSize` — extra kwargs are passed straight to RDKit's `rdFingerprintGenerator` (so `fpSize`, not `n_bits`/`nBits`); datamol's `ecfp` default is `radius=3` (ECFP6), `fpSize=2048`
- **Returns**: Numpy array (default `as_array=True`) or RDKit fingerprint object

### `pdist(mols, n_jobs=1, squareform=True, **fp_args)`
Calculate pairwise Tanimoto distances between all molecules in a list.
- **Supports**: Parallel processing via `n_jobs` parameter
- **Returns**: Square N×N distance matrix by default; `squareform=False` gives the condensed vector

### `cdist(mols1, mols2, ...)`
Calculate Tanimoto distances between two sets of molecules.

## Clustering and Diversity

### `cluster_mols(mols, cutoff=0.2, feature_fn=None, n_jobs=1)`
Cluster molecules using Butina clustering algorithm.
- **Parameters**:
  - `cutoff`: Distance threshold (default 0.2)
  - `feature_fn`: Custom function for molecular features
  - `n_jobs`: Parallelization (-1 for all cores)
- **Important**: Builds full distance matrix - suitable for ~1000 structures, not for 10,000+
- **Returns**: A tuple `(cluster_indices, cluster_mols)` — one tuple of indices and one list of Mols per cluster

### `pick_diverse(mols, npick, ...)`
Select diverse subset of molecules based on fingerprint diversity (MaxMin).
- **Returns**: `(picked_indices, picked_mols)`

### `pick_centroids(mols, npick=0, threshold=0.5, method='sphere', ...)`
Select centroid molecules representing clusters (sphere exclusion by default; `maxmin` or RDKit hierarchical methods also accepted).
- **Returns**: `(centroid_indices, centroid_mols)`

## Graph Operations

### `to_graph(mol)`
Convert molecule to graph representation for graph-based analysis.

### `get_all_path_between(mol, start, end)`
Find all paths between two atoms in molecular structure.

## DataFrame Integration

### `to_df(mols, smiles_column='smiles', mol_column='mol')`
Convert list of molecules to pandas DataFrame.

### `from_df(df, smiles_column='smiles', mol_column='mol')`
Convert pandas DataFrame to list of molecules.
