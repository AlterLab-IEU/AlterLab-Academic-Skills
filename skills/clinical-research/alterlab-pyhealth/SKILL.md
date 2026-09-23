---
name: alterlab-pyhealth
description: Develops, tests, and validates clinical machine learning models with the PyHealth 2.x healthcare AI toolkit. Use when working with electronic health records (EHR), clinical prediction tasks (mortality, readmission, length of stay, drug recommendation), medical coding systems (ICD, NDC, ATC, CCS), physiological signals (EEG, ECG), healthcare datasets (MIMIC-III/IV, eICU, OMOP), or implementing deep learning models for healthcare (RETAIN, SafeDrug, GAMENet, Transformer, GAT/GCN). Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*)
compatibility: "Self-contained — runs under `uv run python` with PyHealth >= 2.0.2 (Python 3.12-3.13) in its own environment; no API key required. MIMIC-III/IV and eICU data need the user's own PhysioNet credentialed access."
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    last_updated: "2026-09-23"
---

# PyHealth: Healthcare AI Toolkit

## Overview

PyHealth is a Python library for healthcare AI that provides datasets, task definitions, models, trainers, and medical-code utilities for clinical machine learning. Use this skill when developing healthcare prediction models, processing clinical data, working with medical coding systems, or validating models before any clinical use.

> **Version gotcha (read first).** This skill targets **PyHealth 2.x** (current release 2.0.2, Sept 2026). The 2.0 rewrite changed the API in ways most tutorials and pre-2025 snippets get wrong:
> - **Tasks are classes you instantiate**, e.g. `MortalityPredictionMIMIC4()`, `DrugRecommendationMIMIC3()` — not the old snake-case `mortality_prediction_mimic4_fn` functions. Pass the instance to `dataset.set_task(task)`.
> - **Datasets take an explicit table list.** Single-source loaders use `root=` + `tables=[...]` (`MIMIC3Dataset`, `MIMIC4EHRDataset`, `eICUDataset`, `OMOPDataset`); the multimodal `MIMIC4Dataset` uses `ehr_root=` + `ehr_tables=[...]` (plus optional `note_root`/`cxr_root`).
> - **Models take only the `SampleDataset` plus hyperparameters**, e.g. `Transformer(dataset=samples, embedding_dim=128)`. Feature keys, label key, and mode are read from the task's `input_schema` / `output_schema`; the 1.x `feature_keys=` / `label_key=` / `mode=` arguments raise `TypeError`.
> - **Metric names have no `_score` suffix**: `pr_auc`, `roc_auc`, `f1`; multilabel/drug-rec use the `*_samples` family (`jaccard_samples`, `f1_samples`, `pr_auc_samples`). Pass `metrics=[...]` to the **`Trainer` constructor** and `monitor=` one of those names.
> - Checkpoints use `trainer.save_ckpt(path)` / `trainer.load_ckpt(path)` (there is no `trainer.save`).
> - 2.0.2 requires **Python 3.12 or 3.13** and pins its own stack (numpy 2.2, pandas 2.3, torch 2.7, transformers 4.53), so install it in a dedicated environment rather than next to pandas 3 / transformers 5.
>
> When unsure of a class or argument name, check the installed source rather than trusting older snippets.

## When to Use This Skill

Invoke this skill when:

- **Working with healthcare datasets**: MIMIC-III, MIMIC-IV, eICU, OMOP, sleep EEG data, medical images
- **Clinical prediction tasks**: Mortality prediction, hospital readmission, length of stay, drug recommendation
- **Medical coding**: Translating between ICD-9/10, NDC, RxNorm, ATC, CCS coding systems
- **Processing clinical data**: Sequential events, physiological signals, clinical text, medical images
- **Implementing healthcare models**: RETAIN, SafeDrug, GAMENet, StageNet, Transformer for EHR
- **Evaluating clinical models**: Fairness metrics, calibration, interpretability, uncertainty quantification

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Cleaning a raw ECG/EEG/EDA trace and computing HRV or SCR features (no model training) | `alterlab-neurokit2` |
| Reading, anonymizing, or converting DICOM image files | `alterlab-pydicom` |
| Kaplan-Meier / Cox time-to-event modeling on a tabular clinical dataset | `alterlab-scikit-survival` |
| Biomarker-stratified cohort report with GRADE-graded treatment recommendations | `alterlab-clinical-decision` |
| General tabular ML on non-EHR data (scikit-learn pipelines) | `alterlab-scikit-learn` |

