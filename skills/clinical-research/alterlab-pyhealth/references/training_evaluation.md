# PyHealth Training, Evaluation, and Interpretability

## Overview

PyHealth provides comprehensive tools for training models, evaluating predictions, ensuring model reliability, and interpreting results for clinical applications.

## Trainer Class

### Core Functionality

The `Trainer` class manages the complete model training and evaluation workflow with PyTorch integration.

**Initialization:**
```python
from pyhealth.trainer import Trainer

trainer = Trainer(
    model=model,                          # PyHealth model
    metrics=["pr_auc", "roc_auc", "f1"],  # metrics computed by evaluate()
    # device is auto-detected; pass device="cpu"/"cuda" to override
)
```

The metric list you pass here is what `evaluate()` reports and what `monitor=` can reference during training.

### Training

**train() method**

Trains models with comprehensive monitoring and checkpointing.

**Parameters:**
- `train_dataloader`: Training data loader
- `val_dataloader`: Validation data loader (optional)
- `epochs`: Number of training epochs
- `optimizer_class`: Optimizer **class** (e.g. `torch.optim.Adam`, `torch.optim.AdamW`)
- `optimizer_params`: Dict of optimizer kwargs (e.g. `{"lr": 1e-3, "weight_decay": 1e-5}`)
- `monitor`: Metric to monitor — one of the names passed to `Trainer(metrics=...)`, e.g. `"pr_auc"`
- `monitor_criterion`: "max" or "min"

**Usage:**
```python
import torch

trainer.train(
    train_dataloader=train_loader,
    val_dataloader=val_loader,
    epochs=50,
    optimizer_class=torch.optim.Adam,
    optimizer_params={"lr": 1e-3, "weight_decay": 1e-5},
    monitor="pr_auc",
    monitor_criterion="max",
)
```

**Training Features:**

1. **Automatic Checkpointing**: Saves the best model by the monitored metric (`best.ckpt`, when logging is enabled)

2. **Early Stopping**: `patience=<epochs>` stops training when the monitored metric stops improving

3. **Gradient Clipping**: `max_grad_norm=<float>` clips gradients

4. **Progress Tracking**: Logs training progress and validation metrics

5. **Device Placement**: Single device — CUDA if available, else CPU (override with `Trainer(device=...)`); multi-GPU training is not built in

### Inference

**inference() method**

Performs predictions on datasets.

**Parameters:**
- `dataloader`: Data loader for inference
- `additional_outputs`: List of additional outputs to return
- `return_patient_ids`: Return patient identifiers

**Usage:**
```python
# Default: returns a 3-tuple
y_true, y_prob, loss = trainer.inference(test_loader)

# With patient IDs: returns a 4-tuple
y_true, y_prob, loss, patient_ids = trainer.inference(test_loader, return_patient_ids=True)

# additional_outputs=[...] inserts a dict before patient_ids; request only keys the
# model's forward() actually returns (e.g. "logit"; calibrated set models add "y_predset")
y_true, y_prob, loss, extra, patient_ids = trainer.inference(
    test_loader, additional_outputs=["logit"], return_patient_ids=True,
)
```

**Returns (tuple, not a dict):**
- `y_true`: Ground truth labels (array)
- `y_prob`: Predicted probabilities (array)
- `loss` / `mean_loss`: Mean loss over the dataset
- `additional_outputs`: Dict of requested extras (only if `additional_outputs=` given)
- `patient_ids`: Patient identifiers (only if `return_patient_ids=True`)

### Evaluation

**evaluate() method**

Computes comprehensive evaluation metrics.

**Parameters:**
- `dataloader`: Data loader for evaluation

`evaluate()` uses the metric list set on the `Trainer` (`Trainer(metrics=[...])`) — it does **not** take a `metrics=` argument. To compute metrics ad hoc, call the metric function directly on `inference()` outputs.

**Usage:**
```python
# Uses metrics passed to Trainer(...)
results = trainer.evaluate(test_loader)
print(results)
# e.g. {'pr_auc': 0.78, 'roc_auc': 0.82, 'f1': 0.73}

# Or compute metrics manually from predictions
from pyhealth.metrics.binary import binary_metrics_fn

y_true, y_prob, loss = trainer.inference(test_loader)
binary_metrics_fn(y_true, y_prob, metrics=["pr_auc", "roc_auc", "f1"])
```

### Checkpoint Management

The `Trainer` saves and restores the model's `state_dict` (there is no `trainer.save()` / `trainer.load()`):

