---
name: alterlab-yok-tez
description: "Searches YÖK Ulusal Tez Merkezi (tez.yok.gov.tr), Turkey's mandatory national graduate-thesis repository, for literature discovery and pre-proposal özgünlük (originality) checks via the saidsurucu/yoktez-mcp connector and YÖK's 2026 search: up to three terms joined by VE/VEYA in one field (Tez Adı, Yazar, Danışman, Konu, Anahtar Kelime, Özet or all), tez türü/year/language filters, İzinli/İzinsiz and Onaylandı/Hazırlanıyor status, anabilim dalı browsing and per-thesis details. Runs paired Turkish+English queries with stems that survive substring matching and emits Türkçe APA-7 citations mapping Tez No to Yayın No. Use when the user wants to search Turkish theses, ara YÖK tez, check thesis novelty before approving a proposal, find dissertations by advisor (danışman) or university, dedupe a topic against existing tezler, or cite a YÖK thesis. For Turkish journal articles use alterlab-dergipark or alterlab-trdizin. Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read Write Edit Bash(python:*) WebFetch
compatibility: "No API key required — searches via the saidsurucu/yoktez-mcp connector (hosted https://yoktezmcp.fastmcp.app/mcp, YokTezMCP 3.3.1 as of 2026-09-23, or local `uvx`) or the public tez.yok.gov.tr search screen; full text is online-view-only, no bulk download"
metadata:
  skill-author: AlterLab
  version: "1.1.0"
  last_updated: "2026-09-23"
---

# YÖK Ulusal Tez Merkezi — Turkish National Thesis Search

