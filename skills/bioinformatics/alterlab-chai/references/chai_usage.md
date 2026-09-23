# Chai-1 — Usage Reference

Deeper detail for `alterlab-chai`, verified against **chai_lab 0.6.1** (current PyPI release
as of 2026-09) and the upstream `chaidiscovery/chai-lab` docs. The project pins its own
version in its README ("API is quite stable, but pin the version"), so pin it in your env too.

## Install

```bash
uv pip install chai_lab==0.6.1
# bleeding edge (updates daily): uv pip install git+https://github.com/chaidiscovery/chai-lab.git
```

Requires Linux, Python >= 3.10, and a CUDA GPU with bfloat16 support. A100/H100 80GB or
L40S 48GB are recommended; A10/A30 and consumer RTX 4090 handle smaller complexes. Weights
download on first use into the installed package directory unless `CHAI_DOWNLOADS_DIR`
points elsewhere (useful in Docker or on a mounted drive).

## Input: one typed FASTA

```text
>protein|name=heavy-chain
EVQLVESGG...
>protein|name=antigen
MKTAYIAKQ...
>ligand|name=cofactor
CC(=O)Oc1ccccc1C(=O)O
>rna|name=aptamer
AGCUUAGC
```

- Entity types: `protein`, `ligand` (SMILES), `rna`, `dna`, `glycan`.
- Header is `type|name=<label>`; the bare `type|label` form also parses. Labels must be
  unique across the file.
- Modified residues go inline in brackets: `AAA(SEP)AAA`.
- Chai warns (rather than fails) when a sequence looks like a different entity type than the
  header claims — read the log.

## Run

```bash
chai-lab fold input.fasta output_dir/
chai-lab fold --use-msa-server --use-templates-server input.fasta output_dir/
chai-lab fold --use-msa-server --msa-server-url https://my-colabfold input.fasta output_dir/
chai-lab a3m-to-pqt msa_dir/        # convert local a3m MSAs to Chai's aligned.pqt
```

The output directory must be empty. Five diffusion samples are produced by default.

Python API:

```python
from chai_lab.chai1 import run_inference

candidates = run_inference(
    fasta_file=fasta_path,
    output_dir=output_dir,
    use_esm_embeddings=True,
    use_msa_server=False,          # msa_directory=... for local MSAs
    constraint_path=None,          # restraints CSV
    num_trunk_recycles=3,
    num_diffn_timesteps=200,
    num_diffn_samples=5,
    seed=42,
    device="cuda:0",
)
cif_paths = candidates.cif_paths
scores = [rd.aggregate_score.item() for rd in candidates.ranking_data]
```

`run_folding_on_context` is the lower-level entry point when you want to build the feature
context (custom templates, embeddings, covalent bonds) yourself.

## MSAs

Single-sequence by default. `--use-msa-server` queries the shared ColabFold MMseqs2 server
— a community resource, and it sends your sequence off-machine, so say so for unpublished
work. Local MSAs are `aligned.pqt` files (a3m plus source/pairing-key columns); convert with
`chai a3m-to-pqt`. Note Chai's published benchmarks used a different search strategy than
MMseqs2, so hosted-MSA results may differ slightly from the paper.

## Restraints

A CSV passed as `constraint_path` / `--constraint-path`:

| restraint_id | chainA | res_idxA | chainB | res_idxB | connection_type | confidence | min_distance_angstrom | max_distance_angstrom | comment |
|---|---|---|---|---|---|---|---|---|---|
| restraint0 | A | R84 | C | G7 | contact | 1.0 | 0.0 | 22.0 | residue↔residue |
| restraint1 | C |  | A | S18 | pocket | 1.0 | 0.0 | 11.0 | chain↔residue |

- `contact` pins two specific residues in different chains; `pocket` is coarser and
  asymmetric (any residue of chain A against a named residue of chain B), so `res_idxA` is
  blank.
- Residue references are the one-letter residue plus its 1-based index (`D4`); Chai checks
  that the residue matches the sequence and errors on a mismatch.
- Chains are lettered A–Z in the order entities appear in the FASTA.
- `confidence` and `min_distance_angstrom` are accepted but currently unused by the model.
- `restraint_id` must be unique; `comment` is ignored.

## Outputs

Per run: `pred.model_idx_{0..4}.cif` and `scores.model_idx_N.npz`. The score arrays are
`aggregate_score` (ranking), `ptm`, `iptm`, `per_chain_ptm`, `per_chain_pair_iptm`,
`has_inter_chain_clashes`, `chain_chain_clashes`. For an interface question read the relevant
`per_chain_pair_iptm` cell and the clash flags, not just `aggregate_score`.

## Choosing between the folding skills

| Task | Skill |
|------|-------|
| Antibody–antigen; mixed one-FASTA assembly; restraint-guided folding | `alterlab-chai` |
| Protein–ligand co-fold **with binding affinity** | `alterlab-boltz` |
| Protein / protein–protein only (AF2 confidence) | `alterlab-alphafold` |
| Ligand pose into a **fixed** receptor (docking) | `alterlab-diffdock` |

## GPU dispatch

Batch an antibody panel against one antigen as separate predictions via
`alterlab-remote-compute` (submit → poll → harvest).
