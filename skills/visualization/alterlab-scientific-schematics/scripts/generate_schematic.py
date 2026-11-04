#!/usr/bin/env python3
"""
Scientific schematics, keyless by default.

Default (``--backend code``, no API key): Claude draws the diagram as code - SVG, or a
standalone TikZ .tex for LaTeX papers - and this script renders it locally to PNG/PDF with
exact, editable labels, lints it (font size at print width, text overflowing its box), and
prints the review threshold for the document type. Claude then Reads the PNG, scores it on
the five criteria, and records the score with ``figure_tools.py score`` (revise below the
threshold, max 2 iterations).

Optional (``--backend ai``, needs OPENROUTER_API_KEY): the AI raster pipeline in
generate_schematic_ai.py (Nano Banana 2 generation + Gemini 3.1 Pro Preview review).

Usage:
    # 1. Print the design brief for a document type (guidelines, threshold, criteria)
    python generate_schematic.py --brief --doc-type journal

    # 2. Render the SVG/TikZ Claude wrote, and lint it
    python generate_schematic.py figures/consort.svg -o figures/consort_v1.png --doc-type journal

    # Optional AI raster generation
    python generate_schematic.py "CONSORT flowchart ..." -o figures/consort.png --backend ai
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import figure_tools  # noqa: E402

AI_SCRIPT = Path(__file__).with_name("generate_schematic_ai.py")
DOC_TYPES = ["journal", "conference", "poster", "presentation", "report", "grant", "thesis",
             "preprint", "default"]

DRAWING_CONVENTIONS = """
DRAWING THE FIGURE AS CODE (keyless path):
- Default to SVG: viewBox in px, explicit font-family (DejaVu Sans / Helvetica / Arial) and
  font-size on the root; boxes as <rect>, connectors as <path> with one arrowhead <marker>;
  multi-line labels as separate <text> lines (SVG does not wrap).
- For a LaTeX manuscript, a standalone TikZ file (\\documentclass[tikz,border=4pt]{standalone})
  keeps the paper's fonts; render it to PDF and include it with \\includegraphics.
- Size for the page: 3.5 in (one column) or 7.2 in (two columns); pass --width-in so the
  script checks the smallest label is >= 7 pt at print size.
