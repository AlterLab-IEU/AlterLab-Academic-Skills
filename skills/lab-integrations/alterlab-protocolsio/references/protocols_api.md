# Protocols API

Source: https://apidoc.protocols.io/ (checked 2026-09-23). Paths are relative to `https://www.protocols.io/api` unless shown in full. Every request needs `Authorization: Bearer <token>`; private or shared protocols need a token for a user who can see them.

## Identifiers

| Form | Example | Accepted by |
|------|---------|-------------|
| Integer id | `8503` | Most protocol endpoints |
| URI (slug) | `tree-mapping-for-leaf-collection-megantic-only-baaciaaw` | Most protocol endpoints; required by publish, bookmarks, comments |
| DOI | `10.17504/protocols.io.baaciaaw` or `protocols.io.baaciaaw` | v4 get protocol, v4 get steps |
| GUID (no dashes) | `28C5E0F0D96211E9A8EB9746B7AE9660` | Create (client-generated), v4 update, v4 steps write/delete |

Append `/v1`, `/v2`, ... to a DOI or URI for a specific version, or `/latest` for the newest version (for example `10.17504/protocols.io.baaciaaw/latest`).

## Search and list

### Search protocols — `GET /v3/protocols`

| Parameter | Notes |
|-----------|-------|
| `filter` (required) | `public` (all public), `user_public` (your published), `user_private` (your private), `shared_with_user` (private, shared with you) |
| `key` (required) | Searches title, description, and authors; wrap the phrase in double quotes for an exact match |
| `order_field` | `activity` (default, popularity), `relevance`, `date`, `name`, `id` |
| `order_dir` | `desc` (default) or `asc` |
| `fields` | Comma-separated list of item fields to return |
| `page_size` / `page_id` | 1–100 (default 10) / from 1 |
| `peer_reviewed` | `1` only journal-peer-reviewed protocols, `0` only the others |

Returns `items` (protocol objects: `id`, `title`, `doi` such as `dx.doi.org/10.17504/protocols.io.c4gytv`, `uri`, `published_on`, `creator`, `versions`, ...), `total`, `total_pages`, and `pagination`. For the `user_*` and `shared_with_user` filters, all versions of a protocol come back as one item; iterate its `versions` field if you need each one. Error `1302` means an unsupported `order_field`.

```bash
curl -H "Authorization: Bearer $PROTOCOLS_IO_TOKEN" \
  "https://www.protocols.io/api/v3/protocols?filter=public&key=%22golden%20gate%22&order_field=relevance&page_size=20"
```

### A researcher's protocols — `GET /v3/researchers/<username>/protocols`

`filter` is `user_all` or `user_public`; optional `key`, `order_field` (`activity`, `date`, `name`, `id`), `order_dir`, `page_size`, `page_id`.

### A workspace's protocols — `GET /v3/workspaces/<workspace_uri>/protocols`

Optional `key`, `order_field`, `order_dir`, `page_size`, `page_id`. Error `132` means access denied (private workspace you are not a member of).

### Recent publications — `GET /v3/publications`

- `?latest=N` returns the N most recent publications (1–100).
- `?from=<unix>&to=<unix>` returns publications in a window; windows longer than 10 days are cut to 10 days from `from`.

## Read

### Get a protocol — `GET /v4/protocols/<id>`

`<id>` is an integer id, URI, or DOI (with optional version suffix). Query parameters: `last_version=1` (return the newest version), `content_format=json|html|markdown` (format of `description`, `before_start`, `guidelines`, `warning`, `materials_text`, and each `steps[i].step`; `json` is Draft.js).

The documented example response wraps the protocol in `payload` (`{"payload": {...}, "status_code": 0}`), while the parameter table calls the field `protocol`; read `payload` and fall back to `protocol`. The protocol object includes `title`, `authors`, `doi`, `uri`, `url`, `guid`, `steps`, `materials`, `units`, `versions`, `version_id`, `stats`, `access` (what the token may do: `can_edit`, `can_publish`, `can_get_doi`, ...), and `warning`.

The v3 form (`GET /v3/protocols/<id>`) is archived; use v4.

### Get steps — `GET /v4/protocols/<id>/steps`

Same `id`, `last_version`, and `content_format` options. Each step has `id`, `guid`, `previous_id`, `previous_guid`, `modified_on`, the step text in `step`, and `components`. Order the list by following `previous_guid` from the step whose `previous_guid` is `null`.

### Get materials — `GET /v3/protocols/<id>/materials`

Returns `materials`, a list of reagent objects.

### Search reagents — `GET /v3/reagents`

`key` (required); `is_citeab` (`true` only CiteAb reagents, `false` exclude them, unset all); optional `from`/`to` timestamps, `page_id`, `page_size`.

