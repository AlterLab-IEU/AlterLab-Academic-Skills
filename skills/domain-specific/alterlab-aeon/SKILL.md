---
name: alterlab-aeon
description: Runs time series machine learning with the aeon library — classification, regression, clustering, forecasting, anomaly detection, segmentation, and similarity search via scikit-learn compatible APIs. Use when working with temporal data, sequential patterns, or time-indexed observations (univariate or multivariate) that need specialized algorithms beyond standard ML approaches. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(uv run python:*) Bash(uv pip install:*)
compatibility: No API key required. Runs locally via `uv run python`; requires the aeon Python package.
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# Aeon Time Series Machine Learning

## Overview

Aeon is a scikit-learn compatible Python toolkit for time series machine learning. It provides state-of-the-art algorithms for classification, regression, clustering, forecasting, anomaly detection, segmentation, and similarity search.

## When to Use This Skill

Apply this skill when:
- Classifying or predicting from time series data
- Detecting anomalies or change points in temporal sequences
- Clustering similar time series patterns
- Forecasting future values
- Finding repeated patterns (motifs) or unusual subsequences (discords)
- Comparing time series with specialized distance metrics
- Extracting features from temporal data

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Zero-shot forecasting with a pretrained foundation model, no training | `alterlab-timesfm` |
| ARIMA/SARIMAX with coefficient tables, residual diagnostics, and econometric inference | `alterlab-statsmodels` |
| Plain tabular features (no temporal ordering) for classification/regression | `alterlab-scikit-learn` |
| Physiological signal processing (ECG/EEG/EDA peaks, HRV) | `alterlab-neurokit2` |

## Installation

```bash
uv pip install "aeon>=1.6"     # core; Python 3.11–3.14
uv pip install "aeon[dl]"      # + TensorFlow/Keras for the deep-learning estimators
uv pip install stumpy          # soft dependency of MatrixProfileTransformer
```

Examples are verified against aeon 1.6.0 (current as of 2026-09). The 1.x line
reorganised modules — forecasters live under `aeon.forecasting.stats`, series anomaly
detectors under `aeon.anomaly_detection.series.*`, similarity search under
`aeon.similarity_search.subsequence` / `.whole_series` — so if an import fails, check
the current API reference rather than assuming an older path.

## Core Capabilities

### 1. Time Series Classification

Categorize time series into predefined classes. See `references/classification.md` for complete algorithm catalog.

**Quick Start:**
```python
from aeon.classification.convolution_based import RocketClassifier
from aeon.datasets import load_classification

# Load data
X_train, y_train = load_classification("GunPoint", split="train")
X_test, y_test = load_classification("GunPoint", split="test")

# Train classifier
clf = RocketClassifier(n_kernels=10000)
clf.fit(X_train, y_train)
accuracy = clf.score(X_test, y_test)
```

**Algorithm Selection:**
- **Speed + Performance**: `MiniRocketClassifier`, `Arsenal`
- **Maximum Accuracy**: `HIVECOTEV2`, `InceptionTimeClassifier`
- **Interpretability**: `ShapeletTransformClassifier`, `Catch22Classifier`
- **Small Datasets**: `KNeighborsTimeSeriesClassifier` with DTW distance

### 2. Time Series Regression

Predict continuous values from time series. See `references/regression.md` for algorithms.

**Quick Start:**
```python
from aeon.regression.convolution_based import RocketRegressor
from aeon.datasets import load_regression

X_train, y_train = load_regression("Covid3Month", split="train")
X_test, y_test = load_regression("Covid3Month", split="test")

reg = RocketRegressor()
reg.fit(X_train, y_train)
predictions = reg.predict(X_test)
```

### 3. Time Series Clustering

Group similar time series without labels. See `references/clustering.md` for methods.

**Quick Start:**
```python
from aeon.clustering import TimeSeriesKMeans

clusterer = TimeSeriesKMeans(
    n_clusters=3,
    distance="dtw",
    averaging_method="ba"
)
labels = clusterer.fit_predict(X_train)
centers = clusterer.cluster_centers_
```

### 4. Forecasting

Predict future time series values. See `references/forecasting.md` for forecasters.

