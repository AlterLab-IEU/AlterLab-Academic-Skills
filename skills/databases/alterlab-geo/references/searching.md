# Searching GEO

Programmatic search via NCBI E-utilities (Biopython `Bio.Entrez`). Always set
`Entrez.email` before any request.

## GEO DataSets Search

Search for studies by keywords, organism, or experimental conditions:

```python
from Bio import Entrez

# Configure Entrez (required)
Entrez.email = "your.email@example.com"

# Search for datasets
def search_geo_datasets(query, retmax=20):
    """Search GEO DataSets database"""
    handle = Entrez.esearch(
        db="gds",
        term=query,
        retmax=retmax,
        usehistory="y"
    )
    results = Entrez.read(handle)
    handle.close()
    return results

# Example searches
results = search_geo_datasets("breast cancer[MeSH Terms] AND Homo sapiens[Organism]")
print(f"Found {results['Count']} datasets")

# Search by specific platform
results = search_geo_datasets("GPL570[Accession]")

# Search by study type
results = search_geo_datasets("expression profiling by array[DataSet Type]")
```

## GEO Profiles Search

Find gene-specific expression patterns:

```python
# Search for gene expression profiles
def search_geo_profiles(gene_name, organism="Homo sapiens", retmax=100):
    """Search GEO Profiles for a specific gene"""
    query = f"{gene_name}[Gene Name] AND {organism}[Organism]"
    handle = Entrez.esearch(
        db="geoprofiles",
        term=query,
        retmax=retmax
    )
    results = Entrez.read(handle)
    handle.close()
    return results

# Find TP53 expression across studies
tp53_results = search_geo_profiles("TP53", organism="Homo sapiens")
print(f"Found {tp53_results['Count']} expression profiles for TP53")
```

## Advanced Search Patterns

```python
# Combine multiple search terms
def advanced_geo_search(terms, operator="AND"):
    """Build complex search queries"""
    query = f" {operator} ".join(terms)
    return search_geo_datasets(query)

# Find recent high-throughput studies
search_terms = [
    "RNA-seq[DataSet Type]",
    "Homo sapiens[Organism]",
    "2024[Publication Date]"
]
results = advanced_geo_search(search_terms)

# Search by author and condition
search_terms = [
    "Smith[Author]",
    "diabetes[Disease]"
]
results = advanced_geo_search(search_terms)
```

## E-utilities Workflow (search → summary → fetch)

E-utilities provide lower-level programmatic access to GEO metadata:

```python
from Bio import Entrez
import time

Entrez.email = "your.email@example.com"

# Step 1: Search for GEO entries
def search_geo(query, db="gds", retmax=100):
    """Search GEO using E-utilities"""
    handle = Entrez.esearch(
        db=db,
        term=query,
        retmax=retmax,
        usehistory="y"
    )
    results = Entrez.read(handle)
    handle.close()
    return results

# Step 2: Fetch summaries
def fetch_geo_summaries(id_list, db="gds"):
    """Fetch document summaries for GEO entries"""
    ids = ",".join(id_list)
    handle = Entrez.esummary(db=db, id=ids)
    summaries = Entrez.read(handle)
    handle.close()
    return summaries

# Step 3: Fetch full records
def fetch_geo_records(id_list, db="gds"):
    """Fetch full GEO records"""
    ids = ",".join(id_list)
    handle = Entrez.efetch(db=db, id=ids, retmode="xml")
    records = Entrez.read(handle)
    handle.close()
    return records

# Example workflow
search_results = search_geo("breast cancer AND Homo sapiens")
id_list = search_results['IdList'][:5]

summaries = fetch_geo_summaries(id_list)
for summary in summaries:
    print(f"GDS: {summary.get('Accession', 'N/A')}")
    print(f"Title: {summary.get('title', 'N/A')}")
    print(f"Samples: {summary.get('n_samples', 'N/A')}")
    print()
```

## Batch Metadata Fetch

```python
from Bio import Entrez
import time

Entrez.email = "your.email@example.com"

def batch_fetch_geo_metadata(accessions, batch_size=100):
    """Fetch metadata for multiple GEO accessions"""
    results = {}

    for i in range(0, len(accessions), batch_size):
        batch = accessions[i:i + batch_size]

        # Search for each accession
        for accession in batch:
            try:
                query = f"{accession}[Accession]"
                search_handle = Entrez.esearch(db="gds", term=query)
                search_results = Entrez.read(search_handle)
                search_handle.close()

                if search_results['IdList']:
                    # Fetch summary
                    summary_handle = Entrez.esummary(
                        db="gds",
                        id=search_results['IdList'][0]
                    )
                    summary = Entrez.read(summary_handle)
                    summary_handle.close()
                    results[accession] = summary[0]

                # Be polite to NCBI servers
                time.sleep(0.34)  # Max 3 requests per second

            except Exception as e:
                print(f"Error fetching {accession}: {e}")

    return results

# Fetch metadata for multiple datasets
gse_list = ["GSE100001", "GSE100002", "GSE100003"]
metadata = batch_fetch_geo_metadata(gse_list)
```
