# Protein Sequence Optimization

## Overview

Before submitting protein sequences for experimental testing, use computational tools to optimize sequences for improved expression, solubility, and stability. This pre-screening reduces experimental costs and increases success rates.

## Common Protein Expression Problems

### 1. Unpaired Cysteines

**Problem:**
- Unpaired cysteines form unwanted disulfide bonds
- Leads to aggregation and misfolding
- Reduces expression yield and stability

**Solution:**
- Remove unpaired cysteines unless functionally necessary
- Pair cysteines appropriately for structural disulfides
- Replace with serine or alanine in non-critical positions

**Example:**
```python
# Check for cysteine pairs
from Bio.Seq import Seq

def check_cysteines(sequence):
    cys_count = sequence.count('C')
    if cys_count % 2 != 0:
        print(f"Warning: Odd number of cysteines ({cys_count})")
    return cys_count
```

### 2. Excessive Hydrophobicity

**Problem:**
- Long hydrophobic patches promote aggregation
- Exposed hydrophobic residues drive protein clumping
- Poor solubility in aqueous buffers

**Solution:**
- Maintain balanced hydropathy profiles
- Use short, flexible linkers between domains
- Reduce surface-exposed hydrophobic residues

**Metrics:**
- Kyte-Doolittle hydropathy plots
- GRAVY score (Grand Average of Hydropathy)
- pSAE (percent Solvent-Accessible hydrophobic residues)

### 3. Low Solubility

**Problem:**
- Proteins precipitate during expression or purification
- Inclusion body formation
- Difficult downstream processing

**Solution:**
- Use solubility prediction tools for pre-screening
- Apply sequence optimization algorithms
- Add solubilizing tags if needed

## Computational Tools for Optimization

### NetSolP - Initial Solubility Screening

**Purpose:** Fast solubility prediction for filtering sequences.

**Method:** Transformer/ESM-based model predicting solubility and usability.

**Access:** NetSolP is the DTU Health Tech web service (no `pip install netsolp` package
exists). Submit via the web UI at `https://services.healthtech.dtu.dk/services/NetSolP-1.0/`,
or run the downloadable model locally per DTU's instructions. The snippet below is a
**sketch** of an HTTP call — confirm the actual request/response shape against the current
service before relying on it.

```python
# Only requests is needed locally: uv pip install requests
import requests

def predict_solubility_netsolp(sequence):
    """Sketch: submit a sequence to the NetSolP web service. Verify the real endpoint/payload."""
    url = "https://services.healthtech.dtu.dk/services/NetSolP-1.0/"
    # The live service is form/job based; treat this as a placeholder, not a working call.
    response = requests.post(url, data={"sequence": sequence, "format": "fasta"})
    return response.json()
```

**Interpretation:**
- Score > 0.5: Likely soluble
- Score < 0.5: Likely insoluble
- Use for initial filtering before more expensive predictions

**When to use:**
- First-pass filtering of large libraries
- Quick validation of designed sequences
- Prioritizing sequences for experimental testing

### SoluProt - Comprehensive Solubility Prediction

**Purpose:** Advanced solubility prediction with higher accuracy.

**Method:** Gradient-boosting model on sequence-derived features (soluble expression in E. coli).

**Access:** SoluProt is a Loschmidt Laboratories web server
(`https://loschmidt.chemi.muni.cz/soluprot/`) — there is no `pip install soluprot` package.
Submit sequences via the web UI (or its batch interface) and read the returned scores. Treat
the helper below as a thin wrapper you would write around whatever programmatic access the
service exposes:

```python
def screen_variants_soluprot(scores_by_name, threshold=0.6):
    """
    Given solubility scores retrieved from the SoluProt web server, flag the soluble ones.

    Args:
        scores_by_name: {name: soluprot_score} obtained from the service.
    """
    return [
        {"name": name, "solubility_score": score, "predicted_soluble": score > threshold}
        for name, score in scores_by_name.items()
    ]
```

**Interpretation:**
- Score > 0.6: High solubility confidence
- Score 0.4-0.6: Uncertain, may need optimization
- Score < 0.4: Likely problematic

**When to use:**
- After initial NetSolP filtering
- When higher prediction accuracy is needed
- Before committing to expensive synthesis/testing

### SolubleMPNN - Sequence Redesign

**Purpose:** Redesign protein sequences to improve solubility while maintaining function.

**Method:** A solubility-biased **weight set for ProteinMPNN** (it ships as a model checkpoint
within the ProteinMPNN / LigandMPNN family, e.g. selectable via a `--model_name`/weights flag),
not a standalone `pip install soluble-mpnn` package. It is structure-conditioned: you provide a
backbone (PDB) and it proposes solubility-improving sequences for it.

