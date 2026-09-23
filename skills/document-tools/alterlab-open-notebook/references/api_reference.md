# Open Notebook API Reference

## Base URL

```
http://localhost:5055/api
```

Interactive API documentation is available at `http://localhost:5055/docs` (Swagger UI) and `http://localhost:5055/redoc` (ReDoc).

Request/response shapes here were checked against the Open Notebook 1.x source (v1.14, 2026-09). The Swagger UI at `/docs` is authoritative for your running version.

## Authentication

If `OPEN_NOTEBOOK_PASSWORD` is configured, send it as a bearer token on every request: `Authorization: Bearer <password>` (Docker secrets are supported via `OPEN_NOTEBOOK_PASSWORD_FILE`). The following routes are excluded from authentication: `/`, `/health`, `/docs`, `/openapi.json`, `/redoc`, `/api/auth/status`, `/api/config`.

---

## Notebooks

### List Notebooks

```
GET /api/notebooks
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `archived` | boolean | Filter by archived status |
| `order_by` | string | Field and direction, e.g. `"updated desc"` (default), `"name asc"`; fields: `name`, `created`, `updated` |

**Response:** Array of notebook objects with `source_count` and `note_count`.

### Create Notebook

```
POST /api/notebooks
```

**Request Body:**
```json
{
  "name": "My Research",
  "description": "Optional description"
}
```

### Get Notebook

```
GET /api/notebooks/{notebook_id}
```

### Update Notebook

```
PUT /api/notebooks/{notebook_id}
```

**Request Body:**
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "archived": false
}
```

### Delete Notebook

```
DELETE /api/notebooks/{notebook_id}
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `delete_exclusive_sources` | boolean | Also delete sources that belong only to this notebook (default: false) |

### Delete Preview

```
GET /api/notebooks/{notebook_id}/delete-preview
```

Returns `notebook_id`, `notebook_name`, `note_count`, `exclusive_source_count`, and `shared_source_count`.

### Link Source to Notebook

```
POST /api/notebooks/{notebook_id}/sources/{source_id}
```

Idempotent operation to associate a source with a notebook.

### Unlink Source from Notebook

```
DELETE /api/notebooks/{notebook_id}/sources/{source_id}
```

---

## Sources

### List Sources

```
GET /api/sources
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `notebook_id` | string | Filter by notebook |
| `limit` | integer | Number of results (1-100, default 50) |
| `offset` | integer | Pagination offset |
| `sort_by` | string | `type`, `title`, `created`, `updated` (default), `insights_count`, or `embedded` |
| `sort_order` | string | `asc` or `desc` (default) |

### Create Source

```
POST /api/sources
```

Accepts multipart form data (use `POST /api/sources/json` for a JSON body with the same fields).

**Form Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | **Required.** `link`, `upload`, or `text` |
| `file` | file | File for `type=upload` (PDF, DOCX, audio, video, ...) |
| `url` | string | Web URL for `type=link` |
| `content` | string | Raw text for `type=text` |
| `title` | string | Optional source title |
| `notebook_id` | string | Associate with one notebook (or `notebooks`: JSON array string of IDs; not both) |
| `transformations` | string | JSON array string of transformation IDs to apply |
| `embed` | `"true"`/`"false"` | Embed for vector search (default `"false"`) |
| `async_processing` | `"true"`/`"false"` | Return immediately and process in the background (default `"false"`) |
| `delete_source` | `"true"`/`"false"` | Delete the uploaded file after processing (default `"false"`) |

The response contains the source `id` (and a `command_id` when processed asynchronously).

### Create Source (JSON)

```
POST /api/sources/json
```

JSON-body variant of source creation (same fields as the form; `notebooks` and `transformations` are real arrays).

### Get Source

```
GET /api/sources/{source_id}
```

### Get Source Status

```
GET /api/sources/{source_id}/status
```

Poll processing status for asynchronously ingested sources: `status` is `queued`, `running`, `completed`, `failed`, or `unknown` (`null` for legacy sources processed before async support), plus a human-readable `message`.

### Update Source

```
PUT /api/sources/{source_id}
```

**Request Body:**
```json
{
  "title": "Updated Title",
  "topics": ["topic one", "topic two"]
}
```

### Delete Source

```
DELETE /api/sources/{source_id}
```

### Download Source File

```
GET /api/sources/{source_id}/download
```

Returns the original uploaded file.

### Check Source File

```
HEAD /api/sources/{source_id}/download
```

### Retry Failed Source

```
POST /api/sources/{source_id}/retry
```

Requeue a failed source for processing.

### Get Source Insights

