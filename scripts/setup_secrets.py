#!/usr/bin/env python3
"""
GitHub Organization Secrets Setup from YAML Configuration
This script reads secrets from a YAML file and creates them in GitHub
"""

import base64
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install PyYAML")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("Error: requests is required. Install with: pip install requests")
    sys.exit(1)

try:
    from nacl import encoding, public
except ImportError:
    print("Error: PyNaCl is required. Install with: pip install PyNaCl")
    sys.exit(1)


class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color


def print_status(color: str, message: str) -> None:
    """Print colored output."""
    print(f"{color}{message}{Colors.NC}")


class SecretsManager:
    def __init__(self, config_file: str):
        self.config_file = Path(config_file)
        self.config = self.load_config()
        self.validate_config()
        
        # Set up GitHub API session
        self.token = self.config['github']['token']
        self.org_name = self.config['github']['organization']
        self.project_name = self.config['project']['name']
        self.repo_name = self.config['project'].get('repository')
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        })
        
        # Advanced settings
        self.update_existing = self.config.get('advanced', {}).get('update_existing', True)
        self.validate_values = self.config.get('advanced', {}).get('validate_values', True)
        self.dry_run = self.config.get('advanced', {}).get('dry_run', False)

    def load_config(self) -> Dict[str, Any]:
        """Load and parse YAML configuration file."""
        if not self.config_file.exists():
            print_status(Colors.RED, f"Error: Configuration file not found: {self.config_file}")
            print_status(Colors.YELLOW, "Create a secrets.yaml file from secrets.example.yaml")
            sys.exit(1)
        
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            print_status(Colors.RED, f"Error parsing YAML file: {e}")
            sys.exit(1)

    def validate_config(self) -> None:
        """Validate the configuration structure."""
        required_sections = ['github', 'project', 'secrets']
        for section in required_sections:
            if section not in self.config:
                print_status(Colors.RED, f"Error: Missing required section '{section}' in configuration")
                sys.exit(1)
        
        # Validate GitHub config
        if not self.config['github'].get('organization'):
            print_status(Colors.RED, "Error: GitHub organization not specified")
            sys.exit(1)
        
        if not self.config['github'].get('token'):
            print_status(Colors.RED, "Error: GitHub token not specified")
            sys.exit(1)
        
        # Validate project config
        if not self.config['project'].get('name'):
            print_status(Colors.RED, "Error: Project name not specified")
            sys.exit(1)

    def api_call(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> requests.Response:
        """Make authenticated API call to GitHub."""
        url = f"https://api.github.com{endpoint}"
        
        if data:
            response = self.session.request(method, url, json=data)
        else:
            response = self.session.request(method, url)
        
        return response

    def validate_github_access(self) -> None:
        """Validate GitHub token and organization access."""
        # Check token validity
        print_status(Colors.YELLOW, "Validating GitHub access...")
        
        try:
            response = self.api_call("GET", "/user")
            response.raise_for_status()
            user_info = response.json()
            username = user_info.get('login')
            print_status(Colors.GREEN, f"✓ Authenticated as: {username}")
        except requests.exceptions.RequestException:
            print_status(Colors.RED, "Error: Invalid GitHub token or network error")
            sys.exit(1)
        
        # Check organization access
        try:
            response = self.api_call("GET", f"/orgs/{self.org_name}")
            response.raise_for_status()
            print_status(Colors.GREEN, f"✓ Organization '{self.org_name}' is accessible")
        except requests.exceptions.RequestException:
            print_status(Colors.RED, f"Error: Cannot access organization '{self.org_name}'")
            sys.exit(1)

    def get_repository_id(self) -> Optional[int]:
        """Get repository ID if repository name is provided."""
        if not self.repo_name:
            return None
        
        try:
            response = self.api_call("GET", f"/repos/{self.org_name}/{self.repo_name}")
            response.raise_for_status()
            repo_id = response.json().get('id')
            print_status(Colors.GREEN, f"✓ Found repository: {self.repo_name} (ID: {repo_id})")
            return repo_id
        except requests.exceptions.RequestException:
            print_status(Colors.YELLOW, f"⚠ Repository '{self.repo_name}' not found (will be linked manually later)")
            return None

    def encrypt_secret(self, public_key: str, secret_value: str) -> str:
        """Encrypt secret value using GitHub's public key."""
        public_key_obj = public.PublicKey(public_key.encode('utf-8'), encoding.Base64Encoder())
        sealed_box = public.SealedBox(public_key_obj)
        encrypted = sealed_box.encrypt(secret_value.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')

    def validate_secret_value(self, name: str, value: str, description: str) -> bool:
        """Validate secret value based on its type."""
        if not self.validate_values:
            return True
        
        if not value:
            print_status(Colors.YELLOW, f"⚠ Warning: Empty value for {name}")
            return True  # Allow empty values for optional secrets
        
        # Basic validation based on secret name
        if 'TOKEN' in name and 'TELEGRAM' in name:
            if not value.startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9')) or ':' not in value:
                print_status(Colors.YELLOW, f"⚠ Warning: {name} doesn't look like a valid Telegram bot token")
        
        elif 'DATABASE_URL' in name:
            if not value.startswith(('postgresql://', 'postgres://')):
                print_status(Colors.YELLOW, f"⚠ Warning: {name} doesn't look like a PostgreSQL URL")
        
        elif 'SSH_KEY' in name:
            if 'BEGIN' not in value or 'END' not in value:
                print_status(Colors.YELLOW, f"⚠ Warning: {name} doesn't look like a valid SSH key")
        
        return True

    def create_secrets(self) -> None:
        """Create all secrets defined in the configuration."""
        print_status(Colors.BLUE, f"\n=== Setting up secrets for project: {self.project_name} ===")
        
        if self.dry_run:
            print_status(Colors.YELLOW, "DRY RUN MODE - No secrets will be created")
        
        # Get organization public key
        print_status(Colors.YELLOW, "Fetching organization public key...")
        try:
            response = self.api_call("GET", f"/orgs/{self.org_name}/actions/secrets/public-key")
            response.raise_for_status()
            public_key_data = response.json()
            key_id = public_key_data['key_id']
            public_key = public_key_data['key']
        except requests.exceptions.RequestException as e:
            print_status(Colors.RED, f"Error: Failed to fetch organization public key: {e}")
            return
        
        # Get repository ID if specified
        repo_id = self.get_repository_id()
        
        # Process each secret
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        for secret_name, secret_config in self.config['secrets'].items():
            # Extract configuration
            value = str(secret_config.get('value', ''))
            description = secret_config.get('description', '')
            visibility = secret_config.get('visibility', 'selected')
            prefix = secret_config.get('prefix', True)
            
            # Determine final secret name
            if prefix:
                final_name = f"{self.project_name}_{secret_name}"
            else:
                final_name = secret_name
            
            print(f"\n{Colors.CYAN}Processing: {final_name}{Colors.NC}")
            if description:
                print(f"  Description: {description}")
            
            # Validate value
            if not value:
                print_status(Colors.YELLOW, f"  ⚠ Skipping (no value provided)")
                skipped_count += 1
                continue
            
            # Validate secret value
            self.validate_secret_value(final_name, value, description)
            
            if self.dry_run:
                print_status(Colors.BLUE, f"  Would create: {final_name} (visibility: {visibility})")
                created_count += 1
                continue
            
            # Check if secret already exists
            if not self.update_existing:
                try:
                    response = self.api_call("GET", f"/orgs/{self.org_name}/actions/secrets/{final_name}")
                    if response.status_code == 200:
                        print_status(Colors.YELLOW, f"  ⚠ Secret already exists (skipping)")
                        skipped_count += 1
                        continue
                except:
                    pass
            
            # Encrypt the secret
            try:
                encrypted_value = self.encrypt_secret(public_key, value)
            except Exception as e:
                print_status(Colors.RED, f"  ✗ Failed to encrypt: {e}")
                error_count += 1
                continue
            
            # Prepare API payload
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
                response = self.api_call("PUT", f"/orgs/{self.org_name}/actions/secrets/{final_name}", payload)
                response.raise_for_status()
                print_status(Colors.GREEN, f"  ✓ Successfully created/updated")
                created_count += 1
            except requests.exceptions.RequestException as e:
                print_status(Colors.RED, f"  ✗ Failed to create: {e}")
                error_count += 1
        
        # Summary
        print_status(Colors.BLUE, f"\n=== Summary ===")
        print_status(Colors.GREEN, f"✓ Created/Updated: {created_count} secrets")
        if skipped_count > 0:
            print_status(Colors.YELLOW, f"⚠ Skipped: {skipped_count} secrets")
        if error_count > 0:
            print_status(Colors.RED, f"✗ Errors: {error_count} secrets")
        
        if created_count > 0 and visibility == 'selected' and not repo_id:
            print_status(Colors.YELLOW, "\n⚠ Note: Remember to add your repository to the secrets' access list in GitHub")

    def list_project_secrets(self) -> None:
        """List all secrets for the current project."""
        print_status(Colors.BLUE, f"\n=== Listing secrets for project: {self.project_name} ===")
        
        try:
            response = self.api_call("GET", f"/orgs/{self.org_name}/actions/secrets")
            response.raise_for_status()
            all_secrets = response.json().get('secrets', [])
            
            # Filter secrets for this project
            project_secrets = []
            shared_secrets = []
            
            for secret in all_secrets:
                if secret['name'].startswith(f"{self.project_name}_"):
                    project_secrets.append(secret)
                elif any(secret['name'] == s for s in self.config['secrets'] 
                        if not self.config['secrets'][s].get('prefix', True)):
                    shared_secrets.append(secret)
            
            if project_secrets:
                print_status(Colors.GREEN, f"\nProject-specific secrets ({len(project_secrets)}):")
                for secret in sorted(project_secrets, key=lambda x: x['name']):
                    print(f"  - {secret['name']} (visibility: {secret['visibility']})")
            else:
                print_status(Colors.YELLOW, "\nNo project-specific secrets found")
            
            if shared_secrets:
                print_status(Colors.GREEN, f"\nShared secrets ({len(shared_secrets)}):")
                for secret in sorted(shared_secrets, key=lambda x: x['name']):
                    print(f"  - {secret['name']} (visibility: {secret['visibility']})")
        
        except requests.exceptions.RequestException as e:
            print_status(Colors.RED, f"Error: Failed to list secrets: {e}")

    def run(self) -> None:
        """Main execution flow."""
        # Validate access
        self.validate_github_access()
        
        # Create secrets
        self.create_secrets()
        
        # List secrets
        if not self.dry_run:
            self.list_project_secrets()


def main():
    """Main entry point."""
    # Check for config file argument
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        # Look for secrets.yaml in current directory or parent
        for path in ['secrets.yaml', '../secrets.yaml']:
            if Path(path).exists():
                config_file = path
                break
        else:
            print_status(Colors.RED, "Error: No secrets.yaml file found")
            print_status(Colors.YELLOW, "Usage: python setup_secrets.py [secrets.yaml]")
            print_status(Colors.YELLOW, "Create a secrets.yaml file from secrets.example.yaml template")
            sys.exit(1)
    
    try:
        manager = SecretsManager(config_file)
        manager.run()
    except KeyboardInterrupt:
        print_status(Colors.YELLOW, "\n⚠ Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print_status(Colors.RED, f"\n✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()