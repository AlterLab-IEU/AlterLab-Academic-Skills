# Code Examples

> Prefer the official SDK (`github.com/adaptyvbio/adaptyv-sdk`, decorator-based
> `@lab.experiment(target=...)`) when it fits. The raw-`requests` recipes below are for when
> you need explicit control over the draft → quote → submit lifecycle. Response field names
> shown here are illustrative — confirm against the live API / OpenAPI doc.

## Setup and Authentication

### Basic Setup

```python
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("ADAPTYV_API_KEY")
BASE_URL = "https://foundry-api-public.adaptyvbio.com/api/v1"

# Standard headers
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def check_api_connection():
    """Verify API connection and credentials by listing experiments."""
    try:
        response = requests.get(f"{BASE_URL}/experiments", headers=HEADERS)
        response.raise_for_status()
        print("✓ API connection successful")
        return True
    except requests.exceptions.HTTPError as e:
        print(f"✗ API authentication failed: {e}")
        return False
```

### Environment Setup

Create a `.env` file:
```bash
ADAPTYV_API_KEY=your_api_key_here
```

Install dependencies:
```bash
uv pip install requests python-dotenv
```

## Experiment Submission

Submission is two steps: create a **draft**, then **submit** it (after reviewing the cost
quote). `sequences` is a `{label: amino_acid_string}` map; multi-chain constructs join chains
with a colon (`"HEAVY:LIGHT"`).

### Create a Draft Experiment

```python
def create_experiment(name, sequences_dict, experiment_type="affinity",
                      method="bli", target_id=None, webhook_url=None):
    """
    Create a DRAFT experiment (does not submit / charge).

    Args:
        name: Human-readable experiment name.
        sequences_dict: {label: amino_acid_string}. Multi-chain uses "HEAVY:LIGHT".
        experiment_type: screening | affinity | thermostability | fluorescence | expression
        method: bli | spr (binding-type assays only).
        target_id: Target UUID from GET /targets (required for screening/affinity).
        webhook_url: Optional callback URL for progress notifications.

    Returns:
        Created experiment dict (status == "draft").
    """

    spec = {
        "experiment_type": experiment_type,
        "sequences": sequences_dict,
    }
    if experiment_type in ("screening", "affinity"):
        spec["method"] = method
        spec["target_id"] = target_id

    payload = {"name": name, "experiment_spec": spec}
    if webhook_url:
        payload["webhook_url"] = webhook_url

    response = requests.post(f"{BASE_URL}/experiments", headers=HEADERS, json=payload)
    response.raise_for_status()
    result = response.json()

    print("✓ Draft experiment created")
    print(f"  Experiment ID: {result['experiment_id']}")
    print(f"  Status: {result['status']}")  # 'draft'
    return result


def submit_experiment(experiment_id):
    """Submit a draft experiment to the lab (after reviewing its quote)."""
    response = requests.post(
        f"{BASE_URL}/experiments/{experiment_id}/submit", headers=HEADERS
    )
    response.raise_for_status()
    print(f"✓ Experiment {experiment_id} submitted")
    return response.json()


# Example: a small affinity screen against a catalog target
sequences = {
    "variant_1": "MKVLWAALLGLLGAAA...",
    "variant_2": "MKVLSAALLGLLGAAA...",
    "wildtype":  "MKVLWAALLGLLGAAA...",
}
draft = create_experiment(
    name="affinity round 3",
    sequences_dict=sequences,
    experiment_type="affinity",
    method="bli",
    target_id="<uuid from GET /targets>",
    webhook_url="https://your-server.com/adaptyv-webhook",
)
# review draft['costs'] / GET /experiments/{id}/quote, then:
submit_experiment(draft["experiment_id"])
```

### Cost Estimate Before Committing

```python
def cost_estimate(sequences_dict, experiment_type, method=None, target_id=None):
    """Get an estimated price for a spec without creating an experiment."""
    spec = {"experiment_type": experiment_type, "sequences": sequences_dict}
    if experiment_type in ("screening", "affinity"):
        spec["method"] = method
        spec["target_id"] = target_id

    response = requests.post(
        f"{BASE_URL}/experiments/cost-estimate",
        headers=HEADERS,
        json={"experiment_spec": spec},
    )
    response.raise_for_status()
    return response.json()  # USD cents, typically split into assay + material costs
```

## Tracking Experiments

### Check Experiment Status

