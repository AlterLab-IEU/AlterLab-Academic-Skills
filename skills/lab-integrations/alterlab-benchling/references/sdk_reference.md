# Benchling Python SDK Reference

## Installation & Setup

### Installation

```bash
# Stable release (pin a 1.x range in production)
uv add "benchling-sdk>=1.23,<2"

# Throwaway / scratch env
uv pip install benchling-sdk

# Pre-release/preview versions (not recommended for production)
uv pip install benchling-sdk --prerelease=allow
```

### Requirements
- Python >= 3.8 (benchling-sdk 1.x; verify against your pinned version)
- API access enabled on your Benchling tenant

### The `fields()` helper (read first)

Custom schema fields are passed as a `Fields` object built with the `fields()`
helper. Import it from `benchling_sdk.helpers.serialization_helpers` and pass a
**nested** dict where each field maps to a `{"value": ...}` object:

```python
from benchling_sdk.helpers.serialization_helpers import fields

my_fields = fields({
    "gene_name": {"value": "GFP"},
    "resistance": {"value": "Kanamycin"},
})
```

Do **not** pass flat strings (`fields({"gene_name": "GFP"})`) and there is no
`benchling.models.fields` accessor — use the `serialization_helpers` import. All
examples below use this `fields(...)` form.

### Basic Initialization

```python
from benchling_sdk.benchling import Benchling
from benchling_sdk.auth.api_key_auth import ApiKeyAuth

benchling = Benchling(
    url="https://your-tenant.benchling.com",
    auth_method=ApiKeyAuth("your_api_key")
)
```

## SDK Architecture

### Main Classes

**Benchling Client:**
The `benchling_sdk.benchling.Benchling` class is the root of all SDK interactions. It provides access to all resource endpoints:

```python
benchling.dna_sequences      # DNA sequence operations
benchling.rna_sequences      # RNA sequence operations
benchling.aa_sequences       # Amino acid sequence operations
benchling.custom_entities    # Custom entity operations
benchling.mixtures           # Mixture operations
benchling.containers         # Container operations
benchling.boxes              # Box operations
benchling.locations          # Location operations
benchling.plates             # Plate operations
benchling.entries            # Notebook entry operations
benchling.workflow_tasks     # Workflow task operations
benchling.requests           # Request operations
benchling.folders            # Folder operations
benchling.projects           # Project operations
benchling.users              # User operations
benchling.teams              # Team operations
```

### Resource Pattern

All resources follow a consistent CRUD pattern. Note the single-fetch method is
`get_by_id` (not `get`), the id keyword is entity-specific (usually
`<entity>_id`, e.g. `dna_sequence_id`; some services like custom entities use
`entity_id`), and `archive` is a bulk call taking a list of ids:

```python
# Create
resource.create(CreateModel(...))

# Read (single)
resource.get_by_id(<entity>_id="resource_id")

# Read (list) -> returns a PageIterator generator
resource.list(optional_filters...)

# Update
resource.update(<entity>_id="resource_id", <entity>=UpdateModel(...))

# Archive (bulk; reason is an enum)
resource.archive(<entity>_ids=["id1", "id2"], reason=...)
```

## Entity Management

### DNA Sequences

**Create:**
```python
from benchling_sdk.models import DnaSequenceCreate
from benchling_sdk.helpers.serialization_helpers import fields

sequence = benchling.dna_sequences.create(
    DnaSequenceCreate(
        name="pET28a-GFP",
        bases="ATCGATCGATCG",
        is_circular=True,
        folder_id="fld_abc123",
        schema_id="ts_abc123",
        fields=fields({
            "gene_name": {"value": "GFP"},
            "resistance": {"value": "Kanamycin"},
            "copy_number": {"value": "High"},
        })
    )
)
```

**Read:**
```python
# Get by ID
seq = benchling.dna_sequences.get_by_id(dna_sequence_id="seq_abc123")
print(f"{seq.name}: {len(seq.bases)} bp")

# List with filters
sequences = benchling.dna_sequences.list(
    folder_id="fld_abc123",
    schema_id="ts_abc123",
    name="pET28a"  # Filter by name
)

for page in sequences:
    for seq in page:
        print(f"{seq.id}: {seq.name}")
```

**Update:**
```python
from benchling_sdk.models import DnaSequenceUpdate
from benchling_sdk.helpers.serialization_helpers import fields

updated = benchling.dna_sequences.update(
    dna_sequence_id="seq_abc123",
    dna_sequence=DnaSequenceUpdate(
        name="pET28a-GFP-v2",
        fields=fields({
            "gene_name": {"value": "eGFP"},
            "notes": {"value": "Codon optimized"},
        })
    )
)
```

