#!/usr/bin/env python3
"""
USPTO patent search via the Open Data Portal (ODP) Patent File Wrapper API.

Status (verified 2026-09): the PatentsView PatentSearch API
(search.patentsview.org) paused when PatentsView migrated to the ODP on
2026-03-20 and its hostname no longer resolves; USPTO has given no date for
its return, and old PatentsView keys do not work on ODP. This client therefore
searches the ODP Patent File Wrapper instead: bibliographic data for
applications filed since 2001-01-01 (granted and pending), refreshed daily.
It has no claims/abstract full text — use ODP bulk grant/pgpub XML for that.

API:  POST https://api.uspto.gov/api/v1/patent/applications/search
Auth: "X-API-KEY" header with an ODP key (data.uspto.gov -> APIs -> Getting
      Started; a USPTO.gov account is required). Environment variable:
      USPTO_ODP_API_KEY (USPTO_API_KEY is accepted as a fallback).

Query body (all parts optional):
    {"q": "applicationMetaData.inventionTitle:\"quantum computing\"",
     "filters": [{"name": "applicationMetaData.applicationTypeLabelName", "value": ["Utility"]}],
     "rangeFilters": [{"field": "applicationMetaData.grantDate",
                       "valueFrom": "2024-01-01", "valueTo": "2024-12-31"}],
     "sort": [{"field": "applicationMetaData.filingDate", "order": "desc"}],
     "fields": ["applicationNumberText", "applicationMetaData"],
     "pagination": {"offset": 0, "limit": 25}}
Response: {"count": N, "patentFileWrapperDataBag": [{"applicationNumberText",
           "applicationMetaData": {inventionTitle, patentNumber, filingDate, grantDate,
           applicationStatusDescriptionText, firstApplicantName, firstInventorName,
           cpcClassificationBag, ...}, ...}]}
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Optional

import requests

ODP_BASE = "https://api.uspto.gov/api/v1/patent/applications"


class PatentSearchClient:
    """Bibliographic patent/application search on the ODP Patent File Wrapper."""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 60):
        self.api_key = api_key or os.getenv("USPTO_ODP_API_KEY") or os.getenv("USPTO_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ODP API key required: set USPTO_ODP_API_KEY (key from data.uspto.gov, "
                "APIs -> Getting Started) or pass api_key=."
            )
        self.headers = {"X-API-KEY": self.api_key, "Accept": "application/json"}
        self.timeout = timeout

    def search(self, q: Optional[str] = None, filters: Optional[List[Dict]] = None,
               range_filters: Optional[List[Dict]] = None, sort: Optional[List[Dict]] = None,
               fields: Optional[List[str]] = None, offset: int = 0, limit: int = 25) -> Dict:
        """POST a Patent File Wrapper search; returns {"count", "patentFileWrapperDataBag"}."""
        body: Dict = {"pagination": {"offset": offset, "limit": limit}}
        if q:
            body["q"] = q
        if filters:
            body["filters"] = filters
        if range_filters:
            body["rangeFilters"] = range_filters
        if sort:
            body["sort"] = sort
        if fields:
            body["fields"] = fields
        response = requests.post(f"{ODP_BASE}/search", headers=self.headers, json=body,
                                 timeout=self.timeout)
        if response.status_code == 404:
            # ODP signals an empty result with 404 "No matching records found"
            return {"count": 0, "patentFileWrapperDataBag": []}
        response.raise_for_status()
        return response.json()

    def get_patent(self, patent_number: str) -> Optional[Dict]:
        """File-wrapper record for a granted patent number (e.g. "11234567")."""
        number = patent_number.upper().replace("US", "").replace(",", "").strip()
        result = self.search(
            filters=[{"name": "applicationMetaData.patentNumber", "value": [number]}], limit=1
        )
        bag = result.get("patentFileWrapperDataBag") or []
        return bag[0] if bag else None

    def search_by_title(self, phrase: str, **kwargs) -> Dict:
        return self.search(q=f'applicationMetaData.inventionTitle:"{phrase}"', **kwargs)

    def search_by_inventor(self, inventor_name: str, **kwargs) -> Dict:
        return self.search(q=f'applicationMetaData.firstInventorName:"{inventor_name}"', **kwargs)

    def search_by_applicant(self, applicant_name: str, **kwargs) -> Dict:
        """First-named applicant. Current owners come from /{app}/assignment instead."""
        return self.search(q=f'applicationMetaData.firstApplicantName:"{applicant_name}"', **kwargs)

    def search_by_date_range(self, start_date: str, end_date: str,
                             date_field: str = "applicationMetaData.grantDate", **kwargs) -> Dict:
        """Dates as YYYY-MM-DD; date_field may also be applicationMetaData.filingDate."""
        return self.search(
            range_filters=[{"field": date_field, "valueFrom": start_date, "valueTo": end_date}],
            **kwargs,
        )


def _summarize(result: Dict) -> Dict:
    rows = []
    for record in result.get("patentFileWrapperDataBag") or []:
        meta = record.get("applicationMetaData") or {}
        rows.append({
            "application": record.get("applicationNumberText"),
            "patent": meta.get("patentNumber"),
            "title": meta.get("inventionTitle"),
            "filed": meta.get("filingDate"),
            "granted": meta.get("grantDate"),
            "status": meta.get("applicationStatusDescriptionText"),
            "applicant": meta.get("firstApplicantName"),
        })
    return {"count": result.get("count", 0), "results": rows}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Search US patents/applications via the USPTO ODP Patent File Wrapper API")
    parser.add_argument("--q", help='Raw query, e.g. \'applicationMetaData.inventionTitle:"lidar"\'')
    parser.add_argument("--title", help="Phrase in the invention title")
    parser.add_argument("--inventor", help="First-named inventor")
    parser.add_argument("--applicant", help="First-named applicant")
    parser.add_argument("--patent", help="Look up one granted patent number")
    parser.add_argument("--granted-from", help="Grant date lower bound (YYYY-MM-DD)")
    parser.add_argument("--granted-to", help="Grant date upper bound (YYYY-MM-DD)")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--raw", action="store_true", help="Print the full API response")
    args = parser.parse_args()

    try:
        client = PatentSearchClient()
        if args.patent:
            print(json.dumps(client.get_patent(args.patent), indent=2))
            return 0
        clauses = []
        if args.q:
            clauses.append(f"({args.q})")
        if args.title:
            clauses.append(f'applicationMetaData.inventionTitle:"{args.title}"')
        if args.inventor:
            clauses.append(f'applicationMetaData.firstInventorName:"{args.inventor}"')
        if args.applicant:
            clauses.append(f'applicationMetaData.firstApplicantName:"{args.applicant}"')
        ranges = None
        if args.granted_from or args.granted_to:
            ranges = [{"field": "applicationMetaData.grantDate",
                       "valueFrom": args.granted_from or "1790-01-01",
                       "valueTo": args.granted_to or "9999-12-31"}]
        if not clauses and not ranges:
            parser.error("give --q/--title/--inventor/--applicant, a grant-date range, or --patent")
        result = client.search(q=" AND ".join(clauses) or None, range_filters=ranges,
                               limit=args.limit)
        print(json.dumps(result if args.raw else _summarize(result), indent=2))
        return 0
    except (ValueError, requests.RequestException) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
