# 🤖 Telegram Bot Cookiecutter Template

A modern, production-ready cookiecutter template for creating Telegram bots in Python. Get your bot running in minutes with built-in CI/CD, database migrations, and multi-language support.

## 🚀 Quick Start

### Option 1: Install CLI Globally (Recommended)
```bash
# Install the CLI tools
pip install git+https://github.com/hustlestar/tg-bot-template.git

# Create a new bot from anywhere
tgbot new "My Bot Name"
```

### Option 2: Direct Usage
```bash
# Clone and use directly
git clone https://github.com/hustlestar/tg-bot-template.git
cd tg-bot-template
python tg_bot_template_cli/create_bot.py "My Bot Name"
```

### Option 3: Traditional Cookiecutter
```bash
cookiecutter https://github.com/hustlestar/tg-bot-template.git
```

That's it! Your bot is created. See [PROJECT_CREATION_GUIDE.md](PROJECT_CREATION_GUIDE.md) for all creation methods and [QUICKSTART.md](QUICKSTART.md) for detailed setup.

## ✨ Features

### Core Features
- **🌐 Multi-language Support** - Built-in localization system
- **⌨️ Dynamic Keyboards** - Inline keyboard management
- **💾 PostgreSQL + Migrations** - Alembic for schema management
- **🔄 Auto-migrations** - Database updates on startup
- **📝 Clean Architecture** - Organized src/ layout

### Optional Features (configured during generation)
- **🤖 AI Integration** - OpenRouter support for GPT/Claude
- **🆘 Support System** - Built-in support bot functionality
- **🐳 Docker Support** - Docker & docker-compose files
- **🚀 GitHub Actions** - Automated CI/CD pipeline

### DevOps & Deployment
- **⚙️ Systemd Service** - Production deployment scripts
- **🔐 Organization Secrets** - GitHub secrets management
- **📊 Automated Testing** - pytest with async support
- **🎯 Type Checking** - mypy configuration

## 📋 Template Options

When you run `cookiecutter`, you'll be asked:

| Variable | Description | Default |
|----------|-------------|---------|
| `project_name` | Your bot's display name | My Telegram Bot |
| `project_slug` | Directory/package name | my-telegram-bot |
| `bot_username` | Telegram @username | my_telegram_bot |
| `use_openrouter` | Enable AI features? | y |
| `use_support_bot` | Enable support system? | n |
| `use_github_actions` | Include CI/CD? | y |
| `use_docker` | Include Docker files? | y |
| `python_version` | Python version | 3.11 |

## 🏗️ Generated Project Structure

```
your-bot-name/
├── src/                    # Clean Python package
│   ├── main.py            # Entry point
│   ├── cli.py             # CLI commands
│   ├── config/            # Settings management
│   ├── core/              # Bot core functionality
│   ├── handlers/          # Command handlers
│   ├── models/            # Database models
│   └── utils/             # Helpers
├── tests/                 # Test suite
├── deployment/            # Deployment scripts
│   ├── setup.sh          # First-time setup
│   ├── deploy.sh         # Quick updates
│   └── *.service         # Systemd service
├── .github/workflows/     # CI/CD pipelines
├── locales/              # Translation files
├── migrations/           # Database migrations
├── requirements.txt      # Dependencies
├── .env.example         # Environment template
└── docker-compose.yml   # Docker setup
```

## 🔧 Prerequisites

- Python 3.10+
- PostgreSQL
- Telegram Bot Token from [@BotFather](https://t.me/botfather)
- (Optional) OpenRouter API key for AI features

## 🚀 Deployment

### GitHub Actions (Recommended)

1. Set up organization secrets:
   ```bash
   cp secrets.example.yaml secrets.yaml
   # Edit secrets.yaml with your values
   python scripts/setup_secrets.py
   ```
   See [SECRETS_SETUP.md](SECRETS_SETUP.md) for details.
2. Push to GitHub
3. Automatic deployment on push to main!

### Manual Deployment

```bash
# On your server
git clone your-repo
cd your-bot
./deployment/setup.sh  # First time
./deployment/deploy.sh # Updates
```

## 🛠️ Development

### Testing the Template

```bash
# Clone this template
git clone https://github.com/hustlestar/tg-bot-template.git
cd tg-bot-template

# Install dependencies
pip install -r requirements.txt

# Run template tests
pytest tests/test_cookiecutter_template.py
```

### Contributing

1. Fork the repository
2. Create your feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📚 Documentation

- [INSTALLATION.md](INSTALLATION.md) - Install CLI tools globally
- [QUICKSTART.md](QUICKSTART.md) - Get started in 5 minutes
- [PROJECT_CREATION_GUIDE.md](PROJECT_CREATION_GUIDE.md) - All ways to create projects
- [SECRETS_SETUP.md](SECRETS_SETUP.md) - Organization secrets setup
- [SECRETS_ARCHITECTURE.md](SECRETS_ARCHITECTURE.md) - How secrets system works

## 🤝 Support

- Create an issue for bugs/features
- Check existing issues before posting
- PRs welcome!

## 📄 License

MIT License - see LICENSE file

---

Built with ❤️ for rapid Telegram bot development