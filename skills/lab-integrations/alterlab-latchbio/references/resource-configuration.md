# Resource Configuration

## Overview
Latch SDK provides flexible resource configuration for workflow tasks, enabling efficient execution on appropriate compute infrastructure including CPU, GPU, and memory-optimized instances.

## Task Resource Decorators

### Standard Decorators

The SDK provides pre-configured task decorators for common resource requirements:

#### @small_task
Default configuration for lightweight tasks:
```python
from latch import small_task

@small_task
def lightweight_processing():
    """Minimal resource requirements"""
    pass
```

**Use cases:**
- File parsing and manipulation
- Simple data transformations
- Quick QC checks
- Metadata operations

#### @large_task
Increased CPU and memory for intensive computations:
```python
from latch import large_task

@large_task
def intensive_computation():
    """Higher CPU and memory allocation"""
    pass
```

**Use cases:**
- Large file processing
- Complex statistical analyses
- Assembly tasks
- Multi-threaded operations

#### @small_gpu_task
GPU-enabled with minimal resources:
```python
from latch import small_gpu_task

@small_gpu_task
def gpu_inference():
    """GPU-enabled task with basic resources"""
    pass
```

**Use cases:**
- Neural network inference
- Small-scale ML predictions
- GPU-accelerated libraries

#### @large_gpu_task
GPU-enabled with maximum resources:
```python
from latch import large_gpu_task

@large_gpu_task
def gpu_training():
    """GPU with maximum CPU and memory"""
    pass
```

**Use cases:**
- Deep learning model training
- Protein structure prediction (AlphaFold)
- Large-scale GPU computations

### Custom Task Configuration (CPU/memory only)

For precise control over CPU, memory, and storage, use the `@custom_task` decorator:

```python
from latch import custom_task

@custom_task(
    cpu=8,
    memory=32,        # Gibibytes of RAM
    storage_gib=100,  # ephemeral storage in GiB (default 500)
)
def custom_processing():
    """Task with custom CPU/memory/storage specifications"""
    pass
```

#### Custom Task Parameters

`custom_task(cpu, memory, *, storage_gib=500, timeout=0)`:

- **cpu**: Number of CPU cores, int (up to 126). May also be a callable for dynamic sizing.
- **memory**: RAM in GiB, int (up to ~975 GiB). May also be a callable.
- **storage_gib**: Ephemeral storage in GiB, int (default 500, up to ~4949 GiB).
- **timeout**: Maximum execution time, a `datetime.timedelta` or int seconds (default `0` = no timeout).

> `@custom_task` does **not** take `gpu`/`gpu_type` parameters. For GPUs, use the dedicated GPU task decorators below.

## GPU Configuration

GPUs are requested via dedicated, pre-configured task decorators — not by passing a GPU flag to `@custom_task`.

### Available GPU decorators

- `@small_gpu_task` — 1 GPU, modest CPU/memory (g4dn.2xlarge class)
- `@large_gpu_task` — 1 GPU, larger CPU/memory (g5.16xlarge class)
- `@v100_x1_task`, `@v100_x4_task`, `@v100_x8_task` — 1/4/8 NVIDIA V100 GPUs
- `@g6e_xlarge_task` … `@g6e_48xlarge_task` — NVIDIA L40S GPUs, increasing CPU/RAM/GPU counts

```python
from latch import small_gpu_task, large_gpu_task, v100_x1_task

@small_gpu_task
def gpu_inference():
    """Single-GPU inference on modest resources"""
    pass

@large_gpu_task
def alphafold_prediction():
    """AlphaFold structure prediction on a large GPU node"""
    pass
```

### Multi-GPU Tasks

```python
from latch import v100_x4_task

@v100_x4_task
def multi_gpu_training():
    """Distributed training across 4 V100 GPUs"""
    pass
```

## Resource Selection Strategies

### By Computational Requirements

**Memory-Intensive Tasks:**
```python
@custom_task(cpu=4, memory=128)  # High memory, moderate CPU
def genome_assembly():
    pass
```

**CPU-Intensive Tasks:**
```python
@custom_task(cpu=64, memory=32)  # High CPU, moderate memory
def parallel_alignment():
    pass
```

**I/O-Intensive Tasks:**
```python
@custom_task(cpu=8, memory=16, storage_gib=1000)  # Large ephemeral storage
def data_preprocessing():
    pass
```

### By Workflow Phase

**Quick Validation:**
```python
@small_task
def validate_inputs():
    """Fast input validation"""
    pass
```

**Main Computation:**
```python
@large_task
def primary_analysis():
    """Resource-intensive analysis"""
    pass
```

**Result Aggregation:**
```python
@small_task
def aggregate_results():
    """Lightweight result compilation"""
    pass
```

## Workflow Resource Planning

### Complete Pipeline Example

```python
from latch import workflow, small_task, large_task, large_gpu_task
from latch.types import LatchFile

@small_task
def quality_control(fastq: LatchFile) -> LatchFile:
    """QC doesn't need much resources"""
    return qc_output

@large_task
def alignment(fastq: LatchFile) -> LatchFile:
    """Alignment benefits from more CPU"""
    return bam_output

@large_gpu_task
def variant_calling(bam: LatchFile) -> LatchFile:
    """GPU-accelerated variant caller"""
    return vcf_output

@small_task
def generate_report(vcf: LatchFile) -> LatchFile:
    """Simple report generation"""
    return report

@workflow
def genomics_pipeline(input_fastq: LatchFile) -> LatchFile:
    """Resource-optimized genomics pipeline"""
    qc = quality_control(fastq=input_fastq)
    aligned = alignment(fastq=qc)
    variants = variant_calling(bam=aligned)
    return generate_report(vcf=variants)
```

