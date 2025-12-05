from fastapi import APIRouter

router = APIRouter(prefix="/auth")


@router.post("/register")
async def register():
    """Create a new user account"""
    # TODO: Implement
    return {"message": "Not implemented"}


@router.post("/login")
async def login():
    """Login and get access token"""
    # TODO: Implement
    return {"message": "Not implemented"}


@router.post("/refresh")
async def refresh_token():
    """Refresh access token"""
    # TODO: Implement
    return {"message": "Not implemented"}


@router.get("/me")
async def get_current_user():
    """Get current user info"""
    # TODO: Implement
    return {"message": "Not implemented"}
