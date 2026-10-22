#!/usr/bin/env python3
"""
Infographics, keyless by default.

Default (``--backend code``, no API key): Claude lays the infographic out as code (SVG, or
matplotlib for chart-heavy panels) with every number and word exact, and this script renders it
locally to PNG/PDF and lints it. With a text description instead of a source file it prints the
design brief for the chosen type, style, palette and document type - and, with ``--research``,
the sourcing protocol Claude follows with web search before any number goes on the page. Claude
then Reads the render, scores it, and records the score with ``figure_tools.py score``
(document-type threshold, max 3 iterations).

Optional (``--backend ai``, needs OPENROUTER_API_KEY): the AI raster pipeline in
generate_infographic_ai.py (Nano Banana Pro generation, Gemini 3.1 Pro review, Perplexity Sonar
research).

Usage:
    python generate_infographic.py "Lab milestones 2010-2025" -o figures/timeline.png --type timeline --style corporate
    python generate_infographic.py figures/timeline.svg -o figures/timeline_v1.png --doc-type report
    python generate_infographic.py --list-options
    python generate_infographic.py "AI market size" -o ai.png --type statistical --research --backend ai
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import figure_tools  # noqa: E402

AI_SCRIPT = Path(__file__).with_name("generate_infographic_ai.py")

# Available options for quick reference
INFOGRAPHIC_TYPES = [
    "statistical", "timeline", "process", "comparison", "list",
    "geographic", "hierarchical", "anatomical", "resume", "social"
]

STYLE_PRESETS = [
    "corporate", "healthcare", "technology", "nature", "education",
    "marketing", "finance", "nonprofit"
]

PALETTE_PRESETS = ["wong", "ibm", "tol"]

DOC_TYPES = [
    "marketing", "report", "presentation", "social", "internal", "draft", "default"
]

RESEARCH_PROTOCOL = """
RESEARCH STEP (--research, keyless): before drawing, gather the numbers with web search.
- Find 5-8 facts or statistics for the topic, preferring 2023-2026 primary sources (agency or
  statistics-office releases, peer-reviewed papers, the original market report) over aggregators.
- Record each one in <output stem>_research.json:
  {"topic": ..., "retrieved": "YYYY-MM-DD", "facts": [{"claim": ..., "value": ..., "unit": ...,
   "year": ..., "source_title": ..., "source_url": ...}]}
- Where sources disagree (market-size estimates often do), show the range or name the source on
  the graphic; never average silently or round into a new number.
- Every number on the infographic must appear in the research file or in the user's data, and
  the infographic carries a source line naming them.
""".strip()

DRAWING_CONVENTIONS = """
DRAWING THE INFOGRAPHIC AS CODE (keyless path):
- SVG with a viewBox matching the target (e.g. 1080x1080 social square, 1200x1800 portrait
  report page, 1920x1080 slide); font-family and font-size set on the root; one <text> per line.
- Draw charts from the numbers themselves: bar lengths and angles computed from the values (or
  render the chart panel with matplotlib and place it as a local <image>), with the value printed
  next to each mark.
- Copy every word, date and number verbatim from the user's data or the research file.
- Use the style's colours for structure and the palette for data series; check the --gray preview.
- Icons: simple geometric shapes or Unicode symbols drawn in SVG; no remote images.
""".strip()


def list_options():
    """Print available types, styles, and palettes."""
    print("""
INFOGRAPHIC OPTIONS

TYPES (--type):
  statistical   Data-driven infographic with charts, numbers, and statistics
  timeline      Chronological events or milestones
  process       Step-by-step instructions or workflow
  comparison    Side-by-side comparison of options
  list          Tips, facts, or key points in list format
  geographic    Map-based data visualization
  hierarchical  Pyramid or organizational structure
  anatomical    Visual metaphor explaining a system
  resume        Professional skills and experience visualization
  social        Social media optimized content

STYLE PRESETS (--style):
  corporate     Navy/gold, professional business style
  healthcare    Blue/cyan, trust-inducing medical style
  technology    Blue/violet, modern tech style
  nature        Green/brown, environmental organic style
  education     Blue/coral, friendly academic style
  marketing     Coral/teal/yellow, bold vibrant style
  finance       Navy/gold, conservative professional style
  nonprofit     Orange/sage/sand, warm human-centered style

