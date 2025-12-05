from fastapi import APIRouter

router = APIRouter(prefix="/shared")


@router.get("/{share_token}")
async def get_shared_trip(share_token: str):
    """View shared trip (no auth required)"""
    # TODO: Implement
    return {"message": "Not implemented"}
