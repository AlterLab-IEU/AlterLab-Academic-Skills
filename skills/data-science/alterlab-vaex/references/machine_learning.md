# Machine Learning Integration

This reference covers Vaex's machine learning capabilities including transformers, encoders, feature engineering, model integration, and building ML pipelines on large datasets.

## Overview

Vaex provides a comprehensive ML framework (`vaex.ml`) that works seamlessly with large datasets. The framework includes:
- Transformers for feature scaling and engineering
- Encoders for categorical variables
- Dimensionality reduction (PCA)
- Clustering algorithms
- Integration with scikit-learn, XGBoost, LightGBM, CatBoost, and Keras
- State management for production deployment

**Key advantage:** All transformations create virtual columns, so preprocessing doesn't increase memory usage.

## Feature Scaling

### Standard Scaler

```python
import vaex
import vaex.ml

df = vaex.open('data.hdf5')

# Fit standard scaler
scaler = vaex.ml.StandardScaler(features=['age', 'income', 'score'])
scaler.fit(df)

# Transform (creates virtual columns)
df = scaler.transform(df)

# Scaled columns created as: 'standard_scaled_age', 'standard_scaled_income', etc.
print(df.column_names)
```

### MinMax Scaler

```python
# Scale to [0, 1] range
minmax_scaler = vaex.ml.MinMaxScaler(features=['age', 'income'])
minmax_scaler.fit(df)
df = minmax_scaler.transform(df)

# Custom range
minmax_scaler = vaex.ml.MinMaxScaler(
    features=['age'],
    feature_range=(-1, 1)
)
```

### MaxAbs Scaler

```python
# Scale by maximum absolute value
maxabs_scaler = vaex.ml.MaxAbsScaler(features=['values'])
maxabs_scaler.fit(df)
df = maxabs_scaler.transform(df)
```

### Robust Scaler

```python
# Scale using median and IQR (robust to outliers)
robust_scaler = vaex.ml.RobustScaler(features=['income', 'age'])
robust_scaler.fit(df)
df = robust_scaler.transform(df)
```

## Categorical Encoding

### Label Encoder

```python
# Encode categorical to integers
label_encoder = vaex.ml.LabelEncoder(features=['category', 'region'])
label_encoder.fit(df)
df = label_encoder.transform(df)

# Creates: 'label_encoded_category', 'label_encoded_region'
```

### One-Hot Encoder

```python
# Create binary columns for each category
onehot = vaex.ml.OneHotEncoder(features=['category'])
onehot.fit(df)
df = onehot.transform(df)

# Creates columns like: 'category_A', 'category_B', 'category_C'

# Control prefix
onehot = vaex.ml.OneHotEncoder(
    features=['category'],
    prefix='cat_'
)
```

### Frequency Encoder

```python
# Encode by category frequency
freq_encoder = vaex.ml.FrequencyEncoder(features=['category'])
freq_encoder.fit(df)
df = freq_encoder.transform(df)

# Each category replaced by its frequency in the dataset
```

### Target Encoder (Bayesian Mean Encoder)

```python
# Encode category by a smoothed target mean (for supervised learning).
# vaex.ml has no plain TargetEncoder; BayesianTargetEncoder shrinks each category
# mean toward the global mean with `weight`.
target_encoder = vaex.ml.BayesianTargetEncoder(
    features=['category'],
    target='target_variable',
    weight=100,
)
target_encoder.fit(df)
df = target_encoder.transform(df)

# Creates: 'mean_encoded_category'; unseen categories get the global mean
```

Fit target encoders on the training split only, then transform validation/test data, to avoid target leakage.

### Weight of Evidence Encoder

```python
# Encode for binary classification
woe_encoder = vaex.ml.WeightOfEvidenceEncoder(
    features=['category'],
    target='binary_target'
)
woe_encoder.fit(df)
df = woe_encoder.transform(df)
```

## Feature Engineering

### Binning/Discretization

```python
# Bin continuous variable into discrete bins
binner = vaex.ml.KBinsDiscretizer(
    features=['age'],
    n_bins=5,
    strategy='uniform'  # or 'quantile' / 'kmeans'
)
binner.fit(df)
df = binner.transform(df)  # creates 'binned_age'
```

### Cyclic Transformations

```python
# Transform cyclic features. `n` is a single int period, so use one transformer per period.
hour_cycle = vaex.ml.CycleTransformer(features=['hour'], n=24)
dow_cycle = vaex.ml.CycleTransformer(features=['day_of_week'], n=7)
df = hour_cycle.fit_transform(df)
df = dow_cycle.fit_transform(df)

# Creates x/y (cos/sin) components, e.g. 'hour_x', 'hour_y'
```

### PCA (Principal Component Analysis)

