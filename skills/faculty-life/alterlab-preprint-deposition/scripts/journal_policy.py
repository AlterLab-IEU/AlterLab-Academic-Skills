#!/usr/bin/env python3
"""Look up a journal's preprint/self-archiving policy in Jisc Open Policy Finder.

Open Policy Finder (Jisc; the successor to Sherpa Romeo) aggregates publisher
open-access policies journal by journal. This helper finds the journal by ISSN or
title and summarises whether the *submitted* (preprint) version may be archived,
what the *accepted* version may do, and the conditions, embargo and permitted
locations. It NEVER asserts a policy from model memory: when nothing can be read it
returns a manual-check instruction instead of a verdict.

Two backends:

* ``web`` (keyless, the default when no key is set) reads the same public record
  page a person sees at https://openpolicyfinder.jisc.ac.uk/publication/<id>: the
  site's own journal search finds the record id, and the policy pathways are read
  from the data embedded in that page. These page formats are not a documented API
  and can change; when parsing fails the script says so and falls back to a manual
  instruction (read the record page or the publisher's own policy page).
* ``api`` (optional key) uses the documented object-retrieval API at
  https://api.openpolicyfinder.jisc.ac.uk/retrieve with the key in an ``x-api-key``
  header (same parameters/JSON as the Sherpa Romeo v2 API, switched off July 2026).
  Keys are free for non-commercial use (request one from help@jisc.ac.uk).

``--backend auto`` uses ``api`` when a key is set, otherwise ``web`` and says so on
stderr. ``--backend api`` without a key exits 2 instead of answering from the web
backend. Only the ISSN/title is sent to Jisc's servers.

Auto-selects an HTTP backend: uses `requests` if installed, else stdlib urllib.

    uv run python scripts/journal_policy.py --issn 1476-4687              # keyless
    uv run python scripts/journal_policy.py --title "Nature Methods" --backend web
    OPEN_POLICY_FINDER_API_KEY=KEY uv run python scripts/journal_policy.py --issn 1548-7091
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse

API_BASE = "https://api.openpolicyfinder.jisc.ac.uk/retrieve"
WEB_UI = "https://openpolicyfinder.jisc.ac.uk/"
WEB_SEARCH = "https://openpolicyfinder.jisc.ac.uk/api/compliance-journal"
WEB_RECORD = "https://openpolicyfinder.jisc.ac.uk/publication/{id}"
KEY_ENV = "OPEN_POLICY_FINDER_API_KEY"
USER_AGENT = "alterlab-preprint-deposition/1.2 (+https://github.com/AlterLab-IEU)"
TOOL = "alterlab-preprint-deposition/journal_policy.py"
VERSION = "1.2.0"
ISSN_RE = re.compile(r"^\d{4}-?\d{3}[\dXx]$")


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


def _get(url: str, headers: dict, timeout: float) -> str:
    """GET the URL and return the body text. Raises NetworkUnavailable on failure."""
    headers = {"User-Agent": USER_AGENT, **headers}
    try:
        try:
            import requests  # type: ignore

            resp = requests.get(url, timeout=timeout, headers=headers)
            resp.raise_for_status()
            return resp.text
        except ImportError:
            import urllib.request

            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
                return r.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001 - any failure => manual fallback
        raise NetworkUnavailable(str(exc)) from exc


def _fetch(url: str, api_key: str, timeout: float) -> dict:
    """GET an API URL with the key header and parse JSON."""
    text = _get(url, {"x-api-key": api_key, "Accept": "application/json"}, timeout)
    try:
        return json.loads(text)
    except ValueError as exc:
        raise NetworkUnavailable(f"non-JSON response: {exc}") from exc


def _manual_instruction(issn, title, reason, record_url=None) -> dict:
    target = f"ISSN {issn}" if issn else f"title '{title}'"
    where = record_url or WEB_UI
    return {
        "tool": TOOL,
        "version": VERSION,
        "status": "unverified",
        "reason": reason,
        "manual_instructions": (
            f"Could not verify the preprint policy for {target}. Read it at {where} "
            "or WebFetch the publisher's own preprint/sharing policy page and quote it. "
            "Do NOT assume a policy."),
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
    """Pull the prearchiving (preprint) permission out of an API publication record.

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


def lookup_api(issn, title, api_key, timeout) -> dict:
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
            "backend": "api",
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
        "backend": "api",
        "matched_title": titles[0].get("title")
        if isinstance(titles, list) and titles and isinstance(titles[0], dict)
        else titles,
        "issns": rec.get("issns"),
        "preprint_policy": summarise(rec),
        "source": (rec.get("system_metadata") or {}).get("uri") or WEB_UI,
        "note": "Confirm conditions (embargo, version, required notice, DOI "
                "link) before posting; see references/journal_policy.md.",
    }


# --------------------------------------------------------------------------- web backend

def _norm_issn(value: str) -> str:
    return value.replace("-", "").upper()


def _pick(items: list, issn: str | None, title: str | None) -> dict | None:
    """Choose the search hit that is the requested journal, or None."""
    for item in items:
        issns = [i.get("issn", "") for i in item.get("issns") or [] if isinstance(i, dict)]
        titles = [t.get("title", "") for t in item.get("title") or [] if isinstance(t, dict)]
        if issn and _norm_issn(issn) in {_norm_issn(i) for i in issns}:
            return item
        if title and title.strip().lower() in {t.strip().lower() for t in titles}:
            return item
    return None


