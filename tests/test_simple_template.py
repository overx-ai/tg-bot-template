#!/usr/bin/env python3
"""
Test script for the simplified Telegram bot template.
This script validates the configuration and tests core components.
"""

import asyncio
import logging
import sys

from telegram_bot_template.config.settings import BotConfig
from telegram_bot_template.core.ai_provider import MockAIProvider
from telegram_bot_template.core.database import DatabaseManager
from telegram_bot_template.core.keyboard_manager import KeyboardManager
from telegram_bot_template.core.locale_manager import LocaleManager

# Setup logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

logger = logging.getLogger(__name__)


async def test_configuration():
    """Test configuration loading."""
    print("🔧 Testing configuration...")
    try:
        config = BotConfig.from_env()
        config.validate()
        print(f"✅ Configuration valid: {config.bot_name}")
        return config
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return None


async def test_locale_manager():
    """Test locale manager."""
    print("🌐 Testing locale manager...")
    try:
        locale_manager = LocaleManager()

        # Test English
        welcome_en = locale_manager.get("welcome_message", "en")
        print(f"✅ English locale: {len(welcome_en)} chars")

        # Test Russian
        welcome_ru = locale_manager.get("welcome_message", "ru")
        print(f"✅ Russian locale: {len(welcome_ru)} chars")

        # Test Spanish
        welcome_es = locale_manager.get("welcome_message", "es")
        print(f"✅ Spanish locale: {len(welcome_es)} chars")

        return locale_manager
    except Exception as e:
        print(f"❌ Locale manager error: {e}")
        return None


async def test_keyboard_manager(locale_manager):
    """Test keyboard manager."""
    print("⌨️ Testing keyboard manager...")
    try:
        keyboard_manager = KeyboardManager(locale_manager)

        # Test main menu keyboard
        main_keyboard = keyboard_manager.get_main_menu_keyboard("en")
        print(f"✅ Main menu keyboard: {len(main_keyboard.inline_keyboard)} rows")

        # Test language selection keyboard
        lang_keyboard = keyboard_manager.get_language_selection_keyboard("en")
        print(f"✅ Language keyboard: {len(lang_keyboard.inline_keyboard)} rows")

        return keyboard_manager
    except Exception as e:
        print(f"❌ Keyboard manager error: {e}")
        return None


async def test_database(config):
    """Test database connection."""
    print("💾 Testing database...")
    try:
        db = DatabaseManager(config.database_url)
        await db.setup()

        # Test user operations
        test_user = await db.ensure_user(12345, "test_user", "en")
        print(f"✅ User created/found: {test_user['user_id']}")

        # Test language update
        success = await db.update_user_language(12345, "ru")
        print(f"✅ Language updated: {success}")

        # Test stats
        stats = await db.get_stats()
        print(f"✅ Database stats: {stats['total_users']} users")

        await db.close()
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


async def test_ai_provider():
    """Test AI provider."""
    print("🤖 Testing AI provider...")
    try:
        # Test mock provider
        mock_ai = MockAIProvider()
        response = await mock_ai.get_response("Hello, this is a test!")
        print(f"✅ Mock AI response: {response[:50]}...")

        return True
    except Exception as e:
        print(f"❌ AI provider error: {e}")
        return False


async def main():
    """Run all tests."""
    print("🧪 Starting Simplified Bot Template Tests\n")

    # Test configuration
    config = await test_configuration()
    if not config:
        print("❌ Configuration test failed, stopping tests")
        return False

    print()

    # Test locale manager
    locale_manager = await test_locale_manager()
    if not locale_manager:
        print("❌ Locale manager test failed")
        return False

    print()

    # Test keyboard manager
    keyboard_manager = await test_keyboard_manager(locale_manager)
    if not keyboard_manager:
        print("❌ Keyboard manager test failed")
        return False

    print()

    # Test database
    db_success = await test_database(config)
    if not db_success:
        print("❌ Database test failed")
        return False

    print()

    # Test AI provider
    ai_success = await test_ai_provider()
    if not ai_success:
        print("❌ AI provider test failed")
        return False

    print("\n✅ All tests passed! The simplified bot template is ready to use.")
    print("\n🚀 To start the bot, run:")
    print("   python -m telegram_bot_template.main")
    print("\n📖 For more options, run:")
    print("   python -m telegram_bot_template.main --help")

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
