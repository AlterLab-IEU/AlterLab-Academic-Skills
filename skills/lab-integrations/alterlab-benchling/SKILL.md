---
name: alterlab-benchling
description: Integrates the Benchling R&D platform via its REST API and SDK — access the registry (DNA, proteins), inventory, ELN entries and workflows, build Benchling Apps, and query the Benchling Data Warehouse. Use when automating Benchling lab data management, syncing sample registry or inventory records, scripting ELN entries/workflows, or running SQL against the Benchling Data Warehouse. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(curl:*) Bash(python:*)
compatibility: Requires a Benchling account and API key
metadata:
    skill-author: AlterLab
    version: "1.0.0"
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

## Core Capabilities

### 1. Authentication & Setup

**Python SDK Installation:**
```bash
# Stable release (benchling-sdk 1.x; requires Python >= 3.8)
uv add benchling-sdk
# or for a throwaway script env
uv pip install benchling-sdk
```
Pin a recent 1.x in production (e.g. `benchling-sdk>=1.23,<2`); the SDK follows
SDK-level semver, not the API version, so check the changelog before bumping a major.

**Authentication Methods:**

API Key Authentication (recommended for scripts):
```python
from benchling_sdk.benchling import Benchling
from benchling_sdk.auth.api_key_auth import ApiKeyAuth

benchling = Benchling(
    url="https://your-tenant.benchling.com",
    auth_method=ApiKeyAuth("your_api_key")
)
```

OAuth Client Credentials (for apps):
```python
from benchling_sdk.auth.client_credentials_oauth2 import ClientCredentialsOAuth2

auth_method = ClientCredentialsOAuth2(
    client_id="your_client_id",
    client_secret="your_client_secret"
)
benchling = Benchling(
    url="https://your-tenant.benchling.com",
    auth_method=auth_method
)
```

**Key Points:**
- API keys are obtained from Profile Settings in Benchling
- Store credentials securely (use environment variables or password managers)
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
to register into) plus a `naming_strategy` (how the registry ID is assigned):
```python
sequence = benchling.dna_sequences.create(
    DnaSequenceCreate(
        name="My Plasmid",
        bases="ATCGATCG",
        is_circular=True,
        folder_id="fld_abc123",
        registry_id="src_abc123",       # registry to register into
        naming_strategy="NEW_IDS",      # or "IDS_FROM_NAMES"
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
# List all DNA sequences (returns a generator)
sequences = benchling.dna_sequences.list()
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
- Archive: `benchling.<entity_type>.archive(<entity>_ids=[...], reason=<EntityArchiveReason>)` (bulk)

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
(bulk), passing a `ContainerTransfer` request object:
```python
from benchling_sdk.models import ContainerTransfer

benchling.containers.transfer_into_container(
    destination_container_id="cont_xyz789",
    transfer_request=ContainerTransfer(...),  # see API reference for transfer fields
)
```
To relocate a container in storage instead (rather than transfer its contents),
update its `parent_storage_id` via `containers.update(...)`.

**Key Inventory Operations:**
- Create containers, boxes, locations, plates
- Update inventory item properties
- Transfer items between locations
- Check in/out items
- Batch operations for bulk transfers

### 4. Notebook & Documentation

Interact with electronic lab notebook (ELN) entries, protocols, and templates.

**Creating Notebook Entries:**
```python
from benchling_sdk.models import EntryCreate
from benchling_sdk.helpers.serialization_helpers import fields

entry = benchling.entries.create_entry(
    EntryCreate(
        name="Experiment 2025-10-20",
        folder_id="fld_abc123",
        schema_id="entry_schema_abc123",
        fields=fields({"objective": {"value": "Test gene expression"}})
    )
)
```

**Linking Entities to Entries:**

There is no `entry_links` service. Entities are linked into an ELN entry through
the entry's content/notes — by inserting an inline entity reference (an
@-mention link to the entity, e.g. `id="seq_xyz789"`) into a note block of the
entry body, then updating the entry with that content:
```python
from benchling_sdk.models import EntryUpdate

