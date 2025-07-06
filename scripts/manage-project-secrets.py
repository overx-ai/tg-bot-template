#!/usr/bin/env python3
"""
GitHub Organization Secrets Management with Project Prefixing
This script manages GitHub organization secrets with project-based prefixing
to prevent conflicts between multiple projects using the same template
"""

import os
import sys
import json
import yaml
import base64
import getpass
import requests
from typing import Optional, List, Dict, Any
from pathlib import Path

try:
    from nacl import encoding, public
except ImportError:
    print("Error: PyNaCl is required. Install with: pip install PyNaCl")
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install PyYAML")
    sys.exit(1)


class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def print_status(color: str, message: str) -> None:
    """Print colored output."""
    print(f"{color}{message}{Colors.NC}")


class ProjectSecretsManager:
    def __init__(self):
        self.config = self.load_config()
        self.project_name = self.get_project_name()
        self.token = self.get_github_token()
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        })
        self.validate_token()
        self.org_name = self.get_organization_name()
        self.validate_org_access()
    
    def load_config(self) -> Dict[str, Any]:
        """Load secrets configuration from YAML file."""
        config_path = Path(__file__).parent.parent / '.github' / 'workflows' / 'secrets-config.yml'
        if not config_path.exists():
            print_status(Colors.RED, f"Error: Configuration file not found at {config_path}")
            sys.exit(1)
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def get_project_name(self) -> str:
        """Get project name from environment variable or user input."""
        project_name = os.getenv('PROJECT_NAME')
        if not project_name:
            print_status(Colors.BLUE, "Project name not found in environment.")
            project_name = input("Enter project name (e.g., 'mybot-prod'): ").strip().upper()
            if not project_name:
                print_status(Colors.RED, "Error: Project name cannot be empty")
                sys.exit(1)
        
        # Validate project name (alphanumeric and hyphens only)
        if not all(c.isalnum() or c in '-_' for c in project_name):
            print_status(Colors.RED, "Error: Project name can only contain letters, numbers, hyphens, and underscores")
            sys.exit(1)
        
        return project_name
    
    def get_prefixed_secret_name(self, base_name: str, is_prefixed: bool = True) -> str:
        """Get the full secret name with project prefix if required."""
        if not is_prefixed:
            return base_name
        
        separator = self.config.get('project_config', {}).get('separator', '_')
        return f"{self.project_name}{separator}{base_name}"
    
    def get_github_token(self) -> str:
        """Get GitHub token from environment or user input."""
        token = os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN')
        if not token:
            token = getpass.getpass("Enter your GitHub Personal Access Token: ")
        
        if not token:
            print_status(Colors.RED, "Error: GitHub token cannot be empty")
            sys.exit(1)
        
        return token
    
    def api_call(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> requests.Response:
        """Make authenticated API call."""
        url = f"https://api.github.com{endpoint}"
        
        if data:
            response = self.session.request(method, url, json=data)
        else:
            response = self.session.request(method, url)
        
        return response
    
    def validate_token(self) -> None:
        """Check if token is valid and has required permissions."""
        try:
            response = self.api_call("GET", "/user")
            response.raise_for_status()
            user_info = response.json()
            username = user_info.get('login')
            print_status(Colors.GREEN, f"✓ Authenticated as: {username}")
        except requests.exceptions.RequestException:
            print_status(Colors.RED, "Error: Invalid GitHub token or insufficient permissions")
            sys.exit(1)
    
    def get_organization_name(self) -> str:
        """Get organization name from user input."""
        org_name = os.getenv('GITHUB_ORG')
        if not org_name:
            org_name = input("Enter GitHub organization name: ").strip()
        if not org_name:
            print_status(Colors.RED, "Error: Organization name cannot be empty")
            sys.exit(1)
        return org_name
    
    def validate_org_access(self) -> None:
        """Validate organization access."""
        try:
            response = self.api_call("GET", f"/orgs/{self.org_name}")
            response.raise_for_status()
            print_status(Colors.GREEN, f"✓ Organization '{self.org_name}' is accessible")
        except requests.exceptions.RequestException:
            print_status(Colors.RED, f"Error: Cannot access organization '{self.org_name}'")
            print("Make sure you have the necessary permissions.")
            sys.exit(1)
    
    def encrypt_secret(self, public_key: str, secret_value: str) -> str:
        """Encrypt secret using sodium."""
        public_key_obj = public.PublicKey(public_key.encode('utf-8'), encoding.Base64Encoder())
        sealed_box = public.SealedBox(public_key_obj)
        encrypted = sealed_box.encrypt(secret_value.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')
    
    def create_project_secrets(self) -> None:
        """Create all required secrets for the project based on configuration."""
        print_status(Colors.BLUE, f"\n=== Creating secrets for project: {self.project_name} ===")
        
        secrets_config = self.config.get('organization_secrets', {}).get('required_secrets', [])
        if not secrets_config:
            print_status(Colors.YELLOW, "No secrets defined in configuration")
            return
        
        # Get organization public key
        print_status(Colors.YELLOW, "Fetching organization public key...")
        try:
            response = self.api_call("GET", f"/orgs/{self.org_name}/actions/secrets/public-key")
            response.raise_for_status()
            public_key_data = response.json()
            key_id = public_key_data['key_id']
            public_key = public_key_data['key']
        except requests.exceptions.RequestException:
            print_status(Colors.RED, "Error: Failed to fetch organization public key")
            return
        
        # Get repository name for selected visibility
        repo_name = None
        repo_id = None
        if any(s.get('visibility') == 'selected' for s in secrets_config):
            repo_name = input(f"Enter repository name for project '{self.project_name}': ").strip()
            if repo_name:
                try:
                    response = self.api_call("GET", f"/repos/{self.org_name}/{repo_name}")
                    response.raise_for_status()
                    repo_id = response.json().get('id')
                except requests.exceptions.RequestException:
                    print_status(Colors.YELLOW, f"Warning: Repository '{repo_name}' not found")
        
        # Process each secret
        created_secrets = []
        for secret_config in secrets_config:
            base_name = secret_config['name']
            is_prefixed = secret_config.get('prefixed', True)
            secret_name = self.get_prefixed_secret_name(base_name, is_prefixed)
            
            print(f"\nConfiguring secret: {Colors.BLUE}{secret_name}{Colors.NC}")
            print(f"Description: {secret_config.get('description', 'No description')}")
            
            # Get secret value
            secret_value = getpass.getpass(f"Enter value for '{secret_name}' (or press Enter to skip): ")
            if not secret_value:
                print_status(Colors.YELLOW, f"Skipping '{secret_name}'")
                continue
            
            # Encrypt the secret
            try:
                encrypted_value = self.encrypt_secret(public_key, secret_value)
            except Exception as e:
                print_status(Colors.RED, f"Error: Failed to encrypt secret: {e}")
                continue
            
            # Prepare API payload
            visibility = secret_config.get('visibility', 'selected')
            payload = {
                'encrypted_value': encrypted_value,
                'key_id': key_id,
                'visibility': visibility
            }
            
            # Add repository ID for selected visibility
            if visibility == 'selected' and repo_id:
                payload['selected_repository_ids'] = [repo_id]
            
            # Create or update the secret
            try:
                response = self.api_call("PUT", f"/orgs/{self.org_name}/actions/secrets/{secret_name}", payload)
                response.raise_for_status()
                print_status(Colors.GREEN, f"✓ Secret '{secret_name}' successfully created/updated")
                created_secrets.append(secret_name)
            except requests.exceptions.RequestException as e:
                print_status(Colors.RED, f"Error: Failed to create/update secret '{secret_name}': {e}")
            
            # Clear sensitive variable
            del secret_value
            del encrypted_value
        
        # Summary
        if created_secrets:
            print_status(Colors.GREEN, f"\n✓ Successfully created/updated {len(created_secrets)} secrets for project '{self.project_name}':")
            for secret in created_secrets:
                print(f"  - {secret}")
    
    def list_project_secrets(self) -> None:
        """List all secrets for the current project."""
        print_status(Colors.BLUE, f"\n=== Listing secrets for project: {self.project_name} ===")
        
        try:
            response = self.api_call("GET", f"/orgs/{self.org_name}/actions/secrets")
            response.raise_for_status()
            all_secrets = response.json().get('secrets', [])
            
            # Filter secrets for this project
            separator = self.config.get('project_config', {}).get('separator', '_')
            prefix = f"{self.project_name}{separator}"
            project_secrets = [s for s in all_secrets if s['name'].startswith(prefix)]
            
            # Also include non-prefixed secrets
            non_prefixed_names = [
                s['name'] for s in self.config.get('organization_secrets', {}).get('required_secrets', [])
                if not s.get('prefixed', True)
            ]
            shared_secrets = [s for s in all_secrets if s['name'] in non_prefixed_names]
            
            if project_secrets:
                print_status(Colors.GREEN, f"\nProject-specific secrets ({len(project_secrets)}):")
                for secret in project_secrets:
                    print(f"  - {secret['name']} (visibility: {secret['visibility']})")
            else:
                print_status(Colors.YELLOW, "No project-specific secrets found")
            
            if shared_secrets:
                print_status(Colors.GREEN, f"\nShared secrets ({len(shared_secrets)}):")
                for secret in shared_secrets:
                    print(f"  - {secret['name']} (visibility: {secret['visibility']})")
            
        except requests.exceptions.RequestException:
            print_status(Colors.RED, "Error: Failed to list organization secrets")
    
    def delete_project_secrets(self) -> None:
        """Delete all secrets for the current project."""
        print_status(Colors.YELLOW, f"\n=== Deleting secrets for project: {self.project_name} ===")
        
        confirm = input(f"Are you sure you want to delete ALL secrets for project '{self.project_name}'? (yes/N): ").strip().lower()
        if confirm != 'yes':
            print_status(Colors.YELLOW, "Deletion cancelled")
            return
        
        try:
            response = self.api_call("GET", f"/orgs/{self.org_name}/actions/secrets")
            response.raise_for_status()
            all_secrets = response.json().get('secrets', [])
            
            # Filter secrets for this project
            separator = self.config.get('project_config', {}).get('separator', '_')
            prefix = f"{self.project_name}{separator}"
            project_secrets = [s for s in all_secrets if s['name'].startswith(prefix)]
            
            if not project_secrets:
                print_status(Colors.YELLOW, "No project-specific secrets found to delete")
                return
            
            deleted_count = 0
            for secret in project_secrets:
                try:
                    response = self.api_call("DELETE", f"/orgs/{self.org_name}/actions/secrets/{secret['name']}")
                    response.raise_for_status()
                    print_status(Colors.GREEN, f"✓ Deleted: {secret['name']}")
                    deleted_count += 1
                except requests.exceptions.RequestException:
                    print_status(Colors.RED, f"✗ Failed to delete: {secret['name']}")
            
            print_status(Colors.GREEN, f"\n✓ Successfully deleted {deleted_count} secrets")
            
        except requests.exceptions.RequestException:
            print_status(Colors.RED, "Error: Failed to list/delete organization secrets")
    
    def show_menu(self) -> None:
        """Display main menu."""
        print()
        print_status(Colors.GREEN, "Project-based Secrets Manager")
        print("=" * 40)
        print(f"Organization: {Colors.BLUE}{self.org_name}{Colors.NC}")
        print(f"Project: {Colors.BLUE}{self.project_name}{Colors.NC}")
        print("=" * 40)
        print("1. Create/Update all project secrets")
        print("2. List project secrets")
        print("3. Delete all project secrets")
        print("4. Change project")
        print("5. Exit")
        print()
    
    def run(self) -> None:
        """Main program loop."""
        while True:
            self.show_menu()
            choice = input("Select an option (1-5): ").strip()
            
            if choice == '1':
                self.create_project_secrets()
            elif choice == '2':
                self.list_project_secrets()
            elif choice == '3':
                self.delete_project_secrets()
            elif choice == '4':
                self.project_name = self.get_project_name()
            elif choice == '5':
                print_status(Colors.GREEN, "Goodbye!")
                break
            else:
                print_status(Colors.RED, "Invalid option. Please try again.")


def main():
    """Main entry point."""
    try:
        manager = ProjectSecretsManager()
        manager.run()
    except KeyboardInterrupt:
        print_status(Colors.YELLOW, "\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print_status(Colors.RED, f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()