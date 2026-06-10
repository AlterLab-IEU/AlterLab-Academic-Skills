---
name: alterlab-rowan
description: Drives the Rowan cloud quantum-chemistry platform via its Python API for computational chemistry — pKa prediction, geometry optimization, conformer searching, molecular property calculations, protein-ligand docking (AutoDock Vina), and AI protein cofolding (Chai-1, Boltz-1/2), with cloud compute and no local setup. Use when running DFT or semiempirical methods, neural network potentials (AIMNet2), molecular property or protein-ligand binding predictions, or automated computational chemistry pipelines. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*)
compatibility: API required
metadata:
    skill-author: AlterLab
    version: "1.1.0"
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

## Installation and Authentication

### Installation

Requires Python >= 3.12. This skill targets `rowan-python` 3.x (the current major version; v2 had a different result API).

```bash
uv pip install "rowan-python>=3.0"
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
workflow = rowan.submit_pka_workflow("c1ccccc1O", name="phenol pKa")
result = workflow.result()        # blocks until done, returns a typed WorkflowResult
print(result.strongest_acid)      # typed attribute access, not a dict key
```

Key facts:
- `workflow.result(wait=True, poll_interval=5)` blocks, fetches, and raises `rowan.WorkflowError` if the workflow failed or was stopped. Use `wait=False` to grab whatever is ready without blocking.
- `workflow.status` is the **integer** enum `stjames.Status` (`QUEUED=0, RUNNING=1, COMPLETED_OK=2, FAILED=3, STOPPED=4`), not a string. Use `workflow.done()` / `workflow.is_finished()` rather than comparing to `"completed"`.
- `submit_*` functions accept a SMILES string, an `stjames.Molecule`, or an RDKit `Mol` directly as `initial_molecule` — you rarely need to build a molecule first. `stjames.Molecule.from_smiles(smiles)` takes only the SMILES (no `charge=`/`multiplicity=` kwargs).

## Core Workflows

### 1. pKa Prediction

Predict micro-pKa / acid dissociation constants:

```python
import rowan

# initial_molecule accepts a SMILES string directly
workflow = rowan.submit_pka_workflow(
    "c1ccccc1O",  # Phenol
    name="phenol pKa calculation",
    pka_range=(2, 12),                  # default
    method="aimnet2_wagen2024",         # default NNP-based pKa model
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
    "CC(=O)O",  # Acetic acid
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
    initial_molecule="Cc1ccc(NC(=O)c2ccc(CN3CCN(C)CC3)cc2)cc1",
    scoring_function="vinardo",  # or "vina"
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
    model="chai_1r",   # or "boltz_1", "boltz_2", "openfold_3"
)

result = workflow.result()
top = result.predictions[0]            # first CofoldingResult sample
print(f"pTM: {top.scores.ptm}")        # predicted TM score (0-1)
print(f"interface pTM: {top.scores.iptm}")
```

> Note: the cofolding model strings are `chai_1r`, `boltz_1`, `boltz_2`, `openfold_3` (there is no `boltz_1x`). Confidence lives on `result.scores` / each prediction's `.scores` as `.ptm` and `.iptm`.

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
# Submit many workflows of one type at once
workflows = rowan.batch_submit_workflow(
    workflow_type="pka",
    initial_smileses=["CCO", "CC(=O)O", "c1ccccc1O"],
)

# Non-blocking status poll (returns a list of {uuid, status, ...} dicts)
statuses = rowan.batch_poll_status([wf.uuid for wf in workflows])
```

### Folder Organization

```python
# Create folder for project
folder = rowan.create_folder(name="Drug Discovery Project")

# Submit workflow to folder
workflow = rowan.submit_pka_workflow(
    "CCO",
    name="compound pKa",
    folder=folder,          # or folder_uuid=folder.uuid
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

# Submit all pKa calculations (SMILES strings are accepted directly)
workflows = [rowan.submit_pka_workflow(smi, name=f"pKa: {smi}") for smi in smiles_list]

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

workflow = rowan.submit_pka_workflow("c1ccccc1O", name="calculation", max_credits=10)

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
