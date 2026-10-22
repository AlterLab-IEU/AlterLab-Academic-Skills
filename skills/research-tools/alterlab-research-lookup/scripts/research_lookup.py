#!/usr/bin/env python3
"""
Research Information Lookup Tool

Routes research queries to the best backend. No API key is needed:
  - scholarly (keyless, stdlib): Crossref, Europe PMC, arXiv, Semantic Scholar and OpenAlex
    index records merged by DOI (scripts/scholarly_backend.py). Used for academic queries
    when OPENROUTER_API_KEY is not set, and for every query when no key is set.
  - Parallel Chat API (core model): general research, when PARALLEL_API_KEY is set
  - Perplexity sonar-pro-search (via OpenRouter): academic paper searches, when
    OPENROUTER_API_KEY is set

Optional environment variables (each only adds a paid backend):
  PARALLEL_API_KEY    - Parallel Chat API
  OPENROUTER_API_KEY  - Perplexity sonar-pro-search via OpenRouter

General web questions (news, statistics, market data, documentation) are not answered by the
keyless scholarly backend; the skill does those with Claude's WebSearch and WebFetch.
A forced keyed backend whose key is missing exits non-zero; it never answers from another.
"""

import os
import sys
import json
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scholarly_backend  # noqa: E402  (stdlib-only sibling module)

KEYLESS_HINT = ("Keyless alternatives: --force-backend scholarly (index records with DOIs), or "
                "do the lookup with WebSearch/WebFetch as SKILL.md describes.")


