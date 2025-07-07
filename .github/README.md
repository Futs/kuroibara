[![Deploy](https://github.com/Futs/kuroibara/actions/workflows/deploy.yml/badge.svg)](https://github.com/Futs/kuroibara/actions/workflows/deploy.yml)
# GitHub Actions CI/CD Documentation

This directory contains the CI/CD configuration for the Kuroibara project using GitHub Actions.

## Workflows

### 1. Pull Request Checks (`pr-checks.yml`)

Runs comprehensive tests and checks on every pull request:

- **Backend Tests**: Runs pytest with coverage reporting
- **Frontend Tests**: Runs Vitest with linting and type checking
- **Security Scan**: Snyk vulnerability scanning for code and dependencies
- **Docker Build**: Validates Docker image builds
- **Integration Tests**: End-to-end testing with Docker Compose
- **Code Quality**: Formatting and linting checks

**Triggers**: Pull requests to `main` or `develop` branches

### 2. Deployment (`deploy.yml`)

Builds and deploys the application:

- **Build and Push**: Creates Docker images and pushes to GitHub Container Registry
- **Deploy Staging**: Deploys to staging environment (on main branch)
- **Deploy Production**: Deploys to production environment (on version tags)
- **Create Release**: Generates release notes and artifacts

**Triggers**: Push to `main` branch or version tags (`v*`)

### 3. Security Scan (`security-scan.yml`)

Comprehensive security scanning (excluding Snyk which only runs on PRs):

- **CodeQL Analysis**: Static code analysis for Python and JavaScript
- **Dependency Review**: Checks for vulnerable dependencies in PRs
- **Secret Scan**: Scans for leaked secrets using TruffleHog

**Triggers**: Daily schedule, pushes to main/develop, pull requests

### 4. Dependency Updates (`dependency-updates.yml`)

Automated dependency management:

- **Python Dependencies**: Updates backend requirements
- **Node.js Dependencies**: Updates frontend packages
- **Automated PRs**: Creates pull requests with dependency updates

**Triggers**: Weekly schedule (Mondays at 9 AM UTC) or manual trigger

## Configuration Files

### Backend

- `backend/pyproject.toml`: Python project configuration including Black, isort, mypy, pytest, and coverage settings
- `backend/.flake8`: Python linting configuration
- `backend/pytest.ini`: Test configuration (also defined in pyproject.toml)

### Frontend

- `frontend/app/vite.config.js`: Includes test configuration for Vitest
- `frontend/app/src/tests/setup.js`: Test setup and global mocks
- `frontend/app/src/tests/App.test.js`: Example test file

## Environment Variables

The workflows use the following environment variables:

- `GITHUB_TOKEN`: Automatically provided by GitHub
- `SNYK_TOKEN`: Snyk authentication token (required for security scanning)
- `DATABASE_URL`: Database connection string for tests
- `REDIS_URL`: Redis connection string for tests
- `SECRET_KEY`: JWT secret key for authentication tests

### Setting up Snyk Integration (PR Scanning Only)

1. **Create a Snyk account** at [snyk.io](https://snyk.io)
2. **Get your Snyk token**:
   - Go to your Snyk account settings
   - Navigate to "General" > "Auth Token"
   - Copy the token
3. **Add the token to GitHub Secrets**:
   - Go to your repository settings
   - Click "Secrets and variables" > "Actions"
   - Click "New repository secret"
   - Name: `SNYK_TOKEN`
   - Value: Your Snyk authentication token

**Note**: Snyk will only run during pull request checks to scan for vulnerabilities. No ongoing monitoring or project integration is configured.

## Branch Protection Rules

Recommended branch protection rules for the `main` branch:

1. Require pull request reviews before merging
2. Require status checks to pass before merging:
   - `Backend Tests`
   - `Frontend Tests`
   - `Security Scan`
   - `Docker Build Test`
   - `Integration Tests`
   - `Code Quality`
3. Require branches to be up to date before merging
4. Require signed commits (optional)
5. Include administrators in restrictions

## Setting Up Branch Protection

1. Go to your repository settings
2. Click on "Branches"
3. Add a rule for the `main` branch
4. Configure the settings as described above

## Manual Triggers

Some workflows can be triggered manually:

- **Dependency Updates**: Go to Actions → Dependency Updates → Run workflow
- **Security Scan**: Triggered automatically but can be run manually

## Monitoring and Notifications

- **Failed builds**: GitHub will automatically notify you of failed workflows
- **Security alerts**: GitHub Security tab shows detected vulnerabilities
- **Dependabot alerts**: Automatic dependency vulnerability notifications

## Docker Images

Built images are published to GitHub Container Registry:

- `ghcr.io/your-username/kuroibara-backend:latest`
- `ghcr.io/your-username/kuroibara-frontend:latest`

## Troubleshooting

### Common Issues

1. **Tests failing**: Check the test logs in the Actions tab
2. **Build failures**: Verify Docker configuration and dependencies
3. **Security scans failing**: Review security alerts in the Security tab
4. **Dependency updates failing**: Check for breaking changes in dependencies

### Debug Tips

- Use the Actions tab to view detailed logs
- Failed workflows can be re-run from the Actions interface
- Check the "Summary" section for quick overview of issues

## Contributing

When contributing to this project:

1. Ensure all tests pass locally before creating a PR
2. Follow the code style guidelines (enforced by linters)
3. Add tests for new features
4. Update documentation as needed
5. Use the provided PR template

## Deployment

### Staging

- Automatically deploys on push to `main` branch
- Environment: `staging`
- Requires manual approval if environment protection rules are set

### Production

- Automatically deploys on version tags (e.g., `v1.0.0`)
- Environment: `production`
- Requires manual approval if environment protection rules are set

To create a release:

1. Create and push a version tag: `git tag v1.0.0 && git push origin v1.0.0`
2. The deployment workflow will automatically trigger
3. A GitHub release will be created with the changelog
