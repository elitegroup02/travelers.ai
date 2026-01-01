"""Tests for city endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from travelers_api.models.city import City


@pytest.fixture
async def test_cities(db_session: AsyncSession) -> list[City]:
    """Create test cities in the database."""
    cities = [
        City(
            id=uuid4(),
            name="Paris",
            country="France",
            wikidata_id="Q90",
            coordinates="POINT(2.3522 48.8566)",
        ),
        City(
            id=uuid4(),
            name="London",
            country="United Kingdom",
            wikidata_id="Q84",
            coordinates="POINT(-0.1276 51.5074)",
        ),
        City(
            id=uuid4(),
            name="New York",
            country="United States",
            wikidata_id="Q60",
            coordinates="POINT(-74.0060 40.7128)",
        ),
        City(
            id=uuid4(),
            name="Parkland",
            country="United States",
            wikidata_id="Q12345",
            coordinates="POINT(-80.2433 26.3103)",
        ),
    ]

    for city in cities:
        db_session.add(city)
    await db_session.commit()

    return cities


class TestCitySearch:
    """Tests for GET /cities/search."""

    async def test_search_cities_by_name(self, client: AsyncClient, test_cities: list[City]):
        """Test searching cities by name."""
        response = await client.get("/api/v1/cities/search", params={"q": "Paris"})

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any(city["name"] == "Paris" for city in data["items"])

    async def test_search_cities_partial_match(self, client: AsyncClient, test_cities: list[City]):
        """Test searching cities with partial name match."""
        response = await client.get("/api/v1/cities/search", params={"q": "Par"})

        assert response.status_code == 200
        data = response.json()
        # Should match both Paris and Parkland
        assert data["total"] >= 2
        names = [city["name"] for city in data["items"]]
        assert "Paris" in names
        assert "Parkland" in names

    async def test_search_cities_no_results(self, client: AsyncClient, test_cities: list[City]):
        """Test searching with no matching cities."""
        response = await client.get("/api/v1/cities/search", params={"q": "Atlantis"})

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_search_cities_limit(self, client: AsyncClient, test_cities: list[City]):
        """Test search respects limit parameter."""
        response = await client.get("/api/v1/cities/search", params={"q": "a", "limit": 2})

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 2

    async def test_search_cities_short_query(self, client: AsyncClient, test_cities: list[City]):
        """Test search with query too short."""
        response = await client.get("/api/v1/cities/search", params={"q": "a"})

        # Could return empty or require minimum length - depends on implementation
        assert response.status_code in [200, 400, 422]


class TestCityDetail:
    """Tests for GET /cities/{city_id}."""

    async def test_get_city_success(self, client: AsyncClient, test_cities: list[City]):
        """Test getting a city by ID."""
        city = test_cities[0]
        response = await client.get(f"/api/v1/cities/{city.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(city.id)
        assert data["name"] == city.name
        assert data["country"] == city.country
        assert "coordinates" in data

    async def test_get_city_not_found(self, client: AsyncClient):
        """Test getting a non-existent city."""
        fake_id = uuid4()
        response = await client.get(f"/api/v1/cities/{fake_id}")

        assert response.status_code == 404

    async def test_get_city_invalid_id(self, client: AsyncClient):
        """Test getting a city with invalid ID format."""
        response = await client.get("/api/v1/cities/not-a-uuid")

        assert response.status_code == 422  # Validation error
