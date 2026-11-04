#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Keyless BRENDA access: the public enzyme pages and BRENDA's SPARQL endpoint.

No login, no API key, standard library only.

1. Enzyme pages - https://www.brenda-enzymes.org/enzyme.php?ecno=<EC>
   One page per EC number holds every BRENDA table for it (KM VALUE, TURNOVER NUMBER,
   kcat/KM VALUE, Ki VALUE, IC50 VALUE, INHIBITOR, ACTIVATING COMPOUND, pH/TEMPERATURE
   OPTIMUM/RANGE/STABILITY, ORGANISM, SUBSTRATE, NATURAL SUBSTRATE, COFACTOR, ...),
   with organism, UniProt accession, commentary (pH, temperature, mutant) and the
   BRENDA literature ID for every row. Pages are cached (default ./brenda_web_cache,
   7 days) and fetched at most once every 2 s (robots.txt Crawl-delay: 2).
2. SPARQL - https://sparql.dsmz.de/api/brenda (DSMZ, BRENDA's operator): reactions,
   substrates/products, inhibitors, cofactors and organisms as RDF, for questions
   across EC numbers ("which enzymes act on 2-phenylethanol?"). It holds no numeric
   kinetics; take those from the enzyme pages.

BRENDA data are CC BY 4.0: cite BRENDA (and the literature IDs) in derived work.

    python brenda_web.py list 1.1.1.1
    python brenda_web.py table 1.1.1.1 km --substrate ethanol --csv
    python brenda_web.py table 6.3.1.2 temperature_optimum --organism "Thermus thermophilus"
    python brenda_web.py enzymes-for 2-phenylethanol            # EC numbers (SPARQL)
    python brenda_web.py reactions 2-phenylethanol --ec 1.1.1.1  # equations (SPARQL)
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

PAGE_URL = "https://www.brenda-enzymes.org/enzyme.php?ecno={ec}"
LIT_URL = "https://www.brenda-enzymes.org/literature.php?e={ec}&r={ref}"
SPARQL_URL = "https://sparql.dsmz.de/api/brenda"
UA = "AlterLab-Academic-Skills/1.0 (alterlab-brenda; keyless BRENDA web/SPARQL)"
CRAWL_DELAY = 2.0
CACHE_TTL = 7 * 24 * 3600
_last_fetch = 0.0

# Short names -> start of BRENDA's table title (case-insensitive prefix match).
ALIASES = {
    "km": "KM VALUE", "kcat": "TURNOVER NUMBER", "turnover": "TURNOVER NUMBER",
    "kcat_km": "kcat/KM VALUE", "ki": "Ki VALUE", "ic50": "IC50 VALUE",
    "inhibitor": "INHIBITOR", "inhibitors": "INHIBITOR", "activator": "ACTIVATING COMPOUND",
    "activators": "ACTIVATING COMPOUND", "specific_activity": "SPECIFIC ACTIVITY",
    "ph_optimum": "pH OPTIMUM", "ph_range": "pH RANGE", "ph_stability": "pH STABILITY",
    "temperature_optimum": "TEMPERATURE OPTIMUM", "temperature_range": "TEMPERATURE RANGE",
    "temperature_stability": "TEMPERATURE STABILITY", "organism": "ORGANISM",
    "substrate": "SUBSTRATE", "natural_substrate": "NATURAL SUBSTRATE", "reaction": "REACTION",
    "cofactor": "COFACTOR", "metals": "METALS and IONS", "synonym": "SYNONYM",
    "systematic_name": "SYSTEMATIC NAME", "molecular_weight": "MOLECULAR WEIGHT",
    "localization": "LOCALIZATION", "source_tissue": "SOURCE TISSUE", "pdb": "PDB",
}
_ROW_ID = re.compile(r"^tab(\d+)r(\d+)sr(\d+)$")
_CELL_ID = re.compile(r"^tab(\d+)r\d+sr\d+c(\d+)$")
_HEAD_ID = re.compile(r"^tab(\d+)_head$")


