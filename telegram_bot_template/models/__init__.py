"""Database models for the Telegram bot template.

This module contains SQLAlchemy Core table definitions used by Alembic
for database migrations. The actual database operations continue to use
asyncpg for performance and simplicity.
"""

from .base import metadata
from .users import users_table

__all__ = [
    "metadata",
    "users_table",
]
