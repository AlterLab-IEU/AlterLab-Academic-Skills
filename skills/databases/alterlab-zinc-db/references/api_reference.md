# ZINC Database API Reference

## Overview

Complete technical reference for programmatic access to the ZINC database, covering API endpoints, query syntax, parameters, response formats, and advanced usage patterns for ZINC22, ZINC20, and legacy versions.

> **Request model (read first).** CartBlanche22 searches are submitted as **form
> fields** — either `curl -F field=value` (multipart) or a form-encoded POST (what
> `scripts/query_zinc.py` sends). The legacy "colon URL" form
> (`/substances.txt:zinc_id=...`) is not supported by the current service. Every
> search is **asynchronous**: the endpoint returns a JSON task handle
> (`{"task": "<uuid>"}`); poll `GET /search/result/<task>` until `status` leaves
> `PENDING` — the finished payload is `{"status": "SUCCESS", "result": {...}}` with rows
> grouped by source (`zinc22`, `zinc20`) and unmatched inputs under `missing` /
> `zinc22_missing` (`scripts/query_zinc.py ... --wait`). For large-scale retrieval use
> the bulk file repository (below).
>
> **Known issue (verified 2026-09-23):** `smiles.txt` returns `"zinc22_missing": [""]`
> for every submission (inline, multipart, or `@file`) — the query never reaches the
> search. Use the CartBlanche22 UI or SmallWorld (`https://sw.docking.org`) for
> similarity searches until it is fixed.

## Base URLs

### ZINC22 (Current)
- **CartBlanche22 API**: `https://cartblanche22.docking.org/`
- **File Repository**: `https://files.docking.org/zinc22/`
- **Main Website**: `https://zinc.docking.org/` (captcha-gated for scripted clients since 2026)

### ZINC20 (Maintained)
- **Web/API**: `https://zinc20.docking.org/` (captcha-gated for scripted clients; use SmallWorld at `https://sw.docking.org` for ZINC20 similarity searches)
- **File Repository**: `https://files.docking.org/zinc20/`

### Documentation
- **Wiki**: `https://wiki.docking.org/`
- **GitHub**: `https://github.com/docking-org/`

## API Endpoints

### 1. Substance Retrieval by ZINC ID

Retrieve compound information using ZINC identifiers.

**Endpoint**: `/substances.txt`

**Parameters** (form fields):
- `zinc_ids` (required): Comma-separated list of ZINC IDs, or `@file` (one per line).
  Note the field is **plural** — `zinc_id` returns HTTP 400.
- `output_fields` (optional): Comma-separated field names (default: all fields)

**Examples**:

Multiple compounds (inline):
```bash
curl -X GET "https://cartblanche22.docking.org/substances.txt" \
  -F zinc_ids="ZINC000019632618,ZINC000000000001" \
  -F output_fields="zinc_id,smiles,catalogs"
```

Batch retrieval from a file:
```bash
# zinc_ids.txt: one ZINC ID per line
curl -X GET "https://cartblanche22.docking.org/substances.txt" \
  -F zinc_ids=@zinc_ids.txt \
  -F output_fields="zinc_id,smiles,tranche"
```

**Response** (JSON task handle):
```json
{"task": "0bf64e3e-ac00-4123-9270-7bfd3572117c"}
```
Poll `GET https://cartblanche22.docking.org/search/result/<task>` for the rows
(`zinc_id`, `smiles`, `catalogs` with supplier codes/prices, `tranche`, …).

### 2. Structure Search by SMILES

Search for compounds by chemical structure with optional similarity thresholds.

**Endpoint**: `/smiles.txt`

**Parameters** (form fields):
- `smiles` (required): Query SMILES string (inline, or `@file` for a batch of queries)
- `dist` (optional): Tanimoto distance threshold (default: 0 = exact)
- `adist` (optional): Anonymous (graph-topology) distance for broader searches (default: 0)
- `output_fields` (optional): Comma-separated field names

**Examples**:

Exact structure match (dist/adist default to 0):
```bash
curl -X GET "https://cartblanche22.docking.org/smiles.txt" \
  -F smiles="c1ccccc1" -F output_fields="zinc_id,smiles"
```

Similarity search (Tanimoto distance = 3):
```bash
curl -X GET "https://cartblanche22.docking.org/smiles.txt" \
  -F smiles="CC(C)Cc1ccc(cc1)C(C)C(=O)O" -F dist=3 \
  -F output_fields="zinc_id,smiles,catalogs"
```

