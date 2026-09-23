---
name: alterlab-pennylane
description: Trains and differentiates quantum circuits with PennyLane, a hardware-agnostic quantum machine-learning framework with automatic differentiation and PyTorch/JAX integration. Use when training quantum circuits via gradients (parameter-shift, backprop, adjoint), building hybrid quantum-classical models or quantum neural networks, or running differentiable variational algorithms (VQE, QAOA). For IBM Quantum hardware and Qiskit Runtime prefer alterlab-qiskit; for Google Quantum AI or NISQ circuits prefer alterlab-cirq; for open-system Lindblad/master-equation dynamics prefer alterlab-qutip. Part of the AlterLab Academic Skills suite.
license: Apache-2.0
allowed-tools: Read Write Edit Bash(python:*)
compatibility: No API key required for local simulation. Runs via `uv run python`; requires the pennylane Python package. Remote hardware (IBM, IonQ, Rigetti) needs separate provider credentials.
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# PennyLane

## Overview

PennyLane is a quantum computing library that enables training quantum computers like neural networks. It provides automatic differentiation of quantum circuits, device-independent programming, and seamless integration with classical machine learning frameworks.

## When to Use This Skill

Use this skill when the user wants to:
- Differentiate and train parameterized circuits (parameter-shift, backprop, adjoint)
- Build hybrid quantum-classical models with PyTorch (`qml.qnn.TorchLayer`) or JAX
- Run differentiable VQE/QAOA or quantum-chemistry workflows (`qml.qchem`)
- Write device-agnostic circuits and swap simulators (default.qubit, lightning) for plugin hardware

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| IBM-specific transpilation, Runtime sessions/batches, or error-mitigation options | `alterlab-qiskit` |
| Google Quantum AI hardware, Cirq-native circuits, or XEB/RB characterization | `alterlab-cirq` |
| Lindblad master equations, decoherence, or cavity-QED dynamics | `alterlab-qutip` |
| Classical deep learning with no quantum circuit | `alterlab-pytorch-lightning` |

## Installation

Install using uv (PennyLane ≥ 0.43; current 0.45.x as of 2026-09 needs Python ≥ 3.11):

```bash
uv pip install pennylane
```

For quantum hardware access, install device plugins:

```bash
# IBM Quantum (0.45 pins qiskit<=2.3 and qiskit-ibm-runtime~=0.45 — use its own env
# if you also run the latest Qiskit directly)
uv pip install pennylane-qiskit

# Amazon Braket (IonQ, IQM, Rigetti, AQT QPUs and managed simulators)
uv pip install amazon-braket-pennylane-plugin

# Cirq simulators
uv pip install pennylane-cirq

# IonQ
uv pip install pennylane-ionq
```

`pennylane-rigetti` is unmaintained (pins `pyquil<4`, `networkx<3`); reach Rigetti QPUs
through Amazon Braket instead.

**Version notes (v0.42–0.45):** TensorFlow is gone (`qml.qnn.KerasLayer` removed in
v0.42, the `tf` interface dropped in v0.44), and shots belong on the QNode —
`@qml.qnode(dev, shots=1000)` or `qml.set_shots(qnode, shots=...)` — because
`qml.device(..., shots=...)` and call-time `circuit(x, shots=...)` are deprecated
since v0.43.

## Quick Start

Build a quantum circuit and optimize its parameters:

```python
import pennylane as qml
from pennylane import numpy as np

# Create device
dev = qml.device('default.qubit', wires=2)

# Define quantum circuit
@qml.qnode(dev)
def circuit(params):
    qml.RX(params[0], wires=0)
    qml.RY(params[1], wires=1)
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.PauliZ(0))

# Optimize parameters
opt = qml.GradientDescentOptimizer(stepsize=0.1)
params = np.array([0.1, 0.2], requires_grad=True)

for i in range(100):
    params = opt.step(circuit, params)
```

## Core Capabilities

New to PennyLane? See `references/getting_started.md` for installation, QNodes,
devices, gradients, and a first optimization loop.

### 1. Quantum Circuit Construction

Build circuits with gates, measurements, and state preparation. See `references/quantum_circuits.md` for:
- Single and multi-qubit gates
- Controlled operations and conditional logic
- Mid-circuit measurements and adaptive circuits
- Various measurement types (expectation, probability, samples)
- Circuit inspection and debugging

### 2. Quantum Machine Learning

Create hybrid quantum-classical models. See `references/quantum_ml.md` for:
- Integration with PyTorch and JAX (TensorFlow/Keras support ended in v0.44)
- Quantum neural networks and variational classifiers
- Data encoding strategies (angle, amplitude, basis, IQP)
- Training hybrid models with backpropagation
- Transfer learning with quantum circuits

### 3. Quantum Chemistry

Simulate molecules and compute ground state energies. See `references/quantum_chemistry.md` for:
- Molecular Hamiltonian generation
- Variational Quantum Eigensolver (VQE)
- UCCSD ansatz for chemistry
- Geometry optimization and dissociation curves
- Molecular property calculations

### 4. Device Management

