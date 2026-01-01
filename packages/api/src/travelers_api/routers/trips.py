"""Trip management router."""

import secrets
from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.database import get_db
from ..dependencies.auth import CurrentUser
from ..models.city import City
from ..models.poi import POI
from ..models.trip import Trip, TripPOI

router = APIRouter(prefix="/trips")


# Request/Response schemas
class CreateTripRequest(BaseModel):
    """Create trip request."""

    name: str = Field(..., min_length=1, max_length=255)
    destination_city_id: UUID
    start_date: date | None = None
    end_date: date | None = None


class UpdateTripRequest(BaseModel):
    """Update trip request."""

    name: str | None = Field(None, min_length=1, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = Field(None, pattern="^(draft|planned|active|completed|archived)$")


class AddPOIRequest(BaseModel):
    """Add POI to trip request."""

    poi_id: UUID
    day_number: int | None = None
    order_in_day: int | None = None
    is_must_see: bool = False
    user_notes: str | None = None


class UpdateTripPOIRequest(BaseModel):
    """Update trip POI request."""

    day_number: int | None = None
    order_in_day: int | None = None
    is_must_see: bool | None = None
    user_notes: str | None = None


class TripPOIResponse(BaseModel):
    """Trip POI response."""

    id: str
    poi_id: str
    poi_name: str
    poi_type: str | None
    image_url: str | None
    day_number: int | None
    order_in_day: int | None
    is_must_see: bool
    user_notes: str | None


class TripResponse(BaseModel):
    """Trip response."""

    id: str
    name: str
    destination_city_id: str
    destination_city_name: str
    start_date: date | None
    end_date: date | None
    status: str
    share_token: str | None
    poi_count: int
    created_at: str
    updated_at: str


class TripDetailResponse(TripResponse):
    """Trip detail response with POIs."""

    pois: list[TripPOIResponse]


class TripsListResponse(BaseModel):
    """List of trips response."""

    items: list[TripResponse]
    total: int


class ShareTokenResponse(BaseModel):
    """Share token response."""

    share_token: str
    share_url: str


@router.get("", response_model=TripsListResponse)
async def list_trips(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> TripsListResponse:
    """Get user's trips with optional status filter."""
    base_filter = Trip.user_id == current_user.id
    if status_filter:
        base_filter = base_filter & (Trip.status == status_filter)

    # Get total count
    count_stmt = select(Trip).where(base_filter)
    count_result = await db.execute(count_stmt)
    total = len(count_result.all())

    # Get trips with city info
    stmt = (
        select(Trip)
        .options(selectinload(Trip.destination_city), selectinload(Trip.trip_pois))
        .where(base_filter)
        .order_by(Trip.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    trips = result.scalars().all()

    return TripsListResponse(
        items=[
            TripResponse(
                id=str(trip.id),
                name=trip.name,
                destination_city_id=str(trip.destination_city_id),
                destination_city_name=trip.destination_city.name,
                start_date=trip.start_date,
                end_date=trip.end_date,
                status=trip.status,
                share_token=trip.share_token,
                poi_count=len(trip.trip_pois),
                created_at=trip.created_at.isoformat(),
                updated_at=trip.updated_at.isoformat(),
            )
            for trip in trips
        ],
        total=total,
    )


@router.post("", response_model=TripDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(
    request: CreateTripRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TripDetailResponse:
    """Create a new trip."""
    # Verify city exists
    stmt = select(City).where(City.id == request.destination_city_id)
    result = await db.execute(stmt)
    city = result.scalar_one_or_none()

    if not city:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="City not found",
        )

    # Validate dates
    if request.start_date and request.end_date:
        if request.end_date < request.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date",
            )

    # Create trip
    trip = Trip(
        user_id=current_user.id,
        destination_city_id=request.destination_city_id,
        name=request.name,
        start_date=request.start_date,
        end_date=request.end_date,
        status="draft",
    )
    db.add(trip)
    await db.commit()
    await db.refresh(trip)

    return TripDetailResponse(
        id=str(trip.id),
        name=trip.name,
        destination_city_id=str(trip.destination_city_id),
        destination_city_name=city.name,
        start_date=trip.start_date,
        end_date=trip.end_date,
        status=trip.status,
        share_token=trip.share_token,
        poi_count=0,
        created_at=trip.created_at.isoformat(),
        updated_at=trip.updated_at.isoformat(),
        pois=[],
    )


@router.get("/{trip_id}", response_model=TripDetailResponse)
async def get_trip(
    trip_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TripDetailResponse:
    """Get trip details with POIs."""
    stmt = (
        select(Trip)
        .options(
            selectinload(Trip.destination_city),
            selectinload(Trip.trip_pois).selectinload(TripPOI.poi),
        )
        .where(Trip.id == trip_id, Trip.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )

    return TripDetailResponse(
        id=str(trip.id),
        name=trip.name,
        destination_city_id=str(trip.destination_city_id),
        destination_city_name=trip.destination_city.name,
        start_date=trip.start_date,
        end_date=trip.end_date,
        status=trip.status,
        share_token=trip.share_token,
        poi_count=len(trip.trip_pois),
        created_at=trip.created_at.isoformat(),
        updated_at=trip.updated_at.isoformat(),
        pois=[
            TripPOIResponse(
                id=str(tp.id),
                poi_id=str(tp.poi_id),
                poi_name=tp.poi.name,
                poi_type=tp.poi.poi_type,
                image_url=tp.poi.image_url,
                day_number=tp.day_number,
                order_in_day=tp.order_in_day,
                is_must_see=tp.is_must_see,
                user_notes=tp.user_notes,
            )
            for tp in sorted(trip.trip_pois, key=lambda x: (x.day_number or 999, x.order_in_day or 999))
        ],
    )


@router.patch("/{trip_id}", response_model=TripDetailResponse)
async def update_trip(
    trip_id: UUID,
    request: UpdateTripRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TripDetailResponse:
    """Update trip details."""
    stmt = (
        select(Trip)
        .options(
            selectinload(Trip.destination_city),
            selectinload(Trip.trip_pois).selectinload(TripPOI.poi),
        )
        .where(Trip.id == trip_id, Trip.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )

    # Update fields
    if request.name is not None:
        trip.name = request.name
    if request.start_date is not None:
        trip.start_date = request.start_date
    if request.end_date is not None:
        trip.end_date = request.end_date
    if request.status is not None:
        trip.status = request.status

    # Validate dates
    if trip.start_date and trip.end_date and trip.end_date < trip.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date",
        )

    await db.commit()
    await db.refresh(trip)

    return TripDetailResponse(
        id=str(trip.id),
        name=trip.name,
        destination_city_id=str(trip.destination_city_id),
        destination_city_name=trip.destination_city.name,
        start_date=trip.start_date,
        end_date=trip.end_date,
        status=trip.status,
        share_token=trip.share_token,
        poi_count=len(trip.trip_pois),
        created_at=trip.created_at.isoformat(),
        updated_at=trip.updated_at.isoformat(),
        pois=[
            TripPOIResponse(
                id=str(tp.id),
                poi_id=str(tp.poi_id),
                poi_name=tp.poi.name,
                poi_type=tp.poi.poi_type,
                image_url=tp.poi.image_url,
                day_number=tp.day_number,
                order_in_day=tp.order_in_day,
                is_must_see=tp.is_must_see,
                user_notes=tp.user_notes,
            )
            for tp in sorted(trip.trip_pois, key=lambda x: (x.day_number or 999, x.order_in_day or 999))
        ],
    )


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(
    trip_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a trip and all associated POIs and itineraries."""
    stmt = select(Trip).where(Trip.id == trip_id, Trip.user_id == current_user.id)
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )

    await db.delete(trip)
    await db.commit()


@router.post("/{trip_id}/pois", response_model=TripPOIResponse, status_code=status.HTTP_201_CREATED)
async def add_poi_to_trip(
    trip_id: UUID,
    request: AddPOIRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TripPOIResponse:
    """Add a POI to a trip."""
    # Verify trip exists and belongs to user
    stmt = select(Trip).where(Trip.id == trip_id, Trip.user_id == current_user.id)
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )

    # Verify POI exists
    poi_stmt = select(POI).where(POI.id == request.poi_id)
    poi_result = await db.execute(poi_stmt)
    poi = poi_result.scalar_one_or_none()

    if not poi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="POI not found",
        )

    # Check if POI is already in trip
    existing_stmt = select(TripPOI).where(
        TripPOI.trip_id == trip_id,
        TripPOI.poi_id == request.poi_id,
    )
    existing_result = await db.execute(existing_stmt)
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="POI already added to trip",
        )

    # Add POI to trip
    trip_poi = TripPOI(
        trip_id=trip_id,
        poi_id=request.poi_id,
        day_number=request.day_number,
        order_in_day=request.order_in_day,
        is_must_see=request.is_must_see,
        user_notes=request.user_notes,
    )
    db.add(trip_poi)
    await db.commit()
    await db.refresh(trip_poi)

    return TripPOIResponse(
        id=str(trip_poi.id),
        poi_id=str(trip_poi.poi_id),
        poi_name=poi.name,
        poi_type=poi.poi_type,
        image_url=poi.image_url,
        day_number=trip_poi.day_number,
        order_in_day=trip_poi.order_in_day,
        is_must_see=trip_poi.is_must_see,
        user_notes=trip_poi.user_notes,
    )


@router.patch("/{trip_id}/pois/{poi_id}", response_model=TripPOIResponse)
async def update_trip_poi(
    trip_id: UUID,
    poi_id: UUID,
    request: UpdateTripPOIRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TripPOIResponse:
    """Update a POI's details within a trip."""
    # Verify trip belongs to user
    trip_stmt = select(Trip).where(Trip.id == trip_id, Trip.user_id == current_user.id)
    trip_result = await db.execute(trip_stmt)
    if not trip_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )

    # Get trip POI
    stmt = (
        select(TripPOI)
        .options(selectinload(TripPOI.poi))
        .where(TripPOI.trip_id == trip_id, TripPOI.poi_id == poi_id)
    )
    result = await db.execute(stmt)
    trip_poi = result.scalar_one_or_none()

    if not trip_poi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="POI not in trip",
        )

    # Update fields
    if request.day_number is not None:
        trip_poi.day_number = request.day_number
    if request.order_in_day is not None:
        trip_poi.order_in_day = request.order_in_day
    if request.is_must_see is not None:
        trip_poi.is_must_see = request.is_must_see
    if request.user_notes is not None:
        trip_poi.user_notes = request.user_notes

    await db.commit()
    await db.refresh(trip_poi)

    return TripPOIResponse(
        id=str(trip_poi.id),
        poi_id=str(trip_poi.poi_id),
        poi_name=trip_poi.poi.name,
        poi_type=trip_poi.poi.poi_type,
        image_url=trip_poi.poi.image_url,
        day_number=trip_poi.day_number,
        order_in_day=trip_poi.order_in_day,
        is_must_see=trip_poi.is_must_see,
        user_notes=trip_poi.user_notes,
    )


@router.delete("/{trip_id}/pois/{poi_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_poi_from_trip(
    trip_id: UUID,
    poi_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Remove a POI from a trip."""
    # Verify trip belongs to user
    trip_stmt = select(Trip).where(Trip.id == trip_id, Trip.user_id == current_user.id)
    trip_result = await db.execute(trip_stmt)
    if not trip_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )

    # Find and delete trip POI
    stmt = select(TripPOI).where(TripPOI.trip_id == trip_id, TripPOI.poi_id == poi_id)
    result = await db.execute(stmt)
    trip_poi = result.scalar_one_or_none()

    if not trip_poi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="POI not in trip",
        )

    await db.delete(trip_poi)
    await db.commit()


@router.post("/{trip_id}/share", response_model=ShareTokenResponse)
async def generate_share_token(
    trip_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ShareTokenResponse:
    """Generate a share token for a trip."""
    stmt = select(Trip).where(Trip.id == trip_id, Trip.user_id == current_user.id)
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )

    # Generate or return existing token
    if not trip.share_token:
        trip.share_token = secrets.token_urlsafe(32)
        await db.commit()
        await db.refresh(trip)

    return ShareTokenResponse(
        share_token=trip.share_token,
        share_url=f"/shared/{trip.share_token}",
    )


@router.delete("/{trip_id}/share", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_share_token(
    trip_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Revoke the share token for a trip."""
    stmt = select(Trip).where(Trip.id == trip_id, Trip.user_id == current_user.id)
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )

    trip.share_token = None
    await db.commit()
