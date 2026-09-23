---
name: alterlab-docentlik-eligibility
description: "Runs a PARTIAL pre-screen of a Turkish associate-professorship (doçentlik) publication list against bundled ÜAK criteria (2026 Mart term) for all 12 temel alanlar: Eğitim, Fen Bilimleri ve Matematik, Filoloji, Güzel Sanatlar, Hukuk, İlahiyat, Mimarlık-Planlama-Tasarım, Mühendislik, Sağlık, Sosyal-Beşeri-İdari Bilimler, Spor, Ziraat-Orman-Su Ürünleri. It applies each field's author-share rule (equal split or başlıca yazar 0.8/0.5/half), checks the 100-point and 90 post-doctorate totals and the field's international/national-article minimums, caps other items entered, and lists the remaining mandatory minimums (thesis-derived work, book, citation, congress, teaching, art/competition items) as a manual checklist; it never emits an ELIGIBLE verdict. Use when the user wants to estimate doçentlik eligibility, compute ÜAK points or audit başlıca yazar rules; resolve TR Dizin status with alterlab-trdizin first; prefer alterlab-akademik-tesvik for the teşvik score. Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read Write Edit Bash WebFetch
compatibility: "No API key required — offline PARTIAL pre-screen (stdlib Python, run with uv) over bundled, dated ÜAK 2026 Mart criteria for all 12 temel alanlar; never emits an ELIGIBLE verdict. Checking the live ÜAK page for a newer term needs web access; live journal-index status is delegated to alterlab-trdizin."
metadata:
  skill-author: AlterLab
  version: "2.2.0"
  last_updated: "2026-09-23"
  depends_on: "alterlab-trdizin (live TR Dizin status feeds scoring), alterlab-akademik-tesvik (separate incentive score)"
---

# Doçentlik Eligibility — PARTIAL Pre-Screen Against the ÜAK Criteria (all 12 temel alanlar)

## Identity

A deterministic, offline pre-screen for faculty preparing a **doçentlik** (associate
professorship) application to **ÜAK** (Üniversitelerarası Kurul, the Inter-University
Council). It holds the 2026 Mart criteria tables of all twelve ÜAK temel alanlar — TABLO 1–6
and 8–13, each transcribed from ÜAK's own PDF on 2026-09-23 — and turns a publication list
into the points, author shares and pass/fail checks that the candidate's own table defines.

## Core Mission

1. **Use the right table.** Every temel alan has its own minimums, author-share rule and
   başlıca-yazar (lead author) definition; the Sağlık numbers are wrong for Sosyal, and so on.
2. **Compute only what a list can prove.** The 100-point total, the 90 post-doctorate points
   and the field's item-1 (international) and item-2 (national) article minimums are checked;
   every other mandatory minimum is handed back as a verify-by-hand checklist.
3. **Never declare eligibility.** The best status is `PRESCREEN_PASS_VERIFY_REMAINING`; the
   decision belongs to the doçentlik jury.

> **This is a PARTIAL pre-screen, not an eligibility decision — it never outputs
> "ELIGIBLE".** A green result means only that the modelled checks pass; the thesis-derived,
> book, citation, congress, teaching and field-specific minimums still need a human. A failed
> modelled check returns `FAIL_MODELLED_CHECK` with the exact shortfall.

## Quick Start

```
Doçentlik için yeterli puanım var mı? Sosyal, Beşeri ve İdari Bilimler; yayın listem ekte.
I'm in architecture (Mimarlık, Planlama ve Tasarım) — do I meet the ÜAK article minimums?
Mühendislikte ilk yazar olduğum makaleler başlıca yazar sayılıyor mu?
Calculate my ÜAK doçentlik points for the Sağlık field.
```

→ Identify the temel alan (and the bilim alanı where it matters), run
`scripts/score_docentlik.py --alan <code>` over the list, then present the report with the
template below. Never restate `PRESCREEN_PASS_VERIFY_REMAINING` as "eligible".

## Verify Against the Current ÜAK Term

ÜAK republishes the criteria for **each application term** (Mart and Ekim), per temel alan.
On **2026-09-23** the ÜAK page listed per-field criteria PDFs only up to the **2026 Mart**
term; its **2026 Ekim** section held just the *Bilim Alanları ve Anahtar Kelimeler* file. That
Ekim file already renames "Filoloji" to "Dil Bilimi ve Filoloji" — a sign the Ekim criteria
may change. Tell every candidate, especially an Ekim applicant, to confirm their own field's
live table at <https://www.uak.gov.tr/page/docentlik-basvuru-sartlari-kLPHX> (fetch it with
WebFetch when available). End every output with the verify-against-current-term disclaimer.

