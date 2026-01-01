"""Wikipedia API client for article extracts and geosearch."""

import asyncio
import logging
from typing import Literal
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

WIKIPEDIA_API = "https://{lang}.wikipedia.org/w/api.php"
# Wikipedia requires a descriptive User-Agent per their API policy
USER_AGENT = "TravelersAI/1.0 (https://github.com/travelers-ai; contact@travelers.ai)"


class WikipediaError(Exception):
    """Base exception for Wikipedia client errors."""

    pass


class WikipediaRateLimitError(WikipediaError):
    """Raised when rate limited by Wikipedia."""

    pass


class WikipediaClient:
    """Client for Wikipedia API.

    Features:
    - Connection pooling (reuses HTTP connections)
    - Automatic retries with exponential backoff
    - Proper User-Agent header (required by Wikipedia)
    - Error handling for different HTTP status codes
    """

    _shared_clients: dict[str, httpx.AsyncClient] = {}

    def __init__(self, timeout: float = 15.0, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries

    @classmethod
    def get_client(cls, language: str, timeout: float = 15.0) -> httpx.AsyncClient:
        """Get or create shared HTTP client for a language."""
        if language not in cls._shared_clients or cls._shared_clients[language].is_closed:
            cls._shared_clients[language] = httpx.AsyncClient(
                base_url=WIKIPEDIA_API.format(lang=language),
                timeout=httpx.Timeout(timeout, connect=10.0),
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/json",
                },
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
                follow_redirects=True,
            )
        return cls._shared_clients[language]

    @classmethod
    async def close_clients(cls) -> None:
        """Close all shared HTTP clients."""
        for lang, client in list(cls._shared_clients.items()):
            if not client.is_closed:
                await client.aclose()
        cls._shared_clients.clear()

    async def _execute_request(
        self, language: str, params: dict
    ) -> dict:
        """Execute API request with retries and error handling."""
        client = self.get_client(language, self.timeout)
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = await client.get("", params=params)

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(
                        f"Wikipedia rate limited, waiting {retry_after}s (attempt {attempt + 1})"
                    )
                    await asyncio.sleep(retry_after)
                    continue

                if response.status_code >= 500:
                    logger.warning(
                        f"Wikipedia server error {response.status_code} (attempt {attempt + 1})"
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2**attempt)  # Exponential backoff
                        continue
                    raise WikipediaError(
                        f"Wikipedia server error: {response.status_code}"
                    )

                response.raise_for_status()
                return response.json()

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"Wikipedia timeout (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue

            except httpx.HTTPStatusError as e:
                last_error = e
                # Don't retry client errors (4xx) except 429
                if 400 <= e.response.status_code < 500:
                    raise WikipediaError(
                        f"Wikipedia client error: {e.response.status_code}"
                    )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue

            except httpx.RequestError as e:
                last_error = e
                logger.warning(f"Wikipedia request error: {e} (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue

        raise WikipediaError(f"Failed after {self.max_retries} attempts: {last_error}")

    async def get_article_extract(
        self, title: str, language: Literal["en", "es"] = "en", sentences: int = 5
    ) -> str | None:
        """Get the introductory extract from a Wikipedia article."""
        params = {
            "action": "query",
            "titles": title,
            "prop": "extracts",
            "exintro": "true",
            "explaintext": "true",
            "exsentences": min(sentences, 10),  # Cap at reasonable limit
            "format": "json",
        }

        try:
            data = await self._execute_request(language, params)
        except WikipediaError as e:
            logger.error(f"Failed to get extract for '{title}': {e}")
            return None

        pages = data.get("query", {}).get("pages", {})

        for page_id, page_data in pages.items():
            if page_id != "-1":
                return page_data.get("extract")

        return None

    async def search_nearby_landmarks(
        self,
        lat: float,
        lng: float,
        language: Literal["en", "es"] = "en",
        radius: int = 10000,
        limit: int = 50,
    ) -> list[dict]:
        """Search for Wikipedia articles about landmarks near coordinates."""
        # Validate inputs
        if not (-90 <= lat <= 90):
            logger.warning(f"Invalid latitude: {lat}")
            return []
        if not (-180 <= lng <= 180):
            logger.warning(f"Invalid longitude: {lng}")
            return []

        params = {
            "action": "query",
            "list": "geosearch",
            "gscoord": f"{lat}|{lng}",
            "gsradius": min(radius, 10000),  # Max 10km per Wikipedia API
            "gslimit": min(limit, 500),  # Max 500 per Wikipedia API
            "gsprop": "type|name|dim|country|region",
            "format": "json",
        }

        try:
            data = await self._execute_request(language, params)
        except WikipediaError as e:
            logger.error(f"Failed to search nearby ({lat}, {lng}): {e}")
            return []

        results = data.get("query", {}).get("geosearch", [])

        landmarks = []
        for result in results:
            poi_type = result.get("type", "")
            if poi_type in [
                "landmark",
                "monument",
                "building",
                "church",
                "castle",
                "museum",
            ]:
                landmarks.append(
                    {
                        "title": result.get("title"),
                        "wikipedia_page_id": result.get("pageid"),
                        "coordinates": {
                            "lat": result.get("lat"),
                            "lng": result.get("lon"),
                        },
                        "type": poi_type,
                        "distance_meters": result.get("dist"),
                    }
                )

        return landmarks

    async def get_article_url(
        self, title: str, language: Literal["en", "es"] = "en"
    ) -> str:
        """Get the Wikipedia URL for an article title."""
        # Properly encode the title for URL
        encoded_title = quote(title.replace(" ", "_"), safe="")
        return f"https://{language}.wikipedia.org/wiki/{encoded_title}"
