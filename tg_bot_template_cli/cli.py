#!/usr/bin/env python3
"""
Unified CLI for Telegram Bot Template.
This provides a single 'tgbot' command with subcommands.
"""

import argparse
import sys
from pathlib import Path

from .create_bot import main as create_main
from .bot_factory import main as factory_main
from .mcp_bot_creator import main as mcp_main


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='tgbot',
        description='Telegram Bot Template - Create production-ready Telegram bots',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  tgbot new "My Bot"                    # Create a new bot with default settings
  tgbot new "AI Bot" --preset ai        # Create an AI-powered bot
  tgbot factory --list-presets          # List available presets
  tgbot mcp                             # Start MCP server for Claude Code

Commands:
  new       Create a new bot (simple mode)
  factory   Advanced bot creation with presets
  mcp       Start MCP server for Claude Code integration
'''
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # 'new' command (simple creation)
    new_parser = subparsers.add_parser('new', help='Create a new bot project')
    new_parser.add_argument('project_name', help='Name of your bot project')
    new_parser.add_argument('--output', '-o', default='.', help='Output directory')
    new_parser.add_argument('--preset', '-p', choices=['simple', 'ai', 'support', 'enterprise'],
                           help='Use a predefined preset')
    new_parser.add_argument('--no-git', action='store_true', help='Skip git initialization')
    new_parser.add_argument('--secrets', action='store_true', help='Create secrets.yaml file')
    
    # 'factory' command (advanced)
    factory_parser = subparsers.add_parser('factory', help='Advanced bot creation')
    factory_parser.add_argument('project_name', nargs='?', help='Name of your bot project')
    factory_parser.add_argument('--output', '-o', default='.', help='Output directory')
    factory_parser.add_argument('--preset', '-p', choices=['simple', 'ai', 'support', 'enterprise'],
                               help='Use a predefined preset')
    factory_parser.add_argument('--list-presets', action='store_true',
                               help='List all available presets')
    factory_parser.add_argument('--git-init', action='store_true', default=True,
                               help='Initialize git repository')
    factory_parser.add_argument('--create-secrets', action='store_true',
                               help='Create secrets.yaml file')
    factory_parser.add_argument('--json', action='store_true',
                               help='Output result as JSON')
    
    # 'mcp' command
    mcp_parser = subparsers.add_parser('mcp', help='Start MCP server')
    
    # 'version' command
    version_parser = subparsers.add_parser('version', help='Show version')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'new':
        # Convert args to sys.argv for create_bot
        sys.argv = ['create_bot.py', args.project_name]
        if args.output != '.':
            sys.argv.extend(['--output', args.output])
        
        # Add extra context for presets and options
        if args.preset:
            from .bot_factory import PRESETS
            preset = PRESETS.get(args.preset)
            if preset:
                if preset.use_openrouter == 'y':
                    sys.argv.append('use_openrouter=y')
                if preset.use_support_bot == 'y':
                    sys.argv.append('use_support_bot=y')
        
        if not args.no_git:
            sys.argv.append('git_init=y')
        if args.secrets:
            sys.argv.append('create_secrets=y')
            
        create_main()
        
    elif args.command == 'factory':
        # Pass through to factory
        factory_main()
        
    elif args.command == 'mcp':
        # Start MCP server
        import asyncio
        asyncio.run(mcp_main())
        
    elif args.command == 'version':
        from . import __version__
        print(f"Telegram Bot Template CLI v{__version__}")


if __name__ == '__main__':
    main()