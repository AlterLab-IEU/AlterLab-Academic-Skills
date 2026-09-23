---
name: alterlab-benchling
description: Integrates the Benchling R&D platform via its REST API and SDK — access the registry (DNA, proteins), inventory, ELN entries and workflows, build Benchling Apps, and query the Benchling Data Warehouse. Use when automating Benchling lab data management, syncing sample registry or inventory records, scripting ELN entries/workflows, or running SQL against the Benchling Data Warehouse. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(curl:*) Bash(python:*)
compatibility: Requires a Benchling tenant with API access plus an API key or OAuth app credentials; benchling-sdk 1.x (current 1.25.0, Python >=3.9)
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# Benchling Integration

## Overview

Benchling is a cloud platform for life sciences R&D. Access registry entities (DNA, proteins), inventory, electronic lab notebooks, and workflows programmatically via Python SDK and REST API.

## When to Use This Skill

This skill should be used when:
- Working with Benchling's Python SDK or REST API
- Managing biological sequences (DNA, RNA, proteins) and registry entities
- Automating inventory operations (samples, containers, locations, transfers)
- Creating or querying electronic lab notebook entries
- Building workflow automations or Benchling Apps
- Syncing data between Benchling and external systems
- Querying the Benchling Data Warehouse for analytics
- Setting up event-driven integrations with AWS EventBridge

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| LabArchives notebooks, entries, attachments, or backups | `alterlab-labarchive` |
| Finding, writing, or publishing protocols on protocols.io | `alterlab-protocolsio` |
| FAIR dataset registries, ontology curation, and lineage with LaminDB | `alterlab-lamindb` |
| Sequence parsing and manipulation outside Benchling (FASTA/GenBank I/O) | `alterlab-biopython` |
| Running bioinformatics pipelines on DNAnexus or LatchBio | `alterlab-dnanexus` / `alterlab-latchbio` |

## Core Capabilities

### 1. Authentication & Setup

**Python SDK Installation:**
```bash
# Stable release (benchling-sdk 1.x; current 1.25.0, requires Python >= 3.9)
uv add "benchling-sdk>=1.25,<2"
# or for a throwaway script env
uv pip install benchling-sdk
```
The SDK follows SDK-level semver, not the API version, so check the changelog before bumping a major.

**Authentication Methods:**

API Key Authentication (recommended for scripts):
```python
import os
from benchling_sdk.benchling import Benchling
from benchling_sdk.auth.api_key_auth import ApiKeyAuth

benchling = Benchling(
    url="https://your-tenant.benchling.com",
    auth_method=ApiKeyAuth(os.environ["BENCHLING_API_KEY"])
)
```

OAuth Client Credentials (for apps):
```python
from benchling_sdk.auth.client_credentials_oauth2 import ClientCredentialsOAuth2

auth_method = ClientCredentialsOAuth2(
    client_id="your_client_id",
    client_secret=os.environ["BENCHLING_CLIENT_SECRET"]
)
benchling = Benchling(
    url="https://your-tenant.benchling.com",
    auth_method=auth_method
)
```

**Key Points:**
- API keys are obtained from Profile Settings in Benchling
- Keep credentials in environment variables or a secret manager, never in code or notebooks
- All API requests require HTTPS
- Authentication permissions mirror user permissions in the UI

For detailed authentication information including OIDC and security best practices, refer to `references/authentication.md`.

### 2. Registry & Entity Management

Registry entities include DNA sequences, RNA sequences, AA sequences, custom entities, and mixtures. The SDK provides typed classes for creating and managing these entities.

**Creating DNA Sequences:**
```python
from benchling_sdk.models import DnaSequenceCreate
from benchling_sdk.helpers.serialization_helpers import fields

sequence = benchling.dna_sequences.create(
    DnaSequenceCreate(
        name="My Plasmid",
        bases="ATCGATCG",
        is_circular=True,
        folder_id="fld_abc123",
        schema_id="ts_abc123",  # optional
        fields=fields({"gene_name": {"value": "GFP"}})
    )
)
```

**Registry Registration:**