Broad similarity search (both metrics):
```bash
curl -X GET "https://cartblanche22.docking.org/smiles.txt" \
  -F smiles="c1ccccc1" -F dist=5 -F adist=5 \
  -F output_fields="zinc_id,smiles,tranche"
```

Because SMILES is sent as a form-field value rather than embedded in the URL, no
URL-encoding of special characters (`(`, `=`, `#`) is needed.

**Distance Parameters Interpretation**:
- `dist=0`: Exact match
- `dist=1-3`: Close analogs (high similarity)
- `dist=4-6`: Moderate analogs
- `dist=7-10`: Diverse chemical space

### 3. Supplier Code Search

Query compounds by vendor catalog numbers.

**Endpoint**: `/catitems.txt`

**Parameters** (form fields):
- `supplier_codes` (required): Supplier catalog code(s) — inline, or `@file`
- `output_fields` (optional): Comma-separated field names

**Example**:
```bash
curl -X GET "https://cartblanche22.docking.org/catitems.txt" \
  -F supplier_codes="SUPPLIER-12345" \
  -F output_fields="zinc_id,smiles,supplier_code,catalogs"
```

### 4. Random Compound Sampling

Generate random compound sets with optional filtering by chemical properties.

**Endpoint**: `/substance/random.txt`

**Parameters** (form fields):
- `count` (optional): Number of compounds to retrieve (default: 100, max: depends on server)
- `subset` (optional): Filter by predefined subset (e.g., 'lead-like', 'drug-like', 'fragment')
- `output_fields` (optional): Comma-separated field names

**Examples**:

Random 100 compounds (default):
```bash
curl "https://cartblanche22.docking.org/substance/random.txt" -F count=100
```

Random lead-like molecules:
```bash
curl "https://cartblanche22.docking.org/substance/random.txt" \
  -F count=1000 -F subset="lead-like" -F output_fields="zinc_id,smiles,tranche"
```

Random fragments:
```bash
curl "https://cartblanche22.docking.org/substance/random.txt" \
  -F count=500 -F subset="fragment" -F output_fields="zinc_id,smiles,tranche"
```

**Subset Definitions**:
- `fragment`: MW < 250, suitable for fragment-based drug discovery
- `lead-like`: MW 250-350, LogP ≤ 3.5, rotatable bonds ≤ 7
- `drug-like`: MW 350-500, follows Lipinski's Rule of Five
- `lugs`: Large, unusually good subset (highly curated)

## Output Fields

### Available Fields

Customize API responses using the `output_fields` parameter:

| Field | Description | Example |
|-------|-------------|---------|
| `zinc_id` | ZINC identifier | ZINC000000000001 |
| `smiles` | Canonical SMILES string | CC(C)O |
| `sub_id` | Internal substance ID | 123456 |
| `supplier_code` | Vendor catalog number | AB-1234567 |
| `catalogs` | List of suppliers | [emolecules, mcule, mcule-ultimate] |
| `tranche` | Tranche (heavy-atom count × logP bin) | H17P050 |
| `mwt` | Molecular weight | 325.45 |
| `logp` | LogP (partition coefficient) | 2.5 |
| `hba` | H-bond acceptors | 4 |
| `hbd` | H-bond donors | 2 |
| `rotatable_bonds` | Rotatable bonds count | 5 |

**Note**: Not all fields are available for all endpoints. Field availability depends on the database version and endpoint.

### Default Fields

If `output_fields` is not specified, endpoints return all available fields in TSV format.

### Custom Field Selection

Request specific fields only:
```bash
curl -X GET "https://cartblanche22.docking.org/substances.txt" \
  -F zinc_ids="ZINC000019632618" -F output_fields="zinc_id,smiles"
```

Request multiple fields:
```bash
curl -X GET "https://cartblanche22.docking.org/substances.txt" \
  -F zinc_ids="ZINC000019632618" -F output_fields="zinc_id,smiles,tranche,catalogs"
```

## Tranche System

ZINC-22 bins every molecule by **heavy-atom count** and **calculated logP** (both computed
with RDKit). Source: Tingle et al., "ZINC-22─A Free Multi-Billion-Scale Database of
Tangible Compounds for Ligand Discovery", *J. Chem. Inf. Model.* 2023, 63, 1166–1176
(doi:10.1021/acs.jcim.2c01253): the tranche browser's two axes are "heavy atom count
(horizontal) and lipophilicity (vertical)".

### Tranche code format

