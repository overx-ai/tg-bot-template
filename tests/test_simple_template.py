#!/usr/bin/env python3
"""
Test script for the simplified Telegram bot template.
This script validates the configuration and tests core components.
"""

import logging
import pytest # Added import

from telegram_bot_template import BotConfig
from telegram_bot_template import MockAIProvider
from telegram_bot_template import DatabaseManager
from telegram_bot_template import KeyboardManager
from telegram_bot_template import LocaleManager

# Setup logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

logger = logging.getLogger(__name__)


async def test_configuration(config: BotConfig): # Injected fixture
    """Test configuration loading and validation (via fixture)."""
    print("🔧 Testing configuration...")
    # The config fixture already loads and validates.
    # We just need to assert it's received and has expected basic properties.
    assert config is not None
    assert config.bot_name is not None
    print(f"✅ Configuration valid (via fixture): {config.bot_name}")
    # No return needed for pytest tests


async def test_locale_manager(locale_manager: LocaleManager): # Injected fixture
    """Test locale manager functionality (via fixture)."""
    print("🌐 Testing locale manager...")
    # The locale_manager fixture already creates an instance.
    # We can add specific assertions here if needed, beyond fixture creation.
    assert locale_manager is not None

    # Test English
    welcome_en = locale_manager.get("welcome_message", "en")
    assert welcome_en is not None and len(welcome_en) > 0
    print(f"✅ English locale: {len(welcome_en)} chars")

    # Test Russian
    welcome_ru = locale_manager.get("welcome_message", "ru")
    assert welcome_ru is not None and len(welcome_ru) > 0
    print(f"✅ Russian locale: {len(welcome_ru)} chars")

    # Test Spanish
    welcome_es = locale_manager.get("welcome_message", "es")
    assert welcome_es is not None and len(welcome_es) > 0
    print(f"✅ Spanish locale: {len(welcome_es)} chars")
    # No return needed for pytest tests


async def test_keyboard_manager(locale_manager: LocaleManager): # Injected fixture
    """Test keyboard manager."""
    print("⌨️ Testing keyboard manager...")
    # try/except removed as pytest handles test failures
    keyboard_manager = KeyboardManager(locale_manager)
    assert keyboard_manager is not None

    # Test main menu keyboard
    main_keyboard = keyboard_manager.get_main_menu_keyboard("en")
    assert main_keyboard is not None and len(main_keyboard.inline_keyboard) > 0
    print(f"✅ Main menu keyboard: {len(main_keyboard.inline_keyboard)} rows")

    # Test language selection keyboard
    lang_keyboard = keyboard_manager.get_language_selection_keyboard("en")
    assert lang_keyboard is not None and len(lang_keyboard.inline_keyboard) > 0
    print(f"✅ Language keyboard: {len(lang_keyboard.inline_keyboard)} rows")
    # No return needed for pytest tests


async def test_database(config: BotConfig): # Injected fixture
    """Test database connection."""
    print("💾 Testing database...")
    # try/except removed as pytest handles test failures
    # The conditional skip is removed as we now expect a PostgreSQL DSN from testcontainers
    db = DatabaseManager(config.database_url)
    await db.setup()
    assert db is not None # Basic assertion

    # Test user operations
    test_user = await db.ensure_user(12345, "test_user", "en")
    assert test_user is not None and test_user['user_id'] == 12345
    print(f"✅ User created/found: {test_user['user_id']}")

    # Test language update
    success = await db.update_user_language(12345, "ru")
    assert success is True
    print(f"✅ Language updated: {success}")

    # Test stats
    stats = await db.get_stats()
    assert stats is not None and 'total_users' in stats
    print(f"✅ Database stats: {stats['total_users']} users")

    await db.close()
    # No return needed for pytest tests


async def test_ai_provider():
    """Test AI provider."""
    print("🤖 Testing AI provider...")
    try:
        # Test mock provider
        mock_ai = MockAIProvider()
        response = await mock_ai.get_response("Hello, this is a test!")
        print(f"✅ Mock AI response: {response[:50]}...")
        # No return needed for pytest tests
    except Exception as e: # This try/except can remain for specific error logging if desired for this test
        print(f"❌ AI provider error: {e}")
        pytest.fail(f"AI provider test failed: {e}")


# The main() function and if __name__ == "__main__": block are removed
# as pytest will discover and run tests automatically.
