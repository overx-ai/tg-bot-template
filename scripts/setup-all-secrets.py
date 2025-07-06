#!/usr/bin/env python3
"""
Quick setup script for all organization secrets needed by the Telegram bot template.
This script helps you set up all required secrets in one go.
"""

import os
import sys
import subprocess
from pathlib import Path


class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def print_status(color: str, message: str) -> None:
    """Print colored output."""
    print(f"{color}{message}{Colors.NC}")


def main():
    """Main setup function."""
    print_status(Colors.GREEN, "=== Telegram Bot Template - Organization Secrets Setup ===")
    print()
    print("This script will help you set up all required GitHub organization secrets")
    print("for deploying Telegram bots created with this template.")
    print()
    
    # Check if we're in the right directory
    if not Path("cookiecutter.json").exists():
        print_status(Colors.RED, "Error: cookiecutter.json not found. Please run this script from the template root directory.")
        sys.exit(1)
    
    # Check dependencies
    try:
        import nacl
        import yaml
    except ImportError:
        print_status(Colors.YELLOW, "Installing required dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "scripts/requirements-secrets.txt"], check=True)
    
    print_status(Colors.GREEN, "Required Organization Secrets:")
    print("1. TELEGRAM_BOT_TOKEN - Your Telegram bot token")
    print("2. DATABASE_URL - PostgreSQL connection string")
    print("3. DEPLOY_SSH_KEY - SSH private key for server deployment")
    print("4. SERVER_HOST - Deployment server hostname")
    print("5. SERVER_USER - Deployment server username")
    print()
    print_status(Colors.GREEN, "Optional Organization Secrets:")
    print("6. OPENROUTER_API_KEY - For AI functionality")
    print("7. SUPPORT_BOT_TOKEN - For support bot feature")
    print("8. SUPPORT_CHAT_ID - Admin chat ID for support")
    print("9. SLACK_WEBHOOK - For deployment notifications")
    print("10. DISCORD_WEBHOOK - For deployment notifications")
    print()
    
    # Ask if user wants to use project-specific secrets
    use_project = input("Do you want to use project-specific secrets (recommended)? (Y/n): ").strip().lower()
    
    if use_project != 'n':
        # Use project-based secrets manager
        print()
        print_status(Colors.BLUE, "Using project-based secrets manager...")
        print("This will prefix secrets with your project name to avoid conflicts.")
        print()
        
        # Set environment variables if not already set
        if not os.getenv('PROJECT_NAME'):
            project_name = input("Enter your project name (e.g., 'mybot-prod'): ").strip().upper()
            if project_name:
                os.environ['PROJECT_NAME'] = project_name
        
        if not os.getenv('GITHUB_ORG'):
            org_name = input("Enter your GitHub organization name: ").strip()
            if org_name:
                os.environ['GITHUB_ORG'] = org_name
        
        # Run the project secrets manager
        subprocess.run([sys.executable, "scripts/manage-project-secrets.py"])
    else:
        # Use organization-wide secrets manager
        print()
        print_status(Colors.BLUE, "Using organization-wide secrets manager...")
        print("WARNING: This will create secrets without project prefixes.")
        print("Multiple projects may conflict if using the same secrets.")
        print()
        
        confirm = input("Are you sure you want to continue? (y/N): ").strip().lower()
        if confirm == 'y':
            subprocess.run([sys.executable, "scripts/manage-org-secrets.py"])
    
    print()
    print_status(Colors.GREEN, "=== Setup Complete ===")
    print()
    print_status(Colors.GREEN, "Next Steps:")
    print("1. Create a new project: cookiecutter /path/to/this/template")
    print("2. Push to GitHub")
    print("3. If using 'selected' visibility, add repository to secret access list")
    print("4. Push to main branch to trigger deployment")
    print()
    print_status(Colors.BLUE, "Tips:")
    print("- Use 'selected' visibility for production secrets")
    print("- Use 'all' visibility for development secrets")
    print("- Remember to rotate secrets every 90 days")
    print("- Check scripts/SECRETS_README.md for detailed documentation")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_status(Colors.YELLOW, "\nSetup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print_status(Colors.RED, f"\nError: {e}")
        sys.exit(1)