# FDA Other Databases - Substances and NSDE

This reference covers FDA substance-related and other specialized API endpoints accessible through openFDA.

## Overview

The FDA maintains additional databases for substance-level information that is precise to the molecular level. These databases support regulatory activities across drugs, biologics, devices, foods, and cosmetics.

## Available Endpoints

### 1. Substance Data

**Endpoint**: `https://api.fda.gov/other/substance.json`

**Purpose**: Access substance information that is precise to the molecular level for internal and external use. This includes information about active pharmaceutical ingredients, excipients, and other substances used in FDA-regulated products.

**Data Source**: FDA Global Substance Registration System (GSRS)

**Key Fields**:
- `uuid` - Unique substance identifier (UUID)
- `approvalID` - FDA Unique Ingredient Identifier (UNII)
- `approved` - Approval date
- `substanceClass` - Type of substance (chemical, protein, nucleic acid, polymer, etc.)
- `names` - Array of substance names
- `names.name` - Name text
- `names.type` - Name type (systematic, brand, common, etc.)
- `names.preferred` - Whether preferred name
- `codes` - Array of substance codes
- `codes.code` - Code value
- `codes.codeSystem` - Code system (CAS, ECHA, EINECS, etc.)
- `codes.type` - Code type
- `relationships` - Array of substance relationships
- `relationships.type` - Relationship type (ACTIVE MOIETY, METABOLITE, IMPURITY, etc.)
- `relationships.relatedSubstance` - Related substance reference
- `moieties` - Molecular moieties
- `properties` - Array of physicochemical properties
- `properties.name` - Property name
- `properties.value` - Property value
- `properties.propertyType` - Property type
- `structure` - Chemical structure information
- `structure.smiles` - SMILES notation
- `structure.inchi` - InChI string
- `structure.inchiKey` - InChI key
- `structure.formula` - Molecular formula
- `structure.molecularWeight` - Molecular weight
- `modifications` - Structural modifications (for proteins, etc.)
- `protein` - Protein-specific information
- `protein.subunits` - Protein subunits
- `protein.sequenceType` - Sequence type
- `nucleicAcid` - Nucleic acid information
- `nucleicAcid.subunits` - Sequence subunits
- `polymer` - Polymer information
- `mixture` - Mixture components
- `mixture.components` - Component substances
- `tags` - Substance tags
- `references` - Literature references

**Substance Classes**:
- **Chemical** - Small molecules with defined chemical structure
- **Protein** - Proteins and peptides
- **Nucleic Acid** - DNA, RNA, oligonucleotides
- **Polymer** - Polymeric substances
- **Structurally Diverse** - Complex mixtures, botanicals
- **Mixture** - Defined mixtures
- **Concept** - Abstract concepts (e.g., groups)

**Common Use Cases**:
- Active ingredient identification
- Molecular structure lookup
- UNII code resolution
- Chemical identifier mapping (CAS to UNII, etc.)
- Substance relationship analysis
- Excipient identification
- Botanical substance information
- Protein and biologic characterization

**Example Queries**:
```python
import requests

api_key = "YOUR_API_KEY"
url = "https://api.fda.gov/other/substance.json"

# Look up substance by UNII code
params = {
    "api_key": api_key,
    "search": "approvalID:R16CO5Y76E",  # Aspirin UNII
    "limit": 1
}

response = requests.get(url, params=params)
data = response.json()
```

```python
# Search by substance name
params = {
    "api_key": api_key,
    "search": "names.name:acetaminophen",
    "limit": 5
}
```

```python
# Find substances by CAS number
params = {
    "api_key": api_key,
    "search": "codes.code:50-78-2",  # Aspirin CAS
    "limit": 1
}
```

```python
# Get chemical substances only
params = {
    "api_key": api_key,
    "search": "substanceClass:chemical",
    "limit": 100
}
```

```python
# Search by molecular formula
params = {
    "api_key": api_key,
    "search": "structure.formula:C8H9NO2",  # Acetaminophen
    "limit": 10
}
```

```python
# Find protein substances
params = {
    "api_key": api_key,
    "search": "substanceClass:protein",
    "limit": 50
}
```

### 2. NSDE (Comprehensive NDC SPL Data Elements File)

**Endpoint**: `https://api.fda.gov/other/nsde.json`

