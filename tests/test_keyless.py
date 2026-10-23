"""Keyless-first: every skill does what it claims without an external API key."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import check_keyless  # noqa: E402


def test_every_skill_is_keyless_first() -> None:
    report = {d.name: v for d in check_keyless.skill_dirs() if (v := check_keyless.check(d))}
    assert not report, "\n".join(f"{n}: {v}" for n, vs in report.items() for v in vs)


def test_a_required_key_is_reported(tmp_path, monkeypatch) -> None:
    skill = tmp_path / "skills" / "x" / "alterlab-demo"
    (skill / "evals").mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: alterlab-demo\ndescription: Demo.\ncompatibility: Requires a free "
        "DEMO_API_KEY.\nmetadata:\n    skill-author: AlterLab\n    version: \"1.0.0\"\n---\n"
        "Set DEMO_API_KEY first.\n", encoding="utf-8")
    (skill / "evals" / "evals.json").write_text(
        '{"skill": "alterlab-demo", "evals": [{"id": "a", "requires": ["env:DEMO_API_KEY"], '
        '"assertions": [{"type": "should_trigger", "value": true}]}]}', encoding="utf-8")
    found = " ".join(check_keyless.check(skill))
    assert "K1" in found and "K2" in found and "K3" in found


def test_declared_optional_credentials_pass(tmp_path) -> None:
    skill = tmp_path / "skills" / "x" / "alterlab-demo"
    (skill / "evals").mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: alterlab-demo\ndescription: Demo.\ncompatibility: No API key required; "
        "an optional DEMO_API_KEY raises the rate limit.\nmetadata:\n    skill-author: AlterLab\n"
        "    version: \"1.0.0\"\n    credentials: \"optional: DEMO_API_KEY (higher rate limit)\"\n"
        "---\nOptionally set DEMO_API_KEY. Example: export YOUR_API_KEY=...\n", encoding="utf-8")
    trig = '{"id": "%s", "assertions": [{"type": "should_trigger", "value": true}]}'
    (skill / "evals" / "evals.json").write_text(
        '{"skill": "alterlab-demo", "evals": [%s]}' % ", ".join(trig % i for i in "abc"),
        encoding="utf-8")
    assert check_keyless.check(skill) == []


def test_cli_exit_status_reflects_findings() -> None:
    proc = subprocess.run([sys.executable, str(REPO / "scripts" / "check_keyless.py")],
                          capture_output=True, text=True)
    assert proc.returncode in (0, 1) and "checked." in proc.stdout
