#!/usr/bin/env python3
"""
Perplexity Search via LiteLLM and OpenRouter

This script performs AI-powered web searches using Perplexity models through
LiteLLM and OpenRouter. It provides real-time, grounded answers with source citations.

Usage:
    python perplexity_search.py "search query" [options]

Requirements:
    - OpenRouter API key set in OPENROUTER_API_KEY environment variable
    - LiteLLM installed: uv pip install litellm

Author: Scientific Skills
License: MIT
"""

import os
import sys
import json
import argparse
from typing import Optional, Dict, Any, List

# Perplexity models on OpenRouter (checked against openrouter.ai/api/v1/models on
# 2026-09-23). `sonar-reasoning` was retired upstream; use `sonar-reasoning-pro`.
MODELS = ["sonar-pro", "sonar-pro-search", "sonar", "sonar-reasoning-pro"]


def check_dependencies():
    """Check if required packages are installed."""
    try:
        import litellm  # noqa: F401  # availability probe; real import is `from litellm import completion` below
        return True
    except ImportError:
        print("Error: LiteLLM is not installed.", file=sys.stderr)
        print("Install it with: uv pip install litellm", file=sys.stderr)
        return False


def check_api_key() -> Optional[str]:
    """Check if OpenRouter API key is configured."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable is not set.", file=sys.stderr)
        print("\nTo set up your API key:", file=sys.stderr)
        print("1. Get an API key from https://openrouter.ai/keys", file=sys.stderr)
        print("2. Set the environment variable:", file=sys.stderr)
        print("   export OPENROUTER_API_KEY='your-api-key-here'", file=sys.stderr)
        print("\nOr create a .env file with:", file=sys.stderr)
        print("   OPENROUTER_API_KEY=your-api-key-here", file=sys.stderr)
        return None
    return api_key


def search_with_perplexity(
    query: str,
    model: str = "openrouter/perplexity/sonar-pro",
    max_tokens: int = 4000,
    temperature: float = 0.2,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Perform a search using Perplexity models via LiteLLM and OpenRouter.

    Args:
        query: The search query
        model: Model to use (default: sonar-pro)
        max_tokens: Maximum tokens in response
        temperature: Response temperature (0.0-1.0)
        verbose: Print detailed information

    Returns:
        Dictionary containing the search results and metadata
    """
    try:
        from litellm import completion
    except ImportError:
        return {
            "success": False,
            "error": "LiteLLM not installed. Run: uv pip install litellm"
        }

    # Check API key
    api_key = check_api_key()
    if not api_key:
        return {
            "success": False,
            "error": "OpenRouter API key not configured"
        }

    if verbose:
        print(f"Model: {model}", file=sys.stderr)
        print(f"Query: {query}", file=sys.stderr)
        print(f"Max tokens: {max_tokens}", file=sys.stderr)
        print(f"Temperature: {temperature}", file=sys.stderr)
        print("", file=sys.stderr)

    try:
        # Perform the search using LiteLLM
        response = completion(
            model=model,
            messages=[{
                "role": "user",
                "content": query
            }],
            max_tokens=max_tokens,
            temperature=temperature
        )

        # Extract the response
        result = {
            "success": True,
            "query": query,
            "model": model,
            "answer": response.choices[0].message.content,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }

        citations = _collect_citations(response)
        if citations:
            result["citations"] = citations

        return result

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "model": model
        }


