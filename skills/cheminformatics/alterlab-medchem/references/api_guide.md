# Medchem API Reference

Verified against `medchem==2.0.5`. For the authoritative, always-current API, run
`mc.rules.RuleFilters.list_available_rules()`,
`mc.structural.CommonAlertsFilters.list_default_available_alerts()`,
`mc.groups.list_default_chemical_groups()`, and
`mc.catalogs.list_named_catalogs()` — and read https://medchem-docs.datamol.io/.

## Cross-cutting conventions

- Inputs accept SMILES strings **or** RDKit mols (`Sequence[Union[str, Chem.Mol]]`).
- Filter **classes** (`medchem.rules.RuleFilters`, `medchem.structural.*`) return a **pandas DataFrame**, one row per input mol, with a `mol` column.
- Filter **functions** (`medchem.functional.*`) return a **NumPy boolean array** (`True` = keep); pass `return_idx=True` for indices instead.
- Common kwargs: `n_jobs` (default `-1` = all cores), `progress` (bool), `scheduler` (`"auto"`/`"threads"`/`"processes"`).

---

## medchem.rules

### RuleFilters

```python
RuleFilters(rule_list: List[Union[str, Callable]], rule_list_names: Optional[List[Optional[str]]] = None)
__call__(mols, n_jobs=-1, progress=False, keep_props=False, fail_if_invalid=True, ...) -> pandas.DataFrame
```

Returns a DataFrame with columns: `mol`, `pass_all`, `pass_any`, and one boolean column per rule.

- `RuleFilters.list_available_rules()` -> DataFrame of rule names + metadata.

### medchem.rules.basic_rules

Single-molecule rule functions returning `bool`:

```python
rule_of_five(mol, mw=None, clogp=None, n_lipinski_hbd=None, n_lipinski_hba=None, **kwargs) -> bool
```

Available (subset): `rule_of_five`, `rule_of_five_beyond`, `rule_of_four`, `rule_of_three`,
`rule_of_three_extended`, `rule_of_two`, `rule_of_ghose`, `rule_of_veber`, `rule_of_reos`,
`rule_of_egan`, `rule_of_pfizer_3_75`, `rule_of_gsk_4_400`, `rule_of_oprea`, `rule_of_xu`,
`rule_of_cns`, `rule_of_respiratory`, `rule_of_zinc`, `rule_of_leadlike_soft`,
`rule_of_druglike_soft`, `rule_of_generative_design`, `rule_of_chemaxon_druglikeness` (needs ChemAxon).

> No `rule_of_drug`, `rule_of_leadlike_strict`, `golden_triangle`, or `pains_filter`. Use the
> alert system for PAINS and `rule_of_leadlike_soft`/`rule_of_oprea` for lead-likeness.

### Helpers

- `in_range(x, min_val=-inf, max_val=inf) -> bool` — gate a numeric descriptor.
- `list_descriptors()` -> names usable for property windows: `mw`, `clogp`, `tpsa`, `fsp3`, `qed`,
  `sas`, `n_lipinski_hbd`, `n_lipinski_hba`, `n_rotatable_bonds`, `n_rings`, `n_aromatic_rings`,
  `n_heavy_atoms`, `n_hetero_atoms`, `formal_charge`, ...
- `n_fused_aromatic_rings`, `n_heavy_metals`, `fraction_atom_in_scaff`, `has_spider_chains`.

---

## medchem.structural

### CommonAlertsFilters

```python
CommonAlertsFilters(alerts_set: Union[str, List[str], None] = None, alerts_db_path=None)
__call__(mols, n_jobs=-1, progress=False, batch_size=None, keep_details=False) -> pandas.DataFrame
```

Returns DataFrame columns: `mol`, `pass_filter` (bool; `True` = clean), `status` (`"ok"`/`"exclude"`),
`reasons` (`;`-joined alert names, `NaN` when clean).

- `CommonAlertsFilters.list_default_available_alerts()` -> DataFrame of alert sets
  (`Glaxo`, `Dundee`, `BMS`, `PAINS`, `SureChEMBL`, ...). Pass a subset via `alerts_set=["PAINS"]`.

### NIBRFilters

```python
NIBRFilters()
__call__(mols, n_jobs=-1, progress=False, keep_details=False) -> pandas.DataFrame
```

Returns DataFrame including `mol`, `pass_filter`, `severity`, `status`, `reasons`,
`n_covalent_motif`, `special_mol`.

### Lilly demerits

The class is `medchem.structural.lilly_demerits.LillyDemeritsFilters` (not exported at
`medchem.structural` top level) and **requires external compiled binaries**
(`mamba install -c conda-forge lilly-medchem-rules`); importing it without them raises
`ImportError`. Prefer the functional entry point (below).

---

## medchem.functional

All return a NumPy bool array (`True` = keep); `return_idx=True` returns passing indices.