```python
# Dimensionality reduction
pca = vaex.ml.PCA(
    features=['feature1', 'feature2', 'feature3', 'feature4'],
    n_components=2
)
pca.fit(df)
df = pca.transform(df)

# Creates: 'PCA_0', 'PCA_1'

# Access explained variance
print(pca.explained_variance_ratio_)
```

### Random Projection

```python
# Fast dimensionality reduction
projector = vaex.ml.RandomProjections(
    features=['x1', 'x2', 'x3', 'x4', 'x5'],
    n_components=3
)
projector.fit(df)
df = projector.transform(df)  # creates 'random_projection_0', ...
```

## Clustering

### K-Means

```python
# Cluster data (KMeans lives in vaex.ml.cluster)
import vaex.ml.cluster

kmeans = vaex.ml.cluster.KMeans(
    features=['feature1', 'feature2', 'feature3'],
    n_clusters=5,
    max_iter=100
)
kmeans.fit(df)
df = kmeans.transform(df)

# Creates 'prediction_kmeans' column with cluster labels

# Access cluster centers (no trailing underscore)
print(kmeans.cluster_centers)
```

## Integration with External Libraries

### Scikit-Learn

```python
from sklearn.ensemble import RandomForestClassifier
import vaex.ml.sklearn  # `import vaex.ml` alone does not load the sklearn/xgboost/... submodules

# Prepare data. Use df['split'], not df.split: DataFrame.split is a method, so
# df.split == 'train' silently compares the method, not the column.
train_df = df[df['split'] == 'train']
test_df = df[df['split'] == 'test']

# Features and target
features = ['feature1', 'feature2', 'feature3']
target = 'target'

# Train scikit-learn model
model = RandomForestClassifier(n_estimators=100)

# Fit using Vaex data
sklearn_model = vaex.ml.sklearn.Predictor(
    features=features,
    target=target,
    model=model,
    prediction_name='rf_prediction'
)
sklearn_model.fit(train_df)

# Predict (creates virtual column)
test_df = sklearn_model.transform(test_df)

# Access predictions
predictions = test_df.rf_prediction.values
```

### XGBoost

```python
import xgboost as xgb
import vaex.ml.xgboost

# Configure parameters
params = {
    'max_depth': 6,
    'eta': 0.1,
    'objective': 'reg:squarederror',
    'eval_metric': 'rmse'
}

# params and num_boost_round are constructor arguments, not fit() arguments
booster = vaex.ml.xgboost.XGBoostModel(
    features=features,
    target=target,
    params=params,
    num_boost_round=100,
    prediction_name='xgb_pred'
)

# Train (loads the training features into memory)
booster.fit(train_df)

# Predict
test_df = booster.transform(test_df)
```

### LightGBM

```python
import lightgbm as lgb
import vaex.ml.lightgbm

# Parameters
params = {
    'objective': 'binary',
    'metric': 'auc',
    'num_leaves': 31,
    'learning_rate': 0.05
}

# params and num_boost_round are constructor arguments
lgb_model = vaex.ml.lightgbm.LightGBMModel(
    features=features,
    target=target,
    params=params,
    num_boost_round=100,
    prediction_name='lgb_pred'
)

# Train
lgb_model.fit(train_df)

# Predict
test_df = lgb_model.transform(test_df)
```

### CatBoost

```python
from catboost import CatBoostClassifier
import vaex.ml.catboost

# Parameters
params = {
    'depth': 6,
    'learning_rate': 0.1,
    'loss_function': 'Logloss'
}

# params / num_boost_round / prediction_type are constructor arguments
catboost_model = vaex.ml.catboost.CatBoostModel(
    features=features,
    target=target,
    params=params,
    num_boost_round=100,
    prediction_type='Probability',  # or 'Class' / 'RawFormulaVal'
    prediction_name='catboost_pred'
)

# Train
catboost_model.fit(train_df)

# Predict
test_df = catboost_model.transform(test_df)
```

### Keras/TensorFlow

The wrapper lives in `vaex.ml.tensorflow` and only serves predictions: train the network with the
Keras API (its `KerasModel.fit` raises `NotImplementedError`), streaming batches from Vaex.

```python
from tensorflow import keras
import vaex.ml.tensorflow

# Stream training batches out of the Vaex DataFrame
gen_train = train_df.ml.tensorflow.to_keras_generator(features=features, target=target, batch_size=10_000)

nn_model = keras.Sequential([
    keras.layers.Dense(64, activation='relu'),
    keras.layers.Dense(32, activation='relu'),
    keras.layers.Dense(1, activation='sigmoid')
])
nn_model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
nn_model.fit(x=gen_train, epochs=10, steps_per_epoch=len(train_df) // 10_000)

# Wrap the fitted model to get lazy predictions + state serialization
keras_model = vaex.ml.tensorflow.KerasModel(
    features=features,
    model=nn_model,
    prediction_name='keras_pred'
)
test_df = keras_model.transform(test_df)
```

