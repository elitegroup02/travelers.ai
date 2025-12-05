from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .routers import auth, cities, health, itineraries, pois, shared, trips

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI-powered travel planning with educational POI content",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix=settings.api_v1_prefix, tags=["Auth"])
app.include_router(cities.router, prefix=settings.api_v1_prefix, tags=["Cities"])
app.include_router(pois.router, prefix=settings.api_v1_prefix, tags=["POIs"])
app.include_router(trips.router, prefix=settings.api_v1_prefix, tags=["Trips"])
app.include_router(itineraries.router, prefix=settings.api_v1_prefix, tags=["Itineraries"])
app.include_router(shared.router, prefix=settings.api_v1_prefix, tags=["Shared"])
