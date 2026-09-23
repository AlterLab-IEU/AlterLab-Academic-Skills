# Etik Kurul Routing — Which Committee Does Your Study Need?

Turkish human-subjects ethics review has **two doors**. Route by what the study
*does to or with participants*, not by discipline. Sending a study to the wrong
committee wastes a review cycle and, for clinical work, can invalidate the
approval entirely.

Glossary: *etik kurul* = ethics committee; *girişimsel olmayan* = non-interventional;
*klinik araştırma* = clinical research; *TİTCK* = Türkiye İlaç ve Tıbbi Cihaz Kurumu
(Turkish Medicines and Medical Devices Agency); *BA/BE* = biyoyararlanım /
biyoeşdeğerlik (bioavailability / bioequivalence); *izin* = permit.

---

## Door 1 — Üniversite Girişimsel Olmayan Etik Kurulu (non-interventional committee)

**Trigger (the TR Dizin / ULAKBİM rule, mandatory for publications from 2020):**
any study that collects data **from participants** by one of these methods needs
ethics-committee approval before data collection:

- **Anket** — survey / questionnaire
- **Görüşme / mülakat** — interview
- **Odak grup** — focus group
- **Gözlem** — observation
- **Deney** — experiment (non-clinical, e.g. behavioral/educational tasks)