## Building ML Pipelines

### Sequential Pipeline

```python
import vaex.ml

# Create preprocessing pipeline
pipeline = []

# Step 1: Encode categorical
label_enc = vaex.ml.LabelEncoder(features=['category'])
pipeline.append(label_enc)

# Step 2: Scale features
scaler = vaex.ml.StandardScaler(features=['age', 'income'])
pipeline.append(scaler)

# Step 3: PCA
pca = vaex.ml.PCA(features=['age', 'income'], n_components=2)
pipeline.append(pca)

# Fit pipeline
for step in pipeline:
    step.fit(df)
    df = step.transform(df)

# Or use fit_transform
for step in pipeline:
    df = step.fit_transform(df)
```

### Complete ML Pipeline

```python
import vaex
import vaex.ml
import vaex.ml.sklearn
from sklearn.ensemble import RandomForestClassifier

# Load data
df = vaex.open('data.hdf5')

# Split data
train_df = df[df.year < 2020]
test_df = df[df.year >= 2020]

# Define pipeline
# 1. Categorical encoding
cat_encoder = vaex.ml.LabelEncoder(features=['category', 'region'])

# 2. Feature scaling
scaler = vaex.ml.StandardScaler(features=['age', 'income', 'score'])

# 3. Model
features = ['label_encoded_category', 'label_encoded_region',
            'standard_scaled_age', 'standard_scaled_income', 'standard_scaled_score']
model = vaex.ml.sklearn.Predictor(
    features=features,
    target='target',
    model=RandomForestClassifier(n_estimators=100),
    prediction_name='prediction'
)

# Fit pipeline
train_df = cat_encoder.fit_transform(train_df)
train_df = scaler.fit_transform(train_df)
model.fit(train_df)

# Apply to test
test_df = cat_encoder.transform(test_df)
test_df = scaler.transform(test_df)
test_df = model.transform(test_df)

# Evaluate
accuracy = (test_df.prediction == test_df.target).mean()
print(f"Accuracy: {accuracy:.4f}")
```

## State Management and Deployment

### Saving Pipeline State

```python
# After fitting all transformers and model
# Save the entire pipeline state
train_df.state_write('pipeline_state.json')

# In production: Load fresh data and apply transformations.
# The state also stores train_df's row filter (e.g. split == 'train'); set_filter=False
# keeps it from being applied to the new data.
prod_df = vaex.open('new_data.hdf5')
prod_df.state_load('pipeline_state.json', set_filter=False)

# All transformations and models are applied
predictions = prod_df.prediction.values
```

### Transferring State Between DataFrames

```python
# Fit on training data
train_df = cat_encoder.fit_transform(train_df)
train_df = scaler.fit_transform(train_df)
model.fit(train_df)

# Save state
train_df.state_write('model_state.json')

# Apply to test data. With the default set_filter=True, the training filter in the
# state replaces test_df's own filter and you would silently evaluate on training rows.
test_df.state_load('model_state.json', set_filter=False)

# Apply to validation data
val_df.state_load('model_state.json', set_filter=False)
```

### Exporting with Transformations

```python
# Export DataFrame with all virtual columns materialized
df_with_features = df.copy()
df_with_features = df_with_features.materialize()
df_with_features.export_hdf5('processed_data.hdf5')
```

## Model Evaluation

### Classification Metrics

```python
# Binary classification
from sklearn.metrics import accuracy_score, roc_auc_score, f1_score

y_true = test_df.target.values
y_pred = test_df.prediction.values
y_proba = test_df.prediction_proba.values if hasattr(test_df, 'prediction_proba') else None

accuracy = accuracy_score(y_true, y_pred)
f1 = f1_score(y_true, y_pred)
if y_proba is not None:
    auc = roc_auc_score(y_true, y_proba)

print(f"Accuracy: {accuracy:.4f}")
print(f"F1 Score: {f1:.4f}")
if y_proba is not None:
    print(f"AUC-ROC: {auc:.4f}")
```

### Regression Metrics

```python
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

y_true = test_df.target.values
y_pred = test_df.prediction.values

mse = mean_squared_error(y_true, y_pred)
rmse = np.sqrt(mse)
mae = mean_absolute_error(y_true, y_pred)
r2 = r2_score(y_true, y_pred)

print(f"RMSE: {rmse:.4f}")
print(f"MAE: {mae:.4f}")
print(f"R²: {r2:.4f}")
```

### Cross-Validation

