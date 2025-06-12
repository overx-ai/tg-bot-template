# Telegram Bot Deployment System

A comprehensive, simple, and effective deployment solution for Telegram bots with automated backup, health checks, and rollback capabilities.

## Features

- 🚀 **One-command deployment** with comprehensive error handling
- 💾 **Automatic database backup** with S3 upload and rotation
- 🔍 **Pre and post-deployment health checks**
- 🔄 **Quick rollback capabilities** for failed deployments
- 📊 **Comprehensive logging** and monitoring
- 🤖 **GitHub Actions integration** for CI/CD
- 🔒 **Security-focused** with proper permissions and isolation

## Quick Start

### 1. Initial Setup

```bash
# Clone your repository
git clone git@github.com:your-username/your-bot.git
cd your-bot

# Make scripts executable
chmod +x deployment/*.sh

# Copy and configure deployment settings
cp deployment/config/deploy.conf.example deployment/config/deploy.conf
nano deployment/config/deploy.conf
```

### 2. Configure Environment

Edit `deployment/config/deploy.conf`:

```bash
# Server Configuration
SERVER_USER="jack"
DEPLOY_PATH="/home/jack/JACK"
REPO_URL="git@github.com:your-username/your-bot.git"
REPO_NAME="your-bot"

# Database Configuration
DATABASE_URL="postgresql://user:password@localhost:5432/botdb"

# Optional: S3 Backup
S3_BUCKET="your-backup-bucket"
```

### 3. Deploy

```bash
# Basic deployment
./deployment/deploy.sh

# Deployment with S3 backup
./deployment/deploy.sh --s3-bucket "my-backups"

# Dry run (test without changes)
./deployment/deploy.sh --dry-run

# Force deployment (skip health checks)
./deployment/deploy.sh --force
```

## Scripts Overview

### Main Deployment Script (`deploy.sh`)

The primary deployment script that orchestrates the entire deployment process.

**Usage:**
```bash
./deployment/deploy.sh [OPTIONS]
```

**Key Features:**
- Pre-deployment health checks
- Database backup with S3 upload
- Git repository management
- Python environment setup with UV
- Database migrations with Alembic
- Systemd service management
- Post-deployment verification
- Automatic rollback on failure

**Options:**
- `--repo-url URL` - Git repository URL
- `--branch BRANCH` - Branch to deploy (default: main)
- `--backup` / `--no-backup` - Enable/disable database backup
- `--s3-bucket BUCKET` - S3 bucket for backups
- `--env-file FILE` - Path to environment file
- `--dry-run` - Simulate deployment without changes
- `--force` - Skip health checks and force deployment
- `--verbose` - Enable verbose output

### Database Backup Script (`backup-db.sh`)

Creates PostgreSQL database backups with optional S3 upload and rotation.

**Usage:**
```bash
./deployment/backup-db.sh [OPTIONS]
```

**Features:**
- PostgreSQL database dumps
- Compression and encryption support
- S3 upload with lifecycle policies
- Backup rotation (keep N latest)
- Integrity verification

**Options:**
- `--db-url URL` - Database connection URL
- `--s3-bucket BUCKET` - S3 bucket for storage
- `--retention COUNT` - Number of backups to keep
- `--compress` / `--no-compress` - Enable/disable compression
- `--encrypt` - Enable GPG encryption

### Health Check Script (`health-check.sh`)

Performs comprehensive health checks for the bot and infrastructure.

**Usage:**
```bash
./deployment/health-check.sh [OPTIONS]
```

**Checks:**
- System resources (disk, memory, load)
- Database connectivity
- Telegram bot API
- Systemd service status
- File permissions
- Dependencies

**Options:**
- `--pre-deployment` - Run pre-deployment checks
- `--post-deployment` - Run post-deployment checks
- `--bot-token TOKEN` - Telegram bot token
- `--db-url URL` - Database connection URL
- `--timeout SECONDS` - Timeout for checks

### Rollback Script (`rollback.sh`)

Provides quick rollback capabilities for failed deployments.

**Usage:**
```bash
./deployment/rollback.sh [OPTIONS]
```

**Features:**
- Database restoration from backup
- Git commit rollback
- Service management
- Verification checks

**Options:**
- `--backup-file FILE` - Database backup to restore
- `--git-commit COMMIT` - Git commit to rollback to
- `--no-database` - Skip database restoration
- `--no-code` - Skip code rollback
- `--list-backups` - List available backups
- `--list-commits` - List recent commits

## GitHub Actions Integration

The deployment system includes a comprehensive GitHub Actions workflow for CI/CD.

### Setup

1. **Add repository secrets:**
   ```
   SSH_PRIVATE_KEY - SSH private key for server access
   SERVER_HOST - Server hostname or IP
   SLACK_WEBHOOK - Slack webhook URL (optional)
   ```

