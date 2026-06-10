# gnomAD GraphQL Query Reference

## API Endpoint

```
POST https://gnomad.broadinstitute.org/api
Content-Type: application/json

Body: { "query": "<graphql_query>", "variables": { ... } }
```

## Dataset Identifiers

These are values of the `DatasetId` enum (used by `variant(...)`, `gene.variants(...)`,
`region.variants(...)`). In v4 there is no separate `_genomes` dataset id: `gnomad_r4`
returns both `exome` and `genome` blocks per variant.

| ID | Description | Reference Genome |
|----|-------------|-----------------|
| `gnomad_r4` | gnomAD v4 exomes + genomes (exomes ~730K, genomes ~76K) | GRCh38 |
| `gnomad_r3` | gnomAD v3 genomes (~76K) | GRCh38 |
| `gnomad_r2_1` | gnomAD v2 exomes (~125K) + genomes | GRCh37 |
| `gnomad_r2_1_non_cancer` | v2 non-cancer subset | GRCh37 |
| `exac` | ExAC (legacy) | GRCh37 |

Structural / copy-number variants use their own enums, NOT `DatasetId`:
- `structural_variants(dataset: StructuralVariantDatasetId!)` — e.g. `gnomad_sv_r4`, `gnomad_sv_r2_1`
- `copy_number_variants(dataset: CopyNumberVariantDatasetId!)` — `gnomad_cnv_r4`

## Core Query Templates

### 1. Variants in a Gene

```graphql
query GeneVariants($gene_symbol: String!, $dataset: DatasetId!, $reference_genome: ReferenceGenomeId!) {
  gene(gene_symbol: $gene_symbol, reference_genome: $reference_genome) {
    gene_id
    symbol             # NB: the field is `symbol`; `gene_symbol` is only the query argument
    chrom
    start
    stop
    variants(dataset: $dataset) {
      variant_id
      pos
      ref
      alt
      consequence
      gene_symbol       # valid here (on the Variant type), unlike on Gene above
      lof
      lof_flags
      lof_filter
      genome {
        af
        ac
        an
        ac_hom
        populations { id ac an ac_hom }   # no `af` subfield — compute af = ac / an
      }
      exome {
        af
        ac
        an
        ac_hom
        populations { id ac an ac_hom }
      }
      rsids
      in_silico_predictors { id value flags }
    }
  }
}
```

### 2. Single Variant Lookup

```graphql
query VariantDetails($variantId: String!, $dataset: DatasetId!) {
  variant(variantId: $variantId, dataset: $dataset) {
    variant_id
    chrom
    pos
    ref
    alt
    rsids
    # consequence/lof are NOT top-level on a single variant — they are per
    # transcript. Pull them from transcript_consequences (use is_canonical
    # to pick the representative one). There is no top-level clinvar_variation_id.
    transcript_consequences {
      gene_symbol
      major_consequence
      consequence_terms
      lof
      lof_flags
      lof_filter
      is_canonical
      polyphen_prediction
      sift_prediction
    }
    genome { af ac an ac_hom populations { id ac an ac_hom } }   # no `af` subfield: af = ac / an
    exome { af ac an ac_hom populations { id ac an ac_hom } }
    in_silico_predictors { id value flags }
  }
}
```

**Variant ID format:** `{chrom}-{pos}-{ref}-{alt}` (e.g., `17-43094692-G-C`)

### 3. Gene Constraint

```graphql
query GeneConstraint($gene_symbol: String!, $reference_genome: ReferenceGenomeId!) {
  gene(gene_symbol: $gene_symbol, reference_genome: $reference_genome) {
    gene_id
    symbol
    gnomad_constraint {
      exp_lof exp_mis exp_syn
      obs_lof obs_mis obs_syn
      oe_lof oe_mis oe_syn
      oe_lof_lower oe_lof_upper
      oe_mis_lower oe_mis_upper
      lof_z mis_z syn_z
      pLI
      flags
    }
  }
}
```

### 4. Region Query (by genomic position)

```graphql
query RegionVariants($chrom: String!, $start: Int!, $stop: Int!, $dataset: DatasetId!, $reference_genome: ReferenceGenomeId!) {
  region(chrom: $chrom, start: $start, stop: $stop, reference_genome: $reference_genome) {
    variants(dataset: $dataset) {
      variant_id
      pos
      ref
      alt
      consequence
      genome { af ac an }
      exome { af ac an }
    }
  }
}
```

### 5. ClinVar Variants in Gene

```graphql
query ClinVarVariants($gene_symbol: String!, $reference_genome: ReferenceGenomeId!) {
  gene(gene_symbol: $gene_symbol, reference_genome: $reference_genome) {
    clinvar_variants {
      variant_id
      pos
      ref
      alt
      clinical_significance
      clinvar_variation_id
      gold_stars
      review_status
      major_consequence
      in_gnomad
      gnomad { exome { ac an } genome { ac an } }   # no `af` subfield: af = ac / an
    }
  }
}
```

## Population IDs

| ID | Population |
|----|-----------|
| `afr` | African/African American |
| `ami` | Amish |
| `amr` | Admixed American |
| `asj` | Ashkenazi Jewish |
| `eas` | East Asian |
| `fin` | Finnish |
| `mid` | Middle Eastern |
| `nfe` | Non-Finnish European |
| `sas` | South Asian |
| `remaining` | Other/Unassigned |
| `XX` | Female (appended to above, e.g., `afr_XX`) |
| `XY` | Male |

## LoF Annotation Fields

| Field | Values | Meaning |
|-------|--------|---------|
| `lof` | `HC`, `LC`, `null` | High/low-confidence LoF, or not annotated as LoF |
| `lof_flags` | comma-separated strings | Quality flags (e.g., `NAGNAG_SITE`, `NON_CANONICAL_SPLICE_SITE`) |
| `lof_filter` | string or null | Reason for LC classification |

## In Silico Predictor IDs

Common values for `in_silico_predictors[].id`:
- `cadd` — CADD PHRED score
- `revel` — REVEL score
- `spliceai_ds_max` — SpliceAI max delta score
- `pangolin_largest_ds` — Pangolin splicing score
- `polyphen` — PolyPhen-2 prediction
- `sift` — SIFT prediction

## Python Helper

```python
import requests
import time

def gnomad_query(query: str, variables: dict, retries: int = 3) -> dict:
    """Execute a gnomAD GraphQL query with retry logic."""
    url = "https://gnomad.broadinstitute.org/api"
    headers = {"Content-Type": "application/json"}

    for attempt in range(retries):
        try:
            response = requests.post(
                url,
                json={"query": query, "variables": variables},
                headers=headers,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()

            if "errors" in result:
                print(f"GraphQL errors: {result['errors']}")
                return result

            return result
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # exponential backoff
            else:
                raise

    return {}
```
