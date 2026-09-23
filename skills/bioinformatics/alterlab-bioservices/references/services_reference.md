# BioServices: Complete Services Reference

This document provides a comprehensive reference for all major services available in BioServices, including key methods, parameters, and use cases.

## Protein & Gene Resources

### UniProt

Protein sequence and functional information database.

**Initialization:**
```python
from bioservices import UniProt
u = UniProt(verbose=False)
```

**Key Methods:**

- `search(query, frmt="tsv", columns=None, include_isoforms=False, sort="score", limit=None, size=25, database="uniprotkb", progress=False)`
  - Search UniProt with flexible query syntax
  - `frmt`: `"tsv"` (default), `"xlsx"`, `"fasta"`, `"json"`, `"gff"`. The pre-2022
    `"tab"`, `"txt"`, `"xml"` and `"rdf"` values are no longer accepted here.
  - `columns`: comma-separated **UniProt return-field names**, e.g.
    `"accession,gene_names,organism_name,length"` (the old display labels such as
    `"id,genes,organism"` were replaced in the June-2022 API)
  - Returns: string in the requested format (all pages concatenated)

- `retrieve(uniprot_id, frmt="json", database="uniprot", include=False)`
  - Retrieve specific UniProt entry (or a list of them)
  - `frmt`: "json" (default), "txt", "xml", "rdf", "gff", "fasta"
  - Returns: entry data in the requested format; a list when given a list of IDs

- `mapping(fr="UniProtKB_AC-ID", to="KEGG", query="P43403", polling_interval_seconds=3, max_waiting_time=100)`
  - Submit an ID-mapping job, poll it, and return the assembled payload
  - `query`: single ID, comma-separated string, or list
  - Returns: `{"results": [{"from": src, "to": tgt}, ...], "failedIds": [...]}` —
    **not** a `{source: [targets]}` dict; build that yourself if you need it
  - `valid_mapping` (property) lists the legal `fr`/`to` pairs straight from UniProt

- `get_df(entries, nChunk=100, organism=None, limit=10, columns=None)`
  - Build a pandas DataFrame for a list of accessions

**Common `columns` values:** accession, id, gene_names, gene_primary, organism_name,
organism_id, protein_name, length, sequence, mass, go_id, ec, xref_pdb, xref_kegg

**Use cases:**
- Protein sequence retrieval for BLAST
- Functional annotation lookup
- Cross-database identifier mapping
- Batch protein information retrieval

---

### KEGG (Kyoto Encyclopedia of Genes and Genomes)

Metabolic pathways, genes, and organisms database.

**Initialization:**
```python
from bioservices import KEGG
k = KEGG()
k.organism = "hsa"  # Set default organism
```

**Key Methods:**

- `list(database)`
  - List entries in KEGG database
  - `database`: "organism", "pathway", "module", "disease", "drug", "compound"
  - Returns: Multi-line string with entries

- `find(database, query)`
  - Search database by keywords
  - Returns: List of matching entries with IDs

- `get(entry_id)`
  - Retrieve entry by ID
  - Supports genes, pathways, compounds, etc.
  - Returns: Raw entry text

- `parse(data)`
  - Parse KEGG entry into dictionary
  - Returns: Dict with structured data

- `lookfor_organism(name)`
  - Search organisms by name pattern
  - Returns: List of matching organism codes

- `lookfor_pathway(name)`
  - Search pathways by name
  - Returns: List of pathway IDs

- `get_pathway_by_gene(gene_id, organism)`
  - Find pathways containing a gene, e.g. `get_pathway_by_gene("7535", "hsa")`
  - Returns the parsed PATHWAY block — a **dict** `{pathway_id: pathway_name}`
    (`{"hsa04064": "NF-kappa B signaling pathway", ...}`), despite the docstring's
    "list of pathway Ids". Iterating it yields the IDs; `.items()` gives you the
    names for free. IDs come back without the `path:` prefix.

- `parse_kgml_pathway(pathway_id)`
  - Parse pathway KGML for interactions
  - Returns: Dict with "entries" and "relations"

- `pathway2sif(pathway_id)`
  - Extract Simple Interaction Format data
  - Filters for activation/inhibition
  - Returns: List of interaction tuples

**Organism codes:**
- hsa: Homo sapiens
- mmu: Mus musculus
- dme: Drosophila melanogaster
- sce: Saccharomyces cerevisiae
- eco: Escherichia coli

**Use cases:**
- Pathway analysis and visualization
- Gene function annotation
- Metabolic network reconstruction
- Protein-protein interaction extraction

---

### HGNC (Human Gene Nomenclature Committee)

Official human gene naming authority.

**Initialization:**
```python
from bioservices import HGNC
h = HGNC()
```

