"""POI endpoints with full data enrichment"""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.cache import CacheService, get_cache_service
from ..core.database import get_db
from ..services.llm import get_llm_provider, LLMProvider
from ..services.poi_service import POIService

router = APIRouter(prefix="/pois")


async def get_poi_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    cache: Annotated[CacheService, Depends(get_cache_service)],
) -> POIService:
    # Try to get LLM provider, but don't fail if not configured
    try:
        llm = get_llm_provider()
    except (ValueError, ImportError):
        llm = None
    return POIService(db, cache, llm=llm)


@router.get("")
async def list_pois(
    city_id: Annotated[UUID, Query(description="City UUID")],
    poi_type: Annotated[str | None, Query(description="Filter by POI type")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    service: POIService = Depends(get_poi_service),
):
    """Get POIs for a city with pagination"""
    return await service.get_pois_for_city(city_id, poi_type, limit, offset)


@router.get("/search")
async def search_pois(
    q: Annotated[str, Query(min_length=2, description="Search query")],
    city_id: Annotated[UUID | None, Query(description="Optional city filter")] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    service: POIService = Depends(get_poi_service),
):
    """Search for POIs by name"""
    results = await service.search_pois(q, city_id, limit)
    return {"items": results, "total": len(results)}


@router.get("/nearby")
async def nearby_pois(
    lat: Annotated[float, Query(ge=-90, le=90, description="Latitude")],
    lng: Annotated[float, Query(ge=-180, le=180, description="Longitude")],
    radius: Annotated[int, Query(ge=100, le=10000, description="Radius in meters")] = 1000,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    service: POIService = Depends(get_poi_service),
):
    """Get POIs near a location"""
    results = await service.get_nearby_pois(lat, lng, radius, limit)
    return {"items": results, "total": len(results)}


@router.get("/{poi_id}")
async def get_poi(
    poi_id: UUID,
    lang: Annotated[Literal["en", "es"], Query(description="Language for summary")] = "en",
    service: POIService = Depends(get_poi_service),
):
    """Get POI details with info card (AI-generated summary)"""
    poi = await service.get_poi(poi_id, language=lang)
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    return poi


@router.post("/{poi_id}/enrich")
async def enrich_poi(
    poi_id: UUID,
    service: POIService = Depends(get_poi_service),
):
    """Manually trigger POI data enrichment (Wikipedia + AI summary)"""
    poi = await service.enrich_poi(poi_id)
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    return poi
