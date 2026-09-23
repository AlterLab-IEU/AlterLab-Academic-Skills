#!/usr/bin/env python3
"""
USPTO examination history via the Open Data Portal (ODP) Patent File Wrapper API.

PEDS (ped.uspto.gov) is retired — its host no longer resolves (verified
2026-09) — and the `uspto-opendata-python` PEDS client no longer works. The
file keeps its old name so existing references still resolve; `PEDSHelper` is
an alias of `FileWrapperClient`.

Endpoints (GET, "X-API-KEY" header with an ODP key; env USPTO_ODP_API_KEY,
falling back to USPTO_API_KEY):
    https://api.uspto.gov/api/v1/patent/applications/{applicationNumberText}
        .../meta-data  .../transactions  .../continuity  .../assignment
        .../documents  .../adjustment  .../attorney  .../foreign-priority
        .../associated-documents
Coverage: applications filed on or after 2001-01-01, refreshed daily.
Each response is {"count": n, "patentFileWrapperDataBag": [ {...} ]}; transactions
are eventDataBag[] items of {eventCode, eventDescriptionText, eventDate}.
"""

import argparse
import json
import os
import sys
from datetime import date
from typing import Any, Dict, List, Optional

import requests

ODP_BASE = "https://api.uspto.gov/api/v1/patent/applications"

# Transaction (event) codes as they appear in eventDataBag[].eventCode
NON_FINAL_REJECTION = "CTNF"
FINAL_REJECTION = "CTFR"
NOTICE_OF_ALLOWANCE = "NOA"
RESPONSE_FILED = "WRIT"
ABANDONED = "ABND"
OFFICE_ACTION_CODES = {NON_FINAL_REJECTION, FINAL_REJECTION, "AOPF", NOTICE_OF_ALLOWANCE}


class FileWrapperClient:
    """Application data, prosecution events, continuity, and assignments from ODP."""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 60):
        self.api_key = api_key or os.getenv("USPTO_ODP_API_KEY") or os.getenv("USPTO_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ODP API key required: set USPTO_ODP_API_KEY (key from data.uspto.gov, "
                "APIs -> Getting Started) or pass api_key=."
            )
        self.headers = {"X-API-KEY": self.api_key, "Accept": "application/json"}
        self.timeout = timeout

    @staticmethod
    def _normalize(application_number: str) -> str:
        return application_number.replace("/", "").replace(",", "").replace(" ", "").strip()

    def _get(self, application_number: str, section: str = "") -> Optional[Dict]:
        url = f"{ODP_BASE}/{self._normalize(application_number)}"
        if section:
            url = f"{url}/{section}"
        response = requests.get(url, headers=self.headers, timeout=self.timeout)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        bag = response.json().get("patentFileWrapperDataBag") or []
        return bag[0] if bag else None

    def get_application(self, application_number: str) -> Optional[Dict]:
        """Full file-wrapper record (metadata, events, continuity, assignments...)."""
        return self._get(application_number)

    def get_patent(self, patent_number: str) -> Optional[Dict]:
        """Record for a granted patent number, found through the search endpoint."""
        number = patent_number.upper().replace("US", "").replace(",", "").strip()
        body = {"filters": [{"name": "applicationMetaData.patentNumber", "value": [number]}],
                "pagination": {"offset": 0, "limit": 1}}
        response = requests.post(f"{ODP_BASE}/search", headers=self.headers, json=body,
                                 timeout=self.timeout)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        bag = response.json().get("patentFileWrapperDataBag") or []
        return bag[0] if bag else None

    def get_transaction_history(self, application_number: str) -> List[Dict]:
        record = self._get(application_number, "transactions") or {}
        return record.get("eventDataBag") or []

    def get_office_actions(self, application_number: str) -> List[Dict]:
        return [event for event in self.get_transaction_history(application_number)
                if event.get("eventCode") in OFFICE_ACTION_CODES]

    def get_continuity(self, application_number: str) -> Dict[str, List[Dict]]:
        record = self._get(application_number, "continuity") or {}
        return {"parents": record.get("parentContinuityBag") or [],
                "children": record.get("childContinuityBag") or []}

    def get_assignments(self, application_number: str) -> List[Dict]:
        record = self._get(application_number, "assignment") or {}
        return record.get("assignmentBag") or []

    def get_status_summary(self, application_number: str) -> Dict[str, Any]:
        record = self._get(application_number, "meta-data") or {}
        meta = record.get("applicationMetaData") or {}
        filing = meta.get("filingDate")
        pendency = None
        if filing:
            try:
                pendency = (date.today() - date.fromisoformat(filing[:10])).days
            except ValueError:
                pendency = None
        return {
            "application": record.get("applicationNumberText"),
            "title": meta.get("inventionTitle"),
            "status": meta.get("applicationStatusDescriptionText"),
            "status_date": meta.get("applicationStatusDate"),
            "filing_date": filing,
            "patent_number": meta.get("patentNumber"),
            "grant_date": meta.get("grantDate"),
            "is_patented": bool(meta.get("patentNumber")),
            "first_applicant": meta.get("firstApplicantName"),
            "first_inventor": meta.get("firstInventorName"),
            "examiner": meta.get("examinerNameText"),
            "art_unit": meta.get("groupArtUnitNumber"),
            "days_since_filing": pendency,
        }

    def analyze_prosecution(self, application_number: str) -> Dict[str, Any]:
        events = self.get_transaction_history(application_number)
        codes = [event.get("eventCode") for event in events]
        return {
            "events": len(events),
            "non_final_rejections": codes.count(NON_FINAL_REJECTION),
            "final_rejections": codes.count(FINAL_REJECTION),
            "responses_filed": codes.count(RESPONSE_FILED),
            "allowed": NOTICE_OF_ALLOWANCE in codes,
            "abandoned": ABANDONED in codes,
            "status": self.get_status_summary(application_number).get("status"),
        }


PEDSHelper = FileWrapperClient  # backwards-compatible name


def main() -> int:
    parser = argparse.ArgumentParser(
        description="USPTO examination data from the ODP Patent File Wrapper API (PEDS successor)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--application", "-a", help="Full record for an application number")
    group.add_argument("--patent", "-p", help="Full record for a granted patent number")
    group.add_argument("--status", "-s", help="Status summary for an application")
    group.add_argument("--analyze", help="Prosecution statistics for an application")
    group.add_argument("--transactions", "-t", help="Transaction (event) history")
    group.add_argument("--office-actions", "-o", help="Office-action events only")
    group.add_argument("--continuity", help="Parent/child continuity data")
    group.add_argument("--assignments", help="Recorded assignments (ownership)")
    args = parser.parse_args()

    try:
        client = FileWrapperClient()
        if args.application:
            result = client.get_application(args.application)
        elif args.patent:
            result = client.get_patent(args.patent)
        elif args.status:
            result = client.get_status_summary(args.status)
        elif args.analyze:
            result = client.analyze_prosecution(args.analyze)
        elif args.transactions:
            result = client.get_transaction_history(args.transactions)
        elif args.office_actions:
            result = client.get_office_actions(args.office_actions)
        elif args.continuity:
            result = client.get_continuity(args.continuity)
        else:
            result = client.get_assignments(args.assignments)
    except (ValueError, requests.RequestException) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not result:
        print("No data found", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
