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
   neighbourhoods. Database-native queries. Angle keys name the output files, so they are made
   unique; angles beyond 6 are counted and make the run `partial`.
2. **Sweep** — one agent per angle (OpenAlex; PubMed, arXiv, citation graph where they fit), up
   to 200 records saved per angle, top 25 returned with why each matters. Retrieved works only. A
   failed sweep is retried once; angles that still failed are named in the search log.
3. **Merge** (code) — de-duplicate by DOI, else normalized title + year; works surfaced by several
   angles rank first; at most 150 go to clustering (more is counted and makes the run `partial`).
4. **Cluster** — 4–8 themes with key works, methods, and open questions the works themselves raise.
   If clustering fails (after one retry) the map presents works by angle, says so, and no gap is checked.
5. **Gaps** — each candidate gap (up to 12) is searched for existing answers (retried once on
   failure); it is reported as open only if that search completed and found none, narrowed if partly
   answered. Gaps beyond the cap, and gaps whose search did not complete, are listed as
   **unchecked** — never as open.
6. **Map** — status and coverage first, then overview, Mermaid theme diagram, theme sections with
   formatted references, a timeline of landmarks, open gaps turned into candidate research
   questions, answered "gaps" with their answering works, unchecked gaps, and the search log. The
   agents are separate passes of one model, so a gap none of them could fill is a lead to verify,
   not proof that none exists. Read back from disk before its path is returned.

The run is `partial` when an angle failed, clustering failed, a gap is unchecked, or a cap applied;
`blocked` when planning or every sweep failed, or the map could not be written or found.

## Returned payload

| Field | Contents |
|---|---|
| `status`, `status_reasons`, `report` | see `running-workflows.md` |
| `angles`, `works`, `themes` | angle keys swept, distinct key works, theme names |
| `open_gaps`, `answered_gaps`, `unchecked_gaps` | gaps that survived a completed search; count answered; unchecked gaps with why |
| `coverage` | `sweeps` (with `failed_angles`), `works`, `clustering`, `gaps` (requested / dispatched / completed / failed / unresolved / retried, `candidates`, `beyond_cap`), `report`, `id_issues`, agent totals |

## Sequential playbook

Plan, then run the angles one by one saving each result list; merge with a script; cluster; test
each gap with its own search before keeping it, and list the ones you did not test as unchecked.

## Pitfalls

- Declaring a gap from absence of evidence in one database — the gap stage exists to try to fill it.
- Calling a gap open when its search never ran.
- Citation-count bias against recent work — keep the strongest recent papers per angle.
- Vocabulary silos: adjacent fields often study the same thing under another name.
