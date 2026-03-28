"""
Knowledge retrieval service.

Searches the internal SQLite knowledge base to find entries
relevant to a user's question. Uses simple keyword matching
(no vector databases or embeddings) as specified in the project requirements.

The retrieval flow:
    1. Normalize the user message (lowercase, remove punctuation)
    2. Extract keywords from the message
    3. Score each knowledge entry by keyword matches against tags + content
    4. Return the top N most relevant entries
"""

import re
import unicodedata

from sqlalchemy.orm import Session

from app.db.models import KnowledgeEntry
from app.core.logging import get_logger

logger = get_logger(__name__)

# Words too common to be useful for searching
STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "must",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us",
    "my", "your", "his", "its", "our", "their",
    "this", "that", "these", "those",
    "in", "on", "at", "to", "for", "of", "with", "by", "from", "about",
    "into", "through", "during", "before", "after", "above", "below",
    "and", "or", "but", "not", "no", "nor", "so", "yet",
    "what", "which", "who", "whom", "when", "where", "why", "how",
    "all", "each", "every", "both", "few", "more", "most", "some", "any",
    "if", "then", "than", "too", "very", "just", "only",
    "up", "down", "out", "off", "over", "under", "again",
    # Spanish common words (since users might ask in Spanish)
    "el", "la", "los", "las", "un", "una", "de", "del", "en", "con",
    "por", "para", "es", "son", "como", "que", "cual", "donde",
    "tiene", "hay", "puede", "cuantos", "cuantas", "quien",
}

# Maximum number of results to return
DEFAULT_TOP_K = 3


def normalize_text(text: str) -> str:
    """Normalize text for comparison.

    - Convert to lowercase
    - Remove accents/diacritics
    - Remove punctuation
    - Collapse whitespace
    """
    # Lowercase
    text = text.lower()
    # Remove accents (é → e, ñ → n, etc.)
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    # Remove punctuation, keep only letters, numbers, spaces
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_keywords(text: str) -> set[str]:
    """Extract meaningful keywords from text.

    Normalizes the text and removes stop words to keep
    only words that carry meaning for search.
    """
    normalized = normalize_text(text)
    words = normalized.split()
    # Keep words that are not stop words and have at least 2 characters
    keywords = {w for w in words if w not in STOP_WORDS and len(w) >= 2}
    return keywords


def score_entry(entry: KnowledgeEntry, keywords: set[str]) -> float:
    """Score a knowledge entry by relevance to the given keywords.

    Scoring strategy:
    - Tag matches are worth 3 points (tags are curated, high signal)
    - Title matches are worth 2 points (titles are descriptive)
    - Content matches are worth 1 point (content is longer, match is weaker signal)

    Returns a float score (higher = more relevant).
    """
    if not keywords:
        return 0.0

    score = 0.0
    entry_tags = set(normalize_text(entry.tags).split())
    entry_title_words = set(normalize_text(entry.title).split())
    entry_content_words = set(normalize_text(entry.content).split())

    for keyword in keywords:
        # Exact match in tags (highest weight)
        if keyword in entry_tags:
            score += 3.0
        # Exact match in title
        if keyword in entry_title_words:
            score += 2.0
        # Exact match in content
        if keyword in entry_content_words:
            score += 1.0

    return score


def retrieve_context(
    db: Session,
    user_message: str,
    top_k: int = DEFAULT_TOP_K,
) -> list[KnowledgeEntry]:
    """Retrieve the most relevant knowledge entries for a user message.

    Args:
        db: Database session.
        user_message: The user's question or message.
        top_k: Maximum number of entries to return.

    Returns:
        List of KnowledgeEntry objects, ordered by relevance (best first).
        Empty list if no relevant entries are found.
    """
    keywords = extract_keywords(user_message)
    logger.info("Extracted keywords: %s", keywords)

    if not keywords:
        logger.warning("No keywords extracted from message: '%s'", user_message)
        return []

    # Fetch all entries and score them
    all_entries = db.query(KnowledgeEntry).all()

    scored_entries = []
    for entry in all_entries:
        score = score_entry(entry, keywords)
        if score > 0:
            scored_entries.append((entry, score))
            logger.debug(
                "Entry '%s' scored %.1f", entry.title, score
            )

    # Sort by score descending and take top K
    scored_entries.sort(key=lambda x: x[1], reverse=True)
    top_entries = [entry for entry, _ in scored_entries[:top_k]]

    logger.info(
        "Retrieved %d entries (from %d with score > 0) for message: '%s'",
        len(top_entries),
        len(scored_entries),
        user_message[:80],
    )

    return top_entries


def format_context(entries: list[KnowledgeEntry]) -> str:
    """Format retrieved entries into a context string for the LLM prompt.

    Produces a clean text block that can be inserted into the system prompt.
    """
    if not entries:
        return ""

    context_parts = []
    for entry in entries:
        context_parts.append(
            f"[{entry.category.upper()}] {entry.title}\n{entry.content}"
        )

    return "\n\n---\n\n".join(context_parts)
