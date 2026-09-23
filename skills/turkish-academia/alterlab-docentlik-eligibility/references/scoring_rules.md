# Scoring Mechanics — Author Share, Checks and Other Items

How `score_docentlik.py` (v2.2.0) turns a publication list into points and pass/fail checks
for the selected ÜAK temel alan. Rule quotes: `field_tables.md`. Field comparison and term
status: `uak_criteria.md`.

## Contents

- Input schema
- Index tiers
- The two author-share rules (worked examples)
- Başlıca yazar: `is_lead`, `lead_basis`, `has_lead`
- Letters, notes and case reports in başlıca-yazar fields
- Post-doctorate points and item 3
- `other_items`: points for items 3 and above, with caps
- How the modelled checks are evaluated
- Verdicts
- Rounding convention
- Unknown or unusable input

## Input schema

```json
{
  "alan": "sosyal",
  "bilim_alani": "İletişim Çalışmaları",
  "publications": [
    {"title": "…", "index": "TRDizin", "authors": 1, "is_lead": true, "post_doc": true,
     "has_lead": true, "lead_basis": "first"}
  ],
  "other_items": [{"item": "4b", "points": 10, "post_doc_points": 10, "label": "BKCI chapter"}]
}
```

- `alan` (or legacy `field`; `--alan`/`--field` on the command line wins): a code from
  `--list-alanlar` or a Turkish/English name — matching ignores case and diacritics.
  Omitted → `saglik` (v2.1 default). Anything unrecognised is refused, never guessed.
- `bilim_alani` (or `--bilim-alani`): **required for `fen`** (its item-1 threshold is 40 or
  20 by bilim alanı); for `sosyal` and `ilahiyat` it decides whether the communication or Dinî
  Musiki manual check applies (omitted → the check is listed with its condition).
- `authors`: omitted → 1 (single author, as in v2.1); a non-integer or < 1 → the item is
  unscored.
- `is_lead`, `post_doc`, `has_lead`: booleans (`"evet"`/`"hayır"` and `"true"`/`"false"`
  accepted); an unrecognised value falls back to the conservative default (`is_lead` false,
  `post_doc` false, `has_lead` true) with a note.
- `lead_basis` (optional): `single`, `first` or `advisor` — checked against the field's
  definition (next sections).

## Index tiers

| Tier | Item | Points | Tier | Item | Points |
|---|---|---|---|---|---|
| `Q1` `Q2` `Q3` `Q4` | 1a | 30 / 20 / 15 / 10 | `TRDizin` | 2a | 10 |
| `AHCI` | 1b | 20 | `OtherNational` | 2b | 4 |
| `ESCI`, `Scopus` | 1c | 10 | `NationalNote` | 2c | 2 |
| `OtherIntl` | 1d | 5 | `CaseReport` (Sağlık only) | 1f | 5 |
| `IntlNote` | 1e | 3 | `SPORTDiscus` (Spor only) | 1c | 10 |

Tier names match case- and space-insensitively (`"TR Dizin"` → `TRDizin`). A bare `SSCI` or
`SCIE` without a quartile is **unscored** — the quartile decides the points. v2.1 bundled only
the eight tiers `Q1`–`Q4`, `AHCI`, `ESCI`, `Scopus`, `TRDizin` and reported the rest unscored;
they are now scored from the verified tables.

## The two author-share rules (worked examples)

**Equal split** — Eğitim, Filoloji, Güzel Sanatlar, Hukuk, İlahiyat, Sosyal: "Tek yazarlı
yayınlarda yazar tam puan alır. Çok yazarlı yayınlarda puan yazarlar arasında eşit olarak
bölünür." Every author gets `1/N`; `is_lead` does not change the score.

- Sosyal, Q2 article (20), 4 authors → 20 / 4 = **5.0**.
- Hukuk, TR Dizin article (10), 2 authors → 10 / 2 = **5.0**.

**Başlıca-yazar split** — Fen, Mimarlık, Mühendislik, Sağlık, Spor, Ziraat (articles):

