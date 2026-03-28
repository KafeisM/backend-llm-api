"""
Database models for the internal knowledge base.

Defines the SQLAlchemy ORM model for knowledge entries.
Each entry represents a piece of internal company information
that the LLM alone would not know.
"""

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class KnowledgeEntry(Base):
    """A single piece of internal company knowledge.

    Attributes:
        id: Auto-incremented primary key.
        title: Short descriptive title (e.g., "Vacation Policy").
        content: Full text content of the knowledge entry.
        tags: Comma-separated keywords for simple retrieval matching.
              Example: "vacation,holidays,time-off,policy"
        category: High-level grouping (e.g., "hr", "engineering", "company").
    """

    __tablename__ = "knowledge_entries"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    title: str = Column(String(200), nullable=False)
    content: str = Column(Text, nullable=False)
    tags: str = Column(String(500), nullable=False, default="")
    category: str = Column(String(100), nullable=False, default="general")

    def __repr__(self) -> str:
        return f"<KnowledgeEntry(id={self.id}, title='{self.title}')>"
