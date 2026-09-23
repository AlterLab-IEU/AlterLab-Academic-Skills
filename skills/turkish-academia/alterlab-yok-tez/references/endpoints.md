# Endpoints — verified vs. unverified

Everything here was checked live on **2026-09-23** or is marked **UNVERIFIED**. Do not
promote an UNVERIFIED item to a hard claim without re-checking the live source.

## YÖK Ulusal Tez Merkezi (the official site)

| Surface | URL | Status |
|---------|-----|--------|
| Repository home | `https://tez.yok.gov.tr/UlusalTezMerkezi/` | Verified live |
| Search screen ("Gelişmiş Arama" + "Detaylı Arama") | `https://tez.yok.gov.tr/UlusalTezMerkezi/tarama.jsp` | Verified live |
| Thesis detail page | `…/UlusalTezMerkezi/tezDetay.jsp?id=<kayitNo>&no=<tezNo>` (opaque tokens) | Verified live via the connector |

YÖK redesigned the search in **2026**. The screen now takes up to three search terms
joined with **VE / VEYA**, one **Aranacak Alan** (Tümü, Tez Adı, Yazar, Danışman, Konu,
Anahtar Kelime, Özet), an **Arama Tipi** ("Sadece yazılan şekilde" = exact, "Kelimenin
içinde geçsin" = contains), and Detaylı Arama dropdowns (üniversite, enstitü, anabilim dalı,
konu, tez türü, yıl, izin durumu, durum — Onaylandı / Hazırlanıyor — and dil). The page
offers an "E-Devlet ile Giriş" login.

**No official public API exists.** There is no published JSON/REST endpoint — do not
fabricate one. Full text is **online-view-only** for *İzinli* theses; *İzinsiz* theses expose
metadata + abstract only. Driving the site by hand needs a real browser; prefer the connector.

## yoktez-mcp (the recommended data path)

- **Repo:** `github.com/saidsurucu/yoktez-mcp` — **MIT** licensed.
- **Hosted connector:** `https://yoktezmcp.fastmcp.app/mcp` — answered `initialize` on
  2026-09-23 as **YokTezMCP 3.3.1**. The repo README still documents the older two-tool
  surface; the live `tools/list` below is authoritative.
- **Local install (uv-first):** `uvx --from git+https://github.com/saidsurucu/yoktez-mcp yoktez-mcp`

### Tools exposed (live `tools/list`, 2026-09-23)

| Tool | Purpose | Key parameters |
|------|---------|----------------|
| `search_yok_tez_detailed` | Keyword search in one field, with filters | `keyword`, `keyword_2`, `keyword_3`, `operator_1`/`operator_2` (`and`/`or`), `search_field`, `match_type`, `thesis_type`, `permission_status`, `thesis_status`, `language`, `year_start`, `year_end`, `page`, `results_per_page`; legacy aliases `thesis_title`, `author_name`, `advisor_name`, `subject_headings`, `index_terms`, `abstract_text` each set `search_field` |
| `list_recent_yok_tez` | No-keyword lists: `mode` "7" = theses uploaded in the last 15 days, "8" = current publication year | `mode`, `page`, `results_per_page` |
| `list_yok_tez_anabilim_dali` | Find department (anabilim dalı) codes by a word in the name | `keyword`, `max_results` |
| `search_yok_tez_by_anabilim_dali` | Search within department codes (≤ 15 per call), with title/author/advisor/index-term filters | `anabilim_dali_codes`, filters as above |
| `get_yok_tez_thesis_details` | Advisor, university/institute/department path, TR and EN abstracts and keywords, and ready-made APA/IEEE/MLA/Chicago/Harvard strings — no PDF download | `detail_page_url` (or `thesis_key` + `encrypted_no`) |
| `get_yok_tez_document_markdown` | One PDF page of a permitted (*İzinli*) thesis as Markdown | `detail_page_url`, `page_number` |

Removed in the 2026 redesign (per the connector's own description): the university /
institute / department **text** filters and the direct **thesis-number** lookup. Filter by
university on the returned `university_info`, or narrow by department with the two anabilim
dalı tools.

### Filter codes (verified live 2026-09-23 unless noted)

| Parameter | Codes |
|-----------|-------|
| `search_field` | `7` Tümü (default), `1` Tez Adı, `2` Yazar, `3` Danışman, `4` Konu, `5` Anahtar Kelime, `6` Özet (1–3 checked against live results; 4–6 follow the connector's documented order) |
| `match_type` | `2` contains (default), `1` exact phrase |
| `thesis_type` | `0` all (default), `1` Yüksek Lisans, `2` Doktora, `3` Tıpta Uzmanlık, `4` Sanatta Yeterlik, `5` Diş Hekimliği Uzmanlık, `6` Tıpta Yan Dal Uzmanlık, `7` Eczacılıkta Uzmanlık |
| `permission_status` | `0` Tümü (default), `1` İzinli, `2` İzinsiz — for a 1995–2000 title query, 0 → 175 = 30 İzinli + 145 İzinsiz |
| `thesis_status` | **`3` Onaylandı is the connector default**, `1` Hazırlanıyor (in preparation), `0` Tümü — for a 2025+ title query, 0 → 1,408 ≈ 825 approved + 582 in preparation |
| `language` | `0` all, `1` Türkçe, `2` İngilizce (other codes exist; UNVERIFIED mapping) |

### Result shape

`theses[]` with `thesis_no`, `title`, `title_translated`, `author`, `year`,
`university_info`, `thesis_type`, `language`, `subject`, `thesis_key`, `encrypted_no`,
`detail_page_url`; plus `total_results_found`, `results_in_batch`, `current_page`,
`total_pages`.

## Result cap

The connector reports that YÖK returns at most **~2,000 results per batch**
(`results_in_batch`) even when `total_results_found` is larger. If a query's total is near
or above 2,000, split it (year ranges, thesis types, departments) and merge locally.

## tezara.org (community mirror)

- **What it is:** "Tez Arama ve Metaveri Analizi Platformu" (Thesis Search and Metadata
  Analysis Platform) — a community mirror of Ulusal Tez Merkezi records. Site responds
  (HTTP 200, 2026-09-23).
- **UNVERIFIED:** the CSV/JSON export, the claim that it bypasses the 2,000-row cap, and the
  per-thesis URL pattern `tezara.org/theses/{thesisNo}`. Verify on the live site before
  relying on them in an automated harvest, and remember it may lag the official registry.
