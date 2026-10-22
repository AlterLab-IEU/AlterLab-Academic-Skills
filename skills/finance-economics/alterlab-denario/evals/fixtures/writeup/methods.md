# Methods (fictional study, eval fixture)

We simulate heat transport in armchair graphene nanoribbons of width 1.5-6.0 nm and length
50 nm with equilibrium molecular dynamics in LAMMPS (optimised Tersoff potential, 300 K,
timestep 0.5 fs). After 1 ns of NVT equilibration at 300 K we run 10 independent 5 ns NVE
trajectories per width and compute the thermal conductivity κ from the Green-Kubo relation,
integrating the heat-current autocorrelation function to 100 ps. The ribbon thickness is taken
as 0.335 nm. Uncertainties are the standard error over the 10 trajectories. Edge roughness is
introduced by removing a random 5% of edge carbon atoms (three random seeds per width).
