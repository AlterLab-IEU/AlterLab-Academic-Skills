# UniProt Query Syntax Reference

Comprehensive guide to UniProt search query syntax for constructing complex searches.

## Basic Syntax

### Simple Queries
```
insulin
kinase
```

### Field-Specific Searches
```
gene:BRCA1
accession:P12345
organism_name:human
protein_name:kinase
```

## Boolean Operators

### AND (both terms must be present)
```
insulin AND diabetes
kinase AND human
gene:BRCA1 AND reviewed:true
```

### OR (either term can be present)
```
diabetes OR insulin
(cancer OR tumor) AND human
```

### NOT (exclude terms)
```
kinase NOT human
protein_name:kinase NOT organism_name:mouse
```

### Grouping with Parentheses
```
(diabetes OR insulin) AND reviewed:true
(gene:BRCA1 OR gene:BRCA2) AND organism_id:9606
```

## Common Search Fields

### Identification
- `accession:P12345` - UniProt accession number
- `id:INSR_HUMAN` - Entry name
- `gene:BRCA1` - Gene name
- `gene_exact:BRCA1` - Exact gene name match

### Organism/Taxonomy
- `organism_name:human` - Organism name
- `organism_name:"Homo sapiens"` - Exact organism name (use quotes for multi-word)
- `organism_id:9606` - NCBI taxonomy ID
- `taxonomy_id:9606` - Same as organism_id
- `taxonomy_name:"Homo sapiens"` - Taxonomy name

### Protein Information
- `protein_name:insulin` - Protein name
- `protein_name:"insulin receptor"` - Exact protein name
- `reviewed:true` - Only Swiss-Prot (reviewed) entries
- `reviewed:false` - Only TrEMBL (unreviewed) entries

### Sequence Properties
- `length:[100 TO 500]` - Sequence length range
- `mass:[50000 TO 100000]` - Molecular mass in Daltons
- Exact/partial sequence matching is not a query field (`sequence:...` returns HTTP 400) — use UniProt BLAST or Peptide Search, or `alterlab-blast`
- `fragment:false` - Exclude fragment sequences

### Gene Ontology (GO)
- `go:0005515` - GO term ID (0005515 = protein binding)
- `go:kinase` - GO term text match
- (`go_f`, `go_p`, `go_c` are **return** fields for `fields=`, not query fields — `go_f:*` returns HTTP 400)

### Annotations
- `ft_signal:*` - Has signal peptide annotation (legacy `annotation:(type:signal)` returns HTTP 400)
- `ft_transmem:*` - Has transmembrane region
- `cc_function:*` - Has function comment
- `cc_interaction:*` - Has interaction comment
- `ft_domain:*` - Has domain feature

### Database Cross-References
- `database:pdb` or `structure_3d:true` - Has a PDB structure
- `database:ensembl` - Has an Ensembl cross-reference
- `xref:pdb-4hhb` - Cross-reference to one specific record (`xref:` needs `<db>-<id>`; bare `xref:pdb` matches nothing)

### Protein Families and Domains
- `family:"protein kinase"` - Protein family
- `keyword:"Protein kinase"` - Keyword annotation
- `cc_similarity:*` - Has similarity comment

## Range Queries

### Numeric Ranges
```
length:[100 TO 500]          # Between 100 and 500
mass:[* TO 50000]            # Less than or equal to 50000
date_created:[2023-01-01 TO *]   # Created after Jan 1, 2023
```

### Date Ranges
```
date_created:[2023-01-01 TO 2023-12-31]
date_modified:[2024-01-01 TO *]      # plain created:/modified: return HTTP 400
```

## Wildcards

### Single Character (?)
```
gene:BRCA?      # Matches BRCA1, BRCA2, etc.
```

### Multiple Characters (*)
```
gene:BRCA*      # Matches BRCA1, BRCA2, BRCA1P1, etc.
protein_name:kinase*
organism_name:Homo*
```

