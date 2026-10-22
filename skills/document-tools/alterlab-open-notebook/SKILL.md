---
name: alterlab-open-notebook
description: Runs and scripts Open Notebook, a self-hosted open-source alternative to Google NotebookLM with a full REST API, for AI-powered research and document analysis. Use when organizing research materials into notebooks, ingesting diverse content sources (PDFs, videos, audio, web pages, Office documents), generating AI-powered notes and summaries, creating multi-speaker podcasts from research, chatting with documents using context-aware AI, searching across materials with full-text and vector search, or running custom content transformations. Runs keyless on local models (Ollama or LM Studio; a local Speaches server for podcast voices), with OpenAI, Anthropic, Google, Groq, Mistral and other cloud providers as optional extras, and data kept on your own infrastructure through self-hosting. For a one-shot file-to-Markdown conversion (no notebook, chat, or search), use alterlab-markitdown instead. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*)
compatibility: "No API key required: a self-hosted Open Notebook 1.x instance (Docker Compose; UI on :8502, REST API on :5055) runs on a local Ollama or LM Studio server; cloud provider keys are optional. OPEN_NOTEBOOK_ENCRYPTION_KEY is a random string you generate for your own instance (not an account); OPEN_NOTEBOOK_PASSWORD is optional (Bearer auth on your API)."
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    last_updated: "2026-10-22"
    credentials: "optional: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, GROQ_API_KEY, MISTRAL_API_KEY (a cloud model provider instead of local Ollama/LM Studio), ELEVENLABS_API_KEY (cloud podcast voices instead of a local Speaches server), OPEN_NOTEBOOK_PASSWORD (Bearer auth on your own instance's API), SURREAL_PASSWORD (your own SurrealDB login)"
---

# Open Notebook

## Overview

Open Notebook is an open-source (MIT), self-hosted alternative to Google's NotebookLM that lets researchers organize materials, generate AI-powered insights, create podcasts, and hold context-aware conversations with their documents. It exposes a full REST API, works with 18+ AI providers through the Esperanto library, and runs entirely on your own infrastructure. This skill targets the **1.x** line (v1.14 as of 2026-09; Docker image `lfnovo/open_notebook:v1-latest`).

**Key advantages over NotebookLM:**
- Full REST API for programmatic access and automation
- Choice of 18+ AI providers (not locked to Google models), including fully local Ollama / LM Studio
- Multi-speaker podcast generation with 1-4 customizable speakers
- Storage stays on your own machine or server
- Open source and extensible (MIT license)

**Data privacy:** self-hosting keeps notebooks and files local, but source text is still sent to whichever cloud model provider you configure. For sensitive or IRB-restricted material, use a local provider (Ollama, LM Studio) or one covered by your data agreements.

**Repository:** https://github.com/lfnovo/open-notebook

## When to Use This Skill

Use this skill when the user wants to:
- Stand up a private, self-hosted NotebookLM-style research workspace
- Ingest PDFs, URLs, audio/video, or text into notebooks and chat with them using source context
- Search a personal research corpus with full-text or vector search
- Generate multi-speaker podcasts or custom transformations (summaries, method extraction) from sources
- Automate any of the above through the REST API

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| One-shot conversion of a file to Markdown (no notebook, chat, or search) | `alterlab-markitdown` |
| Located, cross-section Q&A inside a single PDF | `alterlab-pdf-explore` |
| A one-row-per-paper evidence table across many PDFs | `alterlab-pdf-extract` |
| Managing references, DOIs, or BibTeX in a Zotero library | `alterlab-pyzotero` |
| Systematic searching and screening of new literature | `alterlab-literature-review` |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-markitdown`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

## Quick Start

### Prerequisites

- Docker with Docker Compose v2 (OrbStack or Docker Desktop both work; `docker compose` must be available)
- A model provider: a local Ollama or LM Studio server (no key, no cost, nothing leaves the machine), or optionally a cloud provider key

### Installation

```bash
# 1. Download the official compose file (SurrealDB v2 + lfnovo/open_notebook:v1-latest)
curl -o docker-compose.yml https://raw.githubusercontent.com/lfnovo/open-notebook/main/docker-compose.yml

# 2. Set the encryption key: the compose file hard-codes
#    OPEN_NOTEBOOK_ENCRYPTION_KEY=change-me-to-a-secret-string, so edit that line
#    (exporting a shell variable has no effect on this file)
sed -i.bak "s/change-me-to-a-secret-string/$(openssl rand -hex 32)/" docker-compose.yml

