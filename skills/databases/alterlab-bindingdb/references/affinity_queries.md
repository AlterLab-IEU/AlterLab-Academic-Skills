# BindingDB Affinity Query Reference

## Affinity Measurement Types

### Ki (Inhibition Constant)
- **Definition**: Equilibrium constant for inhibitor-enzyme complex dissociation
- **Equation**: Ki = [E][I]/[EI]
- **Usage**: Enzyme inhibition; preferred for mechanistic studies
- **Note**: Independent of substrate concentration (unlike IC50)

### Kd (Dissociation Constant)
- **Definition**: Thermodynamic binding equilibrium constant
- **Equation**: Kd = [A][B]/[AB]
- **Usage**: Direct binding assays (SPR, ITC, fluorescence anisotropy)
- **Note**: True measure of binding strength; lower = tighter binding

### IC50 (Half-Maximal Inhibitory Concentration)
- **Definition**: Concentration of inhibitor that reduces target activity by 50%
- **Usage**: Most common in drug discovery; assay-dependent
- **Conversion to Ki**: Cheng-Prusoff equation: Ki = IC50 / (1 + [S]/Km)
- **Note**: Depends on substrate concentration and assay conditions

### EC50 (Half-Maximal Effective Concentration)
- **Definition**: Concentration that produces 50% of maximal effect
- **Usage**: Cell-based assays, agonist studies

### Kinetics Parameters
- **kon**: Association rate constant (M⁻¹s⁻¹); describes how fast complex forms
- **koff**: Dissociation rate constant (s⁻¹); describes how fast complex dissociates
- **Residence time**: τ = 1/koff; longer residence = more sustained effect
- **Kd from kinetics**: Kd = koff/kon

## Common API Query Patterns

### By UniProt ID (REST API)

```python
import requests

def query_by_uniprot(uniprot_id, cutoff=10000):
    """
    REST API query for BindingDB affinities by UniProt target ID.
    The 'uniprot' param is formatted as '<accession>;<cutoff in nM>'.
    """
    url = "https://bindingdb.org/rest/getLigandsByUniprot"
    params = {
        "uniprot": f"{uniprot_id};{cutoff}",  # e.g. 'P00519;10000'
        "response": "application/json"
    }
    response = requests.get(url, params=params)
    return response.json()

def query_by_uniprots(uniprot_ids, cutoff=10000):
    """
    Query multiple targets at once. 'uniprot' is a comma-separated list of
    accessions; 'cutoff' is the nM threshold passed separately.
    """
    url = "https://bindingdb.org/rest/getLigandsByUniprots"
    params = {
        "uniprot": ",".join(uniprot_ids),
        "cutoff": cutoff,
        "response": "application/json"
    }
    response = requests.get(url, params=params)
    return response.json()

# Important targets
COMMON_TARGETS = {
    "ABL1": "P00519",    # Imatinib, dasatinib target
    "EGFR": "P00533",    # Erlotinib, gefitinib target
    "BRAF": "P15056",    # Vemurafenib, dabrafenib target
    "CDK2": "P24941",    # Cell cycle kinase
    "HDAC1": "Q13547",   # Histone deacetylase
    "BRD4": "O60885",    # BET bromodomain reader
    "MDM2": "Q00987",    # p53 negative regulator
    "BCL2": "P10415",    # Antiapoptotic protein
    "PCSK9": "Q8NBP7",   # Cholesterol regulator
    "JAK2": "O60674",    # Cytokine signaling kinase
}
```

### By Compound (REST API)

BindingDB has no by-CID endpoint. To query by compound, use `getTargetByCompound`
with a SMILES string (a structural-similarity search). If your input is a PubChem
CID, first convert it to SMILES via PubChem PUG-REST.

```python
def query_by_compound(smiles, cutoff=0.85):
    """Find targets for a compound by SMILES (structural-similarity search)."""
    url = "https://bindingdb.org/rest/getTargetByCompound"
    params = {
        "smiles": smiles,
        "cutoff": cutoff,        # Tanimoto similarity threshold (0.0-1.0)
        "response": "application/json"
    }
    response = requests.get(url, params=params)
    return response.json()

def cid_to_smiles(cid):
    """Convert a PubChem CID to a canonical SMILES via PUG-REST."""
    url = (f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}"
           "/property/CanonicalSMILES/TXT")
    return requests.get(url).text.strip()

# Example: Imatinib PubChem CID = 5291
imatinib_data = query_by_compound(cid_to_smiles(5291))
```