```python
trainer.save_ckpt("./models/best_model.pt")
trainer.load_ckpt("./models/best_model.pt")

# Or load while constructing a trainer for an identically configured model
trainer = Trainer(model=model, checkpoint_path="./models/best_model.pt")
```

With logging enabled (the default), `train()` writes `last.ckpt` and `best.ckpt` (by `monitor`) under `output_path/exp_name` and reloads `best.ckpt` at the end (`load_best_model_at_last=True`). With `enable_logging=False` nothing is written, so call `save_ckpt()` yourself.

## Evaluation Metrics

### Binary Classification Metrics

**Available metric strings:**
- `accuracy`: Overall accuracy
- `f1`: F1 score
- `precision`, `recall`, `balanced_accuracy`, `jaccard`
- `roc_auc`: Area under ROC curve
- `pr_auc`: Area under precision-recall curve
- `cohen_kappa`: Inter-rater reliability

(Strings have no `_score` suffix.)

**Usage:**
```python
from pyhealth.metrics.binary import binary_metrics_fn

# Note: arg is y_prob (predicted probabilities), not thresholded y_pred
metrics = binary_metrics_fn(
    y_true=labels,
    y_prob=probabilities,
    metrics=["accuracy", "f1", "pr_auc", "roc_auc"],
)
```

**Threshold Selection:**
```python
# Default threshold: 0.5
predictions_binary = (predictions > 0.5).astype(int)

# Optimal threshold by F1
from sklearn.metrics import f1_score
thresholds = np.arange(0.1, 0.9, 0.05)
f1_scores = [f1_score(y_true, (y_pred > t).astype(int)) for t in thresholds]
optimal_threshold = thresholds[np.argmax(f1_scores)]
```

**Best Practices:**
- **Use AUROC**: Overall model discrimination
- **Use AUPRC**: Especially for imbalanced classes
- **Use F1**: Balance precision and recall
- **Report confidence intervals**: Bootstrap resampling

### Multi-Class Classification Metrics

**Available metric strings:**
- `accuracy`: Overall accuracy
- `f1_macro`: Unweighted mean F1 across classes
- `f1_micro`: Global F1 (total TP, FP, FN)
- `f1_weighted`: Weighted mean F1 by class frequency
- `cohen_kappa`: Multi-class kappa

**Usage:**
```python
from pyhealth.metrics.multiclass import multiclass_metrics_fn

metrics = multiclass_metrics_fn(
    y_true=labels,
    y_prob=probabilities,
    metrics=["accuracy", "f1_macro", "f1_weighted"],
)
```

**Per-Class Metrics:**
```python
from sklearn.metrics import classification_report

print(classification_report(y_true, y_pred,
    target_names=["Wake", "N1", "N2", "N3", "REM"]))
```

**Confusion Matrix:**
```python
from sklearn.metrics import confusion_matrix
import seaborn as sns

cm = confusion_matrix(y_true, y_pred)
sns.heatmap(cm, annot=True, fmt='d')
```

### Multi-Label Classification Metrics

**Available metric strings** (the `*_samples` family is the per-example average used for drug recommendation):
- `jaccard_samples`: Sample-averaged Jaccard (intersection over union)
- `f1_samples`: Sample-averaged F1
- `pr_auc_samples`: Sample-averaged AUPRC
- `hamming_loss`: Fraction of incorrect labels
- `ddi`: Drug-drug interaction rate (drug-rec models; returned under the key `ddi_score`)

**Usage:**
```python
from pyhealth.metrics.multilabel import multilabel_metrics_fn

# y_prob: [n_samples, n_labels] probability matrix
metrics = multilabel_metrics_fn(
    y_true=label_matrix,
    y_prob=prob_matrix,
    metrics=["jaccard_samples", "f1_samples", "pr_auc_samples"],
)
```

**Drug Recommendation Metrics:**
```python
# Jaccard similarity (intersection/union)
jaccard = len(set(true_drugs) & set(pred_drugs)) / len(set(true_drugs) | set(pred_drugs))

# Precision@k: Precision for top-k predictions
def precision_at_k(y_true, y_pred, k=10):
    top_k_pred = y_pred.argsort()[-k:]
    return len(set(y_true) & set(top_k_pred)) / k
```

### Regression Metrics

**Available metric strings (2.0.2):**
- `mae`: Mean absolute error
- `mse`: Mean squared error
- `kl_divergence`: KL divergence between the normalized target and prediction vectors

Any other name (e.g. `rmse`, `r2`) raises `ValueError`; compute those with scikit-learn.

