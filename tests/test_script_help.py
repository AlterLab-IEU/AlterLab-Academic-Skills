"""Every stdlib-only skill CLI answers ``--help`` with usage text and exit 0.

A skill tells the model to run its scripts; a script that treats ``--help`` as an input path
(or blocks waiting on a TTY) costs the model a failed tool call before it learns the
interface. Scripts with third-party imports are skipped here: whether their dependencies are
installed says nothing about the script.
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
STDLIB = set(sys.stdlib_module_names) | {"__future__"}


def _stdlib_clis() -> list[Path]:
    found = []
    for script in sorted(REPO.glob("skills/*/*/scripts/**/*.py")):
        if "__pycache__" in script.parts or script.name.startswith("_"):
            continue
        src = script.read_text(encoding="utf-8", errors="replace")
        if not ("__main__" in src and re.search(r"\bargparse\b|sys\.argv", src)):
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue  # test_scripts_compile.py reports syntax errors
        mods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                mods.add(node.module.split(".")[0])
        local = {p.stem for p in script.parent.glob("*.py")} | {
            p.name for p in script.parent.iterdir() if p.is_dir()}
        if mods - STDLIB - local:
            continue
        found.append(script)
    return found


CLIS = _stdlib_clis()


def test_there_are_stdlib_clis_to_check() -> None:
    assert len(CLIS) >= 50


@pytest.mark.parametrize("script", CLIS, ids=lambda p: p.relative_to(REPO / "skills").as_posix())
def test_help_exits_zero_with_usage(script: Path, tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(script), "--help"], cwd=tmp_path, stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=30,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, f"exit {proc.returncode}: {out.strip()[-300:]}"
    assert re.search(r"usage", out, re.I), f"no usage text: {out.strip()[:300]}"
