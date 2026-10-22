---
name: alterlab-labarchive
description: Writes and validates LabArchives ELN integration code and analyses exported notebooks with no account — reviews labapi/labarchives-py usage, drafts entry HTML and upload plans, and audits a LabArchives notebook export (folder tree or backup) offline for structure and provenance gaps with scripts/analyze_export.py. Reading or writing a live notebook (entries, attachments, backups) and the Protocols.io/Jupyter/REDCap bridges run against the user's own LabArchives account with their keys. Use when automating LabArchives ELN workflows, checking integration code, auditing an exported notebook, programmatically reading/writing entries or attachments, backing up a notebook, or syncing it with Protocols.io, Jupyter, or REDCap. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(curl:*) Bash(python:*) Bash(python3:*)
compatibility: "No API key required to write/review the integration, draft entry content, and audit an exported notebook offline (scripts/analyze_export.py, stdlib-only). Optional: the user's own LabArchives API access (institutional access key ID + password and their LA App authentication token) for live notebook reads/writes via labapi (PyPI, current 1.2.0, Python >=3.10) or the git-only labarchives-py wrapper the bundled scripts use."
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    last_updated: "2026-10-22"
    credentials: "optional: LABARCHIVES_ACCESS_PASSWORD and LA_APP_TOKEN (the institutional access password and the user's LA App authentication token — together they add live reads/writes/backups of the user's own notebooks; the access key ID and user email are identifiers, not secrets); LABARCHIVES_USER_PASSWORD is a deprecated alias for the LA App token"
---

# LabArchives Integration

## Overview

LabArchives is an electronic lab notebook platform for research documentation and data management. Its REST API (XML responses, HMAC-signed requests) exposes notebooks, the page tree, entries, attachments, and backups. The core job here needs no account: write and review the integration, draft entry content, and audit a notebook the user has exported. Only live notebook access uses their credentials.

## Keyless Path (default — no LabArchives account)

1. **Write and review the integration code** against the real clients — `labapi` (maintained; `uv run --with "labapi[dotenv]" python ...`) or the git-only `labarchives-py` the bundled scripts use. Check method names rather than guessing: in labapi 1.2.0 (verified 2026-10-22) a notebook has `.export(dest, source="auto"|"walk"|"backup")` and `.backup(dest, include_attachments=, as_json=)`, entries are created with `page.entries.create(TextEntry, html)` / `create(AttachmentEntry, Attachment.from_file(...))`, and the client reads `API_URL`/`ACCESS_KEYID`/`ACCESS_PWD` from the environment.
2. **Know the signing before you run it.** Requests are signed `sig = b64(HMAC(access_password, akid + method + expires))`, `expires` in epoch-ms. The two clients differ on the hash — `labapi` uses **HMAC-SHA512**, the git `labarchives-py` wrapper uses **HMAC-SHA1** — so the signature must be tested against the tenant, not assumed; match the client to what your institution's API expects.
3. **Audit an exported notebook offline.** `labapi`'s `notebook.export(dest)` writes a folder mirror (`<order>_<name>/` directories holding `NN_text.html`, `NN_text.txt`, `NN_<filename>`). `python3 scripts/analyze_export.py <dir>` walks that tree (or any same-shape export/backup) with no credentials and reports pages, text vs attachment entries, word counts, attachment types, and **provenance gaps** — pages that hold raw-data attachments with no text entry describing them.
4. **Draft entry content and upload plans offline** — the rich-text HTML for `add_entry`, the caption/provenance note for an attachment, the page-tree layout — ready to push once the user supplies credentials.
5. **Hand over the live step.** The bundled scripts (`notebook_operations.py`, `entry_operations.py`) read `config.yaml` and exit non-zero with a clear message if it is absent; they run only against the user's own notebook. Without credentials, stop at the validated code and the offline audit — never invent notebook contents.

## When to Use This Skill

