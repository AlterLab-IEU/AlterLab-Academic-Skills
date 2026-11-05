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


# ---------------------------------------------------------------------------------------------
# Check tracking (C1): every result carries a status in {valid, invalid, blocked, partial} and a
# list of checks; a missing parser, an unknown format or a missing compiler never yields "valid".
# ---------------------------------------------------------------------------------------------

import json  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
SCRIPT = SKILL / "scripts" / "validate_presentation.py"
FIXTURE_PDF = SKILL / "evals" / "fixtures" / "ml_talk.pdf"


def _a(tag: str) -> str:
    return f"{{{A_NS}}}{tag}"


def _p(tag: str) -> str:
    return f"{{{P_NS}}}{tag}"


def _validate(path, **kwargs) -> dict:
    return vp.PresentationValidator(str(path), **kwargs).validate()


def _check(results: dict, name: str) -> dict:
    return next(c for c in results["checks"] if c["name"] == name)


def _small_text_warning(results: dict) -> str:
    return next((w for w in results["warnings"] if w.startswith("Small text (<18pt)")), "")


def _new_deck():
    pptx = pytest.importorskip("pptx")
    return pptx.Presentation()


def _title_and_body(prs, title: str, body: str):
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = title
    slide.placeholders[1].text = body
    return slide


def _textbox(slide, text: str, top_in: float = 2.0, size_pt=None):
    from pptx.util import Inches, Pt
    box = slide.shapes.add_textbox(Inches(1), Inches(top_in), Inches(6), Inches(1))
    box.text_frame.text = text
    if size_pt is not None:
        box.text_frame.paragraphs[0].runs[0].font.size = Pt(size_pt)
    return box


def _set_list_style_size(lst_style, hundredths: int) -> None:
    """Give an a:lstStyle (or p:*Style) element a level-1 default run size."""
    from lxml import etree
    lvl1 = lst_style.find(_a("lvl1pPr"))
    if lvl1 is None:
        lvl1 = etree.SubElement(lst_style, _a("lvl1pPr"))
        defpp = lst_style.find(_a("defPPr"))
        if defpp is not None:  # schema order: defPPr before lvl1pPr
            defpp.addnext(lvl1)
    defrpr = lvl1.find(_a("defRPr"))
    if defrpr is None:
        defrpr = etree.SubElement(lvl1, _a("defRPr"))
    defrpr.set("sz", str(hundredths))


def _save(prs, tmp_path, name: str = "deck.pptx"):
    path = tmp_path / name
    prs.save(path)
    return path


def test_normal_pptx_deck_is_valid(tmp_path) -> None:
    prs = _new_deck()
    _title_and_body(prs, "Results", "AUC 0.87 against a 0.79 baseline")
    results = _validate(_save(prs, tmp_path))
    assert results["status"] == "valid" and results["valid"] is True
    assert results["issues"] == [] and _small_text_warning(results) == ""
    assert {c["name"] for c in results["checks"]} >= {"file_exists", "supported_format", "file_size",
                                                      "pptx_package", "pptx_font_sizes"}
    assert all(c["state"] == "passed" for c in results["checks"])
    assert all(set(c) == {"name", "required", "state", "detail"} for c in results["checks"])


# --- C2: effective font size through the inheritance chain ----------------------------------

def test_small_body_size_inherited_from_master_text_styles_is_flagged(tmp_path) -> None:
    prs = _new_deck()
    body_style = prs.slide_master.element.find(f"{_p('txStyles')}/{_p('bodyStyle')}")
    _set_list_style_size(body_style, 1400)  # master body text: 14 pt
    control = prs.slides.add_slide(prs.slide_layouts[5])  # Title Only: 44 pt title style
    control.shapes.title.text = "A normal-size title"
    _title_and_body(prs, "Methods", "Body text that inherits 14 pt from the slide master")
    results = _validate(_save(prs, tmp_path))
    assert "found on slides: [2]" in _small_text_warning(results)
    assert results["status"] == "valid"  # small text is a warning, not an issue


def test_small_size_from_layout_placeholder_list_style_is_flagged(tmp_path) -> None:
    prs = _new_deck()
    layout_body = next(ph for ph in prs.slide_layouts[1].placeholders
                       if ph.placeholder_format.idx == 1)
    _set_list_style_size(layout_body.element.find(f"{_p('txBody')}/{_a('lstStyle')}"), 1200)
    _title_and_body(prs, "Data", "Inherits 12 pt from its layout placeholder")
    assert "found on slides: [1]" in _small_text_warning(_validate(_save(prs, tmp_path)))


