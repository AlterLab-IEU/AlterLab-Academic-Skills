---
name: alterlab-qiskit
description: Builds, transpiles, and runs quantum circuits with Qiskit, IBM's quantum computing framework, including Qiskit Runtime primitives (Sampler/Estimator), circuit transpilation, and error mitigation on IBM Quantum hardware. Use when targeting IBM Quantum backends, transpiling circuits, running Runtime sessions or batches, or applying resilience/error mitigation. For Google Quantum AI hardware and NISQ circuits prefer alterlab-cirq; for gradient-trained quantum ML and hybrid quantum-classical models prefer alterlab-pennylane; for open-system Lindblad/master-equation dynamics prefer alterlab-qutip. Part of the AlterLab Academic Skills suite.
license: Apache-2.0
allowed-tools: Read Write Edit Bash(python:*)
compatibility: No API key required for local simulation. Runs via `uv run python`; requires the qiskit Python package. IBM Quantum hardware/Runtime needs an IBM Quantum account and API token.
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# Qiskit

## Overview

Qiskit is an open-source quantum computing framework. Build quantum circuits, optimize for hardware, execute on simulators or real quantum computers, and analyze results. Supports IBM Quantum (100+ qubit Heron and Nighthawk systems), IonQ, Amazon Braket, and other providers.

**Version note:** Examples target Qiskit SDK 2.x (`qiskit>=2,<3`, Python 3.10+; current 2.5.x as of 2026-09) and `qiskit-ibm-runtime` ≥ 0.40 (current 0.49). Older tutorials break on these changes, so check any snippet you adapt against them:
- **Qiskit 1.0 removed** `execute()`, `BasicAer`, `qiskit.tools` (incl. `tools.jupyter`, `job_monitor`) and `bind_parameters` — use primitives, `qiskit.providers.basic_provider.BasicSimulator`, and `assign_parameters`.
- **Qiskit 2.0 removed** `qiskit.pulse`, `BackendV1`, the V1 reference primitives (`qiskit.primitives.Sampler`/`Estimator`) and `Instruction.c_if` (use `with qc.if_test(...)`).
- **Qiskit 2.1 deprecated** the class forms of library circuits (`RealAmplitudes`, `EfficientSU2`, `TwoLocal`, `ZZFeatureMap`, `QFT`, …; removal in 3.0) — use `real_amplitudes()`, `efficient_su2()`, `n_local()`, `zz_feature_map()`, `QFTGate`.
- **Runtime V2 primitives** take `mode=` (a backend, `Session`, or `Batch`); the old `session=`/`backend=` keywords raise `TypeError`. The `Options` class and `channel="ibm_quantum"` are gone — the platform is now quantum.cloud.ibm.com (API key + instance CRN, channel `"ibm_quantum_platform"`).

## When to Use This Skill

Use this skill when the user wants to:
- Build, transpile, and run gate-model circuits on IBM Quantum hardware or local simulators
- Use Qiskit Runtime primitives (SamplerV2 / EstimatorV2) in job, batch, or session mode
- Apply error suppression/mitigation (twirling, dynamical decoupling, TREX, ZNE)
- Run variational or textbook algorithms (VQE, QAOA, Grover, QPE) with the Qiskit ecosystem (Nature, Machine Learning, Optimization)

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Google Quantum AI processors, Cirq-native circuits, or XEB/RB characterization in Cirq | `alterlab-cirq` |
| Gradient-trained hybrid quantum-classical models with PyTorch/JAX autodiff | `alterlab-pennylane` |
| Open-system dynamics — Lindblad master equations, decoherence, cavity QED | `alterlab-qutip` |
| Classical quantum-chemistry (DFT, conformers, pKa) with no quantum circuits | `alterlab-rowan` |

**Key Features:**
- Configurable transpilation with multiple optimization levels
- Circuit optimization that reduces two-qubit gate counts
- Backend-agnostic execution (local simulators or cloud hardware)
- Comprehensive algorithm libraries for optimization, chemistry, and ML

## Quick Start

### Installation

```bash
uv pip install "qiskit>=2,<3"
uv pip install "qiskit[visualization]" matplotlib   # circuit/result plotting
uv pip install qiskit-ibm-runtime                   # IBM hardware + Runtime primitives
```

### First Circuit

