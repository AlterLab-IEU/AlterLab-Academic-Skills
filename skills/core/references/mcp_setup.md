# Academic MCP setup — keys, config, and the `requests` fallback

The `alterlab-core` and `alterlab-databases` plugins bundle four Model Context
Protocol (MCP) servers that give the citation, literature-review, and database
skills live, deterministic access to scholarly metadata:

| Server name | Source | What it does | Keys needed |
| :--- | :--- | :--- | :--- |
| `pubmed` | `mcp-simple-pubmed` (uvx) | Search PubMed / NCBI E-utilities, fetch abstracts and PMIDs | NCBI **email** (required by NCBI usage policy); NCBI **API key** (optional, 3× rate limit) |
| `openalex` | `openalex-mcp` (npx) | Search 240M+ scholarly works, authors, venues, citations | None (a contact email is sent as the polite-pool `mailto`) |
| `crossref` | `@botanicastudios/crossref-mcp` (npx) | Resolve DOIs, fetch work metadata, search by title/author | None (a contact email is sent as the polite-pool `mailto`) |
| `zotero` | `zotero-mcp` (uvx) | Read your Zotero library: search, metadata, full text | Zotero **library ID**, **library type**, **API key** |

All four are documented below. The server *names* (`pubmed`, `openalex`,
`crossref`, `zotero`) are the keys under `mcpServers` in `.mcp.json` and must stay
in sync with this file — `tests/test_mcp_manifest.py` fails if any server is
present in one but not the other.

## Why these servers

- **PubMed + Crossref + OpenAlex** are the three resolvers behind the
  `alterlab-citation-verifier` existence check (`/cite-check`): a citation that
  resolves in none of them is flagged as likely hallucinated.
- **Zotero** lets the citation and writing skills read the user's actual library
  instead of re-deriving references from memory.

## Configuration (`userConfig`)

These servers read their secrets from `${user_config.*}` substitutions. The keys are
declared once in the plugin manifest (`plugin.json`) `userConfig` block, and Claude
Code prompts for them when the plugin is enabled — users never hand-edit
`settings.json`. The manifest owner should declare:

```json
{
  "userConfig": {
    "ncbi_email": {
      "type": "string",
      "title": "NCBI / contact email",
      "description": "Email sent to NCBI E-utilities, OpenAlex, and Crossref polite pools. Required by NCBI usage policy.",
      "required": true
    },
    "ncbi_api_key": {
      "type": "string",
      "title": "NCBI API key (optional)",
      "description": "Free NCBI API key for 3x higher PubMed rate limits. Leave blank to use the default rate.",
      "sensitive": true
    },
    "zotero_library_id": {
      "type": "string",
      "title": "Zotero library ID",
      "description": "Numeric user ID (My Library > Settings > Feeds/API) or group ID."
    },
    "zotero_library_type": {
      "type": "string",
      "title": "Zotero library type",
      "description": "'user' for a personal library or 'group' for a shared group library.",
      "default": "user"
    },
    "zotero_api_key": {
      "type": "string",
      "title": "Zotero API key",
      "description": "Private key from zotero.org/settings/keys. Needs at least read access.",
      "sensitive": true
    }
  }
}
```

`sensitive: true` values are stored in the system keychain, not `settings.json`.

## Key acquisition

### NCBI email + API key (`pubmed`)
1. **Email** — any valid contact email. NCBI requires it so they can reach you if a
   script misbehaves; it is sent on every E-utilities request. This is the same value
   reused as the OpenAlex/Crossref polite-pool `mailto`.
2. **API key (optional)** — sign in at <https://www.ncbi.nlm.nih.gov/account/>,
   open **Account settings → API Key Management**, and create a key. It raises the
   rate limit from 3 to 10 requests/second.

### OpenAlex (`openalex`)
No key. OpenAlex is fully open; passing a contact email (the `ncbi_email` value)
joins the faster "polite pool". See <https://docs.openalex.org/how-to-use-the-api/rate-limits-and-authentication>.

### Crossref (`crossref`)
No key. Crossref's REST API is open; sending a `mailto` (the `ncbi_email` value)
joins the polite pool for better reliability. See <https://api.crossref.org/swagger-ui/index.html>.

### Zotero (`zotero`)
1. **Library ID** — go to <https://www.zotero.org/settings/keys>; your numeric
   *userID* is shown there. For a group library, use the group's numeric ID.
2. **Library type** — `user` (personal) or `group` (shared).
3. **API key** — on the same page, **Create new private key**, grant at least
   *Allow library access (read)*, and copy the key.

## Fallback: no MCP server, no network

Every skill that calls these servers **degrades gracefully** — it must never block
or fabricate when the MCP layer is unavailable (silent-fallback fix, #1154). The
fallback order is:

1. **MCP server** (preferred) — used when the plugin is enabled and the server is up.
2. **`requests` direct to the public REST APIs** — when no MCP server is present but
   the network is reachable. All four back-ends expose free REST endpoints:
   - PubMed: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/` (E-utilities)
   - OpenAlex: `https://api.openalex.org/works`
   - Crossref: `https://api.crossref.org/works`
   - Zotero: `https://api.zotero.org/`
   Drive any helper script through `uv run python ...` (uv owns the env). Always send
   the contact email as the `mailto`/`tool`/`email` parameter on these calls.
3. **WebSearch / WebFetch** — last resort when `requests` is unavailable or a host is
   unreachable. Lower-confidence; the skill must say so explicitly in its output and
   never upgrade an unverified citation to "verified".

A skill that reaches step 2 or 3 must state in its report that it ran in fallback mode
so the user knows the result was not produced by the deterministic MCP path.