class ResearchLookup:
    """Research information lookup with intelligent backend routing.

    Routes queries to the Parallel Chat API (default) or Perplexity
    sonar-pro-search (academic paper searches only).
    """

    ACADEMIC_KEYWORDS = [
        "find papers", "find paper", "find articles", "find article",
        "cite ", "citation", "citations for",
        "doi ", "doi:", "pubmed", "pmid",
        "journal article", "peer-reviewed",
        "systematic review", "meta-analysis",
        "literature search", "literature on",
        "academic papers", "academic paper",
        "research papers on", "research paper on",
        "published studies", "published study",
        "scholarly", "scholar",
        "arxiv", "preprint",
        "foundational papers", "seminal papers", "landmark papers",
        "highly cited", "most cited",
    ]

    PARALLEL_SYSTEM_PROMPT = (
        "You are a deep research analyst. Provide a comprehensive, well-cited "
        "research report on the user's topic. Include:\n"
        "- Key findings with specific data, statistics, and quantitative evidence\n"
        "- Detailed analysis organized by themes\n"
        "- Multiple authoritative sources cited inline\n"
        "- Methodologies and implications where relevant\n"
        "- Future outlook and research gaps\n"
        "Use markdown formatting with clear section headers. "
        "Prioritize authoritative and recent sources."
    )

    # The OpenAI SDK appends /chat/completions, giving the documented
    # POST /v1beta/chat/completions endpoint of Parallel's Chat API (Beta).
    CHAT_BASE_URL = "https://api.parallel.ai/v1beta"

    def __init__(self, force_backend: Optional[str] = None, limit: int = 10,
                 rank: str = "auto", terms: Optional[str] = None):
        """Initialize the research lookup tool. No API key is required.

        Args:
            force_backend: Force a specific backend ('scholarly', 'parallel' or 'perplexity').
                          If None, backend is auto-selected based on query content and keys.
            limit, rank, terms: passed to the keyless scholarly backend.
        """
        self.force_backend = force_backend
        self.parallel_available = bool(os.getenv("PARALLEL_API_KEY"))
        self.perplexity_available = bool(os.getenv("OPENROUTER_API_KEY"))
        self.limit, self.rank, self.terms = limit, rank, terms

    def is_academic(self, query: str) -> bool:
        query_lower = query.lower()
        return any(kw in query_lower for kw in self.ACADEMIC_KEYWORDS)

    def _select_backend(self, query: str) -> str:
        """Select the best backend for a query."""
        if self.force_backend:
            # A forced backend is the user's explicit choice: refuse rather than quietly
            # answer from another one when its key is missing.
            if self.force_backend == "scholarly":
                return "scholarly"
            if self.force_backend == "perplexity":
                if self.perplexity_available:
                    return "perplexity"
                raise ValueError("--force-backend perplexity needs OPENROUTER_API_KEY; "
                                 "not falling back to another backend. " + KEYLESS_HINT)
            if self.force_backend == "parallel":
                if self.parallel_available:
                    return "parallel"
                raise ValueError("--force-backend parallel needs PARALLEL_API_KEY; "
                                 "not falling back to another backend. " + KEYLESS_HINT)

        if self.is_academic(query):
            return "perplexity" if self.perplexity_available else "scholarly"

        if self.parallel_available:
            return "parallel"

        if self.perplexity_available:
            return "perplexity"

        return "scholarly"

    # ------------------------------------------------------------------
    # Parallel Chat API backend
    # ------------------------------------------------------------------

    def _get_chat_client(self):
        """Lazy-load and cache the OpenAI client for Parallel Chat API."""
        if not hasattr(self, "_chat_client"):
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError(
                    "The 'openai' package is required for Parallel Chat API.\n"
                    "Install it with: uv pip install openai"
                )
            self._chat_client = OpenAI(
                api_key=os.getenv("PARALLEL_API_KEY"),
                base_url=self.CHAT_BASE_URL,
            )
        return self._chat_client

    def _parallel_lookup(self, query: str) -> Dict[str, Any]:
        """Run research via the Parallel Chat API (core model)."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        model = "core"

        try:
            client = self._get_chat_client()

            print(f"[Research] Parallel Chat API (model={model})...", file=sys.stderr)

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": self.PARALLEL_SYSTEM_PROMPT},
                    {"role": "user", "content": query},
                ],
                stream=False,
            )

            content = ""
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content or ""

            api_citations = self._extract_basis_citations(response)
            text_citations = self._extract_citations_from_text(content)

            return {
                "success": True,
                "query": query,
                "response": content,
                "citations": api_citations + text_citations,
                "sources": api_citations,
                "timestamp": timestamp,
                "backend": "parallel",
                "model": f"parallel-chat/{model}",
            }

        except Exception as e:
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "timestamp": timestamp,
                "backend": "parallel",
                "model": f"parallel-chat/{model}",
            }

    def _extract_basis_citations(self, response) -> List[Dict[str, str]]:
        """Extract citation sources from the Chat API research basis."""
        citations = []
        basis = getattr(response, "basis", None)
        if not basis:
            return citations

        seen_urls = set()
        if isinstance(basis, list):
            for item in basis:
                cits = (
                    item.get("citations", []) if isinstance(item, dict)
                    else getattr(item, "citations", None) or []
                )
                for cit in cits:
                    url = cit.get("url", "") if isinstance(cit, dict) else getattr(cit, "url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        title = cit.get("title", "") if isinstance(cit, dict) else getattr(cit, "title", "")
                        excerpts = cit.get("excerpts", []) if isinstance(cit, dict) else getattr(cit, "excerpts", [])
                        citations.append({
                            "type": "source",
                            "url": url,
                            "title": title,
                            "excerpts": excerpts,
                        })

        return citations

    # ------------------------------------------------------------------
    # Perplexity academic search backend
    # ------------------------------------------------------------------

    def _perplexity_lookup(self, query: str) -> Dict[str, Any]:
        """Run academic search via Perplexity sonar-pro-search through OpenRouter."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        api_key = os.getenv("OPENROUTER_API_KEY")
        model = "perplexity/sonar-pro-search"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://scientific-writer.local",
            "X-Title": "Scientific Writer Research Tool",
        }

        research_prompt = self._format_academic_prompt(query)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an academic research assistant specializing in finding "
                    "HIGH-IMPACT, INFLUENTIAL research.\n\n"
                    "QUALITY PRIORITIZATION (CRITICAL):\n"
                    "- ALWAYS prefer highly-cited papers over obscure publications\n"
                    "- ALWAYS prioritize Tier-1 venues: Nature, Science, Cell, NEJM, Lancet, JAMA, PNAS\n"
                    "- ALWAYS prefer papers from established researchers\n"
                    "- Include citation counts when known (e.g., 'cited 500+ times')\n"
                    "- Quality matters more than quantity\n\n"
                    "VENUE HIERARCHY:\n"
                    "1. Nature/Science/Cell family, NEJM, Lancet, JAMA (highest)\n"
                    "2. High-impact specialized journals (IF>10), top conferences (NeurIPS, ICML, ICLR)\n"
                    "3. Respected field-specific journals (IF 5-10)\n"
                    "4. Other peer-reviewed sources (only if no better option)\n\n"
                    "Focus exclusively on scholarly sources. Prioritize recent literature (2020-2026) "
                    "and provide complete citations with DOIs."
                ),
            },
            {"role": "user", "content": research_prompt},
        ]

        data = {
            "model": model,
            "messages": messages,
            "max_tokens": 8000,
            "temperature": 0.1,
            # Perplexity-specific academic filter; OpenRouter may not forward it,
            # so treat academic-only sourcing as best-effort.
            "search_mode": "academic",
            # OpenRouter's documented way to request a larger search context.
            "web_search_options": {"search_context_size": "high"},
        }

        try:
            import requests  # only this keyed backend needs it

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=90,
            )
            response.raise_for_status()
            resp_json = response.json()

            if "choices" in resp_json and len(resp_json["choices"]) > 0:
                choice = resp_json["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    content = choice["message"]["content"]

                    api_citations = self._extract_api_citations(resp_json, choice)
                    text_citations = self._extract_citations_from_text(content)
                    citations = api_citations + text_citations

                    return {
                        "success": True,
                        "query": query,
                        "response": content,
                        "citations": citations,
                        "sources": api_citations,
                        "timestamp": timestamp,
                        "backend": "perplexity",
                        "model": model,
                        "usage": resp_json.get("usage", {}),
                    }
                else:
                    raise Exception("Invalid response format from API")
            else:
                raise Exception("No response choices received from API")

        except Exception as e:
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "timestamp": timestamp,
                "backend": "perplexity",
                "model": model,
            }

    # ------------------------------------------------------------------
    # Keyless scholarly backend
    # ------------------------------------------------------------------

    def _scholarly_lookup(self, query: str) -> Dict[str, Any]:
        """Index records (no synthesis) from Crossref, Europe PMC, arXiv, S2, OpenAlex."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        res = scholarly_backend.search(query, limit=self.limit, terms=self.terms, rank=self.rank)
        model = "keyless/" + "+".join(s for s in res["queried"] if s not in res["errors"])
        if not res["records"]:
            why = ("every source failed: " + "; ".join(f"{k}: {v}" for k, v in res["errors"].items())
                   if len(res["errors"]) == len(res["queried"]) else
                   f"no records matched \"{res['terms']}\"; rephrase or pass --terms")
            return {"success": False, "query": query, "error": why, "timestamp": timestamp,
                    "backend": "scholarly", "model": model}
        sources = [{
            "type": "source", "title": r["title"], "date": str(r["year"] or ""),
            "url": r["url"] or (f"https://doi.org/{r['doi']}" if r["doi"] else ""),
            "doi": r["doi"], "snippet": r["abstract"][:300], "cited_by": r["cited_by"],
            "venue": r["venue"], "authors": r["authors"],
        } for r in res["records"]]
        citations = [{"type": "doi", "doi": r["doi"], "url": f"https://doi.org/{r['doi']}"}
                     for r in res["records"] if r["doi"]]
        return {"success": True, "query": query, "response": scholarly_backend.to_markdown(res),
                "citations": citations, "sources": sources, "timestamp": timestamp,
                "backend": "scholarly", "model": model, "search_terms": res["terms"],
                "rank": res["rank"], "source_errors": res["errors"]}

    # ------------------------------------------------------------------
    # Shared utilities
    # ------------------------------------------------------------------

    def _format_academic_prompt(self, query: str) -> str:
        """Format a query for academic research results via Perplexity."""
        return f"""You are an expert research assistant. Please provide comprehensive, accurate research information for the following query: "{query}"

