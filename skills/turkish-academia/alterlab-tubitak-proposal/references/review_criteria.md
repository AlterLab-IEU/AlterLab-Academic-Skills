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

Evaluators themselves may not use generative-AI tools for any part of an evaluation (TÜBİTAK
*Destek Süreçlerinde Üretken Yapay Zekânın Sorumlu ve Güvenilir Kullanımı Rehberi*, Eylül 2025,
Bölüm 2) — relevant if a user asks for help reviewing someone else's proposal.

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
   For 1002-A, keep every section inside its PBS word range (see `form_structure.md`).
2. **Duration/budget over the program ceiling** — re-check the *current* period caps.
3. **No B Planı** for the risky work packages — a required element of the İP tables.
4. **Hedefler not mapped to work packages**, or literature review / reporting / article writing
   / procurement listed as work packages.
5. **Restructuring the form into an IMRaD paper** — the panel scores against the directorate
   headings; keep them.
6. **Fabricated / unverifiable references in EK-1** — run `alterlab-citation-verifier` first.
7. **Undeclared generative-AI drafting** — TÜBİTAK requires significant AI use to be declared
   in the PBS section provided for it (see the SKILL.md section on AI use).