## When to Use This Skill

Use it when the request is about **scoring a publication list for the doçentlik point gate**
in any temel alan: total or post-doctorate points, the international/national article
minimums, the author-share calculation, whether a role counts as başlıca yazar, or which
other minimums remain.

### Does NOT Trigger

| The user actually wants… | Route to |
|---|---|
| The **akademik teşvik** (academic-incentive) annual score — different table, k·r·p coefficients, 30% rule | `alterlab-akademik-tesvik` |
| Whether a journal is **currently TR Dizin-indexed** (status feeds this scorer) | `alterlab-trdizin` |
| A journal's DergiPark hosting, scope or self-declared indexing | `alterlab-dergipark` |
| Broader career planning (Dr. Öğr. Üyesi → Doçent → Profesör, YÖKSİS dossier) | `alterlab-academic-career` |
| TÜBİTAK ARDEB 1001/1002-A proposal scaffolding | `alterlab-tubitak-proposal` |
| Whether a study needed **etik kurul** approval | `alterlab-tr-research-ethics` |
| Turkish APA-7 / TR Dizin reference style | `alterlab-tr-academic-style` |
| Checking that cited references actually **exist** | `alterlab-citation-verifier` |
| Finding a Turkish graduate **thesis** (tez) | `alterlab-yok-tez` |
| An academic's official affiliation or CV (YÖK Akademik) | `alterlab-yok-akademik` |

---

## Fields Covered (ÜAK 2026 Mart)

| TABLO | Temel alan | `--alan` | Author share | Item-1 minimum (post-doc) | Item-2 minimum (post-doc) |
|---|---|---|---|---|---|
| 1 | Eğitim Bilimleri | `egitim` | equal | ≥ 30 pts from 1a Q1–Q3 | ≥ 2 national pubs, ≥ 1 TR Dizin |
| 2 | Fen Bilimleri ve Matematik | `fen` | başlıca | 40 (Biyoloji, Fizik, Kimya, MBG) / 20 (Matematik, İstatistik) pts, lead in a Q1–Q3 article | ≥ 10 TR Dizin pts |
| 3 | Filoloji | `filoloji` | equal | — | ≥ 6 TR Dizin (4 single-author, 3 in different journals) and ≥ 50 pts; or ≥ 2 from 1a–1c (1 single-author) and ≥ 50 pts |
| 4 | Güzel Sanatlar | `guzel_sanatlar` | equal | ≥ 10 pts from 1a–1d | ≥ 1 single-author TR Dizin |
| 5 | Hukuk | `hukuk` | equal | — | as Filoloji |
| 6 | İlahiyat | `ilahiyat` | equal | — | ≥ 5 TR Dizin (3 single-author, 2 in different journals) and ≥ 50 pts; or the Filoloji alternative |
| 8 | Mimarlık, Planlama ve Tasarım | `mimarlik` | başlıca | ≥ 20 pts, lead in a 1a–1c article | ≥ 10 TR Dizin pts |
| 9 | Mühendislik | `muhendislik` | başlıca | 40 pts, lead in a Q1–Q3 article | ≥ 10 TR Dizin pts |
| 10 | Sağlık Bilimleri | `saglik` | başlıca | ≥ 40 pts, lead in ≥ 3 1a articles | manual (≥ 3 national, ≥ 2 TR Dizin, lead in ≥ 2) |
| 11 | Sosyal, Beşeri ve İdari Bilimler | `sosyal` | equal | ≥ 10 pts from 1a–1d | ≥ 5 TR Dizin (3 single-author) in different journals; or ≥ 3 from 1a/1b (1 single-author) |
| 12 | Ziraat, Orman ve Su Ürünleri | `ziraat` | başlıca | ≥ 30 pts from 1a, and ≥ 20 pts with lead in a Q1–Q3 article | ≥ 20 TR Dizin pts |
| 13 | Spor Bilimleri | `spor` | başlıca | ≥ 30 pts, lead in a 1a/1b article | ≥ 3 national pubs, ≥ 2 TR Dizin |

All twelve: total ≥ 100, of which ≥ 90 after the doctorate (item 3 excluded). ÜAK posts no
TABLO 7. Full comparison (books, citations, congress, caps): `references/uak_criteria.md`;
verbatim rule quotes and PDF hashes: `references/field_tables.md`.

## The Scoring Model

### Modelled checks (pass/fail)