## Core Capabilities

PyHealth operates through a modular 5-stage pipeline:

1. **Data Loading**: Standardized loaders for EHR, signal, imaging, and text datasets
2. **Task Definition**: Predefined clinical prediction tasks (task classes) or custom `BaseTask` subclasses
3. **Model Selection**: Baselines, general deep learning, and healthcare-specific models
4. **Training**: `Trainer` with best-checkpoint selection, monitoring, and evaluation
5. **Validation**: Calibration, conformal prediction, fairness metrics, and interpretability methods

PyHealth 2.x uses a **polars-backed** data layer and caches task samples, which keeps large EHR tables memory-efficient.

## Quick Start Workflow

```python
from pyhealth.datasets import MIMIC4EHRDataset, split_by_patient, get_dataloader
from pyhealth.tasks import MortalityPredictionMIMIC4
from pyhealth.models import Transformer
from pyhealth.trainer import Trainer

# 1. Load dataset (declare the tables the task needs) and set the task (a class instance)
dataset = MIMIC4EHRDataset(
    root="/path/to/mimic-iv/2.2",
    tables=["diagnoses_icd", "procedures_icd", "prescriptions"],
)
sample_dataset = dataset.set_task(MortalityPredictionMIMIC4())

# 2. Split data by patient (no leakage across splits)
train, val, test = split_by_patient(sample_dataset, [0.7, 0.1, 0.2], seed=42)

# 3. Create data loaders
train_loader = get_dataloader(train, batch_size=64, shuffle=True)
val_loader = get_dataloader(val, batch_size=64, shuffle=False)
test_loader = get_dataloader(test, batch_size=64, shuffle=False)

# 4. Initialize the model: inputs, label ("mortality"), and mode ("binary")
#    all come from the task schema, so only hyperparameters are passed
model = Transformer(dataset=sample_dataset, embedding_dim=128)

trainer = Trainer(model=model, metrics=["pr_auc", "roc_auc", "f1"])  # device auto-detected
trainer.train(
    train_dataloader=train_loader,
    val_dataloader=val_loader,
    epochs=50,
    monitor="pr_auc",            # AUPRC — robust for the rare-mortality class
    monitor_criterion="max",
)

# 5. Evaluate (uses the metrics passed to the Trainer)
results = trainer.evaluate(test_loader)
```

## Detailed Documentation

Read the reference file that matches the step you are on:

| File | Read when | Key topics |
|------|-----------|------------|
| `references/datasets.md` | Loading MIMIC/eICU/OMOP/signal datasets, splitting data | Patient/Event structures, loaders, `split_by_patient` / `split_by_visit` / `split_by_sample` |
| `references/medical_coding.md` | Translating or grouping ICD, NDC, RxNorm, ATC, CCS codes | `InnerMap` lookups and hierarchy, `CrossMap` translation |
| `references/tasks.md` | Choosing a predefined task or writing a custom one | 2.x task classes, `input_schema` / `output_schema`, custom `BaseTask` |
| `references/models.md` | Selecting and configuring a model | Baselines, RNN/CNN/Transformer, RETAIN, SafeDrug, GAMENet, StageNet, GAT/GCN |
| `references/preprocessing.md` | Understanding how raw events become tensors | Schema-string processors (`"sequence"`, `"timeseries"`, `"binary"`, ...) |
| `references/training_evaluation.md` | Training, metrics, calibration, uncertainty, interpretability | `Trainer`, metric strings, conformal prediction, Chefer/IG attributions |

## Installation

```bash
uv venv --python 3.13 .venv-pyhealth      # PyHealth 2.0.2 supports Python 3.12-3.13
source .venv-pyhealth/bin/activate
uv pip install "pyhealth>=2.0.2"
```

