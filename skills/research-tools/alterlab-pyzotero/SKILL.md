---
name: alterlab-pyzotero
description: Work with your Zotero reference library from code — search and read items, collections and tags, export BibTeX / CSL-JSON / RIS, find duplicates and missing DOIs, and create, update or delete items, collections, tags and attachments with the pyzotero client. Keyless by default — the running Zotero 7+ desktop app's local API (pyzotero local=True) or an exported library file (Better BibTeX .bib, CSL JSON, RIS) read offline with the bundled script; a zotero.org Web API key is optional, for remote or group libraries and web writes. Use when working with Zotero libraries programmatically, managing bibliographic references, exporting citations, searching library contents, uploading PDF attachments, or building research automation workflows that integrate with Zotero. Part of the AlterLab Academic Skills suite.
allowed-tools: Read Write Edit Bash
license: MIT
compatibility: No API key required. Reads the running Zotero 7+ desktop app through its local API (pyzotero >= 1.15, Python >= 3.10, local=True), or exported .bib / CSL JSON / RIS files offline with a stdlib script; new items go out as an importable file. Optional - ZOTERO_API_KEY + ZOTERO_LIBRARY_ID for the zotero.org Web API (remote/group libraries, web writes); local writes use Zotero 10+ and a locally granted key. Runs via `uv run python`.
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    last_updated: "2026-10-22"
    credentials: "optional: ZOTERO_API_KEY and ZOTERO_LIBRARY_ID (zotero.org Web API v3 — remote and group libraries, web writes, file uploads), PYZOTERO_LOCAL_API_KEY (writes to the local Zotero 10+ library, granted in Zotero's own Allow dialog; not a zotero.org key)"
---

# Pyzotero

