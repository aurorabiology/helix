import requests
import time
import threading
import asyncio
import logging
from typing import Any, Dict, Optional, List
from helixlang.runtime.value_types import Protein, Genome

logger = logging.getLogger(__name__)

class APIError(Exception):
    pass

class RateLimitError(APIError):
    pass

class BaseConnector:
    """
    Abstract base class for database connectors.
    """
    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: int = 10):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.lock = threading.Lock()  # for rate limiting
        self.last_request_time = 0
        self.min_interval = 0.3  # seconds between requests

    def _wait_for_rate_limit(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_request_time
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
            self.last_request_time = time.time()

    def _request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict:
        self._wait_for_rate_limit()
        headers = {}
        if self.api_key:
            headers['Authorization'] = f"Bearer {self.api_key}"

        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.get(url, headers=headers, params=params, timeout=self.timeout)
            if response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise APIError(str(e))

    def fetch(self, query: str) -> Any:
        """
        To be implemented by subclasses for specific queries.
        """
        raise NotImplementedError


class NCBIConnector(BaseConnector):
    def __init__(self, api_key=None):
        super().__init__("https://api.ncbi.nlm.nih.gov", api_key)

    def fetch_protein_by_accession(self, accession: str) -> Protein:
        # Example endpoint and params; actual NCBI endpoints may differ
        endpoint = "protein/v1/accession"
        params = {"accession": accession}
        data = self._request(endpoint, params)
        protein = self._parse_protein(data)
        return protein

    def _parse_protein(self, data: Dict) -> Protein:
        # Transform raw JSON to HelixLang Protein object
        # Example - customize with actual fields
        return Protein(
            sequence=data.get('sequence', ''),
            structure=data.get('structure', {}),
            annotations=data.get('annotations', {})
        )


class CacheManager:
    def __init__(self):
        self.cache = {}
        self.lock = threading.Lock()

    def get(self, key):
        with self.lock:
            return self.cache.get(key)

    def set(self, key, value):
        with self.lock:
            self.cache[key] = value

class APIConnector:
    def __init__(self, connectors: Dict[str, BaseConnector]):
        self.connectors = connectors
        self.cache = CacheManager()

    def fetch_protein(self, accession: str, db: str = "NCBI") -> Protein:
        cache_key = f"{db}_protein_{accession}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        connector = self.connectors.get(db)
        if not connector:
            raise ValueError(f"Database {db} not supported")

        protein = connector.fetch_protein_by_accession(accession)
        self.cache.set(cache_key, protein)
        return protein

    async def fetch_protein_async(self, accession: str, db: str = "NCBI") -> Protein:
        # Example async wrapper (using asyncio.to_thread for sync requests)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.fetch_protein, accession, db)

