## CI/CD with GitHub Actions

This project includes GitHub Actions workflows for automated application deployment ([`.github/workflows/deploy.yml`](.github/workflows/deploy.yml:1)) and database backups ([`.github/workflows/backup_workflow.yml`](.github/workflows/backup_workflow.yml)). To enable these workflows, you need to configure the following secrets in your GitHub repository settings (`Settings > Secrets and variables > Actions`):

### Required Secrets for Deployment and Backups

-   `SSH_PRIVATE_KEY`: Your private SSH key that allows access to your deployment server. Ensure the corresponding public key is added to the `authorized_keys` file for the `DEPLOY_USER` on your server.
-   `SERVER_HOST`: The hostname or IP address of your deployment server.

### Optional Secrets

-   `SLACK_WEBHOOK`: (Optional) Your Slack incoming webhook URL. If provided, deployment and backup status notifications will be sent to the configured Slack channel.

The `DEPLOY_USER` (default: `jack`) and `DEPLOY_PATH` (default: `/home/jack/JACK`) are set as environment variables within the workflow files themselves. You can modify them directly in [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml:1) and [`.github/workflows/backup_workflow.yml`](.github/workflows/backup_workflow.yml) if your server setup differs.