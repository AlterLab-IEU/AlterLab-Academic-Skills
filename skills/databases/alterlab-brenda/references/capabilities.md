# BRENDA — Capabilities & Code Examples

Copy-ready snippets for each BRENDA capability area. For the underlying SOAP API methods
and parameter lists, see `api_reference.md`. For end-to-end recipes, see `workflows.md`.
For the helper-script function inventory, see `helper_scripts.md`.

## 1. Kinetic Parameter Retrieval

**Get Km Values by EC Number**:
```python
from scripts.brenda_client import get_km_values

# Get Km values for all organisms
km_data = get_km_values("1.1.1.1")  # Alcohol dehydrogenase

# Get Km values for specific organism
km_data = get_km_values("1.1.1.1", organism="Saccharomyces cerevisiae")

# Get Km values for specific substrate
km_data = get_km_values("1.1.1.1", substrate="ethanol")
```

**Parse Km Results**:
```python
for entry in km_data:
    print(f"Km: {entry}")
    # Example output: "organism*Homo sapiens#substrate*ethanol#kmValue*1.2#commentary*"
```

**Extract Specific Information**:
```python
from scripts.brenda_queries import parse_km_entry, extract_organism_data

for entry in km_data:
    parsed = parse_km_entry(entry)
    organism = extract_organism_data(entry)
    # parse_km_entry exposes raw BRENDA field 'kmValue' (string) and the
    # derived 'km_value_numeric' (float); there is no 'km_value' key.
    print(f"Organism: {parsed.get('organism')}")
    print(f"Substrate: {parsed.get('substrate')}")
    print(f"Km value: {parsed.get('kmValue')}  (numeric: {parsed.get('km_value_numeric')})")
    print(f"pH: {parsed.get('ph', 'N/A')}")
    print(f"Temperature: {parsed.get('temperature', 'N/A')}")
```

## 2. Reaction Information

**Get Reactions by EC Number**:
```python
from scripts.brenda_client import get_reactions

# Get all reactions for EC number
reactions = get_reactions("1.1.1.1")

# Filter by organism
reactions = get_reactions("1.1.1.1", organism="Escherichia coli")

# Search specific reaction
reactions = get_reactions("1.1.1.1", reaction="ethanol + NAD+")
```

**Process Reaction Data**:
```python
from scripts.brenda_queries import parse_reaction_entry, extract_substrate_products

for reaction in reactions:
    parsed = parse_reaction_entry(reaction)
    substrates, products = extract_substrate_products(reaction)

    print(f"Reaction: {parsed['reaction']}")
    print(f"Organism: {parsed['organism']}")
    print(f"Substrates: {substrates}")
    print(f"Products: {products}")
```

## 3. Enzyme Discovery

> Gotcha: `getKmValue` responses do **not** carry an `ecNumber` field, so
> `search_enzymes_by_substrate` (built on Km data) returns `ec_number=''` and has
> no `enzyme_name`/`reaction` keys — it yields organism + substrate + Km. To resolve
> EC numbers and reactions for a substrate, query reaction data
> (`search_by_pattern` / `get_reactions`), whose entries include `ecNumber`.

**Find Enzymes by Substrate** (organism/substrate/Km, no EC number):
```python
from scripts.brenda_queries import search_enzymes_by_substrate

# Find enzymes that act on glucose
enzymes = search_enzymes_by_substrate("glucose", limit=20)

for enzyme in enzymes:
    print(f"Organism: {enzyme['organism']}")
    print(f"Substrate: {enzyme['substrate']}")
    print(f"Km: {enzyme['km_value']}")
```

**Find Enzymes by Product**:
```python
from scripts.brenda_queries import search_enzymes_by_product

# Find enzymes that produce lactate
enzymes = search_enzymes_by_product("lactate", limit=10)
```

**Search by Reaction Pattern**:
```python
from scripts.brenda_queries import search_by_pattern

# Find oxidation reactions
enzymes = search_by_pattern("oxidation", limit=15)
```

## 4. Organism-Specific Enzyme Data

**Get Enzyme Data for Multiple Organisms**:
```python
from scripts.brenda_queries import compare_across_organisms

organisms = ["Escherichia coli", "Saccharomyces cerevisiae", "Homo sapiens"]
comparison = compare_across_organisms("1.1.1.1", organisms)

for org_data in comparison:
    print(f"Organism: {org_data['organism']}")
    print(f"Avg Km: {org_data['average_km']}")
    print(f"Optimal pH: {org_data['optimal_ph']}")
    print(f"Temperature range: {org_data['temperature_range']}")
```

