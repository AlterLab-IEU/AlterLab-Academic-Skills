# Profile, Run Records, Notifications, and Organization Export

Source: https://apidoc.protocols.io/ (checked 2026-09-23). Paths are relative to `https://www.protocols.io/api`; every call needs `Authorization: Bearer <token>` and returns a JSON `status_code` (0 = success). Publication feeds (`GET /v3/publications`) and reagent search are in `protocols_api.md`.

## Profile

| Action | Call | Fields |
|--------|------|--------|
| Read your profile | `GET /v3/session/profile` | Returns an extended `user` object |
| Update your profile | `PUT /v3/session/profile` | Optional `first_name`, `last_name`, `email`, `bio`, `image` (URL), `affiliation`, `link`; `password` needs `old_password` |

Errors: `123` email already in use, `124` invalid email. Profile updates change what co-authors and readers see, so confirm with the user before sending them.

## Run records (experiment runs)

A run record is a copy of a protocol that tracks one execution: steps are checked off or skipped, and notes are attached to the record or to individual steps.

| Action | Call | Notes |
|--------|------|-------|
| List active records | `GET /v3/records?active` | Records with unfinished steps; add `archived` for archived ones; `page_size`, `page_id` |
| Get a record | `GET /v4/records/<record_guid>` | `with_protocol=1` adds the protocol; `content_format=json|html|markdown`; response is `{"payload": {"record": ..., "protocol": ...}}` |
| Create a record | `POST /v3/records` | `protocol_uri` (required); optional `folder_data` (`{"guid": "<folder guid>"}`, default: the user's private folder in the active workspace) and an initial `stack` |
| Save changes | `PUT /v3/records/<record_guid>` | `stack` (required): list of change objects |

`stack` change objects:

| `type` | `data` | Effect |
|--------|--------|--------|
| `base` | `{"title": "..."}` | Rename the record |
| `notes` | `{"id": null, "note": "...", "step_id": 0}` | Add a note (`step_id` 0 = whole record, or a step id); pass an existing note `id` to change it |
| `step` | `{"guid": "<record step guid>", "is_checked": 1}` or `"is_skipped": 1` | Check off or skip a step |

After creating a record, fetch it with the get call before sending changes; the API asks clients to work from the stored record to avoid step collisions. The docs show `stack` as a form field without spelling out its encoding; a JSON-encoded array is the likely form, so try it on a scratch record first.

```python
import json
import os

import requests

BASE = "https://www.protocols.io/api"
HEADERS = {"Authorization": f"Bearer {os.environ['PROTOCOLS_IO_TOKEN']}"}


def ok(resp):
    data = resp.json()
    if data.get("status_code") != 0:
        raise RuntimeError(data.get("error_message") or data.get("status_text"))
    return data


created = ok(requests.post(f"{BASE}/v3/records", headers=HEADERS,
                           data={"protocol_uri": "my-protocol-uri"}, timeout=60))
guid = created["record"]["guid"]
record = ok(requests.get(f"{BASE}/v4/records/{guid}", headers=HEADERS,
                         params={"with_protocol": 1, "content_format": "markdown"}, timeout=60))
stack = [
    {"type": "base", "data": {"title": "Run 2026-09-23, lot A12"}},
    {"type": "notes", "data": {"id": None, "note": "Incubation extended to 45 min.", "step_id": 0}},
]
ok(requests.put(f"{BASE}/v3/records/{guid}", headers=HEADERS,
                data={"stack": json.dumps(stack)}, timeout=60))
```

Run records hold the procedure trail; keep the resulting data in your ELN or a repository and cite the record or protocol version there.

Record comments and record-step discussions are in `discussions.md`.

## Notifications

`GET /v3/researchers/notifications` with `page_size` (1–100) and `page_id` returns `list` (notification objects with `id`, `type_id`, `name`, `pattern` such as "You joined @group", `created_on`, and the related `objects`) plus `pagination`. The API documents no call to mark notifications read.

## Organization content export

Organization accounts can export all of an organization's content as one archive. The host is the organization's subdomain.

| Action | Call |
|--------|------|
| Start an export | `POST https://<subdomain>.protocols.io/api/v4/organizations/<organization_uri>/content/exports` (optional `timezone`, e.g. `America/New_York`; default UTC) |
| Check progress | `GET https://<subdomain>.protocols.io/api/v4/organizations/<organization_uri>/content/exports/<guid>` |

Both return an `export` object: `guid`, `created_on`, `total_files`, `total_processed_files`, `is_finished`, and `download_link` (null until finished). Download the archive with a `GET` on `download_link` using the same `Authorization` header. Errors: `1` server error, `2` not authorized, `3` incorrect or missing parameters.

```python
import time

org_base = "https://mylab.protocols.io/api/v4/organizations/my-org/content/exports"
export = ok(requests.post(org_base, headers=HEADERS, data={"timezone": "UTC"}, timeout=60))["export"]
while not export["is_finished"]:
    time.sleep(30)  # stay well under the 100 requests/minute limit
    export = ok(requests.get(f"{org_base}/{export['guid']}", headers=HEADERS, timeout=60))["export"]
with requests.get(export["download_link"], headers=HEADERS, stream=True, timeout=600) as r:
    r.raise_for_status()
    with open("protocols_io_export", "wb") as fh:  # format undocumented; check it with `file`
        for chunk in r.iter_content(chunk_size=1 << 20):
            fh.write(chunk)
```

The archive format is not documented, so inspect the download before renaming or unpacking it. Store exports with their date, and repeat them on a schedule if protocols.io is part of your records-retention plan.
