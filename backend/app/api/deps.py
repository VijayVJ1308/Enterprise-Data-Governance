from typing import Generator
from backend.app.core.database import SessionLocal


def get_db() -> Generator:
    """Dependency for obtaining DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