To register an entity directly upon creation, set `registry_id` (which registry
to register into) plus a `naming_strategy` (how the registry ID is assigned).
`naming_strategy` must be the `NamingStrategy` enum — a plain string fails when
the request is serialized:
```python
from benchling_sdk.models import DnaSequenceCreate, NamingStrategy

sequence = benchling.dna_sequences.create(
    DnaSequenceCreate(
        name="My Plasmid",
        bases="ATCGATCG",
        is_circular=True,
        folder_id="fld_abc123",
        registry_id="src_abc123",                 # registry to register into
        naming_strategy=NamingStrategy.NEW_IDS,   # or NamingStrategy.IDS_FROM_NAMES
    )
)
```

**Important:** `registry_id` is what triggers registration. There is a separate
`entity_registry_id` field for assigning a specific registry ID directly — and
you **cannot** set both `entity_registry_id` and `naming_strategy` at the same
time (use one or the other for ID assignment).

**Updating Entities:**
```python
from benchling_sdk.models import DnaSequenceUpdate
from benchling_sdk.helpers.serialization_helpers import fields

updated = benchling.dna_sequences.update(
    dna_sequence_id="seq_abc123",
    dna_sequence=DnaSequenceUpdate(
        name="Updated Plasmid Name",
        fields=fields({"gene_name": {"value": "mCherry"}})
    )
)
```

Unspecified fields remain unchanged, allowing partial updates.

**Listing and Pagination:**
```python
# List DNA sequences (a PageIterator that yields pages lazily)
sequences = benchling.dna_sequences.list(schema_id="ts_abc123")  # server-side filters
for page in sequences:
    for seq in page:
        print(f"{seq.name} ({seq.id})")

# Check total count
total = sequences.estimated_count()
```

**Key Operations** (method/parameter names are entity-specific; see `references/sdk_reference.md`):
- Create: `benchling.<entity_type>.create(<CreateModel>)`
- Read: `benchling.<entity_type>.get_by_id(<entity>_id=...)` or `.list(...)`
- Update: `benchling.<entity_type>.update(<entity>_id=..., <entity>=<UpdateModel>)`
- Archive: `benchling.<entity_type>.archive(<entity>_ids=[...], reason=EntityArchiveReason.MADE_IN_ERROR)` (bulk)

Entity types: `dna_sequences`, `rna_sequences`, `aa_sequences`, `custom_entities`, `mixtures`

For comprehensive SDK reference and advanced patterns, refer to `references/sdk_reference.md`.

### 3. Inventory Management

Manage physical samples, containers, boxes, and locations within the Benchling inventory system.

**Creating Containers:**
```python
from benchling_sdk.models import ContainerCreate
from benchling_sdk.helpers.serialization_helpers import fields

container = benchling.containers.create(
    ContainerCreate(
        name="Sample Tube 001",
        schema_id="cont_schema_abc123",
        parent_storage_id="box_abc123",  # optional
        fields=fields({"concentration": {"value": "100 ng/μL"}})
    )
)
```

**Managing Boxes:**
```python
from benchling_sdk.models import BoxCreate

box = benchling.boxes.create(
    BoxCreate(
        name="Freezer Box A1",
        schema_id="box_schema_abc123",
        parent_storage_id="loc_abc123"
    )
)
```

**Transferring Items:**

There is no `containers.transfer(...)` convenience method. Move contents between
containers with `transfer_into_container` (single) or `transfer_into_containers`
(bulk, returns a `TaskHelper`), passing a `ContainerTransfer` request object:
```python
from benchling_sdk.models import ContainerTransfer

benchling.containers.transfer_into_container(
    destination_container_id="cont_xyz789",
    transfer_request=ContainerTransfer(...),  # source_entity_id/source_container_id, transfer_quantity, ...
)
```
To relocate a container in storage instead (rather than transfer its contents),
update its `parent_storage_id` via `containers.update(...)`. Check-in/out are bulk
calls: `containers.checkout(ContainersCheckout(container_ids=[...], assignee_id=...))`
and `containers.checkin(ContainersCheckin(container_ids=[...]))`.

### 4. Notebook & Documentation

Interact with electronic lab notebook (ELN) entries, protocols, and templates.