def test_small_size_from_shape_list_style_is_flagged_and_default_textbox_is_not(tmp_path) -> None:
    prs = _new_deck()
    blank = prs.slide_layouts[6]
    _textbox(prs.slides.add_slide(blank), "Default text box, 18 pt from the presentation default")
    box = _textbox(prs.slides.add_slide(blank), "Text box whose own list style says 10 pt")
    _set_list_style_size(box.text_frame._txBody.find(_a("lstStyle")), 1000)
    assert "found on slides: [2]" in _small_text_warning(_validate(_save(prs, tmp_path)))


def test_explicit_run_sizes_control(tmp_path) -> None:
    prs = _new_deck()
    blank = prs.slide_layouts[6]
    _textbox(prs.slides.add_slide(blank), "Explicit 24 pt run", size_pt=24)
    _textbox(prs.slides.add_slide(blank), "Explicit 10 pt run", size_pt=10)
    assert "found on slides: [2]" in _small_text_warning(_validate(_save(prs, tmp_path)))


def test_text_inside_a_group_shape_is_checked(tmp_path) -> None:
    from pptx.util import Inches, Pt
    prs = _new_deck()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    group = slide.shapes.add_group_shape()
    box = group.shapes.add_textbox(Inches(1), Inches(2), Inches(6), Inches(1))
    box.text_frame.text = "Grouped label at 10 pt"
    box.text_frame.paragraphs[0].runs[0].font.size = Pt(10)
    assert "found on slides: [1]" in _small_text_warning(_validate(_save(prs, tmp_path)))


def test_text_inside_a_table_cell_is_checked(tmp_path) -> None:
    from pptx.util import Inches, Pt
    prs = _new_deck()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    table = slide.shapes.add_table(2, 2, Inches(1), Inches(1.5), Inches(6), Inches(2)).table
    for r in range(2):
        for c in range(2):
            table.cell(r, c).text = f"cell {r}{c}"
    table.cell(1, 1).text_frame.paragraphs[0].runs[0].font.size = Pt(9)
    assert "found on slides: [1]" in _small_text_warning(_validate(_save(prs, tmp_path)))


def _grouped_caption(slide, prs, group_top_emu: int) -> None:
    """A 14 pt caption in a group whose child space starts at y=0 but is placed at group_top."""
    from pptx.util import Inches, Pt
    group = slide.shapes.add_group_shape()
    box = group.shapes.add_textbox(Inches(1), Inches(0), Inches(6), Inches(0.5))
    box.text_frame.text = "Source: Smith et al. (2024)"
    box.text_frame.paragraphs[0].runs[0].font.size = Pt(14)
    xfrm = group.element.find(f"{_p('grpSpPr')}/{_a('xfrm')}")
    xfrm.find(_a("off")).set("y", str(group_top_emu))
    xfrm.find(_a("chOff")).set("y", "0")


def test_footer_band_uses_absolute_position_of_grouped_shapes(tmp_path) -> None:
    prs = _new_deck()
    blank = prs.slide_layouts[6]
    _grouped_caption(prs.slides.add_slide(blank), prs, int(prs.slide_height * 0.90))  # footer
    _grouped_caption(prs.slides.add_slide(blank), prs, int(prs.slide_height * 0.30))  # body
    results = _validate(_save(prs, tmp_path))
    assert "found on slides: [2]" in _small_text_warning(results)
    assert not any(w.startswith("Footer/citation text") for w in results["warnings"])


def test_footer_placeholder_size_comes_from_the_master_footer_placeholder(tmp_path) -> None:
    import copy
    from pptx.enum.shapes import PP_PLACEHOLDER
    for size, expect_warning in ((1200, False), (1000, True)):
        prs = _new_deck()
        master_footer = next(ph for ph in prs.slide_master.placeholders
                             if ph.placeholder_format.type == PP_PLACEHOLDER.FOOTER)
        _set_list_style_size(master_footer.element.find(f"{_p('txBody')}/{_a('lstStyle')}"), size)
        slide = _title_and_body(prs, "Results", "Body")
        layout_footer = next(ph for ph in slide.slide_layout.placeholders
                             if ph.placeholder_format.type == PP_PLACEHOLDER.FOOTER)
        footer_el = copy.deepcopy(layout_footer.element)  # a footer placeholder, as PowerPoint adds
        footer_el.find(f"{_p('nvSpPr')}/{_p('cNvPr')}").set("id", "99")
        slide.shapes._spTree.append(footer_el)
        footer = next(s for s in slide.placeholders
                      if s.placeholder_format.type == PP_PLACEHOLDER.FOOTER)
        footer.text_frame.text = "A. Researcher - EDM 2027"
        results = _validate(_save(prs, tmp_path, f"footer{size}.pptx"))
        footer_warning = [w for w in results["warnings"] if w.startswith("Footer/citation")]
        assert bool(footer_warning) is expect_warning, results["warnings"]
        assert _small_text_warning(results) == ""


