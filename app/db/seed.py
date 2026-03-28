"""
Database seed script.

Populates the SQLite database with initial knowledge entries
from the seed_data.json file. Can be run independently or
called during application startup.

Usage:
    python -m app.db.seed
"""

import json
from pathlib import Path

from app.core.logging import setup_logging, get_logger
from app.db.session import SessionLocal, init_db
from app.db.models import KnowledgeEntry

logger = get_logger(__name__)

# Path to the JSON seed file
SEED_FILE = Path(__file__).parent.parent / "data" / "seed_data.json"


def load_seed_data() -> list[dict]:
    """Load knowledge entries from the JSON seed file."""
    if not SEED_FILE.exists():
        logger.error("Seed file not found: %s", SEED_FILE)
        return []

    with open(SEED_FILE, encoding="utf-8") as f:
        data = json.load(f)

    logger.info("Loaded %d entries from seed file", len(data))
    return data


def seed_database() -> int:
    """Populate the database with seed data.

    Clears existing entries and inserts fresh data from the seed file.
    Returns the number of entries inserted.
    """
    init_db()  # Ensure tables exist

    db = SessionLocal()
    try:
        # Clear existing entries to avoid duplicates on re-seed
        existing_count = db.query(KnowledgeEntry).count()
        if existing_count > 0:
            db.query(KnowledgeEntry).delete()
            logger.info("Cleared %d existing entries", existing_count)

        # Load and insert seed data
        entries = load_seed_data()
        if not entries:
            logger.warning("No seed data to insert")
            return 0

        for entry_data in entries:
            entry = KnowledgeEntry(
                title=entry_data["title"],
                content=entry_data["content"],
                tags=entry_data.get("tags", ""),
                category=entry_data.get("category", "general"),
            )
            db.add(entry)

        db.commit()
        logger.info("Seeded %d knowledge entries successfully", len(entries))
        return len(entries)

    except Exception as e:
        db.rollback()
        logger.error("Failed to seed database: %s", e)
        raise
    finally:
        db.close()


# Allow running as: python -m app.db.seed
if __name__ == "__main__":
    setup_logging()
    count = seed_database()
    print(f"Done! Inserted {count} knowledge entries.")