**Creating Notebook Entries:**
```python
from benchling_sdk.models import EntryCreate
from benchling_sdk.helpers.serialization_helpers import fields

entry = benchling.entries.create_entry(
    EntryCreate(
        name="Experiment 2026-09-23",
        folder_id="fld_abc123",
        schema_id="entry_schema_abc123",
        fields=fields({"objective": {"value": "Test gene expression"}})
    )
)
```

**Linking Entities to Entries:**

The v2 API cannot write note text or @-mentions into an existing entry:
`EntryUpdate` changes metadata only (`name`, `folder_id`, `schema_id`, `fields`,
`author_ids`). Associate entities with an entry in one of these ways:
- Give the entry schema an entity-link field and set it:
  `benchling.entries.update_entry(entry_id="entry_abc123", entry=EntryUpdate(fields=fields({"plasmid": {"value": "seq_xyz789"}})))`
- Create the entry from a template and pre-fill its tables at creation time with
  `EntryCreate(..., entry_template_id="TEMPLATE_ID", initial_tables=[InitialTable(template_table_id="TABLE_ID", csv_data="...")])`
- Record assay results/runs against the entities (see `references/api_endpoints.md`)

**Key Notebook Operations:**
- Create and update lab notebook entries (`create_entry`, `update_entry`, `get_entry_by_id`, `list_entries`)
- Manage entry templates (`list_entry_templates`, `update_entry_template`)
- Link entities through schema fields or template tables
- Export entries for documentation

### 5. Workflows & Automation

Automate laboratory processes using Benchling's workflow system. In the v2 API a
workflow is a **workflow task group**; tasks are created in a group and carry
schema-defined fields.

**Creating Workflow Tasks:**
```python
from benchling_sdk.models import WorkflowTaskCreate
from benchling_sdk.helpers.serialization_helpers import fields

task = benchling.workflow_tasks.create(
    WorkflowTaskCreate(
        workflow_task_group_id="WORKFLOW_TASK_GROUP_ID",
        assignee_id="USER_ID",            # optional
        fields=fields({"template": {"value": "seq_abc123"}})
    )
)
```

**Updating Task Status:**
```python
from benchling_sdk.models import WorkflowTaskUpdate

updated_task = benchling.workflow_tasks.update(
    workflow_task_id="WORKFLOW_TASK_ID",
    workflow_task=WorkflowTaskUpdate(
        status_id="COMPLETE_STATUS_ID"
    )
)
```

**Asynchronous Operations:**

Bulk/long-running operations return a `TaskHelper` (benchling-sdk 1.x). Call its
`wait_for_response()` to block until the task succeeds (or `wait_for_completion()`
for the raw task):
```python
# A bulk call returns a TaskHelper, not a plain task id
task = benchling.dna_sequences.bulk_create(...)
result = task.wait_for_response(
    interval_wait_seconds=2,
    max_wait_seconds=300,
)
```
There is no top-level `wait_for_task(benchling, task_id=...)` function in 1.x;
the helper hangs off the returned task object.

**Key Workflow Operations:**
- Create and manage workflow tasks
- Update task statuses and assignments
- Execute bulk operations asynchronously
- Monitor task progress

### 6. Events & Integration

Subscribe to Benchling events (entity create/update/archive, inventory transfers,
workflow task status changes, entry changes, results registration) through AWS
EventBridge: configure event routing in Benchling settings, create EventBridge
rules to filter events, and route them to Lambda functions or other targets that
update external systems (sync to databases, trigger downstream processes, notify,
audit-log). See Benchling's event documentation for event schemas.

### 7. Data Warehouse & Analytics

The Benchling Data Warehouse provides read-only SQL access to tenant data for
analytics and reporting (aggregate results, inventory trends, compliance reports,
exports). Connect with a standard PostgreSQL client or BI tool (Jupyter, Tableau,
Looker, Power BI) using warehouse credentials issued per user
(`benchling.users.get_warehouse_logins(user_id)` lists them).

## Best Practices

### Error Handling

The SDK automatically retries failed requests:
```python
# Automatic retry for 429, 502, 503, 504 status codes
# Up to 5 retries with exponential backoff
# Customize retry behavior if needed
from benchling_sdk.helpers.retry_helpers import RetryStrategy

benchling = Benchling(
    url="https://your-tenant.benchling.com",
    auth_method=ApiKeyAuth(os.environ["BENCHLING_API_KEY"]),
    retry_strategy=RetryStrategy(max_tries=3)
)
```