IMPORTANT INSTRUCTIONS:
1. Focus on ACADEMIC and SCIENTIFIC sources (peer-reviewed papers, reputable journals, institutional research)
2. Include RECENT information (prioritize 2020-2026 publications)
3. Provide COMPLETE citations with authors, title, journal/conference, year, and DOI when available
4. Structure your response with clear sections and proper attribution
5. Be comprehensive but concise - aim for 800-1200 words
6. Include key findings, methodologies, and implications when relevant
7. Note any controversies, limitations, or conflicting evidence

PAPER QUALITY PRIORITIZATION (CRITICAL):
8. ALWAYS prioritize HIGHLY-CITED papers over obscure publications
9. ALWAYS prioritize papers from TOP-TIER VENUES (Nature, Science, Cell, NEJM, Lancet, JAMA, PNAS)
10. PREFER papers from ESTABLISHED, REPUTABLE AUTHORS
11. For EACH citation include when available: citation count, venue tier, author credentials
12. PRIORITIZE papers that DIRECTLY address the research question

RESPONSE FORMAT:
- Start with a brief summary (2-3 sentences)
- Present key findings and studies in organized sections
- Rank papers by impact: most influential/cited first
- End with future directions or research gaps if applicable
- Include 5-8 high-quality citations

Remember: Quality over quantity. Prioritize influential, highly-cited papers from prestigious venues."""

    def _extract_api_citations(self, response: Dict[str, Any], choice: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract citations from Perplexity API response fields."""
        citations = []

        search_results = (
            response.get("search_results")
            or choice.get("search_results")
            or choice.get("message", {}).get("search_results")
            or []
        )

        for result in search_results:
            citation = {
                "type": "source",
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "date": result.get("date", ""),
            }
            if result.get("snippet"):
                citation["snippet"] = result["snippet"]
            citations.append(citation)

        # OpenRouter normalizes web sources to OpenAI-style url_citation annotations.
        for ann in choice.get("message", {}).get("annotations") or []:
            cite = ann.get("url_citation", ann) if isinstance(ann, dict) else {}
            if cite.get("url"):
                citations.append({
                    "type": "source",
                    "url": cite["url"],
                    "title": cite.get("title", ""),
                    "date": "",
                })

        legacy_citations = (
            response.get("citations")
            or choice.get("citations")
            or choice.get("message", {}).get("citations")
            or []
        )

        for url in legacy_citations:
            if isinstance(url, str):
                citations.append({"type": "source", "url": url, "title": "", "date": ""})
            elif isinstance(url, dict):
                citations.append({
                    "type": "source",
                    "url": url.get("url", ""),
                    "title": url.get("title", ""),
                    "date": url.get("date", ""),
                })

        # The same source can arrive via several fields; keep the first (richest) entry.
        deduped: List[Dict[str, str]] = []
        seen = set()
        for cit in citations:
            if cit["url"] and cit["url"] not in seen:
                seen.add(cit["url"])
                deduped.append(cit)
        return deduped

    def _extract_citations_from_text(self, text: str) -> List[Dict[str, str]]:
        """Extract DOIs and academic URLs from response text as fallback."""
        citations = []

        doi_pattern = r'(?:doi[:\s]*|https?://(?:dx\.)?doi\.org/)(10\.[0-9]{4,}/[^\s\)\]\,\[\<\>]+)'
        doi_matches = re.findall(doi_pattern, text, re.IGNORECASE)
        seen_dois = set()

        for doi in doi_matches:
            doi_clean = doi.strip().rstrip(".,;:)]")
            if doi_clean and doi_clean not in seen_dois:
                seen_dois.add(doi_clean)
                citations.append({
                    "type": "doi",
                    "doi": doi_clean,
                    "url": f"https://doi.org/{doi_clean}",
                })

        url_pattern = (
            r'https?://[^\s\)\]\,\<\>\"\']+(?:arxiv\.org|pubmed|ncbi\.nlm\.nih\.gov|'
            r'nature\.com|science\.org|wiley\.com|springer\.com|ieee\.org|acm\.org)'
            r'[^\s\)\]\,\<\>\"\']*'
        )
        url_matches = re.findall(url_pattern, text, re.IGNORECASE)
        seen_urls = set()

        for url in url_matches:
            url_clean = url.rstrip(".")
            if url_clean not in seen_urls:
                seen_urls.add(url_clean)
                citations.append({"type": "url", "url": url_clean})

        return citations

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def lookup(self, query: str) -> Dict[str, Any]:
        """Perform a research lookup, routing to the best backend.

        Academic queries go to Perplexity when OPENROUTER_API_KEY is set, else to the keyless
        scholarly backend. Other queries go to Parallel (PARALLEL_API_KEY), then Perplexity,
        then the scholarly backend, with a stderr note that web content needs WebSearch.
        """
        backend = self._select_backend(query)
        print(f"[Research] Backend: {backend} | Query: {query[:80]}...", file=sys.stderr)

        if backend == "parallel":
            return self._parallel_lookup(query)
        if backend == "perplexity":
            return self._perplexity_lookup(query)
        if not self.force_backend:
            if not (self.parallel_available or self.perplexity_available):
                print("[Research] No PARALLEL_API_KEY / OPENROUTER_API_KEY set: using the keyless "
                      "scholarly backend (Crossref, Europe PMC, arXiv, Semantic Scholar, OpenAlex).",
                      file=sys.stderr)
            if not self.is_academic(query):
                print("[Research] Note: this is not a paper search. The scholarly backend returns "
                      "papers only; for news, statistics, market data or web pages, do this "
                      "lookup with WebSearch/WebFetch (SKILL.md, keyless web lookup).",
                      file=sys.stderr)
        return self._scholarly_lookup(query)

    def batch_lookup(self, queries: List[str], delay: float = 1.0) -> List[Dict[str, Any]]:
        """Perform multiple research lookups with delay between requests."""
        results = []
        for i, query in enumerate(queries):
            if i > 0 and delay > 0:
                time.sleep(delay)
            result = self.lookup(query)
            results.append(result)
            print(f"[Research] Completed query {i+1}/{len(queries)}: {query[:50]}...", file=sys.stderr)
        return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    """Command-line interface for the research lookup tool."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Research Information Lookup Tool (Parallel Chat API + Perplexity)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Academic paper search: keyless scholarly backend (Perplexity if OPENROUTER_API_KEY is set)
  python research_lookup.py "find papers on CRISPR off-target effects" -o sources/papers_x.md

  # Exact search terms and ordering for the scholarly backend
  python research_lookup.py "find papers" --terms '"testing effect" OR "retrieval practice"' --rank cited

  # General research (Parallel Chat API when PARALLEL_API_KEY is set; without keys the
  # scholarly backend answers with papers only -- use WebSearch/WebFetch for web content)
  python research_lookup.py "latest advances in quantum computing 2025"

  # Force a specific backend (a keyed one exits 1 when its key is missing)
  python research_lookup.py "topic" --force-backend scholarly
  python research_lookup.py "topic" --force-backend parallel
  python research_lookup.py "topic" --force-backend perplexity

  # JSON output
  python research_lookup.py "topic" --json -o results.json
        """,
    )
    parser.add_argument("query", nargs="?", help="Research query to look up")
    parser.add_argument("--batch", nargs="+", help="Run multiple queries")
    parser.add_argument(
        "--force-backend",
        choices=["scholarly", "parallel", "perplexity"],
        help="Force a backend (default: auto-select). scholarly is keyless; parallel needs "
             "PARALLEL_API_KEY and perplexity needs OPENROUTER_API_KEY.",
    )
    parser.add_argument("--limit", type=int, default=10,
                        help="scholarly backend: records to return (default 10)")
    parser.add_argument("--rank", choices=["auto", "relevance", "cited"], default="auto",
                        help="scholarly backend: 'cited' surfaces influential work; auto uses "
                             "'relevance' for recent/latest/dated requests")
    parser.add_argument("--terms", help="scholarly backend: exact search terms (quotes, OR "
                                        "allowed) instead of the words left after routing words")
    parser.add_argument("-o", "--output", help="Write output to file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if not args.query and not args.batch:
        parser.print_help()
        return 1

    chunks: List[str] = []

    def write_output(text):
        chunks.append(text)

    try:
        research = ResearchLookup(force_backend=args.force_backend, limit=args.limit,
                                  rank=args.rank, terms=args.terms)

        if args.batch:
            print(f"Running batch research for {len(args.batch)} queries...", file=sys.stderr)
            results = research.batch_lookup(args.batch)
        else:
            print(f"Researching: {args.query}", file=sys.stderr)
            results = [research.lookup(args.query)]
    except Exception as e:
        # Nothing is written to -o, so a refused or failed run never leaves a stub in sources/.
        print(f"Error: {e}", file=sys.stderr)
        return 1

    failed = [r for r in results if not r["success"]]
    for r in failed:
        print(f"Error ({r.get('backend', '?')}): {r['error']}", file=sys.stderr)

    if args.json:
        write_output(json.dumps(results, indent=2, ensure_ascii=False, default=str))
    else:
        _render_text(results, write_output)

    text = "\n".join(chunks) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"[Research] Saved {len(results) - len(failed)}/{len(results)} result(s) to "
              f"{args.output}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 1 if failed else 0


def _render_text(results: List[Dict[str, Any]], write_output) -> None:
    """Human-readable output with Sources and Additional References sections."""
    for i, result in enumerate(results):
        if result["success"]:
            write_output(f"\n{'='*80}")
            write_output(f"Query {i+1}: {result['query']}")
            write_output(f"Timestamp: {result['timestamp']}")
            write_output(f"Backend: {result.get('backend', 'unknown')} | Model: {result.get('model', 'unknown')}")
            write_output(f"{'='*80}")
            write_output(result["response"])

            sources = result.get("sources", [])
            if sources:
                write_output(f"\nSources ({len(sources)}):")
                for j, source in enumerate(sources):
                    title = source.get("title", "Untitled")
                    url = source.get("url", "")
                    date = source.get("date", "")
                    date_str = f" ({date})" if date else ""
                    write_output(f"  [{j+1}] {title}{date_str}")
                    if url:
                        write_output(f"      {url}")

            citations = result.get("citations", [])
            text_citations = [c for c in citations if c.get("type") in ("doi", "url")]
            if text_citations:
                write_output(f"\nAdditional References ({len(text_citations)}):")
                for j, citation in enumerate(text_citations):
                    if citation.get("type") == "doi":
                        write_output(f"  [{j+1}] DOI: {citation.get('doi', '')} - {citation.get('url', '')}")
                    elif citation.get("type") == "url":
                        write_output(f"  [{j+1}] {citation.get('url', '')}")

            if result.get("usage"):
                write_output(f"\nUsage: {result['usage']}")
        else:
            write_output(f"\nError in query {i+1}: {result['error']}")


if __name__ == "__main__":
    sys.exit(main())
