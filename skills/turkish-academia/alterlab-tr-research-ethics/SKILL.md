---
name: alterlab-tr-research-ethics
description: "Scaffolds Turkish human-subjects etik kurul (ethics committee) applications and routes a study to the right committee. Survey, interview, focus-group, observation, or experiment studies go to a university non-interventional committee (Girişimsel Olmayan / Bilimsel Araştırma Etik Kurulu; TR Dizin rule). Drug, medical-device, stem-cell, or tissue/cell-product trials need a TİTCK-approved Klinik Araştırmalar Etik Kurulu plus a TİTCK permit; BA/BE studies a BY/BE Etik Kurulu; cosmetics their own regulation; observational drug studies the clinical committee only (no permit). Generates bilingual (TR/EN) Etik Kurul Başvuru Formu, başvuru dilekçesi, and Bilgilendirilmiş Gönüllü Olur Formu, and lints a consent draft against TİTCK's minimum-content list. Use for a Turkish etik kurul başvurusu, an onam/olur formu, which committee a study needs, or TİTCK approval questions. For non-Turkey IRB/GDPR use alterlab-research-ethics; for KVKK data plans use alterlab-kvkk-dmp. Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read Write Edit Bash(python:*)
compatibility: No API key required. Guidance + offline scaffolder; the consent linter (scripts/consent_form_check.py) runs locally via `uv run python` with the Python standard library only.
metadata:
  skill-author: AlterLab
  version: "1.1.0"
  last_updated: "2026-09-23"
  depends_on: "alterlab-research-ethics (international IRB/ethics sibling), alterlab-kvkk-dmp (data-protection plans)"
---

# TR Research Ethics — Turkish Etik Kurul & Onam Form Scaffolder

The Turkey-specific counterpart to `alterlab-research-ethics`. Given a study
description, it answers the first question every Turkish researcher faces —
**which etik kurul** (ethics committee) do I need? — then scaffolds the bilingual
dossier (başvuru formu, dilekçe, onam formu) and lints the consent form against
the TİTCK minimum-content checklist. Glossary on first use: *etik kurul* =
ethics committee; *onam / olur formu* = informed-consent form; *dilekçe* = formal
cover petition; *TİTCK* = Türkiye İlaç ve Tıbbi Cihaz Kurumu (Turkish Medicines
and Medical Devices Agency); *öz* = abstract.

This skill scaffolds and routes. It does **not** grant approval, and a draft it
produces is not a substitute for your institution's own committee templates,
which always take precedence.

## When to Use This Skill

Use it when the request is about **Turkish** human-subjects ethics review:

```
IEU anket çalışması için etik kurul başvurusu hazırla
Bu cihaz çalışması için TİTCK onayı / klinik araştırma etik kurulu gerekir mi?
Draft a Turkish bilgilendirilmiş onam (informed consent) form for an interview study
Which ethics committee do I need for a focus-group study at a Turkish university?
Check my olur formu against the TİTCK minimum-content rules
```

### Does NOT Trigger

Route adjacent requests to the correct sibling skill instead of firing here:

| Request | Route to |
|---------|----------|
| US/EU IRB, Belmont Report, HIPAA, GDPR, non-Turkey ethics board | `alterlab-research-ethics` |
| KVKK-compliant **data management plan**, anonymization, VERBIS, açık rıza data basis | `alterlab-kvkk-dmp` |
| TÜBİTAK Veri Yönetim Planı, Aperta deposit, open-access mandate | `alterlab-aperta` |
| Drafting the TÜBİTAK ARDEB 1001/1002-A **proposal** narrative | `alterlab-tubitak-proposal` |
| Survey **instrument design** / item wording (not the ethics dossier) | `alterlab-survey-design` |
| Qualitative interview/focus-group **method design** | `alterlab-qualitative-methods` |
| Pre-registration of hypotheses & analysis plan | `alterlab-open-science` |
| Checking a journal's TR Dizin indexing status | `alterlab-trdizin` |
| Docentlik (associate-professorship) eligibility / point math | `alterlab-docentlik-eligibility` |
| Akademik teşvik (academic-incentive) scoring | `alterlab-akademik-tesvik` |

The boundary with `alterlab-kvkk-dmp` matters: **ethics review (this skill)** and
**KVKK data protection (that skill)** are two separate legal tracks for the same
study. A full project usually needs both — scaffold the etik kurul dossier here,
then hand off to `alterlab-kvkk-dmp` for the data plan.

---

## The Routing Rule (do this first)

Turkish ethics review has **two doors**, and sending a study to the wrong one
wastes a review cycle. Route by what the study *does*, per
`references/etik_kurul_routing.md`:

