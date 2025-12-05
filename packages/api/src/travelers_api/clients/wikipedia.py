"""Wikipedia API client for article extracts and geosearch"""

from typing import Literal

import httpx

WIKIPEDIA_API = "https://{lang}.wikipedia.org/w/api.php"


class WikipediaClient:
    """Client for Wikipedia API"""

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout

    async def get_article_extract(
        self, title: str, language: Literal["en", "es"] = "en", sentences: int = 5
    ) -> str | None:
        """Get the introductory extract from a Wikipedia article"""
        api_url = WIKIPEDIA_API.format(lang=language)
        params = {
            "action": "query",
            "titles": title,
            "prop": "extracts",
            "exintro": "true",
            "explaintext": "true",
            "exsentences": sentences,
            "format": "json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, params=params, timeout=self.timeout)
            response.raise_for_status()

        data = response.json()
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
        """Search for Wikipedia articles about landmarks near coordinates"""
        api_url = WIKIPEDIA_API.format(lang=language)
        params = {
            "action": "query",
            "list": "geosearch",
            "gscoord": f"{lat}|{lng}",
            "gsradius": radius,
            "gslimit": limit,
            "gsprop": "type|name|dim|country|region",
            "format": "json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, params=params, timeout=self.timeout)
            response.raise_for_status()

        data = response.json()
        results = data.get("query", {}).get("geosearch", [])

        landmarks = []
        for result in results:
            poi_type = result.get("type", "")
            if poi_type in ["landmark", "monument", "building", "church", "castle", "museum"]:
                landmarks.append({
                    "title": result.get("title"),
                    "wikipedia_page_id": result.get("pageid"),
                    "coordinates": {
                        "lat": result.get("lat"),
                        "lng": result.get("lon"),
                    },
                    "type": poi_type,
                    "distance_meters": result.get("dist"),
                })

        return landmarks

    async def get_article_url(
        self, title: str, language: Literal["en", "es"] = "en"
    ) -> str:
        """Get the Wikipedia URL for an article title"""
        encoded_title = title.replace(" ", "_")
        return f"https://{language}.wikipedia.org/wiki/{encoded_title}"
