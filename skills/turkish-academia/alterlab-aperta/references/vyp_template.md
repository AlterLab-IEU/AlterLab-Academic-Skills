# Veri Yönetim Planı (VYP) / Data Management Plan — Section Tree

> **Last verified: 2026-09-23.** For ARDEB programmes the VYP is uploaded to PBS with the
> other application documents (VYP Bilgi Notu) and covers the full data lifecycle. Confirm
> the current template before submission — TÜBİTAK may update it.

## The official ARDEB form — five questions

The template TÜBİTAK links from the 1001 and 1002-A pages
(`https://tubitak.gov.tr/sites/default/files/2024-04/veri_yonetim_plani.docx`) opens with a
statement that the plan is prepared in line with the TÜBİTAK Açık Bilim Politikası and then
asks five questions:

| Q | Official question (TR, abridged) | What the explanation asks for |
|---|----------------------------------|-------------------------------|
| 1 | Araştırmanız sırasında hangi tür veriler kullanılacak ve/veya elde edilecektir? | Data types and formats, folder/file naming, metadata standards, and any data transferred from third parties |
| 2 | Proje kapsamında elde edilecek veya üretilecek veri, paylaşım ve tekrar kullanım için uygun olacak mıdır? (Evet / Hayır) | Discoverability measures, sharing conditions or restrictions, a data-sharing agreement if any, timing of release; datasets behind published figures should be reusable. **Evet → answer 3, 4, 5. Hayır → explain why and answer only 5.** |
| 3 | Veriler araştırma devam ederken nerede saklanacaktır? | Retention period, backup frequency and formats (with software if needed), the person responsible and their duties |
| 4 | Proje tamamlandıktan sonra veriler uzun süreli olarak nasıl saklanacak, hangi altyapılar kullanılacak, üçüncü taraflarla nasıl paylaşılacak, kimler erişebilecek? TÜBİTAK'ın planından farklı bir planınız var mı? | Long-term preservation plan and infrastructure; may be updated in progress/final reports |
| 5 | Diğer Önemli Hususlar | Approvals (KVKK compliance, etik kurul), participant confidentiality and anonymisation, secure handling of sensitive data, data owner, reuse licence, access restrictions and authorisation, encryption, and any delay in sharing (patent filing, journal embargo) |

The eight-part scaffold below is a drafting aid; paste its content into the five questions:

| Official question | Scaffold sections |
|-------------------|-------------------|
| 1 | 1 Veri Toplama ve Üretme, 2 Veri Formatları ve Standartları |
| 2 | 5 Veri Paylaşımı ve Erişim (and the Evet/Hayır decision) |
| 3 | 3 Veri Depolama ve Yedekleme, 8 Sorumluluklar ve Kaynaklar |
| 4 | 7 Uzun Süreli Saklama ve Koruma |
| 5 | 4 Yasal ve Etik Hususlar, 6 Kapalı Veri Gerekçesi (İlke-6) |

## Scaffold section tree

This is the bilingual (TR/EN) section tree that `scripts/vyp_scaffold.py` emits.
It follows the data-lifecycle structure of the TÜBİTAK Açık Bilim Politikası (see
`policy_mandates.md`). It is a **scaffold**, not the official form verbatim — fill
each section with the project's specifics, then transfer it into the five questions.

| # | Turkish | English | What goes here |
|---|---------|---------|----------------|
| 1 | Veri Toplama ve Üretme | Data collection & generation | What data the project will create/collect; types, sources, volume; how/with what instruments |
| 2 | Veri Formatları ve Standartları | Formats & standards | File formats, metadata standards, naming conventions, documentation |
| 3 | Veri Depolama ve Yedekleme | Storage & backup | Where data lives during the project; backup; access control; security |
| 4 | Yasal ve Etik Hususlar | Legal & ethical considerations | **KVKK** lawful basis, personal/special-category data, **etik kurul** approval, consent; informs which data can be opened |
| 5 | Veri Paylaşımı ve Erişim | Sharing & access | What is shared openly vs restricted; repository = **Aperta**; publication full texts open ≤ 6 months (STEM) / ≤ 12 months (SSH) after publication (İlke 2); licence |
| 6 | Kapalı Veri Gerekçesi (İlke-6) | Closed-data justification (Principle 6) | If any data stays closed: the documented reason (KVKK/commercial/security/ethics), restricted-access plan, who may request access, opening trigger |
| 7 | Uzun Süreli Saklama ve Koruma | Long-term preservation | Retention period; preservation after project end; deletion/anonymisation plan |
| 8 | Sorumluluklar ve Kaynaklar | Roles & resources | Who is responsible for data management; resources/costs |

## How the script populates it

- `--field stem|ssh` writes the publication open-access ceiling (İlke 2) into the header
  and section 5.
- `--data-closed` activates section 6 and inserts an İlke-6 stub; `--closed-reason`
  picks the justification wording (KVKK / commercial / security / ethics).
- `--lang tr|en|both` selects Turkish, English, or a stacked bilingual document.

## KVKK / İlke-6 cross-link (important)

Sections 4 and 6 are where the **KVKK** decision lands. This skill records *that*
data is open or closed and *why* at the funder level. It does **not** run the KVKK
lawful-basis / anonymisation analysis — that is `alterlab-kvkk-dmp`'s job. Workflow:

1. Run `alterlab-kvkk-dmp` to get the lawful basis and the anonymisation/
   pseudonymisation outcome.
2. Paste that conclusion into VYP section 4, and — if data stays closed — into the
   İlke-6 justification in section 6.

This way one pass yields both the funder-facing VYP and the KVKK-compliance plan,
with the İlke-6 "why closed" paragraph populated from the KVKK decision.

## Disclaimer

Tell the user to verify the current VYP template and any programme-specific
guidance against the live TÜBİTAK pages before submitting, and to transfer the
scaffold into the official five-question form — the scaffold is not the form.
