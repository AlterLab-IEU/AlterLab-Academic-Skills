---
name: alterlab-gwas
description: Query the NHGRI-EBI GWAS Catalog REST API v2 for curated SNP-trait associations, retrieving variants by rs ID, disease/trait (EFO/MONDO), gene, or study (GCST) with p-values, effect sizes, and ancestry, and locate full harmonised summary statistics on the FTP site. Use when investigating genome-wide association study hits, mapping a SNP or rsID to traits, selecting GWAS for polygenic risk scores or fine-mapping, or doing genetic epidemiology lookups. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read WebFetch Bash(curl:*) Bash(python:*)
compatibility: Keyless NHGRI-EBI GWAS Catalog REST API v2 (no authentication; 15 requests/s throttle); summary statistics via FTP (the Summary Statistics API is retired)
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# GWAS Catalog Database

## Overview

The GWAS Catalog is a curated repository of published genome-wide association studies maintained by NHGRI and EBI. It contains SNP-trait associations from thousands of GWAS publications — genetic variants, associated traits and diseases, p-values, effect sizes, and full summary statistics for many studies.

## Scripts

`scripts/query_gwas.py` — query the GWAS Catalog REST API (stdlib only, JSON to stdout):

```bash
python scripts/query_gwas.py variant rs7903146                 # associations for a SNP (strongest first)
python scripts/query_gwas.py trait MONDO_0005148 --size 100    # associations for a trait
python scripts/query_gwas.py gene TCF7L2                       # associations mapped to a gene
python scripts/query_gwas.py find-trait "type 2 diabetes"      # free text -> efo_id
python scripts/query_gwas.py study GCST001795                  # study metadata (+ summary-stats FTP link)
```

## When to Use This Skill

Use this skill for:
- **Genetic variant associations** — SNPs associated with diseases or traits
- **SNP lookups** — information about specific variants (rs IDs)
- **Trait/disease searches** — genetic associations for phenotypes
- **Gene associations** — variants in or near specific genes
- **GWAS summary statistics** — complete genome-wide association data
- **Study metadata** — publication and cohort information
- **Population genetics** — ancestry-specific associations
- **Polygenic risk scores** — variants for risk prediction models
- **Functional genomics** / **systematic reviews** — variant effects, literature synthesis

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Target-disease association scores, L2G / colocalisation evidence for drug targets | `alterlab-opentargets` |
| Clinical pathogenicity of a variant (ACMG/AMP, review stars) | `alterlab-clinvar` |
| Population allele frequencies or gene constraint | `alterlab-gnomad` |
| Which gene/tissue a variant regulates (eQTL/sQTL) | `alterlab-gtex` |
| Variant consequence (VEP), coordinates, gene models | `alterlab-ensembl` |

## Data Model

Four core entities, each with a canonical identifier:
- **Studies** → `GCST` accessions (e.g., GCST001234)
- **Associations** → SNP-trait links with p-values (genome-wide significant: p ≤ 5×10⁻⁸)
- **Variants** → `rs` numbers (e.g., rs7903146)
- **Traits** → ontology short-forms in `efo_id` (e.g., MONDO_0005148 = type 2 diabetes mellitus); genes use HGNC symbols (e.g., TCF7L2)

> **Trait-ID gotcha (verified 2026-09):** many traits have been re-mapped to MONDO / current EFO short-forms, and a stale ID returns an empty page rather than an error — `associations?efo_id=EFO_0001360` (legacy type 2 diabetes) gives 0 rows while `efo_id=MONDO_0005148` gives thousands. Resolve free text first with `GET /v2/efo-traits?efo_trait=type 2 diabetes` and use the returned `efo_id`. Older papers and pipelines may still cite the legacy EFO ID.

## APIs

- **GWAS Catalog REST API v2** (released Aug 2025): `https://www.ebi.ac.uk/gwas/rest/api/v2` — curated top associations, studies, SNPs, traits, genes, publications. Free, no key; throttled at 15 requests/second; default page size 20 (keep `size` ≤ 200 — larger pages time out). Interactive reference: https://www.ebi.ac.uk/gwas/rest/api/v2/docs
- **Legacy v1** (`/gwas/rest/api/singleNucleotidePolymorphisms/...`, `/efoTraits/...`, camelCase fields) is deprecated and was scheduled for retirement by May 2026; it may still answer, but don't write new code against it.
- **Summary Statistics API** (`/gwas/summary-statistics/api`) is retired (HTTP 410); full summary statistics are served from the FTP site (see workflow step 6). EBI describes a replacement API as "coming soon".

