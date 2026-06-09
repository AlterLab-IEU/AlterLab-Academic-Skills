# Data Management

## Overview
Latch provides comprehensive data management through cloud storage abstractions (LatchFile, LatchDir) and a structured Registry system for organizing experimental data.

## Cloud Storage: LatchFile and LatchDir

### LatchFile

Represents a file in Latch's cloud storage system.

```python
from latch.types import LatchFile

# Create reference to existing file
input_file = LatchFile("latch:///data/sample.fastq")

# Access file properties
file_path = input_file.local_path  # Local path when executing
file_remote = input_file.remote_path  # Cloud storage path
```

### LatchDir

Represents a directory in Latch's cloud storage system.

```python
from latch.types import LatchDir

# Create reference to directory
output_dir = LatchDir("latch:///results/experiment_1")

# Directory operations
all_files = output_dir.glob("*.bam")  # Find files matching pattern
subdirs = output_dir.iterdir()  # List contents
```

### Path Formats

Latch storage uses a special URL scheme:
- **Latch paths**: `latch:///path/to/file`
- **Local paths**: Automatically resolved during workflow execution
- **S3 paths**: Can be used directly if configured

### File Transfer

Files are automatically transferred between local execution and cloud storage:

```python
from latch import small_task
from latch.types import LatchFile

@small_task
def process_file(input_file: LatchFile) -> LatchFile:
    # File is automatically downloaded to local execution
    local_path = input_file.local_path

    # Process the file
    with open(local_path, 'r') as f:
        data = f.read()

    # Write output
    output_path = "output.txt"
    with open(output_path, 'w') as f:
        f.write(processed_data)

    # Automatically uploaded back to cloud storage
    return LatchFile(output_path, "latch:///results/output.txt")
```

### Glob Patterns

Find files using pattern matching:

```python
from latch.types import LatchDir

data_dir = LatchDir("latch:///data")

# Find all FASTQ files
fastq_files = data_dir.glob("**/*.fastq")

# Find files in subdirectories
bam_files = data_dir.glob("alignments/**/*.bam")

# Multiple patterns
results = data_dir.glob("*.{bam,sam}")
```

## Registry System

The Registry provides structured data organization with projects, tables, and records.

### Registry Architecture

```
Account/Workspace
└── Projects
    └── Tables
        └── Records
```

> API note: `Project`, `Table`, and `Record` are constructed **by id** (e.g. `Table(table_id)`); they do not expose `.create()`/`.get()`/`.list()` classmethods. You normally discover ids through `Account` and `Project.list_tables()`. Reads use getters (`get_values()`, `get_columns()`); writes go through the `table.update()` transaction context. Always check the current SDK signatures, as the Registry API evolves.

### Working with Projects

```python
from latch.account import Account
from latch.registry.project import Project

# Discover projects in the current workspace
account = Account.current()
projects = account.list_registry_projects()

# Or construct directly by id
project = Project("proj_123")
display_name = project.get_display_name()

# List tables within a project
tables = project.list_tables()
```

### Working with Tables

```python
from latch.registry.table import Table

# Construct a table by id (e.g. obtained from project.list_tables())
table = Table("tbl_456")

# Inspect the schema: {column_key: Column}
columns = table.get_columns()
```

### Column Types

Registry columns are typed. Common Python column types passed to `upsert_column` (from `latch.registry.types`) include:
- `str` - Text data
- `int` / `float` - Numeric values
- `bool` - True/False values
- `datetime.date` / `datetime.datetime` - Date / timestamp values
- `LatchFile` / `LatchDir` - file / directory references
- `LinkedRecordType[...]` - reference to a record in another table (from `latch.registry.types`)
- enums - a fixed set of allowed string values

### Working with Records

Records are read with getters and written through the table's update transaction (upsert is keyed by record **name**).

```python
# Read records: list_records() yields pages of {record_id: Record}
for page in table.list_records():
    for record_id, record in page.items():
        name = record.get_name()
        values = record.get_values()  # {column_key: value}

# Create or update records, and update the schema, atomically
with table.update() as updater:
    updater.upsert_record(
        "S001",
        condition="treated",
        replicate=1,
        fastq_file=LatchFile("latch:///data/S001.fastq"),
    )
    updater.upsert_record("S002", condition="control")
    # updater.delete_record("S003")
# Changes commit when the context exits
```

### Linked Records

Link columns reference records in another table. Add a link column with `upsert_column` using `LinkedRecordType` parameterized by the target table's id, then upsert the record with the linked `Record` (or its id):

```python
from latch.registry.types import LinkedRecordType

with results_table.update() as updater:
    updater.upsert_column("sample", LinkedRecordType["tbl_samples_id"])  # target table id
    updater.upsert_column("alignment_bam", LatchFile)

with results_table.update() as updater:
    updater.upsert_record(
        "result_S001",
        sample=sample_record,  # the linked Record (or its id)
        alignment_bam=LatchFile("latch:///results/aligned.bam"),
    )
```

