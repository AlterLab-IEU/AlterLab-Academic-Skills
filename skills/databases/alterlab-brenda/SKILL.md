---
name: alterlab-brenda
description: Access the BRENDA enzyme database via its SOAP API to retrieve kinetic parameters (Km, kcat, Ki), reaction equations, organism data, and substrate-specific enzyme information indexed by EC number. Use when looking up enzyme kinetics, turnover numbers, or substrate specificity for biochemical research and metabolic pathway analysis. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read WebFetch Bash(curl:*) Bash(python:*)
compatibility: Requires free BRENDA account credentials (BRENDA_EMAIL/BRENDA_PASSWORD) for the SOAP API
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# BRENDA Database

## Overview

BRENDA (BRaunschweig ENzyme DAtabase) is the world's most comprehensive enzyme information
system, containing detailed enzyme data from scientific literature. Query kinetic parameters
(Km, kcat), reaction equations, substrate specificities, organism information, and optimal
conditions for enzymes using the official SOAP API. Access over 45,000 enzymes with millions
of kinetic data points for biochemical research, metabolic engineering, and enzyme discovery.

## When to Use This Skill

This skill should be used when:
- Searching for enzyme kinetic parameters (Km, kcat, Vmax)
- Retrieving reaction equations and stoichiometry
- Finding enzymes for specific substrates or reactions
- Comparing enzyme properties across different organisms
- Investigating optimal pH, temperature, and conditions
- Accessing enzyme inhibition and activation data
- Supporting metabolic pathway reconstruction and retrosynthesis
- Performing enzyme engineering and optimization studies
- Analyzing substrate specificity and cofactor requirements

## Core Capabilities

BRENDA access is organized into nine capability areas. Copy-ready snippets for each live in
`references/capabilities.md`.

1. **Kinetic parameter retrieval** — Km, kcat, Vmax by EC number / organism / substrate.
2. **Reaction information** — reaction equations and stoichiometry.
3. **Enzyme discovery** — find enzymes by substrate, product, or reaction pattern.
4. **Organism-specific data** — compare enzyme properties across organisms.
5. **Environmental parameters** — optimal/stability pH and temperature, cofactors.
6. **Substrate specificity** — Km/Vmax/kcat per substrate, affinity ranking.
7. **Inhibition and activation** — Ki, IC50, activators and mechanisms.
8. **Enzyme engineering support** — thermophilic homologs, pH-stable variants.
9. **Kinetic modeling** — modeling parameters and Michaelis-Menten plots.

## Core Workflow

The typical entry point retrieves kinetic data by EC number, then parses the delimited
response:

```python
from scripts.brenda_client import get_km_values
from scripts.brenda_queries import parse_km_entry

km_data = get_km_values("1.1.1.1", organism="Saccharomyces cerevisiae")
for entry in km_data:
    parsed = parse_km_entry(entry)
    # parse_km_entry keys mirror the raw BRENDA fields: 'kmValue' (string)
    # plus a derived 'km_value_numeric' (float). There is no 'km_value' key.
    print(parsed.get("organism"), parsed.get("substrate"), parsed.get("km_value_numeric"))
```

EC numbers must be fully qualified (e.g. `1.1.1.1`, not `1.1.1`). Wildcards (`*`) broaden
searches. See `references/data_formats.md` for the response format and parsing helpers.

## Installation Requirements

```bash
uv pip install zeep requests pandas matplotlib seaborn
```

## Authentication Setup

BRENDA requires authentication credentials:

1. **Create .env file**:
```
BRENDA_EMAIL=your.email@example.com
BRENDA_PASSWORD=your_brenda_password
```

2. **Or set environment variables**:
```bash
export BRENDA_EMAIL="your.email@example.com"
export BRENDA_PASSWORD="your_brenda_password"
```

3. **Register for BRENDA access**:
   - Visit https://www.brenda-enzymes.org/
   - Create an account
   - Check your email for credentials
   - Note: There's also `BRENDA_EMIAL` (note the typo) for legacy support

## Helper Scripts

This skill ships three Python helper scripts under `scripts/`:

- `scripts/brenda_queries.py` — high-level enzyme data analysis (parsing, search, cross-organism
  comparison, environmental parameters, specificity, inhibitors/activators, engineering targets).
- `scripts/brenda_visualization.py` — kinetic/pH/temperature/substrate plots and Michaelis-Menten curves.
- `scripts/enzyme_pathway_builder.py` — enzymatic pathway and retrosynthetic route construction.

Full function inventories and usage are in `references/helper_scripts.md`.

## Reference Index

- **`references/api_reference.md`** — Complete SOAP API method docs, parameter lists/formats,
  EC number structure/validation, response specs, error codes, literature citation formats.
- **`references/capabilities.md`** — Copy-ready code for all nine capability areas.
- **`references/workflows.md`** — Six end-to-end workflows (discovery, cross-organism comparison,
  engineering targets, pathway construction, kinetic analysis, industrial selection).
- **`references/helper_scripts.md`** — Function inventory and usage for the three helper scripts.
- **`references/data_formats.md`** — BRENDA response formats, parsing patterns, rate limits,
  error handling, troubleshooting, and additional resources.