```python
def check_experiment_status(experiment_id):
    """
    Get current status of an experiment

    Args:
        experiment_id: Experiment identifier

    Returns:
        Status information
    """

    response = requests.get(
        f"{BASE_URL}/experiments/{experiment_id}",
        headers=HEADERS
    )

    response.raise_for_status()
    status = response.json()

    print(f"Experiment: {experiment_id}")
    # Lifecycle state, e.g. Draft / InQueue / InProduction / DataAnalysis / Done
    print(f"  Status: {status['status']}")
    # How much result data is ready: none | partial | all
    print(f"  Results: {status.get('results_status')}")

    return status

# Example
status = check_experiment_status("<experiment uuid>")
```

### List All Experiments

```python
def list_experiments(status_filter=None, limit=50):
    """
    List experiments with optional status filtering

    Args:
        status_filter: Filter by status (submitted, processing, completed, failed)
        limit: Maximum number of results

    Returns:
        List of experiments
    """

    params = {"limit": limit}
    if status_filter:
        params["status"] = status_filter

    response = requests.get(
        f"{BASE_URL}/experiments",
        headers=HEADERS,
        params=params
    )

    response.raise_for_status()
    result = response.json()

    print(f"Found {result['total']} experiments")
    for exp in result['experiments']:
        print(f"  {exp['experiment_id']}: {exp['status']} ({exp['experiment_type']})")

    return result['experiments']

# Example - list all completed experiments
completed_experiments = list_experiments(status_filter="completed")
```

### Poll Until Complete

```python
import time

def wait_for_completion(experiment_id, check_interval=3600):
    """
    Poll experiment status until completion

    Args:
        experiment_id: Experiment identifier
        check_interval: Seconds between status checks (default: 1 hour)

    Returns:
        Final status
    """

    print(f"Monitoring experiment {experiment_id}...")

    while True:
        status = check_experiment_status(experiment_id)

        if status['status'] == 'Done':
            print("✓ Experiment done!")
            return status

        print(f"  Status: {status['status']} - checking again in {check_interval}s")
        time.sleep(check_interval)

# Example (not recommended - use a webhook_url instead!)
# status = wait_for_completion("<experiment uuid>", check_interval=3600)
```

## Retrieving Results

### Download Experiment Results

```python
import json

def download_results(experiment_id, output_dir="results"):
    """
    Download and parse experiment results

    Args:
        experiment_id: Experiment identifier
        output_dir: Directory to save results

    Returns:
        Parsed results data
    """

    # Get results
    response = requests.get(
        f"{BASE_URL}/experiments/{experiment_id}/results",
        headers=HEADERS
    )

    response.raise_for_status()
    results = response.json()

    # Save results JSON
    os.makedirs(output_dir, exist_ok=True)
    output_file = f"{output_dir}/{experiment_id}_results.json"

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"✓ Results downloaded: {output_file}")
    print(f"  Sequences tested: {len(results['results'])}")

    # Download raw data if available
    if 'download_urls' in results:
        for data_type, url in results['download_urls'].items():
            print(f"  {data_type} available at: {url}")

    return results

# Example
results = download_results("exp_abc123xyz")
```

### Parse Binding Results

```python
import pandas as pd

def parse_binding_results(results):
    """
    Parse binding assay results into DataFrame

    Args:
        results: Results dictionary from API

    Returns:
        pandas DataFrame with organized results
    """

    data = []
    for result in results['results']:
        row = {
            'sequence_id': result['sequence_id'],
            'kd': result['measurements']['kd'],
            'kd_error': result['measurements']['kd_error'],
            'kon': result['measurements']['kon'],
            'koff': result['measurements']['koff'],
            'confidence': result['quality_metrics']['confidence'],
            'r_squared': result['quality_metrics']['r_squared']
        }
        data.append(row)

    df = pd.DataFrame(data)

    # Sort by affinity (lower KD = stronger binding)
    df = df.sort_values('kd')

    print("Top 5 binders:")
    print(df.head())

    return df

# Example
experiment_id = "exp_abc123xyz"
results = download_results(experiment_id)
binding_df = parse_binding_results(results)

# Export to CSV
binding_df.to_csv(f"{experiment_id}_binding_results.csv", index=False)
```

### Parse Expression Results

