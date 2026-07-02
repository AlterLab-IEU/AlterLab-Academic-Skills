#!/usr/bin/env python3
"""Provider-agnostic remote-compute dispatcher: submit -> poll -> harvest.

Stdlib-only (subprocess + urllib), so it runs anywhere Python does. Implements the two
backends that need no third-party SDK:

* ``slurm`` — shells out to ``sbatch``/``sacct``/``scancel`` on an HPC login node.
* ``rest``  — a generic HTTP job API (RunPod-style ``/run`` + ``/status/<id>``); the API key
  is read from an environment variable, never a flag, so it never lands in shell history.

The status vocabulary below is the common contract the AlterLab GPU model skills depend on.

    python dispatch.py submit --backend slurm --script run.slurm
    python dispatch.py poll   --backend slurm --handle 123456
    python dispatch.py submit --backend rest --endpoint "$RUNPOD_ENDPOINT" --payload spec.json
    python dispatch.py poll   --backend rest --endpoint "$RUNPOD_ENDPOINT" --handle <job-id>
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

# Common status vocabulary (every backend maps its native states onto these).
PENDING, RUNNING, SUCCEEDED, FAILED, CANCELLED, UNKNOWN = (
    "PENDING", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED", "UNKNOWN",
)

_SLURM_MAP = {
    "PENDING": PENDING, "CONFIGURING": PENDING,
    "RUNNING": RUNNING, "COMPLETING": RUNNING,
    "COMPLETED": SUCCEEDED,
    "FAILED": FAILED, "TIMEOUT": FAILED, "OUT_OF_MEMORY": FAILED, "NODE_FAIL": FAILED,
    "CANCELLED": CANCELLED,
}
_REST_MAP = {
    "IN_QUEUE": PENDING, "QUEUED": PENDING, "PENDING": PENDING,
    "IN_PROGRESS": RUNNING, "RUNNING": RUNNING,
    "COMPLETED": SUCCEEDED, "SUCCEEDED": SUCCEEDED,
    "FAILED": FAILED, "ERROR": FAILED,
    "CANCELLED": CANCELLED, "CANCELED": CANCELLED,
}


def _run(cmd: list[str]) -> str:
    """Run a command, return stdout, raise SystemExit with a clear message on failure."""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        raise SystemExit(f"error: '{cmd[0]}' not found on PATH (run on an HPC login node?)")
    if proc.returncode != 0:
        raise SystemExit(f"error: {' '.join(cmd)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


# --- SLURM backend ----------------------------------------------------------------------
def slurm_submit(script: str) -> str:
    return _run(["sbatch", "--parsable", script]).split(";")[0]


def slurm_poll(handle: str) -> str:
    out = _run(["sacct", "-j", handle, "--format=State", "--noheader", "--parsable2"])
    if not out:  # not yet in the accounting DB, or still queued
        return PENDING
    state = out.splitlines()[0].split("|")[0].strip().split()[0]  # strip "CANCELLED by ..."
    return _SLURM_MAP.get(state, UNKNOWN)


def slurm_cancel(handle: str) -> None:
    _run(["scancel", handle])


# --- Generic REST backend ---------------------------------------------------------------
def _rest_key() -> str:
    key = os.environ.get("REMOTE_COMPUTE_API_KEY") or os.environ.get("RUNPOD_API_KEY")
    if not key:
        raise SystemExit(
            "error: set REMOTE_COMPUTE_API_KEY (or RUNPOD_API_KEY) — the REST backend "
            "refuses to run without a credential in the environment."
        )
    return key


def _rest_request(url: str, data: bytes | None = None) -> dict:
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET")
    req.add_header("Authorization", _rest_key())
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 (trusted endpoint)
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise SystemExit(f"error: request to {url} failed: {exc}")


def rest_submit(endpoint: str, payload_path: str) -> str:
    with open(payload_path, "rb") as fh:
        body = fh.read()
    resp = _rest_request(endpoint.rstrip("/") + "/run", data=body)
    handle = resp.get("id") or resp.get("jobId")
    if not handle:
        raise SystemExit(f"error: no job id in response: {resp}")
    return str(handle)


def rest_poll(endpoint: str, handle: str) -> str:
    resp = _rest_request(f"{endpoint.rstrip('/')}/status/{handle}")
    native = str(resp.get("status", "")).upper()
    return _REST_MAP.get(native, UNKNOWN)


# --- CLI --------------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("action", choices=["submit", "poll", "cancel"])
    ap.add_argument("--backend", choices=["slurm", "rest"], required=True)
    ap.add_argument("--script", help="(slurm submit) path to the job script")
    ap.add_argument("--handle", help="job handle from a prior submit")
    ap.add_argument("--endpoint", help="(rest) base endpoint URL")
    ap.add_argument("--payload", help="(rest submit) path to the JSON job spec")
    args = ap.parse_args(argv)

    if args.backend == "slurm":
        if args.action == "submit":
            if not args.script:
                ap.error("--script is required for slurm submit")
            print(slurm_submit(args.script))
        elif args.action == "poll":
            if not args.handle:
                ap.error("--handle is required for poll")
            print(slurm_poll(args.handle))
        else:
            if not args.handle:
                ap.error("--handle is required for cancel")
            slurm_cancel(args.handle)
            print(CANCELLED)
    else:  # rest
        if not args.endpoint:
            ap.error("--endpoint is required for the rest backend")
        if args.action == "submit":
            if not args.payload:
                ap.error("--payload is required for rest submit")
            print(rest_submit(args.endpoint, args.payload))
        elif args.action == "poll":
            if not args.handle:
                ap.error("--handle is required for poll")
            print(rest_poll(args.endpoint, args.handle))
        else:
            ap.error("cancel is not implemented for the generic rest backend")
    return 0


if __name__ == "__main__":
    sys.exit(main())
