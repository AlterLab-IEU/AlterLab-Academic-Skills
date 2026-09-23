# Academic MCP setup — keys, config, and the `requests` fallback

The `alterlab-core` and `alterlab-databases` plugins bundle three Model Context
Protocol (MCP) servers that give the citation, literature-review, and database
skills live, deterministic access to scholarly metadata:

| Server name | Source (pinned, verified 2026-09-23) | What it does | Keys needed |
| :--- | :--- | :--- | :--- |
| `openalex` | `openalex-mcp@0.1.8` (npx) | Search scholarly works, authors, sources, institutions, topics | OpenAlex **API key** (optional but recommended — keyless use shares a small per-IP daily budget) |
| `crossref` | `@botanicastudios/crossref-mcp@0.0.5` (npx) | Resolve DOIs, fetch work metadata, search by title/author | None (the server reads no environment variables) |
| `zotero` | `zotero-mcp@0.3.1` (uvx) | Read your Zotero library: search, metadata, full text | Zotero **library ID**, **library type**, **API key** (or a local Zotero via `ZOTERO_LOCAL`) |

All three are documented below. The server *names* (`openalex`, `crossref`,
`zotero`) are the keys under `mcpServers` in `.mcp.json` and must stay
in sync with this file — `tests/test_mcp_manifest.py` fails if any server is
present in one but not the other.

Versions are pinned so an upstream release cannot silently break the plugin. The
`openalex` server's `autocomplete` tool ships an invalid input
schema upstream, so Claude Code excludes that one tool; its other ten tools load.

**No bundled PubMed server (since 3.0.0).** The third-party `mcp-simple-pubmed` broke
under mcp 2.x and refuses to start without a contact email, so it was removed rather
than kept as a server that fails for most users. PubMed stays fully available: the
`alterlab-pubmed` skill calls NCBI E-utilities directly (its script reads an optional
`NCBI_API_KEY`), and hosts that offer a PubMed connector (claude.ai does) can use it.

## Why these servers

- **Crossref + OpenAlex** hold the same records that `alterlab-citation-verifier`
  (`/cite-check`) checks references against; its script also queries Semantic
  Scholar, arXiv, and the doi.org Handle API. Biomedical literature goes through the
  `alterlab-pubmed` skill (direct E-utilities) or a host's PubMed connector.
- **Zotero** lets the citation and writing skills read the user's actual library
  instead of re-deriving references from memory.

## Configuration (`userConfig`)

These servers read their secrets from `${user_config.*}` substitutions. The keys are
declared once in the plugin's `userConfig` block (in `.claude-plugin/marketplace.json`),
and Claude Code prompts for them when the plugin is enabled — users never hand-edit
`settings.json`. The declared settings are:

```json
{
  "userConfig": {
    "openalex_api_key": {
      "type": "string",
      "title": "OpenAlex API key (recommended)",
      "description": "Free key from https://openalex.org/settings/api. OpenAlex meters usage per day (since February 2026); keyless requests share a small per-IP budget and fail with HTTP 429 once it is spent.",
      "sensitive": true,
      "default": ""
    },
    "zotero_library_id": {
      "type": "string",
      "title": "Zotero library ID (optional)",
      "description": "Numeric user or group library ID, shown at https://www.zotero.org/settings/keys",
      "default": ""
    },
    "zotero_library_type": {
      "type": "string",
      "title": "Zotero library type",
      "description": "Either 'user' (personal library) or 'group'.",
      "default": "user"
    },
    "zotero_api_key": {
      "type": "string",
      "title": "Zotero API key (optional)",
      "description": "Read access key from https://www.zotero.org/settings/keys",
      "sensitive": true,
      "default": ""
    }
  }
}
```

`sensitive: true` values are stored in the system keychain, not `settings.json`.
The manifests map them to server environment variables: `openalex` gets
`OPENALEX_BEARER_TOKEN`, and `zotero` gets `ZOTERO_LIBRARY_ID` / `ZOTERO_LIBRARY_TYPE` / `ZOTERO_API_KEY`.

## Key acquisition

