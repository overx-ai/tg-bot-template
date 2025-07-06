#!/usr/bin/env python3
"""
GitHub Organization Secrets Management Script
This script manages GitHub organization secrets securely using direct API calls
Secrets are never stored in files or exposed in logs
"""

import os
import sys
import json
import base64
import getpass
import requests
from typing import Optional, List, Dict, Any

try:
    from nacl import encoding, public
except ImportError:
    print("Error: PyNaCl is required. Install with: pip install PyNaCl")
    sys.exit(1)


class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color


def print_status(color: str, message: str) -> None:
    """Print colored output."""
    print(f"{color}{message}{Colors.NC}")


class GitHubSecretsManager:
    def __init__(self):
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
    
    def create_org_secret(self) -> None:
        """Create or update organization secret."""
        secret_name = input("Enter secret name (UPPERCASE recommended): ").strip()
        if not secret_name:
            print_status(Colors.RED, "Error: Secret name cannot be empty")
            return
        
        print("Select visibility:")
        print("1. all - All repositories in the organization")
        print("2. private - Private repositories only")
        print("3. selected - Selected repositories")
        vis_choice = input("Enter choice (1-3): ").strip()
        
        visibility_map = {
            '1': 'all',
            '2': 'private',
            '3': 'selected'
        }
        
        if vis_choice not in visibility_map:
            print_status(Colors.RED, "Invalid choice")
            return
        
        visibility = visibility_map[vis_choice]
        
        secret_value = getpass.getpass(f"Enter value for secret '{secret_name}' (input hidden): ")
        if not secret_value:
            print_status(Colors.RED, "Error: Secret value cannot be empty")
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
        
        # Encrypt the secret
        print_status(Colors.YELLOW, "Encrypting secret...")
        try:
            encrypted_value = self.encrypt_secret(public_key, secret_value)
        except Exception as e:
            print_status(Colors.RED, f"Error: Failed to encrypt secret: {e}")
            return
        
        # Prepare API payload
        payload = {
            'encrypted_value': encrypted_value,
            'key_id': key_id,
            'visibility': visibility
        }
        
        # Handle selected repositories
        if visibility == 'selected':
            repo_names = input("Enter repository names (comma-separated) that should have access to this secret: ").strip()
            if repo_names:
                repo_ids = []
                for repo in [r.strip() for r in repo_names.split(',')]:
                    try:
                        response = self.api_call("GET", f"/repos/{self.org_name}/{repo}")
                        response.raise_for_status()
                        repo_id = response.json().get('id')
                        if repo_id:
                            repo_ids.append(repo_id)
                    except requests.exceptions.RequestException:
                        print_status(Colors.YELLOW, f"Warning: Repository '{repo}' not found or inaccessible")
                
                if repo_ids:
                    payload['selected_repository_ids'] = repo_ids
        
        # Create or update the secret
        print_status(Colors.YELLOW, f"Creating/updating organization secret '{secret_name}'...")
        try:
            response = self.api_call("PUT", f"/orgs/{self.org_name}/actions/secrets/{secret_name}", payload)
            response.raise_for_status()
            print_status(Colors.GREEN, f"✓ Secret '{secret_name}' successfully created/updated")
        except requests.exceptions.RequestException as e:
            print_status(Colors.RED, f"Error: Failed to create/update secret: {e}")
        
        # Clear sensitive variables
        del secret_value
        del encrypted_value
    
    def list_org_secrets(self) -> None:
        """List organization secrets."""
        print_status(Colors.YELLOW, f"Fetching organization secrets for '{self.org_name}'...")
        
        try:
            response = self.api_call("GET", f"/orgs/{self.org_name}/actions/secrets")
            response.raise_for_status()
            secrets_data = response.json()
            secrets = secrets_data.get('secrets', [])
            
            if not secrets:
                print_status(Colors.YELLOW, f"No secrets found for organization '{self.org_name}'")
            else:
                print_status(Colors.GREEN, "Organization secrets:")
                for secret in secrets:
                    print(f"{secret['name']} - Visibility: {secret['visibility']}")
        except requests.exceptions.RequestException:
            print_status(Colors.RED, "Error: Failed to list organization secrets")
    
    def delete_org_secret(self) -> None:
        """Delete organization secret."""
        secret_name = input("Enter secret name to delete: ").strip()
        if not secret_name:
            print_status(Colors.RED, "Error: Secret name cannot be empty")
            return
        
        confirm = input(f"Are you sure you want to delete '{secret_name}'? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print_status(Colors.YELLOW, "Deletion cancelled")
            return
        
        print_status(Colors.YELLOW, f"Deleting organization secret '{secret_name}'...")
        
        try:
            response = self.api_call("DELETE", f"/orgs/{self.org_name}/actions/secrets/{secret_name}")
            response.raise_for_status()
            print_status(Colors.GREEN, f"✓ Secret '{secret_name}' successfully deleted")
        except requests.exceptions.RequestException:
            print_status(Colors.RED, f"Error: Failed to delete secret '{secret_name}'")
    
    def show_menu(self) -> None:
        """Display main menu."""
        print()
        print_status(Colors.GREEN, "GitHub Organization Secrets Manager")
        print("====================================")
        print("1. Create/Update organization secret")
        print("2. List organization secrets")
        print("3. Delete organization secret")
        print("4. Exit")
        print()
    
    def run(self) -> None:
        """Main program loop."""
        print_status(Colors.GREEN, f"✓ Successfully connected to organization '{self.org_name}'")
        
        while True:
            self.show_menu()
            choice = input("Select an option (1-4): ").strip()
            
            if choice == '1':
                self.create_org_secret()
            elif choice == '2':
                self.list_org_secrets()
            elif choice == '3':
                self.delete_org_secret()
            elif choice == '4':
                print_status(Colors.GREEN, "Goodbye!")
                break
            else:
                print_status(Colors.RED, "Invalid option. Please try again.")


def main():
    """Main entry point."""
    try:
        manager = GitHubSecretsManager()
        manager.run()
    except KeyboardInterrupt:
        print_status(Colors.YELLOW, "\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print_status(Colors.RED, f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()