For social, behavioral, educational, and other **non-clinical** human-subjects
research, this is the researcher's **own university's non-interventional ethics
committee** (Girişimsel Olmayan Klinik Araştırmalar / Sosyal ve Beşeri Bilimler
Etik Kurulu, depending on the institution's naming).

What this committee reviews: study aim, design, sampling, instruments,
risk/benefit to participants, the informed-consent procedure, and data-handling
(at a high level — the detailed KVKK data plan is a separate track; route to
`alterlab-kvkk-dmp`).

Two TİTCK rules (Klinik Araştırmalar SSS, checked 2026-09-23) confirm this door:

- **No exemption for "no intervention".** SSS 72: studies without direct
  intervention on people cannot be run without ethics approval ("Helsinki
  bildirgesi gereğince etik kurul onayı alınmadan yapılamaz").
- **Not the clinical committee's job.** A Klinik Araştırmalar Etik Kurulu "Bu
  fıkrada belirtilenler dışındaki araştırmaları ve çalışmaları değerlendiremez"
  (Yönetmelik Art. 61/11); SSS 70 names "retrospektif çalışmalar, anket çalışmaları
  vb. müdahalesiz çalışmalar" as outside its remit, and SSS 73 sends
  non-interventional studies (blood/saliva/imaging material, anthropometry,
  surveys, lifestyle studies, …) to "diğer etik kurullar (Müdahalesiz çalışmalar
  etik kurulu, bilimsel araştırmalar etik kurulu vb.)".

---

## Door 2 — TİTCK-regulated research (designated committee, usually + permit)

Per TİTCK: clinical research is conducted "TİTCK tarafından onay verilen Etik
Kurulların onayı ve Sağlık Bakanlığının izni ile gerçekleştirilmektedir." The
committee type and the permit depend on the product (Yönetmelik Art. 61/11–12;
TİTCK Klinik Araştırmalar SSS 2, 8, 70; checked 2026-09-23):

| Study | Ethics committee | Permit |
|-------|------------------|--------|
| **Beşeri tıbbi ürün** — drug clinical trial, incl. licensed drugs, and low-risk scientific studies | TİTCK-approved **Klinik Araştırmalar Etik Kurulu** | TİTCK Klinik Araştırmalar Dairesi |
| **Gözlemsel çalışma** — observational study of a medicinal product | Klinik Araştırmalar Etik Kurulu **only** (no other committee may approve it) | **None** — outside the regulation's permit scope (SSS 8) |
| **Tıbbi cihaz** — device clinical investigation or post-market study (Tıbbi Cihaz Klinik Araştırmaları Yönetmeliği, R.G. 8/7/2022, No. 31890) | Klinik Araştırmalar Etik Kurulu | TİTCK Tıbbi Cihaz Onaylanmış Kuruluş ve Klinik Araştırmalar Dairesi |
| **Kök hücre** (SHGM Genelge 2018/10) / **insan doku ve hücre ürünleri** (R.G. 4/9/2025, No. 33007) | Klinik Araştırmalar Etik Kurulu | TİTCK Klinik Araştırmalar Dairesi for tissue/cell products; confirm the stem-cell permit route |
| **BA/BE** — bioavailability / bioequivalence | TİTCK-approved **BY/BE Çalışmaları Etik Kurulu** only (Art. 61/12) | TİTCK Klinik Araştırmalar Dairesi |
| **Kozmetik** — cosmetics tested on people (R.G. 20/9/2015, No. 29481) | A committee on TİTCK's "Kozmetik Klinik Etik Kurul Listesi" | TİTCK Kozmetik Ürünler Dairesi |
| **GETAT** — traditional & complementary medicine trials (R.G. 9/3/2019, No. 30709) | As that regulation designates | Sağlık Hizmetleri Genel Müdürlüğü |

> **Legal-validity gate.** Only a committee on TİTCK's approved list can approve
> these studies. TİTCK states that BA/BE decisions from any committee other than an
> approved BY/BE committee are void ("geçersizdir"), and that observational drug
> studies cannot be approved by any committee other than a Klinik Araştırmalar Etik
> Kurulu. Check TİTCK's "Etik Kurul Faaliyet Durumu" list *before* submitting. This
> is the single most common and most expensive routing error.

Governing instrument: *Beşeri Tıbbi Ürünlerin Klinik Araştırmaları Hakkında
Yönetmelik* (Regulation on Clinical Research of Human Medicinal Products),
mevzuat.gov.tr MevzuatNo 40207 (R.G. 27/5/2023, No. 32203; amended by R.G.
29/12/2023, No. 32414 and R.G. 5/6/2025, No. 32921).

---

## Decision Tree

```
Does the study collect data from human participants?
│
├─ NO  → likely no human-subjects ethics review for this skill's scope.
│        (Animal work, purely computational/secondary-public-data work, etc.
│         have their own regimes — out of scope here.)
│
└─ YES
   │
   ├─ Does it involve a drug, medical device, stem cells / tissue-cell
   │  │  products, BA/BE, or cosmetics?
   │  │
   │  ├─ YES → DOOR 2: the committee type in the table above (Klinik
   │  │         Araştırmalar / BY/BE / cosmetics) + the matching TİTCK permit —
   │  │         except observational drug studies (committee only, no permit).
   │  │         Verify the committee is on TİTCK's approved list.
   │  │
   │  └─ NO
   │     │
   │     └─ Collects via survey / interview / focus group / observation /
   │        experiment?
   │        │
   │        ├─ YES → DOOR 1: university Girişimsel Olmayan Etik Kurulu
   │        │         (TR Dizin 2020 trigger).
   │        │
   │        └─ NO  → check edge cases below; many still need Door 1.
   │
   └─ Hits BOTH doors (e.g. a device trial that also runs a participant survey)?
      → The clinical track governs: escalate to DOOR 2.
```

---

## Edge Cases

- **Retrospective record / secondary-data review.** Use of already-collected,
  identifiable participant data is generally still human-subjects research and
  typically needs Door 1 review; confirm with the institution's committee. It needs
  no TİTCK permit, and a Klinik Araştırmalar Etik Kurulu cannot review it (SSS 8,
  70) — unless it is an observational study of a medicinal product, which only that
  committee may approve. If the data are fully and irreversibly anonymized, the
  analysis may fall outside the ethics trigger — but the **anonymization status** is
  a KVKK question; route the data-handling determination to `alterlab-kvkk-dmp`.
- **Generative AI in the study.** YÖK's *Üretken Yapay Zekâ Kullanımına Dair Etik
  Rehber* (Mayıs 2024): "Etik Kurulu başvurusunda ÜYZ kullanımı konusunda Kurula
  gerekli bilgi verilmelidir" — name the tool, its version, and when and at which
  stage it is used — and "Gerçek katılımcılar yerine ÜYZ kullanılması doğru
  değildir" (no synthetic respondents in place of real participants).
- **Minors and vulnerable groups** (çocuklar, gebeler, mahpuslar, bilişsel
  kapasitesi kısıtlı kişiler). Additional safeguards and, for minors, parental/
  guardian consent **plus** age-appropriate assent (çocuk rızası) are required.
  Flag these explicitly in the dossier.
- **Mixed clinical + survey study.** Both doors are in play; the clinical track
  (Door 2) governs and the survey component is reviewed within it.
- **Multi-site / multi-university study.** Each institution may require its own
  committee submission; do not assume one approval covers all sites.
- **No fixed embargo / processing rule is asserted here.** Where a fact (e.g.
  exact form fields, fee, or timeline) is institution-specific, send the user to
  their committee's current documents rather than inventing a value.

---

## Primary Sources

- TİTCK — Klinik Araştırmalar, incl. "Klinik Araştırmalar ilgili Sıkça Sorulan
  Sorular" (SSS 2, 8, 70, 72, 73) and the approved BY/BE, clinical, and cosmetics
  committee lists: https://www.titck.gov.tr/faaliyetalanlari/ilac/klinik-arastirmalar
- *Beşeri Tıbbi Ürünlerin Klinik Araştırmaları Hakkında Yönetmelik* —
  mevzuat.gov.tr MevzuatNo 40207 (R.G. 27/5/2023, No. 32203; amended R.G.
  29/12/2023, No. 32414 and R.G. 5/6/2025, No. 32921), Art. 61/11–12.
- YÖK, *Yükseköğretim Kurumları Bilimsel Araştırma ve Yayın Faaliyetlerinde Üretken
  Yapay Zekâ Kullanımına Dair Etik Rehber* (Mayıs 2024):
  https://proje.yok.gov.tr/documentFiles/17539645334.Y%C3%BCksek%C3%B6%C4%9Fretimde%20%C3%BCretken%20yapay%20zeka%20kullan%C4%B1m%C4%B1-tr.pdf
- TR Dizin (TÜBİTAK ULAKBİM) research-and-publication-ethics criteria — ethics
  approval mandatory for participant data collection in publications from 2020.
  The current criteria page (checked 2026-09-23) requires, for research that needs
  ethics approval, "izinle ilgili bilgilere (kurul adı, tarih ve sayı no) yöntem
  bölümünde, ayrıca makalenin ilk/son sayfalarından birinde" and, for case reports,
  a statement that the signed consent form was obtained: https://trdizin.gov.tr/kriterler/

_Last verified: 2026-09-23 (TİTCK SSS, Yönetmelik text, YÖK guide, TR Dizin
criteria). The trigger-method list and the 2020 start year come from TR Dizin's 2020
criteria and are not repeated on the current page. Committee names, the TİTCK
regulation, and the TR Dizin criteria can change — re-verify against the sources
above before relying on a routing decision for submission._
