# Rowan Molecule Handling Reference

## Overview

Rowan uses the `stjames` library for molecular representations. The `stjames.Molecule` class provides a unified interface for creating molecules from various sources and accessing molecular properties.

## Table of Contents

1. [Creating Molecules](#creating-molecules)
2. [Molecule Attributes](#molecule-attributes)
3. [Geometry Methods](#geometry-methods)
4. [File I/O](#file-io)
5. [Conversion Functions](#conversion-functions)
6. [Working with Atoms](#working-with-atoms)

---

## Creating Molecules

### From SMILES

```python
import stjames

# Simple SMILES
mol = stjames.Molecule.from_smiles("CCO")  # Ethanol
mol = stjames.Molecule.from_smiles("c1ccccc1")  # Benzene

# With stereochemistry
mol = stjames.Molecule.from_smiles("C[C@H](O)[C@@H](O)C")  # meso-2,3-butanediol

# Charged molecules
mol = stjames.Molecule.from_smiles("[NH4+]")  # Ammonium
mol = stjames.Molecule.from_smiles("CC(=O)[O-]")  # Acetate

# Complex drug-like molecules
mol = stjames.Molecule.from_smiles("CC(=O)Oc1ccccc1C(=O)O")  # Aspirin
```

**Note:** `from_smiles()` automatically generates 3D coordinates. Its only argument is the SMILES string — charge and multiplicity are inferred from the SMILES (see below for how to set them explicitly).

---

### From XYZ String

```python
import stjames

xyz_string = """3
Water molecule
O  0.000  0.000  0.117
H  0.000  0.757 -0.469
H  0.000 -0.757 -0.469"""

mol = stjames.Molecule.from_xyz(xyz_string)
```

**XYZ format with optional metadata in comment line:**
```
N_atoms
charge=0 multiplicity=1 energy=-76.4 comment
Element X Y Z
...
```

---

### From XYZ File

```python
import stjames

mol = stjames.Molecule.from_file("structure.xyz")
```

---

### From Extended XYZ (EXTXYZ)

Extended XYZ supports additional properties like forces and cell parameters.

```python
import stjames

extxyz_string = """3
Lattice="10.0 0.0 0.0 0.0 10.0 0.0 0.0 0.0 10.0" Properties=species:S:1:pos:R:3:forces:R:3 energy=-76.4
O  0.000  0.000  0.117  0.01 0.02 0.03
H  0.000  0.757 -0.469  0.00 0.00 0.00
H  0.000 -0.757 -0.469  0.00 0.00 0.00"""

mol = stjames.Molecule.from_extxyz(extxyz_string)

# Access cell information
if mol.cell:
    print(f"Cell: {mol.cell.lattice_vectors}")
```

---

### From RDKit Molecule

```python
import stjames
from rdkit import Chem
from rdkit.Chem import AllChem

# Create RDKit molecule with 3D coordinates
rdkit_mol = Chem.MolFromSmiles("CCO")
rdkit_mol = Chem.AddHs(rdkit_mol)
AllChem.EmbedMolecule(rdkit_mol)
AllChem.MMFFOptimizeMolecule(rdkit_mol)

# Convert to stjames
mol = stjames.Molecule.from_rdkit(rdkit_mol)
```

---

### Specifying Charge and Multiplicity

`from_smiles()` takes **only** the SMILES — it does not accept `charge`/`multiplicity` keywords. Encode charge in the SMILES itself, or set the fields explicitly via `from_xyz(...)` (which does accept them) or by assigning on the model.

```python
import stjames

# Charge encoded in SMILES
mol = stjames.Molecule.from_smiles("CC(=O)[O-]")   # acetate, charge -1 inferred
mol = stjames.Molecule.from_smiles("[NH4+]")        # ammonium, charge +1 inferred

# Explicit charge/multiplicity when building from coordinates
mol = stjames.Molecule.from_xyz(o2_xyz, charge=0, multiplicity=3)  # triplet O2

# Or set on the model (it is a pydantic Molecule)
mol = stjames.Molecule.from_smiles("CCO")
mol.charge = 1
mol.multiplicity = 2
```

---

## Molecule Attributes

### Basic Properties

```python
import stjames

mol = stjames.Molecule.from_smiles("CCO")

# Charge and spin
print(f"Charge: {mol.charge}")  # 0
print(f"Multiplicity: {mol.multiplicity}")  # 1

# Number of atoms
print(f"Number of atoms: {len(mol.atoms)}")
```

### Computed Properties (after calculation)

```python
# After running a calculation
print(f"Energy: {mol.energy} Hartree")
print(f"Dipole: {mol.dipole}")  # (x, y, z) in Debye

# Atomic properties
print(f"Mulliken charges: {mol.mulliken_charges}")
print(f"Mulliken spin densities: {mol.mulliken_spin_densities}")
```

### Thermochemistry (after frequency calculation)

```python
# After frequency calculation
print(f"ZPE: {mol.zero_point_energy} Hartree")
print(f"Thermal enthalpy correction: {mol.thermal_enthalpy_corr}")
print(f"Thermal free-energy correction: {mol.thermal_free_energy_corr}")
print(f"Gibbs free energy: {mol.gibbs_free_energy} Hartree")  # property (alias for sum_energy_free_energy)
```

### Vibrational Modes (after frequency calculation)

```python
for mode in mol.vibrational_modes:
    print(f"Frequency: {mode.frequency} cm⁻¹")
```

### Periodic Cell

```python
if mol.cell:
    print(f"Lattice vectors: {mol.cell.lattice_vectors}")
    print(f"Is periodic: True")
```

---

## Geometry Methods

**Atom indices here are 1-based** (the methods reject 0). This differs from `mol.atoms[...]` list access, which is 0-based.

### Distance Between Atoms

```python
import stjames

mol = stjames.Molecule.from_smiles("CCO")

# Distance between atoms 1 and 2 (1-indexed), in Angstroms
d = mol.distance(1, 2)
print(f"C-C bond length: {d:.3f} Å")
```

### Angle Between Three Atoms

```python
import stjames

mol = stjames.Molecule.from_smiles("CCO")

# Angle formed by atoms 1-2-3 (C-C-O); degrees=True by default
angle = mol.angle(1, 2, 3, degrees=True)
print(f"C-C-O angle: {angle:.1f}°")

angle_rad = mol.angle(1, 2, 3, degrees=False)  # radians
```

### Dihedral Angle

```python
import stjames

mol = stjames.Molecule.from_smiles("CCCC")

# Dihedral angle for atoms 1-2-3-4 (1-indexed)
dihedral = mol.dihedral(1, 2, 3, 4, degrees=True)
print(f"Dihedral: {dihedral:.1f}°")

# positive_domain defaults to True (0 to 360); pass False for -180..180
dihedral_signed = mol.dihedral(1, 2, 3, 4, degrees=True, positive_domain=False)
```

### Translation

```python
import stjames

mol = stjames.Molecule.from_smiles("CCO")

# Translate by vector
translated = mol.translated([1.0, 0.0, 0.0])  # Move 1 Å in x direction
```

---

## File I/O

### Export to XYZ

```python
import stjames

mol = stjames.Molecule.from_smiles("CCO")

# Get XYZ string
xyz_str = mol.to_xyz(comment="Ethanol optimized structure")
print(xyz_str)

# Write to file
mol.to_xyz(comment="Ethanol", out_file="ethanol.xyz")
```

### Export to Extended XYZ

```python
import stjames

mol = stjames.Molecule.from_smiles("CCO")

# Include energy in comment
xyz_str = mol.to_xyz(comment=f"energy={mol.energy}")
```

---

## Conversion Functions

### SMILES to Molecule (Rowan Utility)

```python
import rowan

# Quick conversion using Rowan's utility
mol = rowan.smiles_to_stjames("CCO")
```

> There is no built-in name-to-SMILES lookup (no `rowan.molecule_lookup`). Resolve common names to SMILES with an external source (PubChem, a local dictionary, or RDKit), then submit:
>
> ```python
> import rowan
> aspirin = "CC(=O)Oc1ccccc1C(=O)O"
> workflow = rowan.submit_pka_workflow(aspirin, name="Aspirin pKa")
> ```

---

## Working with Atoms

### Atom Class

Each atom in `mol.atoms` is an `stjames.Atom`. Coordinates live in `position` (a 3-vector); there are no `.x/.y/.z` attributes. Use the `atomic_symbol` property for the element symbol.

```python
import stjames

mol = stjames.Molecule.from_smiles("CCO")

for i, atom in enumerate(mol.atoms):
    x, y, z = atom.position
    print(f"Atom {i}: {atom.atomic_symbol} at ({x:.3f}, {y:.3f}, {z:.3f})")
```

### Atom Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `atomic_number` | int | Atomic number |
| `atomic_symbol` | str | Element symbol (e.g. "C", "O", "H"), derived property |
| `position` | list[float] | `[x, y, z]` coordinates (Å) |
| `mass` | float | Atomic mass (amu) |

### Getting Coordinates as Array

```python
import numpy as np

mol = stjames.Molecule.from_smiles("CCO")

# mol.coordinates is already a list of [x, y, z]; convert to ndarray
positions = np.array(mol.coordinates)
print(f"Positions shape: {positions.shape}")  # (N_atoms, 3)
```

---

## Common Patterns

### Batch Molecule Creation

```python
import stjames

smiles_list = ["CCO", "CC(=O)O", "c1ccccc1", "c1ccccc1O"]

molecules = []
for smi in smiles_list:
    try:
        mol = stjames.Molecule.from_smiles(smi)
        molecules.append(mol)
    except Exception as e:
        print(f"Failed to create molecule from {smi}: {e}")

print(f"Created {len(molecules)} molecules")
```

### Modifying Charge/Multiplicity

```python
import stjames

# Create neutral molecule
mol = stjames.Molecule.from_smiles("c1ccccc1")

# Make a cation-doublet copy by assigning on the model (from_smiles takes no charge kwarg)
mol_cation = mol.model_copy()
mol_cation.charge = 1
mol_cation.multiplicity = 2
```

### Combining Geometry Analysis

```python
import stjames

mol = stjames.Molecule.from_smiles("CCCC")

# Analyze butane conformer (geometry methods are 1-indexed)
print("Butane geometry analysis:")
print(f"  C1-C2 bond: {mol.distance(1, 2):.3f} Å")
print(f"  C2-C3 bond: {mol.distance(2, 3):.3f} Å")
print(f"  C3-C4 bond: {mol.distance(3, 4):.3f} Å")
print(f"  C-C-C angle: {mol.angle(1, 2, 3, degrees=True):.1f}°")
print(f"  C-C-C-C dihedral: {mol.dihedral(1, 2, 3, 4, degrees=True):.1f}°")
```

---

## Electron Sanity Check

The `stjames.Molecule` class can validate that charge and multiplicity are consistent with the number of electrons via `mol.check_electron_sanity()`. Set the spin state when building from coordinates (`from_xyz(..., multiplicity=3)`) or by assigning `mol.multiplicity`:

```python
import stjames

# Triplet oxygen, built from coordinates with explicit multiplicity
mol = stjames.Molecule.from_xyz(o2_xyz, charge=0, multiplicity=3)
mol.check_electron_sanity()   # raises if charge/multiplicity are inconsistent
```

The validation ensures:
- Number of electrons = sum(atomic_numbers) - charge
- Multiplicity is compatible with electron count (odd/even)
