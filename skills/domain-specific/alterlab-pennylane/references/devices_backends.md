# Devices and Backends in PennyLane

## Table of Contents
1. [Built-in Simulators](#built-in-simulators)
2. [Hardware Plugins](#hardware-plugins)
3. [Device Selection](#device-selection)
4. [Device Configuration](#device-configuration)
5. [Custom Devices](#custom-devices)
6. [Performance Optimization](#performance-optimization)

## Built-in Simulators

### default.qubit

General-purpose state vector simulator:

```python
import pennylane as qml

# Basic initialization
dev = qml.device('default.qubit', wires=4)

# Sampling mode: put shots on the QNode, not the device — device-level shots are
# deprecated since v0.43:  @qml.qnode(dev, shots=1000)  or  qml.set_shots(qnode, shots=1000)

# Specify wire labels
dev = qml.device('default.qubit', wires=['a', 'b', 'c', 'd'])
```

### default.mixed

Mixed-state simulator for noisy quantum systems:

```python
# Supports density matrix simulation
dev = qml.device('default.mixed', wires=2)

@qml.qnode(dev)
def noisy_circuit():
    qml.Hadamard(wires=0)

    # Apply noise
    qml.DepolarizingChannel(0.1, wires=0)

    qml.CNOT(wires=[0, 1])

    # Amplitude damping
    qml.AmplitudeDamping(0.05, wires=1)

    return qml.expval(qml.PauliZ(0))
```

### ML framework integration

The separate `default.qubit.torch` / `.tf` / `.jax` devices were removed (v0.39), and
the TensorFlow interface itself was dropped in v0.44. Use a single `default.qubit`
device; the interface is auto-detected from the input types, or set it explicitly on
the QNode:

```python
dev = qml.device('default.qubit', wires=4)

@qml.qnode(dev, interface='torch')   # or 'jax', 'autograd' (default), 'auto'
def circuit(params):
    qml.RX(params[0], wires=0)
    return qml.expval(qml.PauliZ(0))
```

### lightning.qubit

High-performance C++ simulator:

```python
# Faster than default.qubit
dev = qml.device('lightning.qubit', wires=20)

# Supports larger systems efficiently
@qml.qnode(dev)
def large_circuit():
    for i in range(20):
        qml.Hadamard(wires=i)

    for i in range(19):
        qml.CNOT(wires=[i, i+1])

    return qml.expval(qml.PauliZ(0))
```

### default.clifford

Efficient simulator for Clifford circuits:

```python
# Only supports Clifford gates (H, S, CNOT, etc.)
dev = qml.device('default.clifford', wires=100)

@qml.qnode(dev)
def clifford_circuit():
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    qml.S(wires=1)
    # Cannot use RX, RY, RZ, etc.

    return qml.expval(qml.PauliZ(0))
```

## Hardware Plugins

### IBM Quantum (Qiskit)

```bash
# Install plugin. pennylane-qiskit 0.45 pins qiskit<=2.3 and qiskit-ibm-runtime~=0.45,
# so keep it in its own environment if you also use the latest Qiskit directly.
uv pip install pennylane-qiskit
```

```python
import pennylane as qml

# Use IBM simulator
dev = qml.device('qiskit.aer', wires=2)

# Use IBM quantum hardware (via Qiskit Runtime)
from qiskit_ibm_runtime import QiskitRuntimeService

service = QiskitRuntimeService(channel='ibm_quantum_platform')  # requires saved IBM Cloud credentials
backend = service.least_busy(operational=True, simulator=False)
dev = qml.device(
    'qiskit.remote',
    wires=2,
    backend=backend,  # pass a concrete backend object
)
# hardware needs finite shots: @qml.qnode(dev, shots=1024)

# With explicit token (instead of saved credentials)
service = QiskitRuntimeService(channel='ibm_quantum_platform', token='YOUR_API_TOKEN')
backend = service.backend('the_backend_name')
dev = qml.device(
    'qiskit.remote',
    wires=2,
    backend=backend,
)

@qml.qnode(dev)
def circuit():
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.PauliZ(0))
```

### Amazon Braket

```bash
# Install plugin
uv pip install amazon-braket-pennylane-plugin
```

```python
# Use Braket simulators
dev = qml.device(
    'braket.local.qubit',
    wires=2
)

# Use AWS simulators
dev = qml.device(
    'braket.aws.qubit',
    device_arn='arn:aws:braket:::device/quantum-simulator/amazon/sv1',
    wires=4,
    s3_destination_folder=('amazon-braket-outputs', 'outputs')
)

# Use quantum hardware. Braket QPUs change over time (IonQ Harmony/Aria and Rigetti
# Aspen are retired) — take current ARNs from the Braket console or docs, e.g.
#   arn:aws:braket:us-east-1::device/qpu/ionq/Forte-1
#   arn:aws:braket:us-west-1::device/qpu/rigetti/Ankaa-3
#   arn:aws:braket:eu-north-1::device/qpu/iqm/Garnet
dev = qml.device(
    'braket.aws.qubit',
    device_arn='arn:aws:braket:us-east-1::device/qpu/ionq/Forte-1',
    wires=4,
    s3_destination_folder=('amazon-braket-outputs', 'outputs')
)
# QPUs need finite shots on the QNode: @qml.qnode(dev, shots=1000)
```

### Google Cirq

```bash
# Install plugin
uv pip install pennylane-cirq
```

```python
# Use Cirq simulator
dev = qml.device('cirq.simulator', wires=2)

# Use Cirq with qsim (faster; needs `uv pip install qsimcirq`)
dev = qml.device('cirq.qsim', wires=20)
```

pennylane-cirq provides simulators (`cirq.simulator`, `cirq.mixedsimulator`, `cirq.qsim`)
and a Pasqal device model (`cirq.pasqal`); it has no Google-hardware device. For Google
Quantum AI processors or their Quantum Virtual Machine, work in Cirq directly.

### Rigetti

The `pennylane-rigetti` plugin is unmaintained (last release 0.40.0, Jan 2025; it pins
`pyquil<4` and `networkx<3`) and its Aspen QPUs are retired. Reach current Rigetti
systems (Ankaa-3, Cepheus-1-108Q) through the Amazon Braket plugin above.

### Microsoft Azure Quantum

There is no maintained PennyLane plugin for Azure Quantum (no `pennylane-azure`
package exists). Use IonQ directly via `pennylane-ionq`, go through Amazon Braket, or
submit Qiskit/Cirq circuits with the `azure-quantum` SDK.

### IonQ

```bash
# Install plugin
uv pip install pennylane-ionq
```

```python
# Use IonQ hardware
dev = qml.device(
    'ionq.simulator',  # or 'ionq.qpu'
    wires=11,
    api_key='your_api_key'
)
# @qml.qnode(dev, shots=1024)
```

### Xanadu photonic hardware

The Strawberry Fields stack (`strawberryfields` 0.23, 2022; `pennylane-sf`, which pins
`pennylane<0.30`) is no longer compatible with current PennyLane, so the old
`strawberryfields.remote` / Borealis device path does not work with v0.4x.

## Device Selection

### Choosing the Right Device

```python
def select_device(n_qubits, use_hardware=False, noise_model=None, ibm_backend=None):
    """Select appropriate device based on requirements."""

    if use_hardware:
        # Real hardware — remember to give the QNode finite shots
        if ibm_backend is not None and n_qubits <= ibm_backend.num_qubits:
            # ibm_backend is a concrete backend obtained from QiskitRuntimeService
            return qml.device('qiskit.remote', wires=n_qubits, backend=ibm_backend)
        return qml.device('ionq.qpu', wires=n_qubits)   # check the current IonQ system size

    elif noise_model:
        # Use noisy simulator
        return qml.device('default.mixed', wires=n_qubits)

    else:
        # Use ideal simulator
        if n_qubits <= 20:
            return qml.device('lightning.qubit', wires=n_qubits)
        else:
            return qml.device('default.qubit', wires=n_qubits)

# Usage
dev = select_device(n_qubits=10, use_hardware=False)
```

### Device Capabilities

```python
# Check device capabilities
dev = qml.device('default.qubit', wires=4)

print("Device name:", dev.name)
print("Wires:", dev.wires)
print("Device shots:", dev.shots)

# New-style devices (qml.devices.Device) describe support via a capabilities object
# loaded from their TOML config; the legacy dev.operations / dev.observables attributes
# no longer exist on default.qubit.
print(dev.capabilities)
```

## Device Configuration

### Setting Shots

```python
# Exact simulation (no shots)
dev = qml.device('default.qubit', wires=2)

@qml.qnode(dev)
def exact_circuit():
    qml.Hadamard(wires=0)
    return qml.expval(qml.PauliZ(0))

result = exact_circuit()  # Returns exact expectation

# Sampling mode: shots on the QNode (device-level shots are deprecated since v0.43)
@qml.qnode(dev, shots=1000)
def sampled_circuit():
    qml.Hadamard(wires=0)
    return qml.expval(qml.PauliZ(0))

result = sampled_circuit()  # Estimated from samples
```

### Dynamic Shots

```python
# Change shots per execution
dev = qml.device('default.qubit', wires=2)

@qml.qnode(dev)
def circuit():
    qml.Hadamard(wires=0)
    return qml.expval(qml.PauliZ(0))

# Different shot numbers — qml.set_shots returns a new QNode (passing shots= at call
# time is deprecated since v0.43)
result_100 = qml.set_shots(circuit, shots=100)()
result_1000 = qml.set_shots(circuit, shots=1000)()
result_exact = qml.set_shots(circuit, shots=None)()  # Exact
```

### Analytic Mode vs Finite Shots

```python
# Compare analytic vs sampled
dev = qml.device('default.qubit', wires=2)

@qml.qnode(dev)
def circuit_analytic(x):
    qml.RX(x, wires=0)
    return qml.expval(qml.PauliZ(0))

@qml.qnode(dev, shots=1000)
def circuit_sampled(x):
    qml.RX(x, wires=0)
    return qml.expval(qml.PauliZ(0))

import numpy as np
x = np.pi / 4

print(f"Analytic: {circuit_analytic(x)}")
print(f"Sampled: {circuit_sampled(x)}")
print(f"Exact value: {np.cos(x)}")
```

### Seed for Reproducibility

```python
# Set random seed on the device; shots on the QNode
dev = qml.device('default.qubit', wires=2, seed=42)

@qml.qnode(dev, shots=1000)
def circuit():
    qml.Hadamard(wires=0)
    return qml.sample(qml.PauliZ(0))

# The seed fixes the RNG *sequence*: successive calls still differ, but re-creating
# the device with the same seed reproduces the same sequence of results.
samples1 = circuit()
samples2 = circuit()
```

## Custom Devices

### Creating a Custom Device

New-style devices subclass `qml.devices.Device` (or an existing device) and implement
`execute(circuits, execution_config)`, which receives already-preprocessed tapes. The
legacy `apply()` / `short_name` / `pennylane_requires` device API is gone.

```python
from pennylane.devices import DefaultQubit

class LoggingDevice(DefaultQubit):
    """default.qubit that logs every tape it executes."""

    def execute(self, circuits, execution_config=None):
        for tape in circuits:
            print("Executing:", [op.name for op in tape.operations])
        return super().execute(circuits, execution_config)

# Use custom device
dev = LoggingDevice(wires=4)
```

### Plugin Development

```python
# Define a custom operation; devices that don't support it natively decompose it
class CustomGate(qml.operation.Operation):
    """Custom quantum gate."""

    num_wires = 1
    num_params = 1
    grad_method = "A"  # differentiable with the parameter-shift rule

    @staticmethod
    def compute_decomposition(theta, wires):
        """Decompose into standard gates."""
        return [
            qml.RY(theta / 2, wires=wires),
            qml.RZ(theta, wires=wires),
            qml.RY(-theta / 2, wires=wires)
        ]

# Use it like any built-in gate inside a QNode: CustomGate(0.4, wires=0)
```

## Performance Optimization

### Batch Execution

```python
# Execute multiple parameter sets efficiently
dev = qml.device('default.qubit', wires=2)

@qml.qnode(dev)
def circuit(params):
    qml.RX(params[0], wires=0)
    qml.RY(params[1], wires=1)
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.PauliZ(0))

# Batch parameters
params_batch = np.random.random((100, 2))

# Parameter broadcasting: pass arrays with a leading batch dimension per gate
# argument, so each gate parameter here gets shape (100,). One call, shape (100,) out.
results = circuit(params_batch.T)
```

### Device Caching

```python
# Cache device for reuse
_device_cache = {}

def get_device(n_qubits, device_type='default.qubit'):
    """Get or create cached device."""
    key = (device_type, n_qubits)

    if key not in _device_cache:
        _device_cache[key] = qml.device(device_type, wires=n_qubits)

    return _device_cache[key]

# Reuse devices
dev1 = get_device(4)
dev2 = get_device(4)  # Returns same device
```

### JIT Compilation with Catalyst

```python
# Install Catalyst
# uv pip install pennylane-catalyst

import pennylane as qml
from catalyst import qjit

dev = qml.device('lightning.qubit', wires=4)

@qjit  # Just-in-time compilation
@qml.qnode(dev)
def compiled_circuit(x):
    qml.RX(x, wires=0)
    qml.Hadamard(wires=1)
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.PauliZ(0))

# First call compiles, subsequent calls are fast
result = compiled_circuit(0.5)
```

### Parallel Execution

```python
from multiprocessing import Pool

def run_circuit(params):
    """Run circuit with given parameters."""
    dev = qml.device('default.qubit', wires=4)

    @qml.qnode(dev)
    def circuit(p):
        # Circuit definition
        return qml.expval(qml.PauliZ(0))

    return circuit(params)

# Parallel execution
param_list = [np.random.random(10) for _ in range(100)]

with Pool(processes=4) as pool:
    results = pool.map(run_circuit, param_list)
```

### GPU Acceleration

```python
# Use GPU-accelerated devices if available
try:
    dev = qml.device('lightning.gpu', wires=20)
except:
    dev = qml.device('lightning.qubit', wires=20)

@qml.qnode(dev)
def gpu_circuit():
    # Large circuit benefits from GPU
    for i in range(20):
        qml.Hadamard(wires=i)

    for i in range(19):
        qml.CNOT(wires=[i, i+1])

    return [qml.expval(qml.PauliZ(i)) for i in range(20)]
```

## Best Practices

1. **Start with simulators** - Test on `default.qubit` before hardware
2. **Use lightning for speed** - Switch to `lightning.qubit` for larger circuits
3. **Match device to task** - Use `default.mixed` for noise studies
4. **Cache devices** - Reuse device objects to avoid initialization overhead
5. **Set appropriate shots** - Balance accuracy vs speed
6. **Check capabilities** - Verify device supports required operations
7. **Handle hardware errors** - Implement retries and error mitigation
8. **Monitor costs** - Track hardware usage and costs
9. **Use JIT when possible** - Compile circuits with Catalyst for speedup
10. **Test locally first** - Validate on simulators before submitting to hardware

## Device Comparison

| Device | Type | Max Qubits | Speed | Noise | Use Case |
|--------|------|-----------|-------|-------|----------|
| default.qubit | Simulator | ~25 | Medium | No | General purpose |
| lightning.qubit | Simulator | ~30 | Fast | No | Large circuits |
| default.mixed | Simulator | ~15 | Slow | Yes | Noise studies |
| default.clifford | Simulator | 100+ | Very fast | No | Clifford circuits |
| IBM Quantum (Heron/Nighthawk) | Hardware | 100+ | Slow | Yes | Real experiments |
| IonQ (Forte) | Hardware | 36 | Slow | Low | High fidelity, all-to-all |
| Rigetti via Braket (Ankaa-3, Cepheus-1-108Q) | Hardware | ~80–108 | Slow | Yes | Research |
