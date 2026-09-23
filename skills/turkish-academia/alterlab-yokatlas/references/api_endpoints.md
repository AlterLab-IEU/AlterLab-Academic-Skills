# YÖK Atlas JSON API & yokatlas-py reference

Verified 2026-09-23. Sources: the three lookup endpoints below (fetched live),
the yokatlas-py 0.7.0 sdist on PyPI (source read) and live runs of
`scripts/yokatlas_lookup.py` against it. Treat anything not listed here as
unverified — do not invent fields, paths, or enum values.

## The migration (why only the JSON API)

YÖK Atlas migrated from server-rendered PHP to a **React SPA** backed by a JSON
API. As of **April 2026** the legacy pages return only an empty SPA shell:

- `lisans.php?y=…` — **DEAD**
- `lisans-panel.php` — **DEAD**
- `tercih-sihirbazi-*.php` — **DEAD**

Every pre-April-2026 HTML scraper broke. Use only the JSON API below, ideally
through `yokatlas-py` which wraps it.

## JSON API surface — `https://yokatlas.yok.gov.tr/api/tercih-kilavuz/`

| Path | Returns | Status |
|------|---------|--------|
| `/universiteler` | JSON array of `{"universiteAdi": str, "universiteId": int}` (228 on 2026-09-23) | **Verified live** |
| `/universite-programlar` | JSON array of **program groups** `{"birimGrupId": int, "birimGrupAdi": str, "puanTuru": str}` (611) — the lookup behind `program=` names, *not* a per-university program list | **Verified live** |
| `/universite-iller` | JSON array of `{"ilAdi": str, "ilKodu": int}` (83) | **Verified live** |
| `/search` (POST) | program search driven by `SearchFilters`; a page with `content`, `total_elements`, `yil` (data year) | Verified through yokatlas-py |
| `/api/netler/search` (POST) | average nets per test section per program (`search_netler`, yokatlas-py ≥ 0.7.0) | Read from the 0.7.0 source; not exercised |

Verified first record of `/universiteler`:

```json
{ "universiteAdi": "ABDULLAH GÜL ÜNİVERSİTESİ (KAYSERİ)", "universiteId": 173499 }
```

`list_universities()` via yokatlas-py returned **228 records** on 2026-09-23
(227 on 2026-06-06), each as `{"universite_id": int, "universite_adi": str}`
(the wrapper normalizes the raw camelCase API keys to snake_case). The upstream
README still cites "221 universities"; report the count you actually observe.
No API key is required for any path.

## yokatlas-py (the wrapper this skill uses)

- **Version:** 0.7.0 (released 2026-07-23; 0.6.0 of 2026-04-29 was the JSON-API
  rewrite). Pin **>=0.6.0**; 0.7.0 adds `list_program_groups`, `list_cities` and
  `search_netler`.
