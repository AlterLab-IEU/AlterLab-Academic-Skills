# ARDEB 1001, 1002-A & 3501 Form Structure (annotated)

The section trees below follow the directorate's own heading order: the official 1001 `.doc`
form, and — for 1002-A and 3501 — the PBS entry steps described in each programme's *Başvuru
İçeriği Bilgi Notu* (all read on 2026-09-23). Draft **to these headings, in this order**
— ARDEB evaluators score against this structure, not against an IMRaD paper. Keep the Turkish
heading; the English in parentheses is a gloss for the drafter, not a section to add.

Authoritative sources (verify the current period before relying on caps):

- 1001 form: `https://tubitak.gov.tr/sites/default/files/2024-04/1001_basvuru_formu.doc`
- 1001 guide: `https://tubitak.gov.tr/sites/default/files/2024-04/ardeb_1001_basvuru_rehberi.pdf`
- 1002-A content note: `https://tubitak.gov.tr/sites/default/files/2025-12/1002_a_basvuru_icerigi_bilginotu.doc`
- 3501 content note: `https://tubitak.gov.tr/sites/default/files/2026-05/3501_basvuru_icerigi_bilgi_notu.doc`

> Sub-heading wording is revised between periods. Treat the trees as the stable skeleton and
> reconcile labels against the current form / note.

---

# Part A — 1001 (official .doc form)

Form rules from the form header and program page: **Arial 9**, keep the format unchanged,
**≤ 25 pages excluding EK-1 and EK-2**, one file; content shared through links to external
storage is returned without scientific review; no tracked changes or comments.

## ÖZET (TR) + ABSTRACT (EN)

- Written as **two separate blocks** — ÖZET (Turkish) and ABSTRACT (English) — each **≤ 600
  words** counted *independently*. Keep them as distinct headings so the per-language cap can be
  measured; don't merge them into one block.
- Each is followed by its **Anahtar Kelimeler / Keywords**.
- The form asks the özet to cover (a) özgün değer, (b) yöntem, (c) yönetim and (d) yaygın etki,
  and suggests writing it last. It is the panel's first read.

## 1. ÖZGÜN DEĞER (Original Value / Significance)

The most heavily weighted block of a 1001 (35% of the panel score). This is where novelty is
decided.

- **1.1 Konunun Önemi ve Projenin Özgün Değeri** — situate the problem through a critical reading
  of the literature (supported with qualitative/quantitative evidence), name the specific gap,
  and state the conceptual, theoretical and/or methodological contribution. Cite into EK-1.
- **1.2 Araştırma Sorusu ve/veya Hipotezi** — explicit, falsifiable, tied to the aim.
- **1.3 Amaç ve Hedefler** — one aim; several **measurable** hedefler (objectives) that map onto
  work packages in §3.

## 2. YÖNTEM (Method)

- Research design, dependent/independent variables, data-collection instruments, analysis and
  statistical methods, each justified with references; report any preliminary work; a flow
  diagram may be added.
- This section carries **yapılabilirlik** (feasibility): show the method suits the aims *and* is
  achievable with the stated resources and timeline.
- If human/animal subjects or personal data are involved, state that ethics approval / data
  governance is handled — and route the actual etik kurul form to `alterlab-tr-research-ethics`
  and the data plan to `alterlab-kvkk-dmp`. Do not draft those here.

## 3. PROJE YÖNETİMİ (Project Management)

- **3.1 Yönetim Düzeni: İş-Zaman Çizelgesi ve İş Paketleri**
  - **3.1.1 İş-Zaman Çizelgesi** — per work package (İP): number, name, **Projenin Başarısındaki
    Önemi (%)** (the column must total 100), who carries it out, and its months.
    **Literature review, progress/final report writing, dissemination, article writing and
    procurement are not work packages.**
  - **3.1.2 İş Paketleri** — one table per İP: hedef, tasks, people and their contribution,
    **Başarı Ölçütü** (measurable, trackable success criterion), **Ara Çıktılar** (interim
    outputs that evidence the criterion), and **Risk Yönetimi** with the **B Planı** — the
    measures that keep the project on track if the risk occurs. A B plan must not drift from
    the core aims or özgün değer; if it changes the method, say how. (Gantt rendering →
    `alterlab-research-grants`.)
- **3.2 Araştırma Olanakları** — infrastructure and equipment at the executing/partner
  institutions, with what each is used for.

## 4. YAYGIN ETKİ (Broader Impact / Dissemination)

Populate **all three** sub-parts; a thin yaygın etki is a common weakness flagged by panels.

- **4.1 Öngörülen Çıktılar** — a table of outputs with their expected timing (0–12 months,
  12–18 months, after the project, …) in three categories: scientific/academic (articles, books,
  chapters, papers); economic/commercial/social (prototype, product, patent, utility model,
  registration, archive, database, spin-off …); researcher training and new projects (theses,
  new national/international projects). Name the organisations that will use them, if any.
