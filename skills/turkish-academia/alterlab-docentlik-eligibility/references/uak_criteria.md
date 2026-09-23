# ÜAK Doçentlik Criteria — Bundled Table (Sağlık Bilimleri)

> **last_verified: 2026-09-23** — transcribed from the primary ÜAK PDF
> "TABLO 10. SAĞLIK BİLİMLERİ TEMEL ALANI" published for the **2026 Mart**
> term. That PDF is byte-identical to the ones ÜAK posted for the 2025 Mart and
> 2025 Ekim terms, so the Sağlık table has not changed since March 2025. On the
> verification date the **2026 Ekim** section of the ÜAK page listed only the
> *Bilim Alanları ve Anahtar Kelimeler* file (no per-field criteria PDFs yet).
>
> **ÜAK republishes the criteria for every application term.** Re-confirm the
> live table for the candidate's own field and term before relying on any
> output — see *Primary sources* below.

## Contents

- What "doçentlik" is
- Mandatory minimums — MODELLED by the scorer
- Mandatory minimums — NOT modelled (verify by hand)
- Per-index point table — Sağlık Bilimleri TABLO 10
- Başlıca yazar (lead author) — Sağlık definition
- Why this skill is a PARTIAL pre-screen
- Other fields
- Primary sources (re-verify here)

## What "doçentlik" is

**Doçentlik** is the Turkish associate-professorship title, awarded through a
national procedure run by **ÜAK** (Üniversitelerarası Kurul / the Inter-University
Council). Eligibility to *apply* is gated by an objective, points-based
publication threshold plus several item-specific mandatory minimums; the
bundled table and minimums below encode that gate for the **Sağlık Bilimleri
(Health Sciences)** field only. Applications run twice a year, in the March and
October terms (başvuru dönemleri) announced by ÜAK.

## Mandatory minimums — MODELLED by the scorer

`score_docentlik.py` computes these four from a publication list and pass/fail
checks each. **All four must pass** before the scorer returns its non-green
`PRESCREEN_PASS_VERIFY_REMAINING` status (it never returns "ELIGIBLE").

| Check | Threshold | TABLO 10 source |
|---|---|---|
| Total points | **≥ 100** | "asgari yüz (100) puanın sağlanmış olması" |
| Post-doctorate points | **≥ 90** | "en az doksan (90) puanın doktora veya ... uzmanlık ünvanının alınmasından sonra ... elde edilmiş olması" (item-3 thesis-derived points excluded) |
| International-article points (item 1), post-doctorate | **≥ 40** | Item 1 note: "doktora ... sonra, a bendinden en az üç makalede başlıca yazar olmak kaydıyla en az 40 puan almak zorunludur" — counted over all of item 1 (1a SCIE/SSCI Q1–Q4, 1b AHCI, 1c ESCI/Scopus, …) |
| Lead-author item-1a articles, post-doctorate | **≥ 3** | Same note: the three başlıca-yazar articles must come from **1a** (SCIE/SSCI, Q1–Q4; **Q4 counts**) |

## Mandatory minimums — NOT modelled (verify by hand)

The live TABLO 10 also imposes the following mandatory minimums (asgari
koşullar). The scorer **does not** compute these because a bare publication list
does not carry the needed inputs (citation counts, congress papers, teaching,
thesis-derivation, sub-category tags). They are emitted in every report under
`summary.unmodelled_minimums`, so the output can never be mistaken for a
complete eligibility decision.

| Requirement | Threshold (2026 Mart TABLO 10) | Why not modelled |
|---|---|---|
| National articles (item 2) | Post-doctorate: ≥ 3 publications, ≥ 2 of them TR Dizin articles (2a), candidate başlıca yazar in ≥ 2. Foreign nationals and foreign-doçentlik-equivalence applicants may substitute the same number of 1a/1b/1c articles. | Needs national-vs-TR-Dizin status and a per-article lead-author count; resolve TR Dizin status with `alterlab-trdizin` first. |
| Thesis-derived publication (item 3) | ≥ 1 publication from item 3 (a–h). Item 3 is capped at 20 points, its points do not count toward the 90, and a thesis-derived work is scored only here (never also as an item 1/2 article). | The input does not flag thesis-derived work. |
| Citation (item 5) | ≥ 5 points from post-doctorate publications; self-citations excluded; several citations of the same work inside one citing publication count once. | Citation counts are not in the publication list. |
| Scientific meeting (item 8) | ≥ 5 post-doctorate points; at most one paper per meeting. | Congress papers are a separate category. |
| Education / teaching (item 9) | ≥ 2 points (2 years as kadrolu öğretim elemanı after the doctorate counts as 2). | Teaching activity is not a publication. |

### Per-item point caps (2026 Mart TABLO 10)

| Item | Cap |
|---|---|
| 3. Lisansüstü tezlerden üretilmiş yayın | 20 (g/h bentleri together ≤ 5) |
| 4. Kitap | 20 (c/d bentleri together ≤ 5) |
| 5. Atıf | 10 |
| 6. Lisansüstü tez danışmanlığı | 10 |
| 7. Bilimsel araştırma projesi | 20 |
| 8. Bilimsel toplantı | 10 |
| 9. Eğitim-öğretim | 6 |
| 10. Patent / faydalı model | no cap stated |
| 11. Ödül | 25 |
| 12. Editörlük | 4 |
| 13. Diğer (WoS h-index ≥ 5; ≥ 6 months abroad at a top-300 university) | 10 |

