# Workspaces

Source: https://apidoc.protocols.io/ (checked 2026-09-23). Paths are relative to `https://www.protocols.io/api`; every call needs `Authorization: Bearer <token>` and returns a JSON `status_code` (0 = success).

Workspaces are addressed by their string `uri` (for example `verve-net`), not by the integer `id`.

## Find workspaces

### `GET /v3/workspaces`

| Parameter | Notes |
|-----------|-------|
| `filter` | `all_public` (default; also used for unrecognised values), `my_groups` (workspaces the user is a confirmed member of, including private ones), `user_public` (public workspaces the user belongs to), `all_public_request` (public workspaces the user has not joined yet) |
| `key` | Searches workspace name and description |
| `page_size` / `page_id` | 1–100 (default 10) / from 1 |

Use `filter=my_groups` to find the `uri` of a private workspace; the file-manager search endpoint takes that `uri`.

### `GET /v3/researchers/<username>/workspaces`

A researcher's workspaces; optional `key`, `page_size`, `page_id`.

### `GET /v3/workspaces/<uri>`

Returns a `workspace` object:

| Field | Meaning |
|-------|---------|
| `id`, `uri`, `title`, `description`, `research_interests`, `website`, `location`, `affiliation`, `image` | Profile |
| `status.is_visible` | `true` for a public workspace |
| `status.access_level` | `0` anyone can join, `1` users request to join, `2` invitation only |
| `stats.files` | Counts of `publish`, `forks`, `shared`, `archived` items; `stats.total_members` |
| `user_status` | The token user's `is_member`, `is_confimed` (sic), `is_invited`, `is_owner` flags |

## Membership

| Action | Call |
|--------|------|
| Request to join (or join an open workspace) | `POST /v3/workspaces/<uri>/members` |
| Accept an invitation | `PUT /v3/workspaces/<uri>/members` |
| Decline an invitation or leave | `DELETE /v3/workspaces/<uri>/members` |

Each returns `user_status` with the user's new membership state. Adding or removing other members and changing roles are done in the web app; the API documents no endpoints for them.

## Workspace content

- **Protocols:** `GET /v3/workspaces/<uri>/protocols` with optional `key`, `order_field` (`activity`, `date`, `name`, `id`), `order_dir`, `page_size`, `page_id`. Error `132` means access denied.
- **Protocols, folders, run records, and files together:** `GET /v4/filemanager/workspaces/<uri>/search` (see `file_manager.md`).
- **New protocols:** the create call (`POST /v3/protocols/<guid>`) takes no workspace parameter; move or share the new protocol into the workspace from the web app. Error `1905` on create means the workspace's subscription limit is reached.
- **Organization-wide export:** organization accounts can export all content with `POST https://<subdomain>.protocols.io/api/v4/organizations/<organization_uri>/content/exports` (see `additional_features.md`).

## Example: list my workspaces and their protocol counts

```python
import os

import requests

BASE = "https://www.protocols.io/api"
HEADERS = {"Authorization": f"Bearer {os.environ['PROTOCOLS_IO_TOKEN']}"}


def get(path, **params):
    data = requests.get(f"{BASE}{path}", headers=HEADERS, params=params, timeout=60).json()
    if data.get("status_code") != 0:
        raise RuntimeError(f"{data.get('status_code')}: {data.get('error_message')}")
    return data


page = 1
while True:
    data = get("/v3/workspaces", filter="my_groups", page_size=100, page_id=page)
    for ws in data["items"]:
        protocols = get(f"/v3/workspaces/{ws['uri']}/protocols", page_size=1)
        print(ws["uri"], ws["title"], protocols.get("pagination", {}).get("total_results"))
    if not data.get("pagination", {}).get("next_page"):
        break
    page += 1
```

The pagination object carries `current_page`, `total_pages`, `total_results`, `next_page` (a URL or null), `prev_page`, and `page_size`.

## Good practice

- Keep lab protocols in a workspace rather than personal accounts so they survive staff turnover.
- Agree on naming (method, organism, version) and on who publishes, since a published version with a DOI cannot be edited.
- Use private workspaces for unpublished methods and check institutional rules before sharing controlled or proprietary procedures.
