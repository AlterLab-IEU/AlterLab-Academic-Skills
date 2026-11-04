---
name: alterlab-dnanexus
description: Develops genomics apps, applets and workflows for the DNAnexus platform with the dxpy Python SDK and dx CLI — writes dxapp.json and entry-point code, lints the spec offline, runs entry points locally in dxpy's debug harness, and checks WDL for dxCompiler with miniwdl, all without an account; building, uploading data and running jobs on the platform is an optional step with the user's own DNAnexus login. Use when building or running a DNAnexus app, applet, or workflow, writing dxapp.json, using dx-app-wizard or dx build, calling dxpy (find_data_objects, DXApplet.run, upload_local_file), or uploading/downloading sequencing data on DNAnexus. For LatchBio (Latch SDK @workflow/@task, LatchFile) use alterlab-latchbio instead; for Benchling LIMS use alterlab-benchling. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(dx:*) Bash(dx-app-wizard:*) Bash(dx-build-app:*) Bash(uv:*) Bash(python:*) Bash(python3:*)
compatibility: "No API key required to write an app, lint dxapp.json (scripts/lint_dxapp.py), run its entry points locally in dxpy's debug harness and check WDL with miniwdl (dxpy 0.417.1 as of 2026-10; Python >=3.8). Optional: the user's own DNAnexus login (dx login or DX_SECURITY_CONTEXT) for dx build, uploads and jobs, which bill their org."
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-10-22"
    credentials: "optional: DX_SECURITY_CONTEXT (JSON holding the user's DNAnexus API token, or the session `dx login` stores — adds dx build, uploads and downloads in their projects, and running jobs, which bill their org)"
---

# DNAnexus Integration

## Overview

DNAnexus is a cloud platform for biomedical data analysis and genomics. Build and deploy apps/applets, manage data objects, run workflows, and use the dxpy Python SDK for genomics pipeline development and execution. Writing, linting and locally testing the app needs no account; only `dx build`, data transfer and jobs touch the platform.

## Keyless Path (default — no DNAnexus account)

1. **Write the app** (`dxapp.json` + `src/<name>.py` or `.sh`) against dxpy 0.417.1. Keep the processing in a plain function that takes local paths, so it can be tested without the platform.
2. **Lint the spec offline:** `python3 scripts/lint_dxapp.py my-app/` checks classes (lower case: `file`, `int`, `array:file`, ...), `interpreter` (`python3`/`bash`), the execution environment (Ubuntu 24.04 or 20.04, version `"0"`), that `runSpec.file` exists, and that `main()`'s parameters and returned keys match `inputSpec`/`outputSpec`. `dx build --dry-run` is *not* a keyless check: without a login it stops with `ResolutionError: Cannot resolve "."` (verified 2026-10-22).
3. **Run the entry point locally in dxpy's debug harness.** With `DX_JOB_ID` unset, `dxpy.run()` calls the entry point named by `DX_TEST_FUNCTION` (default `main`) with the inputs in `./job_input.json` and writes `./job_output.json`. Platform calls (`download_dxfile`, `upload_local_file`) still need a login, so add a test entry point around the pure function:

```python
@dxpy.entry_point("local_test")          # never called on the platform
def local_test(reads_path, min_mean_quality=30):
    kept, total = filter_fastq(reads_path, "filtered.fastq", min_mean_quality)
    return {"kept": kept, "total": total}
```

```bash
echo '{"reads_path": "test.fastq", "min_mean_quality": 30}' > job_input.json
DX_TEST_FUNCTION=local_test uv run --with dxpy python src/my-app.py   # -> job_output.json
```

4. **WDL destined for dxCompiler:** run `uv run --python ">=3.11" --with miniwdl miniwdl check workflow.wdl` first (catches undefined identifiers, type errors, missing outputs); `java -jar dxCompiler.jar compile` then needs the login.
5. **Hand over the platform step** with the exact commands (`dx login`, `dx build`, `dx run ... --instance-type ...`), an instance type and `timeoutPolicy` chosen on purpose, and a note that jobs bill the user's org. Without a login, stop there — never claim a build, upload or job happened.

## When to Use This Skill

