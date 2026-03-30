"""
Chat orchestration service.

Coordinates the full chat flow:
    1. Retrieve relevant context from the internal knowledge base
    2. Build the prompt with system instructions + context + user message
    3. Call OpenRouter to generate a response
    4. Extract and return the result

This module keeps all business logic out of the route handler,
making it easier to test and maintain.
"""

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.prompts import build_prompt_messages
from app.services.retrieval_service import retrieve_context, format_context
from app.services.openrouter_service import call_openrouter, extract_message

logger = get_logger(__name__)


class ChatResult:
    """Holds the result of a chat interaction.

    Attributes:
        message: The LLM-generated response text.
        model: The model identifier used for generation.
        used_context: Whether internal knowledge was used.
        sources: List of source titles from matched knowledge entries.
    """

    def __init__(
        self,
        message: str,
        model: str,
        used_context: bool,
        sources: list[str],
    ):
        self.message = message
        self.model = model
        self.used_context = used_context
        self.sources = sources


async def handle_chat(db: Session, user_message: str) -> ChatResult:
    """Orchestrate the full chat pipeline.

    This is the main entry point called by the route handler.
    It coordinates all the steps needed to produce a grounded LLM response.

    Args:
        db: Active database session for knowledge retrieval.
        user_message: The user's question or message.

    Returns:
        A ChatResult with the response and metadata.

    Raises:
        app.services.openrouter_service.OpenRouterError: On upstream API errors.
        httpx.TimeoutException: If OpenRouter doesn't respond in time.
        KeyError: If the OpenRouter response has an unexpected format.
    """
    # Step 1: Retrieve relevant internal context
    logger.info("Processing chat message: '%s'", user_message[:80])
    entries = retrieve_context(db, user_message)

    # Step 2: Format context for the prompt
    context_text = format_context(entries)
    used_context = len(entries) > 0
    sources = [entry.title for entry in entries]

    if used_context:
        logger.info(
            "Using %d knowledge entries as context: %s",
            len(entries),
            sources,
        )
    else:
        logger.info("No relevant internal context found")

    # Step 3: Build the prompt messages
    messages = build_prompt_messages(
        user_message=user_message,
        context=context_text,
    )

    # Step 4: Call OpenRouter
    raw_response = await call_openrouter(messages)

    # Step 5: Extract the assistant's message
    response_text = extract_message(raw_response)

    logger.info(
        "Chat completed | context_used=%s | sources=%d | response_length=%d",
        used_context,
        len(sources),
        len(response_text),
    )

    return ChatResult(
        message=response_text,
        model=settings.openrouter_model,
        used_context=used_context,
        sources=sources,
    )