def test_norm_autofit_font_scale_shrinks_effective_size(tmp_path) -> None:
    from lxml import etree
    from pptx.util import Pt
    prs = _new_deck()
    slide = _title_and_body(prs, "Results", "24 pt text shrunk to 50 % by autofit")
    body = slide.placeholders[1].text_frame
    body.paragraphs[0].runs[0].font.size = Pt(24)
    body_pr = body._txBody.find(_a("bodyPr"))
    etree.SubElement(body_pr, _a("normAutofit")).set("fontScale", "50000")
    assert "found on slides: [1]" in _small_text_warning(_validate(_save(prs, tmp_path)))


def test_unresolvable_font_size_is_counted_unchecked_not_passed(tmp_path) -> None:
    prs = _new_deck()
    for root in (prs.part._element.find(_p("defaultTextStyle")),
                 prs.slide_master.element.find(f"{_p('txStyles')}/{_p('otherStyle')}")):
        for defrpr in root.iter(_a("defRPr")):
            defrpr.attrib.pop("sz", None)
    _textbox(prs.slides.add_slide(prs.slide_layouts[6]), "No size anywhere in the chain")
    results = _validate(_save(prs, tmp_path))
    fonts = _check(results, "pptx_font_sizes")
    assert fonts["state"] == "incomplete" and "1 unresolved" in fonts["detail"]
    assert results["status"] == "partial" and results["valid"] is False
    assert any("could not be resolved" in w for w in results["warnings"])


# --- C1: malformed files, missing parsers, unsupported formats -------------------------------

def test_garbage_pptx_is_invalid_with_and_without_python_pptx(tmp_path, monkeypatch) -> None:
    garbage = tmp_path / "garbage.pptx"
    garbage.write_text("garbage not a zip")
    assert _validate(garbage)["status"] == "invalid"
    monkeypatch.setattr(vp, "HAS_PPTX", False)
    results = _validate(garbage)
    assert results["status"] == "invalid" and results["valid"] is False
    assert _check(results, "pptx_package")["state"] == "failed"
    assert _check(results, "pptx_font_sizes")["state"] == "skipped"


def test_zip_that_is_not_a_presentation_is_invalid_without_python_pptx(tmp_path, monkeypatch) -> None:
    import zipfile
    fake = tmp_path / "fake.pptx"
    with zipfile.ZipFile(fake, "w") as z:
        z.writestr("hello.txt", "not a presentation")
    monkeypatch.setattr(vp, "HAS_PPTX", False)
    assert _validate(fake)["status"] == "invalid"


def test_valid_pptx_without_python_pptx_is_blocked_not_valid(tmp_path, monkeypatch) -> None:
    prs = _new_deck()
    _title_and_body(prs, "Results", "Body")
    path = _save(prs, tmp_path)
    monkeypatch.setattr(vp, "HAS_PPTX", False)
    results = _validate(path, duration=5)
    assert results["status"] == "blocked" and results["valid"] is False
    fonts = _check(results, "pptx_font_sizes")
    assert fonts["required"] is True and fonts["state"] == "skipped"
    assert "python-pptx" in fonts["detail"]
    assert _check(results, "pptx_package")["state"] == "passed"
    assert _check(results, "slide_count")["state"] in ("passed", "warning")  # stdlib count


@pytest.mark.parametrize("name", ["notes.docx", "legacy.ppt", "README"])
def test_unsupported_formats_are_blocked(tmp_path, name) -> None:
    path = tmp_path / name
    path.write_bytes(b"\xd0\xcf\x11\xe0 some bytes")
    results = _validate(path)
    assert results["status"] == "blocked" and results["valid"] is False
    assert _check(results, "supported_format")["state"] == "skipped"


def test_missing_file_is_blocked(tmp_path) -> None:
    results = _validate(tmp_path / "nope.pdf")
    assert results["status"] == "blocked" and results["valid"] is False


def test_pdf_without_pymupdf_is_blocked(monkeypatch) -> None:
    monkeypatch.setattr(vp, "pymupdf", None)
    results = _validate(FIXTURE_PDF)
    assert results["status"] == "blocked"
    assert _check(results, "pdf_text_layout")["state"] == "skipped"


def test_garbage_pdf_without_any_parser_is_invalid(tmp_path, monkeypatch) -> None:
    garbage = tmp_path / "talk.pdf"
    garbage.write_text("garbage not a pdf")
    monkeypatch.setattr(vp, "pymupdf", None)
    monkeypatch.setattr(vp, "HAS_PYPDF2", False)
    results = _validate(garbage)
    assert results["status"] == "invalid"
    assert _check(results, "pdf_signature")["state"] == "failed"


