"""
Open Notebook - Chat Interaction Example

Demonstrates creating chat sessions, sending messages with context,
and searching across research materials.

Prerequisites:
    pip install requests

Usage:
    export OPEN_NOTEBOOK_URL="http://localhost:5055"
    export OPEN_NOTEBOOK_PASSWORD="..."   # only if the server sets one
    python chat_interaction.py
"""

import os
import requests

BASE_URL = os.getenv("OPEN_NOTEBOOK_URL", "http://localhost:5055") + "/api"
_PASSWORD = os.getenv("OPEN_NOTEBOOK_PASSWORD")
HEADERS = {"Authorization": f"Bearer {_PASSWORD}"} if _PASSWORD else {}


def create_chat_session(notebook_id, title, model_override=None):
    """Create a new chat session within a notebook."""
    payload = {
        "notebook_id": notebook_id,
        "title": title,
    }
    if model_override:
        payload["model_override"] = model_override
    response = requests.post(f"{BASE_URL}/chat/sessions", headers=HEADERS, json=payload)
    response.raise_for_status()
    session = response.json()
    print(f"Created chat session: {session['id']} - {title}")
    return session


def list_chat_sessions(notebook_id):
    """List all chat sessions for a notebook."""
    response = requests.get(
        f"{BASE_URL}/chat/sessions",
        headers=HEADERS,
        params={"notebook_id": notebook_id},
    )
    response.raise_for_status()
    sessions = response.json()
    print(f"Found {len(sessions)} chat session(s):")
    for s in sessions:
        print(f"  - {s['id']}: {s.get('title', 'Untitled')} "
              f"({s.get('message_count', 0)} messages)")
    return sessions


def send_chat_message(session_id, message, context, model_override=None):
    """Send a message to a chat session.

    `context` is the "context" object returned by build_context(); the model only
    sees the sources and notes it contains.
    """
    payload = {
        "session_id": session_id,
        "message": message,
        "context": context,
    }
    if model_override:
        payload["model_override"] = model_override
    response = requests.post(f"{BASE_URL}/chat/execute", headers=HEADERS, json=payload)
    response.raise_for_status()
    result = response.json()  # {"session_id": ..., "messages": [{id, type, content}, ...]}
    messages = result.get("messages", [])
    print(f"\nUser: {message}")
    print(f"AI: {messages[-1]['content'] if messages else result}")
    return result


def get_session_history(session_id):
    """Retrieve full message history for a chat session."""
    response = requests.get(f"{BASE_URL}/chat/sessions/{session_id}", headers=HEADERS)
    response.raise_for_status()
    session = response.json()
    messages = session.get("messages", [])
    print(f"\n--- Session History ({len(messages)} messages) ---")
    for msg in messages:
        role = msg.get("type", "unknown")  # "human" or "ai"
        content = msg.get("content", "")
        print(f"[{role}]: {content[:200]}...")
    return session


def build_context(notebook_id, source_ids=None, note_ids=None):
    """Build chat context from a notebook's sources and notes.

    With no IDs, every source and note in the notebook is included as short
    context; listed IDs are included in full.
    """
    context_config = {}
    if source_ids:
        context_config["sources"] = {sid: "full content" for sid in source_ids}
    if note_ids:
        context_config["notes"] = {nid: "full content" for nid in note_ids}
    payload = {"notebook_id": notebook_id, "context_config": context_config}
    response = requests.post(f"{BASE_URL}/chat/context", headers=HEADERS, json=payload)
    response.raise_for_status()
    context = response.json()
    print(f"Context built: {context.get('token_count', '?')} tokens, "
          f"{context.get('char_count', '?')} characters")
    return context


def search_knowledge_base(query, search_type="text", limit=5, notebook_id=None):
    """Search across materials ("text" = full-text; "vector" needs an embedding model)."""
    payload = {"query": query, "type": search_type, "limit": limit}
    if notebook_id:
        payload["notebook_id"] = notebook_id
    response = requests.post(f"{BASE_URL}/search", headers=HEADERS, json=payload)
    response.raise_for_status()
    results = response.json()
    print(f"\nSearch results for '{query}' ({results.get('total_count', 0)} hits):")
    for r in results.get("results", []):
        title = r.get("title", "Untitled")
        similarity = r.get("similarity", "N/A")
        print(f"  - {title} (similarity: {similarity})")
    return results


def ask_question(query, notebook_id=None):
    """Ask a question and get an AI-generated answer from the knowledge base.

    The endpoint needs three model IDs; this uses the default chat model for all
    three. Ask also requires an embedding model to be configured.
    """
    defaults = requests.get(f"{BASE_URL}/models/defaults", headers=HEADERS).json()
    chat_model = defaults.get("default_chat_model")
    payload = {
        "question": query,
        "strategy_model": chat_model,
        "answer_model": chat_model,
        "final_answer_model": chat_model,
    }
    if notebook_id:
        payload["notebook_id"] = notebook_id
    response = requests.post(f"{BASE_URL}/search/ask/simple", headers=HEADERS, json=payload)
    response.raise_for_status()
    result = response.json()  # {"answer": ..., "question": ...}
    print(f"\nQ: {query}")
    print(f"A: {result.get('answer', result)}")
    return result


def delete_chat_session(session_id):
    """Delete a chat session."""
    response = requests.delete(f"{BASE_URL}/chat/sessions/{session_id}", headers=HEADERS)
    response.raise_for_status()
    print(f"Deleted chat session: {session_id}")


if __name__ == "__main__":
    print("=== Chat Interaction Demo ===\n")

    # Create a notebook with some content first
    notebook = requests.post(f"{BASE_URL}/notebooks", headers=HEADERS, json={
        "name": "Chat Demo",
        "description": "Demonstrating chat interactions",
    }).json()
    notebook_id = notebook["id"]

    # Add a text source for context
    requests.post(f"{BASE_URL}/sources", headers=HEADERS, data={
        "type": "text",
        "title": "Immunotherapy background",
        "content": (
            "Immunotherapy has revolutionized cancer treatment. "
            "Checkpoint inhibitors targeting PD-1 and PD-L1 have shown "
            "remarkable efficacy in non-small cell lung cancer, melanoma, "
            "and several other tumor types. Tumor mutational burden (TMB) "
            "has emerged as a key biomarker for predicting response to "
            "immunotherapy. Patients with high TMB tend to generate more "
            "neoantigens, making their tumors more visible to the immune system."
        ),
        "notebook_id": notebook_id,
        "embed": "true",
        "async_processing": "false",
    }).raise_for_status()

    # Create a chat session and build context from the notebook
    session = create_chat_session(notebook_id, "Immunotherapy Discussion")
    context = build_context(notebook_id)["context"]

    # Have a conversation
    print()
    send_chat_message(
        session["id"],
        "What are the main biomarkers for immunotherapy response?",
        context,
    )

    send_chat_message(
        session["id"],
        "How does TMB relate to neoantigen load?",
        context,
    )

    # View conversation history
    get_session_history(session["id"])

    # Search the knowledge base
    search_knowledge_base("checkpoint inhibitor efficacy", notebook_id=notebook_id)

    # Ask a standalone question
    ask_question("What is the role of PD-L1 in cancer immunotherapy?", notebook_id=notebook_id)

    # Clean up
    print()
    delete_chat_session(session["id"])
    requests.delete(f"{BASE_URL}/notebooks/{notebook_id}", headers=HEADERS)
    print("Cleanup complete")