- `total_ge_100` and `post_doc_ge_90` — publications plus any capped `other_items`.
- The field's item-1 and item-2 checks from the table above, with ids such as
  `intl_points_a_to_d_ge_10`, `national_articles`, `lead_q1_q3_articles_ge_1`,
  `trdizin_points_ge_10`. Sağlık keeps its v2.1 set (`intl_article_ge_40`,
  `lead_q_articles_ge_3`); its item-2 minimum stays a manual check.

### Author-share rules

- **Equal split** (Eğitim, Filoloji, Güzel Sanatlar, Hukuk, İlahiyat, Sosyal): every author
  gets 1/N; `is_lead` does not change points.
- **Başlıca-yazar split** (Fen, Mimarlık, Mühendislik, Sağlık, Spor, Ziraat): single author
  1.0; two authors 0.8 (başlıca yazar) / 0.5 (other); three or more: başlıca yazar 0.5, others
  share the other half; an article with **no** başlıca yazar (`has_lead: false`) is split
  equally.
- **Başlıca yazar differs by field.** Sağlık, Mimarlık, Spor: single author, first author, or
  advisor with own graduate students. **Fen, Mühendislik, Ziraat: single author or advisor
  only — first authorship does not count.** Pass `lead_basis` (`single`/`first`/`advisor`) and
  the scorer rejects a basis the field does not accept.
- Letters, notes, abstracts, reviews and case reports in başlıca-yazar fields get the smaller
  of the two shares (the tables do not say which applies).

Worked examples and the rounding convention: `references/scoring_rules.md`.

### Ambiguous wording — fail only when every reading fails

Some rules tie the sub-item restriction to the lead article rather than to the points (e.g.
Mühendislik "a bendinden Q1, Q2 veya Q3 dergilerde yayımlanmış makalelerden en az birinde
başlıca yazar olmak kaydıyla 40 puan"). The scorer counts all item-1 points (as v2.1 did for
Sağlık), reports the named-sub-item value beside it, and adds an `interpretation_flags`
entry when only the broader reading passes. Alternative routes whose sentence omits "doktora
ünvanının alınmasından sonra" are counted over all dates, again with a flag if needed.

### Mandatory minimums NOT modelled — the manual checklist

Every report lists them under `summary.unmodelled_minimums`, with the field's own numbers:
thesis-derived publication (all fields); book (Filoloji, Güzel Sanatlar, Hukuk, İlahiyat,
Sosyal, Spor); citation (≥ 5, Güzel Sanatlar ≥ 2); scientific meeting (≥ 5; Güzel Sanatlar
and Hukuk need one paper presented personally); teaching (≥ 2); per-item caps; the
predatory-journal rule (ÜAK S.S.S. Q20); relevance to the bilim alanı; and field-specific
items — Güzel Sanatlar *Özel Başvuru Şartları*, Sosyal communication bilim alanları (≥ 10
from item 13 c–e), Mimarlık item 13 (Yarışma, Proje ve Yazılım ≥ 15), İlahiyat Dinî Musiki
(≥ 10 from item 13 a–d), Sağlık national articles. Conditions no list can show (e.g.
TR Dizin articles "in different journals") appear under `summary.to_verify`.

### Other items and caps

Points for items 3 and above (books, citations, projects, congress papers, teaching,
exhibitions under item 13, …) are not publications. The user may enter self-computed shares
under `other_items` (`{"item": "4c", "points": 5, "post_doc_points": 5}`); the scorer applies
the field's item and sub-item caps and adds them to the totals (item 3 never counts toward
the 90). Without them, the totals cover publications only — say so when a total fails.

---

## Pipeline

### 1. Identify the temel alan and bilim alanı

Ask for the temel alan if it is not stated. `--bilim-alani` is **required for `fen`** (the
item-1 threshold is 40 or 20) and tailors the Sosyal communication and İlahiyat Dinî Musiki
checks. A field the tool does not bundle is refused — send the user to the ÜAK page.

### 2. Capture the publication list

Each item needs a title, the **index tier** (`Q1`–`Q4`, `AHCI`, `ESCI`, `Scopus`,
`OtherIntl`, `IntlNote`, `TRDizin`, `OtherNational`, `NationalNote`; `CaseReport` in Sağlık,
`SPORTDiscus` in Spor), the **author count**, whether the candidate is **başlıca yazar**, and
whether it is **post-doctorate**. Leave thesis-derived articles out (they belong to item 3).