This skill should be used when:
- Working with the LabArchives REST API for notebook automation
- Backing up notebooks programmatically
- Creating text entries or uploading attachments to notebook pages
- Integrating LabArchives with third-party tools (Protocols.io, Jupyter, REDCap)
- Automating data upload to electronic lab notebooks
- Generating institutional (Enterprise) usage reports

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Benchling registry, inventory, ELN entries, or workflow tasks | `alterlab-benchling` |
| Searching, writing, or publishing protocols on protocols.io | `alterlab-protocolsio` |
| Designing REDCap instruments/data dictionaries or CDISC mapping | `alterlab-redcap-cdisc` |
| Choosing a data repository (Zenodo, Dryad, OSF) or FAIR data-sharing plan | `alterlab-open-science` |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-benchling`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

## Core Capabilities

### 1. Clients and Authentication

Two Python clients exist; pick by task:

| Client | Install | Use for |
|--------|---------|---------|
| **labapi** (NIMH DSST; PyPI, current 1.2.0, Python >=3.10) | `uv pip install "labapi[dotenv]"` | Recommended for new work: signing, XML parsing, page-tree navigation, text entries, attachments, backups |
| **labarchives-py** (`labarchivespy` import; git-only) | `uv pip install "git+https://github.com/mcmero/labarchives-py"` | Minimal signed **GET** wrapper (`make_call`); used by the bundled scripts |

**Prerequisites (only for live notebook access; the keyless path above needs none):**
- API access enabled for your institution (Enterprise license); the access key ID and password come from your LabArchives administrator or support@labarchives.com
- The user's email plus the **LA App authentication** token (LabArchives → click your name, top-right → "LA App authentication"). The token is the `password` for `users/user_access_info`, not your login password.

**Regional API endpoints** (labarchives-py `api_url`; labapi's `API_URL` omits the trailing `/api`):
- US/International: `https://api.labarchives.com/api`
- Australia: `https://auapi.labarchives.com/api`
- UK: `https://ukapi.labarchives.com/api`

Create the bundled scripts' `config.yaml` with `python3 scripts/setup_config.py` (prompts for secrets without echoing them and writes the file with mode 600):

```yaml
api_url: https://api.labarchives.com/api  # or regional endpoint
access_key_id: YOUR_ACCESS_KEY_ID
access_password: YOUR_ACCESS_PASSWORD
user_email: researcher@university.edu
user_external_password: YOUR_LA_APP_AUTH_TOKEN
```

Every call is signed: the client appends `akid`, `expires` (ms timestamp), and `sig` = base64 HMAC of `akid + method name + expires` keyed by the access password, so the password itself is never sent. For detailed setup and troubleshooting, see `references/authentication_guide.md`.

### 2. User and Notebook Discovery

`users/user_access_info` returns the user ID (UID) and the notebooks the user can open (`<notebook>` elements with `<id>`, `<name>`, `<is-default>`):

```python
# labapi
import os
from labapi import Client

with Client() as client:  # reads API_URL, ACCESS_KEYID, ACCESS_PWD
    user = client.login(os.environ["LA_EMAIL"], os.environ["LA_APP_TOKEN"])
    print(list(user.notebooks))                       # notebook names
    page = user.notebooks["Lab Notebook"].traverse("Experiments/2026/Run-12")
```

```python
# labarchives-py (signed GET)
import xml.etree.ElementTree as ET
from labarchivespy.client import Client

client = Client(api_url, access_key_id, access_password)
response = client.make_call('users', 'user_access_info',
                            params={'login_or_email': user_email, 'password': auth_token})
root = ET.fromstring(response.content)
uid = root[0].text
notebooks = [(nb.findtext('id'), nb.findtext('name')) for nb in root.iter('notebook')]
```

The labarchives-py wrapper does not URL-encode parameter values, so pass only simple values through `make_call` (or use labapi).

### 3. Notebook Backup

`notebooks/notebook_backup` (params `uid`, `nbid`, optional `json=true`, `no_attachments=true`) returns the notebook as a 7-Zip archive; only the notebook **owner** can download it (error 4547 otherwise).

```bash
# Back up one notebook (credentials come from config.yaml)
python3 scripts/notebook_operations.py backup --nbid NOTEBOOK_ID

# Without attachments, JSON data inside the archive
python3 scripts/notebook_operations.py backup --nbid NOTEBOOK_ID --json --no-attachments

# List notebooks, or back up every notebook you can open
python3 scripts/notebook_operations.py list
python3 scripts/notebook_operations.py backup-all --output backups/
```

With labapi: `user.notebooks["Lab Notebook"].backup("backups/lab_notebook.7z")`.

For the API method reference, see `references/api_reference.md`.

### 4. Entries and Attachments

Entries live on **pages** of the notebook tree, so writes need the notebook ID (`nbid`) and the page tree ID (`pid`):