**Key Methods:**
- `search(database_or_query=None, query=None, frmt="json")`: search gene symbols/names
- `fetch(database, query, frmt="json")`: retrieve a gene record
- `get_info(frmt="json")`: list the searchable/stored fields

**Use cases:**
- Standardizing human gene names
- Looking up official gene symbols

---

### MyGeneInfo

Gene annotation and query service.

**Initialization:**
```python
from bioservices import MyGeneInfo
m = MyGeneInfo()
```

**Key Methods:**
- `get_genes(ids, ...)` / `get_one_gene(geneid, ...)`: gene annotation by ID
- `get_queries(...)` / `get_one_query(...)`: batch or single free-text query
- `get_metadata()`, `get_taxonomy()`

**Use cases:**
- Batch gene annotation retrieval
- Gene ID conversion

---

## Chemical Compound Resources

### ChEBI (Chemical Entities of Biological Interest)

Dictionary of molecular entities.

**Initialization:**
```python
from bioservices import ChEBI
c = ChEBI()
```

**Key Methods** (REST since bioservices 1.13 — the SOAP interface is gone):
- `getCompleteEntity(chebi_id)`: full entry as a dict-like `ChebiEntity`; accepts
  `"CHEBI:27732"` or `"27732"`
- `getLiteEntity(search, searchCategory="ALL", maximumResults=200, stars="ALL")`: search
- `getCompleteEntityByList(chebi_ids)`: batch retrieval
- `conv(chebi_id, target)`: cross-references for one source, e.g.
  `conv("CHEBI:10102", "KEGG COMPOUND accession")`

`ChebiEntity` exposes `.chebiId`, `.chebiAsciiName`, `.formula`, `.mass`, `.charge`,
`.smiles`, `.inchiKey`, and `.DatabaseLinks` (list of `(accession, source_name)` pairs).
Note `.formula` — the old SOAP attribute was `Formulae`.

**Use cases:**
- Small molecule information
- Chemical structure data
- Compound property lookup

---

### ChEMBL

Bioactive drug-like compound database.

**Initialization:**
```python
from bioservices import ChEMBL
c = ChEMBL()
```

**Key Methods (bioservices >= 1.6.0):**
- `get_molecule(query=None, limit=20, offset=0, filters=None)`: retrieve molecule records
  (by ChEMBL ID, list of IDs, or filters)
- `search_molecule(query)`: Free-text molecule search
- `get_target(query)`: Target information
- `get_similarity(smiles_or_id, similarity)`: Find similar compounds
- `get_substructure(smiles_or_id)`: Substructure search

Note: the pre-1.6.0 helpers `get_compound_by_chemblId()` / `get_molecule_form()`
were removed when the API was simplified in 1.6.0; use `get_molecule()` instead.

**Use cases:**
- Drug discovery data
- Find similar compounds
- Bioactivity information
- Target-compound relationships

---

### UniChem

Chemical identifier mapping service.

**Important (bioservices behavior):** The compound-mapping convenience methods
that previously lived on `bioservices.UniChem` (e.g. `get_compound_id_from_kegg`,
`get_src_compound_ids`, `get_all_compound_ids`) were **dropped from bioservices in
2022** and are no longer available. There is also no KEGG -> ChEMBL route in the
KEGG Web Service. For chemical ID cross-referencing today:

- Use `KEGG.conv("chebi", "compound")` for the supported KEGG -> ChEBI mapping
  (ChEBI IDs are also embedded in KEGG compound entries and can be parsed out).
- For KEGG/ChEBI -> ChEMBL (or other UniChem sources), call the **live UniChem
  REST API directly** (`https://www.ebi.ac.uk/unichem/`) or the **ChEMBL web
  service / `chembl_webresource_client`** — these are separate from bioservices.

**Use cases:**
- Cross-database compound ID mapping (via the routes above, not bioservices.UniChem)
- Linking chemical databases

---

### PubChem

Chemical compound database from NIH.

**Initialization:**
```python
from bioservices import PubChem
p = PubChem()
```

**Key Methods** (PUG REST, refreshed in bioservices 1.14):
- `get_cids_by_name(name)`, `get_cids_by_smiles(smiles)`, `get_cids_by_inchikey(...)`
- `get_compound_by_cid(cid)`, `get_compound_by_name(name)`, `get_compound_by_smiles(...)`
- `get_properties(identifier, namespace="cid", properties=None)`, `get_synonyms(...)`,
  `get_xrefs(...)`, `get_assay(aid)`

**Use cases:**
- Chemical structure retrieval
- Compound property information

---

## Sequence Analysis Tools

### NCBIblast

Sequence similarity searching.

**Initialization:**
```python
from bioservices import NCBIblast
s = NCBIblast(verbose=False)
```

