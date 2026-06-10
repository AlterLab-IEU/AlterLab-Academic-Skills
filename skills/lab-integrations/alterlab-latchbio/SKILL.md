---
name: alterlab-latchbio
description: Builds and deploys bioinformatics pipelines on the LatchBio platform using the Latch SDK — author workflows with @workflow/@task decorators, handle LatchFile/LatchDir I/O, register serverless workflows, configure CPU/GPU task resources, organize data in the Latch Registry, and wrap Nextflow/Snakemake pipelines. Use when developing or deploying a Latch SDK workflow, sizing task resources, working with the Registry, or porting a Nextflow/Snakemake bioinformatics pipeline onto LatchBio. Not for DNAnexus (dxpy/dx CLI) or generic Flyte. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(curl:*) Bash(python:*)
compatibility: Requires a LatchBio account and workspace plus the Latch SDK (`uv pip install latch`, latch>=2.x, Python 3.9+); deploying workflows needs Docker running and `latch login`
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# LatchBio Integration

## Overview

Latch is a Python framework for building and deploying bioinformatics workflows as serverless pipelines. Built on Flyte, create workflows with @workflow/@task decorators, manage cloud data with LatchFile/LatchDir, configure resources, and integrate Nextflow/Snakemake pipelines.

## Core Capabilities

The Latch platform provides four main areas of functionality:

### 1. Workflow Creation and Deployment
- Define serverless workflows using Python decorators
- Support for native Python, Nextflow, and Snakemake pipelines
- Automatic containerization with Docker
- Auto-generated no-code user interfaces
- Version control and reproducibility

### 2. Data Management
- Cloud storage abstractions (LatchFile, LatchDir)
- Structured data organization with Registry (Projects → Tables → Records)
- Type-safe data operations with links and enums
- Automatic file transfer between local and cloud
- Glob pattern matching for file selection

### 3. Resource Configuration
- Pre-configured task decorators (@small_task, @large_task, @small_gpu_task, @large_gpu_task)
- Custom resource specifications (CPU, memory, GPU, storage)
- GPU support (K80, V100, A100)
- Timeout and storage configuration
- Cost optimization strategies

### 4. Verified Workflows
- Production-ready pre-built pipelines maintained by Latch
- Importable from the `latch.verified` Python module: `rnaseq`, `deseq2_wf`, `mafft`, `trim_galore`, `gene_ontology_pathway_analysis`
- Many more pipelines (e.g. AlphaFold, single-cell, CRISPR) are available as Verified Workflows in the platform UI; verify the exact import name in `latch.verified` before relying on a Python import (see references/verified-workflows.md)

## Quick Start

### Installation and Setup

```bash
# Install Latch SDK (uv-first; pip install latch also works)
uv pip install latch

# Login to Latch
latch login

# Initialize a new workflow (scaffolds wf/, Dockerfile, version)
latch init my-workflow

# Register workflow to platform (builds container, generates the UI)
latch register my-workflow
```

**Prerequisites:**
- Docker installed and running (registration builds a container locally)
- Latch account credentials
- Python 3.9+ (Latch SDK `requires-python >=3.9`)

### Basic Workflow Example

```python
from latch import workflow, small_task
from latch.types import LatchFile

@small_task
def process_file(input_file: LatchFile) -> LatchFile:
    """Process a single file"""
    # Processing logic
    return output_file

@workflow
def my_workflow(input_file: LatchFile) -> LatchFile:
    """
    My bioinformatics workflow

    Args:
        input_file: Input data file
    """
    return process_file(input_file=input_file)
```

## When to Use This Skill

This skill should be used when encountering any of the following scenarios:

**Workflow Development:**
- "Create a Latch workflow for RNA-seq analysis"
- "Deploy my pipeline to Latch"
- "Convert my Nextflow pipeline to Latch"
- "Add GPU support to my workflow"
- Working with `@workflow`, `@task` decorators

**Data Management:**
- "Organize my sequencing data in Latch Registry"
- "How do I use LatchFile and LatchDir?"
- "Set up sample tracking in Latch"
- Working with `latch:///` paths

**Resource Configuration:**
- "Configure GPU for AlphaFold on Latch"
- "My task is running out of memory"
- "How do I optimize workflow costs?"
- Working with task decorators

**Verified Workflows:**
- "Run AlphaFold on Latch"
- "Use DESeq2 for differential expression"
- "Available pre-built workflows"
- Using `latch.verified` module

## Detailed Documentation

Load the reference that matches the task:

- **references/workflow-creation.md** — `latch init`/`latch register`, `@workflow`/`@task` decorators, type annotations and docstrings (these populate the UI), launch plans, conditional sections, CLI/programmatic execution, parallel `map_task`, registration troubleshooting.
- **references/data-management.md** — `LatchFile`/`LatchDir` and `latch:///` paths, glob patterns, the Registry API (`Project`, `Table`, `Record`), column types, the `table.update()` transaction, and workflow-Registry integration.
- **references/resource-configuration.md** — standard task decorators, `@custom_task(cpu, memory, storage_gib, timeout)`, the GPU task decorators (`small_gpu_task`/`large_gpu_task`, `v100_x{1,4,8}_task`, `g6e_*_task`), and resource/cost right-sizing.
- **references/verified-workflows.md** — pipelines importable from `latch.verified` and how to combine them with custom tasks.

## Common Workflow Patterns

### Complete RNA-seq Pipeline

```python
from latch import workflow, small_task, large_task
from latch.types import LatchFile, LatchDir

@small_task
def quality_control(fastq: LatchFile) -> LatchFile:
    """Run FastQC"""
    return qc_output

@large_task
def alignment(fastq: LatchFile, genome: str) -> LatchFile:
    """STAR alignment"""
    return bam_output

@small_task
def quantification(bam: LatchFile) -> LatchFile:
    """featureCounts"""
    return counts

@workflow
def rnaseq_pipeline(
    input_fastq: LatchFile,
    genome: str,
    output_dir: LatchDir
) -> LatchFile:
    """RNA-seq analysis pipeline"""
    qc = quality_control(fastq=input_fastq)
    aligned = alignment(fastq=qc, genome=genome)
    return quantification(bam=aligned)
```

### GPU-Accelerated Workflow

```python
from latch import workflow, small_task, large_gpu_task
from latch.types import LatchFile

@small_task
def preprocess(input_file: LatchFile) -> LatchFile:
    """Prepare data"""
    return processed

@large_gpu_task
def gpu_computation(data: LatchFile) -> LatchFile:
    """GPU-accelerated analysis"""
    return results

@workflow
def gpu_pipeline(input_file: LatchFile) -> LatchFile:
    """Pipeline with GPU tasks"""
    preprocessed = preprocess(input_file=input_file)
    return gpu_computation(data=preprocessed)
```

### Registry-Integrated Workflow

```python
from latch import workflow, small_task
from latch.registry.table import Table

@small_task
def process_and_track(sample_name: str, table_id: str) -> str:
    """Process a sample tracked in a Registry table and write status/result back."""
    table = Table(table_id)  # construct by id; no Table.get classmethod

    # Find the record by name. list_records() yields pages of {record_id: Record}.
    sample = None
    for page in table.list_records():
        for record in page.values():
            if record.get_name() == sample_name:
                sample = record
                break
        if sample is not None:
            break
    if sample is None:
        raise ValueError(f"No record named {sample_name}")

    # Read column values
    values = sample.get_values()
    input_file = values["fastq_file"]  # a LatchFile for a 'file'-typed column
    # ... processing logic produces an output LatchFile ...

    # Write status/result back via the table.update() transaction (upsert by name)
    with table.update() as updater:
        updater.upsert_record(sample_name, status="completed", result=input_file)
    return "Success"

@workflow
def registry_workflow(sample_name: str, table_id: str) -> str:
    """Workflow integrated with the Latch Registry."""
    return process_and_track(sample_name=sample_name, table_id=table_id)
```

## Best Practices

### Workflow Design
1. Use type annotations for all parameters
2. Write clear docstrings (appear in UI)
3. Start with standard task decorators, scale up if needed
4. Break complex workflows into modular tasks
5. Implement proper error handling

### Data Management
6. Use consistent folder structures
7. Define Registry schemas before bulk entry
8. Use linked records for relationships
9. Store metadata in Registry for traceability

### Resource Configuration
10. Right-size resources (don't over-allocate)
11. Use GPU only when algorithms support it
12. Monitor execution metrics and optimize
13. Design for parallel execution when possible

### Development Workflow
14. Test locally with Docker before registration
15. Use version control for workflow code
16. Document resource requirements
17. Profile workflows to determine actual needs

## Troubleshooting

### Common Issues

**Registration Failures:**
- Ensure Docker is running
- Check authentication with `latch login`
- Verify all dependencies in Dockerfile
- Use `--verbose` flag for detailed logs

**Resource Problems:**
- Out of memory: Increase memory in task decorator
- Timeouts: Increase timeout parameter
- Storage issues: Increase ephemeral storage_gib

**Data Access:**
- Use correct `latch:///` path format
- Verify file exists in workspace
- Check permissions for shared workspaces

**Type Errors:**
- Add type annotations to all parameters
- Use LatchFile/LatchDir for file/directory parameters
- Ensure workflow return type matches actual return

## Additional Resources

- Official Documentation: https://docs.latch.bio
- GitHub Repository (verify current API/decorator names here): https://github.com/latchbio/latch
- Support: support@latch.bio