**Usage:**
```python
from pyhealth.metrics.regression import regression_metrics_fn

# Signature: regression_metrics_fn(x, x_rec, metrics=None) — positional true, predicted
metrics = regression_metrics_fn(true_values, predictions, metrics=["mae", "mse"])

from sklearn.metrics import r2_score, root_mean_squared_error
extra = {"rmse": root_mean_squared_error(true_values, predictions), "r2": r2_score(true_values, predictions)}
```

**Percentage Error Metrics:**
```python
# Mean Absolute Percentage Error
mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

# Median Absolute Percentage Error (robust to outliers)
medape = np.median(np.abs((y_true - y_pred) / y_true)) * 100
```

### Fairness Metrics

**Purpose:** Assess model bias across a protected vs. unprotected group.

**`pyhealth.metrics.fairness.fairness_metrics_fn`** — available metric strings:
- `disparate_impact`: Ratio of favorable-outcome rates (protected / unprotected)
- `statistical_parity_difference`: Difference in favorable-outcome rates

**Signature:** `fairness_metrics_fn(y_true, y_prob, sensitive_attributes, favorable_outcome=1, metrics=[...], threshold=0.5)` where `sensitive_attributes` is a 0/1 array (1 = protected group).

**Usage:**
```python
from pyhealth.metrics.fairness import fairness_metrics_fn

# sensitive_attributes: 1 for the protected group, 0 otherwise
fairness_results = fairness_metrics_fn(
    y_true=labels,
    y_prob=probabilities,
    sensitive_attributes=protected_mask,
    favorable_outcome=1,
    metrics=["disparate_impact", "statistical_parity_difference"],
)
```

**Example:**
```python
# Evaluate fairness across gender
male_mask = (demographics == "male")
female_mask = (demographics == "female")

male_tpr = recall_score(y_true[male_mask], y_pred[male_mask])
female_tpr = recall_score(y_true[female_mask], y_pred[female_mask])

tpr_disparity = abs(male_tpr - female_tpr)
print(f"TPR disparity: {tpr_disparity:.3f}")
```

## Calibration and Uncertainty Quantification

### Model Calibration

**Purpose:** Ensure predicted probabilities match actual frequencies

**Calibration Plot:**
```python
from sklearn.calibration import calibration_curve
import matplotlib.pyplot as plt

fraction_of_positives, mean_predicted_value = calibration_curve(
    y_true, y_prob, n_bins=10
)

plt.plot(mean_predicted_value, fraction_of_positives, marker='o')
plt.plot([0, 1], [0, 1], linestyle='--', label='Perfect calibration')
plt.xlabel('Mean predicted probability')
plt.ylabel('Fraction of positives')
plt.legend()
```

**Expected Calibration Error (ECE):**
```python
def expected_calibration_error(y_true, y_prob, n_bins=10):
    """Compute ECE"""
    bins = np.linspace(0, 1, n_bins + 1)
    bin_indices = np.digitize(y_prob, bins) - 1

    ece = 0
    for i in range(n_bins):
        mask = bin_indices == i
        if mask.sum() > 0:
            bin_accuracy = y_true[mask].mean()
            bin_confidence = y_prob[mask].mean()
            ece += mask.sum() / len(y_true) * abs(bin_accuracy - bin_confidence)

    return ece
```

**Calibration Methods:**

1. **Platt Scaling**: Logistic regression on validation predictions
```python
from sklearn.linear_model import LogisticRegression

calibrator = LogisticRegression()
calibrator.fit(val_predictions.reshape(-1, 1), val_labels)
calibrated_probs = calibrator.predict_proba(test_predictions.reshape(-1, 1))[:, 1]
```

2. **Isotonic Regression**: Non-parametric calibration
```python
from sklearn.isotonic import IsotonicRegression

calibrator = IsotonicRegression(out_of_bounds='clip')
calibrator.fit(val_predictions, val_labels)
calibrated_probs = calibrator.predict(test_predictions)
```

3. **Temperature Scaling and other built-in calibrators**: PyHealth wraps a trained model with a calibrator from `pyhealth.calib.calibration` (`TemperatureScaling`, `HistogramBinning`, `DirichletCalibration`, `KCal`) and fits it on a held-out calibration split. Check each class docstring for the task modes it supports.
```python
from pyhealth.calib.calibration import TemperatureScaling

cal_model = TemperatureScaling(model)       # model = trained PyHealth model
cal_model.calibrate(cal_dataset=val_data)   # a split not used for checkpoint selection, ideally
print(Trainer(model=cal_model, metrics=["accuracy"]).evaluate(test_loader))
```

