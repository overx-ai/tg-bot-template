## CI/CD with GitHub Actions

This project includes GitHub Actions workflows for:
-   Automated Continuous Integration tests: [`.github/workflows/cd-test.yml`](./.github/workflows/cd-test.yml:1)
-   Automated application deployment and rollback: [`.github/workflows/ci-deploy.yml`](./.github/workflows/ci-deploy.yml:1)
-   Automated database backups: ([`.github/workflows/backup_workflow.yml`](.github/workflows/backup_workflow.yml))

To enable these workflows, you need to configure the following secrets in your GitHub repository settings (`Settings > Secrets and variables > Actions`):

### Workflow Descriptions & Triggers

-   **Application CI Tests (`cd-test.yml`)**:
    -   **Purpose**: Runs automated tests (e.g., Pytest) against the codebase.
    -   **Triggers**:
        -   On `push` to the `main` branch.
        -   On `pull_request` targeting the `main` branch.
        -   Manually via `workflow_dispatch`.
-   **Application Deployment (`ci-deploy.yml`)**:
    -   **Purpose**: Deploys the application to the server and handles automatic rollbacks on failure.
    -   **Triggers**:
        -   Automatically after the "Application CI Tests" workflow completes successfully on the `main` branch.
        -   Manually via `workflow_dispatch` with inputs for `environment` and `force_deploy`.
-   **Database Backups (`backup_workflow.yml`)**:
    -   (Description for this workflow, assuming it exists as per original README)

### Required Secrets

-   **For `ci-deploy.yml` and `backup_workflow.yml`**:
    -   `SSH_PRIVATE_KEY`: Your private SSH key that allows access to your deployment server. Ensure the corresponding public key is added to the `authorized_keys` file for the `DEPLOY_USER` on your server.
    -   `SERVER_HOST`: The hostname or IP address of your deployment server.

### Optional Secrets

-   **For `cd-test.yml`**:
    -   `SKIP_DOCKER_TESTS`: (Optional) Set to `true` to skip tests that might require Docker.
-   **For `ci-deploy.yml` and `backup_workflow.yml` (and optionally `cd-test.yml` if test notifications are added)**:
    -   `SLACK_WEBHOOK`: Your Slack incoming webhook URL. If provided, status notifications (deployment, rollback, backup) will be sent to the configured Slack channel.

### Environment Variables

The following environment variables are primarily configured within the workflow files:

-   `REPO_NAME` (e.g., `tg-bot-template`): Used in `cd-test.yml`, `ci-deploy.yml`, and `backup_workflow.yml`.
-   `DEPLOY_USER` (default: `jack`): Used in `ci-deploy.yml` and `backup_workflow.yml`.
-   `DEPLOY_PATH` (default: `/home/jack/JACK`): Used in `ci-deploy.yml` and `backup_workflow.yml`.

You can modify `DEPLOY_USER` and `DEPLOY_PATH` directly in [`.github/workflows/ci-deploy.yml`](./.github/workflows/ci-deploy.yml:1) and [`.github/workflows/backup_workflow.yml`](.github/workflows/backup_workflow.yml) if your server setup differs.
The `REPO_NAME` can be modified in all respective workflow files if needed.