Items 1 and 2 (articles) are uncapped. The scorer applies none of these caps
because the input does not tag items by sub-category — a raw total can
therefore overstate the usable total.

## Per-index point table — Sağlık Bilimleri TABLO 10

| Index tier | Code | Points | Item |
|---|---|---|---|
| SCIE / SSCI, 1st quartile (Web of Science JIF quartile) | `Q1` | 30 | 1a |
| 2nd quartile | `Q2` | 20 | 1a |
| 3rd quartile | `Q3` | 15 | 1a |
| 4th quartile | `Q4` | 10 | 1a |
| Arts & Humanities Citation Index | `AHCI` | 20 | 1b |
| Emerging Sources Citation Index | `ESCI` | 10 | 1c |
| Scopus | `Scopus` | 10 | 1c |
| TR Dizin (ULAKBİM national index) | `TRDizin` | 10 | 2a |

Rows **not** bundled (items with these tiers are reported as unscored): other
international indexes (1d) 5; letter to the editor / research note / abstract /
book review in a 1a–1d journal (1e) 3; case report in a 1a journal (1f) 5; other
peer-reviewed national journal (2b) 4; letter/note/abstract/review in a
peer-reviewed national journal (2c) 2.

**Index tier glossary**

- **Q1–Q4** — the journal's Web of Science Journal Impact Factor quartile. Resolve
  from the candidate's own JCR records.
- **AHCI / ESCI / Scopus** — score a flat value; they count toward the item-1
  ≥ 40 floor but **not** toward the ≥ 3 lead-author 1a articles.
- **TR Dizin** — TÜBİTAK ULAKBİM's national citation index (item 2). Whether a
  journal is *currently* TR Dizin-indexed is a live status — confirm with
  `alterlab-trdizin` before scoring; DergiPark hosting does **not** imply TR
  Dizin indexing.

## Başlıca yazar (lead author) — Sağlık definition

TABLO 10's *Tanımlar* section defines the candidate as başlıca yazar of:

- (a) a single-author article;
- (b) an article where they are the **first-listed author**;
- (c) an article written with the graduate student(s) they supervise (several
  students and a second advisor may appear, but the **second advisor** is not
  başlıca yazar).

Corresponding authorship is **not** in the Sağlık definition. TABLO 10 adds
that where no başlıca yazar is indicated on an article with two or more
authors, the points are split equally among the authors; the scorer does not
model that case (it applies the lead / non-lead split from the declared flag).

## Why this skill is a PARTIAL pre-screen

The scorer models 4 of the TABLO 10 mandatory minimums but not the national /
thesis-derived / citation / congress / education minimums or the per-item caps
(above). Clearing the modelled checks is **necessary but not sufficient** for
eligibility. Accordingly the scorer's verdict vocabulary is deliberately
**FAIL_MODELLED_CHECK** / **PRESCREEN_PASS_VERIFY_REMAINING** — it has **no
"ELIGIBLE" state** and structurally cannot emit a green eligibility verdict. The
official decision is the doçentlik jury's.

## Other fields

Other ÜAK temel alanlar (Eğitim, Fen Bilimleri ve Matematik, Filoloji, Güzel
Sanatlar, Hukuk, İlahiyat, Mimarlık-Planlama-Tasarım, Mühendislik, Sosyal-
Beşeri-İdari, Spor, Ziraat-Orman-Su Ürünleri) each have their **own** table with
different values, minimums and lead-author definitions. The bundled table here
is Sağlık only. To score another field, supply that field's table from the live
ÜAK source — never reuse the Sağlık numbers.

## Primary sources (re-verify here)

- **ÜAK** — Doçentlik başvuru şartları, per term and per field:
  <https://www.uak.gov.tr/page/docentlik-basvuru-sartlari-kLPHX>
  - 2026 Mart Sağlık TABLO 10: `uak.gov.tr/documents/documents/69affdf9bb4a6.pdf`
  - identical earlier copies: 2025 Ekim `68da32f147b67.pdf`, 2025 Mart
    `688340614375c.pdf`
  - The uak.gov.tr server omits its intermediate TLS certificate, so some HTTP
    clients fail with "unable to get local issuer certificate"; a browser loads
    it normally.
- **Doçentlik Yönetmeliği** — the binding regulation (Resmî Gazete 15/4/2018,
  No. 30392), on the official legislation portal:
  `mevzuat.gov.tr/mevzuat?MevzuatNo=24519&MevzuatTur=7&MevzuatTertip=5`
  (Resmî Gazete copy: `resmigazete.gov.tr/eskiler/2018/04/20180415-3.htm`).
  Note: `mevzuat.gov.tr/MevzuatMetin/21.5.201811834.pdf` is a *different*
  regulation — the **Akademik Teşvik Ödeneği Yönetmeliği** (see
  `alterlab-akademik-tesvik`), not the doçentlik binding regulation.
