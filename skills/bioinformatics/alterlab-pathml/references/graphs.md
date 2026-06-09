# Graph Construction & Spatial Analysis

## Overview

PathML provides tools for constructing spatial graphs from tissue images to represent cellular and tissue-level relationships. Graph-based representations enable sophisticated spatial analysis, including neighborhood analysis, cell-cell interaction studies, and graph neural network applications. These graphs capture both morphological features and spatial topology for downstream computational analysis.

## Graph Types

PathML supports construction of multiple graph types:

### Cell Graphs
- Nodes represent individual cells
- Edges represent spatial proximity or biological interactions
- Node features include morphology, marker expression, cell type
- Suitable for single-cell spatial analysis

### Tissue Graphs
- Nodes represent tissue regions or superpixels
- Edges represent spatial adjacency
- Node features include tissue composition, texture features
- Suitable for tissue-level spatial patterns

### Spatial Transcriptomics Graphs
- Nodes represent spatial spots or cells
- Edges encode spatial relationships
- Node features include gene expression profiles
- Suitable for spatial omics analysis

## Graph Construction Workflow

PathML's graph module exposes builder classes (subclasses of `BaseGraphBuilder`) rather than a single `CellGraph` factory: `KNNGraphBuilder`, `RAGGraphBuilder` (region-adjacency, for superpixel/tissue graphs), and `MSTGraphBuilder` (minimum spanning tree). Tissue regions for tissue graphs come from the superpixel extractors (`SLICSuperpixelExtractor`, `ColorMergedSuperpixelExtractor`, etc.), and per-node features come from `GraphFeatureExtractor`. Verify class names and call signatures against the API docs for your installed version.

### From Segmentation to Graphs

Convert a cell instance-segmentation mask into a spatial cell graph with a builder. The builder takes the per-cell centroids and a feature matrix and returns a `pathml.graph.utils.Graph` (PyG-compatible) object.

```python
import numpy as np
from skimage.measure import regionprops
from pathml.graph import KNNGraphBuilder
from pathml.preprocessing import Pipeline, SegmentMIF

# 1. Segment cells
pipeline = Pipeline([
    SegmentMIF(model="mesmer", nuclear_channel=0, cytoplasm_channel=29),
])
slide.run(pipeline)

# 2. Get the instance mask and per-cell centroids + features
inst_map = slide.masks["cell_segmentation"]
props = regionprops(inst_map)
centroids = np.array([p.centroid[::-1] for p in props])  # (x, y) per cell
features = np.array([[p.area, p.eccentricity, p.solidity] for p in props])

# 3. Build a k-NN cell graph
builder = KNNGraphBuilder(k=5, thresh=50)  # k neighbors within a distance threshold
graph = builder.process(inst_map, features=features, centroids=centroids)

# 4. Access components (Graph is a torch_geometric-style object)
x = graph.node_features      # node feature matrix
edge_index = graph.edge_index  # (2, n_edges) connectivity
```

### Builder Choices

- `KNNGraphBuilder(k=..., thresh=...)` - connect each node to its k nearest neighbors within an optional distance threshold; good for cell graphs.
- `RAGGraphBuilder` - region-adjacency graph; connects touching regions, suited to superpixel/tissue graphs.
- `MSTGraphBuilder` - minimum spanning tree over node positions; a sparse, fully connected backbone.

For tissue graphs, first extract superpixels (e.g. `SLICSuperpixelExtractor` or `ColorMergedSuperpixelExtractor`), then pass the label map to `RAGGraphBuilder`.

## Node Features

PathML's `GraphFeatureExtractor` computes per-region features from an instance/label map; you can also compute features yourself with scikit-image and pass them to the builder as the `features` matrix.

### Morphological and Intensity Features (scikit-image)

`skimage.measure.regionprops` / `regionprops_table` covers the common morphology and per-channel intensity statistics:

