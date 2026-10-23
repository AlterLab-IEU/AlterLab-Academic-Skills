---
name: alterlab-remote-compute
description: Dispatch long-running GPU/CPU jobs to remote compute with a provider-agnostic submit → poll → harvest pattern across SLURM/HPC (sbatch, squeue, sacct) and managed APIs (Modal, RunPod, GCP Batch / Vertex AI). Use when submitting a batch job to a cluster, polling job status, retrieving result artifacts from a scheduler or cloud GPU provider, or writing a portable job-submission wrapper; the foundation-model skills (alterlab-alphafold, alterlab-boltz, alterlab-rfdiffusion, and siblings) dispatch their GPU work through this pattern. For Modal-specific serverless container deployment and autoscaling prefer alterlab-modal instead. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*)
compatibility: "No API key required: the portable dispatcher (`scripts/dispatch.py`) is stdlib-only and its keyless `--backend local` runs your job script on this machine so you validate the payload and the submit->poll->harvest flow on CPU (reduced size) with no account. SLURM dispatch needs `sbatch`/`squeue`/`sacct` on an HPC login node (no key); managed cloud backends (RunPod, GCP) are optional and read their token from the environment, never hardcoded. No GPU is needed to submit/poll."
metadata:
    skill-author: AlterLab
    credentials: "optional: RUNPOD_API_KEY / REMOTE_COMPUTE_API_KEY (dispatch to a RunPod-style cloud GPU endpoint); GCP Application Default Credentials (GCP Batch / Vertex AI) — the local and SLURM backends use none"
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# Remote Compute

## Overview

Foundation-model workloads (protein folding, backbone diffusion, single-cell models) need a
GPU and can run for minutes to hours — too long to sit in a synchronous call. This skill is
the **provider-agnostic dispatch layer** the GPU skills build on: a single **submit → poll →
harvest** contract that works the same whether the backend is a SLURM cluster, Modal, RunPod,
or GCP. You describe the job once; the dispatcher submits it, returns a handle, polls status
to a terminal state, and harvests the output artifacts.

It does **not** wrap any single model — each model skill (`alterlab-alphafold`,
`alterlab-boltz`, `alterlab-proteinmpnn`, …) describes *what* to run; this skill describes
*where and how* to run it.

## When to Use This Skill

Use this skill when the user wants to:
- Submit a batch job to a SLURM/HPC cluster and track it to completion (`sbatch` → `sacct`).
- Run a GPU job on a managed provider (Modal, RunPod, GCP Batch / Vertex AI) and retrieve results.
- Write a portable job wrapper that runs the *same* payload across more than one backend.
- Poll a long-running remote job's status and harvest its output files/artifacts.

### Does NOT Trigger

| Scenario | Use instead |
|----------|-------------|
| Deploy a serverless container / autoscaling API specifically on **Modal** | `alterlab-modal` |
| Actually **fold a structure**, design a sequence, or run a specific model | the model's own skill (`alterlab-alphafold`, `alterlab-boltz`, `alterlab-proteinmpnn`, …) |
| Local single-machine data analysis with no remote dispatch | the relevant analysis skill (`alterlab-scanpy`, `alterlab-rdkit`, …) |
| Query a database over HTTP | the database connector skill (`alterlab-pdb`, `alterlab-uniprot`, …) |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-modal`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

## Keyless by default: validate locally before you dispatch

Before sending a job to a cluster or a cloud GPU — which costs money and needs an account —
run it on this machine to confirm the payload works. `scripts/dispatch.py` has a keyless
**`local`** backend (`--backend local`; `--backend` is required on every call, there is no
default) that executes your job script and records its status through the same
submit → poll contract, so the dry run looks exactly like the real dispatch:

```bash
# Write a small, CPU-sized runner (reduced input) for the payload you will later scale up:
cat > run_local.sh <<'SH'
#!/bin/bash
python3 run_model.py --in sample.fasta --out out/ --max-samples 2   # tiny, CPU
SH

