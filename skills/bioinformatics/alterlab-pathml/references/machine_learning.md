# Machine Learning

## Overview

PathML provides comprehensive machine learning capabilities for computational pathology, including pre-built models for nucleus detection and segmentation, PyTorch-integrated training workflows, public dataset access, and ONNX-based inference deployment. The framework seamlessly bridges image preprocessing with deep learning to enable end-to-end pathology ML pipelines.

## Pre-Built Models

PathML includes state-of-the-art pre-trained models for nucleus analysis:

### HoVer-Net

**HoVer-Net** (Horizontal and Vertical Network) performs simultaneous nucleus instance segmentation and classification.

**Architecture:**
- Encoder-decoder structure with three prediction branches:
  - **Nuclear Pixel (NP)** - Binary segmentation of nuclear regions
  - **Horizontal-Vertical (HV)** - Distance maps to nucleus centroids
  - **Classification (NC)** - Nucleus type classification

**Nucleus types:**
1. Epithelial
2. Inflammatory
3. Connective/Soft tissue
4. Dead/Necrotic
5. Background

**Usage:**
```python
from pathml.ml import HoVerNet
import torch

# Construct the model (n_classes = number of nucleus types).
model = HoVerNet(n_classes=5)

# Move to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)

# Inference on a tile. HoVerNet returns a list/tuple of branch outputs
# (NP, HV, and the classification branch when n_classes is set).
tile_image = torch.from_numpy(tile.image).permute(2, 0, 1).unsqueeze(0).float()
tile_image = tile_image.to(device)

with torch.no_grad():
    outputs = model(tile_image)
```

For pretrained weights, download a published HoVer-Net checkpoint and load it with `model.load_state_dict(...)`; the constructor does not fetch weights itself. Confirm the exact constructor argument (`n_classes`) and the branch output layout against the API docs for your installed version.

**Post-processing** (the real function is `post_process_batch_hovernet`, not `hovernet_postprocess`):
```python
from pathml.ml import post_process_batch_hovernet

# Convert a batch of model outputs to instance + type maps
instance_map, type_map = post_process_batch_hovernet(outputs, n_classes=5)

# instance_map: each nucleus has a unique ID
# type_map: each nucleus assigned a type
```

### HACTNet

**HACTNet** is a graph-neural-network model that operates on hierarchical cell-graph + tissue-graph (HACT) representations of a tissue region for region/graph-level classification. It is not a per-pixel nucleus classifier; pair it with the graph builders in `pathml.graph` (see `graphs.md`).

```python
from pathml.ml import HACTNet

# HACTNet consumes batched cell-graph and tissue-graph inputs constructed
# from segmented tissue. Check the API docs for the exact constructor
# arguments and the expected graph batch format for your version.
model = HACTNet(...)
```

## Training Workflows

### Dataset Preparation

PathML provides PyTorch-compatible dataset classes in `pathml.datasets` (note: NOT `pathml.ml`):

**TileDataset** wraps an on-disk h5path slide so its tiles can be served to a PyTorch `DataLoader`:
```python
from pathml.datasets import TileDataset
from torch.utils.data import DataLoader

# Point at an h5path file written by SlideData.write(...)
tile_dataset = TileDataset("processed/slide001.h5path")

loader = DataLoader(tile_dataset, batch_size=32, shuffle=True, num_workers=4)
for images, masks, labels in loader:
    ...
```

`pathml.datasets` also provides `EntityDataset` (for graph/entity inputs) and ready-made downloadable DataModules, `PanNukeDataModule` and `DeepFocusDataModule`. There is no `PathMLDataModule`; build train/val/test `DataLoader`s yourself or use one of the provided DataModules. Confirm the `TileDataset.__getitem__` return tuple against your version.

### Training HoVer-Net

Complete workflow for training HoVer-Net on custom data:

PathML ships the composite HoVer-Net loss as `loss_hovernet` (combining the NP, HV, and classification branch terms) — use it rather than reimplementing the loss by hand.