**Archive:**
Archiving is a bulk operation: it takes an iterable of IDs (`dna_sequence_ids`)
and a `reason` that must be an `EntityArchiveReason` enum member (not a free-text
string). Accepted reasons can vary by tenant configuration — inspect the
`EntityArchiveReason` enum from `benchling_sdk.models` for the members valid on
your tenant:
```python
from benchling_sdk.models import EntityArchiveReason

# Choose a member that exists in EntityArchiveReason on your tenant; inspect it with
#   list(EntityArchiveReason)
benchling.dna_sequences.archive(
    dna_sequence_ids=["seq_abc123"],
    reason=EntityArchiveReason.<MEMBER>,
)
```

### RNA Sequences

Similar pattern to DNA sequences:

```python
from benchling_sdk.models import RnaSequenceCreate, RnaSequenceUpdate
from benchling_sdk.helpers.serialization_helpers import fields

# Create
rna = benchling.rna_sequences.create(
    RnaSequenceCreate(
        name="gRNA-target1",
        bases="AUCGAUCGAUCG",
        folder_id="fld_abc123",
        fields=fields({
            "target_gene": {"value": "TP53"},
            "off_target_score": {"value": "95"},
        })
    )
)

# Update
updated_rna = benchling.rna_sequences.update(
    rna_sequence_id=rna.id,
    rna_sequence=RnaSequenceUpdate(
        fields=fields({
            "validated": {"value": "Yes"},
        })
    )
)
```

### Amino Acid (Protein) Sequences

```python
from benchling_sdk.models import AaSequenceCreate
from benchling_sdk.helpers.serialization_helpers import fields

protein = benchling.aa_sequences.create(
    AaSequenceCreate(
        name="Green Fluorescent Protein",
        amino_acids="MSKGEELFTGVVPILVELDGDVNGHKFSVSGEGEGDATYGKLTLKF",
        folder_id="fld_abc123",
        fields=fields({
            "molecular_weight": {"value": "27000"},
            "extinction_coefficient": {"value": "21000"},
        })
    )
)
```

### Custom Entities

Custom entities are defined by your tenant's schemas:

```python
from benchling_sdk.models import CustomEntityCreate, CustomEntityUpdate
from benchling_sdk.helpers.serialization_helpers import fields

# Create
cell_line = benchling.custom_entities.create(
    CustomEntityCreate(
        name="HEK293T-Clone5",
        schema_id="ts_cellline_abc123",
        folder_id="fld_abc123",
        fields=fields({
            "passage_number": {"value": "15"},
            "mycoplasma_test": {"value": "Negative"},
            "freezing_date": {"value": "2025-10-15"},
        })
    )
)

# Update
updated_cell_line = benchling.custom_entities.update(
    entity_id=cell_line.id,
    custom_entity=CustomEntityUpdate(
        fields=fields({
            "passage_number": {"value": "16"},
            "notes": {"value": "Expanded for experiment"},
        })
    )
)
```

### Mixtures

Mixtures combine multiple components:

```python
from benchling_sdk.models import MixtureCreate, IngredientCreate
from benchling_sdk.helpers.serialization_helpers import fields

mixture = benchling.mixtures.create(
    MixtureCreate(
        name="LB-Amp Media",
        folder_id="fld_abc123",
        schema_id="ts_mixture_abc123",
        ingredients=[
            # Confirm IngredientCreate's exact fields (amount/units, component id)
            # against the API reference for your SDK version.
            IngredientCreate(component_entity_id="ent_lb_base", ...),
            IngredientCreate(component_entity_id="ent_ampicillin", ...),
        ],
        fields=fields({
            "pH": {"value": "7.0"},
            "sterilized": {"value": "Yes"},
        })
    )
)
```

### Registry Operations

**Direct Registry Registration:**
```python
# Register entity upon creation: registry_id selects the registry, naming_strategy
# controls how the registry ID is assigned.
registered_seq = benchling.dna_sequences.create(
    DnaSequenceCreate(
        name="Construct-001",
        bases="ATCG",
        is_circular=True,
        folder_id="fld_abc123",
        registry_id="src_abc123",
        naming_strategy="NEW_IDS",  # or "IDS_FROM_NAMES"
    )
)
print(f"Registry ID: {registered_seq.entity_registry_id}")
```

