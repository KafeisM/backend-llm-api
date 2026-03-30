"""
FastAPI application entry point.

Creates and configures the FastAPI application instance,
registers routes, sets up lifespan events, and configures
global error handling and request logging middleware.
"""

import time
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.api.routes_chat import router as chat_router
from app.db.session import init_db
from app.db.seed import seed_database

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

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

    # Initialize database tables and seed with knowledge data
    init_db()
    seed_database()
    logger.info("Database initialized and seeded")

    yield
    # --- Shutdown lifespan (yield) ---
    logger.info("Shutting down Backend LLM API")


# ---------------------------------------------------------------------------
# Application instance
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Backend LLM API",
    description="REST API that integrates with OpenRouter LLM using internal knowledge context.",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return a consistent JSON error for Pydantic validation failures.

    FastAPI's default 422 response includes the full Pydantic error list,
    which can be verbose. We map it to our standard ErrorResponse shape
    while preserving useful detail for debugging.
    """
    # Build a human-readable summary of validation errors
    error_details = []
    for error in exc.errors():
        loc = " -> ".join(str(part) for part in error["loc"])
        error_details.append(f"{loc}: {error['msg']}")

    detail_text = "; ".join(error_details)
    logger.warning("Validation error on %s: %s", request.url.path, detail_text)

    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "detail": detail_text,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catch-all for any unhandled exceptions that escape route handlers.

    Ensures the API never returns raw stack traces to clients.
    """
    logger.error(
        "Unhandled exception on %s %s: %s",
        request.method,
        request.url.path,
        exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "detail": "An unexpected error occurred. Please try again later.",
        },
    )


# ---------------------------------------------------------------------------
# Request logging middleware
# ---------------------------------------------------------------------------

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log every incoming request and its response time.

    Provides visibility into API usage patterns and performance
    without introducing a heavy observability dependency.
    """
    start_time = time.perf_counter()

    logger.info(
        "→ %s %s",
        request.method,
        request.url.path,
    )

    response = await call_next(request)

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        "← %s %s | status=%d | %.0fms",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )

    return response


# ---------------------------------------------------------------------------
# Register routes
# ---------------------------------------------------------------------------

app.include_router(chat_router)