**Requirements (PyHealth 2.0.2):**
- Python **3.12 or 3.13** (`>=3.12,<3.14`) — if your default interpreter is 3.14, create the environment with `--python 3.13`.
- PyTorch, polars, pandas, scikit-learn, and transformers are installed as pinned dependencies — keep PyHealth in its own environment so these pins don't collide with other projects.
- A `2.1` alpha line exists on PyPI; stay on the 2.0.x releases unless you need an alpha-only feature.

## Common Use Cases

### Use Case 1: ICU Mortality Prediction

**Objective**: Predict patient mortality in intensive care unit

**Approach:**
1. Load MIMIC-IV dataset → Read `references/datasets.md`
2. Apply mortality prediction task → Read `references/tasks.md`
3. Select an interpretable model (RETAIN) or an attribution-friendly one (Transformer) → Read `references/models.md`
4. Train and evaluate → Read `references/training_evaluation.md`
5. Interpret predictions for clinical review → Read `references/training_evaluation.md`

### Use Case 2: Safe Medication Recommendation

**Objective**: Recommend medications while avoiding drug-drug interactions

**Approach:**
1. Load EHR dataset (MIMIC-III/IV, eICU, or OMOP) → Read `references/datasets.md`
2. Apply a `DrugRecommendation*` task → Read `references/tasks.md`
3. Use SafeDrug or GAMENet, which build their DDI graphs from the dataset → Read `references/models.md`
4. Preprocess medication codes → Read `references/medical_coding.md`
5. Evaluate with multi-label metrics (`jaccard_samples`, `f1_samples`, `pr_auc_samples`) → Read `references/training_evaluation.md`

### Use Case 3: Hospital Readmission Prediction

**Objective**: Identify patients at risk of readmission

**Approach:**
1. Load multi-site EHR data (eICU or OMOP) → Read `references/datasets.md`
2. Apply a `ReadmissionPrediction*` task → Read `references/tasks.md`
3. Handle class imbalance (report AUPRC, not only AUROC) → Read `references/training_evaluation.md`
4. Train a Transformer or RNN model → Read `references/models.md`
5. Calibrate predictions and assess fairness → Read `references/training_evaluation.md`

### Use Case 4: Sleep Staging

**Objective**: Classify sleep stages from EEG signals

**Approach:**
1. Load a sleep EEG dataset (SleepEDF, SHHS, ISRUC) → Read `references/datasets.md`
2. Apply sleep staging (`SleepStagingSleepEDF` or the legacy `sleep_staging_*_fn` functions) → Read `references/tasks.md`
3. Preprocess EEG signals (filtering, segmentation) → Read `references/preprocessing.md`
4. Train a CNN, SparcNet, or ContraWR model → Read `references/models.md`
5. Evaluate per-stage performance (`f1_macro`, `cohen_kappa`) → Read `references/training_evaluation.md`

### Use Case 5: Medical Code Translation

**Objective**: Standardize diagnoses across different coding systems

**Approach:**
1. Read `references/medical_coding.md` for comprehensive guidance
2. Use `CrossMap` to translate between ICD-9, ICD-10, and CCS
3. Group codes into clinically meaningful categories
4. Integrate with dataset processing

### Use Case 6: Clinical Text to ICD Coding

**Objective**: Automatically assign ICD codes from clinical notes

**Approach:**
1. Load MIMIC-III with clinical notes → Read `references/datasets.md`
2. Apply the `MIMIC3ICD9Coding` task → Read `references/tasks.md`
3. Preprocess clinical text → Read `references/preprocessing.md`
4. Use `TransformersModel(dataset=..., model_name="emilyalsentzer/Bio_ClinicalBERT")` → Read `references/models.md`
5. Evaluate with multi-label metrics → Read `references/training_evaluation.md`

## Best Practices

### Data Handling

1. **Always split by patient**: Prevent data leakage by ensuring no patient appears in multiple splits
   ```python
   from pyhealth.datasets import split_by_patient
   train, val, test = split_by_patient(sample_dataset, [0.7, 0.1, 0.2], seed=42)
   ```

