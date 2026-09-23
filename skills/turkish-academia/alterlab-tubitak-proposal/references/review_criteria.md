# ARDEB Review Dimensions — drafting to the panel's lens

1001 proposals are scored by a panel (usually 5–9 panelists under a moderator) against four
weighted criteria, per the official *1001 Proje Önerisi Bilimsel Değerlendirme Formu (Panel)*
(read 2026-09-23). Each section of the form feeds one or more of these axes. Write each section
**to** its axis; confirm the weights against the current form before relying on them.

| Criterion (TR) | Weight | English | Mainly carried by | What the panel looks for |
|----------------|--------|---------|-------------------|--------------------------|
| **Özgün Değer** | **35%** | Original value | Özet, §1 ÖZGÜN DEĞER, EK-1 Kaynaklar | A clearly named gap and a genuinely novel contribution; command of the literature; a sharp research question/hypothesis |
| **Yöntem** | **25%** | Method (and feasibility / yapılabilirlik) | §2 YÖNTEM | A design appropriate to the question that is also *achievable* with the stated resources, team, and timeline; sound analysis plan |
| **Proje Yönetimi** | **20%** | Project management, team and resources | §3 (iş paketleri, İş-Zaman Çizelgesi, **B Planı**, §3.2) | Realistic work packages with measurable success criteria; a credible work–time chart; a real contingency (B Planı); adequate infrastructure |
| **Yaygın Etki** | **20%** | Broader impact & dissemination | §4 YAYGIN ETKİ, EK-2 Bütçe | Concrete outputs (çıktılar), credible impacts (etkiler), and a dissemination / science-communication plan |

**1002-A** is evaluated by external advisors (dış danışman) on three criteria — **Bilimsel
Nitelik**, **Proje Yönetimi**, **Çıktı, Etki ve Kazanımlar** — each rated on a six-level scale
from "tüm boyutlarıyla karşılamaktadır" to "çok yetersiz" (2025 evaluation form).

**3501** is scored on **five criteria** by the *3501 Proje Önerisi Bilimsel Değerlendirme Formu*
(2025-05 upload, read 2026-09-23). Each question is rated on the same six-level scale (Çok iyi,
İyi, Geliştirilebilir, Kısmen Yeterli/Sınırlı, Yetersiz, Çok yetersiz), with written strengths
and weaknesses (at least 450 characters for Özgün Değer and Yöntem, 300 for the others). **The
form publishes no criterion weights** — do not borrow 1001's 35/25/20/20. For projects reviewed
by external advisors, TÜBİTAK compiles the final report from all advisors' views.

| Criterion | What the evaluator is asked (form questions, condensed) | Mainly carried by |
|-----------|--------------------------------------------------------|-------------------|
| **1 Özgün Değer** | 1.1 problem, question/hypothesis well defined? 1.2 aims clear, measurable, achievable? 1.3 scope and importance set against the state of the art; conceptual/theoretical/methodological contribution and potential to close the gap | §1 (three fields), EK-1 |
| **2 Yöntem** | 2.1 methods and their links, with citations; 2.2 design, variables, statistics, data/sample sources; 2.3 fit to the aims | §2 |
| **3 Proje Yönetimi** | 3.1 İP definitions, who and when; 3.2 team adequate in quality and number; 3.3 success criteria measurable; 3.4 risks and B Planı realistic without drifting from the aims; 3.5 infrastructure adequate | İş Paketleri step, Araştırma Olanakları, team |
| **4 Kariyer Geliştirme Potansiyeli** | 4.1 relation of the PI's master's/doctoral/specialty work to the proposal; 4.2 contribution to the PI's career; 4.3 new skills and interdisciplinary capability beyond the theses | Tez Bilgileri, §4 |
| **5 Yaygın Etki** | 5.1 outputs clear and reachable; 5.2 impacts (application areas, socio-economic/cultural) clear and reachable; 5.3 dissemination plan concrete (audience, gains, tools, timing) | §5.1–5.3 |

Evaluators themselves may not use generative-AI tools for any part of an evaluation (TÜBİTAK
*Destek Süreçlerinde Üretken Yapay Zekânın Sorumlu ve Güvenilir Kullanımı Rehberi*, Eylül 2025,
Bölüm 2; the 3501 evaluation form restates the ban, and the guide page now serves v04, Ocak 2026,
with the same rule) — relevant if a user asks for help reviewing someone else's proposal.

## How the axes interact

- **Özgün değer is the gatekeeper.** A methodologically clean proposal with weak özgün değer
  rarely funds. Lead with novelty.
- **Feasibility lives across two axes.** The Yöntem axis judges whether the method *can* answer
  the question; the Proje Yönetimi axis judges whether the *plan* (WPs, timeline, B-Planı,
  facilities) can execute it. A proposal can be scientifically strong but fail on an
  unconvincing iş-zaman çizelgesi.
- **Yaygın etki is often under-developed.** Panels frequently flag thin yaygın-etki sections.
  Populate çıktılar, etkiler, *and* bilim iletişimi — not just a publication list.
- **Budget justification ties back to management.** Every EK-2 line should map to a work package;
  unjustified budget undermines the Proje Yönetimi score.

## Common rejection patterns to pre-empt

1. **Form-rule breaches** — 1001 özet over 600 words (TR or EN), more than 25 pages excluding
   EK-1/EK-2, a changed template, or content moved to external links: returned before review.
   For 1002-A and 3501, keep every section inside its PBS word range (see `form_structure.md`).
   For 3501, also confirm the PI's eligibility (doctorate date, title, no earlier 3501) first.
2. **Duration/budget over the program ceiling** — re-check the *current* period caps.
3. **No B Planı** for the risky work packages — a required element of the İP tables.
4. **Hedefler not mapped to work packages**, or literature review / reporting / article writing
   / procurement listed as work packages.
5. **Restructuring the form into an IMRaD paper** — the panel scores against the directorate
   headings; keep them.
6. **Fabricated / unverifiable references in EK-1** — run `alterlab-citation-verifier` first.
7. **Undeclared generative-AI drafting** — TÜBİTAK requires significant AI use to be declared
   in the PBS section provided for it (see the SKILL.md section on AI use).
