# AlterLab MCP Connectors

Aggregated **Model Context Protocol** servers that wrap the highest-traffic scientific-data
clusters behind typed tool surfaces, so an agent gets structured JSON instead of scraping HTML.
Each connector aggregates the endpoints already documented by the corresponding AlterLab
database skills (kept as authoring references — the connectors do not replace them).

These are **standalone FastMCP servers** (one Python module per connector). They live outside
`skills/` on purpose: they are infrastructure, not Agent Skills, so they are not part of the
per-domain plugin marketplace. Add a connector to any MCP client with its `.mcp.json`.

## Run / install

Each server is stdlib-HTTP only; the sole third-party dependency is `fastmcp`:

```bash
uv run --with fastmcp python mcp-servers/structures/server.py
```

To register with an MCP client, point it at the connector's `.mcp.json`, e.g.:

```json
{ "mcpServers": { "structures": {
  "command": "uv",
  "args": ["run", "--with", "fastmcp", "python", "mcp-servers/structures/server.py"] } } }
```

Credentials follow each source's etiquette and are read from the **environment**, never
hardcoded: NCBI E-utilities read a contact email from `NCBI_EMAIL` (and optional
`NCBI_API_KEY`). Every tool returns a typed `{"error": ...}` object instead of raising when a
source API is unreachable.

## Connectors & tools

### `structures` — experimental + predicted structures, complexes
Aggregates `alterlab-pdb`, `alterlab-alphafold-db` (+ EBI Complex Portal).

| Tool | Args | Returns |
|------|------|---------|
| `get_structure` | `pdb_id` | RCSB core-entry metadata (title, method, resolution) |
| `get_alphafold_prediction` | `uniprot_accession` | AlphaFold DB prediction (model URLs, mean pLDDT) |
| `search_complexes` | `query`, `size` | EBI Complex Portal matches |

```
get_structure(pdb_id="1CRN")
get_alphafold_prediction(uniprot_accession="P00520")
```

### `variants` — population frequency + clinical significance
Aggregates `alterlab-gnomad`, `alterlab-clinvar` (+ dbSNP via NCBI).

| Tool | Args | Returns |
|------|------|---------|
| `gene_variants` | `gene_symbol`, `dataset` | gnomAD variants in a gene (consequence, AF) |
| `variant_frequency` | `variant_id`, `dataset` | gnomAD allele frequency for one variant |
| `clinvar_record` | `term`, `retmax` | ClinVar records (clinical significance) via NCBI |

```
gene_variants(gene_symbol="BRCA1")
clinvar_record(term="BRCA1 pathogenic")
```

### `chemistry` — compounds + measured bioactivity
Aggregates `alterlab-pubchem`, `alterlab-bindingdb` (+ ChEBI/Rhea references).

| Tool | Args | Returns |
|------|------|---------|
| `compound_by_name` | `name` | PubChem identity + properties (formula, MW, SMILES, InChIKey) |
| `similarity_search` | `smiles`, `threshold`, `max_records` | PubChem 2D Tanimoto neighbors |
| `binding_affinity` | `uniprot_accession`, `cutoff_nm` | BindingDB measured affinities for a target |

```
compound_by_name(name="aspirin")
similarity_search(smiles="CC(=O)Oc1ccccc1C(=O)O", threshold=90)
```

### `genes-ontologies` — genes, proteins, GO, pathways
Aggregates `alterlab-uniprot`, `alterlab-reactome`, `alterlab-gene-db` (+ MyGene, QuickGO).

| Tool | Args | Returns |
|------|------|---------|
| `gene_info` | `query`, `species` | MyGene.info cross-identifier gene record |
| `uniprot_entry` | `accession` | UniProtKB entry (function, features, xrefs) |
| `go_annotations` | `gene_product_id`, `limit` | EBI QuickGO GO annotations |
| `pathways` | `uniprot_accession`, `species` | Reactome pathways a protein participates in |

```
gene_info(query="TP53")
uniprot_entry(accession="P04637")
pathways(uniprot_accession="P04637")
```

## Notes

- Some source-API paths/params are marked `TODO(verify)` in the server code (gnomAD GraphQL
  schema, BindingDB REST, Reactome mapping) — confirm against the live API before production
  use; the shapes are correct but versioned fields drift.
- The connector Python is covered by the repo's trust manifest
  ([`SECURITY_SCAN.md`](../SECURITY_SCAN.md)) and its `.mcp.json` manifests are shape-validated
  by `tests/test_mcp_manifest.py`.
- Marketplace/plugin registration for connectors (vs. the per-domain skill plugins) is a
  deliberate follow-up: connectors are cross-domain infrastructure and do not map to a single
  domain plugin.
