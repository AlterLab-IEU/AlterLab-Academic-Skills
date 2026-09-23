---
name: alterlab-etetoolkit
description: Manipulate, annotate, and render phylogenetic trees programmatically with the ETE Toolkit (ete3) — parse and edit Newick/NHX, detect duplication/speciation events, infer orthology and paralogy, query NCBI taxonomy, and export PDF/SVG figures. Use when traversing or reformatting tree files, doing phylogenomic comparative analysis, or producing publication tree graphics in Python. Part of the AlterLab Academic Skills suite.
license: GPL-3.0
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*)
compatibility: "Self-contained — runs under `uv run python`. Examples target **ete3 3.1.3** (the last ete3 release, May 2023); `Tree.render()`/`show()` additionally need PyQt5. The maintained line is **ete4 4.4.0**, whose API differs (see the version note in the body). NCBITaxa downloads a ~300MB taxonomy database on first use. No API key or account required."
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# ETE Toolkit Skill

## Overview

ETE (Environment for Tree Exploration) is a toolkit for phylogenetic and hierarchical
tree analysis. Manipulate trees, analyze evolutionary events, visualize results, and
integrate with biological databases for phylogenomic research and clustering analysis.

## ete3 or ete4?

The examples in this skill and its references are written for **ete3 3.1.3**, which is
still what most published pipelines import — but ete3 has had no release since May 2023,
and **ete4 (4.4.0, Sept 2025)** is the maintained line. Port deliberately: the ete4 API is
not drop-in.

| ete3 | ete4 |
|------|------|
| `from ete3 import Tree` | `from ete4 import Tree` |
| `Tree("t.nw", format=1)` | `Tree(open("t.nw"), parser=1)` — the keyword is `parser` |
| `tree.iter_leaves()` / `get_leaves()` | `tree.leaves()` |
| custom features via `node.add_feature()` | `node.props[...]` dictionary |
| Qt-based `show()` / `render()` (needs PyQt5) | browser-based `explore()` with adaptive zoom, plus GTDB taxonomy support |

Check which one is installed before writing code (`python -c "import ete4"`), and say which
you targeted in the methods.

## When to Use

- Parsing, traversing, or reformatting tree files (Newick / NHX / PhyloXML / NeXML)
- Pruning, rooting, collapsing, or resolving polytomies in a tree
- Detecting duplication/speciation events and inferring orthologs/paralogs from gene trees
- Querying NCBI Taxonomy (taxid/name translation, lineages, taxonomy trees)
- Producing publication-quality PDF/SVG/PNG tree figures
- Comparing trees (Robinson-Foulds) or analyzing clustering dendrograms

## Core Capabilities

ETE exposes six capability areas. Each has detailed, copy-ready code in the references
(see Index below).

1. **Tree manipulation** — I/O across formats, traversal (pre/post/levelorder), topology
   edits (prune, root, collapse), distances, RF tree comparison.
2. **Phylogenetic analysis** — alignment linkage, species naming, duplication/speciation
   detection (Species Overlap or reconciliation), orthology/paralogy.
3. **NCBI Taxonomy** — local cached DB, taxid↔name translation, lineage retrieval,
   taxonomy-tree building, tree annotation.
4. **Visualization** — PNG/PDF/SVG export, rectangular/circular layouts, `NodeStyle`,
   `Face` objects, layout functions, interactive GUI.
5. **Clustering analysis** — `ClusterTree`, data-matrix linking, silhouette/Dunn metrics,
   heatmap views.
6. **Tree comparison** — Robinson-Foulds (raw + normalized), partition/bipartition analysis,
   batch pairwise distance matrices.

## Core Workflow

The canonical minimal pattern — load, edit, save:

```python
from ete3 import Tree

# Load tree from file (format 1 = with internal node names)
tree = Tree("tree.nw", format=1)

# Prune to taxa of interest, preserving branch lengths
tree.prune(["species1", "species2", "species3"], preserve_branch_length=True)

# Midpoint root
tree.set_outgroup(tree.get_midpoint_outgroup())

# Save
tree.write(outfile="rooted_tree.nw")
```

For class selection: use `Tree`/`TreeNode` for generic topology work, `PhyloTree` for gene
trees and evolutionary analysis, `ClusterTree` for dendrograms with data matrices, and
`NCBITaxa` for taxonomy queries.

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Build a tree from unaligned sequences (align + model selection + ML inference) | `alterlab-phylogenetics` |
| Distance matrices, diversity metrics, or ordination from alignments | `alterlab-scikit-bio` |
| Tree I/O inside a broader Biopython pipeline (`Bio.Phylo`) | `alterlab-biopython` |
| Generic graph algorithms on a non-tree network | `alterlab-networkx` |
| Taxonomic classification of amplicon reads | `alterlab-qiime2-amplicon` |

## Command-Line Scripts

- `scripts/tree_operations.py` — stats, format conversion, rerooting, pruning, ASCII view.
  Example: `python scripts/tree_operations.py reroot tree.nw rooted.nw --midpoint`
- `scripts/quick_visualize.py` — rapid PDF/PNG rendering with circular layout, support
  coloring, and DPI control. Example:
  `python scripts/quick_visualize.py tree.nw out.pdf --mode c --color-by-support`

## Reference Index

Load the relevant file when detailed information is needed:

- **`references/api_reference.md`** — Complete API for all ETE classes/methods (`Tree`,
  `PhyloTree`, `ClusterTree`, `NCBITaxa`): parameters, return types, code examples.
- **`references/workflows.md`** — Per-task workflow patterns (tree operations, phylogenetic
  analysis, comparison, taxonomy integration, clustering).
- **`references/visualization.md`** — Full visualization guide: `TreeStyle`, `NodeStyle`,
  `Face`s, layout functions, advanced rendering.
- **`references/use_cases.md`** — End-to-end worked use cases (phylogenomic pipeline, batch
  preprocessing, publication figures, automated multi-tree analysis).
- **`references/setup_and_troubleshooting.md`** — Installation, NCBI Taxonomy first-run
  setup, and troubleshooting (imports, Qt rendering, memory, DB corruption).
- **`references/newick_and_best_practices.md`** — Newick/NHX format specifications (0-100)
  and best-practice checklist.

Part of the AlterLab Academic Skills suite.
