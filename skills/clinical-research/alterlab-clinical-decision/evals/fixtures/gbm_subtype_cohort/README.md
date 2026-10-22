# Glioblastoma molecular-subtype cohort export (SYNTHETIC)

**Synthetic data.** Every record in `gbm_cohort.csv` was produced by a seeded simulation for testing
analysis software. None of it describes a real patient, and none of it is evidence about
temozolomide or bevacizumab.

30 patients with newly diagnosed IDH-wildtype glioblastoma treated with temozolomide plus
bevacizumab after surgery, one row per patient. Time zero is the start of TMZ + bevacizumab.
Clusters come from the lab's transcriptomic clustering.

| Column | Meaning |
|---|---|
| `patient_id` | Study ID (`SYN-GBM-###`) |
| `age`, `sex`, `kps` | Age in years, sex, Karnofsky performance status |
| `resection` | `gross_total`, `subtotal` or `biopsy` |
| `idh_status` | IDH1/2 status (all wildtype) |
| `cluster`, `cluster_label` | 1 = Mesenchymal-Immune-Active, 2 = Proneural |
| `mgmt_methylated` | MGMT promoter methylated (1/0) |
| `egfr_amplified`, `pdgfra_amplified` | Gene amplification (1/0) |
| `nf1_loss`, `cdkn2a_deleted`, `tert_promoter_mut` | NF1 loss, CDKN2A/B homozygous deletion, TERT promoter mutation (1/0) |
| `ykl40_tpm` | CHI3L1 (YKL-40) expression, TPM |
| `cd163_cells_per_mm2` | CD163+ macrophage density by IHC, cells/mm² |
| `best_response_rano` | Best response by RANO: CR, PR, SD, PD |
| `pfs_months`, `pfs_event` | Progression-free survival; event 1 = progression or death, 0 = censored |
| `os_months`, `os_event` | Overall survival; event 1 = death, 0 = censored |