### NCBI (no bundled server — used by `alterlab-pubmed` and the scripts)
There is nothing to configure in the plugin. For heavy PubMed use, create a free key
at <https://www.ncbi.nlm.nih.gov/account/> (**Account settings → API Key
Management**) and export it as `NCBI_API_KEY`: it raises the E-utilities limit from 3
to 10 requests/second. NCBI asks scripts to identify themselves with a contact email
(`NCBI_EMAIL` in the `mcp-servers/` connectors).

### OpenAlex (`openalex`)
Optional but recommended. Since February 2026 OpenAlex ignores the old `mailto`
"polite pool" and meters usage in US dollars per day: keyless requests share a
budget of $0.10/day per IP address (single-record lookups such as a DOI are free;
list/filter calls cost $0.0001 and searches $0.001 each) and return HTTP 429 once
it is spent. A free key from <https://openalex.org/settings/api> gets its own
$1/day budget. The plugin passes the key to the server as `OPENALEX_BEARER_TOKEN`
(sent as `Authorization: Bearer <key>`); scripts such as
`alterlab-citation-verifier/scripts/verify_citations.py` read `OPENALEX_API_KEY`.
See <https://help.openalex.org/api/authentication/> and
<https://help.openalex.org/access/pricing/>.

### Crossref (`crossref`)
No key, and the MCP server takes no configuration. Crossref still runs a polite
pool (10 requests/second, 3 concurrent) for clients that identify themselves, so
scripts calling the REST API directly should send a `mailto` query parameter or
User-Agent contact. See
<https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/>.

### Zotero (`zotero`)
1. **Library ID** — go to <https://www.zotero.org/settings/keys>; your numeric
   *userID* is shown there. For a group library, use the group's numeric ID.
2. **Library type** — `user` (personal) or `group` (shared).
3. **API key** — on the same page, **Create new private key**, grant at least
   *Allow library access (read)*, and copy the key.
4. **Local alternative** — `zotero-mcp` also honours `ZOTERO_LOCAL` to read a running
   Zotero desktop app instead of the web API.

## Fallback: no MCP server, no network

Every skill that calls these servers **degrades gracefully** — it must never block
or fabricate when the MCP layer is unavailable (silent-fallback fix, #1154). The
fallback order is:

1. **MCP server** (preferred) — used when the plugin is enabled and the server is up.
2. **`requests` direct to the public REST APIs** — when no MCP server is present but
   the network is reachable. These back-ends (and PubMed) expose free REST endpoints:
   - PubMed: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/` (E-utilities)
   - OpenAlex: `https://api.openalex.org/works`
   - Crossref: `https://api.crossref.org/works`
   - Zotero: `https://api.zotero.org/`
   Drive any helper script through `uv run python ...` (uv owns the env). Identify the
   client where the API asks for it — NCBI `email`/`tool`, Crossref `mailto` — and use
   an `OPENALEX_API_KEY` for OpenAlex, which ignores `mailto`. Treat an HTTP 429 as
   "this source could not answer", never as "not found".
3. **WebSearch / WebFetch** — last resort when `requests` is unavailable or a host is
   unreachable. Lower-confidence; the skill must say so explicitly in its output and
   never upgrade an unverified citation to "verified".

A skill that reaches step 2 or 3 must state in its report that it ran in fallback mode
so the user knows the result was not produced by the deterministic MCP path.

## Aggregated data connectors (mcp-servers/)

Beyond the three academic servers above, the repo ships standalone **aggregated MCP
connectors** under `mcp-servers/` (see [`mcp-servers/README.md`](../../../mcp-servers/README.md)).
Each wraps a high-traffic scientific-data cluster behind a typed tool surface and is added to
an MCP client via its own `.mcp.json`:

- `structures` — experimental (RCSB PDB) + predicted (AlphaFold DB) structures and complexes.
- `variants` — gnomAD population frequencies + ClinVar clinical significance (NCBI).
- `chemistry` — PubChem compound lookup/similarity + BindingDB measured affinities.
- `genes-ontologies` — MyGene gene lookup, UniProt entries, QuickGO annotations, Reactome pathways.

These are cross-domain infrastructure, not per-domain skill plugins; NCBI-backed tools read a
contact email from `NCBI_EMAIL` and never hardcode credentials.
