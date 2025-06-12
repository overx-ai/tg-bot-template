import pytest
from telegram_bot_template.config.settings import BotConfig
from telegram_bot_template.core.locale_manager import LocaleManager
import logging
from testcontainers.postgres import PostgresContainer
import os

logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


@pytest.fixture(scope="session")
def postgres_db_url():
    """Starts a PostgreSQL container and yields its DSN for asyncpg."""
    # Skip if Docker is not available or explicitly disabled for tests
    if os.environ.get("SKIP_DOCKER_TESTS", "false").lower() == "true":
        pytest.skip("Skipping Docker-dependent tests (SKIP_DOCKER_TESTS is true)")

    try:
        # Use a light image like postgres:16-alpine
        with PostgresContainer("postgres:16-alpine") as postgres_container:
            # Ensure the driver is asyncpg for compatibility with DatabaseManager
            dsn = postgres_container.get_connection_url(driver="asyncpg")
            logger.info(f"PostgreSQL container started. DSN: {dsn}")
            yield dsn
            logger.info("PostgreSQL container stopped.")
    except Exception as e:
        logger.error(f"Failed to start PostgreSQL container: {e}. Ensure Docker is running.")
        pytest.skip(f"Skipping Docker-dependent tests: Failed to start PostgreSQL container: {e}")


@pytest.fixture(scope="session")
def session_monkeypatch():
    """A session-scoped monkeypatch fixture."""
    from _pytest.monkeypatch import MonkeyPatch
    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()

@pytest.fixture(scope="session") # Changed scope to session
async def config(session_monkeypatch, postgres_db_url: str): # Use session_monkeypatch
    """Pytest fixture for BotConfig, using Dockerized PostgreSQL."""
    logger.info("🔧 Creating BotConfig fixture (session-scoped, using Dockerized PostgreSQL)...")
    session_monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token_from_conftest")
    session_monkeypatch.setenv("DATABASE_URL", postgres_db_url) # Use DSN from Docker container
    session_monkeypatch.setenv("ADMIN_USER_IDS", "12345")
    # Ensure auto_migrate is true for tests to run migrations on the test DB
    session_monkeypatch.setenv("AUTO_MIGRATE_DB", "true")


    try:
        config_instance = BotConfig.from_env()
        config_instance.validate()
        logger.info(f"✅ Config fixture valid and created: {config_instance.bot_name}")
        return config_instance
    except Exception as e:
        logger.error(f"❌ Config fixture error: {e}")
        pytest.fail(f"Failed to create config fixture: {e}")


@pytest.fixture(scope="session")
async def locale_manager():
    """Pytest fixture for LocaleManager."""
    logger.info("🌐 Creating LocaleManager fixture (session-scoped)...")
    try:
        lm_instance = LocaleManager()
        # Basic check to ensure locales are loaded (optional, but good practice)
        if not lm_instance.get("welcome_message", "en"):
            raise ValueError("English 'welcome_message' not found in LocaleManager fixture.")
        logger.info("✅ LocaleManager fixture created and verified.")
        return lm_instance
    except Exception as e:
        logger.error(f"❌ LocaleManager fixture error: {e}")
        pytest.fail(f"Failed to create locale_manager fixture: {e}")