**Access:** Clone ProteinMPNN or LigandMPNN
(`github.com/dauparas/ProteinMPNN`, `github.com/dauparas/LigandMPNN`), download the weights,
and run the provided design script selecting the soluble model. There is no PyPI package; do
not `uv pip install soluble-mpnn`.

**Usage (conceptual):**
```python
# Pseudocode around the ProteinMPNN/LigandMPNN CLI. Actual invocation is a script call
# (e.g. `python run.py --pdb_path bb.pdb --model_name soluble_... --sampling_temp 0.1`),
# parsed from its FASTA output. Lower temperature = more conservative redesign.
def optimize_for_solubility(structure_pdb, num_variants=10, temperature=0.1):
    """Redesign a backbone for solubility with the soluble ProteinMPNN weights.

    Returns proposed sequences for the given structure. Requires a backbone (PDB);
    SolubleMPNN is structure-conditioned and cannot run from sequence alone.
    """
    ...  # invoke the ProteinMPNN/LigandMPNN script, collect sampled sequences
```

**Design strategy:**
- **Conservative** (temperature=0.1): Minimal changes, safer
- **Moderate** (temperature=0.3): Balance between change and safety
- **Aggressive** (temperature=0.5): More mutations, higher risk

**When to use:**
- Primary tool for sequence optimization
- Default starting point for improving problematic sequences
- Generating diverse soluble variants

**Best practices:**
- Generate 10-50 variants per sequence
- Use structure information when available (improves accuracy)
- Validate key functional residues are preserved
- Test multiple temperature settings

### ESM (Evolutionary Scale Modeling) - Sequence Likelihood

**Purpose:** Assess how "natural" a protein sequence appears based on evolutionary patterns.

**Method:** Protein language model trained on millions of natural sequences.

**Usage:**
```python
# Install: uv pip install fair-esm
import torch
from esm import pretrained

def score_sequence_esm(sequence):
    """
    Calculate ESM likelihood score for sequence
    Higher scores indicate more natural/stable sequences
    """

    model, alphabet = pretrained.esm2_t33_650M_UR50D()
    batch_converter = alphabet.get_batch_converter()

    data = [("protein", sequence)]
    _, _, batch_tokens = batch_converter(data)

    with torch.no_grad():
        results = model(batch_tokens, repr_layers=[33])
        token_logprobs = results["logits"].log_softmax(dim=-1)

    # Calculate perplexity as sequence quality metric
    sequence_score = token_logprobs.mean().item()

    return sequence_score

# Example - Compare variants
sequences = {
    'original': 'MKVLW...',
    'optimized_1': 'MKVLS...',
    'optimized_2': 'MKVLA...'
}

for name, seq in sequences.items():
    score = score_sequence_esm(seq)
    print(f"{name}: ESM score = {score:.3f}")
```

**Interpretation:**
- Higher scores → More "natural" sequence
- Use to avoid unlikely mutations
- Balance with functional requirements

**When to use:**
- Filtering synthetic designs
- Comparing SolubleMPNN variants
- Ensuring sequences aren't too artificial
- Avoiding expression bottlenecks

**Integration with design:**
```python
def rank_variants_by_esm(variants):
    """Rank protein variants by ESM likelihood"""
    scored = []
    for v in variants:
        esm_score = score_sequence_esm(v['sequence'])
        v['esm_score'] = esm_score
        scored.append(v)

    # Sort by combined solubility and ESM score
    scored.sort(
        key=lambda x: x['solubility_score'] * x['esm_score'],
        reverse=True
    )

    return scored
```

### ipTM - Interface Stability (AlphaFold-Multimer)

**Purpose:** Assess protein-protein interface stability and binding confidence.

**Method:** Interface predicted TM-score from AlphaFold-Multimer predictions.

**Usage:**
```python
# Requires AlphaFold-Multimer installation
# Or use ColabFold for easier access

def predict_interface_stability(protein_a_seq, protein_b_seq):
    """
    Predict interface stability using AlphaFold-Multimer

    Returns ipTM score: higher = more stable interface
    """
    from colabfold import run_alphafold_multimer

    sequences = {
        'chainA': protein_a_seq,
        'chainB': protein_b_seq
    }

    result = run_alphafold_multimer(sequences)

    return {
        'ipTM': result['iptm'],
        'pTM': result['ptm'],
        'pLDDT': result['plddt']
    }

# Example for antibody-antigen binding
antibody_seq = "EVQLVESGGGLVQPGG..."
antigen_seq = "MKVLWAALLGLLGAAA..."

stability = predict_interface_stability(antibody_seq, antigen_seq)
print(f"Interface pTM: {stability['ipTM']:.3f}")

# Interpretation
if stability['ipTM'] > 0.7:
    print("High confidence interface")
elif stability['ipTM'] > 0.5:
    print("Moderate confidence interface")
else:
    print("Low confidence interface - may need redesign")
```

