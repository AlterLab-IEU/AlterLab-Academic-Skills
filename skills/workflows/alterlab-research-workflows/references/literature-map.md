# Playbook — literature-map

**Goal:** a map of a field — themes, landmark and recent works, methods, and research gaps that
survive a search for existing answers. **Default output folder:** `alterlab-literature-map/`
(`angle-*.jsonl`, `literature-map.md`).

## Inputs

| Field | Default | Meaning |
|---|---|---|
| `topic` (or the string argument) | required | the field or question |
| `seeds` | none | DOIs of known key papers; adds a citation-neighbourhood angle |
| `years` | all years, recent emphasis | e.g. `2019–2026` |
| `out_dir` | `alterlab-literature-map` | output folder |

## Stages and acceptance rules

1. **Plan** — 4–6 search angles that each surface different papers: core terms and synonyms,
   methods, populations/settings, adjacent fields' vocabulary, recent preprints, seed citation
   neighbourhoods. Database-native queries.
2. **Sweep** — one agent per angle (OpenAlex; PubMed, arXiv, citation graph where they fit), up
   to 200 records saved per angle, top 25 returned with why each matters. Retrieved works only.
3. **Merge** (code) — de-duplicate by DOI, else normalized title + year; works surfaced by several
   angles rank first.
4. **Cluster** — 4–8 themes with key works, methods, and open questions the works themselves raise.
5. **Gaps** — each candidate gap (up to 12) is searched for existing answers; it is kept only if a
   real search finds none, narrowed if partly answered.
6. **Map** — overview, Mermaid theme diagram, theme sections with formatted references, a
   timeline of landmarks, verified gaps turned into candidate research questions, answered
   "gaps" with their answering works, and the search log.

## Sequential playbook

Plan, then run the angles one by one saving each result list; merge with a script; cluster; test
each gap with its own search before keeping it.

## Pitfalls

- Declaring a gap from absence of evidence in one database — the gap stage exists to try to fill it.
- Citation-count bias against recent work — keep the strongest recent papers per angle.
- Vocabulary silos: adjacent fields often study the same thing under another name.