| Authors | Candidate | Factor |
|---|---|---|
| 1 | sole author | **1.0** |
| 2 | başlıca yazar | **0.8** |
| 2 | the other author | **0.5** |
| ≥ 3 | başlıca yazar | **0.5** |
| ≥ 3 | another author | **0.5 / (N − 1)** |
| ≥ 2 | nobody on the article is başlıca yazar (`has_lead: false`) | **1/N** |

- Single-author Q1 → 30 × 1.0 = **30.0**.
- Two-author Q2, candidate başlıca yazar → 20 × 0.8 = **16.0**; the other author gets
  20 × 0.5 = **10.0** (not equal).
- Three-author Q1, candidate başlıca yazar → **15.0**; a non-lead co-author → 15 / 2 = **7.5**.
- Four-author Q3, non-lead → (15 × 0.5) / 3 = **2.5**.
- Fen, five-author Q3 with no başlıca yazar → 15 / 5 = **3.0**.

## Başlıca yazar: `is_lead`, `lead_basis`, `has_lead`

The definition (TABLO *Tanımlar*) differs by field (ÜAK S.S.S. Q19):

- **Sağlık, Mimarlık, Spor:** (a) single-author article, (b) first-listed author, (c) advisor
  on an article written with their own graduate student(s); a second advisor is not
  başlıca yazar.
- **Fen, Mühendislik, Ziraat:** (a) single-author article or (b) advisor with their own
  graduate student(s) — **first authorship alone does not qualify**. A multi-author article
  without a single author or an advisor–student relationship therefore has **no** başlıca
  yazar and is split equally: set `has_lead: false` for it. Leaving `has_lead` at its default
  (true) gives the lower 0.5/(N − 1) share, so omitting it never overstates points.

A single-author item is başlıca yazar automatically. Otherwise the scorer trusts `is_lead`
(as in v2.1) and echoes it per item for audit. If `lead_basis` is given and the field does
not accept it (e.g. `first` in Mühendislik), the item is scored as non-lead, the item carries
a note and `summary.interpretation_flags` gets a `lead_author` entry. The scorer does not
adjudicate authorship disputes.

## Letters, notes and case reports in başlıca-yazar fields

The başlıca-yazar split is worded for "makale"; "Diğer yayınlarda … eşit olarak bölünür".
The tables do not say which applies to letters, research notes, abstracts, book reviews
(1e, 2c) or Sağlık case reports (1f). The scorer uses the **smaller** of the two shares, so
it never overstates, and adds an `author_share` interpretation flag when the two differ.

## Post-doctorate points and item 3

- The **total** (≥ 100) sums every scored publication plus capped `other_items`.
- The **post-doctorate** (≥ 90) sums only publications with `post_doc: true` plus the capped
  `post_doc_points` of `other_items`, and **never** item 3 (thesis-derived work), per the
  common rule "(“3. Lisansüstü Tezlerden Üretilmiş Yayın” başlığından alınacak puanlar
  hariç)". Pre-doctorate work counts toward 100 but not 90 (ÜAK S.S.S. Q29).
- A thesis-derived article is scored only under item 3 (SCIE/SSCI/AHCI 20, ESCI/Scopus 10,
  TR Dizin 8, … with field deviations in `field_tables.md`). Leave it out of `publications`
  and enter it as `{"item": "3a", …}` under `other_items`.
- Sağlık: "doktora veya … uzmanlık"; for a sub-specialty (yan dal) application, count from the
  main-specialty title. Güzel Sanatlar: "doktora/sanatta yeterlik".

## `other_items`: points for items 3 and above, with caps

Each entry is the candidate's **own share**, computed by hand from the TABLO values.
Citations are not divided by the author count (S.S.S. Q27); oral papers are divided equally
(Q33); books and other non-article publications are divided equally in every table — the
equal-split tables split all publications, and the başlıca-yazar tables say "Diğer yayınlarda
… toplam puan yazarlar arasında eşit olarak bölünür" (S.S.S. Q36 defers to each table). The
scorer:

1. rejects items 1 and 2 (they belong in `publications`) and item numbers the table lacks;
2. sums entries per item and per sub-item letter (`"4c"`); an entry without a letter counts
   toward the item cap only;
