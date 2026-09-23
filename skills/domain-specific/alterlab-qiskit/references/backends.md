# Hardware Backends and Execution

Qiskit is backend-agnostic and supports execution on simulators and real quantum hardware from multiple providers.

## Backend Types

### Local Simulators
- Run on your machine
- No account required
- Perfect for development and testing

### Cloud-Based Hardware
- IBM Quantum (100+ qubit Heron / Nighthawk systems; the 127-qubit Eagle family was retired in 2025–26)
- IonQ (trapped ion)
- Amazon Braket (IonQ, IQM, Rigetti, plus managed simulators)
- Other providers via plugins

## IBM Quantum Backends

### Connecting to IBM Quantum

```python
from qiskit_ibm_runtime import QiskitRuntimeService

# First time: save credentials. The legacy channel="ibm_quantum" is gone; the default
# channel is "ibm_quantum_platform" (API key + instance CRN from quantum.cloud.ibm.com).
QiskitRuntimeService.save_account(
    token="<your-api-key>",
    instance="<instance CRN>",   # optional
    set_as_default=True,
)

# Subsequent sessions: load credentials
service = QiskitRuntimeService()
```

### Listing Available Backends

```python
# List all available backends
backends = service.backends()
for backend in backends:
    print(f"{backend.name}: {backend.num_qubits} qubits")

# Filter by minimum qubits
large_backends = service.backends(min_num_qubits=100, operational=True)

# Get a specific backend by name — QPUs are retired over time, so take the
# name from the listing above rather than hard-coding an old one
backend = service.backend(large_backends[0].name)

# Or let Runtime pick the least busy operational QPU
backend = service.least_busy(operational=True, simulator=False)
```

### Backend Properties

```python
backend = service.least_busy(operational=True, simulator=False)

# Basic info
print(f"Name: {backend.name}")
print(f"Qubits: {backend.num_qubits}")
print(f"Version: {backend.version}")
print(f"Status: {backend.status()}")

# Coupling map (qubit connectivity)
print(backend.coupling_map)

# Basis gates
print(backend.operation_names)

# Qubit properties
print(backend.qubit_properties(0))  # Properties of qubit 0
```

### Checking Backend Status

```python
status = backend.status()
print(f"Operational: {status.operational}")
print(f"Pending jobs: {status.pending_jobs}")
print(f"Status message: {status.status_msg}")
```

## Running on IBM Quantum Hardware

### Using Runtime Primitives

```python
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

service = QiskitRuntimeService()
backend = service.least_busy(operational=True, simulator=False)

# Create and transpile circuit
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

# Transpile for backend
transpiled_qc = transpile(qc, backend=backend, optimization_level=3)

# Run with Sampler
sampler = Sampler(backend)
job = sampler.run([transpiled_qc], shots=1024)

# Retrieve results
result = job.result()
counts = result[0].data.meas.get_counts()
print(counts)
```

### Job Management

```python
# Submit job
job = sampler.run([qc], shots=1024)

# Get job ID (save for later retrieval)
job_id = job.job_id()
print(f"Job ID: {job_id}")

# Check job status (a plain string for Runtime V2 jobs: "QUEUED", "RUNNING", "DONE", ...)
print(job.status())

# Wait for completion
result = job.result()

# Retrieve job later
service = QiskitRuntimeService()
retrieved_job = service.job(job_id)
result = retrieved_job.result()
```

### Job Queuing

```python
# Runtime V2 jobs expose status() but no queue position; watch pending jobs in
# the IBM Quantum Platform dashboard
print(job.status())

# Cancel job if needed
job.cancel()
```

## Session Mode

Use sessions for iterative algorithms (VQE, QAOA) to reduce queue time. Sessions
require a paid plan — Open Plan users cannot submit session jobs, so use batch or
job mode (`mode=backend`) there:

```python
from qiskit_ibm_runtime import Session, SamplerV2 as Sampler

service = QiskitRuntimeService()
backend = service.least_busy(operational=True, simulator=False)

with Session(backend=backend) as session:
    sampler = Sampler(mode=session)

    # Multiple iterations in same session
    for iteration in range(10):
        # Parameterized circuit
        qc = create_parameterized_circuit(params[iteration])
        job = sampler.run([qc], shots=1024)
        result = job.result()

        # Update parameters based on results
        params[iteration + 1] = optimize(result)
```

Session benefits:
- Reduced queue waiting between iterations
- Guaranteed backend availability during session
- Better for variational algorithms

## Batch Mode

Use batch mode for independent parallel jobs:

```python
from qiskit_ibm_runtime import Batch, SamplerV2 as Sampler

service = QiskitRuntimeService()
backend = service.least_busy(operational=True, simulator=False)

with Batch(backend=backend) as batch:
    sampler = Sampler(mode=batch)

    # Submit multiple independent jobs
    jobs = []
    for qc in circuit_list:
        job = sampler.run([qc], shots=1024)
        jobs.append(job)

    # Collect all results
    results = [job.result() for job in jobs]
```

## Local Simulators

### StatevectorSampler (Ideal Simulation)

```python
from qiskit.primitives import StatevectorSampler

sampler = StatevectorSampler()
result = sampler.run([qc], shots=1024).result()
counts = result[0].data.meas.get_counts()
```

### Aer Simulator (Realistic Noise)