```python
rules_filter(mols, rules: Union[List, RuleFilters], n_jobs=None, progress=False, ...) -> np.ndarray
alert_filter(mols, alerts: List[str], alerts_db=None, n_jobs=1, progress=False, ...) -> np.ndarray
nibr_filter(mols, n_jobs=None, max_severity=10, progress=False, ...) -> np.ndarray
lilly_demerit_filter(mols, max_demerits=160, n_jobs=None, progress=False, ...) -> np.ndarray  # needs binaries
complexity_filter(mols, complexity_metric="bertz", limit="99", threshold_stats_file="zinc_15_available", ...) -> np.ndarray
chemical_group_filter(mols, chemical_group: ChemicalGroup, exact_match=False, ...) -> np.ndarray
```

> `alert_filter` alert names are **lowercase** (`"pains"`, `"tox"`, `"nih"`, ...). There is no
> `common_alerts_filter` / `lilly_demerits_filter`; the names are `alert_filter` / `lilly_demerit_filter`.

Other helpers: `atom_list_filter`, `bredt_filter`, `catalog_filter`, `halogenicity_filter`,
`macrocycle_filter`, `molecular_graph_filter`, `num_atom_filter`, `num_stereo_center_filter`,
`protecting_groups_filter`, `ring_infraction_filter`, `symmetry_filter`.

---

## medchem.groups

### ChemicalGroup

```python
ChemicalGroup(groups: Union[str, List[str], None] = None, n_jobs=None, groups_db=None)
has_match(mol, exact_match=False, terminal_only=False) -> bool
get_matches(mol, use_smiles=True, exact_match=False, terminal_only=False)
filter(names: List[str], fuzzy=False)
# also: dataframe, get_catalog, list_groups, mols, smarts, smiles
```

- `list_default_chemical_groups()` -> catalog group names (e.g. `hinge_binders`,
  `electrophilic_warheads_for_kinases`, `common_warhead_covalent_inhibitors`,
  `privileged_kinase_inhibitor_scaffolds`, `aggregator`, `privileged_scaffolds`).
- `list_functional_group_names()` -> ~579 fine-grained functional-group names used by the
  query DSL `HASGROUP(...)`.

> `phosphate_binders`, `michael_acceptors`, and `reactive_groups` are **not** default group names.

---

## medchem.complexity

```python
ComplexityFilter(limit="99", complexity_metric="bertz", threshold_stats_file="zinc_15_available")
__call__(mol) -> bool        # per molecule; True = within the limit
```

Metric classes for raw scores: `BaroneCT`, `WhitlockCT`, `SMCM`, `TWC` (metric strings:
`"bertz"`, `"barone"`, `"whitlock"`, `"smcm"`, `"twc"`). There is no `calculate_complexity` and no
`max_complexity` argument; the filter thresholds against a percentile of a reference set.

---

## medchem.catalogs

```python
NamedCatalogs.pains()   # RDKit FilterCatalog; also .pains_a/.pains_b/.pains_c, .brenk, .nih, .bms, ...
list_named_catalogs() -> List[str]   # ['tox','pains','pains_a','pains_b','pains_c','nih', ...]
catalog_from_smarts(...)             # build a catalog from custom SMARTS
merge_catalogs(...)
```

---

## medchem.constraints

```python
Constraints(core: Chem.Mol, constraint_fns: Dict[str, Callable], prop_name="query")
has_match(...) / validate(...) / get_matches(...)
```

Enforces **substructure / R-group** constraints around a query `core` — **not** physchem
property windows. For MW/logP/TPSA/HBD windows use `medchem.rules.in_range` over computed
descriptors, or the query DSL `HASPROP` (below).

---

## medchem.query

```python
QueryFilter(query: str, grammar=None, parser="lalr")
__call__(mols, n_jobs=-1, progress=False) -> array of bool
```

Structured boolean grammar (not free-form text). Primitives:

- `MATCHRULE("rule_of_five")`
- `HASPROP("mw" < 500)` — comparison operators `< > <= >= == !=`; descriptor names from `list_descriptors()`
- `HASALERT("pains")` — alert-set names are lowercase
- `HASGROUP("<functional_group_name>")`
- `HASSUBSTRUCTURE(...)`, `HASSUPERSTRUCTURE(...)`, `LIKE(...)`
- Combine with `AND`, `OR`, `NOT`, parentheses.

```python
qf = mc.query.QueryFilter('MATCHRULE("rule_of_five") AND HASPROP("mw" < 500) AND NOT HASALERT("pains")')
keep = qf(mol_list, n_jobs=-1)
```

> There is no `mc.query.parse()`. Construct `QueryFilter(query_string)` and call it directly.

---

## Working with DataFrames

```python
import pandas as pd
import datamol as dm
import medchem as mc

df = pd.read_csv("molecules.csv")
mols = [dm.to_mol(smi) for smi in df["smiles"]]

res = mc.rules.RuleFilters(rule_list=["rule_of_five", "rule_of_cns"])(mols=mols, n_jobs=-1)
df["passes_ro5"] = res["rule_of_five"].to_numpy()
df["passes_cns"] = res["rule_of_cns"].to_numpy()
df["pass_all"]   = res["pass_all"].to_numpy()

filtered = df[df["pass_all"]]
```