COLORBLIND-SAFE PALETTES (--palette):
  wong          Wong's palette (7 colors) - most widely recommended
  ibm           IBM colorblind-safe (8 colors)
  tol           Tol's qualitative (12 colors)

DOCUMENT TYPES (--doc-type), quality thresholds:
  marketing 8.5 | report 8.0 | presentation 7.5 | social 7.0 | internal 7.0 | draft 6.5 | default 7.5

Examples:
  python generate_infographic.py "5 benefits of exercise" -o benefits.png --type list
  python generate_infographic.py benefits.svg -o benefits_v1.png --doc-type social
""")


def _brief(args) -> str:
    consts = figure_tools.read_constants(
        AI_SCRIPT, ["INFOGRAPHIC_TYPES", "STYLE_PRESETS", "PALETTE_PRESETS", "INFOGRAPHIC_GUIDELINES"],
        "InfographicGenerator")
    parts = [consts.get("INFOGRAPHIC_GUIDELINES", "").strip()]
    if args.type and args.type in consts.get("INFOGRAPHIC_TYPES", {}):
        parts.append(consts["INFOGRAPHIC_TYPES"][args.type]["guidelines"].strip())
    if args.style and args.style in consts.get("STYLE_PRESETS", {}):
        s = consts["STYLE_PRESETS"][args.style]
        parts.append(f"STYLE ({s['name']}): {s['description']}; colours {s['colors']}.")
    if args.palette and args.palette in consts.get("PALETTE_PRESETS", {}):
        pal = consts["PALETTE_PRESETS"][args.palette]
        parts.append(f"DATA PALETTE ({pal['name']}, colourblind-safe): {pal['colors']}.")
    parts.append(f"BACKGROUND: {args.background}.")
    parts.append(DRAWING_CONVENTIONS)
    if args.research:
        parts.append(RESEARCH_PROTOCOL)
    threshold = figure_tools.threshold_for("infographic", args.doc_type)
    criteria = "\n".join(f"  {i}. {c} (0-2)" for i, c in
                         enumerate(figure_tools.CRITERIA["infographic"], 1))
    parts.append(f"REVIEW (Claude, from the rendered PNG):\n{criteria}\n  Document type "
                 f"{args.doc_type}: threshold {threshold}/10, at most "
                 f"{figure_tools.MAX_ITERATIONS['infographic']} iterations.")
    return "\n\n".join(p for p in parts if p) + "\n"


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Render code-drawn infographics (keyless) or generate one with the optional "
                    "AI backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Keyless loop:
  1. python generate_infographic.py "Lab milestones 2010-2025" -o figures/timeline.png \\
         --type timeline --style corporate --doc-type report      # prints the brief
  2. Claude writes figures/timeline.svg from the user's data (and the research file).
  3. python generate_infographic.py figures/timeline.svg -o figures/timeline_v1.png \\
         --doc-type report --gray                                  # render + lint
  4. Claude Reads the PNG, scores it, then:
     python figure_tools.py score figures/timeline_review_log.json --kind infographic \\
         --doc-type report --image figures/timeline_v1.png --score 8.2 --critique "..."

Environment Variables (optional AI backend only):
  OPENROUTER_API_KEY    Needed for --backend ai (or put it in a .env file)
  ALTERLAB_IMAGE_MODEL  Override the image model (default: google/gemini-3-pro-image)
  ALTERLAB_REVIEW_MODEL Override the review model (default: google/gemini-3.1-pro-preview)
        """
    )
    parser.add_argument("prompt", nargs="?",
                        help="An infographic source to render (.svg, .tex), or a text "
                             "description (prints the brief; with --backend ai, generates)")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("--type", "-t", choices=INFOGRAPHIC_TYPES, help="Infographic type preset")
    parser.add_argument("--style", "-s", choices=STYLE_PRESETS, help="Industry style preset")
    parser.add_argument("--palette", "-p", choices=PALETTE_PRESETS, help="Colorblind-safe palette")
    parser.add_argument("--background", "-b", default="white",
                        help="Background color (default: white)")
    parser.add_argument("--doc-type", default="default", choices=DOC_TYPES,
                        help="Document type for quality threshold (default: default)")
    parser.add_argument("--backend", choices=["code", "ai"], default="code",
                        help="code (default, keyless) or ai (OpenRouter, needs a key)")
    parser.add_argument("--brief", action="store_true", help="Print the design brief and exit")
    parser.add_argument("--width-in", type=float, help="Printed width in inches (render check)")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--gray", action="store_true", help="Also write a grayscale preview")
    parser.add_argument("--iterations", type=int, default=3,
                        help="Maximum refinement iterations for --backend ai (default: 3)")
    parser.add_argument("--api-key", help="OpenRouter API key for --backend ai")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--research", "-r", action="store_true",
                        help="Source the numbers first: keyless, adds the web-search research "
                             "protocol to the brief; with --backend ai, Perplexity Sonar")
    parser.add_argument("--list-options", action="store_true",
                        help="List all available types, styles, and palettes")
    args = parser.parse_args()

    if args.list_options:
        list_options()
        return 0
    if args.brief:
        print(_brief(args))
        return 0
    if not args.prompt:
        parser.error("give a source to render or a description, or use --brief / --list-options")
    source = Path(args.prompt)
    is_source = source.suffix.lower() in figure_tools.SOURCE_TYPES and len(args.prompt) < 4096

    if args.backend == "code":
        if not is_source:
            print("Keyless path: no image model is called and no API key is needed. Lay the "
                  "infographic out as SVG following the brief on stdout"
                  + (" (do the research step first)" if args.research else "")
                  + f", then render it: python {Path(__file__).name} figure.svg -o "
                  f"{args.output or 'infographic.png'} --doc-type {args.doc_type}. "
                  "Pass --backend ai for the optional OpenRouter image model.", file=sys.stderr)
            print(_brief(args))
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
                            "threshold": figure_tools.threshold_for("infographic", args.doc_type),
                            "criteria": figure_tools.CRITERIA["infographic"],
                            "next": "Read the PNG, check every number against the data/research "
                                    "file, score it 0-10, then record it with figure_tools.py "
                                    "score ... --kind infographic"}
        print(json.dumps(result, indent=2))
        return 0

    # --backend ai: the explicit, keyed path. Never fall back silently.
    if is_source:
        parser.error("--backend ai takes a text description, not a source file")
    if not args.output:
        parser.error("--output is required")
    api_key = figure_tools.find_openrouter_key(args.api_key)
    if not api_key:
        print("error: --backend ai needs OPENROUTER_API_KEY (environment, .env, or --api-key); "
              "not generating anything else instead. Keyless alternative: lay the infographic out "
              f"as SVG and render it with `python {Path(__file__).name} figure.svg -o OUT` "
              "(see --brief; --research adds the web-search sourcing step).", file=sys.stderr)
        return 2
    if not AI_SCRIPT.exists():
        print(f"Error: AI generation script not found: {AI_SCRIPT}", file=sys.stderr)
        return 1
    # The key goes to the child through its environment, not argv (keeps it out of `ps`).
    child_env = os.environ.copy()
    child_env["OPENROUTER_API_KEY"] = api_key
    cmd = [sys.executable, str(AI_SCRIPT), args.prompt, "-o", args.output]
    for flag, value in (("--type", args.type), ("--style", args.style),
                        ("--palette", args.palette)):
        if value:
            cmd.extend([flag, value])
    if args.background != "white":
        cmd.extend(["--background", args.background])
    if args.doc_type != "default":
        cmd.extend(["--doc-type", args.doc_type])
    if args.iterations != 3:
        cmd.extend(["--iterations", str(args.iterations)])
    if args.verbose:
        cmd.append("-v")
    if args.research:
        cmd.append("--research")
    return subprocess.run(cmd, check=False, env=child_env).returncode


if __name__ == "__main__":
    sys.exit(main())