2. **Check dataset statistics**: Understand your data before modeling
   ```python
   dataset.stats()  # prints patient and event counts (returns None)
   ```

3. **Use appropriate preprocessing**: Match processors to data types (see `references/preprocessing.md`)

### Model Development

1. **Start with baselines**: Establish baseline performance with simple models
   - `LogisticRegression` for binary/multi-class tasks
   - `MLP` for an initial deep learning baseline

2. **Choose task-appropriate models**:
   - Interpretability needed → RETAIN, AdaCare (by design); Transformer (post-hoc attributions)
   - Drug recommendation → SafeDrug, GAMENet
   - Long sequences → Transformer
   - Graph relationships → GAT / GCN

3. **Monitor validation metrics**: Use appropriate metrics for the task and handle class imbalance. PyHealth metric strings (pass to `Trainer(metrics=[...])` / `monitor=`):
   - Binary: `roc_auc`, `pr_auc` (prefer `pr_auc` for rare events), `f1`, `accuracy`
   - Multi-class: `f1_macro`, `f1_weighted`, `accuracy`, `cohen_kappa`
   - Multi-label / drug-rec: `jaccard_samples`, `f1_samples`, `pr_auc_samples`, `ddi` (reported as `ddi_score`)
   - Regression: `mae`, `mse`, `kl_divergence`

### Clinical Validation

1. **Calibrate predictions**: Ensure probabilities are reliable (see `references/training_evaluation.md`)
2. **Assess fairness**: Evaluate across demographic groups to detect bias
3. **Quantify uncertainty**: Provide confidence estimates for predictions (conformal prediction sets)
4. **Interpret predictions**: Attention/relevance maps, SHAP, or integrated gradients for clinician review
5. **Validate thoroughly**: Use held-out test sets from different time periods or sites
6. **Report transparently**: Follow TRIPOD+AI (BMJ 2024;385:e078378) when publishing a clinical prediction model

## Limitations and Considerations

### Data Requirements

- **Large datasets**: Deep learning models require sufficient data (thousands of patients)
- **Data quality**: Missing data and coding errors impact performance
- **Temporal consistency**: Ensure train/test split respects temporal ordering when needed
- **Access**: MIMIC and eICU require PhysioNet credentialing and a data use agreement; never copy restricted records into prompts, notebooks, or repositories that the agreement does not cover

### Clinical Validation

- **External validation**: Test on data from different hospitals/systems
- **Prospective evaluation**: Validate in real clinical settings before deployment
- **Clinical review**: Have clinicians review predictions and interpretations
- **Decision support, not diagnosis**: Present model outputs as research-grade risk estimates for qualified clinicians; deployment as a medical device falls under device regulation (e.g. FDA SaMD, EU MDR)
- **Ethical considerations**: Address privacy (HIPAA/GDPR), fairness, and safety

### Computational Resources

- **GPU recommended**: For training deep learning models efficiently
- **Memory requirements**: Large datasets may require 16GB+ RAM
- **Storage**: Healthcare datasets can be 10s-100s of GB, plus the task-sample cache

## Troubleshooting

### Common Issues

**`TypeError: ... unexpected keyword argument 'feature_keys'` (or `'root'`)**:
- You are using a 1.x-style call. Pass only `dataset=` and hyperparameters to models; use `MIMIC4EHRDataset(root=..., tables=...)` or `MIMIC4Dataset(ehr_root=..., ehr_tables=...)`

**ImportError or missing tables**:
- Ensure dataset files are downloaded and the root path points at the versioned folder
- Confirm the table names exist in the dataset's YAML config

**Out of memory**:
- Reduce batch size
- Reduce sequence length (`max_seq_len` on `Transformer`)
- Pass `dev=True` to the dataset loader (e.g. `MIMIC4EHRDataset(..., dev=True)`) to prototype on the first 1,000 patients
- Process data in chunks

**Poor performance**:
- Check class imbalance and use appropriate metrics (`pr_auc` vs `roc_auc`)
- Verify preprocessing (normalization, missing data handling)
- Increase model capacity or training epochs
- Check for data leakage in the train/test split