**Door 1 — Üniversite Girişimsel Olmayan (non-interventional) Etik Kurulu.**
Triggered by the TR Dizin/ULAKBİM rule (mandatory for publications from **2020**):
any study collecting data **from participants** via **survey (anket), interview
(görüşme), focus group (odak grup), observation (gözlem), or experiment (deney)**
needs ethics-committee approval. For non-clinical social/behavioral/education
research this is the researcher's own university non-interventional committee.
Two rules keep studies out of the wrong door: a study with no direct intervention
**still needs** ethics approval (TİTCK SSS 72, citing Helsinki), and a TİTCK Klinik
Araştırmalar Etik Kurulu **may not** review surveys, retrospective record studies,
or other non-interventional work outside its remit (Yönetmelik Art. 61/11; TİTCK
SSS 70). Those go to the university committee (TİTCK SSS 73: "müdahalesiz
çalışmalar etik kurulu, bilimsel araştırmalar etik kurulu vb.").

**Door 2 — TİTCK-regulated research: a designated committee, usually plus a permit.**
Per TİTCK, clinical research is conducted "TİTCK tarafından onay verilen Etik
Kurulların onayı ve Sağlık Bakanlığının izni ile." Which committee and which permit
depend on the product (Yönetmelik Art. 61/11–12; TİTCK Klinik Araştırmalar SSS 2, 8, 70):

| Study | Ethics committee | Permit |
|-------|------------------|--------|
| Drug (beşeri tıbbi ürün) clinical trial or low-risk scientific study | TİTCK-approved Klinik Araştırmalar Etik Kurulu | TİTCK Klinik Araştırmalar Dairesi |
| Observational study of a medicinal product | Klinik Araştırmalar Etik Kurulu **only** | **None** — no TİTCK permit |
| Medical-device clinical investigation or post-market study (R.G. 8/7/2022, No. 31890) | Klinik Araştırmalar Etik Kurulu | TİTCK Tıbbi Cihaz Onaylanmış Kuruluş ve Klinik Araştırmalar Dairesi |
| Stem cells (SHGM Genelge 2018/10) or human tissue/cell products (R.G. 4/9/2025, No. 33007) | Klinik Araştırmalar Etik Kurulu | TİTCK for tissue/cell products; confirm the stem-cell permit route |
| Bioavailability/bioequivalence (BA/BE) | TİTCK-approved BY/BE Çalışmaları Etik Kurulu **only** | TİTCK Klinik Araştırmalar Dairesi |
| Cosmetics tested on people (R.G. 20/9/2015, No. 29481) | A committee on TİTCK's Kozmetik Klinik Etik Kurul list | TİTCK Kozmetik Ürünler Dairesi |

**Only a committee on TİTCK's approved list can approve these studies**: TİTCK calls
BA/BE decisions from any other committee void ("geçersizdir"), and observational drug
studies cannot be approved by any committee other than a Klinik Araştırmalar Etik
Kurulu. Check TİTCK's "Etik Kurul Faaliyet Durumu" list before you submit.

Governing instrument: *Beşeri Tıbbi Ürünlerin Klinik Araştırmaları Hakkında
Yönetmelik* (Regulation on Clinical Research of Human Medicinal Products),
mevzuat.gov.tr MevzuatNo 40207 (R.G. 27/5/2023, No. 32203; amended by R.G.
29/12/2023, No. 32414 and R.G. 5/6/2025, No. 32921). See
`references/etik_kurul_routing.md` for the full decision tree, edge cases
(retrospective record review, secondary data, minors/vulnerable groups), and
source citations.

> Some studies hit **both** doors (e.g. a device trial that also runs a patient
> survey). When in doubt, the clinical track governs and you escalate to Door 2.

---

## What It Produces

A bilingual (Turkish primary, English gloss) dossier skeleton. Pull the
templates from `references/dossier_templates.md`:

1. **Etik Kurul Başvuru Formu** — application form skeleton: title, PI/araştırmacı
   roster, aim & rationale (öz), design, population & sample, instruments,
   risk/benefit, data-handling summary (with a pointer to the KVKK plan), and the
   informed-consent procedure.
2. **Başvuru Dilekçesi** — the formal cover petition addressed to the committee.
3. **Bilgilendirilmiş Gönüllü Olur Formu** — the participant-facing consent form,
   built to satisfy the TİTCK minimum-content checklist (below).
4. **Ek/CV bundle checklist** — instruments, measurement tools, researcher CVs,
   data-collection-permission letters, and any institutional annexes.

Always tell the user that **their own university committee's official form
overrides this skeleton** where the two differ.

---

## Consent-Form Minimum Content (TİTCK KAD-DD-13)

The Bilgilendirilmiş Gönüllü Olur Formu must, at minimum, carry the elements in
`references/consent_minimum_contents.md`, taken from TİTCK's "BGOF'de Bulunması
Gereken Asgari Bilgiler" (KAD-DD-13). Headline items:

- **Date, version, and "page X of Y" numbering on every page** (and, for
  clinical-track forms, volunteer initials on every page except the signature page).
- **Plain-language** statement of purpose, procedures, expected duration, and
  what participation involves.
- **Foreseeable risks/discomforts and benefits**, stated honestly.
- A **24-hour contact** for problems or questions.
- An explicit statement that participation is **voluntary** and the participant
  may **withdraw at any time without penalty**.
- An explicit **no-coercion** statement.
- For clinical-track studies: insurance, alternative treatments, and the
  sponsor/contact chain as the regulation requires.
- A **signature block** with the volunteer's and the informing researcher's name,
  signature, and date (plus witness / parent or legal guardian where needed).

### Lint a draft consent form

```bash
uv run python skills/turkish-academia/alterlab-tr-research-ethics/scripts/consent_form_check.py \
    path/to/olur_formu.md
```

The linter (`scripts/consent_form_check.py`, standard-library only) scans a draft
for the required elements above (in Turkish or English) and prints a per-element
PASS / MISSING table plus an overall verdict. It is a **completeness aid, not a
legal sign-off**: a PASS means the checklist elements are present, not that the
wording satisfies the committee. Run it, read the JSON/table, and report the
MISSING items to the user with the exact element name.

---

## Workflow

1. **Classify the study** → run the routing rule. State which door (committee
   type) applies and *why*, citing the trigger (e.g. "collects interview data →
   non-interventional committee" or "tests a medical device → TİTCK clinical
   committee + permit").
2. **Flag the clinical-track gate** when Door 2 applies: remind the user to
   confirm the committee is on TİTCK's approved list for that study type and
   whether a TİTCK permit is required (yes for trials and BA/BE; no for
   observational drug studies).
3. **Scaffold the dossier** from `references/dossier_templates.md`, filled with
   the study's specifics; keep Turkish as the primary language with an English
   gloss. If generative AI (ÜYZ) is used anywhere in the study, the application must
   say so: YÖK's *Üretken Yapay Zekâ Kullanımına Dair Etik Rehber* (Mayıs 2024) asks
   for the tool, its version, and when and at which stage it is used, and states that
   AI must not stand in for real participants ("Gerçek katılımcılar yerine ÜYZ
   kullanılması doğru değildir").
4. **Build & lint the consent form** against the TİTCK checklist; run
   `scripts/consent_form_check.py` and surface MISSING elements.
5. **Hand off** the data-protection half to `alterlab-kvkk-dmp` and (if funded /
   open-access) the deposit half to `alterlab-aperta`.
6. **Disclaim**: outputs are drafts; the institution's official forms and the
   committee's own decision are authoritative. Caps, forms, and checklists change
   — verify against the current TİTCK / university committee documents before
   submission.

---

## Self-Check Before Reporting

- Did I name the **specific committee type** (non-interventional, Klinik
  Araştırmalar, BY/BE, or cosmetics) and the trigger that put the study there, and
  did I say whether a TİTCK permit is needed (not for observational drug studies)?
- For any clinical-track study, did I flag the **TİTCK-approval + separate permit**
  requirement and the "non-approved committee = legally void" rule?
- Did I run the consent linter and report **MISSING** elements by name, not just a
  pass/fail?
- Did I route data-protection to `alterlab-kvkk-dmp` rather than improvising KVKK
  advice here?
- If the study uses generative AI, does the dossier state the tool, version, stage,
  and purpose (YÖK ÜYZ Etik Rehberi, 2024)?
- Did I state that institutional forms override the skeleton and that figures/rules
  must be verified against current sources?

---

## References

- `references/etik_kurul_routing.md` — full two-door decision tree, trigger list,
  edge cases, and primary-source citations.
- `references/consent_minimum_contents.md` — the TİTCK minimum-content checklist
  the linter enforces, element by element.
- `references/dossier_templates.md` — bilingual başvuru formu, dilekçe, and olur
  formu skeletons plus the annex checklist.

### Primary sources

- TİTCK — Klinik Araştırmalar, incl. the SSS (FAQ) and approved-committee lists. https://www.titck.gov.tr/faaliyetalanlari/ilac/klinik-arastirmalar
- *Beşeri Tıbbi Ürünlerin Klinik Araştırmaları Hakkında Yönetmelik* — mevzuat.gov.tr MevzuatNo 40207 (R.G. 27/5/2023, No. 32203; amended R.G. 29/12/2023, No. 32414 and R.G. 5/6/2025, No. 32921).
- TİTCK KAD-DD-13, "BGOF'de Bulunması Gereken Asgari Bilgiler" (informed-consent minimum contents), linked from the TİTCK clinical-research page.
- YÖK, *Yükseköğretim Kurumları Bilimsel Araştırma ve Yayın Faaliyetlerinde Üretken Yapay Zekâ Kullanımına Dair Etik Rehber* (Mayıs 2024).
- TR Dizin (TÜBİTAK ULAKBİM) research-and-publication-ethics criteria — ethics-committee approval mandatory for participant data collection in publications from 2020; the article must give the committee name, date, and decision number in the method section and on the first or last page. https://trdizin.gov.tr/kriterler/

Part of the AlterLab Academic Skills suite.