- **License:** MIT. **Python:** >=3.10.
- **Install / run:** `pip install yokatlas-py`, or run ad-hoc with
  `uv run --with yokatlas-py python …` (this skill's convention — no global install).
- **Runtime deps:** httpx >=0.28.1, pydantic (>=2.7,<3), pydantic-settings.
  (So this is **not** stdlib-only; the helper script imports `yokatlas-py` and
  fails loudly with manual instructions if it is absent.)

### Public API

Module-level shortcuts:

| Function | Signature | Returns |
|----------|-----------|---------|
| `search_programs` | `search_programs(filters_dict, size=…)` | paginated page of `Program` |
| `get_program` | `get_program(kilavuz_kodu: int)` | one `Program` or `None` |
| `list_universities` | `list_universities()` | every university (count drifts — see above) |
| `list_program_groups` | `list_program_groups()` (≥ 0.7.0) | every program group: `birim_grup_id`, `birim_grup_adi`, `puan_turu` |
| `list_cities` | `list_cities()` (≥ 0.7.0) | provinces: `il_kodu`, `il_adi` |
| `search_netler` | `search_netler(filters_dict, size=…)` (≥ 0.7.0) | average TYT/AYT/YDT nets per program (`NetFilters`) |

Object API: `YokAtlasClient` (sync) / `AsyncYokAtlasClient` (async),
`SearchFilters`, `Program`, `YearlyStats`, `Settings`.

```python
from yokatlas_py import YokAtlasClient, SearchFilters
with YokAtlasClient() as client:
    page = client.search(SearchFilters(puan_turu="SAY", universite="boğaziçi"), size=20)
    for prog in page.content:
        print(prog.current.min_puan, prog.current.basari_sirasi)
```

`Program` carries up to four years: `prog.current` (latest), `prog.history`
(three prior years), `prog.all_years`.

### SearchFilters fields

| Field | Type | Values / meaning |
|-------|------|------------------|
| `puan_turu` | str | `"SAY"`, `"SÖZ"`, `"EA"`, `"DİL"`, `"TYT"` (note diacritics) |
| `universite` / `universite_id` | str/list or int/list | fuzzy name(s) or id(s) |
| `program` / `birim_grup_id` | str/list or int/list | program-**group** name(s) or group id(s) — a name resolves to ONE group: exact match, else the first group containing the text, else a close match (see below) |
| `il` / `il_kodu` | str/list or int/list | province name(s) or code(s) |
| `universite_turu` | str | `"DEVLET"` (state), `"VAKIF"` (foundation/private) |
| `birim_turu_id` | int | `46` = Lisans (bachelor's), `47` = Önlisans (associate) |
| `burs_orani_id` | int | scholarship ratio |
| `ogrenim_turu_id` | int | study mode (full-time / part-time) |
| `kilavuz_kodu` | int | single-program filter (the guide code); snake_case in `SearchFilters` — the camelCase `kilavuzKodu` only appears in the wire payload built by `to_payload()` |
| `min_basari_sirasi` / `max_basari_sirasi` | int | success-rank window |

### Returned statistic fields (`YearlyStats`)

`year, kontenjan, yerlesen, kontenjan_obs, kontenjan_y34, prof, doc, dou,
ogr_gor, ar_gor, kpss1, kpss2, min_puan, basari_sirasi`

| Field | Türkçe → English gloss |
|-------|------------------------|
| `kontenjan` | kontenjan → quota (seats offered) |
| `yerlesen` | yerleşen → placed/enrolled students |
| `min_puan` | taban puan → minimum admission score |
| `basari_sirasi` | başarı sırası → success rank (national rank of last placed student) |
| `prof` | profesör → full professors |
| `doc` | doçent → associate professors |
| `dou` | doktor öğretim üyesi → assistant professors (Dr. lecturer) |
| `ogr_gor` | öğretim görevlisi → instructors |
| `ar_gor` | araştırma görevlisi → research assistants |

**v0.6.0 caveat:** demographic breakdowns (gender, high-school-type splits) are
**not** returned. Only the fields above are available — do not promise others.

## Name resolution (why a search can come back empty)

`universite`, `program` and `il` strings are resolved against the lookup lists
(`yokatlas_py/_lookup.py`): Turkish-aware normalization, then an exact key, then
the **first** entry whose name contains the text (or is contained in it), then a
`difflib` close match; if nothing fits, the call raises a lookup error. Checked
live on 2026-09-23:

| Input | Resolves to |
|-------|-------------|
| `program="bilgisayar"` | Bilgisayar Bilimleri (SAY) — so Boğaziçi + SAY returns 0 programs |
| `program="bilgisayar mühendisliği"` | Bilgisayar Mühendisliği (SAY) — returns kod 102210277 |
| `program="tıp"` / `"psikoloji"` / `"hukuk"` | Tıp / Psikoloji / Hukuk |
| `universite="odtü"` | lookup error — use "orta doğu teknik" |

Use full program-group names (or `birim_grup_id`), and treat an empty page as
"this group has no program matching the other filters".

## Turkish-character handling

yokatlas-py normalizes İ/ı, Ş/ş, Ğ/ğ, Ç/ç, Ö/ö, Ü/ü for fuzzy matching, so
`"boğaziçi"` and `"bogazici"` both resolve. User-facing output should preserve
correct Turkish spelling with diacritics (e.g. "Boğaziçi Üniversitesi").
