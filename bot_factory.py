#!/usr/bin/env python3
"""
Bot Factory - Advanced bot creation with presets and Claude Code integration.
This can be used as a standalone CLI or imported as a module.
"""

import argparse
import json
import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class BotPreset:
    """Predefined bot configuration preset."""
    name: str
    description: str
    use_openrouter: str = 'n'
    openrouter_model: str = ''
    use_support_bot: str = 'n'
    use_docker: str = 'y'
    use_github_actions: str = 'y'
    extra_features: Dict[str, Any] = None


# Predefined bot presets
PRESETS = {
    'simple': BotPreset(
        name='simple',
        description='Basic bot with minimal features',
        use_openrouter='n',
        use_support_bot='n',
        use_docker='n',
        use_github_actions='n'
    ),
    'ai': BotPreset(
        name='ai',
        description='AI-powered bot with OpenRouter integration',
        use_openrouter='y',
        openrouter_model='google/gemini-2.0-flash-001',
        use_support_bot='n'
    ),
    'support': BotPreset(
        name='support',
        description='Customer support bot with ticket system',
        use_openrouter='y',
        openrouter_model='google/gemini-2.0-flash-001',
        use_support_bot='y'
    ),
    'enterprise': BotPreset(
        name='enterprise',
        description='Full-featured enterprise bot',
        use_openrouter='y',
        openrouter_model='gpt-4',
        use_support_bot='y',
        use_docker='y',
        use_github_actions='y'
    )
}