### Uncertainty Quantification

**Conformal Prediction:**

Provide prediction sets with guaranteed coverage.

**Usage (split conformal, multiclass, plain NumPy):**
```python
import numpy as np

alpha = 0.1                                   # target 90% coverage
n = len(cal_labels)                           # held-out calibration split
scores = 1 - cal_probs[np.arange(n), cal_labels]
q_level = np.ceil((n + 1) * (1 - alpha)) / n  # finite-sample correction
qhat = np.quantile(scores, q_level, method="higher")

prediction_sets = test_probs >= (1 - qhat)    # boolean [n_test, n_classes]
coverage = prediction_sets[np.arange(len(test_labels)), test_labels].mean()
avg_size = prediction_sets.sum(axis=1).mean()
```

PyHealth also ships prediction-set constructors in `pyhealth.calib.predictionset` (`LABEL`, `SCRIB`, `FavMac`, `CovariateLabel`, `ClusterLabel`, `NeighborhoodLabel`). They wrap a trained model, are fit with `.calibrate(cal_dataset=...)`, and expose the sets via `Trainer(model=cal_model).inference(loader, additional_outputs=["y_predset"])`; the multiclass metric function accepts them through `y_predset=` with metrics such as `miscoverage_ps`, `set_size`, and `rejection_rate`.

**Monte Carlo Dropout:**

Estimate uncertainty through dropout at inference.

```python
def predict_with_uncertainty(model, dataloader, num_samples=20):
    """Predict with uncertainty using MC dropout"""
    model.train()  # Keep dropout active

    predictions = []
    for _ in range(num_samples):
        batch_preds = []
        for batch in dataloader:
            with torch.no_grad():
                output = model(**batch)["y_prob"]
                batch_preds.append(output)
        predictions.append(torch.cat(batch_preds))

    predictions = torch.stack(predictions)
    mean_pred = predictions.mean(dim=0)
    std_pred = predictions.std(dim=0)  # Uncertainty

    return mean_pred, std_pred
```

**Ensemble Uncertainty:**

```python
# Train multiple models
models = [train_model(seed=i) for i in range(5)]

# Predict with ensemble
ensemble_preds = []
for model in models:
    pred = model.predict(test_data)
    ensemble_preds.append(pred)

mean_pred = np.mean(ensemble_preds, axis=0)
std_pred = np.std(ensemble_preds, axis=0)  # Uncertainty
```

## Interpretability

### Attention and Attribution Methods

PyHealth models do not return raw attention matrices from `forward()` / `Trainer.inference()` (the output dict is `loss`, `y_prob`, `y_true`, `logit`). Use the interpreters in `pyhealth.interpret.methods` instead; each takes a trained model and returns a dict of per-token scores keyed by input feature (`attribute(**batch)`):

| Method | Works with (2.0.2) |
|--------|--------------------|
| `CheferRelevance`, `AttentionRollout` | Attention models: `Transformer`, `StageAttentionNet` |
| `IntegratedGradients`, `DeepLift` (`use_embeddings=True`) | Models with `forward_from_embedding`: `Transformer`, `MLP`, `StageNet`, `StageAttentionNet`, `TorchvisionModel` |
| `ShapExplainer`, `LimeExplainer` | Perturbation-based; see the class docstrings for input requirements |

```python
from pyhealth.interpret.methods import IntegratedGradients

ig = IntegratedGradients(model, use_embeddings=True, steps=50)
batch = next(iter(get_dataloader(test_data, batch_size=1, shuffle=False)))
attributions = ig.attribute(**batch)          # {"conditions": tensor, ...}
```

**RETAIN** is interpretable by design (visit-level alpha and variable-level beta attention), but PyHealth 2.0.2 does not expose those weights through `forward()`, and RETAIN implements neither the Chefer interface nor `forward_from_embedding`. For attributions you can hand to clinicians, train a `Transformer` alongside it.

### Feature Importance

**Permutation Importance:**

```python
from sklearn.inspection import permutation_importance

def get_predictions(model, X):
    return model.predict(X)

result = permutation_importance(
    model, X_test, y_test,
    n_repeats=10,
    scoring='roc_auc'
)

# Sort features by importance
indices = result.importances_mean.argsort()[::-1]
for i in indices[:10]:
    print(f"{feature_names[i]}: {result.importances_mean[i]:.3f}")
```

**SHAP Values:**

