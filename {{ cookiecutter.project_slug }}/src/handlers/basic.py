"""Basic command handlers for the Telegram bot template."""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot_template.core.database import DatabaseManager
from telegram_bot_template.core.keyboard_manager import KeyboardManager
from telegram_bot_template.core.locale_manager import LocaleManager

logger = logging.getLogger(__name__)


class BasicHandlers:
    """Handles basic bot commands like /start, /help, /about."""

    def __init__(self, locale_manager: LocaleManager, keyboard_manager: KeyboardManager, database: DatabaseManager, config):
        self.locale_manager = locale_manager
        self.keyboard_manager = keyboard_manager
        self.database = database
        self.config = config

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        user = update.effective_user
        chat = update.effective_chat

        if not user:
            return

        try:
            # Ensure user exists in database
            user_data = await self.database.ensure_user(user_id=user.id, username=user.username, language=self.config.default_language)

            user_language = user_data.get("language", self.config.default_language)

            # Get welcome message
            welcome_text = self.locale_manager.format(
                "welcome_message",
                language=user_language,
                bot_name=self.config.bot_name,
                description=self.config.bot_description,
                version=self.config.bot_version,
            )

            # Get main menu keyboard
            keyboard = self.keyboard_manager.get_main_menu_keyboard(user_language)

            await update.message.reply_text(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

            logger.info(f"User {user.id} (@{user.username}) started the bot")

        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text("Sorry, something went wrong. Please try again.")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        user = update.effective_user

        if not user:
            return

        try:
            # Get user language
            user_language = await self.database.get_user_language(user.id)

            # Available commands
            commands = ["/start - Start the bot", "/help - Show this help message", "/about - About this bot"]

            help_text = self.locale_manager.format("help_message", language=user_language, available_commands="\n".join(commands))

            keyboard = self.keyboard_manager.get_back_keyboard(user_language)

            await update.message.reply_text(help_text, reply_markup=keyboard, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error in help command: {e}")
            await update.message.reply_text("Sorry, something went wrong. Please try again.")

    async def about_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /about command."""
        user = update.effective_user

        if not user:
            return

        try:
            # Get user language
            user_language = await self.database.get_user_language(user.id)

            about_text = self.locale_manager.format(
                "about_message",
                language=user_language,
                bot_name=self.config.bot_name,
                description=self.config.bot_description,
                version=self.config.bot_version,
            )

            keyboard = self.keyboard_manager.get_back_keyboard(user_language)

            await update.message.reply_text(about_text, reply_markup=keyboard, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error in about command: {e}")
            await update.message.reply_text("Sorry, something went wrong. Please try again.")

    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback queries from inline keyboards."""
        query = update.callback_query
        user = query.from_user

        if not user:
            return

        await query.answer()

        try:
            # Get user language
            user_language = await self.database.get_user_language(user.id)

            if query.data == "help":
                await self._show_help(query, user_language)

            elif query.data == "about":
                await self._show_about(query, user_language)

            elif query.data == "settings":
                await self._show_settings(query, user_language)

            elif query.data == "change_language":
                await self._show_language_selection(query, user_language)

            elif query.data.startswith("set_language_"):
                new_language = query.data.split("_")[-1]
                await self._set_language(query, user.id, new_language)

            elif query.data == "back_to_menu":
                await self._show_main_menu(query, user_language)

            else:
                logger.warning(f"Unknown callback data: {query.data}")
                await query.edit_message_text(self.locale_manager.get("unknown_command", user_language))

        except Exception as e:
            logger.error(f"Error in callback query handler: {e}")
            await query.edit_message_text("Sorry, something went wrong. Please try again.")

    async def _show_help(self, query, language: str) -> None:
        """Show help message."""
        commands = ["/start - Start the bot", "/help - Show help message", "/about - About this bot"]

        help_text = self.locale_manager.format("help_message", language=language, available_commands="\n".join(commands))

        keyboard = self.keyboard_manager.get_back_keyboard(language)

        await query.edit_message_text(help_text, reply_markup=keyboard, parse_mode="Markdown")

    async def _show_about(self, query, language: str) -> None:
        """Show about message."""
        about_text = self.locale_manager.format(
            "about_message",
            language=language,
            bot_name=self.config.bot_name,
            description=self.config.bot_description,
            version=self.config.bot_version,
        )

        keyboard = self.keyboard_manager.get_back_keyboard(language)

        await query.edit_message_text(about_text, reply_markup=keyboard, parse_mode="Markdown")

    async def _show_settings(self, query, language: str) -> None:
        """Show settings menu."""
        settings_text = "⚙️ Settings"
        keyboard = self.keyboard_manager.get_settings_keyboard(language)

        await query.edit_message_text(settings_text, reply_markup=keyboard)

    async def _show_language_selection(self, query, current_language: str) -> None:
        """Show language selection menu."""
        text = self.locale_manager.get("language_selection", current_language)
        keyboard = self.keyboard_manager.get_language_selection_keyboard(current_language)

        await query.edit_message_text(text, reply_markup=keyboard)

    async def _set_language(self, query, user_id: int, new_language: str) -> None:
        """Set user's language preference."""
        try:
            # Update language in database
            success = await self.database.update_user_language(user_id, new_language)

            if success:
                # Show confirmation
                confirmation_text = self.locale_manager.get("language_changed", new_language)
                keyboard = self.keyboard_manager.get_main_menu_keyboard(new_language)

                await query.edit_message_text(confirmation_text, reply_markup=keyboard)

                logger.info(f"User {user_id} changed language to {new_language}")
            else:
                await query.edit_message_text("Failed to update language preference.")

        except Exception as e:
            logger.error(f"Error setting language: {e}")
            await query.edit_message_text("Sorry, something went wrong while changing the language.")

    async def _show_main_menu(self, query, language: str) -> None:
        """Show main menu."""
        welcome_text = self.locale_manager.format(
            "welcome_message",
            language=language,
            bot_name=self.config.bot_name,
            description=self.config.bot_description,
            version=self.config.bot_version,
        )

        keyboard = self.keyboard_manager.get_main_menu_keyboard(language)

        await query.edit_message_text(welcome_text, reply_markup=keyboard, parse_mode="Markdown")
