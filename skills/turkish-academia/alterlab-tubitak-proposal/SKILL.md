---
name: alterlab-tubitak-proposal
description: "Scaffolds TÜBİTAK ARDEB proposals in the directorate's own section order: 1001 against the official .doc form (TR/EN özet ≤600 words each, ÖZGÜN DEĞER, YÖNTEM, PROJE YÖNETİMİ with iş paketleri and B Planı, YAYGIN ETKİ, EK-1/EK-2; ≤25 pages), and the PBS-typed 1002-A Hızlı Destek and 3501 Kariyer Geliştirme forms with per-section word ranges. Checks program caps (1001 ≤36 months, 3,000,000 TRY; 1002-A ≤12 months, 150,000 TRY/year; 3501 ≤36 months, 1,500,000 TRY, PI ≤7 years post-PhD, doçent or below), drafts to each program's criteria (1001 panel 35/25/20/20; 3501 adds kariyer geliştirme potansiyeli) and applies TÜBİTAK's generative-AI (ÜYZ) disclosure rules; submission via PBS after ARBİS. Delegates generic grant craft to alterlab-research-grants and BİDEB fellowships to alterlab-tubitak-bideb. Use when the user wants to write a TÜBİTAK 1001, 1002-A or 3501 proposal, draft özgün değer or yaygın etki sections, or map broader-impacts framing to TÜBİTAK terms. Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read Write Edit Bash(python:*) WebFetch
compatibility: No API key required — generates proposal scaffolds offline; the structure checker runs via `uv run python` on stdlib only. Program caps/forms change by call period; WebFetch the live program pages to confirm before submission.
metadata:
  skill-author: AlterLab
  version: "1.2.0"
  last_updated: "2026-09-23"
  depends_on: "alterlab-research-grants (generic grant-craft this skill delegates to)"
---

# TÜBİTAK ARDEB Proposal Scaffolder — 1001, 1002-A & 3501

Scaffolds a TÜBİTAK ARDEB (Araştırma Destek Programları Başkanlığı — the Research
Support Programmes directorate) proposal against the **official form structure**, in the
directorate's own Turkish section order, then maps the researcher's content into each
heading and checks the limits a proposal is returned on. It owns the **Turkish-specific
form structure, terminology, and program rules** only — generic grant-craft (broader-impacts
argumentation, feasibility narrative, Gantt aesthetics) is delegated to
`alterlab-research-grants`.

Three variants:

- **1001** — *Bilimsel ve Teknolojik Araştırma Projelerini Destekleme Programı* (Support
  Programme for Scientific and Technological Research Projects). The full program: an uploaded
  .doc form, two calls a year, panel evaluation.
- **1002-A** — *Hızlı Destek Modülü* (Fast Support Module). Short, small-budget, rolling. Since
  the 2025 redesign there is **no .doc template**: the applicant types each section into the PBS
  screens (with word ranges) and the system generates the form. It also funds needs arising in an
  accepted doctoral thesis, with the doctoral student as PI.
- **3501** — *Kariyer Geliştirme Programı* (Career Development Programme). Project support for
  early-career PIs: within 7 years of the doctorate (for 2026 applications, degree dated
  01.01.2019 or later; +1 year per birth), doçent or lower, never funded by 3501 before. Rolling,
  typed into PBS screens with word ranges like 1002-A, and adds a **Kariyer Geliştirme
  Potansiyeli** section and the PI's thesis information.

## Quick Start

```
Write me a TÜBİTAK 1001 proposal outline for <topic>
Draft the özgün değer (original value) section for my ARDEB 1001
Scaffold a 1002-A Hızlı Destek başvurusu
3501 Kariyer Geliştirme projemin başlıklarını ve kelime sınırlarını çıkar
Turn my NSF broader-impacts paragraph into a TÜBİTAK yaygın etki section
```

→ Pick the variant, generate the section tree (`scripts/scaffold_proposal.py`), draft each
heading from the user's material, then run the structure check
(`scripts/scaffold_proposal.py --check`) before reporting. Include the **verify-current-call**
note every time — caps, forms and word ranges change by call period.

## When to Use This Skill

Use this skill when the request is to **author, outline, or section-map a TÜBİTAK ARDEB
1001, 1002-A or 3501 proposal**, check a 3501 PI's career-stage eligibility, draft a specific
Turkish section (özgün değer = original value; yaygın etki = broader impact/dissemination;
yöntem = method; iş paketi = work package; kariyer geliştirme potansiyeli = career-development
potential), or translate international broader-impacts framing into TÜBİTAK terminology.