**Quick Start:**
```python
from aeon.forecasting.stats import ARIMA

# Orders are separate args (p, d, q) — not an `order` tuple.
forecaster = ARIMA(p=1, d=1, q=1)
forecaster.fit(y_train)

# predict(y) takes the series to forecast from and returns ONE float,
# `horizon` steps past the end of y (default 1). Calling predict() with no
# series raises TypeError in aeon 1.6.
next_step = forecaster.predict(y_train)

# For a multi-step path, use iterative_forecast (returns a 1D ndarray):
y_pred = forecaster.iterative_forecast(y_train, prediction_horizon=5)
```

### 5. Anomaly Detection

Identify unusual patterns or outliers. See `references/anomaly_detection.md` for detectors.

**Quick Start:**
```python
import numpy as np
from aeon.anomaly_detection.series.distance_based import STOMP

detector = STOMP(window_size=50)
anomaly_scores = detector.fit_predict(y)

# Higher scores indicate anomalies
threshold = np.percentile(anomaly_scores, 95)
anomalies = anomaly_scores > threshold
```

### 6. Segmentation

Partition time series into regions with change points. See `references/segmentation.md`.

**Quick Start:**
```python
from aeon.segmentation import ClaSPSegmenter

segmenter = ClaSPSegmenter()
change_points = segmenter.fit_predict(y)
```

### 7. Similarity Search

Find similar patterns within or across time series. See `references/similarity_search.md`.

**Quick Start:**
```python
from aeon.similarity_search.subsequence import MASS

# Searchers are fitted on a collection shaped (n_cases, n_channels, n_timepoints)
X = y.reshape(1, 1, -1)
query = X[0, :, 100:150]                  # (n_channels, length) — length must match

searcher = MASS(length=50, normalize=True).fit(X)
indexes, distances = searcher.predict(query, k=3)   # rows are (case, timestamp)
```

aeon 1.6 no longer ships a `StompMotif` estimator. For motifs/discords compute a
matrix profile with `aeon.transformations.series.MatrixProfileTransformer`
(needs `stumpy`): its minima mark motifs and its maxima discords.

## Feature Extraction and Transformations

Transform time series for feature engineering. See `references/transformations.md`.

**ROCKET Features:**
```python
from aeon.transformations.collection.convolution_based import Rocket

rocket = Rocket()
X_features = rocket.fit_transform(X_train)

# Use features with any sklearn classifier
from sklearn.ensemble import RandomForestClassifier
clf = RandomForestClassifier()
clf.fit(X_features, y_train)
```

**Statistical Features:**
```python
from aeon.transformations.collection.feature_based import Catch22

catch22 = Catch22()
X_features = catch22.fit_transform(X_train)
```

**Preprocessing:**
```python
from aeon.transformations.collection import MinMaxScaler, Normalizer

scaler = Normalizer()  # Z-normalization
X_normalized = scaler.fit_transform(X_train)
```

## Distance Metrics

Specialized temporal distance measures. See `references/distances.md` for complete catalog.

**Usage:**
```python
from aeon.distances import dtw_distance, dtw_pairwise_distance

# Single distance
distance = dtw_distance(x, y, window=0.1)

# Pairwise distances
distance_matrix = dtw_pairwise_distance(X_train)

# Use with classifiers
from aeon.classification.distance_based import KNeighborsTimeSeriesClassifier

clf = KNeighborsTimeSeriesClassifier(
    n_neighbors=5,
    distance="dtw",
    distance_params={"window": 0.2}
)
```

**Available Distances:**
- **Elastic**: DTW, DDTW, WDTW, ERP, EDR, LCSS, TWE, MSM
- **Lock-step**: Euclidean, Manhattan, Minkowski
- **Shape-based**: Shape DTW, SBD

## Deep Learning Networks

Neural architectures for time series. See `references/networks.md`. These estimators
need the `aeon[dl]` extra (TensorFlow ≥ 2.14 / Keras 3, Python < 3.14).

**Architectures:**
- Convolutional: `FCNClassifier`, `ResNetClassifier`, `InceptionTimeClassifier`
- Recurrent: `RecurrentNetwork`, `TCNNetwork`
- Autoencoders: `AEFCNClusterer`, `AEResNetClusterer`

**Usage:**
```python
from aeon.classification.deep_learning import InceptionTimeClassifier

clf = InceptionTimeClassifier(n_epochs=100, batch_size=32)
clf.fit(X_train, y_train)
predictions = clf.predict(X_test)
```

## Datasets and Benchmarking

Load standard benchmarks and evaluate performance. See `references/datasets_benchmarking.md`.