# Build entry content (days/notes) containing an inline link to the entity,
# then persist it via update_entry.
benchling.entries.update_entry(
    entry_id="entry_abc123",
    entry=EntryUpdate(days=[...])  # notes containing the inline entity link
)
```
Confirm the exact note/link model classes (for the inline link block) against
your installed `benchling-sdk` version, since linking is expressed within entry
content rather than via a standalone service.

**Key Notebook Operations:**
- Create and update lab notebook entries
- Manage entry templates
- Link entities and results to entries
- Export entries for documentation

### 5. Workflows & Automation

Automate laboratory processes using Benchling's workflow system.

**Creating Workflow Tasks:**
```python
from benchling_sdk.models import WorkflowTaskCreate
from benchling_sdk.helpers.serialization_helpers import fields

task = benchling.workflow_tasks.create(
    WorkflowTaskCreate(
        name="PCR Amplification",
        workflow_id="wf_abc123",
        assignee_id="user_abc123",
        fields=fields({"template": {"value": "seq_abc123"}})
    )
)
```

**Updating Task Status:**
```python
from benchling_sdk.models import WorkflowTaskUpdate

updated_task = benchling.workflow_tasks.update(
    task_id="task_abc123",
    workflow_task=WorkflowTaskUpdate(
        status_id="status_complete_abc123"
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

Subscribe to Benchling events for real-time integrations using AWS EventBridge.

**Event Types:**
- Entity creation, update, archive
- Inventory transfers
- Workflow task status changes
- Entry creation and updates
- Results registration

**Integration Pattern:**
1. Configure event routing to AWS EventBridge in Benchling settings
2. Create EventBridge rules to filter events
3. Route events to Lambda functions or other targets
4. Process events and update external systems

**Use Cases:**
- Sync Benchling data to external databases
- Trigger downstream processes on workflow completion
- Send notifications on entity changes
- Audit trail logging

Refer to Benchling's event documentation for event schemas and configuration.

### 7. Data Warehouse & Analytics

Query historical Benchling data using SQL through the Data Warehouse.

**Access Method:**
The Benchling Data Warehouse provides SQL access to Benchling data for analytics and reporting. Connect using standard SQL clients with provided credentials.

**Common Queries:**
- Aggregate experimental results
- Analyze inventory trends
- Generate compliance reports
- Export data for external analysis

**Integration with Analysis Tools:**
- Jupyter notebooks for interactive analysis
- BI tools (Tableau, Looker, PowerBI)
- Custom dashboards

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
    auth_method=ApiKeyAuth("your_api_key"),
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
    "date_prepared": {"value": "2025-10-20"},
    "notes": {"value": "High quality prep"}
})
```

### Forward Compatibility

The SDK handles unknown enum values and types gracefully:
- Unknown enum values are preserved
- Unrecognized polymorphic types return `UnknownType`
- Allows working with newer API versions

### Security Considerations

- Never commit API keys to version control
- Use environment variables for credentials
- Rotate keys if compromised
- Grant minimal necessary permissions for apps
- Use OAuth for multi-user scenarios

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
# List all containers in a specific location
containers = benchling.containers.list(
    parent_storage_id="box_abc123"
)

for page in containers:
    for container in page:
        print(f"{container.name}: {container.barcode}")
```

**3. Workflow Automation:**
```python
# Update all pending tasks for a workflow
# Filter by status via status_ids (a list of status IDs, not a status name)
tasks = benchling.workflow_tasks.list(
    workflow_id="wf_abc123",
    status_ids=["status_pending_abc123"]
)

for page in tasks:
    for task in page:
        # Perform automated checks
        if auto_validate(task):
            benchling.workflow_tasks.update(
                task_id=task.id,
                workflow_task=WorkflowTaskUpdate(
                    status_id="status_complete_abc123"
                )
            )
```

**4. Data Export:**
```python
# Export all sequences with specific properties
sequences = benchling.dna_sequences.list()
export_data = []

for page in sequences:
    for seq in page:
        if seq.schema_id == "target_schema_id":
            export_data.append({
                "id": seq.id,
                "name": seq.name,
                "bases": seq.bases,
                "length": len(seq.bases)
            })

# Then write export_data to CSV/database as needed (e.g. csv.DictWriter).
```

## Additional Resources

- **Official Documentation:** https://docs.benchling.com
- **Python SDK Reference:** https://benchling.com/sdk-docs/
- **API Reference:** https://benchling.com/api/reference
- **Support:** [email protected]