```python
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

# Create Bell state (entangled qubits)
qc = QuantumCircuit(2)
qc.h(0)           # Hadamard on qubit 0
qc.cx(0, 1)       # CNOT from qubit 0 to 1
qc.measure_all()  # Measure both qubits

# Run locally
sampler = StatevectorSampler()
result = sampler.run([qc], shots=1024).result()
counts = result[0].data.meas.get_counts()
print(counts)  # {'00': ~512, '11': ~512}
```

### Visualization

```python
from qiskit.visualization import plot_histogram

qc.draw('mpl')           # Circuit diagram
plot_histogram(counts)   # Results histogram
```

## Core Capabilities

### 1. Setup and Installation
For detailed installation, authentication, and IBM Quantum account setup:
- **See `references/setup.md`**

Topics covered:
- Installation with uv
- Python environment setup
- IBM Quantum account and API token configuration
- Local vs. cloud execution

### 2. Building Quantum Circuits
For constructing quantum circuits with gates, measurements, and composition:
- **See `references/circuits.md`**

Topics covered:
- Creating circuits with QuantumCircuit
- Single-qubit gates (H, X, Y, Z, rotations, phase gates)
- Multi-qubit gates (CNOT, SWAP, Toffoli)
- Measurements and barriers
- Circuit composition and properties
- Parameterized circuits for variational algorithms

### 3. Primitives (Sampler and Estimator)
For executing quantum circuits and computing results:
- **See `references/primitives.md`**

Topics covered:
- **Sampler**: Get bitstring measurements and probability distributions
- **Estimator**: Compute expectation values of observables
- V2 interface (StatevectorSampler, StatevectorEstimator)
- IBM Quantum Runtime primitives for hardware
- Sessions and Batch modes
- Parameter binding

### 4. Transpilation and Optimization
For optimizing circuits and preparing for hardware execution:
- **See `references/transpilation.md`**

Topics covered:
- Why transpilation is necessary
- Optimization levels (0-3)
- Six transpilation stages (init, layout, routing, translation, optimization, scheduling)
- Advanced features (virtual permutation elision, gate cancellation)
- Common parameters (initial_layout, approximation_degree, seed)
- Best practices for efficient circuits

### 5. Visualization
For displaying circuits, results, and quantum states:
- **See `references/visualization.md`**

Topics covered:
- Circuit drawings (text, matplotlib, LaTeX)
- Result histograms
- Quantum state visualization (Bloch sphere, state city, QSphere)
- Backend topology and error maps
- Customization and styling
- Saving publication-quality figures

### 6. Hardware Backends
For running on simulators and real quantum computers:
- **See `references/backends.md`**

Topics covered:
- IBM Quantum backends and authentication
- Backend properties and status
- Running on real hardware with Runtime primitives
- Job management and queuing
- Session mode (iterative algorithms)
- Batch mode (parallel jobs)
- Local simulators (StatevectorSampler, Aer)
- Third-party providers (IonQ, Amazon Braket)
- Error mitigation strategies

### 7. Qiskit Patterns Workflow
For implementing the four-step quantum computing workflow:
- **See `references/patterns.md`**

Topics covered:
- **Map**: Translate problems to quantum circuits
- **Optimize**: Transpile for hardware
- **Execute**: Run with primitives
- **Post-process**: Extract and analyze results
- Complete VQE example
- Session vs. Batch execution
- Common workflow patterns

### 8. Quantum Algorithms and Applications
For implementing specific quantum algorithms:
- **See `references/algorithms.md`**

Topics covered:
- **Optimization**: VQE, QAOA, Grover's algorithm
- **Chemistry**: Molecular ground states, excited states, Hamiltonians
- **Machine Learning**: Quantum kernels, VQC, QNN
- **Algorithm libraries**: Qiskit Nature, Qiskit ML, Qiskit Optimization
- Physics simulations and benchmarking

## Workflow Decision Guide

**If you need to:**