Pyzotero is a Python wrapper for the [Zotero API v3](https://www.zotero.org/support/dev/web_api/v3/start) (current release 1.15.x as of 2026-09). Use it to programmatically manage Zotero libraries: read items and collections, create and update references, upload attachments, manage tags, and export citations. It also ships an optional CLI and MCP server for a local Zotero library.

**No key is needed for the user's own library.** Pick the access path before writing code:

| Path | Needs | Reads | Writes |
|------|-------|-------|--------|
| **Local API** (default when Zotero is open) | Zotero 7+ desktop running, Settings > Advanced > "Allow other applications on this computer to communicate with Zotero" | everything: items, collections, tags, full text, saved searches | Zotero 10+ after the user clicks Allow in Zotero (`authorize_local`) — a local key, not a zotero.org key |
| **Exported file** (Zotero closed, another machine, a colleague's export) | a `.bib` (Better BibTeX auto-export, or File > Export Library), CSL JSON or RIS file | `scripts/zotero_export.py`: search, tags, stats, duplicates, missing fields, subset export | an importable RIS / CSL JSON / BibTeX file the user adds with File > Import… (`new-item --doi` fills metadata from Crossref, keyless) |
| **Web API** (optional) | `ZOTERO_API_KEY` + `ZOTERO_LIBRARY_ID` from zotero.org/settings/keys | the synced web library, incl. group libraries | direct create / update / delete, file uploads |

Ask for (or check) which one applies only when it matters; when the user has given an export file, use it; when they have neither file nor key, write the local-API code and say which Zotero setting it needs. Never ask the user to paste a key into the chat.

## When to Use This Skill

- Reading, searching, or bulk-editing items, collections, and tags in a Zotero library from code
- Creating items from templates, attaching PDFs, or exporting BibTeX / CSL-JSON / formatted bibliographies
- Automating research workflows that sync with Zotero (web library or the local desktop app)
- Scripting the local Zotero library from the terminal (`pyzotero` CLI) or exposing it to an AI client (MCP server)

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Discovering new papers in scholarly databases | `alterlab-research-lookup` or `alterlab-openalex` |
| Converting DOIs to BibTeX or searching Google Scholar/PubMed without a Zotero library | `alterlab-citation-mgmt` |
| Checking that every bibliography entry exists / spotting hallucinated references | `alterlab-citation-verifier` |
| Building an evidence table from a folder of PDFs | `alterlab-pdf-extract` |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-research-lookup`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

## Connecting

**Local API (no key).** In Zotero 7+, enable Settings > Advanced > "Allow other applications on this computer to communicate with Zotero" and keep Zotero open; pyzotero then talks to `http://localhost:23119/api/` with `Zotero(library_id='0', library_type='user', local=True)`. Every read method below works unchanged.

**Web API (optional key)** — for a library on another machine, group libraries, or writes without Zotero 10 — get from https://www.zotero.org/settings/keys:
- **User ID**: shown as "Your userID for use in API calls"
- **API Key**: create at https://www.zotero.org/settings/keys/new
- **Library ID**: for group libraries, the integer after `/groups/` in the group URL

Ask the user to store them in environment variables or a `.env` file:
```
ZOTERO_LIBRARY_ID=your_user_id
ZOTERO_API_KEY=your_api_key
ZOTERO_LIBRARY_TYPE=user  # or "group"
```

See [references/authentication.md](references/authentication.md) for full setup details.

## Installation

```bash
uv add pyzotero
# or with CLI support (local library search, writes, collection management):
uv add "pyzotero[cli]"
# or the MCP server (read-only unless started with --enable-writes):
uv add "pyzotero[mcp]"
```

## Quick Start

```python
import os
from pyzotero import Zotero

if os.environ.get("ZOTERO_API_KEY"):          # optional zotero.org Web API
    zot = Zotero(os.environ["ZOTERO_LIBRARY_ID"], os.environ.get("ZOTERO_LIBRARY_TYPE", "user"),
                 os.environ["ZOTERO_API_KEY"])
else:                                          # keyless: the running Zotero 7+ desktop app
    zot = Zotero(library_id='0', library_type='user', local=True)

# Retrieve top-level items (returns 100 by default)
items = zot.top(limit=10)
for item in items:
    print(item['data']['title'], item['data']['itemType'])

# Search by keyword
results = zot.items(q='machine learning', limit=20)

# Retrieve all items (use everything() for complete results)
all_items = zot.everything(zot.items())
```

Run it with `uv run --python ">=3.11" --with pyzotero python script.py`. A connection error on the local path means Zotero is closed or the setting is off — say which, or offer the exported-file path.

## Exported Library Files (offline, no key, no running Zotero)

When the user has (or can make) an export — Better BibTeX's auto-exported `.bib`, File > Export Library… as BibTeX/BibLaTeX, CSL JSON or RIS — `scripts/zotero_export.py` (stdlib only) answers the usual questions directly from the file. Tags are BibTeX `keywords` (CSL JSON exports carry none); item types are normalised to CSL names (`article-journal`, `paper-conference`, `book`, `chapter`, `report`, `manuscript`, …).

```bash
S=scripts/zotero_export.py
python $S stats   my_library.bib                       # counts by type/year, top tags, missing DOIs, duplicate groups
python $S search  my_library.bib --tag "machine learning"          # repeat --tag for AND; -q "words" for text
python $S dupes   my_library.bib                       # same DOI (case-insensitive), or same title + year
python $S missing my_library.bib --field doi           # also abstract, year, authors, container, pages
python $S export  my_library.json --type article-journal --year-from 2020 --to bibtex -o recent.bib
python $S new-item --doi 10.1038/nature14539 --tag to-read --to ris -o to_import.ris   # Crossref metadata
```

Report results by citation key (and DOI) so the user can find each item in Zotero. `export` keeps Better BibTeX keys and turns CSL item URIs into `author+year+word` keys. "Writes" on this path never touch the library: they produce a file the user imports with File > Import… — or, for a few DOIs, tell them to paste the DOIs into Zotero's **Add Item by Identifier** (magic-wand) button, which is keyless too. Fixing metadata, merging duplicates and moving items between collections in place need the local API (Zotero 10+ writes) or the Web API.

## Core Concepts

- A `Zotero` instance is bound to a single library (user or group). All methods operate on that library.
- Item data lives in `item['data']`. Access fields like `item['data']['title']`, `item['data']['creators']`.
- Pyzotero returns 100 items by default (API default is 25). Use `zot.everything(zot.items())` to get all items.
- Write methods return `True` on success or raise a `PyZoteroError` subclass (from `pyzotero.errors`; all class names end in `Error`, e.g. `ResourceNotFoundError`).

## Reference Files

| File | Contents |
|------|----------|
| [references/authentication.md](references/authentication.md) | Credentials, library types, local mode |
| [references/read-api.md](references/read-api.md) | Retrieving items, collections, tags, groups |
| [references/search-params.md](references/search-params.md) | Filtering, sorting, search parameters |
| [references/write-api.md](references/write-api.md) | Creating, updating, deleting items |
| [references/collections.md](references/collections.md) | Collection CRUD operations |
| [references/tags.md](references/tags.md) | Tag retrieval and management |
| [references/files-attachments.md](references/files-attachments.md) | File retrieval and attachment uploads |
| [references/exports.md](references/exports.md) | BibTeX, CSL-JSON, bibliography export |
| [references/pagination.md](references/pagination.md) | follow(), everything(), generators |
| [references/full-text.md](references/full-text.md) | Full-text content indexing and retrieval |
| [references/saved-searches.md](references/saved-searches.md) | Saved search management |
| [references/cli.md](references/cli.md) | Command-line interface usage |
| [references/error-handling.md](references/error-handling.md) | Errors and exception handling |
| `scripts/zotero_export.py` | Offline search / stats / duplicates / export over .bib, CSL JSON, RIS |

## Common Patterns

### Fetch and modify an item
```python
item = zot.item('ITEMKEY')
item['data']['title'] = 'New Title'
zot.update_item(item)
```

### Create an item from a template
```python
template = zot.item_template('journalArticle')
template['title'] = 'My Paper'
template['creators'][0] = {'creatorType': 'author', 'firstName': 'Jane', 'lastName': 'Doe'}
zot.create_items([template])
```

### Export as BibTeX
```python
zot.add_parameters(format='bibtex')
bibtex = zot.top(limit=50)
# bibtex is a bibtexparser BibDatabase object
print(bibtex.entries)
```

### Local mode (no web API key)
Talks to the running Zotero desktop app (Zotero 7+, with "Allow other applications on this computer to communicate with Zotero" enabled in Settings > Advanced). Reads need no key:
```python
zot = Zotero(library_id='0', library_type='user', local=True)
items = zot.items()
```
Writes to the local library are possible only with Zotero 10 or later and the user's consent: `zot.authorize_local("My script")` makes Zotero show an Allow / Always Allow / Deny dialog. "Allow" yields a single-use key; "Always Allow" yields a key you can store and pass back as `Zotero(..., local=True, local_api_key=...)`. Local API keys are unrelated to zotero.org API keys. Details: [references/authentication.md](references/authentication.md).

Part of the AlterLab Academic Skills suite.
