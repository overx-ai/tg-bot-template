#!/usr/bin/env python3
"""
Post-generation hook for cookiecutter.
This script runs after the project is generated to:
1. Copy GitHub workflow templates if enabled
2. Remove unused files based on configuration
3. Initialize git repository if requested
"""

import os
import shutil
from pathlib import Path


def remove_file(filepath):
    """Remove a file if it exists."""
    path = Path(filepath)
    if path.exists():
        path.unlink()
        print(f"Removed: {filepath}")


def remove_directory(dirpath):
    """Remove a directory if it exists."""
    path = Path(dirpath)
    if path.exists():
        shutil.rmtree(path)
        print(f"Removed directory: {dirpath}")


def make_scripts_executable():
    """Make deployment scripts executable."""
    scripts = [
        "deployment/deploy.sh",
        "deployment/setup.sh"
    ]
    
    for script in scripts:
        if Path(script).exists():
            os.chmod(script, 0o755)
            print(f"Made executable: {script}")


def main():
    """Main post-generation tasks."""
    print("\n🚀 Running post-generation tasks...")
    
    # Remove Docker files if not using Docker
    if "{{ cookiecutter.use_docker }}" != "y":
        remove_file("Dockerfile")
        remove_file("docker-compose.yml")
    
    # Make scripts executable
    make_scripts_executable()
    
    # Remove support bot module if not used
    if "{{ cookiecutter.use_support_bot }}" != "y":
        remove_directory("src/support")
    
    # Initialize git repository
    if "{{ cookiecutter.use_github_actions }}" == "y":
        print("\n📝 Initializing git repository...")
        os.system("git init")
        os.system("git add .")
        os.system('git commit -m "Initial commit from telegram-bot-template"')
        print("✅ Git repository initialized")
    
    print("\n✨ Project '{{ cookiecutter.project_name }}' created successfully!")
    print("\n📖 Next steps:")
    print("1. cd {{ cookiecutter.project_slug }}")
    print("2. cp .env.example .env")
    print("3. Edit .env with your configuration")
    print("4. createdb {{ cookiecutter.database_name }}")
    print("5. pip install -r requirements.txt")
    print("6. {{ cookiecutter.project_slug }} migrate")
    print("7. python -m main  # or {{ cookiecutter.project_slug }}")
    
    if "{{ cookiecutter.use_github_actions }}" == "y":
        print("\n🔐 Don't forget to set up GitHub organization secrets!")
        print("   Run: python scripts/setup-all-secrets.py")


if __name__ == "__main__":
    main()