This skill should be used when:
- Creating, building, or modifying DNAnexus apps/applets
- Uploading, downloading, searching, or organizing files and records
- Running analyses, monitoring jobs, creating workflows
- Writing scripts using dxpy to interact with the platform
- Setting up dxapp.json, managing dependencies, using Docker
- Processing FASTQ, BAM, VCF, or other bioinformatics files
- Managing projects, permissions, or platform resources

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Latch SDK workflows (`@workflow`/`@task`, LatchFile/LatchDir) on LatchBio | `alterlab-latchbio` |
| Running the nf-core/sarek germline/somatic variant-calling pipeline itself | `alterlab-nf-core-sarek` |
| Generic serverless GPU/CPU jobs or SLURM/HPC submission outside DNAnexus | `alterlab-modal` / `alterlab-remote-compute` |
| Reading or filtering BAM/VCF records locally in Python | `alterlab-pysam` |
| Registry, inventory, or ELN records in Benchling | `alterlab-benchling` |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-latchbio`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

## Core Capabilities

The skill is organized into five main areas, each with detailed reference documentation:

### 1. App Development

**Purpose**: Create executable programs (apps/applets) that run on the DNAnexus platform.

**Key Operations**:
- Generate app skeleton with `dx-app-wizard`
- Write Python or Bash apps with proper entry points
- Handle input/output data objects
- Deploy with `dx build` or `dx build --app`
- Test apps on the platform

**Common Use Cases**:
- Bioinformatics pipelines (alignment, variant calling)
- Data processing workflows
- Quality control and filtering
- Format conversion tools

**Reference**: See `references/app-development.md` for:
- Complete app structure and patterns
- Python entry point decorators
- Input/output handling with dxpy
- Development best practices
- Common issues and solutions

### 2. Data Operations

**Purpose**: Manage files, records, and other data objects on the platform.

**Key Operations**:
- Upload/download files with `dxpy.upload_local_file()` and `dxpy.download_dxfile()`
- Create and manage records with metadata
- Search for data objects by name, properties, or type
- Clone data between projects
- Manage project folders and permissions

**Common Use Cases**:
- Uploading sequencing data (FASTQ files)
- Organizing analysis results
- Searching for specific samples or experiments
- Backing up data across projects
- Managing reference genomes and annotations

**Reference**: See `references/data-operations.md` for:
- Complete file and record operations
- Data object lifecycle (open/closed states)
- Search and discovery patterns
- Project management
- Batch operations

### 3. Job Execution

**Purpose**: Run analyses, monitor execution, and orchestrate workflows.

**Key Operations**:
- Launch jobs with `applet.run()` or `app.run()`
- Monitor job status and logs
- Create subjobs for parallel processing
- Build and run multi-step workflows
- Chain jobs with output references

**Common Use Cases**:
- Running genomics analyses on sequencing data
- Parallel processing of multiple samples
- Multi-step analysis pipelines
- Monitoring long-running computations
- Debugging failed jobs

**Reference**: See `references/job-execution.md` for:
- Complete job lifecycle and states
- Workflow creation and orchestration
- Parallel execution patterns
- Job monitoring and debugging
- Resource management

### 4. Python SDK (dxpy)

**Purpose**: Programmatic access to DNAnexus platform through Python.

**Key Operations**:
- Work with data object handlers (DXFile, DXRecord, DXApplet, etc.)
- Use high-level functions for common tasks
- Make direct API calls for advanced operations
- Create links and references between objects
- Search and discover platform resources

**Common Use Cases**:
- Automation scripts for data management
- Custom analysis pipelines
- Batch processing workflows
- Integration with external tools
- Data migration and organization

**Reference**: See `references/python-sdk.md` for:
- Complete dxpy class reference
- High-level utility functions
- API method documentation
- Error handling patterns
- Common code patterns

### 5. Configuration and Dependencies

**Purpose**: Configure app metadata and manage dependencies.

**Key Operations**:
- Write dxapp.json with inputs, outputs, and run specs
- Install system packages (execDepends)
- Bundle custom tools and resources
- Use assets for shared dependencies
- Integrate Docker containers
- Configure instance types and timeouts

**Common Use Cases**:
- Defining app input/output specifications
- Installing bioinformatics tools (samtools, bwa, etc.)
- Managing Python package dependencies
- Using Docker images for complex environments
- Selecting computational resources

**Reference**: See `references/configuration.md` for:
- Complete dxapp.json specification
- Dependency management strategies
- Docker integration patterns
- Regional and resource configuration
- Example configurations

## Quick Start Examples

### Upload and Analyze Data

```python
import dxpy

# Upload input file
input_file = dxpy.upload_local_file("sample.fastq", project="project-xxxx")

# Run analysis
job = dxpy.DXApplet("applet-xxxx").run({
    "reads": dxpy.dxlink(input_file.get_id())
})

# Wait for completion
job.wait_on_done()

# Download results
output_id = job.describe()["output"]["aligned_reads"]["$dnanexus_link"]
dxpy.download_dxfile(output_id, "aligned.bam")
```

### Search and Download Files

```python
import dxpy

# Find BAM files from a specific experiment.
# name defaults to exact match; pass name_mode="glob" to use wildcards.
files = dxpy.find_data_objects(
    classname="file",
    name="*.bam",
    name_mode="glob",
    properties={"experiment": "exp001"},
    project="project-xxxx"
)