- **4.2 Öngörülen Etkiler** — *Öngörülen Uygulama Alanları* (application areas and links to end
  users such as policy makers, civil society, industry) and *Sosyo-ekonomik/Kültürel Katkı*;
  the form recommends relating these to the targets of higher policy documents, above all the
  On İkinci Kalkınma Planı (2024–2028), with citations.
- **4.3 Proje Sonuçlarının Yayılımı ve Bilim İletişimi Kapsamında Gerçekleştirilecek Faaliyet
  Planı** — Hedef Kitle, Hedefler ve Beklenen Kazanımlar, Kullanılacak Araçlar, Zamanlama.
- **Belirtmek İstediğiniz Diğer Konular** (optional) — only material that helps the evaluation.

## EK-1. Kaynaklar (References)

Cited literature for §1–§4, formatted per TÜBİTAK's bibliographic guidance. Have
`alterlab-citation-verifier` existence-check the bibliography before submission —
fabricated/AI-hallucinated references are a credibility risk in front of a panel.

## EK-2. Bütçe ve Gerekçesi (Budget & Justification)

Itemized budget (makine-teçhizat, sarf, seyahat, hizmet alımı, burs) **with a justification per
line tied to the work packages**, on the official EK-2 table. The total must respect the program
ceiling — for 1001 that ceiling includes scholarships and excludes PTİ and kurum hissesi (see
`program_profiles.md`). For data-management plans route to `alterlab-kvkk-dmp` /
`alterlab-aperta`.

## EK-3. Proje Ekibinin Diğer Projeleri ve Güncel Yayınları

Generated automatically by PBS from the information entered in the system — nothing to draft,
but keep the team's ARBİS records current.

---

# Part B — 1002-A (PBS entry screens)

Since the 2025 redesign, 1002-A has **no .doc template**. The applicant types each section into
the PBS screen; the system builds the application form, EK-1 and EK-2. Word ranges are enforced
per section:

| # | Section (TR) | Words (min–max) | Notes |
|---|--------------|-----------------|-------|
| 1 | **BİLİMSEL NİTELİK** — Konunun Önemi ve Projenin Bilimsel Niteliği | 1,000–3,500 | Scope, limits and importance; the literature gap and how the project closes it; the research question and hypotheses |
| 1 | Amaç ve Hedefler | 100–1,000 | Clear, measurable, realistic, achievable within the project |
| 2 | **YÖNTEM** | 750–3,000 | Methods and techniques with references; design, variables, statistics |
| 3 | **PROJE YÖNETİMİ** | (built from the "Proje İş Paketleri" step) | Per İP: who and when, **Başarı Ölçütü**, **Projenin Başarısındaki Önemi (%)** totalling 100, and risks with a **B Planı** under "Risk Bilgileri" (a risk for every İP is not mandatory). Enter "Proje Personeli" and "Yardımcı Personel" first. Literature review, reporting, dissemination, article writing and procurement are not work packages. ≤ 12 months |
| 4 | **ÇIKTI, ETKİ VE KAZANIMLAR** | 100–400 | Outputs (scientific, economic, social, researcher training, new projects), impacts, gains, and who benefits how |
| – | Belirtmek İstediğiniz Diğer Konular | ≤ 250 (optional) | Only material that helps the evaluation |
| EK-1 | Kaynakça step | — | Every source cited in the text; **DOI mandatory where one exists** |
| EK-2 | Budget steps | — | Justify each line; total must equal "Önerilen Destek Miktarı"; no proforma at application; no foreign travel or foreign field work |

Content pasted from elsewhere should be cleaned with the editor's "remove format" tool; images
must be .jpg/.jpeg/.png. The bilgi notu does not state an özet word limit for 1002-A — check the
"Proje Bilgileri" step in PBS.

---

# Part C — 3501 Kariyer Geliştirme (PBS entry screens)

Like 1002-A, 3501 has **no .doc template**: each section is typed into a PBS screen and the
system builds the form, EK-1 and EK-2. Word ranges below are from the *3501 Başvuru İçeriği
Bilgi Notu*; numbering follows the 3501 evaluation form (1 Özgün Değer … 5 Yaygın Etki).
Content placed behind links to external storage or web pages is returned without review.

