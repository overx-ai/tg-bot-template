"""Helper utility functions for the Telegram bot template."""

import logging
import re
import sys
from typing import List, Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output for different log levels."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[37m",  # White
        "INFO": "\033[34m",  # Blue
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[91m",  # Bright Red
    }
    RESET = "\033[0m"  # Reset color

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Check if output is to a terminal (supports colors)
        self.use_colors = hasattr(sys.stderr, "isatty") and sys.stderr.isatty()

    def format(self, record):
        if self.use_colors and record.levelname in self.COLORS:
            # Add color to the level name
            colored_levelname = f"{self.COLORS[record.levelname]}[{record.levelname}]{self.RESET}"
            # Store original levelname
            original_levelname = record.levelname
            # Temporarily replace levelname with colored version
            record.levelname = colored_levelname
            # Format the message
            formatted = super().format(record)
            # Restore original levelname
            record.levelname = original_levelname
            return formatted
        else:
            # No colors - format normally with brackets around level
            original_levelname = record.levelname
            record.levelname = f"[{record.levelname}]"
            formatted = super().format(record)
            record.levelname = original_levelname
            return formatted


def setup_logging():
    """Set up enhanced logging configuration with colors and detailed format."""
    # Create formatter
    formatter = ColoredFormatter(
        fmt="%(asctime)s %(levelname)s %(filename)s:%(funcName)s:%(lineno)d - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler with proper Unicode handling
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Configure stream to handle Unicode characters properly
    console_handler.stream.reconfigure(errors="backslashreplace")

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Suppress httpx INFO logs
    logging.getLogger("httpx").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)


def escape_markdown(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2 formatting.

    Args:
        text: The input text to escape

    Returns:
        Escaped text safe for MarkdownV2
    """
    # Characters that need escaping in MarkdownV2
    escape_chars = r"_*[]()~`>#+-=|{}.!"

    # Escape each special character with a backslash
    return re.sub(r"([\\" + re.escape(escape_chars) + r"])", r"\\\1", text)


def format_message(template: str, **kwargs) -> str:
    """Format a message template with provided arguments.

    Args:
        template: Message template with placeholders
        **kwargs: Arguments to fill placeholders

    Returns:
        Formatted message
    """
    try:
        return template.format(**kwargs)
    except KeyError as e:
        logger.error(f"Missing format argument {e} for template: {template[:50]}...")
        return template
    except Exception as e:
        logger.error(f"Error formatting message: {e}")
        return template


def split_long_message(message: str, max_length: int = 4000) -> List[str]:
    """Split a long message into multiple parts that fit within Telegram's limits.

    Args:
        message: The message to split
        max_length: Maximum length per part (default: 4000)

    Returns:
        List of message parts
    """
    if len(message) <= max_length:
        return [message]

    parts = []
    remaining = message

    while remaining:
        if len(remaining) <= max_length:
            parts.append(remaining)
            break

        # Find appropriate split points (prefer paragraph breaks, then line breaks, then spaces)
        split_point = remaining[:max_length].rfind("\n\n")
        if split_point == -1:
            split_point = remaining[:max_length].rfind("\n")
        if split_point == -1:
            split_point = remaining[:max_length].rfind(" ")
        if split_point == -1:
            split_point = max_length

        parts.append(remaining[:split_point])
        remaining = remaining[split_point:].lstrip()

    return parts


def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace and normalizing line breaks.

    Args:
        text: Text to clean

    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)

    # Normalize line breaks
    text = re.sub(r"\n\s*\n", "\n\n", text)

    return text.strip()


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncating

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def extract_command_args(text: str) -> tuple:
    """Extract command and arguments from a message.

    Args:
        text: Message text starting with a command

    Returns:
        Tuple of (command, args_list)
    """
    parts = text.strip().split()
    if not parts:
        return "", []

    command = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []

    return command, args


def format_user_mention(user_id: int, username: Optional[str] = None, first_name: Optional[str] = None) -> str:
    """Format a user mention for display.

    Args:
        user_id: User's Telegram ID
        username: User's username (optional)
        first_name: User's first name (optional)

    Returns:
        Formatted user mention
    """
    if username:
        return f"@{username} ({user_id})"
    elif first_name:
        return f"{first_name} ({user_id})"
    else:
        return str(user_id)


def validate_language_code(language: str, supported_languages: List[str]) -> str:
    """Validate and normalize language code.

    Args:
        language: Language code to validate
        supported_languages: List of supported language codes

    Returns:
        Validated language code or default 'en'
    """
    language = language.lower().strip()

    if language in supported_languages:
        return language

    # Try to match by prefix (e.g., 'en-US' -> 'en')
    for supported in supported_languages:
        if language.startswith(supported):
            return supported

    # Default to English
    return "en"


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds}s" if remaining_seconds else f"{minutes}m"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        return f"{hours}h {remaining_minutes}m" if remaining_minutes else f"{hours}h"


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def is_valid_telegram_token(token: str) -> bool:
    """Validate Telegram bot token format.

    Args:
        token: Bot token to validate

    Returns:
        True if token format is valid
    """
    # Telegram bot token format: <bot_id>:<bot_secret>
    # bot_id is numeric, bot_secret is alphanumeric with some special chars
    pattern = r"^\d+:[A-Za-z0-9_-]+$"
    return bool(re.match(pattern, token))


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing/replacing invalid characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)

    # Remove leading/trailing dots and spaces
    filename = filename.strip(". ")

    # Ensure filename is not empty
    if not filename:
        filename = "file"

    return filename


def parse_callback_data(callback_data: str, separator: str = "_") -> List[str]:
    """Parse callback data into components.

    Args:
        callback_data: Callback data string
        separator: Separator character

    Returns:
        List of callback data components
    """
    return callback_data.split(separator) if callback_data else []


def build_callback_data(*components, separator: str = "_") -> str:
    """Build callback data from components.

    Args:
        *components: Components to join
        separator: Separator character

    Returns:
        Joined callback data string
    """
    return separator.join(str(comp) for comp in components)


def get_user_display_name(user) -> str:
    """Get display name for a Telegram user.

    Args:
        user: Telegram User object

    Returns:
        User's display name
    """
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    elif user.first_name:
        return user.first_name
    elif user.username:
        return f"@{user.username}"
    else:
        return f"User {user.id}"


def format_timestamp(timestamp, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format timestamp to string.

    Args:
        timestamp: Timestamp object
        format_str: Format string

    Returns:
        Formatted timestamp string
    """
    try:
        return timestamp.strftime(format_str)
    except Exception as e:
        logger.error(f"Error formatting timestamp: {e}")
        return str(timestamp)