### Enum Columns

Add an enum column by passing a Python `Enum` (or its allowed values) to `upsert_column`:

```python
from enum import Enum

class Status(Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"

with table.update() as updater:
    updater.upsert_column("status", Status)
```

### Transactions and Bulk Updates

The `table.update()` context manager **is** the transaction: every `upsert_record` / `upsert_column` / `delete_record` inside it is committed atomically on exit. Group bulk changes in a single block:

```python
with table.update() as updater:
    for name in record_names:
        updater.upsert_record(name, status="processed")
    # all updates commit atomically here
```

## Integration with Workflows

### Using Registry in Workflows

```python
from latch import workflow, small_task
from latch.types import LatchFile
from latch.registry.table import Table
from latch.registry.record import Record

@small_task
def process_and_save(sample_name: str, table_id: str) -> str:
    table = Table(table_id)

    # Find the record by name
    sample = None
    for page in table.list_records():
        for record in page.values():
            if record.get_name() == sample_name:
                sample = record
                break
        if sample is not None:
            break

    # Read its file column
    input_file = sample.get_values()["fastq_file"]
    # ... processing logic produces output_file (a LatchFile) ...

    # Save results back to the registry via the update transaction
    with table.update() as updater:
        updater.upsert_record(sample_name, status="completed", results_file=input_file)

    return "Success"

@workflow
def registry_workflow(sample_name: str, table_id: str) -> str:
    """Workflow integrated with the Registry"""
    return process_and_save(sample_name=sample_name, table_id=table_id)
```

### Launch plans (preset parameters)

A launch plan attaches named default parameters to a workflow so they pre-fill the console form. (See references/workflow-creation.md for the exact `LaunchPlan(workflow, name, default_params=...)` form.) Automated "run on new data" triggers are configured on the platform side, not via a `trigger_folder` argument to `LaunchPlan`.

## Account and Workspace Management

The active workspace is determined by your login (`latch login` / `latch workspace`). `Account.current()` returns the current workspace's account; use it to enumerate Registry projects. There is no `Account.list()` / `Account.set_current()` — switch workspaces with the CLI (`latch workspace`).

```python
from latch.account import Account

# Get the current workspace's account
account = Account.current()

# Enumerate this workspace's Registry projects
projects = account.list_registry_projects()
```

## Functions for Data Operations

### Channel/data operators

`latch.functions.operators` provides Nextflow-style operators that work on **lists/dicts** (channels), not on Registry `Table` objects:

```python
from latch.functions.operators import left_join, inner_join, outer_join, right_join, latch_filter, group_tuple

# left/right/inner/outer_join take two dicts keyed by a common key
combined = left_join(left_dict, right_dict)

# latch_filter filters a list by a predicate, regex, or type
filtered = latch_filter(channel, predicate=lambda x: x["replicate"] > 1)
```

### Secrets Management

Retrieve secrets stored in your workspace from inside a task:

```python
from latch.functions.secrets import get_secret

api_key = get_secret("api_key")  # get_secret(secret_name)
```

## Best Practices

1. **Path Organization**: Use consistent folder structure (e.g., `/data`, `/results`, `/logs`)
2. **Registry Schema**: Define table schemas before bulk data entry
3. **Linked Records**: Use links to maintain relationships between experiments
4. **Bulk Operations**: Use transactions for updating multiple records
5. **File Naming**: Use consistent, descriptive file naming conventions
6. **Metadata**: Store experimental metadata in Registry for traceability
7. **Validation**: Validate data types when creating records
8. **Cleanup**: Regularly archive or delete unused data

## Common Patterns

### Sample Tracking

Add columns to an existing table via its update transaction. (Create the table itself in the platform UI, or obtain it from `project.list_tables()`.)

```python
import datetime
from enum import Enum
from latch.types import LatchFile

class SampleStatus(Enum):
    pending = "pending"
    processing = "processing"
    complete = "complete"

with samples_table.update() as updater:
    updater.upsert_column("sample_id", str)
    updater.upsert_column("collection_date", datetime.date)
    updater.upsert_column("raw_fastq_r1", LatchFile)
    updater.upsert_column("raw_fastq_r2", LatchFile)
    updater.upsert_column("status", SampleStatus)
```

### Results Organization

```python
from latch.registry.types import LinkedRecordType
from latch.types import LatchFile

with results_table.update() as updater:
    updater.upsert_column("sample", LinkedRecordType["tbl_samples_id"])  # link to a Samples record
    updater.upsert_column("alignment_bam", LatchFile)
    updater.upsert_column("variants_vcf", LatchFile)
    updater.upsert_column("qc_metrics", LatchFile)
```
