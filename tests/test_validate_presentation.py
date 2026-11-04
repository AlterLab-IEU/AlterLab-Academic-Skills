"""alterlab-scientific-slides' validate_presentation.py — PDF text checks.

On a PDF the validator used to count pages only, so a line placed wholly below the slide (no
rendered image shows it, and default text extraction clips it away) went unreported, and PDF
decks (Beamer, PowerPoint exports) got no font-size check at all.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1] / "skills" / "writing-tools" / "alterlab-scientific-slides"
spec = importlib.util.spec_from_file_location("validate_presentation",
                                              SKILL / "scripts" / "validate_presentation.py")
vp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vp)


def test_edges_and_small_fonts_on_a_16x9_slide() -> None:
    spans = [((48, 92, 600, 127), 24, "Inside the slide"),
             ((48, 157, 968, 191), 24, "Runs past the right edge"),
             ((48, 546, 540, 580), 24, "Wholly below the slide"),
             ((48, 300, 300, 310), 7, "Tiny body text"),
             ((48, 500, 300, 512), 13, "Footer citation, allowed at 12 pt")]
    off, small = vp.pdf_text_findings([(960, 540, spans)])
    assert off == [(1, ["right"], False, "Runs past the right edge"),
                   (1, ["bottom"], True, "Wholly below the slide")]
    assert small == {1: 7}


def test_beamer_sizes_are_scaled_to_slide_height() -> None:
    # Beamer default page: 128 x 96 mm = 362.8 x 272.1 pt; 11 pt there reads like ~22 pt.
    ok = [((20, 60, 300, 72), 11, "Normal Beamer body text")]
    tiny = [((20, 60, 300, 68), 7, "\\scriptsize body text")]
    assert vp.pdf_text_findings([(362.8, 272.1, ok)]) == ([], {})
    off, small = vp.pdf_text_findings([(362.8, 272.1, tiny)])
    assert off == [] and 13 < small[1] < 14


def test_blank_spans_are_ignored() -> None:
    assert vp.pdf_text_findings([(960, 540, [((990, 0, 1000, 10), 4, "  ")])]) == ([], {})


def test_fixture_deck_findings_end_to_end() -> None:
    if vp.pymupdf is None:
        pytest.skip("pymupdf not installed")
    v = vp.PresentationValidator(str(SKILL / "evals" / "fixtures" / "ml_talk.pdf"))
    v._check_pdf_text()
    issues = "\n".join(v.issues)
    assert issues.count("Slide 2: text runs past the right edge") == 3
    assert "Slide 2: text wholly off the slide, past the bottom edge" in issues
    assert "External validation on a second university" in issues
    assert "Slide 4: text runs past the right edge" in issues
    assert "Slide 1" not in issues and "Slide 3" not in issues
    small = next(w for w in v.warnings if w.startswith("Small text"))
    assert "3 (smallest 7 pt)" in small and "4 (smallest 10 pt)" in small and " 1 (" not in small
