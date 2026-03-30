"""
Tests for the retrieval service.

Validates keyword extraction, scoring, context retrieval,
and context formatting — all without network calls.
"""

from app.db.models import KnowledgeEntry
from app.services.retrieval_service import (
    normalize_text,
    extract_keywords,
    score_entry,
    retrieve_context,
    format_context,
)


# ---------------------------------------------------------------------------
# normalize_text
# ---------------------------------------------------------------------------

class TestNormalizeText:
    """Text normalization should lowercase, remove accents and punctuation."""

    def test_lowercases(self):
        assert normalize_text("Hello WORLD") == "hello world"

    def test_removes_accents(self):
        assert normalize_text("café résumé") == "cafe resume"

    def test_removes_punctuation(self):
        assert normalize_text("hello, world!") == "hello world"

    def test_collapses_whitespace(self):
        assert normalize_text("too   many   spaces") == "too many spaces"

    def test_handles_empty_string(self):
        assert normalize_text("") == ""


# ---------------------------------------------------------------------------
# extract_keywords
# ---------------------------------------------------------------------------

class TestExtractKeywords:
    """Keyword extraction should filter stop words and short words."""

    def test_removes_stop_words(self):
        keywords = extract_keywords("what is the vacation policy")
        assert "what" not in keywords
        assert "is" not in keywords
        assert "the" not in keywords
        assert "vacation" in keywords
        assert "policy" in keywords

    def test_removes_short_words(self):
        keywords = extract_keywords("I am a go to person")
        # "I", "a" are stop words; "am", "go", "to" are stop words too
        assert "i" not in keywords
        assert "a" not in keywords

    def test_handles_spanish_stop_words(self):
        keywords = extract_keywords("cual es la politica de vacaciones")
        assert "cual" not in keywords
        assert "la" not in keywords
        assert "de" not in keywords
        assert "politica" in keywords
        assert "vacaciones" in keywords

    def test_empty_message_returns_empty(self):
        keywords = extract_keywords("")
        assert keywords == set()

    def test_only_stop_words_returns_empty(self):
        keywords = extract_keywords("the a an is are")
        assert keywords == set()


# ---------------------------------------------------------------------------
# score_entry
# ---------------------------------------------------------------------------

class TestScoreEntry:
    """Scoring should weight tags > titles > content."""

    def _make_entry(self, title="Test", content="test content", tags="test", category="general"):
        """Helper to create a KnowledgeEntry without DB."""
        entry = KnowledgeEntry()
        entry.title = title
        entry.content = content
        entry.tags = tags
        entry.category = category
        return entry

    def test_tag_match_scores_highest(self):
        entry = self._make_entry(tags="vacation policy")
        score = score_entry(entry, {"vacation"})
        # vacation matches in tags (3 points)
        assert score >= 3.0

    def test_title_match_scores_medium(self):
        entry = self._make_entry(title="Vacation Policy", tags="hr")
        score = score_entry(entry, {"vacation"})
        # vacation matches in title (2 points)
        assert score >= 2.0

    def test_content_match_scores_lowest(self):
        entry = self._make_entry(content="Our vacation policy is generous", tags="hr")
        score = score_entry(entry, {"vacation"})
        # vacation matches only in content (1 point)
        assert score >= 1.0

    def test_no_match_scores_zero(self):
        entry = self._make_entry(
            title="Jira Process", content="How to create tickets", tags="jira,engineering"
        )
        score = score_entry(entry, {"vacation"})
        assert score == 0.0

    def test_empty_keywords_scores_zero(self):
        entry = self._make_entry()
        score = score_entry(entry, set())
        assert score == 0.0

    def test_multiple_matches_accumulate(self):
        entry = self._make_entry(
            title="Vacation Policy", content="vacation days off", tags="vacation,policy"
        )
        # "vacation" matches in tags(3), title(2), content(1) = 6
        # "policy" matches in tags(3), title(2) = 5
        score = score_entry(entry, {"vacation", "policy"})
        assert score >= 11.0


# ---------------------------------------------------------------------------
# retrieve_context (uses test DB)
# ---------------------------------------------------------------------------

class TestRetrieveContext:
    """Integration test for full retrieval against the seeded test DB."""

    def test_retrieves_relevant_entries(self, db):
        results = retrieve_context(db, "How many partners does the company have?")
        assert len(results) > 0
        titles = [r.title for r in results]
        assert "Company Overview" in titles

    def test_retrieves_vacation_context(self, db):
        results = retrieve_context(db, "What is the vacation policy?")
        assert len(results) > 0
        titles = [r.title for r in results]
        assert "Vacation Policy" in titles

    def test_retrieves_jira_context(self, db):
        results = retrieve_context(db, "How do I open a Jira ticket?")
        assert len(results) > 0
        titles = [r.title for r in results]
        assert "Jira Ticket Process" in titles

    def test_returns_empty_for_irrelevant_query(self, db):
        results = retrieve_context(db, "xyzzy foobar nonsense")
        assert results == []

    def test_respects_top_k_limit(self, db):
        results = retrieve_context(db, "company vacation jira", top_k=1)
        assert len(results) <= 1

    def test_returns_empty_for_empty_message(self, db):
        results = retrieve_context(db, "")
        assert results == []


# ---------------------------------------------------------------------------
# format_context
# ---------------------------------------------------------------------------

class TestFormatContext:
    """Context formatting should produce readable text blocks."""

    def _make_entry(self, title, content, category="general"):
        entry = KnowledgeEntry()
        entry.title = title
        entry.content = content
        entry.category = category
        return entry

    def test_formats_single_entry(self):
        entries = [self._make_entry("Test Title", "Test content.", "hr")]
        result = format_context(entries)
        assert "[HR] Test Title" in result
        assert "Test content." in result

    def test_formats_multiple_entries_with_separator(self):
        entries = [
            self._make_entry("First", "Content one.", "hr"),
            self._make_entry("Second", "Content two.", "engineering"),
        ]
        result = format_context(entries)
        assert "[HR] First" in result
        assert "[ENGINEERING] Second" in result
        assert "---" in result  # separator between entries

    def test_empty_list_returns_empty_string(self):
        result = format_context([])
        assert result == ""
