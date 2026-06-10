---
name: alterlab-docentlik-eligibility
description: "Scores a Turkish associate-professorship (doçentlik / associate professorship) publication list against the per-field ÜAK (Üniversitelerarası Kurul / Inter-University Council) criteria tables, applying the author-share rule (full; 0.8 + 0.5; lead-author half-the-rest split) and pass-fail checking each mandatory minimum (100 total points, 90 post-doctorate, ≥3 lead-author Q-indexed articles). Ships a dated Sağlık (Health) TABLO 10 reference (Q1 30 / Q2 20 / Q3 15 / Q4 10 / AHCI 20 / ESCI 10 / TR Dizin 10) and a verify-against-current-UAK-period disclaimer. Use when the user wants to check doçentlik eligibility, calculate ÜAK points, audit lead-author (başlıca yazar) requirements, or see if a CV meets associate-professor thresholds; verify a journal's live TR Dizin status with alterlab-trdizin first, and compute the akademik teşvik (academic-incentive) score with alterlab-akademik-tesvik. Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read Write Edit Bash(python:*)
compatibility: No API key required — pure offline scorer (stdlib Python) over a bundled, dated ÜAK criteria table; live journal-index status is delegated to alterlab-trdizin
metadata:
  skill-author: AlterLab
  version: "1.0.0"
  last_updated: "2026-06-06"
  depends_on: "alterlab-trdizin (live TR Dizin status feeds scoring), alterlab-akademik-tesvik (separate incentive score)"
---

# Doçentlik Eligibility — Score a Publication List Against the ÜAK Criteria

Computes whether a candidate meets the **doçentlik** (associate professorship)
point thresholds set by **ÜAK** (Üniversitelerarası Kurul / the Inter-University
Council). Given a publication list with each item's index tier and author role,
it applies the per-field point table, the **author-share rule** (paylaşım
kuralı), and then pass-fail-checks every mandatory minimum, returning a clear
**eligible / not-yet-eligible** verdict with the exact shortfall.

This is a **deterministic offline scorer**, not a judgment call: the same input
always yields the same verdict. It does **not** decide the *quality* of a
candidate's work — that is the doçentlik jury's role — and it does **not** look
up a journal's live index status (use `alterlab-trdizin` for that, then feed the
result in).

## Quick Start

```
Am I eligible for doçentlik? Here is my publication list with indexes and author roles.
Doçentlik için yeterli puanım var mı? Yayın listem ekte (Q tier + yazar sırası ile).
Calculate my ÜAK doçentlik points for the Sağlık (Health) field.
Do I meet the ≥3 lead-author Q-article requirement, or am I short?
```

→ Run `scripts/score_docentlik.py` over the list (JSON), read the verdict, then
present the score breakdown, every failed minimum, and the
**verify-against-current-period** disclaimer below.

---

## CRITICAL: Verify Against the Current ÜAK Period

ÜAK republishes the doçentlik criteria **each application term** (başvuru
dönemi), and the per-field point tables change between terms. The numbers
bundled in this skill are pinned with a `last_verified` date in
`references/uak_criteria.md` and reflect the **Sağlık Bilimleri (Health
Sciences)** TABLO 10 as captured then.

**Before relying on any output**, the candidate MUST confirm the live criteria
for their own field and term against the primary ÜAK source:
<https://www.uak.gov.tr/> (Doçentlik → Başvuru Şartları / criteria tables). The
binding regulation is the **Doçentlik Yönetmeliği** (RG 15/4/2018 No. 30392),
at <https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=24519&MevzuatTur=7&MevzuatTertip=5>.
Every output this skill produces ends with this disclaimer. Never present a
verdict as the final official decision.

---

## When to Use This Skill

Use it when the request is about **scoring a publication list for the doçentlik
point gate** — total points, post-doctorate points, the lead-author Q-article
minimum, or the co-author share calculation.

### Does NOT Trigger