**Load Datasets:**
```python
from aeon.datasets import load_classification, load_regression

# Classification
X_train, y_train = load_classification("ArrowHead", split="train")

# Regression
X_train, y_train = load_regression("Covid3Month", split="train")
```

**Benchmarking:**
```python
from aeon.benchmarking.results_loaders import get_estimator_results

# Compare with published results (estimators + datasets are lists)
published = get_estimator_results(estimators=["ROCKET"], datasets=["GunPoint"])
```

## Common Workflows

### Classification Pipeline

```python
from aeon.transformations.collection import Normalizer
from aeon.classification.convolution_based import RocketClassifier
from sklearn.pipeline import Pipeline

pipeline = Pipeline([
    ('normalize', Normalizer()),
    ('classify', RocketClassifier())
])

pipeline.fit(X_train, y_train)
accuracy = pipeline.score(X_test, y_test)
```

### Feature Extraction + Traditional ML

```python
from aeon.transformations.collection.convolution_based import Rocket
from sklearn.ensemble import GradientBoostingClassifier

# Extract features
rocket = Rocket()
X_train_features = rocket.fit_transform(X_train)
X_test_features = rocket.transform(X_test)

# Train traditional ML
clf = GradientBoostingClassifier()
clf.fit(X_train_features, y_train)
predictions = clf.predict(X_test_features)
```

### Anomaly Detection with Visualization

```python
import numpy as np
import matplotlib.pyplot as plt
from aeon.anomaly_detection.series.distance_based import STOMP

detector = STOMP(window_size=50)
scores = detector.fit_predict(y)

plt.figure(figsize=(15, 5))
plt.subplot(2, 1, 1)
plt.plot(y, label='Time Series')
plt.subplot(2, 1, 2)
plt.plot(scores, label='Anomaly Scores', color='red')
plt.axhline(np.percentile(scores, 95), color='k', linestyle='--')
plt.show()
```

## Best Practices

### Data Preparation

1. **Normalize**: Most algorithms benefit from z-normalization
   ```python
   from aeon.transformations.collection import Normalizer
   normalizer = Normalizer()
   X_train = normalizer.fit_transform(X_train)
   X_test = normalizer.transform(X_test)
   ```

2. **Handle Missing Values**: Impute before analysis
   ```python
   from aeon.transformations.collection import SimpleImputer
   imputer = SimpleImputer(strategy='mean')
   X_train = imputer.fit_transform(X_train)
   ```

3. **Check Data Format**: Aeon expects shape `(n_samples, n_channels, n_timepoints)`

### Model Selection

1. **Start Simple**: Begin with ROCKET variants before deep learning
2. **Use Validation**: Split training data for hyperparameter tuning
3. **Compare Baselines**: Test against simple methods (1-NN Euclidean, Naive)
4. **Consider Resources**: ROCKET for speed, deep learning if GPU available

### Algorithm Selection Guide

**For Fast Prototyping:**
- Classification: `MiniRocketClassifier`
- Regression: `MiniRocketRegressor`
- Clustering: `TimeSeriesKMeans` with Euclidean

**For Maximum Accuracy:**
- Classification: `HIVECOTEV2`, `InceptionTimeClassifier`
- Regression: `InceptionTimeRegressor`
- Forecasting: `ARIMA`, `TCNForecaster`

**For Interpretability:**
- Classification: `ShapeletTransformClassifier`, `Catch22Classifier`
- Features: `Catch22`, `TSFresh`

**For Small Datasets:**
- Distance-based: `KNeighborsTimeSeriesClassifier` with DTW
- Avoid: Deep learning (requires large data)

## Reference Documentation

Detailed information available in `references/`:
- `classification.md` - All classification algorithms
- `regression.md` - Regression methods
- `clustering.md` - Clustering algorithms
- `forecasting.md` - Forecasting approaches
- `anomaly_detection.md` - Anomaly detection methods
- `segmentation.md` - Segmentation algorithms
- `similarity_search.md` - Pattern matching and motif discovery
- `transformations.md` - Feature extraction and preprocessing
- `distances.md` - Time series distance metrics
- `networks.md` - Deep learning architectures
- `datasets_benchmarking.md` - Data loading and evaluation tools

## Additional Resources

- Documentation: https://www.aeon-toolkit.org/
- GitHub: https://github.com/aeon-toolkit/aeon
- Examples: https://www.aeon-toolkit.org/en/stable/examples.html
- API Reference: https://www.aeon-toolkit.org/en/stable/api_reference.html

