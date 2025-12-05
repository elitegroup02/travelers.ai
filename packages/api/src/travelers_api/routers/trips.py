from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/trips")


class CreateTripRequest(BaseModel):
    name: str
    destination_city_id: UUID
    start_date: str | None = None
    end_date: str | None = None


class AddPOIRequest(BaseModel):
    poi_id: UUID
    day_number: int | None = None
    is_must_see: bool = False
    user_notes: str | None = None


@router.get("")
async def list_trips(status: str | None = None):
    """Get user's trips"""
    # TODO: Implement
    return {"items": [], "total": 0}


@router.post("")
async def create_trip(request: CreateTripRequest):
    """Create a new trip"""
    # TODO: Implement
    return {"message": "Not implemented"}


@router.get("/{trip_id}")
async def get_trip(trip_id: UUID):
    """Get trip details with POIs"""
    # TODO: Implement
    return {"message": "Not implemented"}


@router.patch("/{trip_id}")
async def update_trip(trip_id: UUID):
    """Update trip"""
    # TODO: Implement
    return {"message": "Not implemented"}


@router.delete("/{trip_id}")
async def delete_trip(trip_id: UUID):
    """Delete trip"""
    # TODO: Implement
    return {"message": "Deleted"}


@router.post("/{trip_id}/pois")
async def add_poi_to_trip(trip_id: UUID, request: AddPOIRequest):
    """Add POI to trip"""
    # TODO: Implement
    return {"message": "Not implemented"}


@router.delete("/{trip_id}/pois/{poi_id}")
async def remove_poi_from_trip(trip_id: UUID, poi_id: UUID):
    """Remove POI from trip"""
    # TODO: Implement
    return {"message": "Removed"}


@router.post("/{trip_id}/sync")
async def sync_trip(trip_id: UUID):
    """Sync local changes with server"""
    # TODO: Implement
    return {"message": "Not implemented"}
