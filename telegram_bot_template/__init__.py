"""
Simplified Telegram Bot Template

A clean, maintainable Telegram bot template with essential features:
- Locale management
- Keyboard management
- OpenRouter AI integration
- Optional support bot
- Simple user database

Usage:
    from telegram_bot_template import TelegramBot, BotConfig

    config = BotConfig.from_env()
    bot = TelegramBot(config)
    await bot.run()
"""

__version__ = "1.0.0"
__author__ = "Telegram Bot Template"

from telegram_bot_template.config.settings import BotConfig
from telegram_bot_template.core.bot import TelegramBot

__all__ = ["BotConfig", "TelegramBot"]
