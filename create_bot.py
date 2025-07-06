#!/usr/bin/env python3
"""
Simple bot creation script that accepts just a project name.
Usage: python create_bot.py "My Awesome Bot"
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional


def slugify(name: str) -> str:
    """Convert project name to slug format."""
    return name.lower().replace(' ', '-').replace('_', '-')


def load_defaults() -> Dict[str, Any]:
    """Load default values from cookiecutter.json."""
    cookiecutter_path = Path(__file__).parent / 'cookiecutter.json'
    with open(cookiecutter_path, 'r') as f:
        return json.load(f)


def create_cookiecutter_config(project_name: str, output_dir: str = ".", 
                             extra_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create cookiecutter configuration with overrides."""
    defaults = load_defaults()
    
    # Start with project name
    context = {
        'project_name': project_name,
        'project_slug': slugify(project_name)
    }
    
    # Apply any extra overrides
    if extra_context:
        context.update(extra_context)
    
    # Build full config
    config = {
        'default_context': context,
        'output_dir': output_dir,
        'no_input': True  # Don't prompt for inputs
    }
    
    return config


def create_bot(project_name: str, output_dir: str = ".", 
               extra_context: Optional[Dict[str, Any]] = None) -> bool:
    """Create a new bot project using cookiecutter."""
    try:
        # Import cookiecutter
        try:
            from cookiecutter.main import cookiecutter
        except ImportError:
            print("Error: cookiecutter is not installed")
            print("Install with: pip install cookiecutter")
            return False
        
        # Get template path
        template_path = str(Path(__file__).parent)
        
        # Create context
        context = {'project_name': project_name}
        if extra_context:
            context.update(extra_context)
        
        # Run cookiecutter
        project_dir = cookiecutter(
            template_path,
            no_input=True,
            extra_context=context,
            output_dir=output_dir
        )
        
        print(f"✅ Bot project created successfully at: {project_dir}")
        
        # Show next steps
        project_slug = slugify(project_name)
        print(f"\n📋 Next steps:")
        print(f"1. cd {project_slug}")
        print(f"2. cp .env.example .env")
        print(f"3. Edit .env with your bot token and database URL")
        print(f"4. pip install -r requirements.txt")
        print(f"5. python -m {project_slug.replace('-', '_')}.main")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating bot: {e}")
        return False


def parse_extra_args(args: list) -> Dict[str, Any]:
    """Parse extra arguments in key=value format."""
    extra = {}
    for arg in args:
        if '=' in arg:
            key, value = arg.split('=', 1)
            # Convert boolean strings
            if value.lower() in ('true', 'yes', 'y'):
                value = 'y'
            elif value.lower() in ('false', 'no', 'n'):
                value = 'n'
            extra[key] = value
    return extra


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Create a new Telegram bot project',
        epilog='Examples:\n'
               '  python create_bot.py "Weather Bot"\n'
               '  python create_bot.py "Todo Bot" --output ~/bots\n'
               '  python create_bot.py "AI Bot" use_openrouter=y openrouter_model=gpt-4\n',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('project_name', help='Name of your bot project')
    parser.add_argument('--output', '-o', default='.', 
                       help='Output directory (default: current directory)')
    parser.add_argument('--list-options', action='store_true',
                       help='List all available options from cookiecutter.json')
    
    # Allow extra arguments for cookiecutter variables
    args, extra_args = parser.parse_known_args()
    
    if args.list_options:
        print("Available options:")
        defaults = load_defaults()
        for key, value in defaults.items():
            if not key.startswith('_'):
                print(f"  {key} = {value}")
        return
    
    # Parse extra arguments
    extra_context = parse_extra_args(extra_args)
    
    # Create the bot
    success = create_bot(args.project_name, args.output, extra_context)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()