# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Cookiecutter template for creating production-ready Telegram bots in Python. The template itself generates bot projects, and includes a CLI tool for bot creation.

## Key Commands

### Development Commands

```bash
# Install the template CLI globally
pip install -e .
# Or with uv
uv pip install -e .

# Run tests
pytest tests/test_cookiecutter_template.py

# Lint and format code
ruff check .
ruff format .
black .
isort .

# Type checking
mypy tg_bot_template_cli/
```

### Template Usage Commands

```bash
# Create a new bot using CLI (after global install)
tgbot new "Bot Name"
tgbot factory --preset ai "AI Bot"
tgbot mcp  # Start MCP server for Claude Code

# Direct usage without install
python tg_bot_template_cli/create_bot.py "Bot Name"

# Traditional cookiecutter
cookiecutter .
```

### Working with Generated Bots

Generated bots will have their own structure with:
- `python src/cli.py` - CLI commands for the bot
- Database migrations via Alembic
- Docker support with docker-compose
- Systemd deployment scripts in `deployment/`

## Architecture

### Template Structure

The template has two main components:

1. **Template Files** (`{{ cookiecutter.project_slug }}/`): The actual bot template that gets rendered by cookiecutter
2. **CLI Tools** (`tg_bot_template_cli/`): Python package providing the `tgbot` command

### Key Components

- **bot_factory.py**: Advanced bot creation with presets (simple, ai, support, enterprise)
- **mcp_bot_creator.py**: MCP server integration for Claude Code
- **create_bot.py**: Simple bot creation wrapper
- **setup_secrets.py**: GitHub organization secrets management

### Template Features

When creating a bot, the template supports:
- Multi-language localization (locales/)
- PostgreSQL with Alembic migrations
- Optional AI integration via OpenRouter
- Optional support bot functionality
- GitHub Actions CI/CD
- Docker deployment
- Systemd service files

### Secrets Management

The template uses a YAML-based secrets system with automatic project prefixing:
- `secrets.yaml` defines secrets with optional prefixing
- `scripts/setup_secrets.py` pushes to GitHub organization
- Prefixed secrets prevent conflicts between projects

## Important Patterns

1. **Cookiecutter Variables**: Defined in `cookiecutter.json`, automatically generate derived values like `project_prefix` from `project_slug`

2. **Post-Generation Hooks**: `hooks/post_gen_project.py` runs after template generation to clean up optional features

3. **CLI Entry Points**: Defined in `pyproject.toml` under `[project.scripts]`

4. **Testing**: Test the template itself with `pytest tests/test_cookiecutter_template.py`

## Dependencies

- Python 3.11+
- cookiecutter>=2.1.0
- PyNaCl, pyyaml, requests for secrets management
- mcp>=0.1.0 for MCP integration
- Development: pytest, ruff, black, isort, mypy