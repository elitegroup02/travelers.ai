"""Itinerary generation and export router."""

import io
from datetime import date, datetime, time, timedelta
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.database import get_db
from ..dependencies.auth import CurrentUser
from ..models.itinerary import Itinerary
from ..models.trip import Trip, TripPOI

router = APIRouter(prefix="/trips")


# Request/Response schemas
class GenerateItineraryRequest(BaseModel):
    """Generate itinerary request."""

    start_time: str = Field(default="09:00", pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(default="18:00", pattern=r"^\d{2}:\d{2}$")
    lunch_break_start: str | None = Field(default="13:00", pattern=r"^\d{2}:\d{2}$")
    lunch_break_duration: int = Field(default=60, ge=0, le=180)  # minutes


class UpdateDayRequest(BaseModel):
    """Update a day's schedule."""

    schedule: list[dict[str, Any]]


class ScheduleItem(BaseModel):
    """A single item in the daily schedule."""

    poi_id: str
    poi_name: str
    poi_type: str | None
    start_time: str
    end_time: str
    duration_minutes: int
    travel_minutes: int | None
    notes: str | None


class DayItinerary(BaseModel):
    """A day's itinerary."""

    day_number: int
    date: date | None
    schedule: list[ScheduleItem]
    total_duration_minutes: int
    total_travel_minutes: int


class ItineraryResponse(BaseModel):
    """Full itinerary response."""

    trip_id: str
    days: list[DayItinerary]
    generated_at: str


@router.post("/{trip_id}/itinerary", response_model=ItineraryResponse)
async def generate_itinerary(
    trip_id: UUID,
    request: GenerateItineraryRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ItineraryResponse:
    """Generate an itinerary for a trip based on its POIs.

    Groups POIs by their assigned day_number and creates a schedule.
    POIs without a day_number are distributed across available days.
    """
    # Get trip with POIs
    stmt = (
        select(Trip)
        .options(selectinload(Trip.trip_pois).selectinload(TripPOI.poi))
        .where(Trip.id == trip_id, Trip.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )

    if not trip.trip_pois:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trip has no POIs to schedule",
        )

    # Calculate number of days
    if trip.start_date and trip.end_date:
        num_days = (trip.end_date - trip.start_date).days + 1
    else:
        # Default to grouping by max day_number or 1 day
        max_day = max((tp.day_number or 1 for tp in trip.trip_pois), default=1)
        num_days = max(max_day, 1)

    # Parse times
    start_hour, start_min = map(int, request.start_time.split(":"))
    end_hour, end_min = map(int, request.end_time.split(":"))
    daily_minutes = (end_hour * 60 + end_min) - (start_hour * 60 + start_min)

    # Group POIs by day
    pois_by_day: dict[int, list[TripPOI]] = {day: [] for day in range(1, num_days + 1)}

    # First pass: assign POIs with explicit day_number
    unassigned = []
    for tp in trip.trip_pois:
        if tp.day_number and 1 <= tp.day_number <= num_days:
            pois_by_day[tp.day_number].append(tp)
        else:
            unassigned.append(tp)

    # Second pass: distribute unassigned POIs (prioritize must-see)
    unassigned.sort(key=lambda x: (not x.is_must_see, x.order_in_day or 999))
    current_day = 1
    for tp in unassigned:
        pois_by_day[current_day].append(tp)
        current_day = (current_day % num_days) + 1

    # Delete existing itineraries for this trip
    await db.execute(delete(Itinerary).where(Itinerary.trip_id == trip_id))

    # Generate schedule for each day
    days = []
    for day_num in range(1, num_days + 1):
        day_pois = pois_by_day[day_num]

        # Sort POIs by order_in_day, then must_see first
        day_pois.sort(key=lambda x: (x.order_in_day or 999, not x.is_must_see))

        schedule = []
        current_time = start_hour * 60 + start_min
        total_duration = 0
        total_travel = 0

        for tp in day_pois:
            if current_time >= end_hour * 60 + end_min:
                break  # Day is full

            poi = tp.poi
            duration = poi.estimated_visit_duration or 60
            travel = 15  # Default 15 min between POIs

            schedule.append({
                "poi_id": str(poi.id),
                "poi_name": poi.name,
                "poi_type": poi.poi_type,
                "start_time": f"{current_time // 60:02d}:{current_time % 60:02d}",
                "end_time": f"{(current_time + duration) // 60:02d}:{(current_time + duration) % 60:02d}",
                "duration_minutes": duration,
                "travel_minutes": travel if schedule else None,  # No travel for first POI
                "notes": tp.user_notes,
            })

            total_duration += duration
            if schedule and len(schedule) > 1:
                total_travel += travel
            current_time += duration + travel

        # Calculate day date
        day_date = None
        if trip.start_date:
            day_date = trip.start_date + timedelta(days=day_num - 1)

        # Create itinerary record
        itinerary = Itinerary(
            trip_id=trip_id,
            day_number=day_num,
            date=day_date,
            schedule=schedule,
            total_duration_minutes=total_duration,
            total_travel_minutes=total_travel,
        )
        db.add(itinerary)

        days.append(DayItinerary(
            day_number=day_num,
            date=day_date,
            schedule=[ScheduleItem(**item) for item in schedule],
            total_duration_minutes=total_duration,
            total_travel_minutes=total_travel,
        ))

    await db.commit()

    return ItineraryResponse(
        trip_id=str(trip_id),
        days=days,
        generated_at=datetime.utcnow().isoformat(),
    )


@router.get("/{trip_id}/itinerary", response_model=ItineraryResponse)
async def get_itinerary(
    trip_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    day: int | None = Query(None, ge=1),
) -> ItineraryResponse:
    """Get existing itinerary for a trip."""
    # Verify trip ownership
    trip_stmt = select(Trip).where(Trip.id == trip_id, Trip.user_id == current_user.id)
    trip_result = await db.execute(trip_stmt)
    if not trip_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )

    # Get itineraries
    stmt = select(Itinerary).where(Itinerary.trip_id == trip_id)
    if day:
        stmt = stmt.where(Itinerary.day_number == day)
    stmt = stmt.order_by(Itinerary.day_number)

    result = await db.execute(stmt)
    itineraries = result.scalars().all()

    if not itineraries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No itinerary found. Generate one first.",
        )

    days = [
        DayItinerary(
            day_number=it.day_number,
            date=it.date,
            schedule=[ScheduleItem(**item) for item in it.schedule],
            total_duration_minutes=it.total_duration_minutes or 0,
            total_travel_minutes=it.total_travel_minutes or 0,
        )
        for it in itineraries
    ]

    return ItineraryResponse(
        trip_id=str(trip_id),
        days=days,
        generated_at=itineraries[0].generated_at.isoformat(),
    )