**Slow training**:
- Use a GPU (`Trainer(..., device="cuda")`)
- Increase batch size (if memory allows)
- Reduce sequence length
- Use a lighter model (CNN or RNN instead of Transformer)

### Getting Help

- **Documentation**: https://pyhealth.readthedocs.io/
- **GitHub Issues**: https://github.com/sunlabuiuc/PyHealth/issues
- **Examples/notebooks**: https://github.com/sunlabuiuc/PyHealth/tree/master/examples

## Example: Complete Workflow

```python
# Complete mortality prediction pipeline (PyHealth 2.0.x)
import torch
from pyhealth.datasets import MIMIC4EHRDataset, split_by_patient, get_dataloader
from pyhealth.tasks import MortalityPredictionMIMIC4
from pyhealth.models import Transformer
from pyhealth.trainer import Trainer
from pyhealth.interpret.methods import CheferRelevance

# 1. Load dataset (declare the tables the task needs)
dataset = MIMIC4EHRDataset(
    root="/data/mimic-iv/2.2",
    tables=["diagnoses_icd", "procedures_icd", "prescriptions"],
)
dataset.stats()

# 2. Define task (instantiate the task class)
sample_dataset = dataset.set_task(MortalityPredictionMIMIC4())
print(f"Generated {len(sample_dataset)} samples")

# 3. Split data (by patient to prevent leakage)
train_ds, val_ds, test_ds = split_by_patient(sample_dataset, [0.7, 0.1, 0.2], seed=42)

# 4. Create data loaders
train_loader = get_dataloader(train_ds, batch_size=64, shuffle=True)
val_loader = get_dataloader(val_ds, batch_size=64)
test_loader = get_dataloader(test_ds, batch_size=64)

# 5. Initialize the model (schema-driven; swap in RETAIN(dataset=sample_dataset,
#    embedding_dim=128) for a model that is interpretable by design)
model = Transformer(dataset=sample_dataset, embedding_dim=128, heads=2, num_layers=2)

# 6. Train, keeping the best checkpoint by validation AUPRC
trainer = Trainer(model=model, metrics=["accuracy", "pr_auc", "roc_auc", "f1"])
trainer.train(
    train_dataloader=train_loader,
    val_dataloader=val_loader,
    epochs=50,
    optimizer_class=torch.optim.Adam,
    optimizer_params={"lr": 1e-3},
    weight_decay=1e-5,
    monitor="pr_auc",          # AUPRC for the imbalanced (rare-mortality) outcome
    monitor_criterion="max",
    patience=5,                # early stopping
)

# 7. Evaluate on the test set (uses the metrics passed to the Trainer)
for metric, value in trainer.evaluate(test_loader).items():
    print(f"  {metric}: {value:.4f}")

# 8. Predictions with patient IDs: inference() returns (y_true, y_prob, loss),
#    extended with patient_ids when return_patient_ids=True
y_true, y_prob, loss, patient_ids = trainer.inference(test_loader, return_patient_ids=True)
positive_prob = y_prob if y_prob.ndim == 1 else y_prob[..., -1]
high_risk_idx = int(positive_prob.argmax())
print(f"Highest-risk patient: {patient_ids[high_risk_idx]} ({float(positive_prob[high_risk_idx]):.3f})")

# 9. Token-level relevance (Chefer; supported by Transformer and StageAttentionNet)
relevance = CheferRelevance(model)
batch = next(iter(get_dataloader(test_ds, batch_size=1, shuffle=False)))
for feature_key, rel in relevance.attribute(**batch).items():
    print(f"{feature_key}: top tokens -> {rel[0].topk(min(5, rel.shape[-1])).indices.tolist()}")

# 10. Save the trained weights
trainer.save_ckpt("./models/mortality_transformer.pt")
```

## Resources

For detailed information on each component, see the reference files in `references/`: `datasets.md`, `medical_coding.md`, `tasks.md`, `models.md`, `preprocessing.md`, and `training_evaluation.md` (see the table under **Detailed Documentation** for when to read each).

Part of the AlterLab Academic Skills suite.
