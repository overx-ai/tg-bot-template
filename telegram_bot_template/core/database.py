"""Database management for the Telegram bot template."""

import logging
from typing import Optional, Dict, Any
import asyncpg
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Simple database manager with users table only."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self._pool: Optional[asyncpg.Pool] = None
    
    async def setup(self) -> None:
        """Initialize database connection and create tables."""
        try:
            self._pool = await asyncpg.create_pool(self.database_url)
            await self._create_tables()
            logger.info("Database setup completed successfully")
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            raise
    
    async def close(self) -> None:
        """Close database connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("Database connection closed")
    
    async def _create_tables(self) -> None:
        """Create necessary database tables."""
        async with self._pool.acquire() as conn:
            # Create users table if it doesn't exist
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    language VARCHAR(10) DEFAULT 'en',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Check if language column exists and add it if missing
            try:
                await conn.execute("SELECT language FROM users LIMIT 1")
            except Exception:
                # Language column doesn't exist, add it
                logger.info("Adding language column to existing users table")
                await conn.execute("""
                    ALTER TABLE users
                    ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'en'
                """)
                await conn.execute("""
                    ALTER TABLE users
                    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """)
            
            # Create index for faster lookups
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_language ON users(language);
            """)
            
            logger.info("Database tables created/verified")
    
    async def ensure_user(self, user_id: int, username: Optional[str] = None, language: str = "en") -> Dict[str, Any]:
        """Ensure user exists in database, create if not exists."""
        async with self._pool.acquire() as conn:
            # Try to get existing user
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE user_id = $1",
                user_id
            )
            
            if user:
                # Update username if provided and different
                if username and user['username'] != username:
                    await conn.execute(
                        "UPDATE users SET username = $1, updated_at = $2 WHERE user_id = $3",
                        username, datetime.utcnow(), user_id
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
                    user_id, username, language, datetime.utcnow()
                )
                
                # Get the created user
                user = await conn.fetchrow(
                    "SELECT * FROM users WHERE user_id = $1",
                    user_id
                )
                
                logger.info(f"Created new user: {user_id} (@{username})")
                return dict(user)
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        async with self._pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE user_id = $1",
                user_id
            )
            return dict(user) if user else None
    
    async def update_user_language(self, user_id: int, language: str) -> bool:
        """Update user's language preference."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE users SET language = $1, updated_at = $2 WHERE user_id = $3",
                language, datetime.utcnow(), user_id
            )
            
            success = result.split()[-1] == "1"  # Check if one row was updated
            if success:
                logger.info(f"Updated language for user {user_id} to {language}")
            
            return success
    
    async def get_user_language(self, user_id: int) -> str:
        """Get user's language preference."""
        async with self._pool.acquire() as conn:
            language = await conn.fetchval(
                "SELECT language FROM users WHERE user_id = $1",
                user_id
            )
            return language or "en"
    
    async def get_user_count(self) -> int:
        """Get total number of users."""
        async with self._pool.acquire() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM users")
            return count or 0
    
    async def get_users_by_language(self, language: str) -> int:
        """Get number of users by language."""
        async with self._pool.acquire() as conn:
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE language = $1",
                language
            )
            return count or 0
    
    async def get_recent_users(self, limit: int = 10) -> list:
        """Get recently registered users."""
        async with self._pool.acquire() as conn:
            users = await conn.fetch(
                "SELECT * FROM users ORDER BY created_at DESC LIMIT $1",
                limit
            )
            return [dict(user) for user in users]
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete user from database."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM users WHERE user_id = $1",
                user_id
            )
            
            success = result.split()[-1] == "1"
            if success:
                logger.info(f"Deleted user {user_id}")
            
            return success
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get basic database statistics."""
        async with self._pool.acquire() as conn:
            total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
            
            # Get users by language
            language_stats = await conn.fetch(
                "SELECT language, COUNT(*) as count FROM users GROUP BY language"
            )
            
            # Get recent registrations (last 24 hours)
            recent_users = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE created_at > NOW() - INTERVAL '24 hours'"
            )
            
            return {
                "total_users": total_users or 0,
                "recent_users_24h": recent_users or 0,
                "language_distribution": {row['language']: row['count'] for row in language_stats}
            }