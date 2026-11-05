#!/usr/bin/env python3
"""
Presentation Validation Script

Validates scientific presentations for common issues:
- Slide count vs. duration
- LaTeX compilation
- File size checks
- Basic format validation (PDF signature, PPTX package structure — stdlib, no parser needed)
- Font sizes (PowerPoint: effective size resolved through the inheritance chain; PDF via
  PyMuPDF, scaled to slide height)
- PDF text past a slide edge, including a line placed wholly off the slide

Every check is tracked explicitly (name, required, state, detail) and the result carries a
status, so a missing parser or an unsupported file never reads as a pass:

  valid    every requested check completed and found no issue          exit 0
  invalid  a completed check found an issue                            exit 1
  blocked  a required check could not run (parser or compiler missing,
           unsupported/unknown format, file not found)                 exit 2
  partial  every required check ran without an issue, but a requested
           optional check was skipped or a check could not inspect
           everything (e.g. PPTX runs whose font size is unresolvable) exit 3

Precedence: invalid > blocked > partial > valid. Small fonts and slide-count advice are
warnings (state "warning"); they do not make a deck invalid.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

# Try to import pypdf (the maintained successor of the deprecated PyPDF2) for PDF
# analysis; fall back to PyPDF2 for older environments. Both expose PdfReader.
try:
    import pypdf as PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    try:
        import PyPDF2
        HAS_PYPDF2 = True
    except ImportError:
        HAS_PYPDF2 = False

# Try to import python-pptx for PowerPoint analysis
try:
    from pptx import Presentation
    HAS_PPTX = True
except ImportError:
    HAS_PPTX = False

# PyMuPDF reads text positions and font sizes from a PDF deck (PowerPoint export or Beamer).
try:
    import pymupdf
except ImportError:
    try:
        import fitz as pymupdf  # PyMuPDF < 1.24.3
    except ImportError:
        pymupdf = None

# Result schema. Version 2 added status, checks, check_summary and schema_version; the
# version-1 keys (filepath, file_type, info, warnings, issues, valid) are unchanged, except
# that "valid" is now True only when status == "valid".
SCHEMA_VERSION = 2
EXIT_CODES = {"valid": 0, "invalid": 1, "blocked": 2, "partial": 3}
COMPLETED_STATES = ("passed", "warning", "failed", "incomplete")
SUPPORTED_TYPES = {".pdf": "PDF", ".pptx": "PowerPoint (OOXML)", ".tex": "LaTeX Beamer source"}
UNSUPPORTED_HINTS = {
    ".ppt": "legacy binary PowerPoint is not supported; convert it first "
            "(soffice --headless --convert-to pptx FILE.ppt) or validate the exported PDF",
    ".key": "Keynote is not supported; export to PDF or PowerPoint first",
    ".odp": "OpenDocument is not supported; convert to .pptx or PDF first",
}

# Both standard PowerPoint sizes (16:9 and 4:3) are 7.5 in = 540 pt high. PDF font sizes are
# scaled to that height, so the 18 pt rule means the same on a Beamer page (96 mm high, where
# 11 pt body text is ~22 pt) as on a PowerPoint slide.
REFERENCE_SLIDE_HEIGHT_PT = 540.0
BODY_MIN_PT = 18
FOOTER_MIN_PT = 12
FOOTER_BAND = 0.85  # text whose top is in the bottom 15% of the slide is footer/citation text

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
SLIDE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
PPTX_MAIN_TYPES = {
    f"application/vnd.openxmlformats-officedocument.presentationml.{kind}.main+xml"
    for kind in ("presentation", "slideshow", "template")
} | {
    f"application/vnd.ms-powerpoint.{kind}.macroEnabled.main+xml"
    for kind in ("presentation", "slideshow", "template")
}


def _a(tag: str) -> str:
    return f"{{{A_NS}}}{tag}"


def _p(tag: str) -> str:
    return f"{{{P_NS}}}{tag}"


def pdf_text_findings(pages):
    """Check PDF text spans against the slide edges and the font-size minimums.

    pages: [(width, height, [((x0, y0, x1, y1), size_pt, text), ...]), ...] in page
    coordinates (origin top-left). Returns (off_slide, small): off_slide is a list of
    (slide, edges, wholly_off, text); small maps slide -> smallest scaled size below the
    minimum (18 pt body, 12 pt in the bottom 15% footer band).
    """
    off_slide, small = [], {}
    for idx, (width, height, spans) in enumerate(pages, start=1):
        scale = REFERENCE_SLIDE_HEIGHT_PT / height if height else 1.0
        for (x0, y0, x1, y1), size, text in spans:
            text = " ".join(text.split())
            if not text:
                continue
            edges = [name for name, out in (("left", x0 < -1), ("top", y0 < -1),
                                            ("right", x1 > width + 1), ("bottom", y1 > height + 1))
                     if out]
            if edges:
                wholly_off = x0 >= width or y0 >= height or x1 <= 0 or y1 <= 0
                off_slide.append((idx, edges, wholly_off, text))
            scaled = size * scale
            if scaled < (FOOTER_MIN_PT if y0 >= height * FOOTER_BAND else BODY_MIN_PT):
                small[idx] = min(scaled, small.get(idx, scaled))
    return off_slide, small


def extract_pdf_spans(path):
    """[(width, height, spans)] per page via PyMuPDF (spans as pdf_text_findings expects)."""
    pages = []
    with pymupdf.open(path) as doc:
        for page in doc:
            # The default clip is the page, which silently drops a line placed wholly
            # off the slide; an unbounded clip keeps it so it can be reported.
            blocks = page.get_text("dict", clip=pymupdf.INFINITE_RECT())["blocks"]
            spans = [(s["bbox"], s["size"], s["text"]) for b in blocks
                     for line in b.get("lines", []) for s in line["spans"]]
            pages.append((page.rect.width, page.rect.height, spans))
    return pages


def pptx_package_findings(path):
    """Structural check of a .pptx with the standard library only.

    Returns (problems, slide_count, (width_emu, height_emu) or None). A .pptx is a ZIP
    package with [Content_Types].xml, a presentation part at ppt/presentation.xml declared
    with a presentation content type, and one slide part per p:sldId entry.
    """
    if not zipfile.is_zipfile(path):
        return ["Not a PowerPoint package: a .pptx is a ZIP archive and this file is not one"], None, None
    problems = []
    try:
        with zipfile.ZipFile(path) as z:
            names = set(z.namelist())
            for part in ("[Content_Types].xml", "ppt/presentation.xml"):
                if part not in names:
                    problems.append(f"Not a PowerPoint package: missing part {part}")
            if problems:
                return problems, None, None
            types = ET.fromstring(z.read("[Content_Types].xml"))
            declared = {o.get("PartName"): o.get("ContentType")
                        for o in types.iter(f"{{{CT_NS}}}Override")}
            if declared.get("/ppt/presentation.xml") not in PPTX_MAIN_TYPES:
                problems.append("ppt/presentation.xml is not declared as a presentation part "
                                f"(content type: {declared.get('/ppt/presentation.xml')})")
            pres = ET.fromstring(z.read("ppt/presentation.xml"))
            slide_ids = pres.findall(f"{_p('sldIdLst')}/{_p('sldId')}")
            size_el = pres.find(_p("sldSz"))
            size = None
            if size_el is not None and size_el.get("cx") and size_el.get("cy"):
                size = (int(size_el.get("cx")), int(size_el.get("cy")))
            rels_name = "ppt/_rels/presentation.xml.rels"
            if slide_ids and rels_name in names:
                rels = ET.fromstring(z.read(rels_name))
                for rel in rels.iter(f"{{{REL_NS}}}Relationship"):
                    if rel.get("Type") == SLIDE_REL and rel.get("TargetMode") != "External":
                        target = rel.get("Target", "")
                        part = target.lstrip("/") if target.startswith("/") else f"ppt/{target}"
                        if part not in names:
                            problems.append(f"Slide part missing from the package: {part}")
            elif slide_ids:
                problems.append(f"Missing part {rels_name} (slides cannot be located)")
            if not slide_ids:
                problems.append("The presentation has no slides")
            return problems, len(slide_ids), size
    except (zipfile.BadZipFile, ET.ParseError, KeyError, ValueError, OSError) as e:
        return [f"Corrupt PowerPoint package: {e}"], None, None


# --- PPTX effective font size --------------------------------------------------------------

TITLE_TYPES = {"title", "ctrTitle"}
OTHER_PH_TYPES = {"dt", "ftr", "sldNum", "hdr"}


def _sz(el) -> Optional[float]:
    """The sz attribute of an a:rPr / a:defRPr element in points (it is stored in 1/100 pt)."""
    if el is None or el.get("sz") is None:
        return None
    try:
        return int(el.get("sz")) / 100
    except ValueError:
        return None


def _list_style_size(lst, level: int) -> Optional[float]:
    """Default run size for a paragraph level in an a:lstStyle / p:titleStyle-like element:
    the a:lvlNpPr/a:defRPr for that level, else the a:defPPr/a:defRPr."""
    if lst is None:
        return None
    for tag in (f"lvl{level + 1}pPr", "defPPr"):
        ppr = lst.find(_a(tag))
        if ppr is not None:
            size = _sz(ppr.find(_a("defRPr")))
            if size is not None:
                return size
    return None


def _placeholder(el):
    """(type, idx) of a placeholder shape element, or None for an ordinary shape."""
    ph = el.find(f"./*/{_p('nvPr')}/{_p('ph')}")
    if ph is None:
        return None
    try:
        idx = int(ph.get("idx", "0"))
    except ValueError:
        idx = 0
    return ph.get("type", "obj"), idx


def _master_kind(ph_type: str) -> str:
    """Placeholder family used to match a master placeholder and pick a master text style."""
    if ph_type in TITLE_TYPES:
        return "title"
    if ph_type in OTHER_PH_TYPES:
        return ph_type
    return "body"  # body, subTitle, obj, chart, tbl, pic, media, clipArt, dgm ...


def _lst_style(el):
    return el.find(f"{_p('txBody')}/{_a('lstStyle')}") if el is not None else None


class PptxFontResolver:
    """Resolve the effective font size of each text run in a python-pptx Presentation.

    Inheritance chain, first explicit size wins:
      1. the run's a:rPr@sz
      2. the paragraph's a:pPr/a:defRPr@sz
      3. the text body's own a:lstStyle (level N, then defPPr)
      4. placeholders only: the matching layout placeholder's lstStyle (same idx, else same
         type), then the master placeholder of the same family (title / body / dt / ftr ...)
      5. the master's p:txStyles — titleStyle for title/ctrTitle placeholders, bodyStyle for
         body-family placeholders, otherStyle for footer-type placeholders, ordinary shapes
         and table cells
      6. the presentation's p:defaultTextStyle
    The resolved size is multiplied by the shape's own a:normAutofit@fontScale when present.
    A run with no size anywhere in the chain is counted as unresolved, never as passing.
    """

    def __init__(self, prs):
        self.prs = prs
        self.default_style = prs.part._element.find(_p("defaultTextStyle"))
        self.slide_height = prs.slide_height
        self.footer_top = int(prs.slide_height * FOOTER_BAND) if prs.slide_height else None

    def _tail_chain(self, slide, el):
        """[(source label, lstStyle-like element)] after the text body's own lstStyle."""
        layout = slide.slide_layout
        master = layout.slide_master
        chain = []
        ph = _placeholder(el) if el is not None else None
        if ph is not None:
            ph_type, idx = ph
            layout_phs = [(p.element, _placeholder(p.element)) for p in layout.placeholders]
            match = next((e for e, info in layout_phs if info and info[1] == idx), None)
            if match is None:  # lxml elements are falsy when childless: compare with None
                match = next((e for e, info in layout_phs if info and info[0] == ph_type), None)
            if match is not None:
                chain.append(("layout placeholder", _lst_style(match)))
                ph_type = _placeholder(match)[0]
            kind = _master_kind(ph_type)
            master_ph = next((p.element for p in master.placeholders
                              if _master_kind(_placeholder(p.element)[0]) == kind), None)
            if master_ph is not None:
                chain.append(("master placeholder", _lst_style(master_ph)))
            style = {"title": "titleStyle", "body": "bodyStyle"}.get(kind, "otherStyle")
        else:
            style = "otherStyle"
        chain.append((f"master {style}", master.element.find(f"{_p('txStyles')}/{_p(style)}")))
        chain.append(("presentation defaultTextStyle", self.default_style))
        return chain

    def _body_runs(self, tx_body, tail_chain, top_emu):
        """Yield (text, size_pt or None, source, in_footer) for each non-blank run."""
        own = tx_body.find(_a("lstStyle"))
        autofit = tx_body.find(f"{_a('bodyPr')}/{_a('normAutofit')}")
        scale = 1.0
        if autofit is not None and autofit.get("fontScale"):
            try:
                scale = int(autofit.get("fontScale")) / 100000
            except ValueError:
                pass
        in_footer = (self.footer_top is not None and top_emu is not None
                     and top_emu >= self.footer_top)
        chain = [("shape list style", own)] + tail_chain
        for para in tx_body.findall(_a("p")):
            ppr = para.find(_a("pPr"))
            level = 0
            if ppr is not None:
                try:
                    level = min(max(int(ppr.get("lvl", "0")), 0), 8)
                except ValueError:
                    level = 0
            para_size = _sz(ppr.find(_a("defRPr"))) if ppr is not None else None
            for run in para:
                if run.tag not in (_a("r"), _a("fld")):
                    continue
                text = "".join(t.text or "" for t in run.findall(_a("t")))
                if not text.strip():
                    continue
                size, source = _sz(run.find(_a("rPr"))), "run"
                if size is None and para_size is not None:
                    size, source = para_size, "paragraph default"
                for label, lst in ([] if size is not None else chain):
                    size = _list_style_size(lst, level)
                    if size is not None:
                        source = label
                        break
                if size is not None and scale != 1.0:
                    size, source = size * scale, f"{source}, autofit {scale:.0%}"
                yield " ".join(text.split()), size, source, in_footer

    def walk(self, slide):
        """Yield ('run', text, size, source, in_footer), ('bullets', count) per text shape,
        and ('frame', None) for each chart/diagram/OLE frame whose text is not inspected."""
        yield from self._walk_shapes(slide, slide.shapes, 1.0, 0.0)

    def _walk_shapes(self, slide, shapes, a, b):
        # (a, b) maps a y coordinate in this container's space to slide space: y_abs = a*y + b.
        for shape in shapes:
            el = shape.element
            local = el.tag.rsplit("}", 1)[-1]
            top = shape.top
            top_abs = a * top + b if top is not None else None
            if local == "grpSp":
                xfrm = el.find(f"{_p('grpSpPr')}/{_a('xfrm')}")
                ga, gb = 1.0, 0.0
                if xfrm is not None:
                    off, ext = xfrm.find(_a("off")), xfrm.find(_a("ext"))
                    ch_off, ch_ext = xfrm.find(_a("chOff")), xfrm.find(_a("chExt"))
                    if all(x is not None for x in (off, ext, ch_off, ch_ext)):
                        ch_cy = int(ch_ext.get("cy", "0"))
                        ga = int(ext.get("cy", "0")) / ch_cy if ch_cy else 1.0
                        gb = int(off.get("y", "0")) - int(ch_off.get("y", "0")) * ga
                yield from self._walk_shapes(slide, shape.shapes, a * ga, a * gb + b)
            elif local == "graphicFrame" and getattr(shape, "has_table", False) and shape.has_table:
                tail = self._tail_chain(slide, None)
                row_top = top_abs
                for row in shape.table.rows:
                    for cell in row.cells:
                        tx_body = cell._tc.txBody
                        if tx_body is None:
                            continue
                        for run in self._body_runs(tx_body, tail, row_top):
                            yield ("run",) + run
                    if row_top is not None:
                        row_top += a * row.height
            elif local == "graphicFrame":
                yield ("frame", None)
            elif getattr(shape, "has_text_frame", False) and shape.has_text_frame:
                tx_body = shape.text_frame._txBody
                for run in self._body_runs(tx_body, self._tail_chain(slide, el), top_abs):
                    yield ("run",) + run
                paras = tx_body.findall(_a("p"))
                yield ("bullets", sum(1 for p in paras
                                      if p.find(_a("pPr")) is None
                                      or p.find(_a("pPr")).get("lvl", "0") == "0"))


