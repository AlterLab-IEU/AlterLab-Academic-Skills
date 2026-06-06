# ETE Toolkit — Installation, Setup & Troubleshooting

## Installation

```bash
# Basic installation
uv pip install ete3

# With external dependencies for rendering (optional but recommended)
# On macOS:
brew install qt@5

# On Ubuntu/Debian:
sudo apt-get install python3-pyqt5 python3-pyqt5.qtsvg

# For full features including GUI
uv pip install ete3[gui]
```

## First-time NCBI Taxonomy setup

The first time `NCBITaxa` is instantiated, it automatically downloads the NCBI taxonomy
database (~300MB) to `~/.etetoolkit/taxa.sqlite`. This happens only once:

```python
from ete3 import NCBITaxa
ncbi = NCBITaxa()  # Downloads database on first run
```

Update taxonomy database:

```python
ncbi.update_taxonomy_database()  # Download latest NCBI data
```

## Troubleshooting

### Import errors

```bash
# If "ModuleNotFoundError: No module named 'ete3'"
uv pip install ete3

# For GUI and rendering issues
uv pip install ete3[gui]
```

### Rendering issues

If `tree.render()` or `tree.show()` fails with Qt-related errors, install system dependencies:

```bash
# macOS
brew install qt@5

# Ubuntu/Debian
sudo apt-get install python3-pyqt5 python3-pyqt5.qtsvg
```

### NCBI Taxonomy database

If database download fails or becomes corrupted:

```python
from ete3 import NCBITaxa
ncbi = NCBITaxa()
ncbi.update_taxonomy_database()  # Redownload database
```

### Memory issues with large trees

For very large trees (>10,000 leaves), use iterators instead of list comprehensions:

```python
# Memory-efficient iteration
for leaf in tree.iter_leaves():
    process(leaf)

# Instead of
for leaf in tree.get_leaves():  # Loads all into memory
    process(leaf)
```
