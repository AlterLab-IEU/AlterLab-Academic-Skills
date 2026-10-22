#!/usr/bin/env python3
"""
Keyless market and fundamentals data, local technical indicators, and an optional
Alpha Vantage client. Standard library only.

Keyless sources (no API key):
  prices        Yahoo Finance chart endpoint, query1.finance.yahoo.com/v8/finance/chart/<SYM>
                (unofficial and undocumented; personal/research use under Yahoo's terms;
                cross-check figures that go into a paper). `close` is split-adjusted,
                `adjclose` is split- and dividend-adjusted.
  fundamentals  SEC EDGAR XBRL company facts, data.sec.gov (needs a User-Agent with a contact
                email: --user-agent or EDGAR_IDENTITY / SEC_USER_AGENT; no key)
  fx/macro/oil  FRED public CSV, fred.stlouisfed.org/graph/fredgraph.csv (DEXUSEU, DCOILWTICO,
                CPIAUCSL, CBBTCUSD, DGS10, ...)
Optional key:   ALPHAVANTAGE_API_KEY for Alpha Vantage's /query API (`av` subcommand).

Usage:
  python market_data.py prices AAPL --start 2000-01-01 --csv aapl.csv
  python market_data.py rsi AAPL --period 14 --start 2024-01-01
  python market_data.py indicators SPY --start 2025-01-01          # SMA/EMA/RSI/MACD/BBANDS
  python market_data.py fundamentals MSFT --years 3 --user-agent "Jane Doe jane@uni.edu"
  python market_data.py fred DCOILWTICO --frequency m --aggregation avg --start 2015-01-01
  python market_data.py av NEWS_SENTIMENT tickers=TSLA limit=50     # needs ALPHAVANTAGE_API_KEY
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA_DEFAULT = "alterlab-market-data/1.0 (research use)"  # Yahoo answers 429 to the urllib default
# FRED's CDN stalls on some agents (this default included) and answers this form:
UA_FRED = "alterlab-market-data/1.0 (+https://fred.stlouisfed.org)"
YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/"
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv"
SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
SEC_FACTS = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
AV_URL = "https://www.alphavantage.co/query"
FRED_FREQ = {"d": "Daily", "w": "Weekly", "m": "Monthly", "q": "Quarterly", "a": "Annual"}
REVENUE_CONCEPTS = ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues",
                    "SalesRevenueNet", "RevenueFromContractWithCustomerIncludingAssessedTax")


class DataError(RuntimeError):
    pass


def _get(url: str, params: dict | None = None, ua: str = UA_DEFAULT, retries: int = 3) -> bytes:
    if params:
        url = f"{url}?{urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})}"
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept-Encoding": "identity"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last = e
            if e.code not in (429, 500, 502, 503, 504):
                raise DataError(f"HTTP {e.code} for {url}") from e
        except OSError as e:  # URLError, connection reset / remote disconnect, timeouts
            last = e
        time.sleep(2.0 * (2 ** attempt))
    raise DataError(f"request failed after {retries} tries: {url} ({last})")


def _epoch(day: str) -> int:
    return int(dt.datetime.fromisoformat(day).replace(tzinfo=dt.timezone.utc).timestamp())


# ---------------------------------------------------------------- prices (Yahoo, keyless)
def prices(symbol: str, start: str | None = None, end: str | None = None, interval: str = "1d") -> dict:
    """Daily (or 1wk/1mo) OHLCV with split/dividend events. Returns
    {"rows": [(date, open, high, low, close, adjclose, volume)], "splits": [(date, "4:1")],
     "dividends": [(date, amount)], "currency": ..., "exchange": ...}."""
    params = {"interval": interval, "events": "div,split", "includeAdjustedClose": "true",
              "period1": _epoch(start) if start else 0,
              "period2": _epoch(end) + 86400 if end else int(time.time())}
    data = json.loads(_get(YAHOO + urllib.parse.quote(symbol), params))
    chart = data.get("chart", {})
    if chart.get("error") or not chart.get("result"):
        raise DataError(f"no price data for {symbol!r}: {chart.get('error')}")
    res = chart["result"][0]
    q = res["indicators"]["quote"][0]
    adj = (res["indicators"].get("adjclose") or [{}])[0].get("adjclose") or [None] * len(res.get("timestamp", []))
    day = lambda t: dt.datetime.fromtimestamp(t, dt.timezone.utc).date().isoformat()  # noqa: E731
    rows = [(day(t), q["open"][i], q["high"][i], q["low"][i], q["close"][i], adj[i], q["volume"][i])
            for i, t in enumerate(res.get("timestamp", [])) if q["close"][i] is not None]
    ev = res.get("events", {})
    splits = sorted((day(int(k)), v["splitRatio"]) for k, v in ev.get("splits", {}).items())
    divs = sorted((day(int(k)), v["amount"]) for k, v in ev.get("dividends", {}).items())
    return {"rows": rows, "splits": splits, "dividends": divs,
            "currency": res["meta"].get("currency"), "exchange": res["meta"].get("exchangeName")}


# ---------------------------------------------------------------- indicators (local)
def sma(x: list[float], n: int) -> list[float | None]:
    return [None if i + 1 < n else sum(x[i + 1 - n:i + 1]) / n for i in range(len(x))]


def ema(x: list[float], n: int) -> list[float | None]:
    """EMA seeded with the SMA of the first n values, alpha = 2/(n+1)."""
    out: list[float | None] = [None] * len(x)
    if len(x) < n:
        return out
    a, prev = 2 / (n + 1), sum(x[:n]) / n
    out[n - 1] = prev
    for i in range(n, len(x)):
        prev = a * x[i] + (1 - a) * prev
        out[i] = prev
    return out


def rsi(x: list[float], n: int = 14) -> list[float | None]:
    """Wilder's RSI: seed with the simple mean gain/loss of the first n changes, then
    avg = (avg*(n-1) + current)/n."""
    out: list[float | None] = [None] * len(x)
    if len(x) <= n:
        return out
    ch = [x[i] - x[i - 1] for i in range(1, len(x))]
    g = sum(max(c, 0) for c in ch[:n]) / n
    lo = sum(max(-c, 0) for c in ch[:n]) / n
    out[n] = 100.0 if lo == 0 else 100 - 100 / (1 + g / lo)
    for i in range(n + 1, len(x)):
        c = ch[i - 1]
        g = (g * (n - 1) + max(c, 0)) / n
        lo = (lo * (n - 1) + max(-c, 0)) / n
        out[i] = 100.0 if lo == 0 else 100 - 100 / (1 + g / lo)
    return out


def macd(x: list[float], fast: int = 12, slow: int = 26, signal: int = 9):
    ef, es = ema(x, fast), ema(x, slow)
    line = [None if a is None or b is None else a - b for a, b in zip(ef, es)]
    first = next((i for i, v in enumerate(line) if v is not None), len(line))
    sig_part = ema([v for v in line[first:]], signal)
    sig = [None] * first + sig_part
    hist = [None if a is None or b is None else a - b for a, b in zip(line, sig)]
    return line, sig, hist


def bbands(x: list[float], n: int = 20, k: float = 2.0):
    mid = sma(x, n)
    up, dn = [], []
    for i, m in enumerate(mid):
        if m is None:
            up.append(None)
            dn.append(None)
            continue
        w = x[i + 1 - n:i + 1]
        sd = (sum((v - m) ** 2 for v in w) / n) ** 0.5  # population SD, as most charting tools use
        up.append(m + k * sd)
        dn.append(m - k * sd)
    return up, mid, dn


# ---------------------------------------------------------------- FRED CSV (keyless)
def fred(series_id: str, start=None, end=None, frequency=None, aggregation=None) -> list[tuple[str, float | None]]:
    params = {"id": series_id, "cosd": start, "coed": end,
              "fq": FRED_FREQ.get((frequency or "").lower(), frequency) if frequency else None,
              "fam": aggregation}
    text = _get(FRED_CSV, params, ua=UA_FRED).decode()
    if text.lstrip().startswith("<"):
        raise DataError(f"FRED returned no CSV for {series_id!r}")
    rows = list(csv.reader(io.StringIO(text)))[1:]
    return [(r[0], None if r[1] in ("", ".") else float(r[1])) for r in rows if len(r) > 1]


# ---------------------------------------------------------------- SEC EDGAR (keyless)
def _sec_ua(ua: str | None) -> str:
    ua = ua or os.environ.get("EDGAR_IDENTITY") or os.environ.get("SEC_USER_AGENT")
    if not ua or "@" not in ua:
        raise DataError("SEC EDGAR asks every client for a User-Agent with a contact email (no key): "
                        "pass --user-agent \"Your Name you@example.org\" or set EDGAR_IDENTITY")
    return ua


def cik_for(ticker: str, ua: str | None = None) -> tuple[int, str]:
    table = json.loads(_get(SEC_TICKERS, ua=_sec_ua(ua)))
    for row in table.values():
        if row["ticker"].upper() == ticker.upper():
            return int(row["cik_str"]), row["title"]
    raise DataError(f"ticker {ticker!r} not in SEC company_tickers.json")


def company_facts(cik: int, ua: str | None = None) -> dict:
    return json.loads(_get(SEC_FACTS.format(cik=cik), ua=_sec_ua(ua)))


def annual_values(facts: dict, concept: str, unit: str = "USD", taxonomy: str = "us-gaap") -> dict[str, tuple]:
    """{fiscal-year end: (value, accession, filed)} for ~12-month 10-K facts; for each period
    the most recently filed value wins (restatements replace earlier figures)."""
    try:
        items = facts["facts"][taxonomy][concept]["units"][unit]
    except KeyError:
        return {}
    out: dict[str, tuple] = {}
    for x in items:
        if not x.get("form", "").startswith("10-K") or "start" not in x:
            continue
        days = (dt.date.fromisoformat(x["end"]) - dt.date.fromisoformat(x["start"])).days
        if 350 <= days <= 380 and (x["end"] not in out or x["filed"] > out[x["end"]][2]):
            out[x["end"]] = (x["val"], x["accn"], x["filed"])
    return dict(sorted(out.items()))


def fundamentals(ticker: str, years: int = 3, ua: str | None = None) -> dict:
    cik, name = cik_for(ticker, ua)
    f = company_facts(cik, ua)
    rev = {}
    for c in REVENUE_CONCEPTS:
        rev = annual_values(f, c)
        if rev:
            break
    ni = annual_values(f, "NetIncomeLoss")
    eps = annual_values(f, "EarningsPerShareDiluted", "USD/shares")
    shares = f.get("facts", {}).get("dei", {}).get("EntityCommonStockSharesOutstanding", {}).get("units", {}).get("shares", [])
    last_shares = max(shares, key=lambda x: (x["end"], x["filed"])) if shares else None
    ends = sorted(set(rev) | set(ni) | set(eps))[-years:]
    return {"ticker": ticker.upper(), "cik": cik, "name": name,
            "fiscal_years": [{"fy_end": e, "revenue": rev.get(e, (None,))[0], "net_income": ni.get(e, (None,))[0],
                              "eps_diluted": eps.get(e, (None,))[0],
                              "accession": (rev.get(e) or ni.get(e) or eps.get(e) or (None, None))[1]} for e in ends],
            "shares_outstanding": last_shares and {"value": last_shares["val"], "as_of": last_shares["end"]}}


# ---------------------------------------------------------------- Alpha Vantage (optional key)
def alphavantage(function: str, **params) -> dict:
    key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if not key:
        raise SystemExit("error: the Alpha Vantage backend needs ALPHAVANTAGE_API_KEY (free key at "
                         "https://www.alphavantage.co/support/#api-key). Without it use the keyless "
                         "subcommands: prices / rsi / indicators (Yahoo chart), fundamentals (SEC EDGAR), "
                         "fred (FRED CSV).")
    data = json.loads(_get(AV_URL, {"function": function, "apikey": key, **params}))
    for k in ("Error Message", "Information", "Note"):
        if k in data:
            raise DataError(f"Alpha Vantage {k}: {data[k]}")
    return data


def _write(rows, header, path):
    out = open(path, "w", newline="") if path else sys.stdout
    w = csv.writer(out)
    w.writerow(header)
    w.writerows(rows)
    if path:
        out.close()
        print(f"wrote {len(rows)} rows to {path}", file=sys.stderr)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Keyless market/fundamentals data + local indicators; optional Alpha Vantage")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("prices", "rsi", "indicators"):
        p = sub.add_parser(name)
        p.add_argument("symbol")
        p.add_argument("--start"), p.add_argument("--end")
        p.add_argument("--interval", default="1d", choices=["1d", "1wk", "1mo"])
        p.add_argument("--csv")
        if name != "prices":
            p.add_argument("--period", type=int, default=14)
            p.add_argument("--on", choices=["adjclose", "close"], default="adjclose",
                           help="price column (default adjclose: split- and dividend-adjusted)")
    p = sub.add_parser("fundamentals")
    p.add_argument("ticker")
    p.add_argument("--years", type=int, default=3)
    p.add_argument("--user-agent")
    p = sub.add_parser("fred")
    p.add_argument("series")
    p.add_argument("--start"), p.add_argument("--end"), p.add_argument("--frequency"), p.add_argument("--aggregation")
    p.add_argument("--csv")
    p = sub.add_parser("av", help="Alpha Vantage /query (needs ALPHAVANTAGE_API_KEY)")
    p.add_argument("function")
    p.add_argument("params", nargs="*", help="key=value pairs")
    a = ap.parse_args(argv)
    try:
        if a.cmd in ("prices", "rsi", "indicators"):
            print("[market_data] prices from Yahoo's unofficial chart endpoint (no key); "
                  "cross-check figures you publish", file=sys.stderr)
            d = prices(a.symbol, a.start, a.end, a.interval)
            rows = d["rows"]
            if a.cmd == "prices":
                _write(rows, ["date", "open", "high", "low", "close_split_adj", "adjclose", "volume"], a.csv)
                print(f"splits: {d['splits']}  dividends: {len(d['dividends'])}  currency: {d['currency']}",
                      file=sys.stderr)
            else:
                col = 5 if a.on == "adjclose" else 4
                x = [r[col] for r in rows]
                r = rsi(x, a.period)
                if a.cmd == "rsi":
                    _write([(rows[i][0], round(x[i], 4), None if r[i] is None else round(r[i], 2))
                            for i in range(len(rows))], ["date", a.on, f"rsi{a.period}"], a.csv)
                else:
                    s20, e20 = sma(x, 20), ema(x, 20)
                    ml, ms, mh = macd(x)
                    up, mid, dn = bbands(x)
                    rnd = lambda v: None if v is None else round(v, 4)  # noqa: E731
                    _write([(rows[i][0], rnd(x[i]), rnd(s20[i]), rnd(e20[i]), rnd(r[i]), rnd(ml[i]), rnd(ms[i]),
                             rnd(mh[i]), rnd(up[i]), rnd(dn[i])) for i in range(len(rows))],
                           ["date", a.on, "sma20", "ema20", f"rsi{a.period}", "macd", "macd_signal", "macd_hist",
                            "bb_upper", "bb_lower"], a.csv)
        elif a.cmd == "fundamentals":
            print("[market_data] fundamentals from SEC EDGAR XBRL company facts (no key)", file=sys.stderr)
            print(json.dumps(fundamentals(a.ticker, a.years, a.user_agent), indent=2))
        elif a.cmd == "fred":
            print("[market_data] FRED public CSV (no key)", file=sys.stderr)
            _write(fred(a.series, a.start, a.end, a.frequency, a.aggregation), ["date", a.series], a.csv)
        elif a.cmd == "av":
            kv = dict(p.split("=", 1) for p in a.params)
            print(json.dumps(alphavantage(a.function, **kv), indent=2)[:20000])
    except DataError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
