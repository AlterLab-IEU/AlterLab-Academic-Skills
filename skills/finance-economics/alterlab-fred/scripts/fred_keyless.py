#!/usr/bin/env python3
"""
Keyless FRED access: series data, transformations, frequency aggregation, ALFRED vintages,
series search and basic metadata, with no API key and only the Python standard library.

Routes (all public, no key):
  observations  https://fred.stlouisfed.org/graph/fredgraph.csv?id=GDPC1&transformation=pc1
  vintages      https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=GDP&vintage_date=2020-01-30
  search        https://fred.stlouisfed.org/searchresults/?st=consumer+price+index&t=monthly
  metadata      https://fred.stlouisfed.org/series/CPIAUCSL  (title, units, frequency)

The optional FRED_API_KEY (scripts/fred_query.py) adds the JSON API: filtered search,
full metadata, categories, releases, tags, vintage-date lists and GeoFRED maps/shapes.

Usage:
  python fred_keyless.py obs GDPC1 --transformation pc1 --start 2023-01-01
  python fred_keyless.py obs DGS10 --frequency m --aggregation avg --start 2024-01-01 --end 2024-12-31
  python fred_keyless.py obs UNRATE DGS10 --frequency m --start 2024-01-01 --csv out.csv
  python fred_keyless.py obs GDP --vintage-date 2020-01-30 --start 2019-01-01
  python fred_keyless.py search "consumer price index" --tag monthly
  python fred_keyless.py info CPIAUCSL
  python fred_keyless.py states UR --date 2025-12-01      # per-state series {ST}UR
"""

from __future__ import annotations

import argparse
import csv
import html
import io
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv"
ALFRED_CSV = "https://alfred.stlouisfed.org/graph/alfredgraph.csv"
FRED_SEARCH = "https://fred.stlouisfed.org/searchresults/"
FRED_SERIES = "https://fred.stlouisfed.org/series/"
USER_AGENT = "alterlab-fred-keyless/1.0 (+https://fred.stlouisfed.org)"

# FRED API frequency codes -> the names fredgraph.csv takes in `fq`
FREQUENCIES = {"d": "Daily", "w": "Weekly", "bw": "Biweekly", "m": "Monthly", "q": "Quarterly",
               "sa": "Semiannual", "a": "Annual"}
AGGREGATIONS = {"avg", "sum", "eop"}
TRANSFORMATIONS = {"lin", "chg", "ch1", "pch", "pc1", "pca", "cch", "cca", "log"}
# 50 states + DC, as used in FRED's per-state series IDs (e.g. CAUR, TXUR, DCUR)
STATES = ("AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE "
          "NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY").split()


class FREDKeylessError(RuntimeError):
    pass


def _get(url: str, params: dict | None = None, retries: int = 3) -> str:
    if params:
        url = f"{url}?{urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})}"
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            last = e
            if e.code not in (429, 500, 502, 503, 504):
                raise FREDKeylessError(f"HTTP {e.code} for {url}") from e
        except urllib.error.URLError as e:
            last = e
        time.sleep(1.5 * (2 ** attempt))
    raise FREDKeylessError(f"request failed after {retries} tries: {url} ({last})")


def observations(series_id: str, start: str | None = None, end: str | None = None,
                 frequency: str | None = None, aggregation: str | None = None,
                 transformation: str | None = None, vintage_date: str | None = None
                 ) -> list[tuple[str, float | None]]:
    """(date, value) pairs for one series; missing values are None.

    frequency: FRED code (d, w, bw, m, q, sa, a) or name ("Monthly"); aggregation: avg, sum,
    eop (used with a lower frequency); transformation: lin, chg, ch1, pch, pc1, pca, cch, cca,
    log; vintage_date (YYYY-MM-DD): the series as published on that date (ALFRED).
    """
    params = {"id": series_id, "cosd": start, "coed": end}
    if frequency:
        params["fq"] = FREQUENCIES.get(frequency.lower(), frequency)
    if aggregation:
        if aggregation not in AGGREGATIONS:
            raise ValueError(f"aggregation must be one of {sorted(AGGREGATIONS)}")
        params["fam"] = aggregation
    if transformation:
        if transformation not in TRANSFORMATIONS:
            raise ValueError(f"transformation must be one of {sorted(TRANSFORMATIONS)}")
        params["transformation"] = transformation
    if vintage_date:
        params["vintage_date"] = vintage_date
    text = _get(ALFRED_CSV if vintage_date else FRED_CSV, params)
    if text.lstrip().startswith("<"):
        raise FREDKeylessError(f"no CSV for {series_id!r} (unknown series ID or vintage?)")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or len(rows[0]) < 2:
        raise FREDKeylessError(f"unexpected response for {series_id!r}: {text[:120]!r}")
    out = []
    for r in rows[1:]:
        if len(r) < 2:
            continue
        v = r[1].strip()
        out.append((r[0], None if v in ("", ".") else float(v)))
    return out


