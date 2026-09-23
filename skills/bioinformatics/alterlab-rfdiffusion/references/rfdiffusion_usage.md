# RFdiffusion — Usage Reference

Deeper detail for `alterlab-rfdiffusion`. Config keys and contig grammar below were checked
against the upstream `RosettaCommons/RFdiffusion` README (2026-09). RFdiffusion uses a Hydra
config, so keys are version-specific — `configs/inference/base.yml` in your checkout is the
authoritative list. For RFdiffusion2 and RFdiffusion3 (separate repos with different
interfaces) see the version table in SKILL.md.

## Install

Clone `RosettaCommons/RFdiffusion`, install its environment (PyTorch + the SE(3)-transformer
dependency), and download model weights per its instructions (several GB, no account). A CUDA
GPU is required for practical generation.

## Contig map

`contigmap.contigs` is the core control:

- `'[100-100]'` — a single 100-residue chain (unconditional).
- `'[5-15/A10-25/30-40]'` — generated 5–15 residues, then fixed motif A10-25 from the input PDB,
  then generated 30–40: **motif scaffolding**. Ranges are resampled per design unless you pin the
  total with `contigmap.length=55-55`.
- `/0 ` (trailing space) — a chain break, e.g. `'[B1-100/0 100-100]'` = keep target chain B,
  generate a 100-residue binder as a second chain.

## Common modes

| Mode | Config sketch |
|------|---------------|
| Unconditional | `'contigmap.contigs=[N-N]' inference.num_designs=K` |
| Motif scaffolding | `inference.input_pdb=…` + fixed ranges in the contig (+ `contigmap.length`) |
| Binder design | target chain in the contig + `'ppi.hotspot_res=[A30,A33,A34]'` |
| Partial diffusion | `diffuser.partial_T=20` — re-noise an existing design instead of starting from noise. `diffuser.T` defaults to 50, so scale `partial_T` against that (older papers quoting ~80 assumed T=200) |
| Symmetric | `--config-name symmetry inference.symmetry=c4` (or `d2`, `tetrahedral`) — a separate config file, not just a flag |
| Fold-conditioned / scaffold-guided | `scaffoldguided.scaffoldguided=True` + `scaffoldguided.scaffold_dir=…` |
| Auxiliary potentials | `potentials.guiding_potentials=[…]`, `potentials.guide_scale`, `potentials.guide_decay` — nudge packing/oligomer contacts during denoising |

## Outputs

Backbone PDBs (no sequence) plus trajectory/metadata. These are the input to sequence design.

## Design → fold → score

1. **Generate** backbones (RFdiffusion).
2. **Sequence** with `alterlab-proteinmpnn` (or `alterlab-ligandmpnn` when a ligand/metal is
   part of the site).
3. **Validate** by refolding with `alterlab-alphafold`; for binders, read ipTM at the
   interface. Keep only self-consistent designs.

Generation and the fold sweep are GPU-heavy — dispatch both via `alterlab-remote-compute`
(submit → poll → harvest).

## Choosing between the skills

- **alterlab-rfdiffusion** — make the backbone / scaffold a motif / design a binder backbone.
- **alterlab-proteinmpnn** / **alterlab-ligandmpnn** — sequence for a backbone (± ligand).
- **alterlab-alphafold** — fold/validate a sequence.
- **alterlab-esm** — generative multimodal design as an alternative paradigm.
