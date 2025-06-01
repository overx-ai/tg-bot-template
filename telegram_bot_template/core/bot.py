"""Main bot class for the Telegram bot template."""

import asyncio
import logging
from typing import Optional

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from telegram_bot_template.config.settings import BotConfig
from telegram_bot_template.core.ai_provider import OpenRouterProvider, MockAIProvider
from telegram_bot_template.core.database import DatabaseManager
from telegram_bot_template.core.keyboard_manager import KeyboardManager
from telegram_bot_template.core.locale_manager import LocaleManager
from telegram_bot_template.handlers.basic import BasicHandlers
from telegram_bot_template.handlers.message import MessageHandler as MessageHandlerClass
from telegram_bot_template.support.bot import SupportBot
from telegram_bot_template.utils.helpers import setup_logging

# Set up enhanced logging
setup_logging()
logger = logging.getLogger(__name__)


class TelegramBot:
    """Main Telegram bot class."""

    def __init__(self, config: BotConfig):
        self.config = config
        self.app: Optional[Application] = None
        self.database: Optional[DatabaseManager] = None
        self.locale_manager: Optional[LocaleManager] = None
        self.keyboard_manager: Optional[KeyboardManager] = None
        self.ai_provider: Optional[OpenRouterProvider] = None
        self.support_bot: Optional[SupportBot] = None

        # Handlers
        self.basic_handlers: Optional[BasicHandlers] = None
        self.message_handler: Optional[MessageHandlerClass] = None

        logger.info(f"Bot initialized: {config.bot_name} v{config.bot_version}")

    async def setup(self) -> None:
        """Setup all bot components."""
        try:
            # Setup logging
            self.config.setup_logging()

            # Validate configuration
            self.config.validate()

            # Initialize database
            self.database = DatabaseManager(self.config.database_url)
            await self.database.setup()
            logger.info("Database initialized")

            # Initialize locale manager
            self.locale_manager = LocaleManager(
                default_language=self.config.default_language
            )
            logger.info("Locale manager initialized")

            # Initialize keyboard manager
            self.keyboard_manager = KeyboardManager(self.locale_manager)
            logger.info("Keyboard manager initialized")

            # Initialize AI provider if configured
            if self.config.has_ai_support:
                self.ai_provider = OpenRouterProvider(
                    api_key=self.config.openrouter_api_key,
                    model=self.config.openrouter_model
                )

                # Test AI connection
                if await self.ai_provider.test_connection():
                    logger.info(f"AI provider initialized: {self.config.openrouter_model}")
                else:
                    logger.warning("AI provider connection test failed, using mock provider")
                    self.ai_provider = MockAIProvider()
            else:
                logger.info("AI support not configured")

            # Initialize support bot if configured
            if self.config.has_support_bot:
                self.support_bot = SupportBot(
                    support_token=self.config.support_bot_token,
                    support_chat_id=self.config.support_chat_id,
                    locale_manager=self.locale_manager
                )
                await self.support_bot.setup()
                logger.info("Support bot initialized")

            # Initialize handlers
            self.basic_handlers = BasicHandlers(
                locale_manager=self.locale_manager,
                keyboard_manager=self.keyboard_manager,
                database=self.database,
                config=self.config
            )

            self.message_handler = MessageHandlerClass(
                locale_manager=self.locale_manager,
                keyboard_manager=self.keyboard_manager,
                database=self.database,
                ai_provider=self.ai_provider,
                config=self.config
            )

            # Create Telegram application
            self.app = Application.builder().token(self.config.bot_token).build()

            # Add handlers to application
            self._add_handlers()

            logger.info("Bot setup completed successfully")

        except Exception as e:
            logger.error(f"Bot setup failed: {e}")
            raise

    def _add_handlers(self) -> None:
        """Add all handlers to the application."""
        if not self.app:
            raise RuntimeError("Application not initialized")

        # Command handlers
        self.app.add_handler(CommandHandler("start", self.basic_handlers.start_command))
        self.app.add_handler(CommandHandler("help", self.basic_handlers.help_command))
        self.app.add_handler(CommandHandler("about", self.basic_handlers.about_command))

        # Callback query handler
        self.app.add_handler(CallbackQueryHandler(self.basic_handlers.callback_query_handler))

        # Message handlers
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.message_handler.handle_text_message
        ))

        self.app.add_handler(MessageHandler(
            filters.PHOTO,
            self.message_handler.handle_photo
        ))

        self.app.add_handler(MessageHandler(
            filters.Document.ALL,
            self.message_handler.handle_document
        ))

        self.app.add_handler(MessageHandler(
            filters.VOICE,
            self.message_handler.handle_voice
        ))

        self.app.add_handler(MessageHandler(
            filters.Sticker.ALL,
            self.message_handler.handle_sticker
        ))

        self.app.add_handler(MessageHandler(
            filters.LOCATION,
            self.message_handler.handle_location
        ))

        self.app.add_handler(MessageHandler(
            filters.CONTACT,
            self.message_handler.handle_contact
        ))

        logger.info("All handlers added to application")

    async def start(self) -> None:
        """Start the bot."""
        if not self.app:
            await self.setup()

        try:
            # Initialize and start main bot
            await self.app.initialize()
            await self.app.start()

            # Start support bot if configured
            if self.support_bot:
                await self.support_bot.start()

            # Send startup notification
            await self._send_startup_notification()

            # Start polling
            await self.app.updater.start_polling(
                drop_pending_updates=False,
                allowed_updates=None
            )

            logger.info(f"{self.config.bot_name} is now running...")

        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise

    async def stop(self) -> None:
        """Stop the bot."""
        try:
            # Send shutdown notification
            await self._send_shutdown_notification()

            # Stop main bot
            if self.app:
                await self.app.updater.stop()
                await self.app.stop()
                await self.app.shutdown()

            # Stop support bot
            if self.support_bot:
                await self.support_bot.stop()

            # Close database
            if self.database:
                await self.database.close()

            logger.info("Bot stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping bot: {e}")

    async def run(self) -> None:
        """Run the bot (blocking)."""
        try:
            await self.start()

            # Keep running until interrupted
            while True:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Bot runtime error: {e}")
        finally:
            await self.stop()

    async def _send_startup_notification(self) -> None:
        """Send startup notification to support if configured."""
        if self.support_bot:
            message = f"🚀 **{self.config.bot_name}** has started successfully!\n\n"
            message += f"Version: {self.config.bot_version}\n"
            message += f"AI Support: {'✅' if self.config.has_ai_support else '❌'}\n"
            message += f"Support Bot: {'✅' if self.config.has_support_bot else '❌'}"

            await self.support_bot.send_notification(message)

    async def _send_shutdown_notification(self) -> None:
        """Send shutdown notification to support if configured."""
        if self.support_bot:
            message = f"🛑 **{self.config.bot_name}** is shutting down."
            await self.support_bot.send_notification(message)

    async def get_stats(self) -> dict:
        """Get bot statistics."""
        stats = {
            "bot_name": self.config.bot_name,
            "bot_version": self.config.bot_version,
            "ai_support": self.config.has_ai_support,
            "support_bot": self.config.has_support_bot
        }

        if self.database:
            db_stats = await self.database.get_stats()
            stats.update(db_stats)

        if self.ai_provider:
            ai_info = self.ai_provider.get_model_info()
            stats["ai_provider"] = ai_info

        return stats

    async def send_stats_to_support(self) -> bool:
        """Send bot statistics to support."""
        if not self.support_bot:
            return False

        try:
            stats = await self.get_stats()
            return await self.support_bot.send_stats(stats)
        except Exception as e:
            logger.error(f"Error sending stats to support: {e}")
            return False

    def is_running(self) -> bool:
        """Check if bot is running."""
        return self.app is not None and self.app.running

    def get_config(self) -> BotConfig:
        """Get bot configuration."""
        return self.config

    async def reload_locales(self) -> None:
        """Reload locale files."""
        if self.locale_manager:
            self.locale_manager.reload_locales()
            logger.info("Locales reloaded")

    async def clear_keyboard_cache(self) -> None:
        """Clear keyboard cache."""
        if self.keyboard_manager:
            self.keyboard_manager.clear_cache()
            logger.info("Keyboard cache cleared")