**Naming Strategies:**
- `NEW_IDS`: Benchling generates new registry IDs
- `IDS_FROM_NAMES`: Use entity names as registry IDs (names must be unique)

**Gotcha:** `registry_id` is the field that actually triggers registration. The
separate `entity_registry_id` field assigns a specific ID directly — and you
**cannot** pass both `entity_registry_id` and `naming_strategy` in the same
create call.

## Inventory Management

### Containers

```python
from benchling_sdk.models import (
    ContainerCreate,
    ContainerUpdate,
    ContainersCheckin,
    ContainersCheckout,
)
from benchling_sdk.helpers.serialization_helpers import fields

# Create
container = benchling.containers.create(
    ContainerCreate(
        name="Sample-001-Tube",
        schema_id="cont_schema_abc123",
        barcode="CONT001",
        parent_storage_id="box_abc123",  # Place in box
        fields=fields({
            "concentration": {"value": "100 ng/μL"},
            "volume": {"value": "50 μL"},
            "sample_type": {"value": "gDNA"},
        })
    )
)

# Update properties (and/or relocate via parent_storage_id)
updated = benchling.containers.update(
    container_id=container.id,
    container=ContainerUpdate(
        parent_storage_id="box_xyz789",  # relocate in storage
        fields=fields({
            "volume": {"value": "45 μL"},
            "notes": {"value": "Used 5 μL for PCR"},
        })
    )
)

# Check in / out are BULK only (no single-container helpers): pass a request object
benchling.containers.checkout(
    checkout=ContainersCheckout(...)  # populate from the API reference
)
benchling.containers.checkin(
    checkin=ContainersCheckin(...)
)
```
Note: to transfer a container's *contents* into another container, use
`benchling.containers.transfer_into_container(destination_container_id=...,
transfer_request=ContainerTransfer(...))` (or `transfer_into_containers(...)` for
bulk). Confirm the `ContainersCheckin`/`ContainersCheckout`/`ContainerTransfer`
field names against the API reference for your SDK version.

### Boxes

```python
from benchling_sdk.models import BoxCreate
from benchling_sdk.helpers.serialization_helpers import fields

box = benchling.boxes.create(
    BoxCreate(
        name="Freezer-A-Box-01",
        schema_id="box_schema_abc123",
        parent_storage_id="loc_freezer_a",
        barcode="BOX001",
        fields=fields({
            "box_type": {"value": "81-place"},
            "temperature": {"value": "-80C"},
        })
    )
)

# List containers in box
containers = benchling.containers.list(
    parent_storage_id=box.id
)
```

### Locations

```python
from benchling_sdk.models import LocationCreate

location = benchling.locations.create(
    LocationCreate(
        name="Freezer A - Shelf 2",
        parent_storage_id="loc_freezer_a",
        barcode="LOC-A-S2"
    )
)
```

### Plates

```python
from benchling_sdk.models import PlateCreate, WellCreate

# Create 96-well plate
plate = benchling.plates.create(
    PlateCreate(
        name="PCR-Plate-001",
        schema_id="plate_schema_abc123",
        barcode="PLATE001",
        wells=[
            WellCreate(
                position="A1",
                entity_id="sample_entity_abc"
            ),
            WellCreate(
                position="A2",
                entity_id="sample_entity_xyz"
            )
            # ... more wells
        ]
    )
)
```

## Notebook Operations

### Entries

The entry service methods are `create_entry` / `update_entry` / `get_entry_by_id`
/ `list_entries` (NOT the bare `create`/`update`/`get` of the entity services):
```python
from benchling_sdk.models import EntryCreate, EntryUpdate
from benchling_sdk.helpers.serialization_helpers import fields

# Create entry
entry = benchling.entries.create_entry(
    EntryCreate(
        name="Cloning Experiment 2025-10-20",
        folder_id="fld_abc123",
        schema_id="entry_schema_abc123",
        fields=fields({
            "objective": {"value": "Clone GFP into pET28a"},
            "date": {"value": "2025-10-20"},
            "experiment_type": {"value": "Molecular Biology"},
        })
    )
)

# Update entry
updated_entry = benchling.entries.update_entry(
    entry_id=entry.id,
    entry=EntryUpdate(
        fields=fields({
            "results": {"value": "Successful cloning, 10 colonies"},
            "notes": {"value": "Colony 5 shows best fluorescence"},
        })
    )
)
```

### Linking Entities to Entries