@router.patch("/{trip_id}/itinerary/{day_number}", response_model=DayItinerary)
async def update_day_itinerary(
    trip_id: UUID,
    day_number: int,
    request: UpdateDayRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DayItinerary:
    """Update a specific day's schedule."""
    # Verify trip ownership
    trip_stmt = select(Trip).where(Trip.id == trip_id, Trip.user_id == current_user.id)
    trip_result = await db.execute(trip_stmt)
    if not trip_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )

    # Get day itinerary
    stmt = select(Itinerary).where(
        Itinerary.trip_id == trip_id,
        Itinerary.day_number == day_number,
    )
    result = await db.execute(stmt)
    itinerary = result.scalar_one_or_none()

    if not itinerary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No itinerary for day {day_number}",
        )

    # Update schedule
    itinerary.schedule = request.schedule

    # Recalculate totals
    total_duration = sum(item.get("duration_minutes", 0) for item in request.schedule)
    total_travel = sum(item.get("travel_minutes", 0) or 0 for item in request.schedule)
    itinerary.total_duration_minutes = total_duration
    itinerary.total_travel_minutes = total_travel

    await db.commit()
    await db.refresh(itinerary)

    return DayItinerary(
        day_number=itinerary.day_number,
        date=itinerary.date,
        schedule=[ScheduleItem(**item) for item in itinerary.schedule],
        total_duration_minutes=itinerary.total_duration_minutes or 0,
        total_travel_minutes=itinerary.total_travel_minutes or 0,
    )


