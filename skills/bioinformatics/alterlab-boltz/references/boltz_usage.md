# Boltz-2 — Usage Reference

Deeper detail for `alterlab-boltz`, verified against **boltz 2.2.1** (current PyPI release as
of 2026-09) and the upstream `jwohlwend/boltz` prediction docs. Boltz moves fast — re-check
`boltz predict --help` if a flag is rejected.

## Install

```bash
uv pip install 'boltz[cuda]' -U     # drop [cuda] for CPU-only (much slower)
```

Python 3.10–3.12. Weights download on first run and cache in `~/.boltz` (`BOLTZ_CACHE`
overrides the location). Code and weights are MIT-licensed, so commercial use is allowed —
one of the main reasons to pick Boltz over AlphaFold 3's weights terms.

## Input: a YAML spec

FASTA input still parses but is deprecated and cannot express modifications, covalent bonds,
pocket constraints, or affinity. The YAML shape:

```yaml
version: 1
sequences:
  - protein:
      id: [A, B]                 # a list when several chains share a sequence
      sequence: MVTPEG...
      msa: ./msa/seq1.a3m        # omit when using --use_msa_server; 'empty' = single sequence
      modifications:
        - position: 12           # 1-based
          ccd: SEP
      cyclic: false
  - ligand:
      id: C
      smiles: 'N[C@@H](Cc1ccc(O)cc1)C(=O)O'   # or: ccd: SAH  (never both)
  - dna:                          # also: rna
      id: D
      sequence: ATCG...

constraints:
  - pocket:
      binder: C
      contacts: [[A, 42], [A, 46]]   # [chain, residue index] (or atom name for ligands)
      max_distance: 6                # 4–20 Å, default 6
      force: false                   # true adds a potential enforcing it
  - contact:
      token1: [A, 42]
      token2: [C, C1]
      max_distance: 6
  - bond:
      atom1: [A, 12, SG]
      atom2: [C, 1, C7]

templates:
  - cif: ./template.cif
    chain_id: [A]

properties:
  - affinity:
      binder: C
```

Multi-chain custom MSAs use a two-column CSV (`sequence`, `key`) instead of `.a3m`, where
rows sharing a key are treated as paired across chains.

## Run

```bash
boltz predict complex.yaml --out_dir out/ --use_msa_server --use_potentials
boltz predict yaml_dir/   --out_dir out/ --use_msa_server      # batch a directory
```

Flags that matter:

| Flag | Default | Why you'd change it |
|------|---------|---------------------|
| `--use_msa_server` | off | auto-generate MSAs via the ColabFold MMseqs2 server (sends the sequence out) |
| `--msa_server_url` | `https://api.colabfold.com` | point at your own server (basic-auth or API-key flags exist) |
| `--use_potentials` | off | inference-time potentials; better physical plausibility of poses |
| `--diffusion_samples` | 1 | more poses to rank (AF3-like settings: 25 samples, 10 recycles) |
| `--recycling_steps` | 3 | harder targets |
| `--sampling_steps` | 200 | diffusion steps |
| `--output_format` | `mmcif` | `pdb` when downstream tools need it |
| `--override` | off | ignore cached preprocessing/predictions in `--out_dir` |
| `--devices` / `--accelerator` | 1 / gpu | multi-GPU or CPU runs |
| `--diffusion_samples_affinity` | 5 | affinity-head sampling |
| `--affinity_mw_correction` | off | molecular-weight correction on the affinity value |

## Output

```
out/predictions/<input_name>/
  <input_name>_model_0.cif              # ranked by confidence_score
  confidence_<input_name>_model_0.json
  affinity_<input_name>.json            # only when properties.affinity was requested
  pae_/pde_/plddt_<...>.npz
```

`confidence_*.json` keys: `confidence_score` (0.8·complex_plddt + 0.2·iptm — the ranking
number), `ptm`, `iptm`, `ligand_iptm`, `protein_iptm`, `complex_plddt`, `complex_iplddt`,
`complex_pde`, `complex_ipde`, `chains_ptm`, `pair_chains_iptm`. Scores are 0–1 and higher is
better, except the PDE values which are in Å and lower is better.

## Binding affinity

`affinity_*.json` has two ensemble outputs plus their per-model counterparts:

- `affinity_probability_binary` — 0–1 probability that the ligand binds. Use for
  binder-vs-decoy triage in hit discovery.
- `affinity_pred_value` — `log10(IC50)` with IC50 in µM (−3 ≈ 1 nM, 0 ≈ 1 µM, 2 ≈ 100 µM).
  Meant for comparing *active* analogues during hit-to-lead/lead optimisation, not for
  separating actives from inactives. `(6 − y) * 1.364` converts to kcal/mol.

Constraints: exactly one ligand chain as `binder`, protein targets only, ≤128 heavy atoms
(training stayed near 56). Validate top ranks against measured data (`alterlab-bindingdb`).

## Choosing between the folding skills

- **alterlab-boltz** — complex WITH a ligand / nucleic acid, or affinity. MIT-licensed AF3-class.
- **alterlab-alphafold** — protein or protein–protein only (AF2/ColabFold), rich confidence.
- **alterlab-chai** — antibody–antigen and general one-FASTA multi-entity complexes (Chai-1).
- **alterlab-diffdock** — the receptor structure is already known/fixed and you only need to
  place a ligand (docking), not co-fold the protein.

## GPU dispatch

Batch a ligand series against one target as one directory of YAML files via
`alterlab-remote-compute` (submit → poll → harvest).