def _collect_citations(response: Any) -> List[Dict[str, str]]:
    """Gather source URLs from wherever LiteLLM/OpenRouter put them.

    OpenRouter returns Perplexity sources as OpenAI-style `url_citation`
    annotations on the message, and may also pass through Perplexity's top-level
    `citations` (URL strings) and `search_results` lists, which LiteLLM exposes as
    attributes on the response. Deduplicated by URL; empty if none were returned.
    """
    found: List[Dict[str, str]] = []
    seen = set()

    def add(url: Optional[str], title: Optional[str] = "") -> None:
        if url and url not in seen:
            seen.add(url)
            found.append({"url": url, "title": title or ""})

    def field(obj: Any, name: str) -> Any:
        return obj.get(name) if isinstance(obj, dict) else getattr(obj, name, None)

    message = response.choices[0].message
    for ann in field(message, "annotations") or []:
        cite = field(ann, "url_citation") or ann
        add(field(cite, "url"), field(cite, "title"))
    for item in getattr(response, "search_results", None) or []:
        add(field(item, "url"), field(item, "title"))
    for item in getattr(response, "citations", None) or []:
        if isinstance(item, str):
            add(item)
        else:
            add(field(item, "url"), field(item, "title"))
    return found


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Perform AI-powered web searches using Perplexity via LiteLLM and OpenRouter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic search
  python perplexity_search.py "What are the latest developments in CRISPR?"

  # Use Sonar Pro Search for deeper analysis
  python perplexity_search.py "Compare mRNA and viral vector vaccines" --model sonar-pro-search

  # Use Sonar Reasoning Pro for multi-step reasoning
  python perplexity_search.py "Explain quantum entanglement" --model sonar-reasoning-pro

  # Save output to file
  python perplexity_search.py "COVID-19 vaccine efficacy studies" --output results.json

  # Verbose mode
  python perplexity_search.py "Machine learning trends 2024" --verbose

Available Models:
  - sonar-pro (default): General-purpose search with good balance
  - sonar-pro-search: Most advanced agentic search with multi-step reasoning
  - sonar: Standard model for basic searches
  - sonar-reasoning-pro: Search with explicit reasoning
        """
    )

    parser.add_argument(
        "query",
        nargs="?",
        help="The search query (not needed with --check-setup)"
    )

    parser.add_argument(
        "--model",
        default=os.environ.get("DEFAULT_MODEL", "sonar-pro"),
        choices=MODELS,
        help="Perplexity model to use (default: sonar-pro, or $DEFAULT_MODEL)"
    )

    parser.add_argument(
        "--max-tokens",
        type=int,
        default=int(os.environ.get("DEFAULT_MAX_TOKENS", "4000")),
        help="Maximum tokens in response (default: 4000, or $DEFAULT_MAX_TOKENS)"
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=float(os.environ.get("DEFAULT_TEMPERATURE", "0.2")),
        help="Response temperature 0.0-1.0 (default: 0.2, or $DEFAULT_TEMPERATURE)"
    )

    parser.add_argument(
        "--output",
        help="Save results to JSON file"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed information"
    )

    parser.add_argument(
        "--check-setup",
        action="store_true",
        help="Check if dependencies and API key are configured"
    )

    args = parser.parse_args()
    # argparse does not validate defaults, so a stale $DEFAULT_MODEL (e.g. the
    # retired sonar-reasoning) would otherwise reach OpenRouter and fail there.
    if args.model not in MODELS:
        parser.error(f"unsupported model {args.model!r} (from $DEFAULT_MODEL?); choose from {MODELS}")

    # Check setup if requested
    if args.check_setup:
        print("Checking setup...")
        deps_ok = check_dependencies()
        api_key_ok = check_api_key() is not None

        if deps_ok and api_key_ok:
            print("\n✓ Setup complete! Ready to search.")
            return 0
        else:
            print("\n✗ Setup incomplete. Please fix the issues above.")
            return 1

    if not args.query:
        parser.error("a search query is required (or use --check-setup)")

    # Check dependencies
    if not check_dependencies():
        return 1

    # Prepend openrouter/ to model name if not already present
    model = args.model
    if not model.startswith("openrouter/"):
        model = f"openrouter/perplexity/{model}"

    # Perform the search
    result = search_with_perplexity(
        query=args.query,
        model=model,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        verbose=args.verbose
    )

    # Handle results
    if not result["success"]:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1

    # Print answer
    print("\n" + "="*80)
    print("ANSWER")
    print("="*80)
    print(result["answer"])
    print("="*80)

    # Print usage stats if verbose
    if args.verbose:
        print(f"\nUsage:", file=sys.stderr)
        print(f"  Prompt tokens: {result['usage']['prompt_tokens']}", file=sys.stderr)
        print(f"  Completion tokens: {result['usage']['completion_tokens']}", file=sys.stderr)
        print(f"  Total tokens: {result['usage']['total_tokens']}", file=sys.stderr)

    # Save to file if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n✓ Results saved to {args.output}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