## Advanced Searches

### Existence Queries
```
cc_function:*              # Has any function annotation
ft_domain:*                # Has any domain feature
database:pdb               # Has PDB structure
```

### Combined Complex Queries
```
# Human reviewed kinases with PDB structure
(protein_name:kinase OR family:kinase) AND organism_id:9606 AND reviewed:true AND database:pdb

# Cancer-related proteins excluding mice
(cc_disease:cancer OR keyword:cancer) NOT organism_name:mouse

# Membrane proteins with signal peptides
ft_transmem:* AND ft_signal:* AND reviewed:true

# Recently updated human proteins
organism_id:9606 AND date_modified:[2024-01-01 TO *] AND reviewed:true
```

## Field-Specific Examples

### Protein Names
```
protein_name:"insulin receptor"    # Exact phrase
protein_name:insulin*              # Starts with insulin
recommended_name:insulin           # Recommended name only
alternative_name:insulin           # Alternative names only
```

### Genes
```
gene:BRCA1                        # Gene symbol
gene_exact:BRCA1                  # Exact gene match
olnName:BRCA1                     # Ordered locus name
orfName:BRCA1                     # ORF name
```

### Organisms
```
organism_name:human               # Common name
organism_name:"Homo sapiens"      # Scientific name
organism_id:9606                  # Taxonomy ID
lineage:primates                  # Taxonomic lineage
```

### Features
```
ft_signal:*                       # Signal peptide
ft_transmem:*                     # Transmembrane region
ft_domain:"Protein kinase"        # Specific domain
ft_binding:*                      # Binding site
ft_site:*                         # Any site
```

### Comments (cc_)
```
cc_function:*                     # Function description
cc_catalytic_activity:*           # Catalytic activity
cc_pathway:*                      # Pathway involvement
cc_interaction:*                  # Protein interactions
cc_subcellular_location:*         # Subcellular location
cc_tissue_specificity:*           # Tissue specificity
cc_disease:cancer                 # Disease association
```

## Tips and Best Practices

1. **Use quotes for exact phrases**: `organism_name:"Homo sapiens"` not `organism_name:Homo sapiens`

2. **Filter by review status**: Add `AND reviewed:true` for high-quality Swiss-Prot entries

3. **Combine wildcards carefully**: `*kinase*` may be too broad; `kinase*` is more specific

4. **Use parentheses for complex logic**: `(A OR B) AND (C OR D)` is clearer than `A OR B AND C OR D`

5. **Numeric ranges are inclusive**: `length:[100 TO 500]` includes both 100 and 500

6. **Field prefixes**: Learn common prefixes:
   - `cc_` = Comments
   - `ft_` = Features
   - `go_` = Gene Ontology
   - `xref_` = Cross-references

7. **Check field names**: Use the API's `/configure/uniprotkb/result-fields` endpoint to see all available fields

## Query Validation

Test queries using:
- **Web interface**: https://www.uniprot.org/uniprotkb
- **API**: https://rest.uniprot.org/uniprotkb/search?query=YOUR_QUERY
- **API documentation**: https://www.uniprot.org/help/query-fields

## Common Patterns

### Find well-characterized proteins
```
reviewed:true AND database:pdb AND cc_function:*
```

### Find disease-associated proteins
```
cc_disease:* AND organism_id:9606 AND reviewed:true
```

### Find proteins with experimental evidence
```
existence:1 AND reviewed:true     # 1 = evidence at protein level ... 5 = uncertain
```

### Find secreted proteins
```
cc_subcellular_location:secreted AND reviewed:true
```

### Find drug targets
```
keyword:"Pharmaceutical" OR keyword:"Drug target"
```

## Resources

- Full query field reference: https://www.uniprot.org/help/query-fields
- API query documentation: https://www.uniprot.org/help/api_queries
- Text search documentation: https://www.uniprot.org/help/text-search
