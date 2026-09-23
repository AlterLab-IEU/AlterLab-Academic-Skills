# PyHealth Models

## Overview

PyHealth provides 33+ models for healthcare prediction tasks, ranging from simple baselines to state-of-the-art deep learning architectures. Models are organized into general-purpose architectures and healthcare-specific models.

## Model Base Class

All models inherit from `BaseModel` (a `torch.nn.Module`).

> **Init args (PyHealth 2.x, verified on 2.0.2).** Models take the `SampleDataset` returned by `set_task()` plus hyperparameters — e.g. `Transformer(dataset=sample_dataset, embedding_dim=128)`. `BaseModel.__init__(dataset)` reads the feature keys from the task's `input_schema`, the label key from its `output_schema`, and the mode (`"binary"`, `"multiclass"`, `"multilabel"`, `"regression"`) from the output processor. The 1.x arguments `feature_keys=`, `label_key=`, and `mode=` are **not** accepted by the core EHR models (they raise `TypeError`); only a few legacy generative/vision classes (`VAE`, `Graph_TorchvisionModel`) still take them. To change which inputs a model sees, change the task schema.

**Key Attributes (set from the dataset):**
- `dataset`: Associated SampleDataset
- `feature_keys`: List of input keys (from the task's `input_schema`)
- `label_keys`: List of label keys (from the task's `output_schema`; most models require exactly one)
- `mode`: Task type resolved from the output schema
- `embedding_dim`: Feature embedding dimension (constructor argument)

**Key Methods:**
- `forward(**batch)`: Returns a dict with `loss`, `y_prob`, `y_true`, `logit` (plus `embed` when called with `embed=True`)
- `get_output_size()`, `get_loss_function()`, `prepare_y_prob()`: helpers used by subclasses
- Checkpointing lives on the `Trainer` (`save_ckpt()` / `load_ckpt()`), not on the model

## General-Purpose Models

### Baseline Models

**Logistic Regression** (`LogisticRegression`)
- Linear classifier with mean pooling
- Simple baseline for comparison
- Fast training and inference
- Good for interpretability

**Usage:**
```python
from pyhealth.models import LogisticRegression

model = LogisticRegression(
    dataset=sample_dataset,
)
```

**Multi-Layer Perceptron** (`MLP`)
- Feedforward neural network
- Configurable hidden layers
- Mean/sum pooling of nested sequence inputs
- Good baseline for structured data

**Parameters (2.0.2):**
- `embedding_dim`: Embedding size (default 128)
- `hidden_dim`: Hidden layer size (default 128)
- `n_layers`: Number of MLP layers (default 2)
- `activation`: Activation name (default `"relu"`)
- Nested sequence inputs are mean/sum-pooled before the MLP

**Usage:**
```python
from pyhealth.models import MLP

model = MLP(
    dataset=sample_dataset,
    hidden_dim=128,
)
```

### Convolutional Neural Networks

**CNN** (`CNN`)
- Convolutional layers for pattern detection
- Effective for sequential and spatial data
- Captures local temporal patterns
- Parameter efficient

**Architecture:**
- Multiple 1D convolutional layers
- Max pooling for dimension reduction
- Fully connected output layers

**Parameters (2.0.2):**
- `embedding_dim`: Embedding size (default 128)
- `hidden_dim`: Convolution channels (default 128)
- `num_layers`: Number of conv layers (default 1)

**Usage:**
```python
from pyhealth.models import CNN

model = CNN(
    dataset=sample_dataset,
)
```

**Temporal Convolutional Networks** (`TCN`)
- Dilated convolutions for long-range dependencies
- Causal convolutions (no future information leakage)
- Efficient for long sequences
- Good for time-series prediction

**Advantages:**
- Captures long-term dependencies
- Parallelizable (faster than RNNs)
- Stable gradients

**Usage:** `TCN(dataset=sample_dataset, embedding_dim=128, num_channels=128)` (`num_channels` may be a list, one entry per level)

### Recurrent Neural Networks

**RNN** (`RNN`)
- Basic recurrent architecture
- Supports LSTM, GRU, RNN variants
- Sequential processing
- Captures temporal dependencies

**Parameters (2.0.2):**
- `embedding_dim`, `hidden_dim`: Embedding and hidden-state sizes (default 128)
- Passed through to `RNNLayer`: `rnn_type` (`"GRU"` default, `"LSTM"`, `"RNN"`), `num_layers` (1), `dropout` (0.5), `bidirectional` (False)

**Usage:**
```python
from pyhealth.models import RNN

model = RNN(
    dataset=sample_dataset,
    rnn_type="LSTM",
    hidden_dim=128,
)
```

**Best for:**
- Sequential clinical events
- Temporal pattern learning
- Variable-length sequences

### Transformer Models

**Transformer** (`Transformer`)
- Self-attention mechanism
- Parallel processing of sequences
- State-of-the-art performance
- Effective for long-range dependencies

**Architecture:**
- Multi-head self-attention
- Position embeddings
- Feed-forward networks
- Layer normalization

**Parameters (2.0.2):**
- `embedding_dim`: Model width (default 128)
- `heads`: Attention heads per block (default 1)
- `num_layers`: Transformer blocks per feature stream (default 1)
- `dropout`: Dropout rate (default 0.5)
- `max_seq_len`: Maximum sequence length (default 1024)

**Usage:**
```python
from pyhealth.models import Transformer

model = Transformer(
    dataset=sample_dataset,
    embedding_dim=128,
    heads=2,
    num_layers=2,
    dropout=0.1,
)
```

`Transformer` implements the Chefer-relevance interface and `forward_from_embedding`, so it works with `CheferRelevance`, `AttentionRollout`, and the embedding-gradient methods (`IntegratedGradients`, `DeepLift`) in `pyhealth.interpret.methods` (see `references/training_evaluation.md`).

**TransformersModel** (`TransformersModel`)
- Integration with HuggingFace transformers
- Pre-trained language models for clinical text
- Fine-tuning for healthcare tasks
- Examples: BERT, RoBERTa, BioClinicalBERT

**Usage:**
```python
from pyhealth.models import TransformersModel

# Signature: TransformersModel(dataset, model_name, dropout=0.1)
model = TransformersModel(
    dataset=sample_dataset,          # task with a single text input and one label
    model_name="emilyalsentzer/Bio_ClinicalBERT",
)
```

### Graph Neural Networks

**GAT / GCN** (`GAT`, `GCN`) — there is no single `GNN` class in 2.x
- Graph-based learning over the task's inputs
- Models relationships between entities
- `GAT` (graph attention) and `GCN` (graph convolution) are separate classes

**Use Cases:**
- Drug-drug interactions
- Patient similarity networks
- Knowledge graph integration
- Comorbidity relationships

**Parameters (2.0.2):**
- `embedding_dim`: Embedding size (default 128)
- `nhid`: Hidden units per graph layer (default 64)
- `num_layers`: Number of graph layers (default 2)
- `dropout`: Dropout rate (default 0.5)
- `nheads`: Attention heads (`GAT` only, default 1)

**Usage:**
```python
from pyhealth.models import GAT, GCN

model = GAT(dataset=sample_dataset, embedding_dim=128, nhid=64, nheads=2)
# or: GCN(dataset=sample_dataset, embedding_dim=128, nhid=64)
```

## Healthcare-Specific Models

### Interpretable Clinical Models

**RETAIN** (`RETAIN`)
- Reverse time attention mechanism
- Highly interpretable predictions
- Visit-level and event-level attention
- Identifies influential clinical events

**Key Features:**
- Two-level attention (visits and features)
- Temporal decay modeling
- Clinically meaningful explanations
- Published in NeurIPS 2016

**Usage:**
```python
from pyhealth.models import RETAIN

model = RETAIN(
    dataset=sample_dataset,
)

# A forward pass returns a dict: loss, y_prob, y_true, logit.
# RETAIN is interpretable by design, but PyHealth does not return its
# alpha/beta attention weights and it does not implement the Chefer or
# forward_from_embedding interfaces. For post-hoc token attributions,
# train a Transformer (see references/training_evaluation.md).
out = model(**batch)
loss, y_prob = out["loss"], out["y_prob"]
```

**Best for:**
- Mortality prediction
- Readmission prediction
- Clinical risk scoring
- Interpretable predictions

**AdaCare** (`AdaCare`)
- Adaptive care model with feature calibration
- Disease-specific attention
- Handles irregular time intervals
- Interpretable feature importance

**ConCare** (`ConCare`)
- Cross-visit convolutional attention
- Temporal convolutional feature extraction
- Multi-level attention mechanism
- Good for longitudinal EHR modeling

### Medication Recommendation Models

**GAMENet** (`GAMENet`)
- Graph-based medication recommendation
- Drug-drug interaction modeling
- Memory network for patient history
- Multi-hop reasoning

**Architecture:**
- Drug knowledge graph
- Memory-augmented neural network
- DDI-aware prediction

**Usage:**
```python
from pyhealth.models import GAMENet

# GAMENet builds its EHR co-occurrence and DDI adjacency matrices from the
# dataset itself; passing ehr_adj/ddi_adj raises ValueError.
model = GAMENet(
    dataset=sample_dataset,   # from a DrugRecommendation* task
    embedding_dim=64,
    hidden_dim=64,
)
```

Reference: Shang et al., GAMENet: Graph Augmented MEmory Networks for Recommending Medication Combination, AAAI 2019.

**MICRON** (`MICRON`)
- Medication recommendation with DDI constraints
- Interaction-aware predictions
- Safety-focused drug selection

**SafeDrug** (`SafeDrug`)
- Safety-aware drug recommendation
- Molecular structure integration
- DDI constraint optimization
- Balances efficacy and safety

**Key Features:**
- Dual molecular graph encoders (global MPNN + local bipartite substructure encoder)
- DDI-controllable loss that penalizes interacting drug pairs
- Published at IJCAI 2021 (Yang et al., "SafeDrug: Dual Molecular Graph Encoders for Recommending Effective and Safe Drug Combinations")

**Usage:**
```python
from pyhealth.models import SafeDrug

# SafeDrug derives the DDI matrix and molecule set from the dataset's ATC
# drug codes (RDKit is a PyHealth dependency); it requires the label key "drugs".
model = SafeDrug(
    dataset=sample_dataset,   # from a DrugRecommendation* task
    embedding_dim=64,
    hidden_dim=64,
)
```

**MoleRec** (`MoleRec`)
- Molecular-level drug recommendations
- Sub-structure reasoning
- Fine-grained medication selection

### Disease Progression Models

**StageNet** (`StageNet`)
- Disease stage-aware prediction
- Learns clinical stages automatically
- Stage-adaptive feature extraction
- Effective for chronic disease monitoring

**Architecture:**
- Stage-aware LSTM
- Dynamic stage transitions
- Time-decay mechanism

**Usage:**
```python
from pyhealth.models import StageNet

# Use with a StageNet-format task such as MortalityPredictionStageNetMIMIC4
# (inputs "icd_codes" + "labs"); the schema, not the constructor, sets the inputs.
model = StageNet(
    dataset=sample_dataset,
    chunk_size=128,
)
```

**Best for:**
- ICU mortality prediction
- Chronic disease progression
- Time-varying risk assessment

**Deepr** (`Deepr`)
- Convolutional network over sequences of medical-record codes
- Medical concept embeddings with visit separators
- Published in IEEE Journal of Biomedical and Health Informatics (2017)

### Advanced Sequential Models

**Agent** (`Agent`)
- "Dr. Agent": clinical prediction via mimicked second opinions
- Two policy-gradient agents choose which parts of the patient history to attend to (dynamic skip connections)

**GRASP** (`GRASP`)
- Health-status representation learning that incorporates knowledge from similar patients (clustered patient graph); AAAI 2021

### Physiological Signal Models

**SparcNet** (`SparcNet`)
- 1D dense convolutional network from the expert-level EEG classification study of seizures and rhythmic/periodic patterns (Neurology 2023)
- Use for EEG event/abnormality classification tasks

**ContraWR** (`ContraWR`)
- Supervised encoder from the ContraWR sleep-EEG work (STFT + 2D CNN)
- Use for sleep staging and other spectrogram-style signal tasks

### Record Linkage

**MedLink** (`MedLink`)
- De-identified patient health record linkage (Wu et al., KDD 2023) — matches records of the same patient across sources; it is not concept/entity normalization

### Generative Models

- **Synthetic EHR**: `HALO`, `PromptEHR`, `MedGAN`, `CorGAN`, and `GPT`, used with the `EHRGeneration*` tasks
- **Images**: `GAN` and `VAE` generate or reconstruct small (32–128 px) images; `VAE` and `Graph_TorchvisionModel` still take the legacy `feature_keys`/`label_key`/`mode` arguments

### Social Determinants of Health

**SdohClassifier** (`SdohClassifier`)
- Sentence-level classification of social determinants of health from clinical text (MIMIC-III-derived SDoH annotations)

## Model Selection Guidelines

### By Task Type

**Binary Classification** (Mortality, Readmission)
- Start with: Logistic Regression (baseline)
- Standard: RNN, Transformer
- Interpretable: RETAIN, AdaCare
- Advanced: StageNet

**Multi-Label Classification** (Drug Recommendation)
- Standard: CNN, RNN
- Healthcare-specific: GAMENet, SafeDrug, MICRON, MoleRec
- Graph-based: GAT, GCN

**Regression** (Length of Stay)
- Start with: MLP (baseline)
- Sequential: RNN, TCN
- Advanced: Transformer

**Multi-Class Classification** (Medical Coding, Specialty)
- Standard: CNN, RNN, Transformer
- Text-based: TransformersModel (BERT variants)

### By Data Type

**Sequential Events** (Diagnoses, Medications, Procedures)
- RNN, LSTM, GRU
- Transformer
- RETAIN, AdaCare, ConCare

**Time-Series Signals** (EEG, ECG)
- CNN, TCN
- RNN
- Transformer

**Text** (Clinical Notes)
- TransformersModel (ClinicalBERT, BioBERT)
- CNN for shorter text
- RNN for sequential text

**Graphs** (Drug Interactions, Patient Networks)
- GNN (GAT, GCN)
- GAMENet, SafeDrug

**Images** (X-rays, CT scans)
- CNN (ResNet, DenseNet via TransformersModel)
- Vision Transformers

### By Interpretability Needs

**High Interpretability Required:**
- Logistic Regression
- RETAIN
- AdaCare
- SparcNet

**Moderate Interpretability:**
- CNN (filter visualization)
- Transformer (attention visualization)
- GNN (graph attention)

**Black-Box Acceptable:**
- Deep RNN models
- Complex ensembles

## Training Considerations

### Hyperparameter Tuning

**Embedding Dimension:**
- Small datasets: 64-128
- Large datasets: 128-256
- Complex tasks: 256-512

**Hidden Dimension:**
- Proportional to embedding_dim
- Typically 1-2x embedding_dim

**Number of Layers:**
- Start with 2-3 layers
- Deeper for complex patterns
- Watch for overfitting

**Dropout:**
- Start with 0.5
- Reduce if underfitting (0.1-0.3)
- Increase if overfitting (0.5-0.7)

### Computational Requirements

**Memory (GPU):**
- CNN: Low to moderate
- RNN: Moderate (sequence length dependent)
- Transformer: High (quadratic in sequence length)
- GNN: Moderate to high (graph size dependent)

**Training Speed:**
- Fastest: Logistic Regression, MLP, CNN
- Moderate: RNN, GNN
- Slower: Transformer (but parallelizable)

### Best Practices

1. **Start with simple baselines** (Logistic Regression, MLP)
2. **Choose the task's input schema** (the model's inputs) based on data availability
3. **Set the task's output schema to the prediction target** (binary, multiclass, multilabel, regression); the model's mode follows from it
4. **Consider interpretability requirements** for clinical deployment
5. **Validate on held-out test set** for realistic performance
6. **Monitor for overfitting** especially with complex models
7. **Use pretrained models** when possible (TransformersModel)
8. **Consider computational constraints** for deployment

## Example Workflow

```python
from pyhealth.datasets import MIMIC4EHRDataset
from pyhealth.tasks import MortalityPredictionMIMIC4
from pyhealth.models import Transformer
from pyhealth.trainer import Trainer

# 1. Prepare data
dataset = MIMIC4EHRDataset(
    root="/path/to/data",
    tables=["diagnoses_icd", "procedures_icd", "prescriptions"],
)
sample_dataset = dataset.set_task(MortalityPredictionMIMIC4())

# 2. Initialize model
model = Transformer(
    dataset=sample_dataset,
    embedding_dim=128,
    num_layers=2,
    dropout=0.3,
)

# 3. Train model
trainer = Trainer(model=model, metrics=["pr_auc", "roc_auc", "f1"])
trainer.train(
    train_dataloader=train_loader,
    val_dataloader=val_loader,
    epochs=50,
    monitor="pr_auc",
    monitor_criterion="max",
)

# 4. Evaluate
results = trainer.evaluate(test_loader)
print(results)
```
