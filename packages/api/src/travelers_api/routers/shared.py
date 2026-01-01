"""Shared trip viewing router (public, no auth required)."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.database import get_db
from ..models.itinerary import Itinerary
from ..models.trip import Trip, TripPOI

router = APIRouter(prefix="/shared")


# Response schemas (simplified for public view)
class SharedPOIResponse(BaseModel):
    """POI in a shared trip."""

    id: str
    name: str
    poi_type: str | None
    image_url: str | None
    day_number: int | None
    estimated_visit_duration: int


class SharedScheduleItem(BaseModel):
    """Schedule item in shared itinerary."""

    poi_name: str
    poi_type: str | None
    start_time: str
    end_time: str
    duration_minutes: int


class SharedDayItinerary(BaseModel):
    """Day's itinerary in shared view."""

    day_number: int
    date: date | None
    schedule: list[SharedScheduleItem]


class SharedTripResponse(BaseModel):
    """Shared trip response (public view)."""

    name: str
    destination_city: str
    destination_country: str
    start_date: date | None
    end_date: date | None
    poi_count: int
    pois: list[SharedPOIResponse]
    itinerary: list[SharedDayItinerary] | None


@router.get("/{share_token}", response_model=SharedTripResponse)
async def get_shared_trip(
    share_token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SharedTripResponse:
    """View a shared trip (no authentication required).

    Returns trip details, POIs, and itinerary if generated.
    """
    # Find trip by share token
    stmt = (
        select(Trip)
        .options(
            selectinload(Trip.destination_city),
            selectinload(Trip.trip_pois).selectinload(TripPOI.poi),
        )
        .where(Trip.share_token == share_token)
    )
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared trip not found or link has expired",
        )

    # Get itinerary if exists
    it_stmt = select(Itinerary).where(Itinerary.trip_id == trip.id).order_by(Itinerary.day_number)
    it_result = await db.execute(it_stmt)
    itineraries = it_result.scalars().all()

    itinerary_days = None
    if itineraries:
        itinerary_days = [
            SharedDayItinerary(
                day_number=it.day_number,
                date=it.date,
                schedule=[
                    SharedScheduleItem(
                        poi_name=item.get("poi_name", ""),
                        poi_type=item.get("poi_type"),
                        start_time=item.get("start_time", ""),
                        end_time=item.get("end_time", ""),
                        duration_minutes=item.get("duration_minutes", 0),
                    )
                    for item in it.schedule
                ],
            )
            for it in itineraries
        ]

    # Build POI list
    pois = [
        SharedPOIResponse(
            id=str(tp.poi.id),
            name=tp.poi.name,
            poi_type=tp.poi.poi_type,
            image_url=tp.poi.image_url,
            day_number=tp.day_number,
            estimated_visit_duration=tp.poi.estimated_visit_duration,
        )
        for tp in sorted(trip.trip_pois, key=lambda x: (x.day_number or 999, x.order_in_day or 999))
    ]

    return SharedTripResponse(
        name=trip.name,
        destination_city=trip.destination_city.name,
        destination_country=trip.destination_city.country,
        start_date=trip.start_date,
        end_date=trip.end_date,
        poi_count=len(pois),
        pois=pois,
        itinerary=itinerary_days,
    )
