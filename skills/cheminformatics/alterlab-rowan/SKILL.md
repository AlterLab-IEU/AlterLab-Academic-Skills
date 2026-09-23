---
name: alterlab-rowan
description: Drives the Rowan cloud quantum-chemistry platform via its Python API for computational chemistry — pKa prediction, geometry optimization, conformer searching, molecular property calculations, protein-ligand docking (AutoDock Vina), and AI protein cofolding (Chai-1, Boltz-1/2), with cloud compute and no local setup. Use when running DFT or semiempirical methods, neural network potentials (AIMNet2), molecular property or protein-ligand binding predictions, or automated computational chemistry pipelines. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*)
compatibility: "Requires a Rowan account and API key (ROWAN_API_KEY); jobs run on Rowan's cloud and consume credits, and submitted structures are sent to Rowan's servers. rowan-python >= 3.2, Python >= 3.12."
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    last_updated: "2026-09-23"
---

# Rowan: Cloud-Based Quantum Chemistry Platform

## Overview

Rowan is a cloud-based computational chemistry platform that provides programmatic access to quantum chemistry workflows through a Python API. It enables automation of complex molecular simulations without requiring local computational resources or expertise in multiple quantum chemistry packages.

**Key Capabilities:**
- Molecular property prediction (pKa, redox potential, solubility, ADMET-Tox)
- Geometry optimization and conformer searching
- Protein-ligand docking with AutoDock Vina
- AI-powered protein cofolding with Chai-1 and Boltz models
- Access to DFT, semiempirical, and neural network potential methods
- Cloud compute with automatic resource allocation

**Why Rowan:**
- No local compute cluster required
- Unified API for dozens of computational methods
- Results viewable in web interface at labs.rowansci.com
- Automatic resource scaling

## When to Use This Skill

Use this skill when the user wants to:
- Predict pKa / macro-pKa, redox potentials, solubility, or other properties without local QM software
- Run geometry optimizations, conformer searches, or single points with NNPs (AIMNet2, Egret), xTB, or DFT in the cloud
- Dock ligands (Vina/GNINA) or co-fold protein–ligand complexes (Boltz, Chai-1, OpenFold3) as managed cloud jobs
- Script and batch these jobs from Python (`rowan-python`), organized in folders with credit caps

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Running and analyzing a local OpenMM MD trajectory (RMSD/RMSF, contacts) | `alterlab-molecular-dynamics` |
| Open-source, local diffusion docking with DiffDock (no cloud account) | `alterlab-diffdock` |
| Running Boltz-2 or Chai-1 locally on your own GPU | `alterlab-boltz` or `alterlab-chai` |
| Local conformers, descriptors, or RDKit force-field minimization | `alterlab-rdkit` |

## Installation and Authentication

### Installation

Requires Python >= 3.12. This skill targets `rowan-python` 3.x (current 3.2.0 as of 2026-09; v2 had a different result API).

```bash
uv pip install "rowan-python>=3.2"
```

Installing `rowan-python` also pulls in `stjames` (molecule/result models) and `rdkit`.

### Authentication

