"""
Prompt templates for the LLM.

Defines the system prompt and the function to build the final prompt
that gets sent to OpenRouter. The system prompt guides the LLM to:
- Use the provided internal context first
- Avoid hallucinating company-specific information
- Answer clearly and professionally
- Admit when information is not available
"""

# System prompt: sets the LLM's behavior and role
SYSTEM_PROMPT = """You are a helpful internal assistant for Nuria Tech Solutions.

Your job is to answer questions from employees using the internal company knowledge provided below.

Rules:
- ALWAYS prioritize the internal context provided. If the answer is in the context, use it.
- Be concise and professional.
- If the internal context does not contain enough information to answer the question, say so honestly. Do NOT invent company-specific information.
- You may use general knowledge to complement your answers, but clearly distinguish between what comes from internal data and what is general knowledge.
- Answer in the same language the user asks in."""


def build_prompt_messages(
    user_message: str,
    context: str,
) -> list[dict[str, str]]:
    """Build the list of messages to send to the LLM.

    Constructs the standard chat format:
    1. System message (behavior instructions + context)
    2. User message (the actual question)

    Args:
        user_message: The user's question.
        context: Formatted internal knowledge context (can be empty).

    Returns:
        List of message dicts with 'role' and 'content' keys,
        ready to send to the OpenRouter chat completions API.
    """
    # Build system message with context if available
    if context:
        system_content = (
            f"{SYSTEM_PROMPT}\n\n"
            f"--- INTERNAL CONTEXT ---\n\n"
            f"{context}\n\n"
            f"--- END OF CONTEXT ---"
        )
    else:
        system_content = (
            f"{SYSTEM_PROMPT}\n\n"
            f"No internal context was found for this question. "
            f"Answer using general knowledge if possible, "
            f"but clarify that no internal data was available."
        )

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_message},
    ]
