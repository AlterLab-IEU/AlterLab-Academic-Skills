"""The generated portability doc must stay current with the tree."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import gen_portability as gp  # noqa: E402


def test_portability_doc_is_current() -> None:
    rendered = gp.render()
    on_disk = gp.OUT.read_text(encoding="utf-8") if gp.OUT.exists() else ""
    assert on_disk == rendered, (
        "docs/portability.md is stale — regenerate with "
        "`python3 scripts/gen_portability.py` and commit the result."
    )