## Timeout Configuration

### Setting Timeouts

```python
from latch import custom_task

@custom_task(
    cpu=8,
    memory=32,
    timeout=10800  # 3 hours in seconds
)
def long_running_analysis():
    """Analysis with extended timeout"""
    pass
```

### Timeout Best Practices

1. **Estimate conservatively**: Add buffer time beyond expected duration
2. **Monitor actual runtimes**: Adjust based on real execution data
3. **Default timeout**: Most tasks have 1-hour default
4. **Maximum timeout**: Check platform limits for very long jobs

## Storage Configuration

### Ephemeral Storage

Configure temporary storage for intermediate files:

```python
@custom_task(
    cpu=8,
    memory=32,
    storage_gib=500  # 500 GB temporary storage
)
def process_large_dataset():
    """Task with large intermediate files"""
    # Ephemeral storage available at /tmp
    temp_file = "/tmp/intermediate_data.bam"
    pass
```

### Storage Guidelines

- Default storage is typically sufficient for most tasks
- Specify larger storage for tasks with large intermediate files
- Ephemeral storage is cleared after task completion
- Use LatchDir for persistent storage needs

## Cost Optimization

### Resource Efficiency Tips

1. **Right-size resources**: Don't over-allocate
2. **Use appropriate decorators**: Start with standard decorators
3. **GPU only when needed**: GPU tasks cost more
4. **Parallel small tasks**: Better than one large task
5. **Monitor usage**: Review actual resource utilization

### Example: Cost-Effective Design

```python
# INEFFICIENT: All tasks use large resources
@large_task
def validate_input():  # Over-provisioned
    pass

@large_task
def simple_transformation():  # Over-provisioned
    pass

# EFFICIENT: Right-sized resources
@small_task
def validate_input():  # Appropriate
    pass

@small_task
def simple_transformation():  # Appropriate
    pass

@large_task
def intensive_analysis():  # Appropriate
    pass
```

## Monitoring and Debugging

### Resource Usage Monitoring

During workflow execution, monitor:
- CPU utilization
- Memory usage
- GPU utilization (if applicable)
- Execution duration
- Storage consumption

### Common Resource Issues

**Out of Memory (OOM):**
```python
# Solution: Increase memory allocation
@custom_task(cpu=8, memory=64)  # Increased from 32 to 64 GB
def memory_intensive_task():
    pass
```

**Timeout:**
```python
# Solution: Increase timeout
@custom_task(cpu=8, memory=32, timeout=14400)  # 4 hours
def long_task():
    pass
```

**Insufficient Storage:**
```python
# Solution: Increase ephemeral storage
@custom_task(cpu=8, memory=32, storage_gib=1000)
def large_intermediate_files():
    pass
```

## Conditional Resources

Dynamically allocate resources based on input:

```python
from latch import workflow, custom_task
from latch.types import LatchFile

def get_resource_config(file_size_gb: float):
    """Determine resources based on file size"""
    if file_size_gb < 10:
        return {"cpu": 4, "memory": 16}
    elif file_size_gb < 100:
        return {"cpu": 16, "memory": 64}
    else:
        return {"cpu": 32, "memory": 128}

# Note: Resource decorators must be static
# Use multiple task variants for different sizes
@custom_task(cpu=4, memory=16)
def process_small(file: LatchFile) -> LatchFile:
    pass

@custom_task(cpu=16, memory=64)
def process_medium(file: LatchFile) -> LatchFile:
    pass

@custom_task(cpu=32, memory=128)
def process_large(file: LatchFile) -> LatchFile:
    pass
```

## Best Practices Summary

1. **Start small**: Begin with standard decorators, scale up if needed
2. **Profile first**: Run test executions to determine actual needs
3. **GPU sparingly**: Only use GPU when algorithms support it
4. **Parallel design**: Break into smaller tasks when possible
5. **Monitor and adjust**: Review execution metrics and optimize
6. **Document requirements**: Comment why specific resources are needed
7. **Test locally**: Use Docker locally to validate before registration
8. **Consider cost**: Balance performance with cost efficiency

## Platform-Specific Considerations

### Available Resources

Latch platform provides (verify current limits in the docs/SDK, as instance types change):
- CPU: up to ~126 cores per task (`custom_task` cpu cap)
- Memory: up to ~975 GiB per task
- GPUs: via the dedicated decorators above — V100 (`v100_x{1,4,8}_task`) and L40S (`g6e_*_task`), plus the generic `small_gpu_task`/`large_gpu_task`
- Storage: ephemeral storage up to ~4949 GiB (`storage_gib`)

### Resource Limits

Check current platform limits:
- Maximum CPUs per task
- Maximum memory per task
- Maximum GPU allocation
- Maximum concurrent tasks

### Quotas and Limits

Be aware of workspace quotas:
- Total concurrent executions
- Total resource allocation
- Storage limits
- Execution time limits

Contact Latch support for quota increases if needed.
