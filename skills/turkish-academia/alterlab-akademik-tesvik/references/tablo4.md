# TABLO 4 ceilings & coefficients — verified from the regulation

All values below are transcribed from the consolidated text of the
**Akademik Teşvik Ödeneği Yönetmeliği** (Academic Incentive Allowance
Regulation) and its annexed tables, as published on mevzuat.gov.tr.

- Source: `https://www.mevzuat.gov.tr/MevzuatMetin/21.5.201811834.pdf`
- Bakanlar Kurulu Kararı: 14/5/2018, No. **2018/11834**
- Resmî Gazete: 27/6/2018, No. **30461**
- Dayanak (legal basis): 2914 sayılı Yükseköğretim Personel Kanunu, ek 4. madde
- Amended by Cumhurbaşkanı Kararı **CK-2043** (RG 17/1/2020, No. 31011) —
  MADDE 3, 5, 7, 8, 13 and Tablo 4. This is still the only amending regulation.
- Court rulings reflected in the consolidated text:
  - The CK-2043 amendment's own *yürürlük* article (in force on publication, no
    transition rule for 2019 activities) was annulled by Danıştay 8. Daire
    (14/9/2022, E.2020/730, K.2022/4736), final with İDDK 5/2/2024.
  - The **"tanınmış ulusal yayınevi"** definition (MADDE 3/1-k) and the same
    qualifier in the national book / book-chapter / book-citation rows of
    Tablo 4 were annulled by Danıştay 8. Daire (3/4/2024, E.2021/6094,
    K.2024/2115), **final with İDDK 8/9/2025** (E.2024/2221, K.2025/1570). The
    rows' oranlar remain (see the table below); how a university commission
    applies them without the qualifier is for that commission to settle.
  - Part of the "tanınmış uluslararası yayınevi" definition (MADDE 3/1-l) was
    annulled earlier (Danıştay 8. Daire 14/6/2022, final with İDDK 5/4/2023).
- Scope (MADDE 1): **Devlet** (state) yükseköğretim kurumları kadrolarındaki
  öğretim elemanları (state higher-education academic staff). Also applies to
  Milli Savunma Üniversitesi, Jandarma ve Sahil Güvenlik Akademisi, Polis
  Akademisi.
- Scope exclusions (MADDE 6): **yabancı uyruklu** (foreign-national) öğretim
  elemanları cannot benefit at all (MADDE 6/9); faaliyetler done while seconded
  (görevlendirme) to a **vakıf** (foundation) university are not counted
  (MADDE 6/7).
- Last verified against the consolidated PDF: **2026-09-23**.

> Re-verify against the current regulation text before a real başvuru
> (application); an amendment or court ruling can change rows.

## Per-type headline puan (= MADDE 8/3 ceiling)

These are the `(… puan)` headers in the **Faaliyet Hesaplama Tablosu**. Each is
**both** the type multiplier in `türü puanı = Σ(oran) × headline` (MADDE 8/2-a)
**and** the per-type ceiling (MADDE 8/3): a type's puanı cannot exceed it, and
the total cannot exceed 100. All headlines are ≤ 30 — that is how the MADDE 1
%30 weighting is encoded. The calculator key (ASCII-folded) is shown for
`scripts/tesvik_score.py` input.

| Activity type (canonical TR — English gloss) | Headline puan | Calculator key |
|---|---|---|
| PROJE (project)                | 20 | `proje` |
| ARAŞTIRMA (research)           | 15 | `arastirma` |
| YAYIN (publication)            | 30 | `yayin` |
| TASARIM (design)               | 15 | `tasarim` |
| SERGİ (exhibition)             | 15 | `sergi` |
| PATENT (patent)                | 30 | `patent` |
| ATIF (citation)                | 30 | `atif` |
| TEBLİĞ (conference paper)       | 20 | `teblig` |
| ÖDÜL (award)                   | 20 | `odul` |

## Coefficient tables

Each Faaliyet Hesaplama Tablosu cell is an **oran** (a percentage-style
multiplier like `k × p × 60`, `r × 80`, `15 × ay`) built from these coefficients;
`türü puanı = Σ(oran) × headline` (MADDE 8/2). Each coefficient applies only
where the regulation row uses it.

### (k) — author / contributor count (Tablo 1)

| Kişi sayısı (number of contributors) | k |
|---|---|
| 1 | 1 |
| 2 | 0.8 |
| 3 | 0.6 |
| 4 | 0.45 |
| 5 | 1/5 (0.2) |
| 6 | 1/6 (≈0.167) |
| 7 or more | 1 / (number of contributors) |

