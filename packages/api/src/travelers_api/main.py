import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .clients.omen import close_omen_client, init_omen_client
from .clients.wikidata import WikidataClient
from .clients.wikipedia import WikipediaClient
from .core.cache import get_redis
from .core.config import get_settings
from .core.database import engine
from .routers import auth, cities, health, itineraries, omen, pois, shared, trips

logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    # Startup
    logger.info(f"Starting {settings.app_name}...")

    # Validate database connection
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection verified")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

    # Initialize Redis connection pool
    try:
        redis = await get_redis()
        await redis.ping()
        logger.info("Redis connection verified")
    except Exception as e:
        logger.warning(f"Redis connection failed (caching disabled): {e}")

    # Validate LLM configuration if enabled
    if settings.llm_provider != "none":
        try:
            settings.validate_llm_config()
            logger.info(f"LLM provider configured: {settings.llm_provider}")
        except ValueError as e:
            logger.warning(f"LLM configuration invalid: {e}")

    # Initialize Omen AI Engine client if enabled
    if settings.omen_enabled:
        try:
            await init_omen_client(
                url=settings.omen_ws_url,
                api_key=settings.omen_api_key,
            )
            logger.info(f"Omen AI Engine connected at {settings.omen_ws_url}")
        except Exception as e:
            logger.warning(f"Omen connection failed (AI insights disabled): {e}")
    else:
        logger.info("Omen AI Engine disabled")

    logger.info(f"CORS allowed origins: {settings.allowed_origins}")
    logger.info(f"{settings.app_name} started successfully")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.app_name}...")

    # Close Omen connection
    if settings.omen_enabled:
        await close_omen_client()
        logger.info("Omen connection closed")

    # Close HTTP client connections
    await WikidataClient.close_client()
    await WikipediaClient.close_clients()
    logger.info("HTTP clients closed")

    await engine.dispose()
    logger.info("Database connections closed")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI-powered travel planning with educational POI content",
    lifespan=lifespan,
)

# CORS - use allowed_origins from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
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
app.include_router(omen.router, prefix=settings.api_v1_prefix, tags=["Omen AI"])
