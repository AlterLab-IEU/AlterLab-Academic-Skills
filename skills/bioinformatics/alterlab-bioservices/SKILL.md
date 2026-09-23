---
name: alterlab-bioservices
description: Query 40+ bioinformatics web services through one consistent Python API with bioservices (UniProt, KEGG, ChEMBL, Reactome, Ensembl, NCBI and more). Use when a workflow must hit multiple databases together, map identifiers across services, or run cross-database analyses — for quick single-database lookups use gget, for sequence and file manipulation use biopython. Part of the AlterLab Academic Skills suite.
license: GPL-3.0
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*)
compatibility: "Self-contained — runs under `uv run python` with `bioservices` installed (1.16.0 as of 2026-09, Python 3.9–3.14); no API key or account required, though several wrapped services want a contact email."
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# BioServices

## Overview

BioServices is a Python package providing programmatic access to roughly 40 bioinformatics web services and databases. Retrieve biological data, perform cross-database queries, map identifiers, analyze sequences, and integrate multiple biological resources in Python workflows.

**Recent changes that break old scripts** (verified against bioservices 1.16.0):

- **SOAP/WSDL support was removed in 1.15** — every active service is REST now, and the
  `WSDLService` class and its `suds` dependency are gone.
- **`PSICQUIC` and `BioGRID` were removed in 1.14.** For protein interactions use the
  `STRING` class (added in 1.14) or `IntactComplex`; `from bioservices import PSICQUIC`
  raises `ImportError`.
- **`UniProt.mapping()` returns the raw UniProt job payload** —
  `{"results": [{"from": ..., "to": ...}, ...], "failedIds": [...]}` — not a
  `{source_id: [target_ids]}` dict. See "Identifier Mapping" below.
- **NCBIblast methods are snake_case** (`get_status`, `get_result`, `get_result_types`,
  `wait`); the old `getStatus`/`getResult` camelCase names are gone. 1.16 also adds
  `ncbiblastapi.NCBIBlastAPI`, which submits to NCBI directly instead of EBI.

## When to Use This Skill

This skill should be used when:
- Retrieving protein sequences, annotations, or structures from UniProt, PDB, Pfam
- Analyzing metabolic pathways and gene functions via KEGG or Reactome
- Searching compound databases (ChEBI, ChEMBL, PubChem) for chemical information
- Converting identifiers between different biological databases (KEGG↔UniProt, compound IDs)
- Running sequence similarity searches (BLAST, MUSCLE alignment)
- Querying gene ontology terms (QuickGO, GO annotations)
- Accessing protein-protein interaction data (STRING, IntactComplex)
- Mining genomic data (BioMart, ArrayExpress, ENA)
- Integrating data from multiple bioinformatics resources in a single workflow

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| A single quick lookup (one gene, one structure, one enrichment) | `alterlab-gget` |
| Parsing sequence/structure files or scripting Entrez directly | `alterlab-biopython` |
| Local BLAST+ / `makeblastdb` / DIAMOND on your own database | `alterlab-blast` |
| Deep work in one database (full KEGG, UniProt, or ChEMBL feature set) | `alterlab-kegg`, `alterlab-uniprot`, `alterlab-chembl` |
| Cheminformatics on the retrieved structures (descriptors, fingerprints) | `alterlab-rdkit` |

## Core Capabilities

### 1. Protein Analysis

Retrieve protein information, sequences, and functional annotations:

```python
from bioservices import UniProt

u = UniProt(verbose=False)

# Search for protein by name. frmt is one of xlsx/fasta/json/gff/tsv — "tab" was
# retired with the June-2022 UniProt API and now raises.
results = u.search("ZAP70_HUMAN", frmt="tsv", columns="accession,gene_names,organism_name")

# Retrieve FASTA sequence (frmt defaults to json)
sequence = u.retrieve("P43403", frmt="fasta")

# Map identifiers between databases -> {"results": [{"from": ..., "to": ...}], "failedIds": [...]}
job = u.mapping(fr="UniProtKB_AC-ID", to="KEGG", query="P43403")
kegg_ids = [r["to"] for r in job["results"]]
```

**Key methods:**
- `search()`: Query UniProt with flexible search terms (`frmt="tsv"`, `columns` as UniProt
  return-field names such as `accession`, `gene_names`, `organism_name`, `length`)
- `retrieve()`: Get protein entries in various formats (json, txt, xml, rdf, gff, fasta)
- `mapping()`: Submit an ID-mapping job and return its results payload

Reference: `references/services_reference.md` for complete UniProt API details.

### 2. Pathway Discovery and Analysis

Access KEGG pathway information for genes and organisms:

```python
from bioservices import KEGG

k = KEGG()
k.organism = "hsa"  # Set to human

# Search for organisms
k.lookfor_organism("droso")  # Find Drosophila species

# Find pathways by name
k.lookfor_pathway("B cell")  # Returns matching pathway IDs

# Get pathways containing specific genes
pathways = k.get_pathway_by_gene("7535", "hsa")  # ZAP70 gene

# Retrieve and parse pathway data
data = k.get("hsa04660")
parsed = k.parse(data)

# Extract pathway interactions
interactions = k.parse_kgml_pathway("hsa04660")
relations = interactions['relations']  # Protein-protein interactions

# Convert to Simple Interaction Format
sif_data = k.pathway2sif("hsa04660")
```

**Key methods:**
- `lookfor_organism()`, `lookfor_pathway()`: Search by name
- `get_pathway_by_gene()`: Find pathways containing genes
- `parse_kgml_pathway()`: Extract structured pathway data
- `pathway2sif()`: Get protein interaction networks

Reference: `references/workflow_patterns.md` for complete pathway analysis workflows.

### 3. Compound Database Searches

Search and cross-reference compounds across multiple databases:

```python
from bioservices import KEGG

k = KEGG()

# Search compounds by name — the tab-separated result rows are "C11222\tGeldanamycin"
results = k.find("compound", "Geldanamycin")

# Get compound information with database links
compound_info = k.get("cpd:C11222")  # Includes ChEBI links

# Cross-reference KEGG compound → ChEBI (KEGG→ChEMBL has no direct API)
mapping = k.conv("chebi", "compound")
mapping["cpd:C11222"]   # -> 'chebi:5292'  (Geldanamycin)
```

**Common workflow:**
1. Search compound by name in KEGG
2. Extract KEGG compound ID
3. Use `KEGG.conv` for KEGG → ChEBI mapping (ChEBI IDs are also embedded in KEGG entries)
4. If a ChEMBL ID is required, obtain it via a separate route (the ChEMBL web service / `chembl_webresource_client`, or the live UniChem REST API directly) — there is no bioservices `UniChem` convenience method for KEGG → ChEMBL

Reference: `references/identifier_mapping.md` for complete cross-database mapping guide.

### 4. Sequence Analysis

Run BLAST searches and sequence alignments:

```python
from bioservices import NCBIblast

s = NCBIblast(verbose=False)

# Run BLASTP against UniProtKB via the EBI job service
jobid = s.run(
    program="blastp",
    sequence=protein_sequence,
    stype="protein",
    database="uniprotkb",
    email="your.email@example.com"  # a real address is required; jobs are killed without one
)

# Poll, then fetch. Method names are snake_case since the API refresh.
s.wait(jobid)                    # blocks until the job leaves RUNNING
status = s.get_status(jobid)     # RUNNING | FINISHED | ERROR | FAILURE | NOT_FOUND
results = s.get_result(jobid, "out")
print(s.get_result_types(jobid))  # what formats this job can return
```

BLAST jobs are asynchronous — check the status (or call `wait`) before retrieving results.
For jobs submitted to NCBI rather than EBI, bioservices 1.16 adds
`from bioservices import NCBIBlastAPI` with the same run/get_status/get_result shape.

### 5. Identifier Mapping

Convert identifiers between different biological databases:

```python
from bioservices import UniProt, KEGG

# UniProt mapping (many database pairs supported)
u = UniProt()
job = u.mapping(
    fr="UniProtKB_AC-ID",  # Source database
    to="KEGG",              # Target database
    query="P43403"          # Identifier(s) to convert; a list is also accepted
)

# The payload is {"results": [{"from": ..., "to": ...}], "failedIds": [...]}.
# Collapse it yourself when you want a per-source-ID dict:
from collections import defaultdict

mapped = defaultdict(list)
for row in job["results"]:
    mapped[row["from"]].append(row["to"])

# KEGG gene ID -> UniProt. Non-UniProt sources may only map *to* UniProtKB,
# so "KEGG" -> "UniProtKB" is valid while "KEGG" -> "UniProtKB_AC-ID" is not.
kegg_to_uniprot = u.mapping(fr="KEGG", to="UniProtKB", query="hsa:7535")

# For compounds, map KEGG → ChEBI via KEGG.conv
# (KEGG → ChEMBL has no direct API; obtain ChEMBL IDs separately
#  via the ChEMBL web service / chembl_webresource_client or the
#  live UniChem REST API directly)
k = KEGG()
kegg_to_chebi = k.conv("chebi", "compound")
chebi_from_kegg = kegg_to_chebi["cpd:C11222"]  # -> 'chebi:5292'
```

**Supported mappings (UniProt):**
- UniProtKB ↔ KEGG
- UniProtKB ↔ Ensembl
- UniProtKB ↔ PDB
- UniProtKB ↔ RefSeq
- And many more (see `references/identifier_mapping.md`)

### 6. Gene Ontology Queries

Access GO terms and annotations:

```python
from bioservices import QuickGO

g = QuickGO(verbose=False)

# Retrieve GO term information (returns parsed JSON from the QuickGO REST API)
term_info = g.get_go_terms("GO:0003824")
ancestors = g.get_go_ancestors("GO:0003824")

# Annotations: the parameters follow the QuickGO REST API, not the old
# protein=/format= signature. geneProductId is prefixed, limit is capped at 100.
annotations = g.Annotation(
    geneProductId="UniProtKB:P43403",
    includeFields="goName",
    limit=100,
    page=1,
)
for row in annotations["results"][:5]:
    print(row["goId"], row["goName"], row["goAspect"])
```

`Annotation` returns a dict with `numberOfHits` and `results`; page through it rather than
raising `limit` (values above 100 raise a `TypeError`).

### 7. Protein-Protein Interactions

PSICQUIC and BioGRID were removed from bioservices in 1.14. Use the STRING service (or
`IntactComplex` for curated complexes):

```python
from bioservices import STRING

s = STRING()

# Functional + physical partners of a protein
partners = s.get_interaction_partners("ZAP70", species=9606, limit=20)

# Interactions within a given set of proteins
network = s.get_interactions(["ZAP70", "CD247", "LCK"], species=9606)

for row in partners:
    print(row["preferredName_A"], row["preferredName_B"], row["score"])
```

`network_type="physical"` restricts to physical complexes; `required_score` (0–1000) sets
the confidence floor. STRING scores are 0–1 in the JSON output.

## Multi-Service Integration Workflows

BioServices excels at combining multiple services for comprehensive analysis. Common integration patterns:

### Complete Protein Analysis Pipeline

Execute a full protein characterization workflow:

```bash
python scripts/protein_analysis_workflow.py ZAP70_HUMAN your.email@example.com
```

This script demonstrates:
1. UniProt search for protein entry
2. FASTA sequence retrieval
3. BLAST similarity search
4. KEGG pathway discovery
5. STRING interaction mapping

### Pathway Network Analysis

Analyze all pathways for an organism:

```bash
python scripts/pathway_analysis.py hsa output_directory/
```

Extracts and analyzes:
- All pathway IDs for organism
- Protein-protein interactions per pathway
- Interaction type distributions
- Exports to CSV/SIF formats

### Cross-Database Compound Search

Map compound identifiers across databases:

```bash
python scripts/compound_cross_reference.py Geldanamycin
```

Retrieves:
- KEGG compound ID
- ChEBI identifier
- ChEMBL identifier
- Basic compound properties

### Batch Identifier Conversion

Convert multiple identifiers at once:

```bash
python scripts/batch_id_converter.py input_ids.txt --from UniProtKB_AC-ID --to KEGG
```

## Best Practices

### Output Format Handling

Different services return data in various formats:
- **XML**: Parse using BeautifulSoup (most SOAP services)
- **Tab-separated (TSV)**: Pandas DataFrames for tabular data
- **Dictionary/JSON**: Direct Python manipulation
- **FASTA**: BioPython integration for sequence analysis

### Rate Limiting and Verbosity

Control API request behavior:

```python
from bioservices import KEGG

k = KEGG(verbose=False)  # Suppress HTTP request details
k.TIMEOUT = 30  # Adjust timeout for slow connections
```

### Error Handling

Wrap service calls in try-except blocks:

```python
try:
    results = u.search("ambiguous_query")
    if results:
        # Process results
        pass
except Exception as e:
    print(f"Search failed: {e}")
```

### Organism Codes

Use standard organism abbreviations:
- `hsa`: Homo sapiens (human)
- `mmu`: Mus musculus (mouse)
- `dme`: Drosophila melanogaster
- `sce`: Saccharomyces cerevisiae (yeast)

List all organisms: `k.list("organism")` or `k.organismIds`

### Integration with Other Tools

BioServices works well with:
- **BioPython**: Sequence analysis on retrieved FASTA data
- **Pandas**: Tabular data manipulation
- **PyMOL**: 3D structure visualization (retrieve PDB IDs)
- **NetworkX**: Network analysis of pathway interactions
- **Galaxy**: Custom tool wrappers for workflow platforms

## Resources

### scripts/

Executable Python scripts demonstrating complete workflows:

- `protein_analysis_workflow.py`: End-to-end protein characterization
- `pathway_analysis.py`: KEGG pathway discovery and network extraction
- `compound_cross_reference.py`: Multi-database compound searching
- `batch_id_converter.py`: Bulk identifier mapping utility

Scripts can be executed directly or adapted for specific use cases.

### references/

Detailed documentation loaded as needed:

- `services_reference.md`: Comprehensive list of all 40+ services with methods
- `workflow_patterns.md`: Detailed multi-step analysis workflows
- `identifier_mapping.md`: Complete guide to cross-database ID conversion

Load references when working with specific services or complex integration tasks.

## Installation

```bash
uv pip install bioservices
```

Dependencies are automatically managed. Package is tested on Python 3.9-3.12.

## Additional Information

For detailed API documentation and advanced features, refer to:
- Official documentation: https://bioservices.readthedocs.io/
- Source code: https://github.com/cokelaer/bioservices
- Service-specific references in `references/services_reference.md`

Part of the AlterLab Academic Skills suite.