**Find Organisms with Specific Enzyme**:
```python
from scripts.brenda_queries import get_organisms_for_enzyme

organisms = get_organisms_for_enzyme("6.3.5.5")  # Glutamine synthetase
print(f"Found {len(organisms)} organisms with this enzyme")
```

## 5. Environmental Parameters

**Get pH and Temperature Data**:
```python
from scripts.brenda_queries import get_environmental_parameters

params = get_environmental_parameters("1.1.1.1")

print(f"Optimal pH range: {params['ph_range']}")
print(f"Optimal temperature: {params['optimal_temperature']}")
print(f"Stability pH: {params['stability_ph']}")
print(f"Temperature stability: {params['temperature_stability']}")
```

**Cofactor Requirements**:
```python
from scripts.brenda_queries import get_cofactor_requirements

cofactors = get_cofactor_requirements("1.1.1.1")
for cofactor in cofactors:
    print(f"Cofactor: {cofactor['name']}")
    print(f"Type: {cofactor['type']}")
    print(f"Concentration: {cofactor['concentration']}")
```

## 6. Substrate Specificity

**Get Substrate Specificity Data**:
```python
from scripts.brenda_queries import get_substrate_specificity

specificity = get_substrate_specificity("1.1.1.1")

for substrate in specificity:
    print(f"Substrate: {substrate['name']}")
    print(f"Km: {substrate['km']}")
    print(f"Vmax: {substrate['vmax']}")
    print(f"kcat: {substrate['kcat']}")
    print(f"Specificity constant: {substrate['kcat_km_ratio']}")
```

**Compare Substrate Preferences**:
```python
from scripts.brenda_queries import compare_substrate_affinity

comparison = compare_substrate_affinity("1.1.1.1")
sorted_by_km = sorted(comparison, key=lambda x: x['km'])

for substrate in sorted_by_km[:5]:  # Top 5 lowest Km
    print(f"{substrate['name']}: Km = {substrate['km']}")
```

## 7. Inhibition and Activation

**Get Inhibitor Information**:
```python
from scripts.brenda_queries import get_inhibitors

inhibitors = get_inhibitors("1.1.1.1")

for inhibitor in inhibitors:
    print(f"Inhibitor: {inhibitor['name']}")
    print(f"Type: {inhibitor['type']}")
    print(f"Ki: {inhibitor['ki']}")
    print(f"IC50: {inhibitor['ic50']}")
```

**Get Activator Information**:
```python
from scripts.brenda_queries import get_activators

activators = get_activators("1.1.1.1")

for activator in activators:
    print(f"Activator: {activator['name']}")
    print(f"Effect: {activator['effect']}")
    print(f"Mechanism: {activator['mechanism']}")
```

## 8. Enzyme Engineering Support

**Find Thermophilic Homologs**:
```python
from scripts.brenda_queries import find_thermophilic_homologs

thermophilic = find_thermophilic_homologs("1.1.1.1", min_temp=50)

for enzyme in thermophilic:
    print(f"Organism: {enzyme['organism']}")
    print(f"Optimal temp: {enzyme['optimal_temperature']}")
    print(f"Km: {enzyme['km']}")
```

**Find Alkaline/Acid Stable Variants**:
```python
from scripts.brenda_queries import find_ph_stable_variants

alkaline = find_ph_stable_variants("1.1.1.1", min_ph=8.0)
acidic = find_ph_stable_variants("1.1.1.1", max_ph=6.0)
```

## 9. Kinetic Modeling

**Get Kinetic Parameters for Modeling**:
```python
from scripts.brenda_queries import get_modeling_parameters

model_data = get_modeling_parameters("1.1.1.1", substrate="ethanol")

print(f"Km: {model_data['km']}")
print(f"Vmax: {model_data['vmax']}")
print(f"kcat: {model_data['kcat']}")
print(f"Enzyme concentration: {model_data['enzyme_conc']}")
print(f"Temperature: {model_data['temperature']}")
print(f"pH: {model_data['ph']}")
```

**Generate Michaelis-Menten Plots**:
```python
from scripts.brenda_visualization import plot_michaelis_menten

# Generate kinetic plots
plot_michaelis_menten("1.1.1.1", substrate="ethanol")
```
