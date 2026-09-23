# Open Notebook Examples

Request shapes below were checked against the Open Notebook 1.x API source (v1.14, 2026-09). The interactive schema at `http://localhost:5055/docs` is authoritative for your running version. If `OPEN_NOTEBOOK_PASSWORD` is set on the server, every call needs `Authorization: Bearer <password>`; the examples read it from the environment.

```python
import os

BASE_URL = os.getenv("OPEN_NOTEBOOK_URL", "http://localhost:5055") + "/api"
_password = os.getenv("OPEN_NOTEBOOK_PASSWORD")
HEADERS = {"Authorization": f"Bearer {_password}"} if _password else {}
```

## Complete Research Workflow

This example demonstrates a full research workflow: creating a notebook, adding sources, generating notes, chatting with the AI, and searching across materials.

```python
import time
import requests

# BASE_URL and HEADERS as defined above


def complete_research_workflow():
    """End-to-end research workflow with Open Notebook."""

    # 1. Create a research notebook
    notebook = requests.post(f"{BASE_URL}/notebooks", headers=HEADERS, json={
        "name": "Drug Resistance in Cancer",
        "description": "Review of mechanisms of drug resistance in solid tumors",
    }).json()
    notebook_id = notebook["id"]
    print(f"Created notebook: {notebook_id}")

    # 2. Add sources from URLs (type is required; embed enables vector search)
    urls = [
        "https://www.nature.com/articles/s41568-020-0281-y",
        "https://www.cell.com/cancer-cell/fulltext/S1535-6108(20)30211-8",
    ]

    source_ids = []
    for url in urls:
        source = requests.post(f"{BASE_URL}/sources", headers=HEADERS, data={
            "type": "link",
            "url": url,
            "notebook_id": notebook_id,
            "embed": "true",
            "async_processing": "true",
        }).json()
        source_ids.append(source["id"])
        print(f"Added source: {source['id']}")

    # 3. Wait for processing to complete (queued -> running -> completed/failed)
    for source_id in source_ids:
        while True:
            status = requests.get(
                f"{BASE_URL}/sources/{source_id}/status", headers=HEADERS
            ).json()
            if status.get("status") in ("completed", "failed", None):
                break
            time.sleep(5)
        print(f"Source {source_id}: {status.get('status')}")

    # 4. Create a chat session, build context from the notebook, and ask
    session = requests.post(f"{BASE_URL}/chat/sessions", headers=HEADERS, json={
        "notebook_id": notebook_id,
        "title": "Resistance Mechanisms",
    }).json()

    ctx = requests.post(f"{BASE_URL}/chat/context", headers=HEADERS, json={
        "notebook_id": notebook_id,
        "context_config": {"sources": {sid: "full content" for sid in source_ids}},
    }).json()

    reply = requests.post(f"{BASE_URL}/chat/execute", headers=HEADERS, json={
        "session_id": session["id"],
        "message": "What are the primary mechanisms of drug resistance in solid tumors?",
        "context": ctx["context"],
    }).json()
    print(f"AI response: {reply['messages'][-1]['content']}")

    # 5. Search across materials (field is "type", not "search_type")
    results = requests.post(f"{BASE_URL}/search", headers=HEADERS, json={
        "query": "efflux pump resistance mechanism",
        "type": "vector",
        "limit": 5,
        "notebook_id": notebook_id,
    }).json()
    print(f"Found {results['total_count']} search results")

    # 6. Create a human note summarizing findings
    note = requests.post(f"{BASE_URL}/notes", headers=HEADERS, json={
        "title": "Summary of Resistance Mechanisms",
        "content": "Key findings from the literature...",
        "note_type": "human",
        "notebook_id": notebook_id,
    }).json()
    print(f"Created note: {note['id']}")


if __name__ == "__main__":
    complete_research_workflow()
```

## File Upload Example

```python
from pathlib import Path
import requests

# BASE_URL and HEADERS as defined above


def upload_research_papers(notebook_id, file_paths):
    """Upload multiple research papers to a notebook."""
    for path in map(Path, file_paths):
        with path.open("rb") as f:
            response = requests.post(
                f"{BASE_URL}/sources",
                headers=HEADERS,
                data={
                    "type": "upload",
                    "notebook_id": notebook_id,
                    "embed": "true",
                    "async_processing": "true",
                },
                files={"file": (path.name, f)},
            )
        if response.ok:
            print(f"Uploaded: {path}")
        else:
            print(f"Failed: {path} - {response.status_code} {response.text}")


# Usage
upload_research_papers("notebook:abc123", [
    "papers/study_1.pdf",
    "papers/study_2.pdf",
    "papers/supplementary.docx",
])
```

The API rejects request bodies above `OPEN_NOTEBOOK_MAX_UPLOAD_SIZE_MB` (default 100 MB).

## Podcast Generation Example

