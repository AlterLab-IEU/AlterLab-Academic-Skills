# FDA Query Patterns & Result Handling

Reusable `FDAQuery` patterns, response structure, pagination, and best practices.
For per-domain endpoint detail see `drugs.md`, `devices.md`, `foods.md`,
`animal_veterinary.md`, `other.md`; for auth and query syntax see `api_basics.md`.

## Common Query Patterns

### Pattern 1: Safety Profile Analysis

Combine multiple data sources into a comprehensive safety profile:

```python
def drug_safety_profile(fda, drug_name):
    """Generate complete safety profile."""

    # 1. Total adverse events
    events = fda.query_drug_events(drug_name, limit=1)
    total = events["meta"]["results"]["total"]

    # 2. Most common reactions
    reactions = fda.count_by_field(
        "drug", "event",
        search=f"patient.drug.medicinalproduct:*{drug_name}*",
        field="patient.reaction.reactionmeddrapt",
        exact=True
    )

    # 3. Serious events
    serious = fda.query("drug", "event",
        search=f"patient.drug.medicinalproduct:*{drug_name}*+AND+serious:1",
        limit=1)

    # 4. Recent recalls
    recalls = fda.query_drug_recalls(drug_name=drug_name)

    return {
        "total_events": total,
        "top_reactions": reactions["results"][:10],
        "serious_events": serious["meta"]["results"]["total"],
        "recalls": recalls["results"]
    }
```

### Pattern 2: Temporal Trend Analysis

Analyze trends over time using date ranges:

```python
from datetime import datetime, timedelta

def get_monthly_trends(fda, drug_name, months=12):
    """Get monthly adverse event trends."""
    trends = []

    for i in range(months):
        end = datetime.now() - timedelta(days=30*i)
        start = end - timedelta(days=30)

        date_range = f"[{start.strftime('%Y%m%d')}+TO+{end.strftime('%Y%m%d')}]"
        search = f"patient.drug.medicinalproduct:*{drug_name}*+AND+receivedate:{date_range}"

        result = fda.query("drug", "event", search=search, limit=1)
        count = result["meta"]["results"]["total"] if "meta" in result else 0

        trends.append({
            "month": start.strftime("%Y-%m"),
            "events": count
        })

    return trends
```

### Pattern 3: Comparative Analysis

Compare multiple products side-by-side:

```python
def compare_drugs(fda, drug_list):
    """Compare safety profiles of multiple drugs."""
    comparison = {}

    for drug in drug_list:
        # Total events
        events = fda.query_drug_events(drug, limit=1)
        total = events["meta"]["results"]["total"] if "meta" in events else 0

        # Serious events
        serious = fda.query("drug", "event",
            search=f"patient.drug.medicinalproduct:*{drug}*+AND+serious:1",
            limit=1)
        serious_count = serious["meta"]["results"]["total"] if "meta" in serious else 0

        comparison[drug] = {
            "total_events": total,
            "serious_events": serious_count,
            "serious_rate": (serious_count/total*100) if total > 0 else 0
        }

    return comparison
```

### Pattern 4: Cross-Database Lookup

Link data across multiple endpoints:

```python
def comprehensive_device_lookup(fda, device_name):
    """Look up device across all relevant databases."""

    return {
        "adverse_events": fda.query_device_events(device_name, limit=10),
        "510k_clearances": fda.query_device_510k(device_name=device_name),
        "recalls": fda.query("device", "enforcement",
                           search=f"product_description:*{device_name}*"),
        "udi_info": fda.query("device", "udi",
                            search=f"brand_name:*{device_name}*")
    }
```

## Working with Results

### Response Structure

All API responses follow this structure:

```python
{
    "meta": {
        "disclaimer": "...",
        "results": {
            "skip": 0,
            "limit": 100,
            "total": 15234
        }
    },
    "results": [
        # Array of result objects
    ]
}
```

### Error Handling

Always handle potential errors:

```python
result = fda.query_drug_events("aspirin", limit=10)

if "error" in result:
    print(f"Error: {result['error']}")
elif "results" not in result or len(result["results"]) == 0:
    print("No results found")
else:
    # Process results
    for event in result["results"]:
        # Handle event data
        pass
```

### Pagination

For large result sets, use pagination:

```python
# Automatic pagination
all_results = fda.query_all(
    "drug", "event",
    search="patient.drug.medicinalproduct:aspirin",
    max_results=5000
)

# Manual pagination
for skip in range(0, 1000, 100):
    batch = fda.query("drug", "event",
                     search="...",
                     limit=100,
                     skip=skip)
    # Process batch
```

## Best Practices

### 1. Use Specific Searches

**DO:**
```python
# Specific field search
search="patient.drug.medicinalproduct:aspirin"
```

**DON'T:**
```python
# Overly broad wildcard
search="*aspirin*"
```

### 2. Implement Rate Limiting

The `FDAQuery` class handles rate limiting automatically, but be aware of limits:
- 240 requests per minute
- 120,000 requests per day (with API key)

### 3. Cache Frequently Accessed Data

The `FDAQuery` class includes built-in caching (enabled by default):

```python
# Caching is automatic
fda = FDAQuery(api_key=api_key, use_cache=True, cache_ttl=3600)
```

### 4. Use Exact Matching for Counting

When counting/aggregating, use `.exact` suffix:

```python
# Count exact phrases
fda.count_by_field("drug", "event",
                  search="...",
                  field="patient.reaction.reactionmeddrapt",
                  exact=True)  # Adds .exact automatically
```

### 5. Validate Input Data

Clean and validate search terms:

```python
def clean_drug_name(name):
    """Clean drug name for query."""
    return name.strip().replace('"', '\\"')

drug_name = clean_drug_name(user_input)
```
