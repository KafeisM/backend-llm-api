"""
Chat and health route handlers.

Defines the API endpoints for health checks and chat interactions.
Business logic is delegated to service modules — route handlers
remain thin and focused on HTTP concerns (validation, error mapping).
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse, ErrorResponse
from app.services.chat_service import handle_chat
from app.services.openrouter_service import OpenRouterError

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Lightweight health check to verify service status."""
    return {"status": "ok"}


@router.post(
    "/chat/",
    response_model=ChatResponse,
    tags=["Chat"],
    summary="Send a message and get an LLM-powered response",
    responses={
        422: {
            "model": ErrorResponse,
            "description": "Invalid input — message is missing or too long.",
        },
        502: {
            "model": ErrorResponse,
            "description": "OpenRouter upstream error.",
        },
        504: {
            "model": ErrorResponse,
            "description": "OpenRouter request timed out.",
        },
    },
)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Process a user message through the full chat pipeline.

    Flow:
        1. Validate the incoming request (handled by Pydantic)
        2. Delegate to the chat orchestration service
        3. Map any service-layer errors to proper HTTP responses
        4. Return the structured response

    Args:
        request: Validated chat request containing the user message.
        db: Database session injected by FastAPI's dependency system.

    Returns:
        ChatResponse with the LLM answer and metadata.
    """
    logger.info("POST /chat/ | message='%s'", request.message[:80])

    try:
        result = await handle_chat(db=db, user_message=request.message)

        return ChatResponse(
            message=result.message,
            model=result.model,
            used_context=result.used_context,
            sources=result.sources,
        )

    except OpenRouterError as e:
        logger.error("OpenRouter error: %s", e)
        raise HTTPException(
            status_code=502,
            detail={
                "error": "UPSTREAM_LLM_ERROR",
                "detail": f"OpenRouter returned status {e.status_code}: {e.detail[:200]}",
            },
        ) from e

    except httpx.TimeoutException as e:
        logger.error("OpenRouter timeout: %s", e)
        raise HTTPException(
            status_code=504,
            detail={
                "error": "UPSTREAM_TIMEOUT",
                "detail": "The LLM request timed out. Please try again.",
            },
        ) from e

    except httpx.ConnectError as e:
        logger.error("OpenRouter connection failed: %s", e)
        raise HTTPException(
            status_code=502,
            detail={
                "error": "UPSTREAM_UNREACHABLE",
                "detail": "Could not connect to the LLM service.",
            },
        ) from e

    except KeyError as e:
        logger.error("Unexpected LLM response format: %s", e)
        raise HTTPException(
            status_code=502,
            detail={
                "error": "UPSTREAM_INVALID_RESPONSE",
                "detail": "The LLM returned an unexpected response format.",
            },
        ) from e

    except Exception as e:
        logger.error("Unexpected error in chat endpoint: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "detail": "An unexpected error occurred. Please try again later.",
            },
        ) from e
