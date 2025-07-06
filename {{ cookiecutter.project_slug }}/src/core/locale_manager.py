"""Locale management for the Telegram bot template."""

import json
import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class LocaleManager:
    """Manages localization and translations for the bot."""

    def __init__(self, locales_dir: str = "locales", default_language: str = "en"):
        self.locales_dir = locales_dir
        self.default_language = default_language
        self._locales: Dict[str, Dict[str, str]] = {}
        self._current_language = default_language

        # Load all available locales
        self._load_locales()

    def _load_locales(self) -> None:
        """Load all locale files from the locales directory."""
        if not os.path.exists(self.locales_dir):
            logger.warning(f"Locales directory '{self.locales_dir}' not found")
            return

        for filename in os.listdir(self.locales_dir):
            if filename.endswith(".json"):
                language = filename[:-5]  # Remove .json extension
                try:
                    with open(os.path.join(self.locales_dir, filename), "r", encoding="utf-8") as f:
                        self._locales[language] = json.load(f)
                    logger.debug(f"Loaded locale: {language}")
                except Exception as e:
                    logger.error(f"Failed to load locale {language}: {e}")

        if not self._locales:
            logger.warning("No locales loaded, using fallback strings")
            self._create_fallback_locale()

        logger.info(f"Loaded {len(self._locales)} locales: {list(self._locales.keys())}")

    def _create_fallback_locale(self) -> None:
        """Create a fallback locale with basic English strings."""
        self._locales["en"] = {
            "welcome_message": "🤖 Welcome to {bot_name}!\n\n{description}\n\nVersion: {version}",
            "help_message": "ℹ️ *Help*\n\nAvailable commands:\n{available_commands}\n\nJust send me a message and I'll try to help!",
            "about_message": "ℹ️ *About {bot_name}*\n\n{description}\n\nVersion: {version}",
            "language_changed": "✅ Language changed to English",
            "language_selection": "🌐 Please select your language:",
            "back_to_menu": "🔙 Back to Menu",
            "help": "ℹ️ Help",
            "about": "ℹ️ About",
            "settings": "⚙️ Settings",
            "language": "🌐 Language",
            "processing": "⏳ Processing your message...",
            "error_occurred": "❌ An error occurred. Please try again.",
            "ai_not_available": "🤖 AI assistant is not available at the moment.",
            "support_welcome": "👋 Welcome to support! Send your message and we'll help you.",
            "support_reply": "💬 *Support Reply:*\n\n{answer}",
            "support_use_reply": "Please reply to a user message to send a response.",
            "unknown_command": "❓ Unknown command. Type /help for available commands.",
        }

    def set_language(self, language: str) -> bool:
        """Set the current language."""
        if language in self._locales:
            self._current_language = language
            logger.debug(f"Language set to: {language}")
            return True
        else:
            logger.warning(f"Language '{language}' not available, using default")
            return False

    def get_current_language(self) -> str:
        """Get the current language."""
        return self._current_language

    def get_available_languages(self) -> list:
        """Get list of available languages."""
        return list(self._locales.keys())

    def get(self, key: str, language: Optional[str] = None, default: str = "") -> str:
        """Get a localized string."""
        target_language = language or self._current_language

        # Try to get from target language
        if target_language in self._locales:
            value = self._locales[target_language].get(key)
            if value:
                return value

        # Fallback to default language
        if target_language != self.default_language and self.default_language in self._locales:
            value = self._locales[self.default_language].get(key)
            if value:
                logger.debug(f"Using fallback for key '{key}' in language '{target_language}'")
                return value

        # Fallback to English if available
        if "en" in self._locales and target_language != "en":
            value = self._locales["en"].get(key)
            if value:
                logger.debug(f"Using English fallback for key '{key}' in language '{target_language}'")
                return value

        # Return default or key if nothing found
        if default:
            return default

        logger.warning(f"Translation key '{key}' not found for language '{target_language}'")
        return key  # Return the key itself as last resort

    def format(self, key: str, language: Optional[str] = None, **kwargs) -> str:
        """Get a localized string and format it with provided arguments."""
        template = self.get(key, language)
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing format argument {e} for key '{key}'")
            return template
        except Exception as e:
            logger.error(f"Error formatting string for key '{key}': {e}")
            return template

    def has_key(self, key: str, language: Optional[str] = None) -> bool:
        """Check if a translation key exists."""
        target_language = language or self._current_language
        return target_language in self._locales and key in self._locales[target_language]

    def add_translation(self, language: str, key: str, value: str) -> None:
        """Add or update a translation."""
        if language not in self._locales:
            self._locales[language] = {}

        self._locales[language][key] = value
        logger.debug(f"Added translation for '{key}' in '{language}'")

    def get_language_name(self, language_code: str) -> str:
        """Get human-readable language name."""
        language_names = {
            "en": "English",
            "ru": "Русский",
            "es": "Español",
            "de": "Deutsch",
            "fr": "Français",
            "it": "Italiano",
            "pt": "Português",
            "zh": "中文",
            "ja": "日本語",
            "ko": "한국어",
            "ar": "العربية",
            "hi": "हिन्दी",
        }
        return language_names.get(language_code, language_code.upper())

    def get_language_flag(self, language_code: str) -> str:
        """Get flag emoji for language."""
        language_flags = {
            "en": "🇺🇸",
            "ru": "🇷🇺",
            "es": "🇪🇸",
            "de": "🇩🇪",
            "fr": "🇫🇷",
            "it": "🇮🇹",
            "pt": "🇵🇹",
            "zh": "🇨🇳",
            "ja": "🇯🇵",
            "ko": "🇰🇷",
            "ar": "🇸🇦",
            "hi": "🇮🇳",
        }
        return language_flags.get(language_code, "🌐")

    def reload_locales(self) -> None:
        """Reload all locale files."""
        self._locales.clear()
        self._load_locales()
        logger.info("Locales reloaded")


# Global instance for easy access
locale_manager = LocaleManager()
