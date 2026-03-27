"""
Pydantic schemas for chat endpoint request and response validation.

These models act as contracts that define the exact shape of data
flowing in and out of the API. FastAPI uses them automatically to:
- validate incoming request bodies
- serialize outgoing responses
- generate API documentation in /docs
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Schema for incoming chat messages.

    Example:
        {"message": "How many partners does the company have?"}
    """

    message: str = Field(
        ...,  # "..." means this field is REQUIRED (cannot be omitted)
        min_length=1,  # Reject empty strings
        max_length=2000,  # Prevent excessively long messages
        description="The user's question or message.",
        examples=["How many partners does the company have?"],
    )


class ChatResponse(BaseModel):
    """Schema for chat endpoint responses.

    Always includes 'message'. Optional fields provide
    transparency about how the response was generated.

    Example:
        {
            "message": "The company has 5 partners...",
            "model": "meta-llama/llama-3.1-8b-instruct:free",
            "used_context": true,
            "sources": ["company_overview"]
        }
    """

    message: str = Field(
        ...,
        description="The generated response from the LLM.",
    )
    model: str | None = Field(
        default=None,
        description="The LLM model used to generate the response.",
    )
    used_context: bool = Field(
        default=False,
        description="Whether internal knowledge context was used.",
    )
    sources: list[str] = Field(
        default_factory=list,
        description="List of internal knowledge sources used for context.",
    )


class ErrorResponse(BaseModel):
    """Schema for consistent error responses across the API.

    Example:
        {"error": "UPSTREAM_LLM_ERROR", "detail": "OpenRouter request failed"}
    """

    error: str = Field(
        ...,
        description="Error code identifier (e.g., INVALID_INPUT, UPSTREAM_LLM_ERROR).",
    )
    detail: str = Field(
        ...,
        description="Human-readable error description.",
    )