```python
def parse_expression_results(results):
    """
    Parse expression testing results into DataFrame

    Args:
        results: Results dictionary from API

    Returns:
        pandas DataFrame with organized results
    """

    data = []
    for result in results['results']:
        row = {
            'sequence_id': result['sequence_id'],
            'yield_mg_per_l': result['measurements']['total_yield_mg_per_l'],
            'soluble_fraction': result['measurements']['soluble_fraction_percent'],
            'purity': result['measurements']['purity_percent'],
            'percentile': result['ranking']['percentile']
        }
        data.append(row)

    df = pd.DataFrame(data)

    # Sort by yield
    df = df.sort_values('yield_mg_per_l', ascending=False)

    print(f"Mean yield: {df['yield_mg_per_l'].mean():.2f} mg/L")
    print(f"Top performer: {df.iloc[0]['sequence_id']} ({df.iloc[0]['yield_mg_per_l']:.2f} mg/L)")

    return df

# Example
results = download_results("exp_expression123")
expression_df = parse_expression_results(results)
```

## Target Catalog

### Browse Targets

```python
def search_targets(query=None):
    """
    Browse the target antigen catalog (GET /targets).

    Exact filter parameters and response field names vary - confirm against the
    OpenAPI doc. Each target carries a target_id to use when creating a
    screening/affinity experiment.
    """
    params = {}
    if query:
        params["name"] = query  # filter by name; vendor / self-service filters also exist

    response = requests.get(f"{BASE_URL}/targets", headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()

# Example
targets = search_targets("PD-L1")
```

> Need an antigen that isn't in the catalog? Reach out via support@adaptyvbio.com — there is
> no verified public "custom target request" endpoint; don't assume one.

## Complete Workflows

### End-to-End Affinity Assay

```python
def complete_affinity_workflow(sequences_dict, target_id, name):
    """
    Create a draft affinity experiment and submit it. Results arrive later
    (poll status or use a webhook), then download + parse.

    Args:
        sequences_dict: {label: sequence}
        target_id: Target UUID from the catalog
        name: Experiment name
    """

    print("=== Starting Affinity Assay Workflow ===")

    # Step 1: Create the draft experiment
    print("\n1. Creating draft experiment...")
    experiment = create_experiment(
        name=name,
        sequences_dict=sequences_dict,
        experiment_type="affinity",
        method="bli",
        target_id=target_id,
    )

    experiment_id = experiment['experiment_id']

    # Step 2: Save experiment info + review the quote, then submit
    print("\n2. Saving experiment details...")
    with open(f"{experiment_id}_info.json", 'w') as f:
        json.dump(experiment, f, indent=2)

    # Inspect experiment['costs'] / GET /experiments/{id}/quote before this:
    submit_experiment(experiment_id)
    print("  Results arrive in weeks - poll status or use a webhook")

    # Later, once status == 'Done':
    # results = download_results(experiment_id)
    # df = parse_binding_results(results)
    # return df

    return experiment_id

# Example
antibody_variants = {
    "variant_1": "EVQLVESGGGLVQPGG...",   # single-chain example; a Fab uses "HEAVY:LIGHT"
    "variant_2": "EVQLVESGGGLVQPGS...",
    "wildtype":  "EVQLVESGGGLVQPGG...",
}

experiment_id = complete_affinity_workflow(
    antibody_variants,
    target_id="<PD-L1 target uuid from GET /targets>",
    name="antibody_affinity_maturation",
)
```

### Optimization + Testing Pipeline

```python
# Combine computational optimization with experimental testing

def optimization_and_testing_pipeline(initial_sequences, experiment_type="expression"):
    """
    Complete pipeline: optimize sequences computationally, then submit for testing

    Args:
        initial_sequences: Dictionary of {name: sequence}
        experiment_type: Type of experiment

    Returns:
        Experiment ID for tracking
    """

    print("=== Optimization and Testing Pipeline ===")

    # Step 1: Computational optimization
    print("\n1. Computational optimization...")
    from protein_optimization import complete_optimization_pipeline

    optimized = complete_optimization_pipeline(initial_sequences)

    print(f"✓ Optimization complete")
    print(f"  Started with: {len(initial_sequences)} sequences")
    print(f"  Optimized to: {len(optimized)} sequences")

    # Step 2: Select top candidates
    print("\n2. Selecting top candidates for testing...")
    top_candidates = optimized[:50]  # Top 50

    sequences_to_test = {
        seq_data['name']: seq_data['sequence']
        for seq_data in top_candidates
    }

    # Step 3: Submit for experimental validation
    print("\n3. Submitting to Adaptyv Foundry...")
    experiment = create_experiment(
        name="optimized library (computational prescreen)",
        sequences_dict=sequences_to_test,
        experiment_type=experiment_type,  # e.g. "expression" (no target needed)
    )
    submit_experiment(experiment['experiment_id'])  # after reviewing the quote

    print(f"✓ Pipeline complete")
    print(f"  Experiment ID: {experiment['experiment_id']}")

    return experiment['experiment_id']

# Example
initial_library = {
    f"variant_{i}": generate_random_sequence()
    for i in range(1000)
}

experiment_id = optimization_and_testing_pipeline(
    initial_library,
    experiment_type="expression"
)
```