| The user actually wants… | Route to |
|---|---|
| The **akademik teşvik** (academic-incentive) annual score — different table, k·r·p coefficients, 30% rule, 100-point cap | `alterlab-akademik-tesvik` |
| To check whether a target journal is **currently TR Dizin-indexed** (status feeds this scorer) | `alterlab-trdizin` |
| To check a journal's DergiPark hosting / scope / self-declared indexing | `alterlab-dergipark` |
| Broader Turkish career-track planning (Dr. Öğr. Üyesi → Doçent → Profesör, YÖKSİS dossier) | `alterlab-academic-career` |
| TÜBİTAK ARDEB 1001/1002-A proposal scaffolding | `alterlab-tubitak-proposal` |
| Whether a study needed **etik kurul** (ethics committee) approval | `alterlab-tr-research-ethics` |
| Turkish APA-7 / TR Dizin reference style for a manuscript | `alterlab-tr-academic-style` |
| Verifying that cited references actually **exist** (hallucination check) | `alterlab-citation-verifier` |
| Finding a Turkish graduate **thesis** (tez) | `alterlab-yok-tez` |
| An academic's official current **affiliation / CV** (YÖK Akademik) | `alterlab-yok-akademik` |

---

## The Scoring Model

Three independent checks, all of which must pass:

1. **Total points ≥ 100** across all scored work.
2. **Post-doctorate points ≥ 90** — points earned from work published *after*
   the candidate received the doctorate (doktora sonrası). Pre-doctorate work
   still counts toward the 100 total but not toward this 90.
3. **At least 3 lead-author Q-indexed articles** — articles in a Q1–Q4 (SCIE/
   SSCI, quartile-ranked) journal where the candidate is the **başlıca yazar**
   (lead author). For Sağlık, **Q4 counts** toward this ≥3 (verified against the
   live ÜAK Sağlık criteria). See the share rule for who qualifies as lead.

   > **This is a necessary-not-sufficient pre-check.** The live Sağlık criteria
   > also require **≥40 points from SCIE/SSCI articles** (and a TR Dizin
   > national-article minimum, a citation floor, and a thesis-points cap) that
   > this scorer does **not** model. Clearing the three checks here does not by
   > itself confirm eligibility — re-verify the full TABLO 10 checklist.

### Per-field point table (bundled, dated)

The point a publication earns depends on the **field** (alan) and the journal's
**index tier**. This skill bundles the **Sağlık Bilimleri TABLO 10** values
captured on the `last_verified` date:

| Index tier | Points |
|---|---|
| Q1 (SCI-E / SSCI, 1st quartile) | 30 |
| Q2 | 20 |
| Q3 | 15 |
| Q4 | 10 |
| AHCI (Arts & Humanities Citation Index) | 20 |
| ESCI (Emerging Sources Citation Index) | 10 |
| TR Dizin (ULAKBİM national index) | 10 |

Other fields (Fen, Sosyal, Mühendislik, …) use **different** tables — the script
accepts a field selector but only ships the verified Sağlık table. For another
field, supply that field's table from the live ÜAK source; do **not** reuse the
Sağlık numbers. Full table and provenance: `references/uak_criteria.md`.

### Author-share rule (paylaşım kuralı)

A publication's face points are scaled by the candidate's authorship role:

- **Single author** → full points (×1.0).
- **Two authors** → the **lead author (başlıca yazar)** gets **0.8**; the
  **non-lead** second author gets **0.5** (the two are *not* scored equally).
- **Three or more authors** → the **lead author (başlıca yazar)** takes
  **half** the points; the remaining half is split **equally** among all
  remaining authors.

The script computes the candidate's scaled contribution per item from the author
count and the candidate's role. Worked numeric examples and the exact rounding
convention are in `references/scoring_rules.md`.

> **başlıca yazar (lead author)** — first author, corresponding author, or the
> sole supervising (advisor) author of a student-derived article, per ÜAK's
> definition. The candidate declares this per item; the scorer trusts the flag
> but reports it so a reviewer can audit it.

---

## Pipeline (how to run it)

### 1. Capture the publication list

