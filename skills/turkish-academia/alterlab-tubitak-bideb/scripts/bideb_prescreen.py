#!/usr/bin/env python3
"""PARTIAL eligibility pre-screen and call-timing helper for TÜBİTAK BİDEB programmes.

Offline, standard library only. Two modes:

  screen  Read a JSON applicant profile and check the COMPUTABLE hard gates of
          2218, 2219, 2232-A, 2232-B, 2236-A and 2224-A: dates, age, months spent in
          Türkiye, language score and Tablo 1 publication points. Each programme gets
          FAIL_GATE, NEEDS_INPUT or PASS_COMPUTABLE_VERIFY_REST -- never "eligible":
          invitations, host rankings, documents and panel scores cannot be computed, so
          every result lists what the applicant must still verify by hand.

  timing  Given a programme (2221, 2223b or 2224a) and a target date (guest arrival or
          event start), list the 2026 application periods and which of them can be used.

Every rule below was read from the live tubitak.gov.tr programme pages and call documents
on 2026-09-23 (see ../references/program_profiles.md). Rules change with each call:
re-check the live page before relying on any verdict.

Profile keys (JSON object; omit what you do not know -- a missing key that a gate needs
yields NEEDS_INPUT, never a guess):
  as_of                   ISO date the rules are applied on: the application date
                          (2232: the call opening day; 2236-A: the call deadline)
  citizenship             "TR" | "blue_card" | "other"
  doctorate_date          ISO date the doctorate / specialty / sanatta yeterlik was awarded
  doctorate_expected_within_12_months   bool (2218 only)
  defended_unconditionally_before_deadline  bool (2236-A only)
  birth_date              ISO date
  birth_extensions        int: births the call counts for its one-year-per-birth extension
                          for women applicants (2218 window, 2232-B age limit)
  language_score          ÖSYM-type score (YDS, e-YDS, YÖKDİL, e-YÖKDİL, TIPDİL or an
                          ÖSYM-accepted equivalent)
  foreign_language_degree bool: degree/education at a university teaching 100% in a
                          foreign language
  retired, employed_abroad, working_in_turkiye, tubitak_staff, phd_from_host,
  kadrolu_at_proposed_host, obligatory_service, previous_cocirculation_fellow,
  permanent_at_proposed_host, used_2224a_this_year, affiliated_or_resident_in_turkiye,
  private_sector_route, highly_cited_last_5_years            bools
  prior_2219_return_date  ISO date of return from an earlier 2219, or null
  months_in_turkiye_last_36   int
  senior_months_abroad    int: months full-time abroad after the PhD as faculty member,
                          team leader or independent researcher (2232-A)
  postdoc_months_abroad   int (2232-B)
  ranked_months_2232a     int: months in the last 5 years at institutions on the 2232-A lists
  ranked_months_2232b     int: months in the last 5 years at institutions on the 2232-B lists
  advisor_points_last_2y  int (2218);  host_exempt_from_advisor_points  bool (2218)
  outputs_cumulative      {item: count} as of the application date (2218 Tablo 1)
  outputs_last_3_calendar_years  {item: count} in the application year and the two
                          previous calendar years (2219 §5.3.5 and 2224-A Tablo 1)
                          items: wos_scopus_article, trdizin_article, book, book_chapter,
                          cpci_paper, intl_patent, national_patent
  role_2224a              "doctorate_researcher" | "employee_bachelor_plus" |
                          "grad_student_ales70" | "undergraduate"

Usage:
    uv run python bideb_prescreen.py screen profile.json [--programs 2218,2219] [--json]
    uv run python bideb_prescreen.py timing --program 2224a --date 2027-02-15 [--today 2026-09-23]
    uv run python bideb_prescreen.py --self-test
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import date

READ_ON = "2026-09-23"
DISCLAIMER = (
    "PARTIAL PRE-SCREEN, NOT AN ELIGIBILITY DECISION. Only date, age, residence, language "
    "and Tablo 1 gates are computed, from calls read on " + READ_ON + ". Invitations, host "
    "rankings, documents and panel scores decide the outcome; BİDEB's pre-screen and GYK "
    "decide eligibility. Re-check the live programme page before applying."
)
PAGE = "https://tubitak.gov.tr/tr/burslar/doktora-sonrasi/arastirma-burs-programlari/"
SOURCES = {
    "2218": PAGE + "2218-yurt-ici-doktora-sonrasi-arastirma-burs-programi (2026 call)",
    "2219": PAGE + "2219-yurt-disi-doktora-sonrasi-arastirma-burs-programi (2026 call)",
    "2232a": PAGE + "2232-uluslararasi-lider-arastirmacilar-programi (2025 call)",
    "2232b": PAGE + "2232-b-uluslararasi-genc-arastirmacilar-programi (2025 call)",
    "2236a": PAGE + "2236a-uluslararasi-deneyimli-arastirmaci-dolasimi-destek-programi (2025 call)",
    "2224a": "https://tubitak.gov.tr/tr/destekler/bilimsel-etkinlik/etkinliklere-katilma-destekleri/"
             "2224-yurt-disi-bilimsel-etkinliklere-katilimi-destekleme-programi (2026 call)",
    "2223b": "https://tubitak.gov.tr/tr/destekler/bilimsel-etkinlik/etkinlik-duzenleme-destekleri/"
             "2223-b-yurt-ici-bilimsel-etkinlik-duzenleme-destegi (2026 call)",
    "2221": PAGE + "2221-konuk-veya-akademik-izinli-sabbatical-bilim-insani-destekleme-p (2026)",
}
NAMES = {
    "2218": "2218 Yurt İçi Doktora Sonrası Araştırma Burs Programı",
    "2219": "2219 Yurt Dışı Doktora Sonrası Araştırma Burs Programı",
    "2232a": "2232-A Uluslararası Lider Araştırmacılar Programı",
    "2232b": "2232-B Uluslararası Genç Araştırmacılar Programı",
    "2236a": "2236-A Uluslararası Deneyimli Araştırmacı Dolaşım Programı (CoCirculation3)",
    "2224a": "2224-A Yurt Dışı Bilimsel Etkinliklere Katılımı Destekleme Programı",
}

# Tablo 1 point tables, exactly as printed in each call (points per item; caps in points).
POINTS_2218 = {"wos_scopus_article": 2, "trdizin_article": 1, "book": 2, "book_chapter": 1,
               "cpci_paper": 1, "intl_patent": 2, "national_patent": 1}
CAPS_2218 = {"book": 4, "book_chapter": 2}
POINTS_T1 = {"wos_scopus_article": 2, "trdizin_article": 1, "book": 2, "book_chapter": 1,
             "cpci_paper": 1}          # 2219 call §5.3.5 and 2224-A call Tablo 1
CAPS_T1 = {"book_chapter": 4}
THRESHOLDS_2224A = {"doctorate_researcher": 6, "employee_bachelor_plus": 3,
                    "grad_student_ales70": 3}

# 2026 application periods as published on the programme pages (close at 17:30).
PERIODS_2026 = {
    "2221": [("2026/1", "2026-02-02", "2026-03-02"), ("2026/2", "2026-05-04", "2026-06-08"),
             ("2026/3", "2026-08-03", "2026-08-31"), ("2026/4", "2026-11-02", "2026-11-30")],
    "2224a": [("2026/1", "2026-02-02", "2026-02-24"), ("2026/2", "2026-06-08", "2026-06-30"),
              ("2026/3", "2026-10-05", "2026-10-27")],
    "2223b": [("2026/1", "2026-02-02", "2026-02-24"), ("2026/2", "2026-06-08", "2026-06-30"),
              ("2026/3", "2026-10-05", "2026-10-27")],
}
TIMING_RULES = {
    "2221": "apply at the latest in the period before the guest arrives; the guest must then "
            "start within 6 months of the decision",
    "2224a": "apply at the latest in the period before the event; the event must start after "
             "that period's closing date",
    "2223b": "the event must start 60-270 days after the period's closing date",
}


@dataclass
class Gate:
    rule: str
    status: str          # pass | fail | missing | verify
    detail: str


@dataclass
class Result:
    programme: str
    name: str
    verdict: str = ""
    gates: list[Gate] = field(default_factory=list)
    verify: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    source: str = ""


# ---------------------------------------------------------------- helpers ----------

def parse_date(value: object) -> date | None:
    if value in (None, ""):
        return None
    return date.fromisoformat(str(value))


def add_years(d: date, years: int) -> date:
    try:
        return d.replace(year=d.year + years)
    except ValueError:              # 29 February in a non-leap target year
        return d.replace(year=d.year + years, day=28)


def table_points(counts: dict | None, points: dict, caps: dict) -> tuple[int | None, str]:
    if counts is None:
        return None, "no outputs supplied"
    unknown = sorted(set(counts) - set(points))
    total, parts = 0, []
    for key, per in points.items():
        n = int(counts.get(key, 0) or 0)
        if n < 0:
            raise ValueError(f"negative count for {key}")
        pts = min(n * per, caps[key]) if key in caps else n * per
        if n:
            capped = " (capped)" if key in caps and n * per > caps[key] else ""
            parts.append(f"{key} {n}x{per}={pts}{capped}")
        total += pts
    detail = ", ".join(parts) or "no scoring items"
    if unknown:
        detail += f"; ignored keys not in this table: {', '.join(unknown)}"
    return total, detail


def check(rule: str, ok: bool | None, detail: str) -> Gate:
    return Gate(rule, "missing" if ok is None else ("pass" if ok else "fail"), detail)


def flag_is(p: dict, key: str, expected: bool, rule: str, label: str) -> Gate:
    if key not in p or p[key] is None:
        return Gate(rule, "missing", f"{label}: provide `{key}`")
    return check(rule, bool(p[key]) is expected, f"{label}: {key}={bool(p[key])}")


def language_gate(p: dict, minimum: int, rule: str) -> Gate:
    score, degree = p.get("language_score"), p.get("foreign_language_degree")
    if degree:
        return Gate(rule, "pass", "degree/education at a 100% foreign-language university")
    if score is None:
        return Gate(rule, "missing", f"provide `language_score` (needs >= {minimum}) or "
                                     "`foreign_language_degree`")
    return check(rule, float(score) >= minimum, f"language score {score} (needs >= {minimum})")


def months_gate(p: dict, key: str, limit: int, rule: str, label: str) -> Gate:
    value = p.get(key)
    if value is None:
        return Gate(rule, "missing", f"provide `{key}` ({label})")
    return check(rule, int(value) <= limit, f"{label}: {value} months (limit {limit})")


def finish(res: Result) -> Result:
    statuses = {g.status for g in res.gates}
    if "fail" in statuses:
        res.verdict = "FAIL_GATE"
    elif "missing" in statuses:
        res.verdict = "NEEDS_INPUT"
    else:
        res.verdict = "PASS_COMPUTABLE_VERIFY_REST"
    res.verify += [g.detail for g in res.gates if g.status == "verify"]
    return res


# ------------------------------------------------------------- screeners -----------

def screen_2219(p: dict, as_of: date) -> Result:
    r = Result("2219", NAMES["2219"], source=SOURCES["2219"])
    cit = p.get("citizenship")
    r.gates.append(check("§4.1.1 T.C. citizen", None if cit is None else cit == "TR",
                         f"citizenship={cit}"))
    r.gates.append(check("§4.1.2 doctorate/specialty held",
                         None if p.get("doctorate_date") is None else True,
                         f"doctorate_date={p.get('doctorate_date')}"))
    ret = parse_date(p.get("prior_2219_return_date"))
    if ret is None:
        r.gates.append(Gate("§4.1.3 six years since return from a previous 2219", "pass",
                            "no previous 2219 declared"))
    else:
        free = add_years(ret, 6)
        r.gates.append(check("§4.1.3 six years since return from a previous 2219",
                             free <= as_of, f"returned {ret}; eligible again from {free}"))
    r.gates.append(language_gate(p, 65, "§4.1.5 foreign language"))
    r.gates.append(flag_is(p, "employed_abroad", False, "§4.1.6 not employed abroad", "abroad"))
    r.gates.append(flag_is(p, "retired", False, "§4.1.7 not retired", "retired"))
    r.gates.append(flag_is(p, "phd_from_host", False, "§4.1.8 doctorate not from the host",
                           "host"))
    r.gates.append(flag_is(p, "tubitak_staff", False, "§9.1.9 not TÜBİTAK Başkanlık staff",
                           "staff"))
    pts, detail = table_points(p.get("outputs_last_3_calendar_years"), POINTS_T1, CAPS_T1)
    if pts is not None:
        note = "a separate support threshold may apply (>= 8)" if pts >= 8 else "below 8"
        r.notes.append(f"§5.3.5 Tablo 1 (last 3 calendar years): {pts} points -- {note}; {detail}")
    r.verify += [
        "§4.1.4 invitation: host ranked in your field this year in QS/THE top 100 (university) "
        "or Scimago-Government top 250 (institute), OR host advisor CNCI/FWCI >= 1.00 -- "
        "evidence per the Kurum Sıralama ve Danışman Etki Değeri Ekleme Kılavuzu",
        "invitation letter content: month/year dates, topic, research language, letterhead, "
        "signature; one country, one institution",
        "§4.1.9 previous-period TÜBİMER objection completed; §4.1.10 no brand promotion",
        "call window: the 2026 call closed on 15 Sep 2026 at 17:30",
    ]
    return finish(r)


def screen_2218(p: dict, as_of: date) -> Result:
    r = Result("2218", NAMES["2218"], source=SOURCES["2218"])
    cit = p.get("citizenship")
    r.gates.append(check("§4.1.1 T.C. citizen or Mavi Kart",
                         None if cit is None else cit in ("TR", "blue_card"), f"citizenship={cit}"))
    phd = parse_date(p.get("doctorate_date"))
    ext = int(p.get("birth_extensions", 0) or 0)
    rule = "§4.1.2 within 7 years of the doctorate (+1 year per birth)"
    if phd is not None:
        deadline = add_years(phd, 7 + ext)
        gate = check(rule, as_of <= deadline, f"doctorate {phd}, window ends {deadline} "
                                              f"({ext} birth extension(s))")
        if abs((deadline - as_of).days) <= 31:
            gate.detail += " -- BORDERLINE, confirm the exact cut-off with bideb2218@tubitak.gov.tr"
        r.gates.append(gate)
    elif p.get("doctorate_expected_within_12_months"):
        r.gates.append(Gate(rule, "pass", "degree expected: it must be obtained within 12 "
                                          "months of the award date"))
    else:
        r.gates.append(Gate(rule, "missing", "provide `doctorate_date` or "
                                             "`doctorate_expected_within_12_months`"))
    r.gates.append(flag_is(p, "kadrolu_at_proposed_host", False,
                           "§4.1.4 not at the applicant's own kadro institution", "own employer"))
    r.gates.append(flag_is(p, "phd_from_host", False, "§4.1.5 doctorate not from the host",
                           "host"))
    r.gates.append(flag_is(p, "tubitak_staff", False, "TÜBİTAK staff cannot apply", "staff"))
    r.gates.append(language_gate(p, 70, "§4.1.11 foreign language"))
    pts, detail = table_points(p.get("outputs_cumulative"), POINTS_2218, CAPS_2218)
    r.gates.append(check("§4.1.9 applicant >= 5 Tablo 1 points (as of the application date)",
                         None if pts is None else pts >= 5, f"{pts} points: {detail}"))
    if p.get("host_exempt_from_advisor_points"):
        r.gates.append(Gate("§4.1.10 advisor >= 5 points in the last 2 years", "pass",
                            "host type exempts the advisor from Tablo 1"))
    else:
        adv = p.get("advisor_points_last_2y")
        r.gates.append(check("§4.1.10 advisor >= 5 points in the last 2 years",
                             None if adv is None else int(adv) >= 5, f"advisor points={adv}"))
    r.verify += [
        "§4.1.3 host type (university, 6550 infrastructure, public research institute, "
        "R&D/design-centre or technopark company)",
        "§4.1.6 invitation signed by the host's highest official; §4.1.7 employer permission",
        "advisor(s): at most 2, not your PhD advisor, first advisor from the host",
        "every counted output indexed in WoS/Scopus/TR Dizin by the application date",
        "call window: the 2026 call closed on 17 Aug 2026 at 17:30",
    ]
    return finish(r)


def screen_2232(p: dict, as_of: date, variant: str) -> Result:
    key = "2232a" if variant == "A" else "2232b"
    r = Result(key, NAMES[key], source=SOURCES[key])
    r.gates.append(months_gate(p, "months_in_turkiye_last_36", 12,
                               "§4.1 not in Türkiye > 1 year in the last 3 years",
                               "time in Türkiye, last 36 months"))
    r.gates.append(flag_is(p, "working_in_turkiye", False,
                           "§4.1 not working in Türkiye on the call opening day", "working"))
    r.gates.append(flag_is(p, "obligatory_service", False, "§4.1 no current obligatory service",
                           "obligatory service"))
    if variant == "B":
        birth = parse_date(p.get("birth_date"))
        ext = int(p.get("birth_extensions", 0) or 0)
        if birth is None:
            r.gates.append(Gate("§4.1.1 under 40 on the call opening day", "missing",
                                "provide `birth_date`"))
        else:
            limit = add_years(birth, 40 + ext)
            r.gates.append(check("§4.1.1 under 40 on the call opening day", as_of < limit,
                                 f"turns {40 + ext} on {limit} ({ext} birth extension(s))"))
    exp_rule = "§4.1 experience abroad"
    if p.get("private_sector_route"):
        r.gates.append(Gate(exp_rule, "verify", "private-sector route declared: verify the "
                            + ("6 years' research incl. >= 3 years private sector" if variant == "A"
                               else "4 years' research incl. >= 1 year private sector")
                            + " after a bachelor's abroad"))
    elif variant == "A":
        months = p.get("senior_months_abroad")
        r.gates.append(check(exp_rule, None if months is None else int(months) >= 36,
                             f"senior post-PhD months abroad={months} (needs >= 36)"))
    else:
        phd = parse_date(p.get("doctorate_date"))
        post = p.get("postdoc_months_abroad")
        if phd is None or post is None:
            r.gates.append(Gate(exp_rule, "missing",
                                "provide `doctorate_date` and `postdoc_months_abroad`"))
        else:
            recent = as_of <= add_years(phd, 4)
            r.gates.append(check(exp_rule, recent and int(post) >= 12,
                                 f"doctorate {phd} (within 4 years: {recent}); postdoc months "
                                 f"abroad={post} (needs >= 12)"))
    need = 30 if variant == "A" else 12
    ranked = p.get("ranked_months_2232a" if variant == "A" else "ranked_months_2232b")
    hcr = p.get("highly_cited_last_5_years")
    dist_rule = "§4.1 Highly Cited listing or ranked-institution months (last 5 years)"
    if hcr:
        r.gates.append(Gate(dist_rule, "pass", "Highly Cited Researchers listing declared"))
    elif ranked is None:
        r.gates.append(Gate(dist_rule, "missing", "provide `highly_cited_last_5_years` or the "
                            "ranked-institution months"))
    else:
        r.gates.append(check(dist_rule, int(ranked) >= need,
                             f"ranked-institution months={ranked} (needs >= {need})"))
    r.verify += [
        "each institution counted is on the call's lists (QS/THE subject top "
        + ("100" if variant == "A" else "150")
        + ", EC JRC top 2,500 R&D firms, Scimago top 250, unicorns, top 1,000 start-ups)",
        "rules are from the 2025 call; no 2026 call was on the page on " + READ_ON,
    ]
    return finish(r)


def screen_2236a(p: dict, as_of: date) -> Result:
    r = Result("2236a", NAMES["2236a"], source=SOURCES["2236a"])
    phd = parse_date(p.get("doctorate_date"))
    rule = "§4.1.2 doctorate by the call deadline"
    if p.get("defended_unconditionally_before_deadline"):
        r.gates.append(Gate(rule, "pass", "unconditional defence before the deadline declared"))
    else:
        r.gates.append(check(rule, None if phd is None else phd <= as_of,
                             f"doctorate_date={phd}, deadline={as_of}"))
    r.gates.append(months_gate(p, "months_in_turkiye_last_36", 12,
                               "§4.1.3 mobility rule (36 months before the deadline)",
                               "residence/main activity in Türkiye"))
    r.gates.append(flag_is(p, "permanent_at_proposed_host", False,
                           "not permanently employed at the proposed host", "permanent"))
    r.gates.append(flag_is(p, "previous_cocirculation_fellow", False,
                           "no earlier Co-Circulation/CoCirculation2 award", "previous fellow"))
    r.gates.append(flag_is(p, "obligatory_service", False,
                           "no obligatory-service duty (Turkish citizens)", "obligatory service"))
    r.verify += ["project fits the Green Deal focus", "supervisor and host chosen and willing",
                 "rules are from the 2025 call (closed 1 Dec 2025); no new call on " + READ_ON]
    return finish(r)


def screen_2224a(p: dict, as_of: date) -> Result:
    r = Result("2224a", NAMES["2224a"], source=SOURCES["2224a"])
    role = p.get("role_2224a")
    pts, detail = table_points(p.get("outputs_last_3_calendar_years"), POINTS_T1, CAPS_T1)
    rule = "§4.1.10 Tablo 1 points (application year + 2 previous calendar years)"
    if role == "undergraduate":
        r.gates.append(Gate(rule, "verify", "undergraduates need two of five GPA/fellowship/"
                                            "publication conditions -- check §4.1.10.1"))
    elif role not in THRESHOLDS_2224A:
        r.gates.append(Gate(rule, "missing", "provide `role_2224a`"))
    else:
        need = THRESHOLDS_2224A[role]
        r.gates.append(check(rule, None if pts is None else pts >= need,
                             f"{pts} points (needs >= {need} as {role}): {detail}"))
    r.gates.append(language_gate(p, 70, "§4.1.4 foreign language"))
    r.gates.append(flag_is(p, "used_2224a_this_year", False, "§4.1.5 not used 2224-A this year",
                           "used this year"))
    r.gates.append(flag_is(p, "affiliated_or_resident_in_turkiye", True,
                           "§4.1.7 Turkish affiliation or residence", "affiliated/resident"))
    r.gates.append(flag_is(p, "tubitak_staff", False, "§4.1.8 not TÜBİTAK staff", "staff"))
    r.verify += ["event proceedings indexed in CPCI-S/CPCI-SSH or Scopus",
                 "paper submitted/accepted for oral or poster (or invited talk); not yet published",
                 "waivers from ALL co-authors; one supported author per paper",
                 "timing: run `timing --program 2224a --date <event start>`"]
    return finish(r)


SCREENERS = {
    "2218": screen_2218,
    "2219": screen_2219,
    "2232a": lambda p, d: screen_2232(p, d, "A"),
    "2232b": lambda p, d: screen_2232(p, d, "B"),
    "2236a": screen_2236a,
    "2224a": screen_2224a,
}


def screen(profile: dict, programmes: list[str], as_of: date) -> dict:
    results = [asdict(SCREENERS[k](profile, as_of)) for k in programmes]
    return {"tool": "alterlab-tubitak-bideb/bideb_prescreen.py", "rules_read_on": READ_ON,
            "as_of": as_of.isoformat(), "results": results, "disclaimer": DISCLAIMER}


# ---------------------------------------------------------------- timing -----------

def timing(programme: str, target: date, today: date) -> dict:
    rows, usable = [], []
    for label, opens, closes in PERIODS_2026[programme]:
        o, c = date.fromisoformat(opens), date.fromisoformat(closes)
        state = "closed" if c < today else ("open" if o <= today else "upcoming")
        if programme == "2223b":
            gap = (target - c).days
            fits = 60 <= gap <= 270
            why = f"event starts {gap} days after the close (needs 60-270)"
        else:
            fits = c < target
            why = "closes before the target date" if fits else "closes on/after the target date"
        rows.append({"period": label, "opens": opens, "closes": closes + " 17:30",
                     "state": state, "fits_target": fits, "why": why})
        if fits and state != "closed":
            usable.append(label)
    advice = (f"use period {usable[0]}" if usable else
              "no remaining 2026 period fits; the next calendar was not published on "
              + READ_ON + " -- check the programme page")
    return {"programme": programme, "target_date": target.isoformat(),
            "today": today.isoformat(), "rule": TIMING_RULES[programme], "periods": rows,
            "usable_periods": usable, "advice": advice, "source": SOURCES[programme],
            "rules_read_on": READ_ON}


# ------------------------------------------------------------- rendering -----------

def render_screen(report: dict) -> str:
    out = [f"BİDEB pre-screen -- rules read {report['rules_read_on']}, as_of {report['as_of']}"]
    for res in report["results"]:
        out.append(f"\n== {res['name']} -- {res['verdict']}")
        for g in res["gates"]:
            out.append(f"  [{g['status'].upper()}] {g['rule']}: {g['detail']}")
        for n in res["notes"]:
            out.append(f"  [INFO] {n}")
        if res["verify"]:
            out.append("  Verify by hand:")
            out += [f"   - {v}" for v in res["verify"]]
        out.append(f"  Source: {res['source']}")
    out.append("\n" + report["disclaimer"])
    return "\n".join(out)


def render_timing(t: dict) -> str:
    out = [f"{t['programme']} timing for {t['target_date']} (today {t['today']}): {t['rule']}"]
    for row in t["periods"]:
        mark = "fits" if row["fits_target"] else "no  "
        out.append(f"  {row['period']} {row['opens']} -> {row['closes']} [{row['state']}] "
                   f"{mark} ({row['why']})")
    out.append(f"Advice: {t['advice']}\nSource: {t['source']} (read {t['rules_read_on']})")
    return "\n".join(out)


# ------------------------------------------------------------- self-test -----------

def run_self_test() -> int:
    ok = True

    def expect(name: str, got: object, want: object) -> None:
        nonlocal ok
        passed = got == want
        ok = ok and passed
        print(f"[{'PASS' if passed else 'FAIL'}] {name}: got={got!r} want={want!r}")

    def verdict(key: str, profile: dict, as_of: str) -> str:
        return SCREENERS[key](profile, date.fromisoformat(as_of)).verdict

    def gate_status(key: str, profile: dict, as_of: str, prefix: str) -> str:
        res = SCREENERS[key](profile, date.fromisoformat(as_of))
        return next(g.status for g in res.gates if g.rule.startswith(prefix))

    base_2218 = {"citizenship": "TR", "doctorate_date": "2020-03-15",
                 "kadrolu_at_proposed_host": False, "phd_from_host": False,
                 "tubitak_staff": False, "language_score": 72, "advisor_points_last_2y": 6,
                 "outputs_cumulative": {"wos_scopus_article": 1, "book_chapter": 5,
                                        "trdizin_article": 1}}
    expect("2218 all computable gates pass", verdict("2218", base_2218, "2026-07-10"),
           "PASS_COMPUTABLE_VERIFY_REST")
    expect("2218 chapter cap (2 + min(5,2) + 1 = 5)",
           table_points(base_2218["outputs_cumulative"], POINTS_2218, CAPS_2218)[0], 5)
    old = dict(base_2218, doctorate_date="2018-05-01")
    expect("2218 window closed without births", gate_status("2218", old, "2026-07-10", "§4.1.2"),
           "fail")
    expect("2218 two birth extensions reopen it",
           gate_status("2218", dict(old, birth_extensions=2), "2026-07-10", "§4.1.2"), "pass")
    expect("2218 language 69 fails", gate_status("2218", dict(base_2218, language_score=69),
                                                 "2026-07-10", "§4.1.11"), "fail")
    expect("2218 exempt host skips advisor points",
           gate_status("2218", dict(base_2218, advisor_points_last_2y=None,
                                    host_exempt_from_advisor_points=True),
                       "2026-07-10", "§4.1.10"), "pass")
    expect("2219 empty profile needs input", verdict("2219", {}, "2026-08-01"), "NEEDS_INPUT")
    p2219 = {"citizenship": "TR", "doctorate_date": "2015-01-01", "language_score": 64,
             "employed_abroad": False, "retired": False, "phd_from_host": False,
             "tubitak_staff": False}
    expect("2219 language 64 fails", verdict("2219", p2219, "2026-08-01"), "FAIL_GATE")
    expect("2219 foreign-language degree passes",
           verdict("2219", dict(p2219, foreign_language_degree=True), "2026-08-01"),
           "PASS_COMPUTABLE_VERIFY_REST")
    expect("2219 six-year rule after a 2022 return",
           gate_status("2219", dict(p2219, prior_2219_return_date="2022-09-01"),
                       "2026-08-01", "§4.1.3"), "fail")
    p2232b = {"months_in_turkiye_last_36": 3, "working_in_turkiye": False,
              "obligatory_service": False, "birth_date": "1986-10-01",
              "doctorate_date": "2023-06-30", "postdoc_months_abroad": 24,
              "ranked_months_2232b": 24}
    expect("2232-B under 40 on opening day", verdict("2232b", p2232b, "2026-09-27"),
           "PASS_COMPUTABLE_VERIFY_REST")
    expect("2232-B already 40", gate_status("2232b", dict(p2232b, birth_date="1986-09-01"),
                                            "2026-09-27", "§4.1.1"), "fail")
    expect("2232-B birth extension", gate_status("2232b", dict(p2232b, birth_date="1986-09-01",
                                                               birth_extensions=1),
                                                 "2026-09-27", "§4.1.1"), "pass")
    expect("2232-A 14 months in Türkiye fails",
           gate_status("2232a", {"months_in_turkiye_last_36": 14}, "2026-09-27",
                       "§4.1 not in Türkiye"), "fail")
    expect("2232-A private route is a manual check",
           gate_status("2232a", {"private_sector_route": True}, "2026-09-27",
                       "§4.1 experience"), "verify")
    expect("2236-A unconditional defence counts",
           verdict("2236a", {"defended_unconditionally_before_deadline": True,
                             "months_in_turkiye_last_36": 0, "permanent_at_proposed_host": False,
                             "previous_cocirculation_fellow": False,
                             "obligatory_service": False}, "2025-12-01"),
           "PASS_COMPUTABLE_VERIFY_REST")
    p2224 = {"role_2224a": "doctorate_researcher", "language_score": 75,
             "used_2224a_this_year": False, "affiliated_or_resident_in_turkiye": True,
             "tubitak_staff": False,
             "outputs_last_3_calendar_years": {"wos_scopus_article": 2, "book_chapter": 6}}
    expect("2224-A 4 + min(6,4) = 8 >= 6", verdict("2224a", p2224, "2026-10-10"),
           "PASS_COMPUTABLE_VERIFY_REST")
    expect("2224-A 4 points < 6 fails",
           verdict("2224a", dict(p2224, outputs_last_3_calendar_years={
               "wos_scopus_article": 1, "cpci_paper": 2}), "2026-10-10"), "FAIL_GATE")
    today = date(2026, 9, 23)
    expect("timing 2224a Feb-2027 event", timing("2224a", date(2027, 2, 15), today)
           ["usable_periods"], ["2026/3"])
    expect("timing 2223b 125-day gap fits", timing("2223b", date(2027, 3, 1), today)
           ["usable_periods"], ["2026/3"])
    expect("timing 2223b 35-day gap too short", timing("2223b", date(2026, 12, 1), today)
           ["usable_periods"], [])
    expect("timing 2223b 309-day gap too long", timing("2223b", date(2027, 9, 1), today)
           ["usable_periods"], [])
    expect("timing 2221 January arrival", timing("2221", date(2027, 1, 15), today)
           ["usable_periods"], ["2026/4"])
    expect("add_years 29 Feb -> 28 Feb", add_years(date(2020, 2, 29), 7), date(2027, 2, 28))
    print("\nSELF-TEST:", "OK" if ok else "FAILED")
    return 0 if ok else 1


# ------------------------------------------------------------------ main -----------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="PARTIAL BİDEB eligibility pre-screen and "
                                             "call-timing helper (rules read " + READ_ON + ").")
    ap.add_argument("--self-test", action="store_true", help="run the offline self-test")
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("screen", help="screen a JSON profile against computable gates")
    s.add_argument("profile", help="JSON file, '-' for stdin")
    s.add_argument("--programs", default=",".join(SCREENERS),
                   help="comma list from: " + ", ".join(SCREENERS))
    s.add_argument("--as-of", help="override the profile's as_of date (YYYY-MM-DD)")
    s.add_argument("--json", action="store_true", help="print JSON")
    t = sub.add_parser("timing", help="which 2026 period fits a target date")
    t.add_argument("--program", required=True, choices=sorted(PERIODS_2026))
    t.add_argument("--date", required=True, help="guest arrival or event start (YYYY-MM-DD)")
    t.add_argument("--today", help="reference date (default: today)")
    t.add_argument("--json", action="store_true", help="print JSON")
    args = ap.parse_args(argv)

    if args.self_test:
        return run_self_test()
    try:
        if args.cmd == "screen":
            raw = sys.stdin.read() if args.profile == "-" else open(
                args.profile, encoding="utf-8").read()
            profile = json.loads(raw)
            as_of = parse_date(args.as_of or profile.get("as_of")) or date.today()
            wanted = [k.strip().lower().replace("-", "") for k in args.programs.split(",")
                      if k.strip()]
            unknown = [k for k in wanted if k not in SCREENERS]
            if unknown:
                ap.error(f"unknown programme(s) {unknown}; choose from {list(SCREENERS)}")
            report = screen(profile, wanted, as_of)
            print(json.dumps(report, ensure_ascii=False, indent=2) if args.json
                  else render_screen(report))
            return 1 if any(r["verdict"] == "FAIL_GATE" for r in report["results"]) else 0
        if args.cmd == "timing":
            today = parse_date(args.today) or date.today()
            result = timing(args.program, date.fromisoformat(args.date), today)
            print(json.dumps(result, ensure_ascii=False, indent=2) if args.json
                  else render_timing(result))
            return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    ap.error("choose `screen` or `timing`, or pass --self-test")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
