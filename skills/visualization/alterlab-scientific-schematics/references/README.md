# Code-Drawn Scientific Schematics (the keyless default)

Claude writes the diagram as code, renders it locally, looks at the render, and revises it.
No image model and no API key are involved. Compared with an AI-generated raster, a code-drawn
figure keeps every label and count exactly as typed, stays editable (fix one number without
redrawing), exports as vector PDF/SVG for the journal, and never sends unpublished content to a
third party. The optional AI raster backend is documented in `ai_generation_guide.md`.

## Pick the medium

| Diagram | Medium | Why |
|---------|--------|-----|
| Flowcharts (CONSORT, PRISMA), block/system diagrams, architectures, pathways | **SVG** (default) | Full control of boxes, arrows, colours; renders anywhere with cairosvg |
| Any figure going into a LaTeX manuscript, or labels with maths | **TikZ/PGF** standalone `.tex` | Uses the paper's fonts; `$\alpha$` labels; compiles with pdflatex |
| Electrical circuits | **schemdraw** (Python, matplotlib backend) | Standard component symbols, saved as SVG |
| Layout computed from data (a network, a phylogeny, a positioned grid) | **matplotlib** / networkx | Coordinates come from the data, not by hand |
| Auto-laid-out graphs when Graphviz or mermaid-cli is installed | `.dot` / `.mmd` | `figure_tools.py` calls `dot` / `mmdc` if present; otherwise use SVG |

## Render, check, review

```bash
# Render (SVG -> PNG at 300 dpi for a 7.2-inch two-column figure) and lint
uv run --python ">=3.11" --with cairosvg --with pillow python scripts/generate_schematic.py \
    figures/flow.svg -o figures/flow_v1.png --doc-type journal --width-in 7.2 --gray
# Vector copy for submission
uv run --python ">=3.11" --with cairosvg python scripts/figure_tools.py render \
    figures/flow.svg -o figures/flow.pdf
# TikZ: the same command with a .tex source (needs pdflatex/lualatex/xelatex/tectonic)
python scripts/generate_schematic.py figures/flow.tex -o figures/flow_v1.png --doc-type journal
```

The render step reports: the renderer used; the smallest label in points at the printed width
(warns below 7 pt); text that probably runs past the edge of its box (estimated at 0.5 em per
character, so confirm on the image); the colours used; external references; and whether the PNG
is blank. `--gray` writes `<name>_gray.png` for the grayscale check. PNGs are flattened onto
white unless you pass `--transparent` to `figure_tools.py render`.

Then **Read the PNG yourself** and score it, 0-2 points per criterion: scientific accuracy,
clarity and readability, label quality, layout and composition, professional appearance. Check
every number and label against the user's source, not against your memory. Record the score:

```bash
python scripts/figure_tools.py score figures/flow_review_log.json --kind schematic \
    --doc-type journal --image figures/flow_v1.png --source figures/flow.svg \
    --score 7.0 --critique "exclusion reasons overflow the right edge; arm labels unequal size"
```

The command answers `REVISE` (fix the source, render `_v2`, score again), `DONE` (threshold met),
or `STOP` (two iterations used: deliver the best version and list what is still below standard).
The log keeps the schema of the AI path's `*_review_log.json` (iterations, scores, critiques,
final image, early-stop reason) with `"reviewer"` saying the review was Claude's own.

