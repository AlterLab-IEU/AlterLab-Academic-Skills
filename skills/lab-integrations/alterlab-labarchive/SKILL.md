---
name: alterlab-labarchive
description: Integrates the LabArchives electronic lab notebook (ELN) via its REST API — access notebooks, manage entries and attachments, back up notebooks, and bridge to Protocols.io, Jupyter, and REDCap. Use when automating LabArchives ELN workflows, programmatically reading/writing notebook entries or attachments, backing up a LabArchives notebook, or syncing it with Protocols.io, Jupyter, or REDCap. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(curl:*) Bash(python:*)
compatibility: Requires a LabArchives account with API access (institutional access key ID + password, plus the user's LA App authentication token). Python clients - labapi (PyPI, current 1.2.0, Python >=3.10) or the git-only labarchives-py wrapper used by the bundled scripts.
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# LabArchives Integration

## Overview

LabArchives is an electronic lab notebook platform for research documentation and data management. Its REST API (XML responses, HMAC-signed requests) exposes notebooks, the page tree, entries, attachments, and backups.

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

## Core Capabilities

### 1. Clients and Authentication

Two Python clients exist; pick by task:

| Client | Install | Use for |
|--------|---------|---------|
| **labapi** (NIMH DSST; PyPI, current 1.2.0, Python >=3.10) | `uv pip install "labapi[dotenv]"` | Recommended for new work: signing, XML parsing, page-tree navigation, text entries, attachments, backups |
| **labarchives-py** (`labarchivespy` import; git-only) | `uv pip install "git+https://github.com/mcmero/labarchives-py"` | Minimal signed **GET** wrapper (`make_call`); used by the bundled scripts |

**Prerequisites:**
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

- `setup_config.py`: interactive configuration file generator (hidden secret prompts, mode 600)
- `notebook_operations.py`: list notebooks and back them up (single or all)
- `entry_operations.py`: add text entries and upload attachments to a page

### references/

- `api_reference.md`: API classes, methods, and parameters
- `authentication_guide.md`: authentication setup and configuration
- `integrations.md`: third-party integration setup guides and code

Part of the AlterLab Academic Skills suite.
