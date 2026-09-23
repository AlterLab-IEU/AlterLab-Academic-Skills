---
name: alterlab-pytorch-lightning
description: Scalable deep-learning training with PyTorch Lightning — organize PyTorch code into LightningModules, configure Trainers for multi-GPU/TPU, build data pipelines and callbacks, log to W&B or TensorBoard, and run distributed training (DDP, FSDP, DeepSpeed). Use when structuring PyTorch training loops, scaling neural-network training across GPUs/TPUs, or adding checkpointing, logging, and distributed strategies. Part of the AlterLab Academic Skills suite.
license: Apache-2.0
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*)
compatibility: No API key required. Runs locally via `uv run python`; requires the `lightning` package (>= 2.5; current 2.6 as of 2026-09, imported as `import lightning as L`) and torch (multi-GPU/TPU optional, W&B token optional for logging).
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# PyTorch Lightning

## Overview

PyTorch Lightning is a deep learning framework that organizes PyTorch code to eliminate boilerplate while maintaining full flexibility. Automate training workflows, multi-device orchestration, and implement best practices for neural network training and scaling across multiple GPUs/TPUs.

```bash
uv pip install lightning   # provides `import lightning as L` and `lightning.pytorch.*`
```

All code in this skill uses the unified `lightning` package. The separately published `pytorch-lightning` package installs the older `pytorch_lightning` namespace instead; do not mix the two namespaces in one project, because their classes are distinct (e.g. `lightning.Trainer.fit` rejects a `pytorch_lightning.LightningModule` with a `TypeError`).

## When to Use This Skill

This skill should be used when:
- Building, training, or deploying neural networks using PyTorch Lightning
- Organizing PyTorch code into LightningModules
- Configuring Trainers for multi-GPU/TPU training
- Implementing data pipelines with LightningDataModules
- Working with callbacks, logging, and distributed training strategies (DDP, FSDP, DeepSpeed)
- Structuring deep learning projects professionally

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Fine-tuning a pretrained Hugging Face model with the `transformers` Trainer / pipelines | `alterlab-transformers` |
| Designing graph neural network layers or loading graph datasets (GCN, GAT, message passing) | `alterlab-torch-geometric` |
| Reinforcement-learning agents trained on environments (PPO, SAC, DQN) | `alterlab-stable-baselines3` |
| Classical ML on tabular data (random forests, gradient boosting, linear models) | `alterlab-scikit-learn` |

## Core Capabilities

### 1. LightningModule - Model Definition

Organize PyTorch models into six logical sections:

1. **Initialization** - `__init__()` and `setup()`
2. **Training Loop** - `training_step(batch, batch_idx)`
3. **Validation Loop** - `validation_step(batch, batch_idx)`
4. **Test Loop** - `test_step(batch, batch_idx)`
5. **Prediction** - `predict_step(batch, batch_idx)`
6. **Optimizer Configuration** - `configure_optimizers()`

**Quick template reference:** See `scripts/template_lightning_module.py` for a complete boilerplate.

**Detailed documentation:** Read `references/lightning_module.md` for comprehensive method documentation, hooks, properties, and best practices.

### 2. Trainer - Training Automation

The Trainer automates the training loop, device management, gradient operations, and callbacks. Key features:

- Multi-GPU/TPU support with strategy selection (DDP, FSDP, DeepSpeed)
- Automatic mixed precision training
- Gradient accumulation and clipping
- Checkpointing and early stopping
- Progress bars and logging

**Quick setup reference:** See `scripts/quick_trainer_setup.py` for common Trainer configurations.

**Detailed documentation:** Read `references/trainer.md` for all parameters, methods, and configuration options.

### 3. LightningDataModule - Data Pipeline Organization

Encapsulate all data processing steps in a reusable class:

1. `prepare_data()` - Download and process data (single-process)
2. `setup()` - Create datasets and apply transforms (per-GPU)
3. `train_dataloader()` - Return training DataLoader
4. `val_dataloader()` - Return validation DataLoader
5. `test_dataloader()` - Return test DataLoader

