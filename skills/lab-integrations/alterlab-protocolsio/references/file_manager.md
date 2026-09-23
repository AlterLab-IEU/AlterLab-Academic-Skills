# File Manager and File Uploads

Source: https://apidoc.protocols.io/ (checked 2026-09-23). Paths are relative to `https://www.protocols.io/api`; every call needs `Authorization: Bearer <token>` and returns a JSON `status_code` (0 = success).

The file manager lists everything a user can reach — protocols, folders, run records, and files — across personal space and workspaces. The current search endpoints are v4; the older v3 folder calls (`/v3/filemanager/folders?top`, `/v3/folders/<guid>/ids`, items-by-ids) are archived.

## Search

| Scope | Call |
|-------|------|
| One folder | `GET /v4/filemanager/folders/<folder_guid>/search` |
| One workspace | `GET /v4/filemanager/workspaces/<workspace_uri>/search` |
| All workspaces | `GET /v4/filemanager/search` (requires `search_key`) |

Shared query parameters:

| Parameter | Notes |
|-----------|-------|
| `search_key` | Search text |
| `content_types[]` | `1` protocols, `10` folders, `11` run records, `15` files (repeat the parameter for several) |
| `protocol_types[]` | `1` protocol, `3` collection, `4` document |
| `modified_after` / `modified_before` | Unix timestamps |
| `sort_by`, `sort_dir` | Sort field and `ASC` / `DESC` |
| `page_id`, `page_size` | Pagination |

Each result has `item_id` (unique across all content types), `content_id` (the protocol, folder, record, or file id), `type_id`, an `access` object (`can_view`, `can_edit`, `can_remove`, `can_publish`, `can_get_doi`, `can_share`, `can_move`, `can_download`, ...), `space` (`id`, `title`), `kind` (for example "Folder", "Private Protocol", "PDF File"), `in_trash`, `size` (bytes), and `created_on`. Protocol items add `uri`, `doi`, `public`, `is_unlisted` (pre-published), `is_doi_reserved`, `reserved_doi`, and version fields; run-record items add `guid`, `protocol_id`, `total_steps`, `finished_steps`, `is_locked`; folder items add `guid`, `parent_guid`, and `has_subfolders`.

```python
import os

import requests

BASE = "https://www.protocols.io/api"
HEADERS = {"Authorization": f"Bearer {os.environ['PROTOCOLS_IO_TOKEN']}"}

params = {"search_key": "qPCR", "content_types[]": [1, 15], "page_size": 50, "page_id": 1}
data = requests.get(f"{BASE}/v4/filemanager/workspaces/my-lab/search",
                    headers=HEADERS, params=params, timeout=60).json()
if data.get("status_code") != 0:
    raise RuntimeError(data.get("status_text") or data.get("error_message"))
for item in data["items"]:
    print(item["type_id"], item["kind"], item.get("title"), item.get("doi") or "")
```

## Trash and restore

| Action | Call | Body |
|--------|------|------|
| Move items to the trash | `PUT /v3/filemanager/trash` | `ids`: list of `item_id` values; returns `deleted` |
| Restore items from the trash | `DELETE /v3/filemanager/trash` | `ids`: list of `item_id` values; returns `restored` |

Note the unusual verbs: `PUT` trashes and `DELETE` restores. Use `item_id` from a search result, not `content_id`.

## Upload a file

Uploads go to Amazon S3 in three steps.

### 1. Prepare — `POST /v3/files`

| Field | Notes |
|-------|-------|
| `filename` (required) | Original file name |
| `original_file_id` | For a thumbnail: the id of the already uploaded original file |
| `width`, `height`, `color` | Image width, height, and average colour (HEX), for images |

The response contains `formData` (`key`, `s3_bucket`, `AWSAccessKeyId`, `Policy`, `Signature`, `ContentType`, `acl`) and `metaData` (`file_id`, `file_type`, `thumb_url`).

### 2. Send the bytes to S3

POST a multipart form to the bucket with the policy fields, followed by the file as the last field. The API reference does not show this request; the sketch below uses the standard S3 POST-policy form, so check it with a small test file first.

```python
path = "plate_reader_export.csv"
prep = requests.post(f"{BASE}/v3/files", headers=HEADERS,
                     data={"filename": os.path.basename(path)}, timeout=60).json()
if prep.get("status_code") != 0:
    raise RuntimeError(prep.get("error_message"))
form, meta = prep["formData"], prep["metaData"]
fields = {
    "key": form["key"],
    "acl": form["acl"],
    "AWSAccessKeyId": form["AWSAccessKeyId"],
    "Policy": form["Policy"],
    "Signature": form["Signature"],
    "Content-Type": form["ContentType"],
}
with open(path, "rb") as fh:
    s3 = requests.post(f"https://{form['s3_bucket']}.s3.amazonaws.com/", data=fields,
                       files={"file": (os.path.basename(path), fh)}, timeout=600)
s3.raise_for_status()
```

### 3. Verify — `PUT /v3/files/<file_id>`

```python
done = requests.put(f"{BASE}/v3/files/{meta['file_id']}", headers=HEADERS, timeout=60).json()
if done.get("status_code") != 0:
    raise RuntimeError(done.get("error_message"))
```

For an image thumbnail, upload the original first, then repeat the three steps for the thumbnail with `original_file_id` set to the original's `file_id`.

### Where the file ends up

The prepare call has no folder, workspace, tag, or description fields. To attach the file to content, add it to a private collection with `PUT /v4/protocols/<collection>` and `collection_items` (`{"content_id": <file_id>, "content_type_id": 15}`), or place and describe it in the web app.

## Good practice

- Keep raw data in a data repository or your ELN and link it from the protocol; protocols.io is best for the method, small supporting files, and figures.
- Search before uploading to avoid duplicates, and use descriptive file names (date, instrument, sample set).
- Always make the verify call and check its `status_code`; the API documents prepare and verify as the calls that begin and finish an upload.
- Do not upload identifiable human-subject data to shared or public spaces.
