# TÜBİTAK Açık Bilim Politikası — Binding Mandates

> **Last verified: 2026-09-23** against the policy PDF and the ARDEB *Veri Yönetim Planı
> Bilgi Notu*. TÜBİTAK can revise the policy; re-confirm before a researcher relies on it.

## Source documents

- **TÜBİTAK Açık Bilim Politikası** (Open Science Policy) PDF —
  `https://tubitak.gov.tr/sites/default/files/tubitak_acik_bilim_politikasi_190316.pdf`
  (accepted by the TÜBİTAK Board on 14 March 2019; in force from that date, piloted and then
  extended to all programmes within a year — İlke 11).
- **ARDEB Veri Yönetim Planı** template and note —
  `https://tubitak.gov.tr/sites/default/files/2024-04/veri_yonetim_plani.docx`,
  `https://tubitak.gov.tr/sites/default/files/2024-04/veri_yonetim_plani_bilgi_notu.pdf`
- **ULAKBİM — Türkiye Açık Arşivi / Aperta** —
  `https://ulakbim.tubitak.gov.tr/en/turkey-open-archive-aperta/`
- Aperta repository: `https://aperta.ulakbim.gov.tr/`

Scope (policy "Kapsam"): publications (peer-reviewed articles etc.) and research data produced
wholly or partly with **TÜBİTAK support** — which the policy defines broadly as scholarships,
awards, incentives and grants — plus the publications and data of TÜBİTAK's own researchers.

The policy has eleven numbered principles (İlkeler). The ones that bind researchers are below,
with the policy's own wording.

## İlke 1 — Green-road deposit in Aperta, on acceptance

> "TÜBİTAK Yeşil Yol Açık Erişim ile tümüyle ya da kısmen TÜBİTAK desteğiyle üretilmiş hakemli
> makalelerin yayına kabul edilmiş sürümüne ait bir kopyanın TÜBİTAK Açık Arşivinde
> depolanmasını zorunlu kılar. (Depolama, materyal yayına kabul edilir edilmez yapılmalı ve
> depolama tarihinden itibaren tüm üst veriler tamamıyla açık taranabilir ve makine tarafından
> okunabilir olmalıdır.)"

- **What:** the **kabul edilmiş makale** (accepted manuscript / author-accepted version) of every
  peer-reviewed article produced wholly or partly with TÜBİTAK support.
- **Where:** the **TÜBİTAK Açık Arşivi — Aperta** (the policy names it; another repository does
  not satisfy this principle).
- **When:** as soon as the article is accepted — not after publication.
- **Metadata:** fully open, crawlable and machine-readable from the deposit date, even while the
  full text is embargoed.

## İlke 2 — When the full text must become open (field-dependent)

> "TÜBİTAK, yayınların tam metinlerinin mümkünse yayına kabul edilir edilmez, değilse Fen
> Bilimleri, Teknoloji, Mühendislik ve Matematik alanları için yayınlanmasından sonra 6 aydan
> geç olmamak üzere, Sosyal ve Beşeri Bilimler için de yayınlanmasından sonra 12 aydan geç
> olmamak üzere, erişime açılmasını zorunlu kılar."

| Field bucket (policy wording) | Latest open-access date |
|-------------------------------|-------------------------|
| Fen Bilimleri, Teknoloji, Mühendislik ve Matematik (STEM) | **6 months after publication** |
| Sosyal ve Beşeri Bilimler (SSH) | **12 months after publication** |

- The preferred outcome is open access **on acceptance**; the 6/12 months are ceilings.
- The clock starts at **publication** (*yayınlanmasından sonra*), while the deposit itself is due
  at acceptance (İlke 1). Set the Aperta embargo end date from the publication date.
- A publisher embargo longer than the ceiling conflicts with the policy — flag it before the
  author signs the copyright form.

## İlke 3 — Gold OA, copyright retention, open licences (recommended)

TÜBİTAK recommends publishing in open-access venues (altın yol) where there is no conflict of
interest, encourages authors to keep their copyright and transfer only the rights needed for
publication, and recommends licensing for the widest access (a widely used open-access licence
model may be chosen).

## İlke 4 — Data management plan at application time

> "TÜBİTAK, … yayınlara ilişkin araştırma verilerine açık erişim için, destek başvuru sürecinde
> araştırma verileri yönetim planının hazırlanmasını önerir."

The policy itself *recommends* a VYP; for **ARDEB programmes** the *VYP Bilgi Notu* makes it a
submission item: the Veri Yönetim Planı "diğer başvuru belgeleriniz ile birlikte Proje Başvuru
Sistemi'ne yüklenmesi gerekmektedir." The note accepts that not every section can be answered at
the start — some answers can be completed later, and the long-term preservation section can be
updated in progress and final reports. The official template is the five-question form mapped in
`vyp_template.md`. The note also recommends sharing project data in Aperta.

## İlke 5 — Open access to publications and their data (recommended)

TÜBİTAK recommends open access for publications and the research data behind them.

## İlke 6 — Documenting data that cannot be open

> "TÜBİTAK, veriler yasal, mahremiyet veya diğer kaygılar nedeniyle tamamen veya belirli bir
> süre açık olamazsa (örneğin kişisel veya hassas veriler, gizlilik, ulusal güvenlik, sınai
> mülkiyet haklarına ilişkin tescil süreleri vb.) bu durumun belgelenmesini ve açıkça ifade
> edilmesini zorunlu kılar."

Valid grounds named or covered by the policy: personal or sensitive data (**KVKK**, Law 6698 —
health, genetic, biometric data included), confidentiality, national security, industrial-property
registration periods (e.g. a pending patent), and other legal or privacy concerns such as an
**etik kurul** restriction. Closure can be total or **temporary** ("belirli bir süre").

The compliant Aperta pattern is a **restricted (or embargoed) record with open metadata**: the
dataset stays discoverable and citable (DOI + metadata) while file access is gated. The written
justification is carried into both the VYP and the final report.

Bridge to KVKK: a dataset claimed as "anonymised" only qualifies for open release if it is
**genuinely non-re-identifiable**. Re-identifiable pseudonymised data is still personal data under
KVKK and must stay closed/restricted. Get this determination from `alterlab-kvkk-dmp`.

## İlke 7 and 8 — Templates, legality, citation

TÜBİTAK prepares VYP templates and guides (İlke 7). Archiving electronic copies of scholarly work
with the author's permission is lawful, and anyone reusing material from the Archive must cite
the source (İlke 8).

## İlke 9 — Compliance is reported and has consequences

> "TÜBİTAK, hak sahibinin araştırma performansını ve gelecekteki destek başvurularını
> değerlendirirken bu politikaya uygun davranma durumunu göz önüne alacaktır. Hak sahibi,
> TÜBİTAK Açık Bilim Politikasına uyacağını kabul eder ve proje sonuç raporunda politikaya
> uygunluğunu raporlar."

- The grantee reports policy compliance in the project **sonuç raporu** (final report): per
  output, the Aperta DOI, access mode, open-access date, and — for closed data — the İlke-6
  justification.
- Non-compliance can count against the grantee's future TÜBİTAK applications.

## What is deliberately NOT encoded here

- Any TRY budget cap, application deadline or program-specific rule (those belong to
  `alterlab-tubitak-proposal`).
- A fixed maximum embargo for **data**: the 6/12-month ceilings in İlke 2 apply to publication
  full texts; data closure follows İlke 6 (documented, possibly temporary).
- Publisher-specific self-archiving terms — check the journal's policy (e.g. via Sherpa
  Romeo) against the İlke 2 ceiling.
