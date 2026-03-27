"""
FastAPI application entry point.

Creates and configures the FastAPI application instance,
registers routes, and sets up lifespan events.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.api.routes_chat import router as chat_router

logger = get_logger(__name__)

# lifespan is a pattern used in FastAPI to manage the application's lifecycle.

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: startup and shutdown events."""
    # --- Startup lifespan ---
    setup_logging()
    logger.info("Starting Backend LLM API")
    logger.info("Host: %s | Port: %s", settings.app_host, settings.app_port)
    logger.info("Model: %s", settings.openrouter_model)
    logger.info(
        "OpenRouter API key configured: %s",
        "yes" if settings.openrouter_api_key else "NO — set OPENROUTER_API_KEY",
    )
    yield
    # --- Shutdown lifespan (yield) ---
    logger.info("Shutting down Backend LLM API")

# define the FastAPI application instance
app = FastAPI(
    title="Backend LLM API",
    description="REST API that integrates with OpenRouter LLM using internal knowledge context.",
    version="1.0.0",
    lifespan=lifespan,
)

# Register routes
app.include_router(chat_router)