```json
{
  "alan": "sosyal",
  "bilim_alani": "İletişim Çalışmaları",
  "publications": [
    {"title": "Article A", "index": "Q2", "authors": 2, "post_doc": true},
    {"title": "Makale B", "index": "TRDizin", "authors": 1, "post_doc": true}
  ],
  "other_items": [{"item": "4a", "points": 20, "post_doc_points": 20}]
}
```

Resolve an uncertain tier first — `alterlab-trdizin` for TR Dizin status, the candidate's JCR
record for a quartile. Do **not** guess a tier; an unknown one is reported as unscored.

### 3. Run the scorer

```bash
uv run python skills/turkish-academia/alterlab-docentlik-eligibility/scripts/score_docentlik.py \
    publications.json --alan sosyal --bilim-alani "İletişim Çalışmaları" --out report.json
```

- Input may be a file, `-` (stdin) or inline JSON; omit `--out` to print the report.
- `--alan` accepts codes or Turkish/English names; omitted → the input's `alan`/`field`,
  else `saglik` (v2.1 default). `--field` still works as an alias.
- `--list-alanlar` prints the bundled tables; `--self-test` runs hand-computed worked cases
  for all twelve tables offline.
- Pure stdlib — no network, no third-party dependencies, same input → same output.

### 4. Read the report and present it

Parse `summary.verdict` (`FAIL_MODELLED_CHECK` / `PRESCREEN_PASS_VERIFY_REMAINING`; there is
**no** `ELIGIBLE`), then fill in the template below.

## Output Template (user-facing answer)

```
**Doçentlik pre-screen — {TABLO n} {temel alan} ({term}), bilim alanı: {…}**
Status: {verdict} — {one-line meaning; never "eligible"}

| Check | Value | Threshold | Result |
|---|---|---|---|
| Total points | … | 100 | pass / FAIL (short …) |
| Post-doctorate points | … | 90 | … |
| {field item-1 / item-2 checks} | … | … | … |

Per-publication points: {title — tier, authors, share factor, points}
Other items counted (after caps): {item — declared → counted}
Unscored items: {titles + what to resolve}
Interpretation flags: {each flag, in plain words}
Still to verify by hand: {to_verify + unmodelled_minimums, with the field's numbers}
Disclaimer: partial pre-screen, criteria of {term}, verify at the ÜAK page; the jury decides.
```

Answer in the user's language (Turkish prompt → Turkish answer with correct ç ğ ı İ ö ş ü).

## Output Shape (JSON excerpt)

```json
{
  "tool": "alterlab-docentlik-eligibility/score_docentlik.py",
  "version": "2.2.0",
  "field": "sosyal", "alan": "sosyal", "table": "TABLO 11", "term": "2026 Mart",
  "source_pdf": "https://www.uak.gov.tr/documents/documents/69affdf9bdbcc.pdf",
  "table_last_verified": "2026-09-23",
  "prescreen_only": true,
  "summary": {
    "verdict": "PRESCREEN_PASS_VERIFY_REMAINING",
    "total_points": 113.5, "post_doc_points": 105.5,
    "checks": {
      "total_ge_100": {"pass": true, "value": 113.5, "threshold": 100},
      "intl_points_a_to_d_ge_10": {"pass": true, "value": 17.5, "threshold": 10, "rule_tr": "…"},
      "national_articles": {"pass": true, "passed_route": "primary", "routes": {"…": "…"}}
    },
    "interpretation_flags": [],
    "to_verify": ["national_articles: farklı dergilerde — …"],
    "unmodelled_minimums": [{"id": "book_kitap", "requirement": "…", "why_unmodelled": "…"}]
  },
  "publications": [{"title": "…", "index": "TRDizin", "share_factor": 1.0, "scaled": 10.0}],
  "other_items": [{"item": 4, "declared": 13.0, "counted": 13.0, "cap": 20}],
  "disclaimer": "PARTIAL PRE-SCREEN — NOT an eligibility decision. … NEVER returns 'ELIGIBLE' …"
}
```

## Quality Standards

- **Right table, stated:** 100% of outputs name the TABLO, temel alan, term (2026 Mart) and
  `table_last_verified`; a result for one field is never offered for another.
- **Complete check reporting:** every modelled check is shown, passing or failing, with value,
  threshold and (if failing) the exact shortfall.
- **Zero invented numbers:** no point value, threshold or tier appears that is not in the
  bundled tables or the user's input; unknown tiers are listed as unscored.
- **Zero eligibility claims:** the words "eligible"/"yeterli" are never used as a verdict.
- **Manual checklist delivered:** every `unmodelled_minimums` and `to_verify` item appears,
  and every interpretation flag is explained.
- **Reproducible:** `--self-test` passes (worked cases for all twelve tables) before the
  script is changed or a new term's data is added.

