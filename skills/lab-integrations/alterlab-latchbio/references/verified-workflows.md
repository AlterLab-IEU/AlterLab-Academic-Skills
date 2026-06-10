# Verified Workflows

## Overview
Latch Verified Workflows are production-ready, pre-built bioinformatics pipelines maintained by Latch. They are available to launch from the platform UI, and a subset is importable from the `latch.verified` Python module for use inside your own SDK workflows.

> Important: the set of pipelines importable from `latch.verified` is **small and specific**, and differs from the (larger) catalog of Verified Workflows shown in the platform UI. Before writing `from latch.verified import <name>`, confirm the exact symbol exists (`python -c "import latch.verified as v; print(dir(v))"`) and check its parameters — verified-workflow signatures change between releases.

## Importable from `latch.verified`

As of the current SDK, `latch.verified` exports:

| Import | Pipeline |
| --- | --- |
| `rnaseq` | Bulk RNA-seq alignment + quantification |
| `deseq2_wf` | DESeq2 differential expression |
| `trim_galore` | Adapter / quality trimming |
| `mafft` | Multiple sequence alignment |
| `gene_ontology_pathway_analysis` | GO pathway / enrichment analysis |

```python
from latch.verified import (
    rnaseq,
    deseq2_wf,
    trim_galore,
    mafft,
    gene_ontology_pathway_analysis,
)
```

These are ordinary Latch workflow functions: call them inside a `@workflow`, passing `LatchFile`/`LatchDir` inputs. Inspect each one's signature (e.g. `help(rnaseq)` or its docstring/UI parameter form) for the exact parameter names — do not assume them.

### Bulk RNA-seq (`rnaseq`)
- Read quality control, adapter trimming, alignment, and gene-level quantification, with a MultiQC report.
- Takes FASTQ inputs (single- or paired-end) and a reference genome selection.

### Differential expression (`deseq2_wf`)
- Normalization/variance stabilization, differential testing, and standard plots (MA, volcano, PCA) from a count matrix plus sample metadata and a design formula.

### Trimming (`trim_galore`)
- Automatic adapter detection plus quality trimming, single- or paired-end, with FastQC integration.

### Multiple sequence alignment (`mafft`)
- MAFFT alignment (FFT-NS / G-INS-i / L-INS-i families) with automatic algorithm selection for a FASTA input.

### Pathway enrichment (`gene_ontology_pathway_analysis`)
- GO-based enrichment over a gene list.

## Pipelines available in the platform UI (not in `latch.verified`)

Many widely used pipelines — e.g. AlphaFold / ColabFold (protein structure), single-cell tools (ArchR for scATAC-seq, scVelo for RNA velocity, empty-droplet calling), and CRISPR editing analysis (CRISPResso2) — are offered as Verified Workflows you launch from the platform UI. They are **not** guaranteed to be importable from `latch.verified` under those names. To use one, launch it from the platform UI, or wrap your own task around the underlying tool.

## Combining a verified workflow with custom tasks

```python
from latch import workflow, small_task
from latch.verified import rnaseq
from latch.types import LatchFile, LatchDir

@small_task
def preprocess(raw: LatchFile) -> LatchFile:
    """Custom preprocessing before the verified pipeline."""
    # custom logic here
    return raw

@small_task
def postprocess(results: LatchDir) -> LatchFile:
    """Custom post-analysis on the verified pipeline's output."""
    # custom logic here
    return LatchFile("summary.txt", "latch:///results/summary.txt")

@workflow
def custom_rnaseq(input_fastq: LatchFile, output_dir: LatchDir) -> LatchFile:
    """Custom preprocessing -> verified rnaseq -> custom postprocessing."""
    cleaned = preprocess(raw=input_fastq)
    # Pass cleaned into rnaseq(...) using its actual parameter names (verify first).
    results = rnaseq(...)  # noqa: F821 - fill in real params from the workflow's signature
    return postprocess(results=results)
```

## When to use verified vs. custom

**Use a verified workflow for:** standard, well-established analyses where reproducibility and a maintained implementation matter (e.g. bulk RNA-seq, DESeq2, trimming, MSA).

**Build a custom workflow for:** novel methods, custom preprocessing, proprietary tools, or anything not covered by a verified pipeline.

## Versioning

Verified workflows are versioned and maintained by Latch (tool upgrades, fixes). Pin/launch a specific version through the workflow's launch interface; consult the workflow's page for the available versions and parameters.

## Support and Updates

- Documentation: https://docs.latch.bio
- GitHub (authoritative source for `latch.verified` exports and signatures): https://github.com/latchbio/latch
- Support: support@latch.bio
