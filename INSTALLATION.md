# 🚀 Installation Guide

This guide shows how to install the Telegram Bot Template CLI tools globally on your system.

## Prerequisites

- Python 3.11+
- pip or uv package manager

## Installation Methods

### Method 1: Install with uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/hustlestar/tg-bot-template.git
cd tg-bot-template

# Install globally with uv
uv pip install --system .

# Or install in user space
uv pip install --user .
```

### Method 2: Install with pip

```bash
# Clone the repository
git clone https://github.com/hustlestar/tg-bot-template.git
cd tg-bot-template

# Install globally
pip install .

# Or install in user space
pip install --user .
```

### Method 3: Install from GitHub directly

```bash
# Install latest from GitHub
pip install git+https://github.com/hustlestar/tg-bot-template.git

# Or with uv
uv pip install git+https://github.com/hustlestar/tg-bot-template.git
```

### Method 4: Development Installation

For development, install in editable mode:

```bash
# With pip
pip install -e .

# With uv
uv pip install -e .

# Include development dependencies
pip install -e ".[dev]"
```

## Verify Installation

After installation, verify the CLI is available:

```bash
# Check if tgbot command is available
tgbot --help

# Check version
tgbot version
```

## Usage

Once installed globally, you can use the `tgbot` command from anywhere:

### Quick Bot Creation

```bash
# Create a new bot with default settings
tgbot new "My Weather Bot"

# Create with a preset
tgbot new "AI Assistant" --preset ai

# Create in specific directory
tgbot new "My Bot" --output ~/projects
```

### Advanced Options

```bash
# Use the factory with more options
tgbot factory "Enterprise Bot" --preset enterprise --create-secrets

# List available presets
tgbot factory --list-presets

# Start MCP server for Claude Code
tgbot mcp
```

### Command Structure

```
tgbot <command> [options]

Commands:
  new       Create a new bot (simple mode)
  factory   Advanced bot creation with presets
  mcp       Start MCP server for Claude Code
  version   Show version

Examples:
  tgbot new "My Bot"
  tgbot new "AI Bot" --preset ai --secrets
  tgbot factory --list-presets
```

## Shell Completion (Optional)

For bash/zsh completion, add to your shell config:

```bash
# For bash (~/.bashrc)
eval "$(_TGBOT_COMPLETE=bash_source tgbot)"

# For zsh (~/.zshrc)
eval "$(_TGBOT_COMPLETE=zsh_source tgbot)"
```

## Troubleshooting

### Command not found

If `tgbot` command is not found after installation:

1. Check if it's in your PATH:
   ```bash
   which tgbot
   ```

2. If using `--user` installation, add to PATH:
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   export PATH="$HOME/.local/bin:$PATH"
   ```

3. Reload your shell:
   ```bash
   source ~/.bashrc  # or ~/.zshrc
   ```

### Permission denied

If you get permission errors:

1. Use `--user` flag for user installation
2. Or use `sudo` for system-wide installation (not recommended)
3. Consider using a virtual environment

### Import errors

If you get import errors when running `tgbot`:

1. Ensure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Check Python version:
   ```bash
   python --version  # Should be 3.11+
   ```

## Uninstallation

To uninstall the CLI tools:

```bash
# With pip
pip uninstall tg-bot-template

# With uv
uv pip uninstall tg-bot-template
```

## Next Steps

After installation, see:
- [PROJECT_CREATION_GUIDE.md](PROJECT_CREATION_GUIDE.md) - How to create projects
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [README.md](README.md) - Project overview