### Pagination Efficiency

Use generators for memory-efficient pagination:
```python
# Generator-based iteration
for page in benchling.dna_sequences.list():
    for sequence in page:
        process(sequence)

# Check estimated count without loading all pages
total = benchling.dna_sequences.list().estimated_count()
```

### Schema Fields Helper

Use the `fields()` helper for custom schema fields:
```python
# Convert dict to Fields object
from benchling_sdk.helpers.serialization_helpers import fields

custom_fields = fields({
    "concentration": {"value": "100 ng/μL"},
    "date_prepared": {"value": "2026-09-23"},
    "notes": {"value": "High quality prep"}
})
```

### Forward Compatibility

The SDK handles unknown enum values and types gracefully:
- Unknown enum values are preserved
- Unrecognized polymorphic types return `UnknownType`
- Allows working with newer API versions

### Security Considerations

- Rotate keys if compromised, and grant apps only the permissions they need
- Prefer OAuth apps for multi-user or service integrations over personal API keys
- Registry and notebook data can contain unpublished IP or regulated data; follow your institution's data-handling rules before exporting it

## Resources

Load `references/` as needed: **authentication.md** (OIDC, security best
practices, credential management), **sdk_reference.md** (advanced SDK patterns,
all entity types), **api_endpoints.md** (REST endpoints for direct HTTP calls).

## Common Use Cases

**1. Bulk Entity Import:**

For many records prefer a single `bulk_create` (returns a `TaskHelper`) over a
per-record `create` loop — it is one async job instead of N requests. Note the
bulk call takes `DnaSequenceBulkCreate` objects, not `DnaSequenceCreate`:
```python
# Import multiple sequences from a FASTA file in one bulk job
from Bio import SeqIO
from benchling_sdk.models import DnaSequenceBulkCreate

to_create = [
    DnaSequenceBulkCreate(
        name=record.id,
        bases=str(record.seq),
        is_circular=False,
        folder_id="fld_abc123",
    )
    for record in SeqIO.parse("sequences.fasta", "fasta")
]

task = benchling.dna_sequences.bulk_create(to_create)
task.wait_for_response()  # blocks until the bulk job finishes
```
(For a handful of records a plain `benchling.dna_sequences.create(...)` loop with
`DnaSequenceCreate` is fine.)

**2. Inventory Audit:**
```python
# List all containers stored anywhere under a box or location
containers = benchling.containers.list(
    ancestor_storage_id="box_abc123"
)

for page in containers:
    for container in page:
        print(f"{container.name}: {container.barcode}")
```

**3. Workflow Automation:**
```python
from benchling_sdk.models import WorkflowTaskUpdate

# Update all pending tasks in a workflow task group.
# Filter by status via status_ids (a list of status IDs, not a status name)
tasks = benchling.workflow_tasks.list(
    workflow_task_group_ids=["WORKFLOW_TASK_GROUP_ID"],
    status_ids=["PENDING_STATUS_ID"]
)

for page in tasks:
    for task in page:
        # Perform automated checks
        if auto_validate(task):
            benchling.workflow_tasks.update(
                workflow_task_id=task.id,
                workflow_task=WorkflowTaskUpdate(
                    status_id="COMPLETE_STATUS_ID"
                )
            )
```

**4. Data Export:**
```python
# Export all sequences of one schema (filtered server-side)
export_data = []
for page in benchling.dna_sequences.list(schema_id="ts_target_schema"):
    for seq in page:
        export_data.append({
            "id": seq.id,
            "name": seq.name,
            "bases": seq.bases,
            "length": seq.length,
        })

# Then write export_data to CSV/database as needed (e.g. csv.DictWriter).
```

## Additional Resources

- **Official Documentation:** https://docs.benchling.com
- **Python SDK Reference:** https://benchling.com/sdk-docs/
- **API Reference:** https://benchling.com/api/reference
- **Help Center / Support:** https://help.benchling.com

Part of the AlterLab Academic Skills suite.
