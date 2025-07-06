"""Main bot class for the Telegram bot template."""

import asyncio
import logging
import signal
import platform
from typing import Optional

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

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
        self.shutting_down_event: Optional[asyncio.Event] = None # For graceful shutdown

        # Handlers
        self.basic_handlers: Optional[BasicHandlers] = None
        self.message_handler: Optional[MessageHandlerClass] = None

        logger.info(f"Bot initialized: {config.bot_name} v{config.bot_version}")

    async def setup(self) -> None:
        """Setup all bot components."""
        try:
            self.config.setup_logging()
            self.config.validate()

            self.database = DatabaseManager(self.config.database_url)
            await self.database.setup()
            logger.info("Database initialized")

            self.locale_manager = LocaleManager(default_language=self.config.default_language)
            logger.info("Locale manager initialized")

            self.keyboard_manager = KeyboardManager(self.locale_manager)
            logger.info("Keyboard manager initialized")

            if self.config.has_ai_support:
                self.ai_provider = OpenRouterProvider(api_key=self.config.openrouter_api_key, model=self.config.openrouter_model)

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
                    locale_manager=self.locale_manager,
                )
                await self.support_bot.setup()
                logger.info("Support bot initialized")

            # Initialize handlers
            self.basic_handlers = BasicHandlers(
                locale_manager=self.locale_manager, keyboard_manager=self.keyboard_manager, database=self.database, config=self.config
            )

            self.message_handler = MessageHandlerClass(
                locale_manager=self.locale_manager,
                keyboard_manager=self.keyboard_manager,
                database=self.database,
                ai_provider=self.ai_provider,
                config=self.config,
            )

            # Create Telegram application
            self.app = Application.builder().token(self.config.bot_token).build()
            self.app.bot_data['is_shutting_down'] = False
            self.shutting_down_event = asyncio.Event()
            self.app.bot_data['main_loop_stop_event'] = self.shutting_down_event


            # Add handlers to application
            self._add_handlers()

            logger.info("Bot setup completed successfully")

        except Exception as e:
            logger.error(f"Bot setup failed: {e}")
            raise

    async def run(self) -> None:
        """Run the bot, including setup, signal handling, and graceful shutdown."""
        try:
            await self.setup()  # Initialize all components, including self.app and self.shutting_down_event

            if not self.app or not self.shutting_down_event:
                logger.critical("Application or shutdown event not initialized during setup. Exiting.")
                return

            # `async with self.app` handles initialize() on entry and shutdown() (after stop()) on exit
            # This is a robust way to manage the PTB application lifecycle.
            async with self.app:
                logger.info(f"Starting {self.config.bot_name} within 'async with self.app' context...")
                # `await self.app.initialize()` is handled by `async with`
                await self.app.start()  # Starts PTB core background tasks (e.g., _update_fetcher)
                logger.info(f"{self.config.bot_name} PTB application started.")

                loop = asyncio.get_running_loop()
                await self._register_signal_handlers(loop)

                # Startup Notifications
                await self._send_startup_notification()  # To SupportBot
                await self._notify_maintainer(f"🚀 {self.config.bot_name} v{self.config.bot_version} has started successfully!")

                # Start support bot if configured (after main app components are ready)
                if self.support_bot:
                    logger.info("Starting support bot...")
                    await self.support_bot.start()
                    logger.info("Support bot started.")

                logger.info("Starting polling for main bot...")
                # Consider making drop_pending_updates and allowed_updates configurable
                await self.app.updater.start_polling(
                    drop_pending_updates=getattr(self.config, 'drop_pending_updates', False),
                    allowed_updates=None # Update.ALL_TYPES equivalent
                )
                logger.info(f"{self.config.bot_name} is now polling. Press Ctrl+C or send signal to stop.")

                # Wait for the shutdown event to be set
                await self.shutting_down_event.wait()
                logger.info("Shutdown event received, run() method will now proceed to finally block.")

        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received in run(). Initiating graceful shutdown via finally block.")
            # The finally block will handle calling shutdown_gracefully
        except Exception as e:
            logger.error(f"Unhandled error in run() method: {e}", exc_info=True)
            # The finally block will handle calling shutdown_gracefully
        finally:
            logger.info("Run method's finally block reached. Ensuring graceful shutdown.")
            # Check if self.app exists because setup might have failed before its initialization
            if hasattr(self, 'app') and self.app:
                await self.shutdown_gracefully()
            else:
                logger.warning("Application (self.app) was not available for full graceful shutdown in run()'s finally block.")
                # Attempt to close DB at least if it was initialized
                if hasattr(self, 'database') and self.database and hasattr(self.database, 'close'):
                    try:
                        logger.info("Attempting to close database connection (app was not available)...")
                        await self.database.close()
                        logger.info("Database connection closed in finally (app was not available).")
                    except Exception as db_exc:
                        logger.error(f"Error closing database in finally (app was not available): {db_exc}", exc_info=True)
            logger.info(f"{self.config.bot_name} run() method is exiting.")

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
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler.handle_text_message))

        self.app.add_handler(MessageHandler(filters.PHOTO, self.message_handler.handle_photo))

        self.app.add_handler(MessageHandler(filters.Document.ALL, self.message_handler.handle_document))

        self.app.add_handler(MessageHandler(filters.VOICE, self.message_handler.handle_voice))

        self.app.add_handler(MessageHandler(filters.Sticker.ALL, self.message_handler.handle_sticker))

        self.app.add_handler(MessageHandler(filters.LOCATION, self.message_handler.handle_location))

        self.app.add_handler(MessageHandler(filters.CONTACT, self.message_handler.handle_contact))

        # Add error handler
        self.app.add_error_handler(self._error_handler)

        logger.info("All handlers added to application")

    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Log errors caused by Updates."""
        logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)

    async def _notify_maintainer(self, text: str) -> None:
        """Send a message to the maintainer if configured."""
        if self.config.MAINTAINER_CHAT_ID and self.app:
            try:
                await self.app.bot.send_message(chat_id=self.config.MAINTAINER_CHAT_ID, text=text)
                logger.info(f"Sent notification to maintainer: {text}")
            except Exception as e:
                logger.error(f"Failed to send notification to maintainer {self.config.MAINTAINER_CHAT_ID}: {e}")
        elif not self.config.MAINTAINER_CHAT_ID:
            logger.debug("Maintainer chat ID not configured, skipping notification.")

    async def _send_startup_notification(self) -> None:
        """Send startup notification to support if configured."""
        if self.support_bot:
            message = f"🚀 **{self.config.bot_name}** has started successfully!\n\n"
            message += f"Version: {self.config.bot_version}\n"
            message += f"AI Support: {'✅' if self.config.has_ai_support else '❌'}\n"
            message += f"Support Bot: {'✅' if self.config.has_support_bot else '❌'}"

            await self.support_bot.send_notification(message)

    async def get_stats(self) -> dict:
        """Get bot statistics."""
        stats = {
            "bot_name": self.config.bot_name,
            "bot_version": self.config.bot_version,
            "ai_support": self.config.has_ai_support,
            "support_bot": self.config.has_support_bot,
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

    async def _send_shutdown_notification(self) -> None:
        """Send shutdown notification to support if configured."""
        if self.support_bot:
            message = f"🛑 **{self.config.bot_name}** is shutting down."
            await self.support_bot.send_notification(message)

    async def _register_signal_handlers(self, loop) -> None:
        """Register signal handlers for graceful shutdown."""
        if platform.system() == "Windows":
            logger.info("Running on Windows, signal handlers for SIGTERM/SIGINT are not set. Use Ctrl+C to stop.")
            # On Windows, KeyboardInterrupt is the primary way to stop.
            # signal.signal(signal.SIGINT, lambda s, f: asyncio.create_task(self.shutdown_gracefully()))
            # The above often doesn't work well with asyncio apps on Windows. PTB handles Ctrl+C.
            return

        def signal_handler_closure():
            logger.info("Received termination signal, initiating graceful shutdown via signal.")
            if self.app and not self.app.bot_data.get('is_shutting_down', False):
                asyncio.create_task(self.shutdown_gracefully())
            elif not self.app:
                logger.warning("Signal received but application instance is None.")
            else:
                logger.info("Signal received but shutdown already in progress.")

        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, signal_handler_closure)
                logger.info(f"Registered signal handler for {sig.name}")
            except (NotImplementedError, RuntimeError) as e:
                logger.warning(f"Could not set signal handler for {sig.name}: {e}. Ctrl+C (KeyboardInterrupt) should still work.")


    async def shutdown_gracefully(self) -> None:
        """Gracefully shut down the application, support bot, and database."""
        if not self.app:
            logger.info("Application object is None. Attempting to close DB if possible.")
            if self.database and hasattr(self.database, 'close'):
                try:
                    await self.database.close()
                    logger.info("Database connection closed (application was None).")
                except Exception as e_db:
                    logger.error(f"Error closing database (application was None): {e_db}")
            else:
                logger.info("Database object not available for closing (application was None).")
            logger.info("Shutdown for non-existent application complete.")
            return

        if self.app.bot_data.get('is_shutting_down', False):
            logger.info("Shutdown already in progress.")
            return

        self.app.bot_data['is_shutting_down'] = True
        logger.info("Initiating graceful shutdown...")

        # Set the event to signal the main loop to stop
        if self.shutting_down_event:
            self.shutting_down_event.set()

        # Notifications
        await self._notify_maintainer(f"🛑 {self.config.bot_name} is shutting down.")
        await self._send_shutdown_notification() # For SupportBot

        # Stop support bot first (if it exists and is running)
        if self.support_bot and self.support_bot.is_running():
            try:
                logger.info("Stopping support bot...")
                await self.support_bot.stop()
                logger.info("Support bot stopped.")
            except Exception as e:
                logger.error(f"Error stopping support bot: {e}", exc_info=True)

        # Stop main bot components
        if hasattr(self.app, 'updater') and self.app.updater:
            try:
                if self.app.updater.running:
                    logger.info("Stopping updater...")
                    await self.app.updater.stop()
                    logger.info("Updater stopped.")
                else:
                    logger.info("Updater was not running.")
            except RuntimeError as e:
                logger.warning(f"Error stopping updater (may be benign): {e}")
            except Exception as e:
                logger.error(f"Unexpected error stopping updater: {e}", exc_info=True)

        try:
            if self.app.running: # PTB's application.running
                logger.info("Stopping application (background tasks)...")
                await self.app.stop() # Stops background tasks like _update_fetcher
                logger.info("Application (background tasks) stopped.")
            else:
                logger.info("Application (background tasks) was not running.")
        except RuntimeError as e:
            logger.warning(f"Error stopping application (may be benign): {e}")
        except Exception as e:
            logger.error(f"Unexpected error stopping application: {e}", exc_info=True)

        # This is usually handled by `async with application:` on exit,
        # but we call it explicitly to ensure cleanup if shutdown is triggered by other means.
        try:
            if self.app.initialized:
                logger.info("Shutting down application (core cleanup)...")
                await self.app.shutdown() # Cleans up resources
                logger.info("Application (core cleanup) shut down.")
            else:
                logger.info("Application was not initialized for core shutdown.")
        except RuntimeError as e:
            logger.warning(f"Error during core application shutdown (may be benign): {e}")
        except Exception as e:
            logger.error(f"Unexpected error during core application shutdown: {e}", exc_info=True)

        # Close database connection
        if self.database and hasattr(self.database, 'close'):
            try:
                logger.info("Closing database connection...")
                await self.database.close()
                logger.info("Database connection closed.")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}", exc_info=True)
        else:
            logger.warning("Database object 'db' not found or no 'close' method.")

        logger.info(f"{self.config.bot_name} shutdown process complete.")
