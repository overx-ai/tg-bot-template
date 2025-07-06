# 🔐 Organization Secrets Setup Guide

This guide explains how to set up GitHub organization secrets for deploying bots created with this template.

## 📋 Overview

The template uses a YAML-based configuration system for managing GitHub organization secrets. You define all your secrets in a single `secrets.yaml` file, and the setup script automatically creates them in GitHub.

## 🚀 Quick Start

1. **Copy the example configuration:**
   ```bash
   cp secrets.example.yaml secrets.yaml
   ```

2. **Edit `secrets.yaml` with your values:**
   ```bash
   nano secrets.yaml  # or your favorite editor
   ```

3. **Run the setup script:**
   ```bash
   python scripts/setup_secrets.py
   ```

That's it! Your secrets are now configured in GitHub.

## 📝 Configuration File Structure

The `secrets.yaml` file has four main sections:

### 1. GitHub Configuration
```yaml
github:
  organization: "your-org-name"
  token: "ghp_your_token_here"
```

- **organization**: Your GitHub organization name
- **token**: Personal access token with `admin:org` scope
  - Create at: https://github.com/settings/tokens
  - Required scopes: `admin:org` and `repo`

### 2. Project Configuration
```yaml
project:
  name: "WEATHER_BOT"  # Used as prefix for secrets
  repository: "weather-bot"  # Optional, for auto-linking
```

- **name**: Project identifier (UPPERCASE with underscores)
- **repository**: Repository name (optional, for automatic linking)

### 3. Secrets Definition
```yaml
secrets:
  TELEGRAM_BOT_TOKEN:
    value: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
    description: "Telegram Bot API token"
    visibility: "selected"
    prefix: true
```

Each secret can have:
- **value**: The secret value (required)
- **description**: Human-readable description
- **visibility**: `all`, `private`, or `selected` (default: `selected`)
- **prefix**: Whether to prefix with project name (default: `true`)

### 4. Advanced Options
```yaml
advanced:
  update_existing: true    # Update existing secrets
  validate_values: true    # Validate secret formats
  dry_run: false          # Test without creating
```

## 🔑 Required Secrets

### Core Bot Configuration

1. **TELEGRAM_BOT_TOKEN**
   - Get from [@BotFather](https://t.me/botfather)
   - Format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

2. **DATABASE_URL**
   - PostgreSQL connection string
   - Format: `postgresql://user:pass@host:5432/dbname`

### Deployment Configuration

3. **DEPLOY_SSH_KEY**
   - SSH private key for server access
   - Generate: `ssh-keygen -t ed25519 -C "deploy@example.com"`
   - Add public key to server's `~/.ssh/authorized_keys`

4. **SERVER_HOST**
   - Server IP or hostname
   - Example: `192.168.1.100` or `bot.example.com`

5. **SERVER_USER**
   - Username on deployment server
   - Example: `ubuntu`, `deploy`, `bot`

### Optional Secrets

6. **OPENROUTER_API_KEY**
   - For AI features (if enabled)
   - Get from [OpenRouter.ai](https://openrouter.ai)

7. **SUPPORT_BOT_TOKEN**
   - For support bot feature
   - Another token from @BotFather

8. **SUPPORT_CHAT_ID**
   - Admin chat ID for support
   - Get from [@userinfobot](https://t.me/userinfobot)

## 📋 Complete Example

Here's a complete `secrets.yaml` example:

```yaml
github:
  organization: "acme-corp"
  token: "ghp_1234567890abcdef"

project:
  name: "WEATHER_BOT"
  repository: "weather-bot"

secrets:
  # Bot credentials
  TELEGRAM_BOT_TOKEN:
    value: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
    visibility: "selected"
    prefix: true

  DATABASE_URL:
    value: "postgresql://bot:password@db.example.com:5432/weather_bot"
    visibility: "selected"
    prefix: true

  # Deployment (shared across projects)
  DEPLOY_SSH_KEY:
    value: |
      -----BEGIN OPENSSH PRIVATE KEY-----
      b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAA...
      -----END OPENSSH PRIVATE KEY-----
    visibility: "selected"
    prefix: false

  SERVER_HOST:
    value: "bot.example.com"
    visibility: "selected"
    prefix: false

  SERVER_USER:
    value: "deploy"
    visibility: "selected"
    prefix: false

advanced:
  dry_run: false  # Set to true to test without creating
```

## 🎯 Usage Patterns

### Test Run (Dry Run)
```yaml
advanced:
  dry_run: true  # Shows what would be created without actually creating
```

### Multiple Projects
Create separate YAML files for each project:
```bash
python scripts/setup_secrets.py weather-bot-secrets.yaml
python scripts/setup_secrets.py todo-bot-secrets.yaml
```

### Shared vs Project-Specific Secrets
- Set `prefix: false` for secrets shared across projects (e.g., deployment keys)
- Set `prefix: true` for project-specific secrets (e.g., bot tokens)

## 🔍 Verifying Your Setup

The script automatically lists all created secrets. You can also check manually:

1. Go to GitHub → Your Organization → Settings → Secrets and variables → Actions
2. You should see your secrets listed with the correct visibility

## 🚨 Security Best Practices

1. **Never commit `secrets.yaml`** - It's already in `.gitignore`
2. **Use strong values**:
   - Long, random database passwords
   - ED25519 SSH keys (more secure than RSA)
3. **Limit visibility**:
   - Use `selected` visibility when possible
   - Only give access to repositories that need it
4. **Rotate regularly**:
   - Change secrets every 90 days
   - Update both GitHub and your servers

## 🆘 Troubleshooting

### "Invalid GitHub token"
- Ensure token has `admin:org` scope
- Check token hasn't expired

### "Organization not found"
- Verify organization name spelling
- Ensure you have admin access to the organization

### "Secret not available in workflow"
- For `selected` visibility, add repository to secret's access list
- Check secret name matches exactly (including prefix)

### "Failed to encrypt secret"
- Install PyNaCl: `pip install PyNaCl`
- Ensure you have internet connection

## 📚 Next Steps

1. Create your bot with cookiecutter:
   ```bash
   cookiecutter https://github.com/yourusername/tg-bot-template.git
   ```

2. Push to GitHub:
   ```bash
   cd your-bot-name
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourorg/your-bot-name.git
   git push -u origin main
   ```

3. Deployment will trigger automatically!

## 🔗 Additional Resources

- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Template Quick Start Guide](QUICKSTART.md)
- [Deployment Documentation]({{ cookiecutter.project_slug }}/deployment/README.md)