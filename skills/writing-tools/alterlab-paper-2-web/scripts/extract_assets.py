#!/usr/bin/env python3
"""extract_assets.py - pull text, metadata and figures out of a paper PDF (keyless).

Claude reads the paper itself (the Read tool handles PDFs); this script does the mechanical
part that reading cannot: it saves the page text, the PDF metadata, every embedded raster
image, page renders, and high-resolution crops of figure regions, so the website, poster and
video can use the paper's real figures.

    uv run --python ">=3.11" --with pymupdf python scripts/extract_assets.py paper.pdf --out paper_assets/
    # vector figures: Read a page render, then crop the figure by page fractions (0-1)
    uv run --python ">=3.11" --with pymupdf python scripts/extract_assets.py paper.pdf --out paper_assets/ \\
        --clip 3:0.08,0.09,0.92,0.47:fig2 --dpi 300

Writes into --out: manifest.json (metadata, page count, captions found, files written),
text/page-NNN.txt, images/pNNN-iNN.<ext> (embedded rasters at least --min-px wide),
pages/page-NNN.png (with --pages), and figures/<name>.png for each --clip. With a LaTeX source
instead of a PDF, copy the figure files from the project directly; this script is for PDFs.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import pymupdf
except ImportError:  # pragma: no cover - reported to the user
    sys.exit("extract_assets.py needs PyMuPDF: `uv run --with pymupdf python scripts/extract_assets.py ...`")

CAPTION = re.compile(r"^\s*(Fig(?:ure)?\.?|Table)\s*(\d+)[.:]?\s*(.{0,160})", re.I)


def _clip(spec: str):
    try:
        page_s, box_s, name = spec.split(":")
        box = [float(v) for v in box_s.split(",")]
        if len(box) != 4 or not all(0 <= v <= 1 for v in box) or box[2] <= box[0] or box[3] <= box[1]:
            raise ValueError
        return int(page_s), box, name
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"--clip {spec!r}: use PAGE:X0,Y0,X1,Y1:NAME with fractions 0-1, X1>X0, Y1>Y0") from exc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--out", type=Path, required=True, help="output folder")
    ap.add_argument("--min-px", type=int, default=200, help="skip embedded images narrower than this")
    ap.add_argument("--pages", action="store_true", help="also render every page to PNG")
    ap.add_argument("--clip", type=_clip, action="append", default=[],
                    help="PAGE:X0,Y0,X1,Y1:NAME - render a region (page fractions) to figures/NAME.png")
    ap.add_argument("--dpi", type=int, default=200, help="resolution for page renders and clips")
    args = ap.parse_args(argv)
    if not args.pdf.is_file():
        print(f"error: not found: {args.pdf}", file=sys.stderr)
        return 2
    try:
        doc = pymupdf.open(str(args.pdf))
    except Exception as exc:  # noqa: BLE001 - any parse failure is reported, not raised
        print(f"error: cannot open {args.pdf}: {exc}", file=sys.stderr)
        return 2
    out = args.out
    for sub in ("text", "images"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    manifest: dict = {"source": str(args.pdf), "pages": doc.page_count,
                      "metadata": {k: v for k, v in (doc.metadata or {}).items() if v},
                      "captions": [], "images": [], "page_renders": [], "figures": [],
                      "warnings": []}
    chars = 0
    for pno, page in enumerate(doc, 1):
        text = page.get_text("text")
        chars += len(text.strip())
        (out / "text" / f"page-{pno:03d}.txt").write_text(text, encoding="utf-8")
        for block in page.get_text("blocks"):
            m = CAPTION.match(block[4].replace("\n", " "))
            if m:
                manifest["captions"].append({"page": pno, "label": f"{m.group(1)} {m.group(2)}",
                                             "text": m.group(3).strip(),
                                             "bbox_fraction": [round(block[0] / page.rect.width, 3),
                                                               round(block[1] / page.rect.height, 3),
                                                               round(block[2] / page.rect.width, 3),
                                                               round(block[3] / page.rect.height, 3)]})
        for ino, img in enumerate(page.get_images(full=True), 1):
            info = doc.extract_image(img[0])
            if not info or info.get("width", 0) < args.min_px:
                continue
            path = out / "images" / f"p{pno:03d}-i{ino:02d}.{info.get('ext', 'png')}"
            path.write_bytes(info["image"])
            manifest["images"].append({"page": pno, "file": str(path),
                                       "size_px": [info.get("width"), info.get("height")]})
        if args.pages:
            (out / "pages").mkdir(exist_ok=True)
            path = out / "pages" / f"page-{pno:03d}.png"
            page.get_pixmap(dpi=args.dpi).save(str(path))
            manifest["page_renders"].append(str(path))
    for pno, (x0, y0, x1, y1), name in args.clip:
        if not 1 <= pno <= doc.page_count:
            manifest["warnings"].append(f"--clip page {pno} out of range 1-{doc.page_count}")
            continue
        page = doc[pno - 1]
        r = page.rect
        rect = pymupdf.Rect(r.x0 + x0 * r.width, r.y0 + y0 * r.height,
                            r.x0 + x1 * r.width, r.y0 + y1 * r.height)
        (out / "figures").mkdir(exist_ok=True)
        path = out / "figures" / f"{name}.png"
        page.get_pixmap(dpi=args.dpi, clip=rect).save(str(path))
        manifest["figures"].append({"page": pno, "name": name, "file": str(path)})
    if chars < 200 * max(1, doc.page_count) // 4:
        manifest["warnings"].append("very little text layer: the PDF may be scanned; Read the page "
                                    "renders instead of relying on text/")
    if not manifest["images"] and not args.clip:
        manifest["warnings"].append("no embedded raster figures: the figures are probably vector; "
                                    "render pages (--pages), then crop them with --clip")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False),
                                       encoding="utf-8")
    print(json.dumps({k: (v if k not in ("captions",) else v[:12]) for k, v in manifest.items()},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
