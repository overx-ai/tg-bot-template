"""Users table definition for SQLAlchemy Core.

This module defines the users table schema that matches the current
implementation in DatabaseManager. This is used by Alembic for
migration management while keeping asyncpg for actual operations.
"""

from sqlalchemy import Table, Column, BigInteger, String, DateTime, Index
from sqlalchemy.sql import func

from .base import metadata

# Users table definition matching the current schema in DatabaseManager
users_table = Table(
    "users",
    metadata,
    Column("user_id", BigInteger, primary_key=True, comment="Telegram user ID"),
    Column("username", String(255), nullable=True, comment="Telegram username"),
    Column("language", String(10), nullable=False, default="en", server_default="en", comment="User's preferred language"),
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        default=func.current_timestamp(),
        server_default=func.current_timestamp(),
        comment="User registration timestamp",
    ),
    Column(
        "updated_at",
        DateTime(timezone=True),
        nullable=False,
        default=func.current_timestamp(),
        server_default=func.current_timestamp(),
        comment="Last update timestamp",
    ),
)

# Index for faster language-based queries
# Matches the index created in DatabaseManager._create_tables()
users_language_index = Index(
    "idx_users_language",
    users_table.c.language,
)
