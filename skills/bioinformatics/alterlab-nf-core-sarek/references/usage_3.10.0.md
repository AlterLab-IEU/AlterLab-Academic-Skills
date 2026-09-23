# nf-core/sarek 3.10.0 — Usage Reference

Source: https://nf-co.re/sarek/3.10.0/docs/usage/ (pinned release `3.10.0`,
"Aktse", released 2026-08-12). Everything below is for that pinned version.
Newer releases may rename or change defaults — keep `-r 3.10.0` unless the user
explicitly asks to upgrade.

`3.10.0` declares `nextflowVersion = '!>=25.10.4'`, so an older Nextflow refuses
to launch it. The release also completed the migration to topic channels and to
Nextflow **strict syntax**, which becomes the parser in Nextflow 26.x — relevant
if you maintain custom local modules or a `modules.config` alongside it.

## Minimal command

```bash
nextflow run nf-core/sarek -r 3.10.0 \
    -profile docker \
    --input samplesheet.csv \
    --outdir ./results \
    --genome GATK.GRCh38 \
    --tools haplotypecaller
```

- `-r 3.10.0` — pins the pipeline revision. Required for reproducibility.
- `-profile` — **mandatory**, reflects the compute/software environment. Common
  values: `docker`, `singularity`, `apptainer`, `conda`. A `test` profile runs a
  tiny built-in dataset. Combine with institutional configs as needed.
- `--input` — path to the samplesheet CSV (see `samplesheet_schema.md`).
- `--outdir` — results directory (required).
- `--genome` — iGenomes/GATK reference key, e.g. `GATK.GRCh38` or `GATK.GRCh37`.
  Selecting the GATK key wires up the BQSR known-sites automatically (below).
- `--tools` — caller selection. **Defaults to Strelka if omitted** (see
  `caller_accuracy.md`). Set it explicitly.

## Aligner (`--aligner`)

- `bwa-mem` — default.
- `bwa-mem2` — faster, same algorithm family.
- `dragmap` — DRAGEN-style mapper.
- `sentieon-bwamem` — Sentieon's BWA implementation (needs a Sentieon licence).
- `parabricks` — GPU-accelerated; requires a GPU profile
  (e.g. `--aligner parabricks -profile docker,gpu`).

The nf-core benchmark (Hanssen et al., 2024) reports BWA-MEM and BWA-MEM2 give
higher recall than DragMap; see `caller_accuracy.md`.

## Steps (`--step`)

Start or resume the pipeline at a point matching the inputs you already have:

| `--step` | Starts from |
|---|---|
| `mapping` (default) | FASTQ → alignment |
| `markduplicates` | mapped BAM/CRAM → duplicate marking |
| `prepare_recalibration` | → BaseRecalibrator (build recal table) |
| `recalibrate` | → ApplyBQSR |
| `variant_calling` | recalibrated BAM/CRAM → calling |
| `annotate` | existing VCF → annotation only |

Pair `--step` with the matching samplesheet columns (BAM/CRAM/VCF re-entry rows;
see `samplesheet_schema.md`) and Nextflow `-resume` to reuse cached work.

## Preprocessing = GATK best practice

With the GATK genome key, sarek runs the GATK data-pre-processing chain:

1. **Alignment** (`--aligner`).
2. **MarkDuplicates** — flag PCR/optical duplicates.
3. **BQSR** — `BaseRecalibrator` builds a recalibration table from known sites,
   then `ApplyBQSR` writes recalibrated reads.

### BQSR known-sites / GRCh38 resource bundle

These reference resources ship with the GATK genome key and feed recalibration
and calling (per the 3.10.0 reference table):

| Resource | Role | Used by (per docs) |
|---|---|---|
| **dbSNP** | known SNP sites | BaseRecalibrator, GenotypeGVCFs, HaplotypeCaller, ControlFREEC |
| **Mills and 1000G gold-standard indels** (`known_indels`) | known indel sites | BaseRecalibrator(Spark), FilterVariantTranches |

Source bundle: the Broad GATK resource bundle for hg38
(`genomics-public-data/resources/broad/hg38/v0/`), referenced by the pipeline as
`GATKBundle`. With `--genome GATK.GRCh38` you do not supply these by hand.

## Whole-exome / panel (WES)

Pass **both**:

- `--wes` — a boolean that flips targeted-sequencing settings in the individual
  tools ("Enable when exome or panel data is provided"), and
- `--intervals targets.bed` — the capture-kit BED, so calling is restricted to the
  targeted regions.

They do different jobs: `--intervals` limits *where* calling happens; `--wes` tells
the callers and QC modules that coverage is targeted rather than uniform. Running
exome data without `--wes` produces results that look fine but carry WGS-tuned
thresholds. (`--intervals` also speeds WGS by parallelizing over interval lists.)

## Joint germline

Add `--joint_germline` to `--tools haplotypecaller` to run joint genotyping
across a GVCF cohort (HaplotypeCaller in GVCF mode → joint GenotypeGVCFs).

## Output layout

Results are written under `--outdir`, including:

- `preprocessing/` — recalibrated CRAM/BAM and BQSR tables.
- `variant_calling/<tool>/` — per-caller VCFs (e.g. `haplotypecaller/`,
  `mutect2/`, `strelka/`, `deepvariant/`).
- `reports/` — MultiQC and per-tool QC.

Hand the VCFs to `alterlab-pysam` (parse), `alterlab-tiledbvcf` (store/query),
and `alterlab-clinvar` / `alterlab-gnomad` / `alterlab-cosmic` (annotate).
