---
name: alterlab-alphafold-db
description: Access the AlphaFold DB of 240M+ AI-PREDICTED protein structures (v6, plus precomputed homodimer/heterodimer complexes) — retrieve models by UniProt accession, download PDB/mmCIF files, and analyze prediction confidence metrics (pLDDT, PAE). Use when a UniProt ID needs a computationally predicted 3D structure or when no experimental structure exists, for homology modeling, protein engineering, or structure-based drug discovery; for EXPERIMENTALLY determined structures (X-ray, cryo-EM, NMR) prefer alterlab-pdb, to fold a NEW sequence or complex yourself prefer alterlab-alphafold, and for protein sequences, annotations, or accession ID mapping prefer alterlab-uniprot instead. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read WebFetch Bash(curl:*) Bash(python:*)
compatibility: Keyless AlphaFold DB (EBI) REST API (v6 models); EMBL-EBI FTP (v6) or Google Cloud/BigQuery (v4) for bulk proteome downloads
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    last_updated: "2026-09-23"
---

# AlphaFold Database

## Overview

AlphaFold DB is a public repository of AI-predicted 3D protein structures maintained by Google DeepMind and EMBL-EBI. Release v6 (October 2025, synced to UniProt 2025_03) holds ~241 million predictions, including ~40k isoforms and the input MSAs; since March 2026 it also serves precomputed homodimer and heterodimer complex predictions. Access structure predictions with confidence metrics, download coordinate files, retrieve bulk datasets, and integrate predictions into computational workflows.

## When to Use This Skill

This skill should be used when working with AI-predicted protein structures in scenarios such as:

- Retrieving protein structure predictions by UniProt ID or protein name
- Downloading PDB/mmCIF coordinate files for structural analysis
- Analyzing prediction confidence metrics (pLDDT, PAE) to assess reliability
- Accessing bulk proteome datasets (EMBL-EBI FTP or Google Cloud Platform)
- Comparing predicted structures with experimental data
- Performing structure-based drug discovery or protein engineering
- Building structural models for proteins lacking experimental structures
- Integrating AlphaFold predictions into computational pipelines

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Experimental X-ray / cryo-EM / NMR structure by PDB ID | `alterlab-pdb` |
| Folding a new or mutated sequence, or a custom protein–protein complex, yourself (ColabFold / AF2-Multimer) | `alterlab-alphafold` |
| Protein–ligand or protein–nucleic-acid co-folding | `alterlab-boltz` |
| Protein sequence, functional annotation, or accession ID mapping only | `alterlab-uniprot` |

## Core Capabilities

Worked, copy-paste Python recipes for every capability below live in
`references/code_examples.md`. Load it when you need runnable code; the summaries
here give the routing and the key decisions.

### 1. Searching and Retrieving Predictions

Three entry points, in order of preference:

- **Biopython** (recommended): `Bio.PDB.alphafold_db.get_predictions(accession)`,
  `download_cif_for(...)`, `get_structural_models_for(...)` — simplest path.
- **Direct REST**: `GET https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}`.
  The response is a list of every model for that accession — the canonical
  sequence plus isoforms (`P00520-2`, …) and, for some entries, third-party
  models — so select the record whose `uniprotAccession` equals your query
  rather than trusting `[0]`. The model ID is `modelEntityId` (e.g.
  `AF-P00520-F1`); `entryId` is the legacy name that passed its announced
  2026-06-25 sunset, so don't build new code on it. Complex models are
  excluded unless you pass `?include_complexes=true` (or call
  `/api/complex/{id}`).
