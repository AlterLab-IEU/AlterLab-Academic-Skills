# GWAS Catalog Data Fields and Best Practices

Response record fields, pagination, query/interpretation best practices, and data-quality considerations.

## Data Structure Overview

The GWAS Catalog is organized around four core entities:

- **Studies**: GWAS publications with metadata (PMID, author, cohort details)
- **Associations**: SNP-trait associations with statistical evidence (p ≤ 5×10⁻⁸)
- **Variants**: Genetic markers (SNPs) with genomic coordinates and alleles
- **Traits**: Phenotypes and diseases (mapped to EFO ontology terms)

**Key Identifiers:**
- Study accessions: `GCST` IDs (e.g., GCST001234)
- Variant IDs: `rs` numbers (e.g., rs7903146); summary-statistics files add `variant_id` (`chr_pos_ref_alt`, GRCh38)
- Trait IDs: ontology short-forms in `efo_id` (e.g., MONDO_0005148 for type 2 diabetes mellitus; the legacy EFO_0001360 returns no rows)
- Gene symbols: HGNC approved names (e.g., TCF7L2)

## Response Formats and Data Fields

**Key fields in v2 association records** (`_embedded.associations[]`, verified against the live API 2026-09; v1 camelCase names such as `pvalue`, `efoTraits`, `orPerCopyNum` no longer apply):

- `p_value`: float — **underflows to `0.0`** for p below ~1e-308 (rs7903146 in T2D reaches 3e-1315); rank by the tuple (`pvalue_exponent`, `pvalue_mantissa`) and report the string `f"{mantissa}e{exponent}"`
- `pvalue_description`: qualifier text (e.g. conditional analysis, sub-group)
- `snp_allele[]`: `{rs_id, effect_allele}`; `snp_effect_allele[]`: strings like `rs7903146-T`
- `efo_traits[]`: `{efo_id, efo_trait}` mapped ontology terms; `reported_trait[]`: author wording; `bg_efo_traits[]`: background traits
- `or_per_copy_num` (float) / `or_value` (string): odds ratio; `beta_num` (float, often null) and `beta` (text such as `"0.0356 unit decrease"`); absent values are `"-"` or `null`
- `ci_lower`, `ci_upper`, `range` (e.g. `[4.12-25.21]`): 95% CI
- `risk_frequency`: reported risk-allele frequency (string; may be empty or a placeholder when not reported)
- `mapped_genes[]`, `locations[]` (`"10:112998590"`, GRCh38)
- `accession_id`, `pubmed_id`, `first_author`: inline study provenance
- `_links.loci` → `strongest_risk_alleles[].risk_allele_name`; `_links.snp` → the variant record

To list rsID/trait/p-value for an association `a`:
```python
rs = a["snp_allele"][0]["rs_id"] if a.get("snp_allele") else None
trait = "; ".join(t["efo_trait"] for t in a["efo_traits"])
pval = f'{a["pvalue_mantissa"]}e{a["pvalue_exponent"]}'   # keep as text; float() gives 0.0 below ~1e-323
```

**Study metadata fields** (`/v2/studies`):
- `accession_id`, `pubmed_id`, `disease_trait`, `efo_traits[]`
- `initial_sample_size`, `replication_sample_size` (free text with ancestry and case/control counts)
- `discovery_ancestry[]`, `replication_ancestry[]`, `cohort[]`
- `full_summary_stats_available` (bool) and `full_summary_stats` (FTP directory or `"NA"`)
- `snp_count`, `imputed`, `platforms`, `genotyping_technologies[]`, `gxe`, `gxg`, `terms_of_license`

**Pagination:**
Results are paginated (default 20 items per page). Navigate using:
- `size` (keep ≤ 200; larger pages time out) and `page` (0-indexed)
- `page` object in the response: `size`, `totalElements`, `totalPages`, `number`
- `_links.next` / `_links.last` URLs

## Best Practices

### Query Strategy
- Start with web interface to identify relevant EFO terms and study accessions
- Use API for bulk data extraction and automated analyses
- Implement pagination handling for large result sets
- Cache API responses to minimize redundant requests

### Data Interpretation
- Always check p-value thresholds (genome-wide: 5×10⁻⁸)
- Review ancestry information for population applicability
- Consider sample size when assessing evidence strength
- Check for replication across independent studies
- Be aware of winner's curse in effect size estimates

### Rate Limiting and Ethics
- The API throttles each client at 15 requests/second (calls beyond that are slowed down)
- Use summary statistics downloads for genome-wide analyses
- Implement appropriate delays between API calls
- Cache results locally when performing iterative analyses
- Cite the GWAS Catalog in publications

### Data Quality Considerations
- GWAS Catalog curates published associations (may contain inconsistencies)
- Effect sizes reported as published (may need harmonization)
- Some studies report conditional or joint associations
- Check for study overlap when combining results
- Be aware of ascertainment and selection biases

## Important Notes

### Data Updates
- The GWAS Catalog is updated regularly with new publications
- Re-run queries periodically for comprehensive coverage
- Summary statistics are added as studies release data
- EFO mappings may be updated over time

### Limitations
- Not all GWAS publications are included (curation criteria apply)
- Full summary statistics available for subset of studies
- Effect sizes may require harmonization across studies
- Population diversity is growing but historically limited
- Some associations represent conditional or joint effects

### Data Access
- Web interface: Free, no registration required
- REST API v2: Free, no API key needed (15 requests/second throttle)
- FTP downloads: Open access (full and harmonised summary statistics)
- The Summary Statistics API is retired; v1 REST paths are deprecated