```python
import numpy as np
from skimage.measure import regionprops_table

# Morphology
morph = regionprops_table(
    inst_map,
    properties=["area", "perimeter", "eccentricity", "solidity",
                "axis_major_length", "axis_minor_length", "orientation"],
)

# Per-channel mean intensity (image shape (H, W, C))
intensity = regionprops_table(
    inst_map,
    intensity_image=multichannel_image,
    properties=["intensity_mean"],
)

# Stack into a node feature matrix aligned with the builder's node order
node_features = np.column_stack([np.asarray(v) for v in morph.values()])
```

### Cell Type Annotations as Node Features

Append cell-type labels (e.g. from HoVer-Net) as an extra node-feature column or one-hot block before building the graph:

```python
cell_types = hovernet_type_predictions  # array of per-cell type ids, aligned to props order
onehot = np.eye(n_classes)[cell_types]
node_features = np.column_stack([node_features, onehot])
```

## Spatial Analysis

PathML builds the graph; for downstream spatial statistics (neighborhood enrichment, co-occurrence, interaction tests, spatial autocorrelation) move the per-cell coordinates + labels into AnnData and use **squidpy** — the dedicated, maintained tool for this. (`pathml.graph` does not provide `analyze_neighborhoods`, `spatial_clustering`, `cell_interaction_analysis`, or `spatial_statistics` functions; don't assume they exist.) See `multiparametric.md` for the AnnData-based squidpy workflow.

```python
import anndata as ad
import numpy as np
import squidpy as sq

# Wrap centroids + cell types in AnnData
adata = ad.AnnData(node_features)
adata.obsm["spatial"] = centroids
adata.obs["cell_type"] = cell_type_labels.astype(str)

# Spatial neighbors + neighborhood enrichment
sq.gr.spatial_neighbors(adata, coord_type="generic")
sq.gr.nhood_enrichment(adata, cluster_key="cell_type")
sq.pl.nhood_enrichment(adata, cluster_key="cell_type")
```

For plain spatial clustering of positions, scikit-learn's `DBSCAN`/`KMeans` on `centroids` works directly.

## Integration with Graph Neural Networks

### Convert to PyTorch Geometric Format

The `Graph` returned by a builder is already a `torch_geometric.data.Data`-style object, so it plugs straight into PyTorch Geometric (no conversion helper needed):

```python
import torch
from torch_geometric.nn import GCNConv
from pathml.graph import KNNGraphBuilder

graph = KNNGraphBuilder(k=5, thresh=50).process(inst_map, features=features, centroids=centroids)

x = graph.node_features        # node features
edge_index = graph.edge_index  # (2, n_edges)

class GNN(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels):
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, out_channels)

    def forward(self, data):
        x = self.conv1(data.node_features, data.edge_index).relu()
        return self.conv2(x, data.edge_index)

model = GNN(in_channels=x.shape[1], hidden_channels=64, out_channels=5)
output = model(graph)
```

### Dataset of Graphs for Multiple Slides

Use PathML's `EntityDataset` (from `pathml.datasets`) to serve multiple graphs, or collect them into a list and batch with PyG's `DataLoader`:

```python
from torch_geometric.loader import DataLoader
from pathml.graph import KNNGraphBuilder

builder = KNNGraphBuilder(k=5, thresh=50)
graphs = [
    builder.process(s_inst_map, features=s_features, centroids=s_centroids)
    for (s_inst_map, s_features, s_centroids) in per_slide_inputs
]

loader = DataLoader(graphs, batch_size=32, shuffle=True)
for batch in loader:
    output = model(batch)
    loss = criterion(output, batch.y)
    loss.backward()
    optimizer.step()
```

## Visualization

### Graph Visualization

Draw the graph directly from its `edge_index` and the cell `centroids` (no NetworkX conversion required):

```python
import matplotlib.pyplot as plt

edges = graph.edge_index.cpu().numpy()  # (2, n_edges)

fig, ax = plt.subplots(figsize=(12, 12))
# Edges
for s, d in edges.T:
    p1, p2 = centroids[s], centroids[d]
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], "b-", alpha=0.3, linewidth=0.5)
# Nodes colored by type
ax.scatter(centroids[:, 0], centroids[:, 1], c=cell_type_labels, cmap="tab10", s=20)
ax.set_aspect("equal")
ax.axis("off")
plt.title("Cell Graph")
plt.show()
```

### Overlay on Tissue Image

Same as above but `imshow` the tissue image first, then draw edges/nodes on the same axes using `centroids` in image (x, y) coordinates.

## Complete Workflow Example

```python
import numpy as np
from skimage.measure import regionprops, regionprops_table
from pathml.core import CODEXSlide
from pathml.preprocessing import Pipeline, CollapseRunsCODEX, SegmentMIF
from pathml.graph import KNNGraphBuilder

# 1. Load and preprocess slide
slide = CODEXSlide("path/to/codex", stain="IF")
pipeline = Pipeline([
    CollapseRunsCODEX(z=0),
    SegmentMIF(model="mesmer", nuclear_channel=0, cytoplasm_channel=29),
])
slide.run(pipeline)

# 2. Per-cell centroids + features from the instance mask
inst_map = slide.masks["cell_segmentation"]
props = regionprops(inst_map)
centroids = np.array([p.centroid[::-1] for p in props])  # (x, y)
morph = regionprops_table(
    inst_map, properties=["area", "perimeter", "eccentricity", "solidity"]
)
features = np.column_stack([np.asarray(v) for v in morph.values()])

# 3. Build the cell graph
graph = KNNGraphBuilder(k=6, thresh=50).process(
    inst_map, features=features, centroids=centroids
)

# 4. graph is PyG-ready (graph.node_features, graph.edge_index) -> feed to a GNN
#    For neighborhood/interaction statistics, hand centroids + labels to squidpy
#    (see "Spatial Analysis" above).
```

## Performance Considerations

**Large tissue sections:**
- Build graphs tile-by-tile, then merge
- Use sparse adjacency matrices
- Leverage GPU for feature extraction

**Memory efficiency:**
- Store only necessary edge features
- Use int32/float32 instead of int64/float64
- Batch process multiple slides

**Computational efficiency:**
- Parallelize feature extraction across cells
- Use KNN for faster neighbor queries
- Cache computed features

## Best Practices

1. **Choose an appropriate builder:** `KNNGraphBuilder` for cell graphs (tune `k`/`thresh`), `RAGGraphBuilder` for superpixel/tissue adjacency, `MSTGraphBuilder` for a sparse backbone

2. **Normalize features:** Scale morphological and intensity features for GNN compatibility

3. **Handle edge effects:** Exclude boundary cells or use tissue masks to define valid regions

4. **Validate graph construction:** Visualize graphs on small regions before large-scale processing

5. **Combine multiple feature types:** Morphology + intensity + texture provides rich representations

6. **Consider tissue context:** Tissue type affects appropriate graph parameters (connectivity, radius)

## Common Issues and Solutions

**Issue: Too many/few edges**
- Adjust `k` and the `thresh` distance cutoff on `KNNGraphBuilder`
- Verify pixel-to-micron conversion for biological relevance

**Issue: Memory errors with large graphs**
- Process tiles separately and merge graphs
- Use sparse representations and float32 features

**Issue: Missing cells at tissue boundaries**
- Use tissue masks to exclude invalid regions before building the graph

**Issue: Inconsistent feature scales**
- Normalize features: `(x - mean) / std`
- Use robust scaling for outliers

## Additional Resources

- **PathML Graph API:** https://pathml.readthedocs.io/en/latest/api_graph_reference.html
- **PyTorch Geometric:** https://pytorch-geometric.readthedocs.io/
- **NetworkX:** https://networkx.org/
- **Spatial Statistics:** Baddeley et al., "Spatial Point Patterns: Methodology and Applications with R"
