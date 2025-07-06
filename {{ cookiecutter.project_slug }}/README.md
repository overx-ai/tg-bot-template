# {{ cookiecutter.bot_name }}

{{ cookiecutter.project_description }}

## 🚀 Quick Start

### 1. Prerequisites

- Python {{ cookiecutter.python_version }}+
- PostgreSQL database
- Telegram Bot Token (get from [@BotFather](https://t.me/botfather))
{% if cookiecutter.use_openrouter == 'y' -%}
- OpenRouter API Key (get from [OpenRouter.ai](https://openrouter.ai))
{%- endif %}

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/{{ cookiecutter.github_username }}/{{ cookiecutter.github_repo_name }}.git
cd {{ cookiecutter.github_repo_name }}

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your favorite editor
```

Required configuration:
- `TELEGRAM_BOT_TOKEN` - Your bot token from BotFather
- `DATABASE_URL` - PostgreSQL connection string

### 4. Database Setup

```bash
# Create database
createdb {{ cookiecutter.database_name }}

# Run migrations
{{ cookiecutter.project_slug }} migrate
```

### 5. Run the Bot

```bash
# Start the bot
{{ cookiecutter.project_slug }}

# Or with Python
python -m {{ cookiecutter.project_slug.replace('-', '_') }}.main
```

## 🛠️ Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov={{ cookiecutter.project_slug.replace('-', '_') }}
```

### Code Quality

```bash
# Format code
black {{ cookiecutter.project_slug.replace('-', '_') }}/
isort {{ cookiecutter.project_slug.replace('-', '_') }}/

# Type checking
mypy {{ cookiecutter.project_slug.replace('-', '_') }}/
```

### Database Migrations

```bash
# Check migration status
{{ cookiecutter.project_slug }} db status

# Create new migration
{{ cookiecutter.project_slug }} db revision -m "Description"

# Apply migrations
{{ cookiecutter.project_slug }} db upgrade

# Rollback
{{ cookiecutter.project_slug }} db downgrade
```

## 🚀 Deployment

### Using GitHub Actions

1. Set up GitHub Secrets:
   - `DEPLOY_SSH_KEY` - SSH key for server access
   - `SERVER_HOST` - Your server hostname
   - `SERVER_USER` - Server username
   - `TELEGRAM_BOT_TOKEN` - Bot token
   - `DATABASE_URL` - Production database URL
{% if cookiecutter.use_openrouter == 'y' -%}
   - `OPENROUTER_API_KEY` - OpenRouter API key
{%- endif %}

2. Push to main branch to trigger deployment

### Manual Deployment

```bash
# On your server
cd /path/to/deployment
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
{{ cookiecutter.project_slug }} migrate
sudo systemctl restart {{ cookiecutter.project_slug }}
```

## 📚 Features

- 🌐 Multi-language support ({{ cookiecutter.supported_languages }})
- ⌨️ Dynamic inline keyboards
{% if cookiecutter.use_openrouter == 'y' -%}
- 🤖 AI-powered responses via OpenRouter
{%- endif %}
{% if cookiecutter.use_support_bot == 'y' -%}
- 🆘 Built-in support system
{%- endif %}
- 💾 PostgreSQL database with migrations
- 🔄 Auto-migration on startup
- 📝 Clean, extensible architecture

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the {{ cookiecutter.open_source_license }} License.

## 👤 Author

{{ cookiecutter.author_name }} - {{ cookiecutter.author_email }}

---

Built with [telegram-bot-template](https://github.com/hustlestar/tg-bot-template)