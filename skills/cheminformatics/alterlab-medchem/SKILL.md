---
name: alterlab-medchem
description: Applies medicinal-chemistry filters with the medchem library — drug-likeness rules (Lipinski, Veber), PAINS filters, structural alerts, and molecular complexity metrics for compound prioritization and library cleanup. Use when filtering or triaging a compound library, flagging PAINS or reactive groups, or assessing drug-likeness of candidate molecules. Part of the AlterLab Academic Skills suite.
license: Apache-2.0
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*)
compatibility: "Self-contained — runs under `uv run python` with the skill's Python package installed; no API key or account required."
metadata:
    skill-author: AlterLab
    version: "1.1.0"
---

# Medchem

## Overview

Medchem (`datamol-io/medchem`) is a Python library for molecular filtering and prioritization in drug-discovery workflows: medicinal-chemistry rules, structural alerts (ChEMBL/NIBR/PAINS), chemical-group detection, complexity metrics, and a query DSL. Rules and filters are context-specific guidelines, not hard truth — combine with domain expertise.

**Verified against `medchem==2.0.5` (RDKit 2026.3.x, Python 3.12).** API names below are checked against this version; earlier docs/blog posts described a different surface.

## When to Use This Skill

This skill should be used when:
- Applying drug-likeness rules (Lipinski, Veber, etc.) to compound libraries
- Filtering molecules by structural alerts or PAINS patterns
- Prioritizing compounds for lead optimization
- Assessing compound quality and medicinal chemistry properties
- Detecting reactive or problematic functional groups
- Calculating molecular complexity metrics

## Installation

```bash
uv pip install medchem    # PyPI; pulls rdkit + datamol
```

Two features need extra native deps that PyPI cannot provide:
- **Lilly demerits** (`lilly_demerit_filter`) shells out to compiled binaries — install via conda: `mamba install -c conda-forge lilly-medchem-rules`. Without them, the call raises `ImportError`.
- The ChemAxon rule (`rule_of_chemaxon_druglikeness`) needs a licensed ChemAxon install.

Everything else (RuleFilters, CommonAlerts, NIBR, complexity, groups, query) works from the PyPI wheel alone.

## Core Capabilities

> **Conventions that hold across medchem.** Filters take `mols` (a sequence of SMILES strings or RDKit mols), default to `n_jobs=-1` (all cores), and accept `progress=True`. The `medchem.structural` / `medchem.rules` filter *classes* return a **pandas DataFrame** (one row per input mol); the `medchem.functional.*` helpers return a **NumPy boolean array** where `True` = the molecule passes / is kept. Get the canonical rule and alert names from `mc.rules.RuleFilters.list_available_rules()` and `mc.structural.CommonAlertsFilters.list_default_available_alerts()` rather than guessing.

### 1. Medicinal Chemistry Rules — `medchem.rules`

**Single rule** — `medchem.rules.basic_rules.*` functions take one mol (SMILES or RDKit) and return a plain `bool`:

```python
import medchem as mc

smi = "CC(=O)OC1=CC=CC=C1C(=O)O"  # aspirin
mc.rules.basic_rules.rule_of_five(smi)   # -> True
mc.rules.basic_rules.rule_of_veber(smi)  # -> True
mc.rules.basic_rules.rule_of_cns(smi)
```

Available rules (subset; full list via `mc.rules.RuleFilters.list_available_rules()`): `rule_of_five`, `rule_of_five_beyond`, `rule_of_four`, `rule_of_three`, `rule_of_three_extended`, `rule_of_two`, `rule_of_ghose`, `rule_of_veber`, `rule_of_reos`, `rule_of_egan`, `rule_of_pfizer_3_75`, `rule_of_gsk_4_400`, `rule_of_oprea`, `rule_of_xu`, `rule_of_cns`, `rule_of_respiratory`, `rule_of_zinc`, `rule_of_leadlike_soft`, `rule_of_druglike_soft`, `rule_of_generative_design`, `rule_of_chemaxon_druglikeness` (needs ChemAxon).

