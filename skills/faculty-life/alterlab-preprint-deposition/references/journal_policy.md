# Checking a Journal's Preprint Policy (Jisc Open Policy Finder)

Before posting a preprint — especially the *accepted* version — confirm the
intended journal **permits** preprints and on what conditions. The authoritative
machine-readable source is Jisc's **Open Policy Finder**, which merged the former
Sherpa Romeo, Sherpa Juliet, and Sherpa Fact services (launched November 2024)
and aggregates publisher open-access / self-archiving policies journal by
journal.

## Contents

- [Keyless: the public record page](#keyless-the-public-record-page)
- [The API (optional key)](#the-api-optional-key)
- [Reading a prearchiving policy](#reading-a-prearchiving-policy)
- [Offline fallback](#offline-fallback)
- [What to report](#what-to-report)

## Keyless: the public record page

Every journal has a public record page,
`https://openpolicyfinder.jisc.ac.uk/publication/<id>`, readable without an account.
`scripts/journal_policy.py` uses it by default when no key is set (`--backend web`):

1. It finds the record id through the site's own journal search,
   `https://openpolicyfinder.jisc.ac.uk/api/compliance-journal?per_page=10&current_page=1&search=<ISSN or title>`,
   and keeps only an exact ISSN or exact (case-insensitive) title match.
2. It reads the policy pathways embedded in the record page's data
   (`submitted`, `accepted`, `published`, each a list of options with embargo,
   locations, conditions, licence and copyright owner).

```bash
uv run python scripts/journal_policy.py --issn 1476-4687        # Nature
uv run python scripts/journal_policy.py --title "Nature Methods"
```

Checked live on 2026-10-22: ISSN 1476-4687 matched *Nature* (record 4008); the
submitted version is permitted with no embargo in a Preprint Repository (conditions:
link to the publisher version, cite the DOI on publication), while the accepted version
carries a 6-month embargo and is not listed for preprint repositories.

The search endpoint and the page data are the site's own formats, not a documented
API: they can change without notice. When parsing fails the script returns
`unverified` with the record URL, so read that page (or the publisher's policy page)
yourself rather than guessing. The data are licensed CC BY-NC-ND 4.0 — fine for
checking your own submission, not for bulk harvesting (use the API for that).

## The API (optional key)

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

`scripts/journal_policy.py` wraps this when a key is set (`--api-key` or the
`OPEN_POLICY_FINDER_API_KEY` environment variable; `--backend auto` picks the API
then, and `--backend api` forces it) and prints the journal's prearchiving
permission, conditions, embargo, and locations. Without a key the API answers
`{"message":"Forbidden"}`, so `--backend api` with no key exits 2 instead of
silently answering from the record page.

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

## Offline fallback

If the script returns `unverified` or `no_match` (network down, page format changed,
journal not in Open Policy Finder):

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
