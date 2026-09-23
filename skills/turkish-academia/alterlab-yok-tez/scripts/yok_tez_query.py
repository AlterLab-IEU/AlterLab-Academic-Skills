#!/usr/bin/env python3
"""yok_tez_query.py — build YÖK Ulusal Tez Merkezi search args and format citations.

This is an OFFLINE, deterministic helper. It does **not** call any network
endpoint — there is no official public API for tez.yok.gov.tr, and the live
search runs through the `saidsurucu/yoktez-mcp` connector (local `uvx` or hosted
https://yoktezmcp.fastmcp.app/mcp). This script's job is to turn a plain topic
description into:

  1. a normalized query spec applying the verified search-craft rules
     (stems that survive substring matching, up to three keywords joined by
     and/or, paired TR+EN queries, field targeting, and permission_status /
     thesis_status = "0" (Tümü) for originality checks), and
  2. the exact `search_yok_tez_detailed` argument dict for the 2026 connector
     surface (keyword / keyword_2 / keyword_3, operator_1 / operator_2,
     search_field, match_type and coded filters).

It also formats a Türkçe APA-7 thesis citation (and optional BibTeX) from a
record dict, mapping the YÖK Tez No to APA's Yayın No.

Stdlib only — runs in a bare `uv run` env. No third-party deps.

Usage:
  # Build search args for an originality / supervision check (TR+EN paired):
  uv run python yok_tez_query.py search \
      --topic-tr "sanal prodüksiyon veya sanal çekim" \
      --topic-en "virtual production" \
      --thesis-type Doktora --year-start 2015 --year-end 2026 --originality

  # Format a citation from a record JSON (stdin or --record):
  echo '{"author":"Yılmaz, A.","year":2021,
         "title":"Sanal prodüksiyonun sinematografiye etkileri",
         "tez_no":"654321","thesis_type":"Doktora tezi",
         "university":"İzmir Ekonomi Üniversitesi","permission":"İzinli"}' \
    | uv run python yok_tez_query.py cite --bibtex
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict

# yoktez-mcp `search_yok_tez_detailed` argument codes, as served by the hosted
# connector (YokTezMCP 3.3.1, checked live 2026-09-23). YÖK redesigned its search
# in 2026: one field per query, up to three keywords joined by and/or, plus
# dropdown filters. University/institute/department text filters and the direct
# thesis-number lookup were removed.
SEARCH_FIELD = {  # Aranacak Alan
    "all": "7",       # Tümü (default; highest recall)
    "title": "1",     # Tez Adı
    "author": "2",    # Yazar
    "advisor": "3",   # Danışman
    "subject": "4",   # Konu
    "keyword": "5",   # Anahtar Kelime
    "abstract": "6",  # Özet
}
MATCH_TYPE = {"contains": "2", "exact": "1"}   # Kelimenin içinde geçsin / Sadece yazılan şekilde
THESIS_TYPE = {  # Tez Türü
    "yüksek lisans": "1", "doktora": "2", "tıpta uzmanlık": "3", "sanatta yeterlik": "4",
    "diş hekimliği uzmanlık": "5", "tıpta yan dal uzmanlık": "6", "eczacılıkta uzmanlık": "7",
}
LANGUAGE = {"türkçe": "1", "ingilizce": "2"}   # other languages: see the tool schema
PERMISSION_ALL = "0"   # İzin Durumu: "0" Tümü (default), "1" İzinli, "2" İzinsiz
STATUS_ALL = "0"       # Durumu: "0" Tümü, "3" Onaylandı (connector default), "1" Hazırlanıyor

# Turkish consonant alternation (k/ğ, ç/c, t/d, p/b) breaks substring matching:
# "okuryazarlık" does not match "okuryazarlığı". Cut such a final consonant.
_MUTABLE_FINALS = "kçtpğcdb"


@dataclass
class QuerySpec:
    """One concrete yoktez-mcp search call."""

    label: str
    args: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)


def _norm(label: str) -> str:
    return label.replace("I", "ı").replace("İ", "i").lower().strip()


def _stem_notes(term: str) -> list:
    """Flag tokens that substring ("contains") matching will under-match.

    Heuristic only (no morphological analyser in stdlib): inflectional suffixes, and
    a final k/ç/t/p that turns into ğ/c/d/b before a vowel-initial suffix.
    """
    notes = []
    suffixes = ("liğin", "lığın", "lığı", "liği", "nin", "nın", "nün", "nun",
                "lerin", "ların", "leşmenin", "laşmanın")
    for tok in term.split():
        low = _norm(tok)
        if any(low.endswith(s) for s in suffixes) and len(low) > 7:
            notes.append(f"'{tok}' looks inflected — search a shorter stem so the default "
                         "contains-match also finds the other forms.")
        elif len(low) > 5 and low[-1] in _MUTABLE_FINALS:
            notes.append(f"'{tok}' ends in a consonant that alternates before suffixes "
                         f"(e.g. -lık/-lığı); '{tok[:-1]}' matches both forms.")
    return notes


def _split_keywords(topic: str) -> tuple[list, list]:
    """Split "a ve b veya c" into up to three keywords and the operators between them."""
    words = topic.split()
    kws, ops, cur = [], [], []
    for w in words:
        lw = _norm(w)
        if lw in ("ve", "and", "veya", "or") and cur:
            kws.append(" ".join(cur))
            ops.append("and" if lw in ("ve", "and") else "or")
            cur = []
        else:
            cur.append(w)
    if cur:
        kws.append(" ".join(cur))
    return kws[:3], ops[: max(0, min(len(kws), 3) - 1)]


def build_search(args: argparse.Namespace) -> dict:
    """Return paired TR/EN QuerySpecs (plus an advisor query) and merge instructions."""
    specs: list[QuerySpec] = []
    warnings: list[str] = []
    common: dict = {"match_type": MATCH_TYPE["contains"]}
    if args.thesis_type:
        code = THESIS_TYPE.get(_norm(args.thesis_type))
        if code:
            common["thesis_type"] = code
        else:
            warnings.append(f"Unknown thesis type '{args.thesis_type}'; left unfiltered.")
    if args.year_start:
        common["year_start"] = str(args.year_start)
    if args.year_end:
        common["year_end"] = str(args.year_end)
    if args.language:
        code = LANGUAGE.get(_norm(args.language))
        if code:
            common["language"] = code
        else:
            warnings.append(f"Language '{args.language}' has no code here; set it from the "
                            "tool schema or filter results locally.")

    # Originality checks must include İzinsiz (restricted) AND in-preparation
    # (Hazırlanıyor) theses — both are prior art. The connector's own default for
    # thesis_status is "3" (approved only), so set both filters to "0" (Tümü).
    if args.originality:
        common["permission_status"] = PERMISSION_ALL
        common["thesis_status"] = STATUS_ALL

    def make_topic_spec(label: str, topic: str | None) -> QuerySpec | None:
        if not topic:
            return None
        kws, ops = _split_keywords(topic)
        a = dict(common)
        a["search_field"] = SEARCH_FIELD["all"]
        for i, kw in enumerate(kws):
            a["keyword" if i == 0 else f"keyword_{i + 1}"] = kw
        for i, op in enumerate(ops):
            a[f"operator_{i + 1}"] = op
        notes = []
        for kw in kws:
            notes += _stem_notes(kw)
        if any(f" {w} " in f" {_norm(topic)} " for w in ("not", "içermesin")):
            notes.append("The 2026 YÖK search has no NOT operator; drop unwanted hits "
                         "locally after merging.")
        return QuerySpec(label=label, args=a, notes=notes)

    for label, topic in (("turkish", args.topic_tr), ("english", args.topic_en)):
        s = make_topic_spec(label, topic)
        if s:
            specs.append(s)

    if args.advisor:
        a = dict(common)
        a.update({"keyword": args.advisor, "search_field": SEARCH_FIELD["advisor"]})
        note = ("Advisor query: intersect with the topic queries on thesis_no, and "
                "confirm the advisor with get_yok_tez_thesis_details — names repeat.")
        specs.append(QuerySpec(label="advisor", args=a, notes=[note]))

    if args.university:
        warnings.append(
            "YÖK's 2026 search no longer filters by university text: keep only results "
            f"whose university_info matches '{args.university}', or narrow by department "
            "with list_yok_tez_anabilim_dali + search_yok_tez_by_anabilim_dali.")

    out = {
        "tool": "alterlab-yok-tez/yok_tez_query.py",
        "mode": "search",
        "connector": "saidsurucu/yoktez-mcp :: search_yok_tez_detailed",
        "queries": [asdict(s) for s in specs],
        "merge_instruction": (
            "Run each query via search_yok_tez_detailed (page through total_pages), then "
            "MERGE and DEDUPE on thesis_no. Return newest-first "
            "{thesis_no, year, university_info, advisor, title, permission}; fetch the "
            "advisor and abstracts with get_yok_tez_thesis_details where needed."
        ),
        "code_tables": {
            "search_field": SEARCH_FIELD, "match_type": MATCH_TYPE,
            "thesis_type": THESIS_TYPE, "language": LANGUAGE,
            "permission_status": {"all": "0", "izinli": "1", "izinsiz": "2"},
            "thesis_status": {"all": "0", "onaylandi": "3", "hazirlaniyor": "1"},
        },
    }
    if not args.topic_en and args.topic_tr:
        warnings.append(
            "Only a Turkish query was given. English terms hit only the English "
            "fields — add --topic-en to avoid missing English-language theses.")
    if args.originality:
        warnings.append(
            "Originality check: permission_status and thesis_status are both '0' (Tümü) so "
            "restricted and in-preparation theses surface. This is registry coverage, NOT a "
            "plagiarism / text-similarity score.")
    if warnings:
        out["warnings"] = warnings
    return out


def format_apa7(rec: dict) -> str:
    """Türkçe APA-7 thesis citation, switching on permission state."""
    author = rec.get("author", "Soyad, A.")
    year = rec.get("year", "Yıl")
    title = rec.get("title", "Tez başlığı")
    ttype = rec.get("thesis_type", "tez")
    univ = rec.get("university", "Üniversite Adı")
    tez_no = rec.get("tez_no")
    permission = str(rec.get("permission", "")).lower()

    published = permission.startswith("izinli") or permission.startswith("i̇zinli")
    if published and tez_no:
        # Tez No maps directly to APA Yayın No.
        return (
            f"{author} ({year}). {title} (Yayın No. {tez_no}) "
            f"[{ttype}, {univ}]. YÖK Ulusal Tez Merkezi."
        )
    # Unpublished / restricted form. Turkish APA lowercases the type phrase,
    # e.g. "Yüksek Lisans tezi" -> "yüksek lisans tezi". The search form and the
    # --thesis-type flag use bare labels ("Doktora", "Yüksek Lisans"), so ensure
    # the phrase ends in "tezi" — the template is "[Yayımlanmamış ... tezi]".
    low_type = ttype.lower().strip() if ttype else "tez"
    if not low_type.endswith("tez") and not low_type.endswith("tezi"):
        low_type = f"{low_type} tezi"
    return (
        f"{author} ({year}). {title} "
        f"[Yayımlanmamış {low_type}]. {univ}."
    )


def _ascii_key(s: str) -> str:
    """ASCII-fold a Turkish surname into a safe BibTeX cite key.

    BibTeX cite keys must be ASCII; e.g. 'Yılmaz' -> 'yilmaz', 'Şahin' -> 'sahin'.
    """
    tr_map = str.maketrans({
        "ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
        "ç": "c", "Ç": "c", "ö": "o", "Ö": "o", "ü": "u", "Ü": "u",
    })
    folded = s.translate(tr_map).lower()
    return "".join(ch for ch in folded if ch.isascii() and ch.isalnum())


def format_bibtex(rec: dict) -> str:
    ttype = str(rec.get("thesis_type", "")).lower()
    entry = "phdthesis" if "doktora" in ttype or "phd" in ttype else "mastersthesis"
    key = (_ascii_key(str(rec.get("author", "thesis")).split(",")[0])
           or "thesis") + str(rec.get("year", ""))
    note = "YÖK Ulusal Tez Merkezi"
    if rec.get("tez_no"):
        note += f", Tez No. {rec['tez_no']}"
    return (
        f"@{entry}{{{key},\n"
        f"  author = {{{rec.get('author', '')}}},\n"
        f"  title  = {{{rec.get('title', '')}}},\n"
        f"  school = {{{rec.get('university', '')}}},\n"
        f"  year   = {{{rec.get('year', '')}}},\n"
        f"  note   = {{{note}}}\n"
        f"}}"
    )


def cmd_cite(args: argparse.Namespace) -> int:
    if args.record:
        rec = json.loads(args.record)
    else:
        data = sys.stdin.read().strip()
        if not data:
            print("error: no record JSON on stdin or via --record", file=sys.stderr)
            return 2
        rec = json.loads(data)
    print(format_apa7(rec))
    if args.bibtex:
        print()
        print(format_bibtex(rec))
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    print(json.dumps(build_search(args), ensure_ascii=False, indent=2))
    return 0


def main(argv: list | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("search", help="build search_yok_tez_detailed args")
    ps.add_argument("--topic-tr", help="Turkish topic query (up to 3 terms joined by ve/veya)")
    ps.add_argument("--topic-en", help="English topic query")
    ps.add_argument("--advisor", help="advisor (danışman) name")
    ps.add_argument("--university", help="university name (filtered locally; YÖK dropped the filter)")
    ps.add_argument("--thesis-type", help="e.g. Doktora, Yüksek Lisans")
    ps.add_argument("--year-start", type=int)
    ps.add_argument("--year-end", type=int)
    ps.add_argument("--language", help="Türkçe or İngilizce")
    ps.add_argument("--originality", action="store_true",
                    help="include İzinsiz and in-preparation theses (both filters = Tümü)")
    ps.set_defaults(func=cmd_search)

    pc = sub.add_parser("cite", help="format Türkçe APA-7 / BibTeX from a record")
    pc.add_argument("--record", help="record JSON inline (else read stdin)")
    pc.add_argument("--bibtex", action="store_true", help="also emit BibTeX")
    pc.set_defaults(func=cmd_cite)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
