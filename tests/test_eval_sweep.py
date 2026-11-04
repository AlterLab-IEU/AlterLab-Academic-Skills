"""scripts/eval_sweep.sh drives run_evals.py over a list of skills, one results file each."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_behavioral_runner as tbr  # noqa: E402
from test_behavioral_runner import fake_cli  # noqa: E402,F401  (fixture)

REPO = Path(__file__).resolve().parents[1]


def test_sweep_runs_each_listed_skill_and_marks_completion(fake_cli, tmp_path, monkeypatch):  # noqa: F811 (pytest fixture)
    skills = []
    for name in ("one", "two"):
        root = tmp_path / name
        skills.append(tbr._make_skill(root, [tbr._case("a")]))
    lst = tmp_path / "list.txt"
    lst.write_text("# comment\n" + "\n".join(str(s) for s in skills) + "\n\n")
    out = tmp_path / "out"
    proc = subprocess.run([str(REPO / "scripts" / "eval_sweep.sh"), str(lst), "2", str(out),
                           "--runs", "1", "--timeout", "30", "--isolation", "none"],
                          capture_output=True, text=True, timeout=240)
    assert proc.returncode == 0, proc.stderr
    done = (out / "logs" / "_done.txt").read_text().split("\n")
    assert sum("exit=0" in d for d in done) == 2 and "ALL_DONE" in done
    results = sorted(out.glob("behavioral-*.json"))
    assert len(results) == 2
    assert all(json.loads(r.read_text())["status"] == "passed" for r in results)


def test_a_second_sweep_skips_skills_already_claimed(fake_cli, tmp_path, monkeypatch):  # noqa: F811 (pytest fixture)
    skills = [tbr._make_skill(tmp_path / n, [tbr._case("a")]) for n in ("one", "two")]
    lst = tmp_path / "list.txt"
    lst.write_text("\n".join(str(s) for s in skills) + "\n")
    out = tmp_path / "out"
    args = [str(REPO / "scripts" / "eval_sweep.sh"), str(lst), "2", str(out), "--runs", "1",
            "--timeout", "30", "--isolation", "none"]
    subprocess.run(args, capture_output=True, text=True, timeout=240, check=True)
    subprocess.run(args, capture_output=True, text=True, timeout=240, check=True)
    assert len(sorted(out.glob("behavioral-*.json"))) == 2, "a skill ran twice"


def test_a_list_line_may_carry_arguments_for_that_skill_only(fake_cli, tmp_path, monkeypatch):  # noqa: F811 (pytest fixture)
    one = tbr._make_skill(tmp_path / "one", [tbr._case("a"), tbr._case("b")])
    two = tbr._make_skill(tmp_path / "two", [tbr._case("a"), tbr._case("b")])
    lst = tmp_path / "list.txt"
    lst.write_text(f"{one} --case b\n{two}\n")
    out = tmp_path / "out"
    subprocess.run([str(REPO / "scripts" / "eval_sweep.sh"), str(lst), "2", str(out), "--runs",
                    "1", "--timeout", "30", "--isolation", "none"],
                   capture_output=True, text=True, timeout=240, check=True)
    ran = sorted(len(json.loads(r.read_text())["cases"]) for r in out.glob("behavioral-*.json"))
    assert ran == [1, 2], "the --case line runs one case; the bare line runs both"
