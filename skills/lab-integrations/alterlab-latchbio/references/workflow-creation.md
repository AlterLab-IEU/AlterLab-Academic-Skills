# Workflow Creation and Registration

## Overview
The Latch SDK enables defining serverless bioinformatics workflows using Python decorators and deploying them with automatic containerization and UI generation.

## Installation

Install the Latch SDK (Python 3.9+):
```bash
uv pip install latch   # or: pip install latch
```

**Prerequisites:**
- Docker must be installed and running locally (registration builds a container)
- Latch account credentials (`latch login`)

## Initializing a New Workflow

Create a new workflow template:
```bash
latch init <workflow-name>

# Pick a starting template with --template; valid values include:
#   empty, docker, subprocess, r, conda, snakemake, nfcore
latch init my-nf-wf --template nfcore
```

This generates a workflow directory with:
- `wf/__init__.py` - Main workflow definition
- `Dockerfile` - Container configuration
- `version` - Version tracking file

## Workflow Definition Structure

### Basic Workflow Example

```python
from latch import workflow
from latch.types import LatchFile, LatchDir

@workflow
def my_workflow(input_file: LatchFile, output_dir: LatchDir) -> LatchFile:
    """
    Workflow description that appears in the UI

    Args:
        input_file: Input file description
        output_dir: Output directory description
    """
    return process_task(input_file, output_dir)
```

### Task Definition

Tasks are the individual computation steps within workflows:

```python
from latch import small_task, large_task

@small_task
def process_task(input_file: LatchFile, output_dir: LatchDir) -> LatchFile:
    """Task-level computation"""
    # Processing logic here
    return output_file
```

### Task Resource Decorators

The SDK provides multiple task decorators for different resource requirements:

- `@small_task` - Default resources for lightweight tasks
- `@large_task` - Increased memory and CPU
- `@small_gpu_task` - GPU-enabled tasks with minimal resources
- `@large_gpu_task` - GPU-enabled tasks with maximum resources
- `@custom_task` - Custom resource specifications

## Registering Workflows

Register the workflow to the Latch platform:
```bash
latch register <workflow-directory>
```

The registration process:
1. Builds Docker container with all dependencies
2. Serializes workflow code
3. Uploads container to registry
4. Generates no-code UI automatically
5. Makes workflow available on the platform

### Registration Output

Upon successful registration:
- Workflow appears in Latch workspace
- Automatic UI is generated with parameter forms
- Version is tracked and containerized
- Workflow can be executed immediately

## Supporting Multiple Pipeline Languages

Latch supports uploading existing pipelines in:
- **Python** - Native Latch SDK workflows
- **Nextflow** - Import existing Nextflow pipelines
- **Snakemake** - Import existing Snakemake pipelines

### Nextflow Integration

Scaffold with `latch init --template nfcore`, point the metadata at your `main.nf`, then register. The Latch SDK wraps the Nextflow pipeline (generating a Latch entrypoint) and builds the container, giving it an auto-generated no-code UI on the platform:
```bash
# register the directory, pointing at the Nextflow entrypoint script
latch register <workflow-directory> --nf-script main.nf

# or use the dedicated nextflow command group
latch nextflow register <workflow-directory>
```

### Snakemake Integration

Scaffold with `latch init --template snakemake`, then register pointing at the Snakefile:
```bash
latch register <workflow-directory> --snakefile Snakefile
```
For local iteration on a Snakemake workflow, `latch develop --snakemake <workflow-directory>` runs it in a remote dev environment.

## Workflow Execution

The primary way to run a registered workflow is its auto-generated UI on the Latch platform: open the workflow, fill the parameter form, and launch.

### From Python (inside a running execution)

Helpers in `latch.executions` operate on the *current* execution rather than launching new ones — e.g. rename the run or attach result links so they surface in the UI:

```python
from latch.executions import rename_current_execution, add_execution_results

rename_current_execution("rnaseq - sample S001")
add_execution_results(["latch:///results/S001"])
```

> Note: older CLI launch helpers (`latch launch`, `latch get-params`) are deprecated. Prefer launching from the platform UI, or script launches via the Latch GraphQL API. Verify any programmatic-launch API against the current SDK before relying on it.

## Launch Plans

Launch plans define preset parameter configurations:

A launch plan populates the workflow's console form with named preset parameters. `create()` takes the workflow function, a launch-plan name, and `default_params` (note the keyword name and that the first argument is the workflow object, not a string):

```python
from latch.resources.launch_plan import LaunchPlan
from latch.types import LatchFile, LatchDir
from wf import my_workflow

LaunchPlan(
    my_workflow,
    "Default config",
    default_params={
        "input_file": LatchFile("latch:///data/sample.fastq"),
        "output_dir": LatchDir("latch:///results"),
    },
)
```

## Workflow UI Metadata and Conditional Sections

The workflow's docstring and a `LatchMetadata`/`LatchParameter` block control how the parameter form renders (labels, descriptions, grouping). The UI also supports **Fork / conditional sections** that show parameters only when an upstream choice selects a given branch. The exact metadata API changes between SDK versions, so check the current docs (`latch.types.metadata`) for `LatchMetadata`, `LatchParameter`, and the Fork/`_IsPresent` constructs before wiring up a conditional section.

## Best Practices

1. **Type Annotations**: Always use type hints for workflow parameters
2. **Docstrings**: Provide clear docstrings - they populate the UI descriptions
3. **Version Control**: Use semantic versioning for workflow updates
4. **Testing**: Test workflows locally before registration
5. **Resource Sizing**: Start with smaller resource decorators and scale up as needed
6. **Modular Design**: Break complex workflows into reusable tasks
7. **Error Handling**: Implement proper error handling in tasks
8. **Logging**: Use Python logging for debugging and monitoring

## Common Patterns

### Multi-Step Pipeline

```python
from latch import workflow, small_task
from latch.types import LatchFile

@small_task
def quality_control(input_file: LatchFile) -> LatchFile:
    """QC step"""
    return qc_output

@small_task
def alignment(qc_file: LatchFile) -> LatchFile:
    """Alignment step"""
    return aligned_output

@workflow
def rnaseq_pipeline(input_fastq: LatchFile) -> LatchFile:
    """RNA-seq analysis pipeline"""
    qc_result = quality_control(input_file=input_fastq)
    aligned = alignment(qc_file=qc_result)
    return aligned
```

### Parallel Processing

```python
from typing import List
from latch import workflow, small_task, map_task
from latch.types import LatchFile

@small_task
def process_sample(sample: LatchFile) -> LatchFile:
    """Process individual sample"""
    return processed_sample

@workflow
def batch_pipeline(samples: List[LatchFile]) -> List[LatchFile]:
    """Process multiple samples in parallel"""
    return map_task(process_sample)(sample=samples)
```

## Troubleshooting

### Common Issues

1. **Docker not running**: Ensure Docker daemon is active
2. **Authentication errors**: Run `latch login` to refresh credentials
3. **Build failures**: Check Dockerfile for missing dependencies
4. **Type errors**: Ensure all parameters have proper type annotations

### Debug Mode

Enable verbose logging during registration:
```bash
latch register --verbose <workflow-directory>
```

## References

- Official Documentation: https://docs.latch.bio
- GitHub Repository (authoritative for CLI flags and decorator/API names): https://github.com/latchbio/latch
