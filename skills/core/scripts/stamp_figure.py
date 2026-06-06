#!/usr/bin/env python3
"""PostToolUse figure-stamping hook for the alterlab-core plugin.

Reads the hook payload on stdin (the standard Claude Code hook JSON), and when the
tool just wrote/edited a figure or render file, embeds reproducibility provenance —
the current git SHA (with a +dirty marker) and a UTC timestamp — directly into the
file's metadata so any published figure can be traced back to the code that made it.

Two stamping back-ends, in order:
  1. exiftool (if installed)  -> XMP-dc:Source / Creator on PNG, JPG, TIFF, WebP,
     PDF, SVG, MP4, MOV  (the broad path).
  2. stdlib PNG tEXt writer   -> for .png only, when exiftool is absent. This mirrors
     matplotlib's `savefig(..., metadata=...)` tEXt chunks, so the stamp survives.

Design rules:
  - Self-contained: standard library only (plus optional `exiftool` binary). No
    third-party imports, no reference to any other skill.
  - Never breaks the session: any error -> print a note to stderr and exit 0.
  - Idempotent-ish: re-stamping just overwrites the provenance fields.
"""
from __future__ import annotations

import json
import os
import shutil
import struct
import subprocess
import sys
import zlib
from datetime import datetime, timezone
from pathlib import Path

# File extensions we treat as "figures / renders" worth stamping.
EXIFTOOL_EXTS = {
    ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp",
    ".pdf", ".svg", ".mp4", ".mov", ".gif",
}


def _git(args: list[str], cwd: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip()


def build_stamp(file_path: Path) -> str | None:
    """git:<sha>[+dirty] <UTC ISO8601>, or None if not in a git repo."""
    repo_dir = file_path.parent
    sha = _git(["rev-parse", "--short", "HEAD"], repo_dir)
    if not sha:
        return None
    porcelain = _git(["status", "--porcelain"], repo_dir)
    dirty = "+dirty" if porcelain else ""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"git:{sha}{dirty} {ts}"


def stamp_with_exiftool(file_path: Path, stamp: str) -> bool:
    exiftool = shutil.which("exiftool")
    if not exiftool:
        return False
    try:
        res = subprocess.run(
            [
                exiftool,
                "-overwrite_original",
                "-q",
                f"-XMP-dc:Source={stamp}",
                "-XMP-dc:Creator=AlterLab",
                str(file_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return res.returncode == 0


def stamp_png_text(file_path: Path, stamp: str) -> bool:
    """Append a tEXt chunk (key 'Source') to a PNG using only the stdlib.

    Mirrors matplotlib's PNG metadata path so reading it back with
    PIL Image.open(...).text or exiftool returns the stamp.
    """
    try:
        raw = file_path.read_bytes()
    except OSError:
        return False
    sig = b"\x89PNG\r\n\x1a\n"
    if not raw.startswith(sig):
        return False
    # Locate IEND so we can splice the tEXt chunk in just before it.
    iend = raw.rfind(b"IEND")
    if iend < 4:
        return False
    insert_at = iend - 4  # start of IEND's length field

    keyword = b"Source"
    data = keyword + b"\x00" + stamp.encode("latin-1", "replace")
    chunk = (
        struct.pack(">I", len(data))
        + b"tEXt"
        + data
        + struct.pack(">I", zlib.crc32(b"tEXt" + data) & 0xFFFFFFFF)
    )
    new = raw[:insert_at] + chunk + raw[insert_at:]
    try:
        file_path.write_bytes(new)
    except OSError:
        return False
    return True


def extract_path(payload: dict) -> Path | None:
    tool_input = payload.get("tool_input") or {}
    # Write/Edit/MultiEdit use file_path; NotebookEdit uses notebook_path.
    candidate = (
        tool_input.get("file_path")
        or tool_input.get("notebook_path")
        or tool_input.get("path")
    )
    if not candidate:
        return None
    p = Path(candidate)
    if not p.is_absolute():
        base = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        p = Path(base) / p
    return p


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # nothing to do, never block the tool

    file_path = extract_path(payload)
    if file_path is None:
        return 0
    if file_path.suffix.lower() not in EXIFTOOL_EXTS:
        return 0  # not a figure/render; ignore source edits, configs, etc.
    if not file_path.is_file():
        return 0

    stamp = build_stamp(file_path)
    if stamp is None:
        # Not inside a git repo: nothing reproducible to stamp.
        return 0

    ok = stamp_with_exiftool(file_path, stamp)
    if not ok and file_path.suffix.lower() == ".png":
        ok = stamp_png_text(file_path, stamp)

    if ok:
        print(f"[figure-provenance] stamped {file_path.name}: {stamp}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
