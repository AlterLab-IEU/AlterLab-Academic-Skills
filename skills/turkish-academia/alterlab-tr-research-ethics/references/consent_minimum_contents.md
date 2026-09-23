# Bilgilendirilmiş Gönüllü Olur Formu — Minimum Content (TİTCK KAD-DD-13)

The participant-facing informed-consent form (*Bilgilendirilmiş Gönüllü Olur
Formu*; also called *onam formu* / *olur formu*) must carry, at minimum, the
elements below. This checklist is the source of truth for the linter in
`scripts/consent_form_check.py`, which scans a draft for each element (Turkish or
English wording) and reports PASS / MISSING per element.

Glossary: *gönüllü* = volunteer / participant; *onam* = assent/consent; *olur* =
consent; *parafe* = initials.

> A linter PASS means the **checklist elements are present**, not that the wording
> satisfies the committee. The institution's own template and the committee's
> decision are authoritative.

---

## Required Elements

| # | Element (TR) | Element (EN) | What it requires |
|---|--------------|--------------|------------------|
| 1 | Tarih, versiyon ve sayfa numarası | Date, version, page numbers | Every page carries a date, a version, and a page number out of the total ("sayfa 2/5"). |
| 2 | Gönüllü parafe alanı | Volunteer initials per page | (Clinical track) the participant initials every page except the signature page. |
| 3 | Çalışmanın amacı (sade dil) | Purpose, in plain language | Why the study is done, stated without jargon. |
| 4 | İşlemler ve süre | Procedures and duration | What the participant will do and how long it takes. |
| 5 | Öngörülen riskler / rahatsızlıklar | Foreseeable risks / discomforts | Honest statement of risks and burdens. |
| 6 | Beklenen yararlar | Expected benefits | Benefits to the participant and/or to science. |
| 7 | 24 saat ulaşılabilir iletişim | 24-hour contact | A contact reachable for problems/questions. |
| 8 | Gönüllülük beyanı | Voluntary-participation statement | Participation is voluntary. |
| 9 | İstediği zaman ayrılma hakkı | Right to withdraw at any time | May withdraw anytime without penalty. |
| 10 | Baskı/zorlama olmadığı beyanı | No-coercion statement | No pressure or inducement to participate. |
| 11 | Gizlilik / veri kullanımı | Confidentiality / data use | How data are kept confidential and used (link to the KVKK plan). |

### Clinical-track additions (Door 2 studies)

For TİTCK clinical-track studies, the form additionally addresses, as the
regulation requires:

- **Sigorta** — insurance coverage for the participant.
- **Alternatif tedaviler** — available alternative treatments.
- **Sponsor / sorumlu araştırmacı** — sponsor and responsible-investigator
  contact chain.

### Also in KAD-DD-13 — check by hand (the linter does not test these)

KAD-DD-13 lists further headings for the clinical BGOF. Check them manually:

- Araştırmanın adı; **the fact that the study is research**; estimated number of
  volunteers; treatments given and, if any, the chance of random assignment to groups.
- All procedures, including invasive ones; the experimental parts of the study.
- Risks to an embryo, fetus, or breast-fed infant when pregnant or breast-feeding
  women take part; a statement when no clinical benefit to the volunteer is expected.
- Compensation (sigorta) and/or treatment where the legislation requires it;
  payments for travel, meals, and similar costs; the volunteer's responsibilities.
- That monitors, auditors, the ethics committee, and health authorities may see the
  original medical records in confidence, and that signing the form permits this.
- Timely notice of new information that may change the wish to continue; the
  conditions for ending a volunteer's participation; post-study access to the
  investigational product; what biological samples are taken, why, and where they
  are analysed (including any transfer abroad).
- **Signature block**: statements equivalent to "Bilgilendirilmiş gönüllü olur
  formundaki tüm açıklamaları okudum … istediğim zaman gerekçeli veya gerekçesiz
  olarak araştırmadan ayrılabileceğimi biliyorum" and "Söz konusu araştırmaya,
  hiçbir baskı ve zorlama olmaksızın kendi rızamla katılmayı kabul ediyorum"; the
  name, signature, and date of the volunteer, of the researcher who gave the
  information, and, where needed, of a witness and of the parent(s) or legal guardian.
- The form may not contain wording that waives the volunteer's legal rights or
  releases the researcher, institution, or sponsor from liability for negligence.
- Future use of samples needs a separate consent section or form; paediatric studies
  need age-appropriate assent (written assent from age 9; written where possible
  for ages 3–8) and fresh consent when a participant turns 18 during the study.

---

## Notes for Drafting

- Keep Turkish as the primary language; add an English gloss only where a
  bilingual form is needed (e.g. non-Turkish-speaking participants).
- Write at a **plain-language** reading level — avoid clinical and legal jargon.
- The **confidentiality / data-use** element (11) is the bridge to KVKK: describe
  it here briefly, and produce the full KVKK-compliant data plan with
  `alterlab-kvkk-dmp`.
- Vulnerable groups: pair the consent with guardian consent + age-appropriate
  assent (çocuk rızası) for minors, and document any additional safeguards.

---

## Source

- TİTCK, KAD-DD-13 "BGOF'de Bulunması Gereken Asgari Bilgiler" (Word document
  linked from https://www.titck.gov.tr/faaliyetalanlari/ilac/klinik-arastirmalar;
  read 2026-09-23). The file sits in TİTCK's 2019 archive folder and carries no
  revision date; an earlier version of this skill cited an update of 29 Mar 2023,
  which could not be confirmed.
- *Beşeri Tıbbi Ürünlerin Klinik Araştırmaları Hakkında Yönetmelik* —
  mevzuat.gov.tr MevzuatNo 40207 (R.G. 27/5/2023, No. 32203; amended R.G.
  29/12/2023, No. 32414 and R.G. 5/6/2025, No. 32921) for the clinical-track
  consent requirements.

_Last verified: 2026-09-23. KAD-DD-13 is written for clinical research; for a
non-interventional study, the university committee's own consent template governs.
Re-verify against the current TİTCK document before finalizing a form._