def observations_many(series_ids: list[str], **kwargs) -> tuple[list[str], dict[str, dict[str, float | None]]]:
    """Merge several series on date (one request per series). Returns (dates, {date: {id: v}})."""
    table: dict[str, dict[str, float | None]] = {}
    for sid in series_ids:
        for d, v in observations(sid, **kwargs):
            table.setdefault(d, {})[sid] = v
    return sorted(table), table


def search(text: str, tag: str | None = None, limit: int = 25) -> list[tuple[str, str]]:
    """(series_id, title) pairs from FRED's site search; tag e.g. 'monthly', 'usa', 'nsa'."""
    page = _get(FRED_SEARCH, {"st": text, "t": tag})
    seen, out = set(), []
    for sid, title in re.findall(r'href="/series/([A-Z0-9_.-]+)"\s+aria-label="([^"]+)"', page):
        if sid not in seen:
            seen.add(sid)
            out.append((sid, html.unescape(title)))
        if len(out) >= limit:
            break
    return out


def series_info(series_id: str) -> dict[str, str]:
    """Title, units and frequency from the public series page."""
    page = _get(FRED_SERIES + urllib.parse.quote(series_id))
    flat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", page))
    info = {"id": series_id}
    m = re.search(r"<title>\s*(.*?)\s*\|\s*FRED", page, re.S)
    if m:
        info["title"] = html.unescape(re.sub(r"\s*\([A-Z0-9_.-]+\)\s*$", "", m.group(1).strip()))
    m = re.search(r"Units:\s*(.*?)\s*Frequency:", flat)
    if m:
        info["units"] = html.unescape(m.group(1).replace(" ,", ",").strip(" ,"))
    m = re.search(r'series-meta-value-frequency">\s*([^<]+?)\s*<', page)
    if m:
        info["frequency"] = html.unescape(m.group(1).strip())
    return info


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Keyless FRED: CSV data, ALFRED vintages, search, metadata")
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("obs", help="observations for one or more series")
    o.add_argument("series", nargs="+")
    o.add_argument("--start"), o.add_argument("--end")
    o.add_argument("--frequency", help="d, w, bw, m, q, sa, a")
    o.add_argument("--aggregation", choices=sorted(AGGREGATIONS))
    o.add_argument("--transformation", choices=sorted(TRANSFORMATIONS))
    o.add_argument("--vintage-date", help="YYYY-MM-DD: data as published that day (ALFRED)")
    o.add_argument("--csv", help="write the merged table to this CSV file")
    s = sub.add_parser("search", help="search FRED series by text")
    s.add_argument("text")
    s.add_argument("--tag", help="FRED tag filter, e.g. monthly")
    s.add_argument("--limit", type=int, default=25)
    i = sub.add_parser("info", help="title, units and frequency of a series")
    i.add_argument("series")
    st = sub.add_parser("states", help="one value per state from per-state series {ST}<suffix>")
    st.add_argument("suffix", help="series suffix, e.g. UR for state unemployment rates")
    st.add_argument("--date", required=True, help="observation date, e.g. 2025-12-01")
    a = ap.parse_args(argv)

    print("[fred_keyless] keyless FRED/ALFRED public routes; no API key used", file=sys.stderr)
    try:
        if a.cmd == "obs":
            dates, table = observations_many(a.series, start=a.start, end=a.end, frequency=a.frequency,
                                             aggregation=a.aggregation, transformation=a.transformation,
                                             vintage_date=a.vintage_date)
            out = open(a.csv, "w", newline="") if a.csv else sys.stdout
            w = csv.writer(out)
            w.writerow(["date", *a.series])
            for d in dates:
                w.writerow([d, *("" if table[d].get(sid) is None else table[d][sid] for sid in a.series)])
            if a.csv:
                out.close()
                print(f"wrote {len(dates)} rows to {a.csv}", file=sys.stderr)
        elif a.cmd == "search":
            for sid, title in search(a.text, a.tag, a.limit):
                print(f"{sid}\t{title}")
        elif a.cmd == "info":
            for k, v in series_info(a.series).items():
                print(f"{k}: {v}")
        elif a.cmd == "states":
            for code in STATES:
                rows = observations(f"{code}{a.suffix}", start=a.date, end=a.date)
                print(f"{code}\t{rows[0][1] if rows else ''}")
    except (FREDKeylessError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