### (p) — journal quartile (ISI Web of Science çeyreklik grubu, Tablo 3)

| Quartile | p |
|---|---|
| Q1 | 1 |
| Q2 | 0.8 |
| Q3 | 0.5 |
| Q4 | 0.25 |

> The quartile is the latest one Web of Science published for the article's
> publication year. **AHCI journals** use **p = 0.5**; journals added after the
> latest quartile list take their assigned Q value, and journals with no Q value
> take the lowest coefficient (MADDE 8/6, am. CK-2043/4).

### (r) — project role (Tablo 2)

| Role | r |
|---|---|
| Yürütücü (PI / coordinator) | 1 |
| Araştırmacı, Bursiyer (researcher, fellow) | 0.5 |

> **No-share / no-ranking activities (MADDE 8/7):** for faaliyetler with no
> special share ratio and no author ordering, the oran is divided by the number
> of contributors (`oran / kişi sayısı`). **Exception:** SERGİ *karma* (group)
> etkinlikler and international performance-based *karma* audio/video recordings
> are scored at **full points (tam puan), with k NOT applied**, regardless of
> contributor count.

## Faaliyet Hesaplama Tablosu — oran per row and field column

Column groups (bilim alanı of the applicant): **A1** = Eğitim Bilimleri, Fen
Bilimleri ve Matematik, Mühendislik, Sağlık Bilimleri, Ziraat-Orman-Su Ürünleri;
**A2** = Filoloji, Hukuk, İlahiyat, Sosyal-Beşeri-İdari Bilimler, Spor
Bilimleri; **A3** = Mimarlık, Planlama ve Tasarım; **A4** = Güzel Sanatlar.
A dash means the row does not apply to that column. Read the cell's number as a
percentage of the type headline (see `hesaplama.md`).

| Type (headline) | Row | A1 | A2 | A3 | A4 |
|---|---|---|---|---|---|
| PROJE (20) | TÜBİTAK 1001, 1003, 1004, 1007, 1505, 2244, 3501, SAYEM, COST, uluslararası ikili işbirliği | r×80 | r×80 | r×80 | r×80 |
| PROJE (20) | TÜBİTAK 1005, 3001 | r×70 | r×70 | r×70 | r×70 |
| PROJE (20) | H2020 projesi | r×100 | r×100 | r×100 | r×100 |
| PROJE (20) | Other international Ar-Ge project (support ≥ 9 months) | r×40 | r×40 | r×40 | r×40 |
| PROJE (20) | Other national public/private Ar-Ge project (support ≥ 9 months) | r×20 | r×20 | r×20 | r×20 |
| ARAŞTIRMA (15) | Yurt dışı araştırma | 15×ay | 15×ay | 15×ay | 15×ay |
| ARAŞTIRMA (15) | Yurt içi araştırma | 10×ay | 10×ay | 10×ay | 10×ay |
| YAYIN (30) | SCI / SCI-E / SSCI / AHCI research article | k×p×60 | k×p×80 | k×p×60 | k×p×80 |
| YAYIN (30) | SCI / SCI-E / SSCI / AHCI review; stand-alone letter, comment, case report, technical note, research note, book review | k×p×30 | k×p×40 | k×p×30 | k×p×40 |
| YAYIN (30) | Article in an ÜAK-defined alan endeksi journal | k×20 | k×25 | k×20 | k×25 |
| YAYIN (30) | Article in another international peer-reviewed journal | k×15 | k×20 | k×15 | k×20 |
| YAYIN (30) | Article in a TR Dizin national peer-reviewed journal | k×15 | k×20 | k×15 | k×20 |
| YAYIN (30) | Editorship: SCI / SCI-E / SSCI / AHCI journal | 25 | 25 | 25 | 25 |
| YAYIN (30) | Editorship: alan endeksi journal | 15 | 15 | 15 | 15 |
| YAYIN (30) | Editorship: other international peer-reviewed / TR Dizin journal | 10 | 10 | 10 | 10 |
| YAYIN (30) | Original scientific book, recognised international publisher | k×100 | k×100 | k×100 | k×100 |
| YAYIN (30) | Editing such a book | k×60 | k×60 | k×60 | k×60 |
| YAYIN (30) | Chapter in such a book (max two chapters per book) | k×25 | k×25 | k×25 | k×25 |
| YAYIN (30) | Original scientific book, national (qualifier annulled 2025) | k×50 | k×50 | k×50 | k×50 |
| YAYIN (30) | Chapter in such a book (max two per book) | k×15 | k×15 | k×15 | k×15 |
| YAYIN (30) | Performance-based audio/video recording: international personal / international group / national personal | – | – | – | 20 / 10 / 10 |
| TASARIM (15) | Industrial, environmental, graphic, stage, fashion or instrument design | 15 | 15 | 15 | 15 |
| SERGİ (15) | Original solo event abroad / in Türkiye | – | – | – | 30 / 15 |
| SERGİ (15) | Original group event abroad / in Türkiye | – | – | – | 15 / 8 |
| PATENT (30) | Uluslararası patent / ulusal patent | k×100 / k×60 | k×100 / k×60 | k×100 / k×60 | k×100 / k×60 |
| ATIF (30) | Citation in an SCI / SCI-E / SSCI / AHCI article | 4 | 6 | 4 | 6 |
| ATIF (30) | Citation in an alan endeksi journal article | 1.5 | 3 | 1.5 | 3 |
| ATIF (30) | Citation in another international peer-reviewed / ULAKBİM national journal article | 1 | 2 | 1 | 2 |
| ATIF (30) | Citation in a book from a recognised international publisher | 4 | 8 | 4 | 8 |
| ATIF (30) | Citation in a national original scientific book (qualifier annulled 2025) | 2 | 4 | 2 | 4 |
| ATIF (30) | Fine-arts work in international / national sources | – | – | – | 8 / 4 |
| TEBLİĞ (20) | Full paper orally presented at a peer-reviewed international conference and published in its proceedings | k×15 | k×15 | k×15 | k×15 |
| ÖDÜL (20) | YÖK Yılın Doktora Tezi Ödülü; TÜBİTAK Bilim Ödülü; TÜBA Akademi Ödülü | 100 | 100 | 100 | 100 |
| ÖDÜL (20) | Science award from a foreign / domestic institution (regular, awarded ≥ 5 times before, academic jury) | 40 / 20 | 40 / 20 | 40 / 20 | 40 / 20 |
| ÖDÜL (20) | International / national juried fine-arts degree award | – | – | – | 40 / 20 |
| ÖDÜL (20) | Degree award in planning, architecture, urban/landscape/interior/industrial design competitions | – | – | 20 | – |

