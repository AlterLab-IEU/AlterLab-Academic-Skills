# LabArchives API Reference

> **Verification status (2026-09-23).** Method names below marked **verified** are used by a maintained client — `labapi` 1.2.0 (NIMH DSST, PyPI) or `labarchives-py` — against the live API: `users/user_access_info`, `users/user_info_via_id`, `users/max_file_size`, `utilities/institutional_login_urls`, `notebooks/notebook_backup`, `notebooks/create_notebook`, `notebooks/modify_notebook_info`, `tree_tools/get_tree_level`, `tree_tools/insert_node`, `tree_tools/update_node`, `tree_tools/get_entries_for_page`, `entries/add_entry`, `entries/add_attachment`, `entries/update_entry`, `entries/update_attachment`, `entries/entry_attachment`. The `site_reports/*` names are **unverified** — confirm them in your institution's LabArchives API documentation (linked from the LabArchives notebook share page) before relying on them.

## API Structure

All LabArchives API calls follow this URL pattern:

```
https://<base_url>/api/<api_class>/<api_method>?<authentication_parameters>&<method_parameters>
```

## Regional API Endpoints

| Region | Base URL |
|--------|----------|
| US/International | `https://api.labarchives.com/api` |
| Australia | `https://auapi.labarchives.com/api` |
| UK | `https://ukapi.labarchives.com/api` |

## Authentication

Every call carries three signed query parameters instead of the password:

- `akid`: the access key ID provided by your LabArchives administrator
- `expires`: expiry timestamp in milliseconds
- `sig`: base64-encoded HMAC of `akid + <method name> + expires`, keyed by the access password (labarchives-py uses HMAC-SHA1, labapi HMAC-SHA512), URL-encoded

User-scoped methods also take `uid` (from `users/user_access_info`).

## API Classes and Methods

### Users API Class

#### `users/user_access_info`

Retrieve user ID and notebook access information.

**Parameters:**
- `login_or_email` (required): User's email address or login username
- `password` (required): User's "LA App authentication" token (not the regular login password)

**Returns:** XML containing the user ID (first child `<id>`) and one `<notebook>` element per accessible notebook with `<id>`, `<name>`, and `<is-default>`.

**Example:**
```python
params = {
    'login_or_email': 'researcher@university.edu',
    'password': 'external_app_password'
}
response = client.make_call('users', 'user_access_info', params=params)
```

#### `users/user_info_via_id`

Retrieve detailed user information by user ID.

**Parameters:**
- `uid` (required): User ID obtained from user_access_info

**Returns:** User profile information including:
- Name and email
- Account creation date
- Institution affiliation
- Role and permissions
- Storage quota and usage

**Example:**
```python
params = {'uid': '12345'}
response = client.make_call('users', 'user_info_via_id', params=params)
```

### Notebooks API Class

#### `notebooks/notebook_backup`

Download complete notebook data including entries, attachments, and metadata.

**Parameters:**
- `uid` (required): User ID
- `nbid` (required): Notebook ID
- `json` (optional, default: false): Return data in JSON format instead of XML
- `no_attachments` (optional, default: false): Exclude attachments from backup

**Returns:** a 7-Zip archive of the notebook (entry data as XML, or JSON with `json=true`; attachment payloads omitted with `no_attachments=true`). Only the notebook owner can download a backup — other users get error 4547.

**File format:**
The returned archive includes:
- Entry text content in HTML format
- File attachments in original formats
- Metadata XML files with timestamps, authors, and version history
- Comment threads and annotations

**Example:**
```python
# Full backup with attachments
params = {
    'uid': '12345',
    'nbid': '67890',
    'json': 'false',
    'no_attachments': 'false'
}
response = client.make_call('notebooks', 'notebook_backup', params=params)

# Write to file
with open('notebook_backup.7z', 'wb') as f:
    f.write(response.content)
```

```python
# Lighter backup: JSON data, no attachment payloads (still a 7z archive)
params = {
    'uid': '12345',
    'nbid': '67890',
    'json': 'true',
    'no_attachments': 'true'
}
response = client.make_call('notebooks', 'notebook_backup', params=params)
with open('notebook_67890_data.7z', 'wb') as f:
    f.write(response.content)
```

#### Listing notebooks

There is no separate verified list method — `users/user_access_info` already returns every notebook the user can open (see above).

### Tree Tools API Class

Notebooks are trees of folders and pages; entries live on pages.

#### `tree_tools/get_tree_level`

List the children of a tree node. **Parameters:** `uid`, `nbid`, `parent_tree_id` (`0` for the notebook root).

#### `tree_tools/insert_node`

Create a page or folder. **Parameters:** `uid`, `nbid`, `parent_tree_id`, `display_text`, `is_folder` (`true`/`false`). **Returns:** `<node><tree-id>` of the new node — the page ID (`pid`) used by entry methods.

#### `tree_tools/get_entries_for_page`

List a page's entries. **Parameters:** `uid`, `nbid`, `page_tree_id`.

### Entries API Class

#### `entries/add_entry` (POST)