### Batch Result Analysis

```python
def analyze_multiple_experiments(experiment_ids):
    """
    Download and analyze results from multiple experiments

    Args:
        experiment_ids: List of experiment identifiers

    Returns:
        Combined DataFrame with all results
    """

    all_results = []

    for exp_id in experiment_ids:
        print(f"Processing {exp_id}...")

        # Download results
        results = download_results(exp_id, output_dir=f"results/{exp_id}")

        # Parse based on experiment type
        exp_type = results.get('experiment_type', 'unknown')

        if exp_type in ('screening', 'affinity'):
            df = parse_binding_results(results)
            df['experiment_id'] = exp_id
            all_results.append(df)

        elif exp_type == 'expression':
            df = parse_expression_results(results)
            df['experiment_id'] = exp_id
            all_results.append(df)

    # Combine all results
    combined_df = pd.concat(all_results, ignore_index=True)

    print(f"\n✓ Analysis complete")
    print(f"  Total experiments: {len(experiment_ids)}")
    print(f"  Total sequences: {len(combined_df)}")

    return combined_df

# Example
experiment_ids = [
    "exp_round1_abc",
    "exp_round2_def",
    "exp_round3_ghi"
]

all_data = analyze_multiple_experiments(experiment_ids)
all_data.to_csv("combined_results.csv", index=False)
```

## Error Handling

### Robust API Wrapper

```python
import time
from requests.exceptions import RequestException, HTTPError

def api_request_with_retry(method, url, max_retries=3, backoff_factor=2, **kwargs):
    """
    Make API request with retry logic and error handling

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        max_retries: Maximum number of retry attempts
        backoff_factor: Exponential backoff multiplier
        **kwargs: Additional arguments for requests

    Returns:
        Response object

    Raises:
        RequestException: If all retries fail
    """

    for attempt in range(max_retries):
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response

        except HTTPError as e:
            if e.response.status_code == 429:  # Rate limit
                wait_time = backoff_factor ** attempt
                print(f"Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue

            elif e.response.status_code >= 500:  # Server error
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    print(f"Server error. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise

            else:  # Client error (4xx) - don't retry
                error_data = e.response.json() if e.response.content else {}
                print(f"API Error: {error_data.get('error', {}).get('message', str(e))}")
                raise

        except RequestException as e:
            if attempt < max_retries - 1:
                wait_time = backoff_factor ** attempt
                print(f"Request failed. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                raise

    raise RequestException(f"Failed after {max_retries} attempts")

# Example usage
response = api_request_with_retry(
    "POST",
    f"{BASE_URL}/experiments",
    headers=HEADERS,
    json={
        "name": "retry demo",
        "experiment_spec": {
            "experiment_type": "expression",
            "sequences": {"design_a": "MKVLWALLGLLGAA..."},
        },
    },
)
```

## Utility Functions

### Validate a Sequence Map Before Submission

The API expects `sequences` as a `{label: amino_acid_string}` map; multi-chain constructs join
chains with a colon (`"HEAVY:LIGHT"`). Validate locally to catch typos before paying to test.

```python
VALID_AA = set("ACDEFGHIKLMNPQRSTVWY")

def validate_sequence(seq):
    """Validate one entry. Splits multi-chain constructs on ':'. Returns (ok, error)."""
    if not seq:
        return False, "Empty sequence"
    for chain in seq.upper().split(":"):
        if not chain:
            return False, "Empty chain (check ':' placement)"
        invalid = set(chain) - VALID_AA
        if invalid:
            return False, f"Invalid amino acids: {sorted(invalid)}"
    return True, None

def clean_sequence_map(sequences_dict):
    """
    Normalise a {label: sequence} map (strip whitespace, uppercase) and validate
    every entry. Raises ValueError on the first bad sequence. Returns the cleaned map
    ready to drop into experiment_spec['sequences'].
    """
    cleaned = {}
    for label, seq in sequences_dict.items():
        clean = "".join(seq.split()).upper()  # preserves ':' chain separators
        ok, error = validate_sequence(clean)
        if not ok:
            raise ValueError(f"Invalid sequence '{label}': {error}")
        cleaned[label] = clean
    return cleaned

# Example
sequences = {
    "var1": "MKVLWAALLG",
    "fab1": "EVQLVESGG:DIQMTQSPS",  # heavy:light
}
print(clean_sequence_map(sequences))
```
