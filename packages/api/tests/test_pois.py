"""Tests for POI endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from travelers_api.models.city import City
from travelers_api.models.poi import POI


@pytest.fixture
async def test_city(db_session: AsyncSession) -> City:
    """Create a test city."""
    city = City(
        id=uuid4(),
        name="Rome",
        country="Italy",
        wikidata_id="Q220",
        coordinates="POINT(12.4964 41.9028)",
    )
    db_session.add(city)
    await db_session.commit()
    return city


@pytest.fixture
async def test_pois(db_session: AsyncSession, test_city: City) -> list[POI]:
    """Create test POIs in the database."""
    pois = [
        POI(
            id=uuid4(),
            city_id=test_city.id,
            name="Colosseum",
            poi_type="monument",
            wikidata_id="Q10285",
            summary="An ancient amphitheatre in Rome.",
            coordinates="POINT(12.4924 41.8902)",
            estimated_visit_duration=90,
            year_built=80,
        ),
        POI(
            id=uuid4(),
            city_id=test_city.id,
            name="Pantheon",
            poi_type="temple",
            wikidata_id="Q43473",
            summary="A former Roman temple, now a church.",
            coordinates="POINT(12.4768 41.8986)",
            estimated_visit_duration=45,
            year_built=125,
        ),
        POI(
            id=uuid4(),
            city_id=test_city.id,
            name="Trevi Fountain",
            poi_type="fountain",
            wikidata_id="Q187342",
            summary="An iconic fountain in Rome.",
            coordinates="POINT(12.4833 41.9009)",
            estimated_visit_duration=20,
            year_built=1762,
        ),
    ]

    for poi in pois:
        db_session.add(poi)
    await db_session.commit()

    return pois


class TestPOIList:
    """Tests for GET /pois."""

    async def test_list_pois_for_city(
        self, client: AsyncClient, test_city: City, test_pois: list[POI]
    ):
        """Test listing POIs for a city."""
        response = await client.get("/api/v1/pois", params={"city_id": str(test_city.id)})

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

        # Check POI structure
        poi = data["items"][0]
        assert "id" in poi
        assert "name" in poi
        assert "poi_type" in poi
        assert "estimated_visit_duration" in poi

    async def test_list_pois_pagination(
        self, client: AsyncClient, test_city: City, test_pois: list[POI]
    ):
        """Test POI list pagination."""
        # Get first page
        response = await client.get(
            "/api/v1/pois",
            params={"city_id": str(test_city.id), "limit": 2, "offset": 0},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 3
        assert data["has_more"] is True

        # Get second page
        response = await client.get(
            "/api/v1/pois",
            params={"city_id": str(test_city.id), "limit": 2, "offset": 2},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["has_more"] is False

    async def test_list_pois_filter_by_type(
        self, client: AsyncClient, test_city: City, test_pois: list[POI]
    ):
        """Test filtering POIs by type."""
        response = await client.get(
            "/api/v1/pois",
            params={"city_id": str(test_city.id), "poi_type": "monument"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["poi_type"] == "monument"

    async def test_list_pois_no_city_id(self, client: AsyncClient):
        """Test listing POIs without city_id."""
        response = await client.get("/api/v1/pois")

        # Should require city_id or return all (depends on implementation)
        assert response.status_code in [200, 400, 422]


class TestPOIDetail:
    """Tests for GET /pois/{poi_id}."""

    async def test_get_poi_success(
        self, client: AsyncClient, test_city: City, test_pois: list[POI]
    ):
        """Test getting a POI by ID."""
        poi = test_pois[0]
        response = await client.get(f"/api/v1/pois/{poi.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(poi.id)
        assert data["name"] == poi.name
        assert data["poi_type"] == poi.poi_type
        assert "summary" in data
        assert "coordinates" in data

    async def test_get_poi_with_language(
        self, client: AsyncClient, test_city: City, test_pois: list[POI]
    ):
        """Test getting a POI with language parameter."""
        poi = test_pois[0]
        response = await client.get(f"/api/v1/pois/{poi.id}", params={"lang": "es"})

        assert response.status_code == 200
        # Should return POI with Spanish content if available

    async def test_get_poi_not_found(self, client: AsyncClient):
        """Test getting a non-existent POI."""
        fake_id = uuid4()
        response = await client.get(f"/api/v1/pois/{fake_id}")

        assert response.status_code == 404


class TestPOISearch:
    """Tests for GET /pois/search."""

    async def test_search_pois(
        self, client: AsyncClient, test_city: City, test_pois: list[POI]
    ):
        """Test searching POIs by name."""
        response = await client.get("/api/v1/pois/search", params={"q": "Colosseum"})

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any(poi["name"] == "Colosseum" for poi in data["items"])

    async def test_search_pois_in_city(
        self, client: AsyncClient, test_city: City, test_pois: list[POI]
    ):
        """Test searching POIs within a specific city."""
        response = await client.get(
            "/api/v1/pois/search",
            params={"q": "Pantheon", "city_id": str(test_city.id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    async def test_search_pois_no_results(self, client: AsyncClient, test_pois: list[POI]):
        """Test searching with no matching POIs."""
        response = await client.get("/api/v1/pois/search", params={"q": "Nonexistent Place"})

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
