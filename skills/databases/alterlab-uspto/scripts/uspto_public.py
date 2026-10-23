#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Keyless USPTO data: Patent Public Search (full text) and TSDR status pages (trademarks).

No API key, standard library only. Both sources are USPTO's own public web tools; their
JSON/HTML backends are not documented APIs, so keep volumes modest and cite the page.

patents  - Patent Public Search, https://ppubs.uspto.gov/pubwebapp/ : an anonymous
           session (POST /api/users/me/session) then POST /api/searches/searchWithBeFamily
           with a query in the search tool's syntax, e.g.
               google.as. AND G06N$.cpc. AND @pd>=20230101<=20241231
               lidar.ti. AND @ad>=20200101        11234567.pn.        "Thorne".in.
           Fields: .ti. title, .ab. abstract, .clm. claims, .as. assignee, .aanm. applicant,
           .in. inventor, .cpc. CPC (G06N$ = truncation), .pn. patent/publication number;
           @pd publication date, @ad application date. Databases: USPAT (grants),
           US-PGPUB (applications), USOCR (pre-1976 OCR). Returns number, title, dates,
           assignee/applicant, application number, CPC, cited US references; `doc` adds the
           abstract and claims text.
trademarks - TSDR status page, https://tsdr.uspto.gov/statusview/sn<serial> (or rn<reg>):
           mark, status and date, filing/registration dates, owner, goods and services with
           classes, attorney, and the full prosecution history, parsed from the HTML.