```python
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import SamplerV2 as Sampler

# Ideal simulation
simulator = AerSimulator()

# Simulate with backend noise model
backend = service.least_busy(operational=True, simulator=False)
noisy_simulator = AerSimulator.from_backend(backend)

# Run simulation
transpiled_qc = transpile(qc, simulator)
sampler = Sampler(simulator)
job = sampler.run([transpiled_qc], shots=1024)
result = job.result()
```

### Aer GPU Acceleration

```python
# Use GPU for faster simulation
simulator = AerSimulator(method='statevector', device='GPU')
```

## Third-Party Providers

### IonQ

IonQ offers trapped-ion quantum computers with all-to-all connectivity:

```python
from qiskit_ionq import IonQProvider

provider = IonQProvider("YOUR_IONQ_API_TOKEN")

# List IonQ backends
backends = provider.backends()
backend = provider.get_backend("ionq_qpu")

# Run circuit
job = backend.run(qc, shots=1024)
result = job.result()
```

### Amazon Braket

```python
from qiskit_braket_provider import BraketProvider

provider = BraketProvider()

# List available devices
backends = provider.backends()

# Use a specific device by its Braket name (e.g. the managed "SV1" simulator;
# list QPUs with provider.backends())
backend = provider.get_backend("SV1")
job = backend.run(qc, shots=1024)
result = job.result()
```

## Error Mitigation

The legacy `from qiskit_ibm_runtime import Options` class was removed. With V2 primitives,
set options either as a dict at construction (`Estimator(backend, options={...})`) or by
mutating `primitive.options` after construction.

**`resilience_level` is an Estimator-only knob — `SamplerV2` does NOT accept it.** For the
Sampler, reduce noise with `twirling` and `dynamical_decoupling` instead.

### Estimator resilience (expectation values)

```python
from qiskit_ibm_runtime import EstimatorV2 as Estimator

# 0=none, 1=minimal (TREX readout twirling), 2=moderate (adds ZNE) — see docs for exact mapping
estimator = Estimator(backend, options={"resilience_level": 2})

# Or mutate after construction:
estimator.options.resilience_level = 2
estimator.options.resilience.zne_mitigation = True   # explicit ZNE
```

### Sampler noise reduction (bitstrings)

```python
from qiskit_ibm_runtime import SamplerV2 as Sampler

sampler = Sampler(backend)
sampler.options.dynamical_decoupling.enable = True
sampler.options.twirling.enable_gates = True
job = sampler.run([isa_circuit], shots=1024)   # circuit must already be transpiled (ISA)
result = job.result()
```

## Monitoring Usage and Costs

### Check Account Usage

```python
# For IBM Quantum
service = QiskitRuntimeService()

# Inspect usage for your instance (quota/usage stats)
print(service.usage())
```

### Estimate Job Cost

```python
from qiskit_ibm_runtime import EstimatorV2 as Estimator

backend = service.least_busy(operational=True, simulator=False)

# Estimate job cost
estimator = Estimator(backend)
# Cost depends on circuit complexity and shots
```

## Best Practices

### 1. Always Transpile Before Running

```python
# Bad: Run without transpilation
job = sampler.run([qc], shots=1024)

# Good: Transpile first
qc_transpiled = transpile(qc, backend=backend, optimization_level=3)
job = sampler.run([qc_transpiled], shots=1024)
```

### 2. Test with Simulators First

```python
# Test with noisy simulator before hardware
noisy_sim = AerSimulator.from_backend(backend)
qc_test = transpile(qc, noisy_sim, optimization_level=3)

# Verify results look reasonable
# Then run on hardware
```

### 3. Use Appropriate Shot Counts

```python
# For optimization algorithms: fewer shots (100-1000)
# For final measurements: more shots (10000+)

# Adaptive shots based on stage
shots_optimization = 500
shots_final = 10000
```

### 4. Choose Backend Strategically

```python
# For testing: Use least busy backend
backend = service.least_busy(min_num_qubits=5)

# For production: Use backend matching requirements
backend = service.least_busy(operational=True, simulator=False)
```

### 5. Use Sessions for Variational Algorithms

Sessions are ideal for VQE, QAOA, and other iterative algorithms (paid plans only;
on the Open Plan, use batch mode).

### 6. Monitor Job Status

```python
import time

job = sampler.run([qc], shots=1024)

# RuntimeJobV2.status() returns a plain string, not an enum — no `.name`
while not job.in_final_state():
    print(f"Status: {job.status()}")
    time.sleep(10)

result = job.result()
```

## Troubleshooting

### Issue: "Backend not found"
```python
# List available backends
print([b.name for b in service.backends()])
```

### Issue: "Invalid credentials"
```python
# Re-save credentials (API key from quantum.cloud.ibm.com; old quantum.ibm.com
# tokens no longer work)
QiskitRuntimeService.save_account(
    token="<your-api-key>",
    overwrite=True
)
```

### Issue: Long queue times
```python
# Use least busy backend
backend = service.least_busy(min_num_qubits=5)

# Or use batch mode for multiple independent jobs
```

### Issue: Job fails with "Circuit too large"
```python
# Reduce circuit complexity
# Use higher transpilation optimization
qc_opt = transpile(qc, backend=backend, optimization_level=3)
```

## Backend Comparison

| Provider | Connectivity | Gate Set | Notes |
|----------|-------------|----------|--------|
| IBM Quantum | Heavy-hex (Heron) / square lattice (Nighthawk) | CZ, RZ, SX, X | 100+ qubit systems; check `backend.operation_names` |
| IonQ | All-to-all | GPI, GPI2, MS | Trapped ion, low error rates |
| Rigetti | Limited | CZ, RZ, RX | Superconducting qubits |