- Install Qiskit or set up IBM Quantum account → `references/setup.md`
- Build a new quantum circuit → `references/circuits.md`
- Understand gates and circuit operations → `references/circuits.md`
- Run circuits and get measurements → `references/primitives.md`
- Compute expectation values → `references/primitives.md`
- Optimize circuits for hardware → `references/transpilation.md`
- Visualize circuits or results → `references/visualization.md`
- Execute on IBM Quantum hardware → `references/backends.md`
- Connect to third-party providers → `references/backends.md`
- Implement end-to-end quantum workflow → `references/patterns.md`
- Build specific algorithm (VQE, QAOA, etc.) → `references/algorithms.md`
- Solve chemistry or optimization problems → `references/algorithms.md`

## Best Practices

### Development Workflow

1. **Start with simulators**: Test locally before using hardware
   ```python
   from qiskit.primitives import StatevectorSampler
   sampler = StatevectorSampler()
   ```

2. **Always transpile**: Optimize circuits before execution
   ```python
   from qiskit import transpile
   qc_optimized = transpile(qc, backend=backend, optimization_level=3)
   ```

3. **Use appropriate primitives**:
   - Sampler for bitstrings (optimization algorithms)
   - Estimator for expectation values (chemistry, physics)

4. **Choose execution mode**:
   - Session: Iterative algorithms (VQE, QAOA)
   - Batch: Independent parallel jobs
   - Single job: One-off experiments

### Performance Optimization

- Use optimization_level=3 for production
- Minimize two-qubit gates (major error source)
- Test with noisy simulators before hardware
- Save and reuse transpiled circuits
- Monitor convergence in variational algorithms

### Hardware Execution

- Check backend status before submitting
- Use `least_busy()` or list `service.backends()` rather than hard-coding a QPU name — QPUs are retired over time (all 127-qubit Eagle systems, e.g. `ibm_brisbane`, are gone)
- Session mode needs a paid plan; Open Plan users run in job or batch mode
- Save job IDs for later retrieval
- Apply error mitigation — `resilience_level` on the **Estimator** (Sampler has no `resilience_level`; use `twirling` / `dynamical_decoupling`)
- Start with fewer shots, increase for final runs

## Common Patterns

### Pattern 1: Simple Circuit Execution

```python
from qiskit import QuantumCircuit, transpile
from qiskit.primitives import StatevectorSampler

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

sampler = StatevectorSampler()
result = sampler.run([qc], shots=1024).result()
counts = result[0].data.meas.get_counts()
```

### Pattern 2: Hardware Execution with Transpilation

```python
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit.transpiler import generate_preset_pass_manager

service = QiskitRuntimeService()
backend = service.least_busy(operational=True, simulator=False)

# Hardware only accepts ISA circuits (native gates + connectivity)
pm = generate_preset_pass_manager(backend=backend, optimization_level=3)
qc_isa = pm.run(qc)

sampler = Sampler(mode=backend)          # job mode; pass a Session/Batch for other modes
job = sampler.run([qc_isa], shots=1024)
counts = job.result()[0].data.meas.get_counts()
```

### Pattern 3: Variational Algorithm (VQE)

```python
from qiskit_ibm_runtime import Session, EstimatorV2 as Estimator
from scipy.optimize import minimize

# Transpile once, then lay the observable out on the same physical qubits —
# an un-mapped observable does not match the ISA circuit's width.
ansatz_isa = pm.run(ansatz)
hamiltonian_isa = hamiltonian.apply_layout(ansatz_isa.layout)

with Session(backend=backend) as session:      # paid plans; use Batch on the Open Plan
    estimator = Estimator(mode=session)

    def cost_function(params):
        # parameter values travel in the PUB — no re-transpiling per iteration
        result = estimator.run([(ansatz_isa, hamiltonian_isa, params)]).result()
        return float(result[0].data.evs)

    result = minimize(cost_function, initial_params, method='COBYLA')
```

## Additional Resources

- **Official Docs**: https://quantum.cloud.ibm.com/docs
- **IBM Quantum Learning** (successor to the Qiskit Textbook): https://quantum.cloud.ibm.com/learning
- **API Reference**: https://quantum.cloud.ibm.com/docs/en/api/qiskit
- **Patterns Guide**: https://quantum.cloud.ibm.com/docs/en/guides/intro-to-patterns
- **Community packages**: [Nature](https://qiskit-community.github.io/qiskit-nature/), [Machine Learning](https://qiskit-community.github.io/qiskit-machine-learning/), [Optimization](https://qiskit-community.github.io/qiskit-optimization/)

Part of the AlterLab Academic Skills suite.

