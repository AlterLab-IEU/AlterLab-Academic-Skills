# Pinned tool versions & upstream facts

All version-specific claims in this skill trace to the upstream release pages
below. Re-verify against the linked release notes before changing a pin.

## salmon — 2.x (the Rust rewrite)

- Source: COMBINE-lab/salmon — https://github.com/COMBINE-lab/salmon, with the
  breaking changes catalogued in the repo's `MIGRATION.md`.
- Version in bioconda at review time (2026-09-23): **2.7.0** (uploaded 2026-08-30).
- **salmon 2.0 is a from-scratch Rust rewrite.** Same workflow
  (`salmon index` -> `salmon quant` -> `quant.sf`), same downstream output formats,
  single portable binary with no Boost/compiler dependency. The final C++ release is
  salmon **1.12.0**, kept on the upstream `cpp` branch and packaged as `salmon-cpp`.
- **Index break.** 2.0 uses a new index format and *cannot read C++ (pufferfish)
  indices*; the mismatch is detected and rejected with a clear error in both
  directions. Rebuild with the binary you quantify with.
- **Outputs are stable.** `quant.sf` is unchanged, and inferential replicates
  (`aux_info/bootstrap/...` from `--numBootstraps` and `--numGibbsSamples`) keep the
  C++ format, so tximport / tximeta / fishpond / swish work unmodified. The bias
  diagnostic dumps in `aux_info/` moved to a documented Rust format; no standard R
  package reads them.
- **Removed subcommand:** `salmon alevin`. It prints a redirect and exits. Single-cell
  moved to the **piscem + alevin-fry** ecosystem
  (https://github.com/COMBINE-lab/piscem, https://github.com/COMBINE-lab/alevin-fry).
- **Removed options (now error):** `--features` (index); `--mimicBT2`,
  `--mimicStrictBT2`, `--minAssignedFrags`, `--alternativeInitMode`,
  `--bootstrapReproject`, `--noGammaDraw`, `--numBiasSamples` (quant);
  `--auxTargetFile`, `--writeOrphanLinks` (quant -a).
- **Accepted but ignored (parse + warn):** `--validateMappings` (selective alignment is
  the default), `--eqclasses`, `--noFragLengthDist`, `--noSingleFragProb`,
  `--mismatchSeedSkip`, `--disableChainingHeuristic`, `--hitFilterPolicy`,
  `--maxRecoverReadOcc`, `--filterSize` (index), and several `quant -a` options.
- **New in 2.0:** `--sketch` (alignment-free pseudoalignment mode),
  `--sketchStrictOrphans`, `--allowDovetail` honored in sketch mode, and
  `--ignoreTxVersion` for `-g/--geneMap` matching. With `-g`, unmatched transcripts are
  still emitted as single-transcript genes (nothing is dropped), but 2.x warns once
  with a count and writes the names to `aux_info/genemap_unmatched_txps.json` instead
  of warning per transcript.

## kallisto — v0.52.0

- Source: pachterlab/kallisto releases — https://github.com/pachterlab/kallisto/releases
- Latest release at authoring time: **v0.52.0** (released 25 Feb). This release
  restores features (pseudobam, genomebam, fusion) that were missing after the
  index-structure rework; v0.51.1 and v0.51.0 precede it.

## kb-python (the `kb` CLI)

- Source: pachterlab/kb_python releases — https://github.com/pachterlab/kb_python/releases
- Latest release at authoring time: **v0.30.2** (released 19 May).
- **lr-kallisto / `--long`.** kb-python v0.29.1 release notes: *"Added
  lr-kallisto (--long) option, and enabling k>31"* and shipped kallisto/bustools
  binaries with and without long k-mer support. That release upgraded the bundled
  kallisto to **0.51.1** and bustools to **0.44.1**. (The bundled kallisto in a
  given kb-python build may lag the standalone kallisto release above; check
  `kb info` / your install for the exact bundled version.)

## nf-core/rnaseq — v3.26.0 (turnkey alternative)

- Source: nf-core/rnaseq releases — https://github.com/nf-core/rnaseq/releases
- Latest release at authoring time: **v3.26.0** ("Chromium Cuttlefish", released
  7 May).
- **Default route is `--aligner star_salmon`.** From the v3.26.0 usage docs:
  *"By default, the pipeline uses STAR (i.e. `--aligner star_salmon`) to map the
  raw FastQ reads to the reference genome, project the alignments onto the
  transcriptome and to perform the downstream BAM-level quantification with
  Salmon."* (https://nf-co.re/rnaseq/3.26.0/docs/usage)

## tximport / tximeta

- Bioconductor packages used for aggregating transcript-level estimates to the
  gene level (`tximport`) with full transcriptome provenance (`tximeta`,
  `linkedTxome`). They are the canonical R import layer for salmon/kallisto
  output feeding DESeq2. The Python helper in this skill reproduces the
  `countsFromAbundance = "lengthScaledTPM"` computation so the workflow can stay
  in `uv`; use the R packages when you need full `tximeta` metadata.