### Does NOT Trigger

The route below sends adjacent requests to the correct sibling skill in the suite. This skill
does **not** check journal indexing, compute career points, or write a non-Turkish grant.

| The request is really about… | Route to |
|------------------------------|----------|
| Generic grant-craft / NSF / NIH / ERC narrative, broader-impacts argumentation in the abstract | `alterlab-research-grants` |
| A **BİDEB** fellowship, bursary, visiting-scientist or event support (2218, 2219, 2221, 2232-A/B, 2236-A, 2224-A, 2223-B) | `alterlab-tubitak-bideb` |
| Interim/final progress report (gelişme/sonuç raporu) for an **awarded** TÜBİTAK project | `alterlab-grant-reporting` |
| Is a target journal in **TR Dizin** (national index)? | `alterlab-trdizin` |
| Does a candidate clear **doçentlik** (associate-professor) point thresholds? | `alterlab-docentlik-eligibility` |
| Computing the **akademik teşvik** (academic-incentive) net score | `alterlab-akademik-tesvik` |
| The **etik kurul** (ethics-committee) application / informed-consent form | `alterlab-tr-research-ethics` |
| The KVKK-compliant data-management plan / TÜBİTAK Veri Yönetim Planı | `alterlab-kvkk-dmp` |
| Depositing the accepted manuscript on **Aperta** under the Open Science Policy | `alterlab-aperta` |
| Turkish APA-7 / TR Dizin manuscript style for the paper itself | `alterlab-tr-academic-style` |
| Searching DergiPark / YÖK theses for the literature review | `alterlab-dergipark`, `alterlab-yok-tez` |

---

## The Form Trees

Section names are the directorate's own headings; `references/form_structure.md` has the full
annotated trees and a drafting brief per heading.

**1001 (official .doc form)**

| # | Section (TR) | English gloss |
|---|--------------|---------------|
| Özet | ÖZET (TR) + ABSTRACT (EN), each with keywords | Two separate blocks, **≤ 600 words each** |
| 1 | **ÖZGÜN DEĞER** — 1.1 Konunun Önemi ve Projenin Özgün Değeri; 1.2 Araştırma Sorusu ve/veya Hipotezi; 1.3 Amaç ve Hedefler | Original value; research question; aim & measurable objectives |
| 2 | **YÖNTEM** | Method (carries feasibility / yapılabilirlik) |
| 3 | **PROJE YÖNETİMİ** — 3.1 Yönetim Düzeni: İş-Zaman Çizelgesi (önem % totalling 100) ve İş Paketleri (başarı ölçütü, ara çıktılar, risk yönetimi + **B Planı**); 3.2 Araştırma Olanakları | Work–time chart, work packages, contingency, facilities |
| 4 | **YAYGIN ETKİ** — 4.1 Öngörülen Çıktılar; 4.2 Öngörülen Etkiler; 4.3 Yayılım ve Bilim İletişimi Faaliyet Planı | Outputs, impacts, dissemination plan |
| EK-1 / EK-2 | Kaynaklar; Bütçe ve Gerekçesi | References; budget & justification |
| EK-3 | Proje Ekibinin Diğer Projeleri ve Güncel Yayınları | Generated by PBS — nothing to draft |

**1002-A (PBS entry screens, word ranges from the Dec-2025 Başvuru İçeriği Bilgi Notu)**

| # | Section (TR) | Words |
|---|--------------|-------|
| 1 | **BİLİMSEL NİTELİK** — Konunun Önemi ve Projenin Bilimsel Niteliği (incl. research question/hypotheses); Amaç ve Hedefler | 1,000–3,500; 100–1,000 |
| 2 | **YÖNTEM** | 750–3,000 |
| 3 | **PROJE YÖNETİMİ** — built from the İş Paketleri step (başarı ölçütü, önem %, risks + B Planı) | — |
| 4 | **ÇIKTI, ETKİ VE KAZANIMLAR** | 100–400 |
| – | Belirtmek İstediğiniz Diğer Konular (optional) | ≤ 250 |
| EK-1 / EK-2 | Kaynakça step (DOI where one exists); budget steps | — |

**3501 (PBS entry screens, word ranges from the 3501 Başvuru İçeriği Bilgi Notu, 2026-05 upload)**

