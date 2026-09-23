# ProteinMPNN — Usage Reference

Deeper detail for `alterlab-proteinmpnn`. Script names and flags below were checked against the
upstream `dauparas/ProteinMPNN` README (2026-09); forks vary, so confirm against the checkout
you actually run.

## Install

Clone `dauparas/ProteinMPNN`; it ships model weights in-repo (no download). Needs PyTorch —
CPU is fine for typical designs; a GPU only helps very large batches.

The same weights are also served by the newer `dauparas/LigandMPNN` repo via
`--model_type protein_mpnn`. If a project already runs LigandMPNN, keep one checkout rather than
two: the LigandMPNN CLI names residues directly (`A23`) instead of requiring the JSONL helper
scripts below, which is usually less error-prone. Use this repo when you want the original CLI,
the `--ca_only` models, or the tied-positions helpers.

## Inputs (helper scripts)

ProteinMPNN reads a parsed JSONL describing chains and optional constraints, produced by the
repo's `helper_scripts/`:

- `parse_multiple_chains.py` — turn PDB(s) into the parsed JSONL.
- `assign_fixed_chains.py` — choose which chains are designed vs. fixed.
- `make_fixed_positions_dict.py` — pin specific residues (keep catalytic/known positions).
- `make_tied_positions_dict.py` — tie positions across chains for symmetry.
- `make_bias_AA.py` — up/down-weight specific amino acids (e.g. avoid Cys).

## Key run flags

| Flag | Purpose |
|------|---------|
| `--num_seq_per_target N` | sequences designed per backbone (default 1) |
| `--sampling_temp "0.1"` | sampling temperature(s), space-separated string; suggested 0.1–0.3, lower = conservative |
| `--pdb_path` / `--pdb_path_chains` | single structure, and which chains to design |
| `--jsonl_path` | parsed JSONL from `parse_multiple_chains.py` (batch mode) |
| `--out_folder` | output directory |
| `--model_name` | `v_48_002 / v_48_010 / v_48_020 / v_48_030` — the suffix is training-noise in 0.01 Å; `v_48_020` is the default and the usual choice |
| `--use_soluble_model` | load the soluble-only weights |
| `--ca_only` | parse CA-only backbones and use the CA model set |
| `--save_score` / `--score_only` | write `-log_prob` scores to `.npy` |
| `--seed` | 0 (default) picks a random seed |

## Output

A FASTA per target with several designs; headers carry the model **score** (lower is better)
and native-sequence recovery. Rank by score, then validate the top designs.

## Choosing between the design skills

- **alterlab-proteinmpnn** — sequence for a fixed backbone, no ligand context.
- **alterlab-ligandmpnn** — same idea but with ligand/metal/nucleic-acid context (pocket design).
- **alterlab-rfdiffusion** — generate the backbone itself (upstream of MPNN).
- **alterlab-esm** — generative multimodal design / ESM inverse folding.

## Design → fold → score

Feed each designed sequence to `alterlab-alphafold`, refold, and accept only self-consistent
designs (return to the intended backbone, high pLDDT, low PAE). Batch the folds via
`alterlab-remote-compute`.
