# ÜAK Doçentlik Criteria — Term Status and Cross-Field Comparison

> **last_verified: 2026-09-23** — the ÜAK criteria page and all 12 per-field PDFs of the
> **2026 Mart** term were downloaded and read that day. Verbatim rule lines and PDF hashes:
> `field_tables.md`. How the scorer turns them into points and checks: `scoring_rules.md`.
>
> **ÜAK republishes the criteria for every application term, per temel alan.** Re-confirm
> the live table for the candidate's own field and term before relying on any output.

## Contents

- Term status (checked 2026-09-23)
- What "doçentlik" is
- The 12 tables at a glance (share rule, item-1 and item-2 minimums)
- Other mandatory minimums at a glance
- Per-item caps at a glance
- What the scorer models and what stays manual
- Primary sources (re-verify here)

## Term status (checked 2026-09-23)

- The ÜAK page (<https://www.uak.gov.tr/page/docentlik-basvuru-sartlari-kLPHX>) lists one
  section per term. The newest, **"2026 Ekim Dönemi Doçentlik Başvuru Şartları"**, holds only
  the *Bilim Alanları ve Anahtar Kelimeler* file (`6aa40cd9e0ea1.pdf`); its caption still reads
  "2026 Mart Dönemi başvurularına ait bilgilerdir". No per-field criteria PDFs for Ekim 2026
  were posted.
- The newest section **with** per-field criteria is **"2026 Mart Dönemi Doçentlik Başvuru
  Şartları"**: twelve PDFs, TABLO 1–6 and 8–13 (no TABLO 7 is posted). The 2026 Ekim Bilim
  Alanları file lists exactly twelve temel alanlar, so every temel alan has a table.
- **Change signal for Ekim 2026:** the 2026 Ekim Bilim Alanları file names the philology temel
  alan "Dil Bilimi ve Filoloji"; the 2026 Mart Bilim Alanları file (`69b0017962c56.pdf`) and
  TABLO 3 say "Filoloji". Expect at least naming changes in the Ekim criteria.
- The Sağlık 2026 Mart PDF is byte-identical to the 2025 Mart and 2025 Ekim Sağlık PDFs (same
  SHA-256). The other eleven were not compared across terms.

## What "doçentlik" is

**Doçentlik** is the Turkish associate-professorship title, awarded through a national
procedure run by **ÜAK** (Üniversitelerarası Kurul, the Inter-University Council). Eligibility
to apply is gated by a points threshold (100 in total, 90 after the doctorate) plus mandatory
minimums per TABLO item, which differ by temel alan. Applications run in the Mart and Ekim
terms. The binding regulation is the **Doçentlik Yönetmeliği** (its Resmî Gazete details are
UNVERIFIED in this revision — see *Primary sources*); the jury, not a score, makes the
decision.

## The 12 tables at a glance

"post-doc" = after the doctorate (Güzel Sanatlar: or sanatta yeterlik; Sağlık: or the medical,
dental, pharmacy or veterinary specialty). Every item-1/item-2 minimum below is post-doc.

| TABLO | Temel alan (`--alan`) | Author share | Başlıca yazar | Item-1 minimum | Item-2 minimum |
|---|---|---|---|---|---|
| 1 | Eğitim Bilimleri (`egitim`) | equal | — | ≥ 30 pts from 1a **Q1–Q3** (Q4 excluded) | ≥ 2 item-2 publications, ≥ 1 from 2a |
| 2 | Fen Bilimleri ve Matematik (`fen`) | başlıca | single; advisor with own students | lead in ≥ 1 1a Q1–Q3 article and 40 pts (Biyoloji, Fizik, Kimya, Moleküler Biyoloji ve Genetik) or 20 pts (Matematik, İstatistik) | ≥ 10 pts from 2a |
| 3 | Filoloji (`filoloji`) | equal | — | none | ≥ 6 from 2a (4 single-author, 3 in different journals) and ≥ 50 pts; *or* ≥ 2 from 1a–1c (1 single-author) and ≥ 50 pts |
| 4 | Güzel Sanatlar (`guzel_sanatlar`) | equal | — | ≥ 10 pts from 1a–1d | ≥ 1 single-author 2a publication |
| 5 | Hukuk (`hukuk`) | equal | — | none | as Filoloji |
| 6 | İlahiyat (`ilahiyat`) | equal | — | none | ≥ 5 from 2a (3 single-author, 2 in different journals) and ≥ 50 pts; *or* as the Filoloji alternative |
| 8 | Mimarlık, Planlama ve Tasarım (`mimarlik`) | başlıca | single; first author; advisor | lead in ≥ 1 article from 1a–1c and ≥ 20 pts | ≥ 10 pts from 2a |
| 9 | Mühendislik (`muhendislik`) | başlıca | single; advisor with own students | lead in ≥ 1 1a Q1–Q3 article and 40 pts | ≥ 10 pts from 2a |
| 10 | Sağlık Bilimleri (`saglik`) | başlıca | single; first author; advisor | lead in ≥ 3 1a articles and ≥ 40 pts | ≥ 3 item-2 publications, ≥ 2 from 2a, lead in ≥ 2 (manual check) |
| 11 | Sosyal, Beşeri ve İdari Bilimler (`sosyal`) | equal | — | ≥ 10 pts from 1a–1d | ≥ 5 from 2a (3 single-author) in different journals; *or* ≥ 3 from 1a/1b (1 single-author) |
| 12 | Ziraat, Orman ve Su Ürünleri (`ziraat`) | başlıca | single; advisor with own students | ≥ 30 pts from 1a, and ≥ 20 pts with lead in ≥ 1 1a Q1–Q3 article | ≥ 20 pts from 2a |
| 13 | Spor Bilimleri (`spor`) | başlıca | single; first author; advisor | lead in 1a or 1b and ≥ 30 pts | ≥ 3 item-2 publications, ≥ 2 from 2a |

- **Equal split:** "Tek yazarlı yayınlarda yazar tam puan alır. Çok yazarlı yayınlarda puan
  yazarlar arasında eşit olarak bölünür."
- **Başlıca-yazar split (articles):** single author 1.0; two authors 0.8 (başlıca yazar) and
  0.5 (the other); three or more: başlıca yazar half, the rest share the other half; an article
  with no başlıca yazar is split equally; other publications too ("Diğer yayınlarda ise
  toplam puan yazarlar arasında eşit olarak bölünür.").
- **Başlıca yazar definitions differ** (ÜAK S.S.S. Q19). In Fen, Mühendislik and Ziraat,
  first authorship alone does **not** make a başlıca yazar.
- Where a threshold's source is not spelled out (e.g. "a bendinden … en az birinde başlıca
  yazar olmak kaydıyla 40 puan"), see `scoring_rules.md` → *Ambiguous wording*.

## Other mandatory minimums at a glance

All twelve also require ≥ 1 thesis-derived publication (item 3, a–h) and ≥ 2 teaching points
(item 9). Scientific-meeting minimum: ≥ 5 post-doc points everywhere.

| `--alan` | Book (item 4, post-doc) | Citation (item 5, post-doc) | Meeting extra condition | Field-specific |
|---|---|---|---|---|
| `egitim` | — | ≥ 5 | — | — |
| `fen` | — | ≥ 5 | — | — |
| `filoloji` | ≥ 1 from 4a or 4c | ≥ 5 | — | — |
| `guzel_sanatlar` | ≥ 1 book or 1 chapter | **≥ 2** | ≥ 1 paper presented personally | Özel Başvuru Şartları by sanat alanı (see `field_tables.md`) |
| `hukuk` | ≥ 1 from 4a or 4c | ≥ 5 | ≥ 1 paper presented personally | — |
| `ilahiyat` | ≥ 1 from 4a or 4c | ≥ 5 | — | Dinî Musiki: ≥ 10 from item 13 a–d |
| `mimarlik` | — | ≥ 5 | — | item 13 Yarışma, Proje ve Yazılım ≥ 15, else ≥ 1 publication from 1a–1c |
| `muhendislik` | — | ≥ 5 | — | — |
| `saglik` | — | ≥ 5 | — | — |
| `sosyal` | ≥ 1 book or 2 chapters | ≥ 5 | — | Görsel İletişim Tasarımı, İletişim Çalışmaları, Reklamcılık, Sinema, Halkla İlişkiler: ≥ 10 from item 13 c–e |
| `ziraat` | — | ≥ 5 | — | — |
| `spor` | ≥ 1 book or 2 chapters | ≥ 5 | — | — |

## Per-item caps at a glance

"–" = no cap stated; "·" = the table has no such item; parentheses = sub-item caps (e.g.
`cd≤5` = 4c + 4d together ≤ 5). Items 1–2 are uncapped everywhere.

| `--alan` | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `egitim` | 20 (gh≤5) | 20 (cd≤5) | 10 | 10 | 15 | 10 | 6 | – | 25 | 4 | 10 | · |
| `fen` | 20 | 20 (cd≤5) | 10 | 10 | 30 | 10 | 6 | – | 25 | 4 | 10 | · |
| `filoloji` | 20 (gh≤5) | – (cd≤30) | 10 | 10 | 20 | 10 | 6 | – | 25 | 4 | 10 | · |
| `guzel_sanatlar` | 20 (gh≤5) | 20 (cd≤5) | 10 | 10 | 20 | 10 | 6 | – | 25 | 4 | 10 | · |
| `hukuk` | 20 (gh≤10) | – (cd≤30) | 10 | 10 | 20 | 10 | 6 | – | 25 | 4 | 10 | · |
| `ilahiyat` | 20 (gh≤5) | – (cde≤30) | 10 | 10 | 20 | 10 | 6 | – | 25 | 4 | 20 | 10 |
| `mimarlik` | 20 | 20 (cd≤5) | 10 | 10 | 30 | 10 | 6 | – | 25 | 4 | – | 10 |
| `muhendislik` | 20 | 20 (cd≤5) | 10 | 10 | 30 | 10 | 6 | – | 25 | 4 | 10 | · |
| `saglik` | 20 (gh≤5) | 20 (cd≤5) | 10 | 10 | 20 | 10 | 6 | – | 25 | 4 | 10 | · |
| `sosyal` | 20 (gh≤5) | 20 (cd≤5) | 10 | 10 | 20 | 10 | 6 | – | 25 | 4 | 20 | · |
| `ziraat` | 20 | 20 (cd≤5) | 10 | 10 | 60 | 10 | 6 | – | 25 | 4 | 10 | · |
| `spor` | 20 (gh≤5) | 20 (cd≤5) | 10 | 10 | 20 | 10 | 6 | – | 25 | 4 | 15 | 10 |

Item 13 is "Diğer" except in İlahiyat (Sanatsal Uygulama/Etkinlik), Mimarlık (Yarışma, Proje
ve Yazılım) and Spor (Sportif Başarı ve Temsil), where "Diğer" is item 14.

## What the scorer models and what stays manual

**Modelled** (computed from the publication list, pass/fail): the 100-point total, the 90
post-doc points (item 3 excluded), and each field's item-1 and item-2 minimums from the first
table above — except Sağlık's item-2 minimum, which stays a manual check so the v2.1 Sağlık
check set is unchanged.

**Applied when entered:** item and sub-item caps on points supplied under `other_items`.

**Manual** (listed in every report under `summary.unmodelled_minimums`): thesis-derived
publication, book, citation, scientific-meeting and teaching minimums; field-specific
requirements (Güzel Sanatlar Özel şartlar, Sosyal communication item 13, Mimarlık item 13,
İlahiyat Dinî Musiki, Sağlık national articles); the different-journals conditions in
Filoloji, Hukuk, İlahiyat and Sosyal; the predatory-journal rule (S.S.S. Q20); relevance to
the bilim alanı; the foreign-national substitution.

The verdict vocabulary is **FAIL_MODELLED_CHECK** / **PRESCREEN_PASS_VERIFY_REMAINING** —
there is no "ELIGIBLE" state. Passing every modelled check is necessary, not sufficient.

## Primary sources (re-verify here)

- **ÜAK — Doçentlik Başvuru Şartları** (per term, per field):
  <https://www.uak.gov.tr/page/docentlik-basvuru-sartlari-kLPHX> — retrieved 2026-09-23.
  The 12 per-field 2026 Mart PDFs, with SHA-256, are listed in `field_tables.md`.
- **ÜAK — 2026 Mart Dönemi Sıkça Sorulan Sorular** (linked from the same page as "S.S.S."):
  <https://www.uak.gov.tr/documents/documents/6a07202a2ea5f.pdf> — retrieved 2026-09-23.
- **ÜAK — Bilim Alanları ve Anahtar Kelimeler**, 2026 Mart
  (<https://www.uak.gov.tr/documents/documents/69b0017962c56.pdf>) and 2026 Ekim
  (<https://www.uak.gov.tr/documents/documents/6aa40cd9e0ea1.pdf>) — retrieved 2026-09-23.
- **Doçentlik Yönetmeliği** — **UNVERIFIED in this revision.** v2.1 cited it as Resmî
  Gazete 15/4/2018, No. 30392, at
  `mevzuat.gov.tr/mevzuat?MevzuatNo=24519&MevzuatTur=7&MevzuatTertip=5` (Resmî Gazete copy
  `resmigazete.gov.tr/eskiler/2018/04/20180415-3.htm`). On 2026-09-23 both hosts timed out
  from this environment, so those details were not re-checked; nothing in the scorer depends
  on them. v2.1 also warned that `mevzuat.gov.tr/MevzuatMetin/21.5.201811834.pdf` is the
  Akademik Teşvik Ödeneği Yönetmeliği (see `alterlab-akademik-tesvik`), not the doçentlik
  regulation — likewise not re-checked here.
- **TLS note:** uak.gov.tr serves its leaf certificate without the DigiCert intermediate, so
  strict clients fail with "unable to get local issuer certificate". Add the intermediate
  from the certificate's own AIA URL
  (`cacerts.digicert.com/DigiCertGlobalG2TLSRSASHA2562020CA1-1.crt`) to the CA bundle — do
  not disable verification. A browser loads the page normally.