| # | Section (TR) | Words |
|---|--------------|-------|
| – | **PROJE YÜRÜTÜCÜSÜNÜN TEZ BİLGİLERİ** — master's thesis title + yaygın etki (if any); doctoral/uzmanlık thesis title + yaygın etki | ≤ 150; 50–350 |
| 1 | **ÖZGÜN DEĞER** — Konunun Önemi, Projenin Özgün Değeri; Araştırma Sorusu veya Hipotezi; Amaç ve Hedefler | 1,000–4,000; 100–400; 150–500 |
| 2 | **YÖNTEM** | 1,000–3,750 |
| 3 | **PROJE YÖNETİMİ** — İş Paketleri step (başarı ölçütü, önem % totalling 100, ara çıktılar, risks + B Planı); Araştırma Olanakları | — |
| 4 | **KARİYER GELİŞTİRME POTANSİYELİ** | 250–700 |
| 5 | **YAYGIN ETKİ** — 5.1 Öngörülen Çıktılar; 5.2 Öngörülen Etkiler; 5.3 Yayılım ve Bilim İletişimi (Hedef Kitle, Hedefler ve Beklenen Kazanımlar, Kullanılacak Araçlar, Zamanlama) | —; 50–400; 10–125, 10–125, 5–100, 5–75 |
| – | Belirtmek İstediğiniz Diğer Konular (optional) | ≤ 500 |
| EK-1 / EK-2 | Kaynaklar (DOI mandatory where one exists); Bütçe ve Gerekçesi | — |

**Map, don't invent.** Evaluators score against *these* headings; never silently restructure
them into an IMRaD paper. In every variant literature review, report writing, dissemination,
article writing and procurement are **not** work packages.

---

## The Hard Limits

A proposal that breaks these can be returned without scientific review. The checker pins them;
`references/program_profiles.md` has the full table with sources, read on 2026-09-23.

| Item | 1001 | 1002-A | 3501 |
|------|------|--------|------|
| Duration | **≤ 36 months** | **≤ 12 months** | **≤ 36 months** |
| Budget upper limit | **3,000,000 TRY**, burs dahil, PTİ and kurum hissesi hariç, no annual sub-limit (from the 2026-1 period) | **150,000 TRY per year**, burs dahil, no PTİ (from 2026-02-01) | **1,500,000 TRY**, burs dahil, PTİ and kurum hissesi hariç, no annual sub-limit (from 2026-02-01); no infrastructure projects |
| Format | .doc form, Arial 9, unchanged template, **≤ 25 pages excl. EK-1/EK-2**, one file ≤ 20 MB, no content behind external links | PBS text fields within the word ranges above | PBS text fields within the word ranges above; no content behind external links |
| Özet | TR and EN, ≤ 600 words each | Not stated in the bilgi notu — check the PBS "Proje Bilgileri" step | Not stated in the bilgi notu — check the PBS "Proje Bilgileri" step |
| Window | Two calls a year (2026-2: 29 Jul – 14 Sep 2026, closed; next call on the program page) | Rolling, year-round; e-imza within 15 days of approving the application | Rolling, year-round; e-imza within 15 days of approving the application |
| PI | Doctorate + kadrolu/tam zamanlı staff of the executing institution | Doctorate (university/hospital) or qualified doctoral/uzmanlık/sanatta yeterlik student applying for their thesis needs | As 1001, plus: ≤ 7 years after the doctorate (2026: degree dated 01.01.2019 or later; +1 year per birth), doçent or lower, no earlier 3501; professors cannot join as researchers |

> **Verify-current-call note (include it every time).** Every TRY figure, page limit, word range
> and duration is dated. Before the user submits, WebFetch the live program page (and, for 1002-A
> and 3501, the current Başvuru İçeriği Bilgi Notu) listed in `references/program_profiles.md` and
> reconcile.

---

## How Proposals Are Scored

**1001** goes to a panel with these weights (official panel evaluation form); draft each section
to its criterion. Full criteria in `references/review_criteria.md`.

| Criterion (TR) | Weight | Carried mainly by |
|----------------|--------|-------------------|
| **Özgün Değer** | 35% | Özet, §1 ÖZGÜN DEĞER, EK-1 |
| **Yöntem** | 25% | §2 YÖNTEM |
| **Proje Yönetimi** | 20% | §3 (iş paketleri, B Planı, §3.2) |
| **Yaygın Etki** | 20% | §4 YAYGIN ETKİ, EK-2 |

