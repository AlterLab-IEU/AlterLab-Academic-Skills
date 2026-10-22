# NSCLC pembrolizumab cohort export (SYNTHETIC)

**Synthetic data.** Every record in `nsclc_pdl1_cohort.csv` was produced by a seeded simulation for
testing analysis software. None of it describes a real patient, and none of it is evidence about
pembrolizumab.

45 patients with advanced NSCLC on first-line pembrolizumab monotherapy, one row per patient.
Time zero is the first pembrolizumab dose.

| Column | Meaning |
|---|---|
| `patient_id` | Study ID (`SYN-NSCLC-###`) |
| `age`, `sex`, `ecog` | Age in years, sex, ECOG performance status (0/1) |
| `histology`, `smoking_status` | Adenocarcinoma / squamous; current / former / never |
| `pdl1_tps` | PD-L1 tumour proportion score, % (22C3) |
| `pdl1_group` | `<1%`, `1-49%`, `>=50%` |
| `best_overall_response` | RECIST 1.1 best overall response: CR, PR, SD, PD, or NE (no post-baseline assessment) |
| `best_pct_change_target` | Best % change from baseline in the sum of target-lesion diameters (blank when NE) |
| `pfs_months`, `pfs_event` | Progression-free survival; event 1 = progression or death, 0 = censored |
| `os_months`, `os_event` | Overall survival; event 1 = death, 0 = censored |
