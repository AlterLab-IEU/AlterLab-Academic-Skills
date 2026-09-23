# Discussions, Comments, and Messages

Source: https://apidoc.protocols.io/ (checked 2026-09-23). Paths are relative to `https://www.protocols.io/api`; every call needs `Authorization: Bearer <token>` and returns a JSON `status_code` (0 = success).

## How discussions are modelled

- **Protocol comments** belong to the protocol as a whole.
- **Step discussions** hang off one step; each discussion has a first comment and threaded replies.
- A comment object carries `comment_id`, `discussion_id`, `parent_id` (0 for top level), `step_id` (0 for protocol-level comments), `body`, `creator`, `created_on`/`changed_on` (Unix time), `comments` (replies), `can_edit`, `can_delete`, and `is_private`.
- `body` is returned as a Draft.js JSON string. Parse it and join the `text` of its `blocks` to get plain text.

## Protocol comments

| Action | Call | Body fields |
|--------|------|-------------|
| List comments | `GET /v3/protocols/<protocol_uri>/comments` | — (returns `comments`) |
| Add a comment | `POST /v3/protocols/<protocol_uri>/comments` | `body` (required), `is_private` (optional, 1 = private) |
| Reply to a comment | `POST /v3/protocols/<protocol_uri>/comments/<parent_comment_id>` | `body` |

## Step discussions

| Action | Call | Body fields |
|--------|------|-------------|
| Start a discussion on a step | `POST /v3/steps/<step_id>/discussions` | `body`, `protocol_uri` (both required), `is_private` |
| Comment in a discussion | `POST /v3/steps/<step_id>/discussions/<discussion_id>/comments` | `body`, `protocol_uri` |
| Reply to a step comment | `POST /v3/steps/<step_id>/discussions/<discussion_id>/comments/<parent_id>` | `body`, `protocol_uri` |

Use the integer step `id` from `GET /v4/protocols/<id>/steps`. Comment objects carry `step_id` (0 for protocol-level comments, the step's id for step-level ones); use it to tell the two apart in listings.

## Edit and delete

| Action | Call | Notes |
|--------|------|-------|
| Edit a comment | `PUT /v3/discussions/comments/<comment_id>` | `body` required; error 5 if empty |
| Edit a discussion | `PUT /v3/discussions/<discussion_id>` | `body` required |
| Delete a comment | `DELETE /v3/discussions/comments/<comment_id>` | |
| Delete a discussion | `DELETE /v3/discussions/<discussion_id>` | |

Only comments the token's user may edit or delete (see `can_edit` / `can_delete`) can be changed.

## Run-record comments

| Action | Call | Body fields |
|--------|------|-------------|
| List record comments | `GET /v3/records/<record_guid>/comments` | — |
| Add a record comment | `POST /v3/records/<record_guid>/comments` | `body`, `is_private` |
| Start a discussion on a record step | `POST /v3/records/steps/<step_id>/discussions` | `body`, `record_guid` |
| Reply in a record step discussion | `POST /v3/records/steps/<step_id>/discussions/<discussion_id>/comments` | `body`, `record_guid` |

The reference lists the protocol-comment reply path (`POST /v3/protocols/<protocol_uri>/comments/<parent_comment_id>`) for replies to record comments; test it on a scratch record before relying on it.

## Direct messages

| Action | Call | Notes |
|--------|------|-------|
| List conversations | `GET /v3/conversations` | `page_id`, `page_size`, `key` |
| Check for new messages | `GET /v3/conversations?new` | Returns `total` and conversation `guids` |
| Read a conversation | `GET /v3/conversations/<conversation_guid>/messages` | |
| Mark a message read | `PUT /v3/conversations/messages/<message_guid>` | |
| Send a message | `POST /v3/conversations/<conversation_guid>/messages` | `guid` (new message GUID), `subject`, `body`, `username` (recipient); omit the conversation GUID to start a new conversation |
| Delete a conversation | `DELETE /v3/conversations/<conversation_guid>` | |

## Example: summarise open questions on a protocol

```python
import json
import os

import requests

BASE = "https://www.protocols.io/api"
HEADERS = {"Authorization": f"Bearer {os.environ['PROTOCOLS_IO_TOKEN']}"}


def plain_text(body):
    """Comment bodies are Draft.js JSON strings; fall back to the raw value."""
    try:
        return " ".join(block["text"] for block in json.loads(body)["blocks"])
    except (TypeError, ValueError, KeyError):
        return body or ""


def walk(comments, depth=0):
    for c in comments or []:
        where = f"step {c['step_id']}" if c.get("step_id") else "protocol"
        yield depth, where, c["creator"]["name"], plain_text(c["body"])
        yield from walk(c.get("comments"), depth + 1)


data = requests.get(f"{BASE}/v3/protocols/my-protocol-uri/comments", headers=HEADERS, timeout=60).json()
if data.get("status_code") != 0:
    raise RuntimeError(data.get("error_message"))
for depth, where, author, text in walk(data["comments"]):
    print("  " * depth + f"[{where}] {author}: {text[:120]}")
```

## Good practice

- Reply in the existing thread (reply endpoints) instead of starting new top-level comments, so authors see the context.
- Keep troubleshooting reports specific: reagent lot, instrument, deviation from the step, and outcome.
- Use `is_private=1` for notes meant only for collaborators; public comments are visible to every reader of a public protocol.
- Poll comments sparingly (well under 100 requests per minute) or rely on notifications (`GET /v3/researchers/notifications`).
