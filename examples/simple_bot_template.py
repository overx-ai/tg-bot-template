"""
Simple example using the new Telegram Bot Template.

This example shows how to use the simplified bot template with minimal configuration.
"""

import asyncio
import logging
from telegram_bot_template import TelegramBot, BotConfig

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


async def main():
    """Main function to run the bot."""
    try:
        # Load configuration from environment variables
        config = BotConfig.from_env()
        
        # Optional: Override some settings
        config.bot_name = "Simple Bot Example"
        config.bot_description = "A simple bot using the new template"
        config.default_language = "en"
        
        # Create bot instance
        bot = TelegramBot(config)
        
        # Setup and run the bot
        logger.info("Starting Simple Bot Example...")
        await bot.run()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")


if __name__ == "__main__":
    asyncio.run(main())