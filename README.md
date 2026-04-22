# forge-scaffold

A CLI to scaffold new projects and set up enterprise-grade CI/CD pipelines with a single command.

## Install

```bash
pip install forge-scaffold
```

## Commands

### `forge init-ci`

Set up a CI/CD pipeline on an existing project.

```bash
cd my-project
forge init-ci
```

Detects your project type automatically (Python, FastAPI, Node, React, Go) and guides you through:

- **CI jobs** — lint, tests with coverage threshold, security scan, SonarCloud
- **CD jobs** — Docker build, push to Docker Hub, Trivy CVE scan, SBOM generation
- **Deploy** — SSH deploy to any server, with optional Caddy reverse proxy + automatic HTTPS
- **DNS** — manual instructions or automatic Cloudflare A record creation
- **Secrets** — pushes all credentials to GitHub automatically

### `forge init`

Scaffold a new project from scratch with company standards.

```bash
forge init
```

Creates the project structure, Dockerfile, .gitignore, README, and sets up the GitHub repository with branch protection.

### Supported project types

| Type    | Lint          | Test              | Security       |
|---------|---------------|-------------------|----------------|
| Python  | ruff / flake8 | pytest + coverage | pip-audit      |
| FastAPI | ruff / flake8 | pytest + httpx    | pip-audit      |
| Node    | ESLint        | jest / vitest     | npm audit      |
| React   | ESLint        | vitest / jest     | npm audit      |
| Go      | golangci-lint | go test           | govulncheck    |

## CI/CD pipeline example

```
ci.yml        lint → test → security → docker-build (optional)
cd.yml        build → push → trivy scan → SBOM → deploy via SSH
```

Every Docker image is tagged with `:latest`, `:sha-xxxxxxx`, and `:vX.Y.Z` on semver tags.

## Requirements

- Python 3.9+
- GitHub account (optional, for repo creation and secrets)
- Docker Hub account (optional, for image push)
