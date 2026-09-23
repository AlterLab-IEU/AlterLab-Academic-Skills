---
name: alterlab-protocolsio
description: Works with protocols.io through its REST API (v3 and v4 endpoints) and official MCP server — search and retrieve protocols by keyword, URI, or DOI; create private protocols, edit their metadata and steps, and publish them with a DOI; manage protocol and step discussions, workspaces, file-manager items, file uploads, experiment records, and organization exports. Use when discovering, drafting, publishing, or citing protocols.io protocols, recording protocol runs, or wiring protocols.io into lab documentation. Not for general ELN notebooks (use alterlab-benchling or alterlab-labarchive) or for driving liquid-handling robots. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(curl:*) Bash(python:*)
compatibility: Requires a protocols.io access token — a CLIENT_ACCESS_TOKEN from https://www.protocols.io/developers (your own plus public content) or an OAUTH_ACCESS_TOKEN from the OAuth 2.0 flow (another user's content, with their consent). The official remote MCP server at https://www.protocols.io/mcp accepts the same tokens.
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# Protocols.io Integration

## Overview

protocols.io hosts versioned, citable scientific protocols (each published version gets a DOI under `10.17504/protocols.io.*`), plus team workspaces, experiment run records, and a file manager. It offers two programmatic routes:

- **Official MCP server** — `https://www.protocols.io/mcp` (Streamable HTTP; OAuth 2.0 sign-in or a Bearer client token). It is also listed in Claude's connector directory as "protocols.io".
- **REST API** — base `https://www.protocols.io/api`, split across versions: most endpoints are `v3`, while getting/updating protocols, protocol steps, run records, file-manager search, and organization exports use `v4`. The API reference is https://apidoc.protocols.io/.

## When to Use This Skill

- Searching protocols.io for protocols by keyword, author, or workspace, or resolving a protocol from its DOI or URI
- Reading a protocol's steps and materials (as Markdown, HTML, or Draft.js JSON) to analyse, adapt, or compare it
- Creating a private protocol, filling in its metadata and steps, and publishing it (or reserving a DOI) for citation in a paper
- Reading or posting protocol comments and step discussions
- Listing or joining workspaces, searching workspace files, uploading files, and exporting an organization's content
- Creating and updating experiment run records for a protocol

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Recording results in a general electronic lab notebook (entries, attachments, notebook backups) | `alterlab-labarchive` (LabArchives) or `alterlab-benchling` (Benchling) |
| Turning a written protocol into a script for an Opentrons OT-2/Flex or a Hamilton/Tecan liquid handler | `alterlab-opentrons` or `alterlab-pylabrobot` |
| Depositing a preprint or choosing a data/code repository (bioRxiv, OSF, Zenodo) | `alterlab-preprint-deposition` or `alterlab-open-science` |
| Writing or polishing a manuscript's Methods section | `alterlab-scientific-writing` |

## Prefer the MCP Server When It Is Connected

If protocols.io tools are available in the session (connector or MCP server), use them for search, retrieval, and editing: they run on the user's own account, handle OAuth, and return live data. Fall back to the REST calls below for anything the tools do not cover, or when no connector is attached. To connect one, add `https://www.protocols.io/mcp` as a remote MCP server (or add "protocols.io" from Claude's connector directory) and sign in. Either way, cite the protocol DOI and the retrieval date when reporting protocol content.

## Authentication

| Token | Where it comes from | Reaches |
|-------|---------------------|---------|
| `CLIENT_ACCESS_TOKEN` | https://www.protocols.io/developers | Public content + the private content of the user who created the client |
| `OAUTH_ACCESS_TOKEN` | OAuth 2.0 authorization-code flow | Public content + the authorizing user's private content |

Send it on every request as `Authorization: Bearer <token>`, and keep it in an environment variable (for example `PROTOCOLS_IO_TOKEN`), never in code or notebooks. OAuth tokens last about a year; the API warns a month before expiry and a refresh invalidates the old token pair. The authorization link, token exchange, and refresh calls are in `references/authentication.md`.

