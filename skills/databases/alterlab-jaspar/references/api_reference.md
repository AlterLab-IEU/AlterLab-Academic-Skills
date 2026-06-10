# JASPAR API v1 Reference

## Base URL

```
https://jaspar.elixir.no/api/v1/
```

No authentication required. Responses are JSON.

## Core Endpoints

### `GET /matrix/`

Search and list TF binding profiles.

**Parameters:**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `name` | string | TF name (partial match) | `CTCF` |
| `matrix_id` | string | Exact matrix ID | `MA0139.1` |
| `collection` | string | Collection name | `CORE` |
| `tax_group` | string | Taxonomic group | `vertebrates` |
| `tax_id` | string/int | NCBI taxonomy ID (preferred) | `9606` (human) |
| `species` | string | Species name or tax ID (broader match) | `9606`, `Homo sapiens` |
| `tf_class` | string | TF structural class | `C2H2 zinc finger factors` |
| `tf_family` | string | TF family | `More than 3 adjacent zinc fingers` |
| `type` | string | Experimental method | `ChIP-seq`, `SELEX` |
| `version` | string | `latest` or specific version | `latest` |
| `page` | int | Page number | `1` |
| `page_size` | int | Results per page (max 500) | `25` |

**Response** (`count` reflects the full result set for the filters; paginate via `next`):
```json
{
  "count": 6,
  "next": "https://jaspar.elixir.no/api/v1/matrix/?name=CTCF&page=2",
  "previous": null,
  "results": [
    {
      "matrix_id": "MA0139.1",
      "name": "CTCF",
      "collection": "CORE",
      "base_id": "MA0139",
      "version": "1",
      "sequence_logo": "https://jaspar.elixir.no/static/logos/svg/MA0139.1.svg",
      "url": "https://jaspar.elixir.no/api/v1/matrix/MA0139.1/"
    }
  ]
}
```

### `GET /matrix/{id}/`

Fetch a specific matrix with full details.

**Response** (actual fields returned by the live API):
```json
{
  "matrix_id": "MA0139.1",
  "name": "CTCF",
  "base_id": "MA0139",
  "version": 1,
  "collection": "CORE",
  "tax_group": "vertebrates",
  "pfm": {
    "A": [87, 167, 281, "..."],
    "C": [291, 145, 49, "..."],
    "G": [76, 414, 449, "..."],
    "T": [205, 114, 27, "..."]
  },
  "species": [{"tax_id": 9606, "name": "Homo sapiens"}],
  "class": ["C2H2 zinc finger factors"],
  "family": ["More than 3 adjacent zinc fingers"],
  "type": "ChIP-seq",
  "uniprot_ids": ["P49711"],
  "pubmed_ids": ["17512414"],
  "sequence_logo": "https://jaspar.elixir.no/static/logos/svg/MA0139.1.svg"
}
```

> The API does **not** return `consensus` or `length` fields. Motif length = number of PFM columns, i.e. `len(pfm["A"])` (19 for MA0139.1). Derive the consensus yourself by taking the most frequent base per column.

Sequence logos are exposed via the `sequence_logo` URL on each matrix object (e.g. `https://jaspar.elixir.no/static/logos/svg/MA0139.1.svg`), not a dedicated API endpoint.

### `GET /collections/`

List available collections. The current API serves two: `CORE` and `UNVALIDATED` (the legacy PHYLOFACTS/CNE/POLII/FAM/SPLICE collections are no longer populated).

### `GET /taxon/` and `GET /species/`

List available taxa / species.

### `GET /releases/`

List JASPAR releases.

> There are **no** `/tf_class/` or `/tf_family/` listing endpoints (they 404). Filter by class/family directly on `/matrix/` using the `tf_class` / `tf_family` query parameters.

## Matrix ID Format

```
MA{number}.{version}    e.g. MA0139.1
```

- The `base_id` (e.g. `MA0139`) identifies the profile; the suffix is the version.
- `MA`-prefixed IDs are CORE-collection profiles. The version increments when a profile is updated; query `version=latest` to always get the current one.
- The `versions_url` field on a matrix lists all versions of that base_id.

## Common Matrix IDs

Verified against the live API (names/species/methods can change between releases — always re-fetch the matrix for ground truth):

| Matrix ID | TF | Species | Method |
|-----------|-----|---------|--------|
| `MA0139.1` | CTCF | Human | ChIP-seq |
| `MA0098.3` | ETS1 | Human | HT-SELEX |
| `MA0107.1` | RELA (NF-kB p65) | Human | SELEX |
| `MA0048.2` | NHLH1 | Human | HT-SELEX |
| `MA0079.4` | SP1 | Human | HT-SELEX |
| `MA0080.4` | SPI1 (PU.1) | Human | HT-SELEX |
| `MA0025.2` | NFIL3 | Human | ChIP-seq |
| `MA0002.2` | Runx1 | Mouse | ChIP-seq |
| `MA0004.1` | Arnt | Mouse | SELEX |
| `MA0009.2` | TBXT | Human | HT-SELEX |

## TF Classes (partial list)

- `C2H2 zinc finger factors`
- `Basic leucine zipper factors (bZIP)`
- `Basic helix-loop-helix factors (bHLH)`
- `Homeodomain factors`
- `Forkhead box (FOX) factors`
- `ETS-domain factors`
- `Nuclear hormone receptors`
- `Tryptophan cluster factors`
- `p53-like transcription factors`
- `STAT factors`
- `MADS box factors`
- `T-box factors`

## Python Example: Batch Download

```python
import requests, json, time

def download_all_human_profiles(output_file="jaspar_human_profiles.json"):
    """Download all human TF profiles from JASPAR CORE collection."""
    url = "https://jaspar.elixir.no/api/v1/matrix/"
    params = {
        "collection": "CORE",
        "tax_id": "9606",      # NCBI taxonomy ID for human
        "version": "latest",   # one row per profile (skip historical versions)
        "page_size": 500,
        "page": 1
    }

    profiles = []
    while True:
        response = requests.get(url, params=params)
        data = response.json()
        profiles.extend(data["results"])

        if not data["next"]:
            break
        params["page"] += 1
        time.sleep(0.5)

    # Fetch full details for each profile
    full_profiles = []
    for p in profiles:
        detail_url = f"https://jaspar.elixir.no/api/v1/matrix/{p['matrix_id']}/"
        detail = requests.get(detail_url).json()
        full_profiles.append(detail)
        time.sleep(0.1)  # Be respectful

    with open(output_file, "w") as f:
        json.dump(full_profiles, f)

    return full_profiles
```