## Error Handling & Edge Cases

| Situation | What to do |
|---|---|
| Temel alan unknown / not bundled | The script exits 2 — ask the user, or send them to the ÜAK page; never borrow another field's numbers |
| `fen` without a bilim alanı | Exit 2 listing the six bilim alanları and their 40/20 thresholds — ask which applies |
| Ekim 2026 (or later) applicant | Run on 2026 Mart data but lead with the warning that the term's criteria must be checked live |
| Tier missing, "SSCI" without quartile, or TR Dizin status unknown | Item is unscored — resolve (JCR record, `alterlab-trdizin`) and re-run |
| First-author "lead" claim in Fen, Mühendislik or Ziraat | Scored as non-lead; explain the field's definition; ask about advisor–student co-authorship |
| Article with no başlıca yazar (başlıca-yazar fields) | Set `has_lead: false` → equal split |
| Thesis-derived article in the list | Remove it from `publications`; enter it under `other_items` as item 3 |
| Total fails but books/projects/citations were not entered | Say the totals are incomplete and offer to add `other_items` |
| Pass that relies on a broader reading (flag) | Present it as uncertain; suggest confirming with ÜAK or the institution |
| Q4 journal that charges fees | Warn: yağmacı/şaibeli rule (S.S.S. Q20) may exclude it — the scorer cannot tell |
| Güzel Sanatlar candidate | Stress that the Özel Başvuru Şartları (exhibitions, films, concerts…) must also be met |

## AI Disclosure & Ethics

- State that the pre-screen was produced with AI assistance from ÜAK's published tables and
  that it is not an official ÜAK or jury decision.
- The tool models counts, not quality: it cannot judge scientific merit, originality or
  relevance to the bilim alanı — the jury does.
- Treat publication lists as personal data: do not store or share them beyond the task.
- Do not help inflate or misstate authorship roles, index tiers or dates to reach a
  threshold. ÜAK cancels an application that does not meet the asgari başvuru şartları (e.g.
  declared works outside the bilim alanı; a corrected application is possible next term), and
  a candidate found to have committed a research/publication-ethics violation may reapply only
  from the third following term (ÜAK S.S.S. Q13–Q14).

## Self-Check Before Reporting

- Did you name the field, TABLO, term and `table_last_verified`?
- Is every modelled check reported, with shortfalls for failures?
- Did you present the manual checklist, `to_verify` items and interpretation flags?
- Did you avoid calling `PRESCREEN_PASS_VERIFY_REMAINING` "eligible"?
- Were unknown tiers flagged, not dropped or guessed?
- For Fen/Mühendislik/Ziraat, did you check first-author lead claims?
- Did you include the verify-against-current-term disclaimer?

## References

- `references/uak_criteria.md` — term status, the 12 tables side by side (share rule,
  item-1/item-2 minimums, other minimums, caps), what is modelled vs manual, sources.
- `references/field_tables.md` — verbatim rule quotes for each TABLO with PDF URL and
  SHA-256, common point values, Güzel Sanatlar Özel Başvuru Şartları.
- `references/scoring_rules.md` — input schema, both author-share rules with worked examples,
  başlıca-yazar handling, `other_items` caps, ambiguous-wording policy, verdicts, rounding.
- `scripts/score_docentlik.py` — the data-driven scorer (`--alan`, `--list-alanlar`,
  `--self-test`).

## Sources

- ÜAK, *Doçentlik Başvuru Şartları* (term sections and the 12 per-field PDFs of the 2026 Mart
  term): <https://www.uak.gov.tr/page/docentlik-basvuru-sartlari-kLPHX> — retrieved
  2026-09-23; per-PDF URLs and SHA-256 in `references/field_tables.md`.
- ÜAK, *2026 Mart Dönemi Sıkça Sorulan Sorular ve Cevapları*:
  <https://www.uak.gov.tr/documents/documents/6a07202a2ea5f.pdf> — retrieved 2026-09-23.
- ÜAK, *Bilim/Sanat Alanları ve Anahtar Kelimeler*, 2026 Mart
  (<https://www.uak.gov.tr/documents/documents/69b0017962c56.pdf>) and 2026 Ekim
  (<https://www.uak.gov.tr/documents/documents/6aa40cd9e0ea1.pdf>) — retrieved 2026-09-23.
- Doçentlik Yönetmeliği — UNVERIFIED in this revision (the legislation hosts timed out on
  2026-09-23); see `references/uak_criteria.md`.

Part of the AlterLab Academic Skills suite.
