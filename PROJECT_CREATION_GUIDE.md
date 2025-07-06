# 🚀 Project Creation Guide

This guide shows all the different ways to create new Telegram bot projects using this template.

## 📋 Available Methods

### 1. Traditional Cookiecutter (Interactive)

The standard way with prompts for each option:

```bash
cookiecutter https://github.com/hustlestar/tg-bot-template.git
```

### 2. Simple Script (One Command)

Just provide the project name:

```bash
python create_bot.py "My Weather Bot"
```

Options:
```bash
# Create in specific directory
python create_bot.py "My Bot" --output ~/projects

# Override specific settings
python create_bot.py "AI Bot" use_openrouter=y openrouter_model=gpt-4

# List all available options
python create_bot.py --list-options
```

### 3. Bot Factory (Advanced Features)

More powerful with presets and batch creation:

```bash
# Use a preset
python bot_factory.py "Support Bot" --preset support

# Create with secrets file
python bot_factory.py "My Bot" --create-secrets

# Output as JSON (for automation)
python bot_factory.py "My Bot" --json

# List available presets
python bot_factory.py --list-presets
```

Available presets:
- `simple` - Basic bot with minimal features
- `ai` - AI-powered bot with OpenRouter
- `support` - Customer support bot with tickets
- `enterprise` - Full-featured enterprise bot

### 4. Python API (For Scripts/Automation)

```python
from bot_factory import BotFactory

factory = BotFactory()

# Simple creation
result = factory.create_bot("My Bot")

# With options
result = factory.create_bot(
    "AI Assistant",
    preset="ai",
    git_init=True,
    create_secrets=True
)

# Batch creation
projects = [
    {"name": "Weather Bot", "preset": "simple"},
    {"name": "Support Bot", "preset": "support"},
    {"name": "AI Bot", "preset": "ai"}
]
results = factory.batch_create(projects)
```

### 5. Claude Code Integration

#### Option A: Direct Function Call

When using Claude Code, you can use the simple function:

```python
from bot_factory import create_bot_simple

# Claude can call this directly
create_bot_simple("Weather Bot", preset="ai", create_secrets=True)
```

#### Option B: MCP Server (Future)

When MCP (Model Context Protocol) is available:

```bash
# Start the MCP server
python mcp_bot_creator.py
```

Then Claude Code can use tools like:
- `create_telegram_bot` - Create a single bot
- `list_bot_presets` - See available presets
- `create_multiple_bots` - Create multiple bots at once
- `setup_bot_secrets` - Generate secrets configuration

### 6. Shell Aliases (For Power Users)

Add to your `.bashrc` or `.zshrc`:

```bash
# Quick bot creation
alias newbot='python ~/path/to/tg-bot-template/create_bot.py'

# With preset
alias newaibot='python ~/path/to/tg-bot-template/bot_factory.py --preset ai'

# Function for even simpler usage
tgbot() {
    python ~/path/to/tg-bot-template/bot_factory.py "$1" --create-secrets --git-init
}

# Usage: tgbot "My New Bot"
```

## 🎯 Which Method to Use?

### For Beginners
Use the **Simple Script** (`create_bot.py`):
```bash
python create_bot.py "My First Bot"
```

### For Claude Code
Use the **Python API**:
```python
from bot_factory import create_bot_simple
create_bot_simple("Bot Name", preset="ai")
```

### For Automation/CI/CD
Use **Bot Factory with JSON output**:
```bash
python bot_factory.py "Bot Name" --json --preset enterprise
```

### For Batch Operations
Use the **Python API**:
```python
factory = BotFactory()
factory.batch_create([
    {"name": "Bot 1", "preset": "simple"},
    {"name": "Bot 2", "preset": "ai"}
])
```

## 🔧 Common Scenarios

### Create an AI Bot with Everything

```bash
python bot_factory.py "AI Assistant" \
    --preset ai \
    --create-secrets \
    --git-init \
    --output ~/projects
```

This will:
1. Create an AI-enabled bot
2. Initialize git repository
3. Create secrets.yaml file
4. Place it in ~/projects directory

### Create Multiple Bots for an Organization

```python
from bot_factory import BotFactory

factory = BotFactory()

# Create all department bots
departments = ["Sales", "Support", "Marketing", "HR"]
for dept in departments:
    factory.create_bot(
        f"{dept} Bot",
        preset="support" if dept == "Support" else "simple",
        create_secrets=True
    )
```

### Quick Development Bot

```bash
# Minimal bot for testing
python create_bot.py "Test Bot" \
    use_docker=n \
    use_github_actions=n \
    use_openrouter=n
```

## 📝 Next Steps After Creation

Regardless of the creation method, the next steps are similar:

1. **Navigate to project**:
   ```bash
   cd your-bot-name
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your bot token
   ```

3. **Set up secrets** (if using GitHub Actions):
   ```bash
   # Edit secrets.yaml if created
   python scripts/setup_secrets.py
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the bot**:
   ```bash
   python -m your_bot_name.main
   ```

## 🚀 Pro Tips

1. **Use presets** to save time - they include sensible defaults
2. **Always use --create-secrets** if you plan to deploy via GitHub Actions
3. **The project prefix** is automatically generated from the project name
4. **Git init** is recommended to track changes from the start
5. **For Claude Code**, import the factory functions directly for best integration

## 🔗 Related Documentation

- [QUICKSTART.md](QUICKSTART.md) - General quick start guide
- [SECRETS_SETUP.md](SECRETS_SETUP.md) - Secrets management
- [README.md](README.md) - Template overview