# 3. Launch the services
docker compose up -d
```

Access the application (allow 15-20 seconds for startup):
- **Frontend UI:** http://localhost:8502
- **REST API:** http://localhost:5055
- **API Documentation:** http://localhost:5055/docs (the authoritative schema)

SurrealDB defaults to `root:root` and is bound to `127.0.0.1` only. Before exposing the instance beyond your machine, set `SURREAL_USER` / `SURREAL_PASSWORD` in a `.env` file next to the compose file, set `OPEN_NOTEBOOK_PASSWORD`, and put the UI/API behind HTTPS.

### Configure an AI Provider

**Keyless, fully local (default).** Start from the upstream `examples/docker-compose-ollama.yml`
instead of the plain compose file (or `examples/docker-compose-full-local.yml`, which also runs a
Speaches server for local podcast voices and transcription), set the encryption key the same way,
then pull a chat and an embedding model:

```bash
docker compose exec ollama ollama pull qwen3            # ~5 GB; llama3.2 (~2 GB) on small machines
docker compose exec ollama ollama pull nomic-embed-text # embeddings for vector search / Ask
```

In the UI, open **Models**, choose **Ollama**, leave **API Key** empty, set **Base URL** to
`http://ollama:11434` (the compose service name, not `localhost`), **Test**, **Sync Models**, then
**Auto-Assign Defaults**. A cloud provider is the same dialog with its key pasted in.

Or configure via the REST API:

```python
import os
import requests

BASE_URL = "http://localhost:5055/api"
# Only needed when OPEN_NOTEBOOK_PASSWORD is set on the server
HEADERS = {"Authorization": f"Bearer {os.environ['OPEN_NOTEBOOK_PASSWORD']}"} if os.environ.get("OPEN_NOTEBOOK_PASSWORD") else {}

# Keyless: register the local Ollama server (api_key is optional and omitted)
credential = requests.post(f"{BASE_URL}/credentials", headers=HEADERS, json={
    "provider": "ollama",
    "name": "Local Ollama",
    "base_url": "http://ollama:11434",
}).json()
# Optional cloud provider instead (key stored encrypted with OPEN_NOTEBOOK_ENCRYPTION_KEY):
# credential = requests.post(f"{BASE_URL}/credentials", headers=HEADERS, json={
#     "provider": "openai", "name": "My OpenAI Key", "api_key": os.environ["OPENAI_API_KEY"],
# }).json()

# Discover the provider's models: {"credential_id", "provider", "discovered": [{name, provider, model_type}, ...]}
discovered = requests.post(
    f"{BASE_URL}/credentials/{credential['id']}/discover", headers=HEADERS
).json()["discovered"]

# Register them (model_type: language, embedding, text_to_speech, speech_to_text)
requests.post(
    f"{BASE_URL}/credentials/{credential['id']}/register-models",
    headers=HEADERS,
    json={"models": [
        {"name": m["name"], "provider": m["provider"], "model_type": m["model_type"]}
        for m in discovered if m.get("model_type")
    ]},
).raise_for_status()

# Fill empty default slots (chat, transformation, large-context, embedding, TTS, STT, tools)
requests.post(f"{BASE_URL}/models/auto-assign", headers=HEADERS)
```

## Core Features

The snippets below reuse `BASE_URL` and `HEADERS` from above.

### Notebooks
Organize research into separate notebooks, each containing sources, notes, and chat sessions.

```python
notebook = requests.post(f"{BASE_URL}/notebooks", headers=HEADERS, json={
    "name": "Cancer Genomics Research",
    "description": "Literature review on tumor mutational burden",
}).json()
notebook_id = notebook["id"]
```

### Sources
Ingest PDFs, videos, audio, web pages, Office documents, or raw text. `POST /api/sources` takes multipart form fields; `type` is required (`link`, `upload`, or `text`), and `embed="true"` makes the source available to vector search.

```python
# Add a web URL source (processed in the background)
source = requests.post(f"{BASE_URL}/sources", headers=HEADERS, data={
    "type": "link",
    "url": "https://arxiv.org/abs/2301.00001",
    "notebook_id": notebook_id,
    "embed": "true",
    "async_processing": "true",
}).json()

# Upload a PDF file
with open("paper.pdf", "rb") as f:
    upload = requests.post(
        f"{BASE_URL}/sources",
        headers=HEADERS,
        data={"type": "upload", "notebook_id": notebook_id, "embed": "true"},
        files={"file": ("paper.pdf", f, "application/pdf")},
    ).json()

# Poll background processing: status is queued / running / completed / failed
status = requests.get(f"{BASE_URL}/sources/{source['id']}/status", headers=HEADERS).json()
```

