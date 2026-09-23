#!/usr/bin/env python3
"""Query the Jisc Open Policy Finder API for a journal's preprint/self-archiving policy.

Open Policy Finder (Jisc; the successor to Sherpa Romeo) aggregates publisher
open-access policies journal by journal. This helper retrieves a publication
record by ISSN (or title) and summarises whether the *preprint / submitted*
version may be archived, plus any conditions, embargo, and permitted locations.
It NEVER asserts a policy from model memory: with no key or no network it
returns a manual-check instruction instead of a verdict.

Endpoint: https://api.openpolicyfinder.jisc.ac.uk/retrieve (object retrieval
API; same query parameters and JSON format as the retired Sherpa Romeo v2 API at
v2.sherpa.ac.uk, which was switched off at the end of July 2026). The API key is
sent in the ``x-api-key`` request header. Keys are free for non-commercial use
(request one from help@jisc.ac.uk). We send the ISSN/title to Jisc's server —
nothing else leaves the machine.

Auto-selects an HTTP backend: uses `requests` if installed, else stdlib urllib.

    uv run python scripts/journal_policy.py --issn 1234-5678 --api-key KEY
    OPEN_POLICY_FINDER_API_KEY=KEY uv run python scripts/journal_policy.py --title "Nature Methods"
    uv run python scripts/journal_policy.py --issn 1234-5678   # no key -> manual instruction
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse

API_BASE = "https://api.openpolicyfinder.jisc.ac.uk/retrieve"
WEB_UI = "https://openpolicyfinder.jisc.ac.uk/"
KEY_ENV = "OPEN_POLICY_FINDER_API_KEY"
USER_AGENT = "alterlab-preprint-deposition/1.1 (+https://github.com/AlterLab-IEU)"
TOOL = "alterlab-preprint-deposition/journal_policy.py"
VERSION = "1.1.0"


class NetworkUnavailable(RuntimeError):
    pass


def _build_filter(issn: str | None, title: str | None) -> str:
    compact = {"separators": (",", ":")}
    if issn:
        return json.dumps([["issn", "equals", issn]], **compact)
    return json.dumps([["title", "contains-word", title]], **compact)


def build_url(issn: str | None, title: str | None) -> str:
    """Return the fully URL-encoded retrieve URL (the key goes in a header)."""
    params = {
        "item-type": "publication",
        "format": "Json",
        "limit": "1",
        "filter": _build_filter(issn, title),
    }
    return f"{API_BASE}?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"


def _fetch(url: str, api_key: str, timeout: float) -> dict:
    """GET the URL and parse JSON. Raises NetworkUnavailable on failure."""
    headers = {"User-Agent": USER_AGENT, "x-api-key": api_key,
               "Accept": "application/json"}
    try:
        try:
            import requests  # type: ignore

            resp = requests.get(url, timeout=timeout, headers=headers)
            resp.raise_for_status()
            return resp.json()
        except ImportError:
            import urllib.request

            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
                return json.loads(r.read().decode("utf-8", errors="replace"))
    except Exception as exc:  # noqa: BLE001 - any failure => manual fallback
        raise NetworkUnavailable(str(exc)) from exc


def _manual_instruction(issn, title, reason) -> dict:
    target = f"ISSN {issn}" if issn else f"title '{title}'"
    return {
        "tool": TOOL,
        "version": VERSION,
        "status": "unverified",
        "reason": reason,
        "manual_instructions": (
            f"Could not verify the preprint policy for {target}. Look it up "
            f"manually at {WEB_UI} or read the publisher's own preprint/sharing "
            "policy page. Do NOT assume a policy."),
    }


def _phrases(obj: dict, key: str) -> list[str]:
    """Human-readable labels from a '<key>_phrases' array, else the raw values."""
    phrases = obj.get(f"{key}_phrases") or []
    labels = [p.get("phrase") for p in phrases if isinstance(p, dict) and p.get("phrase")]
    if labels:
        return labels
    raw = obj.get(key) or []
    return [str(v) for v in raw] if isinstance(raw, list) else [str(raw)]


def summarise(record: dict) -> dict:
    """Pull the prearchiving (preprint) permission out of a publication record.

    Field names follow the Open Policy Finder publication object
    (publisher_policy[].permitted_oa[]); absent fields are reported as
    'not stated' rather than guessed.
    """
    policies = record.get("publisher_policy") or record.get("policies") or []
    preprint = {"permitted": "not stated", "conditions": [], "embargoes": [],
                "locations": []}
    for pol in policies if isinstance(policies, list) else []:
        perms = pol.get("permitted_oa") or pol.get("permitted") or []
        for perm in perms if isinstance(perms, list) else []:
            versions = perm.get("article_version") or perm.get("version") or []
            if not any("submitted" in str(v).lower() for v in versions):
                continue
            preprint["permitted"] = "permitted (submitted/preprint version)"
            for cond in perm.get("conditions") or []:
                if str(cond) not in preprint["conditions"]:
                    preprint["conditions"].append(str(cond))
            emb = perm.get("embargo") or {}
            if isinstance(emb, dict) and emb.get("amount"):
                label = f"{emb.get('amount')} {emb.get('units', '')}".strip()
                if label not in preprint["embargoes"]:
                    preprint["embargoes"].append(label)
            loc = perm.get("location") or {}
            if isinstance(loc, dict):
                for label in _phrases(loc, "location"):
                    if label not in preprint["locations"]:
                        preprint["locations"].append(label)
    return preprint


def lookup(issn, title, api_key, timeout) -> dict:
    if not api_key:
        return _manual_instruction(
            issn, title, f"no API key supplied (--api-key or ${KEY_ENV})")
    try:
        data = _fetch(build_url(issn, title), api_key, timeout)
    except NetworkUnavailable as exc:
        return _manual_instruction(issn, title, f"network/API error: {exc}")

    items = data.get("items") or []
    if not items:
        return {
            "tool": TOOL,
            "version": VERSION,
            "status": "no_match",
            "query": {"issn": issn, "title": title},
            "manual_instructions": "No Open Policy Finder publication matched; "
                                   "verify the ISSN/title or read the publisher page.",
        }
    rec = items[0]
    titles = rec.get("title")
    return {
        "tool": TOOL,
        "version": VERSION,
        "status": "ok",
        "matched_title": titles[0].get("title")
        if isinstance(titles, list) and titles and isinstance(titles[0], dict)
        else titles,
        "issns": rec.get("issns"),
        "preprint_policy": summarise(rec),
        "source": (rec.get("system_metadata") or {}).get("uri") or WEB_UI,
        "note": "Confirm conditions (embargo, version, required notice, DOI "
                "link) before posting; see references/journal_policy.md.",
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--issn", help="Journal ISSN, e.g. 1234-5678")
    g.add_argument("--title", help="Journal title (word match)")
    p.add_argument("--api-key", default=os.environ.get(KEY_ENV),
                   help=f"Open Policy Finder API key (default: ${KEY_ENV}). "
                        "Omit for a manual fallback instruction (no policy is asserted).")
    p.add_argument("--timeout", type=float, default=20.0)
    args = p.parse_args(argv)

    report = lookup(args.issn, args.title, args.api_key, args.timeout)
    json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
