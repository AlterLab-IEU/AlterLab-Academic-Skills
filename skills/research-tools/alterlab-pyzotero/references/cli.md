# Command-Line Interface

The pyzotero CLI connects to your **local Zotero installation** (not the remote API). It requires a running Zotero 7+ desktop app with "Allow other applications on this computer to communicate with Zotero" enabled (Settings > Advanced). It is read-only until you run `pyzotero authorize`; the write commands below need Zotero 10 or later.

## Installation

```bash
uv add "pyzotero[cli]"
# or run without installing:
uvx --from "pyzotero[cli]" pyzotero search -q "your query"
```

## Searching

```bash
# Search titles and metadata
pyzotero search -q "machine learning"

# Full-text search (includes PDF content)
pyzotero search -q "climate change" --fulltext

# Filter by item type
pyzotero search -q "methodology" --itemtype journalArticle --itemtype book

# Filter by tags (AND logic)
pyzotero search -q "evolution" --tag "reviewed" --tag "high-priority"

# Search within a collection
pyzotero search --collection ABC123 -q "test"

# Paginate results
pyzotero search -q "deep learning" --limit 20 --offset 40

# Output as JSON (for machine processing)
pyzotero search -q "protein" --json
```

## Getting Individual Items

```bash
# Get a single item by key
pyzotero item ABC123

# Get as JSON
pyzotero item ABC123 --json

# Get child items (attachments, notes)
pyzotero children ABC123 --json

# Get multiple items at once (up to 50)
pyzotero subset ABC123 DEF456 GHI789 --json
```

## Collections & Tags

```bash
# List all collections
pyzotero listcollections

# List all tags
pyzotero tags

# Tags in a specific collection
pyzotero tags --collection ABC123
```

## Full-Text Content

```bash
# Get full-text content of an attachment
pyzotero fulltext ABC123
```

## Item Types

```bash
# List all available item types
pyzotero itemtypes
```

## DOI Index

```bash
# Get complete DOI-to-key mapping (useful for caching)
pyzotero doiindex > doi_cache.json
# Returns JSON: {"10.1038/s41592-024-02233-6": {"key": "ABC123", "doi": "..."}}
```

## Writing to the Local Library

```bash
# One-time: approve a local API key in the Zotero dialog ("Always Allow" to keep it).
# The key is stored in ~/.config/pyzotero/local-api-key.json (or $XDG_CONFIG_HOME);
# PYZOTERO_LOCAL_API_KEY overrides the file.
pyzotero authorize --app-name "My tool"

# Create items from a JSON file (or stdin), filed into a collection with a tag
pyzotero createitem items.json --collection FD9AUNP2 --tag "to read"

# Collections
pyzotero createcollection "Frankenstein Cities" --parent FD9AUNP2
pyzotero addtocollection FD9AUNP2 ABC123 DEF456
pyzotero removefromcollection FD9AUNP2 ABC123
pyzotero movetocollection --from FD9AUNP2 --to X7Y8Z9W0 ABC123

# Check the connection to the local Zotero instance
pyzotero test
```

## Semantic Scholar Lookups

The CLI can query Semantic Scholar around a paper (useful for finding what to add next):

```bash
pyzotero related --doi "10.1038/nature12373" --limit 50
pyzotero citations --doi "10.1038/nature12373" --min-citations 50
pyzotero references --doi "10.1038/nature12373"
pyzotero s2search -q "climate adaptation" --year 2020-2024
```

## MCP Server

`uv add "pyzotero[mcp]"` installs `pyzotero-mcp`, which exposes the local library (and the Semantic Scholar lookups) as MCP tools. It is read-only by default; `--enable-writes` registers create/modify tools (using the key from `pyzotero authorize`) and `--enable-deletes` adds permanent deletion.

```json
{ "mcpServers": { "zotero": { "command": "pyzotero-mcp" } } }
```

## Output Format

By default the CLI outputs human-readable text including title, authors, date, publication, volume, issue, DOI, URL, and PDF attachment paths.

Use `--json` for structured JSON output suitable for piping to other tools.

## Search Behaviour Notes

- Default search covers top-level item titles and metadata fields only
- `--fulltext` expands search to PDF content; results show parent bibliographic items (not raw attachments)
- Multiple `--tag` flags use AND logic
- Multiple `--itemtype` flags use OR logic
