# GWAS Catalog API Reference (REST API v2)

Endpoint specifications, query parameters, response formats, error handling, and summary-statistics file access for the NHGRI-EBI GWAS Catalog. Verified against the live API and its OpenAPI spec on 2026-09-23 (API release 2025-08-01; data release 2026-09-13 per `/v2/metadata`).

## Table of Contents

- [API Overview](#api-overview)
- [Authentication and Rate Limiting](#authentication-and-rate-limiting)
- [Endpoints](#endpoints)
- [Response Format](#response-format)
- [Error Handling](#error-handling)
- [Summary Statistics (FTP)](#summary-statistics-ftp)
- [Migrating from v1](#migrating-from-v1)
- [Additional Resources](#additional-resources)

## API Overview

| Item | Value |
|------|-------|
| Base URL | `https://www.ebi.ac.uk/gwas/rest/api/v2` |
| Guide | https://www.ebi.ac.uk/gwas/rest/api/v2/docs |
| Interactive reference (Swagger UI) | https://www.ebi.ac.uk/gwas/rest/api/v2/swagger-ui/index.html |
| OpenAPI spec | https://www.ebi.ac.uk/gwas/rest/api/v2/rest-api-doc.yaml |
| Release metadata | `GET /v2/metadata` (data release date, EFO version, gene build GRCh38.p14) |

The API serves the literature-curated top associations and study metadata (the same data as the website). It does not serve full genome-wide summary statistics — those are files on the FTP site (see below). The former Summary Statistics API (`/gwas/summary-statistics/api`) returns HTTP 410 Gone; EBI states that an improved summary-statistics API is "coming soon".

## Authentication and Rate Limiting

- **No authentication** — no key or registration.
- **Throttle: 15 requests/second per client.** Calls beyond that are slowed down, so a small `time.sleep(0.1)` between paginated calls keeps batch jobs smooth.
- **Page size:** default 20. Pages of 100–200 are practical; `size=1000` routinely times out.
- Use the FTP summary statistics, not the API, for genome-wide work.

## Endpoints

All are `GET`. Collection endpoints accept `page` (0-based), `size`, and usually `sort` + `direction` (`asc`/`desc`).

### Associations

| Path | Purpose |
|------|---------|
| `/v2/associations` | Search associations |
| `/v2/associations/{association_id}` | One association |
| `/v2/associations/{association_id}/loci` | Loci with `strongest_risk_alleles[]` and `author_reported_genes[]` |

Filters: `rs_id`, `efo_id`, `efo_trait` (label), `show_child_trait` (include descendant traits), `mapped_gene`, `extended_geneset`, `accession_id`, `pubmed_id`, `full_pvalue_set`. Sort fields: `p_value`, `risk_frequency`, `or_value`, `beta_num`.

```bash
curl -s "https://www.ebi.ac.uk/gwas/rest/api/v2/associations?efo_id=MONDO_0005148&sort=p_value&direction=asc&size=20"
curl -s "https://www.ebi.ac.uk/gwas/rest/api/v2/associations?rs_id=rs7903146"
curl -s "https://www.ebi.ac.uk/gwas/rest/api/v2/associations?mapped_gene=TCF7L2&extended_geneset=true"
```

### Studies

| Path | Purpose |
|------|---------|
| `/v2/studies` | Search studies |
| `/v2/studies/{accession_id}` | One study (GCST) |
| `/v2/studies/{accession_id}/ancestries` | Per-stage ancestry and sample breakdown |

Filters: `accession_id`, `pubmed_id`, `disease_trait`, `efo_id`, `efo_trait`, `show_child_trait`, `full_pvalue_set` (has full summary statistics), `cohort`, `gxe`, `ancestral_group`, `no_of_individuals`, `mapped_gene`, `extended_geneset`.

### Variants

| Path | Purpose |
|------|---------|
| `/v2/single-nucleotide-polymorphisms` | Search curated variants |
| `/v2/single-nucleotide-polymorphisms/{rs_id}` | One variant: `locations[]` (`chromosome_name`, `chromosome_position`, `region.name`), `functional_class`, `most_severe_consequence`, `mapped_genes[]`, `alleles`, `merged` |
| `/v2/single-nucleotide-polymorphisms/{rs_id}/genomic-contexts` | Nearby genes with distances |

Filters: `rs_id`, `chromosome` + `bp_location` or `bp_start`/`bp_end` (GRCh38), `mapped_gene`, `extended_geneset`, `pubmed_id`. Results are under `_embedded.snps`.

A few heavily studied variants (rs7903146 among them) have intermittently returned HTTP 500 on the single-variant path; `/v2/associations?rs_id=...` still works for them.

### Traits, genes, publications

| Path | Purpose |
|------|---------|
| `/v2/efo-traits?efo_trait=<text>` | Free-text trait search → `efo_id`, `efo_trait`, `uri` (results under `_embedded.efo_traits`) |
| `/v2/efo-traits/{efo_id}` | One trait |
| `/v2/parent-mappings/{efo_term}` | Parent-category mapping for a trait |
| `/v2/genes/{gene_name}` | Gene record: `location` (e.g. `10:112950015-113167678`), `ensembl_gene_ids`, `entrez_gene_ids`, `biotype` |
| `/v2/publications`, `/v2/publications/{pubmed_id}` | Publication metadata (`title`, `first_author`) |
| `/v2/body-of-works`, `/v2/unpublished-studies` | Pre-publication deposited summary statistics |

**Trait filtering:** `show_child_trait=false` returns data annotated with exactly the query term; `true` adds more specific child terms (e.g. asthma subtypes). State which one you used in any methods section.

**Gene filtering:** by default `mapped_gene` uses the Ensembl mapping shown on the website (gene containing the variant, or the nearest up/downstream genes). `extended_geneset=true` adds all Ensembl and RefSeq genes up/downstream — the behaviour of the old v1 API.

## Response Format

HAL+JSON with snake_case fields:

```json
{
  "_embedded": {
    "associations": [
      {
        "association_id": 164634754,
        "p_value": 0.0,
        "pvalue_mantissa": 3,
        "pvalue_exponent": -1315,
        "risk_frequency": "0.22941",
        "or_value": null,
        "beta": "-",
        "efo_traits": [{"efo_id": "MONDO_0005148", "efo_trait": "type 2 diabetes mellitus"}],
        "reported_trait": ["Type 2 diabetes"],
        "snp_allele": [{"rs_id": "rs7903146", "effect_allele": "T"}],
        "snp_effect_allele": ["rs7903146-T"],
        "mapped_genes": ["TCF7L2"],
        "locations": ["10:112998590"],
        "accession_id": "GCST90492734",
        "pubmed_id": "38374256",
        "first_author": "Suzuki K",
        "_links": {"self": {"href": "..."}, "loci": {"href": "..."}, "snp": {"href": "..."}}
      }
    ]
  },
  "_links": {"first": {}, "self": {}, "next": {}, "last": {}},
  "page": {"size": 20, "totalElements": 8848, "totalPages": 443, "number": 0}
}
```

Field notes:
- `p_value` is a double and underflows to `0.0` for extremely small p-values; `pvalue_mantissa` / `pvalue_exponent` carry the exact value.
- Effect sizes: `or_per_copy_num` (float) and `or_value` (string) for odds ratios; `beta_num` (float, often null) and `beta` (text with unit and direction, e.g. `"0.03556 unit decrease"`); CI in `ci_lower` / `ci_upper` / `range`. Missing values appear as `null` or `"-"`.
- Study records expose `full_summary_stats_available` and `full_summary_stats` (FTP directory URL, or `"NA"`).
- Embedded collection keys: `associations`, `studies`, `snps`, `efo_traits`, `loci`.

## Error Handling

| Status | Meaning |
|--------|---------|
| 200 | Success — note that an unknown `efo_id` or gene gives 200 with an empty page, not 404 |
| 400 | Invalid parameter value |
| 404 | Unknown path or single resource |
| 410 | Retired service (Summary Statistics API) |
| 500 | Server error; retry with backoff, or switch to the `/v2/associations?rs_id=` form |

```python
import time

import requests

def gwas_get(url, params=None, retries=3):
    for attempt in range(retries):
        r = requests.get(url, params=params, timeout=120)
        if r.status_code in (429, 500, 502, 503, 504) and attempt < retries - 1:
            time.sleep(2 ** attempt)
            continue
        r.raise_for_status()
        return r.json()
```

## Summary Statistics (FTP)

- Root: `https://ftp.ebi.ac.uk/pub/databases/gwas/summary_statistics/`
- Layout: `GCST<start>-GCST<end>/<GCST>/` in buckets of 1,000 accessions, e.g. `GCST90475001-GCST90476000/GCST90475667/`
- Harmonised: `harmonised/<GCST>.h.tsv.gz` + `.tbi` + `<GCST>.h.tsv.gz-meta.yaml`
- Index of harmonised files: `harmonised_list.txt` (nightly)
- Format: GWAS-SSF v1.0 — `chromosome`, `base_pair_location`, `effect_allele`, `other_allele`, `beta` or `odds_ratio` (+ `ci_lower`/`ci_upper`), `standard_error`, `effect_allele_frequency`, `p_value`, `rsid`, `variant_id`, `hm_code`, plus study-specific extras (e.g. `n`, `num_cases`)
- Access guide: https://www.ebi.ac.uk/gwas/docs/methods/summary-statistics

```python
from pathlib import Path

import requests

def download_harmonised(accession: str, out_dir: str = ".") -> Path:
    """Download the harmonised GWAS-SSF file for a GCST accession."""
    study = requests.get(f"https://www.ebi.ac.uk/gwas/rest/api/v2/studies/{accession}", timeout=60).json()
    if not study.get("full_summary_stats_available"):
        raise ValueError(f"{accession} has no full summary statistics")
    url = f'{study["full_summary_stats"].replace("http://", "https://")}/harmonised/{accession}.h.tsv.gz'
    out = Path(out_dir) / f"{accession}.h.tsv.gz"
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with out.open("wb") as fh:
            for chunk in r.iter_content(chunk_size=1 << 20):
                fh.write(chunk)
    return out
```

Not every study with full summary statistics has a harmonised copy yet; fall back to the raw file in the study directory (check `harmonised_list.txt` first).

## Migrating from v1

| v1 (deprecated) | v2 |
|-----------------|----|
| `/singleNucleotidePolymorphisms/{rs}/associations?projection=associationBySnp` | `/v2/associations?rs_id={rs}` |
| `/efoTraits/{id}/associations` | `/v2/associations?efo_id={id}` |
| `/efoTraits/search/findByTrait?trait=` | `/v2/efo-traits?efo_trait=` |
| `/singleNucleotidePolymorphisms/search/findByGene?geneName=` | `/v2/associations?mapped_gene=` or `/v2/single-nucleotide-polymorphisms?mapped_gene=` |
| `/singleNucleotidePolymorphisms/search/findByChromBpLocationRange` | `/v2/single-nucleotide-polymorphisms?chromosome=&bp_start=&bp_end=` |
| `/studies/{GCST}` | `/v2/studies/{GCST}` |
| `pvalue`, `pvalueMantissa`, `orPerCopyNum`, `betaNum`, `efoTraits[].trait`, `snps[].rsId`, `loci[].strongestRiskAlleles[]` | `p_value`, `pvalue_mantissa`, `or_per_copy_num`, `beta_num`, `efo_traits[].efo_trait`, `snp_allele[].rs_id`, `/loci` → `strongest_risk_alleles[]` |
| Summary Statistics API `/traits/{id}/associations` | FTP harmonised files + tabix |

v1 was announced as retiring no later than May 2026; treat any remaining v1 responses as borrowed time.

## Additional Resources

- **Jupyter notebooks (v2 examples)**: linked from https://www.ebi.ac.uk/gwas/rest/api/v2/docs
- **Workshop materials**: https://github.com/EBISPOT/GWAS_Catalog-workshop
- **Trait mappings download**: https://www.ebi.ac.uk/gwas/api/search/downloads/trait_mappings
- **Population descriptors**: https://www.ebi.ac.uk/gwas/population-descriptors
- **R client (gwasrapidd)**: https://cran.r-project.org/package=gwasrapidd — the current CRAN release (0.99.18, May 2025) wraps the deprecated v1 API, so expect it to break once v1 is switched off
- **Helpdesk**: gwas-info@ebi.ac.uk
