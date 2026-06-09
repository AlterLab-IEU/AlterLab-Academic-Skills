# Rowan API Reference

## Table of Contents

1. [Workflow Class](#workflow-class)
2. [Workflow Submission Functions](#workflow-submission-functions)
3. [Workflow Retrieval Functions](#workflow-retrieval-functions)
4. [Batch Operations](#batch-operations)
5. [Utility Functions](#utility-functions)

---

## Workflow Class

The `Workflow` class represents a submitted computational job.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `uuid` | str | Unique identifier |
| `name` | str | User-assigned name |
| `status` | `stjames.Status` | Int enum: `QUEUED=0, RUNNING=1, COMPLETED_OK=2, FAILED=3, STOPPED=4, AWAITING_QUEUE=5, DRAFT=6, PREEMPTED=7` |
| `created_at` | datetime | Submission timestamp |
| `started_at` | datetime | Execution start (None if not started) |
| `completed_at` | datetime | Completion timestamp (None if not finished) |
| `elapsed` | float | Wall-clock seconds |
| `credits_charged` | float | Credits consumed |
| `data` | dict | Raw workflow results (lazy-loaded; prefer `.result()`) |
| `workflow_type` | str | Type of calculation |
| `parent_uuid` | str | Parent folder UUID |
| `logfile` | str | Log text (useful for diagnosing failures) |

**Note:** `data` is not loaded by default. Use `workflow.result()` for typed access; it fetches for you.

### The result pattern (preferred)

```python
# Block until done, fetch, and return a typed WorkflowResult.
# Raises rowan.WorkflowError if the workflow FAILED or was STOPPED.
result = workflow.result(wait=True, poll_interval=5)

# Non-blocking: return whatever is currently available
partial = workflow.result(wait=False)
```

The returned object is a typed `WorkflowResult` subclass (e.g. `pKaResult`, `DockingResult`) with attribute/property access — see `results_interpretation.md`.

### Methods

#### Status

```python
status = workflow.get_status()       # -> stjames.Status (int enum), re-fetches from API
if workflow.done():                  # non-blocking finished check (also: is_finished())
    print("Done!")

# Deprecated: wait_for_result(poll_interval=5) just blocks and returns self.
# Prefer workflow.result(). (There is no `timeout` argument.)

workflow.fetch_latest(in_place=True)  # refresh fields from API in place
```

#### Data Operations

```python
# Update metadata (only these fields)
workflow.update(name="New name", notes="Additional notes", starred=True)

workflow.delete()        # delete workflow
workflow.delete_data()   # delete only results data, keep metadata

# Downloads (availability depends on workflow type)
workflow.download_dcd_files(output_dir="trajectories/")  # MD trajectories
workflow.download_msa_files(output_dir="msa/")           # MSA / cofolding
```

> There is no `workflow.download_sdf_file` and no `workflow.error_message`. To get poses as structures, use the typed `DockingResult` (`result.best_pose`, `result.get_poses()`); for failure details read `workflow.logfile`.

#### Execution Control

```python
workflow.stop()          # stop a running workflow
workflow.submit_draft()  # start a workflow submitted with is_draft=True
```

---

## Workflow Submission Functions

### Molecule input

Anywhere a function takes `initial_molecule`, you may pass a SMILES `str`, an `stjames.Molecule`, or an RDKit `Chem.Mol`/`RWMol` — the library converts for you. (Some functions, e.g. `submit_macropka_workflow`, take `initial_smiles` instead.)

### Generic Submission

```python
rowan.submit_workflow(
    workflow_type: str,             # one of the supported types, e.g. "pka", "docking", "conformer_search"
    workflow_data: dict | None = None,  # workflow-specific parameters
    initial_molecule: MoleculeInput | None = None,  # SMILES / stjames.Molecule / RDKit Mol
    initial_smiles: str | None = None,
    name: str | None = None,
    folder_uuid: str | Folder | None = None,
    max_credits: int | None = None,
    webhook_url: str | None = None,
    is_draft: bool = False,
) -> Workflow
```

### Specialized Submission Functions

All functions return a `Workflow` object. All accept `initial_molecule` as SMILES/stjames/RDKit, plus the common `name`, `folder_uuid`/`folder`, `max_credits` (int), `webhook_url`, and `is_draft` parameters (omitted below for brevity).

#### Property Prediction

```python
# pKa calculation (micro-pKa)
rowan.submit_pka_workflow(
    initial_molecule,                # SMILES / stjames / RDKit
    pka_range: tuple = (2, 12),
    method: str = "aimnet2_wagen2024",   # also: "gxtb_wagen2026", "chemprop_nevolianis2025", "starling"
    solvent: str | None = "water",
)

# Macroscopic pKa (microstates, pI, logD/solubility vs pH)
rowan.submit_macropka_workflow(
    initial_smiles,                  # NOTE: takes initial_smiles
    min_pH: int = 0, max_pH: int = 14,
    min_charge: int = -2, max_charge: int = 2,
    compute_aqueous_solubility: bool = True,
)

rowan.submit_redox_potential_workflow(initial_molecule, ...)
rowan.submit_solubility_workflow(initial_molecule, ...)
rowan.submit_fukui_workflow(initial_molecule, ...)

# Bond dissociation energy
rowan.submit_bde_workflow(initial_molecule, ...)  # see workflow_types.md for bond-selection params
```

#### Molecular Modeling

```python
# Basic calculation: task-driven (NOT a workflow_type string)
rowan.submit_basic_calculation_workflow(
    initial_molecule,
    tasks: list[str],                # e.g. ["optimize"], ["energy"], ["optimize", "frequencies"]
    method: str | None = None,       # e.g. "aimnet2_wb97md3", "gfn2_xtb"
    basis_set: str | None = None,    # for DFT
    preset: str | None = None,       # "general_nnp" | "organic_nnp" | "rapid_semiempirical" | "routine_dft" | "careful_dft"
)

rowan.submit_conformer_search_workflow(
    initial_molecule,
    final_method: str = "aimnet2_wb97md3",
    transition_state: bool = False,
)

rowan.submit_tautomer_search_workflow(initial_molecule, ...)

# Coordinate / dihedral scan
rowan.submit_scan_workflow(initial_molecule, ...)  # scan settings in workflow_data; see workflow_types.md

# Transition-state search (double-ended / FSM)
rowan.submit_double_ended_ts_search_workflow(initial_molecule, ...)
# Intrinsic reaction coordinate
rowan.submit_irc_workflow(initial_molecule, ...)
```

> There is no `submit_ts_search_workflow` or `submit_dihedral_scan_workflow` in v3 — use `submit_double_ended_ts_search_workflow` and `submit_scan_workflow`.

#### Protein-Ligand Workflows

```python
# Docking — pocket is [[center], [size]], a list of two 3-vectors (Å)
rowan.submit_docking_workflow(
    protein: str | Protein,          # UUID or Protein object
    pocket: list[list[float]],       # [[cx, cy, cz], [sx, sy, sz]]
    initial_molecule,
    executable: str = "vina",        # "vina" or "qvina2"
    scoring_function: str = "vinardo",  # "vina" or "vinardo"
    exhaustiveness: float = 8,
    do_csearch: bool = False,
    do_optimization: bool = False,
    do_pose_refinement: bool = True,
)

# Batch docking — note argument order: smiles_list, protein, pocket
rowan.submit_batch_docking_workflow(
    smiles_list: list[str],
    protein: str | Protein,
    pocket: list[list[float]],
    executable: str = "qvina2",
    scoring_function: str = "vina",
    exhaustiveness: float = 8,
)

# Protein cofolding
rowan.submit_protein_cofolding_workflow(
    initial_protein_sequences: list[str] | None = None,
    initial_dna_sequences: list[str] | None = None,
    initial_rna_sequences: list[str] | None = None,
    initial_smiles_list: list[str] | None = None,
    ligand_binding_affinity_index: int | None = None,
    use_msa_server: bool = True,
    use_potentials: bool = False,
    num_samples: int | None = None,
    compute_strain: bool = False,
    do_pose_refinement: bool = False,
    model: str = "boltz_2",          # "chai_1r" | "boltz_1" | "boltz_2" | "openfold_3"
)
```

#### Spectroscopy & Analysis

```python
rowan.submit_nmr_workflow(initial_molecule, ...)            # NMR shifts
rowan.submit_ion_mobility_workflow(initial_molecule, ...)   # collision cross-section
rowan.submit_descriptors_workflow(initial_molecule, ...)    # molecular descriptors
```

---

## Workflow Retrieval Functions

```python
# Retrieve single workflow by UUID
workflow = rowan.retrieve_workflow(uuid: str) -> Workflow

# Retrieve multiple workflows
workflows = rowan.retrieve_workflows(uuids: list) -> list[Workflow]

# List workflows with filtering
workflows = rowan.list_workflows(
    parent_uuid: str = None,    # Filter by folder
    name_contains: str = None,  # Filter by name (substring)
    status: int = None,         # stjames.Status int value (e.g. 2 == COMPLETED_OK)
    workflow_type: str = None,  # e.g., "pka", "docking"
    starred: bool = None,
    public: bool = None,
    page: int = 0,              # 0-indexed pagination
    size: int = 10              # Results per page
) -> list[Workflow]
```

---

## Batch Operations

```python
# Submit multiple workflows of one type at once
workflows = rowan.batch_submit_workflow(
    workflow_type: str,                 # workflow type for all
    workflow_data: dict | None = None,
    initial_molecules: list | None = None,   # stjames.Molecule / RDKit / SMILES
    initial_smileses: list[str] | None = None,
    names: list[str] | None = None,
    folder_uuid: str | Folder | None = None,
    max_credits: int | None = None,
) -> list[Workflow]

# Poll status of multiple workflows (non-blocking)
statuses = rowan.batch_poll_status(
    uuids: list                 # List of workflow UUIDs
) -> list[dict]                 # one dict per workflow (includes uuid + status)
```

---

## Utility Functions

```python
# Get current user info
user = rowan.whoami() -> User
# user.username, user.email, user.credits, user.weekly_credits

# Convert SMILES to stjames.Molecule
mol = rowan.smiles_to_stjames(smiles: str) -> Molecule

# Get API key from environment
api_key = rowan.get_api_key() -> str

# Low-level API client (context manager wrapping httpx)
with rowan.api_client() as client:
    ...
```

> There is no `rowan.molecule_lookup` (name -> SMILES) in v3. Resolve names to SMILES with an external tool (e.g. RDKit, PubChem) before submitting.

---

## User Class

Returned by `rowan.whoami()`.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `username` | str | Username |
| `email` | str | Email address |
| `firstname` | str | First name |
| `lastname` | str | Last name |
| `credits` | float | Available credits |
| `weekly_credits` | float | Weekly credit allocation |
| `organization` | dict | Organization details |
| `individual_subscription` | dict | Subscription information |

---

## Error Handling

The library raises `rowan.WorkflowError` when you request the result of a failed/stopped workflow, and `requests.HTTPError` on transport/auth/validation failures from the API. (There are no `RowanAPIError` / `AuthenticationError` / `RateLimitError` classes.)

```python
import rowan
import requests

try:
    workflow = rowan.submit_pka_workflow("c1ccccc1O", name="test")
    result = workflow.result()        # raises WorkflowError if it failed/stopped
    print(result.strongest_acid)
except rowan.WorkflowError as e:
    print(f"Workflow failed: {e}")    # inspect workflow.logfile for details
except requests.HTTPError as e:
    print(f"API error: {e}")          # bad key, invalid input, etc.
```

---

## Common Patterns

### Waiting for Multiple Workflows

```python
import rowan
import time

workflows = [rowan.submit_pka_workflow(smi) for smi in smiles_list]

# Poll until all finished (non-blocking)
while not all(wf.done() for wf in workflows):
    time.sleep(10)

# Collect results
for wf in workflows:
    try:
        print(wf.result(wait=False).strongest_acid)
    except rowan.WorkflowError as e:
        print(f"{wf.name}: {e}")
```

### Organizing Workflows in Folders

```python
import rowan

# Top-level folder + subfolder
project = rowan.create_folder("Drug Discovery")
lead_folder = rowan.create_folder("Lead Compounds", parent_uuid=project.uuid)

# Submit to a specific folder
workflow = rowan.submit_pka_workflow(
    "c1ccccc1O",
    name="Lead 1 pKa",
    folder=lead_folder,          # or folder_uuid=lead_folder.uuid
)
```

> `rowan.create_project(name)` exists for top-level projects, but `create_folder` does not accept a `project_uuid` argument — nest folders with `parent_uuid`.
