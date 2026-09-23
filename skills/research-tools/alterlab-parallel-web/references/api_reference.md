# Parallel Web Systems API Quick Reference

**Full Documentation:** https://docs.parallel.ai
**API Key:** https://platform.parallel.ai
**Python SDK:** `uv pip install parallel-web` (imports as `parallel`)
**Environment Variable:** `PARALLEL_API_KEY`

> **What this skill's `scripts/parallel_web.py` actually wraps:**
> - `search` and `research` commands → the **Chat API (Beta)** (`base` / `core` models, via the OpenAI SDK). They do NOT call the raw Search API or Task API.
> - `extract` command → the **Extract API v1** (via the `parallel` SDK, `client.extract()`).
>
> The Search, Task, and Responses API sections below document Parallel's raw endpoints for reference only. The bundled script does not expose `search_queries`, `max_results`, `source_policy`, `mode`, or `processor` — to use them, call the SDK/HTTP API directly. Endpoints, prices, and limits were checked against docs.parallel.ai on 2026-09-23; re-check before quoting costs.

---

## Search API (v1, GA)

**Endpoint:** `POST https://api.parallel.ai/v1/search` (the Beta `/v1beta/search` endpoint and `client.beta.search()` are legacy; `parallel-web` ≥ 1.0 removed the Beta method)

### Request

```json
{
  "objective": "Natural language search goal (optional, up to 5000 chars)",
  "search_queries": ["keyword query 1", "keyword query 2"],
  "mode": "fast",
  "max_chars_total": 50000,
  "advanced_settings": {
    "max_results": 10,
    "excerpt_settings": {"max_chars_per_result": 10000},
    "source_policy": {
      "include_domains": ["example.com"],
      "exclude_domains": ["spam.com"],
      "after_date": "2024-01-01"
    },
    "location": "us"
  }
}
```

`search_queries` is required (at least one; 2-3 short queries work best). `mode` is `turbo`, `fast`, `basic`, or `advanced` (default `advanced`). `max_results` defaults to 10 and public modes cap it at 20.

### Response

```json
{
  "search_id": "search_...",
  "session_id": "...",
  "results": [
    {
      "url": "https://...",
      "title": "Page Title",
      "publish_date": "2025-01-15",
      "excerpts": ["Relevant content..."]
    }
  ],
  "warnings": null
}
```

### Python SDK

```python
from parallel import Parallel
client = Parallel()  # reads PARALLEL_API_KEY
result = client.search(
    objective="...",
    search_queries=["..."],
    mode="fast",
    advanced_settings={"max_results": 10, "excerpt_settings": {"max_chars_per_result": 10000}},
)
```

**Cost:** $1 per 1,000 requests (`turbo`, `fast`) or $5 per 1,000 (`basic`, `advanced`), including 10 results; each additional result is $1 per 1,000
**Rate Limit:** 600 requests/minute

---

## Extract API (v1, GA)

**Endpoint:** `POST https://api.parallel.ai/v1/extract` (Beta `/v1beta/extract` and `client.beta.extract()` are legacy)

### Request

```json
{
  "urls": ["https://example.com/page"],
  "objective": "What to focus on",
  "search_queries": ["optional keywords"],
  "max_chars_total": 50000,
  "advanced_settings": {
    "excerpt_settings": {"max_chars_per_result": 5000},
    "full_content": true
  }
}
```

Up to 20 URLs per request. Excerpts are always returned; `advanced_settings.full_content` (`true` or `{"max_chars_per_result": N}`) adds the full page as markdown. `advanced_settings.fetch_policy` (e.g. `{"max_age_seconds": 3600}`) forces a live fetch when the cached copy is older.

### Response

```json
{
  "extract_id": "extract_...",
  "session_id": "...",
  "results": [
    {
      "url": "https://...",
      "title": "Page Title",
      "publish_date": "2025-01-15",
      "excerpts": ["Focused content..."],
      "full_content": null
    }
  ],
  "errors": [{"url": "https://...", "error_type": "...", "http_status_code": 403}]
}
```

### Python SDK

```python
result = client.extract(
    urls=["https://..."],
    objective="...",
    advanced_settings={"full_content": True},
)
```

**Cost:** $1 per 1,000 URLs
**Rate Limit:** 600 requests/minute

---

## Task API (Deep Research)

**Endpoint:** `POST https://api.parallel.ai/v1/tasks/runs`

### Create Task Run

```json
{
  "input": "Research question (max 15,000 chars)",
  "processor": "pro-fast",
  "task_spec": {
    "output_schema": {
      "type": "text"
    }
  }
}
```

### Response (immediate)

```json
{
  "run_id": "trun_...",
  "status": "queued"
}
```

