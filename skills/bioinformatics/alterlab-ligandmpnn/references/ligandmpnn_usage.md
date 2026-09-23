# LigandMPNN — Usage Reference

Deeper detail for `alterlab-ligandmpnn`. Flags below were checked against the upstream
`dauparas/LigandMPNN` README (2026-09).

## Install

```bash
git clone https://github.com/dauparas/LigandMPNN && cd LigandMPNN
bash get_model_params.sh "./model_params"   # small; no account needed
uv pip install -r requirements.txt          # PyTorch, NumPy, ProDy
```

CPU is adequate for typical designs; a GPU only speeds large batches. Structures are parsed
with ProDy, so chain letters, residue indices, and insertion codes survive round-trip — prefer
the `.pdb` outputs over the `.fasta` ones when numbering matters.

## Model types

One repo serves several models; select with `--model_type` and (optionally) the matching
`--checkpoint_*` path:

| `--model_type` | Checkpoint flag | Use for |
|----------------|-----------------|---------|
| `ligand_mpnn` | `--checkpoint_ligand_mpnn` (e.g. `ligandmpnn_v_32_010_25.pt`) | ligand / metal / nucleic-acid context |
| `protein_mpnn` | `--checkpoint_protein_mpnn` (e.g. `proteinmpnn_v_48_020.pt`) | plain inverse folding (same weights as `alterlab-proteinmpnn`) |
| `soluble_mpnn` | `--checkpoint_soluble_mpnn` | bias toward soluble sequences |
| `global_label_membrane_mpnn` / `per_residue_label_membrane_mpnn` | matching `--checkpoint_*` | membrane-protein design |

The `_v_32_0XX_25` suffix is the training noise level (0.05/0.10/0.20/0.30 Å); higher noise
tolerates rougher backbones, e.g. diffusion output. Side-chain packing is a separate
checkpoint (`--checkpoint_path_sc`).

## Input

The input structure (PDB/mmCIF) must include the **non-protein atoms** — the ligand and/or
metal (HETATM) and any nucleic-acid chains — so the model conditions on them. If the ligand is
absent from the file, the design is not ligand-aware (use `alterlab-proteinmpnn` instead).

## Site-restricted design

Restrict design to residues near the ligand (design the pocket, keep the scaffold) by naming
residues directly:

| Flag | Meaning |
|------|---------|
| `--redesigned_residues "A23 A24 B42D"` | design only these; fix everything else |
| `--fixed_residues "C1 C2 C3"` | the complement — fix these, design the rest |
| `--chains_to_design "A,B"` | design whole chains |
| `--ligand_mpnn_use_side_chain_context 1` | also condition on fixed residues' side chains |
| `--omit_AA "C"` / `--bias_AA "A:10.0"` | composition control (e.g. drop cysteines) |
| `--batch_size` × `--number_of_batches` | total sequences sampled |
| `--temperature 0.05` | lower = conservative, higher = diverse |

This is the common enzyme/binder pocket workflow.

## Choosing between the design skills

- **alterlab-ligandmpnn** — sequence design conditioned on a ligand/metal/nucleic acid.
- **alterlab-proteinmpnn** — sequence design with protein context only.
- **alterlab-rfdiffusion** — generate/scaffold the backbone or functional site.
- **alterlab-boltz** / **alterlab-diffdock** — get a ligand pose (co-fold / dock), not a sequence.

## Pipeline

Scaffold a functional site with `alterlab-rfdiffusion` → design the pocket sequence here →
validate by refolding with `alterlab-alphafold` → obtain a pose/affinity with `alterlab-boltz`
or `alterlab-diffdock`. Batch heavy steps via `alterlab-remote-compute`.
