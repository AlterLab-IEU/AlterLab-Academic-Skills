---
name: alterlab-hmdb
description: Access the Human Metabolome Database (HMDB, 220K+ metabolites), searching by name, HMDB ID, or structure to retrieve chemical properties, biomarker data, NMR/MS reference spectra, and associated pathways. Use when identifying a human metabolite, looking up its biomarker or disease associations, matching NMR/MS spectra, or running metabolomics annotation. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read WebFetch Bash(curl:*) Bash(python:*)
compatibility: No public REST API and hmdb.ca blocks scripted clients (Cloudflare challenge); keyless HMDB content via scripts/hmdb_open.py (PubChem RegistryID xrefs and HMDB-sourced PUG-View annotations, MarkerDB concentrations by biofluid); bulk XML/SDF downloads in a browser
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-10-23"
---

# HMDB Database

## Overview

The Human Metabolome Database (HMDB) is a comprehensive, freely available resource containing detailed information about small molecule metabolites found in the human body.

## Scripts

HMDB serves no public REST API, and the whole site (records, `.xml` URLs, search, downloads)
answers scripted requests with a Cloudflare challenge (HTTP 403, `cf-mitigated: challenge`;
checked 2026-10-23). **Start with `scripts/hmdb_open.py`** (stdlib only, JSON to stdout), which
assembles HMDB content from keyless mirrors and labels every value with its source:

```bash
python scripts/hmdb_open.py record HMDB0000001        # identity + HMDB annotations + concentrations
python scripts/hmdb_open.py disease "diabetes mellitus type 2" --biofluid Blood   # biomarkers
python scripts/hmdb_open.py structure "CN1C=NC2=C1C(=O)N(C(=O)N2)C"   # SMILES -> HMDB ID(s)
```

- `record`: PubChem (HMDB accessions are PubChem RegistryIDs) gives name, formula, average and
  monoisotopic mass, SMILES, InChI/InChIKey; PubChem's HMDB-sourced PUG-View entries give tissue
  and cellular locations, metabolite pathways and disease associations with PubMed IDs; MarkerDB
  (Wishart lab, built on HMDB) gives measured normal and condition concentrations per biofluid.
  HMDB0000001 -> 1-methyl-L-histidine, C7H11N3O2, 169.18; measured in Blood (normal 12.7 µM) and
  Urine. HMDB's full biospecimen list (e.g. CSF, saliva, feces entries without concentrations)
  is only on hmdb.ca: say so instead of filling it in from memory.
- `disease`: MarkerDB's condition card — every chemical biomarker with biofluid, disease vs
  normal concentration, p-value/AUC where given, clinical status, PMIDs and HMDB ID. "Diabetes
  Mellitus Type 2" -> 28 records over 24 metabolites, 21 in Blood (e.g. D-glucose HMDB0000122
  6300 vs 3900 µM; 1,5-anhydrosorbitol HMDB0002712 62 vs 150 µM). MarkerDB/HMDB report serum
  and plasma together as "Blood".
- `structure`: exact-structure match -> PubChem CID -> HMDB accession(s), plus same-formula
  isomers that carry an HMDB accession (paraxanthine HMDB0001860 vs theophylline HMDB0001889 and
  theobromine HMDB0002825 — a mass match alone cannot separate them).

`scripts/query_hmdb.py` fetches and parses the HMDB XML record itself (`python
scripts/query_hmdb.py HMDB0000001`) and works only where hmdb.ca lets your network through.
For bulk work download the XML/SDF dumps from https://www.hmdb.ca/downloads in a browser.

## When to Use This Skill