# Download each file
for file_result in files:
    file_obj = dxpy.DXFile(file_result["id"])
    filename = file_obj.describe()["name"]
    dxpy.download_dxfile(file_result["id"], filename)
```

### Create Simple App

```python
# src/my-app.py
import dxpy
import subprocess

@dxpy.entry_point('main')
def main(input_file, quality_threshold=30):
    # Download input
    dxpy.download_dxfile(input_file["$dnanexus_link"], "input.fastq")

    # Process
    subprocess.check_call([
        "quality_filter",
        "--input", "input.fastq",
        "--output", "filtered.fastq",
        "--threshold", str(quality_threshold)
    ])

    # Upload output
    output_file = dxpy.upload_local_file("filtered.fastq")

    return {
        "filtered_reads": dxpy.dxlink(output_file)
    }

dxpy.run()
```

## Workflow Decision Tree

When working with DNAnexus, follow this decision tree:

1. **Need to create a new executable?**
   - Yes → Use **App Development** (references/app-development.md)
   - No → Continue to step 2

2. **Need to manage files or data?**
   - Yes → Use **Data Operations** (references/data-operations.md)
   - No → Continue to step 3

3. **Need to run an analysis or workflow?**
   - Yes → Use **Job Execution** (references/job-execution.md)
   - No → Continue to step 4

4. **Writing Python scripts for automation?**
   - Yes → Use **Python SDK** (references/python-sdk.md)
   - No → Continue to step 5

5. **Configuring app settings or dependencies?**
   - Yes → Use **Configuration** (references/configuration.md)

Often you'll need multiple capabilities together (e.g., app development + configuration, or data operations + job execution).

## Installation and Authentication

### Install dxpy

```bash
uv pip install dxpy
```

### Login to DNAnexus (optional — only for the platform step)

```bash
dx login
```

This authenticates your session and sets up access to projects and data. Non-interactive scripts can instead set `DX_SECURITY_CONTEXT='{"auth_token_type": "Bearer", "auth_token": "..."}'` from a secret store.

### Verify Installation

```bash
dx --version
dx whoami
```

## Common Patterns

Batch processing (find files, launch parallel jobs) is shown in the Quick Start above; see `references/job-execution.md` for scatter-gather and subjobs.

### Pattern 1: Multi-Step Pipeline

Chain multiple analyses together (`get_output_ref` passes one job's output as the next job's input):

```python
# Step 1: Quality control
qc_job = qc_applet.run({"reads": input_file})

# Step 2: Alignment (uses QC output)
align_job = align_applet.run({
    "reads": qc_job.get_output_ref("filtered_reads")
})

# Step 3: Variant calling (uses alignment output)
variant_job = variant_applet.run({
    "bam": align_job.get_output_ref("aligned_bam")
})
```

### Pattern 2: Data Organization

Organize analysis results systematically:

```python
# Create organized folder structure
dxpy.api.project_new_folder(
    "project-xxxx",
    {"folder": "/experiments/exp001/results", "parents": True}
)

# Upload with metadata
result_file = dxpy.upload_local_file(
    "results.txt",
    project="project-xxxx",
    folder="/experiments/exp001/results",
    properties={
        "experiment": "exp001",
        "sample": "sample1",
        "analysis_date": "2025-10-20"
    },
    tags=["validated", "published"]
)
```

## Best Practices

- Never hardcode API tokens; authenticate via `dx login` or `DX_SECURITY_CONTEXT`.
- `find_*` `name` filters match exactly by default — pass `name_mode="glob"` for wildcards.
- Pass job outputs to downstream inputs with `get_output_ref()` directly (it is already a dxlink).
- Pick instance types deliberately and set `timeoutPolicy` to cap runaway cost.

Each reference file ends with topic-specific best practices for deeper guidance.

## Resources

### scripts/

- **lint_dxapp.py** - offline, stdlib-only lint of an app directory (`dxapp.json` + entry-point source); exit 1 lists every problem

### references/

- **app-development.md** - Complete guide to building and deploying apps/applets
- **data-operations.md** - File management, records, search, and project operations
- **job-execution.md** - Running jobs, workflows, monitoring, and parallel processing
- **python-sdk.md** - Comprehensive dxpy library reference with all classes and functions
- **configuration.md** - dxapp.json specification and dependency management

Load these references when you need detailed information about specific operations or when working on complex tasks.

## Getting Help

- Official documentation: https://documentation.dnanexus.com/
- API reference: http://autodoc.dnanexus.com/
- GitHub repository: https://github.com/dnanexus/dx-toolkit
- Support: support@dnanexus.com

Part of the AlterLab Academic Skills suite.
