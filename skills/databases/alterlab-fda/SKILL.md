---
name: alterlab-fda
description: Query the openFDA API for drugs, medical devices, adverse event reports, recalls, regulatory submissions (510k, PMA), and substance identification (UNII). Use when searching FDA safety data, pharmacovigilance and adverse-event signals, device clearances, drug labels, or recall records for regulatory data analysis and safety research. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read WebFetch Bash(curl:*) Bash(python:*)
compatibility: Keyless openFDA REST API; optional API key raises rate limits
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# FDA Database Access

## Overview

Access comprehensive FDA regulatory data through openFDA, the FDA's initiative to provide open APIs for public datasets. Query information about drugs, medical devices, foods, animal/veterinary products, and substances using Python with standardized interfaces.

**Key capabilities:**
- Query adverse events for drugs, devices, foods, and veterinary products
- Access product labeling, approvals, and regulatory submissions
- Monitor recalls and enforcement actions
- Look up National Drug Codes (NDC) and substance identifiers (UNII)
- Analyze device classifications and clearances (510k, PMA)
- Track drug shortages and supply issues
- Research chemical structures and substance relationships

## When to Use This Skill

This skill should be used when working with:
- **Drug research**: Safety profiles, adverse events, labeling, approvals, shortages
- **Medical device surveillance**: Adverse events, recalls, 510(k) clearances, PMA approvals
- **Food safety**: Recalls, allergen tracking, adverse events, dietary supplements
- **Veterinary medicine**: Animal drug adverse events by species and breed
- **Chemical/substance data**: UNII lookup, CAS number mapping, molecular structures
- **Regulatory analysis**: Approval pathways, enforcement actions, compliance tracking
- **Pharmacovigilance**: Post-market surveillance, safety signal detection
- **Scientific research**: Drug interactions, comparative safety, epidemiological studies

## Quick Start

### 1. Basic Setup

```python
# Run from the skill's scripts/ dir, or add it to sys.path first.
from fda_query import FDAQuery

# API key is optional (works keyless); pass it or set FDA_API_KEY.
fda = FDAQuery(api_key="YOUR_API_KEY")

# Query drug adverse events
events = fda.query_drug_events("aspirin", limit=100)

# Get drug labeling
label = fda.query_drug_label("Lipitor", brand=True)

# Search device recalls
recalls = fda.query("device", "enforcement",
                   search="classification:Class+I",
                   limit=50)
```

### 2. API Key Setup

While the API works without a key, registering provides higher rate limits:
- **Without key**: 240 requests/min, 1,000/day
- **With key**: 240 requests/min, 120,000/day

Register at: https://open.fda.gov/apis/authentication/

Set as environment variable:
```bash
export FDA_API_KEY="your_key_here"
```

### 3. Running Examples

```bash
# Run comprehensive examples
python scripts/fda_examples.py

# This demonstrates:
# - Drug safety profiles
# - Device surveillance
# - Food recall monitoring
# - Substance lookup
# - Comparative drug analysis
# - Veterinary drug analysis
```

## FDA Database Categories

### Drugs

Access 6 drug-related endpoints covering the full drug lifecycle from approval to post-market surveillance.

**Endpoints:**
1. **Adverse Events** - Reports of side effects, errors, and therapeutic failures
2. **Product Labeling** - Prescribing information, warnings, indications
3. **NDC Directory** - National Drug Code product information
4. **Enforcement Reports** - Drug recalls and safety actions
5. **Drugs@FDA** - Historical approval data since 1939
6. **Drug Shortages** - Current and resolved supply issues

**Common use cases:**
```python
# Safety signal detection
fda.count_by_field("drug", "event",
                  search="patient.drug.medicinalproduct:metformin",
                  field="patient.reaction.reactionmeddrapt")

# Get prescribing information
label = fda.query_drug_label("Keytruda", brand=True)

# Check for recalls
recalls = fda.query_drug_recalls(drug_name="metformin")

# Monitor shortages (endpoint is drug/shortages; status values:
# "Current", "To Be Discontinued", "Resolved")
shortages = fda.query("drug", "shortages",
                     search="status:Current")
```

**Reference:** See `references/drugs.md` for detailed documentation

### Devices

Access 9 device-related endpoints covering medical device safety, approvals, and registrations.

**Endpoints:**
1. **Adverse Events** - Device malfunctions, injuries, deaths
2. **510(k) Clearances** - Premarket notifications
3. **Classification** - Device categories and risk classes
4. **Enforcement Reports** - Device recalls
5. **Recalls** - Detailed recall information
6. **PMA** - Premarket approval data for Class III devices
7. **Registrations & Listings** - Manufacturing facility data
8. **UDI** - Unique Device Identification database
9. **COVID-19 Serology** - Antibody test performance data