**Interpretation:**
- ipTM > 0.7: Strong predicted interface
- ipTM 0.5-0.7: Moderate interface confidence
- ipTM < 0.5: Weak interface, consider redesign

**When to use:**
- Antibody-antigen design
- Protein-protein interaction engineering
- Validating binding interfaces
- Comparing interface variants

### pSAE - Solvent-Accessible Hydrophobic Residues

**Purpose:** Quantify exposed hydrophobic residues that promote aggregation.

**Method:** Calculates percentage of solvent-accessible surface area (SASA) occupied by hydrophobic residues.

**Usage:**
```python
# Requires structure (PDB file or AlphaFold prediction)
# Install: uv pip install biopython

from Bio.PDB import PDBParser, DSSP
import numpy as np

def calculate_psae(pdb_file):
    """
    Calculate percent Solvent-Accessible hydrophobic residues (pSAE)

    Lower pSAE = better solubility
    """

    parser = PDBParser(QUIET=True)
    structure = parser.get_structure('protein', pdb_file)

    # Run DSSP to get solvent accessibility
    model = structure[0]
    dssp = DSSP(model, pdb_file, acc_array='Wilke')

    hydrophobic = ['ALA', 'VAL', 'ILE', 'LEU', 'MET', 'PHE', 'TRP', 'PRO']

    total_sasa = 0
    hydrophobic_sasa = 0

    for residue in dssp:
        res_name = residue[1]
        rel_accessibility = residue[3]

        total_sasa += rel_accessibility
        if res_name in hydrophobic:
            hydrophobic_sasa += rel_accessibility

    psae = (hydrophobic_sasa / total_sasa) * 100

    return psae

# Example
pdb_file = "protein_structure.pdb"
psae_score = calculate_psae(pdb_file)
print(f"pSAE: {psae_score:.2f}%")

# Interpretation
if psae_score < 25:
    print("Good solubility expected")
elif psae_score < 35:
    print("Moderate solubility")
else:
    print("High aggregation risk")
```

**Interpretation:**
- pSAE < 25%: Low aggregation risk
- pSAE 25-35%: Moderate risk
- pSAE > 35%: High aggregation risk

**When to use:**
- Analyzing designed structures
- Post-AlphaFold validation
- Identifying aggregation hotspots
- Guiding surface mutations

## Recommended Optimization Workflow

The functions below are **pseudocode** that stitch the tools above into a pipeline. The
helper calls (`predict_solubility_netsolp`, `predict_solubility`, `optimize_sequence`,
`predict_structure_alphafold`) stand in for whatever access each tool actually provides (web
service, cloned repo CLI, or local model) — they are not importable packages. Wire them up to
the real tools before running.

### Step 1: Initial Screening (Fast)

```python
def initial_screening(sequences):
    """
    Quick first-pass filtering using NetSolP
    Filters out obviously problematic sequences
    """
    passed = []
    for name, seq in sequences.items():
        netsolp_score = predict_solubility_netsolp(seq)
        if netsolp_score > 0.5:
            passed.append((name, seq))

    return passed
```

### Step 2: Detailed Assessment (Moderate)

```python
def detailed_assessment(filtered_sequences):
    """
    More thorough analysis with SoluProt and ESM
    Ranks sequences by multiple criteria
    """
    results = []
    for name, seq in filtered_sequences:
        soluprot_score = predict_solubility(seq)
        esm_score = score_sequence_esm(seq)

        combined_score = soluprot_score * 0.7 + esm_score * 0.3

        results.append({
            'name': name,
            'sequence': seq,
            'soluprot': soluprot_score,
            'esm': esm_score,
            'combined': combined_score
        })

    results.sort(key=lambda x: x['combined'], reverse=True)
    return results
```

### Step 3: Sequence Optimization (If needed)

```python
def optimize_problematic_sequences(sequences_needing_optimization):
    """
    Use SolubleMPNN to redesign problematic sequences
    Returns improved variants
    """
    optimized = []
    for name, seq in sequences_needing_optimization:
        # Generate multiple variants
        variants = optimize_sequence(
            sequence=seq,
            num_variants=10,
            temperature=0.2
        )

        # Score variants with ESM
        for variant in variants:
            variant['esm_score'] = score_sequence_esm(variant['sequence'])

        # Keep best variants
        variants.sort(
            key=lambda x: x['solubility_score'] * x['esm_score'],
            reverse=True
        )

        optimized.extend(variants[:3])  # Top 3 variants per sequence

    return optimized
```

### Step 4: Structure-Based Validation (For critical sequences)