| # | Section (TR) | Words (min–max) | Notes |
|---|--------------|-----------------|-------|
| – | **PROJE YÜRÜTÜCÜSÜNÜN TEZ BİLGİLERİ** — Yüksek Lisans Tezi: title + yaygın etki | ≤ 150 | Only if the PI has a master's thesis; list its papers, chapters, books |
| – | Doktora / Tıpta Uzmanlık (or equivalent) Tezi: title + yaygın etki | 50–350 | Feeds the Kariyer Geliştirme criterion (relation of the theses to the proposal) |
| 1 | **ÖZGÜN DEĞER** — Konunun Önemi, Projenin Özgün Değeri | 1,000–4,000 | Critical literature review with qualitative/quantitative support; the gap and the conceptual/theoretical/methodological contribution |
| 1 | Araştırma Sorusu veya Hipotezi | 100–400 | Problem(s), research question and/or hypothesis |
| 1 | Amaç ve Hedefler | 150–500 | Clear, measurable, realistic, achievable within the project |
| 2 | **YÖNTEM** | 1,000–3,750 | Methods and techniques with reasons for the choice (data-collection tools, analysis), design, variables, statistics; preliminary work; optional flow chart |
| 3 | **PROJE YÖNETİMİ** | (built from the "Proje İş Paketleri" step) | ≤ 36 months; no İP longer than the project; per İP who/when, **Başarı Ölçütü**, **Projenin Başarısındaki Önemi (%)** totalling 100, **Ara Çıktılar**, risks with a **B Planı** under "Risk Bilgileri" (not mandatory for every İP); enter "Proje Personeli" and "Yardımcı Personel" first; **Araştırma Olanakları** lists infrastructure and its use. Literature review, reporting, dissemination, article writing and procurement are not work packages |
| 4 | **KARİYER GELİŞTİRME POTANSİYELİ** | 250–700 | How the PI's master's/doctoral/specialty work relates to (and differs from) the proposal; what the project adds to the PI's career, new skills, interdisciplinary capability |
| 5.1 | **YAYGIN ETKİ** — Öngörülen Çıktılar | — | Outputs by category with measurable targets, the time window of each, and users (if any) |
| 5.2 | Öngörülen Etkiler | 50–400 | Application areas, end users (policy makers, civil society, private sector), socio-economic/cultural contribution; link to the On İkinci Kalkınma Planı and other policy documents with citations |
| 5.3 | Proje Sonuçlarının Yayılımı ve Bilim İletişimi Kapsamında Gerçekleştirilecek Faaliyet Planı — Hedef Kitle | 10–125 | Who benefits and how they will be reached |
| 5.3 | Hedefler ve Beklenen Kazanımlar | 10–125 | Awareness/knowledge goals and why sharing matters |
| 5.3 | Kullanılacak Araçlar | 5–100 | Channels (digital platforms, media, workshops, podcasts, infographics, exhibitions …) and why |
| 5.3 | Zamanlama | 5–75 | When and for how long |
| – | Belirtmek İstediğiniz Diğer Konular | ≤ 500 (optional) | Only material that helps the evaluation |
| EK-1 | Kaynaklar ("Kaynakça" step) | — | Every source cited in the text; **DOI mandatory where one exists** |
| EK-2 | Bütçe ve Gerekçesi (budget steps) | — | Detailed justification per line; total must equal "Önerilen Destek Miktarı"; no proforma at application; limits in `program_profiles.md` |

EK-3 (Proje Ekibinin Diğer Projeleri) is generated by PBS. The bilgi notu does not state an
özet word limit for 3501 — check the "Proje Bilgileri" step in PBS.

---

## 1001 vs 1002-A — the delta

- **Format:** 1001 = uploaded .doc (≤ 25 pages excl. EK-1/EK-2); 1002-A = PBS text fields with
  word ranges.
- **Headings:** 1002-A's first block is *Bilimsel Nitelik* (not *Özgün Değer*) and its last is
  *Çıktı, Etki ve Kazanımlar* (not *Yaygın Etki*); there is no separate Araştırma Olanakları or
  EK-3 block to draft.
- **Evaluation:** 1001 = panel (özgün değer 35%, yöntem 25%, proje yönetimi 20%, yaygın etki
  20%); 1002-A = external advisors on Bilimsel Nitelik, Proje Yönetimi, Çıktı-Etki-Kazanımlar.
- **Money and time:** 1002-A has a much lower budget ceiling and ≤ 12 months (see
  `program_profiles.md`), with **rolling** submission instead of a periodic call.
- 1002-A also serves needs arising in an accepted doctoral thesis (the doctoral student can be
  PI). The separate **1002-B Acil Destek Modülü** is for *urgent* needs and is out of scope.

## 1001 vs 3501 — the delta

- **Format:** 3501 is typed into PBS with word ranges (Part C); 1001 is an uploaded .doc.
- **Headings:** 3501 keeps 1001's Özgün Değer / Yöntem / Proje Yönetimi / Yaygın Etki blocks and
  adds the thesis-information step and **4. Kariyer Geliştirme Potansiyeli**; yaygın etki
  becomes section 5.
- **Evaluation:** five criteria on a six-level scale with no published weights (see
  `review_criteria.md`) instead of 1001's four weighted panel criteria.
- **Eligibility, money and timing:** ≤ 7 years after the doctorate, doçent or lower, first 3501;
  1,500,000 TL; rolling submission — full table in `program_profiles.md`.
