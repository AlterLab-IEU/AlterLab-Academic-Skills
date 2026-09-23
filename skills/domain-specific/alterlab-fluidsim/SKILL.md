---
name: alterlab-fluidsim
description: Runs computational fluid dynamics simulations with the FluidSim Python framework using pseudospectral FFT methods, with HPC support and output analysis. Use when simulating Navier-Stokes equations (2D/3D), shallow water equations, or stratified flows, or when analyzing turbulence, vortex dynamics, or geophysical flows. Part of the AlterLab Academic Skills suite.
license: CeCILL-2.1
allowed-tools: Read Write Edit Bash(python:*)
compatibility: No API key required. Runs locally via `uv run python`; requires the fluidsim Python package.
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# FluidSim

## Overview

FluidSim is an object-oriented Python framework for high-performance computational fluid dynamics (CFD) simulations. It provides solvers for periodic-domain equations using pseudospectral methods with FFT, delivering performance comparable to Fortran/C++ while maintaining Python's ease of use.

## When to Use This Skill

Use this skill when the user wants to run or analyze periodic-domain pseudospectral CFD
with FluidSim: 2D/3D Navier-Stokes turbulence, stratified or rotating flows, shallow-water
dynamics, energy spectra and spatial means, parametric sweeps, or MPI runs on a cluster.

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| ML on an already-recorded time series (anomalies, classification, forecasting) | `alterlab-aeon` |
| Remote-sensing / satellite retrievals of ocean or atmospheric fields | `alterlab-geomaster` |
| Submitting the finished job script to SLURM or a cloud GPU queue | `alterlab-remote-compute` |
| Discrete-event or queueing simulation rather than PDE-based CFD | `alterlab-simpy` |

**Key strengths**:
- Multiple solvers: 2D/3D Navier-Stokes, shallow water, stratified flows
- High performance: Pythran/Transonic compilation, MPI parallelization
- Complete workflow: Parameter configuration, simulation execution, output analysis
- Interactive analysis: Python-based post-processing and visualization

## Core Capabilities

### 1. Installation and Setup

Install fluidsim using uv with appropriate feature flags:

```bash
# Basic installation
uv pip install fluidsim

# With FFT support (required for most solvers)
uv pip install "fluidsim[fft]"

# With MPI for parallel computing
uv pip install "fluidsim[fft,mpi]"
```

Set environment variables for output directories (optional):

```bash
export FLUIDSIM_PATH=/path/to/simulation/outputs
export FLUIDDYN_PATH_SCRATCH=/path/to/working/directory
```

No API keys or authentication required.

See `references/installation.md` for complete installation instructions and environment configuration.

### 2. Running Simulations

Standard workflow consists of five steps:

**Step 1**: Import solver
```python
from fluidsim.solvers.ns2d.solver import Simul
```

**Step 2**: Create and configure parameters
```python
params = Simul.create_default_params()
params.oper.nx = params.oper.ny = 256
params.oper.Lx = params.oper.Ly = 2 * 3.14159
params.nu_2 = 1e-3
params.time_stepping.t_end = 10.0
params.init_fields.type = "noise"
```

**Step 3**: Instantiate simulation
```python
sim = Simul(params)
```

**Step 4**: Execute
```python
sim.time_stepping.start()
```

**Step 5**: Analyze results
```python
sim.output.phys_fields.plot("rot")
sim.output.spatial_means.plot()
```

See `references/simulation_workflow.md` for complete examples, restarting simulations, and cluster deployment.

### 3. Available Solvers

Choose solver based on physical problem:

**2D Navier-Stokes** (`ns2d`): 2D turbulence, vortex dynamics
```python
from fluidsim.solvers.ns2d.solver import Simul
```

**3D Navier-Stokes** (`ns3d`): 3D turbulence, realistic flows
```python
from fluidsim.solvers.ns3d.solver import Simul
```

**Stratified flows** (`ns2d.strat`, `ns3d.strat`): Oceanic/atmospheric flows
```python
from fluidsim.solvers.ns2d.strat.solver import Simul
params.N = 1.0  # Brunt-Väisälä frequency
```

