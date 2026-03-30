"""
Shared test fixtures for the test suite.

Provides a test database, seeded knowledge entries, and a
FastAPI test client that uses the test DB instead of production.
"""

import pytest
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker, Session

from fastapi.testclient import TestClient

from app.db.models import Base, KnowledgeEntry
from app.db.session import get_db
from app.main import app


# ---------------------------------------------------------------------------
# Test database (in-memory SQLite — fast & isolated)
# ---------------------------------------------------------------------------
# StaticPool ensures ALL connections share the same in-memory database.
# Without this, each connection would get its own empty database,
# causing "no such table" errors when the route handler opens a new connection.

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine
)


# ---------------------------------------------------------------------------
# Sample knowledge entries for tests
# ---------------------------------------------------------------------------

SAMPLE_ENTRIES = [
    {
        "title": "Company Overview",
        "content": "Nuria Tech Solutions is a technology company founded in 2019. It has 5 partners and around 120 employees.",
        "tags": "company,overview,partners,employees,founded",
        "category": "company",
    },
    {
        "title": "Vacation Policy",
        "content": "All employees receive 23 vacation days per year. Requests must be submitted through BambooHR at least 2 weeks in advance.",
        "tags": "vacation,holidays,time-off,policy,bamboohr",
        "category": "hr",
    },
    {
        "title": "Jira Ticket Process",
        "content": "To open a Jira ticket, go to the internal Jira board, click Create, select the appropriate project, and fill in the required fields.",
        "tags": "jira,ticket,process,engineering,bug,task",
        "category": "engineering",
    },
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(name="db")
def db_session():
    """Create a fresh test database session for each test.

    - Creates all tables before the test
    - Seeds sample knowledge entries
    - Drops all tables after the test (full isolation)
    """
    Base.metadata.create_all(bind=test_engine)
    db = TestSessionLocal()

    # Seed sample data
    for entry_data in SAMPLE_ENTRIES:
        db.add(KnowledgeEntry(**entry_data))
    db.commit()

    yield db

    db.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(name="client")
def test_client(db: Session):
    """Provide a FastAPI TestClient that uses the test database.

    Overrides the get_db dependency so routes use the in-memory
    test DB instead of the production SQLite file.
    """

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
