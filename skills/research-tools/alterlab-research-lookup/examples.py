#!/usr/bin/env python3
"""
Example usage of the Research Lookup skill with automatic backend routing.

Demonstrates:
1. Automatic backend selection (Parallel Chat API vs Perplexity academic search)
2. Manual backend override via force_backend
3. Batch query processing

The router (ResearchLookup) sends academic-keyword queries to Perplexity
sonar-pro-search and everything else to the Parallel Chat API (core model).
"""

import os
import sys

# Import the main research lookup class from scripts/
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts"))
from research_lookup import ResearchLookup


def example_automatic_routing():
    """Demonstrate automatic backend routing."""
    print("=" * 80)
    print("EXAMPLE 1: Automatic Backend Routing")
    print("=" * 80)
    print()

    research = ResearchLookup()

    # General/market query -> Parallel Chat API (core model)
    query1 = "AI adoption in the healthcare industry: statistics and recent developments"
    print(f"Query: {query1}")
    print("Expected backend: parallel (general research)")
    result1 = research.lookup(query1)
    print(f"Actual backend: {result1.get('backend')} | model: {result1.get('model')}")
    print()

    # Academic-keyword query -> Perplexity sonar-pro-search
    query2 = "Find peer-reviewed papers on CRISPR off-target effects with DOIs"
    print(f"Query: {query2}")
    print("Expected backend: perplexity (academic paper search)")
    result2 = research.lookup(query2)
    print(f"Actual backend: {result2.get('backend')} | model: {result2.get('model')}")
    print()


def example_manual_override():
    """Demonstrate manual backend override via force_backend."""
    print("=" * 80)
    print("EXAMPLE 2: Manual Backend Override")
    print("=" * 80)
    print()

    query = "Global renewable energy market trends and projections"

    # Force Parallel even though no academic keywords are present (default would
    # already pick parallel here, but force_backend pins it explicitly).
    research_parallel = ResearchLookup(force_backend="parallel")
    print(f"Query: {query}")
    print("Forced backend: parallel")
    result = research_parallel.lookup(query)
    print(f"Backend used: {result.get('backend')} | model: {result.get('model')}")
    print()

    # Force Perplexity for the same query (overrides the non-academic heuristic).
    research_perplexity = ResearchLookup(force_backend="perplexity")
    print(f"Query: {query}")
    print("Forced backend: perplexity")
    result = research_perplexity.lookup(query)
    print(f"Backend used: {result.get('backend')} | model: {result.get('model')}")
    print()


def example_batch_queries():
    """Demonstrate batch query processing (mixed routing)."""
    print("=" * 80)
    print("EXAMPLE 3: Batch Query Processing")
    print("=" * 80)
    print()

    research = ResearchLookup()

    queries = [
        "Recent clinical trials for Alzheimer's disease",          # -> parallel
        "Find seminal papers on transformer attention mechanisms",  # -> perplexity
        "Statistical power analysis methods overview",              # -> parallel
    ]

    print("Processing batch queries (each auto-routed)...")
    print()

    results = research.batch_lookup(queries, delay=1.0)

    for i, result in enumerate(results):
        print(f"Query {i + 1}: {result['query'][:50]}...")
        print(f"  Backend: {result.get('backend')} | model: {result.get('model')}")
        print(f"  Success: {result.get('success')}")
        print()


def example_routing_preview():
    """Show backend routing decisions without making API calls."""
    print("=" * 80)
    print("ROUTING PREVIEW (No API calls required)")
    print("=" * 80)
    print()

    # _select_backend reads availability from env; stub both keys so it routes
    # purely on the query heuristic for this preview.
    os.environ.setdefault("PARALLEL_API_KEY", "test")
    os.environ.setdefault("OPENROUTER_API_KEY", "test")
    research = ResearchLookup()

    test_queries = [
        ("Recent CRISPR studies", "parallel"),
        ("Find papers on CRISPR off-target effects", "perplexity"),
        ("Compare mRNA vs traditional vaccines", "parallel"),
        ("Systematic review of immunotherapy in NSCLC", "perplexity"),
        ("Global AI market size 2025", "parallel"),
        ("Cite the original BERT paper", "perplexity"),
    ]

    for query, expected in test_queries:
        backend = research._select_backend(query)
        status = "OK " if backend == expected else "XX "
        print(f"{status} {backend:11s} <- '{query}'")
    print()


def main():
    """Run the routing preview; live examples require API keys."""
    if not (os.getenv("PARALLEL_API_KEY") or os.getenv("OPENROUTER_API_KEY")):
        print("Note: set PARALLEL_API_KEY and/or OPENROUTER_API_KEY to run live queries.")
        print("Showing routing decisions only (no API calls).")
        print()

    example_routing_preview()

    # Uncomment to run live examples (requires API keys):
    # example_automatic_routing()
    # example_manual_override()
    # example_batch_queries()


if __name__ == "__main__":
    main()
