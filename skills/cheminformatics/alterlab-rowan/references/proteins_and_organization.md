# Rowan Proteins and Organization Reference

## Table of Contents

1. [Protein Management](#protein-management)
2. [Folder Organization](#folder-organization)
3. [Project Management](#project-management)
4. [Best Practices](#best-practices)

---

## Protein Management

### Protein Class

The `Protein` class represents a protein structure stored on Rowan.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `uuid` | str | Unique identifier |
| `name` | str | User-assigned name |
| `data` | str | PDB structure data (lazy-loaded) |
| `sanitized` | bool | Whether structure has been cleaned |
| `pocket` | list[list[float]] | Stored binding pocket `[[center], [size]]`, if set |
| `public` | bool | Public visibility flag |
| `ancestor_uuid` | str | Containing folder UUID |
| `created_at` | datetime | Upload timestamp |

---

### Upload Protein from File

```python
import rowan

# Upload PDB file
protein = rowan.upload_protein(
    name="EGFR Kinase",
    file_path="protein.pdb"
)

print(f"Protein UUID: {protein.uuid}")
print(f"Name: {protein.name}")
```

---

### Create from PDB ID

Fetch structure directly from RCSB PDB database.

```python
import rowan

# Download from PDB
protein = rowan.create_protein_from_pdb_id(
    name="EGFR Kinase (1M17)",
    code="1M17"
)

print(f"Created protein: {protein.uuid}")
```

---

### Retrieve Protein

```python
import rowan

# Get by UUID
protein = rowan.retrieve_protein("protein-uuid")

# List all proteins
proteins = rowan.list_proteins()
for p in proteins:
    print(f"{p.name}: {p.uuid}")

# Filter by name substring
proteins = rowan.list_proteins(name_contains="EGFR")
```

---

### Sanitize Protein

Clean up protein structure (remove waters, artifacts, fix residues).

```python
import rowan

protein = rowan.create_protein_from_pdb_id("Target", "1M17")

# Sanitize the structure
protein.sanitize()

# Check status
print(f"Sanitized: {protein.sanitized}")
```

**Sanitization performs:**
- Removes non-protein molecules (waters, ligands, ions)
- Fixes missing atoms in residues
- Resolves alternate conformations
- Standardizes residue names

---

### Update Protein Metadata

```python
import rowan

protein = rowan.retrieve_protein("protein-uuid")

# Update name
protein.update(name="EGFR Kinase Domain")

# Define binding pocket — [[center], [size]] (Å), same format as docking
protein.update(
    pocket=[[10.0, 20.0, 30.0],
            [20.0, 20.0, 20.0]]
)
```

---

### Download Protein Structure

```python
import rowan

protein = rowan.retrieve_protein("protein-uuid")

# Load structure data
protein.refresh()  # Fetches PDB data if not loaded

# Download to file
protein.download_pdb_file("output.pdb")

# Or access data directly
pdb_content = protein.data
```

---

### Delete Protein

```python
import rowan

protein = rowan.retrieve_protein("protein-uuid")
protein.delete()
```

---

## Folder Organization

### Folder Class

Folders provide hierarchical organization for workflows.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `uuid` | str | Unique identifier |
| `name` | str | Folder name |
| `parent_uuid` | str | Parent folder UUID (None for root) |
| `starred` | bool | Starred status |
| `public` | bool | Public visibility |
| `created_at` | datetime | Creation timestamp |

---

### Create Folder

```python
import rowan

# Create root folder
folder = rowan.create_folder(name="Drug Discovery Project")

# Create subfolder
subfolder = rowan.create_folder(
    name="Lead Compounds",
    parent_uuid=folder.uuid
)
```

---

### Retrieve Folder

```python
import rowan

# Get by UUID
folder = rowan.retrieve_folder("folder-uuid")

# List all folders
folders = rowan.list_folders()
for f in folders:
    print(f"{f.name}: {f.uuid}")

# Filter (name substring)
folders = rowan.list_folders(name_contains="Project", starred=True)
```

---

### Update Folder

```python
import rowan

folder = rowan.retrieve_folder("folder-uuid")

# Rename
folder.update(name="New Name")

# Move to different parent
folder.update(parent_uuid="new-parent-uuid")

# Star folder
folder.update(starred=True)
```

---

### Print Folder Tree

Visualize folder hierarchy.

```python
import rowan

# Print the tree rooted at a given folder UUID (uuid is required)
rowan.print_folder_tree("folder-uuid")

# Or call it on a Folder object
folder = rowan.retrieve_folder("folder-uuid")
folder.print_folder_tree()
```

Output:
```
📁 Drug Discovery Project
├── 📁 Lead Compounds
│   ├── 📄 Lead 1 pKa (completed)
│   └── 📄 Lead 2 pKa (completed)
└── 📁 Backup Series
    └── 📄 Backup 1 conformers (running)
```

---

### Delete Folder

**Warning:** Deleting a folder removes all workflows inside!

```python
import rowan

folder = rowan.retrieve_folder("folder-uuid")
folder.delete()  # Deletes folder and all contents
```

---

### Submit Workflow to Folder

```python
import rowan
import stjames

folder = rowan.create_folder(name="pKa Calculations")

mol = stjames.Molecule.from_smiles("CCO")
workflow = rowan.submit_pka_workflow(
    initial_molecule=mol,
    name="Ethanol pKa",
    folder_uuid=folder.uuid  # Organize in folder
)
```

---

### List Workflows in Folder

```python
import rowan

folder = rowan.retrieve_folder("folder-uuid")
workflows = rowan.list_workflows(parent_uuid=folder.uuid)   # list_workflows uses parent_uuid

for wf in workflows:
    print(f"{wf.name}: {wf.status.name}")
```

---

## Project Management

### Project Class

Projects are top-level containers for organizing folders and workflows.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `uuid` | str | Unique identifier |
| `name` | str | Project name |
| `root_folder_uuid` | str | UUID of the project's root folder (nest folders under this) |
| `created_at` | datetime | Creation timestamp |

---

### Create Project

```python
import rowan

project = rowan.create_project(name="Cancer Drug Discovery")
print(f"Project UUID: {project.uuid}")
```

---

### Retrieve Project

```python
import rowan

# Get by UUID
project = rowan.retrieve_project("project-uuid")

# List all projects
projects = rowan.list_projects()
for p in projects:
    print(f"{p.name}: {p.uuid}")

# Get default project
default = rowan.default_project()
```

---

### Update Project

```python
import rowan

project = rowan.retrieve_project("project-uuid")
project.update(name="Renamed Project")
```

---

### Delete Project

**Warning:** Deletes all folders and workflows in project!

```python
import rowan

project = rowan.retrieve_project("project-uuid")
project.delete()
```

---

### Create Folder Under a Project

`create_folder` does not take a `project_uuid` — nest folders under a project's root folder via `parent_uuid`.

```python
import rowan

project = rowan.create_project("Drug Discovery")
folder = rowan.create_folder(
    name="Phase 1 Compounds",
    parent_uuid=project.root_folder_uuid,
)
```

---

## Best Practices

### Organizing a Drug Discovery Campaign

```python
import rowan

# Create project structure
project = rowan.create_project("EGFR Inhibitor Campaign")
root = project.root_folder_uuid

# Create organized folders under the project's root folder
target_folder = rowan.create_folder("Target Preparation", parent_uuid=root)
hit_folder = rowan.create_folder("Hit Finding", parent_uuid=root)
lead_folder = rowan.create_folder("Lead Optimization", parent_uuid=root)

# Upload and prepare protein
protein = rowan.create_protein_from_pdb_id("EGFR", "1M17")
protein.sanitize()

# Define binding site — [[center], [size]] (Å)
pocket = [[10.0, 20.0, 30.0],   # from crystal ligand
          [20.0, 20.0, 20.0]]

# Submit docking workflows to hit folder
for smiles in hit_compounds:
    workflow = rowan.submit_docking_workflow(
        protein=protein.uuid,
        pocket=pocket,
        initial_molecule=smiles,    # SMILES accepted directly
        name=f"Dock: {smiles[:20]}",
        folder_uuid=hit_folder.uuid
    )
```

### Reusing Proteins Across Workflows

```python
import rowan

# Upload once
protein = rowan.upload_protein("My Target", "target.pdb")
protein.sanitize()

# Save UUID for later use
protein_uuid = protein.uuid

# Use in multiple workflows
for compound in compounds:
    workflow = rowan.submit_docking_workflow(
        protein=protein_uuid,  # Reuse same protein
        pocket=pocket,
        initial_molecule=compound,
        name=f"Dock: {compound.name}"
    )
```

### Folder Naming Conventions

```python
import rowan
from datetime import datetime

# Include date in folder name
date_str = datetime.now().strftime("%Y%m%d")
folder = rowan.create_folder(f"{date_str}_Lead_Optimization")

# Include project phase
folder = rowan.create_folder("Phase2_pKa_Calculations")

# Include target name
folder = rowan.create_folder("EGFR_Conformer_Search")
```

### Cleaning Up Old Workflows

```python
import rowan
import stjames
from datetime import datetime, timedelta

# Find old completed workflows (status filter takes the Status int value)
old_cutoff = datetime.now() - timedelta(days=30)
workflows = rowan.list_workflows(status=stjames.Status.COMPLETED_OK.value)

for wf in workflows:
    if wf.completed_at and wf.completed_at < old_cutoff:
        # Delete data but keep metadata
        wf.delete_data()
        # Or delete entirely
        # wf.delete()
```

### Monitoring Credit Usage

```python
import rowan

# Check before submitting
user = rowan.whoami()
print(f"Available credits: {user.credits}")

# Cap spend per workflow (max_credits is an int)
workflow = rowan.submit_pka_workflow(
    "c1ccccc1O",
    name="pKa calculation",
    max_credits=10,
)
```
