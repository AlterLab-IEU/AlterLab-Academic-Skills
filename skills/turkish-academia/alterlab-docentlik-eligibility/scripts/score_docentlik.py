#!/usr/bin/env python3
"""score_docentlik.py — PARTIAL pre-screen of a publication list against the ÜAK doçentlik criteria.

Covers all 12 ÜAK temel alanlar with the per-field criteria tables (TABLO 1-6, 8-13)
that ÜAK (Üniversitelerarası Kurul) published for the 2026 Mart application term, the
latest term whose per-field criteria were posted when the tables were transcribed on
2026-09-23 (the 2026 Ekim section then held only the Bilim Alanları ve Anahtar
Kelimeler file). Select the field with --alan (default: saglik, for v2.1 compatibility).

IMPORTANT — this is a PARTIAL PRE-SCREEN, not an eligibility scorer.
  It checks only the minimums that can be computed from a publication list: the
  100-point total, the 90 post-doctorate points, and each field's item-1
  (Uluslararası Makale) and item-2 (Ulusal Makale) article minimums. Every other
  mandatory minimum (thesis-derived publication, books where required, citation,
  scientific meeting, teaching, field-specific artistic/competition requirements)
  is emitted as a verify-by-hand checklist. By design the tool NEVER emits an
  "ELIGIBLE" verdict: the best status is PRESCREEN_PASS_VERIFY_REMAINING.

Design constraints:
- PURE STDLIB. No network, no third-party deps — fully reproducible offline.
- DATA-DRIVEN. Each temel alan is one entry in FIELDS (points, author-share rule,
  başlıca-yazar definition, modelled checks, caps, manual checks). The scoring code
  is generic. Verbatim rule quotes: ../references/field_tables.md.
- NO FABRICATION. Only tables transcribed from the ÜAK PDFs are bundled. An unknown
  field is refused with a pointer to the ÜAK page; an unknown index tier is flagged
  as unscored, never guessed. Where ÜAK's wording admits two readings, a modelled
  check FAILS only if it fails under every reading, and a pass that relies on the
  lenient reading is reported in summary.interpretation_flags.

Usage:
  uv run python score_docentlik.py INPUT [--alan FIELD] [--bilim-alani NAME] [--out FILE]
  uv run python score_docentlik.py - --alan sosyal < publications.json
  uv run python score_docentlik.py --list-alanlar
  uv run python score_docentlik.py --self-test

INPUT is a JSON object (see ../references/scoring_rules.md for every field):
  {"alan": "sosyal", "bilim_alani": "İletişim Çalışmaları",
   "publications": [{"title": "...", "index": "TRDizin", "authors": 1,
                     "is_lead": true, "post_doc": true}],
   "other_items": [{"item": "4a", "points": 20, "post_doc_points": 20}]}

Exit codes: 0 = ran (see summary.verdict) or self-test passed; 1 = self-test failed;
2 = bad input/usage or a field/term this tool has no verified table for.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone

VERSION = "2.2.0"
TABLE_LAST_VERIFIED = "2026-09-23"
TERM = "2026 Mart"
UAK_PAGE = "https://www.uak.gov.tr/page/docentlik-basvuru-sartlari-kLPHX"
PDF_BASE = "https://www.uak.gov.tr/documents/documents/"

VERDICT_FAIL = "FAIL_MODELLED_CHECK"
VERDICT_PASS = "PRESCREEN_PASS_VERIFY_REMAINING"

# --------------------------------------------------------------------------- #
# Index tiers (items 1 and 2). Identical point values in all 12 tables of the  #
# 2026 Mart term; Sağlık adds 1f (case report), Spor adds SPORT Discus to 1c.  #
# tier -> (TABLO sub-item, face points, kind); kind "note" = letter to the     #
# editor / research note / abstract / book review / case report.               #
# --------------------------------------------------------------------------- #

BASE_TIERS: dict[str, tuple[str, int, str]] = {
    "Q1": ("1a", 30, "article"),
    "Q2": ("1a", 20, "article"),
    "Q3": ("1a", 15, "article"),
    "Q4": ("1a", 10, "article"),
    "AHCI": ("1b", 20, "article"),
    "ESCI": ("1c", 10, "article"),
    "Scopus": ("1c", 10, "article"),
    "OtherIntl": ("1d", 5, "article"),
    "IntlNote": ("1e", 3, "note"),
    "TRDizin": ("2a", 10, "article"),
    "OtherNational": ("2b", 4, "article"),
    "NationalNote": ("2c", 2, "note"),
}

Q14 = ("Q1", "Q2", "Q3", "Q4")          # 1a
Q13 = ("Q1", "Q2", "Q3")                # 1a, Q1-Q3 only
IAB = Q14 + ("AHCI",)                   # 1a + 1b
IABC = IAB + ("ESCI", "Scopus")         # 1a + 1b + 1c
IABCD = IABC + ("OtherIntl",)           # 1a-1d
TR = ("TRDizin",)                       # 2a
ITEM1 = "ITEM1"                         # every item-1 tier of the field
ITEM2 = "ITEM2"                         # every item-2 tier of the field

ITEM_NAMES = {
    3: "Lisansüstü Tezlerden Üretilmiş Yayın", 4: "Kitap", 5: "Atıf",
    6: "Lisansüstü Tez Danışmanlığı", 7: "Bilimsel Araştırma Projesi",
    8: "Bilimsel Toplantı", 9: "Eğitim-Öğretim", 10: "Patent/Faydalı Model",
    11: "Ödül", 12: "Editörlük", 13: "Diğer",
}

LEAD_DEF_WITH_FIRST = (
    "başlıca yazar = (a) author of a single-author article, (b) the first-listed author, "
    "or (c) the advisor on an article written with their own graduate student(s); a "
    "second advisor is not başlıca yazar"
)
LEAD_DEF_NO_FIRST = (
    "başlıca yazar = (a) author of a single-author article or (b) the advisor on an "
    "article written with their own graduate student(s); a second advisor is not "
    "başlıca yazar — first authorship alone does NOT qualify in this field"
)


def _pts(tiers, minimum, desc, *, scope="post_doc", who=None, named=None, named_desc=""):
    return {"kind": "points", "tiers": tiers, "min": minimum, "desc": desc, "scope": scope,
            "who": who, "named": named, "named_desc": named_desc}


def _cnt(tiers, minimum, desc, *, scope="post_doc", who=None):
    return {"kind": "count", "tiers": tiers, "min": minimum, "desc": desc, "scope": scope,
            "who": who, "named": None, "named_desc": ""}


def _check(cid, item, quote, conds, *, verify=(), alternative=None):
    routes = [{"name": "rule", "quote": quote, "conds": conds, "verify": list(verify)}]
    if alternative:
        routes[0]["name"] = "primary"
        routes.append({"name": "alternative", **alternative})
    return {"id": cid, "item": item, "routes": routes}


def _manual(mid, label_tr, requirement, why, *, bilim_alani_only=None):
    out = {"id": mid, "label_tr": label_tr, "requirement": requirement, "why_unmodelled": why}
    if bilim_alani_only:
        out["_only"] = bilim_alani_only
    return out


# --------------------------------------------------------------------------- #
# Shared rule sentences (verbatim, whitespace-normalised) used by several fields #
# --------------------------------------------------------------------------- #

_Q_FILOLOJI_HUKUK = (
    "Bu madde kapsamında, doktora ünvanının alınmasından sonra, a bendinden dördü tek "
    "yazarlı olmak üzere, üçü farklı dergilerde yayımlanmış en az altı yayın yapmak ve "
    "en az 50 puan almak zorunludur."
)
_Q_TR_10 = ("Bu madde kapsamında, doktora ünvanının alınmasından sonra, a bendinden en az "
            "10 puan almak zorunludur.")
_Q_EGITIM_2 = ("Bu madde kapsamında, doktora ünvanının alınmasından sonra, biri a bendinden "
               "olmak üzere en az iki yayın zorunludur.")
_Q_FEN_1 = ("Bu madde kapsamında, doktora ünvanının alınmasından sonra, a bendinden Q1, Q2 veya "
            "Q3 dergilerde yayımlanmış makalelerden en az birinde başlıca yazar olmak kaydıyla, "
            "Biyoloji, Fizik, Kimya, Moleküler Biyoloji ve Genetik bilim alanlarında 40 puan, "
            "Matematik ve İstatistik bilim alanlarında 20 puan almak zorunludur.")
_Q_MIM_1 = ("Bu madde kapsamında, doktora ünvanının alınmasından sonra, a, b veya c bentlerinden "
            "en az bir makalede başlıca yazar olmak kaydıyla en az 20 puan almak zorunludur.")
_Q_MUH_1 = ("Bu madde kapsamında, doktora ünvanının alınmasından sonra, a bendinden Q1, Q2 veya "
            "Q3 dergilerde yayımlanmış makalelerden en az birinde başlıca yazar olmak kaydıyla 40 "
            "puan almak zorunludur.")
_Q_SAG_1 = ("Bu madde kapsamında, doktora veya tıpta, diş hekimliğinde, eczacılıkta ve veteriner "
            "hekimlikte uzmanlık ünvanının alınmasından sonra, a bendinden en az üç makalede "
            "başlıca yazar olmak kaydıyla en az 40 puan almak zorunludur.")
_Q_ZIR_1 = ("Bu madde kapsamında, doktora ünvanının alınmasından sonra, a bendinden en az 30 puan "
            "almak ve aynı zamanda bu kapsamdaki Q1, Q2 veya Q3 dergilerde en az bir makalede "
            "başlıca yazar olmak kaydıyla en az 20 puan almak zorunludur.")
_Q_SPOR_1 = ("Bu madde kapsamında, doktora ünvanının alınmasından sonra, a veya b bentlerinden "
             "birinde başlıca yazar olmak üzere en az 30 puan almak zorunludur.")
_Q_SPOR_2 = ("Bu madde kapsamında, doktora ünvanının alınmasından sonra, ikisi a bendinden olmak "
             "üzere en az üç yayın yapmak zorunludur.")


def _alt_2_abc(quote):
    """'1. maddenin a, b veya c bentlerinden biri tek yazarlı ... iki yayın ... 50 puan'."""
    return {
        "quote": quote,
        "conds": [
            _cnt(IABC, 2, "item 1a/1b/1c publications (any date — the sentence does not "
                 "say post-doctorate)", scope="all"),
            _cnt(IABC, 1, "single-author item 1a/1b/1c publications (any date)",
                 scope="all", who="single"),
            _pts(ITEM1, 50, "item-1 points (any date)", scope="all", named=IABC,
                 named_desc="item 1a/1b/1c"),
        ],
        "verify": [],
    }


# --------------------------------------------------------------------------- #
# The 12 temel alan tables — ÜAK 2026 Mart term, transcribed 2026-09-23.         #
# Every number below is quoted in ../references/field_tables.md with its PDF.  #
# --------------------------------------------------------------------------- #

FIELDS: dict[str, dict] = {
    "egitim": {
        "table": "TABLO 1", "name_tr": "Eğitim Bilimleri Temel Alanı",
        "name_en": "Educational Sciences", "pdf": "69affdf9a48a5.pdf",
        "share": "equal", "lead_bases": None,
        "aliases": ["egitim bilimleri", "education", "educational sciences"],
        "checks": [
            _check("intl_q1_q3_points_ge_30", "1",
                   "Bu madde kapsamında, doktora ünvanının alınmasından sonra, a bendinden Q1, "
                   "Q2 veya Q3 dergilerde yayımlanmış makalelerden en az 30 puan almak zorunludur.",
                   [_pts(Q13, 30, "post-doctorate points from item 1a Q1-Q3 articles (Q4 excluded)")]),
            _check("national_pubs_ge_2", "2", _Q_EGITIM_2,
                   [_cnt(ITEM2, 2, "post-doctorate item-2 publications (2a/2b/2c)")]),
            _check("national_trdizin_ge_1", "2", _Q_EGITIM_2,
                   [_cnt(TR, 1, "post-doctorate TR Dizin (2a) articles")]),
        ],
        "caps": {3: 20, 4: 20, 5: 10, 6: 10, 7: 15, 8: 10, 9: 6, 10: None, 11: 25, 12: 4, 13: 10},
        "sub_caps": [(3, "gh", 5), (4, "cd", 5)],
        "citation_min": 5, "meeting_self": False, "book": None, "extra_manual": [],
    },
    "fen": {
        "table": "TABLO 2", "name_tr": "Fen Bilimleri ve Matematik Temel Alanı",
        "name_en": "Natural Sciences and Mathematics", "pdf": "69affdf9a7199.pdf",
        "share": "lead", "lead_bases": ("single", "advisor"),
        "aliases": ["fen bilimleri ve matematik", "fen bilimleri", "science", "sciences",
                    "natural sciences", "mathematics"],
        # The item-1 threshold depends on the bilim alanı (the temel alan has exactly
        # these six in the 2026 Mart/Ekim Bilim Alanları files).
        "bilim_alani_thresholds": {
            "Biyoloji": 40, "Fizik": 40, "Kimya": 40, "Moleküler Biyoloji ve Genetik": 40,
            "Matematik": 20, "İstatistik": 20,
        },
        "checks": [
            _check("intl_points_ge_{T}", "1", _Q_FEN_1,
                   [_pts(ITEM1, "BY_BILIM_ALANI", "post-doctorate item-1 points", named=Q13,
                         named_desc="item 1a Q1-Q3 articles")]),
            _check("lead_q1_q3_articles_ge_1", "1", _Q_FEN_1,
                   [_cnt(Q13, 1, "post-doctorate item 1a Q1-Q3 articles with the candidate as "
                         "başlıca yazar", who="lead")]),
            _check("trdizin_points_ge_10", "2", _Q_TR_10,
                   [_pts(TR, 10, "post-doctorate TR Dizin (2a) points")]),
        ],
        "caps": {3: 20, 4: 20, 5: 10, 6: 10, 7: 30, 8: 10, 9: 6, 10: None, 11: 25, 12: 4, 13: 10},
        "sub_caps": [(4, "cd", 5)],
        "citation_min": 5, "meeting_self": False, "book": None, "extra_manual": [],
    },
    "filoloji": {
        "table": "TABLO 3", "name_tr": "Filoloji Temel Alanı",
        "name_en": "Philology", "pdf": "69affdf9aa08c.pdf",
        "share": "equal", "lead_bases": None,
        "aliases": ["dil bilimi ve filoloji", "philology", "linguistics and philology"],
        "checks": [
            _check("national_articles", "2", _Q_FILOLOJI_HUKUK,
                   [_cnt(TR, 6, "post-doctorate TR Dizin (2a) publications"),
                    _cnt(TR, 4, "single-author post-doctorate TR Dizin (2a) publications",
                         who="single"),
                    _pts(ITEM2, 50, "post-doctorate item-2 points", named=TR,
                         named_desc="item 2a (TR Dizin)")],
                   verify=["üçü farklı dergilerde — at least three of the TR Dizin publications "
                           "must be in different journals (journal names are not an input)"],
                   alternative=_alt_2_abc(
                       "Ulusal makale asgari şartını sağlayamayan adaylar, 1. maddenin a, b veya "
                       "c bentlerinden biri tek yazarlı olmak üzere en az iki yayın yapmak ve en "
                       "az 50 puan almak zorundadırlar.")),
        ],
        "caps": {3: 20, 4: None, 5: 10, 6: 10, 7: 20, 8: 10, 9: 6, 10: None, 11: 25, 12: 4, 13: 10},
        "sub_caps": [(3, "gh", 5), (4, "cd", 30)],
        "citation_min": 5, "meeting_self": False,
        "book": ("At least one publication from item 4a (BKCI book) or 4c (other "
                 "international/national book), published after the doctorate. Item 4 values "
                 "differ here: 4c = 20, 4d = 5 points."),
        "extra_manual": [],
        "notes": ["The 2026 Ekim Bilim Alanları file (the only Ekim file posted on "
                  "2026-09-23) already names this temel alan 'Dil Bilimi ve Filoloji' — expect "
                  "the Ekim criteria to change; re-check before an Ekim application."],
    },
    "guzel_sanatlar": {
        "table": "TABLO 4", "name_tr": "Güzel Sanatlar Temel Alanı",
        "name_en": "Fine Arts", "pdf": "69affdf9ad469.pdf",
        "share": "equal", "lead_bases": None, "doctorate": "doktora/sanatta yeterlik",
        "aliases": ["guzel sanatlar", "fine arts", "gs"],
        "checks": [
            _check("intl_points_a_to_d_ge_10", "1",
                   "Bu madde kapsamında, doktora/sanatta yeterlik ünvanının alınmasından sonra, "
                   "a, b, c veya d bentlerinden en az 10 puan almak zorunludur.",
                   [_pts(IABCD, 10, "post-doctorate/sanatta-yeterlik points from items 1a-1d "
                         "(1e notes excluded)")]),
            _check("trdizin_single_author_ge_1", "2",
                   "Bu madde kapsamında, doktora/sanatta yeterlik ünvanının alınmasından sonra, "
                   "a bendinden tek yazarlı en az bir yayın zorunludur.",
                   [_cnt(TR, 1, "single-author post-doctorate TR Dizin (2a) publications",
                         who="single")]),
        ],
        "caps": {3: 20, 4: 20, 5: 10, 6: 10, 7: 20, 8: 10, 9: 6, 10: None, 11: 25, 12: 4, 13: 10},
        "sub_caps": [(3, "gh", 5), (4, "cd", 5)],
        "citation_min": 2, "meeting_self": True,
        "book": ("At least one book, or one book chapter (every chapter of that book related to "
                 "the applied bilim/sanat alanı), published after the doktora/sanatta yeterlik "
                 "(item 4)."),
        "extra_manual": [
            _manual("ozel_basvuru_sartlari", "Özel Başvuru Şartları (sanat alanına göre)",
                    "TABLO 4 requires the 'Genel' AND the 'Özel Başvuru Şartları' together. "
                    "Geleneksel Türk Sanatları / Plastik Sanatlar / Tasarım / Sinema: after the "
                    "doktora/sanatta yeterlik, at least 40 points from a-c (solo exhibition with "
                    "≥15 original works 20; directing a festival-selected or invited feature/"
                    "documentary/experimental film 20; its cinematography 10) and at least 10 "
                    "points from d-e (group exhibition/biennial/festival etc. 5; crew of such a "
                    "screened film 5); f-h (permanent public display, applied design, "
                    "advertising film/music clip; 5 each) together at most 10; every activity "
                    "needs a different, previously unexhibited work. Müzik and Sahne Sanatları "
                    "sub-areas have their own minimums — see references/field_tables.md. TABLO 4 "
                    "does not say whether Özel points count toward the 100-point total.",
                    "Artistic activities are not publications and the Özel group depends on the "
                    "sanat alanı; verify against TABLO 4 by hand."),
        ],
    },
    "hukuk": {
        "table": "TABLO 5", "name_tr": "Hukuk Temel Alanı",
        "name_en": "Law", "pdf": "69affdf9af864.pdf",
        "share": "equal", "lead_bases": None,
        "aliases": ["law"],
        "checks": [
            _check("national_articles", "2", _Q_FILOLOJI_HUKUK,
                   [_cnt(TR, 6, "post-doctorate TR Dizin (2a) publications"),
                    _cnt(TR, 4, "single-author post-doctorate TR Dizin (2a) publications",
                         who="single"),
                    _pts(ITEM2, 50, "post-doctorate item-2 points", named=TR,
                         named_desc="item 2a (TR Dizin)")],
                   verify=["üçü farklı dergilerde — at least three of the TR Dizin publications "
                           "must be in different journals (journal names are not an input)"],
                   alternative=_alt_2_abc(
                       "Ulusal makale asgari koşulunu sağlayamayan adaylar, 1. maddenin a, b veya "
                       "c bentlerinden biri tek yazarlı olmak üzere en az iki yayın yapmak ve en "
                       "az 50 puan almak zorundadırlar.")),
        ],
        "caps": {3: 20, 4: None, 5: 10, 6: 10, 7: 20, 8: 10, 9: 6, 10: None, 11: 25, 12: 4, 13: 10},
        "sub_caps": [(3, "gh", 10), (4, "cd", 30)],
        "citation_min": 5, "meeting_self": True,
        "book": ("At least one publication from item 4a (BKCI book) or 4c (other "
                 "international/national book), published after the doctorate. Item 4 values "
                 "differ here: 4c = 20, 4d = 10; refereed articles in Armağan/Anma books that are "
                 "not issues of a TR Dizin journal may be scored as book chapters."),
        "extra_manual": [],
    },
    "ilahiyat": {
        "table": "TABLO 6", "name_tr": "İlahiyat Temel Alanı",
        "name_en": "Theology", "pdf": "69affdf9b2d26.pdf",
        "share": "equal", "lead_bases": None,
        "aliases": ["theology", "islamic studies"],
        "item_names": {13: "Sanatsal Uygulama/Etkinlik", 14: "Diğer"},
        "checks": [
            _check("national_articles", "2",
                   "Bu madde kapsamında, doktora ünvanının alınmasından sonra, a bendinden üçü "
                   "tek yazarlı olmak üzere, ikisi farklı dergilerde yayımlanmış en az beş yayın "
                   "yapmak ve en az 50 puan almak zorunludur.",
                   [_cnt(TR, 5, "post-doctorate TR Dizin (2a) publications"),
                    _cnt(TR, 3, "single-author post-doctorate TR Dizin (2a) publications",
                         who="single"),
                    _pts(ITEM2, 50, "post-doctorate item-2 points", named=TR,
                         named_desc="item 2a (TR Dizin)")],
                   verify=["ikisi farklı dergilerde — at least two of the TR Dizin publications "
                           "must be in different journals (journal names are not an input)"],
                   alternative=_alt_2_abc(
                       "Ulusal makale asgari koşulunu sağlayamayan adaylar, 1. maddenin a, b veya "
                       "c bentlerinden biri tek yazarlı olmak üzere en az iki yayın yapmak ve en "
                       "az 50 puan almak zorundadırlar.")),
        ],
        "caps": {3: 20, 4: None, 5: 10, 6: 10, 7: 20, 8: 10, 9: 6, 10: None, 11: 25, 12: 4,
                 13: 20, 14: 10},
        "sub_caps": [(3, "gh", 5), (4, "cde", 30)],
        "citation_min": 5, "meeting_self": False,
        "book": ("At least one publication from item 4a (BKCI or Scopus book) or 4c (other "
                 "international/national book), published after the doctorate. Item 4 here: "
                 "4c = 20, 4d = 5, 4e tahkik (critical edition) = 10; c/d/e together at most 30."),
        "extra_manual": [
            _manual("dini_musiki_item13", "Dinî Musiki: 13. madde asgari koşulu",
                    "Candidates in the Dinî Musiki bilim alanı must earn at least 10 points from "
                    "item 13 a-d (original composition in religious-music forms 5; performer in "
                    "a solo/group concert 5; ≥30-minute recording on a digital platform 5; "
                    "album 5); item 13 is capped at 20 and needs documentation.",
                    "Artistic activities are not publications; verify by hand.",
                    bilim_alani_only=["Dini Musiki"]),
        ],
    },
    "mimarlik": {
        "table": "TABLO 8", "name_tr": "Mimarlık, Planlama ve Tasarım Temel Alanı",
        "name_en": "Architecture, Planning and Design", "pdf": "69affdf9b55bf.pdf",
        "share": "lead", "lead_bases": ("single", "first", "advisor"),
        "aliases": ["mimarlik planlama ve tasarim", "mimarlik", "architecture", "mpt",
                    "architecture planning and design"],
        "item_names": {13: "Yarışma, Proje ve Yazılım", 14: "Diğer"},
        "checks": [
            _check("intl_points_ge_20", "1", _Q_MIM_1,
                   [_pts(ITEM1, 20, "post-doctorate item-1 points", named=IABC,
                         named_desc="items 1a-1c")]),
            _check("lead_intl_a_to_c_articles_ge_1", "1", _Q_MIM_1,
                   [_cnt(IABC, 1, "post-doctorate item 1a-1c articles with the candidate as "
                         "başlıca yazar", who="lead")]),
            _check("trdizin_points_ge_10", "2", _Q_TR_10,
                   [_pts(TR, 10, "post-doctorate TR Dizin (2a) points")]),
        ],
        "caps": {3: 20, 4: 20, 5: 10, 6: 10, 7: 30, 8: 10, 9: 6, 10: None, 11: 25, 12: 4,
                 13: None, 14: 10},
        "sub_caps": [(4, "cd", 5)],
        "citation_min": 5, "meeting_self": False, "book": None,
        "extra_manual": [
            _manual("yarisma_proje_yazilim_item13", "Yarışma, Proje ve Yazılım asgari koşulu",
                    "At least 15 points from item 13 (award/mention in an architecture, planning, "
                    "urban-design, landscape, interior or industrial-design competition as team "
                    "leader/member 15; an applied/completed design, planning or conservation "
                    "project written up in an article, chapter or book 10; software producer in "
                    "project/construction management, design or planning 15). Candidates who "
                    "cannot meet it must have at least one publication from item 1a, 1b or 1c.",
                    "Competitions, projects and software are not in the publication list."),
        ],
    },
    "muhendislik": {
        "table": "TABLO 9", "name_tr": "Mühendislik Temel Alanı",
        "name_en": "Engineering", "pdf": "69affdf9b8303.pdf",
        "share": "lead", "lead_bases": ("single", "advisor"),
        "aliases": ["engineering"],
        "checks": [
            _check("intl_points_ge_40", "1", _Q_MUH_1,
                   [_pts(ITEM1, 40, "post-doctorate item-1 points", named=Q13,
                         named_desc="item 1a Q1-Q3 articles")]),
            _check("lead_q1_q3_articles_ge_1", "1", _Q_MUH_1,
                   [_cnt(Q13, 1, "post-doctorate item 1a Q1-Q3 articles with the candidate as "
                         "başlıca yazar", who="lead")]),
            _check("trdizin_points_ge_10", "2", _Q_TR_10,
                   [_pts(TR, 10, "post-doctorate TR Dizin (2a) points")]),
        ],
        "caps": {3: 20, 4: 20, 5: 10, 6: 10, 7: 30, 8: 10, 9: 6, 10: None, 11: 25, 12: 4, 13: 10},
        "sub_caps": [(4, "cd", 5)],
        "citation_min": 5, "meeting_self": False, "book": None, "extra_manual": [],
    },
    "saglik": {
        "table": "TABLO 10", "name_tr": "Sağlık Bilimleri Temel Alanı",
        "name_en": "Health Sciences", "pdf": "69affdf9bb4a6.pdf",
        "share": "lead", "lead_bases": ("single", "first", "advisor"),
        "doctorate": "doktora veya tıpta/diş hekimliğinde/eczacılıkta/veteriner hekimlikte uzmanlık",
        "aliases": ["saglik bilimleri", "health", "health sciences", "medicine"],
        "extra_tiers": {"CaseReport": ("1f", 5, "note")},
        # v2.1-compatible check set: the national-article minimum stays a manual check.
        "checks": [
            _check("intl_article_ge_40", "1", _Q_SAG_1,
                   [_pts(ITEM1, 40, "post-doctorate item-1 points", named=Q14,
                         named_desc="item 1a (SCIE/SSCI Q1-Q4) articles")]),
            _check("lead_q_articles_ge_3", "1", _Q_SAG_1,
                   [_cnt(Q14, 3, "post-doctorate item 1a Q1-Q4 articles with the candidate as "
                         "başlıca yazar", who="lead")]),
        ],
        "caps": {3: 20, 4: 20, 5: 10, 6: 10, 7: 20, 8: 10, 9: 6, 10: None, 11: 25, 12: 4, 13: 10},
        "sub_caps": [(3, "gh", 5), (4, "cd", 5)],
        "citation_min": 5, "meeting_self": False, "book": None,
        "extra_manual": [
            _manual("national_trdizin_articles", "Ulusal makale / TR Dizin asgari koşulu",
                    "Post-doctorate national publications (item 2): at least 3, of which at "
                    "least 2 are TR Dizin articles (2a), with the candidate başlıca yazar in at "
                    "least 2. Foreign nationals and foreign-doçentlik-equivalence applicants may "
                    "substitute the same number of item 1a/1b/1c articles.",
                    "Kept manual for v2.1 compatibility of the Sağlık check set; resolve TR "
                    "Dizin status with alterlab-trdizin first."),
        ],
        "notes": ["Yan dal uzmanlığından yapılan müracaatta, ana dal uzmanlığının alınmasından "
                  "sonra yapılan çalışmalar esas alınır — for a sub-specialty application, "
                  "post_doc means after the main-specialty title."],
    },
    "sosyal": {
        "table": "TABLO 11", "name_tr": "Sosyal, Beşeri ve İdari Bilimler Temel Alanı",
        "name_en": "Social Sciences, Humanities and Administrative Sciences",
        "pdf": "69affdf9bdbcc.pdf",
        "share": "equal", "lead_bases": None,
        "aliases": ["sosyal beseri ve idari bilimler", "sosyal bilimler", "sosyal beseri idari",
                    "social sciences", "humanities", "administrative sciences", "sbib"],
        "checks": [
            _check("intl_points_a_to_d_ge_10", "1",
                   "Bu madde kapsamında, doktora ünvanının alınmasından sonra, a, b, c veya d "
                   "bentlerinden en az 10 puan almak zorunludur.",
                   [_pts(IABCD, 10, "post-doctorate points from items 1a-1d (1e notes excluded)")]),
            _check("national_articles", "2",
                   "Bu madde kapsamında, doktora ünvanının alınmasından sonra, a bendinden üçü "
                   "tek yazarlı olmak üzere farklı dergilerde yayımlanmış en az beş yayın "
                   "zorunludur.",
                   [_cnt(TR, 5, "post-doctorate TR Dizin (2a) publications"),
                    _cnt(TR, 3, "single-author post-doctorate TR Dizin (2a) publications",
                         who="single")],
                   verify=["farklı dergilerde — the TR Dizin publications must be in different "
                           "journals (journal names are not an input)"],
                   alternative={
                       "quote": "Ulusal makale asgari koşulunu sağlayamayan adaylar, 1. maddenin a "
                                "veya b bentlerinden biri tek yazarlı olmak üzere en az üç yayın "
                                "yapmak zorundadırlar.",
                       "conds": [
                           _cnt(IAB, 3, "item 1a/1b publications (any date — the sentence does "
                                "not say post-doctorate)", scope="all"),
                           _cnt(IAB, 1, "single-author item 1a/1b publications (any date)",
                                scope="all", who="single"),
                       ],
                       "verify": [],
                   }),
        ],
        "caps": {3: 20, 4: 20, 5: 10, 6: 10, 7: 20, 8: 10, 9: 6, 10: None, 11: 25, 12: 4, 13: 20},
        "sub_caps": [(3, "gh", 5), (4, "cd", 5)],
        "citation_min": 5, "meeting_self": False,
        "book": ("At least one book, or two book chapters (every chapter of the book related to "
                 "the applied bilim alanı), published after the doctorate (item 4)."),
        "extra_manual": [
            _manual("iletisim_item13_cde", "İletişim alanları: 13. madde c-e asgari koşulu",
                    "Applicants in Görsel İletişim Tasarımı, İletişim Çalışmaları, Reklamcılık, "
                    "Sinema or Halkla İlişkiler must earn at least 10 points from item 13 c, d or "
                    "e (film-festival jury member/director/coordinator/consultant 5; director/"
                    "assistant director/consultant of a short or feature film 5; a bilim-alanı "
                    "role in a series/documentary/music video/advertising film/film content "
                    "broadcast on national TV, cinema or a digital platform 5); item 13 is "
                    "capped at 20.",
                    "Film/media roles are not publications; enter item-13 points under "
                    "other_items to apply the cap, but verify the c-e minimum by hand.",
                    bilim_alani_only=["Görsel İletişim Tasarımı", "İletişim Çalışmaları",
                                      "Reklamcılık", "Sinema", "Halkla İlişkiler"]),
        ],
    },
    "ziraat": {
        "table": "TABLO 12", "name_tr": "Ziraat, Orman ve Su Ürünleri Temel Alanı",
        "name_en": "Agriculture, Forestry and Aquaculture", "pdf": "69affdf9c2d3b.pdf",
        "share": "lead", "lead_bases": ("single", "advisor"),
        "aliases": ["ziraat orman ve su urunleri", "ziraat", "agriculture", "forestry"],
        "checks": [
            _check("intl_1a_points_ge_30", "1", _Q_ZIR_1,
                   [_pts(Q14, 30, "post-doctorate item 1a (SCIE/SSCI Q1-Q4) points")]),
            _check("intl_points_ge_20", "1", _Q_ZIR_1,
                   [_pts(ITEM1, 20, "post-doctorate item-1 points", named=Q13,
                         named_desc="item 1a Q1-Q3 articles")]),
            _check("lead_q1_q3_articles_ge_1", "1", _Q_ZIR_1,
                   [_cnt(Q13, 1, "post-doctorate item 1a Q1-Q3 articles with the candidate as "
                         "başlıca yazar", who="lead")]),
            _check("trdizin_points_ge_20", "2",
                   "Bu madde kapsamında, doktora ünvanının alınmasından sonra, a bendinden en az "
                   "20 puan almak zorunludur.",
                   [_pts(TR, 20, "post-doctorate TR Dizin (2a) points")]),
        ],
        "caps": {3: 20, 4: 20, 5: 10, 6: 10, 7: 60, 8: 10, 9: 6, 10: None, 11: 25, 12: 4, 13: 10},
        "sub_caps": [(4, "cd", 5)],
        "citation_min": 5, "meeting_self": False, "book": None, "extra_manual": [],
    },
    "spor": {
        "table": "TABLO 13", "name_tr": "Spor Bilimleri Temel Alanı",
        "name_en": "Sport Sciences", "pdf": "69affdf9c4ea1.pdf",
        "share": "lead", "lead_bases": ("single", "first", "advisor"),
        "aliases": ["spor bilimleri", "sport", "sports", "sport sciences"],
        "extra_tiers": {"SPORTDiscus": ("1c", 10, "article")},
        "item_names": {13: "Sportif Başarı ve Temsil", 14: "Diğer"},
        "checks": [
            _check("intl_points_ge_30", "1", _Q_SPOR_1,
                   [_pts(ITEM1, 30, "post-doctorate item-1 points", named=IAB,
                         named_desc="items 1a-1b")]),
            _check("lead_1a_1b_articles_ge_1", "1", _Q_SPOR_1,
                   [_cnt(IAB, 1, "post-doctorate item 1a/1b articles with the candidate as "
                         "başlıca yazar", who="lead")]),
            _check("national_pubs_ge_3", "2", _Q_SPOR_2,
                   [_cnt(ITEM2, 3, "post-doctorate item-2 publications (2a/2b/2c)")]),
            _check("national_trdizin_ge_2", "2", _Q_SPOR_2,
                   [_cnt(TR, 2, "post-doctorate TR Dizin (2a) articles")]),
        ],
        "caps": {3: 20, 4: 20, 5: 10, 6: 10, 7: 20, 8: 10, 9: 6, 10: None, 11: 25, 12: 4,
                 13: 15, 14: 10},
        "sub_caps": [(3, "gh", 5), (4, "cd", 5)],
        "citation_min": 5, "meeting_self": False,
        "book": ("At least one book, or two book chapters (every chapter of the book related to "
                 "the applied bilim alanı), published after the doctorate (item 4)."),
        "extra_manual": [],
    },
}

MIN_TOTAL = 100          # asgari toplam puan — identical in all 12 tables
MIN_POST_DOC = 90        # doktora (vb.) sonrası asgari puan, item 3 excluded — all 12 tables


def lead_definition(spec: dict) -> str | None:
    if spec["share"] != "lead":
        return None
    return LEAD_DEF_WITH_FIRST if "first" in spec["lead_bases"] else LEAD_DEF_NO_FIRST


# --------------------------------------------------------------------------- #
# Normalisation helpers                                                         #
# --------------------------------------------------------------------------- #

_TR_FOLD = str.maketrans({"İ": "i", "I": "i", "ı": "i", "ç": "c", "Ç": "c", "ğ": "g",
                          "Ğ": "g", "ö": "o", "Ö": "o", "ş": "s", "Ş": "s", "ü": "u",
                          "Ü": "u", "â": "a", "Â": "a", "î": "i", "Î": "i", "û": "u",
                          "Û": "u"})


def fold(text: object) -> str:
    """Case- and diacritic-insensitive key: 'Sağlık Bilimleri' -> 'saglikbilimleri'."""
    s = str(text).translate(_TR_FOLD).lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]", "", s)


def resolve_alan(value: object) -> str:
    """Map a field name/alias to its code, or raise ValueError (never guess)."""
    key = fold(value)
    for code, spec in FIELDS.items():
        keys = {fold(code), fold(spec["name_tr"]), fold(spec["name_tr"].replace("Temel Alanı", "")),
                fold(spec["name_en"])} | {fold(a) for a in spec.get("aliases", [])}
        if key in keys:
            return code
    raise ValueError(
        f"no verified ÜAK table for alan {value!r}. Bundled ({TERM} term, transcribed "
        f"{TABLE_LAST_VERIFIED}): {', '.join(FIELDS)}. For any other field or term, read the "
        f"live criteria at {UAK_PAGE} — this tool never guesses point values."
    )


def parse_bool(value: object, default: bool = False) -> tuple[bool, bool]:
    """Return (value, recognised). Strings like 'false'/'hayır' are handled."""
    if value is None:
        return default, True
    if isinstance(value, bool):
        return value, True
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value), True
    s = fold(value)
    if s in {"true", "yes", "evet", "1", "y", "e"}:
        return True, True
    if s in {"false", "no", "hayir", "0", "n", "h"}:
        return False, True
    return default, False


def field_tiers(spec: dict) -> dict[str, tuple[str, int, str]]:
    return {**BASE_TIERS, **spec.get("extra_tiers", {})}


def resolve_tier(raw: str, tiers: dict) -> str | None:
    key = fold(raw)
    for code in tiers:
        if fold(code) == key:
            return code
    return None


def tier_set(tiers_spec, spec: dict) -> tuple[str, ...]:
    tiers = field_tiers(spec)
    if tiers_spec == ITEM1:
        return tuple(t for t, v in tiers.items() if v[0].startswith("1"))
    if tiers_spec == ITEM2:
        return tuple(t for t, v in tiers.items() if v[0].startswith("2"))
    return tuple(tiers_spec)


def item_names(spec: dict) -> dict[int, str]:
    return {**ITEM_NAMES, **spec.get("item_names", {})}


# --------------------------------------------------------------------------- #
# Scoring                                                                       #
# --------------------------------------------------------------------------- #

def share_factor(rule: str, kind: str, authors: int, is_lead: bool,
                 has_lead: bool = True) -> tuple[float, str]:
    """Author-share factor for one publication.

    equal rule (Eğitim, Filoloji, Güzel Sanatlar, Hukuk, İlahiyat, Sosyal):
        1 author -> 1.0; N authors -> 1/N for every author.
    lead rule (Fen, Mimarlık, Mühendislik, Sağlık, Spor, Ziraat), articles:
        1 author -> 1.0; 2 authors: başlıca yazar 0.8, other 0.5;
        >=3: başlıca yazar 0.5, others 0.5/(N-1); no başlıca yazar on the article -> 1/N.
    lead rule, notes (1e/1f/2c): the table does not say whether they are 'makale'
        (lead split) or 'Diğer yayınlarda' (equal split) -> the smaller share is used.
    """
    if authors <= 1:
        return 1.0, "single-author"
    equal = 1.0 / authors
    if rule == "equal":
        return equal, "equal-split"
    if not has_lead:
        return equal, "no-başlıca-yazar-equal-split"
    if authors == 2:
        lead_f = 0.8 if is_lead else 0.5
    else:
        lead_f = 0.5 if is_lead else 0.5 / (authors - 1)
    if kind == "note" and abs(lead_f - equal) > 1e-12:
        return min(lead_f, equal), "note-smaller-of-lead-or-equal"
    return lead_f, "başlıca-yazar-rule"


def score_publication(pub: object, spec: dict) -> dict:
    """Score one publication; flag it unscorable if its tier or author count is unusable."""
    if not isinstance(pub, dict):
        raise ValueError("every entry in 'publications' must be a JSON object")
    notes: list[str] = []
    title = str(pub.get("title", "")).strip() or "(untitled)"
    raw_index = str(pub.get("index", "")).strip()
    tiers = field_tiers(spec)
    code = resolve_tier(raw_index, tiers) if raw_index else None

    authors_raw = pub.get("authors", 1)
    authors: int | None
    if isinstance(authors_raw, bool):
        authors = None
    elif isinstance(authors_raw, int) and authors_raw >= 1:
        authors = authors_raw
    elif isinstance(authors_raw, float) and authors_raw.is_integer() and authors_raw >= 1:
        authors = int(authors_raw)
    elif isinstance(authors_raw, str) and authors_raw.strip().isdigit() and int(authors_raw) >= 1:
        authors = int(authors_raw)
    else:
        authors = None

    is_lead, ok1 = parse_bool(pub.get("is_lead"), False)
    post_doc, ok2 = parse_bool(pub.get("post_doc"), False)
    has_lead, ok3 = parse_bool(pub.get("has_lead"), True)
    for ok, name in ((ok1, "is_lead"), (ok2, "post_doc"), (ok3, "has_lead")):
        if not ok:
            notes.append(f"unrecognised {name} value — treated as the conservative default")
    if authors == 1:
        is_lead = True  # a single-author article is başlıca yazar by every definition
    lead_basis = pub.get("lead_basis")
    if spec["share"] == "lead" and is_lead and authors and authors > 1 and lead_basis:
        if fold(lead_basis) not in {fold(b) for b in spec["lead_bases"]}:
            is_lead = False
            notes.append(f"lead_basis {lead_basis!r} does not make a başlıca yazar in "
                         f"{spec['name_tr']} (allowed: {', '.join(spec['lead_bases'])}) — "
                         "scored as a non-lead co-author")
    if is_lead:
        has_lead = True

    base = {"title": title, "index": code or raw_index or "(unknown)", "authors": authors,
            "is_lead": is_lead, "post_doc": post_doc}
    if code is None or authors is None:
        reason = ("unknown index tier for this field — resolve and re-run (do not guess)"
                  if code is None else "author count missing or invalid — fix and re-run")
        return {**base, "item": None, "kind": None, "scorable": False, "face_points": None,
                "share_factor": None, "share_rule": None, "scaled": 0.0,
                "counts_lead_q": False, "is_scie_ssci": False, "is_intl_article": False,
                "note": reason, "notes": notes}

    item, face, kind = tiers[code]
    factor, rule_applied = share_factor(spec["share"], kind, authors, is_lead, has_lead)
    out = {**base, "item": item, "kind": kind, "scorable": True, "face_points": face,
           "share_factor": round(factor, 4), "share_rule": rule_applied, "scaled": face * factor,
           "counts_lead_q": spec["share"] == "lead" and is_lead and code in Q14 and post_doc,
           "is_scie_ssci": code in Q14, "is_intl_article": item.startswith("1")}
    if notes:
        out["notes"] = notes
    return out


def _cond_pool(cond: dict, scored: list[dict], spec: dict, *, tiers=None, post_doc_only=None):
    tiers = tier_set(cond["tiers"] if tiers is None else tiers, spec)
    scope_pd = (cond["scope"] == "post_doc") if post_doc_only is None else post_doc_only
    pool = [p for p in scored if p["scorable"] and p["index"] in tiers]
    if scope_pd:
        pool = [p for p in pool if p["post_doc"]]
    if cond["who"] == "single":
        pool = [p for p in pool if p["authors"] == 1]
    elif cond["who"] == "lead":
        pool = [p for p in pool if p["is_lead"]]
    return pool


def _measure(cond: dict, pool: list[dict]) -> float:
    if cond["kind"] == "points":
        return sum((p["scaled"] for p in pool), 0.0)
    return float(len(pool))


def _fmt(cond: dict, value: float):
    return round(value, 1) if cond["kind"] == "points" else int(value)


def eval_condition(cond: dict, scored: list[dict], spec: dict, minimum: float,
                   check_id: str, flags: list[dict]) -> dict:
    value = _measure(cond, _cond_pool(cond, scored, spec))
    passed = value >= minimum
    out = {"pass": passed, "value": _fmt(cond, value), "threshold": minimum,
           "desc": cond["desc"]}
    if not passed:
        out["short"] = _fmt(cond, minimum - value)
        return out
    if cond.get("named"):
        named_value = _measure(cond, _cond_pool(cond, scored, spec, tiers=cond["named"]))
        out["named_subitems_value"] = _fmt(cond, named_value)
        if named_value < minimum:
            flags.append({"check": check_id, "note": (
                f"passes only if points from outside {cond['named_desc']} count toward the "
                f"{minimum}-point minimum ({cond['named_desc']} alone: "
                f"{_fmt(cond, named_value)}). ÜAK's wording does not say explicitly where these "
                "points must come from — confirm before relying on this pass.")})
    if cond["scope"] == "all":
        pd_value = _measure(cond, _cond_pool(cond, scored, spec, post_doc_only=True))
        out["post_doc_value"] = _fmt(cond, pd_value)
        if pd_value < minimum:
            flags.append({"check": check_id, "note": (
                f"passes only when pre-doctorate work counts ({cond['desc']}: "
                f"{_fmt(cond, pd_value)} post-doctorate). The alternative-route sentence does "
                "not contain 'doktora ünvanının alınmasından sonra' — confirm with ÜAK.")})
    return out


def eval_check(check: dict, scored: list[dict], spec: dict, threshold_override,
               flags: list[dict], to_verify: list[str]) -> tuple[str, dict]:
    cid = check["id"]
    if "{T}" in cid:
        cid = cid.replace("{T}", str(threshold_override))
    route_results = {}
    passed_route = None
    for route in check["routes"]:
        route_flags: list[dict] = []
        conds = []
        for cond in route["conds"]:
            minimum = threshold_override if cond["min"] == "BY_BILIM_ALANI" else cond["min"]
            conds.append(eval_condition(cond, scored, spec, minimum, cid, route_flags))
        ok = all(c["pass"] for c in conds)
        route_results[route["name"]] = {"pass": ok, "rule_tr": route["quote"], "conditions": conds}
        if route["verify"]:
            route_results[route["name"]]["verify_by_hand"] = route["verify"]
        if ok and passed_route is None:
            passed_route = route["name"]
            flags.extend(route_flags)
            to_verify.extend(f"{cid}: {v}" for v in route["verify"])
    passed = passed_route is not None
    if len(check["routes"]) == 1 and len(check["routes"][0]["conds"]) == 1:
        only = route_results["rule"]
        cond = only["conditions"][0]
        res = {k: v for k, v in cond.items() if k != "desc"}
        res.update({"item": check["item"], "desc": cond["desc"], "rule_tr": only["rule_tr"]})
        return cid, res
    res = {"pass": passed, "item": check["item"], "passed_route": passed_route,
           "routes": route_results}
    return cid, res


def parse_item_code(raw: object) -> tuple[int, str]:
    m = re.fullmatch(r"\s*(\d{1,2})\s*([a-zçğıöşü])?\s*", str(raw).lower())
    if not m:
        raise ValueError(f"other_items: item {raw!r} is not a TABLO item code like 4 or '4c'")
    return int(m.group(1)), (m.group(2) or "")


def _num(value: object, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError(f"other_items: {what} must be a non-negative number, got {value!r}")
    return float(value)


def score_other_items(entries: object, spec: dict, notes: list[str]) -> tuple[list[dict], float, float]:
    """Apply the field's item and sub-item caps to self-computed points for items 3+.

    Each entry: {"item": 4 | "4c", "points": x, "post_doc_points": y, "label": "..."}.
    Points are the candidate's share, computed by hand from the TABLO (citations are not
    divided by author count; oral papers and books are — ÜAK S.S.S. Q27, Q33, Q36).
    """
    if entries in (None, []):
        return [], 0.0, 0.0
    if not isinstance(entries, list):
        raise ValueError("'other_items' must be a list")
    caps = spec["caps"]
    names = item_names(spec)
    agg: dict[int, dict[str, list[float]]] = {}
    for e in entries:
        if not isinstance(e, dict):
            raise ValueError("every entry in 'other_items' must be a JSON object")
        item, sub = parse_item_code(e.get("item"))
        if item in (1, 2):
            raise ValueError("other_items: articles (items 1 and 2) belong in 'publications'")
        if item not in caps:
            raise ValueError(f"other_items: {spec['table']} has no item {item} "
                             f"(items: {', '.join(str(i) for i in sorted(caps))})")
        pts = _num(e.get("points"), "points")
        if "post_doc_points" in e:
            pd = _num(e.get("post_doc_points"), "post_doc_points")
        else:
            pd = 0.0
            notes.append(f"other_items item {item}{sub}: post_doc_points missing — counted as 0 "
                         "toward the 90 post-doctorate points (conservative)")
        if pd > pts:
            notes.append(f"other_items item {item}{sub}: post_doc_points > points — clamped")
            pd = pts
        agg.setdefault(item, {}).setdefault(sub, [0.0, 0.0])
        agg[item][sub][0] += pts
        agg[item][sub][1] += pd
    rows, total, post_doc = [], 0.0, 0.0
    for item in sorted(agg):
        subs = agg[item]
        applied = []
        grouped: set[str] = set()
        raw = [0.0, 0.0]
        for s_item, letters, sub_cap in spec["sub_caps"]:
            if s_item != item:
                continue
            group = [sum(subs[s][i] for s in subs if s and s in letters) for i in (0, 1)]
            if group[0] > 0:
                applied.append(f"{'+'.join(f'{item}{x}' for x in letters)} ≤ {sub_cap}")
            grouped |= set(letters)
            raw[0] += float(min(group[0], sub_cap))
            raw[1] += float(min(group[1], sub_cap))
        for s, (p, d) in subs.items():
            if not s or s not in grouped:
                raw[0] += p
                raw[1] += d
        item_cap = caps[item]
        counted = float(min(raw[0], item_cap)) if item_cap is not None else raw[0]
        counted_pd = float(min(raw[1], item_cap)) if item_cap is not None else raw[1]
        if item == 3:
            counted_pd = 0.0  # item-3 points never count toward the 90
        declared = sum(p for p, _ in subs.values())
        rows.append({"item": item, "name_tr": names.get(item, ""), "declared": round(declared, 2),
                     "counted": round(counted, 2), "cap": item_cap, "sub_caps_applied": applied,
                     "post_doc_declared": round(sum(d for _, d in subs.values()), 2),
                     "post_doc_counted": round(counted_pd, 2)})
        if "" in subs and any(item == s_item for s_item, _, _ in spec["sub_caps"]):
            notes.append(f"other_items item {item}: entries without a sub-item letter are checked "
                         "against the item cap only — tag them (e.g. '4c') to apply sub-item caps")
        total += counted
        post_doc += counted_pd
    return rows, total, post_doc


def caps_text(spec: dict) -> str:
    names = item_names(spec)
    parts = []
    for item in sorted(spec["caps"]):
        cap = spec["caps"][item]
        subs = [f"{'+'.join(f'{i}{x}' for x in letters)} ≤ {c}" for i, letters, c in spec["sub_caps"] if i == item]
        cap_s = f"≤ {cap}" if cap is not None else "no cap stated"
        parts.append(f"{item} {names.get(item, '')} {cap_s}" + (f" ({'; '.join(subs)})" if subs else ""))
    return "; ".join(parts)


def manual_minimums(code: str, bilim_alani: str | None) -> list[dict]:
    spec = FIELDS[code]
    doctorate = spec.get("doctorate", "doktora")
    thesis_sub = [f"{'+'.join(f'{i}{x}' for x in letters)} ≤ {c}" for i, letters, c in spec["sub_caps"] if i == 3]
    items = [
        _manual("thesis_derived_publication", "Lisansüstü tezlerden üretilmiş yayın asgari koşulu",
                "At least 1 publication derived from the candidate's own graduate thesis (item 3, "
                "a-h). Item 3 is capped at 20 points" + (f" ({thesis_sub[0]})" if thesis_sub else "")
                + "; its points never count toward the 90 post-doctorate points, and a "
                "thesis-derived work is scored only under item 3 (never also as an item 1/2 "
                "article).",
                "The input does not flag thesis-derived work; leave such articles out of "
                "'publications' and enter their points under other_items as item 3."),
    ]
    if spec["book"]:
        items.append(_manual("book_kitap", "Kitap asgari koşulu", spec["book"],
                             "Books are not in the article list; verify by hand (enter item-4 "
                             "points under other_items to apply the caps)."))
    for extra in spec["extra_manual"]:  # field-specific requirements, most prominent first
        only = extra.get("_only")
        if only and bilim_alani and fold(bilim_alani) not in {fold(x) for x in only}:
            continue
        items.append({k: v for k, v in extra.items() if k != "_only"})
    meeting_extra = (", at least one of them presented by the candidate personally"
                     if spec["meeting_self"] else "")
    items += [
        _manual("citation_atif", "Atıf (citation) asgari koşulu",
                f"At least {spec['citation_min']} citation (atıf) points from work published after "
                f"the {doctorate}; self-citations excluded; several citations of one work inside "
                "the same citing publication count once; citation points are not divided by the "
                "author count (ÜAK S.S.S. Q27).",
                "Citation counts are not part of the publication list input."),
        _manual("scientific_meeting_bildiri", "Bilimsel toplantı (congress) asgari koşulu",
                f"At least 5 points from scientific-meeting papers after the {doctorate}"
                f"{meeting_extra}; at most one paper per meeting is scored; oral-paper points are "
                "divided equally among all authors (ÜAK S.S.S. Q33).",
                "Congress papers are a separate category not in the article list."),
        _manual("education_egitim_ogretim", "Eğitim-öğretim asgari koşulu",
                f"At least 2 teaching points after the {doctorate} (teaching in four different "
                "semesters, or two different years; 2 years as kadrolu öğretim elemanı after the "
                "doctorate counts as 2); item 9 is capped at 6.",
                "Teaching activity is not a publication and is not in the input."),
    ]
    items += [
        _manual("category_point_caps", "Kategori puan üst sınırları (caps)",
                f"Per-item ceilings in the {TERM} {spec['table']}: {caps_text(spec)}. Items 1 and "
                "2 are uncapped. The scorer applies these caps only to points entered under "
                "other_items; anything not entered is not in the totals.",
                "Caps need each non-article item tagged with its TABLO item and sub-item."),
        _manual("predatory_q4_journals", "Yağmacı/şaibeli dergi kuralı",
                "Articles in journals YÖK classes as yağmacı/şaibeli (decision 2021.18.643: Q4 "
                "journals that charge editorial or article-processing fees, apart from the stated "
                "society/university exceptions) stay on the CV but cannot be used in the "
                "doçentlik beyanname (ÜAK S.S.S. Q20). Remove such items before scoring.",
                "Journal fee models are not in the input."),
        _manual("relevance_bilim_alani", "Bilim alanı ile ilgi koşulu",
                "Every declared work and activity must be related to the bilim alanı applied for "
                "(ÜAK cancels an application whose declared works are partly outside the field — "
                "S.S.S. Q13); each work is scored in only one TABLO section (S.S.S. Q24-25).",
                "Topical relevance is a jury judgement."),
    ]
    return items


def build_report(data: dict, code: str, bilim_alani: str | None) -> dict:
    spec = FIELDS[code]
    pubs = data.get("publications", [])
    if not isinstance(pubs, list):
        raise ValueError("'publications' must be a list")
    notes: list[str] = list(spec.get("notes", []))

    threshold_override = None
    thresholds = spec.get("bilim_alani_thresholds")
    if thresholds:
        match = next((b for b in thresholds if bilim_alani and fold(b) == fold(bilim_alani)), None)
        if match is None:
            raise ValueError(
                f"{spec['name_tr']} sets its item-1 minimum per bilim alanı — pass --bilim-alani "
                f"(or 'bilim_alani' in the input) as one of: "
                + ", ".join(f"{b} ({t} points)" for b, t in thresholds.items())
                + f". Nothing is guessed; see {UAK_PAGE}.")
        bilim_alani = match
        threshold_override = thresholds[match]

    scored = [score_publication(p, spec) for p in pubs]
    other_rows, other_total, other_pd = score_other_items(data.get("other_items"), spec, notes)

    pub_total = sum(p["scaled"] for p in scored)
    pub_pd = sum(p["scaled"] for p in scored if p["post_doc"])
    total = pub_total + other_total
    post_doc_total = pub_pd + other_pd

    flags: list[dict] = []
    to_verify: list[str] = []
    # Totals: scored publications + capped other_items (item 3 never counts toward the 90).
    checks = {
        "total_ge_100": _plain_check(total, MIN_TOTAL),
        "post_doc_ge_90": _plain_check(post_doc_total, MIN_POST_DOC),
    }
    for check in spec["checks"]:
        cid, res = eval_check(check, scored, spec, threshold_override, flags, to_verify)
        checks[cid] = res

    lead_def = lead_definition(spec)
    if spec["share"] == "lead" and any(p["share_rule"] == "note-smaller-of-lead-or-equal"
                                       for p in scored):
        flags.append({"check": "author_share", "note": (
            "letters/notes/abstracts/reviews/case reports were scored with the smaller of the "
            "başlıca-yazar and the equal split — the table does not say which applies to them.")})
    if any(any("lead_basis" in n for n in p.get("notes", [])) for p in scored):
        flags.append({"check": "lead_author", "note": (
            f"at least one claimed başlıca yazar does not meet the {spec['name_tr']} definition "
            f"and was scored as non-lead ({lead_def}).")})

    all_pass = all(c["pass"] for c in checks.values())
    verdict = VERDICT_PASS if all_pass else VERDICT_FAIL
    verdict_meaning = {
        VERDICT_FAIL: (
            "At least one modelled minimum fails on the work supplied, so the application "
            "would not clear ÜAK's asgari koşullar as entered — whatever the unmodelled checks "
            "show. Total and post-doctorate points count only the scored publications plus any "
            "other_items entered, so add missing work (books, citations, projects, ...) before "
            "concluding."),
        VERDICT_PASS: (
            "All MODELLED minimums pass. NOT a green light — the unmodelled mandatory minimums "
            "(see unmodelled_minimums), any to_verify items and any interpretation_flags must "
            f"still be checked by hand against the live {spec['table']}. This tool cannot and "
            "does not declare eligibility."),
    }[verdict]

    if spec["share"] == "lead":
        notes.append(f"Author share ({spec['table']}): {lead_def}. An article with no başlıca "
                     "yazar is split equally — set has_lead: false for it.")
    else:
        notes.append(f"Author share ({spec['table']}): points are split equally among all "
                     "authors (tek yazarlı tam puan); is_lead does not change the score.")
    notes.append("Foreign nationals and foreign-doçentlik-equivalence applicants who cannot meet "
                 "the TR Dizin requirement may use the same number of item 1a/1b/1c publications "
                 "instead; the scorer does not apply this substitution.")

    summary = {
        "verdict": verdict,
        "verdict_meaning": verdict_meaning,
        "all_modelled_checks_pass": all_pass,
        "total_points": round(total, 1),
        "post_doc_points": round(post_doc_total, 1),
        "publication_points": round(pub_total, 1),
        "other_items_points": round(other_total, 1),
        "unscored_count": sum(1 for p in scored if not p["scorable"]),
        "checks": checks,
        "interpretation_flags": flags,
        "to_verify": to_verify,
        "unmodelled_minimums": manual_minimums(code, bilim_alani),
    }
    if code == "saglik":  # v2.1 summary keys, kept for compatibility
        summary["intl_article_points"] = checks["intl_article_ge_40"]["value"]
        summary["lead_q_articles"] = checks["lead_q_articles_ge_3"]["value"]

    return {
        "tool": "alterlab-docentlik-eligibility/score_docentlik.py",
        "version": VERSION,
        "field": code,
        "alan": code,
        "alan_name_tr": spec["name_tr"],
        "table": spec["table"],
        "term": TERM,
        "source_pdf": PDF_BASE + spec["pdf"],
        "table_last_verified": TABLE_LAST_VERIFIED,
        "bilim_alani": bilim_alani,
        "share_rule": spec["share"],
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "prescreen_only": True,
        "summary": summary,
        "unscored": [p["title"] for p in scored if not p["scorable"]],
        "publications": [{**p, "scaled": round(p["scaled"], 2)} for p in scored],
        "other_items": other_rows,
        "notes": notes,
        "disclaimer": disclaimer(spec),
    }


def _plain_check(value: float, threshold: float) -> dict:
    passed = value >= threshold
    out = {"pass": passed, "value": round(value, 1), "threshold": threshold}
    if not passed:
        out["short"] = round(threshold - value, 1)
    return out


def disclaimer(spec: dict) -> str:
    return (
        "PARTIAL PRE-SCREEN — NOT an eligibility decision. This tool models only the "
        "point-total and item-1/item-2 article minimums that are computable from a "
        f"publication list for {spec['table']} ({spec['name_tr']}); it does NOT model the "
        "other mandatory minimums listed in summary.unmodelled_minimums (thesis-derived "
        "publication, citation, scientific meeting, teaching, books or field-specific "
        "requirements where they apply, and caps for work not entered). It therefore NEVER "
        f"returns 'ELIGIBLE'. The bundled criteria are ÜAK's {TERM} tables (transcribed "
        f"{TABLE_LAST_VERIFIED}); ÜAK republishes them each term and they differ per temel alan "
        f"— verify the full table for your field and term at {UAK_PAGE} before relying on "
        "anything here. The official doçentlik decision is the jury's, not this tool's."
    )


# --------------------------------------------------------------------------- #
# I/O                                                                           #
# --------------------------------------------------------------------------- #

def load_input(arg: str) -> dict:
    if arg == "-":
        raw = sys.stdin.read()
    else:
        try:
            with open(arg, "r", encoding="utf-8") as fh:
                raw = fh.read()
        except OSError:
            raw = arg  # treat the argument itself as inline JSON
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"input is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("input JSON must be an object with a 'publications' list")
    return data


def list_alanlar() -> str:
    lines = [f"ÜAK doçentlik criteria bundled here: {TERM} term, transcribed {TABLE_LAST_VERIFIED}"]
    for code, spec in FIELDS.items():
        lines.append(f"  {code:15} {spec['table']:9} {spec['name_tr']} — share rule: {spec['share']}"
                     + (" — needs --bilim-alani" if spec.get("bilim_alani_thresholds") else ""))
    lines.append(f"Live source: {UAK_PAGE}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=("PARTIAL pre-screen of a publication list against the ÜAK doçentlik "
                     f"criteria ({TERM}, all 12 temel alanlar). Never emits an ELIGIBLE verdict."))
    parser.add_argument("input", nargs="?", help="JSON file, '-' for stdin, or inline JSON")
    parser.add_argument("--alan", "--field", dest="alan", default=None,
                        help="ÜAK temel alan code or name (default: the input's 'alan'/'field', "
                             "else saglik). See --list-alanlar.")
    parser.add_argument("--bilim-alani", dest="bilim_alani", default=None,
                        help="bilim alanı (required for fen; tailors field-specific checks)")
    parser.add_argument("--table", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--out", default=None, help="write report JSON to this path")
    parser.add_argument("--list-alanlar", action="store_true", help="list the bundled tables")
    parser.add_argument("--self-test", action="store_true",
                        help="run offline worked cases for every bundled table and exit")
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()
    if args.list_alanlar:
        print(list_alanlar())
        return 0
    if args.table:
        print("error: --table is no longer supported — all 12 ÜAK temel alan tables of the "
              f"{TERM} term are bundled. For another term, verify the new PDFs at {UAK_PAGE} "
              "and update FIELDS.", file=sys.stderr)
        return 2
    if args.input is None:
        parser.error("provide an input JSON (file, '-' or inline), or use --self-test")

    try:
        data = load_input(args.input)
        raw_alan = args.alan or data.get("alan") or data.get("field") or "saglik"
        code = resolve_alan(raw_alan)
        bilim_alani = args.bilim_alani or data.get("bilim_alani")
        report = build_report(data, code, bilim_alani)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(payload + "\n")
        print(f"wrote {args.out} — {report['table']} {report['alan']}: "
              f"{report['summary']['verdict']}")
    else:
        print(payload)
    return 0


# --------------------------------------------------------------------------- #
# Self-test: one or more hand-computed worked cases per bundled table           #
# --------------------------------------------------------------------------- #

def _p(index, authors=1, lead=False, post_doc=True, **extra):
    return {"title": f"{index}-{authors}", "index": index, "authors": authors,
            "is_lead": lead, "post_doc": post_doc, **extra}


def _o(item, points, post_doc_points=None):
    e = {"item": item, "points": points}
    if post_doc_points is not None:
        e["post_doc_points"] = post_doc_points
    return e


# Each case: (name, alan, bilim_alani, input, expected verdict, {check: expected}).
# An expected value is a number (the check's value) or a bool (its pass flag) or a
# (value, pass) tuple; "total"/"post_doc" refer to the two point-total checks.
SELF_TEST_CASES = [
    # Sağlık TABLO 10 — v2.1 behaviour. A 15 (30x0.5), B 20, C 12 (15x0.8), D 5 (10x0.5),
    # E 5 (ESCI 10x0.5), F 5 (TR Dizin, pre-doc), G 20 (AHCI). Total 82, post-doc 77,
    # item-1 post-doc 77, lead 1a post-doc A,B,C,D = 4.
    ("saglik-v21", "saglik", None,
     {"publications": [_p("Q1", 3, True), _p("Q2"), _p("Q3", 2, True), _p("Q4", 4, True),
                       _p("ESCI", 2), _p("TRDizin", 2, post_doc=False), _p("AHCI")]},
     VERDICT_FAIL, {"total": (82.0, False), "post_doc": (77.0, False),
                    "intl_article_ge_40": (77.0, True), "lead_q_articles_ge_3": (4, True)}),
    # Same list + other_items: item 4 = 25 -> cap 20; item 5 = 8; item 3a = 20 (0 post-doc).
    # Total 82+20+8+20 = 130; post-doc 77+20+8 = 105.
    ("saglik-with-other-items", "saglik", None,
     {"publications": [_p("Q1", 3, True), _p("Q2"), _p("Q3", 2, True), _p("Q4", 4, True),
                       _p("ESCI", 2), _p("TRDizin", 2, post_doc=False), _p("AHCI")],
      "other_items": [_o(4, 25, 25), _o(5, 8, 8), _o("3a", 20, 20)]},
     VERDICT_PASS, {"total": (130.0, True), "post_doc": (105.0, True)}),
    # Eğitim TABLO 1 (equal split): Q2/2 = 10, Q3 15, Q4 10, TR 10, OtherNational/2 = 2 -> 47.
    # Other: 4a 20, 7 = 20 -> cap 15, 5 = 10, 8 = 6, 9 = 2, 3d = 8 (not post-doc).
    # Total 47+20+15+10+6+2+8 = 108; post-doc 100; Q1-Q3 floor 10+15 = 25 < 30.
    ("egitim-q4-excluded", "egitim", None,
     {"publications": [_p("Q2", 2), _p("Q3"), _p("Q4"), _p("TRDizin"), _p("OtherNational", 2)],
      "other_items": [_o("4a", 20, 20), _o(7, 20, 20), _o(5, 10, 10), _o(8, 6, 6), _o(9, 2, 2),
                      _o("3d", 8, 8)]},
     VERDICT_FAIL, {"total": (108.0, True), "post_doc": (100.0, True),
                    "intl_q1_q3_points_ge_30": (25.0, False), "national_pubs_ge_2": (2, True),
                    "national_trdizin_ge_1": (1, True)}),
    # Fen TABLO 2, Matematik (20): Q1/3 claimed lead as first author -> rejected -> 30x0.25 =
    # 7.5; Q2/2 advisor lead 16; Q3/5 no başlıca yazar -> 15/5 = 3; ESCI/2 non-lead 5; TR 10.
    # Item-1 post-doc 31.5 (Q1-Q3 alone 26.5); lead Q1-Q3 = 1; TR 10; total 41.5.
    ("fen-matematik", "fen", "Matematik",
     {"publications": [_p("Q1", 3, True, lead_basis="first"), _p("Q2", 2, True, lead_basis="advisor"),
                       _p("Q3", 5, has_lead=False), _p("ESCI", 2), _p("TRDizin")]},
     VERDICT_FAIL, {"total": (41.5, False), "intl_points_ge_20": (31.5, True),
                    "lead_q1_q3_articles_ge_1": (1, True), "trdizin_points_ge_10": (10.0, True)}),
    # Same list, Fizik (40): item-1 31.5 < 40.
    ("fen-fizik", "fen", "Fizik",
     {"publications": [_p("Q1", 3, True, lead_basis="first"), _p("Q2", 2, True, lead_basis="advisor"),
                       _p("Q3", 5, has_lead=False), _p("ESCI", 2), _p("TRDizin")]},
     VERDICT_FAIL, {"intl_points_ge_40": (31.5, False)}),
    # Filoloji TABLO 3: 5 single TR (50) + TR/2 (5) + 2 single OtherNational (8) + AHCI 20 = 83.
    # National: 6 TR, 5 single, item-2 points 63 -> primary passes. Other: 4a 20 + (4c 20 +
    # 4d 15 -> c/d cap 30) = 50 (no item-4 cap in Filoloji); 5 = 12 -> 10; 8 = 5; 9 = 2;
    # 3g = 5 (not post-doc). Total 83+50+10+5+2+5 = 155; post-doc 150.
    ("filoloji-primary", "filoloji", None,
     {"publications": [_p("TRDizin")] * 5 + [_p("TRDizin", 2), _p("OtherNational"),
                                             _p("OtherNational"), _p("AHCI")],
      "other_items": [_o("4a", 20, 20), _o("4c", 20, 20), _o("4d", 15, 15), _o(5, 12, 12),
                      _o(8, 5, 5), _o(9, 2, 2), _o("3g", 5, 5)]},
     VERDICT_PASS, {"total": (155.0, True), "post_doc": (150.0, True), "national_articles": True}),
    # Hukuk TABLO 5: 3 single TR (30) -> primary fails; alternative (any date): Q2 single
    # pre-doc 20, Scopus/2 5, AHCI 20, OtherIntl 5 -> 3 pubs in 1a-1c, 2 single, item-1 50.
    # Passes via the alternative with two interpretation flags. Total 80, post-doc 60.
    ("hukuk-alternative", "hukuk", None,
     {"publications": [_p("TRDizin")] * 3 + [_p("Q2", post_doc=False), _p("Scopus", 2),
                                             _p("AHCI"), _p("OtherIntl")]},
     VERDICT_FAIL, {"total": (80.0, False), "post_doc": (60.0, False), "national_articles": True,
                    "_flags": 2}),
    # İlahiyat TABLO 6: 4 single TR (40) + TR/2 (5): 5 TR, 4 single, item-2 45 < 50 -> primary
    # fails; alternative: one ESCI/2 (5) < 2 publications -> fails. Other: 13 = 25 -> cap 20;
    # 14 = 10. Total 50+20+10 = 80.
    ("ilahiyat-national-fails", "ilahiyat", None,
     {"publications": [_p("TRDizin")] * 4 + [_p("TRDizin", 2), _p("ESCI", 2)],
      "other_items": [_o(13, 25, 25), _o(14, 10, 10)]},
     VERDICT_FAIL, {"total": (80.0, False), "national_articles": False}),
    # Güzel Sanatlar TABLO 4: ESCI 10 (1a-1d = 10), IntlNote 3 (excluded), TR/2 5, TR single
    # pre-doc 10 -> no single-author post-doc TR. Other: 13 = 12 -> cap 10. Total 38, post-doc 28.
    ("guzel-sanatlar", "guzel_sanatlar", None,
     {"publications": [_p("ESCI"), _p("IntlNote"), _p("TRDizin", 2), _p("TRDizin", post_doc=False)],
      "other_items": [_o(13, 12, 12)]},
     VERDICT_FAIL, {"total": (38.0, False), "post_doc": (28.0, False),
                    "intl_points_a_to_d_ge_10": (10.0, True),
                    "trdizin_single_author_ge_1": (0, False)}),
    # Mimarlık TABLO 8: Q3/2 lead (first) 12, ESCI/3 non-lead 2.5, OtherIntl 5, IntlNote/2 1.5,
    # TR/2 non-lead 5, TR/4 no başlıca yazar 2.5. Item-1 21 (1a-1c alone 14.5 -> flag), lead
    # 1a-1c = 1, TR 7.5 < 10. Other: 13 = 30 (no cap), 7 = 35 -> 30, 14 = 5. Total 93.5.
    ("mimarlik", "mimarlik", None,
     {"publications": [_p("Q3", 2, True, lead_basis="first"), _p("ESCI", 3), _p("OtherIntl"),
                       _p("IntlNote", 2), _p("TRDizin", 2), _p("TRDizin", 4, has_lead=False)],
      "other_items": [_o(13, 30, 30), _o(7, 35, 35), _o(14, 5, 5)]},
     VERDICT_FAIL, {"total": (93.5, False), "intl_points_ge_20": (21.0, True),
                    "lead_intl_a_to_c_articles_ge_1": (1, True),
                    "trdizin_points_ge_10": (7.5, False), "_flags": 1}),
    # Mühendislik TABLO 9: Q1 30, Q2/2 advisor 16, Q4/3 non-lead 2.5, TR 10 -> 58.5.
    # Other: 7 = 30, 5 = 10, 8 = 5, 9 = 2 -> total 105.5; item-1 48.5, lead Q1-Q3 = 2.
    ("muhendislik", "muhendislik", None,
     {"publications": [_p("Q1"), _p("Q2", 2, True, lead_basis="advisor"), _p("Q4", 3), _p("TRDizin")],
      "other_items": [_o(7, 30, 30), _o(5, 10, 10), _o(8, 5, 5), _o(9, 2, 2)]},
     VERDICT_PASS, {"total": (105.5, True), "intl_points_ge_40": (48.5, True),
                    "lead_q1_q3_articles_ge_1": (2, True), "trdizin_points_ge_10": (10.0, True)}),
    # Sosyal TABLO 11 (İletişim Çalışmaları): Q3/2 7.5, ESCI 10, 3 single TR 30, 2 TR/2 10,
    # OtherNational 4 -> 61.5. 1a-1d = 17.5; 5 TR, 3 single. Other: 4b 10 + 4d 3 = 13; 5 = 6;
    # 8 = 8; 9 = 2; 13d 10 + 13a 5 = 15; 3d = 8 (not post-doc). Total 113.5; post-doc 105.5.
    ("sosyal-iletisim", "sosyal", "İletişim Çalışmaları",
     {"publications": [_p("Q3", 2), _p("ESCI")] + [_p("TRDizin")] * 3
      + [_p("TRDizin", 2), _p("TRDizin", 2), _p("OtherNational")],
      "other_items": [_o("4b", 10, 10), _o("4d", 3, 3), _o(5, 6, 6), _o(8, 8, 8), _o(9, 2, 2),
                      _o("13d", 10, 10), _o("13a", 5, 5), _o("3d", 8, 8)]},
     VERDICT_PASS, {"total": (113.5, True), "post_doc": (105.5, True),
                    "intl_points_a_to_d_ge_10": (17.5, True), "national_articles": True,
                    "_manual": "iletisim_item13_cde"}),
    # Sosyal alternative route: 2 TR -> primary fails; Q2 20, AHCI/2 10, Q4/2 5 = three 1a/1b
    # publications, one single -> passes; ESCI does not count for this route. Total 65.
    ("sosyal-alternative", "sosyal", None,
     {"publications": [_p("Q2"), _p("AHCI", 2), _p("Q4", 2), _p("ESCI"), _p("TRDizin"), _p("TRDizin")]},
     VERDICT_FAIL, {"total": (65.0, False), "intl_points_a_to_d_ge_10": (45.0, True),
                    "national_articles": True}),
    # Spor TABLO 13: SPORTDiscus 10, Q2/3 lead 10, AHCI/2 non-lead 10, TR 10, TR/2 lead 8,
    # NationalNote 2. Item-1 30 (1a-1b alone 20 -> flag); lead 1a/1b = 1; item-2 pubs 3, TR 2.
    ("spor", "spor", None,
     {"publications": [_p("SPORTDiscus"), _p("Q2", 3, True, lead_basis="first"), _p("AHCI", 2),
                       _p("TRDizin"), _p("TRDizin", 2, True), _p("NationalNote")]},
     VERDICT_FAIL, {"total": (50.0, False), "intl_points_ge_30": (30.0, True),
                    "lead_1a_1b_articles_ge_1": (1, True), "national_pubs_ge_3": (3, True),
                    "national_trdizin_ge_2": (2, True), "_flags": 1}),
    # Ziraat TABLO 12: Q4 10 + Q4 10 + Q3/2 non-lead 7.5 + Q3/3 no başlıca yazar 5 = 32.5 (1a);
    # TR 10 + TR/2 5 = 15 < 20; no lead Q1-Q3 article. Other: 7 = 70 -> cap 60. Total 107.5.
    ("ziraat", "ziraat", None,
     {"publications": [_p("Q4"), _p("Q4"), _p("Q3", 2), _p("Q3", 3, has_lead=False), _p("TRDizin"),
                       _p("TRDizin", 2)],
      "other_items": [_o(7, 70, 70)]},
     VERDICT_FAIL, {"total": (107.5, True), "intl_1a_points_ge_30": (32.5, True),
                    "intl_points_ge_20": (32.5, True), "lead_q1_q3_articles_ge_1": (0, False),
                    "trdizin_points_ge_20": (15.0, False), "_flags": 1}),
]


def run_self_test() -> int:
    ok = True

    def report_line(passed: bool, label: str) -> None:
        nonlocal ok
        ok = ok and passed
        print(f"[{'PASS' if passed else 'FAIL'}] {label}")

    # Author-share factors (both rules).
    expect = [
        (("equal", "article", 3, False), 1 / 3), (("lead", "article", 1, False), 1.0),
        (("lead", "article", 2, True), 0.8), (("lead", "article", 2, False), 0.5),
        (("lead", "article", 3, True), 0.5), (("lead", "article", 3, False), 0.25),
        (("lead", "article", 4, False), 0.5 / 3), (("lead", "note", 3, True), 1 / 3),
    ]
    for args, want in expect:
        got, _ = share_factor(*args)
        report_line(abs(got - want) < 1e-9, f"share_factor{args} = {want:.4f}")
    got, _ = share_factor("lead", "article", 4, False, has_lead=False)
    report_line(abs(got - 0.25) < 1e-9, "share_factor lead, 4 authors, no başlıca yazar = 0.25")

    # Refusals: unknown field, Fen without bilim alanı, articles in other_items.
    for label, fn in [
        ("unknown alan refused", lambda: resolve_alan("Konservatuvar")),
        ("fen without bilim alanı refused", lambda: build_report({"publications": []}, "fen", None)),
        ("item 1 in other_items refused",
         lambda: build_report({"publications": [], "other_items": [_o(1, 5, 5)]}, "sosyal", None)),
    ]:
        try:
            fn()
            report_line(False, label)
        except ValueError as exc:
            report_line(UAK_PAGE in str(exc) or "publications" in str(exc), label)
    report_line(resolve_alan("Sosyal, Beşeri ve İdari Bilimler") == "sosyal"
                and resolve_alan("MİMARLIK") == "mimarlik"
                and resolve_alan("Sağlık Bilimleri") == "saglik", "alan aliases resolve")
    rep = build_report({"publications": [_p("SPORTDiscus"), _p("tr dizin")]}, "sosyal", None)
    report_line(rep["summary"]["unscored_count"] == 1 and rep["publications"][1]["index"] == "TRDizin",
                "SPORTDiscus unscored outside Spor; 'tr dizin' normalises to TRDizin")

    # Worked cases.
    for name, alan, bilim, data, want_verdict, want in SELF_TEST_CASES:
        rep = build_report(json.loads(json.dumps(data)), alan, bilim)
        summ = rep["summary"]
        good = summ["verdict"] == want_verdict and summ["verdict"] != "ELIGIBLE"
        detail = [f"verdict={summ['verdict']}"]
        for key, exp in want.items():
            if key == "_flags":
                got_n = len(summ["interpretation_flags"])
                good = good and got_n == exp
                detail.append(f"flags={got_n}")
                continue
            if key == "_manual":
                good = good and any(m["id"] == exp for m in summ["unmodelled_minimums"])
                continue
            cid = {"total": "total_ge_100", "post_doc": "post_doc_ge_90"}.get(key, key)
            chk = summ["checks"].get(cid)
            if chk is None:
                good = False
                detail.append(f"{cid}=missing")
                continue
            if isinstance(exp, tuple):
                val, want_pass = exp
                good = good and abs(float(chk["value"]) - val) < 1e-6 and chk["pass"] is want_pass
                detail.append(f"{cid}={chk['value']}/{chk['pass']}")
            elif isinstance(exp, bool):
                good = good and chk["pass"] is exp
                detail.append(f"{cid}={chk['pass']}")
        report_line(good, f"{name} ({FIELDS[alan]['table']}): " + ", ".join(detail))

    covered = {alan for _, alan, *_ in SELF_TEST_CASES}
    report_line(covered == set(FIELDS), f"worked cases cover all {len(FIELDS)} bundled tables")
    print("SELF-TEST", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