## SVG building blocks

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 480" width="720" height="480"
     font-family="DejaVu Sans, Helvetica, Arial, sans-serif" font-size="13">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M0,0 L10,5 L0,10 z" fill="#333"/></marker>
    <marker id="bar" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="8" markerHeight="8" orient="auto">
      <path d="M5,0 V10" stroke="#333" stroke-width="2"/></marker>        <!-- inhibition -->
    <style>
      .box  { fill: #fff; stroke: #333; stroke-width: 1.4; }
      .edge { stroke: #333; stroke-width: 1.4; fill: none; marker-end: url(#arrow); }
      .inh  { stroke: #D55E00; stroke-width: 1.4; fill: none; marker-end: url(#bar); }
      .dash { stroke-dasharray: 5 3; }
    </style>
  </defs>
  <rect width="720" height="480" fill="#fff"/>
  <rect class="box" x="40" y="40" width="200" height="40" rx="4"/>
  <text x="140" y="65" text-anchor="middle">Centred label</text>
  <path class="edge" d="M140,80 V140"/>                       <!-- straight connector -->
  <path class="edge" d="M240,60 H320 V140"/>                 <!-- orthogonal elbow -->
</svg>
```

Rules that keep renders clean:

- One `<text>` per line; SVG never wraps. Keep about `box width / (0.55 x font-size)` characters
  per line, and give multi-line boxes 19-20 px line spacing at 13 px type.
- Put the font-family and font-size on the root (or a class) so the lint can compute print size.
- End connectors 2 px short of the target edge so the arrowhead touches, not overlaps, the box.
- Absolute coordinates are easiest to check; if you group with `<g transform=...>`, the overflow
  check skips those elements, so look harder at them on the render.
- Okabe-Ito colours (`#0072B2`, `#E69F00`, `#009E73`, `#D55E00`, `#CC79A7`, `#56B4E9`,
  `#F0E442`) with a second cue (shape, dash, label) for anything colour encodes.
- No "Figure 1" or caption inside the image; captions go in the manuscript.

## Recipes

**CONSORT 2010 (two arms).** Start from `assets/consort_template.svg`: stage labels down the
left (Enrolment, Allocation, Follow-up, Analysis), the assessed box on top, the exclusion box to
the right of the trunk with each reason and n, then two columns of boxes per arm (allocated /
received / did not receive with reasons; lost to follow-up and discontinued with reasons;
analysed / excluded from analysis with reasons). Every n must come from the user's data; check
that the arms sum to the randomised total and that each stage reconciles.

**PRISMA 2020.** Three bands top to bottom: Identification (records from databases / registers;
records removed before screening, with duplicates and automation exclusions), Screening (records
screened -> excluded; reports sought -> not retrieved; reports assessed -> excluded with
reasons), Included (studies and reports included). Exclusion boxes sit to the right of each
main box with a horizontal arrow; a second column for "other methods" is optional.

**Transformer encoder-decoder.** Two vertical stacks (encoder left, decoder right) inside
rounded frames labelled `N x`; bottom-to-top data flow: inputs -> embedding -> positional
encoding (circle with +) -> multi-head self-attention -> add & norm -> feed-forward -> add & norm.
The decoder adds masked multi-head self-attention and a cross-attention block; draw the
encoder-to-decoder connection as a single elbow into the cross-attention block, and residual
connections as thin arrows bypassing each sub-layer. Finish with linear -> softmax ->
output probabilities.

**Signalling pathway.** A vertical cascade (receptor at the membrane, drawn as a double line,
down to the nucleus box). Activation = arrow; inhibition = flat bar (`#bar` marker);
phosphorylation can be a small circled `P` on the target plus the arrow label. Label every arrow
as the user specified (e.g. "phosphorylation", "activation") with small text right of the line.

**System / block diagram.** Columns by layer (sensors -> controller -> network -> cloud -> client),
equal box sizes within a layer, one label per connection naming the protocol (I2C, UART, WiFi,
HTTPS) centred above the line; dashed lines for wireless links.

## TikZ standalone skeleton

```latex
\documentclass[tikz,border=4pt]{standalone}
\usepackage[T1]{fontenc}\usepackage{helvet}\renewcommand{\familydefault}{\sfdefault}
\usetikzlibrary{arrows.meta,positioning}
\definecolor{okblue}{HTML}{0072B2}
\begin{document}
\begin{tikzpicture}[node distance=7mm,
  box/.style={draw=okblue,fill=okblue!10,rounded corners=2pt,minimum width=26mm,minimum height=7mm,font=\small},
  act/.style={-{Stealth[length=2.5mm]},thick}]
  \node[box] (a) {EGFR};
  \node[box,below=of a] (b) {RAS-GTP};
  \draw[act] (a) -- node[right,font=\scriptsize]{activation} (b);
\end{tikzpicture}
\end{document}
```

In the manuscript, `\includegraphics{figures/flow.pdf}` keeps it vector.

## Circuits with schemdraw

```python
import schemdraw, schemdraw.elements as elm
with schemdraw.Drawing(show=False) as d:
    op = elm.Opamp(leads=True)
    elm.Line().left(d.unit / 4).at(op.in2); elm.Ground(lead=False)
    elm.Resistor().at(op.in1).left().label(r"$R_{in}$ 10 kΩ", loc="bot")
    elm.Line().up(d.unit / 2).at(op.in1)
    elm.Resistor().right().length(op.out.x - op.in1.x).label(r"$R_f$ 100 kΩ")
    elm.Line().down().toy(op.out)
    d.save("figures/inverting_amp.svg")
```

Run it with `uv run --python ">=3.11" --with schemdraw --with matplotlib python circuit.py`, then
render the SVG as above (schemdraw draws text as paths, so the font-size check reports nothing:
judge label size on the PNG).

## Troubleshooting (keyless)

| Symptom | Fix |
|---------|-----|
| `no SVG renderer: cairosvg unavailable` | Run through `uv run --with cairosvg`; if the Cairo C library is missing, install it (`brew install cairo`, `apt install libcairo2`) or librsvg (`rsvg-convert`) |
| Text overflow warning | Split the line into two `<text>` elements or widen the box; re-render |
| Smallest text below 7 pt | Raise `font-size`, or design at the real print width (`--width-in 3.5` for one column) |
| Arrowheads detached or overlapping | Shorten the path end by 2 px; use `markerUnits="userSpaceOnUse"` for a fixed head size |
| PNG looks black or empty | The SVG has no background and the viewer shows alpha: renders are flattened on white by default; check for a missing `viewBox` |
| `pdflatex failed` | Read the last lines of the log printed by the script; usually a missing `\usetikzlibrary` or an unescaped `%`, `&`, `_` |