### Get Result (blocking)

**Endpoint:** `GET https://api.parallel.ai/v1/tasks/runs/{run_id}/result`

### Python SDK

```python
# Text output (markdown report with citations)
from parallel.types import TaskSpecParam
task_run = client.task_run.create(
    input="Research question",
    processor="pro-fast",
    task_spec=TaskSpecParam(output_schema={"type": "text"}),
)
result = client.task_run.result(task_run.run_id, api_timeout=3600)
print(result.output.content)

# Auto-schema output (structured JSON)
task_run = client.task_run.create(
    input="Research question",
    processor="pro-fast",
)
result = client.task_run.result(task_run.run_id, api_timeout=3600)
print(result.output.content)  # structured dict
print(result.output.basis)    # citations per field
```

### Processors

| Processor | Latency | Cost/1000 | Best For |
|-----------|---------|-----------|----------|
| `lite-fast` | 10-20s | $5 | Basic metadata |
| `base-fast` | 15-50s | $10 | Standard enrichments |
| `core-fast` | 15s-100s | $25 | Cross-referenced |
| `core2x-fast` | 15s-3min | $50 | High complexity |
| **`pro-fast`** | **30s-5min** | **$100** | **Default: exploratory research** |
| `ultra-fast` | 1-10min | $300 | Deep multi-source |
| `ultra2x-fast` | 1-20min | $600 | Difficult research |
| `ultra4x-fast` | 1-40min | $1200 | Very difficult |
| `ultra8x-fast` | 1hr | $2400 | Most difficult |

Standard (non-fast) processors have the same cost but higher latency and freshest data.

---

## Chat API (Beta)

**Endpoint:** `POST https://api.parallel.ai/v1beta/chat/completions` — with the OpenAI SDK set `base_url="https://api.parallel.ai/v1beta"`.
**Compatible with the OpenAI Chat Completions format.** `temperature`, `max_tokens`, and similar sampling fields are accepted but ignored.

### Models

| Model | Latency | Use Case |
|-------|---------|----------|
| `speed` | ~3s | Low-latency chat, no research basis |
| `lite` | 10-60s | Simple lookups with basis |
| `base` | 15-100s | Standard research with basis (citations, reasoning, excerpts) |
| `core` | 1-5min | Complex research with basis |

The research models return a `basis` field with per-claim citations, which the script turns into its sources list. Parallel's Chat API quickstart now redirects to the Responses API (below) and the pricing page no longer lists Chat API prices; the Chat API remains in the API reference with its own rate limit. If you start a new integration, evaluate the Responses API first.

### Python SDK (OpenAI-compatible)

```python
import os
from openai import OpenAI
client = OpenAI(
    api_key=os.environ["PARALLEL_API_KEY"],
    base_url="https://api.parallel.ai/v1beta",
)
response = client.chat.completions.create(
    model="base",
    messages=[{"role": "user", "content": "What is Parallel Web Systems?"}],
)
```

---

## Responses API (not wrapped by the script)

**Endpoint:** `POST https://api.parallel.ai/v1/responses` — OpenAI Responses-compatible (launched July 2026). One model id, `parallel`; `reasoning.effort` picks the tier:

| `reasoning.effort` | Latency | Cost per 1,000 requests |
|--------------------|---------|-------------------------|
| `low` | ~5-10s | $10 |
| `medium` (default) | ~15-20s | $50 |
| `high` | ~30-60s | $250 |

```python
import os
from openai import OpenAI
client = OpenAI(api_key=os.environ["PARALLEL_API_KEY"], base_url="https://api.parallel.ai/v1")
resp = client.responses.create(model="parallel", input="...", reasoning={"effort": "medium"})
print(resp.output_text)  # URL citations arrive as annotations on the message content
```

It is synchronous only; for long-running or batch research use the Task API.

---

## Rate Limits

| API | Default Limit |
|-----|---------------|
| Search | 600 req/min |
| Extract | 600 req/min |
| Chat | 300 req/min |
| Task / Task Group runs | 2,000 runs/min |

Limits apply to POST requests that create resources; polling results with GET does not count.

---

## Source Policy

Control which sources are used (Search API: inside `advanced_settings`; Task API: top-level `source_policy`):

```json
{
  "source_policy": {
    "include_domains": ["nature.com", "science.org"],
    "exclude_domains": ["unreliable-source.com"],
    "after_date": "2024-01-01"
  }
}
```

`include_domains` is a hard allow-list (nothing else is searched) and can lower result quality; prefer steering through the `objective` unless the task must come from specific publishers. Entries may be domains, domain/path prefixes, or a bare extension such as `.gov`; the two lists together hold at most 200 entries.
