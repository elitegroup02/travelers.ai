"""City search and detail endpoints"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.cache import CacheService, get_cache_service
from ..core.database import get_db
from ..services.city_service import CityService

router = APIRouter(prefix="/cities")


async def get_city_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    cache: Annotated[CacheService, Depends(get_cache_service)],
) -> CityService:
    return CityService(db, cache)


@router.get("/search")
async def search_cities(
    q: Annotated[str, Query(min_length=2, description="Search query")],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    service: CityService = Depends(get_city_service),
):
    """Search for cities by name"""
    results = await service.search_cities(q, limit)
    return {"items": results, "total": len(results)}


@router.get("/nearby")
async def nearby_cities(
    lat: Annotated[float, Query(ge=-90, le=90, description="Latitude")],
    lng: Annotated[float, Query(ge=-180, le=180, description="Longitude")],
    radius_km: Annotated[int, Query(ge=1, le=500)] = 100,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    service: CityService = Depends(get_city_service),
):
    """Find cities near coordinates"""
    results = await service.find_nearby_cities(lat, lng, radius_km, limit)
    return {"items": results, "total": len(results)}


@router.get("/by-country/{country}")
async def cities_by_country(
    country: str,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    service: CityService = Depends(get_city_service),
):
    """Get cities in a country"""
    results = await service.get_cities_by_country(country, limit)
    return {"items": results, "total": len(results)}


@router.get("/{city_id}")
async def get_city(
    city_id: UUID,
    service: CityService = Depends(get_city_service),
):
    """Get city details"""
    city = await service.get_city(city_id)
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    return city
