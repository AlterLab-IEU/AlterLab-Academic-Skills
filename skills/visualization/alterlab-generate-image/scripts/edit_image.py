#!/usr/bin/env python3
"""edit_image.py - keyless edits of an existing image with Pillow (no model, no API key).

Claude looks at the image first (Read), decides the coordinates, and applies operations in
the order they are given. Coordinates are pixels in the image as it stands at that step, with
(0, 0) at the top-left. ``--info`` prints the size, mode, DPI and EXIF summary.

    python edit_image.py --input photo.jpg --info
    python edit_image.py -i micrograph.png -o annotated.png \\
        --crop 0,0,1024,768 --scale-bar 10,0.25,um,br --arrow 300,200,380,260,#FFFFFF,4 \\
        --text "390,270,28,#FFFFFF:mitochondrion"
    python edit_image.py -i screenshot.png -o deidentified.png --redact 40,30,420,70,pixelate
    python edit_image.py -i portrait.png -o portrait_glasses.png \\
        --overlay glasses.png@190,205          # glasses drawn as SVG, rendered with --transparent

Operations (repeatable, applied in order):
  --crop X0,Y0,X1,Y1              keep this box
  --resize WxH | --scale F        Lanczos resampling (one side 0 keeps the aspect ratio)
  --rotate DEG                    counter-clockwise, canvas expanded
  --flip h|v
  --grayscale
  --brightness F / --contrast F / --saturation F / --sharpness F   (1.0 = unchanged)
  --blur R                        Gaussian blur of the whole image
  --redact X0,Y0,X1,Y1[,MODE]     MODE blur (default), pixelate or fill: hide faces, names, IDs
  --rect / --ellipse X0,Y0,X1,Y1[,OUTLINE[,WIDTH[,FILL]]]   colours as #RRGGBB(AA) or names; none
  --line / --arrow X0,Y0,X1,Y1[,COLOR[,WIDTH]]
  --text "X,Y[,SIZE[,COLOR[,ANCHOR]]]:TEXT"   ANCHOR as in Pillow (la = left-ascender, mm = centre)
  --scale-bar LENGTH,UNITS_PER_PX,UNIT[,CORNER]   e.g. 10,0.25,um,br -> a 40-px "10 µm" bar
  --overlay FILE@X,Y[,OPACITY]    paste an image (alpha respected) with its top-left at X,Y
  --pad N[,COLOR]                 add a border of N px
Output format follows the --output suffix; --dpi stamps the resolution (default: keep).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

try:
    from PIL import (ExifTags, Image, ImageColor, ImageDraw, ImageEnhance, ImageFilter, ImageFont,
                     ImageOps, ImageStat)
except ImportError:  # pragma: no cover - reported to the user
    sys.exit("edit_image.py needs Pillow: run it with `uv run --with pillow python scripts/edit_image.py ...`")

UNITS = {"um": "µm", "nm": "nm", "mm": "mm", "cm": "cm", "m": "m", "km": "km", "px": "px"}


class OpAction(argparse.Action):
    """Collect every operation, in command-line order, into namespace.ops."""

    def __call__(self, parser, namespace, values, option_string=None):
        ops = getattr(namespace, "ops", None) or []
        ops.append((self.dest, values))
        namespace.ops = ops


def _nums(text: str, n: int, what: str) -> list[float]:
    parts = [p.strip() for p in text.split(",")]
    try:
        vals = [float(p) for p in parts[:n]]
    except ValueError as exc:
        raise ValueError(f"{what}: expected {n} numbers, got {text!r}") from exc
    if len(vals) != n:
        raise ValueError(f"{what}: expected {n} numbers, got {text!r}")
    return vals


def _colour(text: str | None, default):
    if text is None or text == "":
        return default
    if text.lower() == "none":
        return None
    return ImageColor.getcolor(text, "RGBA")


def _font(size: int):
    for name in ("DejaVuSans.ttf", "Arial.ttf", "Helvetica.ttc", "LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow < 10.1
        return ImageFont.load_default()


def _box(text: str, what: str) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = (round(v) for v in _nums(text, 4, what))
    if x1 <= x0 or y1 <= y0:
        raise ValueError(f"{what}: X1,Y1 must be right of and below X0,Y0 ({text!r})")
    return x0, y0, x1, y1


def _auto_contrast_colour(im: Image.Image, box) -> tuple:
    mean = ImageStat.Stat(im.convert("L").crop(box)).mean[0]
    return (0, 0, 0, 255) if mean > 128 else (255, 255, 255, 255)


def apply(im: Image.Image, op: str, value: str, log: list) -> Image.Image:
    draw = None
    if op == "crop":
        im = im.crop(_box(value, "--crop"))
    elif op == "resize":
        w, h = (int(v) for v in value.lower().split("x"))
        if w == 0:
            w = round(im.width * h / im.height)
        if h == 0:
            h = round(im.height * w / im.width)
        im = im.resize((w, h), Image.LANCZOS)
    elif op == "scale":
        f = float(value)
        im = im.resize((max(1, round(im.width * f)), max(1, round(im.height * f))), Image.LANCZOS)
    elif op == "rotate":
        im = im.rotate(float(value), expand=True, resample=Image.BICUBIC,
                       fillcolor=(255, 255, 255, 0))
    elif op == "flip":
        im = ImageOps.mirror(im) if value.lower().startswith("h") else ImageOps.flip(im)
    elif op == "grayscale":
        im = ImageOps.grayscale(im).convert("RGBA")
    elif op in ("brightness", "contrast", "saturation", "sharpness"):
        enh = {"brightness": ImageEnhance.Brightness, "contrast": ImageEnhance.Contrast,
               "saturation": ImageEnhance.Color, "sharpness": ImageEnhance.Sharpness}[op]
        alpha = im.getchannel("A")
        im = enh(im.convert("RGB")).enhance(float(value)).convert("RGBA")
        im.putalpha(alpha)
    elif op == "blur":
        im = im.filter(ImageFilter.GaussianBlur(float(value)))
    elif op == "redact":
        parts = value.split(",")
        box = _box(",".join(parts[:4]), "--redact")
        mode = (parts[4].strip().lower() if len(parts) > 4 else "blur")
        region = im.crop(box)
        if mode == "pixelate":
            small = region.resize((max(1, region.width // 12), max(1, region.height // 12)),
                                  Image.NEAREST)
            region = small.resize(region.size, Image.NEAREST)
        elif mode == "fill":
            region = Image.new("RGBA", region.size, (0, 0, 0, 255))
        else:
            region = region.filter(ImageFilter.GaussianBlur(max(8, region.height // 4)))
        im.paste(region, box[:2])
    elif op in ("rect", "ellipse", "line", "arrow"):
        parts = value.split(",")
        coords = [round(v) for v in _nums(",".join(parts[:4]), 4, f"--{op}")]
        colour = _colour(parts[4].strip() if len(parts) > 4 else None, (220, 38, 38, 255))
        width = int(parts[5]) if len(parts) > 5 and parts[5].strip() else 4
        fill = _colour(parts[6].strip() if len(parts) > 6 else "none", None)
        draw = ImageDraw.Draw(im, "RGBA")
        if op in ("rect", "ellipse"):
            if coords[2] <= coords[0] or coords[3] <= coords[1]:
                raise ValueError(f"--{op}: X1,Y1 must be right of and below X0,Y0")
            shape = draw.rectangle if op == "rect" else draw.ellipse
            shape(coords, outline=colour, width=width, fill=fill)
        else:
            draw.line(coords, fill=colour, width=width)
            if op == "arrow":
                x0, y0, x1, y1 = coords
                ang = math.atan2(y1 - y0, x1 - x0)
                head = max(10, width * 4)
                pts = [(x1, y1)] + [(x1 - head * math.cos(ang + s * 0.45),
                                     y1 - head * math.sin(ang + s * 0.45)) for s in (-1, 1)]
                draw.polygon(pts, fill=colour)
    elif op == "text":
        params, _, text = value.partition(":")
        if not text:
            raise ValueError('--text: use "X,Y[,SIZE[,COLOR[,ANCHOR]]]:TEXT"')
        parts = params.split(",")
        x, y = _nums(",".join(parts[:2]), 2, "--text")
        size = int(parts[2]) if len(parts) > 2 and parts[2].strip() else max(14, im.height // 30)
        colour = _colour(parts[3].strip() if len(parts) > 3 else None, (0, 0, 0, 255))
        anchor = parts[4].strip() if len(parts) > 4 and parts[4].strip() else "la"
        draw = ImageDraw.Draw(im, "RGBA")
        font = _font(size)
        draw.text((x, y), text, fill=colour, font=font, anchor=anchor)
        l, t_, r, b = draw.textbbox((x, y), text, font=font, anchor=anchor)
        if l < 0 or t_ < 0 or r > im.width or b > im.height:
            log.append({"warning": f"text {text[:40]!r} runs off the image (box {l:.0f},{t_:.0f},"
                                   f"{r:.0f},{b:.0f}; image {im.width}x{im.height})"})
    elif op == "scale_bar":
        parts = [p.strip() for p in value.split(",")]
        if len(parts) < 3:
            raise ValueError("--scale-bar: use LENGTH,UNITS_PER_PX,UNIT[,CORNER]")
        length, per_px = float(parts[0]), float(parts[1])
        if per_px <= 0:
            raise ValueError("--scale-bar: UNITS_PER_PX must be positive")
        unit = UNITS.get(parts[2], parts[2])
        corner = parts[3] if len(parts) > 3 else "br"
        px = round(length / per_px)
        margin, thick = max(10, im.width // 40), max(4, im.height // 120)
        size = max(14, im.height // 28)
        x0 = margin if corner.endswith("l") else im.width - margin - px
        y_bar = (margin + size + 6) if corner.startswith("t") else im.height - margin - thick
        label_y = y_bar - 6
        colour = _auto_contrast_colour(im, (x0, max(0, y_bar - size - 8), x0 + px,
                                            min(im.height, y_bar + thick)))
        draw = ImageDraw.Draw(im, "RGBA")
        draw.rectangle([x0, y_bar, x0 + px, y_bar + thick], fill=colour)
        label = f"{length:g} {unit}"
        draw.text((x0 + px / 2, label_y), label, fill=colour, font=_font(size), anchor="md")
        log.append({"scale_bar_px": px, "label": label})
    elif op == "overlay":
        path, _, where = value.rpartition("@")
        parts = where.split(",")
        x, y = (round(v) for v in _nums(",".join(parts[:2]), 2, "--overlay"))
        opacity = float(parts[2]) if len(parts) > 2 else 1.0
        with Image.open(path) as ov:
            ov = ov.convert("RGBA")
        if opacity < 1:
            ov.putalpha(ov.getchannel("A").point(lambda a: round(a * opacity)))
        im.alpha_composite(ov, (x, y))
    elif op == "pad":
        parts = value.split(",")
        n = int(parts[0])
        colour = _colour(parts[1].strip() if len(parts) > 1 else None, (255, 255, 255, 255))
        im = ImageOps.expand(im, border=n, fill=colour)
    else:  # pragma: no cover
        raise ValueError(f"unknown operation {op}")
    log.append({"op": op.replace("_", "-"), "value": value, "size": list(im.size)})
    return im


def info(path: Path) -> dict:
    with Image.open(path) as im:
        exif = im.getexif()
        tags = {ExifTags.TAGS.get(k, str(k)): str(v)[:80] for k, v in exif.items()}
        return {"file": str(path), "format": im.format, "mode": im.mode, "size_px": list(im.size),
                "dpi": im.info.get("dpi"), "exif": tags}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-i", "--input", type=Path, required=True, help="image to edit")
    ap.add_argument("-o", "--output", type=Path, help="where to write the result")
    ap.add_argument("--info", action="store_true", help="print size, mode, DPI and EXIF, then exit")
    ap.add_argument("--dpi", type=int, help="stamp this resolution on the output")
    for name in ("crop", "resize", "scale", "rotate", "flip", "brightness", "contrast",
                 "saturation", "sharpness", "blur", "redact", "rect", "ellipse", "line", "arrow",
                 "text", "scale-bar", "overlay", "pad"):
        ap.add_argument(f"--{name}", dest=name.replace("-", "_"), action=OpAction)
    ap.add_argument("--grayscale", dest="grayscale", action=OpAction, nargs=0)
    args = ap.parse_args(argv)
    if not args.input.is_file():
        print(f"error: input not found: {args.input}", file=sys.stderr)
        return 2
    if args.info:
        print(json.dumps(info(args.input), indent=2, ensure_ascii=False))
        return 0
    ops = getattr(args, "ops", None) or []
    if not args.output:
        ap.error("--output is required unless --info is given")
    if not ops:
        ap.error("no operation given (see --help)")
    log: list = []
    try:
        with Image.open(args.input) as src:
            dpi = src.info.get("dpi")
            im = src.convert("RGBA")
        for op, value in ops:
            im = apply(im, op, "" if isinstance(value, list) else value, log)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.suffix.lower() in (".jpg", ".jpeg"):
        flat = Image.new("RGB", im.size, (255, 255, 255))
        flat.paste(im, mask=im.getchannel("A"))
        im = flat
    save_kw = {}
    if args.dpi or dpi:
        save_kw["dpi"] = (args.dpi, args.dpi) if args.dpi else dpi
    im.save(args.output, **save_kw)
    print(json.dumps({"input": str(args.input), "output": str(args.output),
                      "size_px": list(im.size), "operations": log}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
