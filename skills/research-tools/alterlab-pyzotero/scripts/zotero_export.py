#!/usr/bin/env python3
"""Work with an exported Zotero library offline — no API key, no running Zotero, stdlib only.

The keyless file path of alterlab-pyzotero. Zotero (File > Export Library…, or Better BibTeX's
auto-export) writes BibTeX/BibLaTeX (.bib), CSL JSON (.json) or RIS (.ris); this script reads
any of them and answers the questions people usually ask the Web API:

  python zotero_export.py stats   library.bib
  python zotero_export.py search  library.bib -q "deep learning" --tag "machine learning"
  python zotero_export.py dupes   library.bib                 # same DOI, or same title + year
  python zotero_export.py missing library.json --field doi
  python zotero_export.py export  library.json --type article-journal --year-from 2020 \
                                  --to bibtex -o recent_articles.bib
  python zotero_export.py new-item --doi 10.1038/nature14539 --to ris -o to_import.ris

"Writes" never touch the library: export / new-item produce a file the user imports with
Zotero's File > Import… (new-item --doi fills metadata from Crossref, keyless). Item types are
normalised to CSL names (article-journal, paper-conference, book, chapter, report, thesis,
manuscript, …) whichever format was read. Exit 1 when a query matches nothing.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional

USER_AGENT = "alterlab-pyzotero/1.2 (https://github.com/AlterLab-IEU)"
BIB2CSL = {"article": "article-journal", "inproceedings": "paper-conference",
           "conference": "paper-conference", "book": "book", "incollection": "chapter",
           "inbook": "chapter", "techreport": "report", "report": "report",
           "phdthesis": "thesis", "mastersthesis": "thesis", "thesis": "thesis",
           "unpublished": "manuscript", "online": "webpage", "misc": "document"}
CSL2BIB = {"article-journal": "article", "paper-conference": "inproceedings", "book": "book",
           "chapter": "incollection", "report": "techreport", "thesis": "phdthesis",
           "manuscript": "unpublished", "webpage": "online"}
RIS2CSL = {"JOUR": "article-journal", "CONF": "paper-conference", "CPAPER": "paper-conference",
           "BOOK": "book", "CHAP": "chapter", "RPRT": "report", "THES": "thesis",
           "UNPB": "manuscript", "ELEC": "webpage", "GEN": "document"}
CSL2RIS = {v: k for k, v in RIS2CSL.items() if k not in ("CPAPER",)}
_ACCENTS = {r"\"a": "ä", r"\"o": "ö", r"\"u": "ü", r"\"A": "Ä", r"\"O": "Ö", r"\"U": "Ü",
            r"'e": "é", r"'a": "á", r"'i": "í", r"'o": "ó", r"'u": "ú", r"`e": "è", r"`a": "à",
            r"^e": "ê", r"~n": "ñ", "cc": "ç", "cs": "ş", "cS": "Ş", "cC": "Ç"}
_LETTERS = {"L": "Ł", "l": "ł", "i": "ı", "o": "ø", "O": "Ø", "ss": "ß", "ae": "æ", "AE": "Æ"}


# ----------------------------------------------------------------------------- readers

def _delatex(s: str) -> str:
    s = re.sub(r"\{\\([\"'`^~]|c )\{?(\w)\}?\}", lambda m: _ACCENTS.get(m.group(1).strip() + m.group(2), m.group(2)), s)
    s = re.sub(r"\\([\"'`^~])\{?(\w)\}?", lambda m: _ACCENTS.get(m.group(1) + m.group(2), m.group(2)), s)
    s = re.sub(r"\\(ss|ae|AE|[LlioO])(?![A-Za-z])\s?", lambda m: _LETTERS[m.group(1)], s)
    s = s.replace(r"\&", "&").replace(r"\%", "%").replace(r"\_", "_").replace("--", "–")
    return " ".join(s.replace("{", "").replace("}", "").split())


def _bib_value(text: str, i: int):
    """Parse one field value starting at text[i]; return (value, next_index)."""
    if text[i] == "{":
        depth, j = 0, i
        while j < len(text):
            depth += {"{": 1, "}": -1}.get(text[j], 0)
            if depth == 0:
                return text[i + 1:j], j + 1
            j += 1
        raise ValueError("unbalanced braces")
    if text[i] == '"':
        j = i + 1
        while j < len(text) and not (text[j] == '"' and text[j - 1] != "\\"):
            j += 1
        return text[i + 1:j], j + 1
    m = re.match(r"[\w.:-]+", text[i:])
    return (m.group(0), i + m.end()) if m else ("", i)


def read_bibtex(text: str) -> List[Dict]:
    items = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text):
        etype = m.group(1).lower()
        if etype in ("comment", "string", "preamble"):
            continue
        i, fields = m.end(), {}
        while i < len(text):
            fm = re.match(r"\s*(\w[\w-]*)\s*=\s*", text[i:])
            if not fm:
                break
            i += fm.end()
            value, i = _bib_value(text, i)
            fields[fm.group(1).lower()] = value
            sep = re.match(r"\s*,?", text[i:])
            i += sep.end()
            if text[i:i + 1] == "}":
                break
        authors = [_delatex(a) for a in re.split(r"\s+and\s+", fields.get("author", "")) if a.strip()]
        kw = re.split(r"\s*[,;]\s*", _delatex(fields.get("keywords", ""))) if fields.get("keywords") else []
        year = re.search(r"\d{4}", fields.get("year", "") or fields.get("date", ""))
        items.append({
            "key": m.group(2), "type": BIB2CSL.get(etype, "document"), "title": _delatex(fields.get("title", "")),
            "authors": authors, "year": int(year.group(0)) if year else None,
            "container": _delatex(fields.get("journal") or fields.get("journaltitle") or fields.get("booktitle")
                                  or fields.get("publisher", "")),
            "volume": fields.get("volume", ""), "issue": fields.get("number", ""),
            "pages": fields.get("pages", "").replace("--", "-"), "doi": fields.get("doi", "").strip(),
            "url": fields.get("url", ""), "tags": [k for k in kw if k],
            "abstract": _delatex(fields.get("abstract", "")), "file": fields.get("file", "")})
    return items


def read_csljson(text: str) -> List[Dict]:
    data = json.loads(text)
    items = []
    for it in data if isinstance(data, list) else data.get("items", []):
        issued = (it.get("issued") or {}).get("date-parts") or [[None]]
        tags = it.get("keyword", "")
        items.append({
            "key": it.get("id") or it.get("citation-key", ""), "type": it.get("type", "document"),
            "title": it.get("title", ""),
            "authors": [f"{a.get('family', '')}, {a.get('given', '')}".strip(", ") if "family" in a
                        else a.get("literal", "") for a in it.get("author", [])],
            "year": int(issued[0][0]) if issued and issued[0] and str(issued[0][0]).isdigit() else None,
            "container": it.get("container-title", "") or it.get("publisher", ""),
            "volume": str(it.get("volume", "")), "issue": str(it.get("issue", "")),
            "pages": str(it.get("page", "")), "doi": (it.get("DOI") or "").strip(), "url": it.get("URL", ""),
            "tags": [t.strip() for t in re.split(r"[,;]", tags) if t.strip()] if isinstance(tags, str) else tags,
            "abstract": it.get("abstract", ""), "file": ""})
    return items


def read_ris(text: str) -> List[Dict]:
    items, cur = [], None
    for line in text.splitlines():
        m = re.match(r"^([A-Z][A-Z0-9])  - ?(.*)$", line)
        if not m:
            continue
        tag, val = m.group(1), m.group(2).strip()
        if tag == "TY":
            cur = {"key": "", "type": RIS2CSL.get(val, "document"), "title": "", "authors": [], "year": None,
                   "container": "", "volume": "", "issue": "", "pages": "", "doi": "", "url": "",
                   "tags": [], "abstract": "", "file": ""}
        elif cur is None:
            continue
        elif tag == "ER":
            cur["key"] = cur["key"] or f"ris{len(items) + 1}"
            items.append(cur)
            cur = None
        elif tag in ("TI", "T1"):
            cur["title"] = val
        elif tag in ("AU", "A1"):
            cur["authors"].append(val)
        elif tag in ("PY", "Y1", "DA") and not cur["year"]:
            y = re.search(r"\d{4}", val)
            cur["year"] = int(y.group(0)) if y else None
        elif tag in ("JO", "T2", "JF", "BT"):
            cur["container"] = cur["container"] or val
        elif tag == "VL":
            cur["volume"] = val
        elif tag == "IS":
            cur["issue"] = val
        elif tag == "SP":
            cur["pages"] = val + cur["pages"]
        elif tag == "EP":
            cur["pages"] += f"-{val}"
        elif tag == "DO":
            cur["doi"] = val
        elif tag == "UR":
            cur["url"] = val
        elif tag == "KW":
            cur["tags"].append(val)
        elif tag == "AB":
            cur["abstract"] = val
        elif tag == "ID":
            cur["key"] = val
    return items


def load(path: Path) -> List[Dict]:
    text = path.read_text(encoding="utf-8-sig")
    ext = path.suffix.lower()
    if ext in (".json", ".csljson"):
        return read_csljson(text)
    if ext == ".ris" or text.lstrip().startswith("TY  -"):
        return read_ris(text)
    return read_bibtex(text)


# ----------------------------------------------------------------------------- writers

_STOP = {"a", "an", "the", "of", "on", "in", "and", "for", "to", "with"}


def _bibkey(it: Dict) -> str:
    """Keep a usable key (Better BibTeX style); replace CSL item URIs with author+year+word."""
    if it["key"] and re.fullmatch(r"[A-Za-z0-9_:.\-]+", it["key"]):
        return it["key"]
    family = it["authors"][0].split(",")[0] if it["authors"] else "anon"
    word = next((w for w in re.findall(r"[A-Za-z0-9]+", it["title"]) if w.lower() not in _STOP), "")
    return re.sub(r"[^A-Za-z0-9]", "", family).lower() + str(it["year"] or "") + word.lower()


def _unique_keys(items: Iterable[Dict]) -> List[tuple]:
    seen: Counter = Counter()
    out = []
    for it in items:
        k = _bibkey(it)
        seen[k] += 1
        out.append((it, k if seen[k] == 1 else f"{k}{chr(96 + seen[k])}"))
    return out


def to_bibtex(items: Iterable[Dict]) -> str:
    out = []
    for it, key in _unique_keys(items):
        f = {"title": "{" + it["title"] + "}", "author": " and ".join(it["authors"]),
             "year": str(it["year"] or ""), "doi": it["doi"], "url": it["url"],
             "volume": it["volume"], "number": it["issue"], "pages": it["pages"].replace("-", "--"),
             "keywords": ", ".join(it["tags"])}
        f["booktitle" if it["type"] in ("paper-conference", "chapter") else
          "publisher" if it["type"] == "book" else "journal"] = it["container"]
        body = ",\n".join(f"  {k} = {{{v}}}" for k, v in f.items() if v)
        out.append(f"@{CSL2BIB.get(it['type'], 'misc')}{{{key},\n{body}\n}}\n")
    return "\n".join(out)


def to_csljson(items: Iterable[Dict]) -> str:
    out = []
    for it, key in _unique_keys(items):
        rec = {"id": key, "type": it["type"], "title": it["title"],
               "author": [{"family": a.split(",")[0].strip(), "given": a.split(",", 1)[1].strip()}
                          if "," in a else {"literal": a} for a in it["authors"]],
               "issued": {"date-parts": [[it["year"]]]} if it["year"] else None,
               "container-title": it["container"], "volume": it["volume"], "issue": it["issue"],
               "page": it["pages"], "DOI": it["doi"], "URL": it["url"], "keyword": ", ".join(it["tags"])}
        out.append({k: v for k, v in rec.items() if v})
    return json.dumps(out, indent=2, ensure_ascii=False) + "\n"


def to_ris(items: Iterable[Dict]) -> str:
    out = []
    for it in items:
        lines = [f"TY  - {CSL2RIS.get(it['type'], 'GEN')}", f"TI  - {it['title']}"]
        lines += [f"AU  - {a}" for a in it["authors"]]
        sp, _, ep = it["pages"].partition("-")
        for tag, val in (("PY", it["year"]), ("T2", it["container"]), ("VL", it["volume"]),
                         ("IS", it["issue"]), ("SP", sp), ("EP", ep), ("DO", it["doi"]),
                         ("UR", it["url"])):
            if val:
                lines.append(f"{tag}  - {val}")
        lines += [f"KW  - {t}" for t in it["tags"]] + ["ER  - ", ""]
        out.append("\n".join(lines))
    return "\n".join(out)


WRITERS = {"bibtex": to_bibtex, "csljson": to_csljson, "ris": to_ris}


# ----------------------------------------------------------------------------- queries

def _norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]", "", t.lower())


def select(items: List[Dict], q: Optional[str] = None, tags: Optional[List[str]] = None,
           itype: Optional[str] = None, year_from: Optional[int] = None,
           year_to: Optional[int] = None) -> List[Dict]:
    out = []
    for it in items:
        hay = " ".join([it["title"], " ".join(it["authors"]), it["container"], it["abstract"],
                        " ".join(it["tags"])]).lower()
        if q and not all(w in hay for w in q.lower().split()):
            continue
        if tags and not all(t.lower() in [x.lower() for x in it["tags"]] for t in tags):
            continue
        if itype and it["type"] != BIB2CSL.get(itype, RIS2CSL.get(itype, itype)):
            continue
        if year_from and not (it["year"] and it["year"] >= year_from):
            continue
        if year_to and not (it["year"] and it["year"] <= year_to):
            continue
        out.append(it)
    return out


def duplicates(items: List[Dict]) -> List[List[Dict]]:
    groups: Dict[str, List[Dict]] = defaultdict(list)
    for it in items:
        groups["doi:" + it["doi"].lower() if it["doi"] else f"title:{_norm_title(it['title'])}:{it['year']}"].append(it)
    return [g for g in groups.values() if len(g) > 1]


def crossref_item(doi: str) -> Dict:
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/:")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        m = json.loads(resp.read())["message"]
    ctype = {"journal-article": "article-journal", "proceedings-article": "paper-conference",
             "book-chapter": "chapter", "posted-content": "manuscript"}.get(m.get("type"), m.get("type", "document"))
    title = (m.get("title") or [""])[0]
    if m.get("subtitle"):
        title += ": " + m["subtitle"][0]
    return {"key": "", "type": ctype, "title": title,
            "authors": [f"{a.get('family', '')}, {a.get('given', '')}".strip(", ") for a in m.get("author", [])],
            "year": ((m.get("issued") or {}).get("date-parts") or [[None]])[0][0],
            "container": (m.get("container-title") or [""])[0], "volume": m.get("volume", ""),
            "issue": m.get("issue", ""), "pages": m.get("page", ""), "doi": m.get("DOI", ""),
            "url": m.get("URL", ""), "tags": [], "abstract": "", "file": ""}


def _line(it: Dict) -> str:
    who = it["authors"][0].split(",")[0] if it["authors"] else "?"
    more = " et al." if len(it["authors"]) > 1 else ""
    return (f"{it['key']}\t{it['type']}\t{who}{more} ({it['year'] or 'n.d.'})\t{it['title'][:90]}"
            f"\t{('doi:' + it['doi']) if it['doi'] else 'NO DOI'}\ttags: {', '.join(it['tags']) or '-'}")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Offline queries over an exported Zotero library "
                                 "(.bib / CSL JSON / .ris). No API key, no running Zotero.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def filt(p):
        p.add_argument("file", type=Path)
        p.add_argument("-q", "--query", help="words that must all appear (title/authors/venue/tags)")
        p.add_argument("--tag", action="append", help="tag (BibTeX keywords / CSL keyword); repeat = AND")
        p.add_argument("--type", help="item type, CSL or BibTeX name (article-journal, article, book, ...)")
        p.add_argument("--year-from", type=int)
        p.add_argument("--year-to", type=int)
        p.add_argument("--json", action="store_true")

    for name in ("search", "export"):
        filt(sub.add_parser(name))
    sub.choices["export"].add_argument("--to", choices=sorted(WRITERS), required=True)
    sub.choices["export"].add_argument("-o", "--output", type=Path)
    sub.add_parser("stats").add_argument("file", type=Path)
    sub.add_parser("dupes").add_argument("file", type=Path)
    mp = sub.add_parser("missing")
    mp.add_argument("file", type=Path)
    mp.add_argument("--field", default="doi", choices=["doi", "abstract", "year", "authors", "container", "pages"])
    np_ = sub.add_parser("new-item", help="write an importable file (File > Import in Zotero)")
    np_.add_argument("--doi", action="append", help="fill metadata from Crossref (keyless); repeatable")
    np_.add_argument("--type", default="article-journal")
    np_.add_argument("--title")
    np_.add_argument("--author", action="append", help='"Family, Given"; repeatable')
    np_.add_argument("--year", type=int)
    np_.add_argument("--container")
    np_.add_argument("--tag", action="append")
    np_.add_argument("--to", choices=sorted(WRITERS), default="ris")
    np_.add_argument("-o", "--output", type=Path)
    args = ap.parse_args(argv)

    if args.cmd == "new-item":
        items = []
        try:
            items += [crossref_item(d) for d in args.doi or []]
        except OSError as exc:
            print(f"error: Crossref lookup failed ({exc}); give --title/--author instead", file=sys.stderr)
            return 1
        if args.title:
            items.append({"key": "", "type": args.type, "title": args.title, "authors": args.author or [],
                          "year": args.year, "container": args.container or "", "volume": "", "issue": "",
                          "pages": "", "doi": "", "url": "", "tags": [], "abstract": "", "file": ""})
        if not items:
            ap.error("new-item needs --doi or --title")
        for it in items:
            it["tags"] = it["tags"] or list(args.tag or [])
        text = WRITERS[args.to](items)
        (args.output.write_text(text, encoding="utf-8") if args.output else sys.stdout.write(text))
        if args.output:
            print(f"wrote {len(items)} item(s) to {args.output}; import it in Zotero with "
                  "File > Import… (nothing was sent to zotero.org)", file=sys.stderr)
        return 0

    items = load(args.file)
    if args.cmd == "stats":
        print(f"{len(items)} items in {args.file.name}")
        print("by type: " + ", ".join(f"{k} {v}" for k, v in Counter(i["type"] for i in items).most_common()))
        years = [i["year"] for i in items if i["year"]]
        print(f"years: {min(years)}-{max(years)}" if years else "years: none")
        print("top tags: " + ", ".join(f"{k} ({v})" for k, v in
                                      Counter(t for i in items for t in i["tags"]).most_common(10)))
        print(f"missing DOI: {sum(not i['doi'] for i in items)}; duplicate groups: {len(duplicates(items))}")
        return 0
    if args.cmd == "dupes":
        groups = duplicates(items)
        for g in groups:
            basis = f"same DOI {g[0]['doi']}" if g[0]["doi"] else "same title + year"
            print(f"{basis}: " + " | ".join(i["key"] for i in g))
        if not groups:
            print("no duplicates (by DOI, or title + year)", file=sys.stderr)
        return 0 if groups else 1
    if args.cmd == "missing":
        hits = [i for i in items if not i[args.field]]
        for i in hits:
            print(_line(i))
        print(f"{len(hits)} of {len(items)} items have no {args.field}", file=sys.stderr)
        return 0
    hits = select(items, args.query, args.tag, args.type, args.year_from, args.year_to)
    if args.cmd == "export":
        text = WRITERS[args.to](hits)
        (args.output.write_text(text, encoding="utf-8") if args.output else sys.stdout.write(text))
        print(f"exported {len(hits)} of {len(items)} items as {args.to}"
              + (f" to {args.output}" if args.output else ""), file=sys.stderr)
        return 0 if hits else 1
    if args.json:
        print(json.dumps(hits, indent=2, ensure_ascii=False))
    else:
        for i in hits:
            print(_line(i))
    print(f"{len(hits)} of {len(items)} items match", file=sys.stderr)
    return 0 if hits else 1


if __name__ == "__main__":
    sys.exit(main())
