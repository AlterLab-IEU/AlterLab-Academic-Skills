# Output and Analysis

## Output Types

FluidSim automatically saves several types of output during simulations.

### Physical Fields

**File format**: NetCDF-4 / HDF5 (`.nc`)

**Location**: `simulation_dir/state_phys_t*.nc`

**Contents**: Velocity, vorticity, and other physical space fields at specific times

**Access**:
```python
sim.output.phys_fields.plot()
sim.output.phys_fields.plot("rot")
sim.output.phys_fields.plot("ux")
sim.output.phys_fields.plot("div")  # check divergence

# Save manually
sim.output.phys_fields.save()

# Get data
vorticity = sim.state.state_phys.get_var("rot")
```

### Spatial Means

**File format**: Text file (`.txt`)

**Location**: `simulation_dir/spatial_means.txt`

**Contents**: Volume-averaged quantities vs time (energy, enstrophy, etc.)

**Access**:
```python
sim.output.spatial_means.plot()

# Load from file
from fluidsim import load_sim_for_plot
sim = load_sim_for_plot("simulation_dir")
sim.output.spatial_means.load()
spatial_means_data = sim.output.spatial_means
```

### Spectra

**File format**: HDF5 (`.h5`)

**Location**: `simulation_dir/spectra1D.h5`, `simulation_dir/spectra2D.h5`

**Contents**: Energy and enstrophy spectra vs wavenumber

**Access**:
```python
sim.output.spectra.plot1d()  # 1D spectrum
sim.output.spectra.plot2d()  # 2D spectrum

# Load spectra data
spectra = sim.output.spectra.load2d_mean()
```

### Spectral Energy Budget

**File format**: HDF5 (`.h5`)

**Location**: `simulation_dir/spect_energy_budg.h5`

**Contents**: Energy transfer between scales

**Access**:
```python
sim.output.spect_energy_budg.plot()
```

## Post-Processing

### Loading Simulations for Analysis

#### Fast Loading (Read-Only)

```python
from fluidsim import load_sim_for_plot

sim = load_sim_for_plot("simulation_dir")

# Access all output types
sim.output.phys_fields.plot()
sim.output.spatial_means.plot()
sim.output.spectra.plot1d()
```

Use this for quick visualization and analysis. Does not initialize full simulation state.

#### Full State Loading

```python
from fluidsim import load_state_phys_file

sim = load_state_phys_file("simulation_dir/state_phys_t010.000.nc")

# Can continue simulation
sim.time_stepping.start()
```

### Visualization Tools

#### Built-in Plotting

FluidSim provides basic plotting through matplotlib:

```python
# Physical fields
sim.output.phys_fields.plot("rot")
sim.output.phys_fields.animate("rot")

# Time series
sim.output.spatial_means.plot()

# Spectra
sim.output.spectra.plot1d()
```

#### Advanced Visualization

For publication-quality or 3D visualization:

**ParaView**: Open the NetCDF state files directly
```bash
paraview simulation_dir/state_phys_t*.nc
```

**VisIt**: Similar to ParaView for large datasets

**Custom Python**:
```python
import h5py
import matplotlib.pyplot as plt

# Load field manually (state files are NetCDF-4, i.e. HDF5, so h5py reads them)
with h5py.File("state_phys_t010.000.nc", "r") as f:
    ux = f["state_phys"]["ux"][:]
    uy = f["state_phys"]["uy"][:]

# Custom plotting
plt.contourf(ux)
plt.show()
```

## Analysis Examples

### Energy Evolution

```python
from fluidsim import load_sim_for_plot
import matplotlib.pyplot as plt

sim = load_sim_for_plot("simulation_dir")
# load() returns a dict of numpy arrays keyed by "t", "E", "EZ" (enstrophy),
# etc. — NOT a pandas DataFrame. Index it like a dict.
data = sim.output.spatial_means.load()

plt.figure()
plt.plot(data["t"], data["E"], label="Kinetic Energy")
plt.xlabel("Time")
plt.ylabel("Energy")
plt.legend()
plt.show()
```

### Spectral Analysis

```python
sim = load_sim_for_plot("simulation_dir")

# Plot energy spectrum
sim.output.spectra.plot1d(tmin=5.0, tmax=10.0)  # average over time range

# Get spectral data. load1d_mean(...) returns a dict of arrays keyed by
# wavenumber and spectrum names (e.g. "kx"/"ky" and the energy spectra) —
# inspect the keys for your solver rather than assuming a fixed tuple.
data = sim.output.spectra.load1d_mean(tmin=5.0, tmax=10.0)
print(data.keys())  # discover the available wavenumber / spectrum arrays

# Check for power law (pick the wavenumber and spectrum keys from data)
import numpy as np
# log_k = np.log(data["kx"]); log_E = np.log(data["spectrum1Dkx_E"])
# fit a power law in the inertial range
```

### Parametric Study Analysis

When running multiple simulations with different parameters:

```python
import os
import pandas as pd
from fluidsim import load_sim_for_plot

# Collect results from multiple simulations
results = []
for sim_dir in os.listdir("simulations"):
    if not os.path.isdir(f"simulations/{sim_dir}"):
        continue

    sim = load_sim_for_plot(f"simulations/{sim_dir}")

    # Extract key metrics. spatial_means.load() returns a dict of numpy
    # arrays, so index with [-1] rather than pandas .iloc[-1].
    data = sim.output.spatial_means.load()
    final_energy = data["E"][-1]

    # Get parameters
    nu = sim.params.nu_2

    results.append({
        "nu": nu,
        "final_energy": final_energy,
        "sim_dir": sim_dir
    })

# Analyze results
results_df = pd.DataFrame(results)
results_df.plot(x="nu", y="final_energy", logx=True)
```

### Field Manipulation

```python
sim = load_sim_for_plot("simulation_dir")

# Load specific time
sim.output.phys_fields.set_of_phys_files.update_times()
times = sim.output.phys_fields.set_of_phys_files.times

# Load field at specific time — returns (array, actual_time_of_file)
vorticity, t_file = sim.output.phys_fields.get_field_to_plot(key="rot", time=5.0)

# Compute derived quantities
import numpy as np
vorticity_rms = np.sqrt(np.mean(vorticity**2))
vorticity_max = np.max(np.abs(vorticity))
```

## Output Directory Structure

```
simulation_dir/
├── params_simul.xml         # Simulation parameters
├── stdout.txt               # Standard output log
├── state_phys_t*.nc         # Physical fields at different times (NetCDF-4/HDF5)
├── spatial_means.txt        # Time series of spatial averages
├── spectra1D.h5, spectra2D.h5  # Spectral data
├── spect_energy_budg.h5     # Energy budget data
└── info_solver.xml          # Solver information
```

## Performance Monitoring

```python
# During simulation, check progress
sim.output.print_stdout.complete_timestep()

# After simulation, review performance
sim.output.print_stdout.plot_deltat()  # plot time step evolution
sim.output.print_stdout.plot_clock_times()  # plot computation time
```

## Data Export

Convert fluidsim output to other formats:

```python
import h5py
import numpy as np

# Export to numpy array
with h5py.File("state_phys_t010.000.nc", "r") as f:
    ux = f["state_phys"]["ux"][:]
    np.save("ux.npy", ux)

# Export to CSV (load() yields a dict of arrays; wrap in a DataFrame first)
import pandas as pd
data = sim.output.spatial_means.load()
pd.DataFrame(data).to_csv("spatial_means.csv", index=False)
```