There is **no** `entry_links` service. Entities are linked into an ELN entry by
embedding an inline entity reference (an @-mention link to the entity) inside a
note block of the entry's content, then persisting it with `update_entry`. Build
the entry's `days`/notes structure containing the inline link and pass it via
`EntryUpdate`:
```python
from benchling_sdk.models import EntryUpdate

benchling.entries.update_entry(
    entry_id="entry_abc123",
    entry=EntryUpdate(days=[...]),  # notes containing the inline entity link
)
```
Confirm the exact note/link block model classes against your installed
`benchling-sdk` version, since linking is expressed within entry content rather
than via a standalone service.

## Workflow Management

### Tasks

```python
from benchling_sdk.models import WorkflowTaskCreate, WorkflowTaskUpdate
from benchling_sdk.helpers.serialization_helpers import fields

# Create task
task = benchling.workflow_tasks.create(
    WorkflowTaskCreate(
        name="PCR Amplification",
        workflow_id="wf_abc123",
        assignee_id="user_abc123",
        schema_id="task_schema_abc123",
        fields=fields({
            "template": {"value": "seq_abc123"},
            "primers": {"value": "Forward: ATCG, Reverse: CGAT"},
            "priority": {"value": "High"},
        })
    )
)

# Update status
completed_task = benchling.workflow_tasks.update(
    task_id=task.id,
    workflow_task=WorkflowTaskUpdate(
        status_id="status_complete_abc123",
        fields=fields({
            "completion_date": {"value": "2025-10-20"},
            "yield": {"value": "500 ng"},
        })
    )
)

# List tasks
tasks = benchling.workflow_tasks.list(
    workflow_id="wf_abc123",
    status_ids=["status_pending", "status_in_progress"]
)
```

## Advanced Features

### Pagination

The SDK uses generators for memory-efficient pagination:

```python
# Automatic pagination
sequences = benchling.dna_sequences.list()

# Get estimated total count
total = sequences.estimated_count()
print(f"Total sequences: {total}")

# Iterate through all pages
for page in sequences:
    for seq in page:
        process(seq)

# Manual page size control
sequences = benchling.dna_sequences.list(page_size=50)
```

### Async Task Handling

Long-running/bulk operations return a `TaskHelper` (benchling-sdk 1.x) — not a
bare task id. Call `wait_for_response()` (typed result) or `wait_for_completion()`
(raw task) on it; there is no top-level `wait_for_task(...)` function:

```python
# A bulk call returns a TaskHelper
task = benchling.dna_sequences.bulk_create(...)

# Wait for completion (default interval 1s, max 600s)
result = task.wait_for_response(
    interval_wait_seconds=2,  # Poll every 2 seconds
    max_wait_seconds=600,     # Timeout after 10 minutes
)
print("Task completed successfully")
```

### Error Handling

```python
from benchling_sdk.errors import (
    BenchlingError,
    NotFoundError,
    ValidationError,
    UnauthorizedError
)

try:
    sequence = benchling.dna_sequences.get_by_id(dna_sequence_id="seq_invalid")
except NotFoundError:
    print("Sequence not found")
except UnauthorizedError:
    print("Insufficient permissions")
except ValidationError as e:
    print(f"Invalid data: {e}")
except BenchlingError as e:
    print(f"General Benchling error: {e}")
```

### Retry Strategy

Customize retry behavior:

```python
from benchling_sdk.benchling import Benchling
from benchling_sdk.auth.api_key_auth import ApiKeyAuth
from benchling_sdk.helpers.retry_helpers import RetryStrategy

# Custom retry configuration (param is max_tries, NOT max_retries;
# defaults: max_tries=5, backoff_factor=1.0, status_codes_to_retry=(429,502,503,504))
retry_strategy = RetryStrategy(
    max_tries=3,
    backoff_factor=0.5,
)

benchling = Benchling(
    url="https://your-tenant.benchling.com",
    auth_method=ApiKeyAuth("your_api_key"),
    retry_strategy=retry_strategy
)

# Disable retries
benchling = Benchling(
    url="https://your-tenant.benchling.com",
    auth_method=ApiKeyAuth("your_api_key"),
    retry_strategy=RetryStrategy.no_retries(),
)
```

### Custom API Calls

For unsupported endpoints:

```python
# GET request with model parsing
from benchling_sdk.models import DnaSequence

response = benchling.api.get_modeled(
    path="/api/v2/dna-sequences/seq_abc123",
    response_type=DnaSequence
)

# POST request
from benchling_sdk.models import DnaSequenceCreate

response = benchling.api.post_modeled(
    path="/api/v2/dna-sequences",
    request_body=DnaSequenceCreate(...),
    response_type=DnaSequence
)

# Raw requests
raw_response = benchling.api.get(
    path="/api/v2/custom-endpoint",
    params={"key": "value"}
)
```

