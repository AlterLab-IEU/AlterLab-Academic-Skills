# GWAS Catalog Query Examples (REST API v2)

Code patterns for the v2 REST API, the canonical query examples, summary-statistics access via FTP, cross-referencing, and a complete paginated Python integration.

## REST API Access

**Base URL:** `https://www.ebi.ac.uk/gwas/rest/api/v2` (no key; throttled at 15 requests/second)

**Documentation:** https://www.ebi.ac.uk/gwas/rest/api/v2/docs (guide) and https://www.ebi.ac.uk/gwas/rest/api/v2/rest-api-doc.yaml (OpenAPI spec)

The legacy v1 paths (`/singleNucleotidePolymorphisms/{rs}/associations`, `/efoTraits/{id}/associations`, `projection=associationBySnp`, camelCase fields such as `pvalue`, `efoTraits`, `strongestRiskAlleles`) are deprecated. The Summary Statistics API (`/gwas/summary-statistics/api`) is retired and answers HTTP 410.

**Core endpoints:**

1. **Studies** — `/v2/studies/{accession_id}` or `/v2/studies?efo_id=...&full_pvalue_set=true`
   ```python
   import requests

   BASE = "https://www.ebi.ac.uk/gwas/rest/api/v2"
   study = requests.get(f"{BASE}/studies/GCST001795", timeout=60).json()
   print(study["disease_trait"], study["initial_sample_size"], study["full_summary_stats"])
   ```

2. **Associations** — `/v2/associations` with `rs_id`, `efo_id`, `efo_trait`, `mapped_gene`, `accession_id`, or `pubmed_id`
   ```python
   r = requests.get(f"{BASE}/associations",
                    params={"rs_id": "rs7903146", "sort": "p_value", "direction": "asc", "size": 50},
                    timeout=120)
   associations = r.json()["_embedded"]["associations"]
   ```

3. **Variants** — `/v2/single-nucleotide-polymorphisms/{rs_id}` (location, consequence, mapped genes)
   ```python
   snp = requests.get(f"{BASE}/single-nucleotide-polymorphisms/rs7412", timeout=60).json()
   loc = snp["locations"][0]
   print(loc["chromosome_name"], loc["chromosome_position"], snp["most_severe_consequence"], snp["mapped_genes"])
   ```

4. **Traits** — `/v2/efo-traits?efo_trait=<free text>` to resolve names to `efo_id`
   ```python
   traits = requests.get(f"{BASE}/efo-traits", params={"efo_trait": "type 2 diabetes"}, timeout=60).json()
   for t in traits["_embedded"]["efo_traits"]:
       print(t["efo_id"], t["efo_trait"])   # MONDO_0005148  type 2 diabetes mellitus, ...
   ```

## Query Examples and Patterns

**Example 1: Genome-wide significant associations for a disease**
```python
import requests

BASE = "https://www.ebi.ac.uk/gwas/rest/api/v2"
params = {"efo_id": "MONDO_0005148",          # type 2 diabetes mellitus (legacy EFO_0001360 returns 0 rows)
          "sort": "p_value", "direction": "asc", "size": 100}
data = requests.get(f"{BASE}/associations", params=params, timeout=120).json()

for a in data["_embedded"]["associations"]:
    allele = a["snp_allele"][0] if a.get("snp_allele") else {}
    # p_value underflows to 0.0 below ~1e-308; mantissa/exponent keep the exact value
    p = f'{a["pvalue_mantissa"]}e{a["pvalue_exponent"]}'
    # or_per_copy_num is numeric (or_value is the same as a string); beta is text such as
    # "0.0356 unit decrease" and "-" when absent
    print(allele.get("rs_id"), allele.get("effect_allele"), p, a.get("or_per_copy_num"), a.get("beta"), a["accession_id"])
```

**Example 2: Pleiotropy — every trait reported for one variant**
```python
data = requests.get(f"{BASE}/associations",
                    params={"rs_id": "rs7903146", "sort": "p_value", "direction": "asc", "size": 200},
                    timeout=120).json()
traits = {t["efo_trait"] for a in data["_embedded"]["associations"] for t in a["efo_traits"]}
print(f'{data["page"]["totalElements"]} associations across {len(traits)} traits (first page)')
```

**Example 3: Gene-centric lookup**
```python
# Default: genes the variant maps into or the nearest up/downstream genes (as on the website).
# extended_geneset=true widens to all Ensembl/RefSeq genes near each variant (the v1 behaviour).
data = requests.get(f"{BASE}/associations",
                    params={"mapped_gene": "TCF7L2", "size": 100}, timeout=120).json()
```

**Example 4: Curated variants in a chromosomal region (GRCh38)**
```python
data = requests.get(f"{BASE}/single-nucleotide-polymorphisms",
                    params={"chromosome": "10", "bp_start": 112_900_000, "bp_end": 113_200_000, "size": 100},
                    timeout=120).json()
rs_ids = [s["rs_id"] for s in data["_embedded"]["snps"]]
```
This returns only variants with curated associations. For every tested variant in a region, use the harmonised summary statistics below.