Core v2 endpoints: `/v2/associations` (filters `rs_id`, `efo_id`, `efo_trait`, `mapped_gene`, `accession_id`, `pubmed_id`; `sort=p_value&direction=asc`), `/v2/studies` and `/v2/studies/{accession_id}`, `/v2/single-nucleotide-polymorphisms` (by `rs_id`, `mapped_gene`, or `chromosome` + `bp_start`/`bp_end`), `/v2/efo-traits`, `/v2/genes/{gene_name}`. Responses are HAL+JSON with snake_case fields: results under `_embedded.<resource>` (`associations`, `studies`, `snps`, `efo_traits`), paging under `page` (`totalElements`, `totalPages`, `number`), next pages in `_links.next`.

## Core Workflow

1. **Identify the entity** — get the `efo_id` (trait; resolve free text via `/v2/efo-traits?efo_trait=`), rs ID (variant), GCST (study), or HGNC symbol (gene).
2. **Query the matching endpoint** — trait/variant/study/gene/region; iterate pages via `page`/`size` or follow `_links.next`.
3. **Filter** — by p-value (≤ 5×10⁻⁸ for genome-wide significance), ancestry, sample size, discovery/replication status.
4. **Extract** — rs IDs and effect alleles (`snp_allele[]`), effect sizes (`or_per_copy_num` or the `beta` text), p-values. `p_value` underflows to `0.0` for very strong signals (rs7903146 in type 2 diabetes reaches 3×10⁻¹³¹⁵), so rank and report with `pvalue_mantissa` / `pvalue_exponent`.
5. **Cross-reference** — Ensembl (consequences), gnomAD (frequencies), Open Targets, PGS Catalog.
6. **For genome-wide analyses** — find studies with `/v2/studies?efo_id=...&full_pvalue_set=true`; each study's `full_summary_stats` field gives its FTP directory. Harmonised files live at `https://ftp.ebi.ac.uk/pub/databases/gwas/summary_statistics/GCST<range>/<GCST>/harmonised/<GCST>.h.tsv.gz` (GWAS-SSF columns, tabix-indexed `.tbi`), so a region can be pulled remotely with `tabix <url> 10:112900000-113200000` instead of downloading the whole file. Don't scrape the association endpoints for this — they hold only curated top hits.

## Routing Guidance

- **Writing API calls / want copy-paste code** (endpoints, the four worked examples, summary-stats access, cross-referencing, full paginated Python helper) → `references/query_examples.md`.
- **Following a multi-step task** (disease-, variant-, gene-centric, systematic review, summary-stats analysis) or **web-interface search syntax** → `references/query_workflows.md`.
- **Need response field names, pagination details, or best-practice / data-quality guidance** → `references/data_fields_and_best_practices.md`.
- **Deep endpoint specs, all query params, error handling, advanced filtering** → `references/api_reference.md`.

## Reference Index

- **`references/query_examples.md`** — REST endpoint code, four canonical query examples (disease, variant, summary stats, chromosomal region), summary-statistics access, cross-referencing, and a complete paginated Python integration returning a DataFrame.
- **`references/query_workflows.md`** — Five step-by-step query workflows (disease, variant, gene, systematic review, summary statistics) plus web-interface search modes.
- **`references/data_fields_and_best_practices.md`** — Association/study response fields, pagination, query and interpretation best practices, rate-limiting ethics, and data-quality considerations.
- **`references/api_reference.md`** — Comprehensive endpoint specifications, query parameters/filters, response formats, error handling, and integration with external databases.

## Citation and Resources

When using GWAS Catalog data, cite:
- Sollis E, et al. (2023) The NHGRI-EBI GWAS Catalog: knowledgebase and deposition resource. Nucleic Acids Research 51:D977-D985. PMID: 36350656. DOI: 10.1093/nar/gkac1010
- Include access date and version when available; cite original studies when discussing specific findings.

- **Website**: https://www.ebi.ac.uk/gwas/
- **Documentation**: https://www.ebi.ac.uk/gwas/docs
- **API v2 docs**: https://www.ebi.ac.uk/gwas/rest/api/v2/docs (OpenAPI: https://www.ebi.ac.uk/gwas/rest/api/v2/rest-api-doc.yaml)
- **Summary statistics access**: https://www.ebi.ac.uk/gwas/docs/methods/summary-statistics
- **FTP site**: https://ftp.ebi.ac.uk/pub/databases/gwas/
- **Training materials**: https://github.com/EBISPOT/GWAS_Catalog-workshop (Jupyter notebooks, Colab)
- **PGS Catalog** (polygenic scores): https://www.pgscatalog.org/
- **Help and support**: gwas-info@ebi.ac.uk