def _policy_block(text: str) -> dict | None:
    """Return the embedded {"submitted": [...], "accepted": [...], ...} object, if any."""
    for body in (text, text.replace('\\"', '"')):
        start = body.find('"submitted":[')
        while start != -1:
            dec = json.JSONDecoder()
            j = start
            for _ in range(400):  # walk back over candidate '{' to the enclosing object
                j = body.rfind("{", 0, j)
                if j == -1:
                    break
                try:
                    obj, _end = dec.raw_decode(body, j)
                except ValueError:
                    continue
                if isinstance(obj, dict) and isinstance(obj.get("submitted"), list):
                    return obj
            start = body.find('"submitted":[', start + 1)
    return None


def _options(pathways: list) -> list[dict]:
    """Flatten the page's pathway objects into readable option summaries."""
    out = []
    for opt in pathways or []:
        if not isinstance(opt, dict):
            continue
        fields = {}
        for d in opt.get("detail") or []:
            if not isinstance(d, dict):
                continue
            vals = [v for v in d.get("data") or [] if v and not str(v).startswith("$")]
            if vals:
                fields[str(d.get("label", "")).lower().replace(" ", "_")] = vals
        out.append({"option": opt.get("monicker"),
                    "embargo": fields.get("embargo", ["not stated"]),
                    "locations": fields.get("locations", []),
                    "conditions": fields.get("conditions", []),
                    "licence": fields.get("licence", []),
                    "copyright_owner": fields.get("copyright_owner", []),
                    "prerequisites": fields.get("prerequisites", [])})
    return out


def lookup_web(issn, title, timeout) -> dict:
    query = issn or title
    url = f"{WEB_SEARCH}?{urllib.parse.urlencode({'per_page': 10, 'current_page': 1, 'search': query})}"
    try:
        hits = json.loads(_get(url, {"Accept": "application/json"}, timeout))
    except NetworkUnavailable as exc:
        if "404" not in str(exc):  # the site's search answers 404 when nothing matches
            return _manual_instruction(issn, title, f"web search failed: {exc}")
        hits = {"items": []}
    except ValueError as exc:
        return _manual_instruction(issn, title, f"web search returned non-JSON: {exc}")
    item = _pick(hits.get("items") or [], issn, title)
    if item is None:
        return {"tool": TOOL, "version": VERSION, "status": "no_match", "backend": "web",
                "query": {"issn": issn, "title": title},
                "candidates": [[t.get("title") for t in h.get("title") or []]
                               for h in (hits.get("items") or [])[:5]],
                "manual_instructions": "No Open Policy Finder journal matched exactly; check the "
                                       "ISSN/title, or read the publisher's policy page."}
    record_url = WEB_RECORD.format(id=item.get("id"))
    block = None
    for headers in ({"RSC": "1"}, {}):  # the page's data payload, then the HTML page
        try:
            block = _policy_block(_get(record_url, headers, timeout))
        except NetworkUnavailable as exc:
            return _manual_instruction(issn, title, f"record page failed: {exc}", record_url)
        if block:
            break
    if not block:
        return _manual_instruction(
            issn, title, "the record page was fetched but its policy data could not be read "
            "(the page format may have changed)", record_url)
    submitted = _options(block.get("submitted"))
    preprint_locations = sorted({loc for o in submitted for loc in o["locations"]})
    return {
        "tool": TOOL,
        "version": VERSION,
        "status": "ok",
        "backend": "web",
        "matched_title": (item.get("title") or [{}])[0].get("title"),
        "issns": [i.get("issn") for i in item.get("issns") or []],
        "openpolicyfinder_id": item.get("id"),
        "preprint_policy": {
            "permitted": ("permitted (submitted/preprint version)" if submitted
                          else "not stated (no submitted-version pathway on the record)"),
            "preprint_repository_listed": any("preprint" in loc.lower() or "any" in loc.lower()
                                              for loc in preprint_locations),
            "locations": preprint_locations,
            "options": submitted,
        },
        "accepted_version_policy": _options(block.get("accepted")),
        "source": record_url,
        "note": "Read live from the public Open Policy Finder record page (its embedded data is "
                "not a documented API). Confirm conditions (embargo, version, required notice, "
                "DOI link) before posting; see references/journal_policy.md.",
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--issn", help="Journal ISSN, e.g. 1476-4687")
    g.add_argument("--title", help="Journal title (exact title for the web backend)")
    p.add_argument("--backend", choices=("auto", "web", "api"), default="auto",
                   help="auto (default): api when a key is set, else the keyless web backend")
    p.add_argument("--api-key", default=os.environ.get(KEY_ENV),
                   help=f"Open Policy Finder API key for --backend api (default: ${KEY_ENV}).")
    p.add_argument("--timeout", type=float, default=20.0)
    args = p.parse_args(argv)
    if args.issn and not ISSN_RE.match(args.issn.strip()):
        p.error(f"not an ISSN: {args.issn!r} (expected NNNN-NNNC)")

    backend = args.backend
    if backend == "api" and not args.api_key:
        print(f"error: --backend api needs {KEY_ENV} (or --api-key); not falling back to the "
              "web backend. Keyless alternatives: --backend web (public record pages) or the "
              "publisher's own policy page via WebFetch.", file=sys.stderr)
        return 2
    if backend == "auto":
        backend = "api" if args.api_key else "web"
        if backend == "web":
            print(f"note: no {KEY_ENV} set - using the keyless web backend (public Open Policy "
                  "Finder record page).", file=sys.stderr)

    if backend == "api":
        report = lookup_api(args.issn, args.title, args.api_key, args.timeout)
    else:
        report = lookup_web(args.issn, args.title, args.timeout)
    json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