This skill should be used when performing metabolomics research, clinical chemistry, biomarker discovery, or metabolite identification tasks: identifying a human metabolite, reading its biofluid concentrations and disease/biomarker associations, or matching it against HMDB reference NMR/MS spectra.

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Generic compound identifiers, properties, or bioassays for any small molecule | `alterlab-pubchem` |
| Primary metabolomics study datasets, RefMet standardized names | `alterlab-metabolomics-wb` |
| Pathway maps and KEGG compound/reaction IDs | `alterlab-kegg` |
| Computing MS/MS spectral similarity on your own spectra files | `alterlab-matchms` |
| Drug pharmacology, targets, and interactions | `alterlab-drugbank` |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-pubchem`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

## Database Contents

HMDB version 5.0 (released 2022; latest major version as of mid-2026) contains:

- **220,945 metabolite entries** covering both water-soluble and lipid-soluble compounds (the v5.0 paper reported 217,920; the live site count grows with curation)
- **~8,600 protein sequences** for enzymes and transporters involved in metabolism
- **130+ data fields per metabolite** including:
  - Chemical properties (structure, formula, molecular weight, InChI, SMILES)
  - Clinical data (biomarker associations, diseases, normal/abnormal concentrations)
  - Biological information (pathways, reactions, locations)
  - Spectroscopic data (NMR, MS, MS-MS spectra)
  - External database links (KEGG, PubChem, MetaCyc, ChEBI, PDB, UniProt, GenBank)

## Core Capabilities

### 1. Web-Based Metabolite Searches

Access HMDB through the web interface at https://www.hmdb.ca/ for:

**Text Searches:**
- Search by metabolite name, synonym, or identifier (HMDB ID)
- Example HMDB IDs: HMDB0000001, HMDB0001234
- Search by disease associations or pathway involvement
- Query by biological specimen type (urine, serum, CSF, saliva, feces, sweat)

**Structure-Based Searches:**
- Use ChemQuery for structure and substructure searches
- Search by molecular weight or molecular weight range
- Use SMILES or InChI strings to find compounds

**Spectral Searches:**
- LC-MS spectral matching
- GC-MS spectral matching
- NMR spectral searches for metabolite identification

**Advanced Searches:**
- Combine multiple criteria (name, properties, concentration ranges)
- Filter by biological locations or specimen types
- Search by protein/enzyme associations

### 2. Accessing Metabolite Information

When retrieving metabolite data, HMDB provides:

**Chemical Information:**
- Systematic name, traditional names, and synonyms
- Chemical formula and molecular weight
- Structure representations (2D/3D, SMILES, InChI, MOL file)
- Chemical taxonomy and classification

**Biological Context:**
- Metabolic pathways and reactions
- Associated enzymes and transporters
- Subcellular locations
- Biological roles and functions

**Clinical Relevance:**
- Normal concentration ranges in biological fluids
- Biomarker associations with diseases
- Clinical significance
- Toxicity information when applicable

**Analytical Data:**
- Experimental and predicted NMR spectra
- MS and MS-MS spectra
- Retention times and chromatographic data
- Reference peaks for identification

### 3. Downloadable Datasets

HMDB offers bulk data downloads at https://www.hmdb.ca/downloads in multiple formats:

**Available Formats:**
- **XML**: Complete metabolite, protein, and spectra data
- **SDF**: Metabolite structure files for cheminformatics
- **FASTA**: Protein and gene sequences
- **TXT**: Raw spectra peak lists
- **CSV/TSV**: Tabular data exports

**Dataset Categories:**
- All metabolites or filtered by specimen type
- Protein/enzyme sequences
- Experimental and predicted spectra (NMR, GC-MS, MS-MS)
- Pathway information

**Best Practices:**
- Download XML format for comprehensive data including all fields
- Use SDF format for structure-based analysis and cheminformatics workflows
- Parse CSV/TSV formats for integration with data analysis pipelines
- Check version dates to ensure up-to-date data (current major version: v5.0)

**Usage Requirements:**
- Free for academic and non-commercial research
- Commercial use requires explicit permission (contact samackay@ualberta.ca)
- Cite HMDB publication when using data

### 4. Programmatic Access

HMDB publishes **no documented public REST API**. Practical programmatic routes, in order of preference:

- **Bulk downloads (preferred for any volume):** Parse the XML/SDF/CSV dumps from https://www.hmdb.ca/downloads locally. This is the only route that scales and won't get rate-limited.
- **Per-record XML endpoint:** Each entry is served as XML at `https://www.hmdb.ca/metabolites/<ID>.xml` (used by `scripts/query_hmdb.py`). Undocumented, and in Sept 2026 it answered scripted clients with a Cloudflare challenge (HTTP 403) — usable only when your network is allowed through; never for batch jobs. When it is blocked, say so rather than filling fields from memory.
- **Keyless HMDB content (works when hmdb.ca blocks you):** `scripts/hmdb_open.py` (see Scripts) combines the two routes below with MarkerDB's concentration records.
- **Cross-references through open APIs:** PubChem indexes HMDB accessions as registry IDs — `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/xref/RegistryID/HMDB0000001/cids/JSON` returns CID 92105 (1-methylhistidine), after which structure and properties come from PubChem (`alterlab-pubchem`). UniChem maps HMDB (source 18) to ChEBI/ChEMBL/KEGG: `POST https://www.ebi.ac.uk/unichem/api/v1/compounds` with `{"type": "sourceID", "compound": "HMDB0000001", "sourceID": 18}`. PubChem also mirrors HMDB's tissue/cellular locations, pathways and disease associations (PUG-View sections whose source is "Human Metabolome Database (HMDB)"), and MarkerDB (https://markerdb.ca, keyless HTML; its JSON API needs a key) holds normal and disease concentrations by biofluid. Reference NMR/MS spectra still require HMDB itself (or its downloads).
- **R/Bioconductor `hmdbQuery`:** deprecated and removed from current Bioconductor (last shipped in 3.21); don't build new workflows on it.
- **Custom API:** For sanctioned bulk/commercial API access, contact the HMDB team (see Usage Requirements above for the listed address).

