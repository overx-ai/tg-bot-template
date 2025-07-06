"""Support bot implementation for the Telegram bot template."""

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from telegram_bot_template.core.locale_manager import LocaleManager

logger = logging.getLogger(__name__)


class SupportBot:
    """Optional support bot for handling user support requests."""

    def __init__(self, support_token: str, support_chat_id: int, locale_manager: LocaleManager):
        self.support_token = support_token
        self.support_chat_id = support_chat_id
        self.locale_manager = locale_manager
        self.app = None

        logger.info(f"Support bot initialized for chat ID: {support_chat_id}")

    async def setup(self) -> None:
        """Setup the support bot application."""
        try:
            self.app = Application.builder().token(self.support_token).build()

            # Add handlers
            self.app.add_handler(CommandHandler("start", self._start_command))
            self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))

            logger.info("Support bot setup completed")

        except Exception as e:
            logger.error(f"Support bot setup failed: {e}")
            raise

    async def start(self) -> None:
        """Start the support bot."""
        if not self.app:
            await self.setup()

        try:
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling(drop_pending_updates=True)

            logger.info("Support bot started successfully")

        except Exception as e:
            logger.error(f"Failed to start support bot: {e}")
            raise

    async def stop(self) -> None:
        """Stop the support bot."""
        if self.app:
            try:
                await self.app.updater.stop()
                await self.app.stop()
                await self.app.shutdown()

                logger.info("Support bot stopped")

            except Exception as e:
                logger.error(f"Error stopping support bot: {e}")

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command for support bot."""
        user = update.effective_user

        if not user:
            return

        welcome_message = self.locale_manager.get("support_welcome")
        await update.message.reply_text(welcome_message)

        logger.info(f"Support bot: User {user.id} (@{user.username}) started support")

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle messages sent to support bot."""
        user = update.effective_user
        message = update.message

        if not user or not message or not message.text:
            return

        try:
            # Check if message is from support admin
            if user.id == self.support_chat_id:
                await self._handle_admin_reply(update, context)
            else:
                await self._forward_to_support(update, context)

        except Exception as e:
            logger.error(f"Error handling support message: {e}")
            await message.reply_text("Sorry, something went wrong. Please try again.")

    async def _forward_to_support(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Forward user message to support admin."""
        user = update.effective_user
        message = update.message

        try:
            # Format message for support admin
            support_message = (
                f"📩 *New Support Message*\n\n"
                f"👤 **User:** {user.id} (@{user.username or 'No username'})\n"
                f"📝 **Message:**\n{message.text}\n\n"
                f"💡 *Reply to this message to respond to the user*"
            )

            # Send to support admin
            await context.bot.send_message(chat_id=self.support_chat_id, text=support_message, parse_mode="Markdown")

            # Confirm to user
            confirmation = "✅ Your message has been sent to support. We'll get back to you soon!"
            await message.reply_text(confirmation)

            logger.info(f"Support message forwarded from user {user.id}")

        except Exception as e:
            logger.error(f"Error forwarding to support: {e}")
            await message.reply_text("Sorry, we couldn't send your message to support. Please try again later.")

    async def _handle_admin_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle reply from support admin."""
        message = update.message

        if not message.reply_to_message:
            await message.reply_text(self.locale_manager.get("support_use_reply"))
            return

        try:
            # Extract user ID from the original message
            original_text = message.reply_to_message.text

            if "👤 **User:** " in original_text:
                # Extract user ID
                user_line = original_text.split("👤 **User:** ")[1].split("\n")[0]
                user_id_str = user_line.split(" ")[0]
                user_id = int(user_id_str)

                # Format reply message
                reply_text = self.locale_manager.format("support_reply", answer=message.text)

                # Send reply to user
                await context.bot.send_message(chat_id=user_id, text=reply_text, parse_mode="Markdown")

                # Confirm to admin
                await message.reply_text(f"✅ Reply sent to user {user_id}")

                logger.info(f"Support reply sent to user {user_id}")

            else:
                await message.reply_text("❌ Could not extract user ID from the original message.")

        except (ValueError, IndexError) as e:
            logger.error(f"Error parsing user ID: {e}")
            await message.reply_text("❌ Could not parse user ID. Please check the message format.")

        except Exception as e:
            logger.error(f"Error sending admin reply: {e}")
            await message.reply_text("❌ Failed to send reply to user. Please try again.")

    def is_configured(self) -> bool:
        """Check if support bot is properly configured."""
        return bool(self.support_token and self.support_chat_id)

    async def send_notification(self, message: str) -> bool:
        """Send a notification to support admin.

        Args:
            message: Notification message to send

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.app:
            return False

        try:
            await self.app.bot.send_message(chat_id=self.support_chat_id, text=f"🔔 **Notification**\n\n{message}", parse_mode="Markdown")
            return True

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False

    async def send_stats(self, stats: dict) -> bool:
        """Send bot statistics to support admin.

        Args:
            stats: Dictionary with bot statistics

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.app:
            return False

        try:
            stats_message = "📊 **Bot Statistics**\n\n"

            for key, value in stats.items():
                if isinstance(value, dict):
                    stats_message += f"**{key.replace('_', ' ').title()}:**\n"
                    for sub_key, sub_value in value.items():
                        stats_message += f"  • {sub_key}: {sub_value}\n"
                else:
                    stats_message += f"**{key.replace('_', ' ').title()}:** {value}\n"

            await self.app.bot.send_message(chat_id=self.support_chat_id, text=stats_message, parse_mode="Markdown")
            return True

        except Exception as e:
            logger.error(f"Failed to send stats: {e}")
            return False
