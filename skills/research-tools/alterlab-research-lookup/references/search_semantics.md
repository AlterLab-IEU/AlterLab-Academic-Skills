# Scholarly backend — query, dedup, ranking and date rules

How `scripts/scholarly_backend.py` (v1.3.0, output `schema_version: 2`) turns a request into
index queries, merges the answers and orders them. Loaded on demand from SKILL.md. The rules
below are what the code does; the offline tests in `tests/test_research_lookup_query.py` check
them.

## 1. Words (natural-language requests)

- The request is NFC-normalised and split into words of **every script**: letters, combining
  marks and digits (Unicode categories L, M, N), with `-` `'` `’` `+` `.` kept inside a word
  (`öz-yeterlik`, `O'Brien`, `C++`, `COVID-19`). Nothing is transliterated or translated:
  `öz-yeterlik öğrenme`, `Μάθηση`, `学习与记忆`, `शिक्षा` reach the indexes as written.
- English routing words ("find", "papers", "on", "recent", "seminal", …) are dropped. The list
  is English only; words in other languages (`ve`, `και`) are kept. If every word is a routing
  word, all words are kept.
- CJK text without spaces stays one word; the indexes do their own segmentation.

## 2. Search syntax

Used when `--terms` is given, or when the request itself contains quotes (`"` `“ ”`),
parentheses, `AND` / `OR` / `NOT` in capitals, or a leading `-` before a word.

| Syntax | Meaning |
|--------|---------|
| `word word` | both (AND) |
| `"exact phrase"` | phrase |
| `a OR b` | either |
| `a AND b` | both |
| `a NOT b`, `a -b` | a, excluding b |
| `( … )` | grouping, any depth |

- **Precedence:** `OR` binds tighter than `AND` (as in Google Scholar):
  `exercise depression OR anxiety` = `exercise AND (depression OR anxiety)`. Use parentheses
  when in doubt; the translated query for each index is printed, fully parenthesised.
- Operators must be capitals. In `--terms`, a lowercase `and` / `or` / `not` is an error
  (write it in capitals, or quote it to search the word); in a request it is an ordinary word.
- `-80` (a digit after the minus) is a word, not an exclusion.
- `--terms` is used **exactly**: no routing-word removal. When syntax is found inside a
  request, routing words are dropped only where they are merely adjacent to other words —
  never an operand of `AND` / `OR` / `NOT`.
- **Malformed syntax.** With `--terms` — unbalanced quote or parenthesis, empty `()` or `""`,
  an operator without a term on both sides, only excluded terms (`NOT fear`), an excluded
  `OR` alternative (`a OR -b`) — the run stops with an error naming the position; nothing is
  searched (`scholarly_backend.py` exits 2, `research_lookup.py` exits 1). In a request
  (no `--terms`), unparseable syntax such as `vitamin D (25(OH)D` falls back to plain words and
  the output carries a note saying so.

### Translation per index (`query_translation`)

Every result records, per index, `{"mode": "exact" | "approximate" | "skipped", "query",
"note"}`, and the markdown output prints it.

| Index | What it receives | Mode |
|-------|------------------|------|
| Europe PMC | `TITLE_ABS:(…)` with `AND` / `OR` / `NOT`, quoted phrases; words with punctuation (`COVID-19`) are quoted | exact |
| arXiv | `all:` terms with `AND` / `OR` / `ANDNOT`, quoted phrases, parentheses | exact (a natural-language request longer than 8 words is cut to 8: approximate) |
| Crossref (`query.bibliographic`) | the positive words as relevance-ranked keywords | natural request or a single word: exact; any `OR` / `AND` / phrase: **approximate** (not enforced); any exclusion: **skipped** |
| Semantic Scholar (`/paper/search`) | same as Crossref; hyphens sent as spaces | same as Crossref |

An excluded term cannot be dropped silently — that would return the excluded topic — so
Crossref and Semantic Scholar are skipped for such a query and listed under "Sources skipped
for this query" with the reason; they are not "no results" and not failures. A record found
only through approximate translations is marked "approximate query only". If you named only
indexes that must be skipped, the run returns no records and says why; it never queries an
index you did not name.

## 3. Merging the same work (dedup)

Records are merged in this order of evidence:

1. **Same DOI** (lower-cased, `https://doi.org/` and `doi:` stripped).
2. **Same provider id** — arXiv id (version stripped), PMID, PMCID — unless both records carry
   **different DOIs**.
