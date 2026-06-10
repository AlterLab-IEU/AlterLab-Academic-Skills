#!/usr/bin/env python3
"""Resolve and download DepMap release files via the Figshare API (no key).

DepMap has no documented, stable public REST API for gene-level queries; the
supported programmatic path is the Figshare deposit, which exposes a list of
files (name + download_url) per release article. This helper lists those files
and resolves a download URL by name so you can fetch the matrix CSVs and analyse
them locally with pandas (see SKILL.md and references/dependency_analysis.md).

Article IDs (Figshare hosting stopped after 24Q4; newer releases are portal-only
at https://depmap.org/portal/data_page/):
    24Q4 -> 27993248   24Q2 -> 25880521   23Q4 -> 24667905

Smoke test (the --article option goes before the subcommand):
    uv run --with requests python query_depmap.py --article 27993248 list
    uv run --with requests python query_depmap.py --article 27993248 url CRISPRGeneEffect.csv
"""
import argparse
import json

import requests

FIGSHARE_API = "https://api.figshare.com/v2"
DEFAULT_ARTICLE = 27993248  # DepMap 24Q4 Public


def list_files(article_id: int) -> list[dict]:
    """Return [{name, download_url, size}, ...] for a Figshare release article."""
    r = requests.get(f"{FIGSHARE_API}/articles/{article_id}/files", timeout=60)
    r.raise_for_status()
    return [
        {"name": f["name"], "download_url": f["download_url"], "size": f.get("size")}
        for f in r.json()
    ]


def resolve_url(filename: str, article_id: int) -> str:
    """Resolve the download URL for a named file in a release (exact match)."""
    for f in list_files(article_id):
        if f["name"] == filename:
            return f["download_url"]
    raise KeyError(f"{filename!r} not found in Figshare article {article_id}")


def main() -> None:
    p = argparse.ArgumentParser(description="Resolve DepMap release files via Figshare API.")
    p.add_argument("--article", type=int, default=DEFAULT_ARTICLE,
                   help=f"Figshare article ID (default {DEFAULT_ARTICLE} = 24Q4)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List all files (name, size, download_url) in a release.")

    pu = sub.add_parser("url", help="Resolve the download URL for one file by name.")
    pu.add_argument("filename")

    args = p.parse_args()
    if args.cmd == "list":
        print(json.dumps(list_files(args.article), indent=2))
    else:
        print(resolve_url(args.filename, args.article))


if __name__ == "__main__":
    main()
