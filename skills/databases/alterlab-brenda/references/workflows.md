# BRENDA — Common Workflows

End-to-end recipes built on the helper scripts. See `helper_scripts.md` for the function
inventory and `capabilities.md` for per-capability snippets.

## Workflow 1: Enzyme Discovery for New Substrate

Find suitable enzymes for a specific substrate:

Note: `getKmValue` entries carry no `ecNumber`, so to recover EC numbers and
reaction equations for a substrate, discover via reaction data (`search_by_pattern`),
then pull kinetics with `get_km_values`.

```python
from scripts.brenda_client import get_km_values
from scripts.brenda_queries import search_by_pattern

# Discover enzymes whose reactions mention the substrate (these entries have ecNumber)
substrate = "2-phenylethanol"
hits = search_by_pattern(substrate, limit=15)

print(f"Found {len(hits)} reaction hits for {substrate}")
for hit in hits:
    print(f"EC {hit['ec_number']} ({hit['organism']}): {hit['reaction']}")

# Get kinetic data for the first candidate with an EC number
candidates = [h for h in hits if h['ec_number']]
if candidates:
    best_ec = candidates[0]['ec_number']
    km_data = get_km_values(best_ec, substrate=substrate)

    if km_data:
        print(f"Kinetic data for {best_ec}:")
        for entry in km_data[:3]:  # First 3 entries
            print(f"  {entry}")
```

## Workflow 2: Cross-Organism Enzyme Comparison

Compare enzyme properties across different organisms:

```python
from scripts.brenda_queries import compare_across_organisms, get_environmental_parameters

# Define organisms for comparison
organisms = [
    "Escherichia coli",
    "Saccharomyces cerevisiae",
    "Bacillus subtilis",
    "Thermus thermophilus"
]

# Compare alcohol dehydrogenase
comparison = compare_across_organisms("1.1.1.1", organisms)

print("Cross-organism comparison:")
for org_data in comparison:
    print(f"\n{org_data['organism']}:")
    print(f"  Average Km: {org_data['average_km']}")
    print(f"  Optimal pH: {org_data['optimal_ph']}")
    print(f"  Temperature: {org_data['optimal_temperature']}°C")

# Get detailed environmental parameters
env_params = get_environmental_parameters("1.1.1.1")
print(f"\nOverall optimal pH range: {env_params['ph_range']}")
```

## Workflow 3: Enzyme Engineering Target Identification

Find engineering opportunities for enzyme improvement:

```python
from scripts.brenda_queries import (
    find_thermophilic_homologs,
    find_ph_stable_variants,
    compare_substrate_affinity
)

# Find thermophilic variants for heat stability
thermophilic = find_thermophilic_homologs("1.1.1.1", min_temp=50)
print(f"Found {len(thermophilic)} thermophilic variants")

# Find alkaline-stable variants
alkaline = find_ph_stable_variants("1.1.1.1", min_ph=8.0)
print(f"Found {len(alkaline)} alkaline-stable variants")

# Compare substrate specificities for engineering targets
specificity = compare_substrate_affinity("1.1.1.1")
print("Substrate affinity ranking:")
for i, sub in enumerate(specificity[:5]):
    print(f"  {i+1}. {sub['name']}: Km = {sub['km']}")
```

## Workflow 4: Enzymatic Pathway Construction

Build enzymatic synthesis pathways:

```python
from scripts.enzyme_pathway_builder import (
    find_pathway_for_product,
    build_retrosynthetic_tree,
    calculate_pathway_feasibility
)

# Find pathway to target product
target = "lactate"
pathway = find_pathway_for_product(target, max_steps=3)

if pathway:
    print(f"Found pathway to {target}:")
    for i, step in enumerate(pathway['steps']):
        print(f"  Step {i+1}: {step['reaction']}")
        print(f"    Enzyme: EC {step['ec_number']}")
        print(f"    Organism: {step['organism']}")

# Evaluate pathway feasibility
feasibility = calculate_pathway_feasibility(pathway)
print(f"\nPathway feasibility score: {feasibility['score']}/10")
print(f"Potential issues: {feasibility['warnings']}")
```

## Workflow 5: Kinetic Parameter Analysis

Comprehensive kinetic analysis for enzyme selection:

```python
from scripts.brenda_client import get_km_values
from scripts.brenda_queries import parse_km_entry, get_modeling_parameters
from scripts.brenda_visualization import plot_kinetic_parameters

# Get comprehensive kinetic data
ec_number = "1.1.1.1"
km_data = get_km_values(ec_number)

# Analyze kinetic parameters. parse_km_entry only sets 'km_value_numeric'
# when the raw kmValue field contained a parseable number, so filter on it.
all_entries = []
for entry in km_data:
    parsed = parse_km_entry(entry)
    if parsed.get('km_value_numeric') is not None:
        all_entries.append(parsed)

print(f"Analyzed {len(all_entries)} kinetic entries")

# Find best kinetic performer (lowest Km = highest affinity)
best_km = min(all_entries, key=lambda x: x['km_value_numeric'])
print(f"\nBest kinetic performer:")
print(f"  Organism: {best_km.get('organism')}")
print(f"  Substrate: {best_km.get('substrate')}")
print(f"  Km: {best_km['km_value_numeric']}")

# Get modeling parameters
model_data = get_modeling_parameters(ec_number, substrate=best_km['substrate'])
print(f"\nModeling parameters:")
print(f"  Km: {model_data['km']}")
print(f"  kcat: {model_data['kcat']}")
print(f"  Vmax: {model_data['vmax']}")

# Generate visualization
plot_kinetic_parameters(ec_number)
```

## Workflow 6: Industrial Enzyme Selection

Select enzymes for industrial applications:

```python
from scripts.brenda_queries import (
    find_thermophilic_homologs,
    get_environmental_parameters,
    get_inhibitors
)

# Industrial criteria: high temperature tolerance, organic solvent resistance
target_enzyme = "1.1.1.1"

# Find thermophilic variants
thermophilic = find_thermophilic_homologs(target_enzyme, min_temp=60)
print(f"Thermophilic candidates: {len(thermophilic)}")

# Check solvent tolerance (inhibitor data)
inhibitors = get_inhibitors(target_enzyme)
solvent_tolerant = [
    inv for inv in inhibitors
    if 'ethanol' not in inv['name'].lower() and
       'methanol' not in inv['name'].lower()
]

print(f"Solvent tolerant candidates: {len(solvent_tolerant)}")

# Evaluate top candidates
for candidate in thermophilic[:3]:
    print(f"\nCandidate: {candidate['organism']}")
    print(f"  Optimal temp: {candidate['optimal_temperature']}°C")
    print(f"  Km: {candidate['km']}")
    print(f"  pH range: {candidate.get('ph_range', 'N/A')}")
```
