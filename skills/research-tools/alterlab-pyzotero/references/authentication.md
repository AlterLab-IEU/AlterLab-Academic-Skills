# Authentication & Setup

## Credentials

Obtain from https://www.zotero.org/settings/keys:

| Credential | Where to Find |
|-----------|---------------|
| **User ID** | "Your userID for use in API calls" section |
| **API Key** | Create new key at /settings/keys/new |
| **Group Library ID** | Integer after `/groups/` in group URL (e.g. `https://www.zotero.org/groups/169947`) |

## Environment Variables

Store in `.env` or export in shell:
```
ZOTERO_LIBRARY_ID=436
ZOTERO_API_KEY=ABC1234XYZ
ZOTERO_LIBRARY_TYPE=user
```

Load in Python:
```python
import os
from dotenv import load_dotenv
from pyzotero import Zotero

load_dotenv()

zot = Zotero(
    library_id=os.environ['ZOTERO_LIBRARY_ID'],
    library_type=os.environ['ZOTERO_LIBRARY_TYPE'],
    api_key=os.environ['ZOTERO_API_KEY']
)
```

## Library Types

```python
# Personal library
zot = Zotero('436', 'user', 'ABC1234XYZ')

# Group library
zot = Zotero('169947', 'group', 'ABC1234XYZ')
```

**Important**: A `Zotero` instance is bound to a single library. To access multiple libraries, create multiple instances.

## Local Mode

Connect to the running Zotero desktop app instead of the web API (Zotero 7+, with "Allow other applications on this computer to communicate with Zotero" enabled under Settings > Advanced). Reads need no API key:

```python
zot = Zotero(library_id='0', library_type='user', local=True)
items = zot.items(limit=10)  # reads from local Zotero
```

Local **writes** (pyzotero ≥ 1.15) need Zotero 10 or later and a local API key granted by the user in Zotero:

```python
zot = Zotero('0', 'user', local=True)
auth = zot.authorize_local("My Application")  # Zotero shows Allow / Always Allow / Deny
zot.create_items([template])
```

- "Allow" gives a single-use key: the first successful write consumes it and the next write raises `LocalAPIKeyRequiredError`.
- "Always Allow" gives a persistent key; store it and pass it back later as `Zotero('0', 'user', local=True, local_api_key=key)`.
- A denied dialog raises `LocalAPIDeniedError`; the authorize endpoint is rate-limited, so do not call it in a retry loop.
- Keys and object versions are scoped to one Zotero instance (`zot.server_id`); local API keys are unrelated to zotero.org API keys.
- The CLI equivalent is `pyzotero authorize`, which stores the key for the CLI write commands and the MCP server.

## Optional Parameters

```python
zot = Zotero(
    library_id='436',
    library_type='user',
    api_key='ABC1234XYZ',
    locale='en-US',             # localise field names (e.g. 'fr-FR' for French)
)
# preserve_json_order is deprecated (dicts keep insertion order); omit it.
```

## Key Permissions

Check what the current API key can access:
```python
info = zot.key_info()
# Returns dict with user info and group access permissions
```

Check accessible groups:
```python
groups = zot.groups()
# Returns list of group libraries accessible to the current key
```

## API Key Scopes

When creating an API key at https://www.zotero.org/settings/keys/new, choose appropriate permissions:
- **Read Only**: For retrieving items and collections
- **Write Access**: For creating, updating, and deleting items
- **Notes Access**: To include notes in read/write operations
- **Files Access**: Required for uploading attachments