class BotFactory:
    """Factory class for creating Telegram bot projects."""
    
    def __init__(self, template_dir: Optional[Path] = None):
        self.template_dir = template_dir or Path(__file__).parent
        self.cookiecutter_json = self.template_dir / 'cookiecutter.json'
        self.defaults = self._load_defaults()
    
    def _load_defaults(self) -> Dict[str, Any]:
        """Load default values from cookiecutter.json."""
        with open(self.cookiecutter_json, 'r') as f:
            return json.load(f)
    
    def _slugify(self, name: str) -> str:
        """Convert project name to slug format."""
        return name.lower().replace(' ', '-').replace('_', '-')
    
    def create_bot(self, 
                   project_name: str,
                   output_dir: str = ".",
                   preset: Optional[str] = None,
                   extra_context: Optional[Dict[str, Any]] = None,
                   git_init: bool = True,
                   create_secrets: bool = False) -> Dict[str, Any]:
        """
        Create a new bot project.
        
        Args:
            project_name: Name of the bot project
            output_dir: Where to create the project
            preset: Use a predefined preset (simple, ai, support, enterprise)
            extra_context: Additional cookiecutter variables
            git_init: Initialize git repository
            create_secrets: Create secrets.yaml from template
            
        Returns:
            Dictionary with creation results and project info
        """
        try:
            from cookiecutter.main import cookiecutter
        except ImportError:
            return {
                'success': False,
                'error': 'cookiecutter not installed. Run: pip install cookiecutter'
            }
        
        # Build context
        context = {'project_name': project_name}
        
        # Apply preset if specified
        if preset and preset in PRESETS:
            preset_config = PRESETS[preset]
            context.update({
                'use_openrouter': preset_config.use_openrouter,
                'openrouter_model': preset_config.openrouter_model,
                'use_support_bot': preset_config.use_support_bot,
                'use_docker': preset_config.use_docker,
                'use_github_actions': preset_config.use_github_actions
            })
        
        # Apply extra context
        if extra_context:
            context.update(extra_context)
        
        # Create project
        try:
            project_dir = cookiecutter(
                str(self.template_dir),
                no_input=True,
                extra_context=context,
                output_dir=output_dir
            )
            
            project_slug = self._slugify(project_name)
            project_path = Path(project_dir)
            
            # Initialize git if requested
            if git_init:
                subprocess.run(['git', 'init'], cwd=project_path, capture_output=True)
                subprocess.run(['git', 'add', '.'], cwd=project_path, capture_output=True)
                subprocess.run(['git', 'commit', '-m', 'Initial commit'], 
                             cwd=project_path, capture_output=True)
            
            # Create secrets.yaml if requested
            if create_secrets:
                self._create_secrets_yaml(project_name, project_slug, output_dir)
            
            return {
                'success': True,
                'project_dir': str(project_path),
                'project_slug': project_slug,
                'project_prefix': project_slug.upper().replace('-', '_'),
                'context': context,
                'next_steps': self._get_next_steps(project_slug, create_secrets)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_secrets_yaml(self, project_name: str, project_slug: str, output_dir: str):
        """Create a project-specific secrets.yaml file."""
        secrets_example = self.template_dir / 'secrets.example.yaml'
        if not secrets_example.exists():
            return
        
        output_path = Path(output_dir) / project_slug / 'secrets.yaml'
        project_prefix = project_slug.upper().replace('-', '_')
        
        # Read example and replace project name
        with open(secrets_example, 'r') as f:
            content = f.read()
        
        # Replace placeholders
        content = content.replace('YOUR_PROJECT_NAME', project_prefix)
        content = content.replace('your-repo-name', project_slug)
        
        # Write to project
        with open(output_path, 'w') as f:
            f.write(content)
    
    def _get_next_steps(self, project_slug: str, has_secrets: bool) -> List[str]:
        """Generate next steps based on project configuration."""
        steps = [
            f"cd {project_slug}",
            "cp .env.example .env",
            "Edit .env with your bot token and database URL",
            "pip install -r requirements.txt"
        ]
        
        if has_secrets:
            steps.insert(0, f"Edit {project_slug}/secrets.yaml with your values")
            steps.insert(1, "python scripts/setup_secrets.py")
        
        steps.append(f"python -m {project_slug.replace('-', '_')}.main")
        
        return steps
    
    def list_presets(self) -> Dict[str, Dict[str, Any]]:
        """Get all available presets."""
        return {name: asdict(preset) for name, preset in PRESETS.items()}
    
    def batch_create(self, projects: List[Dict[str, Any]], output_dir: str = ".") -> List[Dict[str, Any]]:
        """Create multiple bot projects at once."""
        results = []
        for project in projects:
            name = project.pop('name')
            result = self.create_bot(name, output_dir, **project)
            results.append(result)
        return results


def create_bot_simple(project_name: str, **kwargs) -> bool:
    """Simple function for Claude Code integration."""
    factory = BotFactory()
    result = factory.create_bot(project_name, **kwargs)
    
    if result['success']:
        print(f"✅ Created bot: {result['project_dir']}")
        print("\n📋 Next steps:")
        for i, step in enumerate(result['next_steps'], 1):
            print(f"{i}. {step}")
        return True
    else:
        print(f"❌ Error: {result['error']}")
        return False


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Bot Factory - Create Telegram bot projects with ease',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('project_name', nargs='?', help='Name of your bot project')
    parser.add_argument('--output', '-o', default='.', help='Output directory')
    parser.add_argument('--preset', '-p', choices=list(PRESETS.keys()),
                       help='Use a predefined preset')
    parser.add_argument('--list-presets', action='store_true',
                       help='List all available presets')
    parser.add_argument('--git-init', action='store_true', default=True,
                       help='Initialize git repository')
    parser.add_argument('--create-secrets', action='store_true',
                       help='Create secrets.yaml file')
    parser.add_argument('--json', action='store_true',
                       help='Output result as JSON (for automation)')
    
    args, extra_args = parser.parse_known_args()
    
    factory = BotFactory()
    
    if args.list_presets:
        print("Available presets:")
        for name, preset in factory.list_presets().items():
            print(f"\n{name}: {preset['description']}")
            print(f"  - OpenRouter: {preset['use_openrouter']}")
            print(f"  - Support Bot: {preset['use_support_bot']}")
            print(f"  - Docker: {preset['use_docker']}")
            print(f"  - GitHub Actions: {preset['use_github_actions']}")
        return
    
    if not args.project_name:
        parser.print_help()
        return
    
    # Parse extra arguments
    extra_context = {}
    for arg in extra_args:
        if '=' in arg:
            key, value = arg.split('=', 1)
            if value.lower() in ('true', 'yes', 'y'):
                value = 'y'
            elif value.lower() in ('false', 'no', 'n'):
                value = 'n'
            extra_context[key] = value
    
    # Create bot
    result = factory.create_bot(
        args.project_name,
        output_dir=args.output,
        preset=args.preset,
        extra_context=extra_context,
        git_init=args.git_init,
        create_secrets=args.create_secrets
    )
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result['success']:
            print(f"✅ Bot project created: {result['project_dir']}")
            print("\n📋 Next steps:")
            for i, step in enumerate(result['next_steps'], 1):
                print(f"{i}. {step}")
        else:
            print(f"❌ Error: {result['error']}")
            sys.exit(1)


if __name__ == '__main__':
    main()