```python
# Manual K-fold cross-validation
import numpy as np

# Create fold indices
df['fold'] = np.random.randint(0, 5, len(df))

results = []
for fold in range(5):
    train = df[df.fold != fold]
    val = df[df.fold == fold]

    # Fit pipeline
    train = encoder.fit_transform(train)
    train = scaler.fit_transform(train)
    model.fit(train)

    # Validate
    val = encoder.transform(val)
    val = scaler.transform(val)
    val = model.transform(val)

    accuracy = (val.prediction == val.target).mean()
    results.append(accuracy)

print(f"CV Accuracy: {np.mean(results):.4f} ± {np.std(results):.4f}")
```

## Feature Selection

### Correlation-Based

```python
# Compute correlations with target
correlations = {}
for feature in features:
    corr = df.correlation(df[feature], df.target)
    correlations[feature] = abs(corr)

# Sort by correlation
sorted_features = sorted(correlations.items(), key=lambda x: x[1], reverse=True)
top_features = [f[0] for f in sorted_features[:10]]

print("Top 10 features:", top_features)
```

### Variance-Based

```python
# Remove low-variance features
feature_variances = {}
for feature in features:
    var = df[feature].std() ** 2
    feature_variances[feature] = var

# Keep features with variance above threshold
threshold = 0.01
selected_features = [f for f, v in feature_variances.items() if v > threshold]
```

## Handling Imbalanced Data

### Class Weights

```python
# Compute class weights from per-class counts
counts = df['target'].value_counts()  # pandas Series indexed by class label
total = len(df)
weights = {
    label: total / (len(counts) * n)
    for label, n in counts.items()
}

# Use in model
model = RandomForestClassifier(class_weight=weights)
```

### Undersampling

```python
# Undersample majority class
minority_count = df[df.target == 1].count()

# Sample from majority class
majority_sampled = df[df.target == 0].sample(n=minority_count)
minority_all = df[df.target == 1]

# Combine
df_balanced = vaex.concat([majority_sampled, minority_all])
```

### Oversampling (SMOTE alternative)

```python
# Duplicate minority class samples
minority = df[df.target == 1]
majority = df[df.target == 0]

# Replicate minority
minority_oversampled = vaex.concat([minority] * 5)

# Combine
df_balanced = vaex.concat([majority, minority_oversampled])
```

## Common Patterns

### Pattern: End-to-End Classification Pipeline

```python
import vaex
import vaex.ml
import vaex.ml.sklearn
from sklearn.ensemble import RandomForestClassifier

# Load and split
df = vaex.open('data.hdf5')
train = df[df['split'] == 'train']  # df.split is a method, so index the column
test = df[df['split'] == 'test']

# Preprocessing
# Categorical encoding
cat_enc = vaex.ml.LabelEncoder(features=['cat1', 'cat2'])
train = cat_enc.fit_transform(train)

# Feature scaling
scaler = vaex.ml.StandardScaler(features=['num1', 'num2', 'num3'])
train = scaler.fit_transform(train)

# Model training
features = ['label_encoded_cat1', 'label_encoded_cat2',
            'standard_scaled_num1', 'standard_scaled_num2', 'standard_scaled_num3']
model = vaex.ml.sklearn.Predictor(
    features=features,
    target='target',
    model=RandomForestClassifier(n_estimators=100)
)
model.fit(train)
train = model.transform(train)  # adds the 'prediction' column, so the state carries the model

# Save state
train.state_write('production_pipeline.json')

# Apply to test (set_filter=False keeps test's own split filter)
test.state_load('production_pipeline.json', set_filter=False)

# Evaluate
accuracy = (test.prediction == test.target).mean()
print(f"Test Accuracy: {accuracy:.4f}")
```

### Pattern: Feature Engineering Pipeline

```python
# Create rich features
df['age_squared'] = df.age ** 2
df['income_log'] = df.income.log()
df['age_income_interaction'] = df.age * df.income

# Binning
df['age_bin'] = df.age.digitize([0, 18, 30, 50, 65, 100])

# Cyclic features
df['hour_sin'] = (2 * np.pi * df.hour / 24).sin()
df['hour_cos'] = (2 * np.pi * df.hour / 24).cos()

# Aggregate features
avg_by_category = df.groupby('category').agg({'income': 'mean'})
# Join back to create feature
df = df.join(avg_by_category, on='category', rsuffix='_category_mean')
```

## Best Practices

1. **Use virtual columns** - Transformers create virtual columns (no memory overhead)
2. **Save state files** - Enable easy deployment and reproduction
3. **Batch operations** - Use `delay=True` when computing multiple features
4. **Feature scaling** - Always scale features before PCA or distance-based algorithms
5. **Encode categories** - Use appropriate encoder (label, one-hot, target)
6. **Cross-validate** - Always validate on held-out data
7. **Monitor memory** - Check memory usage with `df.byte_size()`
8. **Export checkpoints** - Save intermediate results in long pipelines

## Related Resources

- For data preprocessing: See `data_processing.md`
- For performance optimization: See `performance.md`
- For DataFrame operations: See `core_dataframes.md`