2. **Configure workflow:**
   Edit `.github/workflows/deploy.yml` to match your environment.

### Workflow Features

- **Automated testing** before deployment
- **SSH deployment** to your server
- **Health verification** after deployment
- **Automatic rollback** on failure
- **Slack notifications** for deployment status
- **Manual deployment** with options

### Triggering Deployments

```bash
# Automatic deployment on push to main
git push origin main

# Manual deployment with options
# Go to GitHub Actions → Deploy Telegram Bot → Run workflow
```

## Configuration

### Environment Variables

The deployment system uses environment variables from:

1. **Deployment config** (`deployment/config/deploy.conf`)
2. **Bot environment file** (`.env`)
3. **System environment variables**

### Required Configuration

```bash
# deployment/config/deploy.conf
REPO_URL="git@github.com:your-username/your-bot.git"
REPO_NAME="your-bot"
DEPLOY_PATH="/home/jack/JACK"
DATABASE_URL="postgresql://user:password@localhost:5432/botdb"
```

### Optional Configuration

```bash
# S3 Backup
S3_BUCKET="your-backup-bucket"
S3_REGION="us-east-1"

# Notifications
SLACK_WEBHOOK="https://hooks.slack.com/..."
DISCORD_WEBHOOK="https://discord.com/api/webhooks/..."

# Security
GPG_RECIPIENT="your-email@example.com"
```

## Security Considerations

### SSH Keys
- Use dedicated deployment SSH keys
- Restrict key permissions: `chmod 600 ~/.ssh/deploy_key`
- Add key to `~/.ssh/authorized_keys` on server

### File Permissions
- Scripts are executable only by owner
- Environment files have restricted permissions
- Service runs with limited user privileges

### Database Security
- Use dedicated database user with minimal privileges
- Encrypt backups before S3 upload
- Rotate database passwords regularly

### Environment Variables
- Store sensitive data in secure locations
- Use environment-specific configuration files
- Never commit secrets to version control

## Monitoring and Logging

### Log Files
- Deployment logs: `deployment/logs/deploy_*.log`
- Backup logs: `deployment/logs/backup_*.log`
- Health check logs: `deployment/logs/health_*.log`
- Rollback logs: `deployment/logs/rollback_*.log`

### Service Monitoring
```bash
# Check service status
systemctl status your-bot.service

# View service logs
journalctl -u your-bot.service -f

# Check recent errors
journalctl -u your-bot.service --since "1 hour ago" --grep "ERROR"
```

### Health Monitoring
```bash
# Manual health check
./deployment/health-check.sh

# Automated monitoring (add to cron)
*/5 * * * * /path/to/deployment/health-check.sh --post-deployment
```

## Troubleshooting

### Common Issues

**Deployment fails with permission errors:**
```bash
# Fix script permissions
chmod +x deployment/*.sh

# Fix service file permissions
sudo chown root:root /etc/systemd/system/your-bot.service
sudo chmod 644 /etc/systemd/system/your-bot.service
```

**Database connection fails:**
```bash
# Test database connection
psql "postgresql://user:password@localhost:5432/botdb" -c "SELECT 1;"

# Check database service
systemctl status postgresql
```

**Service fails to start:**
```bash
# Check service logs
journalctl -u your-bot.service --no-pager

# Check Python environment
cd /path/to/bot && source .venv/bin/activate && python -c "import telegram_bot_template"
```

**S3 upload fails:**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Test S3 access
aws s3 ls s3://your-bucket/
```

### Emergency Procedures

**Quick rollback:**
```bash
# Rollback to previous version
./deployment/rollback.sh --git-commit "HEAD~1" --force

# Rollback with database restore
./deployment/rollback.sh --backup-file "backup_20240108_010000.sql.gz" --force
```

**Manual service management:**
```bash
# Stop service
sudo systemctl stop your-bot.service

# Start service
sudo systemctl start your-bot.service

# Restart service
sudo systemctl restart your-bot.service
```

## Best Practices

### Deployment
1. **Always test in staging** before production deployment
2. **Use dry-run mode** to validate changes
3. **Monitor logs** during and after deployment
4. **Keep backups** before major changes
5. **Document changes** in commit messages

### Backup Strategy
1. **Automate backups** before each deployment
2. **Test restore procedures** regularly
3. **Store backups** in multiple locations
4. **Encrypt sensitive data** in backups
5. **Monitor backup success** and failures

### Security
1. **Use dedicated deployment keys**
2. **Limit user privileges** for service accounts
3. **Regularly update dependencies**
4. **Monitor for security vulnerabilities**
5. **Audit access logs** regularly

## Support

For issues and questions:

1. **Check logs** in `deployment/logs/`
2. **Run health checks** to identify problems
3. **Review configuration** files
4. **Test individual components** separately
5. **Use dry-run mode** to debug issues

## License

This deployment system is part of the Telegram Bot Template project and follows the same MIT license.