# KEYLESS: runs here, no account, no token, no GPU.
H=$(python scripts/dispatch.py submit --backend local --script run_local.sh)
python scripts/dispatch.py poll --backend local --handle "$H"   # SUCCEEDED / FAILED
cat .remote-compute-local/$H/stdout.log
```

Only once the logic is validated do you switch `--backend slurm` (an HPC login node) or
`--backend rest` (a cloud GPU endpoint) for the full-size run. The cloud/`rest` backend
refuses to run without a credential rather than silently using another backend. Keep the
cost cautions below in mind on the first real dispatch.

## The submit → poll → harvest contract

Every backend implements three verbs. Keeping the payload backend-independent is what makes a
model skill portable across an HPC allocation and a cloud GPU:

1. **submit(spec) → handle** — enqueue the job; return an opaque handle (SLURM job id, Modal
   call id, RunPod job id, GCP operation name).
2. **poll(handle) → status** — map the backend's states to a common vocabulary:
   `PENDING | RUNNING | SUCCEEDED | FAILED | CANCELLED | UNKNOWN`. Poll on a backoff; never
   busy-loop.
3. **harvest(handle) → artifacts** — copy the declared output files back to a local `out/`
   directory (scp/rsync from HPC scratch; object-store download for cloud).

`scripts/dispatch.py` implements submit and poll (plus cancel for SLURM) for the SLURM and a
generic REST backend, and defines the status vocabulary so model skills can depend on it;
harvest is a copy step (rsync/scp or object-store download) shown in `references/providers.md`. Provider-specific command and
API detail lives in `references/providers.md` (loaded on demand).

## Core Capabilities

### 1. SLURM / HPC clusters

The classic scheduler path. Submit a job script with resource directives, then poll with
`sacct` (authoritative for terminal state) rather than only `squeue` (which drops finished
jobs from its default view):

```bash
# Submit; capture the numeric job id from "Submitted batch job <id>"
JOBID=$(sbatch --parsable run.slurm)

# Poll to a terminal state (COMPLETED / FAILED / CANCELLED / TIMEOUT)
sacct -j "$JOBID" --format=State,ExitCode,Elapsed --noheader --parsable2
```

A minimal GPU job script (`run.slurm`) — one GPU, an 8-hour wall clock, results on scratch:

```bash
#!/bin/bash
#SBATCH --job-name=fold
#SBATCH --gres=gpu:1
#SBATCH --time=08:00:00
#SBATCH --output=%x-%j.out
srun uv run python run_model.py --in input.fasta --out "$SCRATCH/out"
```

Full directive reference, array jobs, and `squeue`/`scancel` usage: see
`references/providers.md`.

### 2. Modal — managed serverless GPU

For serverless containers, autoscaling, and `.remote()` dispatch, this skill defers to
`alterlab-modal`, which owns the Modal SDK surface. Use Modal when you want zero cluster
management and per-second GPU billing. This skill's role is only to treat a Modal call as one
`submit → poll → harvest` backend when a workflow needs to stay provider-agnostic.

### 3. RunPod — on-demand GPU pods

RunPod exposes GPU pods and a serverless endpoint API. Submit to a serverless endpoint and
poll the returned job id; the API key is read from `RUNPOD_API_KEY` and sent as a bearer token. Endpoint/run/status
paths and the pod vs. serverless trade-off are in `references/providers.md`.

### 4. GCP — Batch and Vertex AI

Google Cloud offers **Batch** (containerized batch jobs with GPU allocation) and **Vertex AI**
custom jobs (ML-oriented, managed). Both follow submit → poll (operation/job state) → harvest
(read outputs from a GCS bucket). Auth uses Application Default Credentials; the target bucket
comes from an env var. Command/SDK detail: `references/providers.md`.

### 5. Portable job wrapper

`scripts/dispatch.py` is a stdlib-only CLI that runs the same job spec across backends.
Every call names its backend with `--backend local|slurm|rest` — it is required, so a
cluster batch script is never run on the login node by accident; `local` is the keyless
choice for validating a job on this machine first:

```bash
# Keyless local validation (--backend local) — no account
python scripts/dispatch.py submit --backend local --script run_local.sh

# Submit a SLURM job and print the handle
python scripts/dispatch.py submit --backend slurm --script run.slurm

# Poll a handle to a normalized status
python scripts/dispatch.py poll --backend slurm --handle 123456

# Generic REST backend (RunPod-style): endpoint + key from env
python scripts/dispatch.py submit --backend rest \
  --endpoint "$RUNPOD_ENDPOINT" --payload spec.json
```

It runs the script locally for the keyless `local` backend, shells out to `sbatch`/`sacct`
for SLURM, and uses `urllib` for the REST backend — no third-party dependencies, so it runs
anywhere Python does.

## Validation and status semantics

- **Trust the accounting record, not the queue.** On SLURM, a job missing from `squeue` may
  have finished *or* failed — resolve terminal state with `sacct`/exit code, not absence.
- **Poll with backoff** (e.g. 10s → 30s → 60s, capped) so you neither hammer the scheduler
  nor miss a fast job.
- **Always check the exit code**, not just the state string; a job can report `COMPLETED`
  while the payload wrote no artifacts. Harvest, then verify the expected files exist.
- **Never hardcode credentials.** Read `RUNPOD_API_KEY`, GCP ADC, and cluster hosts from the
  environment; the dispatcher refuses to run if a required secret is unset.

## Resources

- `references/providers.md` — per-backend command/API detail (SLURM directives, RunPod
  endpoints, GCP Batch/Vertex, Modal cross-link) loaded on demand.
- `scripts/dispatch.py` — stdlib-only `submit`/`poll`/`cancel` CLI; keyless `local` backend
  (`--backend local`) for on-machine validation, plus SLURM and generic REST (cloud) backends.

Part of the AlterLab Academic Skills suite.
