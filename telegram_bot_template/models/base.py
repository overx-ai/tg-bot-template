"""Base SQLAlchemy setup for database models.

This module provides the SQLAlchemy metadata object that will be used
by Alembic for migration management. It does not include ORM functionality
as we continue to use asyncpg for actual database operations.
"""

from sqlalchemy import MetaData

# Create metadata object for Alembic migrations
# This will track all table definitions for schema management
metadata = MetaData()

# Naming convention for constraints to ensure consistent naming
# across different database systems and migration operations
metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