> There is **no** `rule_of_drug`, `rule_of_leadlike_strict`, `golden_triangle`, or `pains_filter` function in 2.0.5. PAINS lives in the alert system (`HASALERT("pains")` or `CommonAlertsFilters(alerts_set=["PAINS"])`). For lead-likeness use `rule_of_leadlike_soft` or `rule_of_oprea`.

**Multiple rules** — `RuleFilters` returns a DataFrame with columns `mol`, `pass_all`, `pass_any`, and one boolean column per rule:

```python
import datamol as dm
import medchem as mc

mols = [dm.to_mol(s) for s in smiles_list]
rfilter = mc.rules.RuleFilters(rule_list=["rule_of_five", "rule_of_veber", "rule_of_cns"])
df = rfilter(mols=mols, n_jobs=-1, progress=True)
# df["pass_all"] -> bool per molecule; df["rule_of_five"] -> per-rule bool
clean = [m for m, ok in zip(mols, df["pass_all"]) if ok]
```

**Property windows** — there is no all-in-one "Constraints(mw_range=...)" object (see note in section 7). Build custom property cutoffs with `mc.rules.in_range` over descriptor names from `mc.rules.list_descriptors()` (`mw`, `clogp`, `tpsa`, `n_lipinski_hbd`, `n_lipinski_hba`, `n_rotatable_bonds`, `n_rings`, ...), or use the query DSL (`HASPROP`, section 8).

### 2. Structural Alert Filters — `medchem.structural`

Two filter classes ship in `medchem.structural`: `CommonAlertsFilters` and `NIBRFilters`. (Lilly demerits is reached through `medchem.functional`, see section 3 — its class lives under `medchem.structural.lilly_demerits` and needs external binaries.)

**Common alerts** — curated alert sets from ChEMBL (Glaxo, Dundee, BMS, **PAINS**, SureChEMBL, ...). Returns a DataFrame with `mol`, `pass_filter` (bool), `status` (`ok`/`exclude`), `reasons` (matched alert names, `;`-joined):

```python
import medchem as mc

caf = mc.structural.CommonAlertsFilters()                 # all default sets
caf_pains = mc.structural.CommonAlertsFilters(alerts_set=["PAINS"])  # PAINS only
df = caf(mols=mol_list, n_jobs=-1, progress=True)
clean = df[df["pass_filter"]]
# discover sets: mc.structural.CommonAlertsFilters.list_default_available_alerts()
```

**NIBR filters** — Novartis filter set. Returns a DataFrame including `mol`, `pass_filter`, `severity`, `status`, `reasons`:

```python
nibr = mc.structural.NIBRFilters()
df = nibr(mols=mol_list, n_jobs=-1)
```

### 3. Functional API — `medchem.functional`

One-call helpers that return a NumPy boolean array (`True` = keep). Pass `return_idx=True` to get indices of passing mols instead:

```python
import medchem as mc

mc.functional.rules_filter(mol_list, rules=["rule_of_five", "rule_of_veber"], n_jobs=-1)
mc.functional.alert_filter(mol_list, alerts=["pains"], n_jobs=-1)   # alert names are lowercase here
mc.functional.nibr_filter(mol_list, max_severity=10, n_jobs=-1)
mc.functional.complexity_filter(mol_list, complexity_metric="bertz", limit="99", n_jobs=-1)
mc.functional.chemical_group_filter(mol_list, chemical_group=mc.groups.ChemicalGroup(groups=["hinge_binders"]))
```

**Lilly demerits** — requires the external Lilly binaries (see Installation); raises `ImportError` if missing. Molecules above `max_demerits` (default 160) are rejected:

```python
keep = mc.functional.lilly_demerit_filter(mol_list, max_demerits=160, n_jobs=-1)  # NumPy bool array
```

