# Search craft — stems, VE/VEYA, fields, TR+EN pairing

These rules turn a plain topic into queries for the **2026** YÖK search as exposed by the
`yoktez-mcp` connector (`search_yok_tez_detailed`). Code values are in `endpoints.md`.

## 1. Search stems that survive substring matching

The default match type is **contains** (`match_type` `2`, "Kelimenin içinde geçsin"): a
term matches any word that contains it. So search a **shorter stem**, not an inflected
form — and cut a final **k/ç/t/p**, because Turkish turns it into ğ/c/d/b before a
vowel-initial suffix:

| User concept | Query this | Why |
|--------------|-----------|-----|
| sürdürülebilirliğin | `sürdürülebilir` | Stem is contained in every inflected form |
| dijitalleşmenin | `dijitalleş` | Covers dijitalleşme, dijitalleşen, … |
| okuryazarlık / okuryazarlığı | `okuryazarl` | `okuryazarlık` misses `okuryazarlığı` — live check 2026-09-23: 277 title hits for `okuryazarlık` vs 622 for `okuryazarl` (2025+) |

Use `match_type` `1` (exact, "Sadece yazılan şekilde") only for a fixed phrase or a name.
Keep proper Turkish spelling (ç ğ ı İ ö ş ü) in queries and in user-facing output.

## 2. Up to three terms, joined by and/or

One call takes `keyword`, `keyword_2`, `keyword_3`, joined by `operator_1` / `operator_2`
(`and` / `or`) — the site's **VE / VEYA**. There is **no NOT** operator in the 2026 search:
drop unwanted hits locally after merging.

| Logic | Connector arguments | Example |
|-------|---------------------|---------|
| AND | `operator_1: "and"` | `keyword: "sanal prodüksiyon", keyword_2: "film"` |
| OR (synonyms) | `operator_1: "or"` | `keyword: "sanal prodüksiyon", keyword_2: "virtual production"` |

Prefer OR for recall (synonyms, spelling variants) and AND only when both concepts must
appear; an AND of two long phrases easily returns nothing.

## 3. Always run BOTH a Turkish AND an English query

English terms only match the **English** title/abstract/keyword fields a thesis provides;
Turkish terms only match the Turkish fields. A thesis indexed in English is **silently
missed** by an all-Turkish query, and vice-versa. For any topic:

1. Run query A with the Turkish stems.
2. Run query B with the English equivalents.
3. Merge and dedupe on `thesis_no`.

## 4. One field per call — pick it deliberately

`search_field` applies to all terms of a call:

- **`7` Tümü** (default) — highest recall for topic searches.
- **`1` Tez Adı** / **`6` Özet** / **`4` Konu** / **`5` Anahtar Kelime** — precision
  passes when the Tümü result is too broad.
- **`2` Yazar** / **`3` Danışman** — people. Names repeat across universities, so confirm
  with `get_yok_tez_thesis_details` (it returns the advisor and the full university →
  institute → department path).

University/institute/department **text** filters no longer exist: filter the merged results
on `university_info`, or find department codes with `list_yok_tez_anabilim_dali` and search
them with `search_yok_tez_by_anabilim_dali`.

## 5. Worked example (originality check)

> "A student wants to do a doctorate on *virtual production in cinema*. Has it been done in
> Turkey?"

```
Query A (TR): keyword="sanal prodüksiyon", keyword_2="sanal çekim", operator_1="or",
              search_field="7"
Query B (EN): keyword="virtual production", search_field="7"
Both:         thesis_type="2" (Doktora) only if the user wants doctorates alone,
              year_start/year_end if the user gave a window,
              permission_status="0"  # include İzinsiz theses — still prior art
              thesis_status="0"      # include Hazırlanıyor (in-preparation) theses;
                                     # the connector defaults to "3" = approved only
```

Merge A+B, dedupe on `thesis_no`, return newest-first
`{thesis_no, year, university_info, advisor, title, izin, durum}`; fetch the advisor with
`get_yok_tez_thesis_details` for the rows the supervisor wants to inspect.