3. applies each sub-item cap to tagged entries (e.g. Hukuk `3g`+`3h` ≤ 10, İlahiyat
   `4c`+`4d`+`4e` ≤ 30), then the item cap (e.g. Ziraat item 7 ≤ 60; "no cap stated" items
   such as Filoloji item 4 or Mimarlık item 13 stay uncapped);
4. applies the same caps to `post_doc_points` (missing → 0, conservative; larger than
   `points` → clamped), and drops item 3 from the post-doctorate sum.

Worked example (Filoloji): `4a` 20 + `4c` 20 + `4d` 15 → the 4c+4d group is capped at 30 →
item 4 counts 20 + 30 = **50** (Filoloji states no overall item-4 cap). `5` = 12 → capped at
**10**. `3g` = 5 → counts 5 toward the total, 0 toward the 90.

Points left out of `other_items` are simply not in the totals, so a total check can fail for
missing input — the verdict text says so.

## How the modelled checks are evaluated

Checks are data in `FIELDS` (see the script). Each is one or more **routes** (a primary rule
and, where the table allows one, an alternative); a route passes when all its conditions
pass; the check passes when any route passes.

**Ambiguous wording — a check fails only if it fails under every reading.** Several item-1
rules attach the sub-item restriction to the başlıca-yazar article, not to the points: e.g.
Mühendislik "Bu madde kapsamında, … a bendinden Q1, Q2 veya Q3 dergilerde yayımlanmış
makalelerden en az birinde başlıca yazar olmak kaydıyla 40 puan almak zorunludur." The scorer
counts all post-doctorate item-1 points toward the 40 (as v2.1 did for Sağlık's 40) and also
reports the value from the named sub-items (`named_subitems_value`). If only the broader
reading passes, an `interpretation_flags` entry says so. The same applies to Fen, Mimarlık,
Sağlık, Spor and Ziraat's second clause, and to the ≥ 50-point parts of the Filoloji, Hukuk
and İlahiyat national rules (item-2 points vs TR Dizin points only). Explicit sources are
applied as written — Eğitim "a bendinden Q1, Q2 veya Q3 dergilerde yayımlanmış makalelerden
en az 30 puan", Sosyal/Güzel Sanatlar "a, b, c veya d bentlerinden en az 10 puan", the
"a bendinden en az N puan" TR Dizin rules.

**Alternative routes** (Sosyal, Filoloji, Hukuk, İlahiyat): "Ulusal makale asgari koşulunu
sağlayamayan adaylar, 1. maddenin …" The alternative sentence does not contain "doktora
ünvanının alınmasından sonra", so the scorer counts publications of any date and flags a pass
that needs pre-doctorate work.
Sosyal's alternative names only items 1a and 1b (ESCI/Scopus do not count).

**Not computable → `to_verify`:** the "farklı dergilerde" (different journals) conditions of
Sosyal, Filoloji, Hukuk and İlahiyat — journal names are not an input. They are listed in
`summary.to_verify` whenever the primary route carries the check.

## Verdicts

- `FAIL_MODELLED_CHECK` — at least one modelled check fails on the work supplied.
- `PRESCREEN_PASS_VERIFY_REMAINING` — every modelled check passes; the manual minimums,
  `to_verify` items and interpretation flags still need a human.

There is **no** `ELIGIBLE` value, by design.

## Rounding convention

Per-item scaled points keep full precision and are summed unrounded. Reported figures use one
decimal place (per-publication `scaled` two). Threshold comparisons use the unrounded sums, so
a value shown as `90.0` that is really `89.96` fails the ≥ 90 check and shows the true
shortfall.

## Unknown or unusable input

An unknown tier (or a tier that does not exist in the selected field, e.g. `SPORTDiscus`
outside Spor) or an invalid author count is marked `scorable: false`, contributes **0**, and
is listed under `unscored` so the user can resolve it (`alterlab-trdizin` for TR Dizin status,
the candidate's JCR record for a quartile) and re-run. Guessing a tier would fabricate points.
