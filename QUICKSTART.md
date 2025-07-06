# 🚀 Quick Start Guide - Telegram Bot Template

Get your Telegram bot running in under 5 minutes!

## Prerequisites

- Python 3.10+
- PostgreSQL
- GitHub account (for deployment)
- Telegram Bot Token from [@BotFather](https://t.me/botfather)

## 1️⃣ Set Up Organization Secrets (One-time setup)

Before creating your first bot, set up GitHub organization secrets:

```bash
# Clone the template
git clone https://github.com/hustlestar/tg-bot-template.git
cd tg-bot-template

# Install dependencies for secrets management
pip install -r scripts/requirements-secrets.txt

# Run the setup script
python scripts/setup-all-secrets.py
```

This will guide you through setting up:
- `TELEGRAM_BOT_TOKEN` - Your bot's token
- `DATABASE_URL` - PostgreSQL connection
- `DEPLOY_SSH_KEY` - SSH key for deployment
- `SERVER_HOST` & `SERVER_USER` - Deployment server details
- Optional: `OPENROUTER_API_KEY` for AI features

## 2️⃣ Create Your Bot Project

```bash
# Install cookiecutter
pip install cookiecutter

# Generate your bot from the template
cookiecutter https://github.com/hustlestar/tg-bot-template.git
```

Answer the prompts:
- **project_name**: Your bot's display name (e.g., "Weather Bot")
- **project_slug**: Directory/package name (e.g., "weather-bot")
- **bot_username**: Telegram username (e.g., "weather_bot")
- **use_openrouter**: Enable AI features? (y/n)
- **use_support_bot**: Enable support system? (y/n)

## 3️⃣ Configure Your Bot

```bash
cd your-bot-name

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env  # or your favorite editor
```

Required in `.env`:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
DATABASE_URL=postgresql://user:pass@localhost:5432/your_bot_db
```

## 4️⃣ Set Up Database

```bash
# Create database
createdb your_bot_db

# Install dependencies
pip install -r requirements.txt

# Run migrations
your-bot-name migrate
```

## 5️⃣ Run Your Bot Locally

```bash
# Start the bot
your-bot-name

# Or with Python
python -m your_bot_name.main
```

Your bot is now running! Send `/start` to your bot on Telegram.

## 6️⃣ Deploy to Production

### Option A: GitHub Actions (Recommended)

1. Push to GitHub:
   ```bash
   git remote add origin https://github.com/yourusername/your-bot-name.git
   git push -u origin main
   ```

2. The bot will automatically deploy when you push to `main` branch!

### Option B: Manual Deployment

```bash
# On your server
git clone https://github.com/yourusername/your-bot-name.git
cd your-bot-name

# Set up Python environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env  # Add your configuration

# Run migrations
your-bot-name migrate

# Start with systemd (see deployment docs)
```

## 🎯 Common Commands

### Bot Management
```bash
# Check configuration
your-bot-name validate

# Run migrations
your-bot-name migrate

# Database operations
your-bot-name db status
your-bot-name db upgrade
your-bot-name db history
```

### Development
```bash
# Run tests
pytest

# Format code
black your_bot_name/
isort your_bot_name/

# Type checking
mypy your_bot_name/
```

### Docker
```bash
# Run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f bot
```

## 📋 Feature Checklist

After setup, your bot will have:

- ✅ Multi-language support (configured languages)
- ✅ PostgreSQL database with migrations
- ✅ Inline keyboards with callbacks
- ✅ AI integration (if enabled)
- ✅ Support system (if enabled)
- ✅ Automated deployment via GitHub Actions
- ✅ Docker support
- ✅ Comprehensive logging
- ✅ Error handling

## 🆘 Troubleshooting

### Bot not responding?
1. Check token in `.env`
2. Verify bot is running: `systemctl status your-bot-name`
3. Check logs: `journalctl -u your-bot-name -f`

### Database errors?
1. Ensure PostgreSQL is running
2. Verify DATABASE_URL in `.env`
3. Run migrations: `your-bot-name migrate`

### Deployment failing?
1. Check GitHub secrets are set
2. Verify SSH key has access to server
3. Check GitHub Actions logs

## 📚 Next Steps

1. **Customize handlers**: Edit `handlers/` directory
2. **Add commands**: Register in `core/bot.py`
3. **Extend models**: Add to `models/` directory
4. **Add languages**: Create JSON files in `locales/`

## 🔗 Resources

- [Full Documentation](README.md)
- [Deployment Guide](deployment/README.md)
- [Secrets Management](scripts/SECRETS_README.md)
- [Template Repository](https://github.com/hustlestar/tg-bot-template)

---

**Need help?** Create an issue on GitHub or check the documentation!