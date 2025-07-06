#!/bin/bash
# Initial setup script for {{ cookiecutter.bot_name }}

set -e

echo "🚀 Setting up {{ cookiecutter.bot_name }} for the first time..."

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo "❌ Please don't run this script as root"
   exit 1
fi

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python{{ cookiecutter.python_version }} python{{ cookiecutter.python_version }}-venv postgresql-client

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python{{ cookiecutter.python_version }} -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration!"
    read -p "Press enter when you've updated .env file..."
fi

# Create database if needed
echo "🗄️ Setting up database..."
read -p "Enter PostgreSQL database name [{{ cookiecutter.database_name }}]: " db_name
db_name=${db_name:-{{ cookiecutter.database_name }}}

createdb $db_name || echo "Database might already exist, continuing..."

# Run migrations
echo "🔄 Running database migrations..."
{{ cookiecutter.project_slug }} migrate || python -m cli migrate

# Install systemd service
echo "⚙️ Installing systemd service..."
sudo cp deployment/{{ cookiecutter.project_slug }}.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable {{ cookiecutter.project_slug }}.service

# Start service
echo "▶️ Starting service..."
sudo systemctl start {{ cookiecutter.project_slug }}.service

# Check status
echo "✅ Checking service status..."
sudo systemctl status {{ cookiecutter.project_slug }}.service --no-pager

echo "✨ Setup complete!"
echo ""
echo "📌 Next steps:"
echo "1. Check logs: sudo journalctl -u {{ cookiecutter.project_slug }} -f"
echo "2. Restart service: sudo systemctl restart {{ cookiecutter.project_slug }}"
echo "3. Deploy updates: ./deployment/deploy.sh"