| Operation | API method | Notes |
|-----------|-----------|-------|
| Create a page or folder | `tree_tools/insert_node` | `parent_tree_id`, `display_text`, `is_folder` |
| Add a text entry | `entries/add_entry` (POST) | form field `entry_data`; `part_type` = `text entry` (HTML), `plain text entry`, or `heading` |
| Add an attachment | `entries/add_attachment` (POST) | raw file bytes as the body; `filename`, `caption`, `change_description` |
| Update a text entry | `entries/update_entry` (POST) | `eid` + `entry_data` |
| List a page's entries | `tree_tools/get_entries_for_page` | |

```python
# labapi: text entry + attachment on a page
from labapi import Attachment, AttachmentEntry, TextEntry

page.entries.create(TextEntry, "<p>Run 12 complete; see attached plate map.</p>")
page.entries.create(AttachmentEntry, Attachment.from_file("plate_map.pdf"))
```

```bash
# Bundled script (labarchives-py signing, POSTs issued by the script)
python3 scripts/entry_operations.py create --nbid NOTEBOOK_ID --pid PAGE_ID --content "Results from today's experiment..."
python3 scripts/entry_operations.py upload --nbid NOTEBOOK_ID --pid PAGE_ID --file /path/to/file.pdf --caption "Raw data"
python3 scripts/entry_operations.py batch-upload --nbid NOTEBOOK_ID --pid PAGE_ID --directory ./experiment_data/
```

Comments are not covered by either client; look up the comment method in the LabArchives API notebook before scripting it. Record provenance (instrument, software version, timestamp) in the attachment caption or a text entry instead. Check the per-file size limit (`users/max_file_size`) before large uploads.

### 5. Site Reports (Enterprise)

LabArchives documents institution-level reports (detailed usage, notebook inventory, PDF/offline generation, members, settings) under a `site_reports` class for Enterprise administrators. The method names in `references/api_reference.md` are unverified here — confirm them in your institution's API documentation before use.

### 6. Third-Party Integrations

LabArchives integrates with Protocols.io, GraphPad Prism (8+), SnapGene, Geneious, Jupyter, REDCap, Qeios, and SciSpace, mostly through in-app export features; newer integrations use OAuth. Programmatic bridges (Jupyter → entry, REDCap export → entry, protocol import) are in `references/integrations.md`.

## Common Workflows

### Complete notebook backup

1. Configure credentials (`scripts/setup_config.py`)
2. `python3 scripts/notebook_operations.py backup-all --output backups/`
3. Verify each archive opens (7-Zip) and store it with its timestamp; repeat on a schedule

### Automated data upload

1. Resolve the target page (`notebook.traverse("Experiments/2026/Run-12")` in labapi, or its tree ID)
2. Upload the data files as attachments
3. Add a text entry describing provenance (instrument, software version, parameters, timestamp)

### Jupyter → LabArchives

1. Export the executed notebook to HTML (nbconvert)
2. Add the HTML as a text entry and the `.ipynb` as an attachment on the experiment page
3. Include environment details (`requirements.txt`/`environment.yml`) as a second attachment

## Best Practices

1. **Credentials:** keep access passwords and app tokens in environment variables or a mode-600 config file, never in code or notebooks
2. **Rate limiting:** add short delays in batch loops and back off on errors; LabArchives does not publish a fixed quota here
3. **Backup verification:** open and spot-check archives after each backup
4. **Regional endpoints:** use the API host of your LabArchives region
5. **Compliance:** ELN records may be regulated (21 CFR Part 11, HIPAA); avoid uploading identifiable patient data unless your notebook is approved for it

## Troubleshooting

- **401 / signature errors:** check the access key ID/password and that the machine clock is correct (signatures expire)
- **4547 on backup:** only the notebook owner can download a backup
- **404 / empty response:** confirm `nbid`/`pid` exist and the user can open the notebook
- **Upload failures:** check `users/max_file_size` and the file type

For additional support, contact LabArchives at support@labarchives.com.

## Resources

### scripts/

- `analyze_export.py`: **keyless** — audit an exported notebook tree (or backup) offline for structure and provenance gaps; no credentials
- `setup_config.py`: interactive configuration file generator (hidden secret prompts, mode 600)
- `notebook_operations.py`: list notebooks and back them up (single or all) — needs `config.yaml`
- `entry_operations.py`: add text entries and upload attachments to a page — needs `config.yaml`

### references/

- `api_reference.md`: API classes, methods, and parameters
- `authentication_guide.md`: authentication setup and configuration
- `integrations.md`: third-party integration setup guides and code

Part of the AlterLab Academic Skills suite.