| Part | Meaning | Example |
|------|---------|---------|
| `H##` | heavy-atom count | `H17` = 17 heavy atoms |
| `P###` / `M###` | logP bin; `P` = positive, `M` = negative, value × 100 | `P050` = 0.50, `M100` = −1.00 |

| Tranche | Reading |
|---------|---------|
| `H17P050` | 17 heavy atoms, logP bin 0.50 |
| `H12M100` | 12 heavy atoms, logP bin −1.00 |
| `H08M500` … `H16P240` | the corners of the ZINC-22 2D fragment subset |

`H` is not H-bond donors and `M` is not molecular weight. ZINC15/20 tranches were
letter-coded on other axes (MW, logP, reactivity, purchasability, pH, charge) — do not
decode those with this table. Compute MW, HBD/HBA, TPSA and similar properties from the
SMILES with RDKit (`alterlab-rdkit`).

### ZINC-22 identifiers

ZINC-22 IDs are 16 characters: `ZINC`, two tranche characters, two database-source
characters (`00` for the commercial libraries), then an 8-character radix-62 serial
(Tingle et al. 2023). Legacy ZINC15/20 IDs (`ZINC000019632618`) carry no tranche.

### Parsing tranches in Python

```python
import re

def parse_tranche(code):
    """'H17P050' -> {'heavy_atoms': 17, 'logp_bin': 0.5}; 'H12M100' -> logp_bin -1.0."""
    m = re.search(r"H(\d{2})([PM])(\d{3})", code or "")
    if not m:
        return None
    sign = 1 if m.group(2) == "P" else -1
    return {"heavy_atoms": int(m.group(1)), "logp_bin": sign * int(m.group(3)) / 100.0}

print(parse_tranche("H17P050"))  # {'heavy_atoms': 17, 'logp_bin': 0.5}
```

## File Repository Access

ZINC-22 3D builds are served from https://files.docking.org/zinc22/ (also via Globus, and
as open-data buckets on AWS S3 and Oracle OCI, where a docking program can read the files
without downloading them). The tree is organised by build and tranche and has changed
between releases, so **do not hand-build file paths** — let CartBlanche22 generate them.

### Getting the exact URLs

1. https://cartblanche22.docking.org → **Tranches → 3D** opens the 3D tranche browser.
2. Select tranches (click cells, rows or columns) or a preset such as lead-like or
   fragment-like; each cell shows how many molecules it holds.
3. Choose a format and a method — curl, wget or PowerShell scripts, or an S3/OCI file
   list — and download the generated script. It contains the exact URLs.

### File formats

Four ready-to-dock 3D formats exist (Tingle et al. 2023):

| Format | Program | Notes |
|--------|---------|-------|
| DB2 | UCSF DOCK 3.7 / 3.8 | Multi-conformer, protonated and charged. DOCK 6 does not read DB2 and Open Babel has no DB2 reader, so it cannot be converted |
| MOL2 | DOCK 6, GOLD, Glide (after import) | 3D coordinates |
| SDF | RDKit-based tools, Glide, most toolkits | 3D coordinates |
| PDBQT | AutoDock Vina, AutoDock-GPU | Ready for Vina |

### Bulk download

```bash
# urls.txt = the URL list from the tranche-browser script
aria2c -i urls.txt -x 8 -j 4            # parallel, resumable
xargs -n1 -P8 wget -q -c < urls.txt     # without aria2c
```

A whole 3D format of ZINC-22 is many terabytes; select tranches first and check the
browser's molecule counts before starting.

### Individual compounds

For a short list of ZINC IDs, look them up (`scripts/query_zinc.py id ... --wait`), add the
hits to the CartBlanche22 cart and download the 3D files from there instead of whole
tranches. A compound may have no 3D build yet (over 95% of molecules up to 24 heavy atoms
had been built at publication); build missing ones yourself from the SMILES.

## Advanced Query Patterns

### Combining Multiple Search Criteria

**Python wrapper for complex queries** (form-encoded POST, stdlib only):

