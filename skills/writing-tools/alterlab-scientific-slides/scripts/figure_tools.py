#!/usr/bin/env python3
"""figure_tools.py - keyless rendering, linting and review bookkeeping for code-drawn figures.

Claude draws the figure as code (SVG, a standalone TikZ/PGF .tex, Graphviz .dot, or Mermaid
.mmd) and this script renders it locally to PNG / PDF / SVG. No image model and no API key are
involved, every label is exact text, and the source stays editable. After Claude has looked at
the render (Read the PNG) and scored it, ``score`` records the review in a JSON log and applies
the document-type quality threshold, so the stop/revise decision is made in code.

    python figure_tools.py render figure.svg -o figures/figure.png --width-in 7.2 --dpi 300
    python figure_tools.py render figure.tex -o figures/figure.pdf
    python figure_tools.py score figures/figure_review_log.json --kind schematic \\
        --doc-type journal --image figures/figure_v1.png --source figure.svg \\
        --score 7.5 --critique "n= labels in the exclusion box overlap the arrow"
    python figure_tools.py thresholds --kind infographic

Renderers: SVG -> cairosvg (``uv run --with cairosvg``; needs the Cairo library, present on most
Linux/macOS setups), falling back to ``rsvg-convert`` or ``inkscape`` when installed. TikZ ->
pdflatex / lualatex / xelatex / tectonic, then pdftoppm or PyMuPDF for PNG. DOT -> Graphviz ``dot``.
Mermaid -> ``mmdc``. Pillow (optional) stamps the DPI, checks the PNG is not blank, and writes a
grayscale preview with ``--gray``. This file is shared verbatim by alterlab-generate-image,
alterlab-infographics, alterlab-scientific-schematics and alterlab-scientific-slides.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

SOURCE_TYPES = {".svg": "svg", ".tex": "tikz", ".dot": "dot", ".gv": "dot", ".mmd": "mermaid"}
OUTPUT_TYPES = {".png", ".pdf", ".svg"}

# Fallback copies of the quality thresholds. When the skill's optional AI script sits next to
# this file, the live values are read from it (read_constants), so the keyless and AI paths
# judge against the same numbers.
THRESHOLDS = {
    "schematic": {"journal": 8.5, "conference": 8.0, "thesis": 8.0, "grant": 8.0,
                  "preprint": 7.5, "report": 7.5, "poster": 7.0, "presentation": 6.5,
                  "default": 7.5},
    "infographic": {"marketing": 8.5, "report": 8.0, "presentation": 7.5, "social": 7.0,
                    "internal": 7.0, "draft": 6.5, "default": 7.5},
    "slide": {"default": 6.5},
    "image": {"default": 7.0},
}
MAX_ITERATIONS = {"schematic": 2, "infographic": 3, "slide": 2, "image": 3}
AI_SOURCES = {  # kind -> (sibling AI script, class, constant)
    "schematic": ("generate_schematic_ai.py", "ScientificSchematicGenerator", "QUALITY_THRESHOLDS"),
    "infographic": ("generate_infographic_ai.py", "InfographicGenerator", "QUALITY_THRESHOLDS"),
    "slide": ("generate_slide_image_ai.py", "SlideImageGenerator", "QUALITY_THRESHOLD"),
}
# The same five 0-2 criteria the AI backends' review prompts use, so a keyless score means the
# same thing. Before scoring, every number and label is checked against the user's data: a
# mismatch is fixed first, never traded off against design points.
CRITERIA = {
    "schematic": ["Scientific accuracy", "Clarity and readability", "Label quality",
                  "Layout and composition", "Professional appearance"],
    "infographic": ["Visual hierarchy and layout", "Typography and readability",
                    "Data visualization", "Color and accessibility", "Overall impact"],
    "slide": ["Visual impact", "Clarity", "Readability", "Composition", "Relevance"],
    "image": ["Fidelity to the request", "Composition", "Text and labels exact",
              "Technical quality (size, crispness)", "Fitness for the venue"],
}


# --------------------------------------------------------------------------- constants

def read_constants(path: Path, names: list[str], cls: str | None = None) -> dict:
    """Literal values of top-level (or class-level) assignments in a Python file, without
    importing it (the AI scripts import requests at module load)."""
    found: dict = {}
    if not path.is_file():
        return found
    tree = ast.parse(path.read_text(encoding="utf-8"))
    bodies = [tree.body]
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and (cls is None or node.name == cls):
            bodies.append(node.body)
    for body in bodies:
        for node in body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in names:
                        try:
                            found[target.id] = ast.literal_eval(node.value)
                        except ValueError:
                            pass
    return found


def thresholds(kind: str) -> dict:
    table = dict(THRESHOLDS[kind])
    if kind in AI_SOURCES:
        script, cls, const = AI_SOURCES[kind]
        live = read_constants(Path(__file__).with_name(script), [const], cls).get(const)
        if isinstance(live, dict):
            table = {k: float(v) for k, v in live.items()}
        elif isinstance(live, (int, float)):
            table = {"default": float(live)}
    return table


def threshold_for(kind: str, doc_type: str) -> float:
    table = thresholds(kind)
    return table.get(doc_type.lower(), table["default"])


def find_openrouter_key(explicit: str | None = None) -> str | None:
    """The optional AI backends' key: --api-key, the environment, then a .env file in the
    current or a parent directory. None means the keyed backend cannot run."""
    if explicit:
        return explicit
    if os.environ.get("OPENROUTER_API_KEY"):
        return os.environ["OPENROUTER_API_KEY"]
    for parent in [Path.cwd(), *Path.cwd().parents]:
        env = parent / ".env"
        if env.is_file():
            for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.strip().startswith("OPENROUTER_API_KEY="):
                    value = line.split("=", 1)[1].strip().strip("'\"")
                    if value:
                        return value
    return None


# --------------------------------------------------------------------------- SVG lint

_NUM = re.compile(r"[-+]?\d*\.?\d+")


def _length(value: str | None) -> float | None:
    if not value:
        return None
    m = _NUM.match(value.strip())
    if not m:
        return None
    number = float(m.group())
    unit = value.strip()[m.end():].strip().lower()
    return number * {"": 1, "px": 1, "pt": 96 / 72, "pc": 16, "mm": 96 / 25.4, "cm": 96 / 2.54,
                     "in": 96}.get(unit, 1)


def _font_size(el: ET.Element) -> float | None:
    style = el.get("style", "")
    m = re.search(r"font-size\s*:\s*([^;]+)", style)
    return _length(m.group(1) if m else el.get("font-size"))


def lint_svg(path: Path, width_in: float | None = None, min_pt: float = 7.0) -> dict:
    """Structural checks Claude cannot see by eye: parse errors, font sizes at print width,
    colours used, external references."""
    report: dict = {"warnings": []}
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return {"error": f"SVG does not parse: {exc}", "warnings": []}
    tag = lambda e: e.tag.rsplit("}", 1)[-1]  # noqa: E731
    vb = root.get("viewBox")
    user_w = None
    if vb:
        parts = [float(x) for x in re.split(r"[ ,]+", vb.strip()) if x]
        if len(parts) == 4:
            user_w = parts[2]
    else:
        report["warnings"].append("no viewBox: the figure will not scale cleanly")
    user_w = user_w or _length(root.get("width"))
    sizes, texts, colours, external = [], 0, set(), []
    rects, labels = [], []
    transformed = {root: bool(root.get("transform"))}
    inherited = {root: _font_size(root)}
    for parent in root.iter():
        base = inherited.get(parent)
        for child in list(parent):
            own = _font_size(child)
            inherited[child] = own if own is not None else base
            transformed[child] = transformed.get(parent, False) or bool(child.get("transform"))
            if tag(child) == "style":
                colours.update(c.upper() for c in re.findall(r"#[0-9a-fA-F]{3,8}\b", child.text or ""))
            if tag(child) == "rect" and not transformed[child]:
                geo = [_length(child.get(k)) for k in ("x", "y", "width", "height")]
                if geo[2] and geo[3]:
                    rects.append([g or 0.0 for g in geo])
            if tag(child) in ("text", "tspan", "textPath"):
                if tag(child) == "text":
                    texts += 1
                    content = "".join(child.itertext()).strip()
                    x, y = _length(child.get("x")), _length(child.get("y"))
                    if content and x is not None and y is not None and not transformed[child] \
                            and inherited[child]:
                        labels.append((content, x, y, inherited[child],
                                       child.get("text-anchor", "start")))
                if inherited[child] is not None and (child.text or "").strip():
                    sizes.append(inherited[child])
            for attr in ("fill", "stroke"):
                val = child.get(attr) or ""
                m = re.search(attr + r"\s*:\s*(#[0-9a-fA-F]{3,8})", child.get("style", ""))
                for c in (val, m.group(1) if m else ""):
                    if c.startswith("#"):
                        colours.add(c.upper())
            href = child.get("href") or child.get("{http://www.w3.org/1999/xlink}href") or ""
            if href.startswith(("http://", "https://")):
                external.append(href)
    report.update({"text_elements": texts, "colours": sorted(colours),
                   "min_font_user_units": min(sizes) if sizes else None})
    if texts and not sizes:
        report["warnings"].append("text has no explicit font-size; set one so print size is known")
    if sizes and user_w and width_in:
        pt = min(sizes) * (width_in * 72) / user_w
        report["min_font_pt_at_print_width"] = round(pt, 1)
        if pt < min_pt:
            report["warnings"].append(
                f"smallest text is {pt:.1f} pt at {width_in} in wide (< {min_pt} pt): enlarge it")
    if external:
        report["warnings"].append(f"external references will not render offline: {external[:3]}")
    # Text that probably runs past the edge of the box it sits in (width estimated at
    # 0.5 em per character for a sans-serif face - a heuristic; confirm on the render).
    for content, x, y, size, anchor in labels:
        inside = [r for r in rects if r[0] <= x <= r[0] + r[2] and r[1] <= y <= r[1] + r[3]
                  and r[2] * r[3] < (user_w or 1e9) ** 2 * 0.9]
        if not inside:
            continue
        rx, _ry, rw, _rh = min(inside, key=lambda r: r[2] * r[3])
        width = 0.5 * size * len(content)
        left = {"middle": x - width / 2, "end": x - width}.get(anchor, x)
        if left < rx - 1 or left + width > rx + rw + 1:
            report["warnings"].append(f"text probably overflows its box: {content[:50]!r}")
    return report


# --------------------------------------------------------------------------- rendering

def _run(cmd: list[str], cwd: Path | None = None) -> None:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-15:]
        raise RuntimeError(f"{cmd[0]} failed (exit {proc.returncode}):\n" + "\n".join(tail))


def _svg(src: Path, out: Path, dpi: int, width_px: int | None) -> str:
    fmt = out.suffix.lower()
    try:
        import cairosvg

        kwargs = {"url": str(src), "write_to": str(out)}
        if fmt == ".png":
            if width_px:
                kwargs["output_width"] = width_px
            else:
                kwargs["scale"] = dpi / 96
            cairosvg.svg2png(**kwargs)
        else:
            cairosvg.svg2pdf(**kwargs)
        return "cairosvg"
    except (ImportError, OSError) as exc:  # OSError: the Cairo C library is missing
        first_error = exc
    if shutil.which("rsvg-convert"):
        cmd = ["rsvg-convert", "-f", fmt[1:], "-o", str(out)]
        cmd += ["-w", str(width_px)] if width_px else ["-d", str(dpi), "-p", str(dpi)]
        _run(cmd + [str(src)])
        return "rsvg-convert"
    if shutil.which("inkscape"):
        cmd = ["inkscape", str(src), f"--export-filename={out}"]
        cmd += [f"--export-width={width_px}"] if width_px else [f"--export-dpi={dpi}"]
        _run(cmd)
        return "inkscape"
    raise RuntimeError(f"no SVG renderer: cairosvg unavailable ({first_error}); run with "
                       "`uv run --with cairosvg`, or install librsvg (rsvg-convert) or Inkscape")


def _pdf_to_png(pdf: Path, out: Path, dpi: int) -> str:
    if shutil.which("pdftoppm"):
        _run(["pdftoppm", "-png", "-singlefile", "-r", str(dpi), str(pdf), str(out.with_suffix(""))])
        return "pdftoppm"
    try:
        import pymupdf
    except ImportError as exc:
        raise RuntimeError("PNG from PDF needs pdftoppm (poppler) or `uv run --with pymupdf`") from exc
    pymupdf.open(str(pdf))[0].get_pixmap(dpi=dpi).save(str(out))
    return "pymupdf"


def _tikz(src: Path, out: Path, dpi: int) -> str:
    engine = next((e for e in ("pdflatex", "lualatex", "xelatex", "tectonic") if shutil.which(e)), None)
    if not engine:
        raise RuntimeError("no LaTeX engine (pdflatex/lualatex/xelatex/tectonic) on PATH")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        if engine == "tectonic":
            _run([engine, "--outdir", str(tmp_dir), str(src)])
        else:
            _run([engine, "-interaction=nonstopmode", "-halt-on-error",
                  f"-output-directory={tmp_dir}", str(src)], cwd=src.parent)
        pdf = tmp_dir / f"{src.stem}.pdf"
        if out.suffix.lower() == ".pdf":
            shutil.copyfile(pdf, out)
            return engine
        if out.suffix.lower() == ".png":
            return f"{engine} + {_pdf_to_png(pdf, out, dpi)}"
        raise RuntimeError("TikZ sources render to .pdf or .png (use an SVG source for .svg)")


def _finish_png(out: Path, dpi: int, gray: bool, transparent: bool = False) -> dict:
    info: dict = {}
    try:
        from PIL import Image
    except ImportError:
        return {"note": "Pillow not installed: DPI not stamped, blank-check skipped"}
    with Image.open(out) as src:
        src.load()
        im = src.convert("RGBA")
    flat = Image.new("RGBA", im.size, (255, 255, 255, 255))
    flat.alpha_composite(im)
    if not transparent:  # a figure for a paper or slide gets a white page, not alpha
        im = flat.convert("RGB")
        info["background"] = "white"
    else:
        info["background"] = "transparent"
    info["size_px"] = list(im.size)
    lo_hi = flat.convert("L").getextrema()
    info["blank"] = lo_hi[0] == lo_hi[1]
    im.save(out, dpi=(dpi, dpi))
    info["dpi"] = dpi
    if gray:
        gray_path = out.with_name(f"{out.stem}_gray.png")
        flat.convert("L").save(gray_path, dpi=(dpi, dpi))
        info["grayscale_preview"] = str(gray_path)
    return info


def render(src: Path, out: Path, dpi: int = 300, width_px: int | None = None,
           width_in: float | None = None, gray: bool = False, min_pt: float = 7.0,
           transparent: bool = False) -> dict:
    kind = SOURCE_TYPES.get(src.suffix.lower())
    if kind is None:
        raise ValueError(f"unsupported source {src.suffix!r}; use one of {sorted(SOURCE_TYPES)}")
    if out.suffix.lower() not in OUTPUT_TYPES:
        raise ValueError(f"unsupported output {out.suffix!r}; use .png, .pdf or .svg")
    if not src.is_file():
        raise FileNotFoundError(f"source not found: {src}")
    if width_in and not width_px:
        width_px = round(width_in * dpi)
    out.parent.mkdir(parents=True, exist_ok=True)
    result: dict = {"source": str(src), "output": str(out), "source_type": kind}
    if kind == "svg":
        result["lint"] = lint_svg(src, width_in, min_pt)
        if "error" in result["lint"]:
            raise ValueError(result["lint"]["error"])
        if out.suffix.lower() == ".svg":
            if src.resolve() != out.resolve():
                shutil.copyfile(src, out)
            result["renderer"] = "copy"
        else:
            result["renderer"] = _svg(src, out, dpi, width_px if out.suffix.lower() == ".png" else None)
    elif kind == "tikz":
        result["renderer"] = _tikz(src, out, dpi)
    elif kind == "dot":
        if not shutil.which("dot"):
            raise RuntimeError("Graphviz `dot` is not installed; draw the figure as SVG or TikZ instead")
        _run(["dot", f"-T{out.suffix[1:].lower()}", f"-Gdpi={dpi}", str(src), "-o", str(out)])
        result["renderer"] = "graphviz dot"
    else:
        if not shutil.which("mmdc"):
            raise RuntimeError("mermaid-cli `mmdc` is not installed; draw the figure as SVG instead")
        _run(["mmdc", "-i", str(src), "-o", str(out), "-s", str(max(1, round(dpi / 96)))])
        result["renderer"] = "mermaid-cli"
    if out.suffix.lower() == ".png":
        result["png"] = _finish_png(out, dpi, gray, transparent)
        if result["png"].get("blank"):
            result.setdefault("warnings", []).append("the rendered PNG is a single flat colour")
    return result


# --------------------------------------------------------------------------- review log

def score(log: Path, kind: str, doc_type: str, image: str, value: float, critique: str,
          source: str | None, max_iterations: int | None, prompt: str | None) -> dict:
    if not 0 <= value <= 10:
        raise ValueError("score must be between 0 and 10")
    limit = max_iterations or MAX_ITERATIONS[kind]
    threshold = threshold_for(kind, doc_type)
    if log.is_file():
        data = json.loads(log.read_text(encoding="utf-8"))
    else:
        data = {"kind": kind, "user_prompt": prompt, "doc_type": doc_type,
                "quality_threshold": threshold, "max_iterations": limit,
                "reviewer": "Claude, from the rendered image (keyless; no review model)",
                "criteria": CRITERIA[kind], "iterations": [], "final_image": None,
                "final_score": None, "success": False, "early_stop": False,
                "early_stop_reason": None}
    n = len(data["iterations"]) + 1
    if n > data["max_iterations"]:
        raise ValueError(f"already {data['max_iterations']} iterations logged; the loop is over")
    meets = value >= data["quality_threshold"]
    data["iterations"].append({"iteration": n, "image_path": image, "source_path": source,
                               "score": value, "critique": critique,
                               "needs_improvement": not meets})
    if meets or n == data["max_iterations"]:
        data.update({"final_image": image, "final_score": value, "success": True,
                     "meets_threshold": meets, "early_stop": meets and n < data["max_iterations"]})
        data["early_stop_reason"] = (
            f"score {value} meets threshold {data['quality_threshold']} for {doc_type}" if meets
            else f"maximum {data['max_iterations']} iterations reached below threshold "
                 f"{data['quality_threshold']}: report the remaining issues")
        decision = "DONE" if meets else "STOP (max iterations; below threshold)"
    else:
        decision = f"REVISE (score {value} < {data['quality_threshold']}); render as _v{n + 1}"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return {"iteration": n, "score": value, "threshold": data["quality_threshold"],
            "decision": decision, "log": str(log)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render", help="render a code-drawn figure locally (no API key)")
    r.add_argument("source", type=Path, help=".svg, .tex (standalone TikZ), .dot/.gv, or .mmd")
    r.add_argument("-o", "--output", type=Path, required=True, help=".png, .pdf or .svg")
    r.add_argument("--dpi", type=int, default=300)
    r.add_argument("--width-px", type=int, help="PNG width in pixels (overrides --dpi scaling)")
    r.add_argument("--width-in", type=float,
                   help="printed width in inches (e.g. 3.5 one column, 7.2 two columns): sets the "
                        "PNG width and the font-size check")
    r.add_argument("--min-font-pt", type=float, default=7.0)
    r.add_argument("--gray", action="store_true", help="also write <out>_gray.png")
    r.add_argument("--transparent", action="store_true",
                   help="keep a transparent PNG background (default: flatten onto white), e.g. "
                        "for an overlay pasted onto a photo")
    s = sub.add_parser("score", help="record Claude's review of a render and apply the threshold")
    s.add_argument("log", type=Path)
    s.add_argument("--kind", choices=sorted(THRESHOLDS), required=True)
    s.add_argument("--doc-type", default="default")
    s.add_argument("--image", required=True)
    s.add_argument("--score", type=float, required=True, help="0-10, two points per criterion")
    s.add_argument("--critique", required=True)
    s.add_argument("--source")
    s.add_argument("--prompt", help="the user's request (stored on the first iteration)")
    s.add_argument("--max-iterations", type=int)
    t = sub.add_parser("thresholds", help="print the document-type thresholds and criteria")
    t.add_argument("--kind", choices=sorted(THRESHOLDS), required=True)
    args = ap.parse_args(argv)
    try:
        if args.cmd == "render":
            out = render(args.source, args.output, args.dpi, args.width_px, args.width_in,
                         args.gray, args.min_font_pt, args.transparent)
        elif args.cmd == "score":
            out = score(args.log, args.kind, args.doc_type, args.image, args.score,
                        args.critique, args.source, args.max_iterations, args.prompt)
        else:
            out = {"kind": args.kind, "thresholds": thresholds(args.kind),
                   "max_iterations": MAX_ITERATIONS[args.kind], "criteria": CRITERIA[args.kind]}
    except (ValueError, RuntimeError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