- Copy every number and label verbatim from the user's data; never invent counts.
- Colour: Okabe-Ito (#0072B2 blue, #E69F00 orange, #009E73 green, #D55E00 vermillion,
  #CC79A7 purple, #56B4E9 sky blue, #F0E442 yellow) plus shape/line-style redundancy;
  check the --gray preview.
""".strip()


def _brief(doc_type: str) -> str:
    consts = figure_tools.read_constants(AI_SCRIPT, ["SCIENTIFIC_DIAGRAM_GUIDELINES"],
                                         "ScientificSchematicGenerator")
    guidelines = consts.get("SCIENTIFIC_DIAGRAM_GUIDELINES", "").strip()
    threshold = figure_tools.threshold_for("schematic", doc_type)
    criteria = "\n".join(f"  {i}. {c} (0-2)" for i, c in
                         enumerate(figure_tools.CRITERIA["schematic"], 1))
    return (f"{guidelines}\n\n{DRAWING_CONVENTIONS}\n\nREVIEW (Claude, from the rendered PNG):\n"
            f"{criteria}\n  Document type {doc_type}: threshold {threshold}/10, at most "
            f"{figure_tools.MAX_ITERATIONS['schematic']} iterations.\n")


def main():
    parser = argparse.ArgumentParser(
        description="Render code-drawn scientific schematics (keyless), or generate one with the "
                    "optional AI backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Document types (quality thresholds): journal 8.5, conference 8.0, thesis 8.0, grant 8.0,
preprint 7.5, report 7.5, poster 7.0, presentation 6.5, default 7.5.

Keyless loop:
  python generate_schematic.py --brief --doc-type journal
  # Claude writes figures/flow.svg (or flow.tex), then:
  python generate_schematic.py figures/flow.svg -o figures/flow_v1.png --doc-type journal --width-in 7.2
  # Claude Reads flow_v1.png, scores it, and records the score:
  python figure_tools.py score figures/flow_review_log.json --kind schematic --doc-type journal \\
      --image figures/flow_v1.png --source figures/flow.svg --score 8.0 --critique "..."

Environment Variables (optional AI backend only):
  OPENROUTER_API_KEY    Needed for --backend ai (or put it in a .env file)
  ALTERLAB_IMAGE_MODEL  Override the image model (default: google/gemini-3.1-flash-image)
  ALTERLAB_REVIEW_MODEL Override the review model (default: google/gemini-3.1-pro-preview)
        """
    )
    parser.add_argument("prompt", nargs="?",
                        help="A figure source to render (.svg, .tex, .dot, .mmd), or a text "
                             "description (prints the brief; with --backend ai, generates)")
    parser.add_argument("-o", "--output", help="Output path (.png, .pdf or .svg)")
    parser.add_argument("--doc-type", default="default", choices=DOC_TYPES,
                        help="Document type for quality threshold (default: default)")
    parser.add_argument("--backend", choices=["code", "ai"], default="code",
                        help="code (default, keyless) or ai (OpenRouter, needs a key)")
    parser.add_argument("--brief", action="store_true", help="Print the design brief and exit")
    parser.add_argument("--width-in", type=float, help="Printed width in inches (render check)")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--gray", action="store_true", help="Also write a grayscale preview")
    parser.add_argument("--iterations", type=int, default=2,
                        help="Maximum refinement iterations for --backend ai (max: 2)")
    parser.add_argument("--api-key", help="OpenRouter API key for --backend ai")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    if args.brief:
        print(_brief(args.doc_type))
        return 0
    if not args.prompt:
        parser.error("give a figure source or a description, or use --brief")
    source = Path(args.prompt)
    is_source = source.suffix.lower() in figure_tools.SOURCE_TYPES and len(args.prompt) < 4096

    if args.backend == "code":
        if not is_source:
            print("Keyless path: no image model is called and no API key is needed. Draw the "
                  "diagram as SVG (or standalone TikZ) following the brief on stdout, save it, then "
                  f"render it: python {Path(__file__).name} figure.svg -o "
                  f"{args.output or 'figure.png'} --doc-type {args.doc_type}. "
                  "Pass --backend ai for the optional OpenRouter image model.", file=sys.stderr)
            print(_brief(args.doc_type))
            return 0
        if not args.output:
            parser.error("--output is required to render a source")
        try:
            result = figure_tools.render(source, Path(args.output), args.dpi, None,
                                         args.width_in, args.gray)
        except (ValueError, RuntimeError, FileNotFoundError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        result["review"] = {"doc_type": args.doc_type,
                            "threshold": figure_tools.threshold_for("schematic", args.doc_type),
                            "criteria": figure_tools.CRITERIA["schematic"],
                            "next": "Read the PNG, score it 0-10, then record it with "
                                    "figure_tools.py score ... --kind schematic"}
        print(json.dumps(result, indent=2))
        return 0

    # --backend ai: the explicit, keyed path. Never fall back silently.
    if is_source:
        parser.error("--backend ai takes a text description, not a figure source")
    if not args.output:
        parser.error("--output is required")
    api_key = figure_tools.find_openrouter_key(args.api_key)
    if not api_key:
        print("error: --backend ai needs OPENROUTER_API_KEY (environment, .env, or --api-key); "
              "not generating anything else instead. Keyless alternative: draw the diagram as SVG "
              f"or TikZ and render it with `python {Path(__file__).name} figure.svg -o OUT` "
              "(see --brief).", file=sys.stderr)
        return 2
    if not AI_SCRIPT.exists():
        print(f"Error: AI generation script not found: {AI_SCRIPT}", file=sys.stderr)
        return 1
    # The key goes to the child through its environment, not argv (keeps it out of `ps`).
    child_env = os.environ.copy()
    child_env["OPENROUTER_API_KEY"] = api_key
    cmd = [sys.executable, str(AI_SCRIPT), args.prompt, "-o", args.output]
    if args.doc_type != "default":
        cmd.extend(["--doc-type", args.doc_type])
    iterations = min(args.iterations, 2)
    if iterations != 2:
        cmd.extend(["--iterations", str(iterations)])
    if args.verbose:
        cmd.append("-v")
    return subprocess.run(cmd, check=False, env=child_env).returncode


if __name__ == "__main__":
    sys.exit(main())
