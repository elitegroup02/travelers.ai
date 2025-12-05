from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "travelers-api"}


@router.get("/")
async def root():
    return {"message": "Welcome to travelers.ai API", "docs": "/docs"}
