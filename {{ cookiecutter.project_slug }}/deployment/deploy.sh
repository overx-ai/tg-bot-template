#!/bin/bash
# Simple deployment script for {{ cookiecutter.bot_name }}

set -e

echo "🚀 Deploying {{ cookiecutter.bot_name }}..."

# Update code
echo "📦 Pulling latest changes..."
git pull origin main || git pull origin master

# Update dependencies
echo "📚 Installing dependencies..."
source venv/bin/activate || python{{ cookiecutter.python_version }} -m venv venv && source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Run migrations
echo "🗄️ Running database migrations..."
{{ cookiecutter.project_slug }} migrate || python -m cli migrate

# Restart service
echo "🔄 Restarting service..."
sudo systemctl restart {{ cookiecutter.project_slug }}.service

# Check status
echo "✅ Checking service status..."
sudo systemctl status {{ cookiecutter.project_slug }}.service --no-pager

echo "✨ Deployment complete!"