Not covered keylessly: prosecution transactions of pending applications (ODP Patent File
Wrapper, needs USPTO_ODP_API_KEY) — for granted patents use the Google Patents page
(https://patents.google.com/patent/US<number><kind>/en, via WebFetch): its "Legal events"
table lists USPTO status events (STPP/STCF) and recorded assignments (AS, reel/frame).

    python uspto_public.py search 'google.as. AND G06N$.cpc. AND @pd>=20230101<=20241231' --limit 20
    python uspto_public.py search --assignee google --cpc G06N --from 2023-01-01 --to 2024-12-31
    python uspto_public.py doc 11234567
    python uspto_public.py app 16/117,894                # application -> grant / publication
    python uspto_public.py trademark 87654321           # serial number
    python uspto_public.py trademark 5553479 --registration
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser

PPUBS = "https://ppubs.uspto.gov"
TSDR = "https://tsdr.uspto.gov/statusview/{kind}{number}"
UA = "Mozilla/5.0 (compatible; AlterLab-Academic-Skills/1.0; alterlab-uspto keyless)"
_session: dict = {}


def _call(url, body=None, headers=None, method=None, tries=3):
    hdrs = {"User-Agent": UA, "Accept": "application/json", **(headers or {})}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        hdrs["Content-Type"] = "application/json"
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read()
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            return exc.code, {}, exc.read()
        except urllib.error.URLError as exc:
            if attempt < tries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            raise SystemExit(f"Cannot reach {url.split('?')[0]}: {exc.reason}")
    return 0, {}, b""


# ------------------------------------------------------------------ patents (PPUBS)
def _ppubs_session() -> dict:
    if not _session:
        st, hd, b = _call(f"{PPUBS}/api/users/me/session", body=-1, method="POST")
        if st != 200 or "x-access-token" not in hd:
            raise SystemExit(f"Patent Public Search session failed (HTTP {st}); try again later "
                             "or use the web UI at https://ppubs.uspto.gov/pubwebapp/")
        _session.update(token=hd["x-access-token"], case=json.loads(b)["userCase"]["caseId"])
    return _session


def build_query(title=None, assignee=None, applicant=None, inventor=None, cpc=None,
                date_from=None, date_to=None, date_field="pd") -> str:
    parts = []
    for value, field in ((title, "ti"), (assignee, "as"), (applicant, "aanm"), (inventor, "in")):
        if value:
            parts.append(f'("{value}").{field}.' if " " in value else f"{value}.{field}.")
    if cpc:
        code = cpc.replace(" ", "")
        parts.append(f"{code}{'' if code.endswith('$') or '/' in code else '$'}.cpc.")
    if date_from or date_to:
        lo = (date_from or "1790-01-01").replace("-", "")
        hi = (date_to or "2100-12-31").replace("-", "")
        parts.append(f"@{date_field}>={lo}<={hi}")
    return " AND ".join(parts)


def _date(v):
    if isinstance(v, list):
        v = v[0] if v else None
    return v[:10] if isinstance(v, str) else v


def _summary(p: dict) -> dict:
    cpc = ";".join(x for x in (p.get("cpcInventiveFlattened"), p.get("cpcAdditionalFlattened")) if x)
    return {
        "number": re.sub(r"<[^>]+>", "", p.get("documentId") or p.get("guid") or ""),
        "kind": (p.get("kindCode") or [None])[0],
        "type": p.get("type"),
        "title": re.sub(r"<[^>]+>", "", p.get("inventionTitle") or ""),
        "date_published": _date(p.get("datePublished")),
        "application_number": p.get("applicationNumber"),
        "filing_date": _date(p.get("applicationFilingDate")),
        "assignee": p.get("assigneeName"),
        "applicant": p.get("applicantName"),
        "inventors": p.get("inventorsShort"),
        "cpc": cpc.split(";") if cpc else [],
        "us_references_cited": p.get("urpn") or [],
        "family_id": p.get("familyIdentifierCur"),
        "guid": p.get("guid"),
    }


def search(query: str, databases=("USPAT",), limit: int = 25, sort: str = "date_publ desc") -> dict:
    s = _ppubs_session()
    out, start = [], 0
    total = None
    while len(out) < limit:
        page = min(100, limit - len(out))
        body = {"start": start, "pageCount": page, "sort": sort, "docFamilyFiltering": "noFiltering",
                "searchType": 1, "familyIdEnglishOnly": True, "familyIdFirstPreferred": "USPAT",
                "familyIdSecondPreferred": "US-PGPUB", "familyIdThirdPreferred": "FPRS",
                "showDocPerFamilyPref": "showEnglish", "queryId": 0, "tagDocSearch": False,
                "query": {"caseId": s["case"], "hl_snippets": "2", "op": "OR", "q": query,
                          "queryName": query, "highlights": "0", "qt": "brs", "spellCheck": False,
                          "viewName": "tile", "plurals": True, "britishEquivalents": True,
                          "databaseFilters": [{"databaseName": d, "countryCodes": []} for d in databases],
                          "searchType": 1, "ignorePersist": True, "userEnteredQuery": query}}
        st, _, b = _call(f"{PPUBS}/api/searches/searchWithBeFamily", body=body,
                         headers={"X-Access-Token": s["token"]})
        if st != 200:
            raise SystemExit(f"Patent Public Search returned HTTP {st}: {b[:200]!r}")
        d = json.loads(b)
        if d.get("error"):
            raise SystemExit(f"Query rejected: {d['error']}")
        total = d.get("numFound", 0)
        batch = d.get("patents") or []
        out.extend(_summary(p) for p in batch)
        start += len(batch)
        if not batch or start >= total:
            break
        time.sleep(1)
    return {"query": query, "databases": list(databases), "num_found": total, "results": out[:limit],
            "source": "USPTO Patent Public Search (ppubs.uspto.gov), anonymous session"}


def application(number: str) -> dict:
    """Grant and/or pre-grant publication for a US application number (e.g. 16/117,894)."""
    digits = re.sub(r"\D", "", number)
    hits = search(digits, databases=("USPAT", "US-PGPUB"), limit=50)["results"]
    match = [h for h in hits if re.sub(r"\D", "", h.get("application_number") or "") == digits]
    return {"application_number": digits, "documents": match,
            "note": None if match else (
                "No published application or grant for this number in Patent Public Search: it may "
                "be unpublished (pending < 18 months, or a non-publication request) or abandoned "
                "before publication. Its file wrapper needs the ODP key (or the Patent Center web "
                "UI); the number alone does not reveal it.")}


def document(number: str) -> dict:
    """Bibliographic data plus abstract and claims for one US patent or publication number."""
    n = re.sub(r"[^0-9A-Za-z]", "", number).upper().removeprefix("US")
    n = re.sub(r"(B\d|A\d|E|S|P\d?)$", "", n)
    db = "US-PGPUB" if len(n) == 11 else "USPAT"
    hits = search(f"{n}.pn.", databases=(db,), limit=1)["results"]
    if not hits:
        raise SystemExit(f"No US document {number} in Patent Public Search ({db})")
    s = _ppubs_session()
    st, _, b = _call(f"{PPUBS}/api/patents/highlight/{hits[0]['guid']}?queryId=1&source={db}"
                     "&includeSections=true&uniqueId=", headers={"X-Access-Token": s["token"]})
    if st != 200:
        raise SystemExit(f"Document fetch returned HTTP {st}")
    d = json.loads(b)
    text = {}
    for key in ("abstractHtml", "claimsHtml", "descriptionHtml", "abstract", "claims", "description"):
        if isinstance(d.get(key), str) and d[key].strip():
            clean = re.sub(r"<[^>]+>", " ", d[key])
            text[key.replace("Html", "")] = " ".join(clean.split())
    out = _summary(d)
    out.update({k: v for k, v in text.items() if k != "description"})
    if "description" in text:
        out["description_chars"] = len(text["description"])
    out["google_patents_url"] = (f"https://patents.google.com/patent/US{n}{out.get('kind') or ''}/en")
    return out


# --------------------------------------------------------------- trademarks (TSDR)
class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lines, self._skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            t = " ".join(data.split())
            if t and t != "&nbsp;":
                self.lines.append(t)


_LABELS = {
    "Mark:": "mark_text", "US Serial Number:": "serial_number",
    "Application Filing Date:": "filing_date", "US Registration Number:": "registration_number",
    "Registration Date:": "registration_date", "Register:": "register", "Mark Type:": "mark_type",
    "TM5 Common Status Descriptor:": "tm5_status", "Status:": "status", "Status Date:": "status_date",
    "Publication Date:": "publication_date", "Owner Name:": "owner_name",
    "Legal Entity Type:": "owner_entity_type", "Attorney Name:": "attorney_name",
    "Abandoned Date:": "abandoned_date", "Cancellation Date:": "cancellation_date",
}
_SECTION_END = ("Mark Information", "Goods and Services", "Basis Information", "Current Owner",
                "Attorney/Correspondence", "Prosecution History", "Maintenance Filings", "TM Staff",
                "Assignment Abstract", "Proceedings")


def trademark(number: str, registration: bool = False) -> dict:
    url = TSDR.format(kind="rn" if registration else "sn", number=re.sub(r"\D", "", number))
    st, _, b = _call(url, headers={"Accept": "text/html"})
    if st != 200:
        raise SystemExit(f"TSDR status page returned HTTP {st} for {url} (TSDR also answers "
                         "503 for numbers it does not hold; check the number, then retry later)")
    p = _Text()
    p.feed(b.decode("utf-8", "replace"))
    lines = p.lines
    if not any(ln.startswith("US Serial Number") for ln in lines):
        raise SystemExit(f"No trademark found at {url}")
    rec: dict = {"source": url}
    for i, line in enumerate(lines[:-1]):
        key = _LABELS.get(line)
        if key and key not in rec:
            nxt = lines[i + 1]
            rec[key] = "" if nxt in _LABELS else nxt
        if line == "TM5 Common Status Descriptor:" and i + 2 < len(lines):
            rec["tm5_status_note"] = lines[i + 2]
    # goods and services: "For:" text, "International Class(es):" value, "Class Status:" value
    goods, cur = [], None
    for i, line in enumerate(lines[:-1]):
        if line == "For:":
            cur = {"description": lines[i + 1]}
            goods.append(cur)
        elif cur is not None and line == "International Class(es):":
            cur["international_class"] = lines[i + 1]
        elif cur is not None and line == "Class Status:":
            cur["class_status"] = lines[i + 1]
        elif cur is not None and line == "First Use:":
            cur["first_use"] = lines[i + 1]
        elif cur is not None and line == "Use in Commerce:":
            cur["use_in_commerce"] = lines[i + 1]
    rec["goods_and_services"] = goods
    # prosecution history: rows of date, description[, proceeding number]
    history = []
    if "Prosecution History" in lines:
        start = lines.index("Prosecution History") + 1
        date_re = re.compile(r"^[A-Z][a-z]{2}\.? \d{2}, \d{4}$")
        i = start
        while i < len(lines):
            line = lines[i]
            if any(line.startswith(s) for s in _SECTION_END if s != "Prosecution History"):
                break
            if date_re.match(line) and i + 1 < len(lines):
                entry = {"date": line, "description": lines[i + 1]}
                if i + 2 < len(lines) and re.fullmatch(r"\d{5,}", lines[i + 2]):
                    entry["proceeding_number"] = lines[i + 2]
                    i += 1
                history.append(entry)
                i += 2
                continue
            i += 1
    rec["prosecution_history"] = history
    rec["is_registered"] = bool(rec.get("registration_number")) and "LIVE" in rec.get("tm5_status", "")
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(description="Keyless USPTO: Patent Public Search + TSDR status pages.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ps = sub.add_parser("search", help="patent/publication search (Patent Public Search syntax)")
    ps.add_argument("query", nargs="?", help="raw query, e.g. 'lidar.ti. AND @pd>=20240101'")
    ps.add_argument("--title")
    ps.add_argument("--assignee")
    ps.add_argument("--applicant")
    ps.add_argument("--inventor")
    ps.add_argument("--cpc", help="CPC prefix, e.g. G06N (truncated) or G06N3/08")
    ps.add_argument("--from", dest="date_from", help="YYYY-MM-DD (publication date unless --by-filing)")
    ps.add_argument("--to", dest="date_to")
    ps.add_argument("--by-filing", action="store_true", help="date range on application date")
    ps.add_argument("--db", default="USPAT", help="USPAT, US-PGPUB, USOCR; comma-separated")
    ps.add_argument("--limit", type=int, default=25)
    pd = sub.add_parser("doc", help="one patent/publication with abstract and claims")
    pd.add_argument("number", help="e.g. 11234567, US11234567B2, 20240012345")
    pa = sub.add_parser("app", help="grant/publication for a US application number")
    pa.add_argument("number", help="e.g. 16117894 or 16/117,894")
    pt = sub.add_parser("trademark", help="TSDR status page for a serial (default) or registration")
    pt.add_argument("number")
    pt.add_argument("--registration", action="store_true")
    a = ap.parse_args()

    if a.cmd == "search":
        q = a.query or build_query(a.title, a.assignee, a.applicant, a.inventor, a.cpc,
                                   a.date_from, a.date_to, "ad" if a.by_filing else "pd")
        if not q:
            ap.error("give a query or at least one of --title/--assignee/--applicant/--inventor/--cpc/--from")
        out = search(q, tuple(x.strip() for x in a.db.split(",") if x.strip()), a.limit)
    elif a.cmd == "app":
        out = application(a.number)
    elif a.cmd == "doc":
        out = document(a.number)
    else:
        out = trademark(a.number, a.registration)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
