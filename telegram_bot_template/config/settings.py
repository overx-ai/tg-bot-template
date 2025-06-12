"""Configuration settings for the Telegram bot template."""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class BotConfig:
    """Configuration class for the Telegram bot."""

    # Required settings
    bot_token: str
    database_url: str

    # Optional AI settings
    openrouter_api_key: Optional[str] = None
    openrouter_model: str = "openai/gpt-3.5-turbo"

    # Optional support bot settings
    support_bot_token: Optional[str] = None
    support_chat_id: Optional[int] = None
    MAINTAINER_CHAT_ID: Optional[int] = None  # For critical alerts

    # Database migration settings
    auto_migrate: bool = True
    migration_timeout: int = 300  # 5 minutes

    # Localization settings
    default_language: str = "en"
    supported_languages: List[str] = field(default_factory=lambda: ["en", "ru", "es"])

    # Bot metadata
    bot_name: str = "Telegram Bot"
    bot_description: str = "A simple Telegram bot"
    bot_version: str = "1.0.0"

    # Logging settings
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "BotConfig":
        """Create configuration from environment variables."""

        # Required environment variables
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        database_url = os.getenv("DATABASE_URL")

        if not bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")

        # Optional environment variables
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        openrouter_model = os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")

        support_bot_token = os.getenv("SUPPORT_BOT_TOKEN")
        support_chat_id_str = os.getenv("SUPPORT_CHAT_ID")
        support_chat_id = int(support_chat_id_str) if support_chat_id_str else None

        maintainer_chat_id_str = os.getenv("MAINTAINER_CHAT_ID")
        maintainer_chat_id = int(maintainer_chat_id_str) if maintainer_chat_id_str else None

        # Bot metadata
        bot_name = os.getenv("BOT_NAME", "Telegram Bot")
        bot_description = os.getenv("BOT_DESCRIPTION", "A simple Telegram bot")
        bot_version = os.getenv("BOT_VERSION", "1.0.0")

        # Database migration settings
        auto_migrate_str = os.getenv("AUTO_MIGRATE", "true").lower()
        auto_migrate = auto_migrate_str in ("true", "1", "yes", "on")
        migration_timeout = int(os.getenv("MIGRATION_TIMEOUT", "300"))

        # Localization
        default_language = os.getenv("DEFAULT_LANGUAGE", "en")
        supported_languages_str = os.getenv("SUPPORTED_LANGUAGES", "en,ru,es")
        supported_languages = [lang.strip() for lang in supported_languages_str.split(",")]

        # Logging
        log_level = os.getenv("LOG_LEVEL", "INFO")

        return cls(
            bot_token=bot_token,
            database_url=database_url,
            openrouter_api_key=openrouter_api_key,
            openrouter_model=openrouter_model,
            support_bot_token=support_bot_token,
            support_chat_id=support_chat_id,
            auto_migrate=auto_migrate,
            migration_timeout=migration_timeout,
            default_language=default_language,
            supported_languages=supported_languages,
            bot_name=bot_name,
            bot_description=bot_description,
            bot_version=bot_version,
            log_level=log_level,
            MAINTAINER_CHAT_ID=maintainer_chat_id,
        )

    @property
    def has_ai_support(self) -> bool:
        """Check if AI support is available."""
        return self.openrouter_api_key is not None

    @property
    def has_support_bot(self) -> bool:
        """Check if support bot is configured."""
        return self.support_bot_token is not None and self.support_chat_id is not None

    def setup_logging(self) -> None:
        """Setup logging configuration."""
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=getattr(logging, self.log_level.upper(), logging.INFO)
        )
        logger.info(f"Logging configured with level: {self.log_level}")

    def validate(self) -> None:
        """Validate configuration settings."""
        if not self.bot_token:
            raise ValueError("Bot token is required")

        if not self.database_url:
            raise ValueError("Database URL is required")

        if self.default_language not in self.supported_languages:
            raise ValueError(f"Default language '{self.default_language}' not in supported languages")

        if self.support_bot_token and not self.support_chat_id:
            logger.warning("Support bot token provided but no support chat ID configured")

        if self.support_chat_id and not self.support_bot_token:
            logger.warning("Support chat ID provided but no support bot token configured")

        logger.info("Configuration validation passed")