- **Find accessions first via UniProt** when you only have a gene name or PDB ID —
  use the UniProt ID-mapping job API (`get_uniprot_ids` helper in
  `code_examples.md` §1; valid db names at
  https://rest.uniprot.org/configure/idmapping/fields).

### 2. Downloading Structure Files

The `/prediction` response carries version-stamped file URLs — **use those, don't
hand-build a `_v{N}` suffix.** The DB version advances (currently v6) and old
`_v4` file URLs now 404:

- `cifUrl` / `pdbUrl` / `bcifUrl` — atomic coordinates (mmCIF / PDB / binary CIF).
- `plddtDocUrl` — per-residue pLDDT scores (0-100).
- `paeDocUrl` — PAE matrix.

Download recipe (resolve URLs from the API, write bytes) in `code_examples.md` §2.

### 3. Working with Confidence Metrics

- **pLDDT**: from `plddtDocUrl`, read `confidence['confidenceScore']` (keys:
  `residueNumber`, `confidenceScore`, `confidenceCategory`); thresholds in
  "Confidence Interpretation Guidelines" below.
- **PAE**: from `paeDocUrl`. The endpoint returns a single-element JSON array of
  one object, so index `[0]` before the key
  (`pae[0]['predicted_aligned_error']`). Visualization recipe in
  `code_examples.md` §3.

### 4. Bulk Data Access (FTP v6 or Google Cloud v4)

- **Model organisms, global-health proteomes, Swiss-Prot (v6):** one tar per
  proteome at `https://ftp.ebi.ac.uk/pub/databases/alphafold/latest/`
  (e.g. `UP000005640_9606_HUMAN_v6.tar`; the index is `download_metadata.json`
  in the parent directory). Lower-confidence complex predictions are bulk-only,
  under `.../alphafold/collaborations/nvda/`.
- **Any taxon (v4):** `gs://public-datasets-deepmind-alphafold-v4/proteomes/`
  with `gsutil`, or query `bigquery-public-data.deepmind_alphafold.metadata` to
  filter by organism/confidence. The species-download helper validates the
  taxonomy ID and uses list-form `subprocess.run` (never `shell=True`).

See `code_examples.md` §4 and `references/api_reference.md` (Bulk Downloads).

### 5. Parsing and Analyzing Structures

Parse mmCIF with `Bio.PDB.MMCIFParser`; pLDDT is stored in the B-factor column
(`residue['CA'].get_bfactor()`). Contact-map and B-factor extraction recipes in
`code_examples.md` §5.

### 6. Batch Processing Multiple Proteins

Loop accessions → predictions → confidence stats → summary DataFrame. Full
example in `code_examples.md` §6.

## Installation and Setup

```bash
uv pip install biopython requests          # core: structure access + API
uv pip install numpy matplotlib pandas scipy  # analysis + PAE plots
uv pip install google-cloud-bigquery gsutil   # optional: bulk GCP access
```

**3D-Beacons alternative:** AlphaFold is also reachable via the 3D-Beacons
federated API (`https://www.ebi.ac.uk/pdbe/pdbe-kb/3dbeacons/api/uniprot/summary/{id}.json`),
filtering entries where `structures[i]['summary']['provider'] == 'AlphaFold DB'`. Recipe in
`code_examples.md` (3D-Beacons section).

## Common Use Cases

### Structural Proteomics
- Download complete proteome predictions for analysis
- Identify high-confidence structural regions across proteins
- Compare predicted structures with experimental data
- Build structural models for protein families

### Drug Discovery
- Retrieve target protein structures for docking studies
- Analyze binding site conformations
- Identify druggable pockets in predicted structures
- Compare structures across homologs

### Protein Engineering
- Identify stable/unstable regions using pLDDT
- Design mutations in high-confidence regions
- Analyze domain architectures using PAE
- Model protein variants and mutations

### Evolutionary Studies
- Compare ortholog structures across species
- Analyze conservation of structural features
- Study domain evolution patterns
- Identify functionally important regions

## Key Concepts

**UniProt Accession:** Primary identifier for proteins (e.g., "P00520"). Required for querying AlphaFold DB.

**AlphaFold model ID (`modelEntityId`):** `AF-[UniProt accession]-F[fragment number]` for DeepMind monomer models (e.g., "AF-P00520-F1"; isoforms look like "AF-P00520-2-F1"). Complex and third-party models use opaque numeric IDs (e.g., "AF-0000000365776990"); both forms are accepted by `/api/prediction/{id}`.

**pLDDT (predicted Local Distance Difference Test):** Per-residue confidence metric (0-100). Higher values indicate more confident predictions.

**PAE (Predicted Aligned Error):** Matrix indicating confidence in relative positions between residue pairs. Low values (<5 Å) suggest confident relative positioning.

**Database Version:** The REST API and the FTP `latest/` archives serve v6 (the response reports `latestVersion` / `allVersions`); the GCS/BigQuery datasets lag at v4. File URLs include a version suffix (e.g., `model_v6.cif`, while newer third-party models start at `_v1`) — read them from the prediction response rather than hardcoding the suffix.

**Fragment Number:** Large proteins may be split into fragments. Fragment number appears in AlphaFold ID (e.g., F1, F2).

## Confidence Interpretation Guidelines

**pLDDT Thresholds:**
- **>90**: Very high confidence - suitable for detailed analysis
- **70-90**: High confidence - generally reliable backbone structure
- **50-70**: Low confidence - use with caution, flexible regions
- **<50**: Very low confidence - likely disordered or unreliable

**PAE Guidelines:**
- **<5 Å**: Confident relative positioning of domains
- **5-10 Å**: Moderate confidence in arrangement
- **>15 Å**: Uncertain relative positions, domains may be mobile

## Resources

### references/code_examples.md

Worked, copy-paste Python recipes for every Core Capability: prediction
retrieval (Biopython / REST / UniProt mapping), file downloads, pLDDT + PAE
analysis, GCP/BigQuery bulk access, mmCIF parsing, batch processing, and the
3D-Beacons alternative.

Load this when you need runnable code.

### references/api_reference.md

Comprehensive API documentation covering:
- Complete REST API endpoint specifications
- File format details and data schemas
- Google Cloud dataset structure and access patterns
- Advanced query examples and batch processing strategies
- Rate limiting, caching, and best practices
- Troubleshooting common issues

Consult this reference for detailed API information, bulk download strategies, or when working with large-scale datasets.

## Important Notes

### Data Usage and Attribution

- AlphaFold DB is freely available under CC-BY-4.0 license
- Cite: Jumper et al. (2021) Nature, plus the AFDB paper for the release you used — Varadi et al. (2024) NAR for v4, Bertoni et al. (2026) NAR (doi:10.1093/nar/gkaf1226) for v6
- Predictions are computational models, not experimental structures
- Always assess confidence metrics before downstream analysis

### Version Management

- REST API and FTP `latest/` serve v6 (`latestVersion`); GCS/BigQuery bulk datasets lag at v4
- Read file URLs from the `/prediction` response — never hardcode the `_v{N}` suffix
- Old `_v4` file URLs now 404; superseded versions are removed from `/files` (older releases remain on the FTP site under `v1/`–`v6/`)
- The v6 field renames (`entryId`→`modelEntityId`, `uniprotStart/End`→`sequenceStart/End`, `uniprotSequence`→`sequence`, `isReviewed`→`isUniProtReviewed`) passed their 2026-06-25 sunset; `paeImageUrl` is slated for removal — use `paeDocUrl`
- Track which version a downloaded result came from

### Data Quality Considerations

- High pLDDT doesn't guarantee functional accuracy
- Low confidence regions may be disordered in vivo
- PAE indicates relative domain confidence, not absolute positioning
- Predictions lack ligands, post-translational modifications, and cofactors
- Default `/prediction` results are single chains. Precomputed complexes (≈1.7M high-confidence homodimers and ≈80k heterodimers, added March–May 2026) come back only with `include_complexes=true` or `/api/complex/{id}`; judge them by interface metrics (ipTM, pDockQ) as well as pLDDT. For a complex that is not in the DB, fold it yourself (`alterlab-alphafold`)

### Performance Tips

- Use Biopython for simple single-protein access
- Use the FTP proteome tars or Google Cloud for bulk downloads (much faster than individual files)
- Cache downloaded files locally to avoid repeated downloads
- BigQuery free tier: 1 TB processed data per month
- Consider network bandwidth for large-scale downloads

## Additional Resources

- **AlphaFold DB Website:** https://alphafold.ebi.ac.uk/
- **API Documentation:** https://alphafold.ebi.ac.uk/api-docs (machine-readable spec: https://alphafold.ebi.ac.uk/api/openapi.json)
- **Release notes / FTP changelog:** https://www.ebi.ac.uk/pdbe/news/alphafold-database-release-notes, https://ftp.ebi.ac.uk/pub/databases/alphafold/CHANGELOG.txt
- **Google Cloud Dataset:** https://cloud.google.com/blog/products/ai-machine-learning/alphafold-protein-structure-database
- **3D-Beacons API:** https://www.ebi.ac.uk/pdbe/pdbe-kb/3dbeacons/
- **AlphaFold Papers:**
  - Nature (2021): https://doi.org/10.1038/s41586-021-03819-2
  - Nucleic Acids Research (2024): https://doi.org/10.1093/nar/gkad1011
- **Biopython Documentation:** https://biopython.org/docs/dev/api/Bio.PDB.alphafold_db.html
- **GitHub Repository:** https://github.com/google-deepmind/alphafold

## Scripts

`scripts/query_alphafold.py` — runnable helper for the AlphaFold REST API (no key):

```bash
python scripts/query_alphafold.py prediction P00520
python scripts/query_alphafold.py confidence P00520 --summary
python scripts/query_alphafold.py download P00520 --fmt cif -o ./structures
```

