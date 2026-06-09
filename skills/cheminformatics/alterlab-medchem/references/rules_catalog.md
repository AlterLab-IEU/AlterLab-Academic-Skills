# Medchem Rules and Filters Catalog

Background and selection guidance for medicinal-chemistry rules, structural alerts, and filters.
The rule criteria and literature references below are conceptual background; for the exact
implementation and the canonical name list use `mc.rules.RuleFilters.list_available_rules()`.

> **Verified against `medchem==2.0.5`.** Not every rule below is shipped as a named medchem
> function (e.g. Rule of Drug, strict lead-likeness, and Golden Triangle have no dedicated
> function in this version — see notes). Apply those criteria via `RuleFilters` of the available
> rules plus property windows (`mc.rules.in_range`) or the query DSL.

## Table of Contents

1. [Drug-Likeness Rules](#drug-likeness-rules)
2. [Lead-Likeness Rules](#lead-likeness-rules)
3. [Fragment Rules](#fragment-rules)
4. [CNS Rules](#cns-rules)
5. [Structural Alert Filters](#structural-alert-filters)
6. [Chemical Group Patterns](#chemical-group-patterns)

---

## Drug-Likeness Rules

### Rule of Five (Lipinski)

**Reference:** Lipinski et al., Adv Drug Deliv Rev (1997) 23:3-25

**Purpose:** Predict oral bioavailability

**Criteria:**
- Molecular Weight ≤ 500 Da
- LogP ≤ 5
- Hydrogen Bond Donors ≤ 5
- Hydrogen Bond Acceptors ≤ 10

**Usage:**
```python
mc.rules.basic_rules.rule_of_five(mol)
```

**Notes:**
- One of the most widely used filters in drug discovery
- About 90% of orally active drugs comply with these rules
- Exceptions exist, especially for natural products and antibiotics

---

### Rule of Veber

**Reference:** Veber et al., J Med Chem (2002) 45:2615-2623

**Purpose:** Additional criteria for oral bioavailability

**Criteria:**
- Rotatable Bonds ≤ 10
- Topological Polar Surface Area (TPSA) ≤ 140 Ų

**Usage:**
```python
mc.rules.basic_rules.rule_of_veber(mol)
```

**Notes:**
- Complements Rule of Five
- TPSA correlates with cell permeability
- Rotatable bonds affect molecular flexibility

---

### Rule of Drug (composite — no single function)

**Purpose:** Combined drug-likeness assessment

**Criteria:**
- Passes Rule of Five
- Passes Veber rules
- Does not contain PAINS substructures

**There is no `rule_of_drug` function in medchem 2.0.5.** Compose it explicitly, e.g. with the query DSL:
```python
qf = mc.query.QueryFilter(
    'MATCHRULE("rule_of_five") AND MATCHRULE("rule_of_veber") AND NOT HASALERT("pains")'
)
keep = qf(mol_list, n_jobs=-1)
```

---

### REOS (Rapid Elimination Of Swill)

**Reference:** Walters & Murcko, Adv Drug Deliv Rev (2002) 54:255-271

**Purpose:** Filter out compounds unlikely to be drugs

**Criteria:**
- Molecular Weight: 200-500 Da
- LogP: -5 to 5
- Hydrogen Bond Donors: 0-5
- Hydrogen Bond Acceptors: 0-10

**Usage:**
```python
mc.rules.basic_rules.rule_of_reos(mol)
```

---

### Golden Triangle (no single function)

**Reference:** Johnson et al., J Med Chem (2009) 52:5487-5500

**Purpose:** Balance lipophilicity and molecular weight

**Criteria:**
- 200 ≤ MW ≤ 50 × LogP + 400
- LogP: -2 to 5

**No `golden_triangle` function in medchem 2.0.5.** Implement with computed `mw`/`clogp`
descriptors and `mc.rules.in_range`, or a custom callable passed to `RuleFilters(rule_list=[...])`.

**Notes:**
- Defines an optimal physicochemical space (a triangle on the MW vs LogP plot).

---

## Lead-Likeness Rules

### Rule of Oprea

**Reference:** Oprea et al., J Chem Inf Comput Sci (2001) 41:1308-1315

**Purpose:** Identify lead-like compounds for optimization

**Criteria:**
- Molecular Weight: 200-350 Da
- LogP: -2 to 4
- Rotatable Bonds ≤ 7
- Number of Rings ≤ 4

**Usage:**
```python
mc.rules.basic_rules.rule_of_oprea(mol)
```

**Rationale:** Lead compounds should have "room to grow" during optimization

---

### Rule of Leadlike (Soft)

**Purpose:** Permissive lead-like criteria

**Criteria:**
- Molecular Weight: 250-450 Da
- LogP: -3 to 4
- Rotatable Bonds ≤ 10

**Usage:**
```python
mc.rules.basic_rules.rule_of_leadlike_soft(mol)
```

---

### Rule of Leadlike (Strict) — not shipped

**Purpose:** Restrictive lead-like criteria (more aggressive than `rule_of_leadlike_soft`)

**Criteria (conceptual):**
- Molecular Weight: 200-350 Da
- LogP: -2 to 3.5
- Rotatable Bonds ≤ 7
- Number of Rings: 1-3

**medchem 2.0.5 ships only `rule_of_leadlike_soft`** (there is no `rule_of_leadlike_strict`).
For stricter lead-likeness, combine `rule_of_oprea` with tighter property windows
(`mc.rules.in_range`) or `HASPROP` queries.

---

## Fragment Rules

### Rule of Three

**Reference:** Congreve et al., Drug Discov Today (2003) 8:876-877

**Purpose:** Screen fragment libraries for fragment-based drug discovery

**Criteria:**
- Molecular Weight ≤ 300 Da
- LogP ≤ 3
- Hydrogen Bond Donors ≤ 3
- Hydrogen Bond Acceptors ≤ 3
- Rotatable Bonds ≤ 3
- Polar Surface Area ≤ 60 Ų

**Usage:**
```python
mc.rules.basic_rules.rule_of_three(mol)
```

**Notes:**
- Fragments are grown into leads during optimization
- Lower complexity allows more starting points

---

## CNS Rules

### Rule of CNS

**Purpose:** Central nervous system drug-likeness

**Criteria:**
- Molecular Weight ≤ 450 Da
- LogP: -1 to 5
- Hydrogen Bond Donors ≤ 2
- TPSA ≤ 90 Ų

**Usage:**
```python
mc.rules.basic_rules.rule_of_cns(mol)
```

**Rationale:**
- Blood-brain barrier penetration requires specific properties
- Lower TPSA and HBD count improve BBB permeability
- Tight constraints reflect CNS challenges

---

## Structural Alert Filters

### PAINS (Pan Assay INterference compoundS)

**Reference:** Baell & Holloway, J Med Chem (2010) 53:2719-2740

**Purpose:** Identify compounds that interfere with assays

**Categories:**
- Catechols
- Quinones
- Rhodanines
- Hydroxyphenylhydrazones
- Alkyl/aryl aldehydes
- Michael acceptors (specific patterns)

**Usage** (PAINS lives in the alert system, not a `pains_filter` rule function):
```python
# Functional API (lowercase set name), True = no PAINS / keep:
mc.functional.alert_filter(mol_list, alerts=["pains"], n_jobs=-1)
# Or via the CommonAlerts class restricted to the PAINS set:
mc.structural.CommonAlertsFilters(alerts_set=["PAINS"])(mols=mol_list, n_jobs=-1)
# Or the RDKit catalog: mc.catalogs.NamedCatalogs.pains()
```

**Notes:**
- PAINS compounds show activity in multiple assays through non-specific mechanisms
- Common false positives in screening campaigns
- Should be deprioritized in lead selection

---

### Common Alerts Filters

**Source:** Derived from ChEMBL curation and medicinal chemistry literature

**Purpose:** Flag common problematic structural patterns

**Alert Categories:**
1. **Reactive Groups**
   - Epoxides
   - Aziridines
   - Acid halides
   - Isocyanates

2. **Metabolic Liabilities**
   - Hydrazines
   - Thioureas
   - Anilines (certain patterns)

3. **Aggregators**
   - Polyaromatic systems
   - Long aliphatic chains

4. **Toxicophores**
   - Nitro aromatics
   - Aromatic N-oxides
   - Certain heterocycles

**Usage:**
```python
alert_filter = mc.structural.CommonAlertsFilters()   # or alerts_set=["PAINS", "BMS"]
df = alert_filter(mols=mol_list, n_jobs=-1, progress=True)
```

**Return format** — a pandas DataFrame, one row per molecule:

| column        | meaning                                              |
|---------------|------------------------------------------------------|
| `mol`         | the RDKit molecule                                   |
| `pass_filter` | `True` if clean (no alert triggered)                 |
| `status`      | `"ok"` or `"exclude"`                                |
| `reasons`     | `;`-joined matched alert names (`NaN` when clean)    |

(There is no `check_mol` method in 2.0.5.) Discover the available alert sets with
`mc.structural.CommonAlertsFilters.list_default_available_alerts()`.

---

### NIBR Filters

**Source:** Novartis Institutes for BioMedical Research

**Purpose:** Industrial medicinal chemistry filtering rules

**Features:**
- Proprietary filter set developed from Novartis experience
- Balances drug-likeness with practical medicinal chemistry
- Includes both structural alerts and property filters

**Usage:**
```python
nibr = mc.structural.NIBRFilters()
df = nibr(mols=mol_list, n_jobs=-1)        # DataFrame: mol, pass_filter, severity, status, reasons, ...
# or the functional one-liner returning a NumPy bool array:
keep = mc.functional.nibr_filter(mol_list, max_severity=10, n_jobs=-1)
```

---

### Lilly Demerits Filter

**Reference:** Bruns & Watson, J Med Chem (2012) 55:9763-9772, doi 10.1021/jm301008n
(275 rules developed over ~18 years).

**Purpose:** Identify assay interference and problematic functionalities via a demerit score.

**Mechanism:**
- Each matched pattern adds demerits; molecules above a demerit ceiling are rejected.
- The original paper rejects at >100 demerits; medchem exposes this as the `max_demerits`
  argument (**default 160** in 2.0.5 — set `max_demerits=100` to match the paper).
- High-severity patterns can hard-reject; lower-severity patterns accumulate.

**Requires external binaries** (`mamba install -c conda-forge lilly-medchem-rules`); the call
raises `ImportError` if they are missing. The class lives at
`medchem.structural.lilly_demerits.LillyDemeritsFilters`; use the functional entry point:

```python
keep = mc.functional.lilly_demerit_filter(mol_list, max_demerits=160, n_jobs=-1)
# NumPy bool array: True = within the demerit ceiling (kept)
```

---

## Chemical Group Patterns

`ChemicalGroup(groups=[...])` matches curated catalog groups. **Validate names against
`mc.groups.list_default_chemical_groups()`** — verified default groups include:

| group name                              | use                                  |
|-----------------------------------------|--------------------------------------|
| `hinge_binders`                         | kinase hinge-binding motifs          |
| `electrophilic_warheads_for_kinases`    | covalent kinase warheads             |
| `common_warhead_covalent_inhibitors`    | covalent-inhibitor warheads          |
| `privileged_kinase_inhibitor_scaffolds` | privileged kinase scaffolds          |
| `privileged_scaffolds`                  | privileged drug scaffolds            |
| `aggregator`                            | aggregation-prone motifs             |

```python
group = mc.groups.ChemicalGroup(groups=["hinge_binders"])
group.has_match(mol)                                       # bool for ONE molecule
keep = mc.functional.chemical_group_filter(mol_list, chemical_group=group)  # batch -> bool array
```

> `phosphate_binders`, `michael_acceptors`, and `reactive_groups` are **not** default catalog
> names in 2.0.5. For Michael acceptors / reactive electrophiles, use the alert filters
> (`alert_filter`, `CommonAlertsFilters`) or a custom SMARTS catalog (below). For covalent
> warheads, use `electrophilic_warheads_for_kinases` / `common_warhead_covalent_inhibitors`.

---

## Custom SMARTS Patterns

`ChemicalGroup` has no `custom_smarts` argument. Build a catalog from your own SMARTS with
`mc.catalogs.catalog_from_smarts`, then match via `mc.functional.catalog_filter`:

```python
cat = mc.catalogs.catalog_from_smarts(
    smarts=["[CX3]=[CX3]C(=O)[NX3]", "[C;H0](=O)C(F)(F)F"],  # acrylamide, CF3-ketone warhead
    labels=["acrylamide", "tfm_ketone"],
)
keep = mc.functional.catalog_filter(mol_list, catalogs=[cat])  # True = no match / keep
```

---

## Filter Selection Guidelines

### Initial Screening (High-Throughput)

Recommended filters:
- Rule of Five
- PAINS filter
- Common Alerts (permissive settings)

```python
rfilter = mc.rules.RuleFilters(rule_list=["rule_of_five"])
alert_filter = mc.structural.CommonAlertsFilters(alerts_set=["PAINS"])  # PAINS via alerts, not a rule
```

---

### Hit-to-Lead

Recommended filters:
- Rule of Oprea or Leadlike (soft)
- NIBR filters
- Lilly Demerits (needs external binaries)

```python
rfilter = mc.rules.RuleFilters(rule_list=["rule_of_oprea"])
nibr = mc.structural.NIBRFilters()
# Lilly via the functional API (requires lilly-medchem-rules binaries):
# keep_lilly = mc.functional.lilly_demerit_filter(mols, n_jobs=-1)
```

---

### Lead Optimization

Recommended filters:
- Rule of Five + Veber (compose "rule of drug")
- Lead-likeness (`rule_of_oprea`) + tighter property windows
- Full structural alert analysis
- Complexity filter

```python
rfilter = mc.rules.RuleFilters(rule_list=["rule_of_five", "rule_of_veber", "rule_of_oprea"])
alert_filter = mc.structural.CommonAlertsFilters()
complexity_filter = mc.complexity.ComplexityFilter(limit="95", complexity_metric="bertz")
```

---

### CNS Targets

Recommended filters:
- Rule of CNS
- PAINS / alert screening
- BBB-oriented property windows (low TPSA, low HBD)

```python
rfilter = mc.rules.RuleFilters(rule_list=["rule_of_cns"])
# Property windows via the query DSL (no all-in-one Constraints object):
qf = mc.query.QueryFilter('HASPROP("tpsa" <= 90) AND HASPROP("n_lipinski_hbd" <= 2) AND HASPROP("mw" <= 450)')
```

---

### Fragment-Based Drug Discovery

Recommended filters:
- Rule of Three
- Low complexity
- Reactive-group / alert check

```python
rfilter = mc.rules.RuleFilters(rule_list=["rule_of_three"])
complexity_filter = mc.complexity.ComplexityFilter(limit="90", complexity_metric="bertz")
```

---

## Important Considerations

### False Positives and False Negatives

**Filters are guidelines, not absolutes:**

1. **False Positives** (good drugs flagged):
   - ~10% of marketed drugs fail Rule of Five
   - Natural products often violate standard rules
   - Prodrugs intentionally break rules
   - Antibiotics and antivirals frequently non-compliant

2. **False Negatives** (bad compounds passing):
   - Passing filters doesn't guarantee success
   - Target-specific issues not captured
   - In vivo properties not fully predicted

### Context-Specific Application

**Different contexts require different criteria:**

- **Target Class:** Kinases vs GPCRs vs ion channels have different optimal spaces
- **Modality:** Small molecules vs PROTACs vs molecular glues
- **Administration Route:** Oral vs IV vs topical
- **Disease Area:** CNS vs oncology vs infectious disease
- **Stage:** Screening vs hit-to-lead vs lead optimization

### Complementing with Machine Learning

Modern approaches combine rules with ML:

```python
# Rule-based pre-filtering (RuleFilters returns a DataFrame with a pass_all column)
res = mc.rules.RuleFilters(rule_list=["rule_of_five"])(mols=mols, n_jobs=-1)
filtered_mols = [mol for mol, ok in zip(mols, res["pass_all"]) if ok]

# ML model scoring on the filtered set
ml_scores = ml_model.predict(filtered_mols)

# Combined decision
final_candidates = [
    mol for mol, score in zip(filtered_mols, ml_scores)
    if score > threshold
]
```

---

## References

1. Lipinski CA et al. Adv Drug Deliv Rev (1997) 23:3-25
2. Veber DF et al. J Med Chem (2002) 45:2615-2623
3. Oprea TI et al. J Chem Inf Comput Sci (2001) 41:1308-1315
4. Congreve M et al. Drug Discov Today (2003) 8:876-877
5. Baell JB & Holloway GA. J Med Chem (2010) 53:2719-2740
6. Johnson TW et al. J Med Chem (2009) 52:5487-5500
7. Walters WP & Murcko MA. Adv Drug Deliv Rev (2002) 54:255-271
8. Hann MM & Oprea TI. Curr Opin Chem Biol (2004) 8:255-263
9. Rishton GM. Drug Discov Today (1997) 2:382-384
10. Bruns RF & Watson IA. J Med Chem (2012) 55:9763-9772 (Lilly MedChem Rules)
