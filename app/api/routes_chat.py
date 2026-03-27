"""
Chat and health route handlers.

Defines the API endpoints for health checks and chat interactions.
Business logic is delegated to service modules.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Lightweight health check to verify service status."""
    return {"status": "ok"}
