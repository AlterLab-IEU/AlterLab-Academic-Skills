# GTEx API v2 Reference

## Base URL

```
https://gtexportal.org/api/v2/
```

All endpoints accept GET requests. Responses are JSON. No authentication required.

## Common Query Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `gencodeId` | GENCODE gene ID with version | `ENSG00000130203.10` |
| `geneSymbol` | Gene symbol | `APOE` |
| `variantId` | GTEx variant ID | `chr17_45413693_C_T_b38` |
| `tissueSiteDetailId` | Tissue identifier | `Whole_Blood` |
| `datasetId` | Dataset version | `gtex_v10` |
| `itemsPerPage` | Results per page | `250` |
| `page` | Page number (0-indexed) | `0` |

## Endpoint Reference

### Expression Endpoints

#### `GET /expression/medianGeneExpression`

Median TPM expression for a gene across tissues.

**Parameters:** `gencodeId`, `datasetId`, `itemsPerPage`

**Response fields** (no display-name column — only `tissueSiteDetailId`):
```json
{
  "data": [
    {
      "gencodeId": "ENSG00000130203.10",
      "geneSymbol": "APOE",
      "tissueSiteDetailId": "Liver",
      "median": 3687.51,
      "unit": "TPM",
      "datasetId": "gtex_v10"
    }
  ]
}
```

#### `GET /expression/geneExpression`

Full expression distribution (box plot data) per tissue.

**Parameters:** `gencodeId`, `tissueSiteDetailId`, `datasetId`

**Response fields:**
- `data[].tissueExpressionData.data`: array of TPM values per sample

### Association (QTL) Endpoints

#### `GET /association/singleTissueEqtl`

Significant single-tissue cis-eQTLs.

**Parameters:** `gencodeId` OR `variantId`, `tissueSiteDetailId` (optional), `datasetId`

**Response fields** (verified against gtex_v10):
```json
{
  "data": [
    {
      "gencodeId": "ENSG00000169174.11",
      "geneSymbol": "PCSK9",
      "variantId": "chr1_55057688_A_G_b38",
      "snpId": "rs533375",
      "pos": 55057688,
      "chromosome": "chr1",
      "tissueSiteDetailId": "Esophagus_Muscularis",
      "nes": 0.227,
      "pValue": 6.1e-05,
      "datasetId": "gtex_v10"
    }
  ]
}
```

**Key fields:**
- `nes`: normalized effect size of the alt allele (positive = higher expression with alt); this replaces the older `slope` field name
- `pValue`: nominal p-value (camelCase — not `pval`)
- The single-tissue endpoint returns only pairs already significant at FDR < 0.05; it does **not** carry per-row `qval`, `maf`, or `slopeStandardError`. For the gene-level q-value use `/association/egene` (`qValue`).

#### `GET /association/singleTissueSqtl`

Significant single-tissue sQTLs (splicing).

**Parameters:** Same as eQTL endpoint. **Response** mirrors the eQTL fields (`nes`, `pValue`, `variantId`, `snpId`) and adds `phenotypeId` — the splice cluster/intron the variant affects (e.g. `chr1:55040044:55043843:clu_3551_+:ENSG00000169174.11`).

#### `GET /association/egene`

All eGenes (genes with ≥1 significant eQTL) in a tissue.

**Parameters:** `tissueSiteDetailId`, `datasetId`

**Response fields:** `gencodeId`, `geneSymbol`, `pValue`, `qValue`, `pValueThreshold`, `empiricalPValue`, `log2AllelicFoldChange` (per-gene gene-level statistics; this is where the FDR `qValue` lives).

### Dataset/Metadata Endpoints

#### `GET /dataset/tissueSiteDetail`

List of all available tissues.

**Parameters:** `datasetId`, `itemsPerPage`

**Response fields:**
- `tissueSiteDetailId`: API identifier (use this in queries)
- `tissueSiteDetail`: Display name
- `colorHex`: Color for visualization
- `samplingSite`: Anatomical location

#### `GET /reference/gene`

Gene metadata from GENCODE. Use this to resolve a symbol to the correct versioned `gencodeId` **for a given dataset** (the suffix differs per GENCODE release).

**Parameters:** `geneId` (symbol or Ensembl ID), `gencodeVersion` (`v39` for gtex_v10, `v26` for gtex_v8), `genomeBuild` (`GRCh38/hg38`)

```
GET /reference/gene?geneId=PCSK9&gencodeVersion=v39&genomeBuild=GRCh38/hg38
  -> gencodeId "ENSG00000169174.11" (v10);  v26 yields ".10" (v8)
```

**Key response fields:** `gencodeId`, `gencodeVersion`, `geneSymbol`, `chromosome`, `start`, `end`, `strand`, `tss`, `entrezGeneId`, `geneType`

### Variant Endpoints

#### `GET /variant/variantPage`

Variant metadata and lookup.

**Parameters:** `snpId` (rsID) OR `variantId`

## Tissue IDs Reference (Common Tissues)

| ID | Display Name |
|----|-------------|
| `Whole_Blood` | Whole Blood |
| `Brain_Cortex` | Brain - Cortex |
| `Brain_Hippocampus` | Brain - Hippocampus |
| `Brain_Frontal_Cortex_BA9` | Brain - Frontal Cortex (BA9) |
| `Liver` | Liver |
| `Kidney_Cortex` | Kidney - Cortex |
| `Heart_Left_Ventricle` | Heart - Left Ventricle |
| `Lung` | Lung |
| `Muscle_Skeletal` | Muscle - Skeletal |
| `Adipose_Subcutaneous` | Adipose - Subcutaneous |
| `Colon_Transverse` | Colon - Transverse |
| `Small_Intestine_Terminal_Ileum` | Small Intestine - Terminal Ileum |
| `Skin_Sun_Exposed_Lower_leg` | Skin - Sun Exposed (Lower leg) |
| `Thyroid` | Thyroid |
| `Nerve_Tibial` | Nerve - Tibial |
| `Artery_Coronary` | Artery - Coronary |
| `Artery_Aorta` | Artery - Aorta |
| `Pancreas` | Pancreas |
| `Pituitary` | Pituitary |
| `Spleen` | Spleen |
| `Prostate` | Prostate |
| `Ovary` | Ovary |
| `Uterus` | Uterus |
| `Testis` | Testis |

## Error Handling

```python
import requests
from requests.exceptions import HTTPError, Timeout

def safe_gtex_query(endpoint, params):
    url = f"https://gtexportal.org/api/v2/{endpoint}"
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except HTTPError as e:
        print(f"HTTP error {e.response.status_code}: {e.response.text}")
    except Timeout:
        print("Request timed out")
    except Exception as e:
        print(f"Error: {e}")
    return None
```

## Rate Limiting

GTEx API does not publish explicit rate limits but:
- Add 0.5–1s delays between bulk queries
- Use data downloads for genome-wide analyses instead of API
- Cache results locally for repeated queries