**Quick template reference:** See `scripts/template_datamodule.py` for a complete boilerplate.

**Detailed documentation:** Read `references/data_module.md` for method details and usage patterns.

### 4. Callbacks - Extensible Training Logic

Add custom functionality at specific training hooks without modifying your LightningModule. Built-in callbacks include:

- **ModelCheckpoint** - Save best/latest models
- **EarlyStopping** - Stop when metrics plateau
- **LearningRateMonitor** - Track LR scheduler changes
- **BatchSizeFinder** - Auto-determine optimal batch size

**Detailed documentation:** Read `references/callbacks.md` for built-in callbacks and custom callback creation.

### 5. Logging - Experiment Tracking

Integrate with multiple logging platforms:

- TensorBoard (default when `tensorboard` is installed; otherwise CSV)
- Weights & Biases (WandbLogger)
- MLflow (MLFlowLogger)
- Comet (CometLogger)
- CSV (CSVLogger)

`NeptuneLogger` was removed in Lightning 2.6.4 after Neptune's hosted service shut down (March 2026).

Log metrics using `self.log("metric_name", value)` in any LightningModule method.

**Detailed documentation:** Read `references/logging.md` for logger setup and configuration.

### 6. Distributed Training - Scale to Multiple Devices

Choose the right strategy based on model size:

- **DDP** - For models <500M parameters (ResNet, smaller transformers)
- **FSDP** - For models 500M+ parameters (large transformers, recommended for Lightning users)
- **DeepSpeed** - For cutting-edge features and fine-grained control

Configure with: `Trainer(strategy="ddp", accelerator="gpu", devices=4)`

**Detailed documentation:** Read `references/distributed_training.md` for strategy comparison and configuration.

### 7. Best Practices

- Device agnostic code - Use `self.device` instead of `.cuda()`
- Hyperparameter saving - Use `self.save_hyperparameters()` in `__init__()`
- Metric logging - Use `self.log()` for automatic aggregation across devices
- Reproducibility - Use `seed_everything()` and `Trainer(deterministic=True)`
- Debugging - Use `Trainer(fast_dev_run=True)` to test with 1 batch

**Detailed documentation:** Read `references/best_practices.md` for common patterns and pitfalls.

## Quick Workflow

1. **Define model:**
   ```python
   class MyModel(L.LightningModule):
       def __init__(self):
           super().__init__()
           self.save_hyperparameters()
           self.model = YourNetwork()

       def training_step(self, batch, batch_idx):
           x, y = batch
           loss = F.cross_entropy(self.model(x), y)
           self.log("train_loss", loss)
           return loss

       def configure_optimizers(self):
           return torch.optim.Adam(self.parameters())
   ```

2. **Prepare data:**
   ```python
   # Option 1: Direct DataLoaders
   train_loader = DataLoader(train_dataset, batch_size=32)

   # Option 2: LightningDataModule (recommended for reusability)
   dm = MyDataModule(batch_size=32)
   ```

3. **Train:**
   ```python
   trainer = L.Trainer(max_epochs=10, accelerator="gpu", devices=2)
   trainer.fit(model, train_loader)  # or trainer.fit(model, datamodule=dm)
   ```

## Resources

### scripts/
Executable Python templates for common PyTorch Lightning patterns:

- `template_lightning_module.py` - Complete LightningModule boilerplate
- `template_datamodule.py` - Complete LightningDataModule boilerplate
- `quick_trainer_setup.py` - Common Trainer configuration examples

### references/
Detailed documentation for each PyTorch Lightning component:

- `lightning_module.md` - Comprehensive LightningModule guide (methods, hooks, properties)
- `trainer.md` - Trainer configuration and parameters
- `data_module.md` - LightningDataModule patterns and methods
- `callbacks.md` - Built-in and custom callbacks
- `logging.md` - Logger integrations and usage
- `distributed_training.md` - DDP, FSDP, DeepSpeed comparison and setup
- `best_practices.md` - Common patterns, tips, and pitfalls