### PDF — `GET https://www.protocols.io/view/<id-or-uri>.pdf`

Options: `compact_view`, and one of `only_materials`, `only_commands`, `only_steps` (mutually exclusive). Returns `application/pdf`; 401 not authorized, 404 not found, 429 over the limit (5 per minute signed in, 3 per minute signed out). Cache PDFs rather than re-downloading them.

## Write

Writes apply to protocols the token's user can edit. Plan the sequence: create → update metadata → write steps → review in the web editor → publish.

### Create — `POST /v3/protocols/<guid>`

`<guid>` is a new GUID without dashes that you generate (for example `uuid.uuid4().hex.upper()`). Form field `type_id`: `1` protocol (default), `3` collection, `4` document. Returns `{"status_code": 0, "protocol": {...}}` with the new private protocol (use its `id`, `uri`, `guid`). Error `1905`: workspace subscription limit reached.

### Update metadata — `PUT /v4/protocols/<id-uri-or-guid>`

JSON body; send only the fields to change. Returns `{"status_code": 0}` or an error with `status_text`.

| Field | Editable on | Notes |
|-------|-------------|-------|
| `title`, `description`, `before_start`, `guidelines`, `warning`, `materials_text`, `link` | Private only | Plain strings |
| `collection_items` | Private collections only | Full ordered list, e.g. `[{"content_id": 100, "content_type_id": 1}, {"content_id": 1000, "content_type_id": 15}]` (1 = protocol, 15 = file) |
| `disclaimer`, `ethics_statement`, `manuscript_citation`, `protocol_references`, `keywords` | Private and public | Strings |
| `is_content_confidential`, `is_content_warning`, `is_research` | Private and public | Booleans |
| `status_id` | Private and public | `1` working, `2` still optimizing, `3` could not get it to work |
| `funders` | Private and public | `[{"funder_name": "...", "grant_id": "..."}]` |

Errors include `400 invalid status id`, `400 protocol is not a collection`, `401 you don't have access to edit this protocol`, `401 "<field>" can't be changed for public protocols`, and `404 protocol does not exist`.

```bash
curl -X PUT "https://www.protocols.io/api/v4/protocols/$PROTOCOL_GUID" \
  -H "Authorization: Bearer $PROTOCOLS_IO_TOKEN" -H "Content-Type: application/json" \
  --data '{"title": "Golden Gate assembly of MoClo level-1 constructs", "status_id": 2,
           "funders": [{"funder_name": "Example Foundation", "grant_id": "EF-0000"}]}'
```

The archived v3 "save protocol changes" call (`PUT /v3/protocols/<guid>` with an `actions` array) is superseded by this endpoint.

### Create or update steps — `POST /v4/protocols/<id>/steps`

Private protocols only. JSON body `{"steps": [...]}` containing only the steps to add or change:

| Field | Required | Notes |
|-------|----------|-------|
| `guid` | Yes | Step GUID (new for a new step) |
| `previous_guid` | Yes | GUID of the preceding step; `null` for the first step (only one step may have `null`) |
| `step` | Yes | Step text (plain text) |
| `section`, `section_color` | No | Section name and HEX colour |
| `is_substep` | No | `true` for a substep |

To insert a step between steps 1 and 2, send the new step (with `previous_guid` = step 1's GUID) and step 2 (with `previous_guid` = the new step's GUID). The API validates the chain and rejects loops, multiple first steps, missing first steps, and broken sequences. Protocols that use step cases cannot be edited through this endpoint.

### Delete steps — `DELETE /v4/protocols/<id>/steps`

JSON body `{"steps": ["<guid1>", "<guid2>"]}`. Private protocols only; not supported for protocols with step cases. After removing a step from the middle, re-read the steps and repair the next step's `previous_guid` with the POST call if the chain is broken.

### Publish — `POST /v3/protocols/<protocol_uri>/publish`

Issues a DOI and, unless `prepublish=1`, makes the protocol public. Optional parameters: `title` (sets the title while publishing) and `prepublish=1` (reserve a DOI without making the protocol public, e.g. while a paper is in review). The protocol needs a title and at least one author. Once a version has a DOI it cannot be edited. Errors: `101` not authorized, `255` already public, `256` title required, `257` at least one author required.

### Bookmarks

`POST /v3/protocols/<protocol_uri>/bookmarks` adds a bookmark; `DELETE` on the same path removes it.

## Operational notes

- Check the JSON `status_code` of every response (0 = success); errors typically come back as HTTP 400.
- Stay under 100 requests per minute per user; batch reads with `page_size` up to 100 and cache protocol JSON locally.
- Record the DOI and version of any protocol you use or adapt, and cite it as `https://doi.org/10.17504/protocols.io.<id>` with the version.
