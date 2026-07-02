"""SECURITY_SCAN.md must stay clean and current.

The trust manifest is a CI-attested claim: no shell-pipe, no ``os.system`` / ``shell=True``,
no ``eval``/``exec`` on input, no hardcoded secrets, and a fully-enumerated outbound-host
allowlist. These tests keep that claim honest — a new skill that shells out unsafely, inlines
a key, or talks to a new host makes CI fail until the manifest is regenerated and the code
reviewed.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import gen_security_scan as gss  # noqa: E402


def test_shipped_code_has_no_dangerous_patterns() -> None:
    result = gss.scan()
    offenders = {k: v for k, v in result["danger"].items() if v}
    assert not offenders, (
        "shipped skill code triggered the security scan (shell-pipe / os.system / "
        f"shell=True / eval-exec / hardcoded secret): {offenders}"
    )


def test_security_scan_manifest_is_current() -> None:
    result = gss.scan()
    rendered = gss.render(result)
    on_disk = gss.OUT.read_text(encoding="utf-8") if gss.OUT.exists() else ""
    assert on_disk == rendered, (
        "SECURITY_SCAN.md is stale — regenerate with `python3 scripts/gen_security_scan.py` "
        "and commit the result."
    )