@router.delete("/{trip_id}/itinerary", status_code=status.HTTP_204_NO_CONTENT)
async def delete_itinerary(
    trip_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete all itineraries for a trip."""
    # Verify trip ownership
    trip_stmt = select(Trip).where(Trip.id == trip_id, Trip.user_id == current_user.id)
    trip_result = await db.execute(trip_stmt)
    if not trip_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )

    await db.execute(delete(Itinerary).where(Itinerary.trip_id == trip_id))
    await db.commit()


@router.get("/{trip_id}/export/pdf")
async def export_pdf(
    trip_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StreamingResponse:
    """Export trip itinerary as PDF."""
    # Get trip with itineraries
    stmt = (
        select(Trip)
        .options(selectinload(Trip.destination_city))
        .where(Trip.id == trip_id, Trip.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )

    # Get itineraries
    it_stmt = select(Itinerary).where(Itinerary.trip_id == trip_id).order_by(Itinerary.day_number)
    it_result = await db.execute(it_stmt)
    itineraries = it_result.scalars().all()

    if not itineraries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No itinerary found. Generate one first.",
        )

    # Generate PDF
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Heading1"],
            fontSize=24,
            spaceAfter=20,
        )
        elements.append(Paragraph(f"{trip.name}", title_style))
        elements.append(Paragraph(f"{trip.destination_city.name}", styles["Heading2"]))

        if trip.start_date and trip.end_date:
            elements.append(Paragraph(
                f"{trip.start_date.strftime('%B %d')} - {trip.end_date.strftime('%B %d, %Y')}",
                styles["Normal"],
            ))
        elements.append(Spacer(1, 0.5 * inch))

        # Each day
        for itinerary in itineraries:
            day_title = f"Day {itinerary.day_number}"
            if itinerary.date:
                day_title += f" - {itinerary.date.strftime('%A, %B %d')}"
            elements.append(Paragraph(day_title, styles["Heading2"]))

            if itinerary.schedule:
                data = [["Time", "Place", "Duration"]]
                for item in itinerary.schedule:
                    data.append([
                        f"{item.get('start_time', '')} - {item.get('end_time', '')}",
                        item.get("poi_name", ""),
                        f"{item.get('duration_minutes', 0)} min",
                    ])

                table = Table(data, colWidths=[1.5 * inch, 4 * inch, 1 * inch])
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(table)

            elements.append(Spacer(1, 0.3 * inch))

        doc.build(elements)
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={trip.name.replace(' ', '_')}_itinerary.pdf"},
        )

    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="PDF export not available (reportlab not installed)",
        )


@router.get("/{trip_id}/export/ics")
async def export_ics(
    trip_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StreamingResponse:
    """Export trip itinerary as ICS calendar."""
    # Get trip
    stmt = (
        select(Trip)
        .options(selectinload(Trip.destination_city))
        .where(Trip.id == trip_id, Trip.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )

    # Get itineraries
    it_stmt = select(Itinerary).where(Itinerary.trip_id == trip_id).order_by(Itinerary.day_number)
    it_result = await db.execute(it_stmt)
    itineraries = it_result.scalars().all()

    if not itineraries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No itinerary found. Generate one first.",
        )

    try:
        from icalendar import Calendar, Event

        cal = Calendar()
        cal.add("prodid", "-//travelers.ai//Trip Itinerary//EN")
        cal.add("version", "2.0")
        cal.add("x-wr-calname", f"{trip.name} - {trip.destination_city.name}")

        for itinerary in itineraries:
            if not itinerary.date:
                continue

            for item in itinerary.schedule:
                event = Event()
                event.add("summary", item.get("poi_name", "Visit"))

                # Parse times
                start_time = item.get("start_time", "09:00")
                end_time = item.get("end_time", "10:00")
                start_h, start_m = map(int, start_time.split(":"))
                end_h, end_m = map(int, end_time.split(":"))

                event.add("dtstart", datetime.combine(itinerary.date, time(start_h, start_m)))
                event.add("dtend", datetime.combine(itinerary.date, time(end_h, end_m)))

                if item.get("notes"):
                    event.add("description", item["notes"])

                event.add("location", trip.destination_city.name)
                cal.add_component(event)

        ics_content = cal.to_ical()
        buffer = io.BytesIO(ics_content)

        return StreamingResponse(
            buffer,
            media_type="text/calendar",
            headers={"Content-Disposition": f"attachment; filename={trip.name.replace(' ', '_')}_itinerary.ics"},
        )

    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="ICS export not available (icalendar not installed)",
        )
