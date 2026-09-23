# Qiskit Setup and Installation

## Installation

Install Qiskit using uv (pin the major version — examples here target Qiskit 2.x):

```bash
uv pip install "qiskit>=2,<3"
```

For visualization capabilities:

```bash
uv pip install "qiskit[visualization]" matplotlib
```

## Python Environment Setup

Create and activate a virtual environment to isolate dependencies:

```bash
uv venv .venv                      # macOS/Linux/Windows
source .venv/bin/activate          # Windows: .venv\Scripts\activate
uv pip install "qiskit>=2,<3" qiskit-ibm-runtime
```

## Supported Python Versions

Check the [Qiskit PyPI page](https://pypi.org/project/qiskit/) for currently supported Python versions. Qiskit SDK 2.x requires Python 3.10+ (current release 2.5.x as of 2026-09).

## IBM Quantum Account Setup

To run circuits on real IBM Quantum hardware you need an IBM Quantum Platform account,
an API key, and an instance (the free Open Plan works for small jobs). The classic
platform at quantum.ibm.com and its `channel="ibm_quantum"` were retired in 2025; the
current platform is <https://quantum.cloud.ibm.com> and the default channel is
`"ibm_quantum_platform"`.

### Creating an Account

1. Sign in at [IBM Quantum Platform](https://quantum.cloud.ibm.com/) with an IBMid
2. On the dashboard, create an **API key** and store it securely (it is shown once)
3. From the **Instances** page, copy the CRN of the instance you want to bill against

### Configuring Authentication

Save your credentials once per machine:

```python
from qiskit_ibm_runtime import QiskitRuntimeService

QiskitRuntimeService.save_account(
    token="<your-api-key>",
    instance="<instance CRN or name>",   # optional; omit to auto-select an instance
    set_as_default=True,
    overwrite=True,
)

# Later sessions - load saved credentials
service = QiskitRuntimeService()
```

### Environment Variable Method

Alternatively, read credentials from the environment (useful on shared or CI machines,
so the key never lands in a notebook):

```bash
export QISKIT_IBM_TOKEN="<your-api-key>"
export QISKIT_IBM_INSTANCE="<instance CRN>"
```

## Local Development (No Account Required)

You can build and test quantum circuits locally without an IBM Quantum account using simulators:

```python
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

# Run locally with simulator
sampler = StatevectorSampler()
result = sampler.run([qc], shots=1024).result()
```

## Verifying Installation

Test your installation:

```python
import qiskit
print(qiskit.__version__)

from qiskit import QuantumCircuit
qc = QuantumCircuit(2)
print("Qiskit installed successfully!")
```
