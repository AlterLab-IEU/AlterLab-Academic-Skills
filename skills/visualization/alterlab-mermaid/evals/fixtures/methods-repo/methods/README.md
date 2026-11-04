# Methods

## Sample collection

Gill tissue was dissected from 96 mussels (32 per tidal height) after the final heat-wave cycle,
flash-frozen in liquid nitrogen, and stored at -80 °C until extraction.

## Experimental decision logic

Every sample follows the same rules from extraction to analysis. These rules were fixed before
sequencing and are applied by `pipeline/rules/qc.smk`.

1. **RNA extraction.** Extract total RNA (TRIzol + column clean-up).
2. **RNA quality gate.** Measure RIN on the Bioanalyzer and purity on the NanoDrop.
   - Pass if RIN ≥ 7 **and** A260/280 is between 1.8 and 2.1.
   - If it fails, re-extract from the remaining tissue. A sample may be re-extracted at most
     **two times**. If it still fails after the second re-extraction, **exclude** it and record the
     reason in `exclusions.csv`.
3. **Library preparation.** Poly-A selected, stranded libraries; pool and sequence (PE150).
4. **Depth check.** After demultiplexing:
   - ≥ 20 M read pairs: continue to alignment.
   - < 20 M read pairs: send the library for **one** top-up sequencing run, then re-check. If it is
     still below 20 M after the top-up, **exclude** it (reason "low depth" in `exclusions.csv`).
5. **Alignment check.** Align with STAR to the reference genome.
   - Uniquely mapped rate ≥ 70%: **include** in the count matrix for differential expression.
   - Below 70%: **flag for manual review** (possible contamination or wrong species). The reviewer
     either includes the sample or excludes it with a written reason.

## Library preparation details

Libraries were prepared with 500 ng input RNA and 12 PCR cycles. Pooled libraries were sequenced
on two lanes.

## Differential expression

Counts were modelled in DESeq2 with tidal height, heat treatment, and their interaction.
