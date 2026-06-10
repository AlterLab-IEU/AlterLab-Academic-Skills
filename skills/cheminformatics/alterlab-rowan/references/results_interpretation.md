# Rowan Results Interpretation Reference

## Table of Contents

1. [Accessing Workflow Results](#accessing-workflow-results)
2. [Property Prediction Results](#property-prediction-results)
3. [Molecular Modeling Results](#molecular-modeling-results)
4. [Docking Results](#docking-results)
5. [Cofolding Results](#cofolding-results)
6. [Validation and Quality Assessment](#validation-and-quality-assessment)

---

## Accessing Workflow Results

### Basic Pattern

Use `workflow.result()` — it blocks, fetches, and returns a typed `WorkflowResult` with attribute access. It raises `rowan.WorkflowError` on failure, so you usually do not check status by hand.

```python
import rowan

workflow = rowan.submit_pka_workflow("c1ccccc1O", name="test")

try:
    result = workflow.result()        # blocks until done; raises on failure/stop
    print(result.strongest_acid)      # typed attribute, NOT workflow.data['...']
except rowan.WorkflowError as e:
    print(f"Failed: {e}")             # see workflow.logfile for details
```

> The raw `workflow.data` dict still exists, but field names there are not stable across workflow types — prefer the typed `result` object below. Each result object also exposes `.data` (the raw dict) if you need it.

### Workflow Status Values

`workflow.status` is the integer enum `stjames.Status` (use `.name` for a label, `workflow.done()` for a finished check):

| Status | Value | Description |
|--------|-------|-------------|
| `QUEUED` | 0 | Queued, waiting for resources |
| `RUNNING` | 1 | Currently executing |
| `COMPLETED_OK` | 2 | Successfully finished |
| `FAILED` | 3 | Execution failed |
| `STOPPED` | 4 | Manually stopped |
| `AWAITING_QUEUE` | 5 | Waiting to enter the queue |
| `DRAFT` | 6 | Submitted as a draft (call `submit_draft()`) |
| `PREEMPTED` | 7 | Preempted by the scheduler |

### Credits Charged

```python
# After completion
print(f"Credits used: {workflow.credits_charged}")
```

---

## Property Prediction Results

### pKa Results

```python
workflow = rowan.submit_pka_workflow("c1ccccc1O", name="pKa")
result = workflow.result()                 # pKaResult

strongest_acid = result.strongest_acid     # most acidic pKa
strongest_base = result.strongest_base     # most basic pKa (if applicable)

# Protonation states found
for microstate in result.conjugate_acids:
    print("conjugate acid:", microstate)
for microstate in result.conjugate_bases:
    print("conjugate base:", microstate)
```

For macroscopic pKa / pH-dependent speciation, use `submit_macropka_workflow` and read `result.pka_values`, `result.microstates`, `result.microstate_weights_by_ph`, and `result.isoelectric_point`.

**Interpretation:**
- pKa < 0: Strong acid
- pKa 0-7: Acidic
- pKa 7-14: Basic
- pKa > 14: Very weak acid

---

### Redox Potential Results

```python
result = workflow.result()             # RedoxPotentialResult

print(f"Oxidation: {result.oxidation_potential} V")
print(f"Reduction: {result.reduction_potential} V")
```

**Interpretation:**
- Higher oxidation potential = harder to oxidize
- Lower reduction potential = harder to reduce
- Compare to reference compounds for context

---

### Solubility Results

```python
result = workflow.result()             # SolubilityResult

# result.solubilities holds the predicted solubility entries
# (per solvent / temperature, as log S in mol/L)
for entry in result.solubilities:
    print(entry)
```

**Interpretation:**
- Log S > -1: High solubility (>0.1 M)
- Log S -1 to -3: Medium solubility
- Log S < -3: Low solubility (<0.001 M)

---

### Fukui Index Results

```python
result = workflow.result()             # FukuiResult

f_plus = result.fukui_positive   # f+ : susceptibility to nucleophilic attack (per atom)
f_minus = result.fukui_negative  # f- : susceptibility to electrophilic attack (per atom)
f_zero = result.fukui_zero       # f0 : radical attack (per atom)
print(f"Global electrophilicity index: {result.global_electrophilicity_index}")

for i, (fp, fm, fz) in enumerate(zip(f_plus, f_minus, f_zero)):
    print(f"Atom {i}: f+ = {fp:.3f}, f- = {fm:.3f}, f0 = {fz:.3f}")
```

**Interpretation:**
- High f+ = susceptible to nucleophilic attack
- High f- = susceptible to electrophilic attack
- High f0 = susceptible to radical attack

---

## Molecular Modeling Results

### Geometry Optimization Results

```python
result = workflow.result()             # BasicCalculationResult

final_mol = result.molecule            # stjames.Molecule with optimized coords
final_energy = result.energy           # Hartree
print(f"Final energy: {final_energy:.6f} Hartree")

# Also available: result.molecules (all steps), result.dipole, result.charges,
# result.frequencies (if a frequencies task was requested),
# result.optimization_energies() (energy at each optimization step)
```

---

### Conformer Search Results

```python
result = workflow.result()             # ConformerSearchResult

energies = result.get_energies()       # relative energies (kcal/mol), ascending
print(f"Found {result.num_conformers} conformers")

for i, rel_energy in enumerate(energies):
    print(f"Conformer {i}: ΔE = {rel_energy:.2f} kcal/mol")

conformers = result.get_conformers()   # list of stjames.Molecule
lowest = result.get_conformer(0)       # lowest-energy conformer
# Also: result.sasa, result.polar_sasa, result.radii_of_gyration
```

**Interpretation:**
- Conformers within 3 kcal/mol are typically accessible at room temperature
- Lowest energy conformer may not be most populated in solution
- Consider ensemble averaging for properties

---

### Frequency Calculation Results

Run with `tasks=["optimize", "frequencies"]` (or `["frequencies"]`). The typed `BasicCalculationResult` exposes the frequencies and a molecule carrying thermochemistry.

```python
result = workflow.result()             # BasicCalculationResult

frequencies = result.frequencies       # cm⁻¹ (negative values = imaginary modes)
mol = result.molecule

# Check for imaginary frequencies
imaginary = [f for f in frequencies if f < 0]
if imaginary:
    print(f"Warning: {len(imaginary)} imaginary frequency/frequencies")
else:
    print("Structure is a true minimum")

# Thermochemistry lives on the molecule (Hartree)
print(f"ZPE: {mol.zero_point_energy}")
print(f"Gibbs free energy: {mol.gibbs_free_energy}")
```

**Interpretation:**
- 0 imaginary frequencies = minimum
- 1 imaginary frequency = transition state
- >1 imaginary frequencies = higher-order saddle point

---

### Scan Results

A coordinate/dihedral scan is submitted with `rowan.submit_scan_workflow(...)`. Read the per-point energies from the result; the raw points live in `result.data`. Convert relative energies to kcal/mol with the factor below to find the rotation barrier.

```python
result = workflow.result()             # ScanResult
data = result.data                     # raw scan points (angles + energies, Hartree)
```

---

## Docking Results

### Single Docking Results

```python
result = workflow.result()             # DockingResult

# result.scores is a list of DockingScore (sorted best-first)
best = result.scores[0]
print(f"Best docking score: {best.score:.2f} kcal/mol")   # more negative = better
print(f"Ligand strain: {best.strain} kcal/mol")
print(f"RMSD: {best.rmsd}, PoseBusters valid: {best.posebusters_valid}")

for i, s in enumerate(result.scores):
    print(f"Pose {i}: score = {s.score:.2f} kcal/mol")

# Top pose / all poses as structures
best_pose = result.best_pose           # stjames.Molecule
all_poses = result.get_poses()         # list of stjames.Molecule
```

**Interpretation:**
- Vina scores typically -12 to -6 kcal/mol for drug-like molecules
- More negative = stronger predicted binding
- Ligand strain > 3 kcal/mol suggests unlikely binding mode

---

### Batch Docking Results

`submit_batch_docking_workflow` returns a single workflow whose result (`BatchDockingResult`) exposes `result.scores` for the screened library. Each entry carries the same `DockingScore` fields shown above (`score`, `strain`, `rmsd`, `posebusters_valid`); rank ligands by their best score. Use `result.data` for the full raw aggregation.

**Scoring Function Differences:**
- **Vina**: Original scoring function
- **Vinardo**: Updated parameters, often more accurate

---

## Cofolding Results

### Protein-Ligand Complex Prediction

```python
result = workflow.result()             # ProteinCofoldingResult

# One CofoldingResult per sample; take the first
top = result.predictions[0]
print(f"pTM: {top.scores.ptm:.3f}")          # predicted TM score (0-1)
print(f"interface pTM: {top.scores.iptm:.3f}")
print(f"avg LDDT: {top.scores.avg_lddt}")
print(f"PoseBusters valid: {top.posebusters_valid}")

# Binding-affinity prediction (if computed via ligand_binding_affinity_index)
if result.affinity_score:
    print(f"Affinity pred_value: {result.affinity_score.pred_value}")

# Predicted structures are stored by UUID; download via the workflow
predicted_uuid = top.predicted_structure_uuid
```

> The score attributes are `scores.ptm` and `scores.iptm` (not `ptm_score` / `interface_ptm`). `result.scores` gives the aggregate scores; `result.predictions` gives per-sample results.

**Confidence Score Interpretation:**

| Score Range | Confidence | Recommendation |
|-------------|------------|----------------|
| > 0.8 | High | Likely accurate |
| 0.5 - 0.8 | Moderate | Use with caution |
| < 0.5 | Low | Validate experimentally |

---

### Interpreting Low Confidence

Low confidence may indicate:
- Novel protein fold not well-represented in training data
- Flexible or disordered regions
- Unusual ligand (large, charged, or complex)
- Multiple possible binding modes

**Recommendations for low confidence:**
1. Try multiple models (Chai-1, Boltz-1, Boltz-2)
2. Compare predictions across models
3. Use docking for binding pose refinement
4. Validate with experimental data if available

---

## Validation and Quality Assessment

### Cross-Validation with Multiple Methods

```python
import rowan

energies = {}
for method in ["gfn2_xtb", "aimnet2_wb97md3"]:
    wf = rowan.submit_basic_calculation_workflow(
        "c1ccccc1O",
        tasks=["optimize"],
        method=method,
        name=f"opt_{method}",
    )
    energies[method] = wf.result().energy

for method, energy in energies.items():
    print(f"{method}: {energy:.6f} Hartree")
```

### Consistency Checks

```python
# For pKa (pass a pKaResult)
def validate_pka(result):
    pka = result.strongest_acid
    if pka is not None and (pka < -5 or pka > 20):
        print("Warning: pKa outside typical range")

# For docking (pass a DockingResult)
def validate_docking(result):
    best = result.scores[0]
    if best.score > 0:
        print("Warning: Positive docking score suggests poor binding")
    if best.strain and best.strain > 5:
        print("Warning: High ligand strain - binding mode may be unrealistic")
```

### Experimental Validation Guidelines

| Property | Validation Method |
|----------|-------------------|
| pKa | Potentiometric titration, UV spectroscopy |
| Solubility | Shake-flask, nephelometry |
| Docking pose | X-ray crystallography, cryo-EM |
| Binding affinity | SPR, ITC, fluorescence polarization |
| Cofolding | X-ray, NMR, HDX-MS |

---

## Common Issues and Solutions

### Issue: Workflow Failed

```python
import stjames

if workflow.status == stjames.Status.FAILED:
    print(workflow.logfile)   # diagnostic log; there is no workflow.error_message

    # Common causes:
    # - Invalid SMILES
    # - Molecule too large
    # - Convergence failure
    # - Credit limit exceeded
```

(`workflow.result()` raises `rowan.WorkflowError` for failed/stopped workflows, so wrapping it in try/except is usually simpler than checking status.)

### Issue: Unexpected Results

1. **pKa off by >2 units**: Check tautomers, ensure correct protonation state
2. **Docking gives positive scores**: Ligand may not fit binding site
3. **Optimization not converged**: Try different starting geometry
4. **High strain energy**: Conformer may be wrong

### Issue: Missing Attributes

```python
# Typed result attributes may be None when not computed
energy = getattr(result, "energy", None)
if energy is None:
    print("Energy not available")
```

---

## Data Export Patterns

### Export to CSV

```python
import pandas as pd
import rowan

rows = []
for wf in workflows:
    try:
        result = wf.result(wait=False)   # don't block on still-running jobs
    except rowan.WorkflowError:
        continue
    rows.append({
        "name": wf.name,
        "pka": result.strongest_acid,
        "credits": wf.credits_charged,
    })

pd.DataFrame(rows).to_csv("results.csv", index=False)
```

### Export Structures

```python
# Poses come back as stjames.Molecule objects you can write to XYZ
result = docking_workflow.result()
result.best_pose.to_xyz(out_file="best_pose.xyz")

# Download MD trajectory files (for MD workflows)
workflow.download_dcd_files(output_dir="trajectories/")
```