class PresentationValidator:
    """Validates presentations for common issues."""

    # Recommended slide counts by duration (min, recommended, max)
    SLIDE_GUIDELINES = {
        5: (5, 6, 8),
        10: (8, 11, 14),
        15: (13, 16, 20),
        20: (18, 22, 26),
        30: (22, 27, 33),
        45: (32, 40, 50),
        60: (40, 52, 65),
    }

    def __init__(self, filepath: str, duration: Optional[int] = None, render: bool = False):
        self.filepath = Path(filepath)
        self.duration = duration
        self.render = render
        self.file_type = self.filepath.suffix.lower()
        self.issues = []
        self.warnings = []
        self.info = []
        self.checks: List[Dict] = []

    # --- check bookkeeping -------------------------------------------------------------------

    def _record(self, name: str, required: bool, state: str, detail: str = "") -> str:
        self.checks.append({"name": name, "required": required, "state": state, "detail": detail})
        return state

    def _run(self, name: str, required: bool, fn) -> str:
        """Run one check; fn returns (state, detail). An unexpected exception means the
        check could not complete, so it is recorded as skipped with the reason."""
        try:
            state, detail = fn()
        except Exception as e:  # noqa: BLE001 - a crashed check must be reported, not hidden
            state, detail = "skipped", f"check crashed: {type(e).__name__}: {e}"
        return self._record(name, required, state, detail)

    def status(self) -> str:
        states = [(c["required"], c["state"]) for c in self.checks]
        if any(s == "failed" for _, s in states):
            return "invalid"
        if any(req and s == "skipped" for req, s in states):
            return "blocked"
        if any(s in ("skipped", "incomplete") for _, s in states):
            return "partial"
        return "valid"

    # --- entry point -------------------------------------------------------------------------

    def validate(self) -> Dict:
        """Run all validations and return results."""
        if not self.filepath.is_file():
            what = "is a directory" if self.filepath.is_dir() else "not found"
            self._record("file_exists", True, "skipped", f"File {what}: {self.filepath}")
            self.issues.append(f"File {what}: {self.filepath}")
            return self._format_results()
        self._record("file_exists", True, "passed", str(self.filepath))

        if self.file_type not in SUPPORTED_TYPES:
            hint = UNSUPPORTED_HINTS.get(
                self.file_type, "supported types are .pdf, .pptx and .tex")
            label = self.file_type or "(no extension)"
            self._record("supported_format", True, "skipped",
                         f"Unsupported file type {label}: {hint}")
            self.issues.append(f"Unsupported file type {label}: {hint}")
            return self._format_results()
        self._record("supported_format", True, "passed", SUPPORTED_TYPES[self.file_type])

        self._run("file_size", True, self._check_file_size)

        if self.file_type == '.pdf':
            self._validate_pdf()
        elif self.file_type == '.pptx':
            self._validate_pptx()
        else:
            self._validate_latex()
        if self.render and self.file_type != ".pptx":
            self.info.append("--render applies to .pptx only (a PDF is already a rendering)")
        return self._format_results()

    def _check_file_size(self):
        """Check if file size is reasonable."""
        size_mb = self.filepath.stat().st_size / (1024 * 1024)
        self.info.append(f"File size: {size_mb:.2f} MB")

        if size_mb > 100:
            self.issues.append(
                f"File is very large ({size_mb:.1f} MB). "
                "Consider compressing images."
            )
            return "failed", f"{size_mb:.1f} MB (over 100 MB)"
        if size_mb > 50:
            self.warnings.append(
                f"File is large ({size_mb:.1f} MB). "
                "May be slow to email or upload."
            )
            return "warning", f"{size_mb:.1f} MB (over 50 MB)"
        return "passed", f"{size_mb:.2f} MB"

    # --- PDF ---------------------------------------------------------------------------------

    def _validate_pdf(self):
        """Validate PDF presentation."""
        if self._run("pdf_signature", True, self._check_pdf_signature) == "failed":
            for name in ("pdf_pages", "pdf_text_layout"):
                self._record(name, True, "skipped", "not a PDF file")
            if self.duration:
                self._record("slide_count", True, "skipped", "not a PDF file")
            return
        num_pages = []
        self._run("pdf_pages", True, lambda: self._check_pdf_pages(num_pages))
        self._run("pdf_text_layout", True, self._check_pdf_text)
        if self.duration:
            self._run("slide_count", True, lambda: self._check_slide_count(
                num_pages[0] if num_pages else None))

    def _check_pdf_signature(self):
        with open(self.filepath, "rb") as f:
            head = f.read(1024)
        if b"%PDF-" not in head:
            self.issues.append("Not a PDF file: no %PDF- header in the first 1024 bytes")
            return "failed", "no %PDF- header"
        return "passed", "%PDF- header present"

    def _check_pdf_pages(self, out: list):
        """Page count, dimensions and aspect ratio (pypdf, or PyMuPDF when pypdf is absent)."""
        if HAS_PYPDF2:
            parser = "pypdf"
            try:
                with open(self.filepath, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    num_pages = len(reader.pages)
                    if num_pages:
                        box = reader.pages[0].mediabox
                        width, height = float(box.width), float(box.height)
            except Exception as e:
                self.issues.append(f"Error reading PDF: {str(e)}")
                return "failed", f"unreadable ({parser}): {e}"
        elif pymupdf is not None:
            parser = "pymupdf"
            try:
                with pymupdf.open(self.filepath) as doc:
                    num_pages = doc.page_count
                    if num_pages:
                        width, height = doc[0].rect.width, doc[0].rect.height
            except Exception as e:
                self.issues.append(f"Error reading PDF: {str(e)}")
                return "failed", f"unreadable ({parser}): {e}"
        else:
            return "skipped", ("no PDF parser installed (pypdf or pymupdf); install with: "
                               "uv run --with pypdf --with pymupdf ...")

        out.append(num_pages)
        self.info.append(f"Number of slides: {num_pages}")
        if not num_pages:
            self.issues.append("The PDF has no pages")
            return "failed", f"0 pages ({parser})"

        aspect = width / height if height else 0
        self.info.append(
            f"Slide dimensions: {width / 72:.1f}\" × {height / 72:.1f}\" "
            f"(aspect ratio: {aspect:.2f})"
        )
        state = "passed"
        if abs(aspect - 16/9) < 0.01:
            self.info.append("Aspect ratio: 16:9 (widescreen)")
        elif abs(aspect - 4/3) < 0.01:
            self.info.append("Aspect ratio: 4:3 (standard)")
        else:
            self.warnings.append(
                f"Unusual aspect ratio: {aspect:.2f}. "
                "Confirm this matches venue requirements."
            )
            state = "warning"
        return state, f"{num_pages} page(s), aspect {aspect:.2f} ({parser})"

    def _check_pdf_text(self):
        """Flag text past a slide edge (even a line wholly off the slide) and small fonts."""
        if pymupdf is None:
            reason = ("pymupdf not installed: PDF text-position and font-size checks could not "
                      "run (run with: uv run --with pymupdf ...)")
            self.warnings.append(reason)
            return "skipped", reason
        try:
            pages = extract_pdf_spans(self.filepath)
        except Exception as e:
            self.warnings.append(f"PDF text checks skipped: {e}")
            return "skipped", f"could not extract text: {e}"
        return self._report_pdf_text(pages, prefix="")

    def _report_pdf_text(self, pages, prefix: str):
        off_slide, small = pdf_text_findings(pages)
        for idx, edges, wholly_off, text in off_slide[:12]:
            what = ("wholly off the slide, past the {} edge (not shown at all)" if wholly_off
                    else "runs past the {} edge (cut off)").format("/".join(edges))
            self.issues.append(f"{prefix}Slide {idx}: text {what}: \"{text[:70]}\"")
        if len(off_slide) > 12:
            self.issues.append(f"{prefix}... and {len(off_slide) - 12} more text spans past a slide edge")
        if small:
            self.warnings.append(
                f"{prefix}Small text (under 18 pt, or 12 pt in the footer band; sizes scaled to a "
                "7.5-inch slide height) on slides: "
                + ", ".join(f"{i} (smallest {pt:.0f} pt)" for i, pt in sorted(small.items()))
            )
        with_text = sum(1 for _, _, spans in pages if any(s[2].strip() for s in spans))
        detail = (f"{len(pages)} page(s), {with_text} with a text layer; "
                  f"{len(off_slide)} span(s) past an edge; {len(small)} slide(s) with small text")
        if off_slide:
            return "failed", detail
        if pages and not with_text:
            self.warnings.append(
                f"{prefix}No text layer on any page (slides are images): the font-size and "
                "slide-edge checks could not inspect them; review the page images visually")
            return "incomplete", detail
        return ("warning" if small else "passed"), detail

    # --- PowerPoint --------------------------------------------------------------------------

    def _validate_pptx(self):
        """Validate PowerPoint presentation."""
        pkg = {}
        self._run("pptx_package", True, lambda: self._check_pptx_package(pkg))
        package_ok = pkg.get("ok", False)
        prs = None
        if not HAS_PPTX:
            reason = ("python-pptx not installed: font-size and bullet checks could not run "
                      "(install with: uv run --with python-pptx ...)")
            self.warnings.append(reason)
            self._record("pptx_font_sizes", True, "skipped", reason)
            self._record("pptx_bullet_count", True, "skipped", reason)
        elif not package_ok:
            for name in ("pptx_font_sizes", "pptx_bullet_count"):
                self._record(name, True, "skipped", "the package is not a readable presentation")
        else:
            try:
                prs = Presentation(self.filepath)
            except Exception as e:
                self.issues.append(f"Error reading PowerPoint: {str(e)}")
                self._record("pptx_font_sizes", True, "failed", f"python-pptx cannot open it: {e}")
                self._record("pptx_bullet_count", True, "skipped", "python-pptx cannot open it")
            else:
                found = {}
                self._run("pptx_font_sizes", True, lambda: self._check_pptx_fonts(prs, found))
                self._run("pptx_bullet_count", True, lambda: self._check_pptx_bullets(found))

        if self.duration:
            count = pkg.get("slides")
            self._run("slide_count", True, lambda: self._check_slide_count(
                count if package_ok else None))
        if self.render:
            self._run("rendered_text_layout", False,
                      lambda: self._check_rendered_text(package_ok))

    def _check_pptx_package(self, out: dict):
        problems, slides, size = pptx_package_findings(self.filepath)
        out.update(ok=not problems and slides is not None, slides=slides)
        if problems:
            self.issues.extend(problems)
            return "failed", "; ".join(problems)
        self.info.append(f"Number of slides: {slides}")
        if size:
            w, h = size[0] / 914400, size[1] / 914400  # EMU to inches
            self.info.append(f"Slide dimensions: {w:.1f}\" × {h:.1f}\" "
                             f"(aspect ratio: {size[0] / size[1]:.2f})")
        return "passed", f"{slides} slide(s); package structure OK (stdlib zipfile check)"

    def _check_pptx_fonts(self, prs, found: dict):
        """Effective size of every text run (see PptxFontResolver) against 18/12 pt minimums."""
        resolver = PptxFontResolver(prs)
        small_text, small_footer, unchecked = set(), set(), set()
        examples, bullets = [], []
        checked = unresolved = frames = 0
        for idx, slide in enumerate(prs.slides, start=1):
            for item in resolver.walk(slide):
                if item[0] == "frame":
                    frames += 1
                    continue
                if item[0] == "bullets":
                    bullets.append((idx, item[1]))
                    continue
                _, text, size, source, in_footer = item
                if size is None:
                    unresolved += 1
                    unchecked.add(idx)
                    continue
                checked += 1
                if size < (FOOTER_MIN_PT if in_footer else BODY_MIN_PT):
                    (small_footer if in_footer else small_text).add(idx)
                    if len(examples) < 5:
                        examples.append(f"slide {idx}: {size:.1f} pt from {source}: \"{text[:40]}\"")
        found["bullets"] = bullets

        def _listing(slides):
            ordered = sorted(slides)
            return f"{ordered[:5]}" + (" ..." if len(ordered) > 5 else "")

        if small_text:
            self.warnings.append(f"Small text (<18pt) found on slides: {_listing(small_text)}")
        if small_footer:
            self.warnings.append(
                f"Footer/citation text under 12pt on slides: {_listing(small_footer)}")
        if examples:
            self.info.append("Small-text examples (effective size and where it comes from): "
                             + "; ".join(examples))
        if unresolved:
            self.warnings.append(
                f"Font size could not be resolved for {unresolved} text run(s) on slides "
                f"{_listing(unchecked)}: not checked (no size in the run, paragraph, list styles, "
                "layout/master placeholders, master text styles or presentation default)")
        if frames:
            self.info.append(
                f"{frames} chart/diagram/OLE frame(s) not inspected for font size (their text "
                "lives in separate parts); check them on the exported PDF")
        detail = (f"{checked} text run(s) checked, {unresolved} unresolved; "
                  f"{len(small_text | small_footer)} slide(s) with small text; "
                  f"{frames} chart/diagram frame(s) not inspected")
        if unresolved:
            return "incomplete", detail
        return ("warning" if small_text or small_footer else "passed"), detail

    def _check_pptx_bullets(self, found: dict):
        many = sorted({idx for idx, count in found.get("bullets", []) if count > 6})
        if many:
            self.warnings.append(f"Many bullets (>6) on slides: {many[:5]}"
                                 + (" ..." if len(many) > 5 else ""))
            return "warning", f"{len(many)} slide(s) with more than 6 top-level paragraphs"
        return "passed", "no text frame with more than 6 top-level paragraphs"

    def _check_rendered_text(self, package_ok: bool):
        """Optional (--render): render the deck with LibreOffice and run the PDF text checks.

        Complements the XML font resolution: it sees the sizes as rendered (including
        autofit) and catches text running past a slide edge. LibreOffice's layout can differ
        slightly from PowerPoint's.
        """
        if not package_ok:
            return "skipped", "the package is not a readable presentation"
        office = shutil.which("soffice") or shutil.which("libreoffice")
        if office is None:
            return "skipped", "LibreOffice (soffice) not found on PATH"
        if pymupdf is None:
            return "skipped", "pymupdf not installed (run with: uv run --with pymupdf ...)"
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp, "lo-profile").as_uri()
            try:
                subprocess.run([office, "--headless", f"-env:UserInstallation={profile}",
                                "--convert-to", "pdf", "--outdir", tmp, str(self.filepath)],
                               capture_output=True, timeout=180)
            except (subprocess.TimeoutExpired, OSError) as e:
                return "skipped", f"LibreOffice could not render the deck: {e}"
            rendered = Path(tmp, self.filepath.stem + ".pdf")
            if not rendered.exists():
                return "skipped", "LibreOffice produced no PDF"
            pages = extract_pdf_spans(rendered)
        return self._report_pdf_text(pages, prefix="Rendered (LibreOffice): ")

    # --- LaTeX -------------------------------------------------------------------------------

    def _validate_latex(self):
        """Validate LaTeX Beamer presentation: compile it, then validate the compiled PDF."""
        self.info.append("LaTeX source file detected")
        if self._run("latex_compile", True, self._compile_latex) != "passed":
            return
        pdf_path = self.filepath.with_suffix('.pdf')
        pdf_results = PresentationValidator(str(pdf_path), self.duration).validate()
        self.info.extend(pdf_results['info'])
        self.warnings.extend(pdf_results['warnings'])
        self.issues.extend(pdf_results['issues'])
        for check in pdf_results["checks"]:
            self.checks.append(dict(check, name=f"compiled_pdf:{check['name']}"))

    def _compile_latex(self):
        compiler = shutil.which("pdflatex")
        if compiler is None:
            return "skipped", ("pdflatex not found on PATH: the source could not be compiled "
                               "(install TeX Live / MiKTeX, or validate the compiled PDF)")
        try:
            result = subprocess.run(
                [compiler, '-interaction=nonstopmode', self.filepath.name],
                cwd=self.filepath.parent, capture_output=True, timeout=60)
        except subprocess.TimeoutExpired:
            return "skipped", "pdflatex timed out after 60 s"
        except OSError as e:
            return "skipped", f"pdflatex could not run: {e}"
        if result.returncode != 0:
            self.issues.append("LaTeX compilation failed. Check .log file for errors.")
            return "failed", f"pdflatex exit code {result.returncode}"
        if not self.filepath.with_suffix(".pdf").exists():
            self.issues.append("pdflatex reported success but produced no PDF")
            return "failed", "no PDF produced"
        self.info.append("LaTeX compilation: SUCCESS")
        return "passed", "compiled with pdflatex"

    # --- shared ------------------------------------------------------------------------------

    def _check_slide_count(self, num_slides: Optional[int]):
        """Check if slide count is appropriate for duration."""
        if num_slides is None:
            return "skipped", "slide count unavailable (the deck could not be read)"
        if self.duration not in self.SLIDE_GUIDELINES:
            # Find nearest duration
            durations = sorted(self.SLIDE_GUIDELINES.keys())
            nearest = min(durations, key=lambda x: abs(x - self.duration))
            min_slides, rec_slides, max_slides = self.SLIDE_GUIDELINES[nearest]
            self.info.append(
                f"Using guidelines for {nearest}-minute talk "
                f"(closest to {self.duration} minutes)"
            )
        else:
            min_slides, rec_slides, max_slides = self.SLIDE_GUIDELINES[self.duration]

        self.info.append(
            f"Recommended slides for {self.duration}-minute talk: "
            f"{min_slides}-{max_slides} (optimal: ~{rec_slides})"
        )
        detail = f"{num_slides} slide(s); recommended {min_slides}-{max_slides}"
        if num_slides < min_slides:
            self.warnings.append(
                f"Fewer slides ({num_slides}) than recommended ({min_slides}-{max_slides}). "
                "May have too much time or too little content."
            )
            return "warning", detail
        if num_slides > max_slides:
            self.warnings.append(
                f"More slides ({num_slides}) than recommended ({min_slides}-{max_slides}). "
                "Likely to run over time."
            )
            return "warning", detail
        self.info.append(f"Slide count ({num_slides}) is within recommended range.")
        return "passed", detail

    def _format_results(self) -> Dict:
        """Format validation results."""
        status = self.status()
        summary = {"requested": len(self.checks),
                   "completed": sum(c["state"] in COMPLETED_STATES for c in self.checks)}
        for state in ("passed", "warning", "failed", "incomplete", "skipped"):
            summary[state] = sum(c["state"] == state for c in self.checks)
        return {
            'schema_version': SCHEMA_VERSION,
            'filepath': str(self.filepath),
            'file_type': self.file_type,
            'status': status,
            'valid': status == "valid",
            'checks': self.checks,
            'check_summary': summary,
            'info': self.info,
            'warnings': self.warnings,
            'issues': self.issues,
        }


