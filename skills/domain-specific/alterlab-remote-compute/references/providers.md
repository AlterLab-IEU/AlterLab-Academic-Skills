# Remote Compute — Provider Reference

Per-backend command and API detail for the `submit → poll → harvest` contract. Loaded on
demand from the SKILL.md Core Capabilities section.

## SLURM / HPC

### Submit

```bash
# --parsable prints only the numeric job id (plus cluster, if federated)
JOBID=$(sbatch --parsable run.slurm)
```

Common resource directives (top of the job script, `#SBATCH` lines):

| Directive | Meaning |
|-----------|---------|
| `--gres=gpu:1` | request 1 GPU (use `gpu:a100:1` to pin a type where the site supports it) |
| `--cpus-per-task=8` | CPU cores |
| `--mem=32G` | RAM |
| `--time=08:00:00` | wall-clock limit (HH:MM:SS) |
| `--partition=gpu` | target partition/queue |
| `--array=0-9` | array job (10 tasks; `$SLURM_ARRAY_TASK_ID` selects input) |
| `--output=%x-%j.out` | stdout file (`%x`=name, `%j`=job id) |

### Poll

```bash
# squeue shows only ACTIVE jobs (pending/running) — a finished job disappears from it.
squeue -j "$JOBID" --noheader --format='%T' 2>/dev/null

# sacct is authoritative for terminal state and exit code (accounting DB).
sacct -j "$JOBID" --format=State,ExitCode,Elapsed --noheader --parsable2
```

State → normalized status: `PENDING/CONFIGURING → PENDING`; `RUNNING/COMPLETING → RUNNING`;
`COMPLETED → SUCCEEDED`; `FAILED/TIMEOUT/OUT_OF_MEMORY/NODE_FAIL → FAILED`;
`CANCELLED → CANCELLED`.

### Cancel / harvest

```bash
scancel "$JOBID"
# Harvest: results usually land on $SCRATCH; copy back with rsync/scp.
rsync -a "login-node:$SCRATCH/out/" ./out/
```

## RunPod

Serverless endpoints expose run/status/cancel over REST. The API key is read from
`RUNPOD_API_KEY` (never hardcode it).

```bash
# Submit
curl -s -H "Authorization: $RUNPOD_API_KEY" -H "Content-Type: application/json" \
  -d @spec.json "https://api.runpod.ai/v2/<ENDPOINT_ID>/run"
# → {"id": "<job-id>", "status": "IN_QUEUE"}

# Poll
curl -s -H "Authorization: $RUNPOD_API_KEY" \
  "https://api.runpod.ai/v2/<ENDPOINT_ID>/status/<job-id>"
```

Status → normalized: `IN_QUEUE → PENDING`; `IN_PROGRESS → RUNNING`; `COMPLETED → SUCCEEDED`;
`FAILED → FAILED`; `CANCELLED → CANCELLED`. Pods (persistent GPU VMs) are the alternative when
a workload needs a long-lived box rather than a per-request endpoint.

## GCP — Batch and Vertex AI

- **Batch**: containerized batch jobs with GPU allocation. Auth via Application Default
  Credentials (`gcloud auth application-default login`). Submit a job, poll the job state,
  read outputs from a GCS bucket (`GCS_OUTPUT_BUCKET`).
- **Vertex AI custom jobs**: managed ML training/inference jobs; state polled via the job
  resource; artifacts written to a staging bucket.

Both map to submit → poll (`QUEUED/SCHEDULED → PENDING`, `RUNNING → RUNNING`,
`SUCCEEDED → SUCCEEDED`, `FAILED → FAILED`) → harvest (GCS download). Verify exact resource
names against the current `gcloud`/SDK version — `TODO(verify)` before pinning a command.

## Modal

Modal is owned by `alterlab-modal` (serverless containers, `.remote()`, autoscaling,
per-second GPU billing). When staying provider-agnostic, treat a Modal function call as one
backend: `.spawn()` returns a call id (submit), `.get()` polls/blocks (poll), and the return
value or a mounted volume carries artifacts (harvest). See `alterlab-modal` for the SDK.
