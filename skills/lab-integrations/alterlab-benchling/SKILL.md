---
name: alterlab-benchling
description: Writes Benchling integration code against the official benchling-sdk — registry DNA/protein entities, inventory, ELN entries, workflow tasks, Benchling Apps, Data Warehouse SQL — and validates every create/update payload offline by building the SDK's typed models and serializing them, with no Benchling account; analyses Benchling CSV/warehouse exports locally. Running the code against a tenant is an optional step with the user's own API key or OAuth app. Use when scripting a Benchling registry import, inventory audit, ELN entry or workflow task, checking a Benchling payload or script before it touches a tenant, analysing a Benchling export, or querying the Benchling Data Warehouse. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(curl:*) Bash(python:*) Bash(uv:*)
compatibility: "No API key required to write, validate and test the integration offline: benchling-sdk 1.x (current 1.25.0, Python >=3.9) builds and serializes its request models without a tenant, and exports are analysed locally. Optional: the user's own tenant URL plus an API key or OAuth app to run the code against their data."
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    last_updated: "2026-10-22"
    credentials: "optional: BENCHLING_API_KEY (personal API key — adds reading and writing your own tenant's registry, inventory, notebook and workflows), BENCHLING_CLIENT_SECRET (OAuth app client secret — the same for app or service integrations), BENCHLING_TENANT_URL (your tenant URL; not a secret)"
---

# Benchling Integration

## Overview

Benchling is a cloud platform for life sciences R&D. Its Python SDK and REST API expose registry entities (DNA, proteins), inventory, electronic lab notebooks, and workflows. This skill's core job needs no account: it writes the integration against the SDK, proves the payloads are well-formed offline, and analyses data the user has exported. Only the final run against the user's tenant uses their credentials.

## Keyless Path (default — no Benchling account)

1. **Write the code against the real SDK.** Install it in a throwaway env (`uv run --with "benchling-sdk>=1.25,<2" --with biopython python ...`) and check method names with `inspect.signature` rather than from memory. Verified in benchling-sdk 1.25.0 (2026-10-22): `dna_sequences.create/bulk_create/update/list`, `containers.list(ancestor_storage_id=...)` (there is no `parent_storage_id` filter), `containers.transfer_into_container` (no `containers.transfer`), `entries.create_entry`, `workflow_tasks.create`; bulk calls return a `TaskHelper` (no `wait_for_task` function).
2. **Validate payloads offline.** Every request model serializes with `.to_dict()` — that is the exact JSON body the SDK will send, produced without a network call. The SDK does *not* check bases or ID-assignment rules client-side, so check them yourself:

```python
from Bio import SeqIO
from benchling_sdk.models import DnaSequenceBulkCreate, NamingStrategy

IUPAC_DNA = set("ACGTRYSWKMBDHVN")
records, problems, seen = [], [], set()
for rec in SeqIO.parse("constructs.fasta", "fasta"):
    bases = str(rec.seq).upper()
    if bad := sorted(set(bases) - IUPAC_DNA):          # e.g. 'U' pasted from an mRNA record
        problems.append(f"{rec.id}: non-IUPAC DNA characters {bad}")
    if rec.id in seen:                                   # creates two entities with one name
        problems.append(f"{rec.id}: duplicate name")
    seen.add(rec.id)
    records.append(DnaSequenceBulkCreate(
        name=rec.id, bases=bases, is_circular=True, folder_id="lib_FOLDER",
        registry_id="src_REGISTRY", naming_strategy=NamingStrategy.NEW_IDS))
body = [r.to_dict() for r in records]   # camelCase JSON: folderId, registryId, namingStrategy...
```

   Verified offline: a plain-string `naming_strategy="NEW_IDS"` constructs but fails at `.to_dict()` (`AttributeError: 'str' object has no attribute 'value'`); `entity_registry_id` together with `naming_strategy` serializes fine client-side and is rejected by the server, so flag it before running.
3. **Analyse exports locally.** Inventory, registry and result exports (CSV/XLSX from the web app, or a Data Warehouse extract the user already has) are read with pandas/polars — no credentials.
4. **Hand over the run step.** Deliver the script plus a dry-run summary (what it will create, update or archive, and where). Running it against a tenant is the user's call, with their key; writes to a production registry should go through a test folder or sandbox tenant first.

## Core Capabilities

### 1. Install, and Connect to Your Tenant (optional)

**Python SDK Installation:**
```bash
# Stable release (benchling-sdk 1.x; current 1.25.0, requires Python >= 3.9)
uv add "benchling-sdk>=1.25,<2"
```
The SDK follows SDK-level semver, not the API version, so check the changelog before bumping a major.

**Authentication** — only for running the code against the user's own tenant. API key (scripts):
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
benchling = Benchling(url="https://your-tenant.benchling.com", auth_method=auth_method)
```

**Key Points:**
- API keys are obtained from Profile Settings in Benchling; permissions mirror the user's UI permissions
- Keep credentials in environment variables or a secret manager, never in code or notebooks
- If `BENCHLING_API_KEY` is not set, stop at the validated script and dry-run summary — never fall back to another tenant or invent results

For detailed authentication information including OIDC and security best practices, refer to `references/authentication.md`.

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

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-labarchive`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

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

**Updating Entities:** `benchling.dna_sequences.update(dna_sequence_id="seq_abc123", dna_sequence=DnaSequenceUpdate(name=..., fields=fields({...})))`; unspecified fields remain unchanged (partial update).

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

**Managing Boxes:** `benchling.boxes.create(BoxCreate(name="Freezer Box A1", schema_id="box_schema_abc123", parent_storage_id="loc_abc123"))`.

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

### Error Handling, Pagination, Fields

- The SDK retries 429/502/503/504 up to 5 times with backoff by default (`Benchling(..., retry_strategy=RetryStrategy(max_tries=3))` from `benchling_sdk.helpers.retry_helpers` changes it).
- `list(...)` returns a lazy page iterator: `for page in it: for item in page:`; `it.estimated_count()` avoids loading every page.
- Schema fields go through `fields({"concentration": {"value": "100 ng/μL"}})` (`benchling_sdk.helpers.serialization_helpers`).
- Unknown enum values are preserved and unrecognized polymorphic types return `UnknownType`, so newer API versions do not break parsing.

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
bulk call takes `DnaSequenceBulkCreate` objects, not `DnaSequenceCreate`. Build and
validate `records` offline with the Keyless Path snippet, fix every reported problem, then:
```python
task = benchling.dna_sequences.bulk_create(records)   # needs BENCHLING_API_KEY
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
Without API access, the same report runs offline on a CSV/XLSX export from the
Benchling web app: load it with pandas, filter (archived rows usually excluded), and
state which export and date the numbers come from.

## Additional Resources

- **Official Documentation:** https://docs.benchling.com
- **Python SDK Reference:** https://benchling.com/sdk-docs/
- **API Reference:** https://benchling.com/api/reference
- **Help Center / Support:** https://help.benchling.com

Part of the AlterLab Academic Skills suite.
