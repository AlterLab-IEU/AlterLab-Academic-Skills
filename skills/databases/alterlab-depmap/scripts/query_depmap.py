#!/usr/bin/env python3
"""Resolve and download DepMap release files via the Figshare API (no key).

DepMap has no documented, stable public REST API for gene-level queries; the
supported programmatic path is the Figshare deposit, which exposes a list of
files (name + download_url) per release article. This helper lists those files
and resolves a download URL by name so you can fetch the matrix CSVs and analyse
them locally with pandas (see SKILL.md and references/dependency_analysis.md).

Article IDs (Figshare hosting stopped after 24Q4; newer releases such as 26Q1
are portal-only at https://depmap.org/portal/data_page/, which sits behind a
browser verification check):
    24Q4 -> 27993248   24Q2 -> 25880521   23Q4 -> 24667905

The Figshare files endpoint is paginated (10 files per page by default; a
release has ~70 files), so list_files() requests page_size=1000 and follows
pages — otherwise Model.csv and the Omics matrices are silently missing.

Smoke test (the --article option goes before the subcommand):
    uv run --with requests python query_depmap.py --article 27993248 list
    uv run --with requests python query_depmap.py --article 27993248 url CRISPRGeneEffect.csv
"""
import argparse
import json

import requests

FIGSHARE_API = "https://api.figshare.com/v2"
DEFAULT_ARTICLE = 27993248  # DepMap 24Q4 Public


def list_files(article_id: int, page_size: int = 1000) -> list[dict]:
    """Return [{name, download_url, size}, ...] for every file in a release article."""
    files: list[dict] = []
    page = 1
    while True:
        r = requests.get(
            f"{FIGSHARE_API}/articles/{article_id}/files",
            params={"page": page, "page_size": page_size},
            timeout=60,
        )
        r.raise_for_status()
        batch = r.json()
        files += [
            {"name": f["name"], "download_url": f["download_url"], "size": f.get("size")}
            for f in batch
        ]
        if len(batch) < page_size:
            return files
        page += 1


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