```python
import time
import requests

# BASE_URL and HEADERS as defined above


def generate_research_podcast(notebook_id, episode_name="Research briefing"):
    """Generate a podcast episode from notebook contents."""

    # Profiles are referenced by name; list what is configured
    episode_profiles = requests.get(f"{BASE_URL}/episode-profiles", headers=HEADERS).json()
    profile = episode_profiles[0]
    print(f"Using episode profile {profile['name']} with speakers {profile.get('speaker_config_name')}")

    # Submit podcast generation job
    job = requests.post(f"{BASE_URL}/podcasts/generate", headers=HEADERS, json={
        "episode_profile": profile["name"],
        "speaker_profile": profile["speaker_config_name"],
        "episode_name": episode_name,
        "notebook_id": notebook_id,
    }).json()
    job_id = job["job_id"]
    print(f"Podcast generation started: {job_id}")

    # Poll for completion
    while True:
        status = requests.get(f"{BASE_URL}/podcasts/jobs/{job_id}", headers=HEADERS).json()
        print(f"Status: {status.get('status')}")
        if status.get("status") in ("completed", "failed"):
            break
        time.sleep(10)

    if status["status"] == "completed":
        # The job status has no episode ID; find the episode by name
        episodes = requests.get(f"{BASE_URL}/podcasts/episodes", headers=HEADERS).json()
        episode = next(e for e in episodes if e["name"] == episode_name)
        audio = requests.get(
            f"{BASE_URL}/podcasts/episodes/{episode['id']}/audio", headers=HEADERS
        )
        audio.raise_for_status()
        with open("research_podcast.mp3", "wb") as f:
            f.write(audio.content)
        print("Podcast saved to research_podcast.mp3")
    else:
        print(f"Generation failed: {status.get('error_message')}")


if __name__ == "__main__":
    generate_research_podcast("notebook:abc123")
```

## Custom Transformation Pipeline

```python
import requests

# BASE_URL and HEADERS as defined above


def create_and_run_transformations():
    """Create custom transformations and apply them to content."""

    # Create a methodology extraction transformation
    transform = requests.post(f"{BASE_URL}/transformations", headers=HEADERS, json={
        "name": "extract_methods",
        "title": "Extract Methods",
        "description": "Extract and structure methodology from papers",
        "prompt": (
            "Extract the methodology section from this text. "
            "Organize into: Study Design, Sample Size, Statistical Methods, "
            "and Key Variables. Format as structured markdown."
        ),
        "apply_default": False,
    }).json()

    # Pick a language model (model types: language, embedding, text_to_speech, speech_to_text)
    models = requests.get(f"{BASE_URL}/models", headers=HEADERS, params={"type": "language"}).json()
    model_id = models[0]["id"]

    # Execute the transformation
    result = requests.post(f"{BASE_URL}/transformations/execute", headers=HEADERS, json={
        "transformation_id": transform["id"],
        "input_text": "We conducted a randomized controlled trial with...",
        "model_id": model_id,
    }).json()
    print(f"Extracted methods:\n{result['output']}")


if __name__ == "__main__":
    create_and_run_transformations()
```

## Semantic Search Scoped to a Notebook

```python
import requests

# BASE_URL and HEADERS as defined above


def advanced_search(notebook_id, query):
    """Perform notebook-scoped semantic search and get an AI answer."""

    # Vector search restricted to one notebook (or pass notebook_ids=[...])
    results = requests.post(f"{BASE_URL}/search", headers=HEADERS, json={
        "query": query,
        "type": "vector",
        "limit": 10,
        "notebook_id": notebook_id,
        "minimum_score": 0.5,
        "search_notes": False,
    }).json()

    print(f"Found {results['total_count']} results:")
    for result in results["results"]:
        print(f"  - {result.get('title', 'Untitled')} "
              f"(similarity: {result.get('similarity', 'N/A')})")

    # Get an AI-powered answer; the three model IDs are required
    defaults = requests.get(f"{BASE_URL}/models/defaults", headers=HEADERS).json()
    chat_model = defaults["default_chat_model"]
    answer = requests.post(f"{BASE_URL}/search/ask/simple", headers=HEADERS, json={
        "question": query,
        "strategy_model": chat_model,
        "answer_model": chat_model,
        "final_answer_model": chat_model,
        "notebook_id": notebook_id,
    }).json()
    print(f"\nAI Answer: {answer['answer']}")


if __name__ == "__main__":
    advanced_search("notebook:abc123", "CRISPR gene editing efficiency")
```

## Model Management

```python
import requests

# BASE_URL and HEADERS as defined above


def setup_ai_models():
    """Configure AI models for Open Notebook."""

    # Check available providers
    providers = requests.get(f"{BASE_URL}/models/providers", headers=HEADERS).json()
    print(f"Available providers: {providers}")

    # Discover models from a provider (list of {name, provider, model_type, ...})
    discovered = requests.get(
        f"{BASE_URL}/models/discover/openai", headers=HEADERS
    ).json()
    print(f"Discovered {len(discovered)} OpenAI models")

    # Sync models to make them available
    requests.post(f"{BASE_URL}/models/sync/openai", headers=HEADERS)

    # Auto-assign default models
    requests.post(f"{BASE_URL}/models/auto-assign", headers=HEADERS)

    # Check current defaults
    defaults = requests.get(f"{BASE_URL}/models/defaults", headers=HEADERS).json()
    print(f"Default models: {defaults}")


if __name__ == "__main__":
    setup_ai_models()
```