**Shallow water** (`sw1l`): Geophysical flows, rotating systems
```python
from fluidsim.solvers.sw1l.solver import Simul
params.f = 1.0  # Coriolis parameter
```

See `references/solvers.md` for complete solver list and selection guidance.

### 4. Parameter Configuration

Parameters are organized hierarchically and accessed via dot notation:

**Domain and resolution**:
```python
params.oper.nx = 256  # grid points
params.oper.Lx = 2 * pi  # domain size
```

**Physical parameters**:
```python
params.nu_2 = 1e-3  # viscosity
params.nu_4 = 0     # hyperviscosity (optional)
```

**Time stepping**:
```python
params.time_stepping.t_end = 10.0
params.time_stepping.USE_CFL = True  # adaptive time step
params.time_stepping.cfl_coef = 0.5
```

**Initial conditions**:
```python
params.init_fields.type = "noise"  # or "dipole", "jet", "constant", "from_file", "from_simul", "in_script"
```

**Output settings**:
```python
params.output.periods_save.phys_fields = 1.0  # save every 1.0 time units
params.output.periods_save.spectra = 0.5
params.output.periods_save.spatial_means = 0.1
```

The Parameters object raises `AttributeError` for typos, preventing silent configuration errors.

See `references/parameters.md` for comprehensive parameter documentation.

### 5. Output and Analysis

FluidSim produces multiple output types automatically saved during simulation:

**Physical fields**: Velocity and vorticity saved as `state_phys_t*.nc` (NetCDF-4/HDF5;
ns2d keys `ux`, `uy`, `rot`, plus `b` for `ns2d.strat`)
```python
sim.output.phys_fields.plot("rot")
sim.output.phys_fields.plot("ux")
```

**Spatial means**: Time series of volume-averaged quantities
```python
sim.output.spatial_means.plot()
```

**Spectra**: Energy and enstrophy spectra
```python
sim.output.spectra.plot1d()
sim.output.spectra.plot2d()
```

**Load previous simulations**:
```python
from fluidsim import load_sim_for_plot
sim = load_sim_for_plot("simulation_dir")
sim.output.phys_fields.plot()
```

**Advanced visualization**: Open the `state_phys_t*.nc` files in ParaView or VisIt for 3D visualization.

See `references/output_analysis.md` for detailed analysis workflows, parametric study analysis, and data export.

### 6. Advanced Features

**Custom forcing**: Maintain turbulence or drive specific dynamics
```python
params.forcing.enable = True
params.forcing.type = "tcrandom"  # time-correlated random forcing
params.forcing.forcing_rate = 1.0
```

**Custom initial conditions**: Define fields in script
```python
params.init_fields.type = "in_script"
sim = Simul(params)
X, Y = sim.oper.XX, sim.oper.YY  # local physical grid
rot = np.sin(X) * np.sin(Y)          # ns2d evolves the vorticity "rot"
sim.state.init_from_rotfft(sim.oper.fft2(rot))  # sets rot_fft and derives ux, uy
sim.time_stepping.start()
```

**MPI parallelization**: Run on multiple processors
```bash
mpirun -np 8 python simulation_script.py
```

**Parametric studies**: Run multiple simulations with different parameters
```python
for nu in [1e-3, 5e-4, 1e-4]:
    params = Simul.create_default_params()
    params.nu_2 = nu
    params.output.sub_directory = f"nu{nu}"
    sim = Simul(params)
    sim.time_stepping.start()
```

See `references/advanced_features.md` for forcing types, custom solvers, cluster submission, and performance optimization.

## Common Use Cases

### 2D Turbulence Study

```python
from fluidsim.solvers.ns2d.solver import Simul
from math import pi

params = Simul.create_default_params()
params.oper.nx = params.oper.ny = 512
params.oper.Lx = params.oper.Ly = 2 * pi
params.nu_2 = 1e-4
params.time_stepping.t_end = 50.0
params.time_stepping.USE_CFL = True
params.init_fields.type = "noise"
params.output.periods_save.phys_fields = 5.0
params.output.periods_save.spectra = 1.0

sim = Simul(params)
sim.time_stepping.start()

# Analyze energy cascade
sim.output.spectra.plot1d(tmin=30.0, tmax=50.0)
```