3. **Same title, year and first author**, only when at most one record has a DOI: the full
   title, NFKC-normalised and case-folded with punctuation and spacing collapsed (no
   truncation, no ASCII stripping); both years present and at most 1 apart; first-author
   surnames equal when both are present (accents folded for this comparison only). A title
   with no letters or digits never matches anything, and a title matching more than one
   existing record merges with none.

**Preprint vs published.** Records with different DOIs are kept separate even when an index
links them (e.g. Semantic Scholar lists the journal DOI and the arXiv id): the arXiv preprint
(`10.48550/arxiv.…`) and the journal article are different registered versions and may differ
in content. The link is recorded on both as `related_versions` and printed as "other
version(s)"; cite the version you read.

**Distinct papers with the same title** (editorials, "Introduction", replications) stay
separate when their years differ by more than 1, a year is missing, or first authors differ.

Every record lists what it was built from in `merged_from`:
`[{"source", "id", "title", "matched_on": "first" | "doi" | "arxiv_id" | "pmid" | "pmcid" |
"title+year+author"}]`. Each index's citation count stays under its own name in `cited_by`.

## 4. Order

- **Default: `relevance`** (CLI, `search()` and `research_lookup.py`). Each index's own
  relevance order; a record takes its best position across indexes; ties go to records found
  in more indexes. Indexes use different relevance models, so this is a merge of their
  rankings, not a single score.
- **`--rank cited`** (only when asked): draws a larger pool (3× `--limit`, at most 50 per
  index; Europe PMC sorted by its own citation count) and orders it by **one** index's count —
  `--cite-index crossref` (default), `europepmc` or `semanticscholar`. Records without that
  index's count follow in relevance order. Counts from different indexes are never compared
  with each other (they cover different corpora and citation sources). The impact labels
  ("Seminal Work", …) use the same declared index and are working heuristics.
- `"auto"` was removed in v1.3.0 (it switched to citation order unless the request looked
  recent); passing it is an error.
- An offline fixture of synthetic records with graded labels
  (`evals/fixtures/relevance_fixture.json`; labels assigned by the implementing agent,
  awaiting independent human review) is scored with nDCG@5 in the tests. It reproduces one
  failure mode and is not a measure of search quality.

## 5. Dates

- `--since` / `--until`: `YYYY` or `YYYY-MM-DD`, inclusive (`--until 2021` = through
  2021-12-31). An invalid date or `--since` after `--until` is an error before any request.
- Sent to every index: Crossref `filter=from-pub-date:…,until-pub-date:…`; Europe PMC
  `AND FIRST_PDATE:[from TO to]`; arXiv `AND submittedDate:[YYYYMMDD0000 TO YYYYMMDD2359]`;
  Semantic Scholar `year=from-to` (years only). An open end is filled with 1800-01-01 or
  today for Europe PMC and arXiv.
- **Re-checked on the returned dates** (Crossref `issued`, Europe PMC first publication date,
  arXiv first-version date, Semantic Scholar publication date or year). A date given only as a
  year or month counts as in range when that period overlaps the window. Out-of-range records
  are dropped and counted (`date_filter.dropped_out_of_range`); records with no date are
  **kept**, marked `date_unknown: true` / "date unknown", and counted
  (`date_filter.kept_unknown_date`).
- **"recent", "latest", "last year", "past 5 years"** are never turned into a date filter. The
  output carries a note that the wording was not converted and suggests `--since`. A year in
  the topic (`COVID-19 2020 lockdown`) is a search word, not a filter.

## 6. Output (`schema_version: 2`)

`search()` keeps every v1 key (`terms`, `rank`, `records`, `errors`, `queried`, `searched`)
and adds `schema_version`, `query`, `syntax` (`natural` | `terms` | `query-syntax`),
`rank_basis`, `cite_index`, `skipped`, `query_translation`, `date_filter`, `notes` and
`requested`. `queried` now lists only the indexes actually sent a request (skipped ones are in
`skipped`). Records add `pub_date`, `arxiv_id`, `pmid`, `pmcid`, `merged_from`,
`related_versions` and, under a date filter, `date_unknown`. `research_lookup.py --json`
passes `query_translation`, `skipped_sources`, `date_filter`, `notes` and `schema_version`
through.

Part of the AlterLab Academic Skills suite.
