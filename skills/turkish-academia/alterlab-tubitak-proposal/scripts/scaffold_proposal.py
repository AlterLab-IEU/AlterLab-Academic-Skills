#!/usr/bin/env python3
"""Scaffold and cap-check a TÜBİTAK ARDEB 1001 / 1002-A research proposal.

Two modes, both offline and dependency-free (Python standard library only):

  * **scaffold** (default) — emit the official ARDEB section tree for the chosen
    program, in the directorate's own Turkish heading order, with an English gloss, the
    evaluation criterion each section serves, and a short drafting brief per heading.
      - 1001: the official .doc form tree (Özet → 1 ÖZGÜN DEĞER → 2 YÖNTEM →
        3 PROJE YÖNETİMİ → 4 YAYGIN ETKİ → EK-1 → EK-2).
      - 1002-A: the PBS entry screens that replaced the .doc form (1 BİLİMSEL NİTELİK →
        2 YÖNTEM → 3 PROJE YÖNETİMİ → 4 ÇIKTI, ETKİ VE KAZANIMLAR → EK-1 → EK-2), each
        with the min–max word range from the 1002-A Başvuru İçeriği Bilgi Notu.

  * **--check FILE** — read an existing draft (Markdown) and report, advisory-only:
      - which required sections are missing,
      - word counts against each section's limits (1001: TR and EN özet ≤ 600 words;
        1002-A: the per-section min–max ranges),
      - whether any stated duration / budget exceeds the program ceiling,
      - whether a B Planı (contingency plan) is present.
    It never edits the draft and always restates the verify-current-call disclaimer,
    because every TRY figure / page limit / duration changes by call period.

The structure below is the official form tree (see ../references/form_structure.md). The
numeric caps were read from the live program pages on 2026-09-23 (see
../references/program_profiles.md). CAPS CHANGE BY PERIOD — confirm against the live program
page before submission.

Usage:
    uv run python scaffold_proposal.py --program 1001 --title "My project" --out scaffold.md
    uv run python scaffold_proposal.py --program 1002a --lang both
    uv run python scaffold_proposal.py --check scaffold.md --program 1001
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass

DISCLAIMER = (
    "VERIFY CURRENT CALL: every TRY figure, page limit, word range and duration below is dated "
    "and changes by call period. Before submission, fetch the live program page (and, for "
    "1002-A, the current Başvuru İçeriği Bilgi Notu) and reconcile. Values read on 2026-09-23: "
    "1001 caps from the 2026-1 period, 1002-A caps from 2026-02-01."
)

# Program ceilings — see ../references/program_profiles.md. Dated, period-specific.
PROGRAMS = {
    "1001": {
        "name": "1001 - Bilimsel ve Teknolojik Araştırma Projelerini Destekleme Programı",
        "gloss": "Support Programme for Scientific and Technological Research Projects",
        "max_months": 36,
        "budget_cap_try": 3_000_000,
        "budget_note": "burs dahil; PTİ ve kurum hissesi hariç; from the 2026-1 period",
        "window": "two calls a year (2026-2 closed on 14 Sep 2026)",
        "format_note": (
            "official .doc form, Arial 9, format unchanged, ≤ 25 pages excluding EK-1 and "
            "EK-2, one file ≤ 20 MB, no links to externally hosted content"
        ),
    },
    "1002a": {
        "name": "1002 - A Hızlı Destek Modülü",
        "gloss": "Fast Support Module",
        "max_months": 12,
        "budget_cap_try": 150_000,
        "budget_note": "per year, burs dahil, no PTİ; from 2026-02-01",
        "window": "rolling / year-round",
        "format_note": (
            "content typed into the PBS screens (no .doc template); the system generates the "
            "form, EK-1 and EK-2"
        ),
    },
}


@dataclass
class Section:
    key: str           # stable id for the structure check
    number: str        # e.g. "1.1", "EK-2"; "" = no printed number
    tr: str            # Turkish heading (directorate's own)
    en: str            # English gloss
    criterion: str     # evaluation criterion it mainly serves
    brief: str         # one-line drafting brief
    level: int = 2     # Markdown heading level in the scaffold (2 = ##, 3 = ###)
    min_words: int | None = None
    max_words: int | None = None
    markers: tuple[str, ...] = ()   # heading substrings for --check, most specific first


# 1001 — the official .doc form tree (../references/form_structure.md, Part A).
# ÖZET and ABSTRACT are two SEPARATE blocks on the form, each capped at 600 words.
SECTIONS_1001: list[Section] = [
    Section("ozet", "", "ÖZET (TR) + Anahtar Kelimeler",
            "Turkish abstract (≤600 words) + Turkish keywords", "Özgün Değer (%35)",
            "Cover özgün değer, yöntem, yönetim and yaygın etki; write it last.",
            max_words=600, markers=("özet (tr", "özet")),
    Section("abstract", "", "ABSTRACT (EN) + Keywords",
            "English abstract (≤600 words) + English keywords", "Özgün Değer (%35)",
            "Faithful English rendering of the ÖZET; counted separately.",
            max_words=600, markers=("abstract (en", "summary", "abstract")),
    Section("ozgun_deger", "1", "ÖZGÜN DEĞER", "Original value / significance",
            "Özgün Değer (%35)", "The most weighted block; this is where novelty is decided."),
    Section("konu_onemi", "1.1", "Konunun Önemi ve Projenin Özgün Değeri",
            "Importance of the topic & the project's original value", "Özgün Değer (%35)",
            "Critical literature review; name the gap and the conceptual/theoretical/"
            "methodological contribution; cite into EK-1.", level=3),
    Section("soru_hipotez", "1.2", "Araştırma Sorusu ve/veya Hipotezi",
            "Research question and/or hypothesis", "Özgün Değer (%35)",
            "Sharp, testable, tied to the aim.", level=3),
    Section("amac_hedefler", "1.3", "Amaç ve Hedefler", "Aim & objectives",
            "Özgün Değer (%35)",
            "One amaç; several MEASURABLE hedefler mapped onto work packages.", level=3),
    Section("yontem", "2", "YÖNTEM", "Method", "Yöntem (%25)",
            "Design, variables, instruments, analysis — each justified with references; "
            "carries yapılabilirlik (feasibility)."),
    Section("proje_yonetimi", "3", "PROJE YÖNETİMİ", "Project management",
            "Proje Yönetimi (%20)", "Work packages, timeline, risks, resources."),
    Section("is_paketleri", "3.1", "Yönetim Düzeni: İş-Zaman Çizelgesi ve İş Paketleri",
            "Work–time chart & work packages (with a risk plan per risky İP)", "Proje Yönetimi (%20)",
            "İP table: hedef, tasks, people, Başarı Ölçütü, Ara Çıktılar, Risk Yönetimi with a "
            "B Planı; önem % totals 100; no literature-review/reporting/article-writing/"
            "procurement İPs.", level=3),
    Section("olanaklar", "3.2", "Araştırma Olanakları", "Research facilities/resources",
            "Proje Yönetimi (%20)", "Infrastructure/equipment and what each is used for.",
            level=3),
    Section("yaygin_etki", "4", "YAYGIN ETKİ", "Broader impact / dissemination",
            "Yaygın Etki (%20)",
            "Populate ALL three sub-parts; thin yaygın etki is a common weakness."),
    Section("ciktilar", "4.1", "Öngörülen Çıktılar", "Expected outputs", "Yaygın Etki (%20)",
            "Scientific/academic, economic/commercial/social, researcher-training outputs "
            "with timing.", level=3),
    Section("etkiler", "4.2", "Öngörülen Etkiler", "Expected impacts", "Yaygın Etki (%20)",
            "Application areas, end users, socio-economic/cultural contribution; link to "
            "the On İkinci Kalkınma Planı where relevant.", level=3),
    Section("yayilim", "4.3",
            "Proje Sonuçlarının Yayılımı ve Bilim İletişimi Kapsamında Gerçekleştirilecek "
            "Faaliyet Planı",
            "Dissemination & science-communication plan", "Yaygın Etki (%20)",
            "Hedef kitle, hedefler ve kazanımlar, araçlar, zamanlama.", level=3),
    Section("kaynaklar", "EK-1", "Kaynaklar", "References", "Özgün Değer (%35)",
            "Cited literature; existence-check with alterlab-citation-verifier first."),
    Section("butce", "EK-2", "Bütçe ve Gerekçesi", "Budget & justification",
            "Proje Yönetimi (%20)",
            "Official EK-2 table; every line tied to a work package; respect the cap."),
]

# 1002-A — the PBS entry steps (../references/form_structure.md, Part B), with the word
# ranges from the 1002-A Hızlı Destek Modülü Başvuru İçeriği Bilgi Notu (dated 2025-12).
SECTIONS_1002A: list[Section] = [
    Section("bilimsel_nitelik", "1", "BİLİMSEL NİTELİK", "Scientific quality",
            "Bilimsel Nitelik", "Two PBS text fields follow."),
    Section("konu_onemi", "", "Konunun Önemi ve Projenin Bilimsel Niteliği",
            "Importance of the topic & scientific quality (1,000–3,500 words)",
            "Bilimsel Nitelik",
            "Scope, limits, importance; the literature gap and how the project closes it; "
            "research question and hypotheses.", level=3, min_words=1000, max_words=3500),
    Section("amac_hedefler", "", "Amaç ve Hedefler",
            "Aim & objectives (100–1,000 words)", "Bilimsel Nitelik",
            "Clear, measurable, realistic, achievable within ≤ 12 months.",
            level=3, min_words=100, max_words=1000),
    Section("yontem", "2", "YÖNTEM", "Method (750–3,000 words)", "Bilimsel Nitelik",
            "Methods and techniques with references; design, variables, statistics.",
            min_words=750, max_words=3000),
    Section("proje_yonetimi", "3", "PROJE YÖNETİMİ (İş Paketleri adımı)",
            "Project management — built from the PBS work-package step", "Proje Yönetimi",
            "Per İP: who/when, Başarı Ölçütü, önem % totalling 100, risks with a B Planı; "
            "no literature-review/reporting/article-writing/procurement İPs."),
    Section("cikti_etki", "4", "ÇIKTI, ETKİ VE KAZANIMLAR",
            "Outputs, impacts and gains (100–400 words)", "Çıktı, Etki ve Kazanımlar",
            "Outputs, impacts, gains, and who benefits how.",
            min_words=100, max_words=400),
    Section("diger", "", "Belirtmek İstediğiniz Diğer Konular",
            "Other remarks (optional, ≤ 250 words)", "—",
            "Only material that helps the evaluation; may be left empty.", max_words=250),
    Section("kaynaklar", "EK-1", "Kaynakça", "References (PBS 'Kaynakça' step)",
            "Bilimsel Nitelik",
            "Every source cited in the text; DOI mandatory where one exists."),
    Section("butce", "EK-2", "Bütçe ve Gerekçesi", "Budget & justification (PBS budget steps)",
            "Proje Yönetimi",
            "Justify every line; total = Önerilen Destek Miktarı; no foreign travel."),
]

SECTIONS = {"1001": SECTIONS_1001, "1002a": SECTIONS_1002A}
OPTIONAL_KEYS = {"diger"}   # may legitimately be absent from a draft


def _limits(sec: Section) -> str:
    if sec.min_words and sec.max_words:
        return f"{sec.min_words:,}–{sec.max_words:,} words"
    if sec.max_words:
        return f"≤ {sec.max_words:,} words"
    return ""


def build_scaffold(program: str, title: str, lang: str) -> str:
    p = PROGRAMS[program]
    out: list[str] = []
    out.append(f"# {p['name']}")
    out.append(f"<!-- {p['gloss']} -->")
    if title:
        out.append("")
        out.append(f"**Proje Başlığı / Project Title:** {title}")
    out.append("")
    out.append(f"> {DISCLAIMER}")
    out.append("")
    out.append(
        f"> Program caps (verify): duration ≤ {p['max_months']} months; "
        f"budget ≤ {p['budget_cap_try']:,} TRY ({p['budget_note']}); "
        f"window: {p['window']}; format: {p['format_note']}."
    )
    out.append("")
    for sec in SECTIONS[program]:
        prefix = f"{sec.number}. " if sec.number else ""
        if lang == "en":
            heading = f"{prefix}{sec.en}"
        elif lang == "both":
            heading = f"{prefix}{sec.tr} — {sec.en}"
        else:  # tr (default)
            heading = f"{prefix}{sec.tr}"
        out.append(f"{'#' * sec.level} {heading}")
        out.append(f"<!-- criterion: {sec.criterion} -->")
        limits = _limits(sec)
        out.append(f"<!-- brief: {sec.brief}{' Limit: ' + limits + '.' if limits else ''} -->")
        out.append("")
        out.append("_…_")
        out.append("")
    out.append("---")
    if program == "1001":
        out.append(
            "EK-3 (Proje Ekibinin Diğer Projeleri ve Güncel Yayınları) is generated by PBS from "
            "the entered data — keep the team's ARBİS records current."
        )
    out.append(
        "AI-use disclosure: if generative AI drafted or substantially shaped any section, "
        "declare the tool/version, the sections and the nature of use in the PBS section "
        "provided (TÜBİTAK ÜYZ Rehberi, Eylül 2025)."
    )
    out.append(
        "Handoffs: data plan (Veri Yönetim Planı) → alterlab-kvkk-dmp / alterlab-aperta; ethics → "
        "alterlab-tr-research-ethics; reference existence → alterlab-citation-verifier; "
        "generic grant-craft & Gantt → alterlab-research-grants."
    )
    return "\n".join(out) + "\n"


# ---- structure / cap check -------------------------------------------------

_WORD_RE = re.compile(r"\b[\wçğıöşüÇĞİÖŞÜ’'-]+\b", re.UNICODE)
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_PLACEHOLDER_RE = re.compile(r"^\s*_…_\s*$", re.MULTILINE)


def _word_count(text: str) -> int:
    # Don't count scaffold annotations (<!-- brief/criterion -->) or the _…_ placeholder
    # toward a word limit — only the researcher's own prose counts.
    text = _COMMENT_RE.sub(" ", text)
    text = _PLACEHOLDER_RE.sub(" ", text)
    return len(_WORD_RE.findall(text))


def _extract_block(body: str, *markers: str) -> str | None:
    """Text under the first heading containing a marker, up to the next heading.

    Markers are tried in order (most specific first), so a bilingual heading such as
    "ÖZET (TR) … Turkish abstract" is not mistaken for the English ABSTRACT block.
    Returns None when no such heading exists (as opposed to "" for an empty section).
    """
    lines = body.splitlines()
    start = None
    for m in markers:
        for i, ln in enumerate(lines):
            if ln.lstrip().startswith("#") and m.lower() in ln.lower():
                start = i + 1
                break
        if start is not None:
            break
    if start is None:
        return None
    chunk: list[str] = []
    for ln in lines[start:]:
        if ln.lstrip().startswith("#"):
            break
        chunk.append(ln)
    return "\n".join(chunk).strip()


def _markers(sec: Section) -> tuple[str, ...]:
    # Explicit markers, else a short distinctive substring of the Turkish heading.
    return sec.markers or (sec.tr.split("(")[0].strip().lower()[:18],)


def check_draft(path: str, program: str) -> dict:
    p = PROGRAMS[program]
    with open(path, encoding="utf-8") as fh:
        body = fh.read()
    # Content checks ignore the scaffold's own <!-- brief --> annotations.
    low = _COMMENT_RE.sub(" ", body).lower()

    findings: list[dict] = []

    # 1) required sections present?
    missing: list[str] = []
    for sec in SECTIONS[program]:
        if sec.key in OPTIONAL_KEYS:
            continue
        if not any(m in low for m in _markers(sec)):
            missing.append(f"{sec.number}. {sec.tr}" if sec.number else sec.tr)
    if missing:
        findings.append({"level": "warn", "code": "missing-sections",
                         "detail": f"{len(missing)} required section(s) not found: "
                                   + "; ".join(missing)})

    # 2) word limits per section (1001: özet/abstract ≤ 600; 1002-A: min–max ranges)
    for sec in SECTIONS[program]:
        if sec.max_words is None:
            continue
        block = _extract_block(body, *_markers(sec))
        if block is None:
            continue  # already reported as missing (or optional)
        wc = _word_count(block)
        if wc == 0 and sec.key in OPTIONAL_KEYS:
            continue
        too_long = wc > sec.max_words
        too_short = sec.min_words is not None and 0 < wc < sec.min_words
        level = "fail" if too_long or too_short else "ok"
        if wc == 0:
            level = "warn"
        findings.append({"level": level, "code": f"words-{sec.key}",
                         "detail": f"{sec.tr}: {wc} words (limit {_limits(sec)})"})

    # 3) duration / budget statements over the ceiling (best-effort; advisory)
    for m in re.finditer(r"(\d{1,3})\s*(?:ay|months?)\b", low):
        months = int(m.group(1))
        if months > p["max_months"]:
            findings.append({"level": "fail", "code": "duration-over",
                             "detail": f"Stated {months} months exceeds the "
                                       f"{p['max_months']}-month ceiling."})
            break
    for m in re.finditer(r"([\d][\d.,]{4,})\s*(?:try|tl|₺)\b", low):
        digits = re.sub(r"[.,]", "", m.group(1))
        if digits.isdigit() and int(digits) > p["budget_cap_try"]:
            findings.append({"level": "fail", "code": "budget-over",
                             "detail": f"Stated {int(digits):,} TRY exceeds the "
                                       f"{p['budget_cap_try']:,} TRY ceiling "
                                       f"({p['budget_note']})."})
            break

    # 4) B Planı present?
    if not re.search(r"\bb[\s-]?plan", low):
        findings.append({"level": "warn", "code": "b-plani-missing",
                         "detail": "No B Planı (contingency plan) detected for the work "
                                   "packages — add one for each risky İP."})

    # 5) format reminder (page limits cannot be measured from Markdown)
    findings.append({"level": "info", "code": "format",
                     "detail": f"Format: {p['format_note']} — confirm in the final form."})

    levels = [f["level"] for f in findings]
    verdict = "FAIL" if "fail" in levels else ("REVIEW" if "warn" in levels else "OK")
    return {
        "tool": "alterlab-tubitak-proposal/scaffold_proposal.py",
        "program": p["name"],
        "verdict": verdict,
        "disclaimer": DISCLAIMER,
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--program", choices=["1001", "1002a"], default="1001",
                    help="ARDEB program variant (default: 1001)")
    ap.add_argument("--title", default="", help="Project title to stamp into the scaffold")
    ap.add_argument("--lang", choices=["tr", "en", "both"], default="tr",
                    help="Heading language (default: tr)")
    ap.add_argument("--out", help="Write the scaffold to this path (default: stdout)")
    ap.add_argument("--check", metavar="FILE",
                    help="Check an existing draft against the form structure and caps")
    ap.add_argument("--json", action="store_true", help="(--check) print JSON instead of text")
    args = ap.parse_args(argv)

    if args.check:
        report = check_draft(args.check, args.program)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"# Structure check — {report['program']}")
            print(f"Verdict: {report['verdict']}\n")
            for f in report["findings"]:
                print(f"  [{f['level'].upper()}] {f['code']}: {f['detail']}")
            print(f"\n{report['disclaimer']}")
        return 1 if report["verdict"] == "FAIL" else 0

    scaffold = build_scaffold(args.program, args.title, args.lang)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(scaffold)
        print(f"Wrote {args.program} scaffold to {args.out}")
    else:
        sys.stdout.write(scaffold)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