```python
import shap

# Create explainer
explainer = shap.DeepExplainer(model, train_data)

# Compute SHAP values
shap_values = explainer.shap_values(test_data)

# Visualize
shap.summary_plot(shap_values, test_data, feature_names=feature_names)
```

### Chefer Relevance (PyHealth's built-in attention interpretability)

PyHealth ships the Chefer relevance method for attention-based models (`Transformer`, `StageAttentionNet`; other models raise `ValueError`). The class is `CheferRelevance` in `pyhealth.interpret.methods`; call `attribute(**batch)` (the older `get_relevance_matrix(**batch)` is a deprecated alias).

```python
from pyhealth.interpret.methods import CheferRelevance
from pyhealth.datasets import get_dataloader

relevance = CheferRelevance(model)

# One sample at a time (batch_size=1)
loader = get_dataloader(test_dataset, batch_size=1, shuffle=False)
batch = next(iter(loader))

scores = relevance.attribute(**batch)  # dict: feature_key -> [batch, num_tokens] tensor
for feature_key, rel in scores.items():
    top_tokens = rel[0].topk(5).indices
    print(f"{feature_key}: top-5 tokens -> {top_tokens.tolist()}")
```

## Complete Training Pipeline Example

```python
import torch
from pyhealth.datasets import MIMIC4EHRDataset, split_by_patient, get_dataloader
from pyhealth.tasks import MortalityPredictionMIMIC4
from pyhealth.models import Transformer
from pyhealth.trainer import Trainer

# 1. Load and prepare data
dataset = MIMIC4EHRDataset(
    root="/path/to/mimic4",
    tables=["diagnoses_icd", "procedures_icd", "prescriptions"],
)
sample_dataset = dataset.set_task(MortalityPredictionMIMIC4())

# 2. Split data by patient
train_data, val_data, test_data = split_by_patient(
    sample_dataset, [0.7, 0.1, 0.2]
)

# 3. Create data loaders
train_loader = get_dataloader(train_data, batch_size=64, shuffle=True)
val_loader = get_dataloader(val_data, batch_size=64, shuffle=False)
test_loader = get_dataloader(test_data, batch_size=64, shuffle=False)

# 4. Initialize model
model = Transformer(
    dataset=sample_dataset,
    embedding_dim=128,
    num_layers=2,
    dropout=0.3,
)

# 5. Train model
trainer = Trainer(model=model, metrics=["accuracy", "pr_auc", "roc_auc", "f1"])
trainer.train(
    train_dataloader=train_loader,
    val_dataloader=val_loader,
    epochs=50,
    optimizer_class=torch.optim.Adam,
    optimizer_params={"lr": 1e-3, "weight_decay": 1e-5},
    monitor="pr_auc",
    monitor_criterion="max",
)

# 6. Evaluate on test set (uses the Trainer's metric list)
test_results = trainer.evaluate(test_loader)
print("Test Results:")
for metric, value in test_results.items():
    print(f"{metric}: {value:.4f}")

# 7. Get predictions for analysis (tuple unpacking)
y_true, y_prob, loss = trainer.inference(test_loader)

# 8. Calibration analysis
from sklearn.calibration import calibration_curve

positive_prob = y_prob if y_prob.ndim == 1 else y_prob[..., -1]
fraction_pos, mean_pred = calibration_curve(y_true, positive_prob, n_bins=10)
ece = expected_calibration_error(y_true, positive_prob)
print(f"Expected Calibration Error: {ece:.4f}")

# 9. Save final model
trainer.save_ckpt("./models/mortality_transformer_final.pt")
```

## Best Practices

### Training

1. **Monitor multiple metrics**: Track both loss and task-specific metrics
2. **Use validation set**: Prevent overfitting with early stopping
3. **Gradient clipping**: Stabilize training (max_grad_norm=5.0)
4. **Learning rate scheduling**: Reduce LR on plateau
5. **Checkpoint best model**: Save based on validation performance

### Evaluation

1. **Use task-appropriate metrics**: AUROC/AUPRC for binary, macro-F1 for imbalanced multi-class
2. **Report confidence intervals**: Bootstrap or cross-validation
3. **Stratified evaluation**: Report metrics by subgroups
4. **Clinical metrics**: Include clinically relevant thresholds
5. **Fairness assessment**: Evaluate across demographic groups

### Deployment

1. **Calibrate predictions**: Ensure probabilities are reliable
2. **Quantify uncertainty**: Provide confidence estimates
3. **Monitor performance**: Track metrics in production
4. **Handle distribution shift**: Detect when data changes
5. **Interpretability**: Provide explanations for predictions
