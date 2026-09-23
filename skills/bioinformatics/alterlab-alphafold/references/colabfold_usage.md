# ColabFold / AlphaFold2 — Usage Reference

Deeper detail for `alterlab-alphafold`. Verified against ColabFold **1.6.3** (current release
as of 2026-09). Flags do shift between releases — check `colabfold_batch --help` when a
command is rejected.

## Install

ColabFold couples a folding engine (AlphaFold2 via JAX) with the fast MMseqs2 MSA step.
The upstream `sokrypton/ColabFold` install path is a conda env plus pip:

```bash
conda create -n colabfold -c conda-forge -c bioconda python=3.13 mmseqs2
conda activate colabfold

# CUDA 12 GPU (use jax[cuda13]/openmm[cuda13] on Blackwell or newer)
pip install colabfold[alphafold,openmm] jax[cuda12] openmm[cuda12]

# CPU only (slow — fine for testing the pipeline)
pip install colabfold[alphafold,openmm]

# MSA generation only, no structure prediction
pip install colabfold
```

The `openmm` extra is what enables Amber relaxation. For a one-command installer covering
Linux/macOS/WSL2 there is LocalColabFold (`YoshitakaMo/localcolabfold`); a CUDA Docker image
is published as `ghcr.io/sokrypton/colabfold`.

## MSA modes

- **Hosted MMseqs2 API (default)** — `--msa-mode mmseqs2_uniref_env`. Fastest to start; your
  sequence goes to a public shared server, so disclose this for sensitive or unpublished
  sequences. Other choices: `mmseqs2_uniref_env_envpair`, `mmseqs2_uniref`, `single_sequence`.
- **Local database** — run `colabfold_search` against a local ColabFold DB and feed the
  resulting MSA directory to `colabfold_batch`. Needed on air-gapped HPC. Splitting the run
  this way (`--msa-only`, then predict) also keeps the GPU busy only during folding.

## Key flags

| Flag | Purpose |
|------|---------|
| `--num-models N` | how many of the 5 AF2 models to run (default 5) |
| `--num-recycle N` | recycling iterations; more can help hard targets |
| `--model-type alphafold2_multimer_v3` | multimer models for complexes (`auto` picks `alphafold2_ptm` for monomers, `alphafold2_multimer_v3` for complexes) |
| `--templates` | query PDB templates from the MSA server |
| `--amber --num-relax 1 --use-gpu-relax` | Amber-relax the top N ranked models (`--num-relax` defaults to 0, i.e. no relaxation) |
| `--msa-mode` | MSA source (see above) |
| `--msa-only` | fetch and store MSAs without predicting |
| `--rank` | early-stop criterion; `auto` ranks by pLDDT (monomer) or pTM (multimer) |
| `--pair-mode` / `--pair-strategy` | how chains' MSAs are paired for complexes |
| `--use-fast-kernels` | fused kernels, ~2.5x faster with slightly lower memory (`--kernel-backend auto`) |
| `--af3-json` | export the MSAs as an AlphaFold3-compatible input JSON instead of predicting |

## Outputs

Per FASTA record ColabFold writes: ranked structures (`*_rank_00N_*.pdb` or `.cif`, relaxed
versions only if `--num-relax` > 0), a scores JSON with `plddt` and `pae` arrays, and
coverage/pLDDT/PAE plots. Rank 1 is the highest-confidence model.

## Metric interpretation

- **pLDDT** (0–100, per residue): >90 very high, 70–90 confident, 50–70 low, <50 likely
  disordered.
- **pTM**: global fold confidence (0–1); >0.5 means the overall predicted fold is plausibly
  similar to the true structure.
- **ipTM**: interface confidence (0–1) and the load-bearing number for complexes. DeepMind's
  published bands (AlphaFold 3 output documentation): **>0.8** confident high-quality
  interface, **0.6–0.8** gray zone where the prediction may be right or wrong, **<0.6**
  likely a failed prediction. TM-based scores are strict on very short chains, so fall back
  to PAE/pLDDT for small entities.
- **PAE**: N×N expected error (Å) between residue pairs; confident relative domain/chain
  orientation shows as low off-diagonal blocks.

## Design self-consistency

For a design→fold→score loop, refold the designed sequence and accept only if it returns to
the intended backbone with high pLDDT and low PAE (compare via TM-score/RMSD). This is the
validation gate referenced by `alterlab-proteinmpnn`, `alterlab-ligandmpnn`, and
`alterlab-rfdiffusion`.

## GPU dispatch

`colabfold_batch` needs a CUDA GPU. Batch many targets as a SLURM array or a cloud GPU job via
`alterlab-remote-compute` (submit → poll `sacct`/provider status → harvest `out/`).

## AlphaFold 3

ColabFold also ships an AlphaFold3/OpenFold3 notebook, and DeepMind's own
`google-deepmind/alphafold3` provides the AF3 inference pipeline under Apache-2.0 with model
parameters distributed separately under Google's weights terms of use. The hosted
AlphaFold Server (`alphafoldserver.com`) is free for non-commercial use with a limited ligand
set. For an openly licensed local AF3-class model, see `alterlab-boltz` or `alterlab-chai`.