### Notes
Create and manage notes (human or AI-generated) associated with notebooks.

```python
requests.post(f"{BASE_URL}/notes", headers=HEADERS, json={
    "title": "Key Findings",
    "content": "TMB correlates with immunotherapy response in NSCLC...",
    "note_type": "human",
    "notebook_id": notebook_id,
})
```

### Context-Aware Chat
Chat answers are grounded in the context you pass. Build it with `/api/chat/context` (an empty `context_config` includes every source and note in the notebook as short context; per-item values `"full content"`, `"insights"`, or `"not in context"` refine it), then send it with the message.

```python
session = requests.post(f"{BASE_URL}/chat/sessions", headers=HEADERS, json={
    "notebook_id": notebook_id,
    "title": "TMB Discussion",
}).json()

ctx = requests.post(f"{BASE_URL}/chat/context", headers=HEADERS, json={
    "notebook_id": notebook_id,
    "context_config": {},   # or {"sources": {source_id: "full content"}, "notes": {...}}
}).json()

reply = requests.post(f"{BASE_URL}/chat/execute", headers=HEADERS, json={
    "session_id": session["id"],
    "message": "What are the key biomarkers for immunotherapy response?",
    "context": ctx["context"],
}).json()
print(reply["messages"][-1]["content"])   # messages: [{id, type: human|ai, content}, ...]
```

### Search
Search across all materials using full-text (`"text"`, default) or semantic (`"vector"`, needs an embedding model) search, optionally scoped with `notebook_id` / `notebook_ids`.

```python
results = requests.post(f"{BASE_URL}/search", headers=HEADERS, json={
    "query": "tumor mutational burden immunotherapy",
    "type": "vector",
    "limit": 10,
    "notebook_id": notebook_id,
}).json()   # {"results": [...], "total_count": n, "search_type": "vector"}

# Ask a question: the three model IDs are required (see GET /api/models or /api/models/defaults)
defaults = requests.get(f"{BASE_URL}/models/defaults", headers=HEADERS).json()
chat_model = defaults["default_chat_model"]
answer = requests.post(f"{BASE_URL}/search/ask/simple", headers=HEADERS, json={
    "question": "How does TMB predict checkpoint inhibitor response?",
    "strategy_model": chat_model,
    "answer_model": chat_model,
    "final_answer_model": chat_model,
    "notebook_id": notebook_id,
}).json()["answer"]
```

`POST /api/search/ask` takes the same body and streams Server-Sent Events.

### Podcast Generation
Generate multi-speaker podcasts (1-4 speakers) from a notebook. Profiles are referenced **by name**: an episode profile (format, models, length) and a speaker profile (voices and personas). Ollama has no text-to-speech; for keyless, local voices run a Speaches server (`examples/docker-compose-full-local.yml`) and add it as an **OpenAI Compatible** provider, or use a cloud TTS provider with its key.

```python
episode_profile = requests.get(f"{BASE_URL}/episode-profiles", headers=HEADERS).json()[0]

job = requests.post(f"{BASE_URL}/podcasts/generate", headers=HEADERS, json={
    "episode_profile": episode_profile["name"],
    "speaker_profile": episode_profile["speaker_config_name"],   # or any name from /api/speaker-profiles
    "episode_name": "TMB and immunotherapy",
    "notebook_id": notebook_id,
}).json()

# Poll until the job reports "completed" (or "failed")
status = requests.get(f"{BASE_URL}/podcasts/jobs/{job['job_id']}", headers=HEADERS).json()["status"]

# Then locate the episode and download its audio
episodes = requests.get(f"{BASE_URL}/podcasts/episodes", headers=HEADERS).json()
episode = next(e for e in episodes if e["name"] == "TMB and immunotherapy")
audio = requests.get(f"{BASE_URL}/podcasts/episodes/{episode['id']}/audio", headers=HEADERS)
```

### Content Transformations
Apply custom AI-powered transformations to content for summarization, extraction, and analysis.

```python
transform = requests.post(f"{BASE_URL}/transformations", headers=HEADERS, json={
    "name": "extract_methods",
    "title": "Extract Methods",
    "description": "Extract methodology details from papers",
    "prompt": "Extract and summarize the methodology section...",
    "apply_default": False,
}).json()

result = requests.post(f"{BASE_URL}/transformations/execute", headers=HEADERS, json={
    "transformation_id": transform["id"],
    "input_text": "...",
    # "model_id": "model:...",   # optional; defaults to the transformation model
}).json()["output"]
```

