# salmon quant — flags, library type, QC

Targets salmon **2.x** (the Rust rewrite; selective alignment by default). See
tool_versions.md for the version facts (2.0 cannot read C++/pufferfish indices;
`salmon alevin` removed; `--validateMappings` accepted but ignored).

## Mapping-based quant command

```bash
salmon quant \
  -i salmon_index \
  -l A \
  -1 sampleA_R1.fastq.gz -2 sampleA_R2.fastq.gz \
  --gcBias \
  -p 8 \
  -o quants/sampleA
```

| Flag | Meaning |
|------|---------|
| `-i` | path to the (decoy-aware, freshly built) index |
| `-l A` | **auto-detect** library type / strandedness; verify the result afterwards |
| `-1` / `-2` | paired-end read files (use `-r` for single-end) |
| `--gcBias` | correct fragment-level GC bias (recommended for DE) |
| `--seqBias` | optional: correct 5'/3' sequence-specific bias |
| `--posBias` | optional: correct positional (5'/3' coverage) bias |
| `--sketch` | opt **out** of selective alignment into faster alignment-free pseudoalignment (2.x) |
| `--ignoreTxVersion` | with `-g/--geneMap`, match transcript IDs ignoring the trailing `.N` (2.x) |
| `--numBootstraps` / `--numGibbsSamples` | inferential replicates, written in the same format fishpond/swish expect |
| `-p` | threads |
| `-o` | per-sample output directory |

Selective alignment is the default in 2.x, so there is no flag that enables it.
`--validateMappings` parses and warns; `--mimicBT2`, `--mimicStrictBT2`,
`--minAssignedFrags`, `--numBiasSamples` and `--alternativeInitMode` are removed and
now error.

## Outputs (per sample)

- `quant.sf` — transcript-level table: `Name`, `Length`, `EffectiveLength`,
  `TPM`, `NumReads`. This is the file `tximport` reads.
- `lib_format_counts.json` — the **inferred library type** and compatible
  fragment counts. Always check this when using `-l A`.
- `logs/salmon_quant.log` and `aux_info/meta_info.json` — overall mapping rate
  and run metadata; record the mapping rate as a QC metric.

## Library type (`-l`)

`-l A` lets salmon infer strandedness from the data. The inferred code (e.g.
`ISR`, `ISF`, `IU`) appears in `lib_format_counts.json`. Only override with an
explicit code when you have a documented, trustworthy protocol; a wrong manual
`-l` silently biases counts. If the inferred type is inconsistent across samples
that should share a protocol, investigate before proceeding.

## QC checks before handoff

- **Mapping rate** (`aux_info/meta_info.json` → `percent_mapped`): unexpectedly
  low rates suggest a contaminating organism, wrong reference, or adapter/quality
  issues upstream.
- **Consistent inferred library type** across replicates.
- **Effective length** sanity: very short effective lengths flag fragment-length
  distribution problems for single-end data (set `--fldMean`/`--fldSD` if you
  must quantify SE without a distribution).

## Single-end reads

```bash
salmon quant -i salmon_index -l A -r sampleA.fastq.gz \
  --gcBias -p 8 -o quants/sampleA
```

For SE data salmon cannot empirically learn the fragment-length distribution;
provide `--fldMean` and `--fldSD` if known.