**Purpose**: Package-level NDC data elements extracted from Structured Product Labeling
(SPL) — one record per package NDC, including marketing start/end dates and
inactivation/reactivation dates. Use it to map 10-/11-digit package NDCs to products and
to check whether an NDC is (or was) marketed. It is **not** a substance database; use
the Substance Data endpoint (or `other/unii`) for substance-level information.

**Key Fields** (verified 2026-09):
- `package_ndc` - Package NDC (10-digit, hyphenated)
- `package_ndc11` - Package NDC (11-digit, no hyphens — the billing format)
- `proprietary_name` - Product proprietary (brand) name
- `product_type` - e.g. `HUMAN PRESCRIPTION DRUG`, `HUMAN OTC DRUG`
- `marketing_category` - e.g. `NDA`, `ANDA`, `BLA`, `OTC MONOGRAPH ...`
- `application_number_or_citation` - e.g. `NDA201803`
- `dosage_form` - Dosage form
- `marketing_start_date`, `marketing_end_date` - YYYYMMDD
- `inactivation_date`, `reactivation_date` - YYYYMMDD
- `billing_unit` - Billing unit (e.g. `EA`, `ML`, `GM`) when present

**Common Use Cases**:
- Normalizing 10-digit NDCs to the 11-digit billing format (and back)
- Checking marketing status / discontinuation of a package NDC
- Linking claims or EHR NDCs to proprietary names and application numbers

**Example Queries**:
```python
# All packages for a brand name (quote multi-word or case-sensitive values)
params = {
    "api_key": api_key,
    "search": 'proprietary_name:"Advil"',
    "limit": 20
}

response = requests.get("https://api.fda.gov/other/nsde.json", params=params)
```

```python
# Look up one package by its 11-digit NDC
params = {
    "api_key": api_key,
    "search": "package_ndc11:00573013391",
    "limit": 1
}
```

## Integration Tips

### UNII to CAS Mapping

```python
def get_substance_identifiers(unii, api_key):
    """
    Get all identifiers for a substance given its UNII code.

    Args:
        unii: FDA Unique Ingredient Identifier
        api_key: FDA API key

    Returns:
        Dictionary with substance identifiers
    """
    import requests

    url = "https://api.fda.gov/other/substance.json"
    params = {
        "api_key": api_key,
        "search": f"approvalID:{unii}",
        "limit": 1
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "results" not in data or len(data["results"]) == 0:
        return None

    substance = data["results"][0]

    identifiers = {
        "unii": substance.get("approvalID"),
        "uuid": substance.get("uuid"),
        "preferred_name": None,
        "cas_numbers": [],
        "other_codes": {}
    }

    # Extract names
    if "names" in substance:
        for name in substance["names"]:
            if name.get("preferred"):
                identifiers["preferred_name"] = name.get("name")
                break
        if not identifiers["preferred_name"] and len(substance["names"]) > 0:
            identifiers["preferred_name"] = substance["names"][0].get("name")

    # Extract codes
    if "codes" in substance:
        for code in substance["codes"]:
            code_system = code.get("codeSystem", "").upper()
            code_value = code.get("code")

            if "CAS" in code_system:
                identifiers["cas_numbers"].append(code_value)
            else:
                if code_system not in identifiers["other_codes"]:
                    identifiers["other_codes"][code_system] = []
                identifiers["other_codes"][code_system].append(code_value)

    return identifiers
```

### Chemical Structure Lookup

```python
def get_chemical_structure(substance_name, api_key):
    """
    Get chemical structure information for a substance.

    Args:
        substance_name: Name of the substance
        api_key: FDA API key

    Returns:
        Dictionary with structure information
    """
    import requests

    url = "https://api.fda.gov/other/substance.json"
    params = {
        "api_key": api_key,
        "search": f"names.name:{substance_name}",
        "limit": 1
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "results" not in data or len(data["results"]) == 0:
        return None

    substance = data["results"][0]

    if "structure" not in substance:
        return None

    structure = substance["structure"]

    return {
        "smiles": structure.get("smiles"),
        "inchi": structure.get("inchi"),
        "inchi_key": structure.get("inchiKey"),
        "formula": structure.get("formula"),
        "molecular_weight": structure.get("molecularWeight"),
        "substance_class": substance.get("substanceClass")
    }
```

### Substance Relationship Mapping

