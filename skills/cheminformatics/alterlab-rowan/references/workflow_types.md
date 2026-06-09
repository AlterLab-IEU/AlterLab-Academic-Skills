# Rowan Workflow Types Reference

## Table of Contents

1. [Property Prediction Workflows](#property-prediction-workflows)
2. [Molecular Modeling Workflows](#molecular-modeling-workflows)
3. [Protein-Ligand Workflows](#protein-ligand-workflows)
4. [Spectroscopy Workflows](#spectroscopy-workflows)
5. [Advanced Workflows](#advanced-workflows)

---

## Property Prediction Workflows

### pKa Calculation

Predict acid dissociation constants.

```python
workflow = rowan.submit_pka_workflow(
    "c1ccccc1O",
    name="pKa calculation"
)
```

**Result (`pKaResult`):**
- `result.strongest_acid`: pKa of most acidic proton
- `result.strongest_base`: pKa of most basic site
- `result.conjugate_acids`, `result.conjugate_bases`: protonation microstates

For macroscopic pKa, pH-dependent speciation, and isoelectric point use `submit_macropka_workflow` (`MacropKaResult`: `pka_values`, `microstates`, `isoelectric_point`).

---

### Redox Potential

Calculate oxidation/reduction potentials.

```python
workflow = rowan.submit_redox_potential_workflow(
    mol,
    name="redox potential"
)
```

**Result (`RedoxPotentialResult`):**
- `result.oxidation_potential`: oxidation potential (V)
- `result.reduction_potential`: reduction potential (V)

---

### Solubility Prediction

Predict aqueous and nonaqueous solubility.

```python
workflow = rowan.submit_solubility_workflow(
    mol,
    name="solubility"
)
```

**Result (`SolubilityResult`):**
- `result.solubilities`: predicted solubility entries (log S, per solvent/temperature)

---

### Hydrogen-Bond Basicity

Calculate H-bond acceptor strength.

```python
workflow = rowan.submit_hydrogen_bond_basicity_workflow(
    "CC(=O)C",
    name="H-bond basicity"
)
```

**Output:**
- `hb_basicity`: pKBHX value

---

### Bond Dissociation Energy (BDE)

Calculate homolytic bond dissociation energies.

Select bonds to break by the atom(s) whose bonds to fragment (`atoms=`), or with the convenience flags `all_CH` / `all_CX`. There is no `bond_indices` argument.

```python
workflow = rowan.submit_bde_workflow(
    mol,
    all_CH=True,        # break all C-H bonds; or atoms=[3, 7]
    name="BDE calculation"
)
```

**Result (`BDEResult`):** bond dissociation energies (kcal/mol) per fragmented bond, in `result.data`.

---

### Fukui Indices

Calculate reactivity indices for nucleophilic/electrophilic attack.

```python
workflow = rowan.submit_fukui_workflow(
    mol,
    name="Fukui indices"
)
```

**Result (`FukuiResult`):**
- `result.fukui_positive` (f+): susceptibility to nucleophilic attack, per atom
- `result.fukui_negative` (f-): susceptibility to electrophilic attack, per atom
- `result.fukui_zero` (f0): radical attack, per atom
- `result.global_electrophilicity_index`

---

### Spin States

Calculate relative energies of different spin multiplicities.

```python
workflow = rowan.submit_spin_states_workflow(
    mol,
    name="spin states"
)
```

**Output:**
- `spin_state_energies`: Energy of each multiplicity
- `ground_state`: Lowest energy multiplicity

---

### ADME-Tox Predictions

Predict absorption, distribution, metabolism, excretion, and toxicity.

```python
workflow = rowan.submit_admet_workflow(
    mol,
    name="ADMET"
)
```

**Output:**
- Various ADMET descriptors including:
  - `logP`, `logD`
  - `herg_inhibition`
  - `cyp_inhibition`
  - `bioavailability`
  - `bbb_permeability`

---

## Molecular Modeling Workflows

### Single-Point Energy

Calculate energy at fixed geometry.

```python
workflow = rowan.submit_basic_calculation_workflow(
    mol,
    tasks=["energy"],
    name="single point"
)
```

**Result (`BasicCalculationResult`):**
- `result.energy`: Total energy (Hartree)
- `result.dipole`: Dipole moment vector
- `result.charges`: Atomic partial charges

---

### Geometry Optimization

Optimize molecular geometry to minimum energy.

```python
workflow = rowan.submit_basic_calculation_workflow(
    mol,
    tasks=["optimize"],
    name="optimization"
)
```

**Result (`BasicCalculationResult`):**
- `result.molecule`: Optimized structure (stjames.Molecule)
- `result.energy`: Final energy (Hartree)
- `result.optimization_energies()`: Energy at each step

---

### Vibrational Frequencies

Calculate IR/Raman frequencies and thermochemistry.

```python
workflow = rowan.submit_basic_calculation_workflow(
    mol,
    tasks=["optimize", "frequencies"],
    name="frequency"
)
```

**Result (`BasicCalculationResult`):**
- `result.frequencies`: Vibrational frequencies (cm⁻¹; negative = imaginary)
- `result.molecule.zero_point_energy`, `.thermal_enthalpy_corr`, `.thermal_free_energy_corr`, `.gibbs_free_energy`: thermochemistry (Hartree)

---

### Conformer Search

Generate and optimize conformer ensemble.

```python
workflow = rowan.submit_conformer_search_workflow(
    mol,
    name="conformer search"
)
```

**Result (`ConformerSearchResult`):**
- `result.num_conformers`: number of unique conformers
- `result.get_energies()`: relative energies (kcal/mol), ascending
- `result.get_conformers()` / `result.get_conformer(0)`: conformers as `stjames.Molecule`
- `result.sasa`, `result.polar_sasa`, `result.radii_of_gyration`

---

### Tautomer Search

Enumerate and rank tautomers.

```python
workflow = rowan.submit_tautomer_search_workflow(
    mol,
    name="tautomer search"
)
```

**Result (`TautomerResult`):** ranked tautomers with relative energies and Boltzmann populations (see `result.data`).

---

### Coordinate / Dihedral Scan

Scan a bond, angle, or torsion energy surface with `submit_scan_workflow`. The scan coordinate and range are passed via the scan settings (see the API docs); there is no `submit_dihedral_scan_workflow`.

```python
workflow = rowan.submit_scan_workflow(
    mol,
    name="dihedral scan",
    # scan_settings define the coordinate (atoms), start/stop, and number of steps
)
```

**Result (`ScanResult`):** per-point angles and energies (Hartree) in `result.data`; convert relative energies to kcal/mol (× 627.509) for the rotation barrier.

---

### Multistage Optimization

Progressive refinement with multiple methods.

```python
workflow = rowan.submit_multistage_optimization_workflow(
    mol,
    name="multistage opt"
)
```

Progressively refines the geometry (e.g. xTB → NNP → DFT) using built-in stage settings. **Result:** optimized structure plus per-stage energies in `result.data`.

---

### Transition State Search

Find a transition-state geometry. v3 exposes a double-ended (reactant/product) TS search and an IRC workflow; there is no single-`submit_ts_search_workflow`.

```python
# Double-ended TS search (provide reactant/product endpoints in the inputs)
workflow = rowan.submit_double_ended_ts_search_workflow(
    mol,
    name="TS search"
)

# Intrinsic reaction coordinate from a TS
irc = rowan.submit_irc_workflow(ts_mol, name="IRC")
```

**Output:** transition-state structure, the imaginary frequency, and barrier information in `result.data`.

---

### Strain Calculation

Calculate ligand strain energy.

```python
workflow = rowan.submit_strain_workflow(
    mol,
    name="strain"
)
```

**Output:**
- `strain_energy`: Conformational strain (kcal/mol)
- `reference_energy`: Lowest energy conformer energy

---

### Electronic Properties (orbitals)

Calculate frontier-orbital energies and related electronic properties. (The workflow type is `electronic_properties`; there is no `orbitals` type.)

```python
workflow = rowan.submit_electronic_properties_workflow(
    mol,
    name="electronic properties"
)
```

**Output:**
- HOMO / LUMO energies and HOMO-LUMO gap
- additional electronic descriptors in `result.data`

---

## Protein-Ligand Workflows

### Docking

Dock ligand to protein binding site.

```python
workflow = rowan.submit_docking_workflow(
    protein=protein_uuid,           # UUID or Protein object
    pocket=[[10.0, 20.0, 30.0],     # center (Å)
            [20.0, 20.0, 20.0]],    # box size (Å)
    initial_molecule=mol,
    executable="vina",              # "vina" or "qvina2"
    scoring_function="vinardo",     # "vina" or "vinardo"
    exhaustiveness=8,
    do_csearch=False,               # conformer search before docking
    do_optimization=False,          # optimize conformers
    do_pose_refinement=True,        # refine poses (default True)
    name="docking"
)
```

**Result (`DockingResult`):**
- `result.scores`: list of `DockingScore` (sorted best-first), each with `.score` (kcal/mol), `.strain`, `.rmsd`, `.posebusters_valid`, `.pose`
- `result.best_pose`: top pose as `stjames.Molecule`
- `result.get_poses()`: all poses as molecules

---

### Batch Docking

Screen multiple ligands against one target.

```python
workflow = rowan.submit_batch_docking_workflow(
    smiles_list=["CCO", "c1ccccc1", "CC(=O)O"],   # note: smiles_list is first
    protein=protein_uuid,
    pocket=[[cx, cy, cz], [sx, sy, sz]],
    executable="qvina2",
    scoring_function="vina",
    name="batch docking"
)
```

**Result (`BatchDockingResult`):** `result.scores` holds the per-ligand docking scores (same `DockingScore` fields as single docking); rank ligands by their best score.

---

### Protein Cofolding

Predict protein-ligand complex structure using AI.

```python
workflow = rowan.submit_protein_cofolding_workflow(
    initial_protein_sequences=["MSKGEELFT..."],
    initial_smiles_list=["CCO"],
    model="boltz_2",        # "chai_1r" | "boltz_1" | "boltz_2" | "openfold_3"
    use_msa_server=True,    # build an MSA (default True; improves accuracy)
    use_potentials=False,   # apply physical-potential refinement
    num_samples=None,       # number of predictions to generate
    compute_strain=False,   # calculate ligand strain
    do_pose_refinement=False,
    name="cofolding"
)
```

**Models:** `chai_1r`, `boltz_1`, `boltz_2` (recommended), `openfold_3`. There is no `boltz_1x`.

**Result (`ProteinCofoldingResult`):**
- `result.predictions`: list of per-sample `CofoldingResult`
- each prediction's `.scores.ptm` and `.scores.iptm` (predicted TM / interface confidence, 0-1), `.scores.avg_lddt`
- `result.affinity_score` (if `ligand_binding_affinity_index` was set)
- `result.predicted_structure_uuid` for the predicted structure

---

### Pose-Analysis MD

Molecular dynamics simulation of docked pose.

```python
workflow = rowan.submit_pose_analysis_md_workflow(
    # protein + docked pose inputs; see the function signature for required args
    name="pose MD"
)
```

**Output:** a short MD trajectory plus ligand RMSD / interaction analysis in `result.data`.

> For full, long-timescale explicit-solvent MD trajectories and trajectory analysis, that is a separate molecular-dynamics tool, not this Rowan skill — Rowan's `pose_analysis_md` is a short pose-stability check.

---

## Spectroscopy Workflows

### NMR Prediction

Predict NMR chemical shifts.

```python
workflow = rowan.submit_nmr_workflow(
    initial_molecule=mol,
    name="NMR"
)
```

**Output:**
- `h_shifts`: ¹H chemical shifts (ppm)
- `c_shifts`: ¹³C chemical shifts (ppm)
- `coupling_constants`: J-coupling values

---

### Ion Mobility

Predict collision cross-section for mass spectrometry.

```python
workflow = rowan.submit_ion_mobility_workflow(
    initial_molecule=mol,
    name="ion mobility"
)
```

**Output:**
- `ccs`: Collision cross-section (Å²)
- `conformer_ccs`: CCS per conformer

---

## Advanced Workflows

### Molecular Descriptors

Calculate comprehensive descriptor set.

```python
workflow = rowan.submit_descriptors_workflow(
    initial_molecule=mol,
    name="descriptors"
)
```

**Output:**
- 2D descriptors (RDKit-based)
- 3D descriptors (xTB-based)
- Electronic descriptors

---

### MSA (Multiple Sequence Alignment)

Generate MSA for protein sequences.

```python
workflow = rowan.submit_msa_workflow(
    initial_protein_sequences=["MSKGEELFT..."],   # not `sequences=`
    output_formats={"colabfold"},                 # optional: colabfold | chai | boltz
    name="MSA"
)
```

**Output:** the alignment(s) in the requested format(s), accessible via `result.data` / the typed `MSAResult`.

---

### Protein Binder Design (BoltzGen)

Design protein binders.

```python
workflow = rowan.submit_protein_binder_design_workflow(
    # target sequence + hotspot residues; see the function signature
    name="binder design"
)
```

**Output:**
- designed binder sequences and per-design confidence in `result.data`

---

## Workflow Parameters Reference

### Common Parameters

All workflow submission functions accept:

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Workflow name (optional) |
| `folder_uuid` / `folder` | str / Folder | Organize in folder |
| `max_credits` | int | Credit limit |
| `webhook_url` | str | URL Rowan POSTs to on completion |
| `is_draft` | bool | Submit without starting (call `submit_draft()` later) |

### Method Selection

For basic calculations, pass `tasks` plus `method`/`basis_set`/`preset` as direct keyword arguments (not a `workflow_data` dict):

```python
workflow = rowan.submit_basic_calculation_workflow(
    mol,
    tasks=["optimize"],
    method="gfn2_xtb",        # or e.g. "aimnet2_wb97md3"
    basis_set="def2-SVP",     # for DFT
    # or instead use a preset:
    # preset="organic_nnp",   # general_nnp | organic_nnp | rapid_semiempirical | routine_dft | careful_dft
)
```

**Method families:**
- Neural network potentials (e.g. AIMNet2, Egret)
- Semiempirical: `gfn1_xtb`, `gfn2_xtb`
- DFT: hybrid/GGA functionals with selectable basis sets

The exact accepted method strings come from `stjames.Method`; the `preset` argument is the simplest way to pick a sensible level of theory.