```python
def structure_validation(top_candidates):
    """
    Predict structures and calculate pSAE for top candidates
    Final validation before experimental testing
    """
    validated = []
    for candidate in top_candidates:
        # Predict structure with AlphaFold
        structure_pdb = predict_structure_alphafold(candidate['sequence'])

        # Calculate pSAE
        psae = calculate_psae(structure_pdb)

        candidate['psae'] = psae
        candidate['pass_structure_check'] = psae < 30

        validated.append(candidate)

    return validated
```

### Complete Workflow Example

```python
def complete_optimization_pipeline(initial_sequences):
    """
    End-to-end optimization pipeline

    Input: Dictionary of {name: sequence}
    Output: Ranked list of optimized, validated sequences
    """

    print("Step 1: Initial screening with NetSolP...")
    filtered = initial_screening(initial_sequences)
    print(f"  Passed: {len(filtered)}/{len(initial_sequences)}")

    print("Step 2: Detailed assessment with SoluProt and ESM...")
    assessed = detailed_assessment(filtered)

    # Split into good and needs-optimization
    good_sequences = [s for s in assessed if s['soluprot'] > 0.6]
    needs_optimization = [s for s in assessed if s['soluprot'] <= 0.6]

    print(f"  Good sequences: {len(good_sequences)}")
    print(f"  Need optimization: {len(needs_optimization)}")

    if needs_optimization:
        print("Step 3: Optimizing problematic sequences with SolubleMPNN...")
        optimized = optimize_problematic_sequences(needs_optimization)
        all_sequences = good_sequences + optimized
    else:
        all_sequences = good_sequences

    print("Step 4: Structure-based validation for top candidates...")
    top_20 = all_sequences[:20]
    final_validated = structure_validation(top_20)

    # Final ranking
    final_validated.sort(
        key=lambda x: (
            x['pass_structure_check'],
            x['combined'],
            -x['psae']
        ),
        reverse=True
    )

    return final_validated

# Usage
initial_library = {
    'variant_1': 'MKVLWAALLGLLGAAA...',
    'variant_2': 'MATGVLWAALLGLLGA...',
    # ... more sequences
}

optimized_library = complete_optimization_pipeline(initial_library)

# Submit top sequences to Adaptyv
top_sequences_for_testing = optimized_library[:50]
```

## Best Practices Summary

1. **Always pre-screen** before experimental testing
2. **Use NetSolP first** for fast filtering of large libraries
3. **Apply SolubleMPNN** as default optimization tool
4. **Validate with ESM** to avoid unnatural sequences
5. **Calculate pSAE** for structure-based validation
6. **Test multiple variants** per design to account for prediction uncertainty
7. **Keep controls** - include wild-type or known-good sequences
8. **Iterate** - use experimental results to refine predictions

## Integration with Adaptyv

After computational optimization, submit the top sequences to the Foundry API. The API takes
a `{label: sequence}` map inside `experiment_spec` (not a FASTA blob) and uses a draft → submit
flow — see `reference/api_reference.md` and `reference/examples.md`.

```python
import os, requests

# After optimization pipeline
optimized_sequences = complete_optimization_pipeline(initial_library)

# Build the {label: sequence} map for the top candidates
sequences = {s["name"]: s["sequence"] for s in optimized_sequences[:50]}

base_url = "https://foundry-api-public.adaptyvbio.com/api/v1"
headers = {"Authorization": f"Bearer {os.environ['ADAPTYV_API_KEY']}",
           "Content-Type": "application/json"}

# Create a draft expression experiment (no target needed for expression)
resp = requests.post(f"{base_url}/experiments", headers=headers, json={
    "name": "SolubleMPNN_ESM_pipeline top 50",
    "experiment_spec": {"experiment_type": "expression", "sequences": sequences},
})
resp.raise_for_status()
exp_id = resp.json()["experiment_id"]

# Review the quote, then submit
requests.post(f"{base_url}/experiments/{exp_id}/submit", headers=headers).raise_for_status()
```

## Troubleshooting

**Issue: All sequences score poorly on solubility predictions**
- Check if sequences contain unusual amino acids
- Verify FASTA format is correct
- Consider if protein family is naturally low-solubility
- May need experimental validation despite predictions

**Issue: SolubleMPNN changes functionally important residues**
- Provide structure file to preserve spatial constraints
- Mask critical residues from mutation
- Lower temperature parameter for conservative changes
- Manually revert problematic mutations

**Issue: ESM scores are low after optimization**
- Optimization may be too aggressive
- Try lower temperature in SolubleMPNN
- Balance between solubility and naturalness
- Consider that some optimization may require non-natural mutations

**Issue: Predictions don't match experimental results**
- Predictions are probabilistic, not deterministic
- Host system and conditions affect expression
- Some proteins may need experimental validation
- Use predictions as enrichment, not absolute filters