```
GET /api/sources/{source_id}/insights
```

Retrieve AI-generated insights for a source.

---

## Notes

### List Notes

```
GET /api/notes
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `notebook_id` | string | Filter by notebook |

### Create Note

```
POST /api/notes
```

**Request Body:**
```json
{
  "title": "My Note",
  "content": "Note content...",
  "note_type": "human",
  "notebook_id": "notebook:abc123"
}
```

`note_type` must be `"human"` or `"ai"`. AI notes without titles get auto-generated titles.

### Get Note

```
GET /api/notes/{note_id}
```

### Update Note

```
PUT /api/notes/{note_id}
```

**Request Body:**
```json
{
  "title": "Updated Title",
  "content": "Updated content",
  "note_type": "human"
}
```

### Delete Note

```
DELETE /api/notes/{note_id}
```

---

## Chat

### List Sessions

```
GET /api/chat/sessions
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `notebook_id` | string | Filter by notebook |

### Create Session

```
POST /api/chat/sessions
```

**Request Body:**
```json
{
  "notebook_id": "notebook:abc123",
  "title": "Discussion Topic",
  "model_override": "optional_model_id"
}
```

### Get Session

```
GET /api/chat/sessions/{session_id}
```

Returns session details with message history.

### Update Session

```
PUT /api/chat/sessions/{session_id}
```

### Delete Session

```
DELETE /api/chat/sessions/{session_id}
```

### Execute Chat

```
POST /api/chat/execute
```

**Request Body:**
```json
{
  "session_id": "chat_session:abc123",
  "message": "Your question here",
  "context": {"sources": ["..."], "notes": ["..."]},
  "model_override": "optional_model_id"
}
```

`context` is the `context` object returned by **Build Context** below; the model only sees what you put there. The response is `{"session_id": ..., "messages": [{"id", "type": "human"|"ai", "content", "timestamp"}, ...]}`.

### Build Context

```
POST /api/chat/context
```

**Request Body:**
```json
{
  "notebook_id": "notebook:abc123",
  "context_config": {
    "sources": {"source:xyz": "full content", "source:uvw": "insights"},
    "notes": {"note:123": "full content"}
  }
}
```

Per-item values are `"full content"`, `"insights"` (sources only), or `"not in context"`. An empty `context_config` (`{}`) includes every source and note in the notebook with its short context. Returns `{"context": {"sources": [...], "notes": [...]}, "token_count": n, "char_count": n}`.

---

## Search

### Search Knowledge Base

```
POST /api/search
```

**Request Body:**
```json
{
  "query": "search terms",
  "type": "vector",
  "limit": 10,
  "search_sources": true,
  "search_notes": true,
  "minimum_score": 0.2,
  "notebook_id": "notebook:abc123"
}
```

`type` is `"text"` (default, keyword matching) or `"vector"` (requires an embedding model). `limit` is 1-1000 (default 100); `minimum_score` applies to vector search. Scope with `notebook_id` or `notebook_ids` (up to 50); omit both to search everything. Returns `{"results": [...], "total_count": n, "search_type": "..."}`.

### Ask with Streaming

```
POST /api/search/ask
```

**Request Body:**
```json
{
  "question": "How does TMB predict checkpoint inhibitor response?",
  "strategy_model": "model:...",
  "answer_model": "model:...",
  "final_answer_model": "model:...",
  "notebook_id": "notebook:abc123"
}
```

All three model IDs are required (see `GET /api/models` or `GET /api/models/defaults`), and an embedding model must be configured. Returns Server-Sent Events (`strategy`, `answer`, `final_answer` events).

### Ask Simple

```
POST /api/search/ask/simple
```

Same body; non-streaming. Returns `{"answer": "...", "question": "..."}`.

---

## Podcasts

### Generate Podcast

```
POST /api/podcasts/generate
```

**Request Body:**
```json
{
  "episode_profile": "tech_discussion",
  "speaker_profile": "tech_experts",
  "episode_name": "TMB and immunotherapy",
  "notebook_id": "notebook:abc123",
  "briefing_suffix": "Optional extra instructions"
}
```