### Stratified Flow Simulation

```python
from fluidsim.solvers.ns2d.strat.solver import Simul
import numpy as np

params = Simul.create_default_params()
params.oper.nx = params.oper.ny = 256
params.N = 2.0  # stratification strength (Brunt-Vaisala frequency)
params.nu_2 = 5e-4
params.time_stepping.t_end = 20.0

# Initialize with dense layer
params.init_fields.type = "in_script"
sim = Simul(params)
X, Y = sim.oper.XX, sim.oper.YY  # local physical grid
b = sim.state.state_phys.get_var("b")
b[:] = np.exp(-((X - 3.14)**2 + (Y - 3.14)**2) / 0.5)
# Sync spectral state FROM the physical field just set (not the reverse)
sim.state.statespect_from_statephys()

sim.time_stepping.start()
sim.output.phys_fields.plot("b")
```

### High-Resolution 3D Simulation with MPI

```python
from fluidsim.solvers.ns3d.solver import Simul

params = Simul.create_default_params()
params.oper.nx = params.oper.ny = params.oper.nz = 512
params.nu_2 = 1e-5
params.time_stepping.t_end = 10.0
params.init_fields.type = "noise"

sim = Simul(params)
sim.time_stepping.start()
```

Run with:
```bash
mpirun -np 64 python script.py
```

### Taylor-Green Vortex Validation

```python
from fluidsim.solvers.ns2d.solver import Simul
import numpy as np
from math import pi

params = Simul.create_default_params()
params.oper.nx = params.oper.ny = 128
params.oper.Lx = params.oper.Ly = 2 * pi
params.nu_2 = 1e-3
params.time_stepping.t_end = 10.0
params.init_fields.type = "in_script"

sim = Simul(params)
X, Y = sim.oper.XX, sim.oper.YY  # local physical grid
ux = np.sin(X) * np.cos(Y)
uy = -np.cos(X) * np.sin(Y)
rot = 2 * np.sin(X) * np.sin(Y)   # vorticity d(uy)/dx - d(ux)/dy
# Set the physical state, then compute the spectral state FROM it
# ns2d keys are ux, uy, rot; the solver's spectral state is rot_fft, which
# statespect_from_statephys computes from `rot` — so rot must be set too
sim.state.init_statephys_from(ux=ux, uy=uy, rot=rot)
sim.state.statespect_from_statephys()

sim.time_stepping.start()

# Validate energy decay. spatial_means.load() returns a dict of numpy
# arrays keyed by "t", "E", etc. (NOT a pandas DataFrame).
data = sim.output.spatial_means.load()
t, E = data["t"], data["E"]
# Compare E(t) decay with the analytical Taylor-Green solution
```

## Quick Reference

**Import solver**: `from fluidsim.solvers.ns2d.solver import Simul`

**Create parameters**: `params = Simul.create_default_params()`

**Set resolution**: `params.oper.nx = params.oper.ny = 256`

**Set viscosity**: `params.nu_2 = 1e-3`

**Set end time**: `params.time_stepping.t_end = 10.0`

**Run simulation**: `sim = Simul(params); sim.time_stepping.start()`

**Plot results**: `sim.output.phys_fields.plot("rot")`

**Load simulation**: `sim = load_sim_for_plot("path/to/sim")`

## Resources

**Documentation**: https://fluidsim.readthedocs.io/ (verified against fluidsim 0.9.0; Python ≥ 3.11)

**Reference files**:
- `references/installation.md`: Complete installation instructions
- `references/solvers.md`: Available solvers and selection guide
- `references/simulation_workflow.md`: Detailed workflow examples
- `references/parameters.md`: Comprehensive parameter documentation
- `references/output_analysis.md`: Output types and analysis methods
- `references/advanced_features.md`: Forcing, MPI, parametric studies, custom solvers

Part of the AlterLab Academic Skills suite.