### Batch Operations

Efficiently process multiple items:

```python
# Bulk create
from benchling_sdk.models import DnaSequenceCreate

sequences_to_create = [
    DnaSequenceCreate(name=f"Seq-{i}", bases="ATCG", folder_id="fld_abc")
    for i in range(100)
]

# Create in batches
batch_size = 10
for i in range(0, len(sequences_to_create), batch_size):
    batch = sequences_to_create[i:i+batch_size]
    for seq in batch:
        benchling.dna_sequences.create(seq)
```

### Schema Fields Helper

Convert dictionaries to `Fields` objects. Each value must be a `{"value": ...}`
object, and the helper is imported from `serialization_helpers`:

```python
from benchling_sdk.helpers.serialization_helpers import fields

my_fields = fields({
    "concentration": {"value": "100 ng/μL"},
    "volume": {"value": "50 μL"},
    "quality_score": {"value": "8.5"},
    "date_prepared": {"value": "2025-10-20"},
})

# Use in create/update
container = benchling.containers.create(
    ContainerCreate(
        name="Sample-001",
        schema_id="schema_abc",
        fields=my_fields,
    )
)
```

### Forward Compatibility

The SDK handles unknown API values gracefully:

```python
# Unknown enum values are preserved
entity = benchling.dna_sequences.get_by_id(dna_sequence_id="seq_abc")
# Even if API returns new enum value not in SDK, it's preserved

# Unknown polymorphic types return UnknownType
from benchling_sdk.models import UnknownType

if isinstance(entity, UnknownType):
    print(f"Unknown type: {entity.type}")
    # Can still access raw data
    print(entity.raw_data)
```

## Best Practices

### Use Type Hints

```python
from benchling_sdk.models import DnaSequence, DnaSequenceCreate
from typing import List

def create_sequences(names: List[str], folder_id: str) -> List[DnaSequence]:
    sequences = []
    for name in names:
        seq = benchling.dna_sequences.create(
            DnaSequenceCreate(
                name=name,
                bases="ATCG",
                folder_id=folder_id
            )
        )
        sequences.append(seq)
    return sequences
```

### Efficient Filtering

Use API filters instead of client-side filtering:

```python
# Good - filter on server
sequences = benchling.dna_sequences.list(
    folder_id="fld_abc123",
    schema_id="ts_abc123"
)

# Bad - loads everything then filters
all_sequences = benchling.dna_sequences.list()
filtered = [s for page in all_sequences for s in page if s.folder_id == "fld_abc123"]
```

### Resource Cleanup

```python
# Archive old entities (collect ids, then archive in bulk with an enum reason)
from benchling_sdk.models import EntityArchiveReason

cutoff_date = "2024-01-01"
stale_ids = [
    seq.id
    for page in benchling.dna_sequences.list()
    for seq in page
    if seq.created_at < cutoff_date
]
if stale_ids:
    benchling.dna_sequences.archive(
        dna_sequence_ids=stale_ids,
        reason=EntityArchiveReason.<MEMBER>,  # a member valid on your tenant
    )
```

## Troubleshooting

### Common Issues

**Import Errors:**
```python
# Wrong
from benchling_sdk import Benchling  # ImportError

# Correct
from benchling_sdk.benchling import Benchling
```

**Field Validation:**
```python
# Fields must match schema. Check schema field types in the Benchling UI.
from benchling_sdk.helpers.serialization_helpers import fields

my_fields = fields({
    "numeric_field": {"value": "123"},      # Pass as a string even for numbers
    "date_field": {"value": "2025-10-20"},  # Format: YYYY-MM-DD
    "dropdown_field": {"value": "Option1"}, # Must match a dropdown option exactly
})
```

**Pagination Exhaustion:**
```python
# Generators can only be iterated once
sequences = benchling.dna_sequences.list()
for page in sequences:  # First iteration OK
    pass
for page in sequences:  # Second iteration returns nothing!
    pass

# Solution: Create new generator
sequences = benchling.dna_sequences.list()  # New generator
```

## References

- **SDK Source:** https://pypi.org/project/benchling-sdk/
- **SDK Docs:** https://benchling.com/sdk-docs/
- **API Reference:** https://benchling.com/api/reference
- **Common Examples:** https://docs.benchling.com/docs/common-sdk-interactions-and-examples
