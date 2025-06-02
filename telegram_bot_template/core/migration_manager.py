"""Migration manager for automatic database schema management.

This module provides the MigrationManager class that integrates Alembic
migrations with the bot startup process, allowing for automatic schema
updates while maintaining the existing asyncpg-based database operations.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations using Alembic."""

    def __init__(self, database_url: str, alembic_ini_path: Optional[str] = None):
        """Initialize the migration manager.

        Args:
            database_url: PostgreSQL database connection URL
            alembic_ini_path: Path to alembic.ini file (defaults to project root)
        """
        self.database_url = database_url

        # Determine alembic.ini path
        if alembic_ini_path is None:
            # Default to project root
            project_root = Path(__file__).parent.parent.parent
            alembic_ini_path = project_root / "alembic.ini"

        self.alembic_ini_path = str(alembic_ini_path)

        # Verify alembic.ini exists
        if not os.path.exists(self.alembic_ini_path):
            raise FileNotFoundError(f"Alembic configuration file not found: {self.alembic_ini_path}")

        # Create Alembic configuration
        self.alembic_cfg = Config(self.alembic_ini_path)

        # Override database URL in configuration
        self.alembic_cfg.set_main_option("sqlalchemy.url", self.database_url)

    def get_current_revision(self) -> Optional[str]:
        """Get the current database revision.

        Returns:
            Current revision ID or None if no migrations have been applied
        """
        try:
            engine = create_engine(self.database_url)
            with engine.connect() as connection:
                context = MigrationContext.configure(connection)
                return context.get_current_revision()
        except Exception as e:
            logger.error(f"Failed to get current revision: {e}")
            return None

    def get_head_revision(self) -> Optional[str]:
        """Get the latest available revision.

        Returns:
            Head revision ID or None if no migrations exist
        """
        try:
            script = ScriptDirectory.from_config(self.alembic_cfg)
            return script.get_current_head()
        except Exception as e:
            logger.error(f"Failed to get head revision: {e}")
            return None

    def has_pending_migrations(self) -> bool:
        """Check if there are pending migrations to apply.

        Returns:
            True if there are pending migrations, False otherwise
        """
        current = self.get_current_revision()
        head = self.get_head_revision()

        if head is None:
            # No migrations exist
            return False

        if current is None:
            # Database not initialized, migrations needed
            return True

        return current != head

    def create_migration(self, message: str, autogenerate: bool = True) -> str:
        """Create a new migration.

        Args:
            message: Migration description
            autogenerate: Whether to auto-generate migration from model changes

        Returns:
            Generated revision ID
        """
        try:
            if autogenerate:
                revision = command.revision(self.alembic_cfg, message=message, autogenerate=True)
            else:
                revision = command.revision(self.alembic_cfg, message=message)

            logger.info(f"Created migration: {revision.revision} - {message}")
            return revision.revision
        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            raise

    def apply_migrations(self, target_revision: str = "head") -> bool:
        """Apply migrations to the database.

        Args:
            target_revision: Target revision to migrate to (default: "head")

        Returns:
            True if migrations were applied successfully, False otherwise
        """
        try:
            current = self.get_current_revision()
            logger.info(f"Applying migrations from {current} to {target_revision}")

            # Apply migrations
            command.upgrade(self.alembic_cfg, target_revision)

            new_revision = self.get_current_revision()
            logger.info(f"Successfully applied migrations. Current revision: {new_revision}")
            return True

        except Exception as e:
            logger.error(f"Failed to apply migrations: {e}")
            return False

    def rollback_migration(self, target_revision: str = "-1") -> bool:
        """Rollback migrations to a specific revision.

        Args:
            target_revision: Target revision to rollback to (default: "-1" for previous)

        Returns:
            True if rollback was successful, False otherwise
        """
        try:
            current = self.get_current_revision()
            logger.info(f"Rolling back migrations from {current} to {target_revision}")

            # Rollback migrations
            command.downgrade(self.alembic_cfg, target_revision)

            new_revision = self.get_current_revision()
            logger.info(f"Successfully rolled back migrations. Current revision: {new_revision}")
            return True

        except Exception as e:
            logger.error(f"Failed to rollback migrations: {e}")
            return False

    def get_migration_history(self) -> list:
        """Get migration history.

        Returns:
            List of migration information
        """
        try:
            script = ScriptDirectory.from_config(self.alembic_cfg)
            revisions = []

            for revision in script.walk_revisions():
                revisions.append(
                    {
                        "revision": revision.revision,
                        "down_revision": revision.down_revision,
                        "description": revision.doc,
                        "is_current": revision.revision == self.get_current_revision(),
                    }
                )

            return revisions
        except Exception as e:
            logger.error(f"Failed to get migration history: {e}")
            return []

    def ensure_database_ready(self, auto_migrate: bool = True) -> bool:
        """Ensure database is ready by applying pending migrations.

        This method is designed to be called during bot startup to automatically
        handle database schema updates.

        Args:
            auto_migrate: Whether to automatically apply pending migrations

        Returns:
            True if database is ready, False if there were errors
        """
        try:
            logger.info("Checking database migration status...")

            current = self.get_current_revision()
            head = self.get_head_revision()

            if head is None:
                logger.warning("No migrations found. Database schema management is not initialized.")
                return True

            if current is None:
                logger.info("Database not initialized. Setting up initial schema...")
                if auto_migrate:
                    return self.apply_migrations()
                else:
                    logger.warning("Auto-migration disabled. Database needs manual migration.")
                    return False

            if current == head:
                logger.info(f"Database is up to date (revision: {current})")
                return True

            if auto_migrate:
                logger.info(f"Pending migrations detected. Upgrading from {current} to {head}...")
                return self.apply_migrations()
            else:
                logger.warning(f"Pending migrations detected but auto-migration disabled. " f"Current: {current}, Head: {head}")
                return False

        except Exception as e:
            logger.error(f"Failed to ensure database readiness: {e}")
            return False

    def stamp_database(self, revision: str = "head") -> bool:
        """Stamp the database with a specific revision without running migrations.

        This is useful for marking an existing database as being at a specific
        migration state without actually running the migration scripts.

        Args:
            revision: Revision to stamp the database with

        Returns:
            True if stamping was successful, False otherwise
        """
        try:
            logger.info(f"Stamping database with revision: {revision}")
            command.stamp(self.alembic_cfg, revision)
            logger.info("Database stamped successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to stamp database: {e}")
            return False
