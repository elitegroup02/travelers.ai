from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/trips")


class GenerateItineraryRequest(BaseModel):
    start_time: str = "09:00"
    end_time: str = "18:00"
    start_location: dict | None = None  # {lat, lng}


@router.post("/{trip_id}/itinerary")
async def generate_itinerary(trip_id: UUID, request: GenerateItineraryRequest):
    """Generate itinerary for trip"""
    # TODO: Implement
    return {"message": "Not implemented"}


@router.get("/{trip_id}/itinerary")
async def get_itinerary(trip_id: UUID, day: int | None = None):
    """Get existing itinerary"""
    # TODO: Implement
    return {"message": "Not implemented"}


@router.get("/{trip_id}/export/pdf")
async def export_pdf(trip_id: UUID):
    """Export trip as PDF"""
    # TODO: Implement
    return StreamingResponse(
        iter([b"PDF content"]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=trip-{trip_id}.pdf"},
    )


@router.get("/{trip_id}/export/ics")
async def export_ics(trip_id: UUID):
    """Export trip as ICS calendar"""
    # TODO: Implement
    return StreamingResponse(
        iter([b"ICS content"]),
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=trip-{trip_id}.ics"},
    )


@router.get("/{trip_id}/export/google-maps")
async def export_google_maps(trip_id: UUID):
    """Get Google Maps list URL"""
    # TODO: Implement
    return {"url": "https://www.google.com/maps/..."}


@router.post("/{trip_id}/share")
async def create_share_link(trip_id: UUID):
    """Generate share link for trip"""
    # TODO: Implement
    return {"share_url": f"https://travelers.ai/shared/...", "expires_at": None}
