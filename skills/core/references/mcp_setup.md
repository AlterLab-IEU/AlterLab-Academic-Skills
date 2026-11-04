# Academic MCP setup — config and the `requests` fallback

The `alterlab-core` and `alterlab-databases` plugins bundle one Model Context
Protocol (MCP) server that gives the citation, literature-review, and database
skills live, deterministic access to scholarly metadata, with no key and no account:

| Server name | Source (pinned, verified 2026-09-23) | What it does | Keys needed |
| :--- | :--- | :--- | :--- |
| `crossref` | `@botanicastudios/crossref-mcp@0.0.5` (npx) | Resolve DOIs, fetch work metadata, search by title/author | None (the server reads no environment variables) |

The server *name* (`crossref`) is the key under `mcpServers` in `.mcp.json` and must
stay in sync with this file — `tests/test_mcp_manifest.py` fails if a server is
present in a manifest but not documented here.

Versions are pinned so an upstream release cannot silently break the plugin.

**Removed servers (2026-11-02).** The suite has to work without logging in to
third-party services, so the two bundled servers that needed an account were removed:

- `openalex` — OpenAlex now meters keyless use per IP address: requests without a key
  share a $0.10/day budget, and searches and filtered lists answer HTTP 429
  "Insufficient budget" once it is spent. Real use therefore needs an API key, which
  needs an OpenAlex account. Scholarly search and metadata now go through the keyless
  APIs listed under the fallback below (Crossref, Semantic Scholar, OpenCitations,
  Europe PMC, arXiv, PubMed).
- `zotero` — its web-API mode needs a zotero.org account and API key. The
  `alterlab-pyzotero` skill reads a library keylessly instead: through the running
  Zotero desktop app's local API (`http://localhost:23119/api/`), or from an exported
  `.bib` / CSL-JSON file.

**No bundled PubMed server (since 3.0.0).** The third-party `mcp-simple-pubmed` broke
under mcp 2.x and refuses to start without a contact email, so it was removed rather
than kept as a server that fails for most users. PubMed stays fully available: the
`alterlab-pubmed` skill calls NCBI E-utilities directly (its script reads an optional
`NCBI_API_KEY`), and hosts that offer a PubMed connector (claude.ai does) can use it.

## Why this server

- **Crossref** holds the DOI records that `alterlab-citation-verifier` (`/cite-check`)
  checks references against; its script also queries Semantic Scholar, arXiv, and the
  doi.org Handle API. Biomedical literature goes through the `alterlab-pubmed` skill
  (direct E-utilities) or a host's PubMed connector.
- **The user's own library** comes from `alterlab-pyzotero` (Zotero's local API or an
  exported file), so the citation and writing skills read the user's actual references
  instead of re-deriving them from memory.

## Configuration

Nothing to configure. The `crossref` server reads no environment variables, so the
plugins declare no `userConfig` settings and Claude Code prompts for nothing when they
are enabled.

## Key acquisition

### NCBI (no bundled server — used by `alterlab-pubmed` and the scripts)
There is nothing to configure in the plugin. For heavy PubMed use, create a free key
at <https://www.ncbi.nlm.nih.gov/account/> (**Account settings → API Key
Management**) and export it as `NCBI_API_KEY`: it raises the E-utilities limit from 3
to 10 requests/second. NCBI asks scripts to identify themselves with a contact email
(`NCBI_EMAIL` in the `mcp-servers/` connectors).

### Crossref (`crossref`)
No key, and the MCP server takes no configuration. Crossref also runs a polite pool
(10 requests/second, 3 concurrent) for clients that identify themselves with a contact
address; scripts add one (a `mailto` query parameter or User-Agent contact) only when
the user has set it, for example in `ALTERLAB_CONTACT_EMAIL`. Without it they use the
public pool. See
<https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/>.

### Semantic Scholar (no bundled server — used by the scripts)
Keyless, but the keyless pool is shared by every user and rate-limited, so scripts back
off on HTTP 429. An optional `S2_API_KEY` gives a dedicated rate; nothing needs it.

## Fallback: no MCP server, no network

Every skill that calls these servers **degrades gracefully** — it must never block
or fabricate when the MCP layer is unavailable (silent-fallback fix, #1154). The
fallback order is:

1. **MCP server** (preferred) — used when the plugin is enabled and the server is up.
2. **`requests` direct to the public REST APIs** — when no MCP server is present but
   the network is reachable. These keyless back-ends expose free REST endpoints
   (the web APIs were checked keyless, with no contact address, on 2026-11-02):
   - PubMed: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/` (E-utilities)
   - Crossref: `https://api.crossref.org/works`
   - Semantic Scholar Graph API: `https://api.semanticscholar.org/graph/v1/`
   - OpenCitations Index v2 (citing / cited DOIs, citation counts): `https://api.opencitations.net/index/v2/`
   - Europe PMC: `https://www.ebi.ac.uk/europepmc/webservices/rest/search`
   - arXiv: `https://export.arxiv.org/api/query`
   - Zotero desktop (local, when the app is running): `http://localhost:23119/api/`
   Drive any helper script through `uv run python ...` (uv owns the env). Identify the
   client where the API asks for it — NCBI `tool`, plus NCBI `email` or Crossref
   `mailto` only from a contact address the user set. Treat an HTTP 429 as
   "this source could not answer", never as "not found".
3. **WebSearch / WebFetch** — last resort when `requests` is unavailable or a host is
   unreachable. Lower-confidence; the skill must say so explicitly in its output and
   never upgrade an unverified citation to "verified".

A skill that reaches step 2 or 3 must state in its report that it ran in fallback mode
so the user knows the result was not produced by the deterministic MCP path.

## Aggregated data connectors (mcp-servers/)

Beyond the academic server above, the repo ships standalone **aggregated MCP
connectors** under `mcp-servers/` (see [`mcp-servers/README.md`](../../../mcp-servers/README.md)).
Each wraps a high-traffic scientific-data cluster behind a typed tool surface and is added to
an MCP client via its own `.mcp.json`:

- `structures` — experimental (RCSB PDB) + predicted (AlphaFold DB) structures and complexes.
- `variants` — gnomAD population frequencies + ClinVar clinical significance (NCBI).
- `chemistry` — PubChem compound lookup/similarity + BindingDB measured affinities.
- `genes-ontologies` — MyGene gene lookup, UniProt entries, QuickGO annotations, Reactome pathways.

These are cross-domain infrastructure, not per-domain skill plugins; NCBI-backed tools read a
contact email from `NCBI_EMAIL` and never hardcode credentials.
