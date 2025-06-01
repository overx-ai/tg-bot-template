"""Main entry point for the Telegram bot template with click CLI options."""

import asyncio
import logging
import sys
from pathlib import Path

import click

from telegram_bot_template.config.settings import BotConfig
from telegram_bot_template.core.bot import TelegramBot

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--locale", 
    default="en", 
    help="Bot default language (en, ru, es, etc.)",
    show_default=True
)
@click.option(
    "--debug", 
    is_flag=True, 
    help="Enable debug mode with verbose logging"
)
@click.option(
    "--support", 
    is_flag=True, 
    help="Force enable support bot (overrides env config)"
)
@click.option(
    "--config-file", 
    type=click.Path(exists=True),
    help="Path to custom configuration file"
)
@click.option(
    "--dry-run", 
    is_flag=True, 
    help="Validate configuration without starting the bot"
)
@click.option(
    "--stats", 
    is_flag=True, 
    help="Show bot statistics and exit"
)
@click.version_option(version="1.0.0", prog_name="Telegram Bot Template")
def main(locale: str, debug: bool, support: bool, config_file: str, dry_run: bool, stats: bool):
    """
    Simplified Telegram Bot Template
    
    A clean, maintainable Telegram bot with essential features:
    - Locale management
    - Keyboard management
    - OpenRouter AI integration
    - Optional support bot
    - Simple user database
    
    Examples:
        python -m telegram_bot_template.main --locale ru --debug
        python -m telegram_bot_template.main --support --dry-run
    """
    
    # Setup basic logging first
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=log_level
    )
    
    try:
        # Load configuration
        config = BotConfig.from_env()
        
        # Override locale if provided
        if locale != "en":
            config.default_language = locale
            if locale not in config.supported_languages:
                config.supported_languages.append(locale)
        
        # Override debug mode
        if debug:
            config.log_level = "DEBUG"
        
        # Force enable support bot if requested
        if support and not config.has_support_bot:
            click.echo("⚠️  Support bot requested but not properly configured in environment")
            click.echo("   Please set SUPPORT_BOT_TOKEN and SUPPORT_CHAT_ID")
            sys.exit(1)
        
        # Validate configuration
        config.validate()
        
        click.echo(f"🤖 {config.bot_name} v{config.bot_version}")
        click.echo(f"📍 Language: {config.default_language}")
        click.echo(f"🤖 AI Support: {'✅' if config.has_ai_support else '❌'}")
        click.echo(f"🆘 Support Bot: {'✅' if config.has_support_bot else '❌'}")
        
        if dry_run:
            click.echo("✅ Configuration validation passed")
            click.echo("🔍 Dry run mode - bot not started")
            return
        
        if stats:
            asyncio.run(show_stats(config))
            return
        
        # Create and run bot
        bot = TelegramBot(config)
        
        click.echo("🚀 Starting bot...")
        asyncio.run(bot.run())
        
    except KeyboardInterrupt:
        click.echo("\n👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


async def show_stats(config: BotConfig):
    """Show bot statistics."""
    try:
        bot = TelegramBot(config)
        await bot.setup()
        
        stats = await bot.get_stats()
        
        click.echo("\n📊 Bot Statistics:")
        click.echo("=" * 40)
        
        for key, value in stats.items():
            if isinstance(value, dict):
                click.echo(f"{key.replace('_', ' ').title()}:")
                for sub_key, sub_value in value.items():
                    click.echo(f"  • {sub_key}: {sub_value}")
            else:
                click.echo(f"{key.replace('_', ' ').title()}: {value}")
        
        await bot.stop()
        
    except Exception as e:
        click.echo(f"❌ Error getting stats: {e}", err=True)


@click.group()
def cli():
    """Telegram Bot Template CLI."""
    pass


@cli.command()
@click.option("--output", "-o", default="bot_config.env", help="Output file name")
def init_config(output: str):
    """Initialize a new bot configuration file."""
    config_template = """# Telegram Bot Configuration
# Copy this file to .env and fill in your values

# Required Settings
TELEGRAM_BOT_TOKEN=your_bot_token_here
DATABASE_URL=postgresql://user:password@localhost:5432/botdb

# Optional - OpenRouter AI
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=openai/gpt-3.5-turbo

# Optional - Support Bot
SUPPORT_BOT_TOKEN=your_support_bot_token_here
SUPPORT_CHAT_ID=your_support_chat_id_here

# Optional - Bot Metadata
BOT_NAME=My Telegram Bot
BOT_DESCRIPTION=A simple Telegram bot
BOT_VERSION=1.0.0

# Optional - Localization
DEFAULT_LANGUAGE=en
SUPPORTED_LANGUAGES=en,ru,es

# Optional - Logging
LOG_LEVEL=INFO
"""
    
    try:
        with open(output, 'w') as f:
            f.write(config_template)
        
        click.echo(f"✅ Configuration template created: {output}")
        click.echo("📝 Please edit the file and add your bot token and database URL")
        
    except Exception as e:
        click.echo(f"❌ Error creating config file: {e}", err=True)


@cli.command()
def validate():
    """Validate bot configuration."""
    try:
        config = BotConfig.from_env()
        config.validate()
        
        click.echo("✅ Configuration is valid")
        click.echo(f"🤖 Bot: {config.bot_name}")
        click.echo(f"🔗 Database: {config.database_url[:20]}...")
        click.echo(f"🤖 AI: {'Enabled' if config.has_ai_support else 'Disabled'}")
        click.echo(f"🆘 Support: {'Enabled' if config.has_support_bot else 'Disabled'}")
        
    except Exception as e:
        click.echo(f"❌ Configuration error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--locale", default="en", help="Language for test")
def test_ai(locale: str):
    """Test AI provider connection."""
    async def _test():
        try:
            config = BotConfig.from_env()
            
            if not config.has_ai_support:
                click.echo("❌ AI support not configured")
                return
            
            from telegram_bot_template.core.ai_provider import OpenRouterProvider
            
            provider = OpenRouterProvider(
                api_key=config.openrouter_api_key,
                model=config.openrouter_model
            )
            
            click.echo("🔄 Testing AI connection...")
            
            if await provider.test_connection():
                click.echo("✅ AI provider connection successful")
                
                # Test a simple message
                response = await provider.get_response("Hello, this is a test message.")
                click.echo(f"🤖 Test response: {response[:100]}...")
            else:
                click.echo("❌ AI provider connection failed")
        
        except Exception as e:
            click.echo(f"❌ AI test error: {e}", err=True)
    
    asyncio.run(_test())


@cli.command()
def test_db():
    """Test database connection."""
    async def _test():
        try:
            config = BotConfig.from_env()
            
            from telegram_bot_template.core.database import DatabaseManager
            
            db = DatabaseManager(config.database_url)
            
            click.echo("🔄 Testing database connection...")
            await db.setup()
            
            # Test basic operations
            stats = await db.get_stats()
            click.echo("✅ Database connection successful")
            click.echo(f"📊 Total users: {stats.get('total_users', 0)}")
            
            await db.close()
        
        except Exception as e:
            click.echo(f"❌ Database test error: {e}", err=True)
    
    asyncio.run(_test())


# Add subcommands to main CLI
cli.add_command(init_config)
cli.add_command(validate)
cli.add_command(test_ai)
cli.add_command(test_db)


if __name__ == "__main__":
    main()