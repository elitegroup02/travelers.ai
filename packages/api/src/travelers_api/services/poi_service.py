"""POI service with full data pipeline: Wikidata → Wikipedia → LLM → Cache."""

import logging
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_Distance, ST_DWithin, ST_GeogFromText, ST_X, ST_Y
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..clients.wikidata import WikidataClient
from ..clients.wikipedia import WikipediaClient
from ..core.cache import CacheService
from ..models.city import City
from ..models.poi import POI
from .llm import LLMProvider, POIData, get_llm_provider

logger = logging.getLogger(__name__)


class POIService:
    """Service for POI operations with full data enrichment pipeline"""

    def __init__(
        self,
        db: AsyncSession,
        cache: CacheService | None = None,
        wikidata: WikidataClient | None = None,
        wikipedia: WikipediaClient | None = None,
        llm: LLMProvider | None = None,
    ):
        self.db = db
        self.cache = cache
        self.wikidata = wikidata or WikidataClient()
        self.wikipedia = wikipedia or WikipediaClient()
        self.llm = llm

    async def get_pois_for_city(
        self,
        city_id: UUID,
        poi_type: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """Get POIs for a city with pagination"""
        # Check cache first
        if self.cache and offset == 0:
            cached = await self.cache.get_poi_list(str(city_id), poi_type)
            if cached:
                return {
                    "items": cached[:limit],
                    "total": len(cached),
                    "has_more": len(cached) > limit,
                }

        # Build base filter
        base_filter = POI.city_id == city_id
        if poi_type:
            base_filter = (POI.city_id == city_id) & (POI.poi_type == poi_type)

        # Get total count
        count_stmt = select(func.count()).select_from(POI).where(base_filter)
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Build query with coordinate extraction
        geom = cast(POI.coordinates, Geometry)
        stmt = (
            select(
                POI,
                ST_Y(geom).label("lat"),
                ST_X(geom).label("lng"),
            )
            .where(base_filter)
            .order_by(POI.data_quality_score.desc().nulls_last(), POI.name)
            .offset(offset)
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        poi_list = [self._poi_row_to_dict(poi, lat, lng) for poi, lat, lng in rows]

        # Cache first page of results
        if self.cache and offset == 0:
            await self.cache.set_poi_list(str(city_id), poi_list, poi_type)

        return {
            "items": poi_list,
            "total": total,
            "has_more": (offset + limit) < total,
        }

    async def get_poi(
        self,
        poi_id: UUID,
        language: Literal["en", "es"] = "en",
        generate_summary: bool = True,
    ) -> dict | None:
        """Get POI with full details, generating summary if needed"""
        # Check cache first
        cache_key = f"{poi_id}:{language}"
        if self.cache:
            cached = await self.cache.get_poi(cache_key)
            if cached:
                return cached

        # Query database with coordinate extraction
        geom = cast(POI.coordinates, Geometry)
        stmt = select(
            POI,
            ST_Y(geom).label("lat"),
            ST_X(geom).label("lng"),
        ).where(POI.id == poi_id)
        result = await self.db.execute(stmt)
        row = result.one_or_none()

        if not row:
            return None

        poi, lat, lng = row
        poi_dict = self._poi_row_to_detail_dict(poi, lat, lng, language)

        # Generate summary if missing and LLM is available
        if generate_summary and self.llm:
            summary_field = "summary" if language == "en" else "summary_es"
            if not poi_dict.get(summary_field):
                try:
                    summary = await self._generate_summary(poi, language)
                    if summary:
                        poi_dict[summary_field] = summary
                        # Update database
                        await self._update_poi_summary(poi, summary, language)
                except Exception as e:
                    logger.error(f"Failed to generate summary for POI {poi_id}: {e}")

        # Cache result
        if self.cache:
            await self.cache.set_poi(cache_key, poi_dict)

        return poi_dict

    async def search_pois(
        self,
        query: str,
        city_id: UUID | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Search POIs by name"""
        base_filter = POI.name.ilike(f"%{query}%")
        if city_id:
            base_filter = base_filter & (POI.city_id == city_id)

        geom = cast(POI.coordinates, Geometry)
        stmt = (
            select(
                POI,
                ST_Y(geom).label("lat"),
                ST_X(geom).label("lng"),
            )
            .where(base_filter)
            .order_by(POI.data_quality_score.desc().nulls_last())
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        return [self._poi_row_to_dict(poi, lat, lng) for poi, lat, lng in rows]

    async def get_nearby_pois(
        self,
        lat: float,
        lng: float,
        radius_meters: int = 1000,
        limit: int = 20,
    ) -> list[dict]:
        """Get POIs near coordinates"""
        point = f"SRID=4326;POINT({lng} {lat})"

        geom = cast(POI.coordinates, Geometry)
        stmt = (
            select(
                POI,
                ST_Y(geom).label("lat"),
                ST_X(geom).label("lng"),
                ST_Distance(
                    POI.coordinates,
                    ST_GeogFromText(point)
                ).label("distance")
            )
            .where(
                ST_DWithin(
                    POI.coordinates,
                    ST_GeogFromText(point),
                    radius_meters
                )
            )
            .order_by("distance")
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {**self._poi_row_to_dict(poi, lat, lng), "distance_meters": round(distance)}
            for poi, lat, lng, distance in rows
        ]

    async def fetch_and_store_city_pois(
        self, city: City, limit: int = 50
    ) -> list[POI]:
        """Fetch POIs from Wikidata for a city and store them"""
        if not city.wikidata_id:
            logger.warning(f"City {city.name} has no Wikidata ID")
            return []

        # Fetch attractions from Wikidata
        attractions = await self.wikidata.get_tourist_attractions_in_city(
            city.wikidata_id, limit=limit
        )

        created_pois = []
        for attraction in attractions:
            try:
                poi = await self._create_poi_from_wikidata(city, attraction)
                if poi:
                    created_pois.append(poi)
            except Exception as e:
                logger.error(f"Failed to create POI from {attraction}: {e}")

        if created_pois:
            await self.db.commit()
            # Invalidate cache
            if self.cache:
                await self.cache.invalidate_city_pois(str(city.id))

        return created_pois

    async def enrich_poi(self, poi_id: UUID) -> dict | None:
        """Enrich a POI with Wikipedia data and AI summary"""
        stmt = select(POI).where(POI.id == poi_id)
        result = await self.db.execute(stmt)
        poi = result.scalar_one_or_none()

        if not poi:
            return None

        # Get Wikipedia extract
        if poi.name and not poi.wikipedia_extract:
            try:
                extract = await self.wikipedia.get_article_extract(poi.name)
                if extract:
                    poi.wikipedia_extract = extract
                    poi.wikipedia_url = await self.wikipedia.get_article_url(poi.name)
            except Exception as e:
                logger.error(f"Failed to get Wikipedia extract for {poi.name}: {e}")

        # Generate summaries
        if self.llm:
            try:
                if not poi.summary:
                    summary_en = await self._generate_summary(poi, "en")
                    if summary_en:
                        poi.summary = summary_en

                if not poi.summary_es:
                    summary_es = await self._generate_summary(poi, "es")
                    if summary_es:
                        poi.summary_es = summary_es
            except Exception as e:
                logger.error(f"Failed to generate summaries for {poi.name}: {e}")

        poi.last_verified_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(poi)

        # Invalidate cache
        if self.cache:
            await self.cache.invalidate_poi(str(poi.id))

        geom = cast(POI.coordinates, Geometry)
        stmt = select(
            POI,
            ST_Y(geom).label("lat"),
            ST_X(geom).label("lng"),
        ).where(POI.id == poi.id)
        result = await self.db.execute(stmt)
        row = result.one()
        return self._poi_row_to_detail_dict(row[0], row[1], row[2], "en")

    async def _create_poi_from_wikidata(
        self, city: City, wikidata: dict
    ) -> POI | None:
        """Create or update POI from Wikidata attraction data"""
        wikidata_id = wikidata.get("wikidata_id")
        if not wikidata_id:
            return None

        # Check if POI already exists
        stmt = select(POI).where(POI.wikidata_id == wikidata_id)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            return existing

        coords = wikidata.get("coordinates")
        if not coords:
            return None

        # Create point from coordinates
        lat = coords.get("lat")
        lng = coords.get("lng")
        if lat is None or lng is None:
            return None

        point_wkt = f"SRID=4326;POINT({lng} {lat})"

        # Parse inception year
        year_built = None
        if wikidata.get("inception"):
            try:
                inception_str = str(wikidata["inception"])
                if "T" in inception_str:
                    year_built = int(inception_str.split("-")[0])
                else:
                    year_built = int(inception_str)
            except (ValueError, TypeError):
                pass

        poi = POI(
            city_id=city.id,
            name=wikidata.get("name", "Unknown"),
            wikidata_id=wikidata_id,
            coordinates=point_wkt,
            year_built=year_built,
            architect=wikidata.get("architect"),
            architectural_style=wikidata.get("style"),
            image_url=wikidata.get("image_url"),
            poi_type=wikidata.get("type", "landmark"),
            data_source="wikidata",
        )

        self.db.add(poi)
        return poi

    async def _generate_summary(
        self, poi: POI, language: Literal["en", "es"]
    ) -> str | None:
        """Generate AI summary for POI"""
        if not self.llm:
            return None

        poi_data = POIData(
            name=poi.name,
            year_built=poi.year_built,
            architect=poi.architect,
            architectural_style=poi.architectural_style,
            heritage_status=poi.heritage_status,
            wikipedia_extract=poi.wikipedia_extract,
        )

        return await self.llm.generate_summary(poi_data, language)

    async def _update_poi_summary(
        self, poi: POI, summary: str, language: Literal["en", "es"]
    ) -> None:
        """Update POI summary in database"""
        if language == "en":
            poi.summary = summary
        else:
            poi.summary_es = summary
        await self.db.commit()

    def _poi_row_to_dict(self, poi: POI, lat: float | None, lng: float | None) -> dict:
        """Convert POI with extracted coordinates to list item dictionary"""
        return {
            "id": str(poi.id),
            "name": poi.name,
            "poi_type": poi.poi_type,
            "coordinates": {"lat": lat, "lng": lng} if lat and lng else None,
            "image_url": poi.image_url,
            "year_built": poi.year_built,
            "estimated_visit_duration": poi.estimated_visit_duration,
        }

    def _poi_row_to_detail_dict(
        self, poi: POI, lat: float | None, lng: float | None, language: Literal["en", "es"]
    ) -> dict:
        """Convert POI with extracted coordinates to full detail dictionary"""
        summary = poi.summary if language == "en" else (poi.summary_es or poi.summary)

        return {
            "id": str(poi.id),
            "city_id": str(poi.city_id),
            "name": poi.name,
            "wikidata_id": poi.wikidata_id,
            "google_place_id": poi.google_place_id,
            "wikipedia_url": poi.wikipedia_url,
            "coordinates": {"lat": lat, "lng": lng} if lat and lng else None,
            "address": poi.address,
            "year_built": poi.year_built,
            "year_built_circa": poi.year_built_circa,
            "architect": poi.architect,
            "architectural_style": poi.architectural_style,
            "heritage_status": poi.heritage_status,
            "summary": summary,
            "wikipedia_extract": poi.wikipedia_extract,
            "image_url": poi.image_url,
            "image_attribution": poi.image_attribution,
            "poi_type": poi.poi_type,
            "estimated_visit_duration": poi.estimated_visit_duration,
            "data_quality_score": float(poi.data_quality_score) if poi.data_quality_score else None,
            "last_verified_at": poi.last_verified_at.isoformat() if poi.last_verified_at else None,
        }
