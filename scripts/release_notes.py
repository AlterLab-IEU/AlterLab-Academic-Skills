#!/usr/bin/env python3
"""Print one version's CHANGELOG section as GitHub release-notes Markdown.

The release workflow uses this so the release page carries the real changelog instead of a
generic blurb. Release bodies render every newline as a line break, so the CHANGELOG's
hard-wrapped paragraphs and list items are re-flowed onto single lines; and a release page is
not the repository root, so relative links are rewritten to absolute ``blob/<ref>/`` URLs.

    python scripts/release_notes.py 3.0.0
    python scripts/release_notes.py 3.0.0 --repo owner/name --ref v3.0.0
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_REPO = "AlterLab-IEU/AlterLab-Academic-Skills"

# A line that opens a new Markdown block (list item, heading, table row, quote, fence).
BLOCK_START = re.compile(r"^\s*(?:[-*+] |\d+\. |#|\||>|```)")
# A relative link target: not a URL, an in-page anchor, or a mail link.
RELATIVE_LINK = re.compile(r"\]\((?!https?://|#|mailto:)([^)\s]+)\)")


def section(changelog: str, version: str) -> str:
    """The body under ``## [<version>]``, up to the next ``## [`` heading."""
    out: list[str] = []
    inside = False
    for line in changelog.splitlines():
        if line.startswith("## ["):
            if inside:
                break
            inside = line.startswith(f"## [{version}]")
            continue
        if inside:
            out.append(line)
    return "\n".join(out).strip("\n")


def reflow(markdown: str) -> str:
    """Join hard-wrapped continuation lines onto the line they continue."""
    out: list[str] = []
    in_fence = False
    for line in markdown.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence or not line.strip() or BLOCK_START.match(line) or not out:
            out.append(line)
            continue
        prev = out[-1]
        if not prev.strip() or prev.lstrip().startswith(("#", "|", "```")):
            out.append(line)
            continue
        out[-1] = f"{prev.rstrip()} {line.strip()}"
    return "\n".join(out)


def absolutize(markdown: str, repo: str, ref: str) -> str:
    """Point relative links at the repository files as of ``ref``."""
    return RELATIVE_LINK.sub(
        lambda m: f"](https://github.com/{repo}/blob/{ref}/{m.group(1)})", markdown
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("version", help="CHANGELOG version, e.g. 3.0.0")
    ap.add_argument("--changelog", type=pathlib.Path, default=REPO / "CHANGELOG.md")
    ap.add_argument("--repo", default=DEFAULT_REPO, help="owner/name for absolute links")
    ap.add_argument("--ref", help="git ref the links point at (default: v<version>)")
    args = ap.parse_args(argv)

    body = section(args.changelog.read_text(encoding="utf-8"), args.version)
    if not body:
        print(f"no '## [{args.version}]' section in {args.changelog}", file=sys.stderr)
        return 1
    print(absolutize(reflow(body), args.repo, args.ref or f"v{args.version}"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