YÖK Ulusal Tez Merkezi (the Higher Education Council's *National Thesis
Center*) is the single mandatory repository for every Turkish graduate thesis —
*yüksek lisans* (master's), *doktora* (doctorate), *tıpta/diş/eczacılıkta
uzmanlık* (medical/dental/pharmacy specialty), and *sanatta yeterlik* (art
proficiency). It is the authoritative source for two faculty workflows this
skill serves:

1. **Literature discovery** — finding existing Turkish dissertations for a
   review, by topic, *danışman* (advisor), university, or year.
2. **Pre-proposal *özgünlük* (originality) checks** — before a supervisor
   approves a student's thesis topic, scanning whether the same work already
   exists, is restricted, or is registered as in preparation.

This skill is **discovery + metadata harvesting + citation**, not bulk
full-text download (full text is online-view-only — see access model below).

## When to Use This Skill

```
YÖK Ulusal Tez Merkezi'nde "sürdürülebilir mimari" konulu tezleri ara
Bir öğrencim "sanal prodüksiyon" üzerine doktora yapmak istiyor; daha önce yapılmış mı?
Find every doctoral dissertation supervised by Prof. X at IEU
Cite this YÖK thesis in APA 7 (Turkish)
Is this thesis topic novel, or has it already been done in Turkey?
```

→ Build paired Turkish/English queries, run them through the `yoktez-mcp`
connector, dedupe results into a `{thesis_no, year, university, danışman, title,
izin, durum}` table, and — when asked — emit a Türkçe APA-7 citation.

### Does NOT Trigger — route these elsewhere

| Request | Correct skill |
|---------|---------------|
| Search **Turkish journal articles** on DergiPark | `alterlab-dergipark` |
| Check a **journal's TR Dizin** index status / search the national citation index | `alterlab-trdizin` |
| Look up an **academic's profile / supervised-thesis list / affiliation** on YÖK Akademik | `alterlab-yok-akademik` |
| University **program admission statistics** (kontenjan, taban puan) on YÖK Atlas | `alterlab-yokatlas` |
| Compute **doçentlik** (associate-professorship) eligibility points | `alterlab-docentlik-eligibility` |
| Compute **akademik teşvik** (academic-incentive) score | `alterlab-akademik-tesvik` |
| Hands-on **thesis writing / supervision / defense** coaching (chapters, viva) | `alterlab-thesis-supervisor` |
| Build a **PRISMA systematic review** over biomedical/scientific databases | `alterlab-literature-review` |
| Manage a **Zotero/BibTeX reference library** | `alterlab-citation-mgmt` |
| **Türkçe APA-7 / TR Dizin house style** rules in general (not a thesis cite) | `alterlab-tr-academic-style` |

This skill answers *"does this Turkish thesis exist / has this been done, and how
do I cite it?"* — it does not write the thesis, judge journals, or score careers.

---

## The data path: yoktez-mcp

There is **no official public API** for Ulusal Tez Merkezi. The maintained
community path is the **`saidsurucu/yoktez-mcp`** MCP server (MIT licensed);
prefer it over scraping.

- **Hosted connector:** `https://yoktezmcp.fastmcp.app/mcp` (YokTezMCP 3.3.1 on
  2026-09-23)
- **Local:** `uvx --from git+https://github.com/saidsurucu/yoktez-mcp yoktez-mcp`

YÖK **redesigned its search in 2026**: one field per query, up to three terms
joined by VE/VEYA, and dropdown filters. The university / institute / department
text filters and the thesis-number lookup are gone. The connector's six tools
(live `tools/list`; the repo README still shows the older two):

| Tool | Use it for |
|------|-----------|
| `search_yok_tez_detailed` | Topic, title, author or advisor search: `keyword` (+ `keyword_2`, `keyword_3`, `operator_1`/`operator_2` = `and`/`or`), `search_field`, `match_type`, and coded filters `thesis_type`, `permission_status`, `thesis_status`, `language`, `year_start`, `year_end` |
| `list_yok_tez_anabilim_dali` → `search_yok_tez_by_anabilim_dali` | Narrow to departments (anabilim dalı codes, ≤ 15 per call) — the replacement for the dropped department filter |
| `get_yok_tez_thesis_details` | Advisor, university → institute → department path, TR/EN abstracts and keywords, ready-made citation strings — without downloading the PDF |
| `get_yok_tez_document_markdown` | One PDF page of an *İzinli* thesis as Markdown |
| `list_recent_yok_tez` | Theses uploaded in the last 15 days, or this year's corpus (no keyword needed) |

Filter codes (verified live, full table in
[`references/endpoints.md`](references/endpoints.md)): `search_field` `7` Tümü
(default) / `1` Tez Adı / `2` Yazar / `3` Danışman / `4` Konu / `5` Anahtar
Kelime / `6` Özet; `match_type` `2` contains (default) / `1` exact;
`thesis_type` `1` Yüksek Lisans, `2` Doktora, `3` Tıpta Uzmanlık, `4` Sanatta
Yeterlik, `5`–`7` specialty types; `permission_status` `0` Tümü / `1` İzinli /
`2` İzinsiz; `thesis_status` `0` Tümü / `3` Onaylandı (the connector's default)
/ `1` Hazırlanıyor.

If the connector is unavailable, the search screen at
`https://tez.yok.gov.tr/UlusalTezMerkezi/tarama.jsp` can be driven in a real
browser. Don't invent a JSON/REST endpoint — none is published.

`scripts/yok_tez_query.py` builds the connector arguments offline from a plain
description (TR/EN topics, advisor, thesis type, years, originality mode) and
formats citations; it makes no network call.

---

## Search craft (apply these automatically)

Full rules with worked examples: [`references/search_syntax.md`](references/search_syntax.md).

1. **Search stems that survive substring matching.** The default match is
   *contains*, so `sürdürülebilir` finds every inflected form — but Turkish turns
   a final k/ç/t/p into ğ/c/d/b before a suffix, so cut it: `okuryazarl` found
   622 title hits where `okuryazarlık` found 277 (2025+, live check).
2. **Up to three terms per call, joined by `and`/`or`** (the site's VE/VEYA). There
   is no NOT operator — filter unwanted hits locally.
3. **Run BOTH a Turkish and an English query.** English terms only hit the English
   title/abstract/keyword fields, so an all-Turkish query silently misses theses
   indexed in English, and vice-versa.
4. **Pick the field deliberately.** `search_field` `7` (Tümü) for topic recall;
   `1`/`6`/`4`/`5` for precision passes; `2`/`3` for authors and advisors.

---

## Originality / supervision check (the repeatable recipe)

When a supervisor asks *"has this thesis topic already been done?"*:

1. Build paired TR + EN queries (stems, OR for synonyms) in `search_field` `7`.
2. Constrain `thesis_type` (e.g. `2` Doktora) and a `year_start`–`year_end`
   window only if the user asked for them.
3. Set **`permission_status` `0`** (Tümü) so *İzinsiz* (restricted, abstract-only)
   theses surface, and **`thesis_status` `0`** so *Hazırlanıyor* (in-preparation)
   theses surface too — the connector defaults to approved theses only, and
   restricted or in-progress work is exactly what a naive search hides.
4. Return a **deduplicated table** — `{thesis_no, year, university, danışman,
   title, izin, durum}`, newest first — fetching advisors with
   `get_yok_tez_thesis_details` for the rows that matter.
5. State explicitly that this is *registry coverage*, not a plagiarism /
   text-similarity score (iThenticate/Turnitin territory, out of scope here).

**Advisor at a given university:** search `search_field` `3` with the advisor's
name (plus `thesis_type` if needed), keep the rows whose `university_info`
matches, and confirm the advisor on each with `get_yok_tez_thesis_details` —
names repeat across universities.

---

## Access model (set correct expectations)

- **Full text is online-view-only** for *İzinli* (permitted) theses — viewable in
  the browser, **no photocopy / bulk download**. `get_yok_tez_document_markdown`
  works only on permitted theses.
- **Abstracts (*özet*) are available** even when full text is restricted
  (`get_yok_tez_thesis_details` returns both TR and EN abstracts).
- ***İzinsiz* (restricted) theses** show metadata + abstract only; the print copy
  is reachable via **TÜBESS** / inter-library loan through a university library.
- **Pre-2006 closed theses** can be opened by the author submitting a *Tez
  Yayımlama İzin Belgesi* (thesis-publication permission document).
- **Legal basis:** 2547 sayılı Kanun Ek Madde 40 (added by Law 7100, Art. 10,
  2018) — theses are made electronically accessible by YÖK Ulusal Tez Merkezi
  unless an authorized *gizlilik* (confidentiality) decision applies. YÖK's FAQ
  states **no fixed maximum embargo length**; do not assert a "12-month cap."

Full detail in [`references/access_legal.md`](references/access_legal.md).

---

## Caps and bulk harvest

- **~2,000 results per batch.** YÖK returns at most about 2,000 rows
  (`results_in_batch`) even when `total_results_found` is larger. If a total is near
  or above that, split by year range, thesis type, or department and merge locally.
- The community mirror **tezara.org** may help with large metadata harvests, but its
  export and cap-bypass claims are unverified — see
  [`references/endpoints.md`](references/endpoints.md).
- Bulk Turkish↔English query expansion, advisor-name normalization and CSV dedup are
  repetitive, privacy-neutral work — a good fit for a local model or a short script.

---

## Citing a YÖK thesis (Türkçe APA-7)

Map the YÖK **Tez No** directly to APA's **Yayın No.** (publication number).
The `scripts/yok_tez_query.py cite` mode formats both states; rules and more
examples in [`references/citation_apa7.md`](references/citation_apa7.md).

- **Published / permitted** (has a Yayın No.):
  > Soyad, A. (Yıl). *Tez başlığı* (Yayın No. _NNNNNN_) [Tez türü, Üniversite
  > Adı]. YÖK Ulusal Tez Merkezi.
- **Unpublished / restricted**:
  > Soyad, A. (Yıl). *Tez başlığı* [Yayımlanmamış tez türü tezi]. Üniversite Adı.

`get_yok_tez_thesis_details` also returns YÖK's own APA string (capitalised
surname, "Tez No.") — convert it to the form above unless the journal asks for
YÖK's. Optionally emit BibTeX `@phdthesis` / `@mastersthesis` with
`note = {YÖK Ulusal Tez Merkezi, Tez No. NNNNNN}`.

---

## Self-check before reporting

- Did you run **both** a Turkish and an English query, with stems that survive
  substring matching?
- For an originality check, did you set **`permission_status` `0` and
  `thesis_status` `0`** so restricted and in-preparation theses surfaced?
- Did any query approach the **~2,000 batch cap**? If so, split and re-run.
- Did you filter university/advisor matches on the returned fields rather than
  assume a filter the 2026 search no longer has?
- Are citations using **Tez No → Yayın No.** with the correct
  *published* vs *unpublished* template?
- Did you state that registry coverage ≠ a text-similarity / plagiarism score?

---

## References

- [`references/endpoints.md`](references/endpoints.md) — the 2026 search screen,
  the live yoktez-mcp tool surface and filter codes, result shape, the batch cap,
  tezara.org.
- [`references/search_syntax.md`](references/search_syntax.md) — stems and
  consonant alternation, and/or terms, TR+EN pairing, field choice, worked query.
- [`references/access_legal.md`](references/access_legal.md) — İzinli/İzinsiz,
  TÜBESS, pre-2006 opening, 2547 Ek Madde 40 legal basis, embargo facts.
- [`references/citation_apa7.md`](references/citation_apa7.md) — Türkçe APA-7
  thesis templates, the Tez No → Yayın No. mapping, YÖK's own citation strings.

Part of the AlterLab Academic Skills suite.
