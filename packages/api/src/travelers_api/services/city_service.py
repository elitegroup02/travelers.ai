"""City service for searching and managing cities"""

from uuid import UUID

from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_Distance, ST_DWithin, ST_GeogFromText, ST_X, ST_Y
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.cache import CacheService
from ..models.city import City


class CityService:
    """Service for city operations with caching"""

    def __init__(self, db: AsyncSession, cache: CacheService | None = None):
        self.db = db
        self.cache = cache

    async def search_cities(
        self, query: str, limit: int = 10
    ) -> list[dict]:
        """Search cities by name with caching"""
        # Check cache first
        if self.cache:
            cached = await self.cache.get_city_search(query)
            if cached:
                return cached[:limit]

        # Query database with similarity search and extract coordinates
        # Cast Geography to Geometry to use ST_X/ST_Y
        geom = cast(City.coordinates, Geometry)
        stmt = (
            select(
                City,
                ST_Y(geom).label("lat"),
                ST_X(geom).label("lng"),
            )
            .where(City.name.ilike(f"%{query}%"))
            .order_by(City.name)
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        city_list = [self._city_row_to_dict(city, lat, lng) for city, lat, lng in rows]

        # Cache results
        if self.cache and city_list:
            await self.cache.set_city_search(query, city_list)

        return city_list

    async def get_city(self, city_id: UUID) -> dict | None:
        """Get city by ID with caching"""
        # Check cache first
        if self.cache:
            cached = await self.cache.get_city(str(city_id))
            if cached:
                return cached

        # Query database with coordinate extraction
        geom = cast(City.coordinates, Geometry)
        stmt = select(
            City,
            ST_Y(geom).label("lat"),
            ST_X(geom).label("lng"),
        ).where(City.id == city_id)
        result = await self.db.execute(stmt)
        row = result.one_or_none()

        if not row:
            return None

        city, lat, lng = row
        city_dict = self._city_row_to_dict(city, lat, lng)

        # Cache result
        if self.cache:
            await self.cache.set_city(str(city_id), city_dict)

        return city_dict

    async def get_or_create_city(
        self,
        name: str,
        country: str,
        coordinates: tuple[float, float],  # (lat, lng)
        country_code: str | None = None,
        timezone: str | None = None,
        wikidata_id: str | None = None,
    ) -> City:
        """Get existing city or create new one"""
        # Try to find existing city by name and country
        stmt = select(City).where(
            City.name == name,
            City.country == country,
        )
        result = await self.db.execute(stmt)
        city = result.scalar_one_or_none()

        if city:
            return city

        # Create new city
        lat, lng = coordinates
        point_wkt = f"SRID=4326;POINT({lng} {lat})"

        city = City(
            name=name,
            country=country,
            country_code=country_code,
            coordinates=point_wkt,
            timezone=timezone,
            wikidata_id=wikidata_id,
        )
        self.db.add(city)
        await self.db.commit()
        await self.db.refresh(city)

        return city

    async def get_cities_by_country(self, country: str, limit: int = 50) -> list[dict]:
        """Get cities in a country"""
        geom = cast(City.coordinates, Geometry)
        stmt = (
            select(
                City,
                ST_Y(geom).label("lat"),
                ST_X(geom).label("lng"),
            )
            .where(City.country.ilike(f"%{country}%"))
            .order_by(City.name)
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        return [self._city_row_to_dict(city, lat, lng) for city, lat, lng in rows]

    async def find_nearby_cities(
        self, lat: float, lng: float, radius_km: int = 100, limit: int = 10
    ) -> list[dict]:
        """Find cities within radius of coordinates"""
        point = f"SRID=4326;POINT({lng} {lat})"
        radius_meters = radius_km * 1000

        geom = cast(City.coordinates, Geometry)
        stmt = (
            select(
                City,
                ST_Y(geom).label("lat"),
                ST_X(geom).label("lng"),
                ST_Distance(
                    City.coordinates,
                    ST_GeogFromText(point)
                ).label("distance")
            )
            .where(
                ST_DWithin(
                    City.coordinates,
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
            {**self._city_row_to_dict(city, lat, lng), "distance_km": round(distance / 1000, 2)}
            for city, lat, lng, distance in rows
        ]

    def _city_row_to_dict(self, city: City, lat: float, lng: float) -> dict:
        """Convert City model with extracted coordinates to dictionary"""
        return {
            "id": str(city.id),
            "name": city.name,
            "country": city.country,
            "country_code": city.country_code,
            "coordinates": {"lat": lat, "lng": lng} if lat and lng else None,
            "timezone": city.timezone,
            "wikidata_id": city.wikidata_id,
            "google_place_id": city.google_place_id,
        }
