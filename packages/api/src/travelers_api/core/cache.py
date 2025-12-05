"""Redis caching layer for POI and city data."""

import json

import redis.asyncio as redis

from .config import get_settings

settings = get_settings()

# Global Redis connection pool
_redis_pool: redis.ConnectionPool | None = None


async def get_redis() -> redis.Redis:
    """Get Redis connection from pool"""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool.from_url(
            str(settings.redis_url),
            decode_responses=True,
        )
    return redis.Redis(connection_pool=_redis_pool)


class CacheService:
    """Service for caching POI and city data in Redis"""

    # Cache key prefixes
    PREFIX_POI = "poi:"
    PREFIX_POI_LIST = "poi_list:"
    PREFIX_CITY = "city:"
    PREFIX_CITY_SEARCH = "city_search:"
    PREFIX_WIKIDATA = "wikidata:"

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.default_ttl = settings.cache_ttl_seconds  # 30 days

    # POI caching
    async def get_poi(self, poi_id: str) -> dict | None:
        """Get cached POI by ID"""
        data = await self.redis.get(f"{self.PREFIX_POI}{poi_id}")
        return json.loads(data) if data else None

    async def set_poi(self, poi_id: str, poi_data: dict, ttl: int | None = None) -> None:
        """Cache POI data"""
        await self.redis.setex(
            f"{self.PREFIX_POI}{poi_id}",
            ttl or self.default_ttl,
            json.dumps(poi_data, default=str),
        )

    async def get_poi_list(self, city_id: str, poi_type: str | None = None) -> list[dict] | None:
        """Get cached POI list for a city"""
        key = f"{self.PREFIX_POI_LIST}{city_id}"
        if poi_type:
            key += f":{poi_type}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set_poi_list(
        self, city_id: str, pois: list[dict], poi_type: str | None = None, ttl: int | None = None
    ) -> None:
        """Cache POI list for a city"""
        key = f"{self.PREFIX_POI_LIST}{city_id}"
        if poi_type:
            key += f":{poi_type}"
        await self.redis.setex(
            key,
            ttl or self.default_ttl,
            json.dumps(pois, default=str),
        )

    # City caching
    async def get_city(self, city_id: str) -> dict | None:
        """Get cached city by ID"""
        data = await self.redis.get(f"{self.PREFIX_CITY}{city_id}")
        return json.loads(data) if data else None

    async def set_city(self, city_id: str, city_data: dict, ttl: int | None = None) -> None:
        """Cache city data"""
        await self.redis.setex(
            f"{self.PREFIX_CITY}{city_id}",
            ttl or self.default_ttl,
            json.dumps(city_data, default=str),
        )

    async def get_city_search(self, query: str) -> list[dict] | None:
        """Get cached city search results"""
        key = f"{self.PREFIX_CITY_SEARCH}{query.lower()}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set_city_search(
        self, query: str, results: list[dict], ttl: int = 86400
    ) -> None:
        """Cache city search results (shorter TTL - 1 day)"""
        key = f"{self.PREFIX_CITY_SEARCH}{query.lower()}"
        await self.redis.setex(key, ttl, json.dumps(results, default=str))

    # Wikidata caching
    async def get_wikidata(self, wikidata_id: str) -> dict | None:
        """Get cached Wikidata response"""
        data = await self.redis.get(f"{self.PREFIX_WIKIDATA}{wikidata_id}")
        return json.loads(data) if data else None

    async def set_wikidata(
        self, wikidata_id: str, data: dict, ttl: int | None = None
    ) -> None:
        """Cache Wikidata response"""
        await self.redis.setex(
            f"{self.PREFIX_WIKIDATA}{wikidata_id}",
            ttl or self.default_ttl,
            json.dumps(data, default=str),
        )

    # Utility methods
    async def invalidate_poi(self, poi_id: str) -> None:
        """Invalidate POI cache"""
        await self.redis.delete(f"{self.PREFIX_POI}{poi_id}")

    async def invalidate_city_pois(self, city_id: str) -> None:
        """Invalidate all POI lists for a city"""
        pattern = f"{self.PREFIX_POI_LIST}{city_id}*"
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)


async def get_cache_service() -> CacheService:
    """Dependency injection for cache service"""
    redis_client = await get_redis()
    return CacheService(redis_client)
