---
name: alterlab-pyzotero
description: Interact with Zotero reference management libraries using the pyzotero Python client — retrieve, create, update, and delete items, collections, tags, and attachments via the Zotero Web API v3. Use when working with Zotero libraries programmatically, managing bibliographic references, exporting citations, searching library contents, uploading PDF attachments, or building research automation workflows that integrate with Zotero. Part of the AlterLab Academic Skills suite.
allowed-tools: Read Write Edit Bash
license: MIT
compatibility: pyzotero >= 1.15 (Python >= 3.10). Requires a Zotero account and ZOTERO_API_KEY (plus library ID) for the Web API; local mode reads a running Zotero 7+ desktop app with no key, and local writes need Zotero 10+ plus a locally authorized key. Runs via `uv run python`.
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# Pyzotero

Pyzotero is a Python wrapper for the [Zotero API v3](https://www.zotero.org/support/dev/web_api/v3/start) (current release 1.15.x as of 2026-09). Use it to programmatically manage Zotero libraries: read items and collections, create and update references, upload attachments, manage tags, and export citations. It also ships an optional CLI and MCP server for a local Zotero library.

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

## Authentication Setup

**Required credentials** — get from https://www.zotero.org/settings/keys:
- **User ID**: shown as "Your userID for use in API calls"
- **API Key**: create at https://www.zotero.org/settings/keys/new
- **Library ID**: for group libraries, the integer after `/groups/` in the group URL

Store credentials in environment variables or a `.env` file:
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
from pyzotero import Zotero

zot = Zotero(library_id='123456', library_type='user', api_key='ABC1234XYZ')

# Retrieve top-level items (returns 100 by default)
items = zot.top(limit=10)
for item in items:
    print(item['data']['title'], item['data']['itemType'])

# Search by keyword
results = zot.items(q='machine learning', limit=20)

# Retrieve all items (use everything() for complete results)
all_items = zot.everything(zot.items())
```

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
