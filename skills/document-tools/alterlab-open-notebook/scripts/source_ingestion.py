"""
Open Notebook - Source Ingestion Example

Demonstrates ingesting various content types (URLs, files, text) into
Open Notebook and monitoring processing status.

Prerequisites:
    pip install requests

Usage:
    export OPEN_NOTEBOOK_URL="http://localhost:5055"
    export OPEN_NOTEBOOK_PASSWORD="..."   # only if the server sets one
    python source_ingestion.py
"""

import os
import time
import requests

BASE_URL = os.getenv("OPEN_NOTEBOOK_URL", "http://localhost:5055") + "/api"
_PASSWORD = os.getenv("OPEN_NOTEBOOK_PASSWORD")
HEADERS = {"Authorization": f"Bearer {_PASSWORD}"} if _PASSWORD else {}


def add_url_source(notebook_id, url, process_async=True, embed=True):
    """Add a web URL as a source to a notebook."""
    response = requests.post(f"{BASE_URL}/sources", headers=HEADERS, data={
        "type": "link",
        "url": url,
        "notebook_id": notebook_id,
        "embed": str(embed).lower(),
        "async_processing": str(process_async).lower(),
    })
    response.raise_for_status()
    source = response.json()
    print(f"Added URL source: {source['id']} - {url}")
    return source


def add_text_source(notebook_id, title, text, embed=True):
    """Add raw text as a source."""
    response = requests.post(f"{BASE_URL}/sources", headers=HEADERS, data={
        "type": "text",
        "title": title,
        "content": text,
        "notebook_id": notebook_id,
        "embed": str(embed).lower(),
        "async_processing": "false",
    })
    response.raise_for_status()
    source = response.json()
    print(f"Added text source: {source['id']} - {title}")
    return source


def upload_file_source(notebook_id, file_path, process_async=True, embed=True):
    """Upload a file (PDF, DOCX, audio, video) as a source."""
    filename = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/sources",
            headers=HEADERS,
            data={
                "type": "upload",
                "notebook_id": notebook_id,
                "embed": str(embed).lower(),
                "async_processing": str(process_async).lower(),
            },
            files={"file": (filename, f)},
        )
    response.raise_for_status()
    source = response.json()
    print(f"Uploaded file source: {source['id']} - {filename}")
    return source


def wait_for_processing(source_id, poll_interval=5, timeout=300):
    """Poll source processing status until completion or timeout."""
    elapsed = 0
    while elapsed < timeout:
        response = requests.get(f"{BASE_URL}/sources/{source_id}/status", headers=HEADERS)
        response.raise_for_status()
        status = response.json()
        # queued / running / completed / failed / unknown; None for legacy sources
        current_status = status.get("status")
        print(f"  Source {source_id}: {current_status} - {status.get('message', '')}")

        if current_status in ("completed", "failed", None):
            return status
        time.sleep(poll_interval)
        elapsed += poll_interval

    print(f"  Source {source_id}: timed out after {timeout}s")
    return None


def list_sources(notebook_id=None, limit=20):
    """List sources, optionally filtered by notebook."""
    params = {"limit": limit}
    if notebook_id:
        params["notebook_id"] = notebook_id
    response = requests.get(f"{BASE_URL}/sources", headers=HEADERS, params=params)
    response.raise_for_status()
    sources = response.json()
    print(f"Found {len(sources)} source(s):")
    for src in sources:
        print(f"  - {src['id']}: {src.get('title', 'Untitled')}")
    return sources


def get_source_insights(source_id):
    """Retrieve AI-generated insights for a source."""
    response = requests.get(f"{BASE_URL}/sources/{source_id}/insights", headers=HEADERS)
    response.raise_for_status()
    return response.json()


def retry_failed_source(source_id):
    """Retry processing for a failed source."""
    response = requests.post(f"{BASE_URL}/sources/{source_id}/retry", headers=HEADERS)
    response.raise_for_status()
    print(f"Retrying source: {source_id}")
    return response.json()


def delete_source(source_id):
    """Delete a source."""
    response = requests.delete(f"{BASE_URL}/sources/{source_id}", headers=HEADERS)
    response.raise_for_status()
    print(f"Deleted source: {source_id}")


if __name__ == "__main__":
    print("=== Source Ingestion Demo ===\n")

    # Create a notebook first
    notebook = requests.post(f"{BASE_URL}/notebooks", headers=HEADERS, json={
        "name": "Source Ingestion Demo",
        "description": "Testing various source types",
    }).json()
    notebook_id = notebook["id"]
    print(f"Created notebook: {notebook_id}\n")

    # Add a URL source
    url_source = add_url_source(
        notebook_id,
        "https://en.wikipedia.org/wiki/CRISPR_gene_editing",
    )

    # Add a text source
    text_source = add_text_source(
        notebook_id,
        "Research Notes",
        "CRISPR-Cas9 is a genome editing tool that allows researchers to "
        "alter DNA sequences and modify gene function. It has transformed "
        "biological research and offers potential for treating genetic diseases.",
    )

    # Wait for async processing
    print("\nWaiting for processing...")
    wait_for_processing(url_source["id"])

    # List all sources in the notebook
    print()
    list_sources(notebook_id)

    # Clean up
    print()
    delete_source(url_source["id"])
    delete_source(text_source["id"])
    requests.delete(f"{BASE_URL}/notebooks/{notebook_id}", headers=HEADERS)
    print("Cleanup complete")
