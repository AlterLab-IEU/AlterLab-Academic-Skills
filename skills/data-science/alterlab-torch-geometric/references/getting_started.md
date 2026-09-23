# PyG: Getting Started and Core Concepts

Installation, basic graph creation, the `Data` structure, edge-index format, and mini-batching.

## Installation

```bash
uv pip install torch_geometric
```

PyG 2.8 (current 2.8.0.post1) needs Python >= 3.10; its release notes list PyTorch 2.9–2.12.

Optional compiled extensions — `pyg-lib` provides neighbor sampling (`NeighborLoader`),
`knn_graph`/`radius_graph`, `fps`, and segment ops. Since PyG 2.8 it also replaces
`torch-cluster` and `torch-spline-conv`, which are no longer used:
```bash
# TORCH = your torch version (e.g. 2.12.0), CUDA = cpu | cu126 | cu128 | cu130 | cu132
uv pip install pyg-lib -f https://data.pyg.org/whl/torch-${TORCH}+${CUDA}.html

# torch-scatter / torch-sparse are optional and only published for older torch builds
# (up to 2.12 as of 2026-09):
uv pip install torch-scatter torch-sparse -f https://data.pyg.org/whl/torch-${TORCH}+${CUDA}.html
```
Check what was picked up with `torch_geometric.typing.WITH_PYG_LIB` (and `WITH_TORCH_SPARSE`).

## Basic Graph Creation

```python
import torch
from torch_geometric.data import Data

# Create a simple graph with 3 nodes
edge_index = torch.tensor([[0, 1, 1, 2],  # source nodes
                           [1, 0, 2, 1]], dtype=torch.long)  # target nodes
x = torch.tensor([[-1], [0], [1]], dtype=torch.float)  # node features

data = Data(x=x, edge_index=edge_index)
print(f"Nodes: {data.num_nodes}, Edges: {data.num_edges}")
```

## Loading a Benchmark Dataset

```python
from torch_geometric.datasets import Planetoid

# Load Cora citation network
dataset = Planetoid(root='/tmp/Cora', name='Cora')
data = dataset[0]  # Get the first (and only) graph

print(f"Dataset: {dataset}")
print(f"Nodes: {data.num_nodes}, Edges: {data.num_edges}")
print(f"Features: {data.num_node_features}, Classes: {dataset.num_classes}")
```

## Data Structure

PyG represents graphs using the `torch_geometric.data.Data` class with these key attributes:

- **`data.x`**: Node feature matrix `[num_nodes, num_node_features]`
- **`data.edge_index`**: Graph connectivity in COO format `[2, num_edges]`
- **`data.edge_attr`**: Edge feature matrix `[num_edges, num_edge_features]` (optional)
- **`data.y`**: Target labels for nodes or graphs
- **`data.pos`**: Node spatial positions `[num_nodes, num_dimensions]` (optional)
- **Custom attributes**: Can add any attribute (e.g., `data.train_mask`, `data.batch`)

**Important**: These attributes are not mandatory—extend Data objects with custom attributes as needed.

## Edge Index Format

Edges are stored in COO (coordinate) format as a `[2, num_edges]` tensor:
- First row: source node indices
- Second row: target node indices

```python
# Edge list: (0→1), (1→0), (1→2), (2→1)
edge_index = torch.tensor([[0, 1, 1, 2],
                           [1, 0, 2, 1]], dtype=torch.long)
```

## Mini-Batch Processing

PyG handles batching by creating block-diagonal adjacency matrices, concatenating multiple graphs into one large disconnected graph:

- Adjacency matrices are stacked diagonally
- Node features are concatenated along the node dimension
- A `batch` vector maps each node to its source graph
- No padding needed—computationally efficient

```python
from torch_geometric.loader import DataLoader

loader = DataLoader(dataset, batch_size=32, shuffle=True)
for batch in loader:
    print(f"Batch size: {batch.num_graphs}")
    print(f"Total nodes: {batch.num_nodes}")
    # batch.batch maps nodes to graphs
```