```python
import torch
from torch.utils.data import DataLoader
from pathml.ml import HoVerNet, loss_hovernet, post_process_batch_hovernet
from pathml.datasets import PanNukeDataModule

# 1. Prepare data (PanNukeDataModule lives in pathml.datasets)
data_module = PanNukeDataModule(
    data_dir="path/to/pannuke",
    batch_size=8,
    nucleus_type_labels=True,
)
train_loader = data_module.train_dataloader

# 2. Initialize model
model = HoVerNet(n_classes=5)

# 3. Use PathML's HoVer-Net loss
def criterion(outputs, ground_truth, n_classes=5):
    return loss_hovernet(outputs, ground_truth, n_classes=n_classes)

# 4. Configure optimizer
optimizer = torch.optim.Adam(model.parameters(), lr=1e-4, weight_decay=1e-5)

scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer,
    mode='min',
    factor=0.5,
    patience=10
)

# 5. Training loop.
# PanNukeDataModule yields (images, masks, tissue_types) batches; the
# ground-truth tensors required by loss_hovernet (NP / HV / NC targets)
# are derived from the masks. Consult the PanNuke example in the PathML
# docs for the exact unpacking for your version.
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)

num_epochs = 100
for epoch in range(num_epochs):
    model.train()
    train_loss = 0.0
    n_batches = 0

    for images, masks, tissue_type in train_loader:
        images = images.float().to(device)
        ground_truth = masks.to(device)  # see docs for target construction

        optimizer.zero_grad()
        outputs = model(images)
        loss = loss_hovernet(outputs, ground_truth, n_classes=5)
        loss.backward()
        optimizer.step()

        train_loss += loss.item()
        n_batches += 1

    scheduler.step(train_loss)
    print(f"Epoch {epoch+1}/{num_epochs}  Train Loss: {train_loss / max(n_batches, 1):.4f}")

    if (epoch + 1) % 10 == 0:
        torch.save(model.state_dict(), f"hovernet_epoch_{epoch+1}.pth")
```

## Public Datasets

PathML bundles two downloadable DataModules in `pathml.datasets`: `PanNukeDataModule` and `DeepFocusDataModule`. (There is no built-in TCGA DataModule — download TCGA WSIs via the GDC portal and wrap them with `SlideDataset` / `TileDataset`.)

### PanNuke Dataset

**PanNuke** is a multi-tissue histology dataset with nucleus instance + type annotations across several cell categories, commonly used to train HoVer-Net.

```python
from pathml.datasets import PanNukeDataModule

# PanNukeDataModule will download the data to data_dir on first use.
pannuke = PanNukeDataModule(
    data_dir="path/to/pannuke",
    batch_size=16,
    nucleus_type_labels=True,  # include per-nucleus type labels
)

# DataLoaders are exposed as properties (not methods)
train_loader = pannuke.train_dataloader
valid_loader = pannuke.valid_dataloader
test_loader = pannuke.test_dataloader

# Each batch is a tuple: (images, masks, tissue_type)
for images, masks, tissue_type in train_loader:
    ...
```

Confirm the exact constructor arguments and batch tuple layout against the API docs for your installed version.

### Custom Dataset Integration

Create custom datasets for PathML workflows:

```python
from torch.utils.data import Dataset
import numpy as np
from pathlib import Path

class CustomPathologyDataset(Dataset):
    def __init__(self, data_dir, transform=None):
        self.data_dir = Path(data_dir)
        self.image_paths = list(self.data_dir.glob('images/*.png'))
        self.transform = transform

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        # Load image
        image_path = self.image_paths[idx]
        image = np.array(Image.open(image_path))

        # Load corresponding annotation
        annot_path = self.data_dir / 'annotations' / f'{image_path.stem}.npy'
        annotation = np.load(annot_path)

        # Apply transforms
        if self.transform:
            image = self.transform(image)

        return {
            'image': torch.from_numpy(image).permute(2, 0, 1).float(),
            'annotation': torch.from_numpy(annotation).long(),
            'path': str(image_path)
        }

# Use in PathML workflow
dataset = CustomPathologyDataset('path/to/data')
dataloader = DataLoader(dataset, batch_size=16, shuffle=True, num_workers=4)
```

