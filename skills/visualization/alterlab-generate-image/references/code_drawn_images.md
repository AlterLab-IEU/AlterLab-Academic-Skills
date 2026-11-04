# Code-Drawn Images and Keyless Edits

The default route of alterlab-generate-image: Claude writes the picture as code, renders it
locally, looks at the result, and refines it. No image model, no key, nothing leaves the
machine. This file collects the techniques that make code-drawn images look finished.

## Canvas sizes

| Use | Size | Command flag |
|-----|------|--------------|
| 16:9 slide (full-bleed background or hero) | 1920x1080 px (viewBox 0 0 1920 1080) | `--width-px 1920` |
| Journal figure, one / two columns | 3.5 in / 7.2 in at 300 dpi | `--width-in 3.5` / `--width-in 7.2` |
| Poster hero banner | the poster box in inches at 150-300 dpi | `--width-in 36 --dpi 150` |
| Square social / website card | 1080x1080 or 1200x630 px | `--width-px 1080` |

## SVG techniques for illustration

- **Layering** builds depth: a background gradient, then large soft shapes, then the subject,
  then highlights. Later elements paint over earlier ones.
- **Gradients** give volume without filters (cairosvg renders gradients reliably; SVG filter
  effects such as blur are only partly supported, so avoid relying on them):
  ```xml
  <radialGradient id="cell" cx="0.4" cy="0.35" r="0.7">
    <stop offset="0" stop-color="#F6C9A8"/><stop offset="1" stop-color="#C9765A"/>
  </radialGradient>
  <path d="M..." fill="url(#cell)" stroke="#8A3B2A" stroke-width="3"/>
  ```
- **Organic outlines**: build irregular cell or blob outlines from a closed cubic Bézier path
  (`C` segments) through 8-12 points jittered around a circle; generate the points in Python.
- **Repetition with variation** (T cells, antibodies, molecules): define a shape once in
  `<defs>` / `<symbol>` and place it with `<use href="#tcell" x=".." y=".." transform="rotate(..)"/>`,
  varying position, size and rotation.
- **Opacity** separates planes: background motifs at 0.1-0.25 opacity, subject at 1.
- **Colour**: a restrained palette (3-5 colours) reads as professional; Okabe-Ito for anything
  that encodes meaning; the user's brand colours when given.
- **Text** only if asked; keep it as live `<text>` so it is exact and editable.

### Example: immunotherapy concept illustration (structure)

1. Background: dark-to-mid blue radial gradient suggesting a microscopic field.
2. Two or three cancer cells: large irregular Bézier blobs with a warm radial gradient and a
   darker nucleus blob; small surface bumps as circles along the outline.
3. T cells: smaller round cells (cool gradient) touching the cancer cells, with short
   "synapse" lines at the contact.
4. Antibodies: a `<symbol>` of a Y (three rounded strokes) scattered near the cancer cells,
   some bound to the surface.
5. A few blurred-looking out-of-focus cells: same shapes at 0.15 opacity, larger, behind.

State in the caption that it is a schematic illustration, not microscopy.

## Procedural backgrounds (Python writes the SVG)

```python
import math, random
random.seed(3); W, H = 1920, 1080
out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
       '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F7FAFD"/>'
       '<stop offset="1" stop-color="#D6E6F5"/></linearGradient></defs>',
       f'<rect width="{W}" height="{H}" fill="url(#bg)"/><g fill="none" stroke="#0072B2">']
for _ in range(26):
    cx, cy = random.uniform(0, W), random.uniform(0, H)
    if W*.25 < cx < W*.75 and H*.3 < cy < H*.7:
        continue                                   # keep the title area calm
    r, op = random.uniform(22, 48), random.uniform(.10, .22)
    pts = " ".join(f"{cx + r*math.cos(math.radians(60*k+30)):.1f},{cy + r*math.sin(math.radians(60*k+30)):.1f}"
                   for k in range(6))
    out.append(f'<polygon points="{pts}" stroke-width="2.5" stroke-opacity="{op:.2f}"/>')
out += ["</g>", "</svg>"]
open("slides/background.svg", "w").write("\n".join(out))
```

Render with `python scripts/figure_tools.py render slides/background.svg -o slides/background.png --width-px 1920`.
Leave the area where the title goes quiet, keep motif opacity low, and check the render with a
title placed over it.

## Editing existing images

`scripts/edit_image.py` applies Pillow operations in order (see `--help`). Read the image first
and take coordinates from it; `--info` gives size, mode, DPI and EXIF.

| Task | Operations |
|------|-----------|
| Figure panel from a micrograph | `--crop`, `--scale-bar LEN,UNITS_PER_PX,um,br`, `--arrow`, `--text` |
| De-identify a screenshot or photo | `--redact X0,Y0,X1,Y1,pixelate` (or `fill` for text you must not leak) |
| Web/slide versions | `--resize 1600x0`, `--pad 20,#FFFFFF`, `--dpi 150` |
| Add an object (glasses, badge, icon) | draw it as SVG sized to the spot → `figure_tools.py render x.svg -o x.png --transparent` → `--overlay x.png@X,Y` |
| Grayscale / contrast fix for print | `--grayscale`, `--contrast 1.2` |

Scale bars use the instrument's true pixel size; never resize an image after adding one
(resampling changes the pixels-per-micron). Never alter scientific image data beyond what
journal image-integrity rules allow (uniform brightness/contrast across the whole image,
cropping); say what was changed.

## Real photographs without an image model

When the user needs a photograph (a real lab, a field site, an instrument) and has no image-
model key, look for an openly licensed photo instead of generating one:

- Wikimedia Commons: search `https://commons.wikimedia.org/w/index.php?search=...&title=Special:MediaSearch&type=image`
  with WebFetch/WebSearch, open the file page, and record title, author, licence (CC0, CC BY,
  CC BY-SA) and URL. The API (`commons.wikimedia.org/w/api.php`) answers without a key but
  rate-limits busy shared IPs; send a descriptive User-Agent and back off on HTTP 429.
- Download the file, then crop/resize it with `edit_image.py` and credit it where it is shown
  ("Photo: Author, CC BY 4.0, via Wikimedia Commons").
- Do not use images whose licence is unclear, and never present a code drawing or an AI image
  as a photograph of a real place or experiment.