`episode_profile` and `speaker_profile` are profile **names** (list them with `GET /api/episode-profiles` and `GET /api/speaker-profiles`; an episode profile's `speaker_config_name` gives its default speaker profile). Pass `content` instead of `notebook_id` to generate from raw text. Returns `{"job_id", "status": "submitted", "message", "episode_profile", "episode_name"}`.

### Get Job Status

```
GET /api/podcasts/jobs/{job_id}
```

Returns `job_id`, `status`, `result`, `error_message`, `progress`, and timestamps. It does not include the episode ID — list episodes and match on `name`.

### List Episodes

```
GET /api/podcasts/episodes
```

Each episode includes `id`, `name`, `audio_url`, `job_status`, and the profile snapshots used.

### Get Episode

```
GET /api/podcasts/episodes/{episode_id}
```

### Get Episode Audio

```
GET /api/podcasts/episodes/{episode_id}/audio
```

Streams the podcast audio file.

### Retry Failed Episode

```
POST /api/podcasts/episodes/{episode_id}/retry
```

### Delete Episode

```
DELETE /api/podcasts/episodes/{episode_id}
```

---

## Transformations

### List Transformations

```
GET /api/transformations
```

### Create Transformation

```
POST /api/transformations
```

**Request Body:**
```json
{
  "name": "summarize",
  "title": "Summarize Content",
  "description": "Generate a concise summary",
  "prompt": "Summarize the following text...",
  "apply_default": false
}
```

### Execute Transformation

```
POST /api/transformations/execute
```

**Request Body:**
```json
{
  "transformation_id": "transformation:abc",
  "input_text": "Text to transform...",
  "model_id": "model:xyz"
}
```

### Get Default Prompt

```
GET /api/transformations/default-prompt
```

### Update Default Prompt

```
PUT /api/transformations/default-prompt
```

### Get Transformation

```
GET /api/transformations/{transformation_id}
```

### Update Transformation

```
PUT /api/transformations/{transformation_id}
```

### Delete Transformation

```
DELETE /api/transformations/{transformation_id}
```

---

## Models

### List Models

```
GET /api/models
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Filter by type: `language`, `embedding`, `text_to_speech`, `speech_to_text` |

### Create Model

```
POST /api/models
```

### Delete Model

```
DELETE /api/models/{model_id}
```

### Test Model

```
POST /api/models/{model_id}/test
```

### Get Default Models

```
GET /api/models/defaults
```

Returns default model IDs for seven slots: `default_chat_model`, `default_transformation_model`, `large_context_model`, `default_embedding_model`, `default_text_to_speech_model`, `default_speech_to_text_model`, and `default_tools_model`.

### Update Default Models

```
PUT /api/models/defaults
```

### Get Providers

```
GET /api/models/providers
```

### Discover Models

```
GET /api/models/discover/{provider}
```

### Sync Models (Single Provider)

```
POST /api/models/sync/{provider}
```

### Sync All Models

```
POST /api/models/sync
```

### Auto-Assign Defaults

```
POST /api/models/auto-assign
```

Automatically populate empty default model slots using provider priority rankings.

### Get Model Count

```
GET /api/models/count/{provider}
```

### Get Models by Provider

```
GET /api/models/by-provider/{provider}
```

---

## Credentials

### Get Status

```
GET /api/credentials/status
```

### Get Environment Status

```
GET /api/credentials/env-status
```

### List Credentials

```
GET /api/credentials
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `provider` | string | Filter by provider |

### List by Provider

```
GET /api/credentials/by-provider/{provider}
```

### Create Credential

```
POST /api/credentials
```

**Request Body:**
```json
{
  "provider": "openai",
  "name": "My OpenAI Key",
  "api_key": "sk-...",
  "base_url": null
}
```

### Get Credential

```
GET /api/credentials/{credential_id}
```

Note: API key values are never returned.

### Update Credential

```
PUT /api/credentials/{credential_id}
```

### Delete Credential

```
DELETE /api/credentials/{credential_id}
```

### Test Credential

```
POST /api/credentials/{credential_id}/test
```

### Discover Models via Credential

```
POST /api/credentials/{credential_id}/discover
```

Returns `{"credential_id", "provider", "discovered": [{"name", "provider", "model_type", "description"}, ...]}`.

### Register Models via Credential

```
POST /api/credentials/{credential_id}/register-models
```

**Request Body:**
```json
{
  "models": [
    {"name": "gpt-5-mini", "provider": "openai", "model_type": "language"},
    {"name": "text-embedding-3-small", "provider": "openai", "model_type": "embedding"}
  ]
}
```

Returns `{"created": n, "existing": n}`.

---

## Error Responses

The API returns standard HTTP status codes with JSON error bodies:

| Status | Meaning |
|--------|---------|
| 400 | Invalid input |
| 401 | Authentication required |
| 404 | Resource not found |
| 422 | Configuration error |
| 429 | Rate limited |
| 500 | Internal server error |
| 502 | External service error |

**Error Response Format:**
```json
{
  "detail": "Description of the error"
}
```