Two row-level conditions that change what counts:

- **Tebliğ (MADDE 7/9):** the event counts as international only if speakers
  from at least five countries other than Türkiye present oral papers and more
  than half of the papers come from participants abroad, confirmed by a
  university yönetim kurulu decision; the paper must be documented as presented
  and its full text published in the proceedings.
- **Ödül:** study/project/publication incentives, thank-you or achievement
  certificates and plaques, scholarships, honour and service certificates are
  excluded.

## Worked rows (oran as a fraction of the headline)

| Faaliyet (row, column) | Table cell | oran as fraction | × headline = türü puanı |
|---|---|---|---|
| YAYIN — SCI-E research article, A1 (e.g. Sağlık), Q1, 2 authors | `k × p × 60` | 0.8·1.0·0.60 = **0.48** | 0.48 × 30 = **14.4** |
| YAYIN — SSCI research article, A2 (e.g. Sosyal), Q1, 2 authors | `k × p × 80` | 0.8·1.0·0.80 = **0.64** | 0.64 × 30 = **19.2** |
| ATIF — 1 citation in an SCI article, A1 | `4` | **0.04** | 0.04 × 30 = **1.2** |
| ATIF — 1 citation in an SSCI article, A2 | `6` | **0.06** | 0.06 × 30 = **1.8** |
| TEBLİĞ — single-author international full paper | `k × 15` | 1·0.15 = **0.15** | 0.15 × 20 = **3.0** |
| PATENT — uluslararası patent, single inventor | `k × 100` | **1.00** | 1.00 × 30 = **30** (= tavan) |
| PROJE — H2020 yürütücü | `r × 100` | **1.00** | 1.00 × 20 = **20** (= tavan) |
| PROJE — TÜBİTAK 1005 yürütücü | `r × 70` | **0.70** | 0.70 × 20 = **14** |
| ARAŞTIRMA — yurt içi araştırma, 6 months | `10 × ay` | **0.60** | 0.60 × 15 = **9** |
| ÖDÜL — TÜBA Akademi Ödülü | `100` | **1.00** | 1.00 × 20 = **20** (= tavan) |

> The cell's number is a **percentage of the headline**, not the headline
> itself: a 2-author Q1 SCI-E article in an A1 field is `k·p·60% = 0.48` of the
> Yayın headline 30 = **14.4**, not 24. Always read the column for the
> applicant's own bilim alanı — the A2 and A4 columns are higher for articles
> and citations, so reusing an A1 value for a social scientist understates the
> score.
