"""Compatibility import for the canonical database session dependency."""

from app.db.database import get_db

__all__ = ["get_db"]