## Request Basics

**Identifiers.** Protocol endpoints accept an integer `id`, the protocol `uri` (slug such as `tree-mapping-for-leaf-collection-megantic-only-baaciaaw`), and — for the v4 get/steps endpoints — the DOI (`10.17504/protocols.io.baaciaaw` or `protocols.io.baaciaaw`). Append `/v1` for a specific version or `/latest` for the newest one. Write endpoints also accept the protocol `guid`.

**Content format.** v4 protocol, steps, and record reads take `content_format=json|html|markdown` for rich-text fields (description, guidelines, warnings, materials text, step text). `json` is Draft.js; request `markdown` when the text will be read or summarised.

**Pagination.** List endpoints take `page_id` (starting at 1) and `page_size` (1–100, default 10) and return a `pagination` object.

**Errors are in the body.** Every response carries a JSON `status_code`, where `0` means success. Failures usually arrive as **HTTP 400** with `error_message` (v3) or `status_text` (v4) — a missing or bad token is `1218`, an expired OAuth token `1219` — so check `status_code`, not only the HTTP status.

**Rate limits.** 100 requests per minute per user; the PDF endpoint (`/view/<uri>.pdf`) allows 5 per minute signed in and 3 per minute signed out. Exceeding a limit returns HTTP 429.

## Endpoint Map

| Task | Call | Details |
|------|------|---------|
| Search protocols | `GET /v3/protocols?filter=public&key=...` | `references/protocols_api.md` |
| A researcher's or workspace's protocols | `GET /v3/researchers/<username>/protocols`, `GET /v3/workspaces/<uri>/protocols` | `protocols_api.md`, `workspaces.md` |
| Get a protocol (with steps and materials) | `GET /v4/protocols/<id-uri-or-doi>` | `protocols_api.md` |
| Get steps / materials | `GET /v4/protocols/<id>/steps`, `GET /v3/protocols/<id>/materials` | `protocols_api.md` |
| Create a protocol | `POST /v3/protocols/<new-guid>` | `protocols_api.md` |
| Update metadata | `PUT /v4/protocols/<id>` (JSON) | `protocols_api.md` |
| Add, change, or delete steps | `POST` / `DELETE /v4/protocols/<id>/steps` | `protocols_api.md` |
| Publish or reserve a DOI | `POST /v3/protocols/<uri>/publish` (`prepublish=1` reserves) | `protocols_api.md` |
| Bookmark | `POST` / `DELETE /v3/protocols/<uri>/bookmarks` | `protocols_api.md` |
| PDF | `GET https://www.protocols.io/view/<id-or-uri>.pdf` | `protocols_api.md` |
| Recently published | `GET /v3/publications?latest=N` or `?from=&to=` | `protocols_api.md` |
| Comments and step discussions | `/v3/protocols/<uri>/comments`, `/v3/steps/<step_id>/discussions` | `references/discussions.md` |
| Workspaces and membership | `/v3/workspaces`, `/v3/workspaces/<uri>/members` | `references/workspaces.md` |
| File-manager search, trash, uploads | `/v4/filemanager/.../search`, `/v3/filemanager/trash`, `/v3/files` | `references/file_manager.md` |
| Profile, run records, notifications, org export | `/v3/session/profile`, `/v3/records`, `/v3/researchers/notifications`, `/v4/organizations/<uri>/content/exports` | `references/additional_features.md` |

All paths are relative to `https://www.protocols.io/api` except the PDF view. `https://protocols.io/...` redirects to the `www.` host; there is no `api.protocols.io` host.

## Python Examples

The examples use `requests` and one helper that turns protocols.io's in-body errors into exceptions:

```python
import os
import time
import uuid

import requests

BASE = "https://www.protocols.io/api"
HEADERS = {"Authorization": f"Bearer {os.environ['PROTOCOLS_IO_TOKEN']}"}


def call(method, path, retries=3, **kwargs):
    """Send a request; back off on HTTP 429 and raise when the JSON status_code is not 0."""
    for attempt in range(retries):
        resp = requests.request(method, f"{BASE}{path}", headers=HEADERS, timeout=60, **kwargs)
        if resp.status_code == 429 and attempt < retries - 1:
            time.sleep(int(resp.headers.get("Retry-After", 30 * (attempt + 1))))
            continue
        try:
            data = resp.json()
        except ValueError:  # e.g. an HTML error page from a proxy
            resp.raise_for_status()
            raise
        if data.get("status_code", 0) != 0:
            message = data.get("error_message") or data.get("status_text")
            raise RuntimeError(f"protocols.io {data.get('status_code')}: {message} (HTTP {resp.status_code})")
        return data
    raise RuntimeError("protocols.io rate limit: retries exhausted")
```

### Search and cite

```python
found = call("GET", "/v3/protocols", params={
    "filter": "public", "key": "CRISPR", "order_field": "relevance", "page_size": 10,
})
for item in found["items"]:
    doi = (item.get("doi") or "").removeprefix("dx.doi.org/")  # list items use a dx.doi.org/ prefix
    print(item["title"], f"https://doi.org/{doi}" if doi else "(no DOI yet)")
```

Put the search phrase in double quotes inside `key` for an exact-match search.

### Read a protocol by DOI, as Markdown

```python
data = call("GET", "/v4/protocols/10.17504/protocols.io.baaciaaw",
            params={"content_format": "markdown"})
protocol = data.get("payload") or data.get("protocol")  # current v4 responses use "payload"
print(protocol["title"], protocol["url"])
for number, step in enumerate(protocol.get("steps", []), start=1):
    print(number, step.get("step"))
```

### Create, fill in, and publish a protocol

```python
guid = uuid.uuid4().hex.upper()  # new GUID without dashes, generated client-side
created = call("POST", f"/v3/protocols/{guid}", data={"type_id": 1})  # 1 protocol, 3 collection, 4 document
uri = created["protocol"]["uri"]

call("PUT", f"/v4/protocols/{guid}", json={
    "title": "CRISPR-Cas9 knockout in HEK293T cells",
    "description": "RNP electroporation workflow with T7E1 validation.",
    "materials_text": "SpCas9 nuclease; synthetic sgRNA; Neon electroporation kit",
    "status_id": 2,  # 1 working, 2 still optimizing, 3 could not get it to work
})

# Steps are ordered by previous_guid: the first step has previous_guid None.
texts = ["Anneal and complex sgRNA with Cas9 (10 min, room temperature).",
         "Electroporate 2e5 cells per reaction.",
         "Harvest genomic DNA after 72 h and run the T7E1 assay."]
steps, previous = [], None
for text in texts:
    step_guid = uuid.uuid4().hex.upper()
    steps.append({"guid": step_guid, "previous_guid": previous, "step": text})
    previous = step_guid
call("POST", f"/v4/protocols/{guid}/steps", json={"steps": steps})

# Reserve a DOI without making it public (drop prepublish to publish openly).
call("POST", f"/v3/protocols/{uri}/publish", params={"prepublish": 1})
```

Publishing needs a title and at least one author, and a version with a DOI can no longer be edited, so review the protocol in the web editor first. Published protocols accept only a subset of `PUT` fields (keywords, disclaimer, ethics statement, manuscript citation, references, funders, and the status/warning flags); content changes need a new version, which the API does not document, so create it in the web editor.

### Upload a file

Uploads are three calls: register the file, send the bytes to S3 with the returned policy, then confirm:

