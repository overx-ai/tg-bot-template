# 🔐 Organization Secrets Setup Guide

This guide will help you set up GitHub organization secrets for deploying bots created with this template.

## 📋 What You Need to Provide

### 1. **GitHub Organization Details**
- **Organization Name**: Your GitHub organization (e.g., `mycompany`)
- **GitHub Token**: Personal access token with `admin:org` scope
  - Go to GitHub → Settings → Developer settings → Personal access tokens
  - Create token with `admin:org` and `repo` scopes

### 2. **Project Name**
- **Project Identifier**: A unique name for your bot project (e.g., `WEATHERBOT`, `TODOBOT`)
- This will prefix your secrets to avoid conflicts between projects
- Use UPPERCASE letters and underscores only

### 3. **Required Secrets Values**

#### Core Bot Secrets (Required)
1. **TELEGRAM_BOT_TOKEN**
   - Get from [@BotFather](https://t.me/botfather) on Telegram
   - Format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
   - Each bot needs its own token

2. **DATABASE_URL**
   - PostgreSQL connection string
   - Format: `postgresql://username:password@host:5432/database_name`
   - Example: `postgresql://botuser:secretpass@localhost:5432/weatherbot_db`

#### Deployment Secrets (Required for GitHub Actions)
3. **DEPLOY_SSH_KEY**
   - SSH private key for server access
   - Generate: `ssh-keygen -t ed25519 -C "bot-deploy@example.com"`
   - Copy the private key content (from `~/.ssh/id_ed25519`)
   - Add public key to server's `~/.ssh/authorized_keys`

4. **SERVER_HOST**
   - Your server's IP address or hostname
   - Example: `192.168.1.100` or `bot-server.example.com`

5. **SERVER_USER**
   - Username on the deployment server
   - Example: `ubuntu`, `deploy`, `bot`

#### Optional Secrets
6. **OPENROUTER_API_KEY** (if using AI features)
   - Get from [OpenRouter.ai](https://openrouter.ai)
   - Required only if `use_openrouter: y` in cookiecutter

7. **SUPPORT_BOT_TOKEN** (if using support bot)
   - Another bot token from @BotFather
   - Required only if `use_support_bot: y` in cookiecutter

8. **SUPPORT_CHAT_ID** (if using support bot)
   - Your Telegram user/chat ID
   - Get it by messaging [@userinfobot](https://t.me/userinfobot)

## 🚀 Quick Setup Process

### Option 1: Interactive Setup (Recommended)

```bash
cd tg-bot-template
pip install -r scripts/requirements-secrets.txt
python scripts/setup-all-secrets.py
```

This will guide you through:
1. Entering your GitHub organization name
2. Choosing a project name (e.g., `WEATHERBOT`)
3. Entering each secret value securely
4. Setting repository access permissions

### Option 2: Manual Setup with Script

```bash
# Set environment variables
export GITHUB_ORG="myorganization"
export PROJECT_NAME="WEATHERBOT"
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxx"

# Run the project secrets manager
python scripts/manage-project-secrets.py
```

## 📝 Example Setup Session

```
$ python scripts/setup-all-secrets.py

=== Telegram Bot Template - Organization Secrets Setup ===

Do you want to use project-specific secrets (recommended)? (Y/n): y

Enter your project name (e.g., 'mybot-prod'): WEATHERBOT
Enter your GitHub organization name: mycompany

Configuring secret: WEATHERBOT_TELEGRAM_BOT_TOKEN
Description: Telegram Bot API token from @BotFather
Enter value for 'WEATHERBOT_TELEGRAM_BOT_TOKEN' (or press Enter to skip): [hidden input]

Configuring secret: WEATHERBOT_DATABASE_URL
Description: PostgreSQL connection string
Enter value for 'WEATHERBOT_DATABASE_URL' (or press Enter to skip): [hidden input]

Enter repository name for project 'WEATHERBOT': weather-bot

✓ Successfully created/updated 5 secrets for project 'WEATHERBOT'
```

## 🔍 Verifying Your Setup

After setting up secrets, verify they're created:

```bash
# List your project secrets
python scripts/manage-project-secrets.py
# Choose option 2 (List project secrets)
```

## 🚨 Important Notes

1. **Secret Naming**: With project prefix, your secrets will be named:
   - `WEATHERBOT_TELEGRAM_BOT_TOKEN`
   - `WEATHERBOT_DATABASE_URL`
   - etc.

2. **Repository Access**: When using `selected` visibility:
   - Add your repository to the secret's access list
   - This happens automatically if you provide the repo name

3. **GitHub Actions**: The workflows expect secrets with project prefix:
   ```yaml
   env:
     BOT_TOKEN: ${{ secrets.WEATHERBOT_TELEGRAM_BOT_TOKEN }}
   ```

4. **Security Best Practices**:
   - Never commit secret values
   - Rotate secrets every 90 days
   - Use different secrets for dev/staging/prod
   - Limit access to only necessary repositories

## 🆘 Troubleshooting

- **"Invalid GitHub token"**: Ensure token has `admin:org` scope
- **"Organization not found"**: Check organization name and your access
- **"Secret not available in workflow"**: Add repository to secret's access list
- **"Failed to encrypt"**: Install PyNaCl: `pip install PyNaCl`

## 📚 Next Steps

1. Run `cookiecutter` to generate your bot
2. Push the generated project to GitHub
3. Secrets will be automatically available in GitHub Actions
4. Deploy with confidence! 🚀