### By PDB ID (REST API)

There is no by-target-name endpoint. Query by UniProt ID (see above) or by PDB ID.

```python
def query_by_pdb(pdb_ids, cutoff=100, identity=92):
    """Query BindingDB by PDB ID(s) (comma-separated)."""
    url = "https://bindingdb.org/rest/getLigandsByPDBs"
    params = {
        "pdb": ",".join(pdb_ids),   # e.g. '1Q0L,3ANM'
        "cutoff": cutoff,           # nM threshold
        "identity": identity,       # sequence-identity threshold (%)
        "response": "application/json"
    }
    response = requests.get(url, params=params)
    return response.json()
```

## Dataset Download Guide

### Available Files

Files on the [downloads page](https://www.bindingdb.org/rwd/bind/chemsearch/marvin/Download.jsp)
are dated (`<YYYYMM>`) and refreshed roughly monthly. Sizes below are for the
2026-06 release; they grow slowly over time.

| File | Size (zipped) | Contents |
|------|------|---------|
| `BindingDB_All_<YYYYMM>_tsv.zip` | ~560 MB | All data (~3.2M records), one TSV |
| `BindingDB_All_2D_<YYYYMM>_sdf.zip` | ~1.5 GB | All data, 2D structures (SDF) |
| `BindingDB_All_3D_<YYYYMM>_sdf.zip` | ~3 GB | All data, 3D structures (SDF) |
| `BindingDB_Assays_<YYYYMM>_tsv.zip` | ~9 MB | Assay-level metadata |

There is **no** split by affinity type. Source-specific subsets are offered
instead (ChEMBL, Patents, PubChem, PDSP Ki, CSAR, ITC, ...), each as 2D/3D SDF
and TSV. The full TSV contains all of Ki/IC50/Kd/EC50 in separate columns, so
filter in pandas rather than looking for `BindingDB_Ki.tsv`-style files.
For ML-ready, pre-split BindingDB subsets, see Therapeutics Data Commons (TDC),
which repackages BindingDB separately (covered by the alterlab-pytdc skill).

### Efficient Loading

```python
import pandas as pd

# For large files, use chunking
def load_bindingdb_chunked(filepath, uniprot_ids, affinity_col="Ki (nM)", chunk_size=100000):
    """Load BindingDB in chunks to filter for specific targets."""
    results = []
    for chunk in pd.read_csv(filepath, sep="\t", chunksize=chunk_size,
                              low_memory=False, on_bad_lines='skip'):
        # Filter for target
        mask = chunk["UniProt (SwissProt) Primary ID of Target Chain"].isin(uniprot_ids)
        if mask.any():
            results.append(chunk[mask])

    if results:
        return pd.concat(results)
    return pd.DataFrame()
```

## pKi / pIC50 Conversion

Converting raw affinity to logarithmic scale (common in ML):

```python
import numpy as np

def to_log_affinity(affinity_nM):
    """Convert nM affinity to pAffinity (negative log molar)."""
    affinity_M = affinity_nM * 1e-9  # Convert nM to M
    return -np.log10(affinity_M)

# Examples:
# 1 nM   → pAffinity = 9.0
# 10 nM  → pAffinity = 8.0
# 100 nM → pAffinity = 7.0
# 1 μM   → pAffinity = 6.0
# 10 μM  → pAffinity = 5.0
```

## Quality Filters

When using BindingDB data for ML or SAR:

```python
def filter_quality(df):
    """Apply quality filters to BindingDB data."""
    # 1. Require valid SMILES
    df = df[df["Ligand SMILES"].notna() & (df["Ligand SMILES"] != "")]

    # 2. Require valid affinity
    df = df[df["Ki (nM)"].notna() | df["IC50 (nM)"].notna()]

    # 3. Filter extreme values (artifacts)
    for col in ["Ki (nM)", "IC50 (nM)", "Kd (nM)"]:
        if col in df.columns:
            df = df[~(df[col] > 1e6)]  # Remove > 1 mM (non-specific)

    # 4. Use only human targets
    if "Target Source Organism According to Curator or DataSource" in df.columns:
        df = df[df["Target Source Organism According to Curator or DataSource"].str.contains(
            "Homo sapiens", na=False
        )]

    return df
```
