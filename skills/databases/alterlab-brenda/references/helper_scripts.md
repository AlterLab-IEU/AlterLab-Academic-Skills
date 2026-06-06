# BRENDA — Helper Scripts Reference

This skill ships three helper scripts under `scripts/`. Function inventories below.

## scripts/brenda_queries.py

High-level functions for enzyme data analysis:

- `parse_km_entry(entry)`: Parse BRENDA Km data entries
- `parse_reaction_entry(entry)`: Parse reaction data entries
- `extract_organism_data(entry)`: Extract organism-specific information
- `search_enzymes_by_substrate(substrate, limit)`: Find enzymes for substrates
- `search_enzymes_by_product(product, limit)`: Find enzymes producing products
- `compare_across_organisms(ec_number, organisms)`: Compare enzyme properties
- `get_environmental_parameters(ec_number)`: Get pH and temperature data
- `get_cofactor_requirements(ec_number)`: Get cofactor information
- `get_substrate_specificity(ec_number)`: Analyze substrate preferences
- `get_inhibitors(ec_number)`: Get enzyme inhibition data
- `get_activators(ec_number)`: Get enzyme activation data
- `find_thermophilic_homologs(ec_number, min_temp)`: Find heat-stable variants
- `get_modeling_parameters(ec_number, substrate)`: Get parameters for kinetic modeling
- `export_kinetic_data(ec_number, format, filename)`: Export data to file

```python
from scripts.brenda_queries import search_enzymes_by_substrate, compare_across_organisms

# Search for enzymes
enzymes = search_enzymes_by_substrate("glucose", limit=20)

# Compare across organisms
comparison = compare_across_organisms("1.1.1.1", ["E. coli", "S. cerevisiae"])
```

## scripts/brenda_visualization.py

Visualization functions for enzyme data:

- `plot_kinetic_parameters(ec_number)`: Plot Km and kcat distributions
- `plot_organism_comparison(ec_number, organisms)`: Compare organisms
- `plot_pH_profiles(ec_number)`: Plot pH activity profiles
- `plot_temperature_profiles(ec_number)`: Plot temperature activity profiles
- `plot_substrate_specificity(ec_number)`: Visualize substrate preferences
- `plot_michaelis_menten(ec_number, substrate)`: Generate kinetic curves
- `create_heatmap_data(enzymes, parameters)`: Create data for heatmaps
- `generate_summary_plots(ec_number)`: Create comprehensive enzyme overview

```python
from scripts.brenda_visualization import plot_kinetic_parameters, plot_michaelis_menten

# Plot kinetic parameters
plot_kinetic_parameters("1.1.1.1")

# Generate Michaelis-Menten curve
plot_michaelis_menten("1.1.1.1", substrate="ethanol")
```

## scripts/enzyme_pathway_builder.py

Build enzymatic pathways and retrosynthetic routes:

- `find_pathway_for_product(product, max_steps)`: Find enzymatic pathways
- `build_retrosynthetic_tree(target, depth)`: Build retrosynthetic tree
- `suggest_enzyme_substitutions(ec_number, criteria)`: Suggest enzyme alternatives
- `calculate_pathway_feasibility(pathway)`: Evaluate pathway viability
- `optimize_pathway_conditions(pathway)`: Suggest optimal conditions
- `generate_pathway_report(pathway, filename)`: Create detailed pathway report

```python
from scripts.enzyme_pathway_builder import find_pathway_for_product, build_retrosynthetic_tree

# Find pathway to product
pathway = find_pathway_for_product("lactate", max_steps=3)

# Build retrosynthetic tree
tree = build_retrosynthetic_tree("lactate", depth=2)
```
