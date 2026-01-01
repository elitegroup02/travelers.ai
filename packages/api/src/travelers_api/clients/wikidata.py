"""Wikidata SPARQL client for POI data retrieval."""

import asyncio
import logging
from typing import Any

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "TravelersAI/1.0 (https://github.com/travelers-ai; contact@travelers.ai)"

# Rate limiting: Wikidata allows ~60 requests/minute for anonymous users
MAX_REQUESTS_PER_MINUTE = 50  # Conservative limit
REQUEST_WINDOW_SECONDS = 60


class WikidataError(Exception):
    """Base exception for Wikidata client errors."""

    pass


class WikidataRateLimitError(WikidataError):
    """Raised when rate limited by Wikidata."""

    pass


class WikidataServerError(WikidataError):
    """Raised on Wikidata server errors (5xx)."""

    pass


class WikidataPOIData(BaseModel):
    """POI data from Wikidata."""

    wikidata_id: str
    name: str
    name_es: str | None = None
    inception: int | None = None
    inception_circa: bool = False
    architect: str | None = None
    architectural_style: str | None = None
    heritage_status: str | None = None
    image_url: str | None = None
    coordinates: dict[str, float] | None = None


class WikidataClient:
    """Client for querying Wikidata SPARQL endpoint.

    Features:
    - Connection pooling (reuses HTTP connections)
    - Automatic retries with exponential backoff
    - Rate limiting to stay within API limits
    - Proper error handling for different HTTP status codes
    """

    _shared_client: httpx.AsyncClient | None = None
    _request_times: list[float] = []

    def __init__(self, timeout: float = 30.0, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries

    @classmethod
    def get_client(cls, timeout: float = 30.0) -> httpx.AsyncClient:
        """Get or create shared HTTP client for connection reuse."""
        if cls._shared_client is None or cls._shared_client.is_closed:
            cls._shared_client = httpx.AsyncClient(
                timeout=httpx.Timeout(timeout, connect=10.0),
                headers={
                    "Accept": "application/sparql-results+json",
                    "User-Agent": USER_AGENT,
                },
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )
        return cls._shared_client

    @classmethod
    async def close_client(cls) -> None:
        """Close the shared HTTP client."""
        if cls._shared_client is not None and not cls._shared_client.is_closed:
            await cls._shared_client.aclose()
            cls._shared_client = None

    async def _check_rate_limit(self) -> None:
        """Enforce rate limiting by waiting if necessary."""
        now = asyncio.get_event_loop().time()
        # Remove old request timestamps outside the window
        self._request_times = [
            t for t in self._request_times if now - t < REQUEST_WINDOW_SECONDS
        ]

        if len(self._request_times) >= MAX_REQUESTS_PER_MINUTE:
            # Wait until the oldest request expires from the window
            wait_time = REQUEST_WINDOW_SECONDS - (now - self._request_times[0]) + 0.1
            if wait_time > 0:
                logger.debug(f"Rate limit reached, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                # Clean up again after waiting
                now = asyncio.get_event_loop().time()
                self._request_times = [
                    t for t in self._request_times if now - t < REQUEST_WINDOW_SECONDS
                ]

        self._request_times.append(now)

    async def _execute_query(self, query: str) -> dict[str, Any]:
        """Execute SPARQL query with retries and error handling."""
        client = self.get_client(self.timeout)
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                await self._check_rate_limit()

                response = await client.get(
                    WIKIDATA_ENDPOINT,
                    params={"query": query, "format": "json"},
                )

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(
                        f"Wikidata rate limited, waiting {retry_after}s (attempt {attempt + 1})"
                    )
                    await asyncio.sleep(retry_after)
                    continue

                if response.status_code >= 500:
                    logger.warning(
                        f"Wikidata server error {response.status_code} (attempt {attempt + 1})"
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2**attempt)  # Exponential backoff
                        continue
                    raise WikidataServerError(
                        f"Wikidata server error: {response.status_code}"
                    )

                response.raise_for_status()
                return response.json()

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"Wikidata timeout (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue

            except httpx.HTTPStatusError as e:
                last_error = e
                # Don't retry client errors (4xx) except 429
                if 400 <= e.response.status_code < 500:
                    raise WikidataError(f"Wikidata client error: {e.response.status_code}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue

            except httpx.RequestError as e:
                last_error = e
                logger.warning(f"Wikidata request error: {e} (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue

        raise WikidataError(f"Failed after {self.max_retries} attempts: {last_error}")

    async def get_poi_by_name(
        self, poi_name: str, city_name: str
    ) -> WikidataPOIData | None:
        """Query Wikidata for POI information by name and city."""
        # Escape quotes in names to prevent SPARQL injection
        safe_poi_name = poi_name.replace('"', '\\"')
        safe_city_name = city_name.replace('"', '\\"')

        query = f"""
        SELECT ?item ?itemLabel ?itemLabelEs ?inception ?architectLabel ?styleLabel
               ?heritageLabel ?image ?coords
        WHERE {{
          ?item rdfs:label "{safe_poi_name}"@en .
          ?item wdt:P131* ?city .
          ?city rdfs:label "{safe_city_name}"@en .

          OPTIONAL {{ ?item wdt:P571 ?inception }}
          OPTIONAL {{ ?item wdt:P84 ?architect }}
          OPTIONAL {{ ?item wdt:P149 ?style }}
          OPTIONAL {{ ?item wdt:P1435 ?heritage }}
          OPTIONAL {{ ?item wdt:P18 ?image }}
          OPTIONAL {{ ?item wdt:P625 ?coords }}
          OPTIONAL {{ ?item rdfs:label ?itemLabelEs . FILTER(LANG(?itemLabelEs) = "es") }}

          SERVICE wikibase:label {{
            bd:serviceParam wikibase:language "en".
          }}
        }}
        LIMIT 1
        """

        try:
            data = await self._execute_query(query)
        except WikidataError as e:
            logger.error(f"Failed to query POI {poi_name}: {e}")
            return None

        results = data.get("results", {}).get("bindings", [])

        if not results:
            return None

        result = results[0]
        return self._parse_result(result, poi_name)

    async def get_tourist_attractions_in_city(
        self, city_wikidata_id: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get list of tourist attractions in a city by Wikidata ID."""
        # Validate wikidata_id format (should be Q followed by digits)
        if not city_wikidata_id.startswith("Q") or not city_wikidata_id[1:].isdigit():
            logger.warning(f"Invalid Wikidata ID format: {city_wikidata_id}")
            return []

        query = f"""
        SELECT DISTINCT ?attraction ?attractionLabel ?attractionLabelEs ?coords ?inception
                        ?architectLabel ?styleLabel ?image ?typeLabel
        WHERE {{
          ?attraction (wdt:P31/wdt:P279*) wd:Q570116 .
          ?attraction wdt:P131* wd:{city_wikidata_id} .

          OPTIONAL {{ ?attraction wdt:P625 ?coords }}
          OPTIONAL {{ ?attraction wdt:P571 ?inception }}
          OPTIONAL {{ ?attraction wdt:P84 ?architect }}
          OPTIONAL {{ ?attraction wdt:P149 ?style }}
          OPTIONAL {{ ?attraction wdt:P18 ?image }}
          OPTIONAL {{ ?attraction wdt:P31 ?type }}
          OPTIONAL {{
            ?attraction rdfs:label ?attractionLabelEs .
            FILTER(LANG(?attractionLabelEs) = "es")
          }}

          SERVICE wikibase:label {{
            bd:serviceParam wikibase:language "en".
          }}
        }}
        LIMIT {min(limit, 100)}
        """

        try:
            data = await self._execute_query(query)
        except WikidataError as e:
            logger.error(f"Failed to query attractions in {city_wikidata_id}: {e}")
            return []

        results = data.get("results", {}).get("bindings", [])

        attractions = []
        for result in results:
            attraction = self._parse_attraction(result)
            if attraction:
                attractions.append(attraction)

        return attractions

    def _parse_result(self, result: dict, fallback_name: str) -> WikidataPOIData:
        """Parse a Wikidata SPARQL result into WikidataPOIData."""
        # Parse coordinates from Point format
        coords = None
        if "coords" in result:
            coord_str = result["coords"]["value"]
            if coord_str.startswith("Point("):
                try:
                    parts = coord_str[6:-1].split()
                    coords = {"lng": float(parts[0]), "lat": float(parts[1])}
                except (ValueError, IndexError):
                    logger.warning(f"Failed to parse coordinates: {coord_str}")

        # Parse inception year
        inception = None
        if "inception" in result:
            inception_str = result["inception"]["value"]
            if "T" in inception_str:
                try:
                    inception = int(inception_str.split("-")[0])
                except ValueError:
                    pass
            else:
                try:
                    inception = int(inception_str)
                except ValueError:
                    pass

        return WikidataPOIData(
            wikidata_id=result["item"]["value"].split("/")[-1],
            name=result.get("itemLabel", {}).get("value", fallback_name),
            name_es=result.get("itemLabelEs", {}).get("value"),
            inception=inception,
            architect=result.get("architectLabel", {}).get("value"),
            architectural_style=result.get("styleLabel", {}).get("value"),
            heritage_status=result.get("heritageLabel", {}).get("value"),
            image_url=result.get("image", {}).get("value"),
            coordinates=coords,
        )

    def _parse_attraction(self, result: dict) -> dict | None:
        """Parse attraction result."""
        if "attractionLabel" not in result:
            return None

        coords = None
        if "coords" in result:
            coord_str = result["coords"]["value"]
            if coord_str.startswith("Point("):
                try:
                    parts = coord_str[6:-1].split()
                    coords = {"lng": float(parts[0]), "lat": float(parts[1])}
                except (ValueError, IndexError):
                    logger.warning(f"Failed to parse coordinates: {coord_str}")

        return {
            "wikidata_id": result["attraction"]["value"].split("/")[-1],
            "name": result.get("attractionLabel", {}).get("value"),
            "name_es": result.get("attractionLabelEs", {}).get("value"),
            "coordinates": coords,
            "inception": result.get("inception", {}).get("value"),
            "architect": result.get("architectLabel", {}).get("value"),
            "style": result.get("styleLabel", {}).get("value"),
            "image_url": result.get("image", {}).get("value"),
            "type": result.get("typeLabel", {}).get("value"),
        }