**1002-A** goes to external advisors (dış danışman) on three criteria: Bilimsel Nitelik, Proje
Yönetimi, Çıktı-Etki-Kazanımlar.

**3501** is scored on five criteria — **Özgün Değer, Yöntem, Proje Yönetimi, Kariyer Geliştirme
Potansiyeli, Yaygın Etki** — each question rated on a six-level scale (Çok iyi … Çok yetersiz).
The 3501 evaluation form **publishes no weights**: never apply 1001's 35/25/20/20 to a 3501
draft. The career criterion asks how the PI's master's/doctoral work relates to the proposal and
what new skills or interdisciplinary capability the project brings — so fill the thesis step and
§4 with specifics, not a CV summary.

---

## Generative-AI Use — TÜBİTAK ÜYZ Rehberi (Eylül 2025; v04, Ocak 2026)

TÜBİTAK's *Destek Süreçlerinde Üretken Yapay Zekânın (ÜYZ) Sorumlu ve Güvenilir Kullanımı
Rehberi* (`tubitak.gov.tr/sites/default/files/2025-09/uyz_rehberi_ardeb.pdf`, still linked from
the ARDEB forms) applies to every TÜBİTAK application and to progress/final reports. The guide
page (`tubitak.gov.tr/tr/kurumsal/hakkimizda/uretken-yapay-zeka-rehberi`) now serves **v04, Ocak
2026** (`2026-01/UYZ_Rehberi_v04_TR.pdf`, read 2026-09-23), which keeps the rules below. Because
this skill *is* generative-AI help, tell the user what the guide asks of them:

- **Declare significant use.** Drafting any section, generating code or figures, or producing
  content that supports the main arguments counts as significant (plain spelling/grammar checks
  do not). The declaration goes in the section PBS provides for it and names the tool and
  version, the sections or stages where it was used, and the nature of the use (first draft,
  editing, code, translation).
- **The applicant stays fully responsible.** Treat drafts from this skill as a starting point to
  rewrite in the applicant's own words, and verify every claim and reference (run
  `alterlab-citation-verifier` on EK-1) — fabricated references or data count as research
  misconduct under TÜBİTAK's AYEK regulation.
- **Keep confidential material out of AI tools.** The guide says not to enter unpublished data or
  ideas that are confidential, personal data under KVKK (e.g. team CVs), or third parties'
  confidential information, and to check the tool's privacy and data-use terms first. Work from
  what the user chooses to share, suggest placeholders for sensitive details, and remind them of
  this rule when they paste such material.
- **Evaluators may not use generative AI at all.** If the user is a TÜBİTAK panelist, hakem,
  danışman or izleyici asking for help assessing someone else's proposal or report, explain
  that the guide forbids this (Bölüm 2) and do not process the proposal text.

---

## Terminology Bridge (international ↔ TÜBİTAK)

When the user arrives with NSF/NIH/ERC material, translate the *concept*, not word-for-word.
Full glossary in `references/terminology_bridge.md`.

| International term | TÜBİTAK term | Note |
|-------------------|--------------|------|
| Significance / innovation / intellectual merit | **Özgün değer** (1002-A: *Bilimsel nitelik*) | The most weighted criterion; lead with what is genuinely new |
| Broader impacts | **Yaygın etki** (1002-A: *Çıktı, etki ve kazanımlar*) | Split into çıktılar, etkiler, yayılım / bilim iletişimi |
| Feasibility | **Yapılabilirlik** | Lives inside §2 YÖNTEM + §3 management |
| Contingency / risk plan | **B Planı** | Part of the work-package tables; must not drift from the core aims |
| Work package / Gantt | **İş paketi / İş-Zaman Çizelgesi** | Gantt aesthetics → delegate to `alterlab-research-grants` |
| Aims & objectives | **Amaç ve Hedefler** | Hedefler should be measurable, tied to work packages |
| Career-development plan | **Kariyer Geliştirme Potansiyeli** (3501 §4) | Relate the PI's theses to the project; name the new skills it builds |

---

## Pipeline (how to run it)

### 1. Choose the variant and generate the scaffold

```bash
uv run python skills/turkish-academia/alterlab-tubitak-proposal/scripts/scaffold_proposal.py \
    --program 1001 \
    --title "<project title>" \
    --out proposal_scaffold.md
```

