"""Database management for the Telegram bot template."""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

import asyncpg

from .migration_manager import MigrationManager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager with automatic migration support."""

    def __init__(self, database_url: str, auto_migrate: bool = True):
        """Initialize the database manager.

        Args:
            database_url: PostgreSQL database connection URL
            auto_migrate: Whether to automatically apply pending migrations on setup
        """
        self.database_url = database_url
        self.auto_migrate = auto_migrate
        self._pool: Optional[asyncpg.Pool] = None
        self._migration_manager = MigrationManager(database_url)

    @classmethod
    def from_config(cls, config):
        """Create DatabaseManager from BotConfig.

        Args:
            config: BotConfig instance

        Returns:
            DatabaseManager instance
        """
        return cls(database_url=config.database_url, auto_migrate=config.auto_migrate)

    async def setup(self) -> None:
        """Initialize database connection and ensure schema is up to date."""
        try:
            # Run migrations first if auto_migrate is enabled
            if self.auto_migrate:
                logger.info("Checking for pending database migrations...")
                migration_success = await self._migration_manager.ensure_database_ready(auto_migrate=True) # Added await
                if not migration_success:
                    raise RuntimeError("Database migration failed")

            # Create connection pool
            # asyncpg expects DSN without the +asyncpg dialect part
            asyncpg_compatible_dsn = self.database_url
            if "postgresql+asyncpg://" in asyncpg_compatible_dsn:
                asyncpg_compatible_dsn = asyncpg_compatible_dsn.replace("postgresql+asyncpg://", "postgresql://")
            
            self._pool = await asyncpg.create_pool(asyncpg_compatible_dsn)
            logger.info("Database setup completed successfully")
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            raise

    async def close(self) -> None:
        """Close database connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("Database connection closed")

    @property
    def migration_manager(self) -> MigrationManager:
        """Get the migration manager instance."""
        return self._migration_manager

    def create_migration(self, message: str, autogenerate: bool = True) -> str:
        """Create a new migration.

        Args:
            message: Migration description
            autogenerate: Whether to auto-generate migration from model changes

        Returns:
            Generated revision ID
        """
        return self._migration_manager.create_migration(message, autogenerate)

    def apply_migrations(self, target_revision: str = "head") -> bool:
        """Apply migrations to the database.

        Args:
            target_revision: Target revision to migrate to (default: "head")

        Returns:
            True if migrations were applied successfully, False otherwise
        """
        return self._migration_manager.apply_migrations(target_revision)

    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status.

        Returns:
            Dictionary with migration status information
        """
        current = self._migration_manager.get_current_revision()
        head = self._migration_manager.get_head_revision()
        has_pending = self._migration_manager.has_pending_migrations()

        return {
            "current_revision": current,
            "head_revision": head,
            "has_pending_migrations": has_pending,
            "migration_history": self._migration_manager.get_migration_history(),
        }

    async def ensure_user(self, user_id: int, username: Optional[str] = None, language: str = "en") -> Dict[str, Any]:
        """Ensure user exists in database, create if not exists."""
        async with self._pool.acquire() as conn:
            # Try to get existing user
            user = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)

            if user:
                # Update username if provided and different
                if username and user["username"] != username:
                    await conn.execute(
                        "UPDATE users SET username = $1, updated_at = $2 WHERE user_id = $3", username, datetime.utcnow(), user_id
                    )
                    logger.debug(f"Updated username for user {user_id}")

                return dict(user)
            else:
                # Create new user
                await conn.execute(
                    """
                    INSERT INTO users (user_id, username, language, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $4)
                    """,
                    user_id,
                    username,
                    language,
                    datetime.utcnow(),
                )

                # Get the created user
                user = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)

                logger.info(f"Created new user: {user_id} (@{username})")
                return dict(user)

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        async with self._pool.acquire() as conn:
            user = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
            return dict(user) if user else None

    async def update_user_language(self, user_id: int, language: str) -> bool:
        """Update user's language preference."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE users SET language = $1, updated_at = $2 WHERE user_id = $3", language, datetime.utcnow(), user_id
            )

            success = result.split()[-1] == "1"  # Check if one row was updated
            if success:
                logger.info(f"Updated language for user {user_id} to {language}")

            return success

    async def get_user_language(self, user_id: int) -> str:
        """Get user's language preference."""
        async with self._pool.acquire() as conn:
            language = await conn.fetchval("SELECT language FROM users WHERE user_id = $1", user_id)
            return language or "en"

    async def get_user_count(self) -> int:
        """Get total number of users."""
        async with self._pool.acquire() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM users")
            return count or 0

    async def get_users_by_language(self, language: str) -> int:
        """Get number of users by language."""
        async with self._pool.acquire() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM users WHERE language = $1", language)
            return count or 0

    async def get_recent_users(self, limit: int = 10) -> list:
        """Get recently registered users."""
        async with self._pool.acquire() as conn:
            users = await conn.fetch("SELECT * FROM users ORDER BY created_at DESC LIMIT $1", limit)
            return [dict(user) for user in users]

    async def delete_user(self, user_id: int) -> bool:
        """Delete user from database."""
        async with self._pool.acquire() as conn:
            result = await conn.execute("DELETE FROM users WHERE user_id = $1", user_id)

            success = result.split()[-1] == "1"
            if success:
                logger.info(f"Deleted user {user_id}")

            return success

    async def get_stats(self) -> Dict[str, Any]:
        """Get basic database statistics."""
        async with self._pool.acquire() as conn:
            total_users = await conn.fetchval("SELECT COUNT(*) FROM users")

            # Get users by language
            language_stats = await conn.fetch("SELECT language, COUNT(*) as count FROM users GROUP BY language")

            # Get recent registrations (last 24 hours)
            recent_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE created_at > NOW() - INTERVAL '24 hours'")

            return {
                "total_users": total_users or 0,
                "recent_users_24h": recent_users or 0,
                "language_distribution": {row["language"]: row["count"] for row in language_stats},
            }