```python
import json
import urllib.parse
import urllib.request

BASE = "https://cartblanche22.docking.org"

def _post(path, fields):
    data = urllib.parse.urlencode(fields).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}/{path}", data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))

def advanced_zinc_search(smiles=None, zinc_ids=None, dist=0,
                         subset=None, count=None, output_fields=None):
    """
    Submit a ZINC22 search. Returns the JSON task handle ({"task": "<uuid>"});
    fetch the rows with GET /search/result/<task> once status != "PENDING".

    Exactly one of smiles / zinc_ids / count must be given.
    """
    fields_str = ",".join(output_fields or ["zinc_id", "smiles", "tranche", "catalogs"])

    if smiles:
        return _post("smiles.txt",
                     {"smiles": smiles, "dist": dist, "output_fields": fields_str})
    if zinc_ids:
        return _post("substances.txt",
                     {"zinc_ids": ",".join(zinc_ids), "output_fields": fields_str})
    if count:
        body = {"count": count, "output_fields": fields_str}
        if subset:
            body["subset"] = subset
        return _post("substance/random.txt", body)
    raise ValueError("Must specify smiles, zinc_ids, or count")
```

**Usage examples**:

```python
# Find similar compounds (submits the search, returns a task handle)
task = advanced_zinc_search(
    smiles="CC(C)Cc1ccc(cc1)C(C)C(=O)O",
    dist=3,
    output_fields=["zinc_id", "smiles", "catalogs"],
)

# Batch retrieval
task = advanced_zinc_search(zinc_ids=["ZINC000019632618", "ZINC000000000001"])

# Random drug-like set
task = advanced_zinc_search(
    count=1000, subset="drug-like",
    output_fields=["zinc_id", "smiles", "tranche"],
)
```

### Property-Based Filtering

The tranche gives only heavy-atom count and a logP bin. Filter on those, then compute any
other property from the SMILES:

```python
import pandas as pd

def filter_by_tranche(df, heavy_atoms=None, logp_range=None):
    """Keep rows whose tranche falls inside the given bins.

    df: DataFrame with a 'tranche' column (exported result rows)
    heavy_atoms: (min, max) heavy-atom count, inclusive
    logp_range: (min, max) logP bin, inclusive
    """
    props = df["tranche"].apply(parse_tranche)
    hac = props.apply(lambda p: p["heavy_atoms"] if p else None)
    logp = props.apply(lambda p: p["logp_bin"] if p else None)
    mask = hac.notna()
    if heavy_atoms:
        mask &= hac.between(*heavy_atoms)
    if logp_range:
        mask &= logp.between(*logp_range)
    return df[mask]

# Lead-like-ish window: 17-25 heavy atoms, logP bin -1.0 to 3.5
subset = filter_by_tranche(df, heavy_atoms=(17, 25), logp_range=(-1.0, 3.5))
# MW / HBD / HBA: compute with RDKit (see the RDKit Integration section below)
```

## Rate Limiting and Best Practices

### Rate Limiting

ZINC does not publish explicit rate limits, but users should:

- **Avoid rapid-fire requests**: Space out queries by at least 1 second
- **Use batch operations**: Query multiple ZINC IDs in single request
- **Cache results**: Store frequently accessed data locally
- **Off-peak usage**: Perform large downloads during off-peak hours (UTC nights/weekends)

### Etiquette

```python
import time

def polite_zinc_query(query_func, *args, delay=1.0, **kwargs):
    """Wrapper to add delay between queries."""
    result = query_func(*args, **kwargs)
    time.sleep(delay)
    return result
```

### Error Handling

```python
def robust_zinc_query(url, max_retries=3, timeout=30):
    """
    Query ZINC with retry logic.

    Args:
        url: Full ZINC API URL
        max_retries: Maximum retry attempts
        timeout: Request timeout in seconds

    Returns:
        Query results or None on failure
    """
    import subprocess
    import time

    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                ['curl', '-s', '--max-time', str(timeout), url],
                capture_output=True,
                text=True,
                check=True
            )

            # Check for empty or error responses
            if not result.stdout or 'error' in result.stdout.lower():
                raise ValueError("Invalid response")

            return result.stdout

        except (subprocess.CalledProcessError, ValueError) as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"Failed after {max_retries} attempts")
                return None
```

## Integration with Molecular Docking

### DOCK 3.8 (DB2)

DOCK 3.7/3.8 reads ZINC-22 DB2 files directly: download the DB2 files for the selected
tranches (tranche-browser script, format DB2) and list them in the docking run's ligand
input. DOCK 6 does not read DB2 — use MOL2 for DOCK 6.

### AutoDock Vina

Download the PDBQT build for the selected tranches (tranche-browser script, format PDBQT)
and dock it directly. If you start from SDF instead, prepare PDBQT with Meeko:

```bash
mk_prepare_ligand.py -i ligands.sdf --multimol_outdir pdbqt/
vina --receptor protein.pdbqt --ligand pdbqt/ZINC....pdbqt \
     --center_x 25.0 --center_y 25.0 --center_z 25.0 \
     --size_x 20.0 --size_y 20.0 --size_z 20.0
```

### RDKit Integration

```python
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors
import pandas as pd

def process_zinc_results(zinc_df):
    """
    Process ZINC results with RDKit.

    Args:
        zinc_df: DataFrame with SMILES column

    Returns:
        DataFrame with calculated properties
    """
    # Convert SMILES to molecules
    zinc_df['mol'] = zinc_df['smiles'].apply(Chem.MolFromSmiles)

    # Calculate properties
    zinc_df['mw'] = zinc_df['mol'].apply(Descriptors.MolWt)
    zinc_df['logp'] = zinc_df['mol'].apply(Descriptors.MolLogP)
    zinc_df['hbd'] = zinc_df['mol'].apply(Descriptors.NumHDonors)
    zinc_df['hba'] = zinc_df['mol'].apply(Descriptors.NumHAcceptors)
    zinc_df['tpsa'] = zinc_df['mol'].apply(Descriptors.TPSA)
    zinc_df['rotatable'] = zinc_df['mol'].apply(Descriptors.NumRotatableBonds)

    # Generate 3D conformers
    for mol in zinc_df['mol']:
        if mol:
            AllChem.EmbedMolecule(mol, randomSeed=42)
            AllChem.MMFFOptimizeMolecule(mol)

    return zinc_df

# Save to SDF for docking
def save_to_sdf(zinc_df, output_file):
    """Save molecules to SDF file."""
    writer = Chem.SDWriter(output_file)
    for idx, row in zinc_df.iterrows():
        if row['mol']:
            row['mol'].SetProp('ZINC_ID', row['zinc_id'])
            writer.write(row['mol'])
    writer.close()
```

## Troubleshooting

### Common Issues

**Issue**: Empty or no results
- **Solution**: Check SMILES syntax, verify ZINC IDs exist, try broader similarity search

**Issue**: Timeout errors
- **Solution**: Reduce result count, use batch queries, try during off-peak hours

**Issue**: Invalid SMILES encoding
- **Solution**: URL-encode special characters (use `urllib.parse.quote()` in Python)

**Issue**: Tranche files not found
- **Solution**: Verify tranche code format, check file repository structure

### Debug Mode

```python
def debug_zinc_query(url):
    """Print query details for debugging."""
    print(f"Query URL: {url}")

    result = subprocess.run(['curl', '-v', url],
                          capture_output=True, text=True)

    print(f"Status: {result.returncode}")
    print(f"Stderr: {result.stderr}")
    print(f"Stdout length: {len(result.stdout)}")
    print(f"First 500 chars:\n{result.stdout[:500]}")

    return result.stdout
```

## Version Differences

### ZINC22 vs ZINC20 vs ZINC15

| Feature | ZINC22 | ZINC20 | ZINC15 |
|---------|--------|--------|--------|
| Compounds | 230M+ purchasable | Focused on leads | ~750M total |
| API | CartBlanche22 | Similar | REST-like |
| Tranches | Yes | Yes | Yes |
| 3D Structures | Yes | Yes | Yes |
| Status | Current, growing | Maintained | Legacy |

### API Compatibility

Most query patterns work across versions, but URLs differ:
- ZINC22: `cartblanche22.docking.org`
- ZINC20: `zinc20.docking.org`
- ZINC15: `zinc15.docking.org`

## Additional Resources

- **ZINC Wiki**: https://wiki.docking.org/
- **ZINC22 Documentation**: https://wiki.docking.org/index.php/Category:ZINC22
- **ZINC API Guide**: https://wiki.docking.org/index.php/ZINC_api
- **File Access Guide**: https://wiki.docking.org/index.php/ZINC22:Getting_started
- **Publications**:
  - ZINC22: Tingle et al., *J. Chem. Inf. Model.* 2023, 63(4), 1166–1176. DOI: 10.1021/acs.jcim.2c01253
  - ZINC20: Irwin et al., *J. Chem. Inf. Model.* 2020, 60(12), 6065–6073. DOI: 10.1021/acs.jcim.0c00675
  - ZINC15: Sterling & Irwin, *J. Chem. Inf. Model.* 2015, 55, 2324–2337. DOI: 10.1021/acs.jcim.5b00559
- **Support**: Contact via ZINC website or GitHub issues
