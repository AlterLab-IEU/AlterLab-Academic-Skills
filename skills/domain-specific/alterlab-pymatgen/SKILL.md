---
name: alterlab-pymatgen
description: Analyzes and manipulates materials with the pymatgen toolkit — crystal structures and molecules, phase diagrams and thermodynamic stability, electronic structure (band structures, DOS), surfaces and interfaces, and Materials Project data access. Use when working with crystal structures in materials science, converting between structure formats (CIF, POSCAR, XYZ), analyzing symmetry or space groups, computing phase diagrams, querying Materials Project data (keyless via its OPTIMADE endpoint, or the richer MP API with a key), or handling VASP, Gaussian, or Quantum ESPRESSO output. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*) Bash(uv run:*)
compatibility: "No API key required: pymatgen analyses local structures (CIF/POSCAR/XYZ, symmetry/space groups, slabs, VASP/Gaussian output) offline under `uv run python`, and fetches Materials Project structures and precomputed stability (energy above hull) via the keyless OPTIMADE endpoint. The richer MP API — full computed entries, convex-hull plots, decomposition products — is optional and uses a free MP_API_KEY."
metadata:
    skill-author: AlterLab
    credentials: "optional: MP_API_KEY (the richer Materials Project MP API — full computed entries, convex-hull plots, decomposition, chemical potentials; structure and stability fetches work keyless via the MP OPTIMADE endpoint)"
    version: "1.2.0"
    last_updated: "2026-09-23"
---

# Pymatgen - Python Materials Genomics

## Overview

Pymatgen is a comprehensive Python library for materials analysis that powers the
Materials Project. Create, analyze, and manipulate crystal structures and molecules;
compute phase diagrams and thermodynamic properties; analyze electronic structure (band
structures, DOS); generate surfaces and interfaces; and access the Materials Project
database. Supports 100+ file formats from various computational codes.

## When to Use This Skill

Use when:
- Working with crystal structures or molecular systems in materials science
- Converting between structure file formats (CIF, POSCAR, XYZ, etc.)
- Analyzing symmetry, space groups, or coordination environments
- Computing phase diagrams or assessing thermodynamic stability
- Analyzing electronic structure (band gaps, DOS, band structures)
- Generating surfaces/slabs or studying interfaces
- Accessing the Materials Project database programmatically
- Setting up high-throughput computational workflows
- Working with VASP, Gaussian, Quantum ESPRESSO, or other codes

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Small organic molecules — SMILES, fingerprints, descriptors, substructure search | `alterlab-rdkit` |
| Running DFT / conformer searches / pKa in a managed cloud quantum-chemistry service | `alterlab-rowan` |
| Classical molecular dynamics of proteins or ligands (OpenMM, trajectories) | `alterlab-molecular-dynamics` |
| Variational quantum circuits for molecular ground states (VQE) | `alterlab-pennylane` |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-rdkit`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

## Quick Start

Run install-free — one `uv run` command, no virtualenv and no `uv pip install` (which fails
outside an activated virtualenv). pymatgen needs Python >= 3.11 and uv's default here can be
3.9, so pin the interpreter. The bundled scripts run the same way:

```bash
uv run --python ">=3.11" --with pymatgen python your_script.py
uv run --python ">=3.11" --with pymatgen python scripts/phase_diagram_generator.py Li-Fe-O --analyze LiFeO2   # keyless
uv run --python ">=3.11" --with pymatgen --with mp-api python your_script.py    # + optional MP API client
```

Add a single analysis dependency with another `--with` (`--with phonopy`, `--with seekpath`,
`--with ase`) rather than the `pymatgen[optional]` extra, which now pulls matgl and a full
PyTorch/CUDA stack. Inside an activated virtualenv `uv pip install pymatgen` works too.

```python
from pymatgen.core import Structure, Lattice

struct = Structure.from_file("POSCAR")        # auto format detection
struct.to(filename="structure.cif")           # write any format
print(struct.composition.reduced_formula)
print(struct.get_space_group_info())
print(f"{struct.density:.2f} g/cm³")
```

**Keyless by default.** Everything above — reading, converting, and analysing structures
you provide (CIF/POSCAR/XYZ), symmetry and space groups, slab generation, phase stability,
and parsing VASP/Gaussian/QE output — is local and needs no account. To *fetch* structures
and their stability from Materials Project without a key, use the keyless **OPTIMADE**
endpoint (see "Materials Project access" below). Only the richer MP API (full computed
entries and convex-hull plots) needs a key:

```bash
export MP_API_KEY="your_api_key_here"   # OPTIONAL — only for the richer mp-api client
```

## Core Capabilities (routing)

Each capability has a copy-paste code block in `references/core_examples.md` and deeper
module docs in the references listed below.

1. **Structure creation & manipulation** — from files, from scratch (lattice params or
   space group), transformations (supercell, substitution, primitive). → `core_classes.md`
2. **File-format conversion** — `from_file()`/`to()` plus `scripts/structure_converter.py`
   for single/batch. → `io_formats.md`
3. **Structure analysis & symmetry** — `SpacegroupAnalyzer`, `CrystalNN`, plus
   `scripts/structure_analyzer.py`. → `analysis_modules.md`
4. **Phase diagrams & thermodynamics** — `PhaseDiagram`, energy-above-hull, decomposition,
   plus `scripts/phase_diagram_generator.py`. → `analysis_modules.md`, `transformations_workflows.md`
5. **Electronic structure** — band structures and DOS from `Vasprun`, band gaps,
   metallicity. → `analysis_modules.md`, `io_formats.md`
6. **Surfaces & interfaces** — `SlabGenerator`, `WulffShape`, `AdsorbateSiteFinder`.
   → `analysis_modules.md`, `transformations_workflows.md`
7. **Materials Project access** — **keyless default:** the MP OPTIMADE endpoint
   (`https://optimade.materialsproject.org/v1/structures`, no API key) for structures and
   precomputed stability (`_mp_stability`: energy above hull, formation energy); the
   `optimade` Python client (`OptimadeClient`, with its `[http-client]` extra) or plain
   `urllib` both work, and `optimade.adapters.Structure` converts a result to a pymatgen
   `Structure`. **Optional:** `MPRester` (the `mp-api` client, needs `MP_API_KEY`) for the
   full computed entries, richer property filters, and convex-hull plots.
   → `materials_project_api.md`