`--program` accepts `1001`, `1002a` or `3501`. The script emits the Markdown section tree with the TR
heading, its English gloss, the evaluation criterion each section serves, a short drafting brief,
and (1002-A, 3501) the word range. Use `--lang tr` (default) or `--lang both` for bilingual
headings.

### 2. Draft each section from the user's material

Fill the scaffold from what the user provides. Keep the directorate's ordering. For özgün değer,
state the *gap* and the *new contribution* explicitly. For yaygın etki, populate all three
sub-parts (çıktılar / etkiler / yayılım ve bilim iletişimi). Pull literature into EK-1 — and have
`alterlab-citation-verifier` existence-check the bibliography before submission. For 1002-A and
3501, remind the user that the text goes into the PBS fields, section by section. For 3501, check
the PI's eligibility first (7-year window, title, no earlier 3501), then make the thesis step and
§4 Kariyer Geliştirme Potansiyeli concrete: what the theses established, what this project adds,
which new skills it builds.

### 3. Check the limits and structure

```bash
uv run python skills/turkish-academia/alterlab-tubitak-proposal/scripts/scaffold_proposal.py \
    --check proposal_scaffold.md --program 1001
```

The checker reports missing sections, word counts against each section's limit (1001: TR and EN
özet ≤ 600; 1002-A and 3501: the min–max ranges), stated durations/budgets above the ceiling, and whether
a B Planı is present. It is **advisory** — it never edits the proposal, and it always restates the
verify-current-call note because the ceilings are period-specific. Heading matching is
case-insensitive for Turkish (İ/ı), and `--self-test` runs the offline checks for all three
variants.

### 4. Hand off and disclaim

- Veri Yönetim Planı (uploaded to PBS with the application) → `alterlab-aperta` for the TÜBİTAK
  template and `alterlab-kvkk-dmp` for the KVKK analysis; ethics → `alterlab-tr-research-ethics`.
  For 1002-A and 3501 the etik kurul approval or legal/special permit is requested only once the
  project is selected for funding, within a set deadline, and the project does not start without
  it — so tell the user to start those applications early. For 3501 the Veri Yönetim Planı is
  generated by PBS from the entered information.
- Remind the user of the AI-use declaration and to confirm the live caps before submission.

---

## Submission Surface (read-only facts)

- **PBS** — Proje Başvuru Sistemi at `ardeb-pbs.tubitak.gov.tr`. Proposals are entered and
  submitted here and signed with a qualified **e-imza** by the team and institution officials.
- **ARBİS** — Araştırmacı Bilgi Sistemi at `arbis.tubitak.gov.tr`. A current ARBİS record
  (personal, education, experience, expertise keywords, publications) is a prerequisite; tell
  the user to refresh it *before* starting the PBS entry.

This skill does **not** automate or log into either system — it produces the content the
researcher pastes or uploads.

---

## Self-Check Before Reporting

- Did you use the **directorate's section order and Turkish headings** for the right variant?
- 1001: is the **özet within 600 words in BOTH** Turkish and English? 1002-A and 3501: is every
  section inside its word range?
- 3501: is the PI within the **7-year window** (2026: doctorate dated 01.01.2019 or later, +1 year
  per birth), doçent or lower, with no earlier 3501 — and is no professor listed as a researcher?
  Did you avoid applying 1001's weights to 3501?
- Did you state duration/budget **only with the verify-current-call note**, never as a
  guaranteed cap?
- Does every risky work package have a **B Planı**, and does §4 (or 1002-A §4) cover outputs,
  impacts and dissemination?
- Did you tell the user how to **declare the AI assistance** and to verify every reference?
- Did you **route** data-plan, ethics, indexing, and reporting asks to the correct siblings?

---

## References

- `references/form_structure.md` — the annotated 1001 form tree and the 1002-A and 3501 PBS
  screens, with a drafting brief per heading and the 1001-vs-1002-A and 1001-vs-3501 deltas.
- `references/program_profiles.md` — per-program caps (duration, budget, window, format,
  eligibility) with dates and the live verification URLs, and a 3501-vs-1001 table.
- `references/review_criteria.md` — the 1001 panel criteria and weights, the 1002-A criteria,
  the five 3501 criteria (no published weights), and common rejection patterns.
- `references/terminology_bridge.md` — international ↔ TÜBİTAK concept glossary.

Part of the AlterLab Academic Skills suite.
