"""Tests for trip management endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from travelers_api.models.city import City
from travelers_api.models.poi import POI


@pytest.fixture
async def test_city_for_trip(db_session: AsyncSession) -> City:
    """Create a test city for trip tests."""
    city = City(
        id=uuid4(),
        name="Barcelona",
        country="Spain",
        wikidata_id="Q1492",
        coordinates="POINT(2.1734 41.3851)",
    )
    db_session.add(city)
    await db_session.commit()
    return city


@pytest.fixture
async def test_pois_for_trip(db_session: AsyncSession, test_city_for_trip: City) -> list[POI]:
    """Create test POIs for trip tests."""
    pois = [
        POI(
            id=uuid4(),
            city_id=test_city_for_trip.id,
            name="Sagrada Familia",
            poi_type="church",
            wikidata_id="Q48435",
            coordinates="POINT(2.1744 41.4036)",
            estimated_visit_duration=120,
        ),
        POI(
            id=uuid4(),
            city_id=test_city_for_trip.id,
            name="Park Güell",
            poi_type="park",
            wikidata_id="Q271508",
            coordinates="POINT(2.1527 41.4145)",
            estimated_visit_duration=90,
        ),
    ]

    for poi in pois:
        db_session.add(poi)
    await db_session.commit()

    return pois


class TestTripCRUD:
    """Tests for trip CRUD operations."""

    async def test_create_trip(
        self,
        authenticated_client: tuple[AsyncClient, dict],
        test_city_for_trip: City,
    ):
        """Test creating a new trip."""
        client, user = authenticated_client

        response = await client.post(
            "/api/v1/trips",
            json={
                "name": "Barcelona Adventure",
                "destination_city_id": str(test_city_for_trip.id),
                "start_date": "2024-06-01",
                "end_date": "2024-06-07",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Barcelona Adventure"
        assert data["destination_city"]["id"] == str(test_city_for_trip.id)
        assert data["status"] == "draft"
        assert "id" in data

    async def test_create_trip_unauthenticated(
        self, client: AsyncClient, test_city_for_trip: City
    ):
        """Test creating a trip without authentication fails."""
        response = await client.post(
            "/api/v1/trips",
            json={
                "name": "Test Trip",
                "destination_city_id": str(test_city_for_trip.id),
            },
        )

        assert response.status_code == 401

    async def test_list_trips(
        self,
        authenticated_client: tuple[AsyncClient, dict],
        test_city_for_trip: City,
    ):
        """Test listing user's trips."""
        client, user = authenticated_client

        # Create a trip first
        await client.post(
            "/api/v1/trips",
            json={
                "name": "Trip 1",
                "destination_city_id": str(test_city_for_trip.id),
            },
        )

        response = await client.get("/api/v1/trips")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(trip["name"] == "Trip 1" for trip in data)

    async def test_get_trip_detail(
        self,
        authenticated_client: tuple[AsyncClient, dict],
        test_city_for_trip: City,
    ):
        """Test getting trip details."""
        client, user = authenticated_client

        # Create a trip
        create_response = await client.post(
            "/api/v1/trips",
            json={
                "name": "Detail Test Trip",
                "destination_city_id": str(test_city_for_trip.id),
            },
        )
        trip_id = create_response.json()["id"]

        # Get details
        response = await client.get(f"/api/v1/trips/{trip_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == trip_id
        assert data["name"] == "Detail Test Trip"
        assert "pois" in data  # Should include POI list

    async def test_update_trip(
        self,
        authenticated_client: tuple[AsyncClient, dict],
        test_city_for_trip: City,
    ):
        """Test updating a trip."""
        client, user = authenticated_client

        # Create a trip
        create_response = await client.post(
            "/api/v1/trips",
            json={
                "name": "Original Name",
                "destination_city_id": str(test_city_for_trip.id),
            },
        )
        trip_id = create_response.json()["id"]

        # Update it
        response = await client.patch(
            f"/api/v1/trips/{trip_id}",
            json={"name": "Updated Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    async def test_delete_trip(
        self,
        authenticated_client: tuple[AsyncClient, dict],
        test_city_for_trip: City,
    ):
        """Test deleting a trip."""
        client, user = authenticated_client

        # Create a trip
        create_response = await client.post(
            "/api/v1/trips",
            json={
                "name": "To Delete",
                "destination_city_id": str(test_city_for_trip.id),
            },
        )
        trip_id = create_response.json()["id"]

        # Delete it
        response = await client.delete(f"/api/v1/trips/{trip_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = await client.get(f"/api/v1/trips/{trip_id}")
        assert get_response.status_code == 404

    async def test_get_trip_not_owner(
        self,
        authenticated_client: tuple[AsyncClient, dict],
        client: AsyncClient,
        test_city_for_trip: City,
        sample_user_data: dict,
    ):
        """Test accessing another user's trip fails."""
        auth_client, user = authenticated_client

        # Create a trip as first user
        create_response = await auth_client.post(
            "/api/v1/trips",
            json={
                "name": "Private Trip",
                "destination_city_id": str(test_city_for_trip.id),
            },
        )
        trip_id = create_response.json()["id"]

        # Register a second user
        second_user_data = {
            **sample_user_data,
            "email": "second@example.com",
        }
        second_response = await client.post("/api/v1/auth/register", json=second_user_data)
        second_token = second_response.json()["tokens"]["access_token"]

        # Try to access the trip as second user
        response = await client.get(
            f"/api/v1/trips/{trip_id}",
            headers={"Authorization": f"Bearer {second_token}"},
        )

        assert response.status_code == 404  # Should not find trip


class TestTripPOIs:
    """Tests for trip POI management."""

    async def test_add_poi_to_trip(
        self,
        authenticated_client: tuple[AsyncClient, dict],
        test_city_for_trip: City,
        test_pois_for_trip: list[POI],
    ):
        """Test adding a POI to a trip."""
        client, user = authenticated_client

        # Create a trip
        create_response = await client.post(
            "/api/v1/trips",
            json={
                "name": "POI Test Trip",
                "destination_city_id": str(test_city_for_trip.id),
            },
        )
        trip_id = create_response.json()["id"]

        # Add a POI
        poi = test_pois_for_trip[0]
        response = await client.post(
            f"/api/v1/trips/{trip_id}/pois",
            json={
                "poi_id": str(poi.id),
                "day_number": 1,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["pois"]) == 1
        assert data["pois"][0]["poi"]["id"] == str(poi.id)

    async def test_remove_poi_from_trip(
        self,
        authenticated_client: tuple[AsyncClient, dict],
        test_city_for_trip: City,
        test_pois_for_trip: list[POI],
    ):
        """Test removing a POI from a trip."""
        client, user = authenticated_client

        # Create a trip
        create_response = await client.post(
            "/api/v1/trips",
            json={
                "name": "POI Remove Test",
                "destination_city_id": str(test_city_for_trip.id),
            },
        )
        trip_id = create_response.json()["id"]

        # Add a POI
        poi = test_pois_for_trip[0]
        await client.post(
            f"/api/v1/trips/{trip_id}/pois",
            json={"poi_id": str(poi.id)},
        )

        # Remove the POI
        response = await client.delete(f"/api/v1/trips/{trip_id}/pois/{poi.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["pois"]) == 0


class TestTripSharing:
    """Tests for trip sharing functionality."""

    async def test_generate_share_link(
        self,
        authenticated_client: tuple[AsyncClient, dict],
        test_city_for_trip: City,
    ):
        """Test generating a share link for a trip."""
        client, user = authenticated_client

        # Create a trip
        create_response = await client.post(
            "/api/v1/trips",
            json={
                "name": "Shareable Trip",
                "destination_city_id": str(test_city_for_trip.id),
            },
        )
        trip_id = create_response.json()["id"]

        # Generate share link
        response = await client.post(f"/api/v1/trips/{trip_id}/share")

        assert response.status_code == 200
        data = response.json()
        assert "share_token" in data
        assert "share_url" in data

    async def test_view_shared_trip(
        self,
        authenticated_client: tuple[AsyncClient, dict],
        client: AsyncClient,  # Unauthenticated client
        test_city_for_trip: City,
    ):
        """Test viewing a shared trip without authentication."""
        auth_client, user = authenticated_client

        # Create a trip
        create_response = await auth_client.post(
            "/api/v1/trips",
            json={
                "name": "Public Trip",
                "destination_city_id": str(test_city_for_trip.id),
            },
        )
        trip_id = create_response.json()["id"]

        # Generate share link
        share_response = await auth_client.post(f"/api/v1/trips/{trip_id}/share")
        share_token = share_response.json()["share_token"]

        # View shared trip without auth
        response = await client.get(f"/api/v1/shared/{share_token}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Public Trip"

    async def test_revoke_share_link(
        self,
        authenticated_client: tuple[AsyncClient, dict],
        client: AsyncClient,
        test_city_for_trip: City,
    ):
        """Test revoking a share link."""
        auth_client, user = authenticated_client

        # Create a trip and share it
        create_response = await auth_client.post(
            "/api/v1/trips",
            json={
                "name": "Revoke Test Trip",
                "destination_city_id": str(test_city_for_trip.id),
            },
        )
        trip_id = create_response.json()["id"]

        share_response = await auth_client.post(f"/api/v1/trips/{trip_id}/share")
        share_token = share_response.json()["share_token"]

        # Revoke the share link
        revoke_response = await auth_client.delete(f"/api/v1/trips/{trip_id}/share")
        assert revoke_response.status_code == 200

        # Verify shared link no longer works
        response = await client.get(f"/api/v1/shared/{share_token}")
        assert response.status_code == 404
