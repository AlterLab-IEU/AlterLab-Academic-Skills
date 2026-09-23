#!/usr/bin/env python3
"""
OpenAlex API Client with throttling and error handling.

Provides a robust client for interacting with the OpenAlex API with:
- Client-side request spacing (hard ceiling is 100 requests/second)
- Exponential backoff retry logic on short 429/403/5xx throttles
- Cursor pagination (page-based paging stops at 10,000 results)
- Batch operations support

OpenAlex runs on a daily cost budget: keyless calls share $0.10/day per IP
address; a free API key from openalex.org/settings/api gives your own $1/day.
Set OPENALEX_API_KEY (or pass api_key=); the key is sent as an
"Authorization: Bearer" header so it never appears in URLs or logs. The old
mailto "polite pool" was retired in Feb 2026 — mailto is ignored.
per_page is capped at 100 (200 is deprecated legacy).
"""

import os
import random
import time
import requests
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

MAX_PER_PAGE = 100  # OpenAlex maximum; per_page=200 is deprecated and slated for removal
MAX_OR_VALUES = 100  # values allowed in one OR (|) filter
BUDGET_EXHAUSTED_RETRY_AFTER_S = 120  # a longer Retry-After means the daily budget is spent


def _retry_after_seconds(response: requests.Response) -> int:
    try:
        return int(float(response.headers.get("Retry-After", 0)))
    except ValueError:
        return 0