### 4. Chemical Groups Detection — `medchem.groups`

`ChemicalGroup` matches curated group catalogs. List valid catalog names with `mc.groups.list_default_chemical_groups()` (e.g. `hinge_binders`, `electrophilic_warheads_for_kinases`, `common_warhead_covalent_inhibitors`, `privileged_kinase_inhibitor_scaffolds`, `aggregator`). Per-mol functional-group names (for the query DSL `HASGROUP`) come from `mc.groups.list_functional_group_names()`.

```python
import medchem as mc

group = mc.groups.ChemicalGroup(groups=["hinge_binders"])
group.has_match(mol)        # bool for one mol
group.get_matches(mol)      # detailed matches
# batch: mc.functional.chemical_group_filter(mols, chemical_group=group)
```

> `phosphate_binders`, `michael_acceptors`, and `reactive_groups` are **not** default catalog names. For reactive/electrophilic motifs use `electrophilic_warheads_for_kinases` / `common_warhead_covalent_inhibitors`, the alert filters (section 2), or a custom SMARTS catalog (`mc.catalogs.catalog_from_smarts`).

### 5. Named Catalogs — `medchem.catalogs`

```python
import medchem as mc

mc.catalogs.list_named_catalogs()      # available catalog names
cat = mc.catalogs.NamedCatalogs.pains()  # e.g. a PAINS RDKit FilterCatalog
mc.catalogs.catalog_from_smarts(...)   # build a catalog from custom SMARTS
```

### 6. Molecular Complexity — `medchem.complexity`

`ComplexityFilter` flags molecules whose complexity exceeds a percentile threshold derived from a reference set (default ZINC). It is **called per molecule** and returns a bool (`True` = within limit / keep). Metrics: `bertz`, `whitlock` (`WhitlockCT`), `barone` (`BaroneCT`), `smcm` (`SMCM`), `twc` (`TWC`).

```python
import medchem as mc

cflt = mc.complexity.ComplexityFilter(limit="99", complexity_metric="bertz")
keep = [cflt(m) for m in mol_list]
# or batch: mc.functional.complexity_filter(mol_list, complexity_metric="bertz", limit="99")
```

> There is no `mc.complexity.calculate_complexity(...)` and `ComplexityFilter` takes `limit`/`complexity_metric`/`threshold_stats_file`, **not** `max_complexity`. For a raw score use the metric classes directly (`mc.complexity.TWC`, etc.).

### 7. Substructure Constraints — `medchem.constraints`

`mc.constraints.Constraints(core, constraint_fns, prop_name="query")` enforces **substructure / R-group** constraints around a query core (via `has_match` / `validate`) — it is **not** a physchem property-window filter. For MW/logP/TPSA windows, use `RuleFilters` + `in_range` (section 1) or the query DSL `HASPROP` (section 8).

### 8. Query DSL — `medchem.query`

`QueryFilter` evaluates a boolean expression over rules, properties, alerts, and groups. Operators: `AND`, `OR`, `NOT`, comparisons `< > <= >= == !=`. Primitives: `MATCHRULE("...")`, `HASPROP("<descriptor>" < value)`, `HASALERT("<lowercase set>")`, `HASGROUP("...")`, `HASSUBSTRUCTURE`/`HASSUPERSTRUCTURE`, `LIKE`.

```python
import medchem as mc

qf = mc.query.QueryFilter('MATCHRULE("rule_of_five") AND HASPROP("mw" < 500) AND NOT HASALERT("pains")')
keep = qf(mol_list, n_jobs=-1)   # NumPy bool array
```

> The syntax is the structured DSL above — **not** free-form text like `"rule_of_five AND NOT common_alerts"`. There is no `mc.query.parse()`; construct `mc.query.QueryFilter(query_string)` and call it on the mols. Alert names inside `HASALERT` are lowercase (`pains`, `tox`, `nih`, ...).