## Data Augmentation

Apply augmentations to improve model generalization:

```python
import albumentations as A
from albumentations.pytorch import ToTensorV2

# Define augmentation pipeline
train_transform = A.Compose([
    A.RandomRotate90(p=0.5),
    A.Flip(p=0.5),
    A.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1, p=0.5),
    A.GaussianBlur(blur_limit=(3, 7), p=0.3),
    A.ElasticTransform(alpha=1, sigma=50, alpha_affine=50, p=0.3),
    A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ToTensorV2()
])

val_transform = A.Compose([
    A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ToTensorV2()
])

# Apply augmentations inside your Dataset's __getitem__ (e.g. the
# CustomPathologyDataset above), or wrap a TileDataset and transform each
# tile before returning it. Pass the transform to whichever Dataset you use.
```

## Model Evaluation

### Metrics

Standard nucleus-segmentation metrics — Dice, Aggregated Jaccard Index (AJI), and Panoptic Quality (PQ = SQ x RQ) — are not bundled as a `pathml.ml.metrics` module. Use a published implementation (e.g. the HoVer-Net authors' `compute_stats` code, or a maintained instance-segmentation metrics package) and feed it the post-processed instance + type maps.

### Evaluation Loop

```python
import torch
from pathml.ml import post_process_batch_hovernet

model.eval()
all_pred_inst, all_pred_type = [], []

with torch.no_grad():
    for images, masks, tissue_type in test_loader:
        images = images.float().to(device)
        outputs = model(images)

        # Post-process the whole batch at once
        inst_map, type_map = post_process_batch_hovernet(outputs, n_classes=5)
        all_pred_inst.append(inst_map)
        all_pred_type.append(type_map)

# Pass all_pred_inst/all_pred_type plus the ground-truth instance/type maps
# to your chosen AJI / PQ implementation.
```

## ONNX Inference

Deploy models using ONNX for production inference:

### Export to ONNX

```python
import torch
from pathml.ml import HoVerNet

# Load trained model and weights
model = HoVerNet(n_classes=5)
model.load_state_dict(torch.load("hovernet_epoch_100.pth"))
model.eval()

# Create dummy input
dummy_input = torch.randn(1, 3, 256, 256)

# Export to ONNX
torch.onnx.export(
    model,
    dummy_input,
    'hovernet_model.onnx',
    export_params=True,
    opset_version=11,
    input_names=['input'],
    output_names=['np_output', 'hv_output', 'nc_output'],
    dynamic_axes={
        'input': {0: 'batch_size'},
        'np_output': {0: 'batch_size'},
        'hv_output': {0: 'batch_size'},
        'nc_output': {0: 'batch_size'}
    }
)
```

### ONNX Runtime Inference

```python
import onnxruntime as ort
import numpy as np

# Load ONNX model
session = ort.InferenceSession('hovernet_model.onnx')

# Prepare input
input_name = session.get_inputs()[0].name
tile_image = preprocess_tile(tile)  # Normalize, transpose to (1, 3, H, W)

# Run inference
outputs = session.run(None, {input_name: tile_image})

# Post-process with PathML's batch post-processor (rebuild the tensor
# structure it expects from the ONNX outputs first)
from pathml.ml import post_process_batch_hovernet
inst_map, type_map = post_process_batch_hovernet(outputs, n_classes=5)
```

### Batch Inference Pipeline

```python
from pathml.core import HESlide
from pathml.ml import post_process_batch_hovernet
import onnxruntime as ort

def run_onnx_inference_pipeline(slide_path, onnx_model_path):
    wsi = HESlide(slide_path)
    session = ort.InferenceSession(onnx_model_path)
    input_name = session.get_inputs()[0].name

    results = []
    for tile in wsi.generate_tiles(level=1, shape=256, stride=256):
        tile_array = preprocess_tile(tile.image)  # normalize -> (1, 3, H, W)
        outputs = session.run(None, {input_name: tile_array})
        inst_map, type_map = post_process_batch_hovernet(outputs, n_classes=5)
        results.append({
            "coords": tile.coords,
            "instance_map": inst_map,
            "type_map": type_map,
        })
    return results

results = run_onnx_inference_pipeline("slide.svs", "hovernet_model.onnx")
```

## Transfer Learning

Fine-tune pre-trained models on custom datasets:

```python
from pathml.ml import HoVerNet

# Load a model and a pretrained checkpoint
model = HoVerNet(n_classes=5)
model.load_state_dict(torch.load("pretrained_hovernet.pth"))

# Freeze encoder layers for initial training
for name, param in model.named_parameters():
    if 'encoder' in name:
        param.requires_grad = False

# Fine-tune only decoder and classification heads
optimizer = torch.optim.Adam(
    filter(lambda p: p.requires_grad, model.parameters()),
    lr=1e-4
)

# Train for a few epochs
train_for_n_epochs(model, train_loader, optimizer, num_epochs=10)

# Unfreeze all layers for full fine-tuning
for param in model.parameters():
    param.requires_grad = True

# Continue training with lower learning rate
optimizer = torch.optim.Adam(model.parameters(), lr=1e-5)
train_for_n_epochs(model, train_loader, optimizer, num_epochs=50)
```

## Best Practices

1. **Use pre-trained weights when available:**
   - Load a published checkpoint with `model.load_state_dict(...)` for better initialization
   - Fine-tune on domain-specific data

2. **Apply appropriate data augmentation:**
   - Rotate, flip for orientation invariance
   - Color jitter to handle staining variations
   - Elastic deformation for biological variability

3. **Monitor multiple metrics:**
   - Track detection, segmentation, and classification separately
   - Use domain-specific metrics (AJI, PQ) beyond standard accuracy

4. **Handle class imbalance:**
   - Weighted loss functions for rare cell types
   - Oversampling minority classes
   - Focal loss for hard examples

5. **Validate on diverse tissue types:**
   - Ensure generalization across different tissues
   - Test on held-out anatomical sites

6. **Optimize for inference:**
   - Export to ONNX for faster deployment
   - Batch tiles for efficient GPU utilization
   - Use mixed precision (FP16) when possible

7. **Save checkpoints regularly:**
   - Keep best model based on validation metrics
   - Save optimizer state for training resumption

## Common Issues and Solutions

**Issue: Poor segmentation at nucleus boundaries**
- Use HV maps (horizontal-vertical) to separate touching nuclei
- Increase weight of HV loss term
- Apply morphological post-processing

**Issue: Misclassification of similar cell types**
- Increase classification loss weight
- Add hierarchical classification (HACTNet)
- Augment training data for confused classes

**Issue: Training unstable or not converging**
- Reduce learning rate
- Use gradient clipping: `torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)`
- Check for data preprocessing issues

**Issue: Out of memory during training**
- Reduce batch size
- Use gradient accumulation
- Enable mixed precision training: `torch.cuda.amp`

**Issue: Model overfits to training data**
- Increase data augmentation
- Add dropout layers
- Reduce model capacity
- Use early stopping based on validation loss

## Additional Resources

- **PathML ML API:** https://pathml.readthedocs.io/en/latest/api_ml_reference.html
- **HoVer-Net Paper:** Graham et al., "HoVer-Net: Simultaneous Segmentation and Classification of Nuclei in Multi-Tissue Histology Images," Medical Image Analysis, 2019
- **PanNuke Dataset:** https://warwick.ac.uk/fac/cross_fac/tia/data/pannuke
- **PyTorch Lightning:** https://www.pytorchlightning.ai/
- **ONNX Runtime:** https://onnxruntime.ai/