**Key Methods:**
- `run(program, sequence, stype, database, email, **params)`
  - Submit BLAST job
  - `program`: "blastp", "blastn", "blastx", "tblastn", "tblastx"
  - `stype`: "protein" or "dna"
  - `database`: "uniprotkb", "pdb", "refseq_protein", etc.
  - `email`: Required by NCBI
  - Returns: Job ID

- `get_status(jobid)`
  - Check job status
  - Returns: "RUNNING", "FINISHED", "ERROR", "FAILURE", or "NOT_FOUND"

- `wait(jobid)`
  - Block until the job finishes (polls at `checkInterval` seconds)

- `get_result(jobid, result_type)` / `get_result_types(jobid)`
  - Retrieve results; `result_type` is one of the identifiers `get_result_types` returns
    (e.g. "out", "ids", "xml")

> The camelCase `getStatus` / `getResult` / `parametersDetails` names no longer exist;
> only the docstrings still mention them. `NCBIBlastAPI` (bioservices 1.16) offers the same
> run / get_status / get_result flow against NCBI's own BLAST URL API.

**Important:** BLAST jobs are asynchronous. Always check status before retrieving results.

**Use cases:**
- Protein homology searches
- Sequence similarity analysis
- Functional annotation by homology

---

## Pathway & Interaction Resources

### Reactome

Pathway database.

**Initialization:**
```python
from bioservices import Reactome
r = Reactome()
```

**Key Methods:**
- `get_pathways_top(species)`, `get_pathway_containedEvents(identifier)`,
  `get_event_ancestors(identifier)`, `get_complex_subunits(identifier)`
- `search_query(query)`, `search_facet_query(query)`, `get_species_all()`

**Use cases:**
- Human pathway analysis
- Biological process annotation

---

### STRING (replaces PSICQUIC / BioGRID)

`PSICQUIC` and `BioGRID` were **removed in bioservices 1.14**; importing them raises
`ImportError`. STRING covers the same "who interacts with this protein" question.

**Initialization:**
```python
from bioservices import STRING
s = STRING()
```

**Key Methods:**
- `get_interaction_partners(identifiers, species=None, required_score=None, limit=None, network_type="functional")`
  - Partners of the query proteins, including ones outside the input set
- `get_interactions(identifiers, species=...)` — edges *within* the given set
- `get_network(...)`, `get_enrichment(...)`, `get_functional_annotation(...)`,
  `get_ppi_enrichment(...)`, `get_homology(...)`, `get_string_ids(...)`, `get_version()`

**Parameters that matter:** `species` is an NCBI taxid (9606 = human); `required_score`
is 0–1000 (returned `score` values are 0–1); `network_type` is `"functional"` (default)
or `"physical"`.

**Use cases:**
- Protein-protein interaction discovery
- Network analysis and enrichment of an interactor set
- Interactome mapping

---

### IntactComplex

Protein complex database.

**Initialization:**
```python
from bioservices import IntactComplex
i = IntactComplex()
```

**Key Methods:**
- `search(query)`: Search complexes
- `details(complex_ac)`: Complex details

**Use cases:**
- Protein complex composition
- Multi-protein assembly analysis

---

### OmniPath

Integrated signaling pathway database.

**Initialization:**
```python
from bioservices import OmniPath
o = OmniPath()
```

**Key Methods:**
- `get_interactions(query="", frmt="json", fields=[])`
- `get_ptms(query="", ptm_type=None, frmt="json", fields=[])`
- `get_network(frmt="json")`, `get_resources(frmt="json")`

**Use cases:**
- Cell signaling analysis
- Regulatory network mapping

---

## Gene Ontology

### QuickGO

Gene Ontology annotation service.

**Initialization:**
```python
from bioservices import QuickGO
g = QuickGO()
```

**Key Methods** (the QuickGO REST refresh renamed most of these):
- `get_go_terms(query)` / `go_search(query, limit=600, page=1)`
  - Retrieve or search GO term information (parsed JSON)
- `get_go_ancestors(query, relations=...)`, `get_go_children(query)`, `get_go_paths(_from, _to)`
  - Navigate the ontology graph
- `Annotation(geneProductId=None, goId=None, taxonId=None, aspect=None, includeFields=None, limit=100, page=1, ...)`
  - Get GO annotations. `geneProductId` is prefixed (`"UniProtKB:P43403"`), `limit` is
    capped at 100 (higher raises `TypeError`), and the result is a dict with
    `numberOfHits` plus a `results` list of records (`goId`, `goName`, `goAspect`,
    `qualifier`, `evidenceCode`, ...). The old `protein=` / `format=` parameters are gone.
- `Annotation_from_goid(goId, ...)`, `gene_product_search(...)`

**GO categories:**
- Biological Process (BP)
- Molecular Function (MF)
- Cellular Component (CC)

**Use cases:**
- Functional annotation
- Enrichment analysis
- GO term lookup