class OpenAlexClient:
    """Client for OpenAlex API with rate limiting and error handling."""

    BASE_URL = "https://api.openalex.org"

    def __init__(
        self,
        api_key: Optional[str] = None,
        email: Optional[str] = None,
        requests_per_second: int = 10,
    ):
        """
        Initialize OpenAlex client.

        Args:
            api_key: Free OpenAlex API key (openalex.org/settings/api); defaults to
                the OPENALEX_API_KEY environment variable. Gives your own $1/day
                instead of the $0.10/day keyless budget shared per IP.
            email: Deprecated no-op, kept for backward compatibility — OpenAlex
                has ignored mailto since the polite pool was retired (Feb 2026).
            requests_per_second: Client-side request spacing cap (default: 10;
                the API rejects more than 100/s).
        """
        self.api_key = api_key or os.environ.get("OPENALEX_API_KEY")
        self.email = email
        self.requests_per_second = requests_per_second
        self.min_delay = 1.0 / requests_per_second
        self.last_request_time = 0

    def auth_headers(self) -> Dict[str, str]:
        """Return the Authorization header for direct requests (empty when keyless)."""
        return {'Authorization': f'Bearer {self.api_key}'} if self.api_key else {}

    def auth_params(self) -> Dict[str, str]:
        """Query-param form of the key (?api_key=), for tools that cannot set headers.

        Prefer auth_headers(): a key in the URL ends up in logs and error messages.
        """
        return {'api_key': self.api_key} if self.api_key else {}

    def _rate_limit(self):
        """Ensure requests don't exceed rate limit."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_delay:
            time.sleep(self.min_delay - time_since_last)
        self.last_request_time = time.time()

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        max_retries: int = 5
    ) -> Dict[str, Any]:
        """
        Make API request with retry logic.

        Args:
            endpoint: API endpoint (e.g., '/works', '/authors')
            params: Query parameters
            max_retries: Maximum number of retry attempts

        Returns:
            JSON response as dictionary
        """
        if params is None:
            params = {}

        url = urljoin(self.BASE_URL, endpoint)

        for attempt in range(max_retries):
            try:
                self._rate_limit()
                response = requests.get(url, params=params, headers=self.auth_headers(), timeout=30)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code in (429, 403):
                    retry_after = _retry_after_seconds(response)
                    if response.status_code == 429 and retry_after > BUDGET_EXHAUSTED_RETRY_AFTER_S:
                        # Daily budget spent: retrying cannot succeed before the reset.
                        raise RuntimeError(
                            f"OpenAlex daily budget exhausted (resets in {retry_after}s, at "
                            "midnight UTC). Keyless calls share $0.10/day per IP address; pass "
                            "api_key= (free at openalex.org/settings/api) for your own $1/day."
                        )
                    # Short throttle (e.g. >100 requests/second) or "slow down" (403)
                    wait_time = max(2 ** attempt, retry_after)
                    print(f"Throttled ({response.status_code}). Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                elif response.status_code >= 500:
                    # Server error
                    wait_time = 2 ** attempt
                    print(f"Server error. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    # Other error - don't retry
                    response.raise_for_status()

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Request timeout. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    raise

        raise Exception(f"Failed after {max_retries} retries")

    def search_works(
        self,
        search: Optional[str] = None,
        filter_params: Optional[Dict] = None,
        per_page: int = MAX_PER_PAGE,
        page: int = 1,
        sort: Optional[str] = None,
        select: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search works with filters.

        Args:
            search: Full-text search query
            filter_params: Dictionary of filter parameters
            per_page: Results per page (max: 100)
            page: Page number
            sort: Sort parameter (e.g., 'cited_by_count:desc')
            select: List of fields to return

        Returns:
            API response with meta and results
        """
        params = {
            'per_page': min(per_page, MAX_PER_PAGE),
            'page': page
        }

        if search:
            params['search'] = search

        if filter_params:
            filter_str = ','.join([f"{k}:{v}" for k, v in filter_params.items()])
            params['filter'] = filter_str

        if sort:
            params['sort'] = sort

        if select:
            params['select'] = ','.join(select)

        return self._make_request('/works', params)

    def get_entity(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """
        Get single entity by ID.

        Args:
            entity_type: Type of entity ('works', 'authors', 'institutions', etc.)
            entity_id: OpenAlex ID or external ID (DOI, ORCID, etc.)

        Returns:
            Entity object
        """
        endpoint = f"/{entity_type}/{entity_id}"
        return self._make_request(endpoint)

    def batch_lookup(
        self,
        entity_type: str,
        ids: List[str],
        id_field: str = 'openalex_id'
    ) -> List[Dict[str, Any]]:
        """
        Look up multiple entities by ID efficiently.

        Args:
            entity_type: Type of entity ('works', 'authors', etc.)
            ids: List of IDs (sent in batches of 100, the OR-filter limit)
            id_field: ID field name ('openalex_id', 'doi', 'orcid', etc.)

        Returns:
            List of entity objects
        """
        all_results = []

        for i in range(0, len(ids), MAX_OR_VALUES):
            batch = ids[i:i + MAX_OR_VALUES]
            filter_value = '|'.join(batch)

            params = {
                'filter': f"{id_field}:{filter_value}",
                'per_page': MAX_PER_PAGE
            }

            response = self._make_request(f"/{entity_type}", params)
            all_results.extend(response.get('results', []))

        return all_results

    def paginate_all(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Paginate through all results with cursor paging.

        Page-based paging stops at 10,000 results, so this follows
        meta.next_cursor instead. For whole-corpus pulls use the OpenAlex
        snapshot rather than the API.

        Args:
            endpoint: API endpoint
            params: Query parameters
            max_results: Maximum number of results to retrieve (None for all)

        Returns:
            List of all results
        """
        params = dict(params or {})
        params.pop('per-page', None)
        params.pop('page', None)
        params['per_page'] = MAX_PER_PAGE
        params['cursor'] = '*'

        all_results = []

        while True:
            response = self._make_request(endpoint, params)
            results = response.get('results', [])
            all_results.extend(results)

            if max_results and len(all_results) >= max_results:
                return all_results[:max_results]

            next_cursor = response.get('meta', {}).get('next_cursor')
            if not results or not next_cursor:
                break
            params['cursor'] = next_cursor

        return all_results

    def sample_works(
        self,
        sample_size: int,
        seed: Optional[int] = None,
        filter_params: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Get random sample of works.

        Args:
            sample_size: Number of samples to retrieve
            seed: Random seed for reproducibility
            filter_params: Optional filters to apply

        Returns:
            List of sampled works
        """
        filter_str = None
        if filter_params:
            filter_str = ','.join([f"{k}:{v}" for k, v in filter_params.items()])
        if seed is None:
            # Paging through a sample needs a fixed seed, or each page is a new draw.
            seed = random.randrange(1_000_000)

        def fetch_sample(n: int, seed_value: int) -> List[Dict[str, Any]]:
            """One sample of up to 10,000 works, paged per_page at a time."""
            params = {'sample': n, 'seed': seed_value, 'per_page': MAX_PER_PAGE, 'page': 1}
            if filter_str:
                params['filter'] = filter_str
            out: List[Dict[str, Any]] = []
            while len(out) < n:
                results = self._make_request('/works', params).get('results', [])
                if not results:
                    break
                out.extend(results)
                params['page'] += 1
            return out[:n]

        if sample_size <= 10000:
            return fetch_sample(sample_size, seed)

        # Larger samples: several seeded draws (API max 10,000 each), deduplicated.
        all_samples: List[Dict[str, Any]] = []
        seen_ids = set()
        for i in range((sample_size // 10000) + 1):
            remaining = sample_size - len(all_samples)
            for result in fetch_sample(min(10000, remaining), seed + i):
                work_id = result.get('id')
                if work_id not in seen_ids:
                    seen_ids.add(work_id)
                    all_samples.append(result)
            if len(all_samples) >= sample_size:
                break
        return all_samples[:sample_size]

    def group_by(
        self,
        entity_type: str,
        group_field: str,
        filter_params: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Aggregate results by field.

        Args:
            entity_type: Type of entity ('works', 'authors', etc.)
            group_field: Field to group by
            filter_params: Optional filters

        Returns:
            List of grouped results with counts
        """
        params = {
            'group_by': group_field
        }

        if filter_params:
            filter_str = ','.join([f"{k}:{v}" for k, v in filter_params.items()])
            params['filter'] = filter_str

        response = self._make_request(f"/{entity_type}", params)
        return response.get('group_by', [])


if __name__ == "__main__":
    # Example usage. Reads OPENALEX_API_KEY for the $1/day budget; keyless also works.
    client = OpenAlexClient()

    # Search for works about machine learning
    results = client.search_works(
        search="machine learning",
        filter_params={"publication_year": "2023"},
        per_page=10
    )

    print(f"Found {results['meta']['count']} works")
    for work in results['results']:
        print(f"- {work['title']}")