## Supported AI Providers

Open Notebook supports 18+ AI providers through the Esperanto library. A representative subset:

| Provider | LLM | Embedding | Speech-to-Text | Text-to-Speech |
|----------|-----|-----------|----------------|----------------|
| OpenAI | Yes | Yes | Yes | Yes |
| Anthropic | Yes | No | No | No |
| Google GenAI | Yes | Yes | Yes | Yes |
| Vertex AI | Yes | Yes | No | Yes |
| Ollama | Yes | Yes | No | No |
| Groq | Yes | No | Yes | No |
| Mistral | Yes | Yes | Yes | Yes |
| Azure OpenAI | Yes | Yes | Yes | Yes |
| DeepSeek | Yes | No | No | No |
| xAI | Yes | No | No | Yes |
| OpenRouter | Yes | Yes | Yes | Yes |
| ElevenLabs | No | No | Yes | Yes |
| Voyage | No | Yes | No | No |
| OpenAI-compatible (LM Studio, vLLM, ...) | Yes | Yes | Yes | Yes |

For the full, current matrix (including oMLX, Perplexity, Deepgram, Cohere, DashScope, MiniMax, Novita), see the upstream README.

## Environment Variables

Key configuration variables for Docker deployment:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPEN_NOTEBOOK_ENCRYPTION_KEY` | **Required.** A random string you generate (`openssl rand -hex 32`), not an account key; encrypts stored provider credentials. Keep it stable (changing or losing it makes saved credentials unreadable) | None |
| `OPEN_NOTEBOOK_PASSWORD` | Optional password; when set, API calls need `Authorization: Bearer <password>` | None |
| `SURREAL_URL` | SurrealDB connection URL | `ws://surrealdb:8000/rpc` |
| `SURREAL_USER` / `SURREAL_PASSWORD` | SurrealDB credentials (override via `.env` before exposing the instance) | `root` / `root` |
| `SURREAL_NAMESPACE` | Database namespace | `open_notebook` |
| `SURREAL_DATABASE` | Database name | `open_notebook` |
| `OPEN_NOTEBOOK_WORKER_MAX_TASKS` | Concurrent background jobs; set `1` for a single local GPU | `5` |

## API Reference

The REST API is available at `http://localhost:5055/api`, with interactive documentation at `/docs`.

Core endpoint groups:
- `/api/notebooks` - Notebook CRUD, delete preview, and source association
- `/api/sources` - Source ingestion, status, retry, insights, download
- `/api/notes` - Note management
- `/api/chat/sessions`, `/api/chat/context`, `/api/chat/execute` - Chat sessions, context building, messages
- `/api/search`, `/api/search/ask`, `/api/search/ask/simple` - Full-text/vector search and question answering
- `/api/podcasts`, `/api/episode-profiles`, `/api/speaker-profiles` - Podcast generation and profiles
- `/api/transformations` - Content transformation pipelines
- `/api/models` - Model registration, defaults, sync, auto-assign
- `/api/credentials` - Provider credential management, discovery, registration

For request/response details see `references/api_reference.md`; runnable examples live in `scripts/` and `references/examples.md`.

## Architecture

Open Notebook uses a modern stack:
- **Backend:** Python with FastAPI
- **Database:** SurrealDB (document + relational)
- **AI Integration:** LangChain / LangGraph with the Esperanto multi-provider library
- **Frontend:** Next.js with React
- **Deployment:** Docker Compose with persistent volumes (`./notebook_data`, `./surreal_data`)

## Important Notes

- Open Notebook is deployed with Docker (a from-source setup exists for development)
- At least one model provider must be configured for AI features (a local Ollama/LM Studio server needs no key); vector search and Ask also need an embedding model
- For free local inference without API costs, use Ollama or LM Studio
- The `OPEN_NOTEBOOK_ENCRYPTION_KEY` must be set before first launch and kept consistent across restarts
- Data lives in the bind-mounted `notebook_data/` and `surreal_data/` folders; back them up
- MCP clients (Claude Desktop, VS Code) can reach a running instance through the community `open-notebook-mcp` package that the upstream docs reference (`uvx open-notebook-mcp` with `OPEN_NOTEBOOK_URL` / `OPEN_NOTEBOOK_PASSWORD`)

Part of the AlterLab Academic Skills suite.
