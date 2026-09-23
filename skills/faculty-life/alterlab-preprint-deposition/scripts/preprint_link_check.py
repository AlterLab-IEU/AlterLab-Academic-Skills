#!/usr/bin/env python3
"""Confirm a bioRxiv/medRxiv preprint DOI and surface any published-article link.

Queries the keyless bioRxiv/medRxiv content API (api.biorxiv.org) to (1) confirm
a preprint DOI resolves and report its versions, and (2) surface the
preprint-to-publication link so a posted preprint can be linked to its version of
record. No API key is required.

Endpoints (checked on api.biorxiv.org, 2026-09-23):
  /details/{server}/{doi}/na/json -> manuscript details + versions; each record
                                     carries a `published` field (article DOI or
                                     "NA") once the link is detected
  /pubs/{server}/{doi}/na/json    -> journal name/date for the link; currently
                                     returns nothing for 10.64898 DOIs, so the
                                     `published` field is read first

bioRxiv/medRxiv DOIs use the openRxiv prefix 10.64898 for preprints posted from
1 Dec 2025 and 10.1101 before that; both work here. `server` is `biorxiv` or
`medrxiv`. Degrades gracefully offline.

Auto-selects an HTTP backend: uses `requests` if installed, else stdlib urllib.

    uv run python scripts/preprint_link_check.py --server biorxiv --doi 10.1101/2020.01.01.000000
    uv run python scripts/preprint_link_check.py --server biorxiv --doi 10.64898/2026.01.13.699089
"""
from __future__ import annotations

import argparse
import json
import sys

API_BASE = "https://api.biorxiv.org"
USER_AGENT = "alterlab-preprint-deposition/1.1 (+https://github.com/AlterLab-IEU)"


class NetworkUnavailable(RuntimeError):
    pass


def _fetch(url: str, timeout: float) -> dict:
    try:
        try:
            import requests  # type: ignore

            resp = requests.get(url, timeout=timeout,
                                headers={"User-Agent": USER_AGENT})
            resp.raise_for_status()
            return resp.json()
        except ImportError:
            import urllib.request

            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
                return json.loads(r.read().decode("utf-8", errors="replace"))
    except Exception as exc:  # noqa: BLE001
        raise NetworkUnavailable(str(exc)) from exc


def check(server: str, doi: str, timeout: float) -> dict:
    server = server.lower()
    if server not in ("biorxiv", "medrxiv"):
        return {"status": "error",
                "reason": "server must be 'biorxiv' or 'medrxiv'"}

    details_url = f"{API_BASE}/details/{server}/{doi}/na/json"
    pubs_url = f"{API_BASE}/pubs/{server}/{doi}/na/json"

    out = {
        "tool": "alterlab-preprint-deposition/preprint_link_check.py",
        "version": "1.1.0",
        "server": server,
        "doi": doi,
    }

    try:
        details = _fetch(details_url, timeout)
    except NetworkUnavailable as exc:
        out.update(status="unverified",
                   manual_instructions=(
                       f"Could not reach api.biorxiv.org ({exc}). Confirm the "
                       f"DOI manually at https://doi.org/{doi}."))
        return out

    collection = details.get("collection") or []
    if not collection:
        out.update(status="not_found",
                   detail=details.get("messages"),
                   manual_instructions=(
                       "No record matched this DOI on the content API; check "
                       "the DOI and server."))
        return out

    versions = sorted({str(c.get("version")) for c in collection
                       if c.get("version") is not None},
                      key=lambda v: (not v.isdigit(), int(v) if v.isdigit() else 0, v))
    latest = collection[-1]
    published_doi = next(
        (str(c.get("published")) for c in reversed(collection)
         if c.get("published") and str(c.get("published")).upper() != "NA"),
        None,
    )
    out.update(
        status="found",
        title=latest.get("title"),
        versions=versions,
        latest_version=latest.get("version"),
        posted_date=latest.get("date"),
        category=latest.get("category"),
    )

    # Published-article link (best-effort; absence != not published). The
    # details record's `published` field is authoritative for the DOI; /pubs/
    # only adds journal name and date (and misses 10.64898 DOIs for now).
    link = {"published_doi": published_doi, "published_journal": None,
            "published_date": None} if published_doi else None
    try:
        pubs = _fetch(pubs_url, timeout)
        pub_coll = pubs.get("collection") or []
        if pub_coll:
            rec = pub_coll[0]
            link = {
                "published_doi": rec.get("published_doi") or published_doi,
                "published_journal": rec.get("published_journal"),
                "published_date": rec.get("published_date"),
            }
    except NetworkUnavailable:
        out["pubs_note"] = "pubs endpoint unreachable this run."
    out["published_link"] = link
    if link is None:
        out["published_link_note"] = (
            "No preprint->published link detected yet; this does not mean "
            "the paper is unpublished. Add the link manually on publication.")

    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server", required=True, choices=["biorxiv", "medrxiv"])
    p.add_argument("--doi", required=True,
                   help="Preprint DOI, e.g. 10.64898/... (from Dec 2025) or 10.1101/...")
    p.add_argument("--timeout", type=float, default=20.0)
    args = p.parse_args(argv)

    report = check(args.server, args.doi, args.timeout)
    json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
