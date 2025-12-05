"""Wikidata SPARQL client for POI data retrieval"""

from typing import Any

import httpx
from pydantic import BaseModel

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"


class WikidataPOIData(BaseModel):
    """POI data from Wikidata"""

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
    """Client for querying Wikidata SPARQL endpoint"""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    async def get_poi_by_name(
        self, poi_name: str, city_name: str
    ) -> WikidataPOIData | None:
        """Query Wikidata for POI information by name and city"""
        query = f"""
        SELECT ?item ?itemLabel ?itemLabelEs ?inception ?architectLabel ?styleLabel
               ?heritageLabel ?image ?coords
        WHERE {{
          ?item rdfs:label "{poi_name}"@en .
          ?item wdt:P131* ?city .
          ?city rdfs:label "{city_name}"@en .

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

        async with httpx.AsyncClient() as client:
            response = await client.get(
                WIKIDATA_ENDPOINT,
                params={"query": query, "format": "json"},
                headers={"Accept": "application/sparql-results+json"},
                timeout=self.timeout,
            )
            response.raise_for_status()

        data = response.json()
        results = data.get("results", {}).get("bindings", [])

        if not results:
            return None

        result = results[0]
        return self._parse_result(result, poi_name)

    async def get_tourist_attractions_in_city(
        self, city_wikidata_id: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get list of tourist attractions in a city by Wikidata ID"""
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
        LIMIT {limit}
        """

        async with httpx.AsyncClient() as client:
            response = await client.get(
                WIKIDATA_ENDPOINT,
                params={"query": query, "format": "json"},
                headers={"Accept": "application/sparql-results+json"},
                timeout=self.timeout,
            )
            response.raise_for_status()

        data = response.json()
        results = data.get("results", {}).get("bindings", [])

        attractions = []
        for result in results:
            attraction = self._parse_attraction(result)
            if attraction:
                attractions.append(attraction)

        return attractions

    def _parse_result(self, result: dict, fallback_name: str) -> WikidataPOIData:
        """Parse a Wikidata SPARQL result into WikidataPOIData"""
        # Parse coordinates from Point format
        coords = None
        if "coords" in result:
            coord_str = result["coords"]["value"]
            if coord_str.startswith("Point("):
                parts = coord_str[6:-1].split()
                coords = {"lng": float(parts[0]), "lat": float(parts[1])}

        # Parse inception year
        inception = None
        if "inception" in result:
            inception_str = result["inception"]["value"]
            if "T" in inception_str:
                inception = int(inception_str.split("-")[0])
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
        """Parse attraction result"""
        if "attractionLabel" not in result:
            return None

        coords = None
        if "coords" in result:
            coord_str = result["coords"]["value"]
            if coord_str.startswith("Point("):
                parts = coord_str[6:-1].split()
                coords = {"lng": float(parts[0]), "lat": float(parts[1])}

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
