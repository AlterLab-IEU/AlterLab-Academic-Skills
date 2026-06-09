---
name: alterlab-monarch
description: Query the Monarch Initiative knowledge graph for disease-gene-phenotype associations across species, integrating OMIM, ORPHANET, HPO, ClinVar, and model organism databases. Use when discovering rare disease genes, mapping phenotypes to genes, modeling disease across species, or looking up HPO terms. Part of the AlterLab Academic Skills suite.
license: CC0-1.0
allowed-tools: Read WebFetch Bash(curl:*) Bash(python:*)
compatibility: Keyless Monarch Initiative REST API (no authentication required)
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# Monarch Initiative Database

## Overview

The Monarch Initiative (https://monarchinitiative.org/) is a multi-species integrated knowledgebase that links genes, diseases, and phenotypes across humans and model organisms. It integrates data from over 40 sources including OMIM, ORPHANET, HPO (Human Phenotype Ontology), ClinVar, MGI (Mouse Genome Informatics), ZFIN (Zebrafish), RGD (Rat), FlyBase, and WormBase.

Monarch enables:
- Mapping phenotypes across species to identify candidate disease genes
- Finding all genes associated with a disease or phenotype
- Discovering model organisms for human diseases
- Navigating the HPO hierarchy for phenotype ontology queries

**Key resources:**
- Monarch portal: https://monarchinitiative.org/
- API v3 base URL: `https://api-v3.monarchinitiative.org/v3/api` (all endpoints live under `/v3/api/...`)
- Interactive API docs (Swagger UI): https://api-v3.monarchinitiative.org/v3/docs
- HPO browser: https://hpo.jax.org/

## Scripts

`scripts/query_monarch.py` — query the Monarch Initiative API v3 (stdlib only, JSON to stdout):

```bash
python scripts/query_monarch.py entity HP:0001250        # look up an entity (gene/disease/HPO)
python scripts/query_monarch.py search epilepsy          # text search the knowledge graph
python scripts/query_monarch.py associations HGNC:1100   # associations for an entity
```

## When to Use This Skill

Use Monarch when:

- **Rare disease gene discovery**: What genes are associated with my patient's phenotypes (HPO terms)?
- **Phenotype similarity**: Are two diseases similar based on their phenotypic profiles?
- **Cross-species modeling**: Are there mouse/zebrafish models for my disease of interest?
- **HPO term lookup**: Retrieve HPO term names, definitions, and ontology hierarchy
- **Disease-phenotype mapping**: List all HPO terms associated with a specific disease
- **Gene-phenotype associations**: What phenotypes are caused by variants in a gene?
- **Ortholog-phenotype mapping**: Use animal model phenotypes to infer human gene function

## Core Capabilities

### 1. Monarch API v3

The real endpoints live under `/v3/api` (the `/v3/docs` URL is only the Swagger UI, not a request base). Association items come back **flat** — read `item["subject"]`, `item["subject_label"]`, `item["predicate"]`, `item["object"]`, `item["object_label"]`, `item["object_category"]`, etc. There is no nested `item["object"]["id"]`.

```python
import requests

BASE_URL = "https://api-v3.monarchinitiative.org/v3/api"

def monarch_get(endpoint, params=None):
    """GET a Monarch API v3 endpoint and return parsed JSON."""
    url = f"{BASE_URL}/{endpoint}"
    response = requests.get(url, params=params, headers={"Accept": "application/json"})
    response.raise_for_status()
    return response.json()
```

### 2. Phenotype-to-Gene Association (Pheno2Gene)

For a `GeneToPhenotypicFeatureAssociation`, the gene is the **subject** and the
phenotype is the **object**. To go from a phenotype to its genes, filter on
`object=<HPO>` and `subject_category=biolink:Gene`.

```python
def phenotype_to_gene(hpo_ids, limit=100):
    """
    Return genes whose phenotypes match the given HPO terms (flat per-term links).
    Core use case: rare disease differential diagnosis.

    Args:
        hpo_ids: List of HPO term IDs (e.g., ["HP:0001250", "HP:0004322"])
    """
    all_genes = []
    for hpo_id in hpo_ids:
        data = monarch_get("association", {
            "object": hpo_id,
            "subject_category": "biolink:Gene",
            "category": "biolink:GeneToPhenotypicFeatureAssociation",
            "limit": limit,
        })
        for assoc in data.get("items", []):
            all_genes.append({
                "phenotype_id": hpo_id,
                "gene_id": assoc.get("subject"),
                "gene_name": assoc.get("subject_label"),
                "predicate": assoc.get("predicate"),
            })
    return all_genes

# Example: Find genes associated with seizures and short stature
hpo_terms = ["HP:0001250", "HP:0004322"]  # Seizure, Short stature
genes = phenotype_to_gene(hpo_terms)
```

### 3. Disease-to-Gene Associations

A causal gene-disease link is a `CausalGeneToDiseaseAssociation` (gene = subject,
disease = object, predicate `biolink:causes`). To list genes for a disease,
filter on `object=<disease>` and that category.

```python
def get_disease_genes(disease_id, limit=100):
    """
    Get genes causally linked to a disease.
    Disease IDs: MONDO:0007739, OMIM:146300, ORPHANET:558, etc.
    """
    data = monarch_get("association", {
        "object": disease_id,
        "category": "biolink:CausalGeneToDiseaseAssociation",
        "limit": limit,
    })
    return data.get("items", [])

# Example: genes causally linked to Huntington disease
for assoc in get_disease_genes("MONDO:0007739"):
    print(f"  {assoc.get('subject_label')} ({assoc.get('subject')})")

# MONDO disease IDs (preferred over OMIM for cross-ontology queries)
# MONDO:0007739 - Huntington disease
# MONDO:0009061 - Cystic fibrosis
# OMIM:104300 - Alzheimer disease, susceptibility to, type 1
```

### 4. Gene-to-Phenotype and Disease

```python
def get_phenotypes_for_gene(gene_id, limit=100):
    """
    Get all phenotypes associated with a gene.
    Gene IDs: HGNC:7884, NCBIGene:4137, etc.
    """
    data = monarch_get("association", {
        "subject": gene_id,
        "category": "biolink:GeneToPhenotypicFeatureAssociation",
        "limit": limit,
    })
    return data.get("items", [])

def get_diseases_for_gene(gene_id, limit=100):
    """Get diseases caused by variants in a gene."""
    data = monarch_get("association", {
        "subject": gene_id,
        "category": "biolink:CausalGeneToDiseaseAssociation",
        "limit": limit,
    })
    return data.get("items", [])

# Example: What diseases does BRCA1 cause? (flat fields: object / object_label)
brca1_diseases = get_diseases_for_gene("HGNC:1100")
for assoc in brca1_diseases:
    print(f"  {assoc.get('object_label')} ({assoc.get('object')})")
```

### 5. HPO Term Lookup

```python
def get_hpo_term(hpo_id):
    """Fetch information about an HPO term."""
    return monarch_get(f"entity/{hpo_id}")

def search_hpo_terms(query, limit=20):
    """Search for HPO terms by name."""
    params = {
        "q": query,
        "category": "biolink:PhenotypicFeature",
        "limit": limit
    }
    return monarch_get("search", params)

# Example: look up the HPO term for seizures
seizure_term = get_hpo_term("HP:0001250")
print(f"Name: {seizure_term.get('name')}")
print(f"Definition: {seizure_term.get('description')}")

# Search for related terms
epilepsy_terms = search_hpo_terms("epilepsy")
for term in epilepsy_terms.get("items", [])[:5]:
    print(f"  {term['id']}: {term['name']}")
```

### 6. Semantic Similarity (Disease Comparison)

`semsim/compare` is a **POST** endpoint taking a JSON body of two HPO term sets
(`subjects`, `objects`) and an optional `metric`. Valid metrics:
`ancestor_information_content` (default), `jaccard_similarity`, `phenodigm_score`.
The response includes `average_score` and `best_score`.

```python
def compare_phenotype_sets(subject_hpo_ids, object_hpo_ids,
                           metric="ancestor_information_content"):
    """
    Compare two sets of HPO terms by semantic similarity over the HPO hierarchy.
    Pass each disease's HPO profile as a term set (not the disease CURIE itself).
    """
    body = {
        "subjects": subject_hpo_ids,
        "objects": object_hpo_ids,
        "metric": metric,
    }
    resp = requests.post(f"{BASE_URL}/semsim/compare", json=body)
    resp.raise_for_status()
    return resp.json()

# Example: compare two phenotype profiles
similarity = compare_phenotype_sets(
    ["HP:0001250", "HP:0001263"],  # Seizure, Global developmental delay
    ["HP:0001250", "HP:0004322"],  # Seizure, Short stature
)
print(similarity["average_score"], similarity["best_score"])
```

### 7. Cross-Species Orthologs

```python
def get_orthologs(gene_id, taxon=None, limit=50):
    """
    Get orthologs of a human gene in model organisms.
    Useful for finding animal models of human diseases.
    Each item exposes object / object_label / object_taxon_label (e.g. Mus musculus).
    """
    params = {
        "subject": gene_id,
        "predicate": "biolink:orthologous_to",
        "limit": limit,
    }
    if taxon:
        params["object_taxon"] = taxon  # e.g. "NCBITaxon:10090" for mouse
    return monarch_get("association", params).get("items", [])

# NCBI Taxonomy IDs for common model organisms:
# Mouse: 10090 (Mus musculus)
# Zebrafish: 7955 (Danio rerio)
# Fruit fly: 7227 (Drosophila melanogaster)
# C. elegans: 6239
# Rat: 10116 (Rattus norvegicus)
```

### 8. Full Workflow: Rare Disease Gene Prioritization

```python
import requests
import pandas as pd

def rare_disease_gene_finder(patient_hpo_terms, candidate_gene_ids=None, top_n=20):
    """
    Find genes that match a patient's HPO phenotype profile.

    Args:
        patient_hpo_terms: List of HPO IDs from clinical assessment
        candidate_gene_ids: Optional list to restrict search
        top_n: Number of top candidates to return
    """
    BASE_URL = "https://api-v3.monarchinitiative.org/v3/api"

    # 1. Find genes associated with each phenotype
    gene_phenotype_counts = {}

    for hpo_id in patient_hpo_terms:
        data = requests.get(
            f"{BASE_URL}/association",
            params={
                "object": hpo_id,
                "subject_category": "biolink:Gene",
                "category": "biolink:GeneToPhenotypicFeatureAssociation",
                "limit": 100,
            }
        ).json()

        for item in data.get("items", []):
            gene_id = item.get("subject")        # flat field, not item["subject"]["id"]
            gene_name = item.get("subject_label")
            if gene_id:
                if gene_id not in gene_phenotype_counts:
                    gene_phenotype_counts[gene_id] = {"name": gene_name, "count": 0, "phenotypes": []}
                gene_phenotype_counts[gene_id]["count"] += 1
                gene_phenotype_counts[gene_id]["phenotypes"].append(hpo_id)

    # 2. Rank by number of matching phenotypes
    ranked = sorted(gene_phenotype_counts.items(),
                    key=lambda x: -x[1]["count"])[:top_n]

    results = []
    for gene_id, info in ranked:
        results.append({
            "gene_id": gene_id,
            "gene_name": info["name"],
            "matching_phenotypes": info["count"],
            "total_patient_phenotypes": len(patient_hpo_terms),
            "phenotype_overlap": info["count"] / len(patient_hpo_terms),
            "matching_hpo_terms": info["phenotypes"]
        })

    return pd.DataFrame(results)

# Example usage
patient_phenotypes = [
    "HP:0001250",  # Seizures
    "HP:0004322",  # Short stature
    "HP:0001252",  # Hypotonia
    "HP:0000252",  # Microcephaly
    "HP:0001263",  # Global developmental delay
]
candidates = rare_disease_gene_finder(patient_phenotypes)
print(candidates[["gene_name", "matching_phenotypes", "phenotype_overlap"]].to_string())
```

## Query Workflows

### Workflow 1: HPO-Based Differential Diagnosis

1. Extract HPO terms from clinical notes or genetics consultation
2. Run phenotype-to-gene query against Monarch
3. Rank candidate genes by number of matching phenotypes
4. Cross-reference with gnomAD (constraint scores) and ClinVar (variant evidence)
5. Prioritize genes with high pLI and known pathogenic variants

### Workflow 2: Disease Model Discovery

1. Identify gene or disease of interest
2. Query Monarch for cross-species orthologs
3. Find phenotype associations in model organism databases
4. Identify experimental models that recapitulate human disease features

### Workflow 3: Phenotype Annotation of Novel Genes

1. For a gene with unknown function, query all known phenotype associations
2. Map to HPO hierarchy to understand affected body systems
3. Cross-reference with OMIM and ORPHANET for disease links

## Common Identifier Prefixes

| Prefix | Namespace | Example |
|--------|-----------|---------|
| `HP:` | Human Phenotype Ontology | HP:0001250 (Seizures) |
| `MONDO:` | Monarch Disease Ontology | MONDO:0007739 |
| `OMIM:` | OMIM disease | OMIM:104300 |
| `ORPHANET:` | Orphanet rare disease | ORPHANET:558 |
| `HGNC:` | HGNC gene symbol | HGNC:7884 |
| `NCBIGene:` | NCBI gene ID | NCBIGene:4137 |
| `ENSEMBL:` | Ensembl gene | ENSEMBL:ENSG... |
| `MGI:` | Mouse gene | MGI:1338833 |
| `ZFIN:` | Zebrafish gene | ZFIN:ZDB-GENE... |

## Best Practices

- **Use MONDO IDs** for diseases — they unify OMIM/ORPHANET/MESH identifiers
- **Use HPO IDs** for phenotypes — the standard for clinical phenotype description
- **Handle pagination**: Large queries may require iterating with offset parameter
- **Semantic similarity is better than exact match**: Ancestor HPO terms catch related phenotypes
- **Cross-validate with ClinVar and OMIM**: Monarch aggregates many sources; quality varies
- **Use HGNC IDs for genes**: More stable than gene symbols across database versions

## Additional Resources

- **Monarch portal**: https://monarchinitiative.org/
- **API v3 base**: https://api-v3.monarchinitiative.org/v3/api — **Swagger UI**: https://api-v3.monarchinitiative.org/v3/docs
- **HPO browser**: https://hpo.jax.org/
- **MONDO ontology**: https://mondo.monarchinitiative.org/
- **Citation**: Shefchek KA et al. (2020) Nucleic Acids Research. PMID: 31701156
- **Phenomizer** (HPO-based diagnosis): https://hpo.jax.org/