8. **Computational workflow setup** — VASP input sets (`MPRelaxSet`, `MPStaticSet`,
   `MPNonSCFSet`), Gaussian, Quantum ESPRESSO. → `io_formats.md`, `transformations_workflows.md`
9. **Advanced analysis** — XRD patterns, elastic tensors, magnetic ordering.
   → `analysis_modules.md`

Multi-step worked examples (high-throughput generation, band-structure pipeline, surface
energy): `references/common_workflows_code.md`.

## Bundled Resources

### Scripts (`scripts/`)

The scripts import pymatgen, so run each as `uv run --python ">=3.11" --with pymatgen python
scripts/<name>.py ...` (bare `python scripts/...`, as written below, works only where
pymatgen is already installed).

- **`structure_converter.py`**: convert between structure file formats (batch + auto
  detection). Usage: `python scripts/structure_converter.py POSCAR structure.cif`
- **`structure_analyzer.py`**: symmetry, coordination, lattice parameters, distance
  matrix. Usage: `python scripts/structure_analyzer.py structure.cif --symmetry --neighbors`
- **`phase_diagram_generator.py`**: phase-stability report. **Keyless by default** —
  `python scripts/phase_diagram_generator.py Li-Fe-O --analyze "LiFeO2"` pulls precomputed
  stability from the MP OPTIMADE endpoint (no key) and reports whether the composition is
  on the convex hull. Add `--source mp` (needs `MP_API_KEY`) for the full `PhaseDiagram`
  with a convex-hull plot and decomposition products; without the key that path exits
  non-zero and points back to the keyless default rather than silently switching backends.

All scripts include detailed help, e.g. `python scripts/structure_converter.py --help`

### References (`references/`)

- **`core_examples.md`**: copy-paste code for all nine core capabilities
- **`common_workflows_code.md`**: multi-step worked workflow code
- **`core_classes.md`**: Element, Structure, Lattice, Molecule, Composition classes
- **`io_formats.md`**: file-format support and code integration (VASP, Gaussian, etc.)
- **`analysis_modules.md`**: phase diagrams, surfaces, electronic structure, symmetry
- **`materials_project_api.md`**: complete Materials Project API guide
- **`transformations_workflows.md`**: transformations framework and 10 common workflows

## Best Practices

**Structures**: use auto format detection; prefer `IStructure` when immutable; reduce to
primitive cell with `SpacegroupAnalyzer`; validate for overlapping atoms / bad bond
lengths. **File I/O**: prefer `from_file()`/`to()`; specify format when detection fails;
use `as_dict()`/`from_dict()` for version-safe storage. **MP API**: always use the context
manager; batch queries; cache results; filter by property. **Workflows**: prefer input
sets over manual INCAR; verify convergence; track transformations for provenance.
**Performance**: use primitive cells; bound neighbor-search cutoffs; parallelize where
possible.

## Units and Conventions

Lengths in Å, energies in eV, angles in degrees, magnetic moments in μB, time in fs.
Convert with `pymatgen.core.units`.

## Integration

Integrates with ASE, Phonopy, BoltzTraP, Atomate/Fireworks, AiiDA, Zeo++, and OpenBabel.

## Troubleshooting

- **Import errors**: add the missing package to the run, e.g. `uv run --python ">=3.11" --with pymatgen --with phonopy python ...` (there is no `[analysis]` extra; `[optional]` pulls PyTorch/CUDA via matgl)
- **No MP_API_KEY / don't want an account**: use the keyless OPTIMADE endpoint for
  structures and stability (`scripts/phase_diagram_generator.py` defaults to it); only the
  `mp-api` client needs `export MP_API_KEY="your_key_here"`
- **Structure read failures**: try explicit format, e.g. `Structure.from_file("file.txt", fmt="cif")`
- **Symmetry analysis fails**: increase tolerance, e.g. `SpacegroupAnalyzer(struct, symprec=0.1)`

## Additional Resources

Docs: https://pymatgen.org/ · Materials Project: https://materialsproject.org/ ·
GitHub: https://github.com/materialsproject/pymatgen · Forum: https://matsci.org/ ·
Example notebooks: https://github.com/materialsvirtuallab/matgenb

## Version Notes

Designed for pymatgen 2024.x and later (current 2026.9.x as of 2026-09; calendar
versioning). Since 2026 the `pymatgen` distribution is a thin package on top of
`pymatgen-core`; imports (`pymatgen.core`, `pymatgen.io.vasp`, …) are unchanged. For the
Materials Project API use the `mp-api` package (current 0.46.x; `from mp_api.client import
MPRester`) rather than the legacy `pymatgen.ext.matproj` client. Requirements: Python ≥ 3.11,
pymatgen ≥ 2024.x, mp-api for Materials Project access.

Part of the AlterLab Academic Skills suite.
