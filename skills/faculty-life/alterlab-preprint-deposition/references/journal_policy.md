# Checking a Journal's Preprint Policy (Jisc Open Policy Finder API)

Before posting a preprint — especially the *accepted* version — confirm the
intended journal **permits** preprints and on what conditions. The authoritative
machine-readable source is Jisc's **Open Policy Finder**, which merged the former
Sherpa Romeo, Sherpa Juliet, and Sherpa Fact services (launched November 2024)
and aggregates publisher open-access / self-archiving policies journal by
journal.

## Contents

- [The API](#the-api)
- [Reading a prearchiving policy](#reading-a-prearchiving-policy)
- [Offline / no-key fallback](#offline--no-key-fallback)
- [What to report](#what-to-report)

## The API

- **Endpoint:** `https://api.openpolicyfinder.jisc.ac.uk/retrieve` (object
  retrieval API). The legacy Sherpa Romeo endpoint
  `https://v2.sherpa.ac.uk/cgi/retrieve` was switched off at the end of July
  2026; old integrations must move to the new host.
- **Authentication:** a valid API key sent in the **`x-api-key` request
  header** (the legacy API took `api-key` as a query parameter; the new platform
  does not). Existing Sherpa keys were migrated. New keys are requested by
  emailing help@jisc.ac.uk (subject "Open policy finder API request") with your
  name, organisation, and intended use. The data are licensed CC BY-NC-ND 4.0,
  so the API is for non-commercial use.
- **Parameters** — the query paths and JSON format of the Sherpa API were carried
  over unchanged:
  - `item-type=publication` — query a journal/publication's policy.
  - `format=Json` (or `Ids`).
  - `filter=` — a JSON array of `[fieldname, operator, value]` triples, e.g.
    filter by ISSN or title. URL-encode it.
  - `limit` / `offset` — paging (use `search_after` beyond 10,000 records).

Example shape (do not run with a placeholder key):

```
curl -H "x-api-key: $OPEN_POLICY_FINDER_API_KEY" \
  'https://api.openpolicyfinder.jisc.ac.uk/retrieve?item-type=publication&format=Json&limit=1&filter=%5B%5B%22issn%22%2C%22equals%22%2C%221234-5678%22%5D%5D'
```

`scripts/journal_policy.py` wraps this: pass `--issn` or `--title` plus a key
(`--api-key` or the `OPEN_POLICY_FINDER_API_KEY` environment variable), and it
prints the journal's prearchiving permission, conditions, embargo, and
locations. Without a key the API answers `{"message":"Forbidden"}`.

## Reading a prearchiving policy

A publication record carries `publisher_policy[]`, each with a list of
`permitted_oa[]` pathways. Each pathway names an `article_version` list:

- **submitted** — the manuscript *before* peer review. This is the version a
  preprint server hosts; check a pathway permits it.
- **accepted** (AAM / postprint) — after peer review, before typesetting.
- **published** (version of record) — the publisher PDF; rarely allowed on a
  preprint server.

Per pathway, surface: `conditions` (free-text requirements, e.g. a required
statement or a link to the published DOI), `embargo` (`amount` + `units`),
`location.location` / `location.location_phrases` (e.g. `preprint_repository`,
`any_repository`, `named_repository`), `license`, `prerequisites`, and
`copyright_owner`. Human-readable labels live in the matching `*_phrases`
arrays.

## Offline / no-key fallback

If no API key is available or the network is down:

1. WebFetch the **publisher's own** preprint/sharing policy page and quote it.
2. State explicitly that the policy was read live (not from memory) and link the
   source.
3. If neither is reachable, instruct the user to check the journal manually at
   https://openpolicyfinder.jisc.ac.uk/ and do **not** assert a policy.

## What to report

- The journal name + ISSN matched.
- The **preprint (prearchiving) permission**: permitted / restricted / not
  addressed.
- Any **conditions** (embargo, version, required notice, DOI link, location).
- The **source** (the Open Policy Finder record URL or the publisher policy URL).
- A recommendation: post now / post submitted version only / wait until after
  acceptance / pick a lower-friction license (cross-ref `licensing.md`). Remember
  that bioRxiv and medRxiv will not post a manuscript a journal has already
  accepted, whatever the journal allows.