## Workflow Patterns

### Pattern 1: Initial Triage of Compound Library

Filter a large collection to drug-like candidates, dropping anything with structural alerts.

```python
import datamol as dm
import medchem as mc
import pandas as pd

df = pd.read_csv("compounds.csv")
mols = [dm.to_mol(smi) for smi in df["smiles"]]

# Rule filter -> DataFrame with pass_all + per-rule columns
rule_df = mc.rules.RuleFilters(rule_list=["rule_of_five", "rule_of_veber"])(
    mols=mols, n_jobs=-1, progress=True
)

# Structural alerts -> DataFrame with pass_filter (True = clean)
alert_df = mc.structural.CommonAlertsFilters()(mols=mols, n_jobs=-1, progress=True)

df["passes_rules"] = rule_df["pass_all"].to_numpy()
df["no_alerts"] = alert_df["pass_filter"].to_numpy()
df["drug_like"] = df["passes_rules"] & df["no_alerts"]

df[df["drug_like"]].to_csv("filtered_compounds.csv", index=False)
```

### Pattern 2: Lead Optimization Filtering

Stack stricter filters and keep only molecules passing every stage. The `functional.*` helpers all return aligned NumPy bool arrays, so intersecting them is straightforward.

```python
import numpy as np
import medchem as mc

f = mc.functional
keep = (
    f.rules_filter(candidate_mols, rules=["rule_of_oprea"], n_jobs=-1)
    & f.nibr_filter(candidate_mols, n_jobs=-1)
    & f.complexity_filter(candidate_mols, complexity_metric="bertz", limit="99", n_jobs=-1)
)
# Add lilly_demerit_filter(...) too if the Lilly binaries are installed.
survivors = [m for m, ok in zip(candidate_mols, keep) if ok]
```

### Pattern 3: Identify Specific Chemical Groups

Flag molecules containing a target scaffold/motif (validate names with `mc.groups.list_default_chemical_groups()`).

```python
import medchem as mc

group = mc.groups.ChemicalGroup(groups=["hinge_binders"])
keep = mc.functional.chemical_group_filter(mol_list, chemical_group=group)
with_group = [m for m, ok in zip(mol_list, keep) if ok]
```

## Best Practices

1. **Context Matters**: Don't blindly apply filters. Understand the biological target and chemical space.

2. **Combine Multiple Filters**: Use rules, structural alerts, and domain knowledge together for better decisions.

3. **Use Parallelization**: For large datasets (>1000 molecules), always use `n_jobs=-1` for parallel processing.

4. **Iterative Refinement**: Start with broad filters (Ro5), then apply more specific criteria (CNS, leadlike) as needed.

5. **Document Filtering Decisions**: Track which molecules were filtered out and why for reproducibility.

6. **Validate Results**: Remember that marketed drugs often fail standard filters—use these as guidelines, not absolute rules.

7. **Consider Prodrugs**: Molecules designed as prodrugs may intentionally violate standard medicinal chemistry rules.

## Resources

### references/api_guide.md
Comprehensive API reference covering all medchem modules with detailed function signatures, parameters, and return types.

### references/rules_catalog.md
Complete catalog of available rules, filters, and alerts with descriptions, thresholds, and literature references.

### scripts/filter_molecules.py
Batch filtering CLI. Supports CSV/TSV, SDF, and plain-SMILES `.txt` input, configurable filter combinations, and a summary report.

**Usage:**
```bash
uv run python scripts/filter_molecules.py input.csv \
    --rules rule_of_five,rule_of_cns --nibr --output filtered.csv
```
Flags are individual switches (`--nibr`, `--common-alerts`, `--lilly`, `--pains`), not `--alerts <name>`. `--lilly` needs the external Lilly binaries.

## Documentation

Official documentation: https://medchem-docs.datamol.io/
GitHub repository: https://github.com/datamol-io/medchem