def test_tex_without_pdflatex_is_blocked_not_a_compile_failure(tmp_path, monkeypatch) -> None:
    tex = tmp_path / "talk.tex"
    tex.write_text("\\documentclass{beamer}\\begin{document}\\end{document}\n")
    monkeypatch.setattr(vp.shutil, "which", lambda _name: None)
    results = _validate(tex)
    assert results["status"] == "blocked"
    compile_check = _check(results, "latex_compile")
    assert compile_check["state"] == "skipped" and "pdflatex" in compile_check["detail"]
    assert not any("compilation failed" in i for i in results["issues"])


def test_fixture_pdf_is_invalid_through_validate() -> None:
    pytest.importorskip("pymupdf")
    results = _validate(FIXTURE_PDF, duration=5)
    assert results["status"] == "invalid" and results["valid"] is False
    assert _check(results, "pdf_text_layout")["state"] == "failed"
    assert _check(results, "pdf_pages")["state"] in ("passed", "warning")


def _pdf(tmp_path, name: str, text: str | None):
    pymupdf = pytest.importorskip("pymupdf")
    doc = pymupdf.open()
    page = doc.new_page(width=960, height=540)
    if text:
        page.insert_text((60, 120), text, fontsize=28)
    else:
        page.draw_rect(pymupdf.Rect(100, 100, 400, 300), color=(0, 0, 1), fill=(0, 0, 1))
    path = tmp_path / name
    doc.save(path)
    return path


def test_clean_pdf_is_valid(tmp_path) -> None:
    results = _validate(_pdf(tmp_path, "clean.pdf", "A clean 28 pt line"))
    assert results["status"] == "valid", results["checks"]


def test_image_only_pdf_is_partial_because_text_checks_saw_nothing(tmp_path) -> None:
    results = _validate(_pdf(tmp_path, "images.pdf", None))
    assert _check(results, "pdf_text_layout")["state"] == "incomplete"
    assert results["status"] == "partial"


# --- optional checks and exit codes ----------------------------------------------------------

def test_requested_optional_render_check_skipped_gives_partial(tmp_path, monkeypatch) -> None:
    prs = _new_deck()
    _title_and_body(prs, "Results", "Body")
    path = _save(prs, tmp_path)
    monkeypatch.setattr(vp.shutil, "which", lambda _name: None)
    results = _validate(path, render=True)
    render = _check(results, "rendered_text_layout")
    assert render["required"] is False and render["state"] == "skipped"
    assert results["status"] == "partial"
    assert vp.main([str(path), "--render", "--quiet"]) == 3


def test_render_check_finds_text_past_the_slide_edge(tmp_path) -> None:
    import shutil
    if not (shutil.which("soffice") or shutil.which("libreoffice")):
        pytest.skip("LibreOffice not installed")
    pytest.importorskip("pymupdf")
    from pptx.util import Inches, Pt
    prs = _new_deck()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    box = slide.shapes.add_textbox(Inches(7.5), Inches(3), Inches(6), Inches(1))
    box.text_frame.text = "This sentence starts near the right edge and runs off it"
    box.text_frame.paragraphs[0].runs[0].font.size = Pt(28)
    results = _validate(_save(prs, tmp_path), render=True)
    assert _check(results, "rendered_text_layout")["state"] == "failed"
    assert results["status"] == "invalid"


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True,
                          timeout=120)


def test_cli_exit_codes_and_json(tmp_path) -> None:
    prs = _new_deck()
    _title_and_body(prs, "Results", "Body")
    good = _save(prs, tmp_path)
    docx = tmp_path / "notes.docx"
    docx.write_text("not a deck")
    garbage = tmp_path / "garbage.pptx"
    garbage.write_text("garbage not a zip")

    ok = _run_cli(str(good), "--json")
    assert ok.returncode == 0, ok.stdout + ok.stderr
    payload = json.loads(ok.stdout)
    assert payload["status"] == "valid" and payload["valid"] is True
    assert payload["schema_version"] == 2
    assert _run_cli(str(garbage)).returncode == 1
    blocked = _run_cli(str(docx))
    assert blocked.returncode == 2 and "Validation PASSED" not in blocked.stdout
    assert "exit codes" in _run_cli("--help").stdout.lower()


def test_main_returns_blocked_exit_code_without_parser(tmp_path, monkeypatch, capsys) -> None:
    prs = _new_deck()
    _title_and_body(prs, "Results", "Body")
    path = _save(prs, tmp_path)
    monkeypatch.setattr(vp, "HAS_PPTX", False)
    assert vp.main([str(path), "--json"]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "blocked"
