from __future__ import annotations

from pathlib import Path

import typer

from forge.commands.scaffold import console
from forge.config.settings import settings
from forge.config.store import load_stored_token, save_token
from forge.detectors.project_type import detect_project_type
from forge.generators.ci import generate_ci
from forge.github.branch_protection import set_branch_protection
from forge.github.secrets import set_repo_secrets
from forge.github.errors import GitHubError

app = typer.Typer(help="Set up CI/CD pipeline on an existing project.")

PROJECT_TYPES = ["python", "fastapi", "node", "react", "go"]


@app.callback(invoke_without_command=True)
def init_ci(
    project_dir: Path = typer.Option(Path("."), "--dir", "-d", help="Project directory"),
) -> None:
    """Detect project type and configure CI/CD pipeline."""
    project_dir = project_dir.resolve()

    if not project_dir.exists():
        console.print(f"[red]Error:[/red] Directory '{project_dir}' does not exist.")
        raise typer.Exit(1)

    console.print(f"\n[bold]forge[/bold] — CI/CD setup for [cyan]{project_dir.name}[/cyan]\n")

    # --- Detect project type ---
    detected = detect_project_type(project_dir)
    if detected:
        console.print(f"  Detected project type: [bold cyan]{detected}[/bold cyan]")
        confirmed = typer.confirm(f"  Use '{detected}'?", default=True)
        project_type = detected if confirmed else _ask_type()
    else:
        console.print("  [yellow]Could not detect project type automatically.[/yellow]")
        project_type = _ask_type()

    # --- CI jobs ---
    console.print("\n  [bold]CI jobs[/bold]")
    job_lint = typer.confirm("    Lint?", default=True)
    lint_tool = ""
    if job_lint and project_type in ("python", "fastapi"):
        lint_tool = _ask_choice("    Lint tool", ["ruff (recommended)", "flake8 + black"])
        lint_tool = "flake8" if "flake8" in lint_tool else "ruff"

    job_test = typer.confirm("    Tests?", default=True)
    test_tool = ""
    coverage_threshold = 80
    if job_test:
        if project_type in ("node", "react"):
            test_tool = _ask_choice("    Test runner", ["jest (recommended)", "vitest"])
            test_tool = "vitest" if "vitest" in test_tool else "jest"
        coverage_threshold = typer.prompt("    Coverage threshold (%)", default=80, type=int)

    job_security = typer.confirm("    Security (dependency scan)?", default=True)

    sonar = False
    sonar_secrets: dict = {}
    sonar_project_key = ""
    sonar_organization = ""
    if job_security:
        sonar = typer.confirm("    SonarCloud code quality scan?", default=False)
        if sonar:
            console.print("    [dim]SonarCloud organization = your GitHub username or org (sonarcloud.io/organizations)[/dim]")
            sonar_organization = typer.prompt("    SonarCloud organization")
            sonar_project_key = project_dir.name
            sonar_token = typer.prompt("    SonarCloud token", hide_input=True)
            sonar_secrets["SONAR_TOKEN"] = sonar_token

    # --- CI Docker ---
    docker_build_in_ci = typer.confirm("    Build Docker image in CI?", default=False)

    # --- CD jobs ---
    console.print("\n  [bold]CD[/bold]")
    cd_job_push = False
    cd_job_trivy = False
    cd_job_sbom = False
    cd_job_build = False
    docker_secrets: dict = {}
    if docker_build_in_ci:
        cd_job_push = typer.confirm("    Push image to Docker Hub?", default=False)
        if cd_job_push:
            cd_job_trivy = typer.confirm("    Trivy CVE scan after push?", default=True)
            cd_job_sbom = typer.confirm("    Generate SBOM?", default=True)
            docker_username = typer.prompt("    Docker username")
            docker_password = typer.prompt("    Docker password/token", hide_input=True)
            docker_secrets = {
                "DOCKER_USERNAME": docker_username,
                "DOCKER_PASSWORD": docker_password,
            }
    docker = docker_build_in_ci or cd_job_push

    # --- Test secrets from .env.example ---
    env_example = project_dir / ".env.example"
    test_secrets: dict = {}
    if env_example.exists():
        env_vars = _parse_env_example(env_example)
        if env_vars:
            console.print(f"\n  Found [cyan]{len(env_vars)}[/cyan] variable(s) in .env.example.")
            push_test_secrets = typer.confirm("  Push them as GitHub secrets for CI tests?", default=True)
            if push_test_secrets:
                console.print("  [dim]Variables with a value are used as-is. Leave blank to skip.[/dim]")
                for key, default_value in env_vars.items():
                    if default_value:
                        test_secrets[key] = default_value
                        console.print(f"  [dim]✓ {key} = {default_value}[/dim]")
                    else:
                        value = typer.prompt(f"  {key}", default="", hide_input=True, show_default=False)
                        if value:
                            test_secrets[key] = value

    # --- Repo settings (branch protection) ---
    repo_name = project_dir.name
    setup_branch_protection = typer.confirm(
        "  Apply branch protection rules on main?", default=True
    )

    all_secrets = {**docker_secrets, **sonar_secrets, **test_secrets}
    needs_token = setup_branch_protection or bool(all_secrets)

    if needs_token:
        if not settings.github_token:
            settings.github_token = load_stored_token()
        if not settings.github_token:
            repo_name = typer.prompt("  GitHub repo name", default=project_dir.name)
            token = typer.prompt("  GitHub token", hide_input=True)
            settings.github_token = token
            save_token(token)
            console.print("  [dim]Token saved to ~/.config/forge/config.toml[/dim]")
        else:
            repo_name = typer.prompt("  GitHub repo name", default=project_dir.name)

    console.print()

    # --- Generate CI workflow ---
    generate_ci(
        project_dir,
        project_type,
        project_name=project_dir.name,
        docker=docker,
        sonar=sonar,
        sonar_project_key=sonar_project_key,
        sonar_organization=sonar_organization,
        coverage_threshold=coverage_threshold,
        test_secret_keys=list(test_secrets.keys()),
        job_lint=job_lint,
        job_test=job_test,
        job_security=job_security,
        lint_tool=lint_tool,
        test_tool=test_tool,
        docker_build_in_ci=docker_build_in_ci,
        cd_job_build=cd_job_build,
        cd_job_push=cd_job_push,
        cd_job_trivy=cd_job_trivy,
        cd_job_sbom=cd_job_sbom,
    )
    console.print("[green]✓[/green] .github/workflows/ci.yml generated")
    console.print("[green]✓[/green] .github/dependabot.yml generated")

    # --- .env.example ---
    if not (project_dir / ".env.example").exists():
        (project_dir / ".env.example").write_text("# Add your environment variables here\n")
        console.print("[green]✓[/green] .env.example created")

    # --- Branch protection ---
    if setup_branch_protection and settings.github_token:
        try:
            set_branch_protection(repo_name)
            console.print("[green]✓[/green] Branch protection rules applied")
        except GitHubError as e:
            console.print(f"[yellow]Warning:[/yellow] Branch protection failed: {e}")

    # --- Secrets ---
    if all_secrets and settings.github_token:
        try:
            set_repo_secrets(repo_name, all_secrets)
            console.print(f"[green]✓[/green] {len(all_secrets)} secret(s) pushed to GitHub:")
            for key in all_secrets:
                console.print(f"    [dim]• {key}[/dim]")
        except (GitHubError, RuntimeError) as e:
            console.print(f"[yellow]Warning:[/yellow] Secrets failed: {e}")

    console.print(f"\n[bold green]Done![/bold green] Commit and push to trigger the pipeline:")
    console.print("  git add .github/")
    console.print('  git commit -m "ci: add forge pipeline"')
    console.print("  git push")


def _ask_choice(label: str, choices: list) -> str:
    import questionary
    result = questionary.select(label, choices=choices).ask()
    if not result:
        raise typer.Exit(0)
    return result


def _parse_env_example(path: Path) -> dict:
    """Returns {key: value} from .env.example. Value is empty string if not set."""
    result = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("=", 1)
        key = parts[0].strip()
        value = parts[1].strip() if len(parts) > 1 else ""
        if key:
            result[key] = value
    return result


def _ask_type() -> str:
    import questionary
    project_type = questionary.select("  Project type", choices=PROJECT_TYPES).ask()
    if not project_type:
        raise typer.Exit(0)
    return project_type
