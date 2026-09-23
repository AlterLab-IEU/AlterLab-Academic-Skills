#!/usr/bin/env python3
"""Recommend a preprint server + license shortlist from a few manuscript flags.

Pure-logic, offline, zero-dependency helper that encodes the routing rules in
references/server_selection.md and the license sets in references/licensing.md.
It does NOT assert journal policy (use journal_policy.py for that) and makes no
claim about manuscript quality — it only routes a deposit decision.

Emits a JSON report to stdout: a primary server recommendation, alternatives,
a license shortlist with the trade-off note, and the next steps to take.

    uv run python scripts/server_recommender.py --field cs
    uv run python scripts/server_recommender.py --field biology --needs-doi
    uv run python scripts/server_recommender.py --field clinical --target-journal-known
"""
from __future__ import annotations

import argparse
import json
import sys

# Field keyword -> canonical arXiv-style domain bucket.
FIELD_TO_SERVER = {
    "physics": "arxiv", "math": "arxiv", "cs": "arxiv",
    "computer-science": "arxiv", "stat": "arxiv", "statistics": "arxiv",
    "eess": "arxiv", "ee": "arxiv", "econ": "arxiv", "economics": "arxiv",
    "q-bio": "arxiv", "q-fin": "arxiv",
    "biology": "biorxiv", "life-sciences": "biorxiv", "bio": "biorxiv",
    "chemistry": "chemrxiv", "chem": "chemrxiv",
    "clinical": "medrxiv", "health": "medrxiv", "medicine": "medrxiv",
    "social-science": "ssrn", "law": "ssrn", "business": "ssrn",
    "humanities": "ssrn",
    "psychology": "osf", "earth-science": "osf", "cross-disciplinary": "osf",
}

# Real license option sets per server (verified against each server's docs).
SERVER_LICENSES = {
    "arxiv": [
        "arXiv non-exclusive license 1.0 (lowest journal friction)",
        "CC BY 4.0", "CC BY-SA 4.0", "CC BY-NC-SA 4.0", "CC BY-NC-ND 4.0",
        "CC0 1.0",
    ],
    "biorxiv": ["CC BY", "CC BY-NC", "CC BY-ND", "CC BY-NC-ND", "CC0",
                "No reuse / All rights reserved"],
    "medrxiv": ["CC BY", "CC BY-NC", "CC BY-ND", "CC BY-NC-ND", "CC0",
                "No reuse / All rights reserved"],
    "chemrxiv": ["CC BY 4.0", "CC BY-NC 4.0", "CC BY-NC-ND 4.0"],
    "ssrn": ["Author-selected terms under SSRN posting agreement"],
    "osf": ["CC BY 4.0", "CC0 1.0",
            "(community servers such as PsyArXiv/SocArXiv set their own list, "
            "e.g. 'No license' or NC/ND variants - check the provider)"],
}

# Checked 2026-09-23 (arXiv DOI help page; openRxiv DOI notice; Crossref prefixes).
SERVER_DOI = {
    "arxiv": "arXiv ID is canonical; every paper also gets a DataCite DOI "
             "10.48550/arXiv.<id> automatically",
    "biorxiv": "Crossref DOI on posting (openRxiv): prefix 10.64898 since "
               "Dec 2025, 10.1101 before",
    "medrxiv": "Crossref DOI on posting (openRxiv): prefix 10.64898 since "
               "Dec 2025, 10.1101 before",
    "chemrxiv": "Crossref DOI per version (10.26434/chemrxiv.<id>/v<n>)",
    "ssrn": "Crossref DOI 10.2139/ssrn.<id>",
    "osf": "DOI via OSF",
}