STATUS_LINES = {
    "valid": "✅ Validation PASSED (status: valid) — every requested check ran, no issues",
    "invalid": "❌ Validation FAILED (status: invalid)",
    "blocked": "⛔ Validation BLOCKED (status: blocked) — a required check could not run",
    "partial": "⚠️  Validation PARTIAL (status: partial) — required checks ran, coverage incomplete",
}


def print_results(results: Dict, quiet: bool = False):
    """Print validation results in a readable format."""
    print(f"Validating: {Path(results['filepath']).name}")
    print(f"File type: {results['file_type'] or '(none)'}")
    print("=" * 60)
    if not quiet and results['info']:
        print("\n📋 Information:")
        for item in results['info']:
            print(f"  • {item}")

    if results['warnings']:
        print("\n⚠️  Warnings:")
        for item in results['warnings']:
            print(f"  • {item}")

    if results['issues']:
        print("\n❌ Issues:")
        for item in results['issues']:
            print(f"  • {item}")

    print("\n🔎 Checks:")
    for check in results['checks']:
        if quiet and check['state'] in ("passed",):
            continue
        kind = "required" if check['required'] else "optional"
        print(f"  [{check['state']:<10}] {check['name']} ({kind}): {check['detail']}")

    status = results['status']
    print("\n" + "=" * 60)
    print(STATUS_LINES[status])
    if status == "invalid":
        print(f"   ({len(results['issues'])} issue(s) found)")
    elif status in ("blocked", "partial"):
        for check in results['checks']:
            if check['state'] in ("skipped", "incomplete"):
                print(f"   {check['name']}: {check['detail']}")
    if results['warnings']:
        print(f"   ({len(results['warnings'])} warning(s) found)")
    print("=" * 60)