Generate an API key at [labs.rowansci.com/account/api-keys](https://labs.rowansci.com/account/api-keys).

**Option 1: Direct assignment**
```python
import rowan
rowan.api_key = "your_api_key_here"
```

**Option 2: Environment variable (recommended)**
```bash
export ROWAN_API_KEY="your_api_key_here"
```

The API key is automatically read from `ROWAN_API_KEY` on module import.

### Verify Setup

```python
import rowan

# Check authentication
user = rowan.whoami()
print(f"Logged in as: {user.username}")
print(f"Credits available: {user.credits}")
```

## The Result Pattern (read this first)

Every `submit_*_workflow` returns a `Workflow`. Do NOT read `workflow.data[...]` by hand and do NOT call the deprecated `wait_for_result()`. The v3 idiom is a single call:

```python
mol = rowan.Molecule.from_smiles("c1ccccc1O")   # 3D structure for the default 3D method
workflow = rowan.submit_pka_workflow(mol, name="phenol pKa")
result = workflow.result()        # blocks until done, returns a typed WorkflowResult
print(result.strongest_acid)      # typed attribute access, not a dict key
```

Key facts:
- `workflow.result(wait=True, poll_interval=5)` blocks, fetches, and raises `rowan.WorkflowError` if the workflow failed or was stopped. Use `wait=False` to grab whatever is ready without blocking.
- `workflow.status` is the **integer** enum `stjames.Status` (`QUEUED=0, RUNNING=1, COMPLETED_OK=2, FAILED=3, STOPPED=4, AWAITING_QUEUE=5, DRAFT=6, PREEMPTED=7`), not a string. Use `workflow.done()` / `workflow.is_finished()` rather than comparing to `"completed"`.
- **Geometry-based workflows now reject a bare SMILES string.** As of rowan-python 3.x, `submit_basic_calculation_workflow`, `submit_docking_workflow`, and any 3D pKa/conformer method call `require_coordinates`, which raises `ValueError` on a SMILES with no coordinates. Build a 3D molecule first: `mol = rowan.Molecule.from_smiles("CCO")` (or `stjames.Molecule.from_smiles(...)`, which auto-generates coordinates), then pass `mol`. A SMILES string is still accepted by SMILES-based methods (`submit_macropka_workflow`, and pKa with `method="starling"`/`"chemprop_nevolianis2025"`). `Molecule.from_smiles(smiles)` takes only the SMILES (no `charge=`/`multiplicity=` kwargs).

## Core Workflows

### 1. pKa Prediction

Predict micro-pKa / acid dissociation constants:

```python
import rowan

# The default pKa method is now a 3D method, so build a molecule (bare SMILES is rejected).
workflow = rowan.submit_pka_workflow(
    rowan.Molecule.from_smiles("c1ccccc1O"),   # Phenol
    name="phenol pKa calculation",
    pka_range=(2, 12),                  # default
    method="gxtb_wagen2026",            # default (g-xTB); "aimnet2_wagen2024" also 3D.
                                        # "starling" / "chemprop_nevolianis2025" take a SMILES string.
)

result = workflow.result()
print(f"Strongest acid pKa: {result.strongest_acid}")
print(f"Strongest base pKa: {result.strongest_base}")
```

For macroscopic pKa, microstate populations vs. pH, isoelectric point, and logD/solubility-vs-pH, use `rowan.submit_macropka_workflow(...)` and read `result.pka_values`, `result.microstates`, `result.isoelectric_point`.

### 2. Conformer Search

Generate and rank a conformer ensemble:

```python
import rowan

workflow = rowan.submit_conformer_search_workflow(
    "CCCC",  # Butane
    name="butane conformer search",
    final_method="aimnet2_wb97md3",     # NNP; default
)

result = workflow.result()
print(f"Found {result.num_conformers} conformers")
for energy in result.get_energies():   # relative energies, kcal/mol
    print(f"  ΔE = {energy:.2f} kcal/mol")
lowest = result.get_conformer(0)       # stjames.Molecule of the lowest-energy conformer
```

### 3. Geometry Optimization

`submit_basic_calculation_workflow` is task-driven: pass `tasks` (e.g. `["optimize"]`, `["energy"]`, `["optimize", "frequencies"]`), not a `workflow_type` string.

```python
import rowan

workflow = rowan.submit_basic_calculation_workflow(
    rowan.Molecule.from_smiles("CC(=O)O"),  # Acetic acid (needs 3D coords; SMILES is rejected)
    tasks=["optimize"],
    preset="organic_nnp",     # quick NNP preset; or set method=/basis_set= explicitly
    name="acetic acid optimization",
)

result = workflow.result()
print(f"Final energy: {result.energy} Hartree")
optimized_mol = result.molecule   # stjames.Molecule with optimized coordinates
```

### 4. Protein-Ligand Docking

Dock small molecules to protein targets. The pocket is `[[center_x, center_y, center_z], [size_x, size_y, size_z]]` in Angstroms — a list of two 3-vectors, NOT a dict.

```python
import rowan

# Create protein from a PDB ID (fetched from RCSB)
protein = rowan.create_protein_from_pdb_id(name="EGFR kinase", code="1M17")
protein.sanitize()   # strip waters/ions, fix residues

pocket = [[10.0, 20.0, 30.0],    # center (Å)
          [20.0, 20.0, 20.0]]    # box size (Å)

workflow = rowan.submit_docking_workflow(
    protein=protein,             # Protein object or its .uuid
    pocket=pocket,
    # 3D input required — a bare SMILES string raises ValueError
    initial_molecule=rowan.Molecule.from_smiles("Cc1ccc(NC(=O)c2ccc(CN3CCN(C)CC3)cc2)cc1"),
    # engine options go in docking_settings; the loose scoring_function=/exhaustiveness=
    # kwargs are deprecated (rowan.GninaSettings selects GNINA instead of Vina)
    docking_settings=rowan.VinaSettings(scoring_function="vinardo"),  # or "vina"
    name="EGFR docking",
)

result = workflow.result()
best = result.scores[0]          # DockingScore, sorted best-first
print(f"Best docking score: {best.score} kcal/mol")
best_pose = result.best_pose     # stjames.Molecule of the top pose
```

### 5. Protein Cofolding (AI Structure Prediction)

Predict protein-ligand complex structures using AI models:

```python
import rowan

protein_seq = "MENFQKVEKIGEGTYGVVYKARNKLTGEVVALKKIRLDTETEGVPSTAIREISLLKELNHPNIVKLLDVIHTENKLYLVFEFLHQDLKKFMDASALTGIPLPLIKSYLFQLLQGLAFCHSHRVLHRDLKPQNLLINTEGAIKLADFGLARAFGVPVRTYTHEVVTLWYRAPEILLGCKYYSTAVDIWSLGCIFAEMVTRRALFPGDSEIDQLFRIFRTLGTPDEVVWPGVTSMPDYKPSFPKWARQDFSKVVPPLDEDGRSLLSQMLHYDPNKRISAKAALAHPFFQDVTKPVPHLRL"
ligand = "CCC(C)CN=C1NCC2(CCCOC2)CN1"

workflow = rowan.submit_protein_cofolding_workflow(
    initial_protein_sequences=[protein_seq],
    initial_smiles_list=[ligand],
    name="kinase-ligand cofolding",
    model="chai_1r",   # default is "boltz_2"; see note below for the full list
)

result = workflow.result()
top = result.predictions[0]            # first CofoldingResult sample
print(f"pTM: {top.scores.ptm}")        # predicted TM score (0-1)
print(f"interface pTM: {top.scores.iptm}")
```

> Note: in rowan-python 3.2 the cofolding model strings are `chai_1r`, `boltz_1`, `boltz_2` (default), `boltz_2_1`, `openfold_3`, and `decaf_boltz` (there is no `boltz_1x`). Confidence lives on `result.scores` / each prediction's `.scores` as `.ptm` and `.iptm`.

## Workflow Management

### List and Query Workflows

```python
# List recent workflows (page is 0-indexed; default size=10)
workflows = rowan.list_workflows(size=10)
for wf in workflows:
    print(f"{wf.name}: {wf.status.name}")   # status is an int enum

# Filter by type / name substring / folder
pka_runs = rowan.list_workflows(workflow_type="pka", name_contains="phenol")
folder_runs = rowan.list_workflows(parent_uuid=folder.uuid)

# Retrieve specific workflow
workflow = rowan.retrieve_workflow("workflow-uuid")
```

### Batch Operations

```python
# Submit many workflows of one type at once. This is a thin loop over the generic
# submit_workflow: it skips the per-type input checks the submit_*_workflow helpers do,
# so pass workflow_data= for non-default settings.
workflows = rowan.batch_submit_workflow(
    workflow_type="pka",
    initial_smileses=["CCO", "CC(=O)O", "c1ccccc1O"],
)

# Non-blocking status poll: returns {uuid: status_int} (stjames.Status values)
statuses = rowan.batch_poll_status([wf.uuid for wf in workflows])
```

### Folder Organization

```python
# Create folder for project
folder = rowan.create_folder(name="Drug Discovery Project")

# Submit workflow to folder
workflow = rowan.submit_pka_workflow(
    rowan.Molecule.from_smiles("CCO"),
    name="compound pKa",
    folder=folder,          # or folder_uuid=folder.uuid (not both)
)

# List workflows in folder
folder_workflows = rowan.list_workflows(parent_uuid=folder.uuid)
```

## Computational Methods

Rowan supports multiple levels of theory:

**Neural Network Potentials:**
- AIMNet2 (ωB97M-D3) - Fast and accurate
- Egret - Rowan's proprietary model

**Semiempirical:**
- GFN1-xTB, GFN2-xTB - Fast for large molecules

**DFT:**
- B3LYP, PBE, ωB97X variants
- Multiple basis sets available

Methods are automatically selected based on workflow type, or can be specified explicitly in workflow parameters.

## Reference Documentation

For detailed API documentation, consult these reference files:

- **`references/api_reference.md`**: Workflow class, submission functions, retrieval methods, the result pattern
- **`references/workflow_types.md`**: The full set of workflow types with parameters - pKa, docking, cofolding, etc.
- **`references/molecule_handling.md`**: stjames.Molecule class - creating molecules from SMILES, XYZ, RDKit
- **`references/proteins_and_organization.md`**: Protein upload, folder management, project organization
- **`references/results_interpretation.md`**: Understanding workflow outputs, confidence scores, validation

## Common Patterns

### Pattern 1: Property Prediction Pipeline

Submit everything first, then collect results — submission is non-blocking, `result()` blocks.

```python
import rowan

smiles_list = ["CCO", "c1ccccc1O", "CC(=O)O"]

# Submit all pKa calculations (default 3D method -> build molecules from the SMILES)
workflows = [
    rowan.submit_pka_workflow(rowan.Molecule.from_smiles(smi), name=f"pKa: {smi}")
    for smi in smiles_list
]

# Collect results
for wf in workflows:
    result = wf.result()
    print(f"{wf.name}: pKa = {result.strongest_acid}")
```

### Pattern 2: Virtual Screening

For screening a library against one target, prefer the dedicated batch-docking workflow over a Python loop.

```python
import rowan

protein = rowan.upload_protein(name="Drug Target", file_path="target.pdb")
protein.sanitize()

pocket = [[x, y, z], [20.0, 20.0, 20.0]]   # center, size (Å)

workflow = rowan.submit_batch_docking_workflow(
    smiles_list=compound_library,
    protein=protein,
    pocket=pocket,
    name="library screen",
)
result = workflow.result()
```

### Pattern 3: Conformer-Based Analysis

```python
import rowan

conf_wf = rowan.submit_conformer_search_workflow(
    "C1CCCCC1",  # any SMILES
    name="conformer search",
)
result = conf_wf.result()

energies = result.get_energies()   # relative energies, kcal/mol, ascending
print(f"Found {result.num_conformers} conformers")
print(f"Energy range: {energies[0]:.2f} to {energies[-1]:.2f} kcal/mol")
```

## Best Practices

1. **Set API key via environment variable** for security and convenience
2. **Use folders** to organize related workflows
3. **Use `workflow.result()`** — it waits, fetches, and raises on failure in one call
4. **Use batch functions** (`batch_submit_workflow`, `submit_batch_docking_workflow`) for many similar jobs
5. **Cap spend with `max_credits=`** on any submission, and check `rowan.whoami().credits`

## Error Handling

`workflow.result()` raises `rowan.WorkflowError` if the workflow failed or was stopped, so wrap it:

```python
import rowan

workflow = rowan.submit_pka_workflow(
    rowan.Molecule.from_smiles("c1ccccc1O"), name="calculation", max_credits=10
)   # input problems (e.g. a bare SMILES for a 3D method) raise ValueError at submit time

try:
    result = workflow.result()       # blocks until done; raises on failure
    print(result.strongest_acid)
except rowan.WorkflowError as e:
    # workflow failed/stopped — inspect workflow.logfile for details
    print(f"Workflow failed: {e}")
    print(workflow.logfile)
```

`workflow.status` is the int enum `stjames.Status`; check `workflow.done()` for a non-blocking finished test.

## Additional Resources

- **Web Interface**: https://labs.rowansci.com
- **Documentation**: https://docs.rowansci.com
- **Tutorials**: https://docs.rowansci.com/tutorials

Part of the AlterLab Academic Skills suite.
