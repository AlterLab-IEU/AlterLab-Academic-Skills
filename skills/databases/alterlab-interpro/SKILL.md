---
name: alterlab-interpro
description: Query the EMBL-EBI InterPro REST API for protein family, domain, and functional-site annotations integrated from member databases (Pfam, PANTHER, PRINTS, SMART, SUPERFAMILY, CDD, ProSite, NCBIfam, and others). Use when predicting protein function, analyzing or comparing domain architecture, classifying a protein by family or homologous superfamily, resolving a Pfam/InterPro accession, or mapping a protein's signatures to GO terms. Not for raw UniProt entry/FASTA retrieval or AlphaFold 3D structures. Part of the AlterLab Academic Skills suite.
license: CC0-1.0
allowed-tools: Read WebFetch Bash(curl:*) Bash(python:*)
compatibility: Keyless InterPro REST API (no authentication required)
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# InterPro Database

## Overview

InterPro (https://www.ebi.ac.uk/interpro/) is a comprehensive resource for protein family and domain classification maintained by EMBL-EBI. It integrates predictive signatures from its member databases — including Pfam, PANTHER, PRINTS, ProSite, SMART, NCBIfam, SUPERFAMILY, CDD, Gene3D, and others (see the member-database table below) — into a unified set of entries, providing a single view of functional annotation across UniProtKB. (The legacy TIGRFAMs were absorbed into NCBIfam.)

InterPro classifies proteins into:
- **Families**: Groups of proteins sharing common ancestry and function
- **Domains**: Independently folding structural/functional units
- **Homologous superfamilies**: Structurally similar protein regions
- **Repeats**: Short tandem sequences
- **Sites**: Functional sites (active, binding, PTM)

**Key resources:**
- InterPro website: https://www.ebi.ac.uk/interpro/
- REST API: https://www.ebi.ac.uk/interpro/api/
- API documentation: https://github.com/ProteinsWebTeam/interpro7-api/blob/master/docs/
- Python client: via `requests`

## Scripts

`scripts/query_interpro.py` — query the InterPro REST API (stdlib only, JSON to stdout):

```bash
python scripts/query_interpro.py protein P04637          # InterPro entries for a UniProt protein
python scripts/query_interpro.py entry IPR000719         # entry details
python scripts/query_interpro.py entry-proteins IPR000719 --page-size 25   # proteins with an entry
```

## When to Use This Skill

Use InterPro when:

- **Protein function prediction**: What function(s) does an uncharacterized protein likely have?
- **Domain architecture**: What domains make up a protein, and in what order?
- **Protein family classification**: Which family/superfamily does a protein belong to?
- **GO term annotation**: Map protein sequences to Gene Ontology terms via InterPro
- **Evolutionary analysis**: Are two proteins in the same homologous superfamily?
- **Structure prediction context**: What domains should a new protein structure be compared against?
- **Pipeline annotation**: Batch-annotate proteomes or novel sequences

## Core Capabilities

### 1. InterPro REST API

Base URL: `https://www.ebi.ac.uk/interpro/api/`

```python
import requests

BASE_URL = "https://www.ebi.ac.uk/interpro/api"

def interpro_get(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"
    headers = {"Accept": "application/json"}
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()
```

**Endpoint direction gotcha (read this first).** In the InterPro API the *first*
path segment is the resource type you get back. To list **entries** for a
protein, the protein filter goes last: `entry/InterPro/protein/UniProt/{id}/`.
To list **proteins** for an entry, the protein resource goes first:
`protein/UniProt/entry/InterPro/{id}/`. The reversed forms
(`protein/UniProt/{id}/entry/InterPro/`, `entry/InterPro/{id}/protein/UniProt/`)
return only a `*_url` wrapper with no `results` and `count: null` — a silent
empty, not an error.

### 2. Look Up a Protein

```python
def get_protein_entries(uniprot_id):
    """Get all InterPro entries that match a UniProt protein."""
    # Resource (entry) first, protein filter last — see direction gotcha above.
    data = interpro_get(f"entry/InterPro/protein/UniProt/{uniprot_id}/")
    return data

# Example: Human p53 (TP53)
result = get_protein_entries("P04637")
entries = result.get("results", [])

for entry in entries:
    meta = entry["metadata"]  # `name` is a string on this grouped endpoint
    print(f"  {meta['accession']} ({meta['type']}): {meta['name']}")
    # e.g., IPR002117 (family): p53 tumour suppressor family
    #       IPR011615 (domain): p53, DNA-binding domain
    #       IPR010991 (domain): p53, tetramerisation domain
```

### 3. Get Specific InterPro Entry

```python
def get_entry(interpro_id):
    """Fetch details for an InterPro entry."""
    return interpro_get(f"entry/InterPro/{interpro_id}/")

# Example: Get the InterPro entry the WW domain maps to
ww_entry = get_entry("IPR001202")
# On the single-entry detail endpoint, `name` is a dict {"name", "short"};
# on list/grouped endpoints it is a plain string. Handle both:
name = ww_entry["metadata"]["name"]
print(f"Name: {name['name'] if isinstance(name, dict) else name}")
print(f"Type: {ww_entry['metadata']['type']}")  # -> domain

# Member-database accessions resolve through the same endpoint shape.
# Use lowercase db names (entry/pfam/...); the response carries the
# integrated InterPro accession under metadata['integrated'].
def get_pfam_entry(pfam_id):
    return interpro_get(f"entry/pfam/{pfam_id}/")

pfam = get_pfam_entry("PF00397")  # metadata['integrated'] == 'IPR001202'
```

### 4. Search Proteins by InterPro Entry

```python
def get_proteins_for_entry(interpro_id, database="UniProt", page_size=25):
    """Get all proteins annotated with an InterPro entry."""
    params = {"page_size": page_size}
    # Resource (protein) first, entry filter last — see direction gotcha above.
    data = interpro_get(f"protein/{database}/entry/InterPro/{interpro_id}/", params)
    return data

# Example: count proteins carrying the protein kinase domain
kinase_proteins = get_proteins_for_entry("IPR000719")  # Protein kinase domain
print(f"Total proteins: {kinase_proteins['count']}")  # response has count/next/results
```

### 5. Domain Architecture

Per-residue match locations live on the **entry/protein grouped** endpoint, not
on the bare `protein/UniProt/{id}/` record (that record only carries
`metadata`, with no `entries` key). Each entry's hits are under
`results[].proteins[].entry_protein_locations[].fragments[]`:

```python
def get_domain_architecture(uniprot_id):
    """Get the domain architecture of a protein with sequence positions."""
    data = interpro_get(f"entry/InterPro/protein/UniProt/{uniprot_id}/")

    arch = []
    for result in data.get("results", []):
        meta = result["metadata"]
        for prot in result.get("proteins", []):
            for loc in prot.get("entry_protein_locations", []):
                for frag in loc.get("fragments", []):
                    arch.append({
                        "accession": meta["accession"],
                        "type": meta["type"],
                        "name": meta["name"],
                        "start": frag["start"],
                        "end": frag["end"],
                    })
    # Order along the sequence to read off the architecture N->C terminus
    arch.sort(key=lambda d: d["start"])
    return arch

# Example: full domain architecture for EGFR, ordered along the sequence
for d in get_domain_architecture("P00533"):
    print(f"  {d['start']:>5}-{d['end']:<5} {d['accession']} ({d['type']}): {d['name']}")
```

### 6. GO Term Mapping

The protein record aggregates GO terms from all of its InterPro signatures under
`metadata.go_terms` (already deduplicated), so no per-entry walk is needed:

```python
def get_go_terms_for_protein(uniprot_id):
    """Get GO terms associated with a protein via InterPro."""
    data = interpro_get(f"protein/UniProt/{uniprot_id}/")
    # NB: go_terms can be present but null for proteins with no GO mapping,
    # so coalesce to [] rather than relying on the dict default.
    return data.get("metadata", {}).get("go_terms") or []

# GO terms look like:
# {"identifier": "GO:0004672", "name": "protein kinase activity",
#  "category": {"code": "F", "name": "molecular_function"}}
# category.code is one of F (molecular_function), P (biological_process),
# C (cellular_component).
```

To attribute GO terms to specific signatures instead of the protein as a whole,
read `metadata.go_terms` on each entry from
`entry/InterPro/protein/UniProt/{id}/` (each entry carries its own `go_terms`).

### 7. Batch Protein Lookup

```python
def batch_lookup_proteins(uniprot_ids, database="UniProt"):
    """Look up multiple proteins and collect their InterPro entries."""
    import time
    results = {}
    for uid in uniprot_ids:
        try:
            data = interpro_get(f"entry/InterPro/protein/{database}/{uid}/")
            entries = data.get("results", [])
            results[uid] = [
                {
                    "accession": e["metadata"]["accession"],
                    "name": e["metadata"]["name"],
                    "type": e["metadata"]["type"]
                }
                for e in entries
            ]
        except Exception as e:
            results[uid] = {"error": str(e)}
        time.sleep(0.3)  # Rate limiting
    return results

# Example
proteins = ["P04637", "P00533", "P38398", "Q9Y6I9"]
domain_info = batch_lookup_proteins(proteins)
for uid, entries in domain_info.items():
    print(f"\n{uid}:")
    for e in entries[:3]:
        print(f"  - {e['accession']} ({e['type']}): {e['name']}")
```

### 8. Search by Text or Taxonomy

```python
def search_entries(query, entry_type=None, taxonomy_id=None):
    """Search InterPro entries by text."""
    params = {"search": query, "page_size": 20}
    if entry_type:
        params["type"] = entry_type  # family, domain, homologous_superfamily, etc.

    endpoint = "entry/InterPro/"
    if taxonomy_id:
        # taxonomy is a filter, not the returned resource, so it can follow
        # the entry resource directly (lowercase 'uniprot' in the path).
        endpoint = f"entry/InterPro/taxonomy/uniprot/{taxonomy_id}/"

    return interpro_get(endpoint, params)

# Search for kinase-related entries
kinase_entries = search_entries("kinase", entry_type="domain")
```

## Query Workflows

### Workflow 1: Characterize an Unknown Protein

1. **Run InterProScan** locally or via the web (https://www.ebi.ac.uk/interpro/search/sequence/) to scan a protein sequence
2. **Parse results** to identify domain architecture
3. **Look up each InterPro entry** for biological context
4. **Get GO terms** from associated InterPro entries for functional inference

```python
# After running InterProScan and getting a UniProt ID:
def characterize_protein(uniprot_id):
    """Complete characterization workflow."""

    # 1. Get all annotations
    entries = get_protein_entries(uniprot_id)

    # 2. Group by type
    by_type = {}
    for e in entries.get("results", []):
        t = e["metadata"]["type"]
        by_type.setdefault(t, []).append({
            "accession": e["metadata"]["accession"],
            "name": e["metadata"]["name"]
        })

    # 3. Get GO terms
    go_terms = get_go_terms_for_protein(uniprot_id)

    return {
        "families": by_type.get("family", []),
        "domains": by_type.get("domain", []),
        "superfamilies": by_type.get("homologous_superfamily", []),
        "go_terms": go_terms
    }
```

### Workflow 2: Find All Members of a Protein Family

1. Identify the InterPro family entry ID (e.g., IPR000719 for protein kinases)
2. Query all UniProt proteins annotated with that entry
3. Filter by organism/taxonomy if needed
4. Download FASTA sequences for phylogenetic analysis

### Workflow 3: Comparative Domain Analysis

1. Collect proteins of interest (e.g., all paralogs)
2. Get domain architecture for each protein
3. Compare domain compositions and orders
4. Identify domain gain/loss events

## API Endpoint Summary

The returned-resource type is whatever comes **first** in the path; trailing
filters narrow it. Reversing the two halves yields a `*_url`-only wrapper.

| Endpoint | Description |
|----------|-------------|
| `/protein/UniProt/{id}/` | Full annotation for a protein (incl. `metadata.go_terms`) |
| `/entry/InterPro/protein/UniProt/{id}/` | InterPro entries for a protein (with match locations) |
| `/entry/InterPro/{id}/` | Details of an InterPro entry (`name` is a `{name,short}` dict) |
| `/entry/pfam/{id}/` | Pfam member-db entry details (`metadata.integrated` = InterPro id) |
| `/protein/UniProt/entry/InterPro/{id}/` | Proteins carrying an entry (paginated, with `count`) |
| `/entry/InterPro/?search=...` | Search/list InterPro entries (`name` is a string here) |
| `/entry/InterPro/taxonomy/uniprot/{tax_id}/` | InterPro entries seen in a taxon (paginated) |
| `/structure/PDB/entry/InterPro/{id}/` | Structures mapped to an entry |

## Member Databases

Source-database names as the API returns them (the `source_database` field /
`entry/{db}/...` path segment) are shown in parentheses where they differ.

| Database | Focus |
|----------|-------|
| Pfam (`pfam`) | Protein domains (HMM profiles) |
| PANTHER (`panther`) | Protein families and subfamilies |
| PRINTS (`prints`) | Protein fingerprints |
| ProSite patterns (`prosite`) | Amino acid patterns |
| ProSite profiles (`profile`) | Protein profile patterns |
| SMART (`smart`) | Mobile signalling/extracellular domains |
| NCBIfam (`ncbifam`) | NCBI curated families (absorbed the former TIGRFAMs) |
| SUPERFAMILY (`ssf`) | SCOP structural classification |
| CDD (`cdd`) | Conserved Domain Database (NCBI) |
| HAMAP (`hamap`) | Microbial protein families |
| Gene3D (`cathgene3d`) | CATH structural classification |
| PIRSF (`pirsf`) | PIR whole-protein families |
| SFLD (`sfld`) | Structure-Function Linkage Database (enzymes) |
| AntiFam (`antifam`) | Spurious-ORF filter (false-positive removal) |

## Best Practices

- **Use UniProt accession numbers** (not gene names) for the most reliable lookups
- **Distinguish types**: `family` gives broad classification; `domain` gives specific structural/functional units
- **InterProScan is faster for novel sequences**: For sequences not in UniProt, submit to the web service
- **Handle pagination**: Large result sets require iterating through pages
- **Combine with UniProt data**: InterPro entries often include links to UniProt, PDB, and GO

## Additional Resources

- **InterPro website**: https://www.ebi.ac.uk/interpro/
- **InterProScan** (run locally): https://github.com/ebi-pf-team/interproscan
- **API documentation**: https://github.com/ProteinsWebTeam/interpro7-api/blob/master/docs/
- **Pfam**: https://www.ebi.ac.uk/interpro/entry/pfam/
- **Citation**: Paysan-Lafosse T et al. (2023) Nucleic Acids Research. PMID: 36350672
