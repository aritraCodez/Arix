"""
FastAPI application entry point.
Sets up middleware, routers, and lifecycle events.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routers.signals import router as signals_router
from services.ml_predictor import init_predictor
from utils.rate_limiter import RateLimiterMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown logic."""
    settings = get_settings()

    # Initialize ML predictor
    predictor = init_predictor(
        model_path=settings.ML_MODEL_PATH,
        enabled=settings.ML_ENABLED,
    )
    if predictor.enabled:
        logger.info("ML predictor initialized and ready")
    else:
        logger.info("ML predictor disabled (set ML_ENABLED=true to enable)")

    logger.info("🚀 Trading Signal API started")
    logger.info(f"   Cache TTL: crypto={settings.CACHE_TTL_CRYPTO}s, other={settings.CACHE_TTL_OTHER}s")
    logger.info(f"   Rate limit: {settings.RATE_LIMIT_PER_MINUTE} req/min")

    yield

    logger.info("Trading Signal API shutting down")


# Create FastAPI app
app = FastAPI(
    title="Trading Signal API",
    description="Real-time trading signals powered by technical analysis and optional ML predictions",
    version="1.0.0",
    lifespan=lifespan,
)

# --- Middleware ---

# CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.add_middleware(
    RateLimiterMiddleware,
    requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
)

# --- Routers ---
app.include_router(signals_router)


# --- Health Check ---
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and deployment."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "ml_enabled": settings.ML_ENABLED,
    }

