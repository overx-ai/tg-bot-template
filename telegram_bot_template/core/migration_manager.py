"""Migration manager for automatic database schema management.

This module provides the MigrationManager class that integrates Alembic
migrations with the bot startup process, allowing for automatic schema
updates while maintaining the existing asyncpg-based database operations.
"""

import asyncio # Added
import logging
import os
from pathlib import Path
from typing import Optional

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.ext.asyncio import create_async_engine # Changed

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

    async def get_current_revision(self) -> Optional[str]: # Changed to async
        """Get the current database revision asynchronously."""
        engine = create_async_engine(self.database_url)
        try:
            async with engine.connect() as connection:
                # Alembic context operations are synchronous, run them in a sync manner
                def get_rev_sync(conn_sync):
                    migration_context = MigrationContext.configure(conn_sync)
                    return migration_context.get_current_revision()
                
                current_rev = await connection.run_sync(get_rev_sync)
                return current_rev
        except Exception as e:
            logger.error(f"Failed to get current revision: {e}")
            return None
        finally:
            await engine.dispose()

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

    async def has_pending_migrations(self) -> bool: # Changed to async
        """Check if there are pending migrations to apply asynchronously."""
        current = await self.get_current_revision() # Await async call
        head = self.get_head_revision() # This can remain sync as it reads from files

        if head is None:
            # No migrations exist
            return False

        if current is None:
            # Database not initialized, migrations needed
            return True

        return current != head

    async def create_migration(self, message: str, autogenerate: bool = True) -> str: # Changed to async
        """Create a new migration asynchronously."""
        try:
            # alembic.command.revision is synchronous
            if autogenerate:
                rev_obj = await asyncio.to_thread(
                    command.revision, self.alembic_cfg, message=message, autogenerate=True
                )
            else:
                rev_obj = await asyncio.to_thread(
                    command.revision, self.alembic_cfg, message=message
                )
            
            if rev_obj is None: # command.revision can return None or a list of Script objects
                # Handle cases where multiple heads might cause issues or no revision is created
                logger.warning(f"Alembic command.revision did not return a new revision object for message: {message}")
                # Attempt to get the latest head if no specific revision object was returned directly
                # This is a fallback and might need adjustment based on how `command.revision` behaves with multiple heads
                new_head = self.get_head_revision()
                if not new_head:
                    raise RuntimeError("Failed to create migration and could not determine new head.")
                logger.info(f"Created migration (head determined): {new_head} - {message}")
                return new_head

            # If command.revision returns a single Script object (common case)
            if not isinstance(rev_obj, list):
                 new_revision_id = rev_obj.revision
            # If it returns a list of Script objects (e.g. for multiple heads, though less common for basic revision)
            # We'll assume the first one or the one that is not None. This might need refinement.
            elif rev_obj:
                new_revision_id = rev_obj[0].revision # Take the first one
            else: # Empty list
                raise RuntimeError("Alembic command.revision returned an empty list.")

            logger.info(f"Created migration: {new_revision_id} - {message}")
            return new_revision_id
        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            raise

    async def apply_migrations(self, target_revision: str = "head") -> bool: # Changed to async
        """Apply migrations to the database asynchronously."""
        try:
            current = await self.get_current_revision() # Await async call
            logger.info(f"Applying migrations from {current} to {target_revision}")

            # alembic.command.upgrade is synchronous
            await asyncio.to_thread(command.upgrade, self.alembic_cfg, target_revision)

            new_revision = await self.get_current_revision() # Await async call
            logger.info(f"Successfully applied migrations. Current revision: {new_revision}")
            return True

        except Exception as e:
            logger.error(f"Failed to apply migrations: {e}")
            return False

    async def rollback_migration(self, target_revision: str = "-1") -> bool: # Changed to async
        """Rollback migrations to a specific revision asynchronously."""
        try:
            current = await self.get_current_revision() # Await async call
            logger.info(f"Rolling back migrations from {current} to {target_revision}")

            # alembic.command.downgrade is synchronous
            await asyncio.to_thread(command.downgrade, self.alembic_cfg, target_revision)

            new_revision = await self.get_current_revision() # Await async call
            logger.info(f"Successfully rolled back migrations. Current revision: {new_revision}")
            return True

        except Exception as e:
            logger.error(f"Failed to rollback migrations: {e}")
            return False

    async def get_migration_history(self) -> list: # Changed to async
        """Get migration history asynchronously."""
        try:
            script = ScriptDirectory.from_config(self.alembic_cfg) # This is sync, reads files
            current_rev = await self.get_current_revision() # Await async call
            history = []

            for rev_script in script.walk_revisions():
                history.append(
                    {
                        "revision": rev_script.revision,
                        "down_revision": rev_script.down_revision,
                        "description": rev_script.doc,
                        "is_current": rev_script.revision == current_rev,
                    }
                )
            return history
        except Exception as e:
            logger.error(f"Failed to get migration history: {e}")
            return []

    async def ensure_database_ready(self, auto_migrate: bool = True) -> bool: # Changed to async
        """Ensure database is ready by applying pending migrations asynchronously."""
        try:
            logger.info("Checking database migration status...")

            current = await self.get_current_revision() # Await async call
            head = self.get_head_revision() # Sync call

            if head is None:
                logger.warning("No migrations found. Database schema management is not initialized.")
                return True # Or False, depending on desired behavior for "no migrations"

            if current is None:
                logger.info("Database not initialized. Setting up initial schema...")
                if auto_migrate:
                    return await self.apply_migrations() # Await async call
                else:
                    logger.warning("Auto-migration disabled. Database needs manual migration.")
                    return False

            if current == head:
                logger.info(f"Database is up to date (revision: {current})")
                return True

            # Pending migrations exist
            if auto_migrate:
                logger.info(f"Pending migrations detected. Upgrading from {current} to {head}...")
                return await self.apply_migrations() # Await async call
            else:
                logger.warning(
                    f"Pending migrations detected but auto-migration disabled. "
                    f"Current: {current}, Head: {head}"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to ensure database readiness: {e}")
            return False

    async def stamp_database(self, revision: str = "head") -> bool: # Changed to async
        """Stamp the database with a specific revision asynchronously."""
        try:
            logger.info(f"Stamping database with revision: {revision}")
            # alembic.command.stamp is synchronous
            await asyncio.to_thread(command.stamp, self.alembic_cfg, revision)
            logger.info("Database stamped successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to stamp database: {e}")
            return False