Each item needs: a title (free text), the **field**, the **index tier** (one of
`Q1 Q2 Q3 Q4 AHCI ESCI TRDizin`), the **author count**, whether the candidate is
**lead author**, and whether it is **post-doctorate**. Example JSON:

```json
{
  "field": "saglik",
  "publications": [
    {"title": "Article A", "index": "Q1", "authors": 3, "is_lead": true,  "post_doc": true},
    {"title": "Article B", "index": "Q2", "authors": 1, "is_lead": true,  "post_doc": true},
    {"title": "Article C", "index": "TRDizin", "authors": 2, "is_lead": false, "post_doc": false}
  ]
}
```

If a journal's index tier is uncertain, resolve it first: for TR Dizin status
run `alterlab-trdizin`; for quartile, check the candidate's records. Do **not**
guess a tier — an unknown tier must be flagged, not scored.

### 2. Run the scorer

```bash
uv run python skills/turkish-academia/alterlab-docentlik-eligibility/scripts/score_docentlik.py \
    publications.json \
    --out docentlik_report.json
```

- The input path may be `-` (stdin) or inline JSON.
- `--field saglik` (default) selects the bundled table; other fields require a
  supplied table file and the script refuses to invent one.
- Omit `--out` to print the JSON report to stdout.

The script is **pure stdlib** — no network, no third-party deps — so it runs in a
bare `uv` environment and is fully reproducible offline.

### 3. Read the report and present it

Parse `summary.verdict` (`ELIGIBLE` / `NOT_ELIGIBLE`) and present:

1. The **headline verdict** and the three check results
   (`total_points`, `post_doc_points`, `lead_q_articles`) against their
   thresholds (100 / 90 / 3).
2. A **per-publication table** with each item's face points, the applied share
   factor, and its scaled contribution.
3. For every **failed** minimum, the exact shortfall (e.g. "82 / 100 points — 18
   short" or "2 / 3 lead-author Q articles — 1 short").
4. Any items with an **unknown index tier**, flagged as unscored.
5. The **verify-against-current-period disclaimer**, always.

---

## Output Shape (excerpt)

```json
{
  "tool": "alterlab-docentlik-eligibility/score_docentlik.py",
  "version": "1.0.0",
  "field": "saglik",
  "table_last_verified": "2026-06-06",
  "summary": {
    "verdict": "NOT_ELIGIBLE",
    "total_points": 95.0,
    "post_doc_points": 85.0,
    "lead_q_articles": 2,
    "checks": {
      "total_ge_100":      {"pass": false, "value": 95.0, "threshold": 100, "short": 5.0},
      "post_doc_ge_90":    {"pass": false, "value": 85.0, "threshold": 90,  "short": 5.0},
      "lead_q_articles_ge_3": {"pass": false, "value": 2, "threshold": 3,   "short": 1}
    }
  },
  "publications": [
    {"title": "Article A", "index": "Q1", "face_points": 30, "share_factor": 0.5, "scaled": 15.0, "counts_lead_q": true}
  ],
  "disclaimer": "ÜAK criteria change each term — verify against the current period at https://www.uak.gov.tr/ before relying on this verdict."
}
```

---

## Self-Check Before Reporting

- Did you state the **field** and the table's `last_verified` date? A Sağlık
  verdict must not be presented as valid for another field.
- Are all three checks reported, even the ones that pass?
- Did any item have an **unknown index tier**? Those are unscored — say so, do
  not silently drop or guess them.
- Is the headline `verdict` consistent with the three checks (any failed
  minimum → `NOT_ELIGIBLE`)?
- Did you include the **verify-against-current-period disclaimer**?

---

## References

- `references/uak_criteria.md` — the bundled, dated Sağlık Bilimleri TABLO 10
  point table, the three mandatory minimums, and the primary ÜAK source links.
- `references/scoring_rules.md` — the author-share rule with worked numeric
  examples, the lead-author definition, and the rounding convention.

Part of the AlterLab Academic Skills suite.
