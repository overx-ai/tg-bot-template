# GitHub Organization Secrets Management

This directory contains tools for securely managing GitHub organization-level secrets.

## Prerequisites

1. **GitHub CLI**: Install from https://cli.github.com/
2. **Python 3**: Required for secret encryption
3. **PyNaCl**: Install with `pip install -r requirements-secrets.txt`
4. **Organization Admin Access**: You must have admin permissions in the GitHub organization

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements-secrets.txt
   ```

2. Authenticate with GitHub:
   ```bash
   gh auth login
   ```

3. Ensure you have organization admin permissions

## Usage

Run the script:
```bash
./manage-org-secrets.sh
```

The script provides an interactive menu to:
- Create/update organization secrets
- List existing secrets (names only, values are never shown)
- Delete secrets
- Set visibility (all repos, private repos only, or selected repos)

## Security Features

- **No Storage**: Secrets are never written to disk
- **Encrypted Transmission**: All secrets are encrypted using GitHub's public key
- **Hidden Input**: Secret values are entered with hidden input
- **Memory Cleanup**: Sensitive variables are cleared after use
- **Access Control**: Supports repository-level access restrictions

## Visibility Options

1. **all**: Secret is available to all repositories in the organization
2. **private**: Secret is available only to private repositories
3. **selected**: Secret is available only to specifically selected repositories

## Important Security Notes

- Never commit actual secret values to Git
- Always use organization secrets for sensitive data
- Rotate secrets regularly (recommended: every 90 days)
- Limit secret access to only necessary repositories
- Use branch protection rules to prevent unauthorized changes

## GitHub Actions Usage

In your workflows, access organization secrets like this:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Use organization secret
        env:
          BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
        run: echo "Secret is available"
```

## Troubleshooting

1. **"Not authenticated"**: Run `gh auth login`
2. **"Cannot access organization"**: Ensure you have admin permissions
3. **"Failed to encrypt"**: Install PyNaCl: `pip install PyNaCl`
4. **"Secret not available in workflow"**: Check repository access settings