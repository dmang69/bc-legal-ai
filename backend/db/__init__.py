"""Database layer — SQLite (default/tests) or PostgreSQL when ALA_POSTGRES_URL is set."""

from backend.db.connection import get_connection, get_db_backend, init_db
from backend.db.migrate import apply_migrations

__all__ = ["get_connection", "get_db_backend", "init_db", "apply_migrations"]
