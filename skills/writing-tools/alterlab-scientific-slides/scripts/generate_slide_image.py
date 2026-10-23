#!/usr/bin/env python3
"""
Slide visuals, keyless by default.

Default (``--backend code``, no API key): a slide visual (diagram, icon row, concept graphic,
background) is drawn as code - SVG, or standalone TikZ - and this script renders it locally to a
PNG sized for a 16:9 slide, lints it, and prints the slide review threshold. With a text
description instead of a source file it prints the design brief (full slide or --visual-only)
and points to the keyless deck builders: scripts/build_deck.py (editable PowerPoint) and the
Beamer templates in assets/.

Optional (``--backend ai``, needs OPENROUTER_API_KEY): generate_slide_image_ai.py turns a
description into a complete slide image (or a visual with --visual-only) with Nano Banana Pro and
reviews it with Gemini; --attach passes reference images to the model.

Usage:
    python generate_slide_image.py "Three types of machine learning" -o slides/03.png --visual-only
    python generate_slide_image.py figures/pipeline.svg -o slides/pipeline.png
    python generate_slide_image.py "Title slide: ..." -o slides/01.png --backend ai
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import figure_tools  # noqa: E402

AI_SCRIPT = Path(__file__).with_name("generate_slide_image_ai.py")

KEYLESS_NOTE = """
KEYLESS PATH (no image model):
- Whole deck: write a deck plan and build an editable PowerPoint with
  scripts/build_deck.py (title / section / bullets / image / two_column / takeaway layouts,
  speaker notes, citations), or use a Beamer template from assets/ for equation-heavy talks.
- Slide visual: draw it as SVG on a 1920x1080 (full slide) or 1600x900 (content area) canvas,
  labels >= 24 px, then render it with this script and place the PNG in the deck.
- Data figures: plot the real data with matplotlib at slide size; never redraw numbers by hand.
- Review: export the deck to PDF (soffice --headless --convert-to pdf), convert pages with
  scripts/pdf_to_images.py, Read every page, fix overflow/overlap/small text, repeat.
""".strip()


def _brief(visual_only: bool, attachments) -> str:
    name = "VISUAL_ONLY_GUIDELINES" if visual_only else "FULL_SLIDE_GUIDELINES"
    consts = figure_tools.read_constants(AI_SCRIPT, [name], "SlideImageGenerator")
    parts = [consts.get(name, "").strip(), KEYLESS_NOTE]
    if attachments:
        parts.append("ATTACHED FIGURES: place these files in the deck as they are (do not redraw "
                     "them): " + ", ".join(attachments))
    threshold = figure_tools.threshold_for("slide", "default")
    criteria = "\n".join(f"  {i}. {c} (0-2)" for i, c in enumerate(figure_tools.CRITERIA["slide"], 1))
    parts.append(f"REVIEW (Claude, from the rendered page):\n{criteria}\n  Threshold "
                 f"{threshold}/10, at most {figure_tools.MAX_ITERATIONS['slide']} iterations.")
    return "\n\n".join(p for p in parts if p) + "\n"


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Render code-drawn slide visuals (keyless) or generate slide images with the "
                    "optional AI backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Keyless:
  python generate_slide_image.py "Data pipeline: collect -> clean -> model" -o slides/fig.png --visual-only
      prints the brief; Claude writes slides/fig.svg, then:
  python generate_slide_image.py slides/fig.svg -o slides/fig.png
  python build_deck.py deck.json -o talk.pptx        # the editable deck

Optional AI backend (OPENROUTER_API_KEY):
  python generate_slide_image.py "Title slide: ..." -o slides/01.png --backend ai
  python generate_slide_image.py "Slide about this chart" -o slides/05.png --attach chart.png --backend ai
        """
    )
    parser.add_argument("prompt", help="A visual source to render (.svg, .tex), or a description")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    parser.add_argument("--attach", action="append", dest="attachments", metavar="IMAGE",
                        help="Reference image(s): passed to the model with --backend ai; listed "
                             "in the keyless brief as figures to place as they are")
    parser.add_argument("--visual-only", action="store_true",
                        help="A visual for a slide rather than a complete slide")
    parser.add_argument("--backend", choices=["code", "ai"], default="code",
                        help="code (default, keyless) or ai (OpenRouter, needs a key)")
    parser.add_argument("--width-px", type=int, default=1920, help="PNG width (default 1920)")
    parser.add_argument("--iterations", type=int, default=2,
                        help="Maximum refinement iterations for --backend ai (max: 2)")
    parser.add_argument("--api-key", help="OpenRouter API key for --backend ai")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    source = Path(args.prompt)
    is_source = source.suffix.lower() in figure_tools.SOURCE_TYPES and len(args.prompt) < 4096

    if args.backend == "code":
        if not is_source:
            print("Keyless path: no image model is called and no API key is needed. Build the deck "
                  "with scripts/build_deck.py (or a Beamer template); draw any slide visual as SVG "
                  "following the brief on stdout and render it: python "
                  f"{Path(__file__).name} visual.svg -o {args.output}. "
                  "Pass --backend ai for the optional OpenRouter slide-image model.", file=sys.stderr)
            print(_brief(args.visual_only, args.attachments))
            return 0
        try:
            result = figure_tools.render(source, Path(args.output), 300, args.width_px)
        except (ValueError, RuntimeError, FileNotFoundError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        result["review"] = {"threshold": figure_tools.threshold_for("slide", "default"),
                            "criteria": figure_tools.CRITERIA["slide"],
                            "next": "Read the PNG at slide size; labels must stay legible "
                                    "from the back of the room"}
        print(json.dumps(result, indent=2))
        return 0

    # --backend ai: the explicit, keyed path. Never fall back silently.
    if is_source:
        parser.error("--backend ai takes a text description, not a source file")
    api_key = figure_tools.find_openrouter_key(args.api_key)
    if not api_key:
        print("Error: --backend ai needs OPENROUTER_API_KEY (environment, .env, or --api-key); not "
              "generating anything else instead. Keyless alternatives: build the deck with "
              "scripts/build_deck.py or a Beamer template, and draw slide visuals as SVG rendered "
              f"with `python {Path(__file__).name} visual.svg -o OUT`.", file=sys.stderr)
        return 2
    if not AI_SCRIPT.exists():
        print(f"Error: AI generation script not found: {AI_SCRIPT}", file=sys.stderr)
        return 1
    cmd = [sys.executable, str(AI_SCRIPT), args.prompt, "-o", args.output]
    for att in args.attachments or []:
        cmd.extend(["--attach", att])
    if args.visual_only:
        cmd.append("--visual-only")
    iterations = min(args.iterations, 2)
    if iterations != 2:
        cmd.extend(["--iterations", str(iterations)])
    if args.verbose:
        cmd.append("-v")
    # The key goes to the child through its environment, not argv (keeps it out of `ps`).
    child_env = os.environ.copy()
    child_env["OPENROUTER_API_KEY"] = api_key
    return subprocess.run(cmd, check=False, env=child_env).returncode


if __name__ == "__main__":
    sys.exit(main())