```python
path = "results.csv"
prep = call("POST", "/v3/files", data={"filename": os.path.basename(path)})
form, meta = prep["formData"], prep["metaData"]
fields = {"key": form["key"], "acl": form["acl"], "AWSAccessKeyId": form["AWSAccessKeyId"],
          "Policy": form["Policy"], "Signature": form["Signature"], "Content-Type": form["ContentType"]}
with open(path, "rb") as fh:  # the file must be the last form field
    s3 = requests.post(f"https://{form['s3_bucket']}.s3.amazonaws.com/", data=fields,
                       files={"file": (os.path.basename(path), fh)}, timeout=300)
s3.raise_for_status()
call("PUT", f"/v3/files/{meta['file_id']}")  # verify the upload
```

The documented upload call takes no folder, workspace, or tag fields. Attach the returned `file_id` to a collection (`collection_items` with `content_type_id` 15) or organise it in the web app. The S3 step follows the standard S3 POST-policy form, which the API docs do not spell out; try it with a small file first. See `references/file_manager.md`.

## Common Workflows

**Import and analyse an existing protocol.** Search (`GET /v3/protocols`), fetch the chosen one as Markdown (`GET /v4/protocols/<doi>`), read its comments (`GET /v3/protocols/<uri>/comments`) for reported fixes, and record the DOI and version you used.

**Draft and publish a lab protocol.** Create (`POST /v3/protocols/<guid>`), set metadata (`PUT /v4/protocols/<guid>`), add steps in order (`POST /v4/protocols/<guid>/steps`), review with co-authors in the web editor, then reserve a DOI with `prepublish=1` while the paper is under review and publish when it is accepted.

**Document protocol runs.** Create a run record from the protocol (`POST /v3/records` with `protocol_uri`), then check off steps and add notes with `PUT /v3/records/<guid>` (see `references/additional_features.md`). Store raw data in your ELN or repository and cite the record or protocol there.

**Team workspace.** List the user's workspaces (`GET /v3/workspaces?filter=my_groups`), list or search a workspace's protocols and files, and request to join a public workspace with `POST /v3/workspaces/<uri>/members` (see `references/workspaces.md`).

**Institutional archive.** On an organization account, start a full content export (`POST https://<subdomain>.protocols.io/api/v4/organizations/<org_uri>/content/exports`) and poll it until `download_link` is set.

## Citing Protocols

Cite the version you actually used: `Author(s). Title. protocols.io. https://doi.org/10.17504/protocols.io.<id>`, keeping the version suffix (`/v1`, `/v2`, ...) when the DOI carries one. A version with a DOI cannot be edited, but `/latest` follows new versions, so pin the version in methods sections and data records.

## Troubleshooting

| Symptom | Likely cause and fix |
|---------|----------------------|
| HTTP 400 with `status_code` 1218 | Missing or malformed `Authorization: Bearer <token>` header |
| `status_code` 1219 "token is expired" | Refresh the OAuth token (`grant_type=refresh_token`); the old pair stops working |
| Private protocol returns not found or 132 access denied | Token belongs to a user without access; use an OAuth token for the owning user or ask to be added to the workspace |
| 1905 on create | Workspace subscription limit reached |
| Step POST rejected ("loop detected", "multiple first steps", "steps are not forming a complete sequence") | Fix `previous_guid` chaining; when inserting a step, also resend the following step with its new `previous_guid` |
| 255 / 256 / 257 on publish | Already public / missing title / missing author |
| HTTP 429 | Over 100 requests per minute (or 5 PDF requests per minute); back off and cache reads |
| Mac `curl` prints binary output | Add `--compressed` |

## Reference Files

- `references/authentication.md` — token types, OAuth authorization link, token exchange and refresh, MCP connection, limits
- `references/protocols_api.md` — search, get, create, update, steps, materials, publish, bookmarks, PDF, publications, reagents
- `references/discussions.md` — protocol comments, step discussions, run-record comments, direct messages
- `references/workspaces.md` — workspace lists, details, membership, workspace protocols
- `references/file_manager.md` — file-manager search, trash and restore, S3 file uploads
- `references/additional_features.md` — profile, run records, notifications, organization content export

Part of the AlterLab Academic Skills suite.