### 5. Common Research Workflows

**Metabolite Identification in Untargeted Metabolomics:**
1. Obtain experimental MS or NMR spectra from samples
2. Use HMDB spectral search tools to match against reference spectra
3. Verify candidates by checking molecular weight, retention time, and MS-MS fragmentation
4. Review biological plausibility (expected in specimen type, known pathways)

**Biomarker Discovery:**
1. Search HMDB for metabolites associated with disease of interest
2. Review concentration ranges in normal vs. disease states
3. Identify metabolites with strong differential abundance
4. Examine pathway context and biological mechanisms
5. Cross-reference with literature via PubMed links

**Pathway Analysis:**
1. Identify metabolites of interest from experimental data
2. Look up HMDB entries for each metabolite
3. Extract pathway associations and enzymatic reactions
4. Use linked SMPDB (Small Molecule Pathway Database) for pathway diagrams
5. Identify pathway enrichment for biological interpretation

**Database Integration:**
1. Download HMDB data in XML or CSV format
2. Parse and extract relevant fields for local database
3. Link with external IDs (KEGG, PubChem, ChEBI) for cross-database queries
4. Build local tools or pipelines incorporating HMDB reference data

## Related HMDB Resources

The HMDB ecosystem includes related databases:

- **DrugBank**: ~2,832 drug compounds with pharmaceutical information
- **T3DB (Toxin and Toxin Target Database)**: ~3,670 toxic compounds
- **SMPDB (Small Molecule Pathway Database)**: Pathway diagrams and maps
- **FooDB**: ~70,000 food component compounds

These databases share similar structure and identifiers, enabling integrated queries across human metabolome, drug, toxin, and food databases.

## Best Practices

**Data Quality:**
- Verify metabolite identifications with multiple evidence types (spectra, structure, properties)
- Check experimental vs. predicted data quality indicators
- Review citations and evidence for biomarker associations

**Version Tracking:**
- Note HMDB version used in research (current: v5.0)
- Databases are updated periodically with new entries and corrections
- Re-query for updates when publishing to ensure current information

**Citation:**
- Always cite HMDB in publications using the database
- Reference specific HMDB IDs when discussing metabolites
- Acknowledge data sources for downloaded datasets

**Performance:**
- For large-scale analysis, download complete datasets rather than repeated web queries
- Use appropriate file formats (XML for comprehensive data, CSV for tabular analysis)
- Consider local caching of frequently accessed metabolite information

## Reference Documentation

See `references/hmdb_data_fields.md` for detailed information about available data fields and their meanings.

