"""Cross-skill confusion-matrix guardrails.

The hard, deterministic invariant: every ``alterlab-*`` skill named in any eval's
``expected_output`` or assertion values must resolve to a real skill. A dangling name
means a near-miss defers a user to a skill that does not exist (typo, rename, or a
skill that was removed) — a real routing bug. The overlap-matrix itself is a reporting
tool (``scripts/confusion_matrix.py``); here we just smoke-test that it builds.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import confusion_matrix as cm  # noqa: E402


def test_no_dangling_skill_references_in_evals() -> None:
    skills = cm.load_skills()
    dangles = cm.dangling_refs(set(skills))
    assert not dangles, (
        "eval files name alterlab-* skills that do not exist (broken near-miss deferral "
        f"targets): {dangles[:10]}. Fix the name or create the skill."
    )


def test_confusion_matrix_builds() -> None:
    """The matrix must build over the live corpus without error and find the known clusters."""
    skills = cm.load_skills()
    refs = cm.eval_skill_refs()
    pairs = cm.confusion_pairs(skills, refs)
    assert isinstance(pairs, list) and pairs, "expected some within-domain overlap pairs"
    # Sanity: every pair references two real, distinct, same-category skills.
    for p in pairs:
        assert p["a"] in skills and p["b"] in skills and p["a"] != p["b"]
        assert skills[p["a"]]["category"] == skills[p["b"]]["category"] == p["category"]
        assert 0.0 <= p["overlap"] <= 1.0