Execute on simulators or quantum hardware. See `references/devices_backends.md` for:
- Built-in simulators (default.qubit, lightning.qubit, default.mixed)
- Hardware plugins (IBM, Amazon Braket, Google, Rigetti, IonQ)
- Device selection and configuration
- Performance optimization and caching
- GPU acceleration and JIT compilation

### 5. Optimization

Train quantum circuits with various optimizers. See `references/optimization.md` for:
- Built-in optimizers (Adam, gradient descent, momentum, RMSProp)
- Gradient computation methods (backprop, parameter-shift, adjoint)
- Variational algorithms (VQE, QAOA)
- Training strategies (learning rate schedules, mini-batches)
- Handling barren plateaus and local minima

### 6. Advanced Features

Leverage templates, transforms, and compilation. See `references/advanced_features.md` for:
- Circuit templates and layers
- Transforms and circuit optimization
- Pulse-level programming
- Catalyst JIT compilation
- Noise models and error mitigation
- Resource estimation

## Common Workflows

### Train a Variational Classifier

```python
# 1. Define ansatz
@qml.qnode(dev)
def classifier(x, weights):
    # Encode data
    qml.AngleEmbedding(x, wires=range(4))

    # Variational layers
    qml.StronglyEntanglingLayers(weights, wires=range(4))

    return qml.expval(qml.PauliZ(0))

# 2. Train
opt = qml.AdamOptimizer(stepsize=0.01)
weights = np.random.random((3, 4, 3))  # 3 layers, 4 wires

for epoch in range(100):
    for x, y in zip(X_train, y_train):
        weights = opt.step(lambda w: (classifier(x, w) - y)**2, weights)
```

### Run VQE for Molecular Ground State

```python
from pennylane import qchem

# 1. Build Hamiltonian (returns the qubit Hamiltonian and qubit count).
# Coordinates default to Bohr — state the unit, or H2 at "0.74" is badly compressed.
symbols = ['H', 'H']
coords = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.74])  # Å
mol = qchem.Molecule(symbols, coords, unit="angstrom")
H, n_qubits = qchem.molecular_hamiltonian(mol)

# 2. Set up UCCSD ansatz from the excitations
hf_state = qchem.hf_state(electrons=2, orbitals=n_qubits)
singles, doubles = qchem.excitations(electrons=2, orbitals=n_qubits)
s_wires, d_wires = qchem.excitations_to_wires(singles, doubles)

dev = qml.device('default.qubit', wires=n_qubits)

@qml.qnode(dev)
def vqe_circuit(params):
    qml.UCCSD(params, wires=range(n_qubits),
              s_wires=s_wires, d_wires=d_wires, init_state=hf_state)
    return qml.expval(H)

# 3. Optimize (one parameter per excitation)
opt = qml.AdamOptimizer(stepsize=0.1)
params = np.zeros(len(singles) + len(doubles), requires_grad=True)

for i in range(100):
    params, energy = opt.step_and_cost(vqe_circuit, params)
    print(f"Step {i}: Energy = {energy:.6f} Ha")
```

### Switch Between Devices

```python
# Define the circuit body once, bind it to a device on demand.
def circuit_body(params):
    qml.AngleEmbedding(params, wires=range(4))
    return qml.expval(qml.PauliZ(0))

def make_qnode(dev, shots=None):
    return qml.qnode(dev, shots=shots)(circuit_body)

# Test on simulator
dev_sim = qml.device('default.qubit', wires=4)
result_sim = make_qnode(dev_sim)(params)

# Run on quantum hardware (IBM, via Qiskit Runtime)
from qiskit_ibm_runtime import QiskitRuntimeService

service = QiskitRuntimeService(channel='ibm_quantum_platform')  # requires saved IBM Cloud credentials
backend = service.least_busy(operational=True, simulator=False)
dev_hw = qml.device('qiskit.remote', wires=4, backend=backend)
# Hardware needs finite shots; for gradients use diff_method='parameter-shift'.
result_hw = make_qnode(dev_hw, shots=1024)(params)
```

## Best Practices

1. **Start with simulators** - Test on `default.qubit` before deploying to hardware
2. **Use parameter-shift for hardware** - Backpropagation only works on simulators
3. **Set shots on the QNode** - `@qml.qnode(dev, shots=N)` or `qml.set_shots`; device-level shots are deprecated
4. **Choose appropriate encodings** - Match data encoding to problem structure
5. **Initialize carefully** - Use small random values to avoid barren plateaus
6. **Monitor gradients** - Check for vanishing gradients in deep circuits
7. **Cache devices** - Reuse device objects to reduce initialization overhead
8. **Profile circuits** - Use `qml.specs()` to analyze circuit complexity
9. **Test locally** - Validate on simulators before submitting to hardware
10. **Use templates** - Leverage built-in templates for common circuit patterns
11. **Compile when possible** - Use Catalyst JIT for performance-critical code

## Resources

- Official documentation: https://docs.pennylane.ai
- Codebook (tutorials): https://pennylane.ai/codebook
- QML demonstrations: https://pennylane.ai/demonstrations
- Community forum: https://discuss.pennylane.ai
- GitHub: https://github.com/PennyLaneAI/pennylane
- Deprecations and removals: https://docs.pennylane.ai/en/stable/development/deprecations.html

Part of the AlterLab Academic Skills suite.