## Working with Summary Statistics

The curated associations are top hits only. Full summary statistics (every tested variant) are distributed as files:

1. **Find studies with full summary statistics** — `/v2/studies?efo_id=MONDO_0005148&full_pvalue_set=true`; each study's `full_summary_stats` field is its FTP directory.
2. **Harmonised file layout** — `https://ftp.ebi.ac.uk/pub/databases/gwas/summary_statistics/GCST90475001-GCST90476000/GCST90475667/harmonised/GCST90475667.h.tsv.gz` plus `.tbi` index and `-meta.yaml`. The full list of harmonised files is in `https://ftp.ebi.ac.uk/pub/databases/gwas/summary_statistics/harmonised_list.txt` (updated nightly).
3. **Format** — GWAS-SSF (v1.0 since 2023): `chromosome`, `base_pair_location`, `effect_allele`, `other_allele`, `beta` or `odds_ratio`, `standard_error`, `effect_allele_frequency`, `p_value`, `rsid`, `variant_id`, plus `hm_code` harmonisation flags. Coordinates are GRCh38; chromosomes are written without a `chr` prefix.

```python
import requests

BASE = "https://www.ebi.ac.uk/gwas/rest/api/v2"
studies = requests.get(f"{BASE}/studies",
                       params={"efo_id": "MONDO_0005148", "full_pvalue_set": "true", "size": 50},
                       timeout=120).json()["_embedded"]["studies"]

def harmonised_url(study: dict) -> str:
    acc = study["accession_id"]
    ftp_dir = study["full_summary_stats"].replace("http://", "https://")
    return f"{ftp_dir}/harmonised/{acc}.h.tsv.gz"

url = harmonised_url(studies[0])
```

Region query without downloading the whole file (tabix reads the remote `.tbi`):
```bash
tabix -h "$URL" 10:112900000-113200000 > tcf7l2_region.tsv
```
```python
import pysam  # uv pip install pysam
with pysam.TabixFile(url) as tbx:
    rows = [line.split("\t") for line in tbx.fetch("10", 112_900_000, 113_200_000)]
```

## Data Integration and Cross-referencing

- **Genomic:** Ensembl (VEP consequences, coordinates), dbSNP (rsID merges), gnomAD (population frequencies)
- **Functional:** GTEx (eQTL/sQTL), Open Targets Platform (L2G, colocalisation, target-disease evidence), PGS Catalog (polygenic scores)
- **Phenotype:** EFO / MONDO ontologies (trait hierarchy; `show_child_trait=true` includes descendant traits)

HAL links let you walk from an association to its locus and variant:
```python
a = data["_embedded"]["associations"][0]
loci = requests.get(a["_links"]["loci"]["href"], timeout=60).json()["_embedded"]["loci"]
risk = loci[0]["strongest_risk_alleles"][0]["risk_allele_name"]      # e.g. "rs7903146-T"
snp = requests.get(a["_links"]["snp"]["href"], timeout=60).json()
```

## Complete Python Integration

Paginated query into a DataFrame, following `_links.next` and respecting the throttle:

```python
import time

import pandas as pd
import requests

BASE = "https://www.ebi.ac.uk/gwas/rest/api/v2"


def query_gwas_catalog(efo_id: str, p_threshold: float = 5e-8, page_size: int = 200) -> pd.DataFrame:
    """Curated associations for a trait short-form (e.g. 'MONDO_0005148'), filtered by p-value."""
    url = f"{BASE}/associations"
    params = {"efo_id": efo_id, "sort": "p_value", "direction": "asc", "size": page_size}
    rows = []
    while url:
        data = requests.get(url, params=params, timeout=120).json()
        params = None  # the next link already carries the query string
        for a in data.get("_embedded", {}).get("associations", []):
            p = float(f'{a["pvalue_mantissa"]}e{a["pvalue_exponent"]}')
            if p > p_threshold:
                return pd.DataFrame(rows)  # sorted ascending, so the rest are weaker
            allele = a["snp_allele"][0] if a.get("snp_allele") else {}
            rows.append({
                "rs_id": allele.get("rs_id"),
                "effect_allele": allele.get("effect_allele"),
                "p_value": p,
                "odds_ratio": a.get("or_per_copy_num"),
                "beta": a.get("beta"),  # text incl. unit/direction; "-" when absent
                "ci_lower": a.get("ci_lower"),
                "ci_upper": a.get("ci_upper"),
                "risk_frequency": a.get("risk_frequency"),
                "trait": "; ".join(t["efo_trait"] for t in a["efo_traits"]),
                "mapped_genes": ",".join(a.get("mapped_genes") or []),
                "accession_id": a["accession_id"],
                "pubmed_id": a.get("pubmed_id"),
            })
        url = data.get("_links", {}).get("next", {}).get("href")
        time.sleep(0.1)  # stay well under 15 requests/second
    return pd.DataFrame(rows)


df = query_gwas_catalog("MONDO_0005148")
print(len(df), df["rs_id"].nunique())
```