Add a text entry to a page.

**Query parameters:** `uid`, `nbid`, `pid` (page tree ID), `part_type` — `text entry` (rich HTML), `plain text entry`, or `heading`
**POST body (form):** `entry_data` — the entry content
**Returns:** `<entry><eid>` of the new entry

#### `entries/update_entry` (POST)

Replace a text entry's content. **Query parameters:** `uid`, `eid`. **POST body (form):** `entry_data`.

#### `entries/add_attachment` (POST)

Upload a file as a new attachment entry on a page.

**Query parameters:** `uid`, `nbid`, `pid`, `filename`, `caption`, `change_description` (optional `client_ip`)
**POST body:** the raw file bytes (not multipart form data)
**Returns:** `<entry><eid>` of the new attachment entry

```python
import requests
from urllib.parse import urlencode

expires = client.get_expires_time()                 # labarchives-py signing helpers
sig = client.get_signature('add_attachment', expires)
query = urlencode({'uid': uid, 'nbid': nbid, 'pid': pid, 'filename': 'data.csv',
                   'caption': 'Plate reader export', 'change_description': 'Uploaded via API'})
url = f"{api_url}/entries/add_attachment?{query}&akid={access_key_id}&expires={expires}&sig={sig}"
with open('data.csv', 'rb') as f:
    response = requests.post(url, data=f.read(), timeout=120)
```

`scripts/entry_operations.py` wraps these calls (`create`, `upload`, `batch-upload`). Use `users/max_file_size` to check the upload limit first.

#### Comments

Neither client implements entry comments; find the comment method in the LabArchives API documentation before scripting it.

### Site Reports API Class

Enterprise-only features for institutional reporting and analytics.

#### `site_reports/detailed_usage_report`

Generate comprehensive usage statistics for the institution.

**Parameters:**
- `start_date` (required): Report start date (YYYY-MM-DD)
- `end_date` (required): Report end date (YYYY-MM-DD)
- `format` (optional): Output format (csv, json, xml)

**Returns:** Usage metrics including:
- User login frequency
- Entry creation counts
- Storage utilization
- Collaboration statistics
- Time-based activity patterns

#### `site_reports/detailed_notebook_report`

Generate detailed report on all notebooks in the institution.

**Parameters:**
- `include_settings` (optional, default: false): Include notebook settings
- `include_members` (optional, default: false): Include member lists

**Returns:** Notebook inventory with:
- Notebook names and IDs
- Owner information
- Creation and last modified dates
- Member count and access levels
- Storage size
- Settings (if requested)

#### `site_reports/pdf_offline_generation_report`

Track PDF exports for compliance and auditing purposes.

**Parameters:**
- `start_date` (required): Report start date
- `end_date` (required): Report end date

**Returns:** Export activity log with:
- User who generated PDF
- Notebook and entry exported
- Export timestamp
- IP address

### Utilities API Class

#### `utilities/institutional_login_urls`

Retrieve institutional login URLs for SSO integration.

**Parameters:** None required (uses access key authentication)

**Returns:** List of institutional login endpoints

## Response Formats

### XML Response Example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<users>
    <id>12345</id>
    ...
    <notebooks>
        <notebook>
            <id>67890</id>
            <name>Lab Notebook 2026</name>
            <is-default>true</is-default>
        </notebook>
    </notebooks>
</users>
```
(Abbreviated `users/user_access_info` response: the user ID is the first child element, and notebook IDs are in `<notebook><id>`. The root element name may differ; parse by child tags.)

Responses are XML; JSON appears only inside notebook backups requested with `json=true`.

## Error Codes

Failed calls return an XML body with `<error-code>` and `<error-description>` (ELN-specific codes). Codes seen by the `labapi` client include 4506, 4514, 4520, and 4533 (authentication/credential problems) and 4547 (notebook backup requested by a non-owner). The HTTP status gives the broad class:

| HTTP | Message | Meaning | Solution |
|------|---------|---------|----------|
| 401 | Unauthorized | Invalid credentials or expired signature | Verify the access key ID/password and the machine clock |
| 403 | Forbidden | Insufficient permissions | Check user role and notebook access |
| 404 | Not Found | Resource doesn't exist | Verify uid, nbid, pid, or eid are correct |
| 429 | Too Many Requests | Rate limit exceeded | Implement exponential backoff |
| 500 | Internal Server Error | Server-side issue | Retry request or contact support |

## Rate Limiting

LabArchives may throttle high request volumes (HTTP 429). Exact published limits are not documented here — do not assume a specific number. Practical guidance:

- **Be conservative:** add a short delay (e.g. 1-2 s) between requests in batch loops.
- **Back off on 429:** retry with exponential backoff rather than hammering the endpoint.
- Confirm any institution-specific quota with your LabArchives administrator.

## API Versioning

LabArchives API is backward compatible. New methods are added without breaking existing implementations. Monitor LabArchives announcements for new capabilities.

## Support and Documentation

For API access requests, technical questions, or feature requests:
- Email: support@labarchives.com
- Include your institution name and specific use case for faster assistance
