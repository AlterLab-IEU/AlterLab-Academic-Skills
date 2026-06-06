# ETE Toolkit — Newick Format Reference & Best Practices

## Newick Format Reference

ETE supports multiple Newick format specifications (0-100):

- **Format 0**: Flexible with branch lengths (default)
- **Format 1**: With internal node names
- **Format 2**: With bootstrap/support values
- **Format 5**: Internal node names + branch lengths
- **Format 8**: All features (names, distances, support)
- **Format 9**: Leaf names only
- **Format 100**: Topology only

Specify format when reading/writing:

```python
tree = Tree("tree.nw", format=1)
tree.write(outfile="output.nw", format=5)
```

NHX (New Hampshire eXtended) format preserves custom features:

```python
tree.write(outfile="tree.nhx", features=["habitat", "temperature", "depth"])
```

## Best Practices

1. **Preserve branch lengths**: Use `preserve_branch_length=True` when pruning for phylogenetic analysis
2. **Cache content**: Use `get_cached_content()` for repeated access to node contents on large trees
3. **Use iterators**: Employ `iter_*` methods for memory-efficient processing of large trees
4. **Choose appropriate traversal**: Postorder for bottom-up analysis, preorder for top-down
5. **Validate monophyly**: Always check returned clade type (monophyletic/paraphyletic/polyphyletic)
6. **Vector formats for publication**: Use PDF or SVG for publication figures (scalable, editable)
7. **Interactive testing**: Use `tree.show()` to test visualizations before rendering to file
8. **PhyloTree for phylogenetics**: Use PhyloTree class for gene trees and evolutionary analysis
9. **Copy method selection**: "newick" for speed, "cpickle" for full fidelity, "deepcopy" for complex objects
10. **NCBI query caching**: Store NCBI taxonomy query results to avoid repeated database access