**Common use cases:**
```python
# Monitor device safety
events = fda.query_device_events("pacemaker", limit=100)

# Look up device classification
classification = fda.query_device_classification("DQY")

# Find 510(k) clearances
clearances = fda.query_device_510k(applicant="Medtronic")

# Search by UDI
device_info = fda.query("device", "udi",
                       search="identifiers.id:00884838003019")
```

**Reference:** See `references/devices.md` for detailed documentation

### Foods

Access 2 food-related endpoints for safety monitoring and recalls.

**Endpoints:**
1. **Adverse Events** - Food, dietary supplement, and cosmetic events
2. **Enforcement Reports** - Food product recalls

**Common use cases:**
```python
# Monitor allergen recalls
recalls = fda.query_food_recalls(reason="undeclared peanut")

# Track dietary supplement events
events = fda.query_food_events(
    industry="Dietary Supplements")

# Find contamination recalls
listeria = fda.query_food_recalls(
    reason="listeria",
    classification="I")
```

**Reference:** See `references/foods.md` for detailed documentation

### Animal & Veterinary

Access veterinary drug adverse event data with species-specific information.

**Endpoint:**
1. **Adverse Events** - Animal drug side effects by species, breed, and product

**Common use cases:**
```python
# Species-specific events
dog_events = fda.query_animal_events(
    species="Dog",
    drug_name="flea collar")

# Breed predisposition analysis
breed_query = fda.query("animalandveterinary", "event",
    search="reaction.veddra_term_name:*seizure*+AND+"
           "animal.breed.breed_component:*Labrador*")
```

**Reference:** See `references/animal_veterinary.md` for detailed documentation

### Substances & Other

Access molecular-level substance data with UNII codes, chemical structures, and relationships.

**Endpoints:**
1. **Substance Data** - UNII, CAS, chemical structures, relationships
2. **NSDE** - Historical substance data (legacy)

**Common use cases:**
```python
# UNII to CAS mapping
substance = fda.query_substance_by_unii("R16CO5Y76E")

# Search by name
results = fda.query_substance_by_name("acetaminophen")

# Get chemical structure
structure = fda.query("other", "substance",
    search="names.name:ibuprofen+AND+substanceClass:chemical")
```

**Reference:** See `references/other.md` for detailed documentation

## Query Patterns & Result Handling

Reusable `FDAQuery` patterns (safety profiles, temporal trends, comparative and
cross-database lookups), the response structure, error handling, pagination, and
best practices live in `references/query_patterns.md`.

Essentials to keep in mind:
- Use **specific field searches** (`patient.drug.medicinalproduct:aspirin`), not
  bare wildcards.
- `FDAQuery` handles rate limiting (240/min, 120,000/day with key) and caching
  automatically.
- Use `exact=True` on `count_by_field` to count exact phrases (adds `.exact`).
- All responses share the `{meta: {results: {total, ...}}, results: [...]}` shape;
  always check for `error` and empty `results`.

## API Reference

For detailed information about:
- **Authentication and rate limits** → See `references/api_basics.md`
- **Query patterns & result handling** → See `references/query_patterns.md`
- **Drug databases** → See `references/drugs.md`
- **Device databases** → See `references/devices.md`
- **Food databases** → See `references/foods.md`
- **Animal/veterinary databases** → See `references/animal_veterinary.md`
- **Substance databases** → See `references/other.md`

## Scripts

### `scripts/fda_query.py`

Main query module with `FDAQuery` class providing:
- Unified interface to all FDA endpoints
- Automatic rate limiting and caching
- Error handling and retry logic
- Common query patterns

### `scripts/fda_examples.py`

Comprehensive examples demonstrating:
- Drug safety profile analysis
- Device surveillance monitoring
- Food recall tracking
- Substance lookup
- Comparative drug analysis
- Veterinary drug analysis

Run examples:
```bash
python scripts/fda_examples.py
```

## Additional Resources

- **openFDA Homepage**: https://open.fda.gov/
- **API Documentation**: https://open.fda.gov/apis/
- **Interactive API Explorer**: https://open.fda.gov/apis/try-the-api/
- **GitHub Repository**: https://github.com/FDA/openfda
- **Terms of Service**: https://open.fda.gov/terms/

## Support and Troubleshooting

### Common Issues

**Issue**: Rate limit exceeded
- **Solution**: Use API key, implement delays, or reduce request frequency

**Issue**: No results found
- **Solution**: Try broader search terms, check spelling, use wildcards

**Issue**: Invalid query syntax
- **Solution**: Review query syntax in `references/api_basics.md`

**Issue**: Missing fields in results
- **Solution**: Not all records contain all fields; always check field existence

### Getting Help

- **GitHub Issues**: https://github.com/FDA/openfda/issues
- **Email**: open-fda@fda.hhs.gov