def recommend(field: str, needs_doi: bool, target_journal_known: bool,
              funder_requires_cc_by: bool) -> dict:
    key = field.strip().lower()
    server = FIELD_TO_SERVER.get(key)
    notes = []
    alternatives = []

    if server is None:
        server = "osf"
        notes.append(
            f"Field '{field}' not in the known map; defaulting to OSF Preprints "
            "(multi-disciplinary). Confirm a field-specific community server.")

    # Clinical content is medRxiv-only regardless of other flags.
    if key in ("clinical", "health", "medicine"):
        notes.append("Clinical/health content must go to medRxiv; do not post "
                     "identifiable patient data.")

    # Economics: arXiv econ and SSRN both have a strong readership.
    if key in ("econ", "economics"):
        alternatives = ["ssrn"]
        notes.append("Economics fits arXiv econ or SSRN; SSRN is the dominant "
                     "social-science preprint culture, arXiv suits "
                     "econometrics/theory read by quantitative fields.")

    # Computational-biology overlap.
    if key in ("q-bio", "bio", "biology"):
        alternatives = ["arxiv (q-bio)"] if server == "biorxiv" else ["biorxiv"]
        notes.append("Computational biology fits both arXiv q-bio and bioRxiv; "
                     "choose by target audience and DOI need.")

    if needs_doi:
        notes.append("Every server listed here now issues a DOI on posting "
                     "(arXiv via DataCite 10.48550), so DOI need no longer "
                     "decides between them.")

    if server == "arxiv":
        notes.append("arXiv gatekeeping (2025-26): new submitters need an "
                     "institutional email plus a claimed paper in the same "
                     "endorsement domain, or a personal endorsement; CS "
                     "review/position papers need proof of prior peer review; "
                     "non-English papers need a full English version.")
    if server in ("biorxiv", "medrxiv"):
        notes.append("bioRxiv/medRxiv do not post manuscripts a journal has "
                     "already accepted; post before or at submission.")

    licenses = list(SERVER_LICENSES.get(server, []))
    if funder_requires_cc_by:
        notes.append("Funder requires CC BY (e.g. Plan S): pick CC BY 4.0; "
                     "NC/ND variants generally do not comply.")
    elif target_journal_known and server == "arxiv":
        notes.append("Target journal known: the arXiv non-exclusive license is "
                     "the lowest-friction choice if the journal dislikes a "
                     "permissive CC preprint. Verify with journal_policy.py.")

    next_steps = [
        "Run journal_policy.py (Sherpa Romeo) to confirm the journal allows a "
        "preprint BEFORE posting." if target_journal_known else
        "If a target journal is known later, check its preprint policy with "
        "journal_policy.py before posting.",
        "Assemble metadata per references/submission_metadata.md.",
        "Choose the license deliberately (see references/licensing.md); CC/CC0 "
        "are irrevocable on posted versions.",
    ]

    return {
        "tool": "alterlab-preprint-deposition/server_recommender.py",
        "version": "1.1.0",
        "input": {
            "field": field, "needs_doi": needs_doi,
            "target_journal_known": target_journal_known,
            "funder_requires_cc_by": funder_requires_cc_by,
        },
        "recommended_server": server,
        "alternatives": alternatives,
        "doi_behaviour": SERVER_DOI.get(server, "unknown"),
        "license_shortlist": licenses,
        "notes": notes,
        "next_steps": next_steps,
        "disclaimer": "Routing only — does not assert journal policy or judge "
                      "manuscript quality.",
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--field", required=True,
                   help="e.g. cs, math, biology, chemistry, clinical, economics, psychology")
    p.add_argument("--needs-doi", action="store_true",
                   help="A citable DOI is required immediately on posting.")
    p.add_argument("--target-journal-known", action="store_true",
                   help="A target journal is already chosen (affects license).")
    p.add_argument("--funder-requires-cc-by", action="store_true",
                   help="A funder mandate (e.g. Plan S) requires CC BY.")
    args = p.parse_args(argv)

    report = recommend(args.field, args.needs_doi,
                       args.target_journal_known, args.funder_requires_cc_by)
    json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
