# Secrets Architecture

This document explains how secrets are managed in the Telegram Bot Template.

## Overview

The template uses a YAML-based configuration system with automatic project prefixing to manage GitHub organization secrets.

## How It Works

### 1. Secret Definition (secrets.yaml)

```yaml
project:
  name: "WEATHER_BOT"  # This becomes the prefix

secrets:
  TELEGRAM_BOT_TOKEN:
    value: "123456:ABC..."
    prefix: true         # Creates: WEATHER_BOT_TELEGRAM_BOT_TOKEN
  
  DEPLOY_SSH_KEY:
    value: "ssh-key..."
    prefix: false        # Creates: DEPLOY_SSH_KEY (shared)
```

### 2. GitHub Actions Integration

The workflow automatically uses the correct prefixed secrets:

```yaml
env:
  # Shared secrets (no prefix)
  DEPLOY_KEY: ${{ secrets.DEPLOY_SSH_KEY }}
  
  # Project-specific secrets (with prefix)
  BOT_TOKEN: ${{ secrets.WEATHER_BOT_TELEGRAM_BOT_TOKEN }}
```

### 3. Local Development (.env)

For local development, use unprefixed names in .env:

```env
TELEGRAM_BOT_TOKEN=123456:ABC...
DATABASE_URL=postgresql://...
```

## Cookiecutter Variables

The template automatically generates a `project_prefix` variable:

```json
{
  "project_slug": "weather-bot",
  "project_prefix": "WEATHER_BOT"  // Auto-generated from slug
}
```

This prefix is used in:
- GitHub Actions workflows
- Documentation
- Deployment scripts

## Multiple Projects

Each project gets its own prefixed secrets:

- `WEATHER_BOT_TELEGRAM_BOT_TOKEN`
- `TODO_BOT_TELEGRAM_BOT_TOKEN`
- `SHOP_BOT_TELEGRAM_BOT_TOKEN`

But they can share deployment infrastructure:
- `DEPLOY_SSH_KEY` (shared)
- `SERVER_HOST` (shared)
- `SERVER_USER` (shared)

## Security Benefits

1. **Isolation**: Each project's secrets are isolated
2. **No Conflicts**: Multiple projects can coexist
3. **Easy Rotation**: Update project-specific secrets without affecting others
4. **Access Control**: Grant repository access to only needed secrets

## Usage Flow

1. Define secrets in `secrets.yaml`
2. Run `python scripts/setup_secrets.py`
3. Generate project with `cookiecutter`
4. Push to GitHub
5. GitHub Actions automatically uses prefixed secrets
6. Bot deploys with correct configuration