---

## Genomic Resources

### BioMart

Data mining tool for genomic data.

**Initialization:**
```python
from bioservices import BioMart
b = BioMart()
```

**Key Methods:**
- `registry()`, `datasets(mart)`, `attributes(dataset)`, `filters(dataset)`
- `new_query()` + `add_dataset_to_xml` / `add_attribute_to_xml` / `add_filter_to_xml`
  + `get_xml()`, then `query(xmlq)`

**Use cases:**
- Bulk genomic data retrieval
- Custom genome annotations
- SNP information

---

### ArrayExpress

Gene expression database.

**Initialization:**
```python
from bioservices import ArrayExpress
a = ArrayExpress()
```

**Key Methods:**
- `search(query, page=1, page_size=20, ...)`: search studies (current BioStudies-backed API)
- `get_study(accession)`, `get_files(accession)`, `retrieve_file(accession, filename)`
- The legacy `queryExperiments` / `retrieveExperiment` helpers remain but target the
  retired ArrayExpress endpoints

**Use cases:**
- Gene expression data
- Microarray analysis
- RNA-seq data retrieval

---

### ENA (European Nucleotide Archive)

Nucleotide sequence database.

**Initialization:**
```python
from bioservices import ENA
e = ENA()
```

**Key Methods:**
- `get_data(identifier, frmt=...)`: retrieve records by accession
- `get_taxon(taxon)`, `data_warehouse()`

**Use cases:**
- Nucleotide sequence retrieval
- Genome assembly access

---

## Structural Biology

### PDB (Protein Data Bank)

3D protein structure database.

**Initialization:**
```python
from bioservices import PDB
p = PDB()
```

**Key Methods:**
- `search(query, request_options=None, request_info=None, return_type=None)`: RCSB Search API v2
- `get_current_ids()`, `get_similarity_sequence(seq)`

For downloading coordinate files, fetch from RCSB directly (or use `alterlab-pdb`);
the v2 API wrapper in bioservices is search-oriented.

**Use cases:**
- 3D structure retrieval
- Structure-based analysis
- PyMOL visualization

---

### Pfam

Protein family database.

**Initialization:**
```python
from bioservices import Pfam
p = Pfam()
```

**Key Methods:**
- `show(Id)`, `get_protein(ID, output="json")`

Pfam is now served through InterPro; the bioservices class scrapes those pages rather
than calling a dedicated Pfam REST API, so prefer `alterlab-interpro` for real work.

**Use cases:**
- Protein domain identification
- Family classification
- Functional motif discovery

---

## Specialized Resources

### BioModels

Systems biology model repository.

**Initialization:**
```python
from bioservices import BioModels
b = BioModels()
```

**Key Methods:**
- `get_model(model_id, frmt="json")`, `get_model_files(model_id)`,
  `get_model_download(model_id, filename=...)`, `search(query)`

**Use cases:**
- Systems biology modeling
- SBML model retrieval

---

### COG (Clusters of Orthologous Genes)

Orthologous gene classification.

**Initialization:**
```python
from bioservices import COG
c = COG()
```

**Use cases:**
- Orthology analysis
- Functional classification

---

### BiGG Models

Metabolic network models.

**Initialization:**
```python
from bioservices import BiGG
b = BiGG()
```

**Key Methods:**
- `models` (property): available models
- `get_model(model_id)`, `metabolites(...)`, `reactions(...)`, `genes(model_id)`,
  `search(query, type_)`, `download(model_id, format_="json")`

**Use cases:**
- Metabolic network analysis
- Flux balance analysis

---

## General Patterns

### Error Handling

All services may throw exceptions. Wrap calls in try-except:

```python
try:
    result = service.method(params)
    if result:
        # Process result
        pass
except Exception as e:
    print(f"Error: {e}")
```

### Verbosity Control

Most services support `verbose` parameter:
```python
service = Service(verbose=False)  # Suppress HTTP logs
```

### Rate Limiting

Timeouts live on the `REST` object each service holds (`service.services`), so set them
there — most classes are plain wrappers now rather than `REST` subclasses:
```python
k = KEGG()
k.services.TIMEOUT = 30       # seconds
k.services.settings.TIMEOUT = 30   # equivalent, via the settings object
```

### Output Formats

Common format parameters:
- `frmt`: "xml", "json", "tab", "txt", "fasta"
- `format`: Service-specific variants

### Caching

Caching is opt-in at construction and backed by `requests_cache`:
```python
k = KEGG(cache=True)       # store responses in a local sqlite cache
k.services.clear_cache()   # drop it
```

## Additional Resources

For detailed API documentation:
- Official docs: https://bioservices.readthedocs.io/
- Individual service docs linked from main page
- Source code: https://github.com/cokelaer/bioservices