```python
def get_substance_relationships(unii, api_key):
    """
    Get all related substances (metabolites, active moieties, etc.).

    Args:
        unii: FDA Unique Ingredient Identifier
        api_key: FDA API key

    Returns:
        Dictionary organizing relationships by type
    """
    import requests

    url = "https://api.fda.gov/other/substance.json"
    params = {
        "api_key": api_key,
        "search": f"approvalID:{unii}",
        "limit": 1
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "results" not in data or len(data["results"]) == 0:
        return None

    substance = data["results"][0]

    relationships = {}

    if "relationships" in substance:
        for rel in substance["relationships"]:
            rel_type = rel.get("type")
            if rel_type not in relationships:
                relationships[rel_type] = []

            related = {
                "uuid": rel.get("relatedSubstance", {}).get("uuid"),
                "unii": rel.get("relatedSubstance", {}).get("approvalID"),
                "name": rel.get("relatedSubstance", {}).get("refPname")
            }
            relationships[rel_type].append(related)

    return relationships
```

### Active Ingredient Extraction

```python
def find_active_ingredients_by_product(product_name, api_key):
    """
    Find active ingredients in a drug product.

    Args:
        product_name: Drug product name
        api_key: FDA API key

    Returns:
        List of active ingredient UNIIs and names
    """
    import requests

    # First search drug label database
    label_url = "https://api.fda.gov/drug/label.json"
    label_params = {
        "api_key": api_key,
        "search": f"openfda.brand_name:{product_name}",
        "limit": 1
    }

    response = requests.get(label_url, params=label_params)
    data = response.json()

    if "results" not in data or len(data["results"]) == 0:
        return None

    label = data["results"][0]

    # Extract UNIIs from openfda section
    active_ingredients = []

    if "openfda" in label:
        openfda = label["openfda"]

        # Get UNIIs
        unii_list = openfda.get("unii", [])
        generic_names = openfda.get("generic_name", [])

        for i, unii in enumerate(unii_list):
            ingredient = {"unii": unii}
            if i < len(generic_names):
                ingredient["name"] = generic_names[i]

            # Get additional substance info
            substance_info = get_substance_identifiers(unii, api_key)
            if substance_info:
                ingredient.update(substance_info)

            active_ingredients.append(ingredient)

    return active_ingredients
```

## Best Practices

1. **Use UNII as primary identifier** - Most consistent across FDA databases
2. **Map between identifier systems** - CAS, UNII, InChI Key for cross-referencing
3. **Handle substance variations** - Different salt forms, hydrates have different UNIIs
4. **Check substance class** - Different classes have different data structures
5. **Validate chemical structures** - SMILES and InChI should be verified
6. **Consider substance relationships** - Active moiety vs. salt form matters
7. **Use preferred names** - More consistent than trade names
8. **Cache substance data** - Substance information changes infrequently
9. **Cross-reference with other endpoints** - Link substances to drugs/products
10. **Handle mixture components** - Complex products have multiple components

## UNII System

The FDA Unique Ingredient Identifier (UNII) system provides:
- **Unique identifiers** - Each substance gets one UNII
- **Substance specificity** - Different forms (salts, hydrates) get different UNIIs
- **Global recognition** - Used internationally
- **Stability** - UNIIs don't change once assigned
- **Free access** - No licensing required

**UNII Format**: 10-character alphanumeric code (e.g., `R16CO5Y76E`)

## Substance Classes Explained

### Chemical
- Traditional small molecule drugs
- Have defined molecular structure
- Include organic and inorganic compounds
- SMILES, InChI, molecular formula available

### Protein
- Polypeptides and proteins
- Sequence information available
- May have post-translational modifications
- Includes antibodies, enzymes, hormones

### Nucleic Acid
- DNA and RNA sequences
- Oligonucleotides
- Antisense, siRNA, mRNA
- Sequence data available

### Polymer
- Synthetic and natural polymers
- Structural repeat units
- Molecular weight distributions
- Used as excipients and active ingredients

### Structurally Diverse
- Complex natural products
- Botanical extracts
- Materials without single molecular structure
- Characterized by source and composition

### Mixture
- Defined combinations of substances
- Fixed or variable composition
- Each component trackable

## Additional Resources

- FDA Substance Registration System: https://precision.fda.gov/uniisearch
- UNII Search: https://precision.fda.gov/uniisearch
- OpenFDA Other APIs: https://open.fda.gov/apis/other/
- API Basics: See `api_basics.md` in this references directory
- Python helper: See `scripts/fda_query.py` (the `FDAQuery` class) and `scripts/fda_examples.py`
