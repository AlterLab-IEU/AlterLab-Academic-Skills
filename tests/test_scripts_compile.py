"""Every skills/**/scripts/*.py must byte-compile cleanly.

This is a syntax-only gate: it runs `py_compile` (which parses and compiles
to bytecode) on each script. It does NOT import the module, so missing
third-party dependencies never cause a failure — only genuine SyntaxErrors do.

Genuine failures are ratcheted via known_failures.SCRIPTS_COMPILE_FAILURES so
CI stays green while the debt stays visible. Fix one and remove its entry; if
it regresses the test flips from XPASS to a hard failure.
"""

from __future__ import annotations

import py_compile
from pathlib import Path

import pytest

from tests.known_failures import SCRIPTS_COMPILE_FAILURES

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

SCRIPT_FILES = sorted(SKILLS_DIR.glob("*/*/scripts/*.py"))
SCRIPT_IDS = [str(p.relative_to(REPO_ROOT)) for p in SCRIPT_FILES]


def test_script_files_discovered() -> None:
    """Guard against a glob that silently matches nothing."""
    assert SCRIPT_FILES, "no skills/**/scripts/*.py files were discovered"


@pytest.mark.parametrize("script", SCRIPT_FILES, ids=SCRIPT_IDS)
def test_script_compiles(script: Path) -> None:
    rel = str(script.relative_to(REPO_ROOT))
    if rel in SCRIPTS_COMPILE_FAILURES:
        pytest.xfail(f"known compile debt: {SCRIPTS_COMPILE_FAILURES[rel]}")
    try:
        py_compile.compile(str(script), doraise=True)
    except py_compile.PyCompileError as exc:  # pragma: no cover - failure path
        pytest.fail(f"{rel} failed to compile:\n{exc.msg}")