class _TableParser(HTMLParser):
    """Collect BRENDA's div-based tables: tabN_head headers and tabNrXsrY rows."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.headers: dict[str, list[str]] = {}
        self.rows: dict[str, list[list[str]]] = {}
        self._stack: list[tuple] = []  # (kind, tab) per open div
        self._text: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag != "div":
            return
        a = dict(attrs)
        did, cls = a.get("id") or "", a.get("class") or ""
        kind, tab = None, None
        if m := _HEAD_ID.match(did):
            kind, tab = "head", m.group(1)
            self.headers.setdefault(tab, [])
        elif m := _ROW_ID.match(did):
            kind, tab = "row", m.group(1)
            self.rows.setdefault(tab, []).append([])
        elif m := _CELL_ID.match(did):
            kind, tab = "cell", m.group(1)
            self._text = []
        elif cls == "header" and self._stack and self._stack[-1][0] == "head":
            kind, tab = "hcell", self._stack[-1][1]
            self._text = []
        self._stack.append((kind, tab))

    def handle_endtag(self, tag):
        if tag != "div" or not self._stack:
            return
        kind, tab = self._stack.pop()
        if kind in ("cell", "hcell") and self._text is not None:
            value = " ".join("".join(self._text).split())
            if kind == "cell":
                self.rows[tab][-1].append(value)
            else:
                self.headers[tab].append(value)
            self._text = None

    def handle_data(self, data):
        if self._text is not None:
            self._text.append(data)


def _get(url: str, data: bytes | None = None, headers: dict | None = None, tries: int = 3) -> bytes:
    global _last_fetch
    hdrs = {"User-Agent": UA, **(headers or {})}
    for attempt in range(tries):
        wait = CRAWL_DELAY - (time.monotonic() - _last_fetch)
        if wait > 0:
            time.sleep(wait)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=hdrs),
                                        timeout=180) as r:
                return r.read()
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            code = getattr(exc, "code", None)
            if attempt == tries - 1 or (code is not None and code < 500 and code != 429):
                raise SystemExit(f"BRENDA request failed ({code or exc}): {url.split('?')[0]}")
            time.sleep(2 ** (attempt + 1))
        finally:
            _last_fetch = time.monotonic()
    raise SystemExit("unreachable")


def _check_ec(ec: str) -> str:
    ec = ec.strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+\.(\d+|[A-Z]\d+|n\d+)", ec):
        raise SystemExit(f"'{ec}' is not a full EC number (e.g. 1.1.1.1); BRENDA pages need all 4 levels.")
    return ec


def fetch_page(ec: str, cache_dir: str | None = "brenda_web_cache", refresh: bool = False) -> str:
    """Return the enzyme page HTML for an EC number, from cache when fresh."""
    ec = _check_ec(ec)
    path = Path(cache_dir) / f"enzyme_{ec}.html" if cache_dir else None
    if path and path.exists() and not refresh and time.time() - path.stat().st_mtime < CACHE_TTL:
        return path.read_text(encoding="utf-8", errors="replace")
    text = _get(PAGE_URL.format(ec=ec)).decode("utf-8", "replace")
    if "<title>" in text and "not found" in text.split("</title>")[0].lower():
        raise SystemExit(f"BRENDA has no page for EC {ec}")
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return text


def parse_tables(page: str) -> dict[str, list[dict]]:
    """Parse every table on an enzyme page into {title: [row dicts]}."""
    p = _TableParser()
    p.feed(page)
    tables: dict[str, list[dict]] = {}
    for tab, header in p.headers.items():
        if not header:
            continue
        title = header[0]
        cols = [("VALUE" if i == 0 and len(header) > 1 and "VALUE" in h else h) for i, h in enumerate(header)]
        cols = [re.sub(r"\s*\(Commentary\)$", "", c) for c in cols]
        cols = ["REVERSIBILITY" if c.startswith("Reversibility") else c for c in cols]
        out = []
        for cells in p.rows.get(tab, []):
            row = {}
            for col, cell in zip(cols, cells):
                if col.upper() in ("IMAGE", "REACTION DIAGRAM"):
                    continue
                row[col] = "" if cell == "-" else html.unescape(cell)
            if any(row.values()):
                out.append(row)
        tables[title] = out
    return tables


def find_table(tables: dict, name: str) -> tuple[str, list[dict]]:
    want = ALIASES.get(name.lower(), name).lower()
    for title, rows in tables.items():
        if title.lower().startswith(want):
            return title, rows
    raise SystemExit(f"No '{name}' table for this EC. Tables here: {', '.join(tables)}")


def get_table(ec: str, name: str, substrate: str | None = None, organism: str | None = None,
              cache_dir: str | None = "brenda_web_cache") -> tuple[str, list[dict]]:
    """Rows of one BRENDA table, optionally filtered (exact substrate, organism substring)."""
    title, rows = find_table(parse_tables(fetch_page(ec, cache_dir)), name)
    if substrate:
        key = next((k for k in ("SUBSTRATE", "INHIBITOR", "ACTIVATING COMPOUND", "COFACTOR")
                    if rows and k in rows[0]), None)
        if key:
            s = substrate.lower()
            # SUBSTRATE cells hold a whole side ("ethanol + NAD+"): match any part exactly
            rows = [r for r in rows if s == r.get(key, "").lower()
                    or s in [x.strip() for x in r.get(key, "").lower().split(" + ")]]
    if organism:
        o = organism.lower()
        rows = [r for r in rows if o in r.get("ORGANISM", "").lower()]
    for r in rows:
        r["EC"] = ec
        r["TABLE"] = title
        if r.get("LITERATURE"):
            r["LITERATURE_URL"] = LIT_URL.format(ec=ec, ref=re.split(r"[,\s]+", r["LITERATURE"])[0])
    return title, rows


def sparql(query: str) -> list[dict]:
    body = urllib.parse.urlencode({"query": query}).encode()
    raw = _get(SPARQL_URL, data=body, headers={"Accept": "application/sparql-results+json",
                                               "Content-Type": "application/x-www-form-urlencoded"})
    d = json.loads(raw)
    return [{k: v.get("value") for k, v in b.items()} for b in d["results"]["bindings"]]


_PREFIX = ("PREFIX s: <https://purl.dsmz.de/schema/> "
           "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> ")


def _lit(text: str) -> str:
    return json.dumps(text.lower())  # a safe, quoted SPARQL string literal


def enzymes_for(compound: str, role: str = "Substrate", limit: int = 100) -> list[dict]:
    """EC numbers linked to `compound` (exact name, any case) as Substrate/Product of a
    reaction, or as an Inhibitor/Activator of the enzyme class."""
    if role in ("Inhibitor", "Activator"):
        link, count = f"?r s:refersToCompound ?c ; a s:{role} ; s:affectsClass ?ec . ", "?r"
    else:
        link = f"?r s:refersToCompound ?c ; a s:{role} ; s:partOf ?rxn . ?rxn s:catalyzedByClass ?ec . "
        count = "?rxn"
    q = (_PREFIX + f"SELECT ?ec (SAMPLE(?n) AS ?name) (COUNT(DISTINCT {count}) AS ?records) WHERE {{ "
         f"?c rdfs:label ?l . FILTER(LCASE(STR(?l)) = {_lit(compound)}) "
         f"{link}?ec rdfs:label ?n }} "
         f"GROUP BY ?ec ORDER BY DESC(?records) LIMIT {int(limit)}")
    rows = sparql(q)
    for r in rows:
        r["ec"] = r["ec"].rsplit("/", 1)[-1]
    return rows


def reactions_for(compound: str, ec: str | None = None, limit: int = 50) -> list[dict]:
    """Reaction equations (substrates = products) that involve `compound` as a substrate."""
    ec_filter = f"FILTER(?ec = <https://purl.dsmz.de/brenda/ec/{_check_ec(ec)}>) " if ec else ""
    q = (_PREFIX + "SELECT ?rxn ?ec (GROUP_CONCAT(DISTINCT ?sl; separator=\" + \") AS ?substrates) "
         "(GROUP_CONCAT(DISTINCT ?pl; separator=\" + \") AS ?products) WHERE { "
         f"?c rdfs:label ?l . FILTER(LCASE(STR(?l)) = {_lit(compound)}) "
         "?r s:refersToCompound ?c ; a s:Substrate ; s:partOf ?rxn . "
         f"?rxn s:catalyzedByClass ?ec . {ec_filter}"
         "?sr a s:Substrate ; s:partOf ?rxn ; s:refersToCompound/rdfs:label ?sl . "
         "OPTIONAL { ?pr a s:Product ; s:partOf ?rxn ; s:refersToCompound/rdfs:label ?pl } } "
         f"GROUP BY ?rxn ?ec LIMIT {int(limit)}")
    rows = sparql(q)
    for r in rows:
        r["ec"] = r["ec"].rsplit("/", 1)[-1]
        r["equation"] = f"{r.get('substrates', '')} = {r.get('products', '')}"
    return rows


def _emit(rows: list[dict], as_csv: bool) -> None:
    if as_csv:
        cols = list(dict.fromkeys(k for r in rows for k in r))
        w = csv.DictWriter(sys.stdout, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    else:
        print(json.dumps(rows, indent=2, ensure_ascii=False))


def main() -> int:
    ap = argparse.ArgumentParser(description="Keyless BRENDA: public enzyme pages + DSMZ SPARQL.")
    ap.add_argument("--cache-dir", default="brenda_web_cache", help="'' disables the page cache")
    sub = ap.add_subparsers(dest="cmd", required=True)
    pl = sub.add_parser("list", help="tables on an EC page with row counts")
    pl.add_argument("ec")
    pt = sub.add_parser("table", help="rows of one table, e.g. km, kcat, ki, inhibitor, ph_optimum")
    pt.add_argument("ec")
    pt.add_argument("name", help=f"alias ({', '.join(sorted(ALIASES))}) or a title prefix")
    pt.add_argument("--substrate", help="exact substrate/inhibitor/compound name (any case)")
    pt.add_argument("--organism", help="organism substring, e.g. 'Saccharomyces cerevisiae'")
    pt.add_argument("--csv", action="store_true")
    pe = sub.add_parser("enzymes-for", help="EC numbers acting on a compound (SPARQL)")
    pe.add_argument("compound")
    pe.add_argument("--role", choices=["Substrate", "Product", "Inhibitor", "Activator"],
                    default="Substrate")
    pe.add_argument("--limit", type=int, default=100)
    pr = sub.add_parser("reactions", help="reaction equations with a compound as substrate (SPARQL)")
    pr.add_argument("compound")
    pr.add_argument("--ec")
    pr.add_argument("--limit", type=int, default=50)
    pq = sub.add_parser("sparql", help="run a raw SPARQL query against the BRENDA endpoint")
    pq.add_argument("query")
    a = ap.parse_args()
    cache = a.cache_dir or None

    if a.cmd == "list":
        tables = parse_tables(fetch_page(a.ec, cache))
        print(json.dumps({t: len(r) for t, r in tables.items()}, indent=2))
    elif a.cmd == "table":
        title, rows = get_table(a.ec, a.name, a.substrate, a.organism, cache)
        print(f"{title}: {len(rows)} row(s) for EC {a.ec} "
              f"(BRENDA, CC BY 4.0; source {PAGE_URL.format(ec=a.ec)})", file=sys.stderr)
        _emit(rows, a.csv)
    elif a.cmd == "enzymes-for":
        _emit(enzymes_for(a.compound, a.role, a.limit), False)
    elif a.cmd == "reactions":
        _emit(reactions_for(a.compound, a.ec, a.limit), False)
    else:
        _emit(sparql(a.query), False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
