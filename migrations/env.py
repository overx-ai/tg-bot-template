import asyncio # Added
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
# Use create_async_engine for async support
from sqlalchemy.ext.asyncio import create_async_engine # Added

from alembic import context

# Add the project root to the Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import our models and configuration
from telegram_bot_template import metadata
from telegram_bot_template import BotConfig

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate support
target_metadata = metadata


# Get database URL from our project configuration
def get_database_url():
    """Get database URL from project configuration."""
    try:
        bot_config = BotConfig.from_env()
        return bot_config.database_url
    except Exception as e:
        # Fallback to environment variable if config fails
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError(
                f"Could not get database URL from configuration: {e}. " "Please ensure DATABASE_URL environment variable is set."
            )
        return database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None: # Changed to async
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Override the sqlalchemy.url in the configuration
    # This part remains synchronous as it prepares config for the engine
    db_url = get_database_url()
    
    # Create an async engine
    connectable = create_async_engine(
        db_url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection: # Use async connect
        # Define a synchronous callback for Alembic operations
        def do_run_migrations(connection_sync):
            context.configure(
                connection=connection_sync,
                target_metadata=target_metadata,
                compare_type=True,
                compare_server_default=True,
                # include_schemas=True, # Add if using schemas
            )
            with context.begin_transaction():
                context.run_migrations()

        # Run the synchronous Alembic operations using run_sync
        await connection.run_sync(do_run_migrations)

    await connectable.dispose() # Dispose of the async engine


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online()) # Run the async function
