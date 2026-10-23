"""defect_scan.py classifies model-independent failures in saved behavioral results."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import defect_scan  # noqa: E402


def _results(tmp_path: Path, runs_by_arm: dict) -> Path:
    case = {"skill": "alterlab-x", "eval_id": "e1"}
    for arm, (outcome, runs) in runs_by_arm.items():
        case[arm] = {"outcome": outcome, "runs": runs}
    p = tmp_path / "behavioral-20260101T000000Z.json"
    p.write_text(json.dumps({"cases": [case]}), encoding="utf-8")
    return p


def test_each_category_is_detected(tmp_path) -> None:
    p = _results(tmp_path, {
        "skilled": ("FAIL", [{"call_outcome": "answer", "permission_denials": 2,
                              "denied_tools": ["Bash: uv pip install semopy"],
                              "response": "Your draft didn't come through, and installing "
                                          "semopy needs your approval. Traceback (most recent "
                                          "call last): ModuleNotFoundError: semopy"}]),
        "bare": ("INFRA_ERROR", [{"call_outcome": "infra_error", "response": None}]),
    })
    rows = {r["arm"]: r for r in defect_scan.scan_file(p)}
    assert set(rows["skilled"]["defects"]) == {"input_missing", "install_blocked",
                                               "script_error", "tool_denied"}
    assert rows["skilled"]["denied_tools"] == ["Bash: uv pip install semopy"]
    assert rows["bare"]["defects"] == ["no_answer"]


def test_a_clean_answer_has_no_defects(tmp_path) -> None:
    p = _results(tmp_path, {"skilled": ("PASS", [{"call_outcome": "answer",
                                                  "permission_denials": 0,
                                                  "response": "Pooled g = 0.38 [0.28, 0.47]."}])})
    assert defect_scan.scan_file(p) == []


def test_turkish_missing_input_is_detected(tmp_path) -> None:
    p = _results(tmp_path, {"skilled": ("FAIL", [{"call_outcome": "answer",
                                                  "response": "Makale metni bana ulaşmadı."}])})
    assert defect_scan.scan_file(p)[0]["defects"] == ["input_missing"]


def test_cli_summarises_a_directory(tmp_path, capsys) -> None:
    _results(tmp_path, {"skilled": ("FAIL", [{"call_outcome": "answer",
                                              "response": "The fixtures/ folder is empty."}])})
    assert defect_scan.main([str(tmp_path), "--json", str(tmp_path / "d.json")]) == 0
    assert "input_missing" in capsys.readouterr().out
    assert json.loads((tmp_path / "d.json").read_text())[0]["skill"] == "alterlab-x"