EPILOG = """
Examples:
  %(prog)s presentation.pdf --duration 15
  %(prog)s slides.pptx --duration 45 --render
  %(prog)s beamer_talk.tex --duration 20 --json

Supported file types: PDF (.pdf), PowerPoint (.pptx), LaTeX Beamer (.tex).
Legacy .ppt, .key, .odp and unknown extensions are not validated (status: blocked).

Checks (R = required, O = optional):
  all    file_exists R, supported_format R, file_size R, slide_count R (with --duration)
  .pdf   pdf_signature R (stdlib), pdf_pages R (pypdf or pymupdf),
         pdf_text_layout R (pymupdf: text past a slide edge, font sizes)
  .pptx  pptx_package R (stdlib zip structure), pptx_font_sizes R (python-pptx: effective
         size through the inheritance chain), pptx_bullet_count R (python-pptx),
         rendered_text_layout O (with --render: LibreOffice + pymupdf)
  .tex   latex_compile R (pdflatex), then every .pdf check on the compiled PDF

Status and exit codes:
  0  valid    every requested check completed and found no issue
  1  invalid  a completed check found an issue (text off a slide, unreadable file ...)
  2  blocked  a required check could not run (parser or compiler missing, unsupported
              format, file not found); argparse usage errors also exit 2
  3  partial  required checks passed, but a requested optional check was skipped or a
              check could not inspect everything (e.g. unresolvable PPTX font sizes,
              a PDF with no text layer)
Small fonts, bullet counts and slide-count advice are warnings; they do not change the status.
"""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description='Validate scientific presentations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG,
    )
    parser.add_argument('filepath', help='Path to presentation file (PDF, PPTX, or TEX)')
    parser.add_argument('--duration', '-d', type=int, help='Presentation duration in minutes')
    parser.add_argument('--render', action='store_true',
                        help='PPTX only: also render with LibreOffice and run the PDF text '
                             'checks on the rendering (optional check)')
    parser.add_argument('--json', action='store_true',
                        help='Print the results as JSON (schema_version 2) instead of text')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Only show issues, warnings and checks that did not pass')
    args = parser.parse_args(argv)

    results = PresentationValidator(args.filepath, args.duration, render=args.render).validate()

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    elif args.quiet and results['status'] == "valid" and not results['warnings']:
        print("✅ No issues found (status: valid)")
    else:
        print_results(results, quiet=args.quiet)
    return EXIT_CODES[results['status']]


if __name__ == '__main